"""
Esempi recuperati CONGELATI per il Passo 3b (2026-10-11, voce 129). Nessun LLM, nessuna nuova scelta: retriever e
parametri sono quelli chiusi (voci 105-110, 115, 122, 124).

Per ognuno degli 80 esercizi come query (pool unico, 79 candidati), con lo STESSO codice del prompt builder
(generation/prompt_builder.PromptBuilder.hits, modalita' "live"):
  bm25   k = 2 e k = 3   configurazione congelata retrieval/config_bm25.yaml, indice rifittato senza la query
  dense  k = 3           all-MiniLM-L6-v2 alla revisione fissata (config_dense.yaml), CPU, offline
  hybrid k = 3           RRF (c = 60) tra bm25 e dense
  random k = 3           voce 130: un'estrazione per esercizio E ripetizione (r = 0, 1, 2), seme
                         prompt_builder.random_seed(id, r); l'estrazione dipende da sha256(seme, traccia) sul pool
salva gli id nell'ordine del retriever (rango 1 = il piu' simile; random: ordine di estrazione) e i punteggi in
data/retrieval_frozen/retrievals_3b.jsonl (versionato) e, accanto, retrievals_3b.meta.json con lo sha256 del file e la
provenienza (commit, modello e revisione del denso, versioni dei pacchetti, sha256 della cache degli embedding, dei
config e dei dati). Il prompt builder con retrieval_source "frozen" legge questo file e ne verifica lo sha256.

Pareggi: l'ordinamento a parita' di punteggio e' per id crescente (base.rank_results), come sempre. Si riportano i
pareggi ESATTI di punteggio (il punto fragile tra macchine diverse): dentro i top-k (cambiano solo l'ordine nel prompt)
e al confine k / k+1 (cambiano gli esempi scelti).

`--solo-random` (voce 130): rigenera SOLO le righe random; quelle di bm25 / dense / hybrid si copiano TALI E QUALI dal
file esistente (nessun ricalcolo, quindi nessuna deriva del denso) e si verifica che restino identiche byte per byte; i
metadati del denso, delle versioni e dei pareggi restano quelli della generazione precedente (si riferiscono alle righe
non random), con lo sha256 precedente in "storia".

Uso:
    python retrieval/freeze_retrievals.py [--out data/retrieval_frozen/retrievals_3b.jsonl] [--force] [--solo-random]
"""

from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # i modelli si scaricano una volta (download_dense_models.py)

import argparse
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "retrieval"), str(ROOT / "generation"), str(ROOT / "experiments"), str(ROOT / "corpus")]
from prompt_builder import (BM25_CONFIG, DENSE_CONFIG, FROZEN_PATH, PromptBuilder, PromptSpec,  # noqa: E402
                            dense_model, random_seed)

PLAN = (("bm25", 2), ("bm25", 3), ("dense", 3), ("hybrid", 3), ("random", 3))
RANDOM_REPETITIONS = 3  # voce 130: ripetizioni del 3b indicate dall'utente; se saranno di piu', vanno aggiunte
SCORED = ("bm25", "dense", "hybrid")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def embedding_digest(path: Path, records: list[dict]) -> str | None:
    """sha256 del CONTENUTO della cache per i testi usati: (chiave del testo, vettore float32) nell'ordine degli id.
    Lo sha256 del file .npz non e' stabile (l'archivio si riscrive a ogni ricalcolo, voce 129)."""
    import numpy as np
    from dense_retriever import EmbeddingCache, text_key
    if not path.exists():
        return None
    vectors = EmbeddingCache(path).vectors
    h = hashlib.sha256()
    for r in sorted(records, key=lambda x: x["id"]):
        k = text_key(r["description"])
        h.update(k.encode("ascii"))
        h.update(np.asarray(vectors[k], dtype=np.float32).tobytes())
    return h.hexdigest()


def freeze_rows(builder: PromptBuilder, queries: list[dict], plan=PLAN, repetitions=RANDOM_REPETITIONS,
                only: tuple[str, ...] | None = None) -> list[dict]:
    """Una riga per (query, retriever, k, seme); random: una riga per ripetizione r con il seme random_seed(id, r)
    (voce 130). Ordine stabile: query per id, poi il piano, poi r. only: solo questi retriever."""
    rows = []
    for q in sorted(queries, key=lambda x: x["id"]):
        for cond, k in plan:
            if only is not None and cond not in only:
                continue
            for r in (range(repetitions) if cond == "random" else (None,)):
                seed = None if r is None else random_seed(q["id"], r)
                hits = builder.hits(q, PromptSpec(cond, k=k, seed=seed or 0))
                if len(hits) != k:
                    raise AssertionError(f"{q['id']} {cond} k={k}: {len(hits)} risultati")
                rows.append({"query": q["id"], "retriever": cond, "k": k, "seed": seed,
                             **({"repetition": r} if r is not None else {}), "ids": [h.id for h in hits],
                             "scores": [float(h.score) for h in hits], "score_norm": [float(h.score_norm) for h in hits]})
    return rows


def merge_random(old_lines: list[str], random_rows: list[dict], order: list[str]) -> list[str]:
    """Righe non random copiate tali e quali dal file esistente + nuove righe random, nell'ordine canonico (query per
    id, poi il piano, poi la ripetizione)."""
    rank = {c: i for i, (c, _k) in enumerate(PLAN)}
    keep = [(json.loads(x), x) for x in old_lines if x.strip() and json.loads(x)["retriever"] != "random"]
    new = [(r, json.dumps(r, ensure_ascii=False)) for r in random_rows]
    pos = {q: i for i, q in enumerate(order)}
    items = sorted(keep + new, key=lambda t: (pos[t[0]["query"]], rank[t[0]["retriever"]], t[0]["k"],
                                              t[0].get("repetition", -1)))
    return [x for _, x in items]


def tie_report(builder: PromptBuilder, queries: list[dict], plan=PLAN) -> dict:
    """Pareggi ESATTI di punteggio per retriever con punteggio: query con almeno due punteggi uguali nei top-k (solo
    l'ordine nel prompt dipende dall'id) e query con il k-esimo uguale al (k+1)-esimo (gli esempi scelti dipendono
    dall'id)."""
    out = {}
    for cond, k in plan:
        if cond not in SCORED:
            continue
        inside, boundary = [], []
        for q in sorted(queries, key=lambda x: x["id"]):
            hits = builder.hits(q, PromptSpec(cond, k=k + 1))
            s = [h.score for h in hits]
            if len(set(s[:k])) < k:
                inside.append(q["id"])
            if s[k - 1] == s[k]:
                boundary.append(q["id"])
        out[f"{cond}@{k}"] = {"query_con_pareggi_nei_top_k": len(inside), "query_con_pareggio_al_confine": len(boundary),
                              "esercizi_nei_top_k": inside, "esercizi_al_confine": boundary}
    return out


PACKAGES = ("numpy", "rank-bm25", "snowballstemmer", "sentence-transformers", "transformers", "torch", "tokenizers",
            "huggingface-hub")


def versions() -> dict:
    """Versioni dai metadati dei pacchetti installati (senza importarli: transformers + torchaudio rotto, voce 107)."""
    from importlib.metadata import PackageNotFoundError, version
    out = {"python": platform.python_version()}
    for name in PACKAGES:
        try:
            out[name] = version(name)
        except PackageNotFoundError:
            out[name] = None
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out", default=str(FROZEN_PATH))
    ap.add_argument("--force", action="store_true", help="sovrascrive un file congelato esistente (da motivare)")
    ap.add_argument("--solo-random", action="store_true", help="rigenera solo le righe random (voce 130)")
    args = ap.parse_args(argv)
    if args.solo_random:
        return main_only_random(Path(args.out))
    out = Path(args.out)
    meta_path = out.with_suffix(".meta.json")
    if out.exists() and not args.force:
        raise SystemExit(f"{out} esiste gia': il file congelato non si sovrascrive senza --force (e una nuova voce)")

    import corpus_loader as cl
    import paths
    import provenance
    from dense_retriever import cache_path
    builder = PromptBuilder(pool="all", retrieval_source="live")
    queries = builder.candidates + builder.test_queries
    assert len(queries) == 80 and len({q["id"] for q in queries}) == 80
    rows = freeze_rows(builder, queries)
    ties = tie_report(builder, queries)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8", newline="\n")
    model, revision = dense_model()
    cache = cache_path(model, revision)
    roles = paths.load_roles()
    meta = {
        "file": str(out.relative_to(ROOT)).replace("\\", "/") if out.is_relative_to(ROOT) else str(out),
        "sha256": sha256_file(out), "righe": len(rows),
        "voce": 129, "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": git("rev-parse", "HEAD"), "working_tree_dirty": bool(git("status", "--porcelain")),
        "piano": [{"retriever": c, "k": k} for c, k in PLAN], **RANDOM_META,
        "ordine": "ids nell'ordine del retriever (rango 1 = il piu' simile; random = ordine di estrazione); nel prompt "
                  "bm25 / dense / hybrid si invertono (il piu' simile per ultimo), random no",
        "pool": "unico (voce 115): 80 esercizi, per ogni query gli altri 79",
        "query": {"totale": len(queries), "sviluppo": sum(r["role"] == "sviluppo" for r in roles.values()),
                  "valutazione": sum(r["role"] == "valutazione" for r in roles.values())},
        "denso": {"modello": model, "revisione": revision, "dispositivo": "cpu",
                  "cache_embedding": str(cache.relative_to(ROOT)).replace("\\", "/"),
                  "embedding_sha256_contenuto": embedding_digest(cache, queries),
                  "nota": "sha256 dei vettori (float32) degli 80 testi, chiave = sha256 del testo; il file .npz si "
                          "riscrive a ogni ricalcolo, quindi il suo sha256 non e' un'impronta stabile"},
        "versioni": versions(),
        "sha256_input": {"config_bm25": sha256_file(BM25_CONFIG), "config_dense": sha256_file(DENSE_CONFIG),
                   "corpus_jsonl": sha256_file(paths.CORPUS_JSONL), "testset_jsonl": sha256_file(paths.TESTSET_JSONL),
                   "roles_yaml": sha256_file(paths.ROLES_YAML),
                   "gt_80": provenance.gt_digest({q["id"]: q["diagram_apollon_json"] for q in queries})},
        "pareggi": ties,
    }
    assert cl.load_pool("all80") and len(builder.all_by_id) == 80
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _set_output(out)
    print(f"scritto {out} ({len(rows)} righe, sha256 {meta['sha256']}) e {meta_path.name}")
    for key, t in ties.items():
        print(f"  pareggi {key}: nei top-k {t['query_con_pareggi_nei_top_k']}, al confine "
              f"{t['query_con_pareggio_al_confine']}")
    return 0


RANDOM_META = {
    "random_ripetizioni": RANDOM_REPETITIONS,
    "nota_random": "voce 130: un'estrazione per esercizio e ripetizione r = 0..2, seme = int(sha256('random|<id>|<r>')"
                   "[:8], 16) (prompt_builder.random_seed); l'estrazione dipende da sha256(seme, traccia) sul pool "
                   "ordinato per id; il runner la usa con random_seed: per_esercizio_ripetizione"}


def main_only_random(out: Path) -> int:
    """Voce 130: solo le righe random, il resto copiato tale e quale e verificato byte per byte."""
    meta_path = out.with_suffix(".meta.json")
    old_bytes = out.read_bytes()
    old_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if hashlib.sha256(old_bytes).hexdigest() != old_meta["sha256"]:
        raise SystemExit("il file congelato non corrisponde al suo .meta.json: non si rigenera la parte random")
    old_lines = old_bytes.decode("utf-8").split("\n")
    builder = PromptBuilder(pool="all", retrieval_source="live")  # random non usa il denso: nessun modello caricato
    queries = builder.candidates + builder.test_queries
    rows = freeze_rows(builder, queries, only=("random",))
    lines = merge_random(old_lines, rows, sorted(q["id"] for q in queries))
    nonrandom = lambda xs: [x for x in xs if x.strip() and json.loads(x)["retriever"] != "random"]  # noqa: E731
    assert nonrandom(lines) == nonrandom(old_lines), "righe bm25 / dense / hybrid cambiate"
    out.write_text("".join(x + "\n" for x in lines), encoding="utf-8", newline="\n")
    assert nonrandom(out.read_text(encoding="utf-8").split("\n")) == nonrandom(old_lines)
    meta = dict(old_meta)
    for key in ("semi_random",):
        meta.pop(key, None)
    meta.update({"sha256": sha256_file(out), "righe": len(lines), "voce": 130, **RANDOM_META,
                 "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "commit": git("rev-parse", "HEAD"), "working_tree_dirty": bool(git("status", "--porcelain")),
                 "storia": old_meta.get("storia", []) + [{
                     "sha256": old_meta["sha256"], "voce": old_meta.get("voce"),
                     "nota": "versione precedente; voce 130: rigenerate SOLO le righe random (seme per esercizio e "
                             "ripetizione), righe bm25 / dense / hybrid identiche byte per byte"}]})
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _set_output(out)
    print(f"scritto {out} ({len(lines)} righe, sha256 {meta['sha256']}); righe non random identiche: "
          f"{len(nonrandom(lines))}; righe random: {len(rows)}")
    return 0


def _set_output(path) -> None:
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(path)


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
