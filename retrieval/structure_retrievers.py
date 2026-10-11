"""
Varianti del retriever che usano il DIAGRAMMA DEI CANDIDATI (voce 120). Del diagramma della query non si usa nulla:
la query resta il solo testo della traccia. Parametri fissati nella voce 120 prima dei calcoli; nessuno si tara.

Stessa interfaccia di base.py (fit(records), retrieve(query_text, k, exclude_ids)); i record devono avere 'id',
'description' e, per le varianti che guardano la struttura, 'diagram_apollon_json'. Parita': id crescente.

  StructureBM25(synonyms=False)   variante 2  : BM25 sui token dei nomi di classe dei candidati (2s: + sinonimi WordNet)
  StructureDense(dense)           variante 2d : coseno MiniLM tra la traccia e i nomi di classe dei candidati
  RRF(a, b)                       combinazione con la base (c = 60), come l'ibrido
  MMR(base, lam=0.7)              variante 3  : diversita' tra gli esempi (somiglianza = Jt tra i nomi di classe)
  ConstructBoost(base)            variante 4  : favorisce i candidati con i costrutti segnalati dalla traccia
  QualityWeighted(base)           variante 5  : score_norm della base x qualita' del GT del candidato
La variante 6 (MiniLM a pezzi) e' un'opzione di dense_retriever.DenseRetriever (chunk_tokens).
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

try:
    from . import relevance as rv
    from .base import RetrievalResult, Retriever, rank_results
    from .hybrid_retriever import rrf_scores
    from .keyword_retriever import KeywordRetriever
    from .text_preprocessing import PreprocessConfig, tokenize
except ImportError:
    import relevance as rv
    from base import RetrievalResult, Retriever, rank_results
    from hybrid_retriever import rrf_scores
    from keyword_retriever import KeywordRetriever
    from text_preprocessing import PreprocessConfig, tokenize

RRF_K = 60
MMR_LAMBDA = 0.7
# segnali dei costrutti nella traccia (voce 120), su testo minuscolo
INHERITANCE_CUES = re.compile(r"\bis an? (?:\w+ )?(?:kind|type) of\b|\bkinds of\b|\btypes of\b|\beither\b.{1,80}?\bor\b|"
                              r"\bcan be (?:a|an|either)\b|\bsubclass|\bspeciali[sz](?:ed|ation)\b|\bspecial kind\b|"
                              r"\bis a specific\b", re.S)
PART_CUES = re.compile(r"\bconsists? of\b|\bcomposed of\b|\bmade (?:up )?of\b|\bpart of\b|\bcontains?\b|\bcomprises?\b")
INHERITANCE_TYPES = {"ClassInheritance"}
PART_TYPES = {"ClassComposition", "ClassAggregation"}


# ---------------------------------------------------------------- testo dei nomi di classe

def class_name_words(diagram: dict) -> list[str]:
    """Parole dei nomi di classe (CamelCase spezzato, minuscole), nell'ordine del diagramma."""
    return [w for n in diagram["nodes"] for w in rv.name_tokens(n["data"]["name"])]


WORDNET_HELP = ("la variante 2s richiede nltk (dipendenza opzionale, requirements.txt) e i dati WordNet: "
                "pip install nltk==3.10.3, poi python -m nltk.downloader wordnet (docs/STATUS.md, sezione 'Ambiente della tesi')")


def wordnet_missing() -> str | None:
    """None se nltk e i dati WordNet sono disponibili, altrimenti il motivo. Import pigro: nltk serve SOLO alla
    variante 2s (voce 120, non entrata nel 3b, voce 122); nessun download a runtime."""
    try:
        from nltk.corpus import wordnet as wn
    except ImportError:
        return "nltk non installato"
    try:
        wn.ensure_loaded()
    except LookupError:
        return "dati WordNet di nltk non scaricati"
    return None


def wordnet_expand(words: Sequence[str]) -> list[str]:
    """Ogni parola + i lemmi del suo PRIMO significato nominale in WordNet (parole composte spezzate)."""
    missing = wordnet_missing()
    if missing:
        raise RuntimeError(f"{missing}: {WORDNET_HELP}")
    from nltk.corpus import wordnet as wn
    out = []
    for w in words:
        out.append(w)
        synsets = wn.synsets(w, pos="n")
        if synsets:
            for lemma in synsets[0].lemma_names():
                out += [x for x in re.split(r"[_\-\s]+", lemma.lower()) if x and x != w]
    return out


# ---------------------------------------------------------------- variante 2 / 2s

class StructureBM25(Retriever):
    """BM25 (k1, b e preprocessing della configurazione congelata) i cui documenti sono le parole dei nomi di classe del
    diagramma del candidato; la query e' la traccia."""

    def __init__(self, synonyms: bool = False, k1: float = 1.5, b: float = 0.75,
                 preprocess: PreprocessConfig = PreprocessConfig()):
        self.synonyms, self.k1, self.b, self.preprocess = synonyms, k1, b, preprocess
        self.ids: list[str] = []

    def document(self, record: dict) -> str:
        words = class_name_words(record["diagram_apollon_json"])
        return " ".join(wordnet_expand(words) if self.synonyms else words)

    def fit(self, records: Sequence[dict]) -> "StructureBM25":
        self.ids = [r["id"] for r in records]
        self.inner = KeywordRetriever(self.k1, self.b, self.preprocess).fit(
            [{"id": r["id"], "description": self.document(r)} for r in records])
        return self

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        return self.inner.retrieve(query_text, k, exclude_ids)


# ---------------------------------------------------------------- variante 2d

class StructureDense(Retriever):
    """Coseno tra l'embedding della traccia e quello del testo dei nomi di classe del candidato ("a b, c d, ...")."""

    def __init__(self, dense):
        self.dense = dense  # DenseRetriever (MiniLM, voce 108) o uno finto nei test
        self.ids: list[str] = []

    @staticmethod
    def document(record: dict) -> str:
        return ", ".join(" ".join(rv.name_tokens(n["data"]["name"])) for n in record["diagram_apollon_json"]["nodes"])

    def fit(self, records: Sequence[dict]) -> "StructureDense":
        self.ids = [r["id"] for r in records]
        self.dense.fit([{"id": r["id"], "description": self.document(r)} for r in records])
        return self

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        return self.dense.retrieve(query_text, k, exclude_ids)


# ---------------------------------------------------------------- combinazione

class RRF(Retriever):
    """Reciprocal Rank Fusion di due retriever (c = 60), ranghi sull'ordinamento completo dei candidati non esclusi."""

    def __init__(self, a: Retriever, b: Retriever, c: int = RRF_K):
        self.a, self.b, self.c = a, b, c
        self.ids: list[str] = []

    def fit(self, records: Sequence[dict]) -> "RRF":
        self.ids = [r["id"] for r in records]
        self.a.fit(records)
        self.b.fit(records)
        return self

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        excluded, n = set(exclude_ids), len(self.ids)
        ranks = [[r.id for r in x.retrieve(query_text, n, excluded)] for x in (self.a, self.b)]
        scores = rrf_scores(ranks, self.c)
        best = 2.0 / (self.c + 1)
        return rank_results(((i, s, s / best) for i, s in scores.items()), k, excluded)


# ---------------------------------------------------------------- variante 3

class MMR(Retriever):
    """Maximal Marginal Relevance sulla base: a ogni passo il candidato che massimizza
    lam * rilevanza - (1 - lam) * max somiglianza con quelli gia' scelti; rilevanza = score della base normalizzato
    min-max sul pool, somiglianza = Jt tra i nomi di classe."""

    def __init__(self, base: Retriever, lam: float = MMR_LAMBDA):
        self.base, self.lam = base, lam
        self.ids: list[str] = []

    def fit(self, records: Sequence[dict]) -> "MMR":
        self.ids = [r["id"] for r in records]
        self.tokens = {r["id"]: rv.class_tokens(r["diagram_apollon_json"]) for r in records}
        self.base.fit(records)
        return self

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        excluded = set(exclude_ids)
        full = self.base.retrieve(query_text, len(self.ids), excluded)
        if not full:
            return []
        lo, hi = min(r.score for r in full), max(r.score for r in full)
        rel = {r.id: (r.score - lo) / (hi - lo) if hi > lo else 1.0 for r in full}
        order = {r.id: r.rank for r in full}
        chosen: list[tuple[str, float]] = []
        left = [r.id for r in full]
        while left and len(chosen) < k:
            def mmr(i):
                sim = max((rv.cl.jaccard(self.tokens[i], self.tokens[j]) for j, _ in chosen), default=0.0)
                return self.lam * rel[i] - (1 - self.lam) * sim
            best = max(left, key=lambda i: (mmr(i), -order[i]))
            chosen.append((best, mmr(best)))
            left.remove(best)
        return [RetrievalResult(id=i, rank=n, score=s, score_norm=rel[i]) for n, (i, s) in enumerate(chosen, start=1)]


# ---------------------------------------------------------------- variante 4

def cued_constructs(text: str) -> set[str]:
    t = text.lower()
    return ({"inheritance"} if INHERITANCE_CUES.search(t) else set()) | ({"part"} if PART_CUES.search(t) else set())


def has_constructs(diagram: dict) -> set[str]:
    types = {e["type"] for e in diagram["edges"]}
    return ({"inheritance"} if types & INHERITANCE_TYPES else set()) | ({"part"} if types & PART_TYPES else set())


class ConstructBoost(Retriever):
    """Senza segnali nella traccia = la base. Con segnali: RRF(base, ranking per numero di costrutti segnalati presenti
    nel candidato, parita' per rango della base)."""

    def __init__(self, base: Retriever, c: int = RRF_K):
        self.base, self.c = base, c
        self.ids: list[str] = []

    def fit(self, records: Sequence[dict]) -> "ConstructBoost":
        self.ids = [r["id"] for r in records]
        self.constructs = {r["id"]: has_constructs(r["diagram_apollon_json"]) for r in records}
        self.base.fit(records)
        return self

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        excluded = set(exclude_ids)
        cues = cued_constructs(query_text)
        if not cues:
            return self.base.retrieve(query_text, k, excluded)
        full = [r.id for r in self.base.retrieve(query_text, len(self.ids), excluded)]
        pos = {i: n for n, i in enumerate(full)}
        by_construct = sorted(full, key=lambda i: (-len(cues & self.constructs[i]), pos[i]))
        scores = rrf_scores([full, by_construct], self.c)
        best = 2.0 / (self.c + 1)
        return rank_results(((i, s, s / best) for i, s in scores.items()), k, excluded)


# ---------------------------------------------------------------- variante 5

def gt_quality(diagram: dict) -> float:
    """1 - (quota di relazioni non di generalizzazione senza entrambe le molteplicita' + quota di attributi senza
    tipo) / 2 (voce 120)."""
    rels = [e for e in diagram["edges"] if e["type"] not in ("ClassInheritance", "ClassRealization")]
    nomult = sum(1 for e in rels if not ((e.get("data") or {}).get("sourceMultiplicity")
                                         and (e.get("data") or {}).get("targetMultiplicity")))
    attrs = [a["name"] for n in diagram["nodes"] if n["data"].get("stereotype") != "enumeration"
             for a in n["data"].get("attributes", [])]
    untyped = sum(":" not in a for a in attrs)
    return 1 - ((nomult / len(rels) if rels else 0) + (untyped / len(attrs) if attrs else 0)) / 2


class QualityWeighted(Retriever):
    """score_norm della base moltiplicato per la qualita' del GT del candidato."""

    def __init__(self, base: Retriever):
        self.base = base
        self.ids: list[str] = []

    def fit(self, records: Sequence[dict]) -> "QualityWeighted":
        self.ids = [r["id"] for r in records]
        self.quality = {r["id"]: gt_quality(r["diagram_apollon_json"]) for r in records}
        self.base.fit(records)
        return self

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        excluded = set(exclude_ids)
        full = self.base.retrieve(query_text, len(self.ids), excluded)
        return rank_results(((r.id, r.score_norm * self.quality[r.id], r.score_norm * self.quality[r.id])
                             for r in full), k, excluded)
