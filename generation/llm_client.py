"""
Client verso l'LLM (es. Anthropic Claude, OpenAI) per generare il diagramma
UML (PlantUML) a partire dal prompt costruito.
"""


class LLMClient:
    def __init__(self, provider: str = "anthropic", model: str = None):
        self.provider = provider
        self.model = model
        # TODO: inizializzare il client dell'SDK corrispondente

    def generate(self, prompt: str) -> str:
        """Ritorna il diagramma PlantUML generato come stringa."""
        raise NotImplementedError
