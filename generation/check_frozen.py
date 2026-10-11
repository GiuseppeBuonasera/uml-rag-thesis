"""
Verifica del file congelato degli esempi (voce 129), con il retriever denso REALE (per questo non sta nella suite di
test, che non carica sentence-transformers). Nessun LLM.

Per i 26 esercizi di sviluppo (corpus/roles.yaml), nelle due configurazioni di lavoro (P-G: PlantUML, istruzioni v5,
serializzazione compact; C-G: compatto, istruzioni v5, esempi indentati) e per ogni condizione congelata (bm25 k = 2 e
3, dense k = 3, hybrid k = 3, random k = 3 nelle ripetizioni 0, 1, 2 con il seme random_seed(id, r), voce 130):
  1. prompt dal file congelato (retrieval_source "frozen") IDENTICI, sha256 dei messaggi come nel runner, a quelli
     costruiti dal vivo;
  2. dove esiste una run di sviluppo con la stessa configurazione e lo stesso pool unico, IDENTICI anche ai prompt
     registrati nel suo manifest (prompt_sha256): dev_v5__P-G, dev_v5__C-G (v5, compact), dev_c5indent__C-G (v5,
     indent2), dev_v5base__P-G e __C-G (v4), tutte bm25 k = 3. dev_retrievers (dense / hybrid) NON e' confrontabile:
     usava il pool storico di 58 candidati del corpus (prima della voce 115).

Uso:
    python generation/check_frozen.py
"""

from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "generation"), str(ROOT / "retrieval"), str(ROOT / "corpus")]
import paths  # noqa: E402
from prompt_builder import PromptBuilder, PromptSpec, random_seed  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
CONFIGS = {"P-G": {"output_format": "plantuml", "serialization": "compact"},
           "C-G": {"output_format": "compact", "serialization": "indent2"}}
CONDITIONS = (("bm25", 2), ("bm25", 3), ("dense", 3), ("hybrid", 3), ("random", 3))
# run di sviluppo sul pool unico con bm25 k = 3: (run, configurazione, versione delle istruzioni, serializzazione)
RUNS = (("dev_v5", "P-G", "v5", "compact"), ("dev_v5", "C-G", "v5", "compact"), ("dev_c5indent", "C-G", "v5", "indent2"),
        ("dev_v5base", "P-G", "v4", "compact"), ("dev_v5base", "C-G", "v4", "compact"))


def sha(bp) -> str:
    return hashlib.sha256(json.dumps(bp.messages, ensure_ascii=False).encode()).hexdigest()  # come il runner


def spec(cond, k, conf, version="v5", serialization=None, seed=0) -> PromptSpec:
    c = CONFIGS[conf]
    return PromptSpec(cond, k=k, seed=seed, output_format=c["output_format"], instructions_version=version,
                      serialization=serialization or c["serialization"], layout="user_only", drop_interactive=True)


def main() -> int:
    dev = sorted(i for i, r in paths.load_roles().items() if r["role"] == "sviluppo")
    live = PromptBuilder(pool="all", retrieval_source="live")
    frozen = PromptBuilder(pool="all", retrieval_source="frozen")
    print(f"file congelato sha256 {frozen.frozen_sha256}; {len(dev)} esercizi di sviluppo")
    n = 0
    for q in dev:
        query = live.all_by_id[q]
        for conf in CONFIGS:
            for cond, k in CONDITIONS:
                for seed in ([random_seed(q, r) for r in range(3)] if cond == "random" else [0]):
                    a, b = live.build(query, spec(cond, k, conf, seed=seed)), frozen.build(query, spec(cond, k, conf, seed=seed))
                    assert a.example_ids == b.example_ids and sha(a) == sha(b), (q, conf, cond, k, seed)
                    n += 1
    print(f"  OK  {n} prompt (26 esercizi x 2 configurazioni x (4 condizioni + random in 3 ripetizioni)): "
          "congelato = dal vivo (sha256)")
    for run, conf, version, ser in RUNS:
        run_dir = RESULTS / f"{run}__{conf}"
        cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))["config"]
        p = cfg.get("prompt") or {}
        assert (p.get("instructions_version", "v4"), p.get("serialization", "compact")) == (version, ser), (run, p)
        assert cfg.get("pool", "all") == "all" and cfg["conditions"] == ["bm25"], run
        manifest = [json.loads(x) for x in (run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if x]
        checked = 0
        for m in manifest:
            if m["k"] != 3:
                continue
            bp = frozen.build(frozen.all_by_id[m["query_id"]], spec("bm25", 3, conf, version, ser))
            assert bp.example_ids == m["example_ids"] and sha(bp) == m["prompt_sha256"], (run, conf, m["call_id"])
            checked += 1
        print(f"  OK  {run}__{conf}: {checked} prompt del manifest = prompt dal file congelato (sha256)")
    print("Verifica del file congelato superata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
