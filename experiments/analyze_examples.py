"""
Quali esempi aiutano? (2026-10-10, voce 120, passo 1). Analisi SOLO descrittiva, nessuna chiamata a un LLM: sulle
risposte di sviluppo gia' generate da Gemma 4 12B QAT con le istruzioni v4 (stesso prompt salvo gli esempi), mette in
relazione la qualita' della risposta (R per risposta, 0 se non valida) con le proprieta' degli esempi ricevuti.

Run usate (configurazione 2, istruzioni v4, esempi su una riga): dev_k (k = 2, 3, 5, 8), dev_retrievers (dense, hybrid,
oracle_jt), dev_v5base; formati PlantUML (P-G) e compatto (C-G). Escluse le run con istruzioni diverse (dev_instructions,
dev_v5) o esempi serializzati diversamente (dev_cindent, dev_cboth) e le run della versione 1 (dev_formats).

Per togliere la difficolta' dell'esercizio, ogni valore (R e proprieta') e' espresso come scarto dalla media delle
risposte dello STESSO esercizio e formato; si riporta lo Spearman tra gli scarti (con il p) per ciascuna proprieta':
- jt_query      Jt medio tra il GT della query e il GT degli esempi (somiglianza dei nomi di classe; usa il GT della query:
                solo analisi, non realizzabile in un retriever);
- coverage      quota dei tipi di relazione del GT della query presenti in almeno un esempio (idem);
- quality       qualita' media degli esempi: 1 - (quota di relazioni senza entrambe le molteplicita' + quota di attributi
                senza tipo) / 2 (variante 5 della voce 120);
- size          numero medio di relazioni degli esempi;
- debari        quota di esempi De Bari;
- k             numero di esempi.

Uso:
    python experiments/analyze_examples.py
"""

from __future__ import annotations

import statistics
import sys
from collections import defaultdict
from pathlib import Path

from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "retrieval"))
import analyze_instructions as ai  # noqa: E402
import analyze_pilot as ap  # noqa: E402
import relevance as rv  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
OUT = RESULTS / "dev_examples_analysis"
MODEL_ID = "google/gemma-4-12b-qat"
RUNS = ("dev_k", "dev_retrievers", "dev_v5base")
FEATURES = ("jt_query", "coverage", "quality", "size", "debari", "k")


def quality(diagram: dict) -> float:
    rels = [e for e in diagram["edges"] if e["type"] not in ("ClassInheritance", "ClassRealization")]
    nomult = sum(1 for e in rels if not (e["data"].get("sourceMultiplicity") and e["data"].get("targetMultiplicity")))
    attrs = [a["name"] for n in diagram["nodes"] if n["data"].get("stereotype") != "enumeration"
             for a in n["data"].get("attributes", [])]
    untyped = sum(":" not in a for a in attrs)
    return 1 - ((nomult / len(rels) if rels else 0) + (untyped / len(attrs) if attrs else 0)) / 2


def r_call(c: dict) -> float:
    n = len(c["gt"]["edges"])
    return 0.0 if c["v"].level < 3 or not n else ap.compare_relations(c["v"].diagram, c["gt"])["same_type"] / n


def rows() -> list[dict]:
    cands, queries = cl.load_all()
    every = {r["id"]: r["diagram_apollon_json"] for r in cands + queries}
    tokens = {i: rv.class_tokens(d) for i, d in every.items()}
    types = {i: {e["type"] for e in d["edges"]} for i, d in every.items()}
    gt = {c["id"]: c["diagram_apollon_json"] for c in cands}
    out = []
    for run in RUNS:
        for name, fmt in (("P-G", "plantuml"), ("C-G", "compact")):
            info = ai.load_run(RESULTS, run, name, gt, MODEL_ID)
            for c in info["calls"]:
                ex = c["m"]["example_ids"]
                if not ex:
                    continue
                q = c["q"]
                out.append({
                    "run": run, "format": fmt, "q": q, "R": r_call(c),
                    "jt_query": statistics.mean(cl.jaccard(tokens[q], tokens[e]) for e in ex),
                    "coverage": len(types[q] & set().union(*(types[e] for e in ex))) / len(types[q]) if types[q] else 1,
                    "quality": statistics.mean(quality(every[e]) for e in ex),
                    "size": statistics.mean(len(every[e]["edges"]) for e in ex),
                    "debari": sum(cl.DEBARI_ID_RE.match(e) is not None for e in ex) / len(ex),
                    "k": len(ex)})
    return out


def within(data: list[dict], key: str) -> list[float]:
    """Scarti dalla media dello stesso esercizio e formato."""
    groups = defaultdict(list)
    for d in data:
        groups[(d["q"], d["format"])].append(d[key])
    means = {g: statistics.mean(v) for g, v in groups.items()}
    return [d[key] - means[(d["q"], d["format"])] for d in data]


def main() -> int:
    data = rows()
    L = ["# Quali esempi aiutano? (analisi descrittiva, voce 120 passo 1)", "",
         "Risposte di sviluppo di Gemma 4 12B QAT con istruzioni v4 (dev_k, dev_retrievers, dev_v5base). R per risposta "
         "(0 se non valida). Spearman tra gli SCARTI dalla media dello stesso esercizio e formato (toglie la difficoltà "
         "dell'esercizio). Solo descrittivo: nessuna decisione.", "", provenance.provenance_line(), "",
         "| formato | risposte | " + " | ".join(FEATURES) + " |", "|---|---|" + "---|" * len(FEATURES)]
    for fmt in ("plantuml", "compact"):
        sub = [d for d in data if d["format"] == fmt]
        r = within(sub, "R")
        cells = []
        for f in FEATURES:
            x = within(sub, f)
            rho, p = spearmanr(x, r) if len(set(x)) > 1 else (float("nan"), float("nan"))
            cells.append(f"{rho:+.2f} (p {p:.3f})")
        L.append(f"| {fmt} | {len(sub)} | " + " | ".join(cells) + " |")
    L += ["", "Proprietà: jt_query = somiglianza dei nomi di classe tra GT della query ed esempi; coverage = quota dei tipi "
          "di relazione della query presenti negli esempi; quality = completezza del GT degli esempi (molteplicità e "
          "tipi degli attributi); size = relazioni per esempio; debari = quota di esempi De Bari; k = numero di esempi. "
          "Un rho positivo vuol dire che, a parità di esercizio, risposte con valori più alti hanno R più alto."]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
