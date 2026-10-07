"""
Schema JSON usato per la GENERAZIONE VINCOLATA della strada 2 (secondo pilota, 2026-10-07). La validazione (L2) usa
sempre evaluation/uml-model-4.schema.json, che NON si modifica.

Trasformazioni rispetto allo schema ufficiale (documentate in docs/decisions.md, voce 78):
1. $ref espansi in linea e "definitions" rimosso: llama.cpp (motore di LM Studio per i GGUF) dichiara "Nested $refs
   are broken" nella conversione JSON Schema -> grammatica, e lo schema ufficiale ha un $ref annidato
   (OrthogonalEdgeData -> IPoint). Lo schema risultante accetta esattamente gli stessi documenti.
2. "maxItems" su "edges" = 3 x il massimo di relazioni nei ground truth del corpus SELEZIONABILI per i piloti
   (experiments/select_pilot.py: senza known_issues e con GT compatto <= massimo del test set). Tetto contro i cicli
   di relazioni osservati nel primo pilota (voce 77); e' l'unico vincolo in piu'.

Uso:  python generation/make_generation_schema.py   (scrive generation/schemas/apollon_v4_generation.schema.json)
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "evaluation" / "uml-model-4.schema.json"
TARGET = HERE / "schemas" / "apollon_v4_generation.schema.json"
EDGE_CAP_FACTOR = 3


def inline_refs(node, definitions: dict):
    if isinstance(node, dict):
        if set(node) == {"$ref"}:
            return inline_refs(copy.deepcopy(definitions[node["$ref"].split("/")[-1]]), definitions)
        return {k: inline_refs(v, definitions) for k, v in node.items() if k != "definitions"}
    if isinstance(node, list):
        return [inline_refs(x, definitions) for x in node]
    return node


def max_selectable_edges() -> tuple[int, str, int]:
    sys.path.insert(0, str(ROOT / "experiments"))
    sys.path.insert(0, str(HERE))
    import select_pilot
    from prompt_builder import PromptBuilder, cl
    candidates, queries = cl.load_all()
    rows = [r for r in select_pilot.table(PromptBuilder(candidates, queries)) if not r["excluded"]]
    by_id = {c["id"]: c for c in candidates}
    best = max(rows, key=lambda r: (len(by_id[r["id"]]["diagram_apollon_json"]["edges"]), r["id"]))
    return len(by_id[best["id"]]["diagram_apollon_json"]["edges"]), best["id"], len(rows)


def build_schema() -> tuple[dict, dict]:
    src = json.loads(SOURCE.read_text(encoding="utf-8"))
    schema = inline_refs(src, src.get("definitions", {}))
    max_edges, where, n = max_selectable_edges()
    schema["properties"]["edges"]["maxItems"] = EDGE_CAP_FACTOR * max_edges
    info = {"source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(), "max_edges_selectable": max_edges,
            "max_edges_exercise": where, "selectable_candidates": n, "edges_maxItems": EDGE_CAP_FACTOR * max_edges}
    return schema, info


def main() -> int:
    schema, info = build_schema()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(schema, ensure_ascii=False, indent=1) + "\n"
    TARGET.write_text(text, encoding="utf-8")
    info["generation_schema_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(json.dumps(info, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
