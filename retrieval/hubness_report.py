"""
Hubness del retrieval (Passo 2, 2026-10-05), SOLO descrittivo: per ogni candidato del corpus, quante volte compare al
rank 1 e nei top-3 nel leave-one-out e sul test set. Legge soltanto i CSV delle due run (non rifà il retrieval, non
tocca la configurazione congelata).

Scrive <run test set>/hubness.csv e aggiunge (o sostituisce) la sezione "## Hubness" in <run test set>/summary.md.

Uso:
    python retrieval/hubness_report.py [--loo loo_2026-10-04_stop1] [--test testset_2026-10-04_stop2]
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus_loader as cl

RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "results" / "retrieval"
SECTION = "## Hubness"


def counts(path: Path, query_col: str, neighbor_col: str) -> tuple[Counter, Counter, int]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    rank1 = Counter(r[neighbor_col] for r in rows if r["rank"] == "1")
    top3 = Counter(r[neighbor_col] for r in rows)
    return rank1, top3, len({r[query_col] for r in rows})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--loo", default="loo_2026-10-04_stop1")
    ap.add_argument("--test", default="testset_2026-10-04_stop2")
    args = ap.parse_args()

    loo1, loo3, n_loo = counts(RESULTS_DIR / args.loo / "loo_top3.csv", "query", "neighbor")
    tst1, tst3, n_tst = counts(RESULTS_DIR / args.test / "testset_top3.csv", "esercizio", "vicino")
    ids = sorted(c["id"] for c in cl.load_candidates())

    rows = [{"candidato": i, "loo_rank1": loo1[i], "loo_top3": loo3[i], "test_rank1": tst1[i], "test_top3": tst3[i]}
            for i in ids]
    rows.sort(key=lambda r: (-(r["loo_top3"] + r["test_top3"]), -(r["loo_rank1"] + r["test_rank1"]), r["candidato"]))
    out = RESULTS_DIR / args.test
    with (out / "hubness.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    def mai(c: Counter) -> int:
        return sum(1 for i in ids if c[i] == 0)

    L = [SECTION, "",
         f"Solo descrittivo (da `{args.loo}/loo_top3.csv` e `{args.test}/testset_top3.csv`; tabella completa in "
         "`hubness.csv`). Nessuna modifica alla configurazione congelata.", "",
         f"- Candidati distinti al rank 1: LOO {len(loo1)} su {len(ids)} ({n_loo} query); test set {len(tst1)} su "
         f"{len(ids)} ({n_tst} query).",
         f"- Candidati distinti nei top-3: LOO {len(loo3)}; test set {len(tst3)}.",
         f"- Candidati mai nei top-3: LOO {mai(loo3)}; test set {mai(tst3)}.",
         f"- Massimo al rank 1: LOO {max(loo1.values())}; test set {max(tst1.values())}. Massimo nei top-3: LOO "
         f"{max(loo3.values())} (atteso uniforme {3 * n_loo / len(ids):.1f}); test set {max(tst3.values())} (atteso "
         f"{3 * n_tst / len(ids):.1f}).", "",
         "| Candidato | LOO rank 1 | LOO top-3 | test rank 1 | test top-3 |", "|---|---|---|---|---|"]
    L += [f"| {r['candidato']} | {r['loo_rank1']} | {r['loo_top3']} | {r['test_rank1']} | {r['test_top3']} |"
          for r in rows if r["loo_top3"] + r["test_top3"] >= 5]
    L.append("")
    summary = out / "summary.md"
    text = summary.read_text(encoding="utf-8")
    if SECTION in text:
        text = text[:text.index(SECTION)].rstrip("\n") + "\n"
    summary.write_text(text.rstrip("\n") + "\n\n" + "\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
