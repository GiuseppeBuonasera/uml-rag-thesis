"""
Leva "attributes sempre presente" del compatto (istruzioni v5c, docs/decisions.md, voce 150). Scritto e testato PRIMA
della run (sulla sola baseline): da qui la regola (costanti, adopt, outcome) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Confronto APPAIATO sui 20 esercizi di sviluppo × 2 ripetizioni, Gemma 4 26B A4B QAT,
compatto con esempi indentati e vista clean_v1, bm25 k = 3 (file congelato): TRATTAMENTO dev_g26c__C-G (istruzioni
v5c + esempi con "attributes": [] esplicita) contro BASELINE v5, ricostruita come nella voce 140 (dev_g26ev per le
query toccate dalla pulizia, dev_g26 per le altre: prompt identici). Metriche e scheletri come in analyze_v5b.py
(element_metrics rilassato, macro per esercizio; R, M primaria e Vc da evaluation/metrics.py).

REGOLA (voce 150): adottare v5c per il compatto del 3b se
  scheletri <= MAX_SKELETONS (meno della meta' dei 7 della baseline) E, sulle 40 risposte, d(recall attributi) >= 0,
  d(precision attributi) >= -0,05, dF1_relazioni >= -0,03, dR >= -0,03, dM_primaria >= -0,03, dVc >= -2 e meno di 2
  troncamenti.
Riportati: F1 attributi, quota di classi senza attributi, molteplicita' presenti, token, dettaglio per esercizio.

Uso:
    python experiments/analyze_v5c.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "generation"), str(ROOT / "experiments"), str(ROOT)]
import analyze_dev as ad  # noqa: E402
import analyze_instructions as ai  # noqa: E402
import analyze_v5b as v5b  # noqa: E402  (scores, is_skeleton, n_attrs: stesse definizioni della voce 146)
from evaluation import element_metrics as el  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
CONFIGS = ROOT / "experiments" / "configs"
MODEL_26 = v5b.MODEL_26
K = 3
TREATMENT, CONF = "dev_g26c", "C-G"
BASE_RAW, BASE_CLEAN = "dev_g26", "dev_g26ev"
OUT_NAME = "dev_g26c_analysis"
# --- regola (voce 150): non si modifica senza una nuova voce in docs/decisions.md ---
MAX_SKELETONS = 3
MIN_ATTR_R_GAIN = 0.0
MAX_ATTR_P_LOSS = 0.05
MAX_F1_LOSS = 0.03
MAX_R_LOSS = 0.03
MAX_M_LOSS = 0.03
MAX_VC_LOSS = 2
MAX_TRUNCATED = 1
EPS = 1e-9


def empty_class_share(calls: list[dict]) -> float | None:
    """Quota di classi non enum senza attributi nelle risposte valide (descrittivo)."""
    n = e = 0
    for c in calls:
        if c["v"].level < 3:
            continue
        els = el.elements(c["v"].diagram)
        for attrs in els["attributes"].values():
            n += 1
            e += not attrs
    return e / n if n else None


def adopt(base: dict, treat: dict) -> dict:
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    d = {"skeletons": treat["skeletons"], "dAttrR": z(treat["attrR"]) - z(base["attrR"]),
         "dAttrP": z(treat["attrP"]) - z(base["attrP"]), "dF1rel": z(treat["F1rel"]) - z(base["F1rel"]),
         "dR": z(treat["R"]) - z(base["R"]), "dM1": z(treat["M1"]) - z(base["M1"]), "dVc": treat["Vc"] - base["Vc"],
         "truncated": treat["truncated"]}
    d["ok"] = (d["skeletons"] <= MAX_SKELETONS and d["dAttrR"] >= MIN_ATTR_R_GAIN - EPS
               and d["dAttrP"] >= -MAX_ATTR_P_LOSS - EPS and d["dF1rel"] >= -MAX_F1_LOSS - EPS
               and d["dR"] >= -MAX_R_LOSS - EPS and d["dM1"] >= -MAX_M_LOSS - EPS and d["dVc"] >= -MAX_VC_LOSS
               and d["truncated"] <= MAX_TRUNCATED)
    return d


def outcome(d: dict | None) -> str:
    if d is None:
        return "STOP: controllo preliminare non superato (run assente, incompleta o con ragionamento)"
    return "v5c ADOTTATA per il compatto del 3b" if d["ok"] else "v5c NON adottata (il compatto resta v5)"


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
    L = ["# Leva \"attributes sempre presente\" (istruzioni v5c) — `dev_g26c__C-G` contro v5 (stessa configurazione)", "",
         "SVILUPPO: 20 esercizi × 2 ripetizioni, Gemma 4 26B A4B QAT, compatto con esempi indentati, vista clean_v1, bm25 "
         "k = 3 (file congelato). v5c = istruzioni con \"attributes\" obbligatoria nelle classi non enum + esempi con "
         "\"attributes\": [] esplicita. Baseline v5 ricostruita da dev_g26 e dev_g26ev (prompt identici). Regola "
         "registrata PRIMA della run (voce 150), applicata da `experiments/analyze_v5c.py`.", "",
         provenance.provenance_line(), ""]
    b, t = data["base"]["calls"], data["treat"]["calls"]
    pre = [x["excluded"] for x in data.values() if x["excluded"]]
    if pre or not t or len(t) != len(b):
        res["outcome"] = outcome(None)
        return "\n".join(L + [f"**Esito: {res['outcome']}** ({'; '.join(pre or ['risposte mancanti'])})"]) + "\n", res
    sb, st = v5b.scores(b), v5b.scores(t)
    d = adopt(sb, st)
    res["rule"] = d
    res["outcome"] = outcome(d)
    L += ["## Regola (voce 150)", "",
          f"Scheletri ≤ {MAX_SKELETONS}; sulle 40 risposte d(recall attributi) ≥ {MIN_ATTR_R_GAIN}, d(precision "
          f"attributi) ≥ −{MAX_ATTR_P_LOSS}, dF1_relazioni ≥ −{MAX_F1_LOSS}, dR ≥ −{MAX_R_LOSS}, dM_primaria ≥ "
          f"−{MAX_M_LOSS}, dVc ≥ −{MAX_VC_LOSS}, meno di 2 troncamenti.", "",
          f"- scheletri: {sb['skeletons']} → **{st['skeletons']}**",
          f"- attributi: recall {fmt(sb['attrR'])} → {fmt(st['attrR'])} (d {d['dAttrR']:+.3f}), precision "
          f"{fmt(sb['attrP'])} → {fmt(st['attrP'])} (d {d['dAttrP']:+.3f})",
          f"- dF1_relazioni {d['dF1rel']:+.3f}, dR {d['dR']:+.3f}, dM_primaria {d['dM1']:+.3f}, dVc {d['dVc']:+d}, "
          f"troncate {d['truncated']}", "", f"**Esito: {res['outcome']}**", "",
          "## Metriche (40 risposte per parte; element_metrics rilassato, macro)", "",
          "| istruzioni | V | Vc | J | R | M primaria | F1 classi | F1 relazioni | attributi P | attributi R | attributi "
          "F1 | scheletri | classi senza attributi | molteplicità presenti | troncate | token (med) | latenza (med, s) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for label, s, cs in (("v5 (baseline)", sb, b), ("v5c", st, t)):
        L.append(f"| {label} | {s['V']} | {s['Vc']} | {fmt(s['J'])} | {fmt(s['R'])} | {fmt(s['M1'])} | "
                 f"{fmt(s['F1cls'])} | {fmt(s['F1rel'])} | {fmt(s['attrP'])} | {fmt(s['attrR'])} | {fmt(s['attrF1'])} | "
                 f"{s['skeletons']} | {fmt(empty_class_share(cs))} | {fmt(s['mult_present'])} | {s['truncated']} | "
                 f"{s['tokens']:g} | {s['latency']:.1f} |")
    L += ["", "## Per esercizio (attributi della risposta sommati sulle 2 ripetizioni; metriche medie)", "",
          "| esercizio | attributi GT | attributi v5 | attributi v5c | scheletri v5 → v5c | attributi F1 v5 → v5c | "
          "F1 relazioni v5 → v5c |", "|---|---|---|---|---|---|---|"]
    fb, ft = el.per_exercise(b, t="attributes"), el.per_exercise(t, t="attributes")
    rb, rt = el.per_exercise(b), el.per_exercise(t)
    na = lambda cs: sum(v5b.n_attrs(c["v"].diagram) for c in cs if c["v"].level >= 3)  # noqa: E731
    for q in sorted({c["q"] for c in t}):
        cb, ctq = [c for c in b if c["q"] == q], [c for c in t if c["q"] == q]
        L.append(f"| {q} | {v5b.n_attrs(cb[0]['gt'])} | {na(cb)} | {na(ctq)} | {sum(map(v5b.is_skeleton, cb))} → "
                 f"{sum(map(v5b.is_skeleton, ctq))} | {fmt(fb.get(q))} → {fmt(ft.get(q))} | {fmt(rb.get(q))} → "
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
