"""
Passo 2 rifatto con il retriever dense (docs/decisions.md, voce 142). Scritto e testato PRIMA della run: la regola e'
quella della voce 140, con le stesse funzioni di experiments/analyze_hybrid26.py (scores, keeps), riusate senza
modifiche.

Nessuna chiamata a un LLM. Per formato, confronto APPAIATO sui 20 esercizi di sviluppo × 2 ripetizioni, Gemma 4 26B
A4B QAT con la configurazione di lavoro del 3b (vista clean_v1): TRATTAMENTO dev_g26de (dense k = 3) contro la BASELINE
bm25 k = 3 della voce 140 (dev_g26ev per le 8 query toccate dalla pulizia, dev_g26 per le altre 12). Descrittivo: il
confronto con hybrid (dev_g26hy), se presente.

REGOLA (voce 142, non inferiorita'): dense resta nel 3b se, in ENTRAMBI i formati, dF1_relazioni >= -0,03 E dR >= -0,03
E dVc >= -2 E meno di 2 troncamenti; altrimenti decide l'utente.

Uso:
    python experiments/analyze_dense26.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "generation"), str(ROOT / "experiments"), str(ROOT)]
import analyze_dev as ad  # noqa: E402
import analyze_hybrid26 as ah  # noqa: E402  (scores, keeps, baseline: regola della voce 140, invariata)
import analyze_instructions as ai  # noqa: E402
from evaluation import element_metrics as el  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ah.RESULTS
TREATMENT = "dev_g26de"
HYBRID = "dev_g26hy"
OUT_NAME = "dev_g26de_analysis"


def outcome(formats: dict[str, dict | None]) -> str:
    if any(v is None for v in formats.values()):
        return "STOP: controllo preliminare non superato (run assente, incompleta o con ragionamento)"
    if all(v["ok"] for v in formats.values()):
        return "dense RESTA nel 3b (non inferiore a bm25 in entrambi i formati)"
    failed = [ad.FORMAT_NAME[f] for f, v in formats.items() if not v["ok"]]
    return f"dense inferiore a bm25 in {', '.join(failed)}: DECIDE L'UTENTE se toglierlo dal 3b"


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    base = ah.load_all(results)  # bm25 ricostruita (e hybrid come "treat", se presente)
    out = {}
    for f, name in ah.FORMATS.items():
        out[f] = {"base": base[f]["base"], "treat": ai.load_run(results, TREATMENT, name, gt, ah.MODEL_26, ah.K),
                  "hybrid": base[f]["treat"]}
    return out


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def report(data: dict) -> tuple[str, dict]:
    res = {"formats": {}, "outcome": None}
    L = ["# Passo 2 rifatto con il retriever dense — `dev_g26de` contro bm25 (stessa configurazione)", "",
         "SVILUPPO: 20 esercizi × 2 ripetizioni, Gemma 4 26B A4B QAT, configurazione di lavoro del 3b (vista clean_v1, "
         "file congelato). Baseline bm25 della voce 140. Regola registrata PRIMA della run (voce 142), applicata da "
         "`experiments/analyze_dense26.py` con le funzioni di `analyze_hybrid26.py`.", "", provenance.provenance_line(),
         "", "## Regola (voce 142)", "",
         f"Dense resta nel 3b se, in entrambi i formati, dF1_relazioni ≥ −{ah.MAX_F1_LOSS}, dR ≥ −{ah.MAX_R_LOSS}, dVc ≥ "
         f"−{ah.MAX_VC_LOSS}, meno di 2 troncamenti.", ""]
    rows = []
    for f, d in data.items():
        pre = [x["excluded"] for k, x in d.items() if k != "hybrid" and x["excluded"]]
        if pre or len(d["treat"]["calls"]) != len(d["base"]["calls"]) or not d["treat"]["calls"]:
            res["formats"][f] = None
            L.append(f"- **{ad.FORMAT_NAME[f]}: non decidibile** ({'; '.join(pre or ['risposte mancanti'])})")
            continue
        sb, st = ah.scores(d["base"]["calls"]), ah.scores(d["treat"]["calls"])
        sh = ah.scores(d["hybrid"]["calls"]) if d["hybrid"]["calls"] and not d["hybrid"]["excluded"] else None
        k = ah.keeps(sb, st)
        res["formats"][f] = k
        L.append(f"- **{ad.FORMAT_NAME[f]}: {'non inferiore' if k['ok'] else 'INFERIORE'}** (dF1_relazioni "
                 f"{k['dF1rel']:+.3f}, dR {k['dR']:+.3f}, dVc {k['dVc']:+d}, troncate {k['truncated']})")
        rows.append((f, sb, st, sh, d))
    res["outcome"] = outcome(res["formats"])
    L += ["", f"**Esito: {res['outcome']}**", "", "## Metriche (40 risposte per cella; hybrid solo descrittivo)", "",
          "| formato | retriever | V | Vc | J | R | M primaria | F1 classi | F1 relazioni | F1 generalizz. | esempi De "
          "Bari | troncate | token (med) | latenza (med, s) |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f, sb, st, sh, _ in rows:
        for label, s in (("bm25", sb), ("hybrid", sh), ("dense", st)):
            if s is None:
                continue
            L.append(f"| {ad.FORMAT_NAME[f]} | {label} | {s['V']} | {s['Vc']} | {fmt(s['J'])} | {fmt(s['R'])} | "
                     f"{fmt(s['M1'])} | {fmt(s['F1cls'])} | {fmt(s['F1rel'])} | {fmt(s['F1gen'])} | "
                     f"{100 * s['debari']:.0f} % | {s['truncated']} | {s['tokens']:g} | {s['latency']:.1f} |")
    if rows:
        L += ["", "## Per esercizio (F1 relazioni, rilassato; media delle 2 ripetizioni)", "",
              "| esercizio | " + " | ".join(f"{ad.FORMAT_NAME[f]} bm25 → dense" for f, *_ in rows) + " |",
              "|---|" + "---|" * len(rows)]
        per = {f: (el.per_exercise(d["base"]["calls"]), el.per_exercise(d["treat"]["calls"])) for f, *_, d in rows}
        for q in sorted(per[rows[0][0]][0]):
            L.append(f"| {q} | " + " | ".join(f"{fmt(per[f][0].get(q))} → {fmt(per[f][1].get(q))}"
                                              for f, *_ in rows) + " |")
        for f, *_ in rows:
            b, t = per[f]
            up = sum((t.get(q) or 0) > (b.get(q) or 0) for q in b)
            down = sum((t.get(q) or 0) < (b.get(q) or 0) for q in b)
            L.append(f"\n- {ad.FORMAT_NAME[f]}: dense meglio in {up} esercizi, peggio in {down}, pari negli altri.")
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
