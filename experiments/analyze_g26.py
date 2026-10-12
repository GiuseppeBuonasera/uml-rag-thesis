"""
Controllo di Gemma 4 26B A4B QAT sull'insieme di sviluppo (docs/decisions.md, voci 131-132). Scritto e testato PRIMA
della run (sulle sole baseline): da qui la regola (costanti, adopt, outcome) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Per formato confronta la BASELINE di Gemma 4 12B QAT (configurazione di lavoro:
dev_v5__P-G, PlantUML v5; dev_c5indent__C-G, compatto v5 con esempi indentati) con il 26B nella STESSA configurazione
(dev_g26__P-G / __C-G: stessi 20 esercizi, stessi esempi, stesse ripetizioni, `thinking: none`). Metriche di
evaluation/metrics.py (via experiments/analyze_v5.all_metrics), su TUTTE le risposte (0 per le non valide).

REGOLA (voce 132), per formato, delta = 26B - 12B su 40 risposte:
  il 26B diventa il modello del Passo 3b se, in ENTRAMBI i formati, dR >= -0,03 E dVc >= -2 E dM_primaria >= -0,03 E
  meno di 2 troncamenti, E la stima delle ore del 3b e' <= 30.
  Stima: per formato, latenza mediana del 26B in questa run x 1.131 generazioni del 3b di quel formato, sommate
  (prudente: zero_shot e static hanno prompt piu' corti di bm25 k = 3).
  Se passa in un solo formato: decide l'utente. Controllo preliminare: run complete (40), senza ragionamento, del
  modello atteso; altrimenti quel formato non si decide.
Riportati fuori regola: J, R_fam, generalizzazioni invertite, classi / generalizzazioni / composizioni in piu', token di
output e latenze.

Uso:
    python experiments/analyze_g26.py [--results-dir data/results/generation]
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
import analyze_v5 as av  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
MODEL_12 = "google/gemma-4-12b-qat"
MODEL_26 = "google/gemma-4-26b-a4b-qat"
K = 3
FORMATS = {"plantuml": ("P-G", "dev_v5"), "compact": ("C-G", "dev_c5indent")}
TREATMENT = "dev_g26"
OUT_NAME = "dev_g26_analysis"
GENERATIONS_3B_PER_FORMAT = 1131  # voce 132: 34 x 7 x 3 - 3 (static di AirTravel) + 20 x 7 x 3
# --- regola (voce 132): non si modifica senza una nuova voce in docs/decisions.md ---
MAX_R_LOSS = 0.03
MAX_VC_LOSS = 2
MAX_M_LOSS = 0.03
MAX_TRUNCATED = 1
MAX_HOURS_3B = 30.0
EPS = 1e-9


def keeps(base: dict, treat: dict, truncated: int) -> dict:
    """Non inferiorita' del 26B in un formato (voce 132)."""
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    dr, dm, dvc = z(treat["R"]) - z(base["R"]), z(treat["M1"]) - z(base["M1"]), treat["Vc"] - base["Vc"]
    ok = dr >= -MAX_R_LOSS - EPS and dvc >= -MAX_VC_LOSS and dm >= -MAX_M_LOSS - EPS and truncated <= MAX_TRUNCATED
    return {"ok": ok, "dR": dr, "dVc": dvc, "dM1": dm, "truncated": truncated,
            "dR_fam": z(treat["R_fam"]) - z(base["R_fam"]), "dJ": z(treat["J"]) - z(base["J"])}


def hours_3b(latency_by_format: dict[str, float]) -> float:
    return sum(lat * GENERATIONS_3B_PER_FORMAT for lat in latency_by_format.values()) / 3600


def outcome(formats: dict[str, dict | None], hours: float | None) -> str:
    """formats: formato -> esito di keeps, None se il formato non e' decidibile."""
    if any(v is None for v in formats.values()) or hours is None:
        return "STOP: controllo preliminare non superato (run assente, incompleta o con ragionamento)"
    passed = [f for f, v in formats.items() if v["ok"]]
    if hours > MAX_HOURS_3B + EPS:
        return f"26B NON adottato: stima del 3b {hours:.1f} ore > {MAX_HOURS_3B:g}"
    if len(passed) == len(formats):
        return "26B ADOTTATO come modello del Passo 3b (non inferiore in entrambi i formati, stima entro le 30 ore)"
    if passed:
        return f"passa solo in {', '.join(ad.FORMAT_NAME[f] for f in passed)}: DECIDE L'UTENTE"
    return "26B NON adottato: inferiore in entrambi i formati"


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    return {f: {"base": ai.load_run(results, base, name, gt, MODEL_12, K),
                "g26": ai.load_run(results, TREATMENT, name, gt, MODEL_26, K)} for f, (name, base) in FORMATS.items()}


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def report(data: dict) -> tuple[str, dict]:
    res = {"formats": {}, "hours_3b": None, "outcome": None}
    L = ["# Insieme di sviluppo — Gemma 4 26B A4B QAT contro Gemma 4 12B QAT (configurazione di lavoro)", "",
         "SVILUPPO: 20 esercizi, pool unico, bm25 k = 3 (file congelato), temperatura 0,3, ragionamento spento, 2 "
         "ripetizioni. Baseline 12B: dev_v5__P-G (PlantUML v5) e dev_c5indent__C-G (compatto v5 + esempi indentati). "
         "Regola registrata PRIMA della run (voce 132), applicata da `experiments/analyze_g26.py`.", "",
         provenance.provenance_line(), "", "## Regola (voce 132)", "",
         "Il 26B diventa il modello del 3b se, in entrambi i formati, dR >= -0,03 e dVc >= -2 e dM_primaria >= -0,03 e "
         "meno di 2 troncamenti, e la stima del 3b e' <= 30 ore (latenza mediana del 26B × 1.131 generazioni per "
         "formato).", ""]
    lat, rows = {}, []
    for f, d in data.items():
        pre = [x["excluded"] for x in d.values() if x["excluded"]]
        if pre:
            res["formats"][f] = None
            L.append(f"- **{ad.FORMAT_NAME[f]}: non decidibile** ({'; '.join(pre)})")
            continue
        mb, mt = av.all_metrics(d["base"]["calls"]), av.all_metrics(d["g26"]["calls"])
        k = keeps(mb, mt, mt["truncated"])
        res["formats"][f] = k
        lat[f] = statistics.median(c["m"]["latency_s"] for c in d["g26"]["calls"])
        L.append(f"- **{ad.FORMAT_NAME[f]}: {'non inferiore' if k['ok'] else 'INFERIORE'}** (dR {k['dR']:+.3f}, dVc "
                 f"{k['dVc']:+d}, dM_primaria {k['dM1']:+.3f}, troncate {k['truncated']})")
        rows.append((f, mb, mt, d))
    if len(lat) == len(data):
        res["hours_3b"] = hours_3b(lat)
        L.append(f"- Stima del 3b con il 26B: **{res['hours_3b']:.1f} ore** (soglia {MAX_HOURS_3B:g})")
    res["outcome"] = outcome(res["formats"], res["hours_3b"])
    L += ["", f"**Esito: {res['outcome']}**", "", "## Metriche (40 risposte per cella)", "",
          "| formato | modello | V | Vc | J | R | R_fam | M primaria | generalizzazioni invertite | classi in più | "
          "generalizzazioni in più | composizioni in più | troncate | token di output (med) | latenza (med, s) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f, mb, mt, d in rows:
        for label, m, calls in (("12B", mb, d["base"]["calls"]), ("26B", mt, d["g26"]["calls"])):
            tok = statistics.median(c["m"].get("completion_tokens_server") or 0 for c in calls)
            la = statistics.median(c["m"]["latency_s"] for c in calls)
            L.append(f"| {ad.FORMAT_NAME[f]} | {label} | {m['V']} | {m['Vc']} | {fmt(m['J'])} | {fmt(m['R'])} | "
                     f"{fmt(m['R_fam'])} | {fmt(m['M1'])} | {m['inv_gen']} | {m['extra_cls']} | {m['extra_gen']} | "
                     f"{m['extra_comp']} | {m['truncated']} | {tok:g} | {la:.1f} |")
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
