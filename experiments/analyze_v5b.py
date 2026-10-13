"""
Leva "attributi del compatto" (docs/decisions.md, voce 135, riallineata dalla voce 146). Scritto e testato PRIMA della
run (sulla sola baseline): da qui la regola (costanti, adopt, outcome) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Confronto APPAIATO sugli stessi 8 esercizi di sviluppo × 2 ripetizioni, Gemma 4 26B A4B
QAT, compatto con esempi indentati e vista clean_v1, bm25 k = 3 (file congelato): TRATTAMENTO dev_g26b__C-G
(istruzioni v5b) contro BASELINE con istruzioni v5, ricostruita come nella voce 140 (dev_g26ev per le query toccate
dalla pulizia, dev_g26 per le altre: prompt identici). Esercizi: i 6 con risposte senza attributi + 2 di controllo
(CONTROLS) che gli attributi li scrivevano bene. Metriche: evaluation/element_metrics.py (abbinamento rilassato, macro
per esercizio) per attributi e relazioni; evaluation/metrics.py per R, M primaria e Vc.

Scheletro = risposta valida senza nessun attributo (element_metrics.elements) per un esercizio il cui GT ne ha.

REGOLA (voce 146): adottare v5b per il compatto del 3b se
  scheletri <= MAX_SKELETONS (almeno dimezzati rispetto ai 7 della baseline) E, sui 2 esercizi di controllo,
  d(recall attributi) >= -0,05 e d(precision attributi) >= -0,05 E, sulle 16 risposte, dF1_relazioni >= -0,03,
  dR >= -0,03, dM_primaria >= -0,03, dVc >= -1 e meno di 2 troncamenti.
Riportati: F1 attributi, molteplicita' presenti, attributi aggiunti per ProjectManagement (GT senza attributi),
dettaglio per esercizio.

Uso:
    python experiments/analyze_v5b.py [--results-dir data/results/generation]
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
CONFIGS = ROOT / "experiments" / "configs"
MODEL_26 = "google/gemma-4-26b-a4b-qat"
K = 3
TREATMENT, CONF = "dev_g26b", "C-G"
BASE_RAW, BASE_CLEAN = "dev_g26", "dev_g26ev"  # bm25 + clean_v1: le query di dev_g26ev da li', le altre da dev_g26
OUT_NAME = "dev_g26b_analysis"
CONTROLS = ("EUScienceConnect", "Facepage")
NO_ATTR_GT = ("ProjectManagement",)
# --- regola (voce 146): non si modifica senza una nuova voce in docs/decisions.md ---
MAX_SKELETONS = 3
MAX_CONTROL_R_LOSS = 0.05
MAX_CONTROL_P_LOSS = 0.05
MAX_F1_LOSS = 0.03
MAX_R_LOSS = 0.03
MAX_M_LOSS = 0.03
MAX_VC_LOSS = 1
MAX_TRUNCATED = 1
EPS = 1e-9
NO_MULT_TYPES = ("ClassInheritance", "ClassRealization", "ClassDependency")


def n_attrs(diagram: dict | None) -> int:
    return sum(len(v) for v in el.elements(diagram)["attributes"].values())


def is_skeleton(c: dict) -> bool:
    return c["v"].level >= 3 and n_attrs(c["v"].diagram) == 0 and n_attrs(c["gt"]) > 0


def scores(calls: list[dict]) -> dict:
    m = em.multiplicity_metrics(calls)
    agg = el.aggregate(calls)["relaxed"]
    rels = [e for c in calls if c["v"].level >= 3 for e in c["v"].diagram.get("edges", []) if e["type"] not in NO_MULT_TYPES]
    return {"R": m["R"], "J": m["J"], "M1": m["M1"], "V": m["V"], "Vc": m["Vc"], "truncated": m["truncated"],
            "F1rel": agg["relations"]["macro"]["F1"], "F1cls": agg["classes"]["macro"]["F1"],
            "attrP": agg["attributes"]["macro"]["P"], "attrR": agg["attributes"]["macro"]["R"],
            "attrF1": agg["attributes"]["macro"]["F1"], "skeletons": sum(is_skeleton(c) for c in calls),
            "mult_present": (sum(bool((e.get("data") or {}).get("sourceMultiplicity"))
                                 and bool((e.get("data") or {}).get("targetMultiplicity")) for e in rels) / len(rels)
                             if rels else None),
            "latency": m["latency_median"],
            "tokens": statistics.median(c["m"].get("completion_tokens_server") or 0 for c in calls) if calls else None}


def adopt(base: dict, treat: dict, base_ctrl: dict, treat_ctrl: dict) -> dict:
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    d = {"skeletons": treat["skeletons"], "dF1rel": z(treat["F1rel"]) - z(base["F1rel"]),
         "dR": z(treat["R"]) - z(base["R"]), "dM1": z(treat["M1"]) - z(base["M1"]), "dVc": treat["Vc"] - base["Vc"],
         "truncated": treat["truncated"], "dAttrR_ctrl": z(treat_ctrl["attrR"]) - z(base_ctrl["attrR"]),
         "dAttrP_ctrl": z(treat_ctrl["attrP"]) - z(base_ctrl["attrP"])}
    d["ok"] = (d["skeletons"] <= MAX_SKELETONS and d["dAttrR_ctrl"] >= -MAX_CONTROL_R_LOSS - EPS
               and d["dAttrP_ctrl"] >= -MAX_CONTROL_P_LOSS - EPS and d["dF1rel"] >= -MAX_F1_LOSS - EPS
               and d["dR"] >= -MAX_R_LOSS - EPS and d["dM1"] >= -MAX_M_LOSS - EPS and d["dVc"] >= -MAX_VC_LOSS
               and d["truncated"] <= MAX_TRUNCATED)
    return d


def outcome(d: dict | None) -> str:
    if d is None:
        return "STOP: controllo preliminare non superato (run assente, incompleta o con ragionamento)"
    return "v5b ADOTTATA per il compatto del 3b" if d["ok"] else "v5b NON adottata (il compatto resta v5)"


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    load = lambda n: yaml.safe_load((CONFIGS / f"{n}.yaml").read_text(encoding="utf-8"))  # noqa: E731
    ids, clean_ids = set(load(TREATMENT)["query_ids"]), set(load(BASE_CLEAN)["query_ids"])
    treat = ai.load_run(results, TREATMENT, CONF, gt, MODEL_26, K)
    raw = ai.load_run(results, BASE_RAW, CONF, gt, MODEL_26, K)
    clean = ai.load_run(results, BASE_CLEAN, CONF, gt, MODEL_26, K)
    base = {"name": f"v5 ({BASE_RAW} + {BASE_CLEAN})", "excluded": raw["excluded"] or clean["excluded"],
            "calls": [c for c in raw["calls"] if c["q"] in ids - clean_ids]
            + [c for c in clean["calls"] if c["q"] in ids & clean_ids]}
    return {"base": base, "treat": treat}


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def report(data: dict) -> tuple[str, dict]:
    res = {"outcome": None, "rule": None}
    L = ["# Leva \"attributi del compatto\" (istruzioni v5b) — `dev_g26b__C-G` contro v5 (stessa configurazione)", "",
         "SVILUPPO, sottoinsieme di 8 esercizi × 2 ripetizioni (6 con risposte senza attributi + 2 di controllo), Gemma "
         "4 26B A4B QAT, compatto con esempi indentati, vista clean_v1, bm25 k = 3 (file congelato). Baseline v5 "
         "ricostruita da dev_g26 e dev_g26ev (prompt identici). Regola registrata PRIMA della run (voce 146), applicata "
         "da `experiments/analyze_v5b.py`.", "", provenance.provenance_line(), ""]
    b, t = data["base"]["calls"], data["treat"]["calls"]
    pre = [x["excluded"] for x in data.values() if x["excluded"]]
    if pre or not t or len(t) != len(b):
        res["outcome"] = outcome(None)
        return "\n".join(L + [f"**Esito: {res['outcome']}** ({'; '.join(pre or ['risposte mancanti'])})"]) + "\n", res
    ctrl = lambda cs: [c for c in cs if c["q"] in CONTROLS]  # noqa: E731
    sb, st, sbc, stc = scores(b), scores(t), scores(ctrl(b)), scores(ctrl(t))
    d = adopt(sb, st, sbc, stc)
    res["rule"] = d
    res["outcome"] = outcome(d)
    L += ["## Regola (voce 146)", "",
          f"Scheletri ≤ {MAX_SKELETONS}; sui 2 di controllo d(recall attributi) ≥ −{MAX_CONTROL_R_LOSS} e d(precision "
          f"attributi) ≥ −{MAX_CONTROL_P_LOSS}; sulle 16 risposte dF1_relazioni ≥ −{MAX_F1_LOSS}, dR ≥ −{MAX_R_LOSS}, "
          f"dM_primaria ≥ −{MAX_M_LOSS}, dVc ≥ −{MAX_VC_LOSS}, meno di 2 troncamenti.", "",
          f"- scheletri: {sb['skeletons']} → **{st['skeletons']}**",
          f"- controllo ({', '.join(CONTROLS)}): recall attributi {fmt(sbc['attrR'])} → {fmt(stc['attrR'])} (d "
          f"{d['dAttrR_ctrl']:+.3f}), precision attributi {fmt(sbc['attrP'])} → {fmt(stc['attrP'])} (d "
          f"{d['dAttrP_ctrl']:+.3f})",
          f"- 16 risposte: dF1_relazioni {d['dF1rel']:+.3f}, dR {d['dR']:+.3f}, dM_primaria {d['dM1']:+.3f}, dVc "
          f"{d['dVc']:+d}, troncate {d['truncated']}",
          "", f"**Esito: {res['outcome']}**", "", "## Metriche (16 risposte per parte; element_metrics rilassato, macro)", "",
          "| istruzioni | V | Vc | J | R | M primaria | F1 classi | F1 relazioni | attributi P | attributi R | attributi "
          "F1 | scheletri | molteplicità presenti | troncate | token (med) | latenza (med, s) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for label, s in (("v5 (baseline)", sb), ("v5b", st)):
        L.append(f"| {label} | {s['V']} | {s['Vc']} | {fmt(s['J'])} | {fmt(s['R'])} | {fmt(s['M1'])} | "
                 f"{fmt(s['F1cls'])} | {fmt(s['F1rel'])} | {fmt(s['attrP'])} | {fmt(s['attrR'])} | {fmt(s['attrF1'])} | "
                 f"{s['skeletons']} | {fmt(s['mult_present'])} | {s['truncated']} | {s['tokens']:g} | "
                 f"{s['latency']:.1f} |")
    L += ["", "## Per esercizio (attributi della risposta sommati sulle 2 ripetizioni; metriche medie)", "",
          "| esercizio | ruolo | attributi GT | attributi v5 | attributi v5b | scheletri v5 → v5b | attributi F1 v5 → v5b "
          "| F1 relazioni v5 → v5b |", "|---|---|---|---|---|---|---|---|"]
    fb, ft = el.per_exercise(b, t="attributes"), el.per_exercise(t, t="attributes")
    rb, rt = el.per_exercise(b), el.per_exercise(t)
    for q in sorted({c["q"] for c in t}, key=lambda x: (x in CONTROLS, x in NO_ATTR_GT, x)):
        cb, ctq = [c for c in b if c["q"] == q], [c for c in t if c["q"] == q]
        na = lambda cs: sum(n_attrs(c["v"].diagram) for c in cs if c["v"].level >= 3)  # noqa: E731
        role = "controllo" if q in CONTROLS else "GT senza attributi" if q in NO_ATTR_GT else "senza attributi in v5"
        L.append(f"| {q} | {role} | {n_attrs(cb[0]['gt'])} | {na(cb)} | {na(ctq)} | {sum(map(is_skeleton, cb))} → "
                 f"{sum(map(is_skeleton, ctq))} | {fmt(fb.get(q))} → {fmt(ft.get(q))} | {fmt(rb.get(q))} → "
                 f"{fmt(rt.get(q))} |")
    return "\n".join(L) + "\n", res


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    data = load_all(results)
    if not data["treat"]["calls"] or data["treat"]["excluded"]:  # guardia: nessun summary senza la run completa
        print(f"run {TREATMENT}__{CONF} assente o incompleta ({data['treat']['excluded']}): nessuna analisi scritta")
        return 1
    text, _ = report(data)
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
