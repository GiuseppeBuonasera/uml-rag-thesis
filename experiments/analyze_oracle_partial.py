"""
Controllo "esempio parzialmente simile" (oracle_partial, docs/decisions.md, voce 163). Scritto e testato PRIMA della
run: da qui la regola (costanti, threshold) non si modifica senza una nuova voce. SOLO ANALISI.

Domanda: quanto deve essere simile un esempio perche' serva? Curva "somiglianza dell'esempio -> guadagno di completezza
rispetto a zero_shot", PlantUML, 54 esercizi di validazione:
- livelli 25 / 50 / 75 % (oracle_partial: la soluzione dell'esercizio con quella frazione delle classi);
- livello 100 % = oracle_self, variante libera (voce 162);
- riferimento = esempi del 3b (bm25, hybrid, random, static), raggruppati per somiglianza del miglior esempio.
Somiglianza = Jt (Jaccard dei token dei nomi di classe) tra la soluzione dell'esempio e quella dell'esercizio.
Completezza = come analyze_oracle_self.response_scores (elementi ritrovati / elementi del riferimento; non valide = 0).
Guadagno = completezza della risposta − media della completezza dello stesso esercizio con zero_shot nel 3b.

REGOLA (voce 163): SOGLIA DI UTILITA' = il livello piu' basso (25, 50, 75, 100) il cui guadagno medio per esercizio
e' >= GUADAGNO_UTILE (0,05, sopra la differenza minima rilevabile di circa 0,03 sui 54); si riporta con la sua
somiglianza media misurata. Nessun livello sopra la soglia -> "nemmeno l'esempio quasi identico basta".

Uso:
    python experiments/analyze_oracle_partial.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "experiments"), str(ROOT / "generation"), str(ROOT / "retrieval"), str(ROOT)]
import analyze_oracle_self as aos  # noqa: E402  (response_scores: stessa completezza della voce 162)
import review_report as rr  # noqa: E402
import provenance  # noqa: E402

RESULTS = rr.RESULTS
OUT_NAME = "oracle_partial_analysis"
SPLITS = ("corpus", "testset")
LEVELS = (25, 50, 75)
BINS = ((0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.45))
# --- regola (voce 163): non si modifica senza una nuova voce in docs/decisions.md ---
GUADAGNO_UTILE = 0.05


def jt(a: dict, b: dict) -> float:
    from relevance import class_tokens
    x, y = class_tokens(a), class_tokens(b)
    return len(x & y) / len(x | y) if x | y else 0.0


def per_exercise_gain(calls: list[dict], base: dict[str, float]) -> float | None:
    """Guadagno medio per esercizio (prima la media delle risposte dell'esercizio, poi sugli esercizi)."""
    by_q = defaultdict(list)
    for c in calls:
        by_q[c["q"]].append((aos.response_scores(c)["comp"] or 0.0) - base[c["q"]])
    return st.mean(st.mean(v) for v in by_q.values()) if by_q else None


def threshold(points: list[tuple[int, float | None, float | None]]) -> tuple[int | None, float | None]:
    """points = (livello, somiglianza media, guadagno); il livello piu' basso con guadagno >= GUADAGNO_UTILE."""
    for lvl, sim, gain in sorted(points):
        if gain is not None and gain >= GUADAGNO_UTILE - 1e-9:
            return lvl, sim
    return None, None


def load_all(results: Path) -> dict:
    import corpus_loader as cl
    from prompt_builder import PromptBuilder, PromptSpec
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates() + cl.load_queries()}
    b = PromptBuilder(retrieval_source="frozen")
    queries = {x["id"]: x for x in cl.load_candidates() + cl.load_queries()}
    out = {"missing": []}
    zs = [x for s in SPLITS for x in rr.load_run(results / f"passo3b__P-{s}-G26", {"cond": {"zero_shot"}}, gt)] \
        if (results / "passo3b__P-corpus-G26" / "manifest.jsonl").exists() else []
    by_q = defaultdict(list)
    for c in zs:
        by_q[c["q"]].append(aos.response_scores(c)["comp"] or 0.0)
    out["base"] = {q: st.mean(v) for q, v in by_q.items()}
    for lvl in LEVELS:
        calls = []
        for s in SPLITS:
            d = results / f"oracle_partial__P-{s}-{lvl}"
            if not (d / "manifest.jsonl").exists():
                out["missing"].append(d.name)
                continue
            calls += rr.load_run(d, {}, gt)
        spec = PromptSpec(condition="oracle_partial", k=1, output_format="plantuml", instructions_version="v5",
                          example_view="clean_v1", examples_block="libero", oracle_keep=lvl / 100)
        sims = [jt(b.select(queries[q], spec)[0]["diagram_apollon_json"], gt[q]) for q in {c["q"] for c in calls}]
        out[lvl] = {"calls": calls, "sim": st.mean(sims) if sims else None}
    full = []
    for s in SPLITS:
        d = results / f"oracle_self__P-{s}-libero"
        if not (d / "manifest.jsonl").exists():
            out["missing"].append(d.name)
            continue
        full += rr.load_run(d, {}, gt)
    out[100] = {"calls": full, "sim": 1.0}
    ref = [x for s in SPLITS for x in rr.load_run(results / f"passo3b__P-{s}-G26", {}, gt)] \
        if (results / "passo3b__P-corpus-G26" / "manifest.jsonl").exists() else []
    pts = []
    for c in ref:
        if c["m"]["example_ids"] and c["q"] in out["base"]:
            sim = max(jt(gt[e], gt[c["q"]]) if e in gt else 0.0 for e in c["m"]["example_ids"])
            pts.append((sim, (aos.response_scores(c)["comp"] or 0.0) - out["base"][c["q"]]))
    out["ref"] = pts
    return out


def report(data: dict) -> tuple[str, dict]:
    res = {}
    L = ["# Controllo \"esempio parzialmente simile\" (oracle_partial) — SOLO ANALISI", "",
         "PlantUML, 54 esercizi di validazione, Gemma 4 26B A4B QAT, configurazione del 3b, blocco esempi libero. Esempio = "
         "la traccia vera dell'esercizio con la soluzione ridotta al 25 / 50 / 75 % delle classi; 100 % = oracle_self. "
         "Regola registrata PRIMA della run (voce 163), applicata da `experiments/analyze_oracle_partial.py`.", "",
         provenance.provenance_line(), "", "## Curva: somiglianza dell'esempio → guadagno di completezza su zero_shot", "",
         "| esempio | somiglianza (Jt) | risposte | guadagno medio |", "|---|---|---|---|"]
    for lo, hi in BINS:
        g = [d for j, d in data["ref"] if lo <= j < hi]
        if g:
            L.append(f"| 3b, miglior esempio con Jt {lo:.2f}-{hi:.2f} | {lo:.2f}-{hi:.2f} | {len(g)} | {st.mean(g):+.3f} |")
    points = []
    for lvl in (*LEVELS, 100):
        d = data[lvl]
        gain = per_exercise_gain(d["calls"], data["base"]) if d["calls"] else None
        points.append((lvl, d["sim"], gain))
        name = "esercizio stesso (oracle_self)" if lvl == 100 else f"soluzione al {lvl}% delle classi"
        L.append(f"| {name} | {aos.fmt(d['sim'], 2)} | {len(d['calls'])} | "
                 f"{'—' if gain is None else f'{gain:+.3f}'} |")
    lvl, sim = threshold(points)
    res["points"], res["threshold"] = points, (lvl, sim)
    res["outcome"] = (f"soglia di utilita' al livello {lvl}% (somiglianza media {sim:.2f}): sotto, l'esempio non porta un "
                      f"guadagno di almeno {GUADAGNO_UTILE}" if lvl is not None
                      else "nemmeno l'esempio quasi identico porta un guadagno di almeno 0,05")
    L += ["", f"**Esito (regola della voce 163): {res['outcome']}.**", "",
          "Guadagno = completezza della risposta − media dello stesso esercizio con zero_shot nel 3b; completezza = "
          "elementi del riferimento ritrovati / elementi del riferimento (classi + attributi + relazioni + "
          "generalizzazioni, abbinamento rilassato). Le fasce del 3b sono descrittive (esempi reali, non controllati)."]
    return "\n".join(L) + "\n", res


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    data = load_all(results)
    if data["missing"] or not data["base"]:
        print(f"run assenti: {data['missing'] or ['passo3b']}: nessuna analisi scritta")
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
