"""
Retriever keyword-based (es. BM25) sul corpus di coppie
(descrizione esercizio, diagramma di riferimento).
"""


class KeywordRetriever:
    def __init__(self, corpus):
        """corpus: lista di dict con almeno le chiavi 'description' e 'diagram'."""
        self.corpus = corpus
        # TODO: costruire l'indice BM25 (es. rank_bm25.BM25Okapi)

    def retrieve(self, query: str, top_k: int = 3):
        """Ritorna i top_k esempi più simili alla query per overlap lessicale."""
        raise NotImplementedError
