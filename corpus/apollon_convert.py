"""
Converte i diagrammi di riferimento PlantUML in corpus/processed/corpus.jsonl nel
formato di output scelto per il progetto, Apollon JSON (vedi docs/decisions.md,
2026-09-22).

Perche' serve: il corpus raccolto (corpus/raw/models/*/plantuml.txt) e' in PlantUML,
ma la generazione/valutazione finale usa Apollon JSON (schema confermato leggendo
@ls1intum/apollon@3.4.6, pacchetto npm dell'editor Apollon). I pochi-shot mostrati
all'LLM devono essere nello stesso formato che gli si chiede di produrre.

Schema Apollon confermato (non dedotto): "Class" / "AbstractClass" / "Enumeration"
sono tipi di elemento validi (uml-class-diagram/{uml-class,uml-abstract-class,
uml-enumeration}); i valori di un'enumerazione sono modellati come "ClassAttribute"
di proprieta' dell'elemento Enumeration (stesso meccanismo degli attributi di classe).
Per le relazioni si segue la convenzione imposta dal prompt.docx del progetto (non lo
schema "nativo" di Apollon, che avrebbe anche "ClassInheritance"): tutte le relazioni
semplici e l'ereditarieta' usano "ClassBidirectional" (l'ereditarieta' con
name="is-a" e molteplicita' vuote), aggregazioni/composizioni usano rispettivamente
"ClassAggregation" / "ClassComposition" — cosi' i pochi-shot restano coerenti con cio'
che il prompt chiede all'LLM di generare.

Limiti noti (vedi anche i "conversion_warnings" scritti per ciascun record):
- Il costrutto "classe associativa" di PlantUML, es. "(A,B) .. C", non ha un
  equivalente diretto documentato in Apollon: viene approssimato con due relazioni
  semplici C--A e C--B, entrambe di molteplicita' "1". E' un'approssimazione, non la
  semantica esatta di una classe associativa.
- I due casi di vincolo XOR modellati con "note \"{XOR}\" as N" (FilmSet,
  TransportCompany) non sono rappresentati: non esiste un costrutto equivalente
  documentato, quindi vengono scartati con un warning invece di essere inventati.
- Il layout (bounds/path) e' calcolato con una griglia semplice deterministica, non
  rispecchia il posizionamento originale del diagramma PlantUML (che non lo
  specifica comunque, essendo testuale).

Uso:
    python corpus/apollon_convert.py
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

NAMESPACE = uuid.UUID("a5f3d2b0-6b8e-4e6a-9b1f-9b7f6f6b0a11")  # namespace fisso per id riproducibili

CORPUS_JSONL = Path(__file__).parent / "processed" / "corpus.jsonl"
APOLLON_OUT_DIR = Path(__file__).parent / "processed" / "apollon"

# --- Riconoscimento delle relazioni --------------------------------------------

OPS = [
    "<|--", "--|>", "<|-", "-|>", "<-->", "*-->", "*->", "-->", "<--",
    "..>", "<..", "*--", "--*", "o--", "--o", "*-", "-*", "--", "..", "-o", "o-", "-", ".",
]
_OPS_ALT = "|".join(re.escape(o) for o in sorted(OPS, key=len, reverse=True))
REL_RE = re.compile(
    r'^\s*([\w]+)\s*(?:"([^"]*)")?\s*'
    r"(" + _OPS_ALT + r')\s*'
    r'(?:"([^"]*)")?\s*([\w]+)\s*(?::\s*(.*))?\s*$'
)
ASSOC1_RE = re.compile(r"^\s*(\w+)\s*\.{1,2}\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*$")
ASSOC2_RE = re.compile(r"^\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*\.{1,2}\s*(\w+)\s*$")
NOTE_RE = re.compile(r"^note\b.*\bas\s+(\w+)", re.IGNORECASE)
CLASS_HEADER_RE = re.compile(
    r"^(abstract\s+class|class|enum)\s+(\w+)(?:\s*<<\w+>>)?\s*(\{)?\s*(\})?\s*$"
)


def stable_id(seed: str) -> str:
    return str(uuid.uuid5(NAMESPACE, seed))


# --- Parsing del PlantUML --------------------------------------------------------


class ParsedClass:
    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind  # "class" | "abstract class" | "enum"
        self.attributes: list[tuple[str, str]] = []  # (nome, tipo) — tipo vuoto per i valori enum
        self.methods: list[str] = []
        self.placeholder = False  # creata perche' referenziata ma mai dichiarata


def parse_plantuml(text: str) -> tuple[dict[str, ParsedClass], list[dict], list[str]]:
    classes: dict[str, ParsedClass] = {}
    relationships: list[dict] = []
    warnings: list[str] = []
    notes: set[str] = set()

    current: ParsedClass | None = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("@"):
            continue

        if current is not None:
            if line == "}":
                current = None
                continue
            if current.kind == "enum":
                current.attributes.append((line, ""))
            elif "(" in line:
                current.methods.append(line)
            else:
                parts = line.rsplit(None, 1)
                if len(parts) == 2:
                    current.attributes.append((parts[1], parts[0]))
                else:
                    current.attributes.append((line, ""))
            continue

        m = CLASS_HEADER_RE.match(line)
        if m:
            kind, name, has_open, has_close = m.groups()
            pc = ParsedClass(name, kind)
            classes[name] = pc
            if has_open and not has_close:
                current = pc
            continue

        note_m = NOTE_RE.match(line)
        if note_m:
            notes.add(note_m.group(1))
            continue

        assoc_m = ASSOC1_RE.match(line) or ASSOC2_RE.match(line)
        if assoc_m:
            g = assoc_m.groups()
            # ASSOC1: (label, A, B) — "label .. (A,B)"; ASSOC2: (A, B, label) — "(A,B) .. label"
            if ASSOC1_RE.match(line):
                label, a, b = g
            else:
                a, b, label = g
            if label in notes:
                warnings.append(
                    f"scartato vincolo/nota '{label}' su ({a},{b}): nessun costrutto Apollon "
                    "equivalente documentato"
                )
                continue
            relationships.append({"kind": "assoc_class", "assoc": label, "a": a, "b": b, "raw": line})
            continue

        m = REL_RE.match(line)
        if m:
            src, src_mult, op, tgt_mult, tgt, label = m.groups()
            relationships.append(
                {
                    "kind": "binary",
                    "source": src,
                    "source_mult": src_mult or "",
                    "op": op,
                    "target_mult": tgt_mult or "",
                    "target": tgt,
                    "label": (label or "").strip(),
                    "raw": line,
                }
            )
            continue

        warnings.append(f"riga non riconosciuta e ignorata: {line!r}")

    # Crea placeholder per classi referenziate ma mai dichiarate (dati di origine incompleti)
    referenced = set()
    for r in relationships:
        if r["kind"] == "binary":
            referenced.add(r["source"])
            referenced.add(r["target"])
        else:
            referenced.add(r["a"])
            referenced.add(r["b"])
            referenced.add(r["assoc"])
    for name in referenced:
        if name not in classes:
            pc = ParsedClass(name, "class")
            pc.placeholder = True
            classes[name] = pc
            warnings.append(
                f"classe '{name}' referenziata in una relazione ma mai dichiarata nel PlantUML "
                "sorgente: creata come placeholder senza attributi"
            )

    return classes, relationships, warnings


INHERITANCE_OPS = {"<|--", "--|>", "<|-", "-|>"}
AGGREGATION_OPS = {"o--", "--o", "-o", "o-"}
COMPOSITION_OPS = {"*--", "--*", "*-", "-*", "*-->", "*->"}


def relationship_kind(op: str, source: str, target: str) -> tuple[str, str, str, str]:
    """Ritorna (apollon_type, effective_source, effective_target, name) applicando la
    convenzione del prompt.docx del progetto (non lo schema nativo Apollon)."""
    if op in INHERITANCE_OPS:
        # regola: il lato adiacente al simbolo '|' (triangolo) e' la superclasse
        if op in ("<|--", "<|-"):
            parent, child = source, target
        else:  # "--|>", "-|>"
            parent, child = target, source
        return "ClassBidirectional", child, parent, "is-a"
    if op in AGGREGATION_OPS:
        # 'o' adiacente = lato aggregatore (contenitore)
        if op in ("o--", "o-"):
            whole, part = source, target
        else:  # "--o", "-o"
            whole, part = target, source
        return "ClassAggregation", whole, part, ""
    if op in COMPOSITION_OPS:
        if op in ("*--", "*-", "*-->", "*->"):
            whole, part = source, target
        else:  # "--*", "-*"
            whole, part = target, source
        return "ClassComposition", whole, part, ""
    return "ClassBidirectional", source, target, ""


# --- Layout ------------------------------------------------------------------

ROW_GAP = 60
COL_GAP = 60
CLASS_WIDTH = 220
HEADER_H = 40
MEMBER_H = 30
MARGIN = 40


def layout_classes(classes: dict[str, ParsedClass]) -> dict[str, dict]:
    """Griglia semplice e deterministica: non rispecchia un layout originale (il
    PlantUML testuale non lo specifica)."""
    import math

    names = list(classes.keys())
    ncols = max(1, math.ceil(math.sqrt(len(names))))

    positions: dict[str, dict] = {}
    x = MARGIN
    y = MARGIN
    row_h = 0
    col = 0
    for name in names:
        pc = classes[name]
        n_members = len(pc.attributes) + len(pc.methods)
        height = HEADER_H + max(n_members, 0) * MEMBER_H
        if n_members == 0:
            height = HEADER_H
        positions[name] = {"x": x, "y": y, "width": CLASS_WIDTH, "height": height}
        row_h = max(row_h, height)
        col += 1
        x += CLASS_WIDTH + COL_GAP
        if col >= ncols:
            col = 0
            x = MARGIN
            y += row_h + ROW_GAP
            row_h = 0
    return positions


def edge_direction(from_center: tuple[float, float], to_center: tuple[float, float]) -> str:
    dx = to_center[0] - from_center[0]
    dy = to_center[1] - from_center[1]
    if abs(dx) >= abs(dy):
        return "Right" if dx >= 0 else "Left"
    return "Down" if dy >= 0 else "Up"


def touch_point(box: dict, direction: str) -> tuple[float, float]:
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    if direction == "Right":
        return box["x"] + box["width"], cy
    if direction == "Left":
        return box["x"], cy
    if direction == "Down":
        return cx, box["y"] + box["height"]
    return cx, box["y"]  # Up


# --- Costruzione del JSON Apollon ---------------------------------------------


def build_apollon_json(model_id: str, classes: dict[str, ParsedClass], relationships: list[dict]):
    positions = layout_classes(classes)
    elements: dict[str, dict] = {}
    class_ids: dict[str, str] = {}

    for name, pc in classes.items():
        cls_id = stable_id(f"{model_id}:class:{name}")
        class_ids[name] = cls_id
        box = positions[name]
        elem_type = "Enumeration" if pc.kind == "enum" else ("AbstractClass" if pc.kind == "abstract class" else "Class")

        attr_ids, method_ids = [], []
        offset = 0
        for attr_name, attr_type in pc.attributes:
            attr_id = stable_id(f"{model_id}:attr:{name}:{attr_name}:{offset}")
            display = attr_name if pc.kind == "enum" else f"+ {attr_name} : {attr_type or 'string'}"
            elements[attr_id] = {
                "id": attr_id,
                "name": display,
                "type": "ClassAttribute",
                "owner": cls_id,
                "bounds": {
                    "x": box["x"],
                    "y": box["y"] + HEADER_H + offset * MEMBER_H,
                    "width": box["width"],
                    "height": MEMBER_H,
                },
            }
            attr_ids.append(attr_id)
            offset += 1
        for method_sig in pc.methods:
            method_id = stable_id(f"{model_id}:method:{name}:{method_sig}:{offset}")
            elements[method_id] = {
                "id": method_id,
                "name": method_sig,
                "type": "ClassMethod",
                "owner": cls_id,
                "bounds": {
                    "x": box["x"],
                    "y": box["y"] + HEADER_H + offset * MEMBER_H,
                    "width": box["width"],
                    "height": MEMBER_H,
                },
            }
            method_ids.append(method_id)
            offset += 1

        elements[cls_id] = {
            "id": cls_id,
            "name": name,
            "type": elem_type,
            "owner": None,
            "bounds": box,
            "attributes": attr_ids,
            "methods": method_ids,
        }

    apollon_relationships: dict[str, dict] = {}
    warnings: list[str] = []

    def add_relationship(apollon_type, source_name, target_name, name, source_mult, target_mult):
        if source_name not in class_ids or target_name not in class_ids:
            warnings.append(f"relazione scartata, classe mancante: {source_name} -> {target_name}")
            return
        rel_id = stable_id(f"{model_id}:rel:{source_name}:{target_name}:{apollon_type}:{name}:{len(apollon_relationships)}")
        source_box, target_box = positions[source_name], positions[target_name]
        s_center = (source_box["x"] + source_box["width"] / 2, source_box["y"] + source_box["height"] / 2)
        t_center = (target_box["x"] + target_box["width"] / 2, target_box["y"] + target_box["height"] / 2)
        s_dir = edge_direction(s_center, t_center)
        t_dir = edge_direction(t_center, s_center)
        p1 = touch_point(source_box, s_dir)
        p2 = touch_point(target_box, t_dir)
        bx, by = min(p1[0], p2[0]), min(p1[1], p2[1])
        bw, bh = max(abs(p1[0] - p2[0]), 2), max(abs(p1[1] - p2[1]), 2)
        apollon_relationships[rel_id] = {
            "id": rel_id,
            "name": name,
            "type": apollon_type,
            "owner": None,
            "bounds": {"x": bx, "y": by, "width": bw, "height": bh},
            "path": [
                {"x": p1[0] - bx, "y": p1[1] - by},
                {"x": p2[0] - bx, "y": p2[1] - by},
            ],
            "source": {
                "direction": s_dir,
                "element": class_ids[source_name],
                "multiplicity": source_mult,
                "role": "",
            },
            "target": {
                "direction": t_dir,
                "element": class_ids[target_name],
                "multiplicity": target_mult,
                "role": "",
            },
            "isManuallyLayouted": False,
        }

    for r in relationships:
        if r["kind"] == "binary":
            apollon_type, eff_src, eff_tgt, forced_name = relationship_kind(r["op"], r["source"], r["target"])
            name = forced_name or r["label"]
            src_mult = "" if forced_name else r["source_mult"]
            tgt_mult = "" if forced_name else r["target_mult"]
            add_relationship(apollon_type, eff_src, eff_tgt, name, src_mult, tgt_mult)
        else:  # association class, approssimata con due associazioni semplici
            warnings.append(
                f"classe associativa '{r['assoc']}' tra {r['a']} e {r['b']} approssimata con due "
                "relazioni semplici, entrambe molteplicita' '1' (semantica non esatta)"
            )
            add_relationship("ClassBidirectional", r["assoc"], r["a"], "", "1", "1")
            add_relationship("ClassBidirectional", r["assoc"], r["b"], "", "1", "1")

    max_x = max((b["x"] + b["width"] for b in positions.values()), default=200) + MARGIN
    max_y = max((b["y"] + b["height"] for b in positions.values()), default=200) + MARGIN

    diagram = {
        "version": "3.0.0",
        "type": "ClassDiagram",
        "size": {"width": max_x, "height": max_y},
        "interactive": {"elements": {}, "relationships": {}},
        "elements": elements,
        "relationships": apollon_relationships,
        "assessments": {},
    }
    return diagram, warnings


def verify_apollon_json(diagram: dict, model_id: str) -> list[str]:
    problems = []
    elements = diagram["elements"]
    for eid, el in elements.items():
        if el["id"] != eid:
            problems.append(f"{model_id}: id incoerente per elemento {eid}")
        if el["type"] in ("Class", "AbstractClass", "Enumeration"):
            for member_id in el.get("attributes", []) + el.get("methods", []):
                if member_id not in elements:
                    problems.append(f"{model_id}: membro {member_id} di {el['name']} non trovato tra gli elementi")
        elif el["type"] in ("ClassAttribute", "ClassMethod"):
            if el["owner"] not in elements:
                problems.append(f"{model_id}: owner mancante per {el['name']} ({eid})")
        b = el["bounds"]
        if b["width"] <= 0 or b["height"] <= 0:
            problems.append(f"{model_id}: bounds non positivi per {el['name']}")
    for rid, rel in diagram["relationships"].items():
        if rel["source"]["element"] not in elements or rel["target"]["element"] not in elements:
            problems.append(f"{model_id}: relazione {rid} referenzia un elemento inesistente")
        b = rel["bounds"]
        if b["width"] <= 0 or b["height"] <= 0:
            problems.append(f"{model_id}: bounds non positivi per relazione {rid}")
    return problems


# --- Main ----------------------------------------------------------------------


def main() -> None:
    if not CORPUS_JSONL.exists():
        raise SystemExit(f"{CORPUS_JSONL} non trovato: esegui prima corpus/build_manifest.py")

    records = [json.loads(line) for line in CORPUS_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]

    APOLLON_OUT_DIR.mkdir(parents=True, exist_ok=True)
    total_warnings = 0
    total_problems = 0
    for record in records:
        model_id = record["id"]
        classes, relationships, parse_warnings = parse_plantuml(record["diagram_plantuml"])
        diagram, build_warnings = build_apollon_json(model_id, classes, relationships)
        problems = verify_apollon_json(diagram, model_id)

        warnings = parse_warnings + build_warnings
        total_warnings += len(warnings)
        total_problems += len(problems)

        record["diagram_apollon_json"] = diagram
        record["apollon_conversion_warnings"] = warnings

        out_path = APOLLON_OUT_DIR / f"{model_id}.json"
        out_path.write_text(json.dumps(diagram, ensure_ascii=False, indent=2), encoding="utf-8")

        if problems:
            print(f"[ERRORE] {model_id}: {problems}")

    CORPUS_JSONL.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8"
    )

    assert total_problems == 0, f"{total_problems} problemi di integrita' rilevati, vedi sopra"
    print(f"Convertiti {len(records)} diagrammi. Warning totali (approssimazioni/costrutti non gestiti): {total_warnings}")
    print(f"JSON Apollon scritti in {APOLLON_OUT_DIR}")
    print(f"corpus.jsonl aggiornato con diagram_apollon_json + apollon_conversion_warnings")


if __name__ == "__main__":
    main()
