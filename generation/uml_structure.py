"""
Struttura comune dei diagrammi delle classi (2026-10-08, FASE 1 del formato JSON compatto): rappresentazione
intermedia condivisa da tutte le strade di generazione, e UNICO espansore struttura -> Apollon v4 completo.

    PlantUML (risposta) --parse_plantuml + regola delle etichette--> struttura --espansore--> Apollon completo
    JSON compatto       --from_compact------------------------------> struttura --espansore--> Apollon completo
    Apollon completo    --structure_from_apollon--> struttura --to_compact--> JSON compatto (esempi del prompt)

Struttura (UMLStructure):
  - classi in ordine (UMLClass): nome, tipo "class" | "abstract" | "interface" | "enum", attributi e metodi nella forma
    del corpus ("+ nome : tipo", "+ nome(parametri) : Tipo"; per un enum gli attributi sono i valori);
  - relazioni in ordine (UMLRelation): tipo Apollon (ClassBidirectional, ...), estremi PER NOME con la convenzione di
    Apollon (generalizzazione / realizzazione: sorgente = figlia, destinazione = madre / interfaccia; composizione /
    aggregazione: sorgente = parte, destinazione = tutto; unidirezionale / dipendenza: destinazione = lato della
    freccia), molteplicita', ruoli, etichetta;
  - vincoli di generalizzazione ({disjoint, complete} ...), presenti solo se la fonte e' PlantUML: Apollon non li
    rappresenta (come nel Passo 1, dove vanno nel campo "constraints" del manifest).

NESSUNA LOGICA DUPLICATA (corpus/apollon_convert.py e' in sola lettura): la resa di attributi, metodi, tipi e
molteplicita' esiste solo in build_apollon_json. Percio' structure_from_parsed costruisce l'Apollon con il convertitore
e ne legge la struttura, e l'espansore ricostruisce gli input del convertitore (ParsedClass, relazioni binarie con un
operatore canonico per tipo) e richiama build_apollon_json: id deterministici (uuid5 su id del modello, nome, indice),
layout a griglia, punti e adattamento al canvas sono quelli del Passo 1. Il controllo di sanita'
(generation/compact_sanity_check.py) verifica che il giro restituisca l'Apollon del Passo 1 identico.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "corpus"))
import apollon_convert as ac  # noqa: E402  (sola lettura)

KINDS = ("class", "abstract", "interface", "enum")
KIND_TO_PARSED = {"class": "class", "abstract": "abstract class", "interface": "interface", "enum": "enum"}
# operatore PlantUML canonico per tipo, con il verso di Apollon (relationship_kind: swapped = False)
CANONICAL_OP = {"ClassBidirectional": "--", "ClassUnidirectional": "-->", "ClassInheritance": "--|>",
                "ClassRealization": "..|>", "ClassAggregation": "--o", "ClassComposition": "--*",
                "ClassDependency": "..>"}
for _t, _op in CANONICAL_OP.items():  # coerenza con il convertitore, verificata all'import
    assert ac.relationship_kind(_op)[:2] == (_t, False), (_t, _op)
EDGE_TYPES = tuple(CANONICAL_OP)
NO_LABEL_TYPES = ("ClassInheritance", "ClassRealization")  # il convertitore toglie etichetta, molteplicita' e ruoli


class StructureError(ValueError):
    """Diagramma non riducibile alla struttura (es. relazione verso un nodo inesistente, nomi di classe ripetuti)."""


@dataclass
class UMLClass:
    name: str
    kind: str = "class"
    attributes: list[str] = field(default_factory=list)  # per un enum: i valori
    methods: list[str] = field(default_factory=list)


@dataclass
class UMLRelation:
    type: str
    source: str
    target: str
    label: str = ""
    source_multiplicity: str = ""
    target_multiplicity: str = ""
    source_role: str = ""
    target_role: str = ""


@dataclass
class UMLStructure:
    classes: list[UMLClass] = field(default_factory=list)
    relations: list[UMLRelation] = field(default_factory=list)
    constraints: list[dict] = field(default_factory=list)  # solo da PlantUML (Apollon non li rappresenta)
    warnings: list[str] = field(default_factory=list)  # warning del convertitore (attributi senza tipo, ...)

    def class_names(self) -> list[str]:
        return [c.name for c in self.classes]


# --- Apollon completo -> struttura ----------------------------------------------------------------------------------


def node_kind(data: dict) -> str:
    stereo = data.get("stereotype")
    if data.get("isAbstract"):
        if stereo:
            raise StructureError(f"classe {data.get('name')!r} astratta con stereotipo {stereo!r}")
        return "abstract"
    if stereo in (None, ""):
        return "class"
    if stereo == "enumeration":
        return "enum"
    if stereo == "interface":
        return "interface"
    raise StructureError(f"stereotipo non previsto {stereo!r} sulla classe {data.get('name')!r}")


def structure_from_apollon(diagram: dict) -> UMLStructure:
    """Legge la struttura da un Apollon v4 completo (id, layout e metadati si scartano)."""
    st = UMLStructure()
    by_id = {}
    for n in diagram.get("nodes", []):
        d = n["data"]
        c = UMLClass(d["name"], node_kind(d), [a["name"] for a in d.get("attributes", [])],
                     [m["name"] for m in d.get("methods", [])])
        if c.name in st.class_names():
            raise StructureError(f"nome di classe ripetuto: {c.name!r}")
        if n["id"] in by_id:
            raise StructureError(f"id di nodo ripetuto: {n['id']!r}")
        by_id[n["id"]] = c.name
        st.classes.append(c)
    for e in diagram.get("edges", []):
        if e["source"] not in by_id or e["target"] not in by_id:
            raise StructureError(f"relazione {e.get('id')!r} verso un nodo inesistente")
        if e["type"] not in CANONICAL_OP:
            raise StructureError(f"tipo di relazione non previsto: {e['type']!r}")
        x = e.get("data") or {}
        st.relations.append(UMLRelation(e["type"], by_id[e["source"]], by_id[e["target"]], x.get("label", ""),
                                        x.get("sourceMultiplicity", ""), x.get("targetMultiplicity", ""),
                                        x.get("sourceRole", ""), x.get("targetRole", "")))
    return st


def structure_from_parsed(classes: dict, relationships: list[dict], model_id: str,
                          constraints: list[dict] | None = None) -> UMLStructure:
    """Uscita del parser del convertitore (classi, relazioni gia' passate per la regola delle etichette e per
    reify_association_classes) -> struttura. La resa la fa build_apollon_json (nessuna logica duplicata)."""
    diagram, warnings = ac.build_apollon_json(model_id, classes, relationships)
    st = structure_from_apollon(diagram)
    st.constraints, st.warnings = list(constraints or []), warnings
    return st


# --- espansore: struttura -> Apollon completo ----------------------------------------------------------------------


def to_converter_input(st: UMLStructure) -> tuple[dict, list[dict]]:
    """Struttura -> input di build_apollon_json (ParsedClass e relazioni binarie con operatore canonico)."""
    classes = {}
    for c in st.classes:
        if c.kind not in KINDS:
            raise StructureError(f"tipo di classe non previsto {c.kind!r} ({c.name})")
        if c.name in classes:
            raise StructureError(f"nome di classe ripetuto: {c.name!r}")
        pc = ac.ParsedClass(c.name, KIND_TO_PARSED[c.kind])
        for a in c.attributes:
            if c.kind == "enum":
                pc.attributes.append((a, ""))
                pc.attribute_extras.append({"default": None, "modifiers": []})
            else:
                name, typ, extra = ac.parse_attribute(a)
                pc.attributes.append((name, typ))
                pc.attribute_extras.append(extra)
        pc.methods = list(c.methods)
        classes[c.name] = pc
    rels = []
    for r in st.relations:
        if r.type not in CANONICAL_OP:
            raise StructureError(f"tipo di relazione non previsto: {r.type!r}")
        for end in (r.source, r.target):
            if end not in classes:
                raise StructureError(f"relazione {r.type} {r.source} -> {r.target}: classe {end!r} non dichiarata")
        rels.append({"kind": "binary", "source": r.source, "target": r.target, "op": CANONICAL_OP[r.type],
                     "source_mult": r.source_multiplicity, "target_mult": r.target_multiplicity,
                     "source_role": r.source_role, "target_role": r.target_role, "label": r.label,
                     "raw": f"(struttura) {r.source} {CANONICAL_OP[r.type]} {r.target}"})
    return classes, rels


def expand(st: UMLStructure, model_id: str) -> tuple[dict, list[str]]:
    """UNICO espansore: struttura -> Apollon v4 completo (id, layout e punti del convertitore del Passo 1)."""
    classes, rels = to_converter_input(st)
    return ac.build_apollon_json(model_id, classes, rels)


# --- formato JSON compatto ------------------------------------------------------------------------------------------
# Specifica: docs/compact_format.md. Chiavi omesse quando vuote; tipo di classe omesso quando "class".

COMPACT_REL_TYPES = {"ClassBidirectional": "association", "ClassUnidirectional": "unidirectional",
                     "ClassInheritance": "inheritance", "ClassRealization": "realization",
                     "ClassAggregation": "aggregation", "ClassComposition": "composition",
                     "ClassDependency": "dependency"}
FROM_COMPACT_REL = {v: k for k, v in COMPACT_REL_TYPES.items()}
REL_KEYS = (("label", "label"), ("sourceMultiplicity", "source_multiplicity"),
            ("targetMultiplicity", "target_multiplicity"), ("sourceRole", "source_role"), ("targetRole", "target_role"))


def to_compact(st: UMLStructure) -> dict:
    classes = []
    for c in st.classes:
        d = {"name": c.name}
        if c.kind != "class":
            d["kind"] = c.kind
        if c.kind == "enum":
            if c.attributes:
                d["values"] = list(c.attributes)
        else:
            if c.attributes:
                d["attributes"] = list(c.attributes)
            if c.methods:
                d["methods"] = list(c.methods)
        classes.append(d)
    rels = []
    for r in st.relations:
        d = {"type": COMPACT_REL_TYPES[r.type], "source": r.source, "target": r.target}
        d.update({k: getattr(r, attr) for k, attr in REL_KEYS if getattr(r, attr)})
        rels.append(d)
    return {"classes": classes, "relations": rels}


def from_compact(data: dict) -> UMLStructure:
    """JSON compatto -> struttura. Conversione STRETTA (FASE 1): qualunque scostamento dalla specifica solleva
    StructureError; la validazione a livelli delle risposte (C0-C2, scarti contati) e' della FASE 2."""
    if not isinstance(data, dict) or set(data) - {"classes", "relations"} or "classes" not in data:
        raise StructureError("oggetto di primo livello: servono 'classes' (e 'relations'), nessun'altra chiave")
    st = UMLStructure()
    for c in data["classes"]:
        extra = set(c) - {"name", "kind", "attributes", "methods", "values"}
        if extra:
            raise StructureError(f"classe {c.get('name')!r}: chiavi non previste {sorted(extra)}")
        kind = c.get("kind", "class")
        if kind not in KINDS:
            raise StructureError(f"classe {c.get('name')!r}: kind {kind!r} non previsto")
        if kind == "enum" and ("attributes" in c or "methods" in c):
            raise StructureError(f"enum {c['name']!r}: usare 'values', non attributi o metodi")
        if kind != "enum" and "values" in c:
            raise StructureError(f"classe {c['name']!r}: 'values' solo per gli enum")
        st.classes.append(UMLClass(c["name"], kind, list(c.get("values" if kind == "enum" else "attributes", [])),
                                   list(c.get("methods", []))))
    names = st.class_names()
    if len(names) != len(set(names)):
        raise StructureError("nomi di classe ripetuti")
    for r in data.get("relations", []):
        extra = set(r) - {"type", "source", "target", *(k for k, _ in REL_KEYS)}
        if extra:
            raise StructureError(f"relazione {r.get('source')!r} -> {r.get('target')!r}: chiavi non previste {sorted(extra)}")
        if r.get("type") not in FROM_COMPACT_REL:
            raise StructureError(f"tipo di relazione non previsto: {r.get('type')!r}")
        st.relations.append(UMLRelation(FROM_COMPACT_REL[r["type"]], r["source"], r["target"],
                                        **{attr: r.get(k, "") for k, attr in REL_KEYS}))
    return st


def apollon_to_compact(diagram: dict) -> dict:
    """Apollon completo (es. un esempio del corpus) -> JSON compatto per il prompt."""
    return to_compact(structure_from_apollon(diagram))


def compact_to_apollon(data: dict, model_id: str) -> tuple[dict, list[str]]:
    """JSON compatto -> struttura -> Apollon completo (formato di consegna)."""
    return expand(from_compact(data), model_id)
