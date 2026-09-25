"""
Verifica automatica per gli esercizi tradotti in corpus/raw/translated_it/<Nome>/.

Controlli:
1. ogni termine-identificatore (classe, attributo, tipo non primitivo, etichetta
   di relazione) usato in plantuml_it.txt ha una voce nel glossario;
2. plantuml.txt e plantuml_it.txt hanno lo stesso numero di classi, attributi,
   metodi e relazioni, con gli stessi tipi di relazione e le stesse
   molteplicita', nella stessa corrispondenza (via glossario) — verificato
   riparsando entrambi i file con apollon_convert.parse_plantuml, non fidandosi
   della sola riuscita di apply_glossary.py;
3. ogni nome di classe/attributo/etichetta di plantuml.txt compare nel
   glossario come valore di traduzione (o e' un tipo primitivo esente);
4. nessun termine italiano residuo (parola intera) in description.md o
   plantuml.txt;
5. nessun termine italiano residuo nel JSON Apollon compilato
   (corpus/processed/apollon/<id>.json) — non solo in plantuml.txt: un bug
   nella conversione potrebbe introdurre un residuo che il solo controllo 4
   non vedrebbe.

Uso:
    python corpus/check_translated.py <cartella_esercizio>
    python corpus/check_translated.py --all
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import apollon_convert as ac
import apply_glossary as ag

TRANSLATED_IT_DIR = Path(__file__).parent / "raw" / "translated_it"

PRIMITIVE_TYPES = {
    "string", "int", "integer", "float", "double", "bool", "boolean",
    "date", "time", "datetime", "void", "long", "char", "list", "set", "map",
}


def load_glossary(folder: Path) -> dict[str, str]:
    raw = json.loads((folder / "glossary.json").read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def identifier_terms_from_parse(classes: dict, relationships: list[dict]) -> set[str]:
    """Termini-identificatore che dovrebbero avere una voce nel glossario: nomi di
    classe, nomi di attributo, tipi non primitivi, etichette di relazione non vuote."""
    terms: set[str] = set()
    for name, pc in classes.items():
        if pc.placeholder:
            continue
        terms.add(name)
        for attr_name, attr_type in pc.attributes:
            terms.add(attr_name)
            if attr_type and attr_type.lower() not in PRIMITIVE_TYPES:
                terms.add(attr_type)
    for r in relationships:
        if r["kind"] == "binary":
            if r["label"]:
                terms.add(r["label"].lstrip("+"))  # "+responsabile" -> "responsabile"
            if r.get("source_role"):
                terms.add(r["source_role"])
            if r.get("target_role"):
                terms.add(r["target_role"])
        if r["kind"] == "assoc_class":
            terms.add(r["assoc"])
    return terms


def check_glossary_coverage(folder: Path, glossary: dict[str, str], classes_it, rels_it) -> list[str]:
    problems = []
    terms = identifier_terms_from_parse(classes_it, rels_it)
    for term in terms:
        if term not in glossary:
            problems.append(f"termine '{term}' usato in plantuml_it.txt ma assente dal glossario")
    return problems


def translate(term: str, glossary: dict[str, str]) -> str:
    """Sostituzione per parola intera (stessa logica di apply_glossary.py), non un
    lookup esatto sull'intera stringa — necessario per etichette come
    '+responsabile' (con un prefisso non alfanumerico) che nel glossario compare
    solo come 'responsabile'."""
    return ag.apply_glossary(term, glossary)


def translate_type(term: str, glossary: dict[str, str]) -> str:
    """Come translate(), ma applica anche la normalizzazione di tipo
    bool->boolean fatta da apply_glossary.normalize_types su plantuml.txt."""
    return ag.normalize_types(translate(term, glossary))


def check_structural_correspondence(classes_it, rels_it, classes_en, rels_en, glossary: dict[str, str]) -> list[str]:
    problems = []

    if len(classes_it) != len(classes_en):
        problems.append(f"numero di classi diverso: it={len(classes_it)} en={len(classes_en)}")

    for name_it, pc_it in classes_it.items():
        if pc_it.placeholder:
            continue
        name_en = translate(name_it, glossary)
        pc_en = classes_en.get(name_en)
        if pc_en is None:
            problems.append(f"classe '{name_it}' (-> '{name_en}') non trovata in plantuml.txt")
            continue
        if pc_it.kind != pc_en.kind:
            problems.append(f"classe '{name_it}': kind diverso — it={pc_it.kind} en={pc_en.kind}")
        expected_attrs = sorted((translate(n, glossary), translate_type(t, glossary)) for n, t in pc_it.attributes)
        got_attrs = sorted(pc_en.attributes)
        if expected_attrs != got_attrs:
            problems.append(f"classe '{name_it}': attributi non corrispondenti — attesi {expected_attrs}, trovati {got_attrs}")
        if len(pc_it.methods) != len(pc_en.methods):
            problems.append(f"classe '{name_it}': numero di metodi diverso — it={len(pc_it.methods)} en={len(pc_en.methods)}")

    binary_it = [r for r in rels_it if r["kind"] == "binary"]
    binary_en = [r for r in rels_en if r["kind"] == "binary"]
    if len(binary_it) != len(binary_en):
        problems.append(f"numero di relazioni binarie diverso: it={len(binary_it)} en={len(binary_en)}")

    used_idx: set[int] = set()
    for r in binary_it:
        expected_source = translate(r["source"], glossary)
        expected_target = translate(r["target"], glossary)
        expected_label = translate(r["label"], glossary) if r["label"] else ""
        expected_source_mult = ag.normalize_multiplicity_token(r["source_mult"])
        expected_target_mult = ag.normalize_multiplicity_token(r["target_mult"])
        expected_source_role = translate(r.get("source_role", ""), glossary)
        expected_target_role = translate(r.get("target_role", ""), glossary)
        candidate = None
        for i, e in enumerate(binary_en):
            if i in used_idx:
                continue
            if (
                e["source"] == expected_source
                and e["target"] == expected_target
                and e["op"] == r["op"]
                and e["source_mult"] == expected_source_mult
                and e["target_mult"] == expected_target_mult
                and e.get("source_role", "") == expected_source_role
                and e.get("target_role", "") == expected_target_role
                and e["label"] == expected_label
            ):
                candidate = i
                break
        if candidate is None:
            problems.append(
                f"relazione '{r['raw']}' non trovata (tradotta) in plantuml.txt — "
                f"attesa {expected_source} {r['op']} {expected_target}, mult "
                f"{expected_source_mult!r}/{expected_target_mult!r}, ruoli "
                f"{expected_source_role!r}/{expected_target_role!r}, label {expected_label!r}"
            )
            continue
        used_idx.add(candidate)

    assoc_it = [r for r in rels_it if r["kind"] == "assoc_class"]
    assoc_en = [r for r in rels_en if r["kind"] == "assoc_class"]
    if len(assoc_it) != len(assoc_en):
        problems.append(f"numero di classi associative diverso: it={len(assoc_it)} en={len(assoc_en)}")

    return problems


def italian_terms_in_text(label: str, text: str, it_only_terms: list[str]) -> list[str]:
    problems = []
    for term in it_only_terms:
        if re.search(r"\b" + re.escape(term) + r"\b", text):
            problems.append(f"{label}: termine italiano residuo '{term}'")
    return problems


def check_no_residual_italian(folder: Path, glossary: dict[str, str]) -> list[str]:
    it_only_terms = [k for k, v in glossary.items() if k.lower() != v.lower()]
    problems = []
    for fname in ("description.md", "plantuml.txt"):
        path = folder / fname
        if not path.exists():
            continue
        problems += italian_terms_in_text(fname, path.read_text(encoding="utf-8"), it_only_terms)
    return problems


def collect_apollon_json_strings(diagram: dict) -> str:
    """Concatena tutti i campi testuali del JSON Apollon compilato che
    dovrebbero essere in inglese: nomi di nodo/attributo/metodo, etichette e
    ruoli degli edge. Non include id/uuid/tipi di sistema (source/target/type)."""
    parts = []
    for n in diagram.get("nodes", []):
        parts.append(n["data"].get("name", ""))
        for a in n["data"].get("attributes", []):
            parts.append(a.get("name", ""))
        for m in n["data"].get("methods", []):
            parts.append(m.get("name", ""))
    for e in diagram.get("edges", []):
        d = e.get("data", {})
        parts.append(d.get("label", "") or "")
        parts.append(d.get("sourceRole", "") or "")
        parts.append(d.get("targetRole", "") or "")
    return "\n".join(parts)


def check_no_residual_italian_in_apollon_json(folder: Path, glossary: dict[str, str]) -> list[str]:
    """Controlla corpus/processed/apollon/<id>.json — il JSON che finisce
    davvero nella pipeline/nei pochi-shot — non solo plantuml.txt: un bug nella
    conversione potrebbe lasciar passare un termine italiano anche se
    plantuml.txt e' pulito."""
    apollon_path = Path(__file__).parent / "processed" / "apollon" / f"{folder.name}.json"
    if not apollon_path.exists():
        return [f"{apollon_path.name}: non trovato — esegui prima corpus/apollon_convert.py"]
    diagram = json.loads(apollon_path.read_text(encoding="utf-8"))
    it_only_terms = [k for k, v in glossary.items() if k.lower() != v.lower()]
    text = collect_apollon_json_strings(diagram)
    return italian_terms_in_text(apollon_path.name, text, it_only_terms)


def check_translation_coverage(classes_en, rels_en, glossary: dict[str, str]) -> list[str]:
    problems = []
    translated_values = set(glossary.values())
    for name_en, pc_en in classes_en.items():
        if pc_en.placeholder:
            continue
        if name_en not in translated_values:
            problems.append(f"classe '{name_en}' in plantuml.txt non e' un valore di traduzione nel glossario")
        for attr_name, attr_type in pc_en.attributes:
            if attr_name not in translated_values:
                problems.append(f"attributo '{attr_name}' (classe {name_en}) non e' un valore di traduzione nel glossario")
            if attr_type and attr_type.lower() not in PRIMITIVE_TYPES and attr_type not in translated_values:
                problems.append(f"tipo '{attr_type}' (attributo di {name_en}) non e' un valore di traduzione ne' un tipo primitivo")
    for r in rels_en:
        if r["kind"] != "binary":
            continue
        if r["label"] and r["label"].lstrip("+") not in translated_values:
            problems.append(f"etichetta '{r['label']}' in plantuml.txt non e' un valore di traduzione nel glossario")
        for role in (r.get("source_role", ""), r.get("target_role", "")):
            if role and role not in translated_values:
                problems.append(f"ruolo '{role}' in plantuml.txt non e' un valore di traduzione nel glossario")
    return problems


def check_exercise(folder: Path) -> list[str]:
    problems: list[str] = []
    required = ["plantuml_it.txt", "plantuml.txt", "glossary.json", "description.md", "transcription_notes.md"]
    missing = [f for f in required if not (folder / f).exists()]
    if missing:
        return [f"{folder.name}: file mancanti {missing}"]

    glossary = load_glossary(folder)
    text_it = (folder / "plantuml_it.txt").read_text(encoding="utf-8")
    text_en = (folder / "plantuml.txt").read_text(encoding="utf-8")

    classes_it, rels_it, warn_it, unsupported_it = ac.parse_plantuml(text_it)
    classes_en, rels_en, warn_en, unsupported_en = ac.parse_plantuml(text_en)

    if unsupported_it or unsupported_en:
        problems.append(f"costrutti non supportati dal parser: it={unsupported_it} en={unsupported_en}")

    problems += [f"[copertura glossario] {p}" for p in check_glossary_coverage(folder, glossary, classes_it, rels_it)]
    problems += [f"[corrispondenza strutturale] {p}" for p in check_structural_correspondence(classes_it, rels_it, classes_en, rels_en, glossary)]
    problems += [f"[copertura traduzione] {p}" for p in check_translation_coverage(classes_en, rels_en, glossary)]
    problems += [f"[residuo italiano] {p}" for p in check_no_residual_italian(folder, glossary)]
    problems += [f"[residuo italiano JSON Apollon] {p}" for p in check_no_residual_italian_in_apollon_json(folder, glossary)]

    return [f"{folder.name}: {p}" for p in problems]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("uso: python corpus/check_translated.py <cartella_esercizio> | --all")

    if sys.argv[1] == "--all":
        folders = sorted(p for p in TRANSLATED_IT_DIR.iterdir() if p.is_dir() and not p.name.startswith("_"))
    else:
        folders = [Path(sys.argv[1])]

    all_problems: list[str] = []
    for folder in folders:
        problems = check_exercise(folder)
        all_problems += problems
        status = "OK" if not problems else f"{len(problems)} problemi"
        print(f"{folder.name}: {status}")
        for p in problems:
            print(f"  - {p}")

    if all_problems:
        raise SystemExit(f"\n{len(all_problems)} problemi totali trovati.")
    print(f"\nTutti i controlli superati su {len(folders)} esercizio/i.")


if __name__ == "__main__":
    main()
