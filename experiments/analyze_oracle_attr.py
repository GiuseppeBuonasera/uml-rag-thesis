"""
Controllo "esempi senza attributi" (docs/decisions.md, voce 167). Scritto e testato PRIMA della run: da qui la regola
(costanti, verdetti) non si modifica senza una nuova voce. SOLO ANALISI.

Due varianti, 54 esercizi di validazione, PlantUML e compatto, 1 ripetizione:
- A (oracle_attr_self): l'esercizio stesso con classi e relazioni perfette e NESSUN attributo. Domanda: quanta parte
  degli attributi ritrovati viene dal testo? Confronto con oracle_self libero (voce 162, attributi presenti).
- B (oracle_attr_bm25): gli stessi 3 esempi di bm25 k3 del 3b, senza attributi. Domanda CAUSALE: la forma vuota degli
  esempi causa gli scheletri? Confronto con bm25 k3 del 3b (stessi esercizi, stessi esempi, media delle 3 ripetizioni).
Scheletro = risposta valida senza nessun attributo per un esercizio il cui GT ne ha (analyze_v5b.is_skeleton);
risposte non valide escluse dal conteggio degli scheletri, contate a parte.

REGOLA (voce 167), variante B, per formato, sulla quota di scheletri per esercizio (media delle risposte):
  d = scheletri(B) − scheletri(3b bm25 k3);
  d >= EFFETTO (0,10) e Wilcoxon appaiato p < 0,05 → "la forma vuota degli esempi CAUSA gli scheletri";
  d <  NULLO (0,05)                                → "nessun effetto causale rilevabile";
  altrimenti                                       → "effetto debole".
Variante A (descrittiva): quota dal testo = recall degli attributi (A) / recall degli attributi (oracle_self libero).

Uso:
    python experiments/analyze_oracle_attr.py [--results-dir data/results/generation]
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
import analyze_v5b as v5b  # noqa: E402  (is_skeleton, n_attrs)
import review_report as rr  # noqa: E402
from evaluation import element_metrics as el  # noqa: E402
import provenance  # noqa: E402

RESULTS = rr.RESULTS
OUT_NAME = "oracle_attr_analysis"
FORMATS = {"P": "PlantUML", "C": "JSON compatto"}
SPLITS = ("corpus", "testset")
# --- regola (voce 167): non si modifica senza una nuova voce in docs/decisions.md ---
EFFETTO = 0.10
NULLO = 0.05
ALPHA = 0.05


def per_exercise(calls: list[dict]) -> dict[str, dict]:
    """Esercizio -> medie: scheletro (sulle risposte valide con GT dotato di attributi), recall / precision / F1 degli
    attributi, completezza (non valide = 0)."""
    acc = defaultdict(lambda: defaultdict(list))
    for c in calls:
        q = c["q"]
        if c["v"].level >= 3 and v5b.n_attrs(c["gt"]) > 0:
            acc[q]["sk"].append(int(v5b.is_skeleton(c)))
        s = el.evaluate_call(c)["relaxed"]["scores"]["attributes"]
        for k in ("P", "R", "F1"):
            if s[k] is not None:
                acc[q]["attr" + k].append(s[k])
        acc[q]["comp"].append(aos.response_scores(c)["comp"] or 0.0)
        acc[q]["invalid"].append(int(c["v"].level < 3))
    return {q: {k: st.mean(v) for k, v in d.items() if v} for q, d in acc.items()}


def mean_of(per: dict[str, dict], key: str) -> float | None:
    vals = [d[key] for d in per.values() if key in d]
    return st.mean(vals) if vals else None


def verdict_b(d: float, p: float | None) -> str:
    if d >= EFFETTO - 1e-9 and p is not None and p < ALPHA:
        return "la forma vuota degli esempi CAUSA gli scheletri"
    if d < NULLO - 1e-9:
        return "nessun effetto causale rilevabile"
    return "effetto debole"


def load_all(results: Path) -> dict:
    import corpus_loader as cl
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates() + cl.load_queries()}
    out, missing = {}, []

    def runs(prefix, filters=None):
        calls = []
        for s in SPLITS:
            d = results / prefix.format(s=s)
            if not (d / "manifest.jsonl").exists():
                missing.append(d.name)
                continue
            calls += rr.load_run(d, filters or {}, gt)
        return calls
    for f in FORMATS:
        out[(f, "A")] = per_exercise(runs(f"oracle_attr_self__{f}-{{s}}"))
        out[(f, "B")] = per_exercise(runs(f"oracle_attr_bm25__{f}-{{s}}"))
        out[(f, "oracle_self")] = per_exercise(runs(f"oracle_self__{f}-{{s}}-libero"))
        out[(f, "3b bm25")] = per_exercise(runs(f"passo3b__{f}-{{s}}-G26", {"cond": {"bm25"}, "k": {"3"}}))
    out["missing"] = missing
    return out


def paired(a: dict, b: dict, key: str) -> tuple[float, float | None, int]:
    from scipy.stats import wilcoxon
    qs = sorted(q for q in set(a) & set(b) if key in a[q] and key in b[q])
    d = [a[q][key] - b[q][key] for q in qs]
    p = wilcoxon(d).pvalue if any(d) else None
    return (st.mean(d) if d else 0.0), p, len(qs)


def report(data: dict) -> tuple[str, dict]:
    res = {}
    fx = lambda x, nd=3: "—" if x is None else f"{x:.{nd}f}"  # noqa: E731
    L = ["# Controllo \"esempi senza attributi\" — SOLO ANALISI", "",
         "54 esercizi di validazione, Gemma 4 26B A4B QAT, configurazione del 3b, 1 ripetizione. A = esercizio stesso con "
         "classi e relazioni perfette e nessun attributo (blocco libero); B = gli esempi bm25 k3 del 3b senza attributi "
         "(blocco standard). Regola registrata PRIMA della run (voce 167), applicata da `experiments/analyze_oracle_attr.py`.",
         "", provenance.provenance_line(), "", "## Esito B (causa degli scheletri)", ""]
    for f, fname in FORMATS.items():
        d, p, n = paired(data[(f, "B")], data[(f, "3b bm25")], "sk")
        v = verdict_b(d, p)
        res[f] = {"B": v, "d": d, "p": p}
        L.append(f"- **{fname}: {v}** (scheletri B {fx(mean_of(data[(f, 'B')], 'sk'), 2)} contro 3b bm25 k3 "
                 f"{fx(mean_of(data[(f, '3b bm25')], 'sk'), 2)}; d = {d:+.3f}, Wilcoxon p {fx(p)}, {n} esercizi)")
    L += ["", "## Metriche (media per esercizio)", "",
          "| formato | esempi | scheletri | attributi R | attributi P | attributi F1 | completezza | non valide |",
          "|---|---|---|---|---|---|---|---|"]
    names = {"A": "A: esercizio stesso senza attributi", "oracle_self": "esercizio stesso con attributi",
             "B": "B: bm25 k3 senza attributi", "3b bm25": "bm25 k3 del 3b (con attributi)"}
    for f, fname in FORMATS.items():
        for k in ("A", "oracle_self", "B", "3b bm25"):
            x = data[(f, k)]
            L.append(f"| {fname} | {names[k]} | {fx(mean_of(x, 'sk'), 2)} | {fx(mean_of(x, 'attrR'))} | "
                     f"{fx(mean_of(x, 'attrP'))} | {fx(mean_of(x, 'attrF1'))} | {fx(mean_of(x, 'comp'))} | "
                     f"{fx(mean_of(x, 'invalid'), 2)} |")
        ra, ro = mean_of(data[(f, "A")], "attrR"), mean_of(data[(f, "oracle_self")], "attrR")
        res[f]["quota_testo"] = ra / ro if ra is not None and ro else None
    L += ["", "## Variante A: quanta parte degli attributi viene dal testo", ""]
    for f, fname in FORMATS.items():
        L.append(f"- {fname}: recall degli attributi senza attributi nell'esempio / con attributi = "
                 f"{fx(res[f]['quota_testo'], 2)}")
    L += ["", "Scheletro = risposta valida senza nessun attributo per un GT che ne ha (non valide escluse, riportate a "
          "parte); completezza come la voce 162."]
    return "\n".join(L) + "\n", res


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
