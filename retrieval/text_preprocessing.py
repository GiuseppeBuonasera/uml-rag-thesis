"""
Tokenizzazione deterministica per il retrieval keyword (Passo 2, 2026-10-04).

- minuscole; token = sequenze di lettere / cifre (regex [^\\W_]+: anche i separatori '_' spezzano, "photo_url" ->
  "photo", "url");
- stopword opzionali: lista FISSA nel repo (retrieval/stopwords_en.txt, 318 parole copiate da scikit-learn), mai
  scaricata a runtime;
- stemming opzionale: Snowball inglese (Porter2) da `snowballstemmer` (Python puro, nessun dato scaricato).
L'ordine dei token e' quello del testo (BM25 usa le frequenze, non l'ordine).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import snowballstemmer

STOPWORDS_PATH = Path(__file__).resolve().parent / "stopwords_en.txt"
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True)
class PreprocessConfig:
    stopwords: bool = True
    stem: bool = True


@lru_cache(maxsize=1)
def load_stopwords() -> frozenset[str]:
    words = [l.strip() for l in STOPWORDS_PATH.read_text(encoding="utf-8").splitlines()]
    return frozenset(w for w in words if w and not w.startswith("#"))


@lru_cache(maxsize=1)
def _stemmer():
    return snowballstemmer.stemmer("english")


def tokenize(text: str, config: PreprocessConfig = PreprocessConfig()) -> list[str]:
    tokens = TOKEN_RE.findall(text.lower())
    if config.stopwords:
        stop = load_stopwords()
        tokens = [t for t in tokens if t not in stop]
    if config.stem:
        tokens = _stemmer().stemWords(tokens)
    return tokens
