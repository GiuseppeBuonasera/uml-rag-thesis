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

Normalizza anche i tipi di attributo (String->string, Int/Integer->int,
Double->double, Float->float, Boolean/bool->boolean, Date->date, Time->time,
DateTime->datetime, Long->long) — SOLO in plantuml.txt, mai in
plantuml_it.txt. Riusa la stessa tabella di apollon_convert.TYPE_NORMALIZATION
(FASE 1, 2026-09-25, vedi docs/decisions.md) invece di duplicarla, cosi'
plantuml.txt (l'artefatto testuale intermedio) e il JSON Apollon finale non
possono disallinearsi sui tipi normalizzati.

Glossario condiviso (2026-09-29, traduzione esercizi 2-15): i termini comuni a
piu' esercizi (es. "Corso", "Docente", "Cliente") vivono in
corpus/raw/translated_it/glossary_shared.json, non ripetuti in ogni
glossary.json — load_merged_glossary() unisce condiviso + locale, e fallisce
esplicitamente se lo stesso termine italiano ha una traduzione diversa nei
due file (deve essere identica in tutto il corpus tradotto).

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

sys.path.insert(0, str(Path(__file__).parent))
import apollon_convert as ac

# identificatori singoli oppure frasi di parole separate da spazio singolo (es. etichette
# di associazione come "Appartiene a") — le frasi libere del glossario non compaiono in
# plantuml_it.txt, quindi applicarle non ha effetti collaterali.
IDENTIFIER_RE = re.compile(r"^\w+( \w+)*$")
QUOTED_RE = re.compile(r'"([^"]*)"')
import paths  # noqa: E402  (percorsi condivisi, voce 116)

SHARED_GLOSSARY_PATH = paths.RAW_TRANSLATED_DIR / "glossary_shared.json"


def normalize_multiplicity_token(mult: str) -> str:
    return ac.normalize_multiplicity(mult)


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


def normalize_types(text: str) -> str:
    for src, dst in sorted(ac.TYPE_NORMALIZATION.items(), key=lambda kv: -len(kv[0])):
        if src == dst:
            continue
        text = re.sub(r"\b" + re.escape(src) + r"\b", dst, text)
    return text


def load_merged_glossary(folder: Path) -> dict[str, str]:
    """Unisce corpus/raw/translated_it/glossary_shared.json (termini comuni a
    piu' esercizi) con <folder>/glossary.json (specifico dell'esercizio).
    Fallisce esplicitamente se lo stesso termine italiano ha una traduzione
    diversa nei due file — deve essere la stessa in tutto il corpus tradotto
    (decisione utente, 2026-09-29). Il glossario locale puo' aggiungere nuovi
    termini, non contraddire quelli condivisi."""
    merged: dict[str, str] = {}
    if SHARED_GLOSSARY_PATH.exists():
        shared_raw = json.loads(SHARED_GLOSSARY_PATH.read_text(encoding="utf-8"))
        merged.update({k: v for k, v in shared_raw.items() if not k.startswith("_")})

    local_raw = json.loads((folder / "glossary.json").read_text(encoding="utf-8"))
    for k, v in local_raw.items():
        if k.startswith("_"):
            continue
        if k in merged and merged[k] != v:
            raise ValueError(
                f"{folder.name}: termine '{k}' ha traduzioni diverse tra glossario "
                f"condiviso ('{merged[k]}') e glossario locale ('{v}') — deve essere "
                "la stessa in tutto il corpus tradotto"
            )
        merged[k] = v
    return merged


def load_term_glossary(folder: Path) -> dict[str, str]:
    merged = load_merged_glossary(folder)
    return {k: v for k, v in merged.items() if IDENTIFIER_RE.match(k)}


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

    glossary = load_term_glossary(folder)
    text_it = it_path.read_text(encoding="utf-8")
    text_en = apply_glossary(text_it, glossary)
    text_en = normalize_multiplicities(text_en)
    text_en = normalize_types(text_en)
    out_path.write_text(text_en, encoding="utf-8")

    print(f"Glossario applicato: {len(glossary)} termini identificatore.")
    print("Molteplicita' normalizzate: 0..n->0..*, 1..n->1..*, n->* (solo plantuml.txt)")
    print("Tipi normalizzati secondo apollon_convert.TYPE_NORMALIZATION (solo plantuml.txt)")
    print(f"Scritto: {out_path}")


if __name__ == "__main__":
    main()
