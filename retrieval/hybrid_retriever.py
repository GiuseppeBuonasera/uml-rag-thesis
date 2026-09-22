"""
Retriever ibrido: combina keyword e dense retrieval (es. reciprocal rank fusion
o combinazione pesata degli score).
"""

from retrieval.keyword_retriever import KeywordRetriever
from retrieval.dense_retriever import DenseRetriever


class HybridRetriever:
    def __init__(self, corpus, alpha: float = 0.5):
        self.keyword = KeywordRetriever(corpus)
        self.dense = DenseRetriever(corpus)
        self.alpha = alpha  # peso relativo tra i due retriever

    def retrieve(self, query: str, top_k: int = 3):
        raise NotImplementedError
