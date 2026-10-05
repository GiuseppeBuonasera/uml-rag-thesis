"""
Retriever keyword BM25 (Passo 2, 2026-10-04): rank_bm25.BM25Okapi (versione fissata in requirements.txt), k1 e b
configurabili, preprocessing di retrieval/text_preprocessing.py. Indicizza SOLO `description`.

score      = punteggio BM25Okapi di rank_bm25 (IDF con floor epsilon * idf medio per i termini molto frequenti).
score_norm = score / self_score(query), dove self_score e' il punteggio BM25 della query contro se' stessa trattata
             come un documento (tf dei termini nella query, lunghezza = numero di token della query), calcolato con la
             STESSA formula e le statistiche del corpus indicizzato (IDF, avgdl): vale quindi anche per query fuori
             indice (test set). Come in rank_bm25, i termini ripetuti nella query contano una volta per occorrenza e i
             termini assenti dal corpus hanno IDF 0. score_norm NON e' limitato a 1: un documento piu' corto della
             query, o con piu' occorrenze dei termini rari, puo' superare il punteggio della query su se' stessa.
             Se self_score e' 0 (nessun termine della query nel corpus) score_norm vale 0.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Sequence

from rank_bm25 import BM25Okapi

try:  # import come pacchetto (retrieval.keyword_retriever) o come script accanto agli altri moduli
    from .base import RetrievalResult, Retriever, rank_results
    from .text_preprocessing import PreprocessConfig, tokenize
except ImportError:
    from base import RetrievalResult, Retriever, rank_results
    from text_preprocessing import PreprocessConfig, tokenize


class KeywordRetriever(Retriever):
    def __init__(self, k1: float = 1.5, b: float = 0.75, preprocess: PreprocessConfig = PreprocessConfig()):
        self.k1, self.b, self.preprocess = k1, b, preprocess
        self.ids: list[str] = []
        self.bm25: BM25Okapi | None = None

    def fit(self, records: Sequence[dict]) -> "KeywordRetriever":
        self.ids = [r["id"] for r in records]
        if len(self.ids) != len(set(self.ids)):
            raise ValueError("id duplicati nei record indicizzati")
        corpus = [tokenize(r["description"], self.preprocess) for r in records]
        self.bm25 = BM25Okapi(corpus, k1=self.k1, b=self.b)
        return self

    def self_score(self, query_tokens: list[str]) -> float:
        """Punteggio BM25 della query contro se' stessa (vedi docstring del modulo)."""
        tf = Counter(query_tokens)
        dl = len(query_tokens)
        total = 0.0
        for q in query_tokens:
            f = tf[q]
            total += (self.bm25.idf.get(q) or 0) * (f * (self.k1 + 1) /
                                                     (f + self.k1 * (1 - self.b + self.b * dl / self.bm25.avgdl)))
        return total

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        if self.bm25 is None:
            raise RuntimeError("chiamare fit() prima di retrieve()")
        tokens = tokenize(query_text, self.preprocess)
        scores = self.bm25.get_scores(tokens)
        norm = self.self_score(tokens)
        return rank_results(((i, float(s), float(s) / norm if norm > 0 else 0.0) for i, s in zip(self.ids, scores)),
                            k, exclude_ids)
