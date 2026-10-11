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

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "corpus"))
import paths  # noqa: E402  (percorsi condivisi, voce 116; modulo leggero, non carica la pipeline del Passo 1)

CORPUS_JSONL = paths.CORPUS_JSONL
TESTSET_JSONL = paths.TESTSET_JSONL
DEBARI_ID_RE = paths.DEBARI_ID_RE

# campi esposti all'analisi (il diagramma serve SOLO a misurare la pertinenza, mai al ranking)
FIELDS = ("id", "name", "domain", "description", "diagram_apollon_json", "known_issues")
TEST_FIELDS = FIELDS + ("debari_number", "debari_title", "gt_counts", "debari_ed_avg", "ambiguities")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"{path} non trovato: esegui prima la pipeline del Passo 1 (vedi corpus/README.md)")
    return paths.read_jsonl(path)


def check_disjoint(candidates: list[dict], queries: list[dict]) -> None:
    """Hard-fail se un esercizio del test set compare in corpus.jsonl. Il test set entra nel retrieval solo a runtime
    (pool unico della voce 115, costruito da generation/prompt_builder.py); il file del corpus resta senza esercizi del
    test set."""
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


# --- protocolli di pool (voce 129) ---------------------------------------------------------------------------------
# all80    = pool unico della voce 115 (default delle run nuove): 80 esercizi (60 del corpus + 20 De Bari); per ogni
#            query i candidati sono gli altri 79. Le query su cui si misura la pertinenza sono i 26 esercizi di SVILUPPO
#            (corpus/roles.yaml): quelli di valutazione entrano solo come candidati (voce 117).
# corpus59 = protocollo STORICO delle run del 2026-10-04 .. 2026-10-09 (loo_2026-10-04_stop1, dense_2026-10-09_22f5adf,
#            testset_*): i candidati del corpus SENZA Cruise, che allora non era convertito (recuperato il 2026-10-10,
#            voce 114). Serve solo a riprodurre le run versionate.
POOLS = ("all80", "corpus59")
CORPUS59_EXCLUDED = ("Cruise",)


def load_pool(pool: str) -> list[dict]:
    """Universo del protocollo: corpus59 = candidati del corpus senza Cruise; all80 = corpus (60) + test set (20)."""
    if pool not in POOLS:
        raise ValueError(f"pool sconosciuto: {pool} (ammessi: {POOLS})")
    candidates = load_candidates()
    if pool == "corpus59":
        return [c for c in candidates if c["id"] not in CORPUS59_EXCLUDED]
    queries = load_queries()
    check_disjoint(candidates, queries)
    universe = candidates + queries
    if len(universe) != 80:
        raise AssertionError(f"pool unico: attesi 80 esercizi, trovati {len(universe)}")
    return universe


def development_ids() -> set[str]:
    """I 26 esercizi di sviluppo (corpus/roles.yaml, voce 117)."""
    return {i for i, r in paths.load_roles().items() if r["role"] == "sviluppo"}


def pool_queries(pool: str, universe: list[dict]) -> list[dict]:
    """Query su cui si misura la pertinenza: corpus59 = tutte (protocollo storico); all80 = SOLO le 26 di sviluppo."""
    if pool == "corpus59":
        return list(universe)
    dev = development_ids()
    out = [r for r in universe if r["id"] in dev]
    assert len(out) == len(dev) == 26, (len(out), len(dev))
    return out


def class_names(diagram: dict) -> set[str]:
    """Nomi dei nodi del diagramma Apollon (classi, interfacce, enumerazioni), normalizzati come in
    corpus/check_debari.py: minuscole, solo caratteri alfanumerici (confronto case-insensitive)."""
    return {re.sub(r"[^0-9a-z]", "", n["data"]["name"].lower()) for n in diagram["nodes"]}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0
