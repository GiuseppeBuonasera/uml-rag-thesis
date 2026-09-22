"""
Retriever dense (embedding-based, es. SBERT/SROBERTA) sul corpus.
"""


class DenseRetriever:
    def __init__(self, corpus, model_name: str = "all-MiniLM-L6-v2"):
        self.corpus = corpus
        self.model_name = model_name
        # TODO: caricare il modello di embedding e precomputare gli embedding del corpus

    def retrieve(self, query: str, top_k: int = 3):
        """Ritorna i top_k esempi più simili per similarità coseno tra embedding."""
        raise NotImplementedError
