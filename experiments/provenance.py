"""
Riga di provenienza dei report di analisi (2026-10-09, voce 106): commit git, flag di modifiche non committate e
impronta del ground truth del corpus usato, scritta in automatico in testa a ogni report (analyze_*.py,
review_report.py, retrieval/analyze_retrieval.py). Sostituisce le note manuali "rigenerato dopo correzione GT".

Impronta del GT: sha256 del CONTENUTO, cioe' del JSON canonico (chiavi ordinate, separatori compatti, UTF-8) della mappa
{id: diagram_apollon_json} dei record del corpus con diagramma; e' indipendente dagli a capo del file (che su un clone
Windows possono cambiare, voce 68), quindi confrontabile tra macchine. Per informazione si riporta anche lo sha256 dei
byte di corpus/processed/corpus.jsonl (che invece dipende dagli a capo del checkout).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "retrieval"))
CORPUS_JSONL = ROOT / "corpus" / "processed" / "corpus.jsonl"


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def gt_digest(diagrams: dict[str, dict]) -> str:
    """sha256 del JSON canonico di {id: diagramma}."""
    blob = json.dumps(diagrams, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def corpus_gt() -> dict[str, dict]:
    import corpus_loader as cl
    return {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}


def provenance_line(diagrams: dict[str, dict] | None = None) -> str:
    """Riga Markdown: commit, modifiche non committate, impronta del GT del corpus."""
    diagrams = corpus_gt() if diagrams is None else diagrams
    commit = git("rev-parse", "HEAD")[:12] or "?"
    dirty = " (con modifiche non committate)" if git("status", "--porcelain") else ""
    file_sha = hashlib.sha256(CORPUS_JSONL.read_bytes()).hexdigest()[:16] if CORPUS_JSONL.exists() else "?"
    return (f"Analisi eseguita sul commit `{commit}`{dirty}. GT del corpus: {len(diagrams)} diagrammi, sha256 del "
            f"contenuto `{gt_digest(diagrams)}` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); "
            f"file `corpus/processed/corpus.jsonl` sha256 `{file_sha}…`.")
