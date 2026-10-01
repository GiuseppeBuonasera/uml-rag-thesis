"""
Correzioni di contenuto (FASE 3, 2026-09-28, vedi docs/decisions.md) applicate al
testo PlantUML letto da corpus/raw/models_original/<id>/plantuml.txt PRIMA che
diventi il campo "diagram_plantuml" di corpus.jsonl (chiamato da
corpus/build_manifest.py) — MAI applicate scrivendo su corpus/raw/ (sorgente
immutabile). Ogni correzione e' dichiarata come DATO in
corpus/corrections/<id>.yaml (una lista di operazioni), non codificata in questo
modulo: aggiungere una correzione significa scrivere un nuovo file YAML, non
toccare il codice — stesso principio gia' in uso per
corpus/label_classification.json.

Otto operazioni supportate, ciascuna con "reason" obbligatorio (motivazione
testuale, riportata in corpus.jsonl campo "corrections_applied" per
tracciabilita'):
- rename_token: sostituisce un identificatore intero (confine di parola \\b) in
  TUTTO il testo del diagramma — per refusi di nomi (classi, enum, valori enum,
  attributi). Campi: from, to.
- remove_line: rimuove la/le riga/righe che corrispondono ESATTAMENTE (dopo
  strip) al campo "match" — per relazioni duplicate/errate da eliminare.
- replace_line: sostituisce la/le riga/righe che corrispondono ESATTAMENTE (dopo
  strip) al campo "match" con "replacement" — per correzioni di
  molteplicita'/ruolo su una singola relazione. Campi: match, replacement.
- change_edge_type (2026-09-28): cambia il TIPO di una relazione binaria
  individuata per (class_a, class_b, label) — non per testo esatto della riga,
  cosi' la correzione resta leggibile senza dover scrivere a mano la sintassi
  PlantUML dell'operatore. Campi: class_a, class_b, label (default ""),
  new_type ("association"|"aggregation"|"composition"|"unidirectional"|
  "dependency"), container (nome classe, OBBLIGATORIO per aggregation/
  composition: chi e' il contenitore/whole — il convertitore lo mette sempre
  come target dell'edge, vedi apollon_convert.py::relationship_kind, quindi
  qui basta scegliere l'operatore con '*'/'o' adiacente al lato giusto della
  riga, senza dover scambiare a mano classi o molteplicita').
- remove_label (2026-09-28): svuota l'etichetta di una relazione binaria
  individuata per (class_a, class_b, label) — stessa identificazione di
  change_edge_type, utile per rimuovere un'etichetta ridondante senza
  toccare tipo/molteplicita'. Campi: class_a, class_b, label.
- set_role (2026-09-28, aggiunta non esplicitamente richiesta ma necessaria
  per il caso Boeing Airline-Airline: un'auto-relazione dove class_a==class_b
  non puo' identificare un estremo per nome classe): assegna un ruolo per
  estremo su una relazione binaria individuata per (class_a, class_b, label),
  scegliendo l'estremo tramite la sua MOLTEPLICITA' attuale (deve comparire
  su un solo estremo, altrimenti fallisce per ambiguita'). Campi: class_a,
  class_b, label (default ""), roles (lista di {endpoint_mult, role}).
- add_line (2026-09-29, caso BuildingManagement: diagramma incompleto
  rispetto a description.md, servono relazioni che non esistono affatto nel
  sorgente): aggiunge una riga di relazione nuova, inserita prima di
  "@enduml" se presente (altrimenti in fondo al testo). Campo: line.
  Fallisce se la riga e' GIA' presente (stesso principio hard-fail, in
  direzione opposta: un `add_line` che troverebbe la riga gia' li' non e'
  piu' la correzione per cui era stata scritta).
- add_block (2026-10-01, caso EatAtHome: enum inline 'status : enum{...}' non
  rappresentabile, sostituito da un'enumerazione separata): aggiunge UNA
  dichiarazione completa di classe/enum su piu' righe (intestazione, membri,
  "}"), inserita prima di "@enduml" — add_line non basta perche' aggiunge una
  sola riga e non puo' inserire un "}" gia' presente altrove. Campo: block
  (stringa multi-riga). Fallisce se il blocco non e' esattamente una
  dichiarazione (1 classe/enum, 0 relazioni) o se il nome dichiarato esiste
  gia' nel diagramma.

Le operazioni change_edge_type/remove_label/set_role ri-analizzano il
PlantUML corrente (non operano sulla riga grezza data dall'utente) per
individuare la relazione e ricostruiscono la riga preservando classi/
molteplicita'/ruoli non toccati — evita di dover scrivere a mano operatori
come '--*'/'o--' con lo spazio esatto.

Fallisce esplicitamente (ValueError, non un warning silenzioso) se
un'operazione non trova corrispondenza nel testo, o se la relazione indicata
non e' individuabile in modo univoco: una correzione scritta oggi contro il
plantuml.txt di oggi non deve applicarsi in modo diverso — o non applicarsi
affatto — senza che qualcuno se ne accorga, se il sorgente cambiasse o se ci
fosse un errore di trascrizione nella correzione stessa.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

import apollon_convert as ac

CORRECTIONS_DIR = Path(__file__).parent / "corrections"

_AGGREGATION_OP_BY_SIDE = {"source": "o--", "target": "--o"}
_COMPOSITION_OP_BY_SIDE = {"source": "*--", "target": "--*"}
_EDGE_TYPE_TO_OP = {
    "association": "--",
    "unidirectional": "-->",
    "dependency": "..>",
}
_CONTAINER_REQUIRED_TYPES = {"aggregation", "composition"}


def _find_binary_relationship(model_id: str, plantuml: str, class_a: str, class_b: str, label: str, op_type: str) -> dict:
    classes, relationships, _warnings, unsupported = ac.parse_plantuml(plantuml)
    if unsupported:
        raise ValueError(f"{model_id}: correzione '{op_type}' non applicabile, PlantUML con costrutti non supportati")
    matches = [
        r for r in relationships
        if r["kind"] == "binary" and {r["source"], r["target"]} == {class_a, class_b} and r["label"] == label
    ]
    if len(matches) != 1:
        raise ValueError(
            f"{model_id}: correzione '{op_type}' fallita — relazione ({class_a}, {class_b}, "
            f"label={label!r}) trovata {len(matches)} volte (attesa esattamente 1)"
        )
    return matches[0]


def _format_side(mult: str, role: str) -> str:
    return f"{mult} {role}".strip() if role else mult


def _rebuild_relationship_line(r: dict, op: str, label: str, source_role: str, target_role: str) -> str:
    src_side = _format_side(r["source_mult"], source_role)
    tgt_side = _format_side(r["target_mult"], target_role)
    line = f'{r["source"]} "{src_side}" {op} "{tgt_side}" {r["target"]}'
    return f"{line} : {label}" if label else line


def _replace_exact_line(model_id: str, plantuml: str, old_line: str, new_line: str, op_type: str) -> str:
    lines = plantuml.splitlines()
    target = old_line.strip()
    matched = [i for i, line in enumerate(lines) if line.strip() == target]
    if not matched:
        raise ValueError(f"{model_id}: correzione '{op_type}' fallita — riga ricostruita non trovata: {target!r}")
    for i in matched:
        lines[i] = new_line
    return "\n".join(lines)


def load_corrections(model_id: str) -> list[dict]:
    path = CORRECTIONS_DIR / f"{model_id}.yaml"
    if not path.exists():
        return []
    ops = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ops or []


def apply_corrections(model_id: str, plantuml: str, ops: list[dict]) -> tuple[str, list[str]]:
    """Ritorna (testo_corretto, elenco_descrizioni_applicate). Le operazioni sono
    applicate in ordine, ciascuna sul risultato della precedente."""
    applied: list[str] = []

    for op in ops:
        op_type = op["type"]
        reason = op.get("reason", "")
        # "correzione_errore" (default) vs "chiarimento_modellazione" (2026-09-28,
        # caso Boeing): il PlantUML non era sbagliato in senso stretto, ma
        # description.md descrive la relazione in modo piu' preciso di quanto
        # disegnato — usato da corpus/diff_report.py per una sezione separata.
        category = op.get("category", "correzione_errore")

        if op_type == "rename_token":
            pattern = re.compile(rf'\b{re.escape(op["from"])}\b')
            if not pattern.search(plantuml):
                raise ValueError(
                    f"{model_id}: correzione 'rename_token' fallita — "
                    f"'{op['from']}' non trovato nel PlantUML sorgente"
                )
            plantuml = pattern.sub(op["to"], plantuml)
            applied.append(f"[{category}] rename_token: '{op['from']}' -> '{op['to']}' ({reason})")

        elif op_type in ("remove_line", "replace_line"):
            lines = plantuml.splitlines()
            target = op["match"].strip()
            matched = [i for i, line in enumerate(lines) if line.strip() == target]
            if not matched:
                raise ValueError(
                    f"{model_id}: correzione '{op_type}' fallita — riga non trovata: {target!r}"
                )
            if op_type == "remove_line":
                lines = [line for i, line in enumerate(lines) if i not in matched]
                applied.append(f"[{category}] remove_line: {target!r} rimossa ({reason})")
            else:
                replacement = op["replacement"]
                for i in matched:
                    lines[i] = replacement
                applied.append(f"[{category}] replace_line: {target!r} -> {replacement!r} ({reason})")
            plantuml = "\n".join(lines)

        elif op_type == "change_edge_type":
            class_a, class_b, label = op["class_a"], op["class_b"], op.get("label", "")
            new_type = op["new_type"]
            r = _find_binary_relationship(model_id, plantuml, class_a, class_b, label, op_type)

            if new_type in _CONTAINER_REQUIRED_TYPES:
                container = op["container"]
                op_by_side = _AGGREGATION_OP_BY_SIDE if new_type == "aggregation" else _COMPOSITION_OP_BY_SIDE
                if container == r["source"]:
                    new_op = op_by_side["source"]
                elif container == r["target"]:
                    new_op = op_by_side["target"]
                else:
                    raise ValueError(
                        f"{model_id}: correzione 'change_edge_type' fallita — 'container' {container!r} "
                        f"non corrisponde a nessuno dei due estremi ({r['source']}, {r['target']})"
                    )
            elif new_type in _EDGE_TYPE_TO_OP:
                new_op = _EDGE_TYPE_TO_OP[new_type]
            else:
                raise ValueError(f"{model_id}: 'new_type' non supportato in 'change_edge_type': {new_type!r}")

            new_line = _rebuild_relationship_line(r, new_op, r["label"], r["source_role"], r["target_role"])
            plantuml = _replace_exact_line(model_id, plantuml, r["raw"], new_line, op_type)
            applied.append(
                f"[{category}] change_edge_type: ({class_a}, {class_b}, label={label!r}) -> new_type={new_type!r} "
                f"(op '{r['op']}' -> '{new_op}') ({reason})"
            )

        elif op_type == "remove_label":
            class_a, class_b, label = op["class_a"], op["class_b"], op["label"]
            r = _find_binary_relationship(model_id, plantuml, class_a, class_b, label, op_type)
            new_line = _rebuild_relationship_line(r, r["op"], "", r["source_role"], r["target_role"])
            plantuml = _replace_exact_line(model_id, plantuml, r["raw"], new_line, op_type)
            applied.append(f"[{category}] remove_label: ({class_a}, {class_b}) label {label!r} -> '' ({reason})")

        elif op_type == "set_role":
            class_a, class_b, label = op["class_a"], op["class_b"], op.get("label", "")
            r = _find_binary_relationship(model_id, plantuml, class_a, class_b, label, op_type)
            source_role, target_role = r["source_role"], r["target_role"]
            for item in op["roles"]:
                mult, role_text = item["endpoint_mult"], item["role"]
                on_source = r["source_mult"] == mult
                on_target = r["target_mult"] == mult
                if on_source == on_target:  # ne' l'uno ne' l'altro, o entrambi (ambiguo)
                    raise ValueError(
                        f"{model_id}: correzione 'set_role' fallita — molteplicita' {mult!r} su "
                        f"{int(on_source) + int(on_target)} estremi di ({class_a}, {class_b}), attesa esattamente 1"
                    )
                if on_source:
                    source_role = role_text
                else:
                    target_role = role_text
            new_line = _rebuild_relationship_line(r, r["op"], r["label"], source_role, target_role)
            plantuml = _replace_exact_line(model_id, plantuml, r["raw"], new_line, op_type)
            applied.append(f"[{category}] set_role: ({class_a}, {class_b}) ruoli {op['roles']} ({reason})")

        elif op_type == "add_line":
            new_rel_line = op["line"].strip()
            lines = plantuml.splitlines()
            if any(line.strip() == new_rel_line for line in lines):
                raise ValueError(
                    f"{model_id}: correzione 'add_line' fallita — riga gia' presente: {new_rel_line!r} "
                    "(il diagramma non e' piu' quello per cui la correzione era stata scritta)"
                )
            insert_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().lower() == "@enduml":
                    insert_idx = i
                    break
            lines.insert(insert_idx, new_rel_line)
            plantuml = "\n".join(lines)
            applied.append(f"[{category}] add_line: {new_rel_line!r} aggiunta ({reason})")

        elif op_type == "add_block":
            block_lines = [line.rstrip() for line in op["block"].strip().splitlines()]
            b_classes, b_rels, _w, b_unsupported = ac.parse_plantuml("\n".join(block_lines))
            declared = [c for c in b_classes.values() if not c.placeholder]
            if len(declared) != 1 or b_rels or b_unsupported or block_lines[-1].strip() != "}":
                raise ValueError(
                    f"{model_id}: correzione 'add_block' fallita — il blocco deve essere esattamente una "
                    f"dichiarazione di classe/enum chiusa da '}}' (trovate {len(declared)} classi, "
                    f"{len(b_rels)} relazioni)"
                )
            new_name = declared[0].name
            existing, _r, _w, _u = ac.parse_plantuml(plantuml)
            if new_name in existing and not existing[new_name].placeholder:
                raise ValueError(
                    f"{model_id}: correzione 'add_block' fallita — '{new_name}' gia' dichiarata nel diagramma "
                    "(il diagramma non e' piu' quello per cui la correzione era stata scritta)"
                )
            lines = plantuml.splitlines()
            insert_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().lower() == "@enduml":
                    insert_idx = i
                    break
            lines[insert_idx:insert_idx] = block_lines + [""]
            plantuml = "\n".join(lines)
            applied.append(f"[{category}] add_block: dichiarazione '{new_name}' aggiunta ({reason})")

        else:
            raise ValueError(f"{model_id}: tipo di correzione sconosciuto: {op_type!r}")

    return plantuml, applied
