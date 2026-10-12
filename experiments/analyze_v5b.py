"""
Leva "attributi del compatto" (docs/decisions.md, voce 135). Scritto e testato PRIMA della run (sulla sola baseline):
da qui la regola (costanti, adopt) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Confronto APPAIATO sugli stessi 8 esercizi di sviluppo × 2 ripetizioni: BASELINE
dev_g26__C-G (Gemma 4 26B A4B QAT, compatto, istruzioni v5, esempi indentati), ristretta agli esercizi di dev_g26b,
contro il TRATTAMENTO dev_g26b__C-G (stessa configurazione, istruzioni v5b). Esercizi: i 6 con risposte della
baseline senza attributi + 2 di controllo (CONTROLS) che gli attributi li scrivevano bene. Metriche di
evaluation/metrics.py: R, Vc, M primaria (all_metrics) e attributi (attribute_metrics: A, A_prec, scheletri).

REGOLA (voce 135): adottare v5b per il compatto del 3b se
  scheletri <= MAX_SKELETONS (almeno dimezzati rispetto agli 8 della baseline) E, sui 2 esercizi di controllo,
  dA >= -0,05 e dA_prec >= -0,05 E, sulle 16 risposte, dR >= -0,03, dM_primaria >= -0,03, dVc >= -1 e meno di 2
  troncamenti.
Riportati per esercizio: attributi della risposta, A, A_prec, R, relazioni con entrambe le molteplicita'; per
ProjectManagement (GT senza attributi) gli attributi aggiunti.

Uso:
    python experiments/analyze_v5b.py [--results-dir data/results/generation]
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
from evaluation import metrics as em  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
MODEL_26 = "google/gemma-4-26b-a4b-qat"
K = 3
BASELINE, TREATMENT, CONF = "dev_g26", "dev_g26b", "C-G"
OUT_NAME = "dev_g26b_analysis"
CONTROLS = ("EUScienceConnect", "Facepage")
NO_ATTR_GT = ("ProjectManagement",)
# --- regola (voce 135): non si modifica senza una nuova voce in docs/decisions.md ---
MAX_SKELETONS = 4
MAX_CONTROL_A_LOSS = 0.05
MAX_CONTROL_PREC_LOSS = 0.05
MAX_R_LOSS = 0.03
MAX_M_LOSS = 0.03
MAX_VC_LOSS = 1
MAX_TRUNCATED = 1
EPS = 1e-9
NO_MULT_TYPES = ("ClassInheritance", "ClassRealization", "ClassDependency")


def adopt(base: dict, treat: dict, base_ctrl: dict, treat_ctrl: dict) -> dict:
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    d = {"skeletons": treat["skeletons"], "dR": z(treat["R"]) - z(base["R"]), "dM1": z(treat["M1"]) - z(base["M1"]),
         "dVc": treat["Vc"] - base["Vc"], "truncated": treat["truncated"],
         "dA_ctrl": z(treat_ctrl["A"]) - z(base_ctrl["A"]), "dA_prec_ctrl": z(treat_ctrl["A_prec"]) - z(base_ctrl["A_prec"]),
         "dA": z(treat["A"]) - z(base["A"])}
    d["ok"] = (d["skeletons"] <= MAX_SKELETONS and d["dA_ctrl"] >= -MAX_CONTROL_A_LOSS - EPS
               and d["dA_prec_ctrl"] >= -MAX_CONTROL_PREC_LOSS - EPS and d["dR"] >= -MAX_R_LOSS - EPS
               and d["dM1"] >= -MAX_M_LOSS - EPS and d["dVc"] >= -MAX_VC_LOSS and d["truncated"] <= MAX_TRUNCATED)
    return d


def metrics(calls: list[dict]) -> dict:
    m = em.all_metrics(calls)
    m.update(em.attribute_metrics(calls))
    rels = [e for c in calls if c["v"].level >= 3 for e in c["v"].diagram.get("edges", []) if e["type"] not in NO_MULT_TYPES]
    m["mult_present"] = (sum(bool((e.get("data") or {}).get("sourceMultiplicity"))
                             and bool((e.get("data") or {}).get("targetMultiplicity")) for e in rels) / len(rels)
                         if rels else None)
    return m


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    treat = ai.load_run(results, TREATMENT, CONF, gt, MODEL_26, K)
    base = ai.load_run(results, BASELINE, CONF, gt, MODEL_26, K)
    ids = {c["q"] for c in treat["calls"]} or set()
    base["calls"] = [c for c in base["calls"] if c["q"] in ids]
    return {"base": base, "treat": treat}


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def report(data: dict) -> tuple[str, dict]:
    res = {"outcome": None, "rule": None}
    L = ["# Leva \"attributi del compatto\" (istruzioni v5b) — `dev_g26b__C-G` contro `dev_g26__C-G`", "",
         "SVILUPPO, sottoinsieme di 8 esercizi × 2 ripetizioni (6 con risposte senza attributi + 2 di controllo), Gemma "
         "4 26B A4B QAT, compatto con esempi indentati, bm25 k = 3 (file congelato). Regola registrata PRIMA della run "
         "(voce 135), applicata da `experiments/analyze_v5b.py`.", "", provenance.provenance_line(), ""]
    pre = [x["excluded"] for x in data.values() if x["excluded"]]
    if pre or not data["treat"]["calls"]:
        res["outcome"] = "STOP: controllo preliminare non superato (" + "; ".join(pre or ["trattamento assente"]) + ")"
        return "\n".join(L + [f"**Esito: {res['outcome']}**"]) + "\n", res
    b, t = data["base"]["calls"], data["treat"]["calls"]
    mb, mt = metrics(b), metrics(t)
    ctrl = lambda cs: [c for c in cs if c["q"] in CONTROLS]  # noqa: E731
    mbc, mtc = em.attribute_metrics(ctrl(b)), em.attribute_metrics(ctrl(t))
    d = adopt(mb, mt, mbc, mtc)
    res["rule"] = d
    res["outcome"] = ("v5b ADOTTATA per il compatto del 3b" if d["ok"] else "v5b NON adottata (il compatto resta v5)")
    L += ["## Regola (voce 135)", "",
          f"Scheletri ≤ {MAX_SKELETONS}; sui 2 di controllo dA ≥ −{MAX_CONTROL_A_LOSS} e dA_prec ≥ "
          f"−{MAX_CONTROL_PREC_LOSS}; sulle 16 risposte dR ≥ −{MAX_R_LOSS}, dM_primaria ≥ −{MAX_M_LOSS}, dVc ≥ "
          f"−{MAX_VC_LOSS}, meno di 2 troncamenti.", "",
          f"- scheletri: {mb['skeletons']} → **{mt['skeletons']}**",
          f"- controllo ({', '.join(CONTROLS)}): A {fmt(mbc['A'])} → {fmt(mtc['A'])} (d {d['dA_ctrl']:+.3f}), A_prec "
          f"{fmt(mbc['A_prec'])} → {fmt(mtc['A_prec'])} (d {d['dA_prec_ctrl']:+.3f})",
          f"- 16 risposte: dR {d['dR']:+.3f}, dM_primaria {d['dM1']:+.3f}, dVc {d['dVc']:+d}, troncate {d['truncated']}",
          "", f"**Esito: {res['outcome']}**", "", "## Metriche (16 risposte per parte)", "",
          "| istruzioni | V | Vc | J | R | R_fam | M primaria | A | A_prec | scheletri | molteplicità presenti | "
          "classi in più | token (med) | latenza (med, s) |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for label, m, cs in (("v5 (baseline)", mb, b), ("v5b", mt, t)):
        tok = statistics.median(c["m"].get("completion_tokens_server") or 0 for c in cs)
        lat = statistics.median(c["m"]["latency_s"] for c in cs)
        L.append(f"| {label} | {m['V']} | {m['Vc']} | {fmt(m['J'])} | {fmt(m['R'])} | {fmt(m['R_fam'])} | {fmt(m['M1'])} | "
                 f"{fmt(m['A'])} | {fmt(m['A_prec'])} | {m['skeletons']} | {fmt(m['mult_present'])} | {m['extra_cls']} | "
                 f"{tok:g} | {lat:.1f} |")
    L += ["", "## Per esercizio (somma delle 2 ripetizioni; attributi della risposta, A, A_prec, R)", "",
          "| esercizio | ruolo | attributi GT (per risposta) | attributi v5 | attributi v5b | A v5 → v5b | A_prec v5 → "
          "v5b | R v5 → v5b |", "|---|---|---|---|---|---|---|---|"]
    for q in sorted({c["q"] for c in t}, key=lambda x: (x in CONTROLS, x in NO_ATTR_GT, x)):
        cb, ctq = [c for c in b if c["q"] == q], [c for c in t if c["q"] == q]
        ab, at = em.attribute_metrics(cb), em.attribute_metrics(ctq)
        rb, rt = em.core_metrics(cb)["R"], em.core_metrics(ctq)["R"]
        role = "controllo" if q in CONTROLS else "GT senza attributi" if q in NO_ATTR_GT else "senza attributi in v5"
        L.append(f"| {q} | {role} | {ab['attr_counts']['gt_attrs'] // max(len(cb), 1)} | {ab['attr_counts']['resp_attrs']} | "
                 f"{at['attr_counts']['resp_attrs']} | {fmt(ab['A'])} → {fmt(at['A'])} | {fmt(ab['A_prec'])} → "
                 f"{fmt(at['A_prec'])} | {fmt(rb)} → {fmt(rt)} |")
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
