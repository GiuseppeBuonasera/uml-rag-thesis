"""
Varianti del retriever, passo 4 (docs/decisions.md, voci 120-121): generazioni di sviluppo per struct (v2), construct
(v4) e struct_construct (v2 + v4) contro bm25, nella configurazione di lavoro di ciascun formato. Scritto e testato
PRIMA della run (sulle sole baseline): da qui la regola (MAX_R_LOSS, MAX_VC_LOSS, MAX_M_LOSS, ADOPT_R, MAX_TRUNCATED,
TIE, SIMPLICITY, verdict, outcome) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Baseline bm25 (stessi esercizi, parametri, istruzioni e pool unico):
  PlantUML  data/results/generation/dev_v5__P-G       (istruzioni v5)
  compatto  data/results/generation/dev_cindent__C-G  (istruzioni v4, esempi indentati)
Varianti: dev_structP__P-G e dev_structC__C-G, condizioni struct / construct / struct_construct (40 risposte per
condizione e formato). Metriche di experiments/analyze_instructions.py.

REGOLA (voce 121): una variante ENTRA nel Passo 3b (accanto a bm25 e MiniLM) se
  in ENTRAMBI i formati dR >= -0,03, dVc >= -2, dM_primaria >= -0,03 e meno di 2 troncamenti per max_tokens
  (controllo preliminare come voce 98), E in ALMENO UN formato dR >= +0,03.
  Tra quelle che entrano vince la media di dR sui due formati piu' alta; entro 0,01 vince la piu' semplice
  (construct < struct < struct_construct). Nessuna: nel 3b restano bm25 e MiniLM.

Uso:
    python experiments/analyze_struct.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import analyze_dev as ad  # noqa: E402
import analyze_instructions as ai  # noqa: E402
import analyze_retrievers as ar  # noqa: E402  (load_condition)
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
MODEL_ID = "google/gemma-4-12b-qat"
K = 3
FORMATS = {"plantuml": {"name": "P-G", "baseline": "dev_v5", "treatment": "dev_structP"},
           "compact": {"name": "C-G", "baseline": "dev_cindent", "treatment": "dev_structC"}}
SIMPLICITY = ("construct", "struct", "struct_construct")
LABEL = {"construct": "v4 costrutti", "struct": "v2 struttura", "struct_construct": "v2 + v4"}
OUT_NAME = "dev_struct_analysis"
# --- regola (voce 121): non si modifica senza una nuova voce in docs/decisions.md ---
MAX_R_LOSS = 0.03
MAX_VC_LOSS = 2
MAX_M_LOSS = 0.03
ADOPT_R = 0.03
MAX_TRUNCATED = 1
TIE = 0.01
EPS = 1e-9


def verdict(base: dict, var: dict) -> dict:
    """Esito per un formato: 'keeps' (nessun peggioramento oltre le soglie) e 'gain' (dR >= +0,03)."""
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    dr, dvc, dm = z(var["R"]) - z(base["R"]), var["Vc"] - base["Vc"], z(var["M1"]) - z(base["M1"])
    keeps = (dr >= -MAX_R_LOSS - EPS and dvc >= -MAX_VC_LOSS and dm >= -MAX_M_LOSS - EPS
             and var["truncated"] <= MAX_TRUNCATED)
    return {"dR": dr, "dVc": dvc, "dM1": dm, "truncated": var["truncated"], "keeps": keeps,
            "gain": dr >= ADOPT_R - EPS}


def outcome(per_format: dict[str, dict[str, dict]]) -> dict:
    """per_format: formato -> variante -> verdict (o {'excluded': motivo})."""
    res = {"enters": [], "winner": None, "tied": [], "mean_dR": {}}
    for v in SIMPLICITY:
        vs = [per_format[f][v] for f in per_format]
        if any("excluded" in x for x in vs):
            continue
        res["mean_dR"][v] = statistics.mean(x["dR"] for x in vs)
        if all(x["keeps"] for x in vs) and any(x["gain"] for x in vs):
            res["enters"].append(v)
    if res["enters"]:
        best = max(res["mean_dR"][v] for v in res["enters"])
        res["tied"] = [v for v in res["enters"] if best - res["mean_dR"][v] <= TIE + EPS]
        res["winner"] = res["tied"][0]
    return res


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    data = {}
    for f, spec in FORMATS.items():
        data[f] = {"bm25": ai.load_run(results, spec["baseline"], spec["name"], gt, MODEL_ID, K)}
        for v in SIMPLICITY:
            data[f][v] = ar.load_condition(results, spec["treatment"], spec["name"], gt, MODEL_ID, v, 40)
    return data


def report(data: dict) -> tuple[str, dict]:
    metrics = {f: {c: ai.metrics(x["calls"]) if x["calls"] else None for c, x in d.items()} for f, d in data.items()}
    per_format = {}
    for f, d in data.items():
        per_format[f] = {}
        for v in SIMPLICITY:
            pre = [x["excluded"] for x in (d["bm25"], d[v]) if x["excluded"]]
            per_format[f][v] = {"excluded": "; ".join(pre)} if pre else verdict(metrics[f]["bm25"], metrics[f][v])
    res = outcome(per_format)
    L = ["# Varianti del retriever: generazioni di sviluppo (passo 4, voci 120-121)", "",
         "SVILUPPO: 20 esercizi di sviluppo, pool unico, k = 3, Gemma 4 12B QAT, configurazione di lavoro di ciascun "
         "formato (PlantUML v5; compatto v4 con esempi indentati). Baseline bm25: `dev_v5__P-G`, `dev_cindent__C-G`. "
         "Regola registrata PRIMA della run (voce 121), applicata da `experiments/analyze_struct.py`.", "",
         provenance.provenance_line(), "", "## Regola (voce 121)", "",
         "Entra nel 3b se in entrambi i formati dR >= -0,03, dVc >= -2, dM_primaria >= -0,03 e meno di 2 troncamenti, e "
         "in almeno un formato dR >= +0,03; tra quelle che entrano vince la media di dR più alta, entro 0,01 la più "
         "semplice (construct < struct < struct_construct).", ""]
    for v in SIMPLICITY:
        parts = []
        for f in FORMATS:
            x = per_format[f][v]
            parts.append(f"{ad.FORMAT_NAME[f]}: " + (f"esclusa ({x['excluded']})" if "excluded" in x else
                         f"dR {x['dR']:+.3f}, dVc {x['dVc']:+d}, dM {x['dM1']:+.3f}, troncate {x['truncated']}"
                         f"{'' if x['keeps'] else ' — PEGGIORA oltre le soglie'}{' — guadagno' if x['gain'] else ''}"))
        L.append(f"- **{LABEL[v]}** ({'ENTRA' if v in res['enters'] else 'non entra'}): " + "; ".join(parts))
    L += ["", f"**Esito: {('nel 3b entra ' + LABEL[res['winner']] + ' (in parità: ' + ', '.join(LABEL[v] for v in res['tied']) + ')') if res['winner'] else 'nessuna variante entra: nel 3b restano bm25 e MiniLM'}.**",
          "", "## Metriche", "", "| formato | retriever | V | Vc | J | R | M primaria | troncate |",
          "|---|---|---|---|---|---|---|---|"]
    for f, d in data.items():
        for c in ("bm25", *SIMPLICITY):
            m = metrics[f][c]
            name = "bm25 (baseline)" if c == "bm25" else LABEL[c]
            if m is None:
                L.append(f"| {ad.FORMAT_NAME[f]} | {name} | — | — | — | — | — | — |")
                continue
            L.append(f"| {ad.FORMAT_NAME[f]} | {name} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {ad.fmt(m['J'])} | "
                     f"{ad.fmt(m['R'])} | {ad.fmt(m['M1'])} | {m['truncated']} |")
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
