"""
Controllo di leakage per gli esercizi tradotti: similarita' coseno TF-IDF della
description.md di ciascun esercizio contro (a) le descrizioni degli altri esercizi
del corpus (corpus.jsonl) e (b) i 20 esercizi De Bari (docs/dati/debari/Exercises.pdf).
Top-3 con punteggio e titolo per ciascun confronto; segnala se il punteggio > 0.4.

Vettorizzazione: TfidfVectorizer(stop_words="english", sublinear_tf=True) addestrata
sull'unione dei testi indicizzati (idf comune). Richiede pypdf e scikit-learn.

Opzioni (2026-10-03, FASE 5 test set De Bari; senza opzioni il comportamento e' invariato):
- --debari-test: i 20 esercizi De Bari sono presi da corpus/processed/testset_debari.jsonl
  (descrizioni pulite, id DBNN_...) invece che dal testo grezzo del PDF; i bersagli possono
  essere id DBNN_ (oppure --all-debari per tutti e 20).
- --prompt: indicizza anche le descrizioni degli esempi few-shot del prompt statico
  (docs/dati/apollon_format_reference/prompt_template_v4.txt: bank loans, AirTravel) come pool
  separato "prompt" (id PROMPT_example_1_bank_loans, PROMPT_example_2_airtravel).

Uso:
    python corpus/leakage_check.py Hospital ResearchCenter ...
    python corpus/leakage_check.py --debari-test --prompt --all-debari
    python corpus/leakage_check.py --debari-test --prompt DB06_Flights --vs AirTravel
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, str(Path(__file__).parent))
import paths  # noqa: E402  (percorsi condivisi, voce 116)

ROOT = paths.ROOT
THRESHOLD = 0.4
PROMPT_PATH = ROOT / "docs/dati/apollon_format_reference/prompt_template_v4.txt"
TESTSET_PATH = paths.TESTSET_JSONL


def load_debari() -> dict[str, str]:
    text = "\n".join(p.extract_text() or "" for p in PdfReader(ROOT / "docs/dati/debari/Exercises.pdf").pages)
    parts = re.split(r"\n\s*(\d{1,2})\.\s+([A-Z][^\n]{2,40})\n", text)
    out = {}
    for i in range(1, len(parts) - 2, 3):
        out[f"De Bari {parts[i]}: {parts[i + 1].strip()}"] = re.split(r"Source:", parts[i + 2])[0]
    return out


def load_debari_test() -> dict[str, str]:
    if not TESTSET_PATH.exists():
        raise SystemExit(f"{TESTSET_PATH} non trovato: esegui build_manifest.py --split debari_test")
    return {r["id"]: r["description"] for r in paths.read_jsonl(TESTSET_PATH)}


def load_prompt_examples() -> dict[str, str]:
    """Descrizioni degli esempi few-shot del prompt statico ('Example N — text:' ... 'Example N — JSON: see
    file <nome>.json'), con id PROMPT_<nome file senza _v4.json>."""
    text = PROMPT_PATH.read_text(encoding="utf-8")
    found = re.findall(r"Example (\d) — text:\n(.*?)\nExample \1 — JSON: see file (\S+?)_v4\.json", text, re.S)
    if len(found) != 2:
        raise SystemExit(f"{PROMPT_PATH.name}: attesi 2 esempi few-shot, trovati {len(found)}")
    return {f"PROMPT_{name}": body.strip() for _, body, name in found}


def main() -> None:
    args = sys.argv[1:]
    # --vs <id>: riporta anche il punteggio verso un esercizio specifico, anche se sotto
    # soglia o fuori dal top-3 (caso es. 15 ApartmentBuilding vs House, 2026-10-01)
    extra = []
    while "--vs" in args:
        i = args.index("--vs")
        extra.append(args[i + 1])
        del args[i : i + 2]
    debari_test = "--debari-test" in args
    with_prompt = "--prompt" in args
    all_debari = "--all-debari" in args
    targets = [a for a in args if a not in ("--debari-test", "--prompt", "--all-debari")]

    corpus = {r["id"]: r["description"] for r in paths.read_jsonl(paths.CORPUS_JSONL)}
    debari = load_debari_test() if debari_test else load_debari()
    prompt = load_prompt_examples() if with_prompt else {}
    if all_debari:
        targets += list(debari)
    if not targets:
        raise SystemExit("uso: python corpus/leakage_check.py <id> [<id> ...] [--vs <id>] "
                         "[--debari-test] [--prompt] [--all-debari]")

    names = list(corpus) + list(debari) + list(prompt)
    texts = list(corpus.values()) + list(debari.values()) + list(prompt.values())
    vec = TfidfVectorizer(stop_words="english", sublinear_tf=True)
    matrix = vec.fit_transform(texts)
    index = {n: i for i, n in enumerate(names)}

    pools = [("corpus", list(corpus))]
    if not debari_test:
        pools.append(("De Bari", list(debari)))
    if prompt:
        pools.append(("prompt statico", list(prompt)))

    for t in targets:
        if t not in index:
            print(f"{t}: non indicizzato (esegui build_manifest.py)")
            continue
        sims = cosine_similarity(matrix[index[t]], matrix)[0]
        for label, pool in pools:
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
