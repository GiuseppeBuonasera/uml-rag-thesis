"""
Metriche di valutazione dei diagrammi UML generati (formato Apollon v4 JSON, vedi
docs/decisions.md):
- sintattiche (validità contro evaluation/uml-model-4.schema.json — vedi
  corpus/apollon_convert.py::validate_against_schema per un validatore già pronto)
- semantiche (correttezza rispetto al diagramma di riferimento: classi, attributi,
  relazioni — inclusa la distinzione tra i tipi nativi ClassInheritance/
  ClassAggregation/ClassComposition/ecc., non più solo associazioni generiche)
- pragmatiche (utilità/qualità percepita, es. via LLM-as-judge o rubric)
"""


def syntactic_score(generated_diagram: str) -> float:
    raise NotImplementedError


def semantic_score(generated_diagram: str, reference_diagram: str) -> float:
    raise NotImplementedError


def pragmatic_score(generated_diagram: str, exercise_description: str) -> float:
    raise NotImplementedError
