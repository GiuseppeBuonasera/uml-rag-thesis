"""
Smoke test MANUALE del server locale di LM Studio (Passo 3a, 2026-10-05; corretto il 2026-10-06 dopo il primo smoke
test con Gemma 4 12B QAT; opzione --save il 2026-10-06). NON fa parte dei test automatici: lo esegue l'utente con LM
Studio aperto e un modello caricato. Solo prompt banali, nessun dato del corpus o del test set.

Uso:
    python experiments/smoke_lmstudio.py --list-models      # GET /v1/models, per leggere l'id esatto
    python experiments/smoke_lmstudio.py --model <id del modello in LM Studio> [--base-url http://localhost:1234/v1]
    python experiments/smoke_lmstudio.py --model <id> --save   # salva anche la prova in docs/smoke_tests/

1. Risposta attesa: prompt che chiede di rispondere {"ok": true}; stampa risposta, modello, finish_reason, token
   riportati dal server e latenza.
2. Verifica del seed: un prompt banale con risposte variabili (inventare il nome di un gatto) inviato due volte con lo
   stesso seed (le risposte devono coincidere) e una volta con un seed diverso, prima con temperature 0.8 (caso
   significativo: senza seed due risposte uguali sono improbabili) e poi con temperature 0 (riportato, ma poco
   informativo). Per ogni chiamata stampa finish_reason e token di completamento. Esito: "si", "no", "non
   determinabile" (risposta uguale anche con seed diverso) oppure "non valutabile" se una risposta e' vuota o
   troncata (finish_reason = length): in quel caso NON si conclude mai si' o no.
3. Ragionamento: per ogni risposta, marcatori nel testo (<think>, Gemma 4 <|channel>thought ... <channel|>, ...) e
   campo separato (reasoning_content) con i token. Se c'e' ragionamento stampa un avviso ben visibile
   (REASONING_WARNING): va disattivato in LM Studio, perche' consuma max_tokens e lascia la risposta vuota.
Tutti i parametri di campionamento sono inviati in modo esplicito (top_k compreso), come nel runner, e stampati.

--save: scrive l'output completo in docs/smoke_tests/<data>_<id-modello>_smokeN.txt (intestazione con data/ora,
base_url, id del modello, versione e sha256 dello script) e accanto <stesso nome>.json con gli esiti strutturati
(confrontabili tra modelli). N e' progressivo per data e modello; un file esistente non si sovrascrive mai (creazione
esclusiva). Se una chiamata fallisce, la prova si salva comunque, con l'errore.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
import traceback
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
from llm_client import GenerationParams, LMStudioClient  # noqa: E402
from postprocess import reasoning_markers, strip_reasoning  # noqa: E402

SCRIPT_VERSION = "2026-10-06.3"  # da aggiornare a ogni modifica del comportamento dello script
SAVE_DIR = ROOT / "docs" / "smoke_tests"
PROMPT_OK = 'Reply with exactly this JSON object and nothing else: {"ok": true}'
PROMPT_SEED = "Invent an unusual name for a cat and write one short sentence about it."
SEED, OTHER_SEED = 1234, 98765
TOP_P, TOP_K = 1.0, 40  # solo per lo smoke test: parametri espliciti, nessun default del modello
OK_MAX_TOKENS = 1024
SEED_MAX_TOKENS = 512  # sufficiente per una frase sul gatto SENZA ragionamento
NOT_EVALUABLE = "non valutabile (risposte vuote o troncate)"
REASONING_WARNING = ("RAGIONAMENTO ATTIVO: disattiva Enable Thinking nelle impostazioni del modello in LM Studio "
                     "(My Models), poi ricarica il modello")


def has_reasoning(res) -> bool:
    return bool(res.reasoning_field or reasoning_markers(res.text))


def warn_reasoning() -> None:
    bar = "!" * len(REASONING_WARNING)
    print(f"\n{bar}\n{REASONING_WARNING}\n{bar}\n")


def describe_reasoning(res) -> None:
    markers = reasoning_markers(res.text)
    print(f"marcatori di ragionamento nel testo: {', '.join(markers) if markers else 'nessuno'}")
    if res.reasoning_field:
        print(f"campo di ragionamento separato: {res.reasoning_field}, {len(res.reasoning_text)} caratteri, "
              f"{res.reasoning_tokens} token ({res.reasoning_tokens_source})")
    else:
        print("campo di ragionamento separato: assente")


def call_record(res, seed: int | None = None) -> dict:
    """Esito strutturato di una chiamata (per il .json di --save)."""
    rec = {"seed": seed, "answer": strip_reasoning(res.text)[0].strip(), "finish_reason": res.finish_reason,
           "prompt_tokens": res.prompt_tokens, "completion_tokens": res.completion_tokens,
           "latency_s": round(res.latency_s, 3), "request_params": res.request_params,
           "params_not_sent": res.params_not_sent, "model_reported": res.model,
           "reasoning": {"present": has_reasoning(res), "field": res.reasoning_field,
                         "chars": len(res.reasoning_text), "tokens": res.reasoning_tokens,
                         "tokens_source": res.reasoning_tokens_source, "markers_in_text": reasoning_markers(res.text)}}
    if seed is None:
        rec.pop("seed")
    return rec


def show(res) -> None:
    print(f"risposta      : {res.text!r}")
    print(f"modello       : {res.model}")
    print(f"finish_reason : {res.finish_reason}")
    print(f"token (server): prompt={res.prompt_tokens} completion={res.completion_tokens}")
    print(f"latenza       : {res.latency_s:.2f} s")
    print(f"parametri     : {res.request_params}" + (f"  (non inviati: {res.params_not_sent})"
                                                   if res.params_not_sent else ""))
    describe_reasoning(res)


def seed_verdict(results) -> str:
    """results = [stesso seed, stesso seed, seed diverso]. Risposte vuote o troncate -> non valutabile, mai si'/no."""
    answers = [strip_reasoning(r.text)[0].strip() for r in results]
    if any(not ans or r.finish_reason == "length" for ans, r in zip(answers, results)):
        return NOT_EVALUABLE
    a, b, c = answers
    if a != b:
        return "no"
    return "si" if c != a else "non determinabile (risposta uguale anche con seed diverso)"


def seed_check(client: LMStudioClient, temperature: float) -> dict:
    msgs = [{"role": "user", "content": PROMPT_SEED}]
    seeds = (SEED, SEED, OTHER_SEED)
    results = [client.generate(msgs, GenerationParams(temperature=temperature, top_p=TOP_P, top_k=TOP_K,
                                                      max_tokens=SEED_MAX_TOKENS, seed=sd)) for sd in seeds]
    print(f"\n--- seed, temperature {temperature}")
    print(f"parametri: {results[0].request_params}")
    for label, sd, r in zip(("(1)", "(2)", "   "), seeds, results):
        # si confronta il testo senza ragionamento (il ragionamento puo' variare anche quando la risposta coincide)
        print(f"seed {sd} {label}: {strip_reasoning(r.text)[0].strip()!r}  [finish_reason={r.finish_reason}, "
              f"token di completamento={r.completion_tokens}]")
        if has_reasoning(r):
            describe_reasoning(r)
    reasoning = any(has_reasoning(r) for r in results)
    if reasoning:
        warn_reasoning()
    verdict = seed_verdict(results)
    print(f"seed rispettato: {verdict}" + ("" if temperature > 0 else "   [temperature 0: poco informativo]"))
    return {"temperature": temperature, "verdict": verdict, "reasoning_present": reasoning,
            "calls": [call_record(r, sd) for sd, r in zip(seeds, results)]}


def run_checks(client: LMStudioClient, summary: dict) -> None:
    """Esegue i controlli stampando l'output e riempiendo `summary` man mano (resta valido anche se fallisce)."""
    print("--- 1. risposta attesa {\"ok\": true}")
    res = client.generate([{"role": "user", "content": PROMPT_OK}],
                          GenerationParams(temperature=0.0, top_p=TOP_P, top_k=TOP_K, max_tokens=OK_MAX_TOKENS,
                                           seed=SEED))
    show(res)
    if has_reasoning(res):
        warn_reasoning()
    body, had_reasoning = strip_reasoning(res.text)
    try:
        ok = json.loads(body.strip()) == {"ok": True}
    except json.JSONDecodeError:
        ok = False
    print(f"blocchi di ragionamento rimossi dal testo prima del controllo: {'si' if had_reasoning else 'no'}")
    print(f"risposta attesa {{\"ok\": true}}: {'SI' if ok else 'NO'}")
    summary["ok_check"] = {"expected_answer": ok, **call_record(res)}

    print("\n--- 2. verifica del seed")
    for temperature in (0.8, 0.0):
        summary["seed_checks"].append(seed_check(client, temperature))
    hot, cold = (c["verdict"] for c in summary["seed_checks"])
    print(f"\nRIEPILOGO: seed rispettato (temperature 0.8): {hot}; (temperature 0, poco informativo): {cold}")
    summary["reasoning_present"] = (summary["ok_check"]["reasoning"]["present"]
                                    or any(c["reasoning_present"] for c in summary["seed_checks"]))
    if summary["reasoning_present"]:
        warn_reasoning()


# --- --save ---------------------------------------------------------------------------------------------------------


class Tee(io.TextIOBase):
    """Scrive sul terminale e in memoria (output completo per --save)."""

    def __init__(self, stream):
        self.stream, self.buffer_ = stream, io.StringIO()

    def write(self, s):
        self.stream.write(s)
        self.buffer_.write(s)
        return len(s)

    def flush(self):
        self.stream.flush()


def model_slug(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", model).strip("-") or "modello"


def next_paths(save_dir: Path, date: str, model: str) -> tuple[Path, Path]:
    """Primo N libero (progressivo per data e modello) tale che ne' il .txt ne' il .json esistano."""
    prefix = f"{date}_{model_slug(model)}_smoke"
    used = [int(m.group(1)) for p in save_dir.glob(f"{prefix}*")
            if (m := re.fullmatch(re.escape(prefix) + r"(\d+)\.(txt|json)", p.name))]
    n = max(used, default=0) + 1
    return save_dir / f"{prefix}{n}.txt", save_dir / f"{prefix}{n}.json"


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def save_evidence(save_dir: Path, summary: dict, output: str) -> tuple[Path, Path]:
    save_dir.mkdir(parents=True, exist_ok=True)
    txt, js = next_paths(save_dir, summary["date"], summary["model_requested"])
    header = (f"Smoke test di LM Studio (experiments/smoke_lmstudio.py --save)\n"
              f"data/ora:          {summary['timestamp']}\n"
              f"base_url:          {summary['base_url']}\n"
              f"id del modello:    {summary['model_requested']}\n"
              f"versione script:   {summary['script_version']} (sha256 {summary['script_sha256']})\n"
              f"esiti strutturati: {js.name}\n" + "=" * 80 + "\n\n")
    with txt.open("x", encoding="utf-8") as f:  # "x": mai sovrascrivere
        f.write(header + output)
    with js.open("x", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return txt, js


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="")
    ap.add_argument("--base-url", default="http://localhost:1234/v1")
    ap.add_argument("--list-models", action="store_true")
    ap.add_argument("--save", action="store_true", help="salva output e esiti in docs/smoke_tests/")
    ap.add_argument("--save-dir", default=str(SAVE_DIR), help=argparse.SUPPRESS)  # per i test
    a = ap.parse_args(argv)
    if a.list_models or not a.model:
        with urllib.request.urlopen(f"{a.base_url.rstrip('/')}/models", timeout=30) as r:
            print(json.dumps(json.loads(r.read().decode("utf-8")), indent=2))
        if not a.model:
            print("\nIndica il modello con --model <id>.")
        return 0
    client = LMStudioClient(model=a.model, base_url=a.base_url, timeout_s=300, retries=1, backoff_s=1.0)
    summary = {"script_version": SCRIPT_VERSION, "script_sha256": script_sha256(),
               "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "date": time.strftime("%Y-%m-%d"),
               "base_url": a.base_url, "model_requested": a.model, "ok_check": None, "seed_checks": [],
               "reasoning_present": None, "error": None}
    if not a.save:
        run_checks(client, summary)
        return 0
    tee, real_stdout = Tee(sys.stdout), sys.stdout
    sys.stdout = tee
    try:
        run_checks(client, summary)
    except Exception as e:  # la prova si salva comunque, con l'errore
        summary["error"] = f"{type(e).__name__}: {e}"
        traceback.print_exc(file=tee)
    finally:
        sys.stdout = real_stdout
    txt, js = save_evidence(Path(a.save_dir), summary, tee.buffer_.getvalue())
    print(f"\nsalvati: {txt}\n         {js}")
    return 1 if summary["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
