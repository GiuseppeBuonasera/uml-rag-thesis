"""
Client verso l'LLM (es. Anthropic Claude, OpenAI) per generare il diagramma
UML (Apollon v4 JSON, vedi docs/decisions.md) a partire dal prompt costruito.
"""


class LLMClient:
    def __init__(self, provider: str = "anthropic", model: str = None):
        self.provider = provider
        self.model = model
        # TODO: inizializzare il client dell'SDK corrispondente

    def generate(self, prompt: str) -> str:
        """Ritorna il diagramma Apollon v4 JSON generato, come stringa."""
        raise NotImplementedError
