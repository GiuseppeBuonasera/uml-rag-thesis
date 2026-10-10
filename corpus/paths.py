"""
Percorsi condivisi dei dati del corpus e lettura dei file JSONL (2026-10-10, voce 116): un solo posto per le
cartelle raw/, i file processati, gli split e il formato degli id De Bari, usato dagli script di corpus/ e da
retrieval/corpus_loader.py, experiments/provenance.py e dai controlli di sanita' di generation/. Modulo leggero:
importarlo non carica la pipeline del Passo 1.

Le cartelle raw/ restano separate per fonte (fonti e licenze diverse; i percorsi sono citati dalle note di
trascrizione e dal tag testset-v1): qui si definiscono, non si spostano.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
ROOT = CORPUS_DIR.parent

# --- sorgenti (sola lettura) ---
RAW_DIR = CORPUS_DIR / "raw"
RAW_ORIGINAL_DIR = RAW_DIR / "models_original"  # Golden UML Modelset (45)
RAW_TRANSLATED_DIR = RAW_DIR / "translated_it"  # esercizi italiani tradotti (15, non versionati)
RAW_DEBARI_DIR = RAW_DIR / "debari_test"  # test set De Bari (20, tag testset-v1)

# --- uscite della pipeline del Passo 1 ---
PROCESSED_DIR = CORPUS_DIR / "processed"
CORPUS_JSONL = PROCESSED_DIR / "corpus.jsonl"
TESTSET_JSONL = PROCESSED_DIR / "testset_debari.jsonl"
APOLLON_DIR = PROCESSED_DIR / "apollon"
APOLLON_DEBARI_DIR = PROCESSED_DIR / "apollon_debari"

# split -> (cartelle raw, jsonl, cartella dei JSON Apollon)
SPLITS = {
    "corpus": ((RAW_ORIGINAL_DIR, RAW_TRANSLATED_DIR), CORPUS_JSONL, APOLLON_DIR),
    "debari_test": ((RAW_DEBARI_DIR,), TESTSET_JSONL, APOLLON_DEBARI_DIR),
}

# id degli esercizi De Bari: DBNN_NomeInCamelCase
DEBARI_ID_RE = re.compile(r"^DB(\d{2})_[A-Z][A-Za-z0-9]*$")


def read_jsonl(path: Path) -> list[dict]:
    """Record di un file JSONL, una riga per record; le righe vuote si ignorano."""
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
