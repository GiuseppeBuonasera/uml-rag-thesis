"""
Controllo di funzionamento dei retriever sull'insieme di sviluppo e run oracolo (docs/decisions.md, voce 109). Scritto e
testato PRIMA delle run (anche sulla sola baseline): da qui la regola di esclusione e l'interpretazione dell'oracolo
(MAX_VC_LOSS, MAX_TRUNCATED, MAX_OVER_BUDGET, ORACLE_MARGIN, exclusion, oracle_reading) non si modificano senza una
nuova voce.

Nessuna chiamata a un LLM. Per formato (P-G = PlantUML, C-G = compatto), confronta la BASELINE (Gemma 4 12B QAT, bm25
k = 3 di data/results/generation/dev_k__P-G e __C-G) con le condizioni di data/results/generation/dev_retrievers__P-G e
__C-G: dense (all-MiniLM-L6-v2), hybrid (RRF BM25 + MiniLM) e oracle_jt (solo diagnostica). Validazione e metriche come
experiments/analyze_instructions.py (V, Vc, J, R su TUTTE le risposte, 0 per le non valide; M primaria; verso), ground
truth ATTUALE del corpus. Scrive solo data/results/generation/dev_retrievers_analysis/summary.md.

Il tipo di retriever e' un FATTORE sperimentale: qui NON si sceglie un vincitore.

REGOLA DI ESCLUSIONE (voce 109, con le modifiche approvate), per dense e hybrid, per formato: escluso dal Passo 3b in
quel formato se, rispetto a BM25 k = 3:
  - Vc peggiora di piu' di 4 su 40 (Vc(retriever) - Vc(BM25) < -4), oppure
  - i troncamenti per max_tokens (finish_reason = length) sono 2 o piu' (con 1 solo: non escluso, la risposta si riporta
    e si allega nel report), oppure
  - anche un solo prompt oltre il budget di contesto (token di prompt del server + max_tokens > contesto).
  Nessun criterio su R, J o M. Controllo preliminare: baseline e condizione complete (40 risposte), senza ragionamento,
  del modello del config; altrimenti quel formato non si decide.
ORACOLO (oracle_jt, solo diagnostica, MAI nel 3b): dR = R(oracolo) - R(BM25) per formato;
  dR < 0,03 in entrambi i formati -> "la qualita' del retrieval non e' il collo di bottiglia con questo corpus e questo
  modello"; dR >= 0,03 in almeno un formato -> "un retrieval migliore avrebbe margine" (si riporta il valore, nessuna
  scelta per il 3b).

Uso:
    python experiments/analyze_retrievers.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import analyze_dev as ad  # noqa: E402
import analyze_instructions as ai  # noqa: E402  (caricamento, metriche M e verso: riuso, nessuna modifica)
import run_experiment as rx  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402  (riga di provenienza, voce 106)

RESULTS = ROOT / "data" / "results" / "generation"
CONFIG = ROOT / "experiments" / "configs" / "dev_retrievers.yaml"
BASELINE_PREFIX, TREATMENT_PREFIX, K = "dev_k", "dev_retrievers", 3
OUT_NAME = "dev_retrievers_analysis"
CONFIGURATIONS = {"P-G": "plantuml", "C-G": "compact"}
FORMAT_NAME = ad.FORMAT_NAME
RETRIEVERS = ("dense", "hybrid")  # soggetti alla regola di esclusione
ORACLE = "oracle_jt"
LABEL = {"bm25": "BM25 (baseline dev_k)", "dense": "MiniLM (dense)", "hybrid": "ibrido RRF (hybrid)",
         "oracle_jt": "oracolo Jt (solo diagnostica)"}
# --- regola (voce 109): non si modifica senza una nuova voce in docs/decisions.md ---
MAX_VC_LOSS = 4  # escluso se dVc < -4 (su 40)
MAX_TRUNCATED = 1  # escluso se troncamenti >= 2
MAX_OVER_BUDGET = 0  # escluso con anche un solo prompt oltre il budget
ORACLE_MARGIN = 0.03
EPS = 1e-9


# --- caricamento ----------------------------------------------------------------------------------------------------


def load_condition(results: Path, prefix: str, name: str, gt: dict, model_id: str, condition: str, expected: int) -> dict:
    """Le risposte di UNA condizione a k = 3 di una run, con il controllo preliminare per condizione."""
    info = ai.load_run(results, prefix, name, gt, model_id, K)
    info["name"] = f"{prefix}__{name} [{condition}]"
    info["calls"] = [c for c in info["calls"] if c["m"]["condition"] == condition]
    if info["excluded"] and not info["excluded"].startswith("incompleta"):
        return info
    info["excluded"] = None
    if any(c["m"].get("reasoning_field") or c["m"].get("reasoning_markers_in_content") for c in info["calls"]):
        info["excluded"] = "fermata per ragionamento (stop_on_reasoning)"
    elif len(info["calls"]) < expected:
        info["excluded"] = f"incompleta ({len(info['calls'])}/{expected} risposte): riprenderla con --resume"
    return info


def over_budget(calls: list[dict], context: int, max_tokens: int) -> list[str]:
    """Chiamate con prompt oltre il budget: token di prompt del server (o stimati, se mancano) + max_tokens > contesto."""
    out = []
    for c in calls:
        p = c["m"].get("prompt_tokens_server") or c["m"].get("prompt_tokens_est") or 0
        if p + max_tokens > context:
            out.append(c["m"]["call_id"])
    return out


# --- regola ---------------------------------------------------------------------------------------------------------


def exclusion(base: dict, treat: dict, truncated: int, n_over_budget: int) -> dict:
    """Regola di esclusione della voce 109 per un retriever e un formato."""
    dvc = treat["Vc"] - base["Vc"]
    reasons = []
    if dvc < -MAX_VC_LOSS:
        reasons.append(f"Vc peggiora di {-dvc} su 40 (> {MAX_VC_LOSS})")
    if truncated > MAX_TRUNCATED:
        reasons.append(f"{truncated} troncamenti per max_tokens (>= {MAX_TRUNCATED + 1})")
    if n_over_budget > MAX_OVER_BUDGET:
        reasons.append(f"{n_over_budget} prompt oltre il budget di contesto")
    return {"excluded": bool(reasons), "reasons": reasons, "dVc": dvc, "truncated": truncated,
            "over_budget": n_over_budget, "report_truncated": truncated == 1}


def oracle_reading(d_r: dict[str, float]) -> str:
    """d_r: formato -> R(oracolo) - R(BM25). Interpretazione fissata prima delle run (voce 109)."""
    if all(v < ORACLE_MARGIN - EPS for v in d_r.values()):
        return ("la qualità del retrieval non è il collo di bottiglia con questo corpus e questo modello "
                f"(R(oracolo) − R(BM25) < {ORACLE_MARGIN} in entrambi i formati)")
    return ("un retrieval migliore avrebbe margine (R(oracolo) − R(BM25) >= "
            f"{ORACLE_MARGIN} in almeno un formato); nessuna scelta per il 3b")


# --- report ---------------------------------------------------------------------------------------------------------


def common_examples(base: dict, treat: dict) -> dict[str, int]:
    """Esempi recuperati in comune con BM25 per esercizio (dai manifest; uguali tra le ripetizioni)."""
    b = {c["q"]: set(c["m"]["example_ids"]) for c in base["calls"]}
    return {c["q"]: len(b[c["q"]] & set(c["m"]["example_ids"])) for c in treat["calls"] if c["q"] in b}


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def report(data: dict, context: int, max_tokens: int) -> tuple[str, dict]:
    """data: formato -> {condizione: info}, con 'bm25' = baseline."""
    res = {"formats": {}, "oracle": None, "oracle_dR": {}}
    L = ["# Insieme di sviluppo — controllo di funzionamento dei retriever e run oracolo (`dev_retrievers` contro "
         "`dev_k`, k = 3)", "",
         "Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set. Gemma 4 12B QAT, versione di "
         "configurazione 2, k = 3, prompt senza blocco di istruzioni mirate. Il tipo di retriever è un FATTORE "
         "sperimentale del Passo 3b: qui NON si sceglie un vincitore, si applica solo la regola di esclusione "
         "registrata PRIMA delle run (voce 109) da `experiments/analyze_retrievers.py`. Ground truth attuale del corpus; "
         "confronto per contenuto, mai per id.", "",
         provenance.provenance_line()]
    mism = {x["name"]: x["level_mismatch"] for d in data.values() for x in d.values() if x["level_mismatch"]}
    if mism:
        L.append(f"**ATTENZIONE**: livello ricalcolato diverso dal manifest in {mism} risposte.")
    L += ["", "## Regola di esclusione (voce 109), applicata così com'è", "",
          f"Escluso dal 3b in quel formato se Vc peggiora di più di {MAX_VC_LOSS} su 40, oppure se i troncamenti per "
          f"max_tokens sono 2 o più (1 solo: riportato e allegato), oppure con anche un solo prompt oltre il budget di "
          f"contesto (prompt + max_tokens {max_tokens} > {context}). Nessun criterio su R, J o M.", ""]
    metrics = {f: {c: ai.metrics(x["calls"]) if x["calls"] else None for c, x in d.items()} for f, d in data.items()}
    attach = []
    for f, d in data.items():
        res["formats"][f] = {}
        for c in RETRIEVERS:
            pre = {x["name"]: x["excluded"] for x in (d["bm25"], d[c]) if x["excluded"]}
            if pre:
                res["formats"][f][c] = {"excluded": None, "pre": pre}
                L.append(f"- **{FORMAT_NAME[f]}, {LABEL[c]}: non decidibile** (controllo preliminare): "
                         + "; ".join(f"{n}: {w}" for n, w in pre.items()))
                continue
            mb, mt = metrics[f]["bm25"], metrics[f][c]
            e = exclusion(mb, mt, mt["truncated"], len(over_budget(d[c]["calls"], context, max_tokens)))
            res["formats"][f][c] = e
            verdict = ("**ESCLUSO** dal 3b: " + "; ".join(e["reasons"])) if e["excluded"] else "**ammesso** al 3b"
            L.append(f"- {FORMAT_NAME[f]}, {LABEL[c]}: {verdict} (dVc {e['dVc']:+d}, troncamenti {e['truncated']}, "
                     f"prompt oltre il budget {e['over_budget']})")
            if e["report_truncated"]:
                attach += [x for x in d[c]["calls"] if x["v"].truncated]
    # oracolo
    dr = {f: metrics[f][ORACLE]["R"] - metrics[f]["bm25"]["R"] for f, d in data.items()
          if metrics[f][ORACLE] is not None and not d[ORACLE]["excluded"] and not d["bm25"]["excluded"]}
    res["oracle_dR"] = dr
    L += ["", "## Run oracolo (solo diagnostica, MAI nel 3b)", ""]
    if len(dr) == len(data):
        res["oracle"] = oracle_reading(dr)
        L += [f"- R(oracolo) − R(BM25): " + ", ".join(f"{FORMAT_NAME[f]} {v:+.3f}" for f, v in dr.items()) + ".",
              f"- **Interpretazione (fissata prima): {res['oracle']}.**"]
    else:
        L.append("- non interpretabile: run oracolo incompleta o assente in almeno un formato ("
                 + "; ".join(f"{x['name']}: {x['excluded']}" for d in data.values() for x in (d[ORACLE], d["bm25"])
                             if x["excluded"]) + ")")

    L += ["", "## Metriche per formato e retriever", "",
          "J, R, M su tutte le risposte (0 per le non valide); M primaria: estremi del GT con molteplicità esplicita; "
          "verso: relazioni dello stesso tipo orientato con lo stesso verso.", "",
          "| formato | retriever | V | Vc | J | R | M primaria | verso uguale | troncate | prompt med (server) | "
          "completamento med | latenza med (s) |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f, d in data.items():
        for c, x in d.items():
            m = metrics[f][c]
            if m is None:
                L.append(f"| {FORMAT_NAME[f]} | {LABEL[c]} | — | — | — | — | — | — | — | — | — | — |")
                continue
            med = lambda key: statistics.median([y["m"][key] for y in x["calls"] if y["m"].get(key)] or [0])  # noqa
            mc = m["mult_counts"]
            L.append(f"| {FORMAT_NAME[f]} | {LABEL[c]} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {fmt(m['J'])} | "
                     f"{fmt(m['R'])} | {fmt(m['M1'])} ({mc['explicit_same']}/{mc['explicit']}) | {m['dir']} | "
                     f"{m['truncated']} | {med('prompt_tokens_server'):.0f} | {med('completion_tokens_server'):.0f} | "
                     f"{med('latency_s'):.1f} |")

    L += ["", "## Esempi recuperati in comune con BM25 (per esercizio, su 3)", ""]
    for f, d in data.items():
        conds = [c for c in (*RETRIEVERS, ORACLE) if d[c]["calls"] and d["bm25"]["calls"]]
        if not conds:
            L.append(f"- {FORMAT_NAME[f]}: nessuna condizione eseguita.")
            continue
        com = {c: common_examples(d["bm25"], d[c]) for c in conds}
        L += [f"### {FORMAT_NAME[f]}", "", "| esercizio | " + " | ".join(LABEL[c] for c in conds) + " |",
              "|---|" + "---|" * len(conds)]
        for q in sorted({q for v in com.values() for q in v}, key=str.lower):
            L.append(f"| {q} | " + " | ".join(str(com[c].get(q, "—")) for c in conds) + " |")
        L.append("| **totale** | " + " | ".join(f"{sum(com[c].values())}/{3 * len(com[c])}" for c in conds) + " |")
        L.append("")

    if attach:
        L += ["## Allegato: risposte troncate (1 sola per retriever e formato: riportata, non esclude)", ""]
        for x in attach:
            L += [f"### `{x['m']['call_id']}` ({FORMAT_NAME[x['format']]}, {x['m'].get('completion_tokens_server')} "
                  "token di completamento)", "", "```", x["raw"]["text"], "```", ""]
    return "\n".join(L) + "\n", res


def load_all(results: Path) -> tuple[dict, int, int]:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    data, ctx = {}, set()
    for name, f in CONFIGURATIONS.items():
        r = rx.resolve_configuration(cfg, name)
        model_id, expected = r["model_metadata"]["model_id"], len(r["query_ids"]) * r.get("repetitions", 1)
        ctx.add(r["model_metadata"]["context_length"])
        data[f] = {"bm25": load_condition(results, BASELINE_PREFIX, name, gt, model_id, "bm25", expected)}
        for c in (*RETRIEVERS, ORACLE):
            data[f][c] = load_condition(results, TREATMENT_PREFIX, name, gt, model_id, c, expected)
    assert len(ctx) == 1
    return data, ctx.pop(), cfg["generation"]["max_tokens"]


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    data, context, max_tokens = load_all(results)
    text, _ = report(data, context, max_tokens)
    out = results / OUT_NAME
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(text, encoding="utf-8")
    _set_output(out / "summary.md")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    print(f"scritto in {out / 'summary.md'}")
    return 0


def _set_output(path) -> None:
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(path)


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
