"""
Analisi del secondo pilota, strada 1 PlantUML contro strada 2 JSON vincolato (docs/decisions.md: regola nella voce 78,
approvata allo STOP 1 nella voce 79; questo script nella voce 82). Scritto PRIMA delle run: da qui in poi la regola nel
codice (decide, criteri di spareggio, soglie) NON si modifica senza una nuova voce in docs/decisions.md.

Nessuna chiamata a un LLM. Legge in sola lettura le run data/results/generation/pilot2_formats__<C>/ (C = P-G, P-Q,
J-G, J-Q) e ricalcola tutto dalle risposte grezze (raw/): strada 1 con generation/plantuml_postprocess.py, strada 2 con
generation/postprocess.py, come il runner. Scrive solo data/results/generation/pilot2_formats_analysis/summary.md.

REGOLA DI DECISIONE (voce 78, approvata nella voce 79), per ogni configurazione C (12 risposte):
- S(C) = risposte che arrivano a un Apollon valido fino a L3 (livello >= 3). Strada 1: P0 + P1b + conversione + L2 + L3;
  strada 2: L0-L3.
- Controllo preliminare: una configurazione che non si puo' eseguire o fermata per ragionamento e' esclusa e
  segnalata; se ne restano meno di 2 ci si ferma senza decidere. Lettura operativa (voce 82): "non si puo' eseguire" =
  run assente (nessun config.json) oppure incompleta (meno risposte del previsto nel manifest, es. server che rifiuta
  response_format alla prima chiamata, oppure run interrotta: in quel caso va ripresa con --resume prima dell'analisi).
- Soglia minima: se il massimo di S e' sotto 6/12, nessuna configurazione passa al Passo 3b.
- Scelta: la configurazione con S piu' alto (strada e modello insieme).
- Pareggio = configurazioni con S >= max(S) - 1. Tra queste, nell'ordine (ogni criterio tiene solo le migliori):
  (1) meno troncamenti (finish_reason = length); (2) Jaccard medio dei nomi di classe con il GT piu' alto (risposte
  valide fino a L3); (3) accordo sulle relazioni piu' alto (relazioni del GT con stessa coppia di classi e stesso tipo
  / relazioni del GT, sommate sulle risposte valide); (4) latenza mediana piu' bassa (tutte le risposte); poi strada 1
  (PlantUML) e, a parita' di strada, Gemma.
- Aggiunta della voce 79: si riporta SEMPRE la classifica completa delle 4 configurazioni (S, troncamenti, criteri di
  spareggio), non solo la vincitrice. Posizione k = vincitrice della stessa regola (pareggio entro 1 e spareggi)
  applicata alle configurazioni non ancora classificate; le escluse in fondo, con il motivo.

RIFERIMENTI (voce 83), solo descrittivi, FUORI dalla regola e dalla classifica: J0-Q (Qwen, Apollon JSON libero, run
pilot2_formats__J0-Q) e Gemma in Apollon JSON libero a temperature 0.3 del primo pilota (pilot_temperature_gemma4-12b-qat,
18 risposte, stesso prompt: controllato con lo sha256 dei messaggi), con le stesse metriche, piu' la tabella 2x2 di S
della strada JSON (Gemma / Qwen x libero / vincolato).

Riportato ma fuori dalla regola: livelli P0 / P1b / P1 e L0-L4, esiti di fallimento, righe scartate, verso e
molteplicita' delle relazioni, scambi di tipo, latenze e token, rapporto token reali / stima, diagnostici.

ANALISI v2 (voce 89), SOLO DESCRITTIVA: `--postprocess v2` rilegge le STESSE risposte salvate con il post-processing
PlantUML v2 (intestazioni extends / implements riscritte, blocco senza @enduml letto fino alla fine) e scrive
data/results/generation/pilot2_formats_analysis_v2/summary.md, accanto all'analisi originale (post-processing
pilot2_v1, invariata). La regola vi e' riapplicata solo per descrivere l'effetto delle correzioni: l'esito valido del
secondo pilota resta quello dell'analisi originale (voce 88). La strada 2 (JSON) non cambia tra le due versioni.

Uso:
    python experiments/analyze_pilot2.py [--results-dir data/results/generation] [--postprocess pilot2_v1|v2]
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import analyze_pilot as ap  # noqa: E402  (nomi di classe, confronto delle relazioni: stesse definizioni del primo pilota)
import plantuml_postprocess as ppu  # noqa: E402
import postprocess as pp  # noqa: E402
from prompt_builder import cl  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
RUN_PREFIX = "pilot2_formats"
OUT_NAME = "pilot2_formats_analysis"
CONFIGURATIONS = ("P-G", "P-Q", "J-G", "J-Q")  # ordine di presentazione (strada-modello)
PATH_NAME = {"P": "strada 1 (PlantUML)", "J": "strada 2 (JSON vincolato)"}
MODEL_NAME = {"G": "Gemma 4 12B QAT", "Q": "Qwen2.5-Coder 7B"}
PILOT2_CONFIG = ROOT / "experiments" / "configs" / "pilot2_formats.yaml"
SIZE_NOTE = ("Il confronto generalista / coding e' tra modelli di **taglia diversa**: Gemma 4 12B QAT (generalista) "
             "contro Qwen2.5-Coder 7B Instruct Q6_K (coding), perche' il 14B non entra in VRAM a 32768 (voci 84-85). Le "
             "differenze tra i due modelli non si possono attribuire alla sola specializzazione sul codice.")
# --- costanti della regola (voce 78): non si modificano senza una nuova voce in docs/decisions.md ---
MIN_INCLUDED = 2  # meno di 2 configurazioni eseguibili -> nessuna decisione
MIN_S = 6  # massimo di S sotto 6/12 -> nessuna configurazione passa al Passo 3b
TIE_WINDOW = 1  # pareggio: entro 1 risposta dal massimo di S
EPS = 1e-9  # uguaglianza tra valori reali (Jaccard, accordo, latenza)
# --- RIFERIMENTI (voce 83): solo descrittivi, FUORI dalla regola e dalla classifica ---
REFERENCE_CONFIGURATIONS = ("J0-Q",)  # Qwen in Apollon JSON libero (senza response_format)
FIRST_PILOT_RUN = "pilot_temperature_gemma4-12b-qat"  # Gemma in Apollon JSON libero, primo pilota (voce 75)
FIRST_PILOT_TEMPERATURE = 0.3  # stessa temperatura del secondo pilota
FIRST_PILOT_NAME = "G-libero (primo pilota)"


# criteri di spareggio, nell'ordine: (etichetta, grandezza, verso: +1 = vince il valore piu' alto, -1 = il piu' basso).
# Un valore non definito (None: nessuna risposta valida o nessuna relazione nel GT) perde sempre.
TIEBREAKS = (
    ("meno troncamenti", "truncated", -1),
    ("Jaccard medio dei nomi di classe piu' alto", "J", +1),
    ("accordo sulle relazioni piu' alto", "R", +1),
    ("latenza mediana piu' bassa", "latency_median", -1),
    ("strada 1 (PlantUML)", "plantuml", +1),
    ("Gemma", "gemma", +1),
)


def value(m: dict, field: str):
    if field == "plantuml":
        return int(m["name"].startswith("P"))
    if field == "gemma":
        return int(m["name"].endswith("G"))
    return m[field]


def key(m: dict, field: str, sign: int) -> float:
    x = value(m, field)
    return float("-inf") if x is None else sign * x


# --- metriche -------------------------------------------------------------------------------------------------------


def validate(output_format: str, text: str, finish_reason: str | None, call_id: str,
             version: str = ppu.PILOT2_VERSION):
    """Stessa validazione del runner (experiments/run_experiment.run). Strada 1: post-processing nella versione con
    cui e' stata fatta l'analisi originale (pilot2_v1), salvo richiesta esplicita della v2 (analisi descrittiva)."""
    if output_format == "plantuml":
        return ppu.validate_plantuml_response(text, finish_reason, call_id, version)
    return pp.validate_response(text, finish_reason)


def metrics(name: str, calls: list[dict]) -> dict:
    """Metriche di una configurazione. Ogni chiamata: {"v": Validation, "gt": diagramma, "latency_s": float, ...}."""
    valid = [c for c in calls if c["v"].level >= 3]
    rel = Counter()
    for c in valid:
        rel += ap.compare_relations(c["v"].diagram, c["gt"])
    lat = [c["latency_s"] for c in calls if c.get("latency_s") is not None]
    return {
        "name": name, "n": len(calls), "S": len(valid),
        "truncated": sum(bool(c["v"].truncated) for c in calls),
        "J": statistics.mean(cl.jaccard(ap.class_names(c["v"].diagram), ap.class_names(c["gt"])) for c in valid)
        if valid else None,
        "R": rel["same_type"] / rel["gt_edges"] if rel["gt_edges"] else None,
        "latency_median": statistics.median(lat) if lat else None,
        "relations": rel,
    }


# --- regola di decisione (voce 78) ----------------------------------------------------------------------------------


def pick(pool: dict[str, dict]) -> tuple[str, list[dict]]:
    """Vincitrice tra le configurazioni del pool: pareggio entro TIE_WINDOW dal massimo di S, poi gli spareggi
    nell'ordine. Ritorna (nome, passi) dove ogni passo registra il criterio, i valori e chi resta."""
    best = max(m["S"] for m in pool.values())
    tied = sorted((n for n, m in pool.items() if m["S"] >= best - TIE_WINDOW), key=CONFIGURATIONS.index)
    steps = [{"criterion": f"S piu' alto (pareggio: S >= {best} - {TIE_WINDOW})",
              "values": {n: pool[n]["S"] for n in pool}, "kept": list(tied)}]
    for crit, field, sign in TIEBREAKS:
        if len(tied) == 1:
            break
        top = max(key(pool[n], field, sign) for n in tied)
        kept = [n for n in tied if key(pool[n], field, sign) >= top - EPS]
        steps.append({"criterion": crit, "values": {n: value(pool[n], field) for n in tied}, "kept": kept})
        tied = kept
    return tied[0], steps


def decide(configs: dict[str, dict]) -> dict:
    """configs: nome -> {"excluded": motivo o None, "metrics": dict o None}. Applica la regola della voce 78 e
    costruisce la classifica completa."""
    included = {n: c["metrics"] for n, c in configs.items() if not c.get("excluded")}
    excluded = {n: c["excluded"] for n, c in configs.items() if c.get("excluded")}
    out = {"included": sorted(included, key=CONFIGURATIONS.index), "excluded": excluded, "winner": None,
           "steps": [], "reasons": [], "ranking": []}
    # classifica completa: la regola applicata ripetutamente alle configurazioni restanti
    rest = dict(included)
    while rest:
        n, steps = pick(rest)
        out["ranking"].append({"name": n, "decided_by": steps[-1]["criterion"]})
        del rest[n]
    out["ranking"] += [{"name": n, "decided_by": None, "excluded": excluded[n]}
                       for n in sorted(excluded, key=CONFIGURATIONS.index)]
    if len(included) < MIN_INCLUDED:
        out["reasons"].append(f"configurazioni eseguibili: {len(included)} (servono almeno {MIN_INCLUDED})")
        out["outcome"] = "STOP: nessuna decisione (controllo preliminare)"
        return out
    best = max(m["S"] for m in included.values())
    if best < MIN_S:
        out["reasons"].append(f"miglior S = {best}/12, sotto la soglia minima di {MIN_S}/12")
        out["outcome"] = "STOP: nessuna configurazione passa al Passo 3b (soglia minima)"
        return out
    out["winner"], out["steps"] = pick(included)
    out["outcome"] = f"scelta la configurazione {out['winner']}"
    return out


# --- caricamento ----------------------------------------------------------------------------------------------------


def expected_model_ids(config_path: Path = PILOT2_CONFIG) -> dict[str, str]:
    """Configurazione -> model_id del config ATTUALE del secondo pilota (per scartare run di modelli sostituiti)."""
    import yaml
    import run_experiment as rx
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return {n: rx.resolve_configuration(cfg, n)["model_metadata"]["model_id"] for n in cfg["configurations"]}


def load_configuration(results: Path, name: str, gt: dict[str, dict], expected_model_id: str | None = None,
                       postprocess_version: str = ppu.PILOT2_VERSION) -> dict:
    """expected_model_id: se indicato, una run con un altro model_id (es. del Qwen 14B sostituito, voce 84) NON si usa:
    resta come traccia e la configurazione risulta non eseguita."""
    run_dir = results / f"{RUN_PREFIX}__{name}"
    info = {"name": name, "run_dir": run_dir, "cfg": None, "calls": [], "expected": None, "excluded": None,
            "metrics": None, "level_mismatch": 0}
    if not (run_dir / "config.json").exists():
        info["excluded"] = f"non eseguita (nessun config.json in {run_dir.name}/)"
        return info
    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))["config"]
    if cfg.get("configuration") != name:
        raise SystemExit(f"{run_dir}: config.json riporta la configurazione {cfg.get('configuration')!r}, non {name}")
    run_model = (cfg.get("model_metadata") or {}).get("model_id")
    if expected_model_id is not None and run_model != expected_model_id:
        info["excluded"] = (f"non eseguita con il modello del config attuale ({expected_model_id}): la run in "
                            f"{run_dir.name}/ e' di {run_model}, traccia NON usata")
        return info
    info["cfg"] = cfg
    info["expected"] = len(cfg["query_ids"]) * cfg.get("repetitions", 1) * len(cfg["conditions"]) * len(cfg["k"])
    mpath = run_dir / "manifest.jsonl"
    manifest = [json.loads(x) for x in mpath.read_text(encoding="utf-8").splitlines() if x] if mpath.exists() else []
    fmt = cfg["prompt"]["output_format"]
    for m in manifest:
        raw = json.loads((run_dir / "raw" / f"{m['call_id']}.json").read_text(encoding="utf-8"))
        v = validate(fmt, raw["text"], raw["finish_reason"], m["call_id"], postprocess_version)
        info["level_mismatch"] += v.level != m.get("level")
        info["calls"].append({"m": m, "raw": raw, "v": v, "gt": gt[m["query_id"]], "q": m["query_id"],
                              "latency_s": m.get("latency_s")})
    if any(m.get("reasoning_field") or m.get("reasoning_markers_in_content") for m in manifest):
        info["excluded"] = "fermata per ragionamento (stop_on_reasoning)"
    elif len(manifest) < info["expected"]:
        info["excluded"] = (f"incompleta ({len(manifest)}/{info['expected']} risposte): non eseguibile, oppure "
                            "interrotta (riprenderla con --resume prima dell'analisi)")
    elif len(manifest) > info["expected"]:
        raise SystemExit(f"{run_dir}: {len(manifest)} risposte nel manifest, attese {info['expected']}")
    info["metrics"] = metrics(name, info["calls"])
    return info


def load_first_pilot(results: Path, gt: dict[str, dict]) -> dict:
    """Riferimento (voce 83): le risposte a temperature 0.3 del primo pilota (Gemma, Apollon JSON libero, stesso prompt
    del secondo pilota), validate con la stessa funzione della strada 2."""
    run_dir = results / FIRST_PILOT_RUN
    info = {"name": FIRST_PILOT_NAME, "run_dir": run_dir, "cfg": None, "calls": [], "expected": None, "excluded": None,
            "metrics": None, "level_mismatch": 0}
    if not (run_dir / "manifest.jsonl").exists():
        info["excluded"] = f"run del primo pilota assente ({run_dir.name}/)"
        return info
    info["cfg"] = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))["config"]
    manifest = [json.loads(x) for x in (run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if x]
    for m in manifest:
        if float(m["temperature"]) != FIRST_PILOT_TEMPERATURE:
            continue
        raw = json.loads((run_dir / "raw" / f"{m['call_id']}.json").read_text(encoding="utf-8"))
        v = validate("apollon", raw["text"], raw["finish_reason"], m["call_id"])
        info["level_mismatch"] += v.level != m.get("level")
        info["calls"].append({"m": m, "raw": raw, "v": v, "gt": gt[m["query_id"]], "q": m["query_id"],
                              "latency_s": m.get("latency_s")})
    info["expected"] = len(info["cfg"]["query_ids"]) * info["cfg"].get("repetitions", 1)
    info["metrics"] = metrics(FIRST_PILOT_NAME, info["calls"])
    return info


# --- report ---------------------------------------------------------------------------------------------------------


def fmt(x, nd=3) -> str:
    if x is None:
        return "—"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def label(name: str) -> str:
    return f"{name} ({PATH_NAME[name[0]]}, {MODEL_NAME[name[-1]]})"


def ratio(m: dict | None) -> str:
    return "—" if not m or not m["n"] else f"{m['S']}/{m['n']} ({m['S'] / m['n']:.2f})"


def references_section(refs: dict[str, dict], infos: dict[str, dict]) -> list[str]:
    """Riferimenti (voce 83): stesse metriche delle configurazioni, fuori dalla classifica, e tabella 2x2 di S per la
    strada JSON (Gemma / Qwen x libero / vincolato)."""
    desc = {FIRST_PILOT_NAME: ("Gemma 4 12B QAT", f"`{FIRST_PILOT_RUN}`, solo temperature {FIRST_PILOT_TEMPERATURE:g}"),
            "J0-Q": (MODEL_NAME["Q"], f"`{RUN_PREFIX}__J0-Q`")}
    L = ["", "## Riferimenti (solo descrittivi, fuori dalla regola e dalla classifica)", "",
         "Configurazioni in Apollon JSON LIBERO (senza response_format), voce 83: completano il confronto 2x2 della "
         "strada JSON, per separare l'effetto del modello da quello del vincolo. Stesse metriche delle configurazioni "
         "(S = risposte valide fino a L3; J, R e latenza come nella classifica). G-libero viene dal primo pilota: altra "
         "run, 3 ripetizioni per esercizio (18 risposte) invece di 2; le proporzioni sono quindi su totali diversi.", "",
         "| riferimento | modello | run | S | L0 | L1 | L2 | L3 | L4 | troncate | J | R | latenza mediana (s) | stato |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, i in refs.items():
        mod, run = desc[n]
        m, cs = i["metrics"], i["calls"]
        if not cs:
            L.append(f"| {n} | {mod} | {run} | — | — | — | — | — | — | — | — | — | — | {i['excluded'] or '—'} |")
            continue
        lv = [sum(c["v"].L0_extracted for c in cs), *(sum(c["v"].level >= x for c in cs) for x in range(1, 5))]
        state = i["excluded"] or (f"completa ({len(cs)}/{i['expected']})" if len(cs) == i["expected"]
                                  else f"{len(cs)} risposte su {i['expected']} attese")
        L.append(f"| {n} | {mod} | {run} | {ratio(m)} | " + " | ".join(map(str, lv)) +
                 f" | {m['truncated']} | {fmt(m['J'])} | {fmt(m['R'])} | {fmt(m['latency_median'], 1)} | {state} |")
    L += ["", "Esiti di fallimento e relazioni (risposte valide fino a L3):", ""]
    for n, i in refs.items():
        if not i["calls"]:
            continue
        cnt = Counter(c["v"].failure or "nessuno (L4)" for c in i["calls"])
        r = i["metrics"]["relations"]
        L.append(f"- {n}: " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items())) +
                 f"; relazioni: stessa coppia {r['same_pair']}/{r['gt_edges']}, stesso tipo {r['same_type']}, stesso "
                 f"verso {r['same_direction']}/{r['directional_same_type']}, stesse molteplicita' "
                 f"{r['same_mult']}/{r['mult_compared']}")

    # stesso prompt? sha256 dei messaggi confrontato con il primo pilota, esercizio per esercizio
    first = {c["q"]: c["m"].get("prompt_sha256") for c in (refs.get(FIRST_PILOT_NAME) or {}).get("calls", [])}
    if first:
        L += ["", "Prompt identico al primo pilota (sha256 dei messaggi, stesso esercizio):", ""]
        others = [(n, infos[n]) for n in ("J-G", "J-Q") if n in infos]
        others += [(n, i) for n, i in refs.items() if n != FIRST_PILOT_NAME]
        if not any(i["calls"] for _, i in others):
            L.append("- nessuna run in JSON del secondo pilota da confrontare")
        for n, i in others:
            cs = [c for c in i["calls"] if c["q"] in first]
            if cs:
                same = sum(c["m"].get("prompt_sha256") == first[c["q"]] for c in cs)
                L.append(f"- {n}: {same}/{len(cs)} risposte" + ("" if same == len(cs) else " — **PROMPT DIVERSI**"))

    cell = {("G", "libero"): refs.get(FIRST_PILOT_NAME), ("Q", "libero"): refs.get("J0-Q"),
            ("G", "vincolato"): infos.get("J-G"), ("Q", "vincolato"): infos.get("J-Q")}
    L += ["", "### Tabella 2x2 della strada JSON: S (risposte valide fino a L3)", "",
          "| modello | JSON libero | JSON vincolato (schema) |", "|---|---|---|"]
    for mk in ("G", "Q"):
        L.append(f"| {MODEL_NAME[mk]} | " + " | ".join(
            ratio((cell[(mk, k)] or {}).get("metrics")) for k in ("libero", "vincolato")) + " |")
    L += ["", "Gemma libero: primo pilota (18 risposte a temperature 0.3); le altre celle: secondo pilota (12 risposte). "
          f"{SIZE_NOTE} Solo descrittivo: nessun test statistico, n piccoli; una cella vuota (—) e' una run assente. Le celle "
          "riportano S anche per le run escluse dalla regola (stato nella tabella sopra o nella classifica)."]
    return L


def changes_section(infos: dict[str, dict]) -> list[str]:
    """Analisi v2: risposte della strada 1 il cui livello o le cui righe scartate cambiano rispetto al manifest
    (post-processing pilot2_v1), con le riscritture e i diagnostici della v2."""
    L = ["", "## Risposte cambiate rispetto all'analisi originale (post-processing v2)", "",
         "Livello del manifest (post-processing pilot2_v1, analisi originale) contro livello con la v2. Riscritture: "
         "intestazioni `extends` / `implements` trasformate in relazioni; `enduml_mancante`: blocco letto fino alla "
         "fine del testo (finish_reason diverso da length).", "",
         "| chiamata | livello originale | livello v2 | righe scartate v2 | riscritture | enduml_mancante |",
         "|---|---|---|---|---|---|"]
    rows = 0
    for n, i in infos.items():
        for c in i["calls"]:
            v = c["v"]
            rw = {k: x for k, x in (getattr(v, "syntax_rewrites", None) or {}).items() if x}
            miss = "enduml_mancante" in v.format_issues
            if v.level != c["m"].get("level") or rw or miss:
                rows += 1
                L.append(f"| {n} {c['m']['call_id']} | {c['m'].get('level')} | {v.level} | "
                         f"{len(getattr(v, 'discarded_lines', []))} | "
                         f"{', '.join(f'{k} {x}' for k, x in sorted(rw.items())) or '—'} | {'si' if miss else '—'} |")
    if not rows:
        L.append("| nessuna | — | — | — | — | — |")
    return L


def report(infos: dict[str, dict], refs: dict[str, dict] | None = None,
           postprocess_version: str = ppu.PILOT2_VERSION) -> tuple[str, dict]:
    v2 = postprocess_version != ppu.PILOT2_VERSION
    dec = decide({n: {"excluded": i["excluded"], "metrics": i["metrics"]} for n, i in infos.items()})
    cfgs = [i["cfg"] for i in infos.values() if i["cfg"]]
    ref = cfgs[0] if cfgs else None
    L = (["# Secondo pilota — ANALISI v2 (SOLO DESCRITTIVA, post-processing PlantUML v2)", "",
          "**Analisi descrittiva** (voce 89): le STESSE risposte salvate, rilette con il post-processing PlantUML v2 "
          "(intestazioni `extends` / `implements`, blocco senza `@enduml`). La regola della voce 78 e' riapplicata solo "
          "per mostrare l'effetto delle correzioni: **l'esito valido del secondo pilota resta quello dell'analisi "
          "originale** (`pilot2_formats_analysis/summary.md`, voce 88). La strada 2 (JSON) non cambia.", ""]
         if v2 else [])
    L += ["# Secondo pilota — PlantUML contro JSON vincolato (`pilot2_formats`)" if not v2 else
          "Post-processing: v2 (strada 1); strada 2 invariata.", "",
         "**Esperimento PRELIMINARE** sul corpus (split `corpus`, selezione leave-one-out), mai sul test set: da "
         "dichiarare come tale in tesi. Regola di decisione registrata PRIMA delle run (docs/decisions.md, voce 78, "
         "approvata nella voce 79) e applicata cosi' com'e' da `experiments/analyze_pilot2.py` (voce 82), ricalcolando "
         "tutto dalle risposte grezze (`raw/`).", "",
         f"Analisi eseguita sul commit `{git('rev-parse', 'HEAD')[:12] or '?'}`"
         f"{' (con modifiche non committate)' if git('status', '--porcelain') else ''}."]
    if ref:
        g = ref["generation"]
        L += ["", f"Esercizi: {', '.join(ref['query_ids'])}; bm25 k={ref['k'][0]}; {ref['repetitions']} ripetizioni; "
              f"temperature {g['temperature']}, top_p {g['top_p']}, top_k {g['top_k']}, max_tokens {g['max_tokens']}."]
        keys = ("query_ids", "k", "conditions", "repetitions", "split")
        diff = [f"{i['name']}: {k}" for i in infos.values() if i["cfg"] for k in keys if i["cfg"].get(k) != ref.get(k)]
        diff += [f"{i['name']}: generation.{k}" for i in infos.values() if i["cfg"]
                 for k in ("temperature", "top_p", "top_k", "max_tokens", "seed")
                 if i["cfg"]["generation"].get(k) != g.get(k)]
        if diff:
            L.append(f"**ATTENZIONE, run non omogenee**: {'; '.join(diff)}.")
    L += ["", SIZE_NOTE]
    mism = {n: i["level_mismatch"] for n, i in infos.items() if i["level_mismatch"]}
    if mism and not v2:
        L.append(f"**ATTENZIONE**: livello ricalcolato diverso da quello del manifest in {mism} risposte (codice di "
                 "validazione cambiato dopo la run?).")

    # regola
    L += ["", "## Regola di decisione (voce 78), applicata cosi' com'e'" if not v2 else
          "## Regola della voce 78 riapplicata (SOLO DESCRITTIVA: l'esito valido e' quello dell'analisi originale)", "",
          f"**Esito: {dec['outcome']}**" if not v2 else f"Esito che la regola darebbe con la v2: {dec['outcome']}"]
    L += [f"- {r}" for r in dec["reasons"]]
    for n, why in dec["excluded"].items():
        L.append(f"- esclusa {n}: {why}")
    if dec["winner"]:
        L += ["", "Passi della scelta:", ""]
        for s in dec["steps"]:
            vals = ", ".join(f"{n} {fmt(v)}" for n, v in s["values"].items())
            L.append(f"- {s['criterion']}: {vals} → restano {', '.join(s['kept'])}")
        L.append(f"\nVincitrice: **{label(dec['winner'])}**.")

    L += ["", "### Classifica completa delle configurazioni", "",
          "Posizione k = vincitrice della stessa regola (pareggio entro 1 risposta dal massimo di S, poi gli spareggi "
          "nell'ordine) applicata alle configurazioni non ancora classificate; la soglia minima vale solo per la "
          "scelta. J = Jaccard medio dei nomi di classe (risposte valide fino a L3); R = relazioni del GT con stessa "
          "coppia e stesso tipo / relazioni del GT (risposte valide); latenza mediana su tutte le risposte. P1 (fuori "
          "dalla regola, voce 89) = risposte della strada 1 valide fino a L3 e senza righe scartate.", "",
          "| posizione | configurazione | S (su 12) | P1 senza righe scartate | troncate | J | R | latenza mediana (s) | "
          "decisa da | nota |", "|---|---|---|---|---|---|---|---|---|---|"]
    def p1(name: str) -> str:
        if not name.startswith("P") or not infos[name]["calls"]:
            return "—"
        cs = infos[name]["calls"]
        return f"{sum(c['v'].level >= 3 and c['v'].P1_clean for c in cs)}/{len(cs)}"

    for k, r in enumerate(dec["ranking"], 1):
        m = infos[r["name"]]["metrics"]
        if r.get("excluded"):
            cells = ([f"{m['S']}/{m['n']}", p1(r["name"]), str(m["truncated"]), fmt(m["J"]), fmt(m["R"]),
                      fmt(m["latency_median"], 1)] if m else ["—"] * 6)
            L.append(f"| — | {label(r['name'])} | " + " | ".join(cells) + f" | — | ESCLUSA: {r['excluded']} |")
            continue
        note = "scelta" if r["name"] == dec["winner"] else ""
        L.append(f"| {k} | {label(r['name'])} | {m['S']}/{m['n']} | {p1(r['name'])} | {m['truncated']} | "
                 f"{fmt(m['J'])} | {fmt(m['R'])} | "
                 f"{fmt(m['latency_median'], 1)} | {r['decided_by']} | {note} |")
    L += ["", "Riferimenti in JSON libero (Gemma del primo pilota, J0-Q): sezione \"Riferimenti\", fuori dalla "
          "classifica."]

    # secondarie
    L += ["", "## Metriche secondarie (riportate, fuori dalla regola)", "", "### Validita' per livello", "",
          "Risposte che superano ciascun livello (cumulativo). Strada 1: P0 = blocco @startuml/@enduml, P1b = parsing "
          "tollerante e conversione riusciti (corrisponde a L1), P1 = come P1b senza righe scartate; poi gli stessi "
          "L2-L4 della strada 2.", "",
          "| configurazione | P0 / L0 | P1b / L1 | P1 (solo strada 1) | L2 schema | L3 integrita' | L4 stile | troncate | "
          "righe scartate (totale) |", "|---|---|---|---|---|---|---|---|---|"]
    for n, i in infos.items():
        cs = i["calls"]
        if not cs:
            L.append(f"| {n} | — | — | — | — | — | — | — | — |")
            continue
        # P0 / L0 dal flag (nella strada 1 il livello resta -1 finche' il parsing non riesce)
        lv = [sum(c["v"].L0_extracted for c in cs), *(sum(c["v"].level >= x for c in cs) for x in range(1, 5))]
        p1 = sum(getattr(c["v"], "P1_clean", False) for c in cs) if n.startswith("P") else "—"
        disc = sum(len(getattr(c["v"], "discarded_lines", [])) for c in cs) if n.startswith("P") else "—"
        L.append(f"| {n} | {lv[0]} | {lv[1]} | {p1} | {lv[2]} | {lv[3]} | {lv[4]} | "
                 f"{sum(bool(c['v'].truncated) for c in cs)} | {disc} |")
    L += ["", "Esiti di fallimento (`failure`):", ""]
    for n, i in infos.items():
        if i["calls"]:
            cnt = Counter(c["v"].failure or "nessuno (L4)" for c in i["calls"])
            L.append(f"- {n}: " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items())))
    queries = ref["query_ids"] if ref else []
    L += ["", "Per esercizio (livello raggiunto da ciascuna ripetizione; −1 = niente estratto):", "",
          "| esercizio | " + " | ".join(infos) + " |", "|---|" + "---|" * len(infos)]
    for q in queries:
        cells = []
        for i in infos.values():
            cs = sorted((c for c in i["calls"] if c["q"] == q), key=lambda c: c["m"]["repetition"])
            cells.append(" / ".join(f"{c['v'].level}{' (length)' if c['v'].truncated else ''}" for c in cs) or "—")
        L.append(f"| {q} | " + " | ".join(cells) + " |")

    L += ["", "### Relazioni rispetto al ground truth (risposte valide fino a L3)", "",
          "Accoppiamento 1:1 per coppia di classi non ordinata (come nel primo pilota, `analyze_pilot.compare_relations`). "
          "Verso solo per relazioni dello stesso tipo orientato; molteplicita' per estremo, esclusi generalizzazione e "
          "realizzazione, con 'n' -> '*' e '0..*' = '*'.", "",
          "| configurazione | risposte valide | relazioni risposta | relazioni GT | stessa coppia | stesso tipo | stesso "
          "verso (tipi orientati) | comp./aggr.: stesso verso | stesse molteplicita' |",
          "|---|---|---|---|---|---|---|---|---|"]
    for n, i in infos.items():
        m = i["metrics"]
        if not m:
            L.append(f"| {n} | — | — | — | — | — | — | — | — |")
            continue
        t = m["relations"]
        L.append(f"| {n} | {m['S']} | {t['resp_edges']} | {t['gt_edges']} | {t['same_pair']} | {t['same_type']} | "
                 f"{t['same_direction']}/{t['directional_same_type']} | "
                 f"{t['part_whole_same_direction']}/{t['part_whole_same_type']} | {t['same_mult']}/{t['mult_compared']} |")
    for n, i in infos.items():
        swaps = {k: v for k, v in (i["metrics"] or {}).get("relations", Counter()).items() if k.startswith("type ")}
        if swaps:
            L.append(f"\nTipo diverso con la stessa coppia, {n} (GT -> risposta): " +
                     ", ".join(f"{k[5:]} {v}" for k, v in sorted(swaps.items(), key=lambda x: (-x[1], x[0]))))

    L += ["", "### Tempi e token", "",
          "| configurazione | latenza s (min / mediana / max) | token di completamento (min / mediana / max) | prompt "
          "reale (min / mediana / max) | token reali / stima cl100k_base (min / mediana / max) | durata totale (min) |",
          "|---|---|---|---|---|---|"]
    for n, i in infos.items():
        cs = i["calls"]
        if not cs:
            L.append(f"| {n} | — | — | — | — | — |")
            continue
        lat = ap.stats3([c["m"]["latency_s"] for c in cs])
        tok = ap.stats3([c["m"]["completion_tokens_server"] for c in cs if c["m"].get("completion_tokens_server")])
        pr = ap.stats3([c["m"]["prompt_tokens_server"] for c in cs if c["m"].get("prompt_tokens_server")])
        ra = ap.stats3([c["m"]["prompt_tokens_server"] / c["m"]["prompt_tokens_est"] for c in cs
                        if c["m"].get("prompt_tokens_server") and c["m"].get("prompt_tokens_est")])

        def tri(t, nd=0):
            return " / ".join(fmt(float(x) if x is not None else None, nd) for x in t)

        L.append(f"| {n} | {tri(lat, 1)} | {tri(tok)} | {tri(pr)} | {tri(ra, 3)} | "
                 f"{sum(c['m']['latency_s'] for c in cs) / 60:.1f} |")

    L += ["", "### Diagnostici (non metriche; non si combinano con i livelli)", "",
          "Risposte con almeno un diagnostico, tra quelle che superano L1. Strada 1: i diagnostici sul JSON (es. "
          "`interactive_present`, layout) riguardano l'Apollon prodotto dal convertitore, non la risposta del modello; "
          "solo `extra_text` (testo attorno al blocco PlantUML) riguarda la risposta.", "",
          "| configurazione | formato della risposta | layout |", "|---|---|---|"]
    for n, i in infos.items():
        l1 = [c for c in i["calls"] if c["v"].L1_json]
        # strada 1: "interactive" lo aggiunge il convertitore, non il modello (voce 89) -> n/a, non contato
        f = Counter(k for c in l1 for k in c["v"].format_issues
                    if not (n.startswith("P") and k == "interactive_present"))
        la = Counter(k for c in l1 for k in c["v"].layout_issues)
        cells = [f"{k} {x}" for k, x in sorted(f.items())]
        if n.startswith("P") and l1:
            cells.append("interactive_present n/a (aggiunto dal convertitore)")
        L.append(f"| {n} | " + (", ".join(cells) or "nessuno") + " | " +
                 (", ".join(f"{k} {x}" for k, x in sorted(la.items())) or "nessuno") + " |")
    if v2:
        L += changes_section(infos)
    if refs is not None:
        L += references_section(refs, infos)
    return "\n".join(L) + "\n", dec


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--results-dir", default=str(RESULTS))
    a.add_argument("--postprocess", default=ppu.PILOT2_VERSION, choices=ppu.VERSIONS,
                   help="pilot2_v1 = analisi originale (default); v2 = analisi descrittiva con le correzioni (voce 89)")
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    ver = args.postprocess
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    models = expected_model_ids()
    infos = {n: load_configuration(results, n, gt, models[n], ver) for n in CONFIGURATIONS}
    refs = {FIRST_PILOT_NAME: load_first_pilot(results, gt),
            **{n: load_configuration(results, n, gt, models[n], ver) for n in REFERENCE_CONFIGURATIONS}}
    text, _ = report(infos, refs, ver)
    out = results / (OUT_NAME if ver == ppu.PILOT2_VERSION else f"{OUT_NAME}_v2")
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(text, encoding="utf-8")
    _set_output(out / "summary.md")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    print(f"scritto in {out / 'summary.md'}")
    return 0


def _set_output(path) -> None:
    """Registro delle esecuzioni (voce 102): dichiara l'uscita, se lo script e' lanciato da riga di comando."""
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(path)


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102): due righe in data/results/run_log.jsonl
    with run_log.logged(__file__):
        sys.exit(main())
