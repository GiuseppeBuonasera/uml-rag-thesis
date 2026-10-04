"""
Estrae i 20 esercizi di De Bari et al. (docs/dati/debari/Exercises.pdf) in
corpus/raw/debari_test/ — TEST SET, mai nel corpus di retrieval (vedi
build_manifest.py --split debari_test e docs/decisions.md, 2026-10-02).

Per ogni esercizio N scrive:
  _images/dbNN.png                  immagine "Reference Solution" (pypdf; le .jp2 convertite in PNG con Pillow)
  DBNN_<Nome>/description.md        solo la traccia (senza "Source:" e "Reference Solution:")
  DBNN_<Nome>/metadata.txt          name (titolo originale), language, tags, domain, source, citation, contact
  DBNN_<Nome>/extraction_notes.md   correzioni di artefatti di estrazione applicate (generato)
Non scrive mai plantuml.txt / transcription_notes.md / relations_table.md (FASE 3, trascrizione).

Testo: leakage_check.load_debari (stessa segmentazione usata per il leakage).
Ricostruzione delle righe (le righe del PDF sono andate a capo per impaginazione):
una riga si unisce alla successiva salvo che (a) la successiva inizi con "•",
(b) la riga finisca con 2+ spazi (fine paragrafo nel testo estratto), (c) sia
corta (< 60% della riga piu' lunga dell'esercizio), (d) finisca con punteggiatura
di fine frase e sia < 90% della riga piu' lunga — eccezioni verificate sul PDF
renderizzato in FORCE_JOIN. Un paragrafo per riga; elementi puntati "- ".
Gli artefatti di estrazione (parole spezzate, spazi) sono corretti SOLO tramite
TEXT_FIXES / SOURCE_FIXES, ognuno verificato sul PDF renderizzato; hard-fail se il
testo da correggere non c'e'. Refusi dell'originale (appointement, ammount,
Bycicle, "ordered .", "rented- Each", ...) NON sono corretti.

Uso:
    python corpus/extract_debari.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).parent))
import build_manifest as bm
import leakage_check as lc

PDF_PATH = Path(__file__).parent.parent / "docs" / "dati" / "debari" / "Exercises.pdf"
OUT_DIR = bm.DEBARI_RAW_DIR
CITATION = (
    'De Bari, Garaccione, Coppola, Ardito, Torchiano, "Evaluating Large Language Models in Exercises of '
    'UML Class Diagram Modeling" — docs/dati/debari/Exercises.pdf, esercizio {n}'
)

# Il dominio e' assegnato dal trascrittore (non dalla fonte): approvato come PROVVISORIO (2026-10-02).
DOMAIN_NOTE = "PROVVISORIO, assegnato dal trascrittore dal vocabolario del corpus, non dalla fonte"
# numero -> (id cartella, dominio). Titoli dal PDF; domini dal vocabolario del corpus.
EXERCISES = {
    1: ("DB01_ProjectManagementSystem", "Business Services"),
    2: ("DB02_HollywoodApproach", "Media and Publishing"),
    3: ("DB03_WordProcessor", "Media and Publishing"),
    4: ("DB04_PatientRecordAndSchedulingSystem", "Healthcare"),
    5: ("DB05_MovieShop", "Sales"),
    6: ("DB06_Flights", "Logistics"),
    7: ("DB07_BankSystem", "Financial Services"),
    8: ("DB08_VeterinaryClinic", "Healthcare"),
    9: ("DB09_AutoRepair", "Business Services"),
    10: ("DB10_Restaurant", "Leisure and Recreation"),
    11: ("DB11_Deliveries", "Logistics"),
    12: ("DB12_Furniture", "Manufacturing"),
    13: ("DB13_Factory", "Manufacturing"),
    14: ("DB14_BicycleRental", "Leisure and Recreation"),
    15: ("DB15_SaturnIntManagement", "Business Services"),
    16: ("DB16_OOBank", "Financial Services"),
    17: ("DB17_PrepaidCellPhone", "Business Services"),
    18: ("DB18_LibrarySystem", "Education"),
    19: ("DB19_MyDoctor", "Healthcare"),
    20: ("DB20_OnlineShopping", "Sales"),
}

# Artefatti di estrazione pypdf, verificati sul PDF renderizzato (pdftoppm, 2026-10-02):
# (numero, testo estratto, testo del PDF)
TEXT_FIXES = [
    (1, "wor k product", "work product"),
    (2, "Approach” .", "Approach”."),
    (2, "sce ne", "scene"),
    (4, "physicia n", "physician"),
    (8, "owner -less", "owner-less"),
    (12, "Hi -Key-Ah", "Hi-Key-Ah"),
    (16, "account number ;", "account number;"),
    (16, "a ttached", "attached"),
    (20, "w hich", "which"),
]
SOURCE_FIXES = [
    (4, "Changin g", "Changing"),
    (15, "Models ,", "Models,"),
    (16, "us ing", "using"),
]
# a capo di impaginazione con punteggiatura finale (riga giustificata a piena larghezza nel PDF)
FORCE_JOIN = [
    (15, "and give them access to the company car park."),
    (19, "on the 4th of September during 1 PM - 5PM."),
]

SENTENCE_END = re.compile(r"[.:!?)”’]$")


def page_images() -> list:
    """Immagini del PDF in ordine di pagina (una per esercizio)."""
    images = [im for page in PdfReader(PDF_PATH).pages for im in page.images]
    if len(images) != len(EXERCISES):
        raise SystemExit(f"attese {len(EXERCISES)} immagini nel PDF, trovate {len(images)}")
    return images


def sources() -> dict[int, str]:
    text = "\n".join(p.extract_text() or "" for p in PdfReader(PDF_PATH).pages)
    found = [" ".join(m.group(1).split()) for m in re.finditer(r"Source:(.*?)Reference Solution", text, re.S)]
    if len(found) != len(EXERCISES):
        raise SystemExit(f"attese {len(EXERCISES)} righe 'Source:', trovate {len(found)}")
    return dict(enumerate(found, start=1))


def apply_fixes(n: int, text: str, fixes: list[tuple[int, str, str]], what: str) -> tuple[str, list[str]]:
    applied = []
    for num, old, new in fixes:
        if num != n:
            continue
        if old not in text:
            raise ValueError(f"es. {n}: correzione {what} non applicabile, testo non trovato: {old!r}")
        text = text.replace(old, new)
        applied.append(f"{what}: {old!r} -> {new!r}")
    return text, applied


def rebuild_lines(n: int, raw: str) -> tuple[str, list[str]]:
    """Righe del PDF -> un paragrafo/elemento puntato per riga (vedi docstring del modulo)."""
    lines = [l for l in raw.split("\n") if l.strip()]
    max_len = max(len(l.rstrip()) for l in lines)
    forced = [t for num, t in FORCE_JOIN if num == n]
    used_forced = set()
    out: list[str] = []
    current = ""
    for i, line in enumerate(lines):
        stripped = " ".join(line.split())
        current = f"{current} {stripped}".strip() if current else stripped
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        if nxt is None:
            break_here = True
        elif nxt.lstrip().startswith("•"):
            break_here = True
        elif line.endswith("  "):
            break_here = True
        elif len(line.rstrip()) < 0.6 * max_len:
            break_here = True
        elif SENTENCE_END.search(line.rstrip()) and len(line.rstrip()) < 0.9 * max_len:
            hit = [t for t in forced if line.rstrip().endswith(t)]
            used_forced.update(hit)
            break_here = not hit
        else:
            break_here = False
        if break_here:
            out.append(current)
            current = ""
    unused = set(forced) - used_forced
    if unused:
        raise ValueError(f"es. {n}: FORCE_JOIN non usati: {sorted(unused)}")
    out = [re.sub(r"^•\s*", "- ", l) for l in out]
    notes = [f"a capo di impaginazione forzato (riga giustificata nel PDF): ...{t!r}" for t in forced]
    return "\n".join(out) + "\n", notes


def check_ids() -> list[str]:
    """Id univoci, nel formato DBNN_, mai uguali a un id del corpus; segnala suffissi uguali."""
    ids = [i for i, _ in EXERCISES.values()]
    assert len(ids) == len(set(ids)), "id De Bari duplicati"
    corpus_ids = bm.split_ids("corpus")
    for n, (model_id, _) in EXERCISES.items():
        m = bm.DEBARI_ID_RE.match(model_id)
        assert m and int(m.group(1)) == n, f"id {model_id!r} non coerente con il numero {n}"
        assert model_id not in corpus_ids, f"id {model_id!r} gia' nel corpus"
    lowered = {c.lower(): c for c in corpus_ids}
    return [f"{i} (suffisso uguale a '{lowered[i.split('_', 1)[1].lower()]}' del corpus)"
            for i in ids if i.split("_", 1)[1].lower() in lowered]


def main() -> None:
    suffix_notes = check_ids()
    texts = list(lc.load_debari().items())
    if len(texts) != len(EXERCISES):
        raise SystemExit(f"load_debari: attesi {len(EXERCISES)} esercizi, trovati {len(texts)}")
    srcs = sources()
    images = page_images()

    (OUT_DIR / "_images").mkdir(parents=True, exist_ok=True)
    for n, ((key, raw), image) in enumerate(zip(texts, images), start=1):
        title = key.split(":", 1)[1].strip()
        assert key.startswith(f"De Bari {n}:"), f"ordine inatteso: {key!r} in posizione {n}"
        model_id, domain = EXERCISES[n]
        folder = OUT_DIR / model_id
        folder.mkdir(exist_ok=True)

        image.image.convert("RGB").save(OUT_DIR / "_images" / f"db{n:02d}.png")

        description, line_notes = rebuild_lines(n, raw)
        description, text_notes = apply_fixes(n, description, TEXT_FIXES, "testo")
        description = re.sub(r"(?<=\S) {2,}(?=\S)", " ", description)
        source, source_notes = apply_fixes(n, srcs[n], SOURCE_FIXES, "source")

        (folder / "description.md").write_text(description, encoding="utf-8")
        (folder / "metadata.txt").write_text(
            f"name: {title}\nlanguage: English\ntags: debari_test\ndomain: {domain}\n"
            f"domain_note: {DOMAIN_NOTE}\nsource: {source}\n"
            f"citation: {CITATION.format(n=n)}\ncontact:\n",
            encoding="utf-8",
        )
        notes = [
            f"# Note di estrazione — De Bari {n}: {title}",
            "",
            f"Generato da `corpus/extract_debari.py` (non modificare a mano). Immagine: `_images/db{n:02d}.png`"
            f" ({image.name} nel PDF).",
            "",
            "Normalizzazioni generali: righe del PDF ricomposte in un paragrafo per riga, elementi puntati"
            " `- `, spazi multipli ridotti a uno. Refusi dell'originale non corretti.",
            "",
            "## Correzioni di artefatti di estrazione (verificate sul PDF renderizzato)",
        ]
        notes += [f"- {x}" for x in text_notes + source_notes + line_notes] or ["- nessuna"]
        (folder / "extraction_notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
        print(f"{n:2d} {model_id}: {title} | {len(description.splitlines())} righe | "
              f"{len(text_notes) + len(source_notes) + len(line_notes)} correzioni")

    if suffix_notes:
        print("Id con suffisso uguale a un esercizio del corpus (nessuna collisione esatta):", suffix_notes)


if __name__ == "__main__":
    main()
