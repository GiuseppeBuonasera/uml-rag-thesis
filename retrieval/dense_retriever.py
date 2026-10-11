"""
Retriever denso (voce 107, 2026-10-09): embedding di sentence-transformers su CPU e similarita' coseno esatta (numpy).
Indicizza SOLO `description` (come BM25), senza stopword ne' stemming e senza prefissi.

score      = coseno tra embedding normalizzati della query e del candidato.
score_norm = uguale a score (il coseno e' gia' su una scala comune tra query).
Parita': id crescente (base.rank_results), come BM25.

Modello alla revisione fissata (`revision=<commit>` di Hugging Face), `trust_remote_code=False`, `device="cpu"`.
Gli embedding si salvano in una cache su disco (fuori da git), un file per modello e revisione, indicizzata dallo
sha256 del testo: un testo cambiato si ricalcola. Per i test si passa un `encoder` finto (lista di testi -> matrice):
in quel caso sentence-transformers non viene nemmeno importato e non si scarica nulla.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Callable, Iterable, Sequence

import numpy as np

try:
    from .base import RetrievalResult, Retriever, rank_results
except ImportError:
    from base import RetrievalResult, Retriever, rank_results

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache" / "embeddings"

Encoder = Callable[[list[str]], np.ndarray]


def text_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cache_path(model_name: str, revision: str, cache_dir: Path = CACHE_DIR, chunk_tokens: int | None = None) -> Path:
    """Nome del file con modello e revisione, es. BAAI__bge-small-en-v1.5@5c38ec7c405e.npz; con i pezzi (variante 6,
    voce 120) un file a parte, es. ...@1110a243fdf4_chunk256.npz."""
    suffix = f"_chunk{chunk_tokens}" if chunk_tokens else ""
    return cache_dir / f"{re.sub(r'[^A-Za-z0-9._-]', '_', model_name.replace('/', '__'))}@{revision[:12]}{suffix}.npz"


def _disable_broken_torchaudio() -> None:
    """transformers importa torchaudio se e' installato; nell'ambiente attuale torchaudio 2.6 non si carica con torch
    2.10 (conflitto segnalato in docs/STATUS.md, voce 107). Il progetto non usa l'audio: si dichiara torchaudio non
    disponibile SOLO in questo processo, senza toccare l'ambiente ne' torch."""
    import transformers.utils as tu
    import transformers.utils.import_utils as iu
    tu.is_torchaudio_available = iu.is_torchaudio_available = lambda: False


def load_sentence_transformer(model_name: str, revision: str):
    _disable_broken_torchaudio()
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name, revision=revision, device="cpu", trust_remote_code=False)


class EmbeddingCache:
    """{sha256 del testo: vettore} su un file .npz; si salva solo se ci sono vettori nuovi."""

    def __init__(self, path: Path | None):
        self.path, self.vectors, self.dirty = path, {}, False
        if path is not None and path.exists():
            with np.load(path) as z:
                self.vectors = dict(zip(z["keys"].tolist(), z["vectors"]))

    def save(self) -> None:
        if self.path is None or not self.dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        keys = sorted(self.vectors)
        tmp = self.path.with_suffix(".tmp.npz")
        np.savez(tmp, keys=np.array(keys), vectors=np.stack([self.vectors[k] for k in keys]))
        tmp.replace(self.path)
        self.dirty = False


class DenseRetriever(Retriever):
    def __init__(self, model_name: str, revision: str, encoder: Encoder | None = None,
                 cache_dir: Path | None = CACHE_DIR, batch_size: int = 8, chunk_tokens: int | None = None):
        """chunk_tokens (variante 6, voce 120): testi piu' lunghi divisi in pezzi di al piu' chunk_tokens token del
        tokenizer del modello (token speciali compresi, senza sovrapposizione); embedding = media dei pezzi
        normalizzati, rinormalizzata. None = comportamento della voce 107 (troncamento del modello)."""
        self.model_name, self.revision, self.batch_size = model_name, revision, batch_size
        self.chunk_tokens = chunk_tokens
        self._encoder = encoder
        self._model = None
        self.cache = EmbeddingCache(cache_path(model_name, revision, cache_dir, chunk_tokens)
                                    if cache_dir is not None else None)
        self.ids: list[str] = []
        self.matrix: np.ndarray | None = None
        self.encoded_texts = 0  # testi effettivamente passati all'encoder (non trovati in cache)

    # --- modello ---
    @property
    def model(self):
        if self._model is None:
            self._model = load_sentence_transformer(self.model_name, self.revision)
        return self._model

    def _encode_raw(self, texts: list[str]) -> np.ndarray:
        if self.chunk_tokens:
            out = self._encode_chunked(texts)
        elif self._encoder is not None:
            out = np.asarray(self._encoder(texts), dtype=np.float32)
        else:
            out = self.model.encode(texts, batch_size=self.batch_size, convert_to_numpy=True,
                                    normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        if np.any(norms == 0):
            raise ValueError("embedding nullo: coseno non definito")
        return out / norms

    def split_text(self, text: str) -> list[str]:
        """Pezzi di al piu' chunk_tokens token (2 riservati ai token speciali), ricostruiti come testo."""
        if self._encoder is not None:  # test: pezzi di chunk_tokens parole
            words = text.split()
            return [" ".join(words[i:i + self.chunk_tokens]) for i in range(0, len(words), self.chunk_tokens)] or [""]
        tok = self.model.tokenizer
        ids = tok(text, add_special_tokens=False, truncation=False)["input_ids"]
        size = self.chunk_tokens - 2
        return [tok.decode(ids[i:i + size]) for i in range(0, len(ids), size)] or [""]

    def _encode_chunked(self, texts: list[str]) -> np.ndarray:
        pieces = [self.split_text(t) for t in texts]
        flat = [p for ps in pieces for p in ps]
        if self._encoder is not None:
            vec = np.asarray(self._encoder(flat), dtype=np.float32)
        else:
            vec = self.model.encode(flat, batch_size=self.batch_size, convert_to_numpy=True,
                                    normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
        vec = vec / np.linalg.norm(vec, axis=1, keepdims=True)
        out, i = [], 0
        for ps in pieces:
            out.append(vec[i:i + len(ps)].mean(axis=0))
            i += len(ps)
        return np.stack(out)

    def encode(self, texts: Sequence[str], use_cache: bool = True) -> np.ndarray:
        """Embedding normalizzati, dalla cache quando possibile."""
        keys = [text_key(t) for t in texts]
        missing = sorted({k: t for k, t in zip(keys, texts) if not (use_cache and k in self.cache.vectors)}.items())
        if missing:
            fresh = self._encode_raw([t for _, t in missing])
            self.encoded_texts += len(missing)
            for (k, _), v in zip(missing, fresh):
                self.cache.vectors[k] = v
            self.cache.dirty = True
            self.cache.save()
        return np.stack([self.cache.vectors[k] for k in keys])

    def token_counts(self, texts: Sequence[str]) -> list[int]:
        """Numero di token (con i token speciali, senza troncamento) secondo il tokenizer del modello."""
        tok = self.model.tokenizer
        return [len(tok(t, add_special_tokens=True, truncation=False)["input_ids"]) for t in texts]

    @property
    def max_seq_length(self) -> int:
        return int(self.model.max_seq_length)

    # --- interfaccia Retriever ---
    def fit(self, records: Sequence[dict]) -> "DenseRetriever":
        self.ids = [r["id"] for r in records]
        if len(self.ids) != len(set(self.ids)):
            raise ValueError("id duplicati nei record indicizzati")
        self.matrix = self.encode([r["description"] for r in records])
        return self

    def scores(self, query_text: str) -> np.ndarray:
        if self.matrix is None:
            raise RuntimeError("chiamare fit() prima di retrieve()")
        return self.matrix @ self.encode([query_text])[0]

    def retrieve(self, query_text: str, k: int, exclude_ids: Iterable[str] = ()) -> list[RetrievalResult]:
        sims = self.scores(query_text)
        return rank_results(((i, float(s), float(s)) for i, s in zip(self.ids, sims)), k, exclude_ids)
