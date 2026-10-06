"""
Client LLM (Passo 3a, 2026-10-05). Interfaccia comune: generate(messages, params) -> GenerationResult (risposta grezza +
metadati). NESSUNA chiamata reale nei test automatici: si usa MockClient o un server HTTP finto locale.

- MockClient: risposte preparate (dizionario o cartella di file <chiave>.txt), per i test e per la prova end-to-end.
- LMStudioClient: server LOCALE di LM Studio, API compatibile OpenAI (POST {base_url}/chat/completions, default
  http://localhost:1234/v1). Nessuna chiave API. Parametri: temperature, top_p, max_tokens, seed. LM Studio elenca
  seed tra i parametri supportati; che il server lo RISPETTI (stessa richiesta -> stessa risposta) si verifica con
  experiments/smoke_lmstudio.py. Timeout e retry con backoff esponenziale su errori di rete, timeout, 5xx e 429; gli
  altri 4xx (richiesta sbagliata) falliscono subito. Solo libreria standard (urllib).
- Parametri di campionamento (2026-10-06): LMStudioClient invia SEMPRE in modo esplicito temperature, top_p, top_k,
  max_tokens e seed (tutti elencati come supportati nella pagina "Chat Completions" della compatibilita' OpenAI di LM
  Studio), cosi' nessuno resta al default del modello (per Gemma 4: temperature 1, top_k 64, top_p 0.95). Un parametro
  dichiarato non supportato (`unsupported_params`, da config) non si invia e si registra nei metadati
  (`GenerationResult.params_not_sent`); un parametro a None fa fallire la richiesta.
- Ragionamento in un campo separato (2026-10-06): se il messaggio ha `reasoning_content` (impostazione di LM Studio
  "separate reasoning_content and content in API responses") o `reasoning`, il testo va in
  `GenerationResult.reasoning_text` e nel raw, MAI in `text`: il post-processing estrae il JSON solo da `text`. I
  token del ragionamento: da usage.completion_tokens_details.reasoning_tokens se il server li fornisce, altrimenti
  stimati con cl100k_base (`reasoning_tokens_source`).
- CachedClient: cache su disco davanti a qualsiasi client. Chiave = sha256 di (messaggi, modello, parametri, indice di
  ripetizione): una chiamata gia' fatta non si ripete, una ripetizione diversa si'.

Output strutturato: LM Studio accetta su /v1/chat/completions response_format = {"type": "json_schema", "json_schema":
{"name", "strict", "schema"}} (campionamento vincolato da grammatica in llama.cpp per i GGUF, Outlines per MLX; non
tutti i modelli lo supportano, specie sotto i 7B). Qui lo schema e' evaluation/uml-model-4.schema.json. Preparato ma
DISATTIVATO di default (structured_output=False): attivarlo e' una decisione metodologica (domanda ai relatori).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))  # token_estimate (stima dei token del ragionamento)
SCHEMA_PATH = ROOT / "evaluation" / "uml-model-4.schema.json"


@dataclass(frozen=True)
class GenerationParams:
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 8192
    seed: int | None = None
    top_k: int | None = None  # obbligatorio (non None) con LM Studio: vedi SAMPLING_PARAMS
    structured_output: bool = False  # response_format json_schema (schema Apollon v4): DISATTIVATO di default


@dataclass
class GenerationResult:
    text: str
    finish_reason: str | None  # "stop", "length" (troncata dal limite max_tokens o dal contesto), ...
    model: str
    params: dict
    repetition: int
    latency_s: float
    prompt_tokens: int | None = None  # dal server, se li fornisce (usage)
    completion_tokens: int | None = None
    cached: bool = False
    raw: dict = field(default_factory=dict)
    reasoning_text: str = ""  # ragionamento restituito in un campo separato (mai usato per l'estrazione del JSON)
    reasoning_field: str | None = None  # "reasoning_content" | "reasoning" | None
    reasoning_tokens: int | None = None
    reasoning_tokens_source: str | None = None  # "server" | "stima_cl100k" | None
    request_params: dict = field(default_factory=dict)  # parametri di campionamento effettivamente inviati
    params_not_sent: list = field(default_factory=list)  # parametri dichiarati non supportati dall'endpoint


class LLMClient:
    model: str = ""
    kind: str = ""

    def generate(self, messages: list[dict], params: GenerationParams, repetition: int = 0,
                 key: str = "default") -> GenerationResult:
        raise NotImplementedError


def cache_key(messages: list[dict], model: str, params: GenerationParams, repetition: int) -> str:
    payload = {"messages": messages, "model": model, "params": asdict(params), "repetition": repetition}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class MockClient(LLMClient):
    """`key` (il runner passa l'id dell'esercizio) sceglie la risposta; se manca si usa "default". Conta le chiamate."""

    kind = "mock"

    def __init__(self, responses: dict[str, str] | None = None, responses_dir: Path | str | None = None,
                 model: str = "mock", finish_reasons: dict[str, str] | None = None):
        self.responses = {}
        if responses_dir:
            for p in sorted(Path(responses_dir).glob("*.txt")):
                self.responses[p.stem] = p.read_text(encoding="utf-8")
        self.responses.update(responses or {})
        self.model = model
        self.finish_reasons = finish_reasons or {}
        self.calls = 0

    def generate(self, messages, params, repetition=0, key="default") -> GenerationResult:
        self.calls += 1
        text = self.responses.get(key, self.responses.get("default", ""))
        return GenerationResult(text=text, finish_reason=self.finish_reasons.get(key, "stop"), model=self.model,
                                params=asdict(params), repetition=repetition, latency_s=0.0)


SAMPLING_PARAMS = ("temperature", "top_p", "top_k", "max_tokens", "seed")  # inviati SEMPRE in modo esplicito
REASONING_FIELDS = ("reasoning_content", "reasoning")


class LMStudioClient(LLMClient):
    kind = "lmstudio"

    def __init__(self, model: str, base_url: str = "http://localhost:1234/v1", timeout_s: float = 600.0,
                 retries: int = 3, backoff_s: float = 2.0, unsupported_params: list[str] | tuple = ()):
        self.model, self.base_url = model, base_url.rstrip("/")
        self.timeout_s, self.retries, self.backoff_s = timeout_s, retries, backoff_s
        unknown = set(unsupported_params) - set(SAMPLING_PARAMS)
        if unknown:
            raise ValueError(f"unsupported_params sconosciuti: {sorted(unknown)}")
        self.unsupported = [p for p in SAMPLING_PARAMS if p in set(unsupported_params)]
        self.attempts = 0  # tentativi dell'ultima generate (per i test sul retry)

    def sampling_params(self, params: GenerationParams) -> dict:
        sent = {}
        for name in SAMPLING_PARAMS:
            if name in self.unsupported:
                continue
            value = getattr(params, name)
            if value is None:
                raise ValueError(f"parametro {name} non impostato: va inviato in modo esplicito (nessun default del "
                                 "modello)")
            sent[name] = value
        return sent

    def request_body(self, messages: list[dict], params: GenerationParams) -> dict:
        body: dict[str, Any] = {"model": self.model, "messages": messages, **self.sampling_params(params),
                                "stream": False}
        if params.structured_output:
            body["response_format"] = {"type": "json_schema", "json_schema": {
                "name": "apollon_v4_class_diagram", "strict": True,
                "schema": json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))}}
        return body

    def generate(self, messages, params, repetition=0, key="default") -> GenerationResult:
        data = json.dumps(self.request_body(messages, params), ensure_ascii=False).encode("utf-8")
        last_error: Exception | None = None
        self.attempts = 0
        for attempt in range(self.retries + 1):
            self.attempts += 1
            req = urllib.request.Request(f"{self.base_url}/chat/completions", data=data, method="POST",
                                         headers={"Content-Type": "application/json"})
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    raw = json.loads(resp.read().decode("utf-8"))
                latency = time.perf_counter() - t0
                choice = raw["choices"][0]
                usage = raw.get("usage") or {}
                message = choice.get("message") or {}
                rfield = next((f for f in REASONING_FIELDS if message.get(f)), None)
                reasoning = message.get(rfield) if rfield else ""
                r_tokens = ((usage.get("completion_tokens_details") or {}).get("reasoning_tokens"))
                r_source = "server" if r_tokens is not None else None
                if r_tokens is None and reasoning:
                    from token_estimate import count_tokens  # stima, vocabolario versionato
                    r_tokens, r_source = count_tokens(reasoning), "stima_cl100k"
                return GenerationResult(text=message.get("content") or "",
                                        finish_reason=choice.get("finish_reason"), model=raw.get("model", self.model),
                                        params=asdict(params), repetition=repetition, latency_s=latency,
                                        prompt_tokens=usage.get("prompt_tokens"),
                                        completion_tokens=usage.get("completion_tokens"), raw=raw,
                                        reasoning_text=reasoning, reasoning_field=rfield, reasoning_tokens=r_tokens,
                                        reasoning_tokens_source=r_source,
                                        request_params=self.sampling_params(params),
                                        params_not_sent=list(self.unsupported))
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code < 500 and e.code != 429:
                    raise RuntimeError(f"LM Studio ha rifiutato la richiesta: HTTP {e.code} "
                                       f"{e.read().decode('utf-8', 'replace')[:500]}") from e
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                last_error = e
            if attempt < self.retries:
                time.sleep(self.backoff_s * (2 ** attempt))
        raise RuntimeError(f"LM Studio non raggiungibile dopo {self.retries + 1} tentativi: {last_error!r}")


class CachedClient(LLMClient):
    """Cache su disco: <cache_dir>/<sha256>.json. Una chiamata gia' fatta non si ripete."""

    def __init__(self, inner: LLMClient, cache_dir: Path | str):
        self.inner, self.cache_dir = inner, Path(cache_dir)
        self.model, self.kind = inner.model, inner.kind
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, messages, params, repetition=0, key="default") -> GenerationResult:
        path = self.cache_dir / f"{cache_key(messages, self.inner.model, params, repetition)}.json"
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            return GenerationResult(**{**d, "cached": True})
        result = self.inner.generate(messages, params, repetition, key=key)
        path.write_text(json.dumps(asdict(result), ensure_ascii=False), encoding="utf-8")
        return result
