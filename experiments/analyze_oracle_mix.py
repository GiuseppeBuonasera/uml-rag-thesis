"""
Controllo "piu' esempi insieme" (oracle_mix, docs/decisions.md, voce 164). Scritto e testato PRIMA della run: da qui la
regola (costanti, verdetti) non si modifica senza una nuova voce. SOLO ANALISI.

Due domande, PlantUML, 54 esercizi di validazione, rispetto all'esempio al 50 % da solo (oracle_partial, voce 163):
1. DILUIZIONE: l'esempio al 50 % accompagnato da 2 esempi bm25 (lontani) perde il suo guadagno?
2. SOMMA: due esempi al 50 % con classi complementari valgono piu' di uno solo, fino all'esercizio intero (oracle_self)?
Guadagno = completezza della risposta − media dello stesso esercizio con zero_shot nel 3b (come la voce 163).

REGOLA (voce 164), sulle differenze appaiate per esercizio:
  diluizione: d = guadagno(diluito) − guadagno(50 %): d >= −MARGINE (0,03) → "nessuna diluizione", altrimenti
              "diluizione";
  somma:      guadagno(complemento) >= guadagno(100 %) − MARGINE → "le due meta' si sommano del tutto";
              altrimenti guadagno(complemento) − guadagno(50 %) >= SOMMA_MIN (0,05) → "si sommano in parte";
              altrimenti "non si sommano".
Riportati anche il test di Wilcoxon sulle differenze appaiate (descrittivo) e il dettaglio per livello.

Uso:
    python experiments/analyze_oracle_mix.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "experiments"), str(ROOT / "generation"), str(ROOT / "retrieval"), str(ROOT)]
import analyze_oracle_self as aos  # noqa: E402
import review_report as rr  # noqa: E402
import provenance  # noqa: E402

RESULTS = rr.RESULTS
OUT_NAME = "oracle_mix_analysis"
SPLITS = ("corpus", "testset")
# --- regola (voce 164): non si modifica senza una nuova voce in docs/decisions.md ---
MARGINE = 0.03
SOMMA_MIN = 0.05


def gains(calls: list[dict], base: dict[str, float]) -> dict[str, float]:
    """Esercizio -> guadagno medio delle sue risposte."""
    by_q = defaultdict(list)
    for c in calls:
        by_q[c["q"]].append((aos.response_scores(c)["comp"] or 0.0) - base[c["q"]])
    return {q: st.mean(v) for q, v in by_q.items()}


def verdict_dilution(g_dil: float, g_50: float) -> str:
    return "nessuna diluizione" if g_dil - g_50 >= -MARGINE - 1e-9 else "diluizione"


def verdict_sum(g_comp: float, g_50: float, g_100: float) -> str:
    if g_comp >= g_100 - MARGINE - 1e-9:
        return "le due meta' si sommano del tutto"
    if g_comp - g_50 >= SOMMA_MIN - 1e-9:
        return "le due meta' si sommano in parte"
    return "le due meta' non si sommano"


def load_all(results: Path) -> dict:
    import corpus_loader as cl
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates() + cl.load_queries()}
    out, missing = {}, []

    def runs(prefix):
        calls = []
        for s in SPLITS:
            d = results / prefix.format(s=s)
            if not (d / "manifest.jsonl").exists():
                missing.append(d.name)
                continue
            calls += rr.load_run(d, {}, gt)
        return calls
    zs = []
    for s in SPLITS:
        d = results / f"passo3b__P-{s}-G26"
        if (d / "manifest.jsonl").exists():
            zs += rr.load_run(d, {"cond": {"zero_shot"}}, gt)
        else:
            missing.append(d.name)
    by_q = defaultdict(list)
    for c in zs:
        by_q[c["q"]].append(aos.response_scores(c)["comp"] or 0.0)
    base = {q: st.mean(v) for q, v in by_q.items()}
    for key, prefix in (("50", "oracle_partial__P-{s}-50"), ("100", "oracle_self__P-{s}-libero"),
                        ("diluito", "oracle_mix__P-{s}-diluito"), ("complemento", "oracle_mix__P-{s}-complemento")):
        out[key] = gains(runs(prefix), base) if base else {}
    out["missing"] = missing
    return out


def paired(a: dict[str, float], b: dict[str, float]) -> tuple[float, float | None, int]:
    from scipy.stats import wilcoxon
    qs = sorted(set(a) & set(b))
    d = [a[q] - b[q] for q in qs]
    p = wilcoxon(d).pvalue if any(d) else None
    return st.mean(d), p, len(qs)


def report(data: dict) -> tuple[str, dict]:
    m = {k: st.mean(v.values()) for k, v in data.items() if k != "missing" and v}
    dil = verdict_dilution(m["diluito"], m["50"])
    som = verdict_sum(m["complemento"], m["50"], m["100"])
    d1, p1, n1 = paired(data["diluito"], data["50"])
    d2, p2, n2 = paired(data["complemento"], data["50"])
    d3, p3, n3 = paired(data["complemento"], data["100"])
    pf = lambda p: "—" if p is None else f"{p:.3f}"  # noqa: E731
    L = ["# Controllo \"piu' esempi insieme\" (oracle_mix) — SOLO ANALISI", "",
         "PlantUML, 54 esercizi di validazione, Gemma 4 26B A4B QAT, configurazione del 3b, blocco esempi libero. Regola "
         "registrata PRIMA della run (voce 164), applicata da `experiments/analyze_oracle_mix.py`.", "",
         provenance.provenance_line(), "", "## Guadagno di completezza su zero_shot (media per esercizio)", "",
         "| esempi nel prompt | guadagno |", "|---|---|",
         f"| soluzione al 50 % da sola (oracle_partial) | {m['50']:+.3f} |",
         f"| 2 esempi bm25 + soluzione al 50 % (diluito) | {m['diluito']:+.3f} |",
         f"| soluzione al 50 % + meta' complementare (complemento) | {m['complemento']:+.3f} |",
         f"| esercizio intero (oracle_self, libero) | {m['100']:+.3f} |", "",
         "## Esito (regola della voce 164)", "",
         f"- **Diluizione: {dil}** (diluito − 50 % = {d1:+.3f}, Wilcoxon p {pf(p1)}, {n1} esercizi; margine {MARGINE})",
         f"- **Somma: {som}** (complemento − 50 % = {d2:+.3f}, p {pf(p2)}; complemento − 100 % = {d3:+.3f}, p {pf(p3)})", "",
         "Guadagno = completezza (elementi del riferimento ritrovati / elementi del riferimento) − media dello stesso "
         "esercizio con zero_shot nel 3b."]
    return "\n".join(L) + "\n", {"means": m, "diluizione": dil, "somma": som}


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    data = load_all(results)
    if data["missing"]:
        print(f"run assenti: {data['missing']}: nessuna analisi scritta")
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
