"""
Genera relations_table.md per un esercizio in corpus/raw/translated_it/<Nome>/,
riparsando plantuml_it.txt con apollon_convert.parse_plantuml — MAI scritta a
mano, per non ripetere l'errore di trascrizione del pilota CourseManagement
(2026-09-25, vedi docs/decisions.md): la tabella e' generata dalla stessa
struttura dati usata per costruire plantuml_it.txt/plantuml.txt e per la
pipeline, non da una rilettura indipendente dell'immagine.

Una riga per ogni relazione: classe A (IT ed EN), classe B (IT ed EN), tipo
(associazione / aggregazione / composizione / generalizzazione / dipendenza),
molteplicita' lato A, molteplicita' lato B, ruoli, etichetta. In fondo: numero
totale di classi e di relazioni. I nomi EN sono ottenuti applicando
glossary.json (apply_glossary.apply_glossary), non riparsando plantuml.txt —
la corrispondenza IT/EN esatta e' gia' verificata da check_translated.py.

Uso:
    python corpus/generate_relations_table.py <cartella_esercizio>
    (legge <cartella_esercizio>/plantuml_it.txt e glossary.json, scrive
    <cartella_esercizio>/relations_table.md)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import apollon_convert as ac
import apply_glossary as ag

TYPE_LABELS = {
    "ClassInheritance": "generalizzazione",
    "ClassRealization": "dipendenza (realizzazione)",
    "ClassAggregation": "aggregazione",
    "ClassComposition": "composizione",
    "ClassDependency": "dipendenza",
    "ClassUnidirectional": "associazione",
    "ClassBidirectional": "associazione",
}


def relation_row(r: dict, glossary: dict[str, str]) -> tuple[str, str, str, str, str, str, str, str, str]:
    """(classeA_it, classeA_en, classeB_it, classeB_en, tipo, molt.A, molt.B,
    ruoli, etichetta) — A e B nello stesso ordine source/target del PlantUML
    originale, NON riordinati secondo la convenzione source/target di Apollon
    (quella e' interna alla conversione, qui si riporta la relazione cosi'
    com'e' scritta in plantuml_it.txt)."""
    edge_type, _swapped, _no_label_no_mult = ac.relationship_kind(r["op"])
    tipo = TYPE_LABELS.get(edge_type, edge_type)
    ruoli = []
    if r.get("source_role"):
        ruoli.append(f"A={r['source_role']}")
    if r.get("target_role"):
        ruoli.append(f"B={r['target_role']}")
    return (
        r["source"],
        ag.apply_glossary(r["source"], glossary),
        r["target"],
        ag.apply_glossary(r["target"], glossary),
        tipo,
        r["source_mult"] or "—",
        r["target_mult"] or "—",
        ", ".join(ruoli) if ruoli else "—",
        r["label"] or "—",
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("uso: python corpus/generate_relations_table.py <cartella_esercizio>")
    folder = Path(sys.argv[1])
    it_path = folder / "plantuml_it.txt"
    glossary_path = folder / "glossary.json"
    if not it_path.exists():
        raise SystemExit(f"non trovato: {it_path}")
    if not glossary_path.exists():
        raise SystemExit(f"non trovato: {glossary_path}")

    glossary = ag.load_term_glossary(glossary_path)
    text = it_path.read_text(encoding="utf-8")
    classes, relationships, warnings, unsupported = ac.parse_plantuml(text)
    if unsupported:
        raise SystemExit(f"costrutti non supportati, tabella non generata: {unsupported}")

    n_classes = sum(1 for pc in classes.values() if not pc.placeholder)
    n_placeholder = sum(1 for pc in classes.values() if pc.placeholder)

    lines = [
        f"# Tabella delle relazioni — {folder.name}",
        "",
        f"Generata da `corpus/generate_relations_table.py` a partire da `plantuml_it.txt` "
        f"({sum(1 for r in relationships if r['kind']=='binary')} relazioni binarie, "
        f"{sum(1 for r in relationships if r['kind']=='assoc_class')} classi associative). "
        "Nomi EN da glossary.json.",
        "",
        "| Classe A (IT) | Classe A (EN) | Classe B (IT) | Classe B (EN) | Tipo | Molt. A | Molt. B | Ruoli | Etichetta |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for r in relationships:
        if r["kind"] == "binary":
            a_it, a_en, b_it, b_en, tipo, ma, mb, ruoli, etichetta = relation_row(r, glossary)
            lines.append(f"| {a_it} | {a_en} | {b_it} | {b_en} | {tipo} | {ma} | {mb} | {ruoli} | {etichetta} |")
        elif r["kind"] == "assoc_class":
            assoc_en = ag.apply_glossary(r["assoc"], glossary)
            a_en = ag.apply_glossary(r["a"], glossary)
            b_en = ag.apply_glossary(r["b"], glossary)
            lines.append(
                f"| {r['assoc']} | {assoc_en} | {r['a']}, {r['b']} | {a_en}, {b_en} | classe associativa "
                f"| — | — | — | approssimata con 2 associazioni semplici (vedi apollon_conversion_warnings) |"
            )

    if warnings:
        lines.append("")
        lines.append("## Warning del parser")
        for w in warnings:
            lines.append(f"- {w}")

    lines.append("")
    lines.append("## Totali")
    lines.append(f"- Classi: {n_classes}" + (f" (+ {n_placeholder} placeholder non dichiarate)" if n_placeholder else ""))
    lines.append(f"- Relazioni: {len(relationships)}")

    out_path = folder / "relations_table.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Scritto: {out_path}")


if __name__ == "__main__":
    main()
