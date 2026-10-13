"""
Leva "esempi senza istruzioni per lo studente" (vista clean_v1, docs/decisions.md, voce 138). Scritto e testato PRIMA
della run (sulla sola baseline): da qui la regola (costanti, keeps, outcome) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Per formato, confronto APPAIATO sulle stesse 8 query di sviluppo × 2 ripetizioni: BASELINE
dev_g26 (Gemma 4 26B A4B QAT, configurazione di lavoro, vista raw) ristretta alle query di dev_g26ev, contro il
TRATTAMENTO dev_g26ev (stessa configurazione, vista clean_v1 degli esempi).

REGOLA (voce 138, non inferiorita'): adottare clean_v1 per tutte le condizioni del 3b se, in ENTRAMBI i formati,
  dF1_relazioni >= -0,03 (F1 macro per esercizio delle relazioni strutturali, abbinamento rilassato,
  evaluation/element_metrics.py) E dR >= -0,03 E dVc >= -1 E meno di 2 troncamenti. Se passa in un solo formato:
  decide l'utente. Riportati: F1 classi e generalizzazioni, J, token, latenza, dettaglio per esercizio.

Uso:
    python experiments/analyze_exview.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

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
BASELINE, TREATMENT = "dev_g26", "dev_g26ev"
FORMATS = {"plantuml": "P-G", "compact": "C-G"}
OUT_NAME = "dev_g26ev_analysis"
# --- regola (voce 138): non si modifica senza una nuova voce in docs/decisions.md ---
MAX_F1_LOSS = 0.03
MAX_R_LOSS = 0.03
MAX_VC_LOSS = 1
MAX_TRUNCATED = 1
EPS = 1e-9


def scores(calls: list[dict]) -> dict:
    core = em.core_metrics(calls)
    agg = el.aggregate(calls)["relaxed"]
    return {"R": core["R"], "J": core["J"], "Vc": core["Vc"], "V": core["V"], "truncated": core["truncated"],
            "F1rel": agg["relations"]["macro"]["F1"], "F1cls": agg["classes"]["macro"]["F1"],
            "F1gen": agg["generalizations"]["macro"]["F1"], "latency": core["latency_median"],
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
    passed = [f for f, v in formats.items() if v["ok"]]
    if len(passed) == len(formats):
        return "clean_v1 ADOTTATA per tutte le condizioni del 3b (non inferiore in entrambi i formati)"
    if passed:
        return f"passa solo in {', '.join(ad.FORMAT_NAME[f] for f in passed)}: DECIDE L'UTENTE"
    return "clean_v1 NON adottata (gli esempi restano raw)"


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    out = {}
    for f, name in FORMATS.items():
        treat = ai.load_run(results, TREATMENT, name, gt, MODEL_26, K)
        base = ai.load_run(results, BASELINE, name, gt, MODEL_26, K)
        ids = {c["q"] for c in treat["calls"]}
        base["calls"] = [c for c in base["calls"] if c["q"] in ids]
        out[f] = {"base": base, "treat": treat}
    return out


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def report(data: dict) -> tuple[str, dict]:
    res = {"formats": {}, "outcome": None}
    L = ["# Leva \"esempi senza istruzioni per lo studente\" (vista clean_v1) — `dev_g26ev` contro `dev_g26`", "",
         "SVILUPPO: le 8 query toccate dalla vista con bm25 k = 3, × 2 ripetizioni, Gemma 4 26B A4B QAT, configurazione di "
         "lavoro. Regola registrata PRIMA della run (voce 138), applicata da `experiments/analyze_exview.py`.", "",
         provenance.provenance_line(), "", "## Regola (voce 138)", "",
         f"In entrambi i formati: dF1_relazioni ≥ −{MAX_F1_LOSS}, dR ≥ −{MAX_R_LOSS}, dVc ≥ −{MAX_VC_LOSS}, meno di 2 "
         "troncamenti.", ""]
    rows = []
    for f, d in data.items():
        pre = [x["excluded"] for x in d.values() if x["excluded"]]
        if pre or not d["treat"]["calls"]:
            res["formats"][f] = None
            L.append(f"- **{ad.FORMAT_NAME[f]}: non decidibile** ({'; '.join(pre or ['trattamento assente'])})")
            continue
        sb, st = scores(d["base"]["calls"]), scores(d["treat"]["calls"])
        k = keeps(sb, st)
        res["formats"][f] = k
        L.append(f"- **{ad.FORMAT_NAME[f]}: {'non inferiore' if k['ok'] else 'INFERIORE'}** (dF1_relazioni "
                 f"{k['dF1rel']:+.3f}, dR {k['dR']:+.3f}, dVc {k['dVc']:+d}, troncate {k['truncated']})")
        rows.append((f, sb, st, d))
    res["outcome"] = outcome(res["formats"])
    L += ["", f"**Esito: {res['outcome']}**", "", "## Metriche (16 risposte per cella)", "",
          "| formato | vista | V | Vc | J | R | F1 classi | F1 relazioni | F1 generalizz. | troncate | token (med) | "
          "latenza (med, s) |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f, sb, st, _ in rows:
        for label, s in (("raw", sb), ("clean_v1", st)):
            L.append(f"| {ad.FORMAT_NAME[f]} | {label} | {s['V']} | {s['Vc']} | {fmt(s['J'])} | {fmt(s['R'])} | "
                     f"{fmt(s['F1cls'])} | {fmt(s['F1rel'])} | {fmt(s['F1gen'])} | {s['truncated']} | "
                     f"{s['tokens']:g} | {s['latency']:.1f} |")
    L += ["", "## Per esercizio (F1 relazioni, rilassato; media delle 2 ripetizioni)", "",
          "| esercizio | " + " | ".join(f"{ad.FORMAT_NAME[f]} raw → clean_v1" for f, *_ in rows) + " |",
          "|---|" + "---|" * len(rows)]
    if rows:
        for q in sorted({c["q"] for _, _, _, d in rows for c in d["treat"]["calls"]}):
            cells = []
            for _, _, _, d in rows:
                b = el.per_exercise([c for c in d["base"]["calls"] if c["q"] == q])
                t = el.per_exercise([c for c in d["treat"]["calls"] if c["q"] == q])
                cells.append(f"{fmt(b.get(q))} → {fmt(t.get(q))}")
            L.append(f"| {q} | " + " | ".join(cells) + " |")
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
