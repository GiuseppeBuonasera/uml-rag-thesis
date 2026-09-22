"""
Costruzione del prompt few-shot dinamico a partire dagli esempi recuperati
dal componente di retrieval.
"""


def build_prompt(exercise_description: str, retrieved_examples: list, template: str = None) -> str:
    """
    exercise_description: descrizione testuale dell'esercizio da risolvere
    retrieved_examples: lista di dict {'description': ..., 'diagram': ...}
    template: template di prompt opzionale; se None, usa un default interno
    """
    raise NotImplementedError
