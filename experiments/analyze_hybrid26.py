"""
Passo 2 rifatto con il retriever hybrid (docs/decisions.md, voce 140). Scritto e testato PRIMA della run (sulla sola
baseline): da qui la regola (costanti, keeps, outcome) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Per formato, confronto APPAIATO sui 20 esercizi di sviluppo × 2 ripetizioni, Gemma 4 26B
A4B QAT con la configurazione di lavoro del 3b (vista clean_v1): TRATTAMENTO dev_g26hy (hybrid k = 3) contro BASELINE
bm25 k = 3 con la stessa configurazione, ricostruita da run esistenti con prompt identici (dev_g26ev per le 8 query
toccate dalla pulizia, dev_g26 per le altre 12).

REGOLA (voce 140, non inferiorita'): hybrid resta nel 3b se, in ENTRAMBI i formati, dF1_relazioni >= -0,03 (F1 macro
delle relazioni strutturali, abbinamento rilassato) E dR >= -0,03 E dVc >= -2 E meno di 2 troncamenti; altrimenti
decide l'utente. Riportati: F1 classi e generalizzazioni, J, M primaria, quota di esempi De Bari, token, latenza,
dettaglio per esercizio.

Uso:
    python experiments/analyze_hybrid26.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "generation"), str(ROOT / "experiments"), str(ROOT)]
import analyze_dev as ad  # noqa: E402
import analyze_instructions as ai  # noqa: E402
from evaluation import element_metrics as el  # noqa: E402
from evaluation import metrics as em  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
MODEL_26 = "google/gemma-4-26b-a4b-qat"
K = 3
TREATMENT = "dev_g26hy"
BASE_RAW, BASE_CLEAN = "dev_g26", "dev_g26ev"  # bm25: le query di dev_g26ev da li', le altre da dev_g26
FORMATS = {"plantuml": "P-G", "compact": "C-G"}
OUT_NAME = "dev_g26hy_analysis"
# --- regola (voce 140): non si modifica senza una nuova voce in docs/decisions.md ---
MAX_F1_LOSS = 0.03
MAX_R_LOSS = 0.03
MAX_VC_LOSS = 2
MAX_TRUNCATED = 1
EPS = 1e-9


def scores(calls: list[dict]) -> dict:
    m = em.multiplicity_metrics(calls)
    agg = el.aggregate(calls)["relaxed"]
    slots = [e for c in calls for e in c["m"]["example_ids"]]
    return {"R": m["R"], "J": m["J"], "M1": m["M1"], "V": m["V"], "Vc": m["Vc"], "truncated": m["truncated"],
            "F1rel": agg["relations"]["macro"]["F1"], "F1cls": agg["classes"]["macro"]["F1"],
            "F1gen": agg["generalizations"]["macro"]["F1"], "latency": m["latency_median"],
            "debari": sum(e.startswith("DB") for e in slots) / len(slots) if slots else None,
            "tokens": statistics.median(c["m"].get("completion_tokens_server") or 0 for c in calls) if calls else None}


def keeps(base: dict, treat: dict) -> dict:
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    d = {"dF1rel": z(treat["F1rel"]) - z(base["F1rel"]), "dR": z(treat["R"]) - z(base["R"]),
         "dVc": treat["Vc"] - base["Vc"], "truncated": treat["truncated"]}
    d["ok"] = (d["dF1rel"] >= -MAX_F1_LOSS - EPS and d["dR"] >= -MAX_R_LOSS - EPS and d["dVc"] >= -MAX_VC_LOSS
               and d["truncated"] <= MAX_TRUNCATED)
    return d


def outcome(formats: dict[str, dict | None]) -> str:
    if any(v is None for v in formats.values()):
        return "STOP: controllo preliminare non superato (run assente, incompleta o con ragionamento)"
    if all(v["ok"] for v in formats.values()):
        return "hybrid RESTA nel 3b (non inferiore a bm25 in entrambi i formati)"
    failed = [ad.FORMAT_NAME[f] for f, v in formats.items() if not v["ok"]]
    return f"hybrid inferiore a bm25 in {', '.join(failed)}: DECIDE L'UTENTE se toglierlo dal 3b"


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    clean_ids = set(yaml.safe_load((ROOT / "experiments" / "configs" / "dev_g26ev.yaml").read_text(encoding="utf-8"))
                    ["query_ids"])
    out = {}
    for f, name in FORMATS.items():
        treat = ai.load_run(results, TREATMENT, name, gt, MODEL_26, K)
        raw = ai.load_run(results, BASE_RAW, name, gt, MODEL_26, K)
        clean = ai.load_run(results, BASE_CLEAN, name, gt, MODEL_26, K)
        base = {"name": f"bm25 ({BASE_RAW} + {BASE_CLEAN})", "excluded": raw["excluded"] or clean["excluded"],
                "calls": [c for c in raw["calls"] if c["q"] not in clean_ids] + clean["calls"]}
        out[f] = {"base": base, "treat": treat}
    return out


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def report(data: dict) -> tuple[str, dict]:
    res = {"formats": {}, "outcome": None}
    L = ["# Passo 2 rifatto con il retriever hybrid — `dev_g26hy` contro bm25 (stessa configurazione)", "",
         "SVILUPPO: 20 esercizi × 2 ripetizioni, Gemma 4 26B A4B QAT, configurazione di lavoro del 3b (PlantUML v5, "
         "compatto v5 + esempi indentati, vista clean_v1, file congelato). Baseline bm25 k = 3 ricostruita da dev_g26 e "
         "dev_g26ev (prompt identici). Regola registrata PRIMA della run (voce 140), applicata da "
         "`experiments/analyze_hybrid26.py`.", "", provenance.provenance_line(), "", "## Regola (voce 140)", "",
         f"Hybrid resta nel 3b se, in entrambi i formati, dF1_relazioni ≥ −{MAX_F1_LOSS}, dR ≥ −{MAX_R_LOSS}, dVc ≥ "
         f"−{MAX_VC_LOSS}, meno di 2 troncamenti.", ""]
    rows = []
    for f, d in data.items():
        pre = [x["excluded"] for x in d.values() if x["excluded"]]
        if pre or len(d["treat"]["calls"]) != len(d["base"]["calls"]) or not d["treat"]["calls"]:
            res["formats"][f] = None
            L.append(f"- **{ad.FORMAT_NAME[f]}: non decidibile** ({'; '.join(pre or ['risposte mancanti'])})")
            continue
        sb, st = scores(d["base"]["calls"]), scores(d["treat"]["calls"])
        k = keeps(sb, st)
        res["formats"][f] = k
        L.append(f"- **{ad.FORMAT_NAME[f]}: {'non inferiore' if k['ok'] else 'INFERIORE'}** (dF1_relazioni "
                 f"{k['dF1rel']:+.3f}, dR {k['dR']:+.3f}, dVc {k['dVc']:+d}, troncate {k['truncated']})")
        rows.append((f, sb, st, d))
    res["outcome"] = outcome(res["formats"])
    L += ["", f"**Esito: {res['outcome']}**", "", "## Metriche (40 risposte per cella)", "",
          "| formato | retriever | V | Vc | J | R | M primaria | F1 classi | F1 relazioni | F1 generalizz. | esempi De "
          "Bari | troncate | token (med) | latenza (med, s) |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f, sb, st, _ in rows:
        for label, s in (("bm25", sb), ("hybrid", st)):
            L.append(f"| {ad.FORMAT_NAME[f]} | {label} | {s['V']} | {s['Vc']} | {fmt(s['J'])} | {fmt(s['R'])} | "
                     f"{fmt(s['M1'])} | {fmt(s['F1cls'])} | {fmt(s['F1rel'])} | {fmt(s['F1gen'])} | "
                     f"{100 * s['debari']:.0f} % | {s['truncated']} | {s['tokens']:g} | {s['latency']:.1f} |")
    if rows:
        L += ["", "## Per esercizio (F1 relazioni, rilassato; media delle 2 ripetizioni)", "",
              "| esercizio | " + " | ".join(f"{ad.FORMAT_NAME[f]} bm25 → hybrid" for f, *_ in rows) + " |",
              "|---|" + "---|" * len(rows)]
        per = {f: (el.per_exercise(d["base"]["calls"]), el.per_exercise(d["treat"]["calls"])) for f, _, _, d in rows}
        for q in sorted(per[rows[0][0]][0]):
            L.append(f"| {q} | " + " | ".join(f"{fmt(per[f][0].get(q))} → {fmt(per[f][1].get(q))}"
                                              for f, *_ in rows) + " |")
        for f, *_ in rows:
            b, t = per[f]
            up = sum((t.get(q) or 0) > (b.get(q) or 0) for q in b)
            down = sum((t.get(q) or 0) < (b.get(q) or 0) for q in b)
            L.append(f"\n- {ad.FORMAT_NAME[f]}: hybrid meglio in {up} esercizi, peggio in {down}, pari negli altri.")
    return "\n".join(L) + "\n", res


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    text, _ = report(load_all(results))
    out = results / OUT_NAME
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(text, encoding="utf-8")
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(out / "summary.md")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    print(f"scritto in {out / 'summary.md'}")
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
