"""
Riproduzione delle run di retrieval versionate con il protocollo STORICO `--pool corpus59` (voce 129). Nessun LLM.
Lento (circa 8 minuti: griglia BM25 e tre modelli densi su CPU), per questo non sta nella suite di test; la suite
controlla in pochi secondi i top-3 e la logica dei protocolli (retrieval/test_retrieval.py, check_pool_protocols).

  1. analyze_retrieval.py --pool corpus59 -> loo_2026-10-04_stop1: sensitivity.csv, variants.csv, near_duplicates.csv,
     loo_top3.csv identici byte per byte; summary.md identico salvo titolo (run id), riga del commit e riga di
     provenienza (aggiunta dalla voce 106, dopo quella run);
  2. analyze_dense.py --pool corpus59 -> dense_2026-10-09_22f5adf: relevance.csv, top3.csv, hubness.csv identici byte per
     byte; summary.md identico salvo titolo, provenienza e tempi di calcolo (righe della tabella dei modelli);
  3. hubness_report.py su copie di loo_2026-10-04_stop1 e testset_2026-10-04_stop2: hubness.csv e summary.md identici.
Tutto in una cartella temporanea: le run versionate non vengono toccate.

Uso:
    python retrieval/check_protocols.py
"""

from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import contextlib
import io
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_dense  # noqa: E402
import analyze_retrieval  # noqa: E402
import hubness_report  # noqa: E402

RUNS = HERE.parent / "data" / "results" / "retrieval"


def same_bytes(a: Path, b: Path) -> None:
    assert a.read_bytes() == b.read_bytes(), f"{a.name}: diverso da {b}"


def same_summary(a: Path, b: Path, skip) -> None:
    la = [x for x in a.read_text(encoding="utf-8").splitlines()[1:] if not skip(x)]
    lb = [x for x in b.read_text(encoding="utf-8").splitlines()[1:] if not skip(x)]
    assert la == lb, f"{a}: {[(x, y) for x, y in zip(la, lb) if x != y][:2]}"


def quiet(fn, *args):
    out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    with contextlib.redirect_stdout(out):
        fn(*args)


def main() -> int:
    prov = ("Analisi eseguita sul commit",)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        quiet(analyze_retrieval.main, ["--pool", "corpus59", "--run-id", "loo", "--out-dir", str(tmp)])
        ref = RUNS / "loo_2026-10-04_stop1"
        for f in ("sensitivity.csv", "variants.csv", "near_duplicates.csv", "loo_top3.csv"):
            same_bytes(tmp / "loo" / f, ref / f)
        same_summary(tmp / "loo" / "summary.md", ref / "summary.md",
                     lambda x: x.startswith(prov) or x.startswith("Commit `") or not x.strip())
        print("  OK  analyze_retrieval --pool corpus59 = loo_2026-10-04_stop1 (4 CSV byte per byte, summary.md)")

        quiet(analyze_dense.main, ["--pool", "corpus59", "--run-id", "dense", "--out-dir", str(tmp)])
        ref = RUNS / "dense_2026-10-09_22f5adf"
        for f in ("relevance.csv", "top3.csv", "hubness.csv"):
            same_bytes(tmp / "dense" / f, ref / f)
        timing = ("| sentence-transformers/", "| BAAI/", "| Alibaba-NLP/")
        same_summary(tmp / "dense" / "summary.md", ref / "summary.md", lambda x: x.startswith(prov + timing))
        print("  OK  analyze_dense --pool corpus59 = dense_2026-10-09_22f5adf (3 CSV byte per byte, summary.md salvo "
              "tempi)")

        for run in ("loo_2026-10-04_stop1", "testset_2026-10-04_stop2"):
            shutil.copytree(RUNS / run, tmp / "hub" / run)
        quiet(hubness_report.main, ["--results-dir", str(tmp / "hub")])
        for f in ("hubness.csv", "summary.md"):
            same_bytes(tmp / "hub" / "testset_2026-10-04_stop2" / f, RUNS / "testset_2026-10-04_stop2" / f)
        print("  OK  hubness_report (pool corpus59 dal config.json) = testset_2026-10-04_stop2 (hubness.csv, summary.md)")
    print("Protocolli storici riprodotti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
