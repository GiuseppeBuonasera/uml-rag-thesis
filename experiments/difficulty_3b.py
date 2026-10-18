"""
Difficolta' dei 54 esercizi di valutazione del 3b (2026-10-17, schema di analisi concordato con i relatori). Sola
lettura: nessuna chiamata a un LLM, nessun risultato del modello.

Per ogni esercizio:
- difficolta_fk: Flesch-Kincaid Grade Level della traccia data al modello (textstat 0.7.4, inglese americano; piu'
  alto = piu' difficile; per i 15 esercizi tradotti misura lo stile della traduzione);
- difficolta_size: numero di classi + relazioni del diagramma di riferimento (relazioni = tutti gli archi:
  associazioni, composizioni, aggregazioni, dipendenze, generalizzazioni e realizzazioni);
- n_classi, n_relazioni: le due parti della dimensione; split (corpus / debari) e tradotto (1 se la traccia e' una
  traduzione dall'italiano).
Righe ordinate per difficolta_fk decrescente (a parita', per id). Le colonne F1 per prompt si aggiungono dopo.

Uso:
    python experiments/difficulty_3b.py [--out data/results/generation/analisi_3b/difficolta.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "experiments"), str(ROOT / "generation"), str(ROOT / "retrieval"), str(ROOT)]
import compare_3b as c3  # noqa: E402  (evaluation_ids: i 54 di valutazione)
from evaluation import element_metrics as el  # noqa: E402

OUT = ROOT / "data" / "results" / "generation" / "analisi_3b" / "difficolta.csv"
COLUMNS = ("esercizio", "split", "tradotto", "difficolta_fk", "difficolta_size", "n_classi", "n_relazioni")


def flesch_kincaid(text: str) -> float:
    import textstat
    textstat.set_lang("en_US")
    return float(textstat.flesch_kincaid_grade(text))


def rows() -> list[dict]:
    import corpus_loader as cl
    by_id = {c["id"]: c for c in cl.load_candidates() + cl.load_queries()}
    corpus = ROOT / "corpus" / "processed" / "corpus.jsonl"
    translated = {r["id"] for r in map(json.loads, corpus.read_text(encoding="utf-8").splitlines()) if r.get("translated")}
    queries = {x["id"] for x in cl.load_queries()}
    out = []
    for q in c3.evaluation_ids():
        e = el.elements(by_id[q]["diagram_apollon_json"])
        n_cls, n_rel = len(e["classes"]), len(e["relations"]) + len(e["generalizations"])
        out.append({"esercizio": q, "split": "debari" if q in queries else "corpus", "tradotto": int(q in translated),
                    "difficolta_fk": round(flesch_kincaid(by_id[q]["description"]), 2),
                    "difficolta_size": n_cls + n_rel, "n_classi": n_cls, "n_relazioni": n_rel})
    return sorted(out, key=lambda r: (-r["difficolta_fk"], r["esercizio"]))


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--out", default=str(OUT))
    args = a.parse_args(argv)
    data = rows()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(data)
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(out)
    print(f"scritto {out}: {len(data)} esercizi")
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
