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

VERSIONI DEL POST-PROCESSING (parametro `version`; decisioni dello STOP 2 del secondo pilota, docs/decisions.md voce 89):
  pilot2_v1  comportamento con cui sono state analizzate le run del secondo pilota (analisi ORIGINALE, invariata);
  v2         (default per le run nuove) due correzioni, entrambe contate e registrate, mai nascoste:
             - intestazioni "class X extends Y" / "class X implements A, B" (anche abstract class / interface, con o
               senza corpo { } sulla stessa riga; sintassi PlantUML valida, non riconosciuta da apollon_convert):
               l'intestazione diventa "class X ..." e si aggiungono le relazioni "X --|> Y" (extends) e "X ..|> A"
               (implements) in fondo al blocco; conteggi in `syntax_rewrites`;
             - @startuml senza @enduml con finish_reason diverso da "length": il blocco arriva fino alla fine del
               testo, con il diagnostico di formato "enduml_mancante" (con "length" resta "truncated").
  corpus/apollon_convert.py non cambia: le correzioni riscrivono il testo della risposta prima del parser.

REGOLA AUTOMATICA DELLE ETICHETTE "auto_v1" (APPROVATA allo STOP 1 del secondo pilota, docs/decisions.md voci 78-79; per le
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
VERSIONS = ("pilot2_v1", "v2")
PILOT2_VERSION = "pilot2_v1"  # analisi originale del secondo pilota (voce 88)
DEFAULT_VERSION = "v2"  # run nuove (voce 89)
BLOCK_RE = re.compile(r"@startuml\b(.*?)@enduml", re.S | re.I)
# "forma di molteplicita'": solo cifre, '*', '.', ',', 'n' / 'N', con almeno una cifra, '*' o 'n' (comprende "1",
# "0..*", "1..n", "1...*" e anche la grafia "0..1*" presente in un ground truth del corpus, HomeForTheElderly)
MULT_RE = re.compile(r"^(?=.*[0-9*nN])[0-9*.,nN]+$")
# v2: intestazione con extends / implements (anche corpo { ... } sulla stessa riga)
JAVA_HEADER_RE = re.compile(r"^(abstract\s+class|class|interface|enum)\s+(\w+)(\s*<<\w+>>)?\s+"
                            r"((?:extends|implements)\b[^{]*?)\s*(\{.*)?$")
JAVA_CLAUSE_RE = re.compile(r"(extends|implements)\s+([\w\s,]+?)\s*(?=\b(?:extends|implements)\b|$)")


def rewrite_java_headers(block: str) -> tuple[str, dict]:
    """v2: 'class X extends Y implements A, B { ...' -> 'class X { ...' + relazioni 'X --|> Y', 'X ..|> A', 'X ..|> B'
    in fondo al blocco (non dentro un eventuale corpo aperto). Ritorna (testo, conteggi)."""
    counts = {"headers": 0, "extends": 0, "implements": 0}
    out, rels = [], []
    for raw in block.splitlines():
        m = JAVA_HEADER_RE.match(raw.strip())
        if not m:
            out.append(raw)
            continue
        kind, name, stereo, clause, body = m.groups()
        counts["headers"] += 1
        for word, parents in JAVA_CLAUSE_RE.findall(clause):
            for parent in (x.strip() for x in parents.split(",")):
                if parent:
                    counts[word] += 1
                    rels.append(f"{name} {'--|>' if word == 'extends' else '..|>'} {parent}")
        head = f"{kind} {name}{stereo or ''}"
        body = (body or "").strip()
        if not body:
            out.append(head)
        elif re.fullmatch(r"\{\s*\}", body):
            out.append(head + " {}")
        else:  # '{' oppure '{ contenuto' oppure '{ contenuto }': il contenuto va su righe sue
            inner = body[1:].strip()
            closed = inner.endswith("}")
            inner = inner[:-1].strip() if closed else inner
            out += [head + " {"] + ([inner] if inner else []) + (["}"] if closed else [])
    return "\n".join(out + rels), counts


@dataclass
class PlantValidation(pp.Validation):
    P0_block: bool = False
    P1b_parsed: bool = False
    P1_clean: bool = False
    discarded_lines: list = field(default_factory=list)
    parse_warnings: int = 0
    postprocess_version: str = DEFAULT_VERSION
    syntax_rewrites: dict = field(default_factory=dict)  # v2: intestazioni extends / implements riscritte

    def row(self) -> dict:
        d = super().row()
        d["discarded_lines_count"] = len(self.discarded_lines)
        d["discarded_lines"] = " | ".join(self.discarded_lines)[:2000]
        d["syntax_rewrites"] = ";".join(f"{k}={v}" for k, v in sorted(self.syntax_rewrites.items()) if v)
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


def validate_plantuml_response(text: str, finish_reason: str | None, model_id: str,
                                version: str = DEFAULT_VERSION) -> PlantValidation:
    if version not in VERSIONS:
        raise ValueError(f"versione del post-processing sconosciuta: {version} (ammesse: {VERSIONS})")
    v = PlantValidation(finish_reason=finish_reason, truncated=finish_reason == "length", postprocess_version=version)
    body, v.reasoning_removed = pp.strip_reasoning(text or "")
    m = BLOCK_RE.search(body)
    missing_enduml = False
    if m:
        block, outside = m.group(0), (body[:m.start()] + body[m.end():]).strip()
    else:
        start = re.search(r"@startuml\b", body, re.I)
        if version == "v2" and start and not v.truncated:  # v2: il blocco arriva fino alla fine del testo
            block, outside, missing_enduml = body[start.start():], body[:start.start()].strip(), True
        else:
            v.failure = "truncated" if v.truncated else "incomplete_block" if start else "no_block"
            return v
    v.P0_block, v.L0_extracted, v.extraction = True, True, "plantuml_block"
    if version == "v2":
        block, v.syntax_rewrites = rewrite_java_headers(block)
    diagram, info = plantuml_to_apollon(block, model_id)
    v.discarded_lines, v.parse_warnings = info["discarded_lines"], len(info["warnings"])
    if diagram is None:
        v.failure = "unsupported" if info["unsupported"] else "parse_error" if info["error"] else "no_classes"
        v.errors["P1"] = info["unsupported"] or [info["error"] or "nessuna classe"]
        return v
    v.P1b_parsed, v.P1_clean = True, not info["discarded_lines"]
    v.L1_json, v.level, v.diagram = True, 1, diagram  # l'Apollon prodotto e' JSON per costruzione
    v.format_issues, v.layout_issues = pp.instruction_checks(diagram, bool(outside))
    if missing_enduml:
        v.format_issues["enduml_mancante"] = "blocco senza @enduml, letto fino alla fine del testo (finish_reason " \
                                             f"{finish_reason})"
    return pp.check_l2_l4(v, diagram)
