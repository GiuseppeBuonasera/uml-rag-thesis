"""
Selezione DETERMINISTICA dell'insieme di sviluppo (2026-10-08, FASE 3 del formato compatto, voce 92): 20 esercizi del
CORPUS, mai il test set. Query in leave-one-out come nei piloti (il prompt builder esclude la query dai suoi esempi).

Regola (dichiarata prima delle run):
1. candidati: quelli del primo pilota (experiments/select_pilot.table: 59 convertiti, esclusi EatAtHome per
   known_issues e i 14 fuori scala rispetto al test set, ground truth compatto > 3.509 token) -> 44; per default
   (PROPOSTA) esclusi anche i 6 esercizi dei piloti (le correzioni del post-processing v2 sono nate dalle loro risposte,
   voce 89: l'insieme di sviluppo deve esserne indipendente) -> 38; con --include-pilot restano 44;
2. fascia: score_norm del top-1 BM25 in leave-one-out con i cut-off congelati (basso / medio / alto);
3. quote per fascia proporzionali ai candidati della fascia, 20 in tutto, arrotondate con il metodo dei resti piu'
   grandi (a parita' di resto: ordine basso, medio, alto);
4. dentro la fascia, candidati ordinati per (dimensione, id) con la dimensione del primo pilota (classi + interfacce +
   enumerazioni + attributi + operazioni + valori + relazioni); scelti i k alle posizioni floor((i + 0.5) * n / k),
   i = 0..k-1: quantili equispaziati, dal piccolo al grande.

Uso:
    python experiments/select_dev.py [--include-pilot]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "generation"))
import select_pilot as sp  # noqa: E402
from prompt_builder import PromptBuilder, cl  # noqa: E402

N_DEV = 20
PILOT_IDS = tuple(yaml.safe_load((ROOT / "experiments" / "configs" / "pilot_temperature.yaml").read_text(
    encoding="utf-8"))["query_ids"])


def quotas(counts: dict[str, int], total: int = N_DEV) -> dict[str, int]:
    """Metodo dei resti piu' grandi (Hamilton); a parita' di resto conta l'ordine di sp.BANDS."""
    n = sum(counts.values())
    exact = {b: total * counts[b] / n for b in sp.BANDS}
    q = {b: math.floor(exact[b]) for b in sp.BANDS}
    for b in sorted(sp.BANDS, key=lambda b: (-(exact[b] - q[b]), sp.BANDS.index(b)))[:total - sum(q.values())]:
        q[b] += 1
    return q


def spread(rows: list[dict], k: int) -> list[dict]:
    rows = sorted(rows, key=lambda r: (r["size"], r["id"]))
    n = len(rows)
    if k > n:
        raise ValueError(f"servono {k} esercizi, la fascia ne ha {n}")
    return [rows[math.floor((i + 0.5) * n / k)] for i in range(k)]


def select(builder: PromptBuilder, include_pilot: bool = False) -> tuple[list[dict], dict, dict]:
    rows = [r for r in sp.table(builder) if not r["excluded"] and (include_pilot or r["id"] not in PILOT_IDS)]
    counts = {b: sum(r["band"] == b for r in rows) for b in sp.BANDS}
    q = quotas(counts)
    chosen = [dict(r, band_quota=q[b]) for b in sp.BANDS for r in spread([r for r in rows if r["band"] == b], q[b])]
    return chosen, counts, q


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-pilot", action="store_true", help="non escludere i 6 esercizi dei piloti")
    a = ap.parse_args(argv)
    chosen, counts, q = select(PromptBuilder(*cl.load_all()), a.include_pilot)
    print(f"candidati per fascia {counts} -> quote {q} (piloti {'inclusi' if a.include_pilot else 'esclusi'})\n")
    print("| fascia | id | score_norm top-1 (LOO) | dimensione | GT Apollon compatto (token) | nel pilota |")
    print("|---|---|---|---|---|---|")
    for r in chosen:
        print(f"| {r['band']} | {r['id']} | {r['score_norm']:.4f} | {r['size']} | {r['gt_tokens']} | "
              f"{'si' if r['id'] in PILOT_IDS else '—'} |")
    print("\nquery_ids:", [r["id"] for r in chosen])
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102): due righe in data/results/run_log.jsonl
    with run_log.logged(__file__):
        sys.exit(main())
