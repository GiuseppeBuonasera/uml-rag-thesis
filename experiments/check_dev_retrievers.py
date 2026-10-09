"""
Controlli PRIMA delle run del controllo di funzionamento dei retriever (voce 109). Nessuna chiamata a un LLM; il test set
non si legge (split corpus, PromptBuilder senza query del test set).

1. Baseline riprodotta: per ogni configurazione (P-G, C-G) e per i 20 esercizi, il prompt bm25 k = 3 ricostruito oggi ha
   lo stesso prompt_sha256 registrato nel manifest di dev_k (stessi esempi, stesso testo).
2. Prompt diversi SOLO negli esempi: per dense, hybrid e oracle_jt, istruzioni e traccia identiche alla baseline e
   testo identico togliendo il blocco esempi; per un esercizio per formato e condizione si stampa il diff (righe).
3. Leave-one-out e candidati: per ogni condizione e ciascuna delle 59 query del corpus, la query non e' mai tra gli
   esempi e gli esempi stanno in pool(query), che e' lo stesso insieme di candidati di bm25 (indice BM25 = pool,
   excluded(query) = {query}); oracle_jt = top-3 per Jt ricalcolato a parte; dense e hybrid coincidono con i top-3 del
   LOO della voce 108 (data/results/retrieval/dense_2026-10-09_22f5adf/top3.csv).
4. Esempi in comune con bm25 per esercizio (dev set).

Uso:
    python experiments/check_dev_retrievers.py [--config experiments/configs/dev_retrievers.yaml]
"""

from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import argparse
import csv
import difflib
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import run_experiment as rx  # noqa: E402
from prompt_builder import PromptBuilder, PromptSpec, cl  # noqa: E402
import relevance  # noqa: E402  (dal path di retrieval aggiunto da prompt_builder)

RESULTS = ROOT / "data" / "results" / "generation"
LOO_TOP3 = ROOT / "data" / "results" / "retrieval" / "dense_2026-10-09_22f5adf" / "top3.csv"
BASELINE_PREFIX, BASELINE_K = "dev_k", 3


def sha(bp) -> str:
    return hashlib.sha256(json.dumps(bp.messages, ensure_ascii=False).encode()).hexdigest()


def spec_for(cfg: dict, conf: dict, cond: str, k: int) -> PromptSpec:
    p = cfg.get("prompt", {})
    return PromptSpec(cond, k=k, seed=cfg.get("seed", 0), serialization=p.get("serialization", "compact"),
                      layout=p.get("layout", "user_only"), drop_interactive=p.get("drop_interactive", True),
                      output_format=conf["output_format"], instructions_variant=p.get("instructions_variant", "base"))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "experiments" / "configs" / "dev_retrievers.yaml"))
    a = ap.parse_args()
    cfg = yaml.safe_load(Path(a.config).read_text(encoding="utf-8"))
    assert cfg["split"] == "corpus"
    candidates = cl.load_candidates()
    builder = PromptBuilder(candidates, [])  # nessuna query del test set: si lavora solo sul corpus
    dev = [c for c in candidates if c["id"] in set(cfg["query_ids"])]
    assert len(dev) == 20

    # 1-2. baseline e diff
    print("1-2. Baseline riprodotta e prompt diversi solo negli esempi")
    for name, conf in cfg["configurations"].items():
        manifest = RESULTS / f"{BASELINE_PREFIX}__{name}" / "manifest.jsonl"
        logged = {}
        for line in manifest.read_text(encoding="utf-8").splitlines():
            m = json.loads(line)
            if m["condition"] == "bm25" and m["k"] == BASELINE_K:
                logged.setdefault(m["query_id"], set()).add((m["prompt_sha256"], tuple(m["example_ids"])))
        base = {q["id"]: builder.build(q, spec_for(cfg, conf, "bm25", BASELINE_K)) for q in dev}
        for qid, bp in base.items():
            assert logged[qid] == {(sha(bp), tuple(bp.example_ids))}, (name, qid, logged[qid])
        print(f"  OK  {name}: prompt bm25 k = 3 identici a quelli di {BASELINE_PREFIX}__{name} (20/20, sha256 ed esempi)")
        for cond in cfg["conditions"]:
            for k in cfg["k"]:
                spec = spec_for(cfg, conf, cond, k)
                for q in dev:
                    bp, b0 = builder.build(q, spec), base[q["id"]]
                    assert bp.instructions == b0.instructions and bp.task == b0.task
                    assert bp.text.replace(bp.examples_block, "<ESEMPI>") == b0.text.replace(b0.examples_block, "<ESEMPI>")
                    assert len(bp.example_ids) == k
                q = dev[0]
                bp, b0 = builder.build(q, spec), base[q["id"]]
                d = [l for l in difflib.unified_diff(b0.text.splitlines(), bp.text.splitlines(), lineterm="", n=0)
                     if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
                start = b0.text.index(b0.examples_block)
                inside = all(l[1:] in b0.examples_block or l[1:] in bp.examples_block for l in d)
                print(f"  OK  {name} {cond}: 20/20 prompt uguali alla baseline fuori dal blocco esempi; diff su "
                      f"{q['id']}: {len(d)} righe cambiate, tutte nel blocco esempi: {inside} (esempi bm25 "
                      f"{b0.example_ids} -> {bp.example_ids}; il blocco inizia al carattere {start})")
                assert inside

    # 3. leave-one-out e candidati
    print("3. Leave-one-out e candidati (59 query del corpus)")
    loo = {}
    for r in csv.DictReader(LOO_TOP3.open(encoding="utf-8")):
        loo.setdefault((r["retriever"], r["query"]), []).append((int(r["rank"]), r["vicino"]))
    dense_name = "sentence-transformers/all-MiniLM-L6-v2"
    hybrid_name = "Ibrido RRF (BM25 + all-MiniLM-L6-v2)"
    spec = {c: PromptSpec(c, k=3) for c in ("bm25", "dense", "hybrid", "oracle_jt")}
    for q in candidates:
        pool = {c["id"] for c in builder.pool(q)}
        assert builder.excluded(q) == {q["id"]} and len(pool) == 58
        assert set(builder.bm25_for(q).ids) == pool  # indice BM25 della query = stesso insieme di candidati
        sel = {c: [e["id"] for e in builder.select(q, s)] for c, s in spec.items()}
        for c, ids in sel.items():
            assert q["id"] not in ids and set(ids) <= pool and len(set(ids)) == 3, (c, q["id"], ids)
        qt = relevance.class_tokens(q["diagram_apollon_json"])
        expect = sorted(pool, key=lambda i: (-cl.jaccard(qt, builder.tokens[i]), i))[:3]
        assert sel["oracle_jt"] == list(reversed(expect)), (q["id"], sel["oracle_jt"], expect)
        for c, rname in (("dense", dense_name), ("hybrid", hybrid_name), ("bm25", "BM25")):
            ref = [i for _, i in sorted(loo[(rname, q["id"])])]
            assert sel[c] == list(reversed(ref)), (c, q["id"], sel[c], ref)
    print("  OK  per bm25, dense, hybrid, oracle_jt: la query non e' mai tra gli esempi; candidati = pool(query) = gli "
          "altri 58 (stesso insieme dell'indice BM25, nessuna altra esclusione); oracle_jt = top-3 per Jt (pareggi per "
          "id); bm25, dense e hybrid identici ai top-3 del LOO della voce 108")

    # 4. esempi in comune con bm25
    print("4. Esempi in comune con bm25 (dev set, k = 3)")
    print("  | esercizio | dense | hybrid | oracle_jt |")
    tot = {c: 0 for c in ("dense", "hybrid", "oracle_jt")}
    for q in dev:
        b = set(e["id"] for e in builder.select(q, spec["bm25"]))
        row = {c: len(b & {e["id"] for e in builder.select(q, spec[c])}) for c in tot}
        for c in tot:
            tot[c] += row[c]
        print(f"  | {q['id']} | {row['dense']}/3 | {row['hybrid']}/3 | {row['oracle_jt']}/3 |")
    print("  | totale | " + " | ".join(f"{tot[c]}/60" for c in tot) + " |")
    print("\nTutti i controlli prima delle run sono passati.")


if __name__ == "__main__":
    main()
