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

Tre operazioni supportate, ciascuna con "reason" obbligatorio (motivazione
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

Fallisce esplicitamente (ValueError, non un warning silenzioso) se
un'operazione non trova corrispondenza nel testo: una correzione scritta oggi
contro il plantuml.txt di oggi non deve applicarsi in modo diverso — o non
applicarsi affatto — senza che qualcuno se ne accorga, se il sorgente
cambiasse o se ci fosse un errore di trascrizione nella correzione stessa.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

CORRECTIONS_DIR = Path(__file__).parent / "corrections"


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

        if op_type == "rename_token":
            pattern = re.compile(rf'\b{re.escape(op["from"])}\b')
            if not pattern.search(plantuml):
                raise ValueError(
                    f"{model_id}: correzione 'rename_token' fallita — "
                    f"'{op['from']}' non trovato nel PlantUML sorgente"
                )
            plantuml = pattern.sub(op["to"], plantuml)
            applied.append(f"rename_token: '{op['from']}' -> '{op['to']}' ({reason})")

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
                applied.append(f"remove_line: {target!r} rimossa ({reason})")
            else:
                replacement = op["replacement"]
                for i in matched:
                    lines[i] = replacement
                applied.append(f"replace_line: {target!r} -> {replacement!r} ({reason})")
            plantuml = "\n".join(lines)

        else:
            raise ValueError(f"{model_id}: tipo di correzione sconosciuto: {op_type!r}")

    return plantuml, applied
