"""
Controllo di leakage per gli esercizi tradotti: similarita' coseno TF-IDF della
description.md di ciascun esercizio contro (a) le descrizioni degli altri esercizi
del corpus (corpus.jsonl) e (b) i 20 esercizi De Bari (docs/dati/debari/Exercises.pdf).
Top-3 con punteggio e titolo per ciascun confronto; segnala se il punteggio > 0.4.

Vettorizzazione: TfidfVectorizer(stop_words="english", sublinear_tf=True) addestrata
sull'unione corpus + De Bari (idf comune). Richiede pypdf e scikit-learn.

Uso:
    python corpus/leakage_check.py Hospital ResearchCenter ...
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).parent.parent
THRESHOLD = 0.4


def load_debari() -> dict[str, str]:
    text = "\n".join(p.extract_text() or "" for p in PdfReader(ROOT / "docs/dati/debari/Exercises.pdf").pages)
    parts = re.split(r"\n\s*(\d{1,2})\.\s+([A-Z][^\n]{2,40})\n", text)
    out = {}
    for i in range(1, len(parts) - 2, 3):
        out[f"De Bari {parts[i]}: {parts[i + 1].strip()}"] = re.split(r"Source:", parts[i + 2])[0]
    return out


def main() -> None:
    args = sys.argv[1:]
    # --vs <id>: riporta anche il punteggio verso un esercizio specifico, anche se sotto
    # soglia o fuori dal top-3 (caso es. 15 ApartmentBuilding vs House, 2026-10-01)
    extra = []
    while "--vs" in args:
        i = args.index("--vs")
        extra.append(args[i + 1])
        del args[i : i + 2]
    targets = args
    if not targets:
        raise SystemExit("uso: python corpus/leakage_check.py <id> [<id> ...] [--vs <id>]")
    records = [json.loads(l) for l in (ROOT / "corpus/processed/corpus.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    corpus = {r["id"]: r["description"] for r in records}
    debari = load_debari()

    names = list(corpus) + list(debari)
    texts = list(corpus.values()) + list(debari.values())
    vec = TfidfVectorizer(stop_words="english", sublinear_tf=True)
    matrix = vec.fit_transform(texts)
    index = {n: i for i, n in enumerate(names)}

    for t in targets:
        if t not in index:
            print(f"{t}: non nel corpus (esegui build_manifest.py)")
            continue
        sims = cosine_similarity(matrix[index[t]], matrix)[0]
        for label, pool in (("corpus", list(corpus)), ("De Bari", list(debari))):
            ranked = sorted(((sims[index[n]], n) for n in pool if n != t), reverse=True)[:3]
            flag = "  <-- > 0.4" if ranked and ranked[0][0] > THRESHOLD else ""
            print(f"{t} vs {label}:{flag}")
            for score, n in ranked:
                print(f"    {score:.3f}  {n}")
        for n in extra:
            if n in index and n != t:
                print(f"{t} vs {n} (richiesto con --vs): {sims[index[n]]:.3f}")


if __name__ == "__main__":
    main()
