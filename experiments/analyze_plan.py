"""
Leva "piano breve" sull'insieme di sviluppo (docs/decisions.md, voce 126). Scritto e testato PRIMA della run (sulle sole
baseline): da qui la regola (costanti, adopt) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Per formato confronta la BASELINE (istruzioni v5: dev_v5__P-G; v5 + esempi indentati:
dev_c5indent__C-G) con il TRATTAMENTO v5plan (dev_plan__P-G / __C-G: la risposta ha un PLAN e poi il DIAGRAM; le
metriche si calcolano SOLO sul diagramma, generation/plan_split.py). Metriche di experiments/analyze_v5.py.

REGOLA (voce 126), per formato, delta = piano - baseline su 40 risposte:
  adottare se (dR >= +0,03 OPPURE dR_fam >= +0,03) E dVc >= -2 E dM_primaria >= -0,03 E meno di 2 troncamenti
  E latenza mediana <= 2,5 x quella della baseline (misurata a GPU libera).
  Se adottata in un formato, v5plan diventa la configurazione di lavoro di quel formato per tutte le condizioni del 3b.
Riportati: marcatore mancante, token di output, latenza, stima delle ore del 3b (circa 2.300 generazioni); coerenza
piano-diagramma (quota di classi del diagramma presenti nel piano, quota di classi del piano presenti nel diagramma,
classi in piu' rispetto al GT gia' presenti nel piano); 3 esempi in cui il piano migliora R e 3 in cui peggiora.

Uso:
    python experiments/analyze_plan.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import analyze_dev as ad  # noqa: E402
import analyze_instructions as ai  # noqa: E402
import analyze_pilot as ap  # noqa: E402
import analyze_v5 as av  # noqa: E402
from plan_split import plan_lines, split_plan  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
MODEL_ID = "google/gemma-4-12b-qat"
K = 3
FORMATS = {"plantuml": ("P-G", "dev_v5"), "compact": ("C-G", "dev_c5indent")}
TREATMENT = "dev_plan"
OUT_NAME = "dev_plan_analysis"
GENERATIONS_3B = 2300
# --- regola (voce 126): non si modifica senza una nuova voce in docs/decisions.md ---
ADOPT_R = 0.03
ADOPT_R_FAM = 0.03
MAX_VC_LOSS = 2
MAX_M_LOSS = 0.03
MAX_TRUNCATED = 1
MAX_LATENCY_RATIO = 2.5
EPS = 1e-9
PLAN_CLASS_RE = re.compile(r"^[-*]\s*(?:class\s+)?`?([A-Za-z_][A-Za-z0-9_]*)`?\s*:", re.I)


def adopt(base: dict, treat: dict, truncated: int, latency_ratio: float) -> dict:
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    dr, drf = z(treat["R"]) - z(base["R"]), z(treat["R_fam"]) - z(base["R_fam"])
    dvc, dm = treat["Vc"] - base["Vc"], z(treat["M1"]) - z(base["M1"])
    gain = dr >= ADOPT_R - EPS or drf >= ADOPT_R_FAM - EPS
    ok = (gain and dvc >= -MAX_VC_LOSS and dm >= -MAX_M_LOSS - EPS and truncated <= MAX_TRUNCATED
          and latency_ratio <= MAX_LATENCY_RATIO + EPS)
    return {"adopt": ok, "dR": dr, "dR_fam": drf, "dVc": dvc, "dM1": dm, "truncated": truncated,
            "latency_ratio": latency_ratio, "gain": gain}


def plan_classes(plan: str) -> set[str]:
    """Nomi di classe del piano (righe "- Nome: citazione"; le righe "- Relationship ..." si ignorano), normalizzati."""
    out = set()
    for line in plan_lines(plan):
        if re.match(r"^[-*]\s*relationship", line, re.I):
            continue
        m = PLAN_CLASS_RE.match(line)
        if m:
            out.add(ap.norm(m.group(1)))
    return out


def r_call(c: dict) -> float:
    n = len(c["gt"]["edges"])
    return 0.0 if c["v"].level < 3 or not n else ap.compare_relations(c["v"].diagram, c["gt"])["same_type"] / n


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    return {f: {"base": ai.load_run(results, base, name, gt, MODEL_ID, K),
                "plan": ai.load_run(results, TREATMENT, name, gt, MODEL_ID, K)} for f, (name, base) in FORMATS.items()}


def coherence(calls: list[dict]) -> dict:
    in_plan = in_diag = diag_tot = plan_tot = extra = extra_in_plan = 0
    for c in calls:
        if c["v"].level < 3:
            continue
        plan = split_plan(c["raw"]["text"])[0]
        pc, dc, gc = plan_classes(plan), ap.class_names(c["v"].diagram), ap.class_names(c["gt"])
        diag_tot += len(dc)
        plan_tot += len(pc)
        in_plan += len(dc & pc)
        in_diag += len(pc & dc)
        extra += len(dc - gc)
        extra_in_plan += len((dc - gc) & pc)
    return {"diag_in_plan": in_plan / diag_tot if diag_tot else float("nan"),
            "plan_in_diag": in_diag / plan_tot if plan_tot else float("nan"), "extra": extra,
            "extra_in_plan": extra_in_plan}


def report(data: dict) -> tuple[str, dict]:
    res = {"formats": {}, "hours_3b": None}
    L = ["# Insieme di sviluppo — piano breve prima del diagramma (`dev_plan` contro la configurazione di lavoro)", "",
         "SVILUPPO: 20 esercizi di sviluppo, pool unico, bm25 k = 3, Gemma 4 12B QAT, temperatura 0,3, ragionamento "
         "spento. Istruzioni v5plan: PLAN (al più 15 righe) e poi DIAGRAM; metriche SOLO sul diagramma. Regola registrata "
         "PRIMA della run (voce 126), applicata da `experiments/analyze_plan.py`.", "", provenance.provenance_line(), "",
         "## Regola (voce 126)", "",
         "Adottare se (dR >= +0,03 oppure dR_fam >= +0,03) e dVc >= -2 e dM_primaria >= -0,03 e meno di 2 troncamenti "
         "e latenza mediana <= 2,5 × baseline.", ""]
    rows, plan_lat = [], []
    for f, d in data.items():
        pre = [x["excluded"] for x in d.values() if x["excluded"]]
        if pre:
            res["formats"][f] = None
            L.append(f"- **{ad.FORMAT_NAME[f]}: non decidibile** ({'; '.join(pre)})")
            continue
        mb, mt = av.all_metrics(d["base"]["calls"]), av.all_metrics(d["plan"]["calls"])
        bl = statistics.median(c["m"]["latency_s"] for c in d["base"]["calls"])
        tl = [c["m"]["latency_s"] for c in d["plan"]["calls"]]
        plan_lat += tl
        a = adopt(mb, mt, mt["truncated"], statistics.median(tl) / bl)
        res["formats"][f] = a
        missing = sum(c["m"].get("plan_marker_found") is False for c in d["plan"]["calls"])
        L.append(f"- **{ad.FORMAT_NAME[f]}: piano {'ADOTTATO' if a['adopt'] else 'NON adottato'}** (dR {a['dR']:+.3f}, "
                 f"dR_fam {a['dR_fam']:+.3f}, dVc {a['dVc']:+d}, dM_primaria {a['dM1']:+.3f}, troncate {a['truncated']}, "
                 f"latenza {a['latency_ratio']:.2f} × baseline)")
        rows.append((f, mb, mt, missing, d))
    L += ["", "## Metriche (solo diagramma)", "",
          "| formato | istruzioni | V | Vc | J | R | R_fam | M primaria | generalizzazioni invertite | classi in più | "
          "generalizzazioni in più | composizioni in più | troncate | marcatore mancante | token di output (med) | "
          "latenza med (s) |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f, mb, mt, missing, d in rows:
        for lab, m, x, miss in (("v5 (baseline)", mb, d["base"], "—"), ("v5plan", mt, d["plan"], missing)):
            tok = statistics.median(c["m"].get("completion_tokens_server") or 0 for c in x["calls"])
            lat = statistics.median(c["m"]["latency_s"] for c in x["calls"])
            L.append(f"| {ad.FORMAT_NAME[f]} | {lab} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {ad.fmt(m['J'])} | "
                     f"{ad.fmt(m['R'])} | {ad.fmt(m['R_fam'])} | {ad.fmt(m['M1'])} | {m['inv_gen']}/{m['inv_gen_tot']} | "
                     f"{m['extra_cls']} | {m['extra_gen']} | {m['extra_comp']} | {m['truncated']} | {miss} | {tok:.0f} | "
                     f"{lat:.1f} |")
    if rows:
        res["hours_3b"] = h = statistics.median(plan_lat) * GENERATIONS_3B / 3600
        L += ["", f"Stima del Passo 3b con il piano: {GENERATIONS_3B} generazioni × latenza mediana "
              f"{statistics.median(plan_lat):.1f} s ≈ **{h:.1f} ore**.", "", "## Coerenza piano-diagramma (risposte valide)", "",
              "| formato | classi del diagramma presenti nel piano | classi del piano presenti nel diagramma | classi in più "
              "rispetto al GT | di cui già nel piano |", "|---|---|---|---|---|"]
        for f, mb, mt, missing, d in rows:
            co = coherence(d["plan"]["calls"])
            L.append(f"| {ad.FORMAT_NAME[f]} | {co['diag_in_plan']:.0%} | {co['plan_in_diag']:.0%} | {co['extra']} | "
                     f"{co['extra_in_plan']} |")
    for f, mb, mt, missing, d in rows:
        rb, rp = {}, {}
        for c in d["base"]["calls"]:
            rb.setdefault(c["q"], []).append(r_call(c))
        for c in d["plan"]["calls"]:
            rp.setdefault(c["q"], []).append(r_call(c))
        diff = sorted((statistics.mean(rp[q]) - statistics.mean(rb[q]), q) for q in rb if q in rp)
        first = {c["q"]: c for c in sorted(d["plan"]["calls"], key=lambda c: -c["r"])}
        L += ["", f"## Esempi — {ad.FORMAT_NAME[f]} (R medio per esercizio; piano e diagramma della prima ripetizione)", ""]
        for lab, sel in (("migliora", diff[::-1][:3]), ("peggiora", diff[:3])):
            for dd, q in sel:
                plan, diagram, _ = split_plan(first[q]["raw"]["text"])
                dl = diagram.strip().splitlines()
                L += [f"### {lab}: {q} (R {statistics.mean(rb[q]):.2f} → {statistics.mean(rp[q]):.2f}, {dd:+.2f})", "",
                      "```", "PLAN:", plan, "", "DIAGRAM (prime 25 righe):", *dl[:25],
                      *(["…"] if len(dl) > 25 else []), "```", ""]
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
