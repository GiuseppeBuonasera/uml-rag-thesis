"""
Varianti del retriever (voce 120, passo 3): valutazione SOLO del retrieval in leave-one-out sul pool unico (80 esercizi:
per ogni query gli altri 79, voce 115). Nessun LLM. Descrittiva: la scelta delle varianti da portare alle generazioni
si fa allo STOP dopo questo passo.

Retriever: bm25 (congelato), dense (MiniLM, voce 108), hybrid (RRF bm25 + MiniLM), e le varianti della voce 120:
  v2 struttura BM25, v2s struttura BM25 + sinonimi WordNet, v2d struttura densa (ciascuna in RRF con bm25),
  v3 MMR su bm25, v4 costrutti su bm25, v5 qualita' su bm25, v6 MiniLM a pezzi (256 token).
Misure (voce 107, nessun embedding): J, Jt, S a k = 1, 2, 3; copertura dei tipi di relazione del GT della query nei
primi 3 esempi; sovrapposizione dei top-3 con bm25; hubness. ATTENZIONE: v2 / v2s / v2d confrontano la traccia con i nomi
di classe dei candidati e J / Jt misurano i nomi di classe: sono favorite per costruzione.

Uso:
    python retrieval/analyze_variants.py [--run-id ID]
"""

from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import argparse
import datetime as dt
import json
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus_loader as cl
import structure_retrievers as sr
from dense_retriever import DenseRetriever
from hybrid_retriever import HybridRetriever
from keyword_retriever import KeywordRetriever
from relevance import Relevance
from text_preprocessing import PreprocessConfig

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "data" / "results" / "retrieval"
TOP_K = 3
MEASURES = ("J", "Jt", "S")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def bm25():
    cfg = yaml.safe_load((Path(__file__).resolve().parent / "config_bm25.yaml").read_text(encoding="utf-8"))
    r, p = cfg["retriever"], cfg["preprocessing"]
    return KeywordRetriever(k1=r["k1"], b=r["b"], preprocess=PreprocessConfig(p["stopwords"], p["stemming"]))


def minilm(chunk: int | None = None) -> DenseRetriever:
    esito = yaml.safe_load((Path(__file__).resolve().parent / "config_dense.yaml").read_text(encoding="utf-8"))["esito"]
    return DenseRetriever(esito["scelto"], esito["revisione"], chunk_tokens=chunk)


class Prefitted:
    """Retriever indicizzato una volta su tutti gli 80 (le esclusioni si passano a retrieve): per i densi, il cui indice
    non dipende dal pool."""

    def __init__(self, inner, records):
        self.inner = inner.fit(records)

    def fit(self, records):
        return self

    def retrieve(self, query_text, k, exclude_ids=()):
        return self.inner.retrieve(query_text, k, exclude_ids)


def factories(records: list[dict]) -> dict:
    """nome -> funzione che costruisce il retriever (rifittato per ogni query sul pool; i densi indicizzati una volta)."""
    dense = Prefitted(minilm(), records)
    chunked = Prefitted(minilm(256), records)
    sdense = Prefitted(sr.StructureDense(minilm()), records)
    return {
        "bm25": bm25,
        "dense (MiniLM)": lambda: dense,
        "hybrid (RRF bm25 + MiniLM)": lambda: HybridRetriever(bm25(), dense),
        "v2 struttura BM25": lambda: sr.RRF(bm25(), sr.StructureBM25()),
        "v2s struttura + sinonimi": lambda: sr.RRF(bm25(), sr.StructureBM25(synonyms=True)),
        "v2d struttura densa": lambda: sr.RRF(bm25(), sdense),
        "v3 MMR": lambda: sr.MMR(bm25()),
        "v4 costrutti": lambda: sr.ConstructBoost(bm25()),
        "v5 qualità": lambda: sr.QualityWeighted(bm25()),
        "v6 MiniLM a pezzi": lambda: chunked,
    }


def run_loo(records: list[dict], make) -> list[dict]:
    rows = []
    for q in records:
        pool = [r for r in records if r["id"] != q["id"]]
        top = make().fit(pool).retrieve(q["description"], TOP_K, exclude_ids={q["id"]})
        assert q["id"] not in {t.id for t in top} and len(top) == TOP_K
        rows.append({"query": q["id"], "top": [t.id for t in top]})
    return rows


def evaluate(rows, rel: Relevance, types: dict) -> dict:
    out = {}
    for m in MEASURES:
        for k in (1, 2, 3):
            out[f"{m}@{k}"] = statistics.mean(statistics.mean(rel.measure(r["query"], d)[m] for d in r["top"][:k])
                                              for r in rows)
    out["copertura@3"] = statistics.mean(
        len(types[r["query"]] & set().union(*(types[d] for d in r["top"]))) / len(types[r["query"]])
        if types[r["query"]] else 1.0 for r in rows)
    c1, c3 = Counter(r["top"][0] for r in rows), Counter(d for r in rows for d in r["top"])
    out["distinti@1"], out["max_top3"] = len(c1), max(c3.values())
    out["mai_top3"] = len(rows) - len(c3)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args()
    cands, queries = cl.load_all()
    records = cands + queries
    assert len(records) == 80
    rel = Relevance(records)
    types = {r["id"]: {e["type"] for e in r["diagram_apollon_json"]["edges"]} for r in records}
    rows, metrics, timing = {}, {}, {}
    for name, make in factories(records).items():
        t0 = time.perf_counter()
        rows[name] = run_loo(records, make)
        timing[name] = round(time.perf_counter() - t0, 1)
        metrics[name] = evaluate(rows[name], rel, types)
        print(name, {k: round(v, 3) if isinstance(v, float) else v for k, v in metrics[name].items()}, flush=True)
    base = {r["query"]: set(r["top"]) for r in rows["bm25"]}
    overlap = {n: statistics.mean(len(base[r["query"]] & set(r["top"])) / TOP_K for r in rs) for n, rs in rows.items()}

    run_id = args.run_id or f"variants_{dt.date.today().isoformat()}_{git('rev-parse', '--short', 'HEAD')}"
    out = RESULTS / run_id
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "experiments"))
    import provenance
    L = [f"# Varianti del retriever — leave-one-out sul pool unico ({run_id})", "",
         "Voce 120, passo 3: SOLO retrieval, nessuna generazione, descrittivo. 80 query, per ognuna gli altri 79 "
         "candidati (voce 115). Misure senza embedding (voce 107); copertura = quota dei tipi di relazione del GT della "
         "query presenti nei primi 3 esempi. **v2 / v2s / v2d sono favorite per costruzione su J e Jt** (confrontano la "
         "traccia con i nomi di classe dei candidati).", "", provenance.provenance_line(), "",
         "| retriever | J@1 | J@3 | Jt@1 | Jt@3 | S@3 | copertura@3 | ∩ top-3 con bm25 | distinti al rango 1 | max nei "
         "top-3 | mai nei top-3 | secondi |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, m in metrics.items():
        L.append(f"| {n} | {m['J@1']:.3f} | {m['J@3']:.3f} | {m['Jt@1']:.3f} | {m['Jt@3']:.3f} | {m['S@3']:.3f} | "
                 f"{m['copertura@3']:.3f} | {overlap[n]:.2f} | {m['distinti@1']} | {m['max_top3']} | {m['mai_top3']} | "
                 f"{timing[n]} |")
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "top3.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"Scritto: {out}")
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(ROOT / "experiments"))
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        main()
