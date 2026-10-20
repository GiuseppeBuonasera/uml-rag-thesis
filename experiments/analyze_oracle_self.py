"""
Controllo "esercizio stesso come esempio" (oracle_self, docs/decisions.md, voce 162). Scritto e testato PRIMA della run:
da qui la regola (costanti, outcome) non si modifica senza una nuova voce. SOLO ANALISI: i risultati non entrano nel
3b ne' nei dati dei relatori.

Domanda: con un esempio PERFETTO (l'esercizio stesso con la sua soluzione) il modello ne riprende il contenuto? Se si',
il retrieval del 3b non aiuta perche' il pool non contiene esempi abbastanza vicini (limite del corpus); se no, il
modello riscrive comunque dal testo e gli esempi servono solo per la forma (limite del modello o delle istruzioni).

Metriche (evaluation/element_metrics.py, abbinamento rilassato), per risposta e poi media per esercizio:
- completezza = elementi del riferimento ritrovati / elementi del riferimento (classi + attributi + relazioni +
  generalizzazioni, sommati: la versione nostra della completeness dei relatori); risposte non valide = 0;
- precision complessiva (stessi elementi), F1 per tipologia, Jaccard dei nomi di classe;
- copia quasi esatta = completezza >= 0,90 E precision >= 0,90.
Riferimento: le stesse metriche sul 3b (bm25 k3 e zero_shot, media delle 3 ripetizioni).

REGOLA DI LETTURA (voce 162), sulla variante "libero" (senza "do not copy their classes"), per formato:
  completezza media >= SOGLIA_USA (0,80)  -> "il modello SA usare il contenuto di un esempio perfetto": il limite del
                                             retrieval nel 3b e' il corpus (esempi non abbastanza vicini);
  completezza media <  SOGLIA_NON_USA (0,60) -> "il modello NON usa il contenuto nemmeno di un esempio perfetto":
                                             il limite e' il modello o le istruzioni;
  in mezzo                                  -> "uso parziale".
Effetto della frase sul copiare = variante libero − standard (descrittivo).

Uso:
    python experiments/analyze_oracle_self.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "experiments"), str(ROOT / "generation"), str(ROOT / "retrieval"), str(ROOT)]
import review_report as rr  # noqa: E402
from evaluation import element_metrics as el  # noqa: E402
import provenance  # noqa: E402

RESULTS = rr.RESULTS
OUT_NAME = "oracle_self_analysis"
FORMATS = {"P": "PlantUML", "C": "JSON compatto"}
SPLITS = ("corpus", "testset")
VARIANTS = ("standard", "libero")
TYPES = ("classes", "attributes", "relations", "generalizations")
# --- regola (voce 162): non si modifica senza una nuova voce in docs/decisions.md ---
SOGLIA_USA = 0.80
SOGLIA_NON_USA = 0.60
COPIA = 0.90


def response_scores(c: dict) -> dict:
    """Completezza, precision, F1 per tipologia e Jaccard dei nomi di una risposta (non valida = diagramma vuoto)."""
    e = el.evaluate_call(c)["relaxed"]
    tp = sum(e["counts"][t]["tp"] for t in TYPES)
    fn = sum(e["counts"][t]["fn"] for t in TYPES)
    fp = sum(e["counts"][t]["fp"] for t in TYPES)
    comp = tp / (tp + fn) if tp + fn else None
    prec = tp / (tp + fp) if tp + fp else None
    out = {"comp": comp, "prec": prec, "copia": int(bool(comp is not None and prec is not None
                                                          and comp >= COPIA and prec >= COPIA))}
    for t in TYPES:
        out[f"F1_{t}"] = e["scores"][t]["F1"]
    r = el.elements(c["v"].diagram if c["v"].level >= 3 else None)["classes"].values()
    g = el.elements(c["gt"])["classes"].values()
    rn, gn = {el.norm(x) for x in r if el.norm(x)}, {el.norm(x) for x in g if el.norm(x)}
    out["J"] = len(rn & gn) / len(rn | gn) if rn | gn else None
    return out


def summarize(calls: list[dict]) -> dict:
    """Medie per esercizio (prima sulle ripetizioni), poi sugli esercizi; valori non definiti esclusi."""
    by_q = defaultdict(lambda: defaultdict(list))
    for c in calls:
        for k, v in response_scores(c).items():
            if v is not None:
                by_q[c["q"]][k].append(v)
    keys = {k for d in by_q.values() for k in d}
    res = {k: st.mean(st.mean(d[k]) for d in by_q.values() if d.get(k)) for k in keys}
    res["n_esercizi"] = len(by_q)
    res["n_risposte"] = len(calls)
    res["non_valide"] = sum(c["v"].level < 3 for c in calls)
    return res


def outcome(comp: float | None) -> str:
    if comp is None:
        return "STOP: run assente o incompleta"
    if comp >= SOGLIA_USA:
        return "il modello SA usare il contenuto di un esempio perfetto (limite del retrieval: il corpus)"
    if comp < SOGLIA_NON_USA:
        return "il modello NON usa il contenuto nemmeno di un esempio perfetto (limite: modello o istruzioni)"
    return "uso PARZIALE del contenuto di un esempio perfetto"


def load_all(results: Path) -> dict:
    import corpus_loader as cl
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates() + cl.load_queries()}
    data = {}
    for f in FORMATS:
        for v in VARIANTS:
            calls, missing = [], []
            for s in SPLITS:
                d = results / f"oracle_self__{f}-{s}-{v}"
                if not (d / "manifest.jsonl").exists():
                    missing.append(d.name)
                    continue
                calls += rr.load_run(d, {}, gt)
            data[(f, v)] = {"calls": calls, "missing": missing}
        for cond, k in (("bm25", "3"), ("zero_shot", "0")):
            calls = []
            for s in SPLITS:
                d = results / f"passo3b__{f}-{s}-G26"
                if (d / "manifest.jsonl").exists():
                    calls += rr.load_run(d, {"cond": {cond}, "k": {k}}, gt)
            data[(f, f"3b {cond}")] = {"calls": calls, "missing": [] if calls else ["passo3b"]}
    return data


def fmt(x, nd=3) -> str:
    return "—" if x is None else f"{x:.{nd}f}"


def report(data: dict) -> tuple[str, dict]:
    res = {"formats": {}}
    L = ["# Controllo \"esercizio stesso come esempio\" (oracle_self) — SOLO ANALISI", "",
         "54 esercizi di validazione, Gemma 4 26B A4B QAT, configurazione del 3b; unico esempio = l'esercizio stesso con la "
         "sua soluzione. Varianti: `standard` (\"do not copy their classes\" nel blocco esempi) e `libero` (senza). Regola di "
         "lettura registrata PRIMA della run (voce 162), applicata da `experiments/analyze_oracle_self.py`.", "",
         provenance.provenance_line(), "", "## Esito (regola della voce 162, variante libero)", ""]
    rows = []
    for f, fname in FORMATS.items():
        s = {}
        for v in (*VARIANTS, "3b bm25", "3b zero_shot"):
            d = data[(f, v)]
            s[v] = summarize(d["calls"]) if d["calls"] and not d["missing"] else None
        lib = s["libero"]
        complete = lib is not None and lib["n_esercizi"] == 54
        res["formats"][f] = {"outcome": outcome(lib["comp"] if complete else None), "scores": s}
        L.append(f"- **{fname}: {res['formats'][f]['outcome']}** (completezza libero "
                 f"{fmt(lib['comp'] if lib else None)}, standard {fmt(s['standard']['comp'] if s['standard'] else None)})")
        rows.append((fname, s))
    L += ["", "## Metriche (media per esercizio)", "",
          "| formato | prompt | completezza | precision | copia quasi esatta | J nomi | F1 classi | F1 attributi | F1 "
          "relazioni | F1 generalizz. | non valide |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for fname, s in rows:
        for v in ("libero", "standard", "3b bm25", "3b zero_shot"):
            x = s[v]
            if x is None:
                L.append(f"| {fname} | {v} | — | — | — | — | — | — | — | — | — |")
                continue
            L.append(f"| {fname} | {v} | {fmt(x.get('comp'))} | {fmt(x.get('prec'))} | {100 * x.get('copia', 0):.0f}% | "
                     f"{fmt(x.get('J'))} | {fmt(x.get('F1_classes'))} | {fmt(x.get('F1_attributes'))} | "
                     f"{fmt(x.get('F1_relations'))} | {fmt(x.get('F1_generalizations'))} | {x['non_valide']} |")
    L += ["", "Effetto della frase \"do not copy their classes\" = libero − standard; riferimento = 3b, stessi esercizi, "
          "media delle 3 ripetizioni. Completezza = elementi del riferimento ritrovati (classi + attributi + relazioni + "
          "generalizzazioni) / elementi del riferimento; copia quasi esatta = completezza e precision >= 0,90."]
    return "\n".join(L) + "\n", res


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    data = load_all(results)
    if any(data[(f, v)]["missing"] for f in FORMATS for v in VARIANTS):
        miss = [m for f in FORMATS for v in VARIANTS for m in data[(f, v)]["missing"]]
        print(f"run assenti: {miss}: nessuna analisi scritta")
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
