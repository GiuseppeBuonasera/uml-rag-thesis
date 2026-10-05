"""
Caricamento in SOLA LETTURA dei candidati del retrieval e delle query del test set (Passo 2, 2026-10-04).

- Candidati = solo i record CONVERTITI di corpus/processed/corpus.jsonl (diagram_apollon_json non nullo: 59 su 60,
  Cruise escluso).
- Query = i 20 record di corpus/processed/testset_debari.jsonl.
- Hard-fail se un record del test set (id, split o formato DBNN_) e' tra i candidati: lo stesso invariante del
  Passo 1 (build_manifest.check_split_separation), ricontrollato qui perche' il retriever non deve mai poter
  restituire un esercizio del test set.
Nulla viene mai scritto in corpus/.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_JSONL = ROOT / "corpus" / "processed" / "corpus.jsonl"
TESTSET_JSONL = ROOT / "corpus" / "processed" / "testset_debari.jsonl"
# stesso formato di corpus/build_manifest.DEBARI_ID_RE (non importato per non caricare la pipeline del Passo 1)
DEBARI_ID_RE = re.compile(r"^DB(\d{2})_[A-Z][A-Za-z0-9]*$")

# campi esposti all'analisi (il diagramma serve SOLO a misurare la pertinenza, mai al ranking)
FIELDS = ("id", "name", "domain", "description", "diagram_apollon_json", "known_issues")
TEST_FIELDS = FIELDS + ("debari_number", "debari_title", "gt_counts", "debari_ed_avg", "ambiguities")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"{path} non trovato: esegui prima la pipeline del Passo 1 (vedi corpus/README.md)")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check_disjoint(candidates: list[dict], queries: list[dict]) -> None:
    """Hard-fail se un esercizio del test set compare tra i candidati."""
    query_ids = {q["id"] for q in queries}
    leaked = sorted(c["id"] for c in candidates
                    if c["id"] in query_ids or DEBARI_ID_RE.match(c["id"]) or c.get("split") == "debari_test")
    if leaked:
        raise AssertionError(f"esercizi del test set tra i candidati del retrieval: {leaked}")


def load_candidates(path: Path = CORPUS_JSONL) -> list[dict]:
    records = _read_jsonl(path)
    candidates = [{f: r.get(f) for f in FIELDS} | {"split": r.get("split")}
                  for r in records if r.get("diagram_apollon_json") is not None]
    ids = [c["id"] for c in candidates]
    if len(ids) != len(set(ids)):
        raise AssertionError("id duplicati tra i candidati")
    return candidates


def load_queries(path: Path = TESTSET_JSONL) -> list[dict]:
    return [{f: r.get(f) for f in TEST_FIELDS} for r in _read_jsonl(path)]


def load_all() -> tuple[list[dict], list[dict]]:
    """(candidati, query del test set), con il controllo di disgiunzione."""
    candidates, queries = load_candidates(), load_queries()
    check_disjoint(candidates, queries)
    return candidates, queries


def class_names(diagram: dict) -> set[str]:
    """Nomi dei nodi del diagramma Apollon (classi, interfacce, enumerazioni), normalizzati come in
    corpus/check_debari.py: minuscole, solo caratteri alfanumerici (confronto case-insensitive)."""
    return {re.sub(r"[^0-9a-z]", "", n["data"]["name"].lower()) for n in diagram["nodes"]}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0
