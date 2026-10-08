"""
Runner degli esperimenti di generazione (Passo 3a, 2026-10-05).

Uso:
    python experiments/run_experiment.py experiments/configs/<config>.yaml            # run
    python experiments/run_experiment.py experiments/configs/<config>.yaml --resume   # ripresa di una run interrotta
    python experiments/run_experiment.py experiments/configs/<config>.yaml --dry-run  # solo prompt e stime, nessuna chiamata

Output in data/results/generation/<run_id>/ (la cartella esistente NON si sovrascrive; --resume la riprende):
    config.json        configurazione + provenienza (commit, tag testset-v1, sha256 di config_bm25.yaml, versioni)
    prompts/<call>.json  messaggi inviati + id degli esempi
    raw/<call>.json      risposta grezza e metadati (GenerationResult)
    parsed/<call>.json   JSON estratto (se decodificabile)
    validation.csv       livelli L0-L4 e istruzioni non rispettate, una riga per chiamata
    manifest.jsonl       una riga per chiamata: condizione, k, ripetizione, esempi, caratteri e token del prompt
                         (stimati con tiktoken cl100k_base e, se il server li fornisce, reali), finish_reason, livello
    cache/               cache su disco delle risposte (chiave = sha256 di messaggi, modello, parametri, ripetizione)
--dry-run scrive invece dry_run/<run_id>/: dry_run.csv (lunghezza dei prompt per esercizio, condizione e k),
    summary.md (tabelle: lunghezze, token di output stimati dai ground truth, finestre di contesto 8k/16k/32k).

Split (2026-10-06): "testset" (i 20 esercizi De Bari) oppure "corpus" (i 59 record convertiti; selezione degli esempi
in leave-one-out, vedi generation/prompt_builder.py: la query non compare mai tra i propri esempi). Temperature:
generation.temperature puo' essere una LISTA (es. [0.0, 0.3], pilota): ogni temperatura e' una cella, l'id della
chiamata riceve il suffisso __t<temperatura>. stop_on_reasoning: true ferma la run (dopo aver salvato la chiamata) se
in una risposta compare ragionamento (campo separato o marcatori nel testo).

Contesto effettivo (2026-10-06, dopo il primo tentativo del pilota fallito con il modello caricato a 8192): con il
client lmstudio, PRIMA della prima chiamata il runner legge da GET /api/v1/models il contesto dell'istanza caricata e
lo confronta con model_metadata.context_length: se non coincide, o il modello non e' caricato, non parte. Se l'endpoint
non risponde stampa un avviso e chiede conferma (o --accept-unverified-context). L'esito si registra in config.json
(provenance.server_context) e, a ogni ripresa, in server_checks.jsonl.

Configurazioni (secondo pilota, 2026-10-07): se la config ha "configurations", si esegue UNA configurazione per
volta con --configuration NOME (un solo modello caricato alla volta in LM Studio). Ogni configurazione sceglie un
modello da "models" (client + model_metadata), il formato di uscita (apollon | plantuml) e structured_output; la run si
chiama <run_id>__<NOME>. Le risposte PlantUML passano da generation/plantuml_postprocess.py (conversione in Apollon,
poi gli stessi L2-L4), solo se la regola automatica delle etichette e' approvata (plantuml_label_rule).

Un client reale (lmstudio) parte solo se la config contiene TUTTI i metadati del modello (MODEL_METADATA_REQUIRED),
senza segnaposto. Regola metodologica (STOP 2, decisions.md voce 66; versioni dalla voce 93): per uno stesso modello
(model_id + quantization) e una stessa versione di configurazione (config_version, assente = 1) la lunghezza di
contesto impostata in LM Studio e max_tokens sono IDENTICI per tutte le condizioni e tutti i k; dentro una config sono unici per costruzione, tra config diverse il runner confronta la nuova run con le
run gia' presenti nella cartella dei risultati e rifiuta di partire se differiscono. Ripetizioni: indice r = 0..n-1 nella chiave di cache; se generation.seed e' impostato, la
ripetizione r usa seed + r.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
import plantuml_postprocess as ppu  # noqa: E402
import compact_postprocess as cpp  # noqa: E402
import postprocess as pp  # noqa: E402
from plantuml_format import apollon_to_plantuml  # noqa: E402
from llm_client import CachedClient, GenerationParams, LMStudioClient, MockClient  # noqa: E402
from prompt_builder import BM25_CONFIG, CONDITIONS, PromptBuilder, PromptSpec, cl, serialize_diagram  # noqa: E402
import token_estimate  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
TOKENIZER = "cl100k_base"
WINDOWS = (8192, 16384, 32768)
MODEL_METADATA_REQUIRED = ("model_id", "quantization", "context_length", "lmstudio_version", "enable_thinking",
                           "kv_cache_quant", "flash_attention",  # impostazioni di caricamento (2026-10-07)
                           "hardware.cpu", "hardware.gpu", "hardware.ram_gb", "hardware.vram_gb")
BOOL_METADATA = ("enable_thinking", "flash_attention")
# parametri di campionamento espliciti in config, mai lasciati al default del modello (llm_client.SAMPLING_PARAMS)
GENERATION_REQUIRED = ("temperature", "top_p", "top_k", "max_tokens", "seed")
PLACEHOLDERS = {"", "TODO", "todo", "?", None}
SPLITS = ("testset", "corpus")


def is_placeholder(value) -> bool:
    if isinstance(value, list):
        return not value or any(is_placeholder(v) for v in value)
    return value is None or (isinstance(value, str) and value.strip() in PLACEHOLDERS)


def token_counter():
    """Stima dei token con tiktoken cl100k_base dal vocabolario versionato in generation/tokenizer/ (nessun download):
    APPROSSIMAZIONE, i modelli locali hanno tokenizer propri."""
    token_estimate.encoding()  # verifica subito lo sha256 del vocabolario
    return token_estimate.count_tokens


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def provenance() -> dict:
    import tiktoken
    return {"commit": git("rev-parse", "HEAD"), "worktree_dirty": bool(git("status", "--porcelain")),
            "testset_tag": "testset-v1", "testset_tag_commit": git("rev-parse", "testset-v1^{commit}"),
            "config_bm25": str(BM25_CONFIG.relative_to(ROOT)).replace("\\", "/"),
            "config_bm25_sha256": hashlib.sha256(BM25_CONFIG.read_bytes()).hexdigest(),
            "python": platform.python_version(), "tiktoken": tiktoken.__version__,
            "token_estimate": f"tiktoken {TOKENIZER} (approssimazione)",
            "token_vocab": str(token_estimate.VOCAB_PATH.relative_to(ROOT)).replace("\\", "/"),
            "token_vocab_sha256": token_estimate.expected_sha256(),
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")}


def missing_metadata(meta: dict | None) -> list[str]:
    out = []
    for key in MODEL_METADATA_REQUIRED:
        cur = meta or {}
        for part in key.split("."):
            cur = cur.get(part) if isinstance(cur, dict) else None
        if is_placeholder(cur) or cur == {}:
            out.append(key)
        elif key in BOOL_METADATA and not isinstance(cur, bool):
            out.append(f"{key} (true/false, come impostato in LM Studio)")
    return out


# Versione di configurazione (voce 93): le run senza la chiave (piloti, insieme di sviluppo dei formati) sono la
# versione 1 (contesto 32768, max_tokens 12288); le run nuove dichiarano config_version: 2 (32768, 4096). Il vincolo
# "contesto e max_tokens identici" vale tra run dello stesso modello E della stessa versione.
DEFAULT_CONFIG_VERSION = 1


def config_version(cfg: dict) -> int:
    return int(cfg.get("config_version", DEFAULT_CONFIG_VERSION))


def model_key(cfg: dict) -> tuple[str, str, int] | None:
    meta = cfg.get("model_metadata") or {}
    if cfg.get("client", {}).get("kind") != "lmstudio":
        return None
    return str(meta.get("model_id")), str(meta.get("quantization")), config_version(cfg)


def inconsistent_runs(cfg: dict, results_root: Path) -> list[str]:
    """Run gia' presenti dello stesso modello e della stessa versione di configurazione con context_length o
    max_tokens diversi da quelli di cfg."""
    key = model_key(cfg)
    if key is None or not results_root.exists():
        return []
    mine = ((cfg.get("model_metadata") or {}).get("context_length"), (cfg.get("generation") or {}).get("max_tokens"))
    out = []
    for path in sorted(results_root.glob("*/config.json")):
        other = json.loads(path.read_text(encoding="utf-8")).get("config", {})
        if other.get("run_id") == cfg.get("run_id") or model_key(other) != key:
            continue
        theirs = ((other.get("model_metadata") or {}).get("context_length"),
                  (other.get("generation") or {}).get("max_tokens"))
        if theirs != mine:
            out.append(f"{path.parent.name}: context_length={theirs[0]}, max_tokens={theirs[1]}")
    return out


def make_client(cfg: dict):
    c = cfg["client"]
    if c["kind"] == "mock":
        rdir = c.get("responses_dir")
        return MockClient(responses_dir=ROOT / rdir if rdir else None, model=c.get("model", "mock"),
                          finish_reasons=c.get("finish_reasons"))
    if c["kind"] == "lmstudio":
        missing = missing_metadata(cfg.get("model_metadata"))
        gen = cfg.get("generation") or {}
        missing += [f"generation.{k}" for k in GENERATION_REQUIRED if is_placeholder(gen.get(k))]
        if is_placeholder(c.get("model")):
            missing.append("client.model")
        if missing:
            raise SystemExit(f"client reale senza metadati obbligatori del modello: {missing} (vedi model_metadata)")
        schema = c.get("response_schema")
        return LMStudioClient(model=c["model"], base_url=c.get("base_url", "http://localhost:1234/v1"),
                              timeout_s=c.get("timeout_s", 600), retries=c.get("retries", 3),
                              backoff_s=c.get("backoff_s", 2.0), unsupported_params=c.get("unsupported_params", []),
                              response_schema=ROOT / schema if schema else None)
    raise SystemExit(f"client sconosciuto: {c['kind']}")


def temperatures(cfg: dict) -> list:
    """Temperature della run: lista se generation.temperature e' una lista, altrimenti [None] (una sola, senza
    suffisso nell'id della chiamata)."""
    t = (cfg.get("generation") or {}).get("temperature")
    return list(t) if isinstance(t, list) else [None]


def plan(cfg: dict, queries: list[dict]) -> list[tuple[dict, PromptSpec, int, float | None]]:
    """(query, spec, ripetizione, temperatura) nell'ordine di esecuzione. zero_shot e static non dipendono da k: una
    sola volta. Con piu' temperature l'ordine e' query > condizione > k > temperatura > ripetizione."""
    p = cfg.get("prompt", {})
    ids = cfg.get("query_ids")
    sel = [q for q in queries if not ids or q["id"] in ids]
    if ids and len(sel) != len(ids):
        raise SystemExit(f"query_ids non trovati nello split {cfg.get('split', 'testset')}: "
                         f"{sorted(set(ids) - {q['id'] for q in sel})}")
    out = []
    for q in sel:
        for cond in cfg["conditions"]:
            if cond not in CONDITIONS:
                raise SystemExit(f"condizione sconosciuta: {cond}")
            ks = [0] if cond == "zero_shot" else [2] if cond == "static" else cfg["k"]
            for k in ks:
                spec = PromptSpec(condition=cond, k=k, seed=cfg.get("seed", 0),
                                  serialization=p.get("serialization", "compact"),
                                  layout=p.get("layout", "user_only"), drop_interactive=p.get("drop_interactive", True),
                                  output_format=p.get("output_format", "apollon"))
                for t in temperatures(cfg):
                    for r in range(cfg.get("repetitions", 1)):
                        out.append((q, spec, r, t))
    return out


# regole automatiche delle etichette PlantUML approvate dall'utente (auto_v1: STOP 1 del secondo pilota, voce 79)
APPROVED_LABEL_RULES = ("auto_v1",)


def resolve_configuration(cfg: dict, name: str | None) -> dict:
    """Config piatta per UNA configurazione (client, model_metadata, formato, structured_output); invariata se la
    config non ha 'configurations'."""
    confs = cfg.get("configurations")
    if not confs:
        if name:
            raise SystemExit("--configuration indicata ma la config non ha 'configurations'")
        return cfg
    if not name:
        raise SystemExit(f"scegli una configurazione con --configuration: {sorted(confs)}")
    if name not in confs:
        raise SystemExit(f"configurazione sconosciuta {name}: {sorted(confs)}")
    conf = confs[name]
    model = cfg["models"][conf["model"]]
    out = {k: v for k, v in cfg.items() if k not in ("configurations", "models")}
    out["run_id"] = f"{cfg['run_id']}__{name}"
    out["configuration"] = name
    out["client"] = dict(model["client"])
    out["model_metadata"] = dict(model["model_metadata"])
    out["prompt"] = {**cfg.get("prompt", {}), "output_format": conf["output_format"]}
    out["generation"] = {**cfg.get("generation", {}), "structured_output": bool(conf.get("structured_output"))}
    if conf.get("structured_output"):
        out["client"]["response_schema"] = conf["response_schema"]
    return out


def check_label_rule(cfg: dict) -> None:
    if (cfg.get("prompt") or {}).get("output_format") == "plantuml":
        rule = cfg.get("plantuml_label_rule")
        if rule not in APPROVED_LABEL_RULES:
            raise SystemExit(f"plantuml_label_rule = {rule!r} non approvata (approvate: {list(APPROVED_LABEL_RULES)}): "
                             "la regola automatica delle etichette va approvata prima delle run PlantUML (voce 78)")


def call_id(qid: str, spec: PromptSpec, r: int, temperature: float | None = None) -> str:
    t = "" if temperature is None else f"__t{temperature:g}"
    return f"{qid}__{spec.condition}__k{spec.k}{t}__r{r}"


def params_for(cfg: dict, r: int, temperature: float | None = None) -> GenerationParams:
    g = dict(cfg.get("generation", {}))
    if temperature is not None:
        g["temperature"] = temperature
    params = GenerationParams(**g)
    return replace(params, seed=params.seed + r) if params.seed is not None else params


def stats(xs: list[int]) -> tuple[int, float, int]:
    return min(xs), statistics.median(xs), max(xs)


# --- dry run --------------------------------------------------------------------------------------------------------


def dry_run(cfg: dict, builder: PromptBuilder, queries: list[dict], out_dir: Path) -> str:
    ntok = token_counter()
    gen = dict(cfg.get("generation") or {})
    if isinstance(gen.get("temperature"), list):  # le lunghezze non dipendono dalla temperatura
        gen["temperature"] = gen["temperature"][0]
    cfg = {**cfg, "repetitions": 1, "generation": gen}
    rows = []
    for q, spec, _, _ in plan(cfg, queries):
        bp = builder.build(q, spec)
        rows.append({"query_id": q["id"], "condition": spec.condition, "k": spec.k, "analysis_only": bp.analysis_only,
                     "example_ids": "|".join(bp.example_ids), "prompt_chars": len(bp.text),
                     "prompt_tokens_est": ntok(bp.text)})
    if (cfg.get("prompt") or {}).get("output_format") == "plantuml":  # output = PlantUML canonico del GT
        gt_c = {q["id"]: ntok(apollon_to_plantuml(q["diagram_apollon_json"])) for q in queries}
        gt_i = dict(gt_c)
    else:
        gt_c = {q["id"]: ntok(serialize_diagram(q["diagram_apollon_json"], "compact", True)) for q in queries}
        gt_i = {q["id"]: ntok(serialize_diagram(q["diagram_apollon_json"], "indent2", True)) for q in queries}

    out_dir.mkdir(parents=True)
    with (out_dir / "dry_run.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[*rows[0], "gt_output_tokens_compact", "gt_output_tokens_indent2"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "gt_output_tokens_compact": gt_c[r["query_id"]],
                        "gt_output_tokens_indent2": gt_i[r["query_id"]]})

    groups: dict[tuple[str, int], list[dict]] = {}
    for r in rows:
        groups.setdefault((r["condition"], r["k"]), []).append(r)
    L = [f"# Dry run `{cfg['run_id']}`", "",
         f"Nessuna chiamata a un LLM. {len({r['query_id'] for r in rows})} esercizi dello split "
         f"`{cfg.get('split', 'testset')}`, prompt costruiti con "
         f"serializzazione `{cfg.get('prompt', {}).get('serialization', 'compact')}`, layout "
         f"`{cfg.get('prompt', {}).get('layout', 'user_only')}`. Token stimati con tiktoken `{TOKENIZER}`: "
         "**approssimazione**, i modelli locali usano tokenizer propri e i conteggi reali possono differire "
         "(il manifest delle run registra anche i token riportati dal server). Finestre: 8k = 8192, 16k = 16384, "
         "32k = 32768 token. oracle = solo analisi.", "",
         "## Lunghezza dei prompt (min / mediana / max sugli esercizi)", "",
         "| condizione | k | caratteri | token stimati |", "|---|---|---|---|"]
    for (c, k), g in groups.items():
        ch, tk = stats([r["prompt_chars"] for r in g]), stats([r["prompt_tokens_est"] for r in g])
        L.append(f"| {c} | {k} | {ch[0]} / {ch[1]:.0f} / {ch[2]} | {tk[0]} / {tk[1]:.0f} / {tk[2]} |")
    oc, oi = stats(list(gt_c.values())), stats(list(gt_i.values()))
    L += ["", "## Token di output stimati dai ground truth (senza `interactive`)", "",
          "| serializzazione | min | mediana | max |", "|---|---|---|---|",
          f"| compatta (stima richiesta) | {oc[0]} | {oc[1]:.0f} | {oc[2]} |",
          f"| indentata a 2 spazi (se il modello indenta) | {oi[0]} | {oi[1]:.0f} | {oi[2]} |", "",
          "Non include eventuali token di ragionamento (`<think>`) dei modelli che li producono.", "",
          "## Finestre di contesto: input + output stimato", "",
          "Per ogni esercizio: token del prompt + token del suo ground truth compatto. Celle = esercizi (sul totale) che "
          "stanno nella finestra; tra parentesi il caso peggiore (prompt piu' lungo + output massimo compatto, "
          f"{oc[2]} token): si / no.", "",
          "| condizione | k | " + " | ".join(f"{w // 1024}k" for w in WINDOWS) + " |",
          "|---|---|" + "---|" * len(WINDOWS)]
    for (c, k), g in groups.items():
        cells = []
        worst = max(r["prompt_tokens_est"] for r in g) + oc[2]
        for wnd in WINDOWS:
            n = sum(1 for r in g if r["prompt_tokens_est"] + gt_c[r["query_id"]] <= wnd)
            cells.append(f"{n}/{len(g)} ({'si' if worst <= wnd else 'no'})")
        L.append(f"| {c} | {k} | " + " | ".join(cells) + " |")
    L += ["", "Stessa tabella con output indentato (ground truth indentato di ciascun esercizio):", "",
          "| condizione | k | " + " | ".join(f"{w // 1024}k" for w in WINDOWS) + " |",
          "|---|---|" + "---|" * len(WINDOWS)]
    for (c, k), g in groups.items():
        cells = [f"{sum(1 for r in g if r['prompt_tokens_est'] + gt_i[r['query_id']] <= wnd)}/{len(g)}"
                 for wnd in WINDOWS]
        L.append(f"| {c} | {k} | " + " | ".join(cells) + " |")
    summary = "\n".join(L) + "\n"
    (out_dir / "summary.md").write_text(summary, encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps({"config": cfg, "provenance": provenance()}, indent=2,
                                                    ensure_ascii=False), encoding="utf-8")
    return summary


# --- run ------------------------------------------------------------------------------------------------------------


CONTEXT_WARNING = ("CONTESTO DEL MODELLO CARICATO NON VERIFICABILE: controlla in LM Studio (My Models / Developer) che "
                   "il modello sia caricato con Context Length = {expected}")


def check_server_context(client, cfg: dict, accept_unverified: bool = False, ask=input) -> dict:
    """Confronta il contesto dell'istanza caricata in LM Studio con model_metadata.context_length. Restituisce
    l'esito da registrare; SystemExit se non coincide, se il modello non e' caricato o se l'utente non conferma."""
    expected = (cfg.get("model_metadata") or {}).get("context_length")
    info = client.loaded_context()
    info["expected_context_length"] = expected
    info["checked_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if info["available"]:
        if not info["loaded"]:
            raise SystemExit(f"il modello {client.model} non risulta caricato in LM Studio ({info['endpoint']}): "
                             f"caricalo con Context Length = {expected} prima di lanciare la run")
        if any(c != expected for c in info["context_lengths"]):
            raise SystemExit(f"contesto del modello caricato {info['context_lengths']} diverso da quello del config "
                             f"({expected}): ricarica il modello in LM Studio con Context Length = {expected}")
        # Flash Attention: confrontata se LM Studio la riporta nella config dell'istanza (la quantizzazione della KV
        # cache non e' esposta da /api/v1/models: resta un metadato dichiarato, non verificato)
        fa_expected = (cfg.get("model_metadata") or {}).get("flash_attention")
        fa_loaded = [i["config"].get("flash_attention") for i in info["instances"] if "flash_attention" in i["config"]]
        if isinstance(fa_expected, bool) and any(fa != fa_expected for fa in fa_loaded):
            raise SystemExit(f"Flash Attention del modello caricato {fa_loaded} diversa da quella del config "
                             f"({fa_expected}): ricarica il modello in LM Studio con le impostazioni del config")
        info["verified"] = True
        return info
    bar = "!" * 100
    print(f"\n{bar}\n{CONTEXT_WARNING.format(expected=expected)}\n({info['endpoint']}: {info['error']})\n{bar}\n")
    if accept_unverified:
        info["verified"], info["accepted_by"] = False, "--accept-unverified-context"
        return info
    if ask is input and (not sys.stdin or not sys.stdin.isatty()):  # solo la conferma vera richiede un terminale
        raise SystemExit("contesto non verificabile e nessuna conferma possibile (input non interattivo): usa "
                         "--accept-unverified-context dopo aver controllato LM Studio")
    try:
        answer = ask(f"Confermi che il modello e' caricato con Context Length = {expected}? [si/no] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() != "si":
        raise SystemExit("run annullata: contesto non confermato")
    info["verified"], info["accepted_by"] = False, "conferma interattiva"
    return info


def run(cfg: dict, builder: PromptBuilder, queries: list[dict], out_dir: Path, resume: bool,
        accept_unverified_context: bool = False) -> dict:
    client = make_client(cfg)
    clash = inconsistent_runs(cfg, out_dir.parent)
    if clash:
        meta = cfg.get("model_metadata") or {}
        raise SystemExit(f"stesso modello ({meta.get('model_id')}, {meta.get('quantization')}) con context_length o "
                         f"max_tokens diversi da run esistenti della stessa versione di configurazione "
                         f"({config_version(cfg)}): {clash}. Devono essere identici per tutte le condizioni e tutti i k "
                         f"(docs/STATUS.md, regole della generazione)")
    ntok = token_counter()
    if out_dir.exists() and not resume:
        raise SystemExit(f"{out_dir} esiste gia': non si sovrascrive (usa --resume per riprendere)")
    if resume:
        saved = json.loads((out_dir / "config.json").read_text(encoding="utf-8"))["config"]
        if saved != cfg:
            raise SystemExit("--resume con una configurazione diversa da quella della run salvata")
    server_context = (check_server_context(client, cfg, accept_unverified_context)
                      if isinstance(client, LMStudioClient) else None)
    for sub in ("prompts", "raw", "parsed"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)
    if not resume:
        prov = provenance()
        if server_context is not None:
            prov["server_context"] = server_context
        if (cfg.get("generation") or {}).get("structured_output") and isinstance(client, LMStudioClient):
            prov["response_schema"] = str(client.response_schema.relative_to(ROOT)).replace("\\", "/")
            prov["response_schema_sha256"] = hashlib.sha256(client.response_schema.read_bytes()).hexdigest()
        if (cfg.get("prompt") or {}).get("output_format") == "plantuml":
            prov["plantuml_label_rule"] = cfg.get("plantuml_label_rule")
            prov["plantuml_postprocess_version"] = ppu.DEFAULT_VERSION  # v2 dal 2026-10-08 (voce 89)
        if (cfg.get("prompt") or {}).get("output_format") == "compact":
            prov["compact_format_spec"] = "docs/compact_format.md"  # voci 90-91
        (out_dir / "config.json").write_text(json.dumps({"config": cfg, "provenance": prov}, indent=2,
                                                        ensure_ascii=False), encoding="utf-8")
    elif server_context is not None:  # a ogni ripresa: config.json non si riscrive, l'esito va in un file a parte
        with (out_dir / "server_checks.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(server_context, ensure_ascii=False) + "\n")
    cached = CachedClient(client, out_dir / "cache")
    manifest_path = out_dir / "manifest.jsonl"
    done = set()
    if manifest_path.exists():
        done = {json.loads(line)["call_id"] for line in manifest_path.read_text(encoding="utf-8").splitlines() if line}
    val_path = out_dir / "validation.csv"
    counts = {"calls": 0, "skipped_done": 0, "from_cache": 0}
    for q, spec, r, temp in plan(cfg, queries):
        cid = call_id(q["id"], spec, r, temp)
        if cid in done:
            counts["skipped_done"] += 1
            continue
        bp = builder.build(q, spec)
        (out_dir / "prompts" / f"{cid}.json").write_text(json.dumps(
            {"messages": bp.messages, "example_ids": bp.example_ids, "spec": asdict(spec)}, ensure_ascii=False,
            indent=1), encoding="utf-8")
        params = params_for(cfg, r, temp)
        res = cached.generate(bp.messages, params, r, key=q["id"])
        counts["calls"] += 1
        counts["from_cache"] += res.cached
        (out_dir / "raw" / f"{cid}.json").write_text(json.dumps(asdict(res), ensure_ascii=False, indent=1),
                                                     encoding="utf-8")
        if spec.output_format == "plantuml":
            v = ppu.validate_plantuml_response(res.text, res.finish_reason, cid)
        elif spec.output_format == "compact":  # JSON compatto -> struttura -> espansore unico (voce 91)
            v = cpp.validate_compact_response(res.text, res.finish_reason, cid)
        else:
            v = pp.validate_response(res.text, res.finish_reason)
        if v.diagram is not None:
            (out_dir / "parsed" / f"{cid}.json").write_text(json.dumps(v.diagram, ensure_ascii=False, indent=1),
                                                            encoding="utf-8")
        row = {"call_id": cid, "query_id": q["id"], "condition": spec.condition, "k": spec.k, "repetition": r,
               "temperature": params.temperature,
               **v.row()}
        new_file = not val_path.exists()
        with val_path.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new_file:
                w.writeheader()
            w.writerow(row)
        entry = {"call_id": cid, "split": cfg.get("split", "testset"), "configuration": cfg.get("configuration"),
                 "output_format": spec.output_format, "structured_output": params.structured_output,
                 "valid_L3": v.level >= 3, "query_id": q["id"],
                 "condition": spec.condition, "k": spec.k, "repetition": r, "temperature": params.temperature,
                 "analysis_only": bp.analysis_only, "example_ids": bp.example_ids,
                 "prompt_sha256": hashlib.sha256(json.dumps(bp.messages, ensure_ascii=False).encode()).hexdigest(),
                 "prompt_chars": len(bp.text), "prompt_tokens_est": ntok(bp.text),
                 "prompt_tokens_server": res.prompt_tokens, "completion_tokens_server": res.completion_tokens,
                 "model": res.model, "params": res.params, "finish_reason": res.finish_reason,
                 "latency_s": round(res.latency_s, 3), "cached": res.cached, "level": v.level, "failure": v.failure,
                 "l4_rewrites": v.l4_rewrites, "style_raw_count": len(v.style_raw),
                 "format_issues": sorted(v.format_issues), "layout_issues": sorted(v.layout_issues),
                 "request_params": res.request_params, "params_not_sent": res.params_not_sent,
                 "reasoning_field": res.reasoning_field, "reasoning_chars": len(res.reasoning_text),
                 "reasoning_tokens": res.reasoning_tokens, "reasoning_tokens_source": res.reasoning_tokens_source,
                 "reasoning_markers_in_content": pp.reasoning_markers(res.text),
                 "content_empty": not res.text.strip(),
                 "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
        with manifest_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if cfg.get("stop_on_reasoning") and (res.reasoning_field or pp.reasoning_markers(res.text)):
            raise SystemExit(f"ragionamento nella risposta {cid} (campo {res.reasoning_field}, marcatori "
                             f"{pp.reasoning_markers(res.text)}): run FERMATA (stop_on_reasoning). Disattiva Enable "
                             "Thinking in LM Studio; la chiamata e' salvata in raw/ e nel manifest")
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--accept-unverified-context", action="store_true",
                    help="parti anche se il contesto del modello caricato non e' verificabile via API (dopo averlo "
                         "controllato a mano in LM Studio)")
    ap.add_argument("--results-dir", default=str(RESULTS), help="radice dell'output (i test usano una cartella temporanea)")
    ap.add_argument("--configuration", help="configurazione da eseguire (config con 'configurations')")
    a = ap.parse_args(argv)
    cfg = resolve_configuration(yaml.safe_load(Path(a.config).read_text(encoding="utf-8")), a.configuration)
    if not a.dry_run:
        check_label_rule(cfg)
    split = cfg.get("split", "testset")
    if split not in SPLITS:
        raise SystemExit(f"split non supportato: {split} (ammessi: {SPLITS})")
    candidates, test_queries = cl.load_all()
    builder = PromptBuilder(candidates, test_queries)
    # corpus: le query sono i 59 candidati (selezione LOO nel prompt builder); il test set non viene usato
    queries = test_queries if split == "testset" else candidates
    root = Path(a.results_dir)
    if a.dry_run:
        out = root / "dry_run" / cfg["run_id"]
        if out.exists():
            raise SystemExit(f"{out} esiste gia': non si sovrascrive")
        print(dry_run(cfg, builder, queries, out))
        print(f"scritto in {out}")
        return 0
    counts = run(cfg, builder, queries, root / cfg["run_id"], a.resume, a.accept_unverified_context)
    print(f"run {cfg['run_id']}: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
