"""
Post-processing della strada 1 del secondo pilota (2026-10-07): risposta PlantUML -> Apollon v4 con il convertitore
della tesi (corpus/apollon_convert.py, importato in SOLA LETTURA e mai modificato), poi GLI STESSI controlli L2-L4
della strada 2 (generation/postprocess.check_l2_l4). Apollon e' il formato di consegna: id, coordinate e riferimenti
li produce il convertitore in modo deterministico.

Livelli propri della strada 1 (cumulativi):
  P0   blocco @startuml ... @enduml trovato (tolti i blocchi di ragionamento; fence e testo attorno ammessi e
       registrati come diagnostico extra_text);
  P1b  parsing riuscito in modalita' TOLLERANTE: parse_plantuml non solleva eccezioni, nessun costrutto non
       supportato (diamante n-ario), almeno una classe; le righe non riconosciute sono registrate (quante e quali) ma
       non bloccano;
  P1   come P1b e nessuna riga scartata;
  poi conversione in Apollon (regola automatica delle etichette, vincoli di generalizzazione, classi associative,
  build_apollon_json) e L2 schema, L3 integrita', L4 stile sull'Apollon prodotto.
Troncamento: finish_reason = length senza @enduml -> failure "truncated".

REGOLA AUTOMATICA DELLE ETICHETTE "auto_v1" (PROPOSTA allo STOP 1 del secondo pilota, docs/decisions.md voce 78; per le
risposte generate non esiste corpus/label_classification.json). Uguale per tutte le condizioni, deterministica:
  (a) testo dopo i due punti = NOME DI ASSOCIAZIONE (label), tolti i marcatori di verso di lettura (gia' nel parser);
  (b) testo tra virgolette a un estremo = "molteplicita' ruolo" se la prima parola ha forma di molteplicita'
      (MULT_RE: solo cifre, '*', '.', ',', 'n'/'N'), altrimenti e' tutto RUOLO senza molteplicita';
  (c) etichette {...} su generalizzazioni = vincoli (extract_generalization_constraints, come nel Passo 1); etichette e
      molteplicita' di generalizzazioni / realizzazioni si scartano (come nel Passo 1).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "corpus"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import apollon_convert as ac  # noqa: E402  (sola lettura)
import postprocess as pp  # noqa: E402

LABEL_RULE = "auto_v1"
BLOCK_RE = re.compile(r"@startuml\b(.*?)@enduml", re.S | re.I)
# "forma di molteplicita'": solo cifre, '*', '.', ',', 'n' / 'N', con almeno una cifra, '*' o 'n' (comprende "1",
# "0..*", "1..n", "1...*" e anche la grafia "0..1*" presente in un ground truth del corpus, HomeForTheElderly)
MULT_RE = re.compile(r"^(?=.*[0-9*nN])[0-9*.,nN]+$")


@dataclass
class PlantValidation(pp.Validation):
    P0_block: bool = False
    P1b_parsed: bool = False
    P1_clean: bool = False
    discarded_lines: list = field(default_factory=list)
    parse_warnings: int = 0

    def row(self) -> dict:
        d = super().row()
        d["discarded_lines_count"] = len(self.discarded_lines)
        d["discarded_lines"] = " | ".join(self.discarded_lines)[:2000]
        return d


def apply_auto_label_rule(relationships: list[dict]) -> int:
    """Regola (b): sposta nel ruolo il testo tra virgolette che non ha forma di molteplicita'. La (a) e' gia' il
    comportamento del parser (il testo dopo i due punti resta in label). Ritorna quante riscritture."""
    changed = 0
    for r in relationships:
        if r.get("kind") != "binary":
            continue
        for mult_key, role_key in (("source_mult", "source_role"), ("target_mult", "target_role")):
            mult = r.get(mult_key) or ""
            if mult and not MULT_RE.match(mult):
                r[role_key] = " ".join(x for x in (mult, r.get(role_key) or "") if x)
                r[mult_key] = ""
                changed += 1
    return changed


def plantuml_to_apollon(text: str, model_id: str) -> tuple[dict | None, dict]:
    """PlantUML (blocco gia' estratto) -> (Apollon o None, dettagli). Usata sia per le risposte sia per il controllo
    di sanita' sui diagrammi del corpus e del test set."""
    info = {"discarded_lines": [], "unsupported": [], "warnings": [], "error": None, "label_rule_rewrites": 0}
    try:
        classes, relationships, warnings, unsupported = ac.parse_plantuml(text)
    except Exception as e:  # modalita' tollerante: un errore del parser non deve fermare la run
        info["error"] = f"parse: {type(e).__name__}: {e}"
        return None, info
    info["warnings"] = warnings
    info["discarded_lines"] = [w for w in warnings if w.startswith("riga non riconosciuta")]
    info["unsupported"] = unsupported
    if unsupported or not classes:
        return None, info
    try:
        info["label_rule_rewrites"] = apply_auto_label_rule(relationships)
        ac.extract_generalization_constraints(relationships)
        relationships, _ = ac.reify_association_classes(relationships)
        diagram, build_warnings = ac.build_apollon_json(model_id, classes, relationships)
    except Exception as e:
        info["error"] = f"build: {type(e).__name__}: {e}"
        return None, info
    info["warnings"] += build_warnings
    return diagram, info


def validate_plantuml_response(text: str, finish_reason: str | None, model_id: str) -> PlantValidation:
    v = PlantValidation(finish_reason=finish_reason, truncated=finish_reason == "length")
    body, v.reasoning_removed = pp.strip_reasoning(text or "")
    m = BLOCK_RE.search(body)
    if not m:
        v.failure = ("truncated" if v.truncated else
                     "incomplete_block" if re.search(r"@startuml", body, re.I) else "no_block")
        return v
    v.P0_block, v.L0_extracted, v.extraction = True, True, "plantuml_block"
    outside = (body[:m.start()] + body[m.end():]).strip()
    diagram, info = plantuml_to_apollon(m.group(0), model_id)
    v.discarded_lines, v.parse_warnings = info["discarded_lines"], len(info["warnings"])
    if diagram is None:
        v.failure = "unsupported" if info["unsupported"] else "parse_error" if info["error"] else "no_classes"
        v.errors["P1"] = info["unsupported"] or [info["error"] or "nessuna classe"]
        return v
    v.P1b_parsed, v.P1_clean = True, not info["discarded_lines"]
    v.L1_json, v.level, v.diagram = True, 1, diagram  # l'Apollon prodotto e' JSON per costruzione
    v.format_issues, v.layout_issues = pp.instruction_checks(diagram, bool(outside))
    return pp.check_l2_l4(v, diagram)
