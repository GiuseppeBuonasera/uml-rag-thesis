"""
Retriever denso e ibrido: valutazione SOLO del retrieval in leave-one-out sul corpus (voce 107, FASE 3). Nessun LLM,
nessuna generazione; il test set NON viene letto (si caricano solo i candidati del corpus).

Per ogni query q (59 candidati): candidati = gli altri 58, stesse esclusioni del BM25 (variante base della run
loo_2026-10-04_stop1: solo q). BM25 congelato rifittato senza q (come in analyze_retrieval.py); i densi indicizzano
tutti i candidati una volta (l'embedding di un documento non dipende dagli altri) ed escludono q; ibrido = RRF (c = 60)
tra BM25 e ciascun denso sui 58 candidati.

Pertinenza (retrieval/relevance.py, nessun embedding): J, Jt, S a k = 1, 2, 3 (media dei primi k, poi media sulle
query). Riferimenti: casuale (20 seed, media e deviazione standard tra seed) e oracolo (per ciascuna misura).
Regola di scelta del denso (config_dense.yaml, fissata prima dei calcoli): Jt@3 massimo; entro 0,01 dal migliore
vince il modello piu' piccolo. Bootstrap al 95% (solo descrittivo). Sovrapposizione top-3 BM25 / denso, hubness, le 3
query piu' divergenti, testi troncati, tempi di calcolo degli embedding.

Esecuzione offline (HF_HUB_OFFLINE=1, impostato qui): i modelli vanno scaricati prima con
retrieval/download_dense_models.py.

Uso:
    python retrieval/analyze_dense.py [--run-id ID] [--seeds 20]
"""

from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # prima di qualunque import di huggingface_hub

import argparse
import csv
import datetime as dt
import json
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus_loader as cl
from dense_retriever import DenseRetriever
from hybrid_retriever import HybridRetriever
from keyword_retriever import KeywordRetriever
from random_retriever import RandomRetriever
from relevance import Relevance
from text_preprocessing import PreprocessConfig

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "data" / "results" / "retrieval"
CONFIG_DENSE = Path(__file__).resolve().parent / "config_dense.yaml"
CONFIG_BM25 = Path(__file__).resolve().parent / "config_bm25.yaml"
KS = (1, 2, 3)
TOP_K = 3
MEASURES = Relevance.MEASURES


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


# ---------------------------------------------------------------- funzioni pure (testate in test_retrieval.py)

def measures_at_k(rows: list[dict], rel: Relevance) -> dict[str, dict[int, float]]:
    """rows = [{'query': id, 'top': [id, ...]}] -> {misura: {k: media sulle query della media dei primi k}}."""
    out = {m: {} for m in MEASURES}
    for k in KS:
        per_q = [[rel.measure(r["query"], d) for d in r["top"][:k]] for r in rows]
        for m in MEASURES:
            out[m][k] = statistics.mean(statistics.mean(v[m] for v in q) for q in per_q)
    return out


def per_query(rows: list[dict], rel: Relevance, measure: str, k: int) -> np.ndarray:
    return np.array([statistics.mean(rel.measure(r["query"], d)[measure] for d in r["top"][:k]) for r in rows])


def choose_model(jt3: dict[str, float], params: dict[str, float], tie: float) -> tuple[str, list[str]]:
    """Regola 1f: Jt@3 massimo; i modelli entro `tie` dal migliore sono in parita' e vince il piu' piccolo."""
    best = max(jt3.values())
    tied = sorted((m for m, v in jt3.items() if best - v <= tie + 1e-12), key=lambda m: (params[m], m))
    return tied[0], tied


def bootstrap_ci(diff: np.ndarray, n_resamples: int, seed: int, level: float) -> tuple[float, float, float]:
    """Media della differenza appaiata e intervallo percentile (ricampionamento delle query con reinserimento)."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diff), size=(n_resamples, len(diff)))
    means = diff[idx].mean(axis=1)
    a = (1 - level) / 2 * 100
    return float(diff.mean()), float(np.percentile(means, a)), float(np.percentile(means, 100 - a))


def overlap(a: list[dict], b: list[dict]) -> tuple[float, float, list[int]]:
    """Media di |top3_a ∩ top3_b| / 3, quota di query con lo stesso top-1, intersezioni per query."""
    inter = [len(set(x["top"]) & set(y["top"])) for x, y in zip(a, b)]
    assert [x["query"] for x in a] == [y["query"] for y in b]
    same1 = sum(1 for x, y in zip(a, b) if x["top"][0] == y["top"][0])
    return statistics.mean(i / TOP_K for i in inter), same1 / len(a), inter


def hubness(rows: list[dict], ids: list[str]) -> dict:
    r1 = Counter(r["top"][0] for r in rows)
    r3 = Counter(d for r in rows for d in r["top"])
    top1, top3 = min(r1.items(), key=lambda t: (-t[1], t[0])), min(r3.items(), key=lambda t: (-t[1], t[0]))
    return {"distinti_rank1": len(r1), "distinti_top3": len(r3), "mai_top3": sum(1 for i in ids if r3[i] == 0),
            "max_rank1": top1[1], "max_rank1_id": top1[0], "max_top3": top3[1], "max_top3_id": top3[0]}


# ---------------------------------------------------------------- retrieval LOO

def bm25_factory():
    cfg = yaml.safe_load(CONFIG_BM25.read_text(encoding="utf-8"))
    assert cfg["frozen"] is True
    r, p = cfg["retriever"], cfg["preprocessing"]
    return lambda: KeywordRetriever(k1=r["k1"], b=r["b"], preprocess=PreprocessConfig(p["stopwords"], p["stemming"]))


def loo_rows(candidates, make_retriever, k=TOP_K) -> list[dict]:
    rows = []
    for q in candidates:
        pool = [c for c in candidates if c["id"] != q["id"]]
        top = make_retriever().fit(pool).retrieve(q["description"], k)
        rows.append({"query": q["id"], "top": [r.id for r in top], "scores": [r.score for r in top]})
    return rows


def dense_rows(candidates, dense: DenseRetriever, k=TOP_K) -> list[dict]:
    rows = []
    for q in candidates:
        top = dense.retrieve(q["description"], k, exclude_ids={q["id"]})
        rows.append({"query": q["id"], "top": [r.id for r in top], "scores": [r.score for r in top]})
    return rows


class _Fitted:
    """Retriever gia' indicizzato su tutto il corpus: fit() non ricalcola (gli embedding non dipendono dal pool)."""

    def __init__(self, inner):
        self.inner = inner

    def fit(self, records):
        return self

    def retrieve(self, query_text, k, exclude_ids=()):
        return self.inner.retrieve(query_text, k, exclude_ids)


def hybrid_rows(candidates, dense: DenseRetriever, make_bm25) -> list[dict]:
    rows = []
    for q in candidates:
        pool = [c for c in candidates if c["id"] != q["id"]]
        h = HybridRetriever(make_bm25(), _Fitted(dense))
        h.fit(pool)
        top = h.retrieve(q["description"], TOP_K, exclude_ids={q["id"]})
        rows.append({"query": q["id"], "top": [r.id for r in top], "scores": [r.score for r in top]})
    return rows


def oracle(candidates, rel: Relevance) -> dict[str, dict[int, float]]:
    out = {m: {} for m in MEASURES}
    for m in MEASURES:
        best = [sorted((rel.measure(q["id"], c["id"])[m] for c in candidates if c["id"] != q["id"]), reverse=True)
                for q in candidates]
        for k in KS:
            out[m][k] = statistics.mean(statistics.mean(b[:k]) for b in best)
    return out


# ---------------------------------------------------------------- main

def versions() -> dict:
    import huggingface_hub, sentence_transformers, tokenizers, torch, transformers  # noqa: E401
    return {"python": platform.python_version(), "sentence-transformers": sentence_transformers.__version__,
            "transformers": transformers.__version__, "torch": torch.__version__, "tokenizers": tokenizers.__version__,
            "huggingface_hub": huggingface_hub.__version__, "numpy": np.__version__,
            "torch_threads": torch.get_num_threads(), "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE")}


def snapshot_dir(name: str, revision: str) -> str:
    """Cartella della revisione fissata nella cache locale (download parziale voluto: niente ONNX ecc.)."""
    from huggingface_hub.constants import HF_HUB_CACHE
    path = Path(HF_HUB_CACHE) / f"models--{name.replace('/', '--')}" / "snapshots" / revision
    assert (path / "config.json").exists() and (path / "model.safetensors").exists(), \
        f"{name}@{revision} non in cache: eseguire retrieval/download_dense_models.py"
    return str(path)


def fmt(x: float) -> str:
    return f"{x:.3f}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--seeds", type=int, default=20)
    args = ap.parse_args()
    assert os.environ.get("HF_HUB_OFFLINE") == "1", "l'analisi gira offline (HF_HUB_OFFLINE=1)"

    cfg = yaml.safe_load(CONFIG_DENSE.read_text(encoding="utf-8"))
    rule, boot = cfg["regola_di_scelta"], cfg["regola_di_scelta"]["bootstrap"]
    candidates = cl.load_candidates()  # SOLO il corpus: il test set non si legge
    leaked = [c["id"] for c in candidates if cl.DEBARI_ID_RE.match(c["id"]) or c.get("split") == "debari_test"]
    assert not leaked, leaked
    ids = sorted(c["id"] for c in candidates)
    title = {c["id"]: c["name"] for c in candidates}
    rel = Relevance(candidates)
    run_id = args.run_id or f"dense_{dt.date.today().isoformat()}_{git('rev-parse', '--short', 'HEAD')}"
    out = RESULTS_DIR / run_id
    out.mkdir(parents=True, exist_ok=True)

    make_bm25 = bm25_factory()
    rows = {"BM25": loo_rows(candidates, make_bm25)}
    models, timing, trunc, snaps = {}, {}, {}, {}
    descriptions = [c["description"] for c in candidates]
    for m in cfg["modelli"]:
        name = m["nome"]
        snaps[name] = snapshot_dir(name, m["revisione"])
        d = DenseRetriever(name, m["revisione"], batch_size=cfg["embedding"]["batch_size"])
        t0 = time.perf_counter()
        _ = d.model
        t_load = time.perf_counter() - t0
        assert d.max_seq_length == m["limite_token"], (name, d.max_seq_length)
        t0 = time.perf_counter()
        fresh = d.encode(descriptions, use_cache=False)  # calcolo completo e cronometrato (aggiorna la cache)
        t_enc = time.perf_counter() - t0
        d.fit(candidates)
        assert np.allclose(d.matrix, fresh)
        counts = d.token_counts(descriptions)
        trunc[name] = {"troncati": sum(1 for n in counts if n > d.max_seq_length), "limite": d.max_seq_length,
                       "mediana_token": statistics.median(counts), "max_token": max(counts)}
        timing[name] = {"caricamento_s": round(t_load, 2), "embedding_59_s": round(t_enc, 2),
                        "ms_per_testo": round(1000 * t_enc / len(descriptions), 1), "dimensione": int(fresh.shape[1])}
        models[name] = d
        rows[name] = dense_rows(candidates, d)
        print(f"{name}: {timing[name]} troncati {trunc[name]['troncati']}", flush=True)

    # --- regola di scelta (Jt@3, voce 107 1f) ---
    params = {m["nome"]: m["parametri_milioni"] for m in cfg["modelli"]}
    rel_at = {r: measures_at_k(v, rel) for r, v in rows.items()}
    jt3 = {m: rel_at[m]["Jt"][3] for m in params}
    chosen, tied = choose_model(jt3, params, rule["pareggio_entro"])
    ranked = sorted(params, key=lambda m: (-jt3[m], params[m]))
    jt3_q = {r: per_query(v, rel, "Jt", 3) for r, v in rows.items()}
    ci_top2 = bootstrap_ci(jt3_q[ranked[0]] - jt3_q[ranked[1]], boot["ricampionamenti"], boot["seme"], boot["livello"])
    ci_bm25 = bootstrap_ci(jt3_q[chosen] - jt3_q["BM25"], boot["ricampionamenti"], boot["seme"], boot["livello"])

    # --- ibrido: ufficiale con il denso scelto, descrittivo con gli altri ---
    for name, d in models.items():
        rows[f"Ibrido RRF (BM25 + {name.split('/')[-1]})"] = hybrid_rows(candidates, d, make_bm25)
    hybrid_official = f"Ibrido RRF (BM25 + {chosen.split('/')[-1]})"
    rel_at.update({r: measures_at_k(v, rel) for r, v in rows.items() if r not in rel_at})

    # --- casuale e oracolo ---
    rnd = [measures_at_k(loo_rows(candidates, lambda s=s: RandomRetriever(seed=s)), rel) for s in range(args.seeds)]
    rnd_mean = {m: {k: statistics.mean(x[m][k] for x in rnd) for k in KS} for m in MEASURES}
    rnd_sd = {m: {k: statistics.stdev(x[m][k] for x in rnd) for k in KS} for m in MEASURES}
    orc = oracle(candidates, rel)

    # --- sovrapposizione, hubness, query divergenti ---
    ovl = {name: overlap(rows["BM25"], rows[name]) for name in models}
    hub = {r: hubness(v, ids) for r, v in rows.items()}
    inter = ovl[chosen][2]
    divergent = sorted(range(len(candidates)), key=lambda i: (inter[i], rows["BM25"][i]["query"]))[:3]

    # --- file ---
    meta = {"run_id": run_id, "commit": git("rev-parse", "HEAD"), "working_tree_dirty": bool(git("status", "--porcelain")),
            "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "versions": versions(), "config_dense": cfg, "snapshot": snaps, "tempi": timing, "troncamenti": trunc,
            "random_seeds": args.seeds, "loo": "58 candidati per query (esclusa solo la query); BM25 rifittato senza q",
            "esito_regola": {"Jt@3": jt3, "scelto": chosen, "in_parita": tied,
                             "bootstrap_top2": {"modelli": ranked[:2], "media": ci_top2[0], "ic95": ci_top2[1:]},
                             "bootstrap_scelto_vs_bm25": {"media": ci_bm25[0], "ic95": ci_bm25[1:]}},
            "test_set_letto": False}
    (out / "config.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def write_csv(fname, recs):
        with (out / fname).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(recs[0]), lineterminator="\n")
            w.writeheader()
            w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in recs)

    write_csv("relevance.csv", [{"retriever": r, "misura": m, "k": k, "valore": rel_at[r][m][k]}
                                for r in rel_at for m in MEASURES for k in KS]
              + [{"retriever": f"casuale ({args.seeds} seed, media)", "misura": m, "k": k, "valore": rnd_mean[m][k]}
                 for m in MEASURES for k in KS]
              + [{"retriever": "oracolo", "misura": m, "k": k, "valore": orc[m][k]} for m in MEASURES for k in KS])
    write_csv("top3.csv", [{"retriever": r, "query": row["query"], "rank": i, "vicino": d, "score": s,
                            **{m: v for m, v in rel.measure(row["query"], d).items()}}
                           for r, v in rows.items() for row in v
                           for i, (d, s) in enumerate(zip(row["top"], row["scores"]), start=1)])
    write_csv("hubness.csv", [{"retriever": r, **h} for r, h in hub.items()])

    # --- summary.md ---
    short = {n: n.split("/")[-1] for n in params}
    order = ["BM25", *params, hybrid_official]
    L = [f"# Retriever denso e ibrido — leave-one-out sul corpus ({run_id})", "",
         "Voce 107 di `docs/decisions.md`. SOLO retrieval, nessuna generazione; test set NON letto. "
         f"{len(candidates)} query, 58 candidati ciascuna (esclusa solo la query, come BM25). Generato da "
         "`retrieval/analyze_dense.py`.", "",
         _provenance_line(candidates), "",
         "**Le misure servono SOLO a scegliere il modello denso.** J e Jt sono lessicali sui nomi del GT e favoriscono "
         "BM25 per costruzione: il confronto BM25 / denso / ibrido si decide con le generazioni sull'insieme di "
         "sviluppo (voce 107, precisazione 1).", "",
         "## Pertinenza (media sulle 59 query della media dei primi k)", "",
         "| Retriever | J@1 | J@2 | J@3 | Jt@1 | Jt@2 | Jt@3 | S@1 | S@2 | S@3 |", "|---|---|---|---|---|---|---|---|---|---|"]
    L.append(f"| casuale ({args.seeds} seed: media ± sd) | "
             + " | ".join(f"{rnd_mean[m][k]:.3f} ± {rnd_sd[m][k]:.3f}" for m in MEASURES for k in KS) + " |")
    for r in order:
        label = f"**{short.get(r, r)}** (scelto)" if r == chosen else short.get(r, r)
        L.append(f"| {label} | " + " | ".join(fmt(rel_at[r][m][k]) for m in MEASURES for k in KS) + " |")
    L.append("| oracolo (massimo per misura) | " + " | ".join(fmt(orc[m][k]) for m in MEASURES for k in KS) + " |")
    L += ["", "Ibrido RRF con gli altri densi (solo descrittivo):", "",
          "| Retriever | J@1 | J@3 | Jt@1 | Jt@3 | S@1 | S@3 |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r} | " + " | ".join(fmt(rel_at[r][m][k]) for m in MEASURES for k in (1, 3)) + " |"
          for r in rows if r.startswith("Ibrido") and r != hybrid_official]
    L += ["", "## Regola di scelta del modello denso (fissata prima dei calcoli)", "",
          f"Jt@3 massimo; modelli entro {rule['pareggio_entro']} dal migliore in parità, vince il più piccolo.", "",
          "| Modello | parametri (M) | Jt@3 | distanza dal migliore |", "|---|---|---|---|"]
    L += [f"| {short[m]} | {params[m]} | {jt3[m]:.4f} | {max(jt3.values()) - jt3[m]:.4f} |" for m in ranked]
    L += ["", f"- In parità: {', '.join(short[m] for m in tied)}. **Scelto: `{chosen}`** "
          f"(revisione `{next(x['revisione'] for x in cfg['modelli'] if x['nome'] == chosen)}`).",
          f"- Bootstrap al {boot['livello']:.0%} ({boot['ricampionamenti']} ricampionamenti delle query, seme "
          f"{boot['seme']}; solo descrittivo, la regola non cambia):",
          f"  - Jt@3 {short[ranked[0]]} − {short[ranked[1]]}: {ci_top2[0]:+.4f} [{ci_top2[1]:+.4f}, {ci_top2[2]:+.4f}]",
          f"  - Jt@3 {short[chosen]} − BM25: {ci_bm25[0]:+.4f} [{ci_bm25[1]:+.4f}, {ci_bm25[2]:+.4f}]", "",
          "## Sovrapposizione dei top-3 tra BM25 e ciascun denso", "",
          "| Denso | media di \\|∩\\| / 3 | stesso top-1 | query con ∩ = 0 / 1 / 2 / 3 |", "|---|---|---|---|"]
    for name in params:
        c = Counter(ovl[name][2])
        L.append(f"| {short[name]} | {ovl[name][0]:.3f} | {ovl[name][1]:.0%} ({round(ovl[name][1] * len(candidates))}"
                 f"/{len(candidates)}) | {c[0]} / {c[1]} / {c[2]} / {c[3]} |")
    L += ["", "## Hubness", "",
          "| Retriever | distinti al rango 1 | distinti nei top-3 | mai nei top-3 | max al rango 1 | max nei top-3 |",
          "|---|---|---|---|---|---|"]
    for r in order:
        h = hub[r]
        L.append(f"| {short.get(r, r)} | {h['distinti_rank1']} | {h['distinti_top3']} | {h['mai_top3']} | "
                 f"{h['max_rank1']} ({h['max_rank1_id']}) | {h['max_top3']} ({h['max_top3_id']}) |")
    L += ["", f"Atteso con distribuzione uniforme nei top-3: {3 * len(candidates) / len(candidates):.1f} per candidato.",
          "", f"## Le 3 query più divergenti tra BM25 e {short[chosen]}", "",
          "Ordinate per intersezione dei top-3 crescente, poi per id. Titoli = campo `name` del corpus; tra "
          "parentesi Jt con la query.", ""]
    by_q = {r: {row["query"]: row["top"] for row in v} for r, v in rows.items()}
    for i in divergent:
        q = candidates[i]["id"]
        L.append(f"- **{q}** ({title[q]}), ∩ = {inter[i]}")
        for r in ("BM25", chosen, hybrid_official):
            L.append(f"  - {short.get(r, r)}: " + "; ".join(
                f"{d} ({title[d]}, Jt {rel.measure(q, d)['Jt']:.2f})" for d in by_q[r][q]))
    L += ["", "## Modelli, troncamenti, tempi (CPU)", "",
          "| Modello | revisione | limite | testi troncati | mediana / max token | dim. | caricamento | embedding 59 testi |",
          "|---|---|---|---|---|---|---|---|"]
    for m in cfg["modelli"]:
        n, t, tr = m["nome"], timing[m["nome"]], trunc[m["nome"]]
        L.append(f"| {n} | `{m['revisione'][:12]}` | {tr['limite']} | {tr['troncati']}/{len(candidates)} | "
                 f"{tr['mediana_token']:.0f} / {tr['max_token']} | {t['dimensione']} | {t['caricamento_s']} s | "
                 f"{t['embedding_59_s']} s ({t['ms_per_testo']} ms/testo) |")
    v = meta["versions"]
    L += ["", "Versioni: " + ", ".join(f"{k} {val}" for k, val in v.items()) + ".", ""]
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    _set_output(out)
    print(f"Scritto: {out}")
    print("\n".join(L))


def _provenance_line(candidates) -> str:
    sys.path.insert(0, str(ROOT / "experiments"))
    import provenance
    return provenance.provenance_line({c["id"]: c["diagram_apollon_json"] for c in candidates})


def _set_output(path) -> None:
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows (cp1252): il sommario contiene caratteri come "−"
    sys.path.insert(0, str(ROOT / "experiments"))
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        main()
