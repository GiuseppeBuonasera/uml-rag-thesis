"""
Hubness del retrieval (Passo 2, 2026-10-05), SOLO descrittivo: per ogni candidato del corpus, quante volte compare al
rank 1 e nei top-3 nel leave-one-out e sul test set. Legge soltanto i CSV delle due run (non rifà il retrieval, non
tocca la configurazione congelata).

Scrive <run test set>/hubness.csv e aggiunge (o sostituisce) la sezione "## Hubness" in <run test set>/summary.md.

PROTOCOLLO DI POOL (voce 129): l'elenco dei candidati si ricava dal config.json delle due run: `params.pool` per le run
di analyze_retrieval.py, `params.protocol` per quelle di run_testset.py (all80 -> pool unico di 80 esercizi; loo e
fixed59 -> corpus59); senza chiave (run storiche) -> corpus59, i 59 candidati del corpus senza Cruise. Le due run devono
avere lo stesso pool. `--pool` forza il valore.

Uso:
    python retrieval/hubness_report.py [--loo loo_2026-10-04_stop1] [--test testset_2026-10-04_stop2]
                                       [--pool all80|corpus59] [--results-dir DIR]
"""

from __future__ import annotations

import argparse
import csv
import json
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


def run_pool(run_dir: Path) -> str:
    """Pool di una run dal suo config.json: params.pool, params.protocol (all80 / loo / fixed59), altrimenti corpus59."""
    params = json.loads((run_dir / "config.json").read_text(encoding="utf-8")).get("params", {})
    if "pool" in params:
        return params["pool"]
    return "all80" if params.get("protocol") == "all80" else "corpus59"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--loo", default="loo_2026-10-04_stop1")
    ap.add_argument("--test", default="testset_2026-10-04_stop2")
    ap.add_argument("--pool", choices=cl.POOLS, default=None, help="default: dal config.json delle run")
    ap.add_argument("--results-dir", default=str(RESULTS_DIR))
    args = ap.parse_args(argv)
    results = Path(args.results_dir)

    pools = {run_pool(results / args.loo), run_pool(results / args.test)}
    if args.pool is None and len(pools) > 1:
        raise SystemExit(f"le due run hanno pool diversi ({sorted(pools)}): indicare --pool")
    pool = args.pool or pools.pop()
    loo1, loo3, n_loo = counts(results / args.loo / "loo_top3.csv", "query", "neighbor")
    tst1, tst3, n_tst = counts(results / args.test / "testset_top3.csv", "esercizio", "vicino")
    ids = sorted(c["id"] for c in cl.load_pool(pool))

    rows = [{"candidato": i, "loo_rank1": loo1[i], "loo_top3": loo3[i], "test_rank1": tst1[i], "test_top3": tst3[i]}
            for i in ids]
    rows.sort(key=lambda r: (-(r["loo_top3"] + r["test_top3"]), -(r["loo_rank1"] + r["test_rank1"]), r["candidato"]))
    out = results / args.test
    with (out / "hubness.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    def mai(c: Counter) -> int:
        return sum(1 for i in ids if c[i] == 0)

    L = [SECTION, "",
         f"Solo descrittivo (da `{args.loo}/loo_top3.csv` e `{args.test}/testset_top3.csv`; tabella completa in "
         "`hubness.csv`). Nessuna modifica alla configurazione congelata." +
         ("" if pool == "corpus59" else f" Pool {pool} (voce 129): {len(ids)} candidati."), "",
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
