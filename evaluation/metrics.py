"""
Metriche di valutazione dei diagrammi UML generati:
- sintattiche (validità PlantUML, parsing corretto)
- semantiche (correttezza rispetto al diagramma di riferimento: classi, attributi,
  associazioni)
- pragmatiche (utilità/qualità percepita, es. via LLM-as-judge o rubric)
"""


def syntactic_score(generated_diagram: str) -> float:
    raise NotImplementedError


def semantic_score(generated_diagram: str, reference_diagram: str) -> float:
    raise NotImplementedError


def pragmatic_score(generated_diagram: str, exercise_description: str) -> float:
    raise NotImplementedError
