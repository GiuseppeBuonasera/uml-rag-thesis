"""
Stima dei token dei prompt (Passo 3a, 2026-10-06) con l'encoding cl100k_base di tiktoken, caricato dal file
VERSIONATO generation/tokenizer/cl100k_base.tiktoken: nessun download a runtime (stessa regola delle stopword).

tiktoken.get_encoding("cl100k_base") scaricherebbe il vocabolario da openaipublic.blob.core.windows.net al primo uso:
offline, o con il download bloccato, fallisce. Qui l'Encoding si costruisce esplicitamente:
- mergeable_ranks dal file nel repo, verificato con lo sha256 registrato in cl100k_base.tiktoken.sha256 (uguale
  all'expected_hash di tiktoken 0.14.0, tiktoken_ext/openai_public.py); se non coincide -> errore;
- pat_str e token speciali copiati da tiktoken_ext/openai_public.py (tiktoken 0.14.0, funzione cl100k_base).
Il risultato e' lo stesso encoding di tiktoken.get_encoding("cl100k_base") (verificato il 2026-10-06 sui conteggi
della dry run), quindi gli stessi numeri.

La stima e' un'APPROSSIMAZIONE: i modelli locali usano tokenizer propri.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache
from pathlib import Path

TOKENIZER_DIR = Path(__file__).resolve().parent / "tokenizer"
VOCAB_PATH = TOKENIZER_DIR / "cl100k_base.tiktoken"
SHA256_PATH = TOKENIZER_DIR / "cl100k_base.tiktoken.sha256"
ENCODING_NAME = "cl100k_base"

# da tiktoken 0.14.0, tiktoken_ext/openai_public.py, cl100k_base()
CL100K_PAT_STR = (r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++[\r\n]*+|"""
                  r"""\s++$|\s*[\r\n]|\s+(?!\S)|\s""")
CL100K_SPECIAL_TOKENS = {"<|endoftext|>": 100257, "<|fim_prefix|>": 100258, "<|fim_middle|>": 100259,
                         "<|fim_suffix|>": 100260, "<|endofprompt|>": 100276}


def expected_sha256(path: Path = SHA256_PATH) -> str:
    return path.read_text(encoding="utf-8").split()[0].strip().lower()


def load_ranks(vocab_path: Path = VOCAB_PATH, sha256_path: Path = SHA256_PATH) -> dict[bytes, int]:
    data = vocab_path.read_bytes()
    got, want = hashlib.sha256(data).hexdigest(), expected_sha256(sha256_path)
    if got != want:
        raise ValueError(f"sha256 di {vocab_path} = {got}, atteso {want}: vocabolario alterato (es. conversione degli "
                         "a capo in CRLF, vedi .gitattributes)")
    ranks = {}
    for line in data.splitlines():
        if line:
            token, rank = line.split()
            ranks[base64.b64decode(token)] = int(rank)
    return ranks


def build_encoding(vocab_path: Path = VOCAB_PATH, sha256_path: Path = SHA256_PATH):
    import tiktoken
    return tiktoken.Encoding(name=ENCODING_NAME, pat_str=CL100K_PAT_STR, mergeable_ranks=load_ranks(vocab_path,
                             sha256_path), special_tokens=CL100K_SPECIAL_TOKENS)


@lru_cache(maxsize=1)
def encoding():
    return build_encoding()


def count_tokens(text: str) -> int:
    # disallowed_special=(): un eventuale "<|endoftext|>" nel testo si conta come testo normale invece di dare errore
    return len(encoding().encode(text, disallowed_special=()))
