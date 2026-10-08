"""
Post-processing della strada "JSON compatto" (2026-10-08, FASE 2, voce 91): risposta nel formato compatto
(docs/compact_format.md) -> struttura comune -> espansore unico (generation/uml_structure.py) -> GLI STESSI controlli
L2-L4 delle altre strade (generation/postprocess.check_l2_l4). Nessuna chiamata a un LLM.

Livelli propri (cumulativi), come P0 / P1b / P1 della strada PlantUML:
  C0   JSON trovato: stessa estrazione di postprocess.py (tolti i blocchi di ragionamento; risposta intera, blocco ```
       o oggetto {...} bilanciato; testo attorno ammesso e registrato come diagnostico extra_text);
  C1   JSON valido: si decodifica ed e' un oggetto;
  C2b  conversione TOLLERANTE riuscita (uml_structure.read_compact con strict=False): "classes" e' una lista e resta
       almeno una classe; ogni elemento non conforme e' SCARTATO (o la chiave ignorata) e registrato con categoria e
       dettaglio in `compact_issues`; nulla viene riparato o inventato (le chiavi presenti ma vuote sono ammesse);
  C2   come C2b e nessuno scarto: conforme alla specifica (classi uniche, relazioni verso classi esistenti con le
       chiavi della propria famiglia, tipi dell'elenco chiuso);
  poi espansore -> Apollon completo e L2 schema, L3 integrita', L4 stile. Come per PlantUML, superato C2b il livello
  e' 1 (l'Apollon prodotto e' JSON per costruzione).
Troncamento: come postprocess.validate_response, `truncated` se finish_reason = length e il JSON non si estrae o non
si decodifica (un oggetto che si decodifica e' sintatticamente completo).
Normalizzazioni dell'espansore (stesse funzioni del convertitore del Passo 1: tipi noti, visibilita' -> "+",
molteplicita' "n" -> "*"): contate a parte in `normalizations`, per tipo; non sono scarti.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import postprocess as pp  # noqa: E402
import uml_structure as us  # noqa: E402

SCHEMA_PATH = HERE / "schemas" / "compact_generation.schema.json"
MAX_RELATIONS = 39  # come lo schema di generazione dell'Apollon (3 x 13, massimo dei GT selezionabili, voce 78)


@dataclass
class CompactValidation(pp.Validation):
    C0_found: bool = False
    C1_valid_json: bool = False
    C2b_converted: bool = False
    C2_clean: bool = False
    compact_issues: list = field(default_factory=list)  # [(categoria, dettaglio)]
    normalizations: dict = field(default_factory=dict)  # tipo -> numero (non scarti)

    def row(self) -> dict:
        d = super().row()
        d["compact_issues_count"] = len(self.compact_issues)
        d["compact_issues"] = json.dumps(dict(Counter(c for c, _ in self.compact_issues)), ensure_ascii=False,
                                         sort_keys=True)
        d["normalizations"] = json.dumps(self.normalizations, sort_keys=True)
        return d


def normalizations(st: us.UMLStructure, diagram: dict) -> dict:
    """Differenze tra quanto scritto nel compatto e quanto reso dall'espansore (stesse posizioni)."""
    back = us.structure_from_apollon(diagram)
    c = Counter()
    for a, b in zip(st.classes, back.classes):
        c["attributi"] += sum(x != y for x, y in zip(a.attributes, b.attributes))
        c["metodi"] += sum(x != y for x, y in zip(a.methods, b.methods))
    for a, b in zip(st.relations, back.relations):
        c["molteplicita'"] += (a.source_multiplicity != b.source_multiplicity) + \
                              (a.target_multiplicity != b.target_multiplicity)
    return {k: v for k, v in sorted(c.items()) if v}


def validate_compact_response(text: str, finish_reason: str | None, model_id: str) -> CompactValidation:
    v = CompactValidation(finish_reason=finish_reason, truncated=finish_reason == "length")
    body, v.reasoning_removed = pp.strip_reasoning(text or "")
    cand, v.extraction, extra = pp.extract_json(body)
    if cand is None:
        v.failure = ("truncated" if v.truncated else
                     "incomplete_json" if pp._balanced_objects(body)[1] else "no_json")
        return v
    v.C0_found, v.L0_extracted, v.level = True, True, 0
    try:
        data = json.loads(cand)
    except json.JSONDecodeError as e:
        v.failure, v.errors["C1"] = ("truncated" if v.truncated else "invalid_json"), [str(e)]
        return v
    if not isinstance(data, dict):
        v.failure, v.errors["C1"] = "not_object", [type(data).__name__]
        return v
    v.C1_valid_json = True
    try:
        st, v.compact_issues = us.read_compact(data, strict=False)
    except us.StructureError as e:  # primo livello non conforme (manca la lista "classes")
        v.failure, v.errors["C2"] = "not_compact", [str(e)]
        return v
    if v.compact_issues:
        v.errors["C2"] = [f"{c}: {d}" for c, d in v.compact_issues]
    if not st.classes:
        v.failure = "no_classes"
        return v
    try:
        diagram, _ = us.expand(st, model_id)
    except us.StructureError as e:  # non dovrebbe accadere dopo la lettura tollerante
        v.failure, v.errors["C2"] = "expand_error", [str(e)]
        return v
    v.C2b_converted, v.C2_clean = True, not v.compact_issues
    v.L1_json, v.level, v.diagram = True, 1, diagram
    v.normalizations = normalizations(st, diagram)
    # diagnostici di formato della RISPOSTA (il resto dell'Apollon lo produce l'espansore)
    v.format_issues = {"extra_text": True} if extra else {}
    return pp.check_l2_l4(v, diagram)


# --- schema per la generazione vincolata (PREPARATO, DISATTIVATO: nessuna config lo usa) ---------------------------


def generation_schema() -> dict:
    """JSON Schema del formato compatto per response_format (grammatica di llama.cpp: niente $ref; anyOf per le tre
    famiglie di relazione). Non vincola i riferimenti per nome (come lo schema Apollon non vincola gli id)."""
    s = {"type": "string"}
    strings = {"type": "array", "items": {"type": "string"}}

    def family(types: list[str], keys: dict) -> dict:
        ends = list(keys)[:2]
        props = {"type": {"type": "string", "enum": types}, **{k: s for k in keys}}
        return {"type": "object", "properties": props, "required": ["type", *ends], "additionalProperties": False}

    rel = {"anyOf": [family([t for t, f in us.REL_FAMILY.items() if f == fam], keys)
                     for fam, keys in us.FAMILY_KEYS.items()]}
    cls = {"type": "object", "properties": {"name": s, "kind": {"type": "string", "enum": list(us.KINDS)},
                                            "attributes": strings, "methods": strings, "values": strings},
           "required": ["name"], "additionalProperties": False}
    return {"$schema": "http://json-schema.org/draft-07/schema#", "title": "Compact class diagram (generation)",
            "type": "object", "properties": {"classes": {"type": "array", "items": cls, "minItems": 1},
                                             "relations": {"type": "array", "items": rel,
                                                           "maxItems": MAX_RELATIONS}},
            "required": ["classes", "relations"], "additionalProperties": False}


def write_schema() -> Path:
    SCHEMA_PATH.write_text(json.dumps(generation_schema(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return SCHEMA_PATH


if __name__ == "__main__":  # rigenera lo schema (disattivato) e verifica che coincida con il codice
    print(f"scritto {write_schema()}")
