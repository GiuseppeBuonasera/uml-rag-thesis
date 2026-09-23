"""
Converte i diagrammi di riferimento PlantUML in corpus/processed/corpus.jsonl nel
formato di output scelto per il progetto: **Apollon v4** (modello wire-format
"4.2.0", pacchetto npm @tumaet/apollon@5.3.0). Sostituisce la conversione verso
Apollon v3 usata fino al 2026-09-23 — vedi docs/decisions.md per il perche' del
cambio ("classi astratte/enum come nodo unico con isAbstract/stereotype invece di
elementi separati con owner", "tipi di relazione nativi come ClassInheritance invece
di un'associazione chiamata 'is-a'", "schema JSON ufficiale pubblicato per validare").

Schema v4 confermato leggendo i sorgenti (non dedotto), non solo lo schema JSON
pubblicato ma anche il codice TypeScript che lo implementa:
- schema JSON ufficiale: @tumaet/apollon/schema/uml-model-4.schema.json (copiato in
  evaluation/uml-model-4.schema.json, usato per la validazione strutturale — vedi
  validate_against_schema). Campi di primo livello richiesti: version, id, title,
  type, nodes, edges, assessments.
- library/lib/types/nodes/NodeProps.ts: un nodo "class" ha in "data" i campi name,
  attributes (lista di {id, name}), methods (lista di {id, name, isAbstract?}),
  stereotype opzionale ("interface" | "enumeration", da
  library/lib/types/nodes/enums/ClassStereotype.ts), isAbstract opzionale a livello
  di classe. Non esistono nodi "AbstractClass"/"Enumeration" separati come in v3:
  restano tutti "type": "class", la distinzione e' dentro "data".
- library/lib/edges/EdgeProps.ts: un edge ha in "data" i campi points (lista di
  {x,y} — assoluti, niente piu' "bounds" separato come in v3), sourceMultiplicity,
  targetMultiplicity, sourceRole, targetRole, label.
- library/lib/nodes/wrappers/DefaultNodeWrapper.tsx (enum HandleId): i punti di
  aggancio centrali di ciascun lato sono letteralmente "top" / "right" / "bottom" /
  "left" (ne esistono altri piu' fini per il trascinamento manuale nell'editor, non
  necessari per una generazione programmatica).
- versionConverter-*.js (bundle compilato): versione corrente del modello = "4.2.0".

Punto NON verificato nei sorgenti (nessun file di marker/arrowhead trovato in tempo
utile): quale estremo di ClassInheritance/ClassRealization porta il triangolo
nell'editor. Si e' assunta la convenzione UML standard (fonte-figlio,
target-superclasse/interfaccia), la stessa gia' usata per il parsing PlantUML e per
la v3. **Da confermare aprendo qualche diagramma convertito nell'editor Apollon
online** (motivo per cui non e' stato ancora spuntato "verifica visiva" nella
checklist di questa decisione).

Limiti noti (vedi anche i "apollon_conversion_warnings" scritti per ciascun record):
- Il costrutto "classe associativa" di PlantUML, es. "(A,B) .. C", non ha un
  equivalente diretto in Apollon: approssimato con due relazioni semplici verso i
  due partecipanti (ClassBidirectional, molteplicita' vuote perche' non ricavabili
  dal testo). La relazione A-B originale, se presente nel sorgente, resta comunque
  tra le relazioni convertite.
- I due casi di vincolo XOR (`note "{XOR}" as N`) non sono rappresentati: nessun
  costrutto equivalente documentato, scartati con un warning.
- Il costrutto "diamante" n-ario nativo di PlantUML (es. "<> diamond" in Cruise) non
  ha equivalente v4 documentato: il modello viene escluso dalla conversione
  (diagram_apollon_json resta None).
- Le classi usate in una relazione ma mai dichiarate con "class X {...}" sono create
  come nodi senza attributi — legale in PlantUML, non un errore nei dati.
- Il layout (position/width/height) e' calcolato con una griglia semplice
  deterministica, non rispecchia un layout originale (il PlantUML testuale non lo
  specifica). Scalato per rientrare nell'area 0-1600 x 0-780 se necessario.

Verifica a piu' livelli, ciascuno con uno scopo diverso:
1. validate_against_schema: conformita' strutturale allo schema JSON ufficiale
   (campi presenti, tipi, enum validi). Non valida il contenuto di "data" (lo schema
   stesso lo lascia libero).
2. verify_apollon_json: integrita' referenziale interna (id univoci, source/target
   degli edge che esistono davvero, dimensioni positive).
3. round_trip_check: contenuto SEMANTICO — nomi/tipi di attributi e molteplicita'
   per estremo — confrontato tra il PlantUML originale e il JSON prodotto, scritta
   senza riusare la logica di relationship_kind (per non validare un bug con la
   stessa funzione che lo ha causato — cosi' erano passati inosservati due bug reali
   nella versione precedente di questo script, trovati in revisione il 2026-09-23).

Uso:
    python corpus/build_manifest.py
    python corpus/apollon_convert.py
"""

from __future__ import annotations

import json
import math
import re
import uuid
from pathlib import Path

NAMESPACE = uuid.UUID("a5f3d2b0-6b8e-4e6a-9b1f-9b7f6f6b0a11")  # namespace fisso per id riproducibili

CORPUS_JSONL = Path(__file__).parent / "processed" / "corpus.jsonl"
APOLLON_OUT_DIR = Path(__file__).parent / "processed" / "apollon"
SCHEMA_PATH = Path(__file__).parent.parent / "evaluation" / "uml-model-4.schema.json"

MODEL_VERSION = "4.2.0"
MAX_CANVAS_WIDTH = 1600
MAX_CANVAS_HEIGHT = 780

# --- Riconoscimento delle relazioni --------------------------------------------

OPS = [
    "<|--", "--|>", "<|-", "-|>", "..|>", "<|..",  # ereditarieta' / realizzazione
    "<-->", "*-->", "*->", "-->", "<--",  # associazioni dirette/bidirezionali
    "..>", "<..",  # dipendenza
    "*--", "--*", "o--", "--o", "*-", "-*", "--", "..", "-o", "o-", "-", ".",
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
DIAMOND_RE = re.compile(r"^<>\s+(\w+)\s*$")

INHERITANCE_OPS = {"<|--", "--|>", "<|-", "-|>"}
REALIZATION_OPS = {"..|>", "<|.."}
AGGREGATION_OPS = {"o--", "--o", "-o", "o-"}
COMPOSITION_OPS = {"*--", "--*", "*-", "-*", "*-->", "*->"}
DIRECTED_OPS = {"-->", "<--"}
DEPENDENCY_OPS = {"..>", "<.."}


def stable_id(seed: str) -> str:
    return str(uuid.uuid5(NAMESPACE, seed))


# --- Parsing del PlantUML (invariato: agnostico rispetto al formato di output) ---


class ParsedClass:
    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind  # "class" | "abstract class" | "enum"
        self.attributes: list[tuple[str, str]] = []  # (nome, tipo) — tipo vuoto per i valori enum
        self.methods: list[str] = []
        self.placeholder = False  # referenziata in una relazione ma mai dichiarata (legale in PlantUML)


def parse_attribute(line: str) -> tuple[str, str]:
    """Gestisce sia 'Tipo nome' (stile Java) sia 'nome : Tipo' (stile PlantUML piu'
    comune), rimuove il prefisso di visibilita' (+-#~) e i modificatori {static}/
    {abstract}."""
    s = line.strip()
    if s and s[0] in "+-#~":
        s = s[1:].strip()
    s = re.sub(r"\{[^}]*\}", "", s).strip()
    if ":" in s:
        name, _, typ = s.partition(":")
        return name.strip(), typ.strip()
    parts = s.rsplit(None, 1)
    if len(parts) == 2:
        return parts[1], parts[0]
    return s, ""


def parse_plantuml(text: str) -> tuple[dict[str, ParsedClass], list[dict], list[str], list[str]]:
    """Ritorna (classi, relazioni, warning, costrutti_non_supportati). Se
    costrutti_non_supportati non e' vuoto, il modello va escluso dalla conversione."""
    classes: dict[str, ParsedClass] = {}
    relationships: list[dict] = []
    warnings: list[str] = []
    unsupported: list[str] = []
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
                current.attributes.append(parse_attribute(line))
            continue

        m = CLASS_HEADER_RE.match(line)
        if m:
            kind, name, has_open, has_close = m.groups()
            pc = ParsedClass(name, kind)
            classes[name] = pc
            if has_open and not has_close:
                current = pc
            continue

        diamond_m = DIAMOND_RE.match(line)
        if diamond_m:
            unsupported.append(
                f"costrutto diamante n-ario '{line}' senza equivalente Apollon documentato"
            )
            continue

        note_m = NOTE_RE.match(line)
        if note_m:
            notes.add(note_m.group(1))
            continue

        assoc_m = ASSOC1_RE.match(line) or ASSOC2_RE.match(line)
        if assoc_m:
            g = assoc_m.groups()
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

    if unsupported:
        return classes, relationships, warnings, unsupported

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
                f"classe '{name}' non ha una dichiarazione esplicita 'class {name} {{...}}' nel "
                "PlantUML sorgente (dichiarazione implicita tramite uso in una relazione, valida "
                "in PlantUML): creata come nodo senza attributi"
            )

    return classes, relationships, warnings, unsupported


def relationship_kind(op: str) -> tuple[str, bool, bool]:
    """Ritorna (edge_type, swapped, no_label_no_mult) usando i tipi NATIVI Apollon v4
    (non piu' un'associazione chiamata 'is-a' come nel v3): ClassInheritance,
    ClassRealization, ClassAggregation, ClassComposition, ClassUnidirectional,
    ClassDependency, ClassBidirectional.

    swapped=True significa: il lato che deve comparire come "source" nell'edge
    (il figlio per ereditarieta'/realizzazione, l'aggregatore/contenitore per
    aggregazione/composizione, l'origine della freccia per le associazioni dirette)
    e' il TARGET originale della riga PlantUML. Chi chiama deve scambiare insieme
    classi e molteplicita' — mai l'una senza l'altra (era il Bug 2 della versione
    precedente di questo script).
    """
    if op in INHERITANCE_OPS:
        return "ClassInheritance", op in ("<|--", "<|-"), True
    if op in REALIZATION_OPS:
        return "ClassRealization", op == "<|..", True
    if op in AGGREGATION_OPS:
        return "ClassAggregation", op in ("--o", "-o"), False
    if op in COMPOSITION_OPS:
        return "ClassComposition", op in ("--*", "-*"), False
    if op in DIRECTED_OPS:
        return "ClassUnidirectional", op == "<--", False
    if op in DEPENDENCY_OPS:
        return "ClassDependency", op == "<..", False
    return "ClassBidirectional", False, False


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
        return "right" if dx >= 0 else "left"
    return "bottom" if dy >= 0 else "top"


def touch_point(box: dict, handle: str) -> tuple[float, float]:
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    if handle == "right":
        return box["x"] + box["width"], cy
    if handle == "left":
        return box["x"], cy
    if handle == "bottom":
        return cx, box["y"] + box["height"]
    return cx, box["y"]  # top


def fit_to_canvas(nodes: list[dict], edges: list[dict], max_x: float, max_y: float) -> tuple[float, float]:
    """Il prompt impone coordinate positive tra 0 e 1600 (x) / 0 e 780 (y). Se il
    layout a griglia eccede quell'area, scala tutto proporzionalmente (mai verso
    l'alto). Per diagrammi con molte classi puo' produrre riquadri piccoli: e' il
    compromesso del vincolo di canvas fisso del prompt, non un bug di questa funzione."""
    scale = min(MAX_CANVAS_WIDTH / max_x, MAX_CANVAS_HEIGHT / max_y, 1.0)
    if scale >= 1.0:
        return max_x, max_y

    for n in nodes:
        n["position"]["x"] *= scale
        n["position"]["y"] *= scale
        n["width"] *= scale
        n["height"] *= scale
        n["measured"]["width"] *= scale
        n["measured"]["height"] *= scale
    for e in edges:
        for p in e["data"]["points"]:
            p["x"] *= scale
            p["y"] *= scale

    return max_x * scale, max_y * scale


# --- Costruzione del JSON Apollon v4 --------------------------------------------


def build_apollon_json(model_id: str, classes: dict[str, ParsedClass], relationships: list[dict]):
    positions = layout_classes(classes)
    nodes: list[dict] = []
    node_by_class: dict[str, dict] = {}
    class_ids: dict[str, str] = {}

    for name, pc in classes.items():
        node_id = stable_id(f"{model_id}:class:{name}")
        class_ids[name] = node_id
        box = positions[name]

        attributes = []
        for i, (attr_name, attr_type) in enumerate(pc.attributes):
            attr_id = stable_id(f"{model_id}:attr:{name}:{attr_name}:{i}")
            if pc.kind == "enum":
                display = attr_name
            elif attr_type:
                display = f"+ {attr_name} : {attr_type}"
            else:
                display = f"+ {attr_name}"  # nessun tipo nel sorgente: non se ne inventa uno
            attributes.append({"id": attr_id, "name": display})

        methods = []
        for i, method_sig in enumerate(pc.methods):
            method_id = stable_id(f"{model_id}:method:{name}:{method_sig}:{i}")
            methods.append({"id": method_id, "name": method_sig})

        data: dict = {"name": name, "attributes": attributes, "methods": methods}
        if pc.kind == "abstract class":
            data["isAbstract"] = True
        elif pc.kind == "enum":
            data["stereotype"] = "enumeration"

        node = {
            "id": node_id,
            "type": "class",
            "position": {"x": box["x"], "y": box["y"]},
            "width": box["width"],
            "height": box["height"],
            "measured": {"width": box["width"], "height": box["height"]},
            "data": data,
        }
        nodes.append(node)
        node_by_class[name] = node

    edges: list[dict] = []
    warnings: list[str] = []

    def add_edge(edge_type, source_name, target_name, label, source_mult, target_mult):
        if source_name not in class_ids or target_name not in class_ids:
            warnings.append(f"relazione scartata, classe mancante: {source_name} -> {target_name}")
            return
        source_box, target_box = positions[source_name], positions[target_name]
        s_center = (source_box["x"] + source_box["width"] / 2, source_box["y"] + source_box["height"] / 2)
        t_center = (target_box["x"] + target_box["width"] / 2, target_box["y"] + target_box["height"] / 2)
        s_handle = edge_direction(s_center, t_center)
        t_handle = edge_direction(t_center, s_center)
        p1 = touch_point(source_box, s_handle)
        p2 = touch_point(target_box, t_handle)
        edge_id = stable_id(f"{model_id}:rel:{source_name}:{target_name}:{edge_type}:{label}:{len(edges)}")
        edges.append(
            {
                "id": edge_id,
                "source": class_ids[source_name],
                "target": class_ids[target_name],
                "type": edge_type,
                "sourceHandle": s_handle,
                "targetHandle": t_handle,
                "data": {
                    "points": [{"x": p1[0], "y": p1[1]}, {"x": p2[0], "y": p2[1]}],
                    "label": label,
                    "sourceMultiplicity": source_mult,
                    "targetMultiplicity": target_mult,
                    "sourceRole": "",
                    "targetRole": "",
                },
            }
        )

    for r in relationships:
        if r["kind"] == "binary":
            edge_type, swapped, no_label_no_mult = relationship_kind(r["op"])
            if swapped:
                eff_src, eff_tgt = r["target"], r["source"]
                src_mult, tgt_mult = r["target_mult"], r["source_mult"]
            else:
                eff_src, eff_tgt = r["source"], r["target"]
                src_mult, tgt_mult = r["source_mult"], r["target_mult"]
            label = "" if no_label_no_mult else r["label"]
            if no_label_no_mult:
                src_mult = tgt_mult = ""
            add_edge(edge_type, eff_src, eff_tgt, label, src_mult, tgt_mult)
        else:  # classe associativa, approssimata con due associazioni semplici
            warnings.append(
                f"classe associativa '{r['assoc']}' tra {r['a']} e {r['b']} approssimata con due "
                "relazioni semplici verso i due partecipanti; molteplicita' lasciate vuote "
                "(non ricavabili in modo affidabile dal testo). La relazione originale "
                f"{r['a']}-{r['b']}, con le sue molteplicita' reali, resta tra le relazioni "
                "del diagramma se presente nel sorgente."
            )
            add_edge("ClassBidirectional", r["assoc"], r["a"], "", "", "")
            add_edge("ClassBidirectional", r["assoc"], r["b"], "", "", "")

    max_x = max((n["position"]["x"] + n["width"] for n in nodes), default=200) + MARGIN
    max_y = max((n["position"]["y"] + n["height"] for n in nodes), default=200) + MARGIN
    max_x, max_y = fit_to_canvas(nodes, edges, max_x, max_y)

    diagram = {
        "version": MODEL_VERSION,
        "id": model_id,
        "title": model_id,
        "type": "ClassDiagram",
        "nodes": nodes,
        "edges": edges,
        "assessments": {},
        "interactive": {"elements": {}, "relationships": {}},
    }
    return diagram, warnings


# --- Verifica --------------------------------------------------------------------

_SCHEMA_CACHE = None


def validate_against_schema(diagram: dict, model_id: str) -> list[str]:
    """Conformita' strutturale allo schema JSON ufficiale Apollon v4. Non valida il
    contenuto di "data" (lo schema stesso lo lascia intenzionalmente libero)."""
    global _SCHEMA_CACHE
    import jsonschema

    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(_SCHEMA_CACHE)
    return [f"{model_id}: schema — {e.message} (percorso: {list(e.absolute_path)})" for e in validator.iter_errors(diagram)]


def verify_apollon_json(diagram: dict, model_id: str) -> list[str]:
    """Integrita' referenziale interna (id univoci, source/target esistenti,
    dimensioni positive) — non correttezza semantica, vedi round_trip_check."""
    problems = []
    node_ids = {n["id"] for n in diagram["nodes"]}
    if len(node_ids) != len(diagram["nodes"]):
        problems.append(f"{model_id}: id di nodo duplicati")
    for n in diagram["nodes"]:
        if n["width"] <= 0 or n["height"] <= 0:
            problems.append(f"{model_id}: dimensioni non positive per il nodo {n['data'].get('name')}")
        member_ids = [m["id"] for m in n["data"].get("attributes", []) + n["data"].get("methods", [])]
        if len(member_ids) != len(set(member_ids)):
            problems.append(f"{model_id}: id di membro duplicati nel nodo {n['data'].get('name')}")
    for e in diagram["edges"]:
        if e["source"] not in node_ids or e["target"] not in node_ids:
            problems.append(f"{model_id}: edge {e['id']} referenzia un nodo inesistente")
        if len(e["data"]["points"]) < 2:
            problems.append(f"{model_id}: edge {e['id']} ha meno di 2 punti nel path")
    return problems


def _v4_attribute_to_tuple(name: str) -> tuple[str, str]:
    s = name[2:] if name.startswith("+ ") else name
    if " : " in s:
        nm, _, tp = s.partition(" : ")
        return nm.strip(), tp.strip()
    return s.strip(), ""


def round_trip_check(model_id: str, classes: dict[str, ParsedClass], relationships: list[dict], diagram: dict) -> list[str]:
    """Confronta il CONTENUTO SEMANTICO tra il PlantUML originale e il JSON v4
    prodotto, senza riusare relationship_kind (per non validare un eventuale bug con
    la stessa funzione che lo ha causato)."""
    problems = []
    name_by_id = {n["id"]: n["data"]["name"] for n in diagram["nodes"]}

    attrs_by_class: dict[str, list[tuple[str, str]]] = {}
    is_enum_by_class: dict[str, bool] = {}
    for n in diagram["nodes"]:
        is_enum = n["data"].get("stereotype") == "enumeration"
        is_enum_by_class[n["data"]["name"]] = is_enum
        if is_enum:
            attrs_by_class[n["data"]["name"]] = sorted((a["name"], "") for a in n["data"]["attributes"])
        else:
            attrs_by_class[n["data"]["name"]] = sorted(_v4_attribute_to_tuple(a["name"]) for a in n["data"]["attributes"])

    for name, pc in classes.items():
        if pc.placeholder:
            continue
        expected = sorted(pc.attributes) if pc.kind != "enum" else sorted((n, "") for n, _ in pc.attributes)
        got = attrs_by_class.get(name)
        if got is None:
            problems.append(f"{model_id}: classe '{name}' non trovata nel JSON convertito")
        elif got != expected:
            problems.append(
                f"{model_id}: attributi di '{name}' non coincidono — originale={expected} convertito={got}"
            )

    out_edges = list(diagram["edges"])
    used_idx: set[int] = set()
    for r in relationships:
        if r["kind"] != "binary":
            continue
        pair = {r["source"], r["target"]}
        no_label = r["op"] in INHERITANCE_OPS or r["op"] in REALIZATION_OPS
        expected_label = "" if no_label else r["label"]
        candidate_idx = None
        for i, e in enumerate(out_edges):
            if i in used_idx:
                continue
            e_pair = {name_by_id.get(e["source"]), name_by_id.get(e["target"])}
            if e_pair == pair and e["data"]["label"] == expected_label:
                candidate_idx = i
                break
        if candidate_idx is None:
            problems.append(f"{model_id}: relazione originale '{r['raw']}' non trovata nel JSON convertito")
            continue
        used_idx.add(candidate_idx)
        if no_label:
            continue  # molteplicita' forzate vuote per convenzione, niente da confrontare
        e = out_edges[candidate_idx]
        expected = {r["source"]: r["source_mult"], r["target"]: r["target_mult"]}
        got = {
            name_by_id.get(e["source"]): e["data"]["sourceMultiplicity"],
            name_by_id.get(e["target"]): e["data"]["targetMultiplicity"],
        }
        if expected != got:
            problems.append(
                f"{model_id}: molteplicita' errate per '{r['raw']}' — attese {expected}, ottenute {got}"
            )

    return problems


# --- Main ----------------------------------------------------------------------


def main() -> None:
    if not CORPUS_JSONL.exists():
        raise SystemExit(f"{CORPUS_JSONL} non trovato: esegui prima corpus/build_manifest.py")
    if not SCHEMA_PATH.exists():
        raise SystemExit(f"{SCHEMA_PATH} non trovato: scarica uml-model-4.schema.json da @tumaet/apollon")

    records = [json.loads(line) for line in CORPUS_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]

    APOLLON_OUT_DIR.mkdir(parents=True, exist_ok=True)
    total_warnings = 0
    total_problems = 0
    total_roundtrip_problems = 0
    total_schema_problems = 0
    skipped: list[str] = []

    for record in records:
        model_id = record["id"]
        classes, relationships, parse_warnings, unsupported = parse_plantuml(record["diagram_plantuml"])

        if unsupported:
            skipped.append(model_id)
            record["diagram_apollon_json"] = None
            record["diagram_format"] = "plantuml"
            record["apollon_conversion_warnings"] = [
                f"modello escluso dalla conversione Apollon: {u}" for u in unsupported
            ]
            out_path = APOLLON_OUT_DIR / f"{model_id}.json"
            out_path.unlink(missing_ok=True)
            continue

        diagram, build_warnings = build_apollon_json(model_id, classes, relationships)
        schema_problems = validate_against_schema(diagram, model_id)
        problems = verify_apollon_json(diagram, model_id)
        roundtrip_problems = round_trip_check(model_id, classes, relationships, diagram)

        warnings = parse_warnings + build_warnings
        total_warnings += len(warnings)
        total_problems += len(problems)
        total_roundtrip_problems += len(roundtrip_problems)
        total_schema_problems += len(schema_problems)

        record["diagram_apollon_json"] = diagram
        record["diagram_apollon_model_version"] = MODEL_VERSION
        record["apollon_conversion_warnings"] = warnings

        out_path = APOLLON_OUT_DIR / f"{model_id}.json"
        out_path.write_text(json.dumps(diagram, ensure_ascii=False, indent=2), encoding="utf-8")

        if schema_problems:
            print(f"[ERRORE SCHEMA] {model_id}: {schema_problems}")
        if problems:
            print(f"[ERRORE INTEGRITA'] {model_id}: {problems}")
        if roundtrip_problems:
            print(f"[ERRORE ROUND-TRIP] {model_id}: {roundtrip_problems}")

    CORPUS_JSONL.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8"
    )

    assert total_schema_problems == 0, f"{total_schema_problems} violazioni dello schema rilevate, vedi sopra"
    assert total_problems == 0, f"{total_problems} problemi di integrita' rilevati, vedi sopra"
    assert total_roundtrip_problems == 0, f"{total_roundtrip_problems} problemi di round-trip rilevati, vedi sopra"

    converted = len(records) - len(skipped)
    print(f"Convertiti {converted}/{len(records)} diagrammi in Apollon v{MODEL_VERSION} (esclusi: {skipped or 'nessuno'}).")
    print(f"Warning totali (approssimazioni/costrutti non gestiti): {total_warnings}")
    print("Validazione schema JSON ufficiale: 0 violazioni")
    print("Round-trip semantico (attributi + molteplicita' per estremo): 0 discrepanze")
    print(f"JSON Apollon scritti in {APOLLON_OUT_DIR}")
    print("corpus.jsonl aggiornato con diagram_apollon_json + apollon_conversion_warnings")


if __name__ == "__main__":
    main()
