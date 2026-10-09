"""
Misure di pertinenza tra due diagrammi GT (voce 107, 2026-10-09), SOLO in analisi e mai nel ranking. Nessuna usa
embedding (ne' del modello valutato ne' di altri). Servono SOLO a scegliere il modello denso: il confronto BM25 /
denso / ibrido si decide con le generazioni (voce 107, precisazione 1).

- J  : Jaccard dei nomi di classe esatti normalizzati (corpus_loader.class_names), la misura del Passo 2.
- Jt : Jaccard dei TOKEN dei nomi di classe: CamelCase / cifre / separatori spezzati, minuscole, stemming Snowball
       inglese (lo stesso stemmer di text_preprocessing), nessuna stopword. `ReservationSlot` -> {reserv, slot}.
- S  : profilo strutturale, neutro rispetto al vocabolario:
       S = 1/2 * [(1 - 1/2 * ||p_a - p_b||_1) + min(n_a, n_b) / max(n_a, n_b)]
       con p = proporzioni dei 7 tipi di relazione Apollon (vettore nullo se il diagramma non ha relazioni) e n = numero
       di classi. Il primo termine e' 1 meno la distanza di variazione totale (in [0, 1]); entrambi in [0, 1].
"""

from __future__ import annotations

import re

try:
    from . import corpus_loader as cl
    from .text_preprocessing import _stemmer
except ImportError:
    import corpus_loader as cl
    from text_preprocessing import _stemmer

RELATION_TYPES = ("ClassBidirectional", "ClassUnidirectional", "ClassAggregation", "ClassComposition",
                  "ClassInheritance", "ClassRealization", "ClassDependency")
_CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def name_tokens(name: str) -> list[str]:
    """`HTTPRequestLog2` -> ['http', 'request', 'log', '2'] (prima dello stemming)."""
    return [t.lower() for t in _CAMEL_RE.findall(name)]


def class_tokens(diagram: dict) -> set[str]:
    return set(_stemmer().stemWords([t for n in diagram["nodes"] for t in name_tokens(n["data"]["name"])]))


def relation_profile(diagram: dict) -> list[float]:
    counts = [sum(1 for e in diagram["edges"] if e["type"] == t) for t in RELATION_TYPES]
    unknown = {e["type"] for e in diagram["edges"]} - set(RELATION_TYPES)
    if unknown:
        raise ValueError(f"tipi di relazione non previsti: {sorted(unknown)}")
    total = sum(counts)
    return [c / total for c in counts] if total else [0.0] * len(RELATION_TYPES)


def structural_similarity(a: dict, b: dict) -> float:
    pa, pb = relation_profile(a), relation_profile(b)
    rel = 1.0 - 0.5 * sum(abs(x - y) for x, y in zip(pa, pb))
    na, nb = len(a["nodes"]), len(b["nodes"])
    size = min(na, nb) / max(na, nb) if max(na, nb) else 1.0
    return 0.5 * (rel + size)


class Relevance:
    """Precalcola nomi, token e diagrammi dei candidati; measure(q, d) -> {'J', 'Jt', 'S'}."""

    MEASURES = ("J", "Jt", "S")

    def __init__(self, candidates: list[dict]):
        self.diagrams = {c["id"]: c["diagram_apollon_json"] for c in candidates}
        self.names = {i: cl.class_names(d) for i, d in self.diagrams.items()}
        self.tokens = {i: class_tokens(d) for i, d in self.diagrams.items()}

    def measure(self, a: str, b: str) -> dict[str, float]:
        return {"J": cl.jaccard(self.names[a], self.names[b]), "Jt": cl.jaccard(self.tokens[a], self.tokens[b]),
                "S": structural_similarity(self.diagrams[a], self.diagrams[b])}
