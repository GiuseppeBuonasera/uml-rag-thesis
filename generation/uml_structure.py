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
# Specifica: docs/compact_format.md (voce 90). Chiavi vuote omesse; kind omesso quando "class". Il VERSO e' dato da
# chiavi che dicono il ruolo (decisione dello STOP 1): composizione / aggregazione "whole" / "part", generalizzazione /
# realizzazione "child" / "parent", associazioni "source" / "target"; l'espansore converte nel verso di Apollon.

COMPACT_REL_TYPES = {"ClassBidirectional": "association", "ClassUnidirectional": "unidirectional",
                     "ClassDependency": "dependency", "ClassComposition": "composition",
                     "ClassAggregation": "aggregation", "ClassInheritance": "inheritance",
                     "ClassRealization": "realization"}
FROM_COMPACT_REL = {v: k for k, v in COMPACT_REL_TYPES.items()}
# famiglia -> {chiave del compatto: campo di UMLRelation (verso di Apollon)}; le prime due chiavi sono gli estremi
FAMILY_KEYS = {
    "source_target": {"source": "source", "target": "target", "label": "label",
                      "sourceMultiplicity": "source_multiplicity", "targetMultiplicity": "target_multiplicity",
                      "sourceRole": "source_role", "targetRole": "target_role"},
    # Apollon: sorgente = parte, destinazione = tutto (il rombo e' sul target)
    "whole_part": {"whole": "target", "part": "source", "label": "label",
                   "wholeMultiplicity": "target_multiplicity", "partMultiplicity": "source_multiplicity",
                   "wholeRole": "target_role", "partRole": "source_role"},
    # Apollon: sorgente = figlia / classe che implementa, destinazione = madre / interfaccia; nient'altro
    "child_parent": {"child": "source", "parent": "target"},
}
REL_FAMILY = {"association": "source_target", "unidirectional": "source_target", "dependency": "source_target",
              "composition": "whole_part", "aggregation": "whole_part",
              "inheritance": "child_parent", "realization": "child_parent"}
CLASS_KEYS = ("name", "kind", "attributes", "methods", "values")


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
        typ = COMPACT_REL_TYPES[r.type]
        keys = FAMILY_KEYS[REL_FAMILY[typ]]
        d = {"type": typ}
        for i, (k, attr) in enumerate(keys.items()):
            if i < 2 or getattr(r, attr):  # gli estremi sempre, il resto solo se non vuoto
                d[k] = getattr(r, attr)
        lost = [a for a in ("label", "source_multiplicity", "target_multiplicity", "source_role", "target_role")
                if getattr(r, a) and a not in keys.values()]
        if lost:  # generalizzazione con etichetta / molteplicita': il convertitore le toglierebbe comunque
            raise StructureError(f"{typ} {r.source} -> {r.target}: campi non rappresentabili nel compatto {lost}")
        rels.append(d)
    return {"classes": classes, "relations": rels}


def read_compact(data, strict: bool = True) -> tuple[UMLStructure, list[tuple[str, str]]]:
    """JSON compatto (gia' decodificato) -> (struttura, scarti). strict=True: il primo scostamento dalla specifica
    solleva StructureError. strict=False (post-processing delle risposte): ogni elemento non conforme si SCARTA (o si
    ignora la chiave) e si registra come (categoria, dettaglio); nulla viene riparato o inventato. Le chiavi presenti
    ma vuote sono ammesse (non sono scarti)."""
    issues: list[tuple[str, str]] = []

    def issue(cat: str, detail: str) -> None:
        if strict:
            raise StructureError(f"{cat}: {detail}")
        issues.append((cat, detail))

    if not isinstance(data, dict):
        raise StructureError("il primo livello non e' un oggetto JSON")
    for k in data:
        if k not in ("classes", "relations"):
            issue("chiave di primo livello non prevista (ignorata)", repr(k))
    if not isinstance(data.get("classes"), list):
        raise StructureError("manca la lista 'classes'")
    st = UMLStructure()
    for c in data["classes"]:
        if not isinstance(c, dict) or not isinstance(c.get("name"), str) or not c["name"].strip():
            issue("classe senza nome (scartata)", repr(c)[:80])
            continue
        name = c["name"]
        for k in c:
            if k not in CLASS_KEYS:
                issue("chiave di classe non prevista (ignorata)", f"{name}.{k}")
        kind = c.get("kind") or "class"
        if kind not in KINDS:
            issue("kind non previsto (classe scartata)", f"{name}: {kind!r}")
            continue
        if name in st.class_names():
            issue("classe ripetuta (seconda scartata)", name)
            continue
        lists = {}
        for k in ("attributes", "methods", "values"):
            v = c.get(k) or []
            if not isinstance(v, list):
                issue(f"'{k}' non e' una lista (ignorato)", name)
                v = []
            bad = [x for x in v if not isinstance(x, str) or not x.strip()]
            for x in bad:
                issue(f"elemento di '{k}' non stringa o vuoto (scartato)", f"{name}: {x!r}"[:80])
            lists[k] = [x for x in v if isinstance(x, str) and x.strip()]
        if kind == "enum":
            for k in ("attributes", "methods"):
                if lists[k]:
                    issue(f"enum con '{k}' (ignorati: i valori vanno in 'values')", name)
            st.classes.append(UMLClass(name, kind, lists["values"], []))
        else:
            if lists["values"]:
                issue("'values' su una classe non enum (ignorati)", name)
            st.classes.append(UMLClass(name, kind, lists["attributes"], lists["methods"]))
    rels = data.get("relations") or []
    if not isinstance(rels, list):
        issue("'relations' non e' una lista (ignorata)", "")
        rels = []
    names = set(st.class_names())
    for r in rels:
        if not isinstance(r, dict) or r.get("type") not in REL_FAMILY:
            issue("tipo di relazione non previsto (relazione scartata)", repr(r.get("type") if isinstance(r, dict) else r)[:80])
            continue
        typ, keys = r["type"], FAMILY_KEYS[REL_FAMILY[r["type"]]]
        ends = list(keys)[:2]
        known = {k for fk in FAMILY_KEYS.values() for k in fk}
        # chiavi di altre famiglie presenti ma VUOTE: nessuna informazione, ammesse come le chiavi vuote (STOP 1)
        others = [k for k in r if k != "type" and k not in keys and not (k in known and r[k] in ("", None))]
        wrong_ends = [k for k in others if any(k in fk for fk in FAMILY_KEYS.values())]
        if any(not isinstance(r.get(e), str) or not r.get(e) for e in ends):
            cat = ("chiavi di verso di un'altra famiglia (relazione scartata)" if wrong_ends
                   else "estremo mancante (relazione scartata)")
            issue(cat, f"{typ}: servono {ends}, presenti {sorted(k for k in r if k != 'type')}")
            continue
        for k in others:
            issue("chiave di relazione non prevista (ignorata)", f"{typ} {r[ends[0]]}-{r[ends[1]]}: {k}")
        missing = [r[e] for e in ends if r[e] not in names]
        if missing:
            issue("relazione verso una classe non dichiarata (scartata)", f"{typ} {r[ends[0]]}-{r[ends[1]]}: {missing}")
            continue
        vals = {}
        for k, attr in keys.items():
            v = r.get(k, "")
            if v is None:
                v = ""
            if not isinstance(v, str):
                issue("valore non stringa (ignorato)", f"{typ} {r[ends[0]]}-{r[ends[1]]}: {k}={v!r}")
                v = ""
            vals[attr] = v
        st.relations.append(UMLRelation(FROM_COMPACT_REL[typ], **vals))
    return st, issues


def from_compact(data: dict) -> UMLStructure:
    """JSON compatto -> struttura, conversione STRETTA (esempi, controlli): qualunque scostamento solleva errore."""
    return read_compact(data, strict=True)[0]


def apollon_to_compact(diagram: dict) -> dict:
    """Apollon completo (es. un esempio del corpus) -> JSON compatto per il prompt."""
    return to_compact(structure_from_apollon(diagram))


def compact_to_apollon(data: dict, model_id: str) -> tuple[dict, list[str]]:
    """JSON compatto -> struttura -> Apollon completo (formato di consegna)."""
    return expand(from_compact(data), model_id)
