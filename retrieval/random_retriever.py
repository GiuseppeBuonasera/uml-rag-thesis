"""
Baseline random (Passo 2, 2026-10-04): k candidati casuali, stessa interfaccia e stessi exclude_ids del BM25.

Riproducibile: l'ordine casuale dipende solo da (seed, testo della query), tramite sha256 (non dall'hash di Python,
che cambia tra esecuzioni). score e score_norm valgono 0.0 (il random non ha un punteggio).
"""

from __future__ import annotations

import hashlib
import random
from typing import Iterable, Sequence

try:
    from .base import RetrievalResult, Retriever
except ImportError:
    from base import RetrievalResult, Retriever


class RandomRetriever(Retriever):
    def __init__(self, seed: int = 0):
        self.seed = seed
        self.ids: list[str] = []

    def fit(self, records: Sequence[dict]) -> "RandomRetriever":
        self.ids = sorted(r["id"] for r in records)  # ordine canonico prima dello shuffle
        return self

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        excluded = set(exclude_ids)
        pool = [i for i in self.ids if i not in excluded]
        digest = hashlib.sha256(f"{self.seed}\x00{query_text}".encode("utf-8")).hexdigest()
        rng = random.Random(int(digest, 16))
        chosen = rng.sample(pool, min(k, len(pool)))
        return [RetrievalResult(id=i, rank=r, score=0.0, score_norm=0.0) for r, i in enumerate(chosen, start=1)]
