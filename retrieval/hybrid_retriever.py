"""
Retriever ibrido (voce 107, 2026-10-09): Reciprocal Rank Fusion tra BM25 (configurazione congelata) e un retriever
denso, costante 60, nessun parametro da tarare.

score(d)   = 1 / (c + rango_BM25(d)) + 1 / (c + rango_denso(d)), ranghi da 1 sull'ordinamento COMPLETO dei candidati
             non esclusi di ciascun retriever (ciascuno con la propria regola di parita' per id).
score_norm = score / (2 / (c + 1)), cioe' 1 se d e' primo per entrambi.
Parita' di score: id crescente (base.rank_results).
"""

from __future__ import annotations

from typing import Iterable, Sequence

try:
    from .base import RetrievalResult, Retriever, rank_results
except ImportError:
    from base import RetrievalResult, Retriever, rank_results

RRF_K = 60


def rrf_scores(rankings: Sequence[Sequence[str]], c: int = RRF_K) -> dict[str, float]:
    """rankings = liste di id ordinate (rango 1 = primo); un id assente da una lista non riceve contributo da essa."""
    out: dict[str, float] = {}
    for ranking in rankings:
        for rank, i in enumerate(ranking, start=1):
            out[i] = out.get(i, 0.0) + 1.0 / (c + rank)
    return out


class HybridRetriever(Retriever):
    def __init__(self, keyword: Retriever, dense: Retriever, c: int = RRF_K):
        self.keyword, self.dense, self.c = keyword, dense, c
        self.ids: list[str] = []

    @classmethod
    def prefitted(cls, keyword: Retriever, dense: Retriever, ids: Sequence[str], c: int = RRF_K) -> "HybridRetriever":
        """Ibrido su due retriever GIA' indicizzati (prompt builder: BM25 rifittato senza la query, denso su tutti i
        candidati); ids = candidati ammessi, le esclusioni si passano a retrieve()."""
        h = cls(keyword, dense, c)
        h.ids = list(ids)
        return h

    def fit(self, records: Sequence[dict]) -> "HybridRetriever":
        self.ids = [r["id"] for r in records]
        self.keyword.fit(records)
        self.dense.fit(records)
        return self

    def component_rankings(self, query_text: str, exclude_ids: Iterable[str] = ()) -> tuple[list[str], list[str]]:
        excluded = set(exclude_ids)
        n = len(self.ids)
        return ([r.id for r in self.keyword.retrieve(query_text, n, excluded)],
                [r.id for r in self.dense.retrieve(query_text, n, excluded)])

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        scores = rrf_scores(self.component_rankings(query_text, exclude_ids), self.c)
        best = 2.0 / (self.c + 1)
        return rank_results(((i, s, s / best) for i, s in scores.items()), k, exclude_ids)
