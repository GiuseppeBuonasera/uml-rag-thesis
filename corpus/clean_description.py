"""
Esclusioni di paragrafi da description.md (2026-09-29, vedi docs/decisions.md)
applicate al testo letto da corpus/raw/<...>/<id>/description.md PRIMA che
diventi il campo "description" di corpus.jsonl (chiamato da
corpus/build_manifest.py) — MAI applicate scrivendo su corpus/raw/ (sorgente
immutabile), stesso principio di corpus/apply_corrections.py.

Caso d'uso: alcune description.md contengono, oltre ai requisiti di dominio,
un paragrafo di consegna/istruzioni per lo studente (es. "Create a UML class
diagram based on the project description. Assign the use cases...",
BuildingManagement) — testo che non descrive il sistema da modellare e non
dovrebbe contaminare il testo indicizzato per il retrieval. Non tutte le
description.md con testo simile sono risolvibili cosi': SellingGoods ha
istruzioni metodologiche intrecciate in tutto il testo (STEP 1-4), non un
singolo paragrafo isolabile — lasciata invariata, vedi docs/decisions.md.

Ogni esclusione e' dichiarata come DATO in
corpus/description_exclusions/<id>.yaml (una lista di paragrafi, testo
esatto), non codificata a mano. Fallisce esplicitamente (ValueError) se un
paragrafo indicato non e' trovato ESATTAMENTE (substring) nella descrizione —
stesso principio hard-fail di apply_corrections.py.

Uso:
    python corpus/build_manifest.py
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

EXCLUSIONS_DIR = Path(__file__).parent / "description_exclusions"


def load_exclusions(model_id: str) -> list[str]:
    path = EXCLUSIONS_DIR / f"{model_id}.yaml"
    if not path.exists():
        return []
    paragraphs = yaml.safe_load(path.read_text(encoding="utf-8"))
    return paragraphs or []


def apply_exclusions(model_id: str, description: str, paragraphs: list[str]) -> tuple[str, list[str]]:
    applied: list[str] = []
    for text in paragraphs:
        text = text.strip()
        if text not in description:
            raise ValueError(
                f"{model_id}: esclusione fallita — paragrafo non trovato in description.md: "
                f"{text[:80]!r}{'...' if len(text) > 80 else ''}"
            )
        description = description.replace(text, "")
        applied.append(f"paragrafo escluso: {text[:80]!r}{'...' if len(text) > 80 else ''}")

    if applied:
        # ripulisce le righe vuote multiple lasciate dalla rimozione del paragrafo
        description = re.sub(r"\n{3,}", "\n\n", description).strip()

    return description, applied
