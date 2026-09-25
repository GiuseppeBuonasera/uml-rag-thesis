"""
Applica glossary.json a plantuml_it.txt per produrre plantuml.txt (stessa
struttura — classi, relazioni, molteplicita' — solo i nomi cambiano). Usato per
gli esercizi in corpus/raw/translated_it/<Nome>/, vedi docs/decisions.md.

Sostituisce solo le chiavi del glossario che sono identificatori PlantUML validi
(classi/attributi/etichette: lettere, cifre, underscore, senza spazi) — le voci
frase libera (es. "corsi di Master") non compaiono in plantuml_it.txt e vengono
ignorate qui. Sostituzione per parola intera (word boundary), dalle chiavi piu'
lunghe alle piu' corte, per evitare che "Docente" sostituisca per errore una
parte di "DocenteInterno".

Normalizza anche le molteplicita' in stile PlantUML "n" verso lo stile
"*" (0..n -> 0..*, 1..n -> 1..*, n -> *) — SOLO nell'output inglese
(plantuml.txt), MAI in plantuml_it.txt che resta fedele alla notazione
dell'immagine originale. Convenzione decisa il 2026-09-25, vedi
docs/decisions.md. La normalizzazione opera solo sul primo token dentro le
virgolette (la molteplicita'), lasciando intatto un eventuale ruolo dopo lo
spazio (es. '"1..n responsabile"' -> '"1..* responsabile"' — anche se in
pratica un ruolo tradotto non dovrebbe mai iniziare per "n").

Normalizza anche il tipo di attributo "bool" -> "boolean" — SOLO in
plantuml.txt, mai in plantuml_it.txt. "time" non viene toccato (e' gia' nella
lista dei tipi ammessi in prompt_template_v4.txt). Convenzione decisa il
2026-09-25, vedi docs/decisions.md.

Uso:
    python corpus/apply_glossary.py <cartella_esercizio>
    (richiede <cartella_esercizio>/plantuml_it.txt e <cartella_esercizio>/glossary.json,
    scrive <cartella_esercizio>/plantuml.txt)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

IDENTIFIER_RE = re.compile(r"^\w+$")
QUOTED_RE = re.compile(r'"([^"]*)"')


def normalize_multiplicity_token(mult: str) -> str:
    if mult == "n":
        return "*"
    if mult.endswith("..n"):
        return mult[:-1] + "*"
    return mult


def normalize_multiplicities(text: str) -> str:
    def repl(m: re.Match) -> str:
        content = m.group(1)
        parts = content.split(None, 1)
        if not parts:
            return m.group(0)
        mult = normalize_multiplicity_token(parts[0])
        rest = (" " + parts[1]) if len(parts) == 2 else ""
        return f'"{mult}{rest}"'

    return QUOTED_RE.sub(repl, text)


BOOL_RE = re.compile(r"\bbool\b")


def normalize_types(text: str) -> str:
    return BOOL_RE.sub("boolean", text)


def load_term_glossary(glossary_path: Path) -> dict[str, str]:
    raw = json.loads(glossary_path.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_") and IDENTIFIER_RE.match(k)}


def apply_glossary(text: str, glossary: dict[str, str]) -> str:
    # dalle chiavi piu' lunghe alle piu' corte, cosi' "DocenteInterno" viene
    # sostituito prima che "Docente" possa intaccarne una parte
    for term in sorted(glossary, key=len, reverse=True):
        pattern = re.compile(r"\b" + re.escape(term) + r"\b")
        text = pattern.sub(glossary[term], text)
    return text


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("uso: python corpus/apply_glossary.py <cartella_esercizio>")
    folder = Path(sys.argv[1])
    it_path = folder / "plantuml_it.txt"
    glossary_path = folder / "glossary.json"
    out_path = folder / "plantuml.txt"

    if not it_path.exists():
        raise SystemExit(f"non trovato: {it_path}")
    if not glossary_path.exists():
        raise SystemExit(f"non trovato: {glossary_path}")

    glossary = load_term_glossary(glossary_path)
    text_it = it_path.read_text(encoding="utf-8")
    text_en = apply_glossary(text_it, glossary)
    text_en = normalize_multiplicities(text_en)
    text_en = normalize_types(text_en)
    out_path.write_text(text_en, encoding="utf-8")

    print(f"Glossario applicato: {len(glossary)} termini identificatore.")
    print("Molteplicita' normalizzate: 0..n->0..*, 1..n->1..*, n->* (solo plantuml.txt)")
    print("Tipi normalizzati: bool->boolean (solo plantuml.txt)")
    print(f"Scritto: {out_path}")


if __name__ == "__main__":
    main()
