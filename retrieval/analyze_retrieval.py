"""
Analisi leave-one-out (LOO) del retrieval sul corpus (Passo 2, FASE 2, 2026-10-04). Nessun LLM.

Per ogni candidato q (59 record convertiti): l'indice si costruisce sugli ALTRI candidati (cosi' q non entra nelle
statistiche IDF / avgdl, come le query del test set) e si recuperano i top-3 per la description di q.
Pertinenza proxy, SOLO in analisi e mai nel ranking: Jaccard dei nomi di classe normalizzati (case-insensitive) tra
il diagramma di q e quello del vicino.

Riepiloghi: Jaccard medio @1 e @3 per BM25, random (N seed: media e deviazione standard tra seed) e oracolo (miglior
Jaccard possibile = limite superiore); Spearman tra score_norm e Jaccard del top-1. Sensibilita' (solo LOO): stopword,
stemming, griglia k1 x b. Varianti: senza quasi-duplicati come vicini, senza EatAtHome (known_issues).

Il test set NON viene mai letto qui, a parte il controllo di disgiunzione del loader.

Output in data/results/retrieval/<run_id>/: config.json (commit, tag del test set, parametri), summary.md,
sensitivity.csv, variants.csv, near_duplicates.csv, loo_top3.csv.

Uso:
    python retrieval/analyze_retrieval.py [--run-id ID] [--seeds 20]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import itertools
import json
import math
import platform
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus_loader as cl
from keyword_retriever import KeywordRetriever
from random_retriever import RandomRetriever
from text_preprocessing import PreprocessConfig

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "data" / "results" / "retrieval"
TESTSET_TAG = "testset-v1"
TESTSET_PATHS = ["corpus/raw/debari_test", "corpus/processed/testset_debari.jsonl", "corpus/processed/apollon_debari"]

K1_GRID = (0.9, 1.2, 1.5, 2.0)
B_GRID = (0.5, 0.75, 0.9)
DEFAULT = {"stopwords": True, "stem": True, "k1": 1.5, "b": 0.75}  # default di rank_bm25 + preprocessing completo
TOP_K = 3
NEAR_DUP_JACCARD = 0.25  # coppie in cima alla distribuzione dei Jaccard tra candidati (massimo osservato: 0.25)
NEAR_DUP_TFIDF = 0.25  # coppie in cima alla distribuzione della similarita' delle descrizioni (TF-IDF del leakage)
KNOWN_ISSUE_ID = "EatAtHome"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def run_metadata(params: dict) -> dict:
    tag_commit = git("rev-list", "-n", "1", TESTSET_TAG)
    unchanged = subprocess.run(["git", "diff", "--quiet", TESTSET_TAG, "--", *TESTSET_PATHS], cwd=ROOT).returncode == 0
    import rank_bm25, snowballstemmer, sklearn, scipy  # noqa: E401 - solo per le versioni
    return {
        "commit": git("rev-parse", "HEAD"),
        "working_tree_dirty": bool(git("status", "--porcelain")),
        "testset_tag": TESTSET_TAG,
        "testset_tag_commit": tag_commit,
        "testset_unchanged_since_tag": unchanged,
        "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": platform.python_version(),
        "versions": {"rank_bm25": "0.2.2 (pin in requirements.txt)", "snowballstemmer": snowballstemmer.__version__
                     if hasattr(snowballstemmer, "__version__") else "3.1.1 (pin)", "scikit-learn": sklearn.__version__,
                     "scipy": scipy.__version__, "numpy": np.__version__},
        "params": params,
    }


def near_duplicate_pairs(candidates: list[dict], names: dict[str, set[str]]) -> list[dict]:
    """Coppie candidate a quasi-duplicato (NON una decisione: domanda 10 per i relatori)."""
    ids = [c["id"] for c in candidates]
    tfidf = TfidfVectorizer(stop_words="english", sublinear_tf=True).fit_transform([c["description"] for c in candidates])
    sim = cosine_similarity(tfidf)
    out = []
    for i, j in itertools.combinations(range(len(ids)), 2):
        a, b = ids[i], ids[j]
        jac = cl.jaccard(names[a], names[b])
        same_case = a.split("_")[0] == b.split("_")[0]
        reasons = [r for r, ok in (("stesso caso (nome)", same_case), (f"Jaccard >= {NEAR_DUP_JACCARD}", jac >= NEAR_DUP_JACCARD),
                                   (f"TF-IDF descrizioni >= {NEAR_DUP_TFIDF}", sim[i, j] >= NEAR_DUP_TFIDF)) if ok]
        if reasons:
            out.append({"a": a, "b": b, "jaccard": round(jac, 4), "tfidf": round(float(sim[i, j]), 4),
                        "motivo": "; ".join(reasons)})
    return sorted(out, key=lambda p: (-p["jaccard"] - p["tfidf"], p["a"], p["b"]))


def partners(pairs: list[dict]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for p in pairs:
        out.setdefault(p["a"], set()).add(p["b"])
        out.setdefault(p["b"], set()).add(p["a"])
    return out


def loo(candidates, names, make_retriever, exclude=None, drop=frozenset()):
    """Righe per query: top-3 (id, score, score_norm, jaccard) e Jaccard dell'oracolo, indice rifittato senza q."""
    exclude = exclude or {}
    pool_all = [c for c in candidates if c["id"] not in drop]
    rows = []
    for q in pool_all:
        pool = [c for c in pool_all if c["id"] != q["id"]]
        excl = exclude.get(q["id"], set())
        retriever = make_retriever().fit(pool)
        top = retriever.retrieve(q["description"], TOP_K, exclude_ids=excl)
        oracle = sorted((cl.jaccard(names[q["id"]], names[c["id"]]) for c in pool if c["id"] not in excl), reverse=True)
        rows.append({"query": q["id"],
                     "top": [(r.id, r.score, r.score_norm, cl.jaccard(names[q["id"]], names[r.id])) for r in top],
                     "oracle": oracle[:TOP_K]})
    return rows


def summarize(rows) -> dict:
    j1 = [r["top"][0][3] for r in rows]
    j3 = [statistics.mean(t[3] for t in r["top"]) for r in rows]
    n1 = [r["top"][0][2] for r in rows]
    rho, p = spearmanr(n1, j1) if len(set(n1)) > 1 and len(set(j1)) > 1 else (float("nan"), float("nan"))
    return {"n": len(rows), "j1": statistics.mean(j1), "j3": statistics.mean(j3), "rho": float(rho), "p": float(p),
            "oracle1": statistics.mean(r["oracle"][0] for r in rows),
            "oracle3": statistics.mean(statistics.mean(r["oracle"]) for r in rows), "_j1": j1, "_j3": j3}


def random_summary(candidates, names, seeds, exclude=None, drop=frozenset()) -> dict:
    per_seed = [summarize(loo(candidates, names, lambda s=s: RandomRetriever(seed=s), exclude, drop)) for s in range(seeds)]
    return {"j1_mean": statistics.mean(x["j1"] for x in per_seed), "j1_sd": statistics.stdev(x["j1"] for x in per_seed),
            "j3_mean": statistics.mean(x["j3"] for x in per_seed), "j3_sd": statistics.stdev(x["j3"] for x in per_seed)}


def paired(diff_a: list[float], diff_b: list[float]) -> tuple[float, float]:
    d = [a - b for a, b in zip(diff_a, diff_b)]
    return statistics.mean(d), statistics.stdev(d) / math.sqrt(len(d))


def bm25_factory(cfg: dict):
    return lambda: KeywordRetriever(k1=cfg["k1"], b=cfg["b"], preprocess=PreprocessConfig(cfg["stopwords"], cfg["stem"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--seeds", type=int, default=20)
    args = ap.parse_args()

    candidates, _queries = cl.load_all()  # le query del test set servono solo al controllo di disgiunzione
    names = {c["id"]: cl.class_names(c["diagram_apollon_json"]) for c in candidates}
    run_id = args.run_id or f"loo_{dt.date.today().isoformat()}_{git('rev-parse', '--short', 'HEAD')}"
    out = RESULTS_DIR / run_id
    out.mkdir(parents=True, exist_ok=True)

    # --- sensibilita' (variante base) ---
    grid = [{"stopwords": s, "stem": t, "k1": k1, "b": b}
            for s, t, k1, b in itertools.product((True, False), (True, False), K1_GRID, B_GRID)]
    results = {}
    for cfg in grid:
        results[tuple(cfg.values())] = summarize(loo(candidates, names, bm25_factory(cfg)))
    base = results[tuple(DEFAULT.values())]
    sens_rows = []
    for cfg in grid:
        r = results[tuple(cfg.values())]
        d1, se1 = paired(r["_j1"], base["_j1"])
        d3, se3 = paired(r["_j3"], base["_j3"])
        sens_rows.append({**cfg, "j1": r["j1"], "j3": r["j3"], "spearman_rho": r["rho"], "spearman_p": r["p"],
                          "d_j1_vs_default": d1, "se_d_j1": se1, "d_j3_vs_default": d3, "se_d_j3": se3,
                          "significativo_2se": abs(d1) > 2 * se1 or abs(d3) > 2 * se3})
    better = [s for s in sens_rows if s["significativo_2se"] and s["d_j1_vs_default"] > 0 and s["d_j3_vs_default"] >= 0]
    proposal = DEFAULT if not better else {k: max(better, key=lambda s: (s["j1"], s["j3"]))[k] for k in DEFAULT}

    # --- varianti (configurazione proposta) ---
    pairs = near_duplicate_pairs(candidates, names)
    gas = [p for p in pairs if "stesso caso" in p["motivo"]]
    variants = {
        "base": {},
        "senza quasi-duplicati 'stesso caso' come vicini": {"exclude": partners(gas)},
        "senza tutte le coppie candidate come vicini": {"exclude": partners(pairs)},
        f"senza {KNOWN_ISSUE_ID} (query e candidato)": {"drop": frozenset({KNOWN_ISSUE_ID})},
    }
    var_rows = []
    for label, opt in variants.items():
        rows = loo(candidates, names, bm25_factory(proposal), opt.get("exclude"), opt.get("drop", frozenset()))
        s = summarize(rows)
        rnd = random_summary(candidates, names, args.seeds, opt.get("exclude"), opt.get("drop", frozenset()))
        var_rows.append({"variante": label, "n_query": s["n"], "bm25_j1": s["j1"], "bm25_j3": s["j3"],
                         "random_j1_mean": rnd["j1_mean"], "random_j1_sd": rnd["j1_sd"],
                         "random_j3_mean": rnd["j3_mean"], "random_j3_sd": rnd["j3_sd"],
                         "oracolo_j1": s["oracle1"], "oracolo_j3": s["oracle3"],
                         "spearman_rho": s["rho"], "spearman_p": s["p"]})
        if label == "base":
            base_rows = rows

    # --- file ---
    meta = run_metadata({"top_k": TOP_K, "random_seeds": args.seeds, "default": DEFAULT, "proposta": proposal,
                         "griglia": {"stopwords": [True, False], "stem": [True, False], "k1": K1_GRID, "b": B_GRID},
                         "near_dup_soglie": {"jaccard": NEAR_DUP_JACCARD, "tfidf": NEAR_DUP_TFIDF},
                         "loo": "indice rifittato senza la query; exclude_ids solo per le varianti",
                         "pertinenza": "Jaccard dei nomi di nodo Apollon normalizzati (minuscole, alfanumerici)"})
    (out / "config.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def write_csv(name, rows, fields):
        with (out / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k in fields})

    write_csv("sensitivity.csv", sens_rows, list(sens_rows[0]))
    write_csv("variants.csv", var_rows, list(var_rows[0]))
    write_csv("near_duplicates.csv", pairs, ["a", "b", "jaccard", "tfidf", "motivo"])
    top_rows = [{"query": r["query"], "rank": i, "neighbor": t[0], "score": t[1], "score_norm": t[2], "jaccard": t[3]}
                for r in base_rows for i, t in enumerate(r["top"], start=1)]
    write_csv("loo_top3.csv", top_rows, ["query", "rank", "neighbor", "score", "score_norm", "jaccard"])

    # --- summary.md ---
    L = [f"# Retrieval BM25 — leave-one-out sul corpus ({run_id})", "",
         f"Commit `{meta['commit'][:7]}` (working tree {'modificato' if meta['working_tree_dirty'] else 'pulito'}), "
         f"test set `{TESTSET_TAG}` (invariato dal tag: {meta['testset_unchanged_since_tag']}). "
         f"{len(candidates)} candidati, top-{TOP_K}, random su {args.seeds} seed. Pertinenza = Jaccard dei nomi di classe.", "",
         f"Configurazione di default: {DEFAULT}. Proposta: {proposal}.", "",
         "## Varianti (configurazione proposta)", "",
         "| Variante | n | BM25 J@1 | BM25 J@3 | Random J@1 (sd) | Random J@3 (sd) | Oracolo J@1 | Oracolo J@3 | Spearman rho (p) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for v in var_rows:
        L.append(f"| {v['variante']} | {v['n_query']} | {v['bm25_j1']:.3f} | {v['bm25_j3']:.3f} | "
                 f"{v['random_j1_mean']:.3f} ({v['random_j1_sd']:.3f}) | {v['random_j3_mean']:.3f} ({v['random_j3_sd']:.3f}) | "
                 f"{v['oracolo_j1']:.3f} | {v['oracolo_j3']:.3f} | {v['spearman_rho']:.2f} ({v['spearman_p']:.3f}) |")
    L += ["", "## Sensibilità (variante base; differenze appaiate rispetto al default, ±2 errori standard)", "",
          "| stopword | stem | k1 | b | J@1 | J@3 | Δ J@1 (2se) | Δ J@3 (2se) | rho |", "|---|---|---|---|---|---|---|---|---|"]
    for s in sorted(sens_rows, key=lambda s: (-s["j1"], -s["j3"])):
        L.append(f"| {s['stopwords']} | {s['stem']} | {s['k1']} | {s['b']} | {s['j1']:.3f} | {s['j3']:.3f} | "
                 f"{s['d_j1_vs_default']:+.3f} ({2*s['se_d_j1']:.3f}) | {s['d_j3_vs_default']:+.3f} ({2*s['se_d_j3']:.3f}) | "
                 f"{s['spearman_rho']:.2f} |")
    L += ["", "## Coppie candidate a quasi-duplicato (nessuna decisione: domanda 10 per i relatori)", "",
          "| A | B | Jaccard | TF-IDF | motivo |", "|---|---|---|---|---|"]
    L += [f"| {p['a']} | {p['b']} | {p['jaccard']:.3f} | {p['tfidf']:.3f} | {p['motivo']} |" for p in pairs]
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    _set_output(out)
    print(f"Scritto: {out}")
    print("\n".join(L[:12 + len(var_rows)]))


def _set_output(path) -> None:
    """Registro delle esecuzioni (voce 102): dichiara l'uscita, se lo script e' lanciato da riga di comando."""
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(path)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "experiments"))
    import run_log  # registro delle esecuzioni (voce 102): due righe in data/results/run_log.jsonl
    with run_log.logged(__file__):
        main()
