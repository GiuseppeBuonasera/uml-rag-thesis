"""
Interfaccia comune dei retriever (Passo 2, 2026-10-04): BM25, baseline random e, in seguito, dense / hybrid
e il few-shot statico.

Un retriever indicizza SOLO il campo `description` dei candidati (il testo che riceve il modello): in generazione
la query non ha diagramma, quindi il diagramma non entra mai nel ranking. L'ordinamento e' deterministico:
punteggio decrescente, a parita' di punteggio id crescente.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RetrievalResult:
    id: str
    rank: int  # 1 = primo risultato
    score: float
    score_norm: float  # vedi il retriever concreto per il significato (BM25: score / punteggio della query su se' stessa)


class Retriever(ABC):
    """fit(records): records = sequenza di dict con almeno 'id' e 'description'.
    retrieve(query_text, k, exclude_ids): i k migliori candidati, esclusi gli id in exclude_ids."""

    @abstractmethod
    def fit(self, records: Sequence[dict]) -> "Retriever":
        ...

    @abstractmethod
    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        ...


def rank_results(scored: Iterable[tuple[str, float, float]], k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
    """(id, score, score_norm) -> primi k RetrievalResult, esclusi exclude_ids; tie-break per id crescente."""
    excluded = set(exclude_ids)
    kept = sorted((t for t in scored if t[0] not in excluded), key=lambda t: (-t[1], t[0]))
    return [RetrievalResult(id=i, rank=r, score=s, score_norm=n) for r, (i, s, n) in enumerate(kept[:k], start=1)]
