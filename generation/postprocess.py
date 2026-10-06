"""
Post-processing della risposta di un LLM (Passo 3a, 2026-10-05): estrazione del JSON e validazione a livelli separati.
Nessuna chiamata a LLM; corpus/ letto e mai scritto (da corpus/apollon_convert.py si importano solo funzioni di sola
lettura).

Livelli (cumulativi: un livello si valuta solo se il precedente e' superato):
  L0 estratto   nella risposta c'e' un candidato JSON (risposta intera, blocco ``` o oggetto {...} bilanciato), tolti
                i blocchi di ragionamento (REASONING_MARKERS: <think>...</think> e simili, Gemma 4
                <|channel>thought ... <channel|>), anche troncati o senza apertura;
  L1 JSON       il candidato si decodifica in un oggetto JSON;
  L2 schema     conforme a evaluation/uml-model-4.schema.json (validate_against_schema);
  L3 integrita' id unici in TUTTO il diagramma (nodi, attributi, metodi, edge) e riferimenti coerenti
                (verify_apollon_json, protetta da strutture malformate). NON si richiede che gli id siano UUID validi:
                il template v4 stesso usa come esempio "a1b2c3d4-e5f6-4890-81h2-i3j4k5l6m7n8" (decisions.md, voce 64);
  L4 stile      style_check su una copia in cui si applicano SOLO le riscritture dell'elenco chiuso L4_REWRITES
                (forme ammesse dalle istruzioni v4 ma segnalate da style_check; approvato allo STOP 2, decisions.md
                voce 66: qualunque altra riscrittura richiede una decisione esplicita). Si registrano anche il numero
                di riscritture applicate e i messaggi originali di style_check sul JSON non riscritto.

Troncamento: finish_reason == "length" -> truncated=True; se il JSON non si estrae o non si decodifica il motivo e'
"truncated", distinto da "invalid_json" / "no_json".

Istruzioni non rispettate: DIAGNOSTICI, non metriche di qualita'. Registrati a parte, fuori dai livelli L0-L4, in due
categorie separate che non si combinano tra loro ne' con L0-L4 in un unico punteggio:
  formato della risposta (FORMAT_ISSUES): extra_text (testo o fence attorno al JSON), interactive_present (chiave
    "interactive": lo schema la ammette, non e' un errore), version_not_4_2_0, type_not_class_diagram,
    node_type_not_class, empty_method_name;
  layout (LAYOUT_ISSUES): out_of_canvas (nodi fuori da [0,1600]x[0,780]), overlapping_nodes, measured_mismatch
    (width/height diversi da measured).
"""

from __future__ import annotations

import copy
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "corpus"))
from apollon_convert import style_check, validate_against_schema, verify_apollon_json  # noqa: E402

CANVAS_W, CANVAS_H = 1600, 780
# Marcatori di ragionamento nel testo della risposta: nome -> (apertura, chiusura), regex. Gemma 4 (2026-10-06): il
# ragionamento e' tra "<|channel>thought" e "<channel|>" (configurazione del modello in LM Studio).
REASONING_MARKERS = {
    "think": (r"<think>", r"</think>"),
    "thinking": (r"<thinking>", r"</thinking>"),
    "reasoning": (r"<reasoning>", r"</reasoning>"),
    "gemma4_channel_thought": (r"<\|channel>\s*thought", r"<channel\|>"),
}
_FENCE = re.compile(r"```[ \t]*(?:json|JSON)?[ \t]*\n(.*?)```", re.S)
_V4_METHOD = re.compile(r"^([A-Za-z_]\w*)\s*\((.*)\)\s*(?::\s*(\S.*?))?\s*$")  # "methodName(parameters): ReturnType"

# Riscritture AMMESSE prima di style_check (L4). Elenco CHIUSO (STOP 2, decisions.md voce 66): ogni altra riscrittura
# richiede una decisione esplicita.
L4_REWRITES = {
    "method_v4_form": 'metodo nella forma del template v4 "nome(parametri): Tipo" (o "nome(parametri)") senza "+ " '
                      '-> forma del corpus "+ nome(parametri) : Tipo"',
    "multiplicity_n": 'molteplicita\' "1..n" / "0..n" / "n" -> "1..*" / "0..*" / "*" (solo queste tre, n minuscola)',
}
_MULT_N = {"1..n": "1..*", "0..n": "0..*", "n": "*"}
FORMAT_ISSUES = ("extra_text", "interactive_present", "version_not_4_2_0", "type_not_class_diagram",
                 "node_type_not_class", "empty_method_name")
LAYOUT_ISSUES = ("out_of_canvas", "overlapping_nodes", "measured_mismatch")


@dataclass
class Validation:
    L0_extracted: bool = False
    L1_json: bool = False
    L2_schema: bool = False
    L3_integrity: bool = False
    L4_style: bool = False
    level: int = -1  # ultimo livello superato (-1 = nessuno)
    failure: str = ""  # "", no_json, truncated, incomplete_json, invalid_json, not_object, schema, integrity, style
    truncated: bool = False
    finish_reason: str | None = None
    reasoning_removed: bool = False
    extraction: str = ""  # raw | fence | braces
    errors: dict = field(default_factory=dict)  # livello -> messaggi
    style_raw: list = field(default_factory=list)  # messaggi originali di style_check (JSON non riscritto)
    l4_rewrites: dict = field(default_factory=dict)  # riscritture L4_REWRITES applicate: tipo -> numero
    format_issues: dict = field(default_factory=dict)  # diagnostici "formato della risposta": nome -> dettaglio
    layout_issues: dict = field(default_factory=dict)  # diagnostici "layout": nome -> dettaglio
    diagram: dict | None = None

    def row(self) -> dict:
        d = asdict(self)
        d.pop("diagram")
        d["errors"] = json.dumps(d["errors"], ensure_ascii=False)
        d["style_raw_count"] = len(self.style_raw)
        d["style_raw"] = json.dumps(self.style_raw, ensure_ascii=False)
        d["l4_rewrites_total"] = sum(self.l4_rewrites.values())
        d["l4_rewrites"] = json.dumps(self.l4_rewrites, sort_keys=True)
        d["format_issues"] = ";".join(sorted(self.format_issues))
        d["layout_issues"] = ";".join(sorted(self.layout_issues))
        return d


def reasoning_markers(text: str) -> list[str]:
    """Nomi dei marcatori di ragionamento (apertura o chiusura) presenti nel testo."""
    return [name for name, (op, cl) in REASONING_MARKERS.items()
            if re.search(op, text or "", re.I) or re.search(cl, text or "", re.I)]


def strip_reasoning(text: str) -> tuple[str, bool]:
    """Toglie i blocchi di ragionamento di REASONING_MARKERS. Per ogni marcatore: blocchi completi; chiusura senza
    apertura (apertura inserita dal chat template: si scarta tutto cio' che precede la chiusura); apertura mai chiusa
    (risposta troncata nel ragionamento: si scarta tutto cio' che segue)."""
    out, removed = text, False
    for op, cl in REASONING_MARKERS.values():
        new = re.sub(f"{op}.*?{cl}", "", out, flags=re.S | re.I)
        close = re.search(cl, new, re.I)
        if close:
            new = new[close.end():]
        opened = re.search(op, new, re.I)
        if opened:
            new = new[:opened.start()]
        removed |= new != out
        out = new
    return out, removed


def _balanced_objects(text: str):
    """Sottostringhe {...} bilanciate, in ordine, rispettando stringhe ed escape. Restituisce anche se l'ultima
    apertura e' rimasta senza chiusura (JSON incompleto)."""
    found, i, n = [], 0, len(text)
    unclosed = False
    while i < n:
        start = text.find("{", i)
        if start < 0:
            break
        depth, in_str, esc, j = 0, False, False, start
        while j < n:
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth != 0:
            unclosed = True
            break
        found.append(text[start:j + 1])
        i = j + 1
    return found, unclosed


def extract_json(text: str) -> tuple[str | None, str, bool]:
    """(candidato, metodo, testo_extra). Ordine: risposta intera, primo blocco ``` che si decodifica (altrimenti il
    primo blocco ```), oggetto {...} bilanciato piu' lungo che si decodifica (altrimenti il piu' lungo)."""
    s = text.strip()
    if s.startswith("{") and s.endswith("}"):
        try:
            json.loads(s)
            return s, "raw", False
        except json.JSONDecodeError:
            pass
    fences = [f.strip() for f in _FENCE.findall(text)]
    if fences:
        for f in fences:
            try:
                json.loads(f)
                return f, "fence", True
            except json.JSONDecodeError:
                pass
        return fences[0], "fence", True
    objs, _ = _balanced_objects(text)
    if objs:
        for o in sorted(objs, key=len, reverse=True):
            try:
                json.loads(o)
                return o, "braces", True
            except json.JSONDecodeError:
                pass
        best = max(objs, key=len)
        return (best, "raw", False) if best == s else (best, "braces", True)
    return None, "", bool(s)


def integrity_errors(diagram: dict) -> list[str]:
    """L3: verify_apollon_json (protetta) + unicita' globale degli id. Nessun controllo di formato UUID."""
    try:
        problems = verify_apollon_json(diagram, "output")
    except (KeyError, TypeError, AttributeError) as e:
        return [f"struttura malformata per verify_apollon_json: {type(e).__name__} {e}"]
    ids: list[str] = []
    try:
        for n in diagram["nodes"]:
            ids.append(n["id"])
            for m in n["data"].get("attributes", []) + n["data"].get("methods", []):
                ids.append(m["id"])
        ids += [e["id"] for e in diagram["edges"]]
    except (KeyError, TypeError, AttributeError) as e:
        return problems + [f"struttura malformata (id): {type(e).__name__} {e}"]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        problems.append(f"output: id duplicati nel diagramma: {dup[:10]}")
    return problems


def v4_normalized_copy(diagram: dict) -> tuple[dict, dict]:
    """(copia, conteggi): copia su cui si applica style_check per L4, con SOLO le riscritture di L4_REWRITES."""
    d = copy.deepcopy(diagram)
    counts = {k: 0 for k in L4_REWRITES}
    for n in d["nodes"]:
        for m in n["data"].get("methods", []):
            name = m.get("name")
            if isinstance(name, str) and not name.startswith("+ "):
                hit = _V4_METHOD.match(name)
                if hit:
                    fn, params, ret = hit.groups()
                    m["name"] = f"+ {fn}({params})" + (f" : {ret}" if ret else "")
                    counts["method_v4_form"] += 1
    for e in d["edges"]:
        for f in ("sourceMultiplicity", "targetMultiplicity"):
            v = e.get("data", {}).get(f)
            if v in _MULT_N:
                e["data"][f] = _MULT_N[v]
                counts["multiplicity_n"] += 1
    return d, {k: c for k, c in counts.items() if c}


def instruction_checks(diagram: dict, extra_text: bool) -> tuple[dict, dict]:
    """(formato della risposta, layout): diagnostici separati, non metriche. Robusto a strutture malformate."""
    try:
        out = _instruction_checks(diagram, extra_text)
    except (KeyError, TypeError, AttributeError) as e:
        out = {"extra_text": True} if extra_text else {}
        out["unchecked"] = f"struttura malformata: {type(e).__name__}"
    fmt = {k: v for k, v in out.items() if k not in LAYOUT_ISSUES}
    return fmt, {k: v for k, v in out.items() if k in LAYOUT_ISSUES}


def _instruction_checks(diagram: dict, extra_text: bool) -> dict:
    out: dict[str, object] = {}
    if "interactive" in diagram:
        out["interactive_present"] = True
    if extra_text:
        out["extra_text"] = True
    if diagram.get("version") != "4.2.0":
        out["version_not_4_2_0"] = diagram.get("version")
    if diagram.get("type") != "ClassDiagram":
        out["type_not_class_diagram"] = diagram.get("type")
    nodes = diagram.get("nodes", [])
    bad_type = [n.get("id") for n in nodes if n.get("type") != "class"]
    if bad_type:
        out["node_type_not_class"] = len(bad_type)
    boxes = []
    for n in nodes:
        try:
            x, y, w, h = n["position"]["x"], n["position"]["y"], n["width"], n["height"]
        except (KeyError, TypeError):
            continue
        boxes.append((x, y, w, h))
        if (w, h) != (n.get("measured", {}).get("width"), n.get("measured", {}).get("height")):
            out["measured_mismatch"] = out.get("measured_mismatch", 0) + 1
    outside = sum(1 for x, y, w, h in boxes if x < 0 or y < 0 or x + w > CANVAS_W or y + h > CANVAS_H)
    if outside:
        out["out_of_canvas"] = outside
    overlaps = sum(1 for i, a in enumerate(boxes) for b in boxes[i + 1:]
                   if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3])
    if overlaps:
        out["overlapping_nodes"] = overlaps
    empty = sum(1 for n in nodes for m in (n.get("data") or {}).get("methods", []) or []
                if isinstance(m, dict) and not str(m.get("name", "")).strip())
    if empty:
        out["empty_method_name"] = empty
    return out


def validate_response(text: str, finish_reason: str | None = "stop") -> Validation:
    v = Validation(finish_reason=finish_reason, truncated=finish_reason == "length")
    body, v.reasoning_removed = strip_reasoning(text or "")
    cand, v.extraction, extra = extract_json(body)
    if cand is None:
        # truncated: il server dichiara finish_reason=length; incomplete_json: oggetto aperto e mai chiuso senza
        # che il server dichiari il troncamento; no_json: nessun oggetto nella risposta
        v.failure = ("truncated" if v.truncated else
                     "incomplete_json" if _balanced_objects(body)[1] else "no_json")
        return v
    v.L0_extracted, v.level = True, 0
    try:
        diagram = json.loads(cand)
    except json.JSONDecodeError as e:
        v.failure = "truncated" if v.truncated else "invalid_json"
        v.errors["L1"] = [str(e)]
        return v
    if not isinstance(diagram, dict):
        v.failure, v.errors["L1"] = "not_object", [type(diagram).__name__]
        return v
    v.L1_json, v.level, v.diagram = True, 1, diagram
    v.format_issues, v.layout_issues = instruction_checks(diagram, extra)
    errs = validate_against_schema(diagram, "output")
    if errs:
        v.failure, v.errors["L2"] = "schema", errs
        return v
    v.L2_schema, v.level = True, 2
    errs = integrity_errors(diagram)
    if errs:
        v.failure, v.errors["L3"] = "integrity", errs
        return v
    v.L3_integrity, v.level = True, 3
    try:
        v.style_raw = style_check(diagram, "output")
        normalized, v.l4_rewrites = v4_normalized_copy(diagram)
        errs = style_check(normalized, "output")
    except (KeyError, TypeError, AttributeError) as e:
        errs = [f"struttura malformata per style_check: {type(e).__name__} {e}"]
    if errs:
        v.failure, v.errors["L4"] = "style", errs
        return v
    v.L4_style, v.level = True, 4
    return v
