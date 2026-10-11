"""
Due verifiche prima del Passo 3b (docs/decisions.md, voce 123). Scritto e testato PRIMA delle run (sulle sole baseline):
da qui le regole A e B (costanti e funzioni rule_a, rule_b) non si modificano senza una nuova voce.

Nessuna chiamata a un LLM. Gemma 4 12B QAT, config v2, bm25 k = 3, 20 esercizi di sviluppo, 2 ripetizioni.
  A. compatto con istruzioni v5 + esempi indentati (dev_c5indent__C-G) contro v4 + esempi indentati (dev_cindent__C-G),
     pool unico:
       adottare v5 per il compatto se (dR >= +0,03 OPPURE dR_fam >= +0,03) E dVc >= -2 E dM_primaria >= -0,03.
  B. pool dei soli 60 del corpus (dev_poolC__C-G, dev_poolC__P-G) contro il pool unico (dev_cindent__C-G, dev_v5__P-G),
     configurazione di lavoro di ciascun formato:
       il 3b usa il pool "corpus60" se nel compatto dR(corpus60 - all) >= +0,05 E in PlantUML dR >= -0,03 E in nessuno
       dei due formati dVc < -2; altrimenti resta il pool unico.
     Si riporta anche R separato per gli esercizi i cui esempi cambiano tra i due pool e per quelli invariati.
Se A e B cambiano entrambi la configurazione, l'interazione (v5 del compatto con il pool 60) non si testa qui.

Uso:
    python experiments/analyze_pool.py [--results-dir data/results/generation]
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
import analyze_pilot as ap  # noqa: E402
import analyze_v5 as av  # noqa: E402  (r_fam)
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
MODEL_ID = "google/gemma-4-12b-qat"
K = 3
OUT_NAME = "dev_pool_analysis"
# --- regole (voce 123): non si modificano senza una nuova voce in docs/decisions.md ---
A_ADOPT_R = 0.03
A_ADOPT_R_FAM = 0.03
A_MAX_VC_LOSS = 2
A_MAX_M_LOSS = 0.03
B_MIN_COMPACT_GAIN = 0.05
B_MAX_PLANTUML_LOSS = 0.03
B_MAX_VC_LOSS = 2
EPS = 1e-9


def z(x):
    return 0.0 if x is None else x


def rule_a(base: dict, treat: dict) -> dict:
    dr, drf = z(treat["R"]) - z(base["R"]), z(treat["R_fam"]) - z(base["R_fam"])
    dvc, dm = treat["Vc"] - base["Vc"], z(treat["M1"]) - z(base["M1"])
    gain = dr >= A_ADOPT_R - EPS or drf >= A_ADOPT_R_FAM - EPS
    adopt = gain and dvc >= -A_MAX_VC_LOSS and dm >= -A_MAX_M_LOSS - EPS
    return {"adopt": adopt, "dR": dr, "dR_fam": drf, "dVc": dvc, "dM1": dm, "gain": gain}


def rule_b(base: dict[str, dict], treat: dict[str, dict]) -> dict:
    """base / treat: formato ('plantuml', 'compact') -> metriche."""
    d = {f: {"dR": z(treat[f]["R"]) - z(base[f]["R"]), "dVc": treat[f]["Vc"] - base[f]["Vc"]} for f in base}
    use60 = (d["compact"]["dR"] >= B_MIN_COMPACT_GAIN - EPS and d["plantuml"]["dR"] >= -B_MAX_PLANTUML_LOSS - EPS
             and all(x["dVc"] >= -B_MAX_VC_LOSS for x in d.values()))
    return {"use_corpus60": use60, "deltas": d}


def metrics(calls: list[dict]) -> dict:
    m = ai.metrics(calls)
    m["R_fam"] = av.r_fam(m)
    return m


def r_by_exercise(calls: list[dict]) -> dict[str, float]:
    out: dict[str, list[float]] = {}
    for c in calls:
        n = len(c["gt"]["edges"])
        r = 0.0 if c["v"].level < 3 or not n else ap.compare_relations(c["v"].diagram, c["gt"])["same_type"] / n
        out.setdefault(c["q"], []).append(r)
    return {q: statistics.mean(v) for q, v in out.items()}


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    run = lambda prefix, name: ai.load_run(results, prefix, name, gt, MODEL_ID, K)  # noqa: E731
    return {"a_base": run("dev_cindent", "C-G"), "a_treat": run("dev_c5indent", "C-G"),
            "b_base": {"compact": run("dev_cindent", "C-G"), "plantuml": run("dev_v5", "P-G")},
            "b_treat": {"compact": run("dev_poolC", "C-G"), "plantuml": run("dev_poolC", "P-G")}}


def report(data: dict) -> tuple[str, dict]:
    res = {"A": None, "B": None}
    L = ["# Verifiche prima del Passo 3b: compatto v5 + esempi indentati e pool dei soli 60 del corpus (voce 123)", "",
         "SVILUPPO: 20 esercizi di sviluppo, Gemma 4 12B QAT, bm25 k = 3. Regole registrate PRIMA delle run (voce 123), "
         "applicate da `experiments/analyze_pool.py`.", "", provenance.provenance_line(), "", "## A. Compatto: v5 + indent contro v4 + indent (pool unico)", ""]
    pre = [x["excluded"] for x in (data["a_base"], data["a_treat"]) if x["excluded"]]
    if pre:
        L.append(f"- non decidibile: {'; '.join(pre)}")
    else:
        mb, mt = metrics(data["a_base"]["calls"]), metrics(data["a_treat"]["calls"])
        res["A"] = rule_a(mb, mt)
        a = res["A"]
        L += [f"Regola: adottare v5 se (dR >= +0,03 oppure dR_fam >= +0,03) e dVc >= -2 e dM_primaria >= -0,03.", "",
              f"- **{'v5 ADOTTATA per il compatto' if a['adopt'] else 'v5 NON adottata: il compatto resta v4 + indent'}** "
              f"(dR {a['dR']:+.3f}, dR_fam {a['dR_fam']:+.3f}, dVc {a['dVc']:+d}, dM_primaria {a['dM1']:+.3f})", "",
              "| istruzioni | V | Vc | J | R | R_fam | M primaria | troncate |", "|---|---|---|---|---|---|---|---|"]
        for lab, m in (("v4 + indent (baseline)", mb), ("v5 + indent", mt)):
            L.append(f"| {lab} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {ad.fmt(m['J'])} | {ad.fmt(m['R'])} | "
                     f"{ad.fmt(m['R_fam'])} | {ad.fmt(m['M1'])} | {m['truncated']} |")
    L += ["", "## B. Pool: soli 60 del corpus contro pool unico (configurazione di lavoro)", ""]
    pre = [x["excluded"] for d in (data["b_base"], data["b_treat"]) for x in d.values() if x["excluded"]]
    if pre:
        L.append(f"- non decidibile: {'; '.join(pre)}")
    else:
        mb = {f: metrics(x["calls"]) for f, x in data["b_base"].items()}
        mt = {f: metrics(x["calls"]) for f, x in data["b_treat"].items()}
        res["B"] = b = rule_b(mb, mt)
        L += ["Regola: pool dei 60 se nel compatto dR >= +0,05 e in PlantUML dR >= -0,03 e in nessun formato dVc < -2.", "",
              f"- **{'il 3b usa il pool dei SOLI 60 del corpus' if b['use_corpus60'] else 'resta il pool unico'}** ("
              + "; ".join(f"{ad.FORMAT_NAME[f]}: dR {d['dR']:+.3f}, dVc {d['dVc']:+d}" for f, d in b["deltas"].items()) + ")",
              "", "| formato | pool | V | Vc | J | R | M primaria | R (esercizi con esempi cambiati) | R (esempi invariati) |",
              "|---|---|---|---|---|---|---|---|---|"]
        for f in ("plantuml", "compact"):
            ex_base = {c["q"]: c["m"]["example_ids"] for c in data["b_base"][f]["calls"]}
            ex_treat = {c["q"]: c["m"]["example_ids"] for c in data["b_treat"][f]["calls"]}
            changed = {q for q in ex_base if ex_base[q] != ex_treat.get(q)}
            for lab, x, m in (("unico (80)", data["b_base"][f], mb[f]), ("solo corpus (60)", data["b_treat"][f], mt[f])):
                rq = r_by_exercise(x["calls"])
                rc = statistics.mean(rq[q] for q in changed) if changed else float("nan")
                ru = statistics.mean(rq[q] for q in rq if q not in changed)
                L.append(f"| {ad.FORMAT_NAME[f]} | {lab} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {ad.fmt(m['J'])} | "
                         f"{ad.fmt(m['R'])} | {ad.fmt(m['M1'])} | {rc:.3f} ({len(changed)}) | {ru:.3f} ({len(rq) - len(changed)}) |")
    if res["A"] and res["B"] and res["A"]["adopt"] and res["B"]["use_corpus60"]:
        L += ["", "**A e B cambiano entrambi la configurazione**: la combinazione (v5 del compatto con il pool dei 60) non è "
              "testata qui; si registra come configurazione del 3b e si dichiara."]
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
