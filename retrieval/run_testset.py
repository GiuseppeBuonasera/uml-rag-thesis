"""
Retrieval sul test set De Bari con la configurazione CONGELATA (Passo 2, FASE 3, 2026-10-04). Nessun LLM.

Per ciascuno dei 20 esercizi: top-3 vicini tra i 59 candidati, score, score_norm, Jaccard dei nomi di classe con il
ground truth (SOLO descrittivo, mai nel ranking), fascia di score_norm del top-1 secondo i cut-off congelati in
retrieval/config_bm25.yaml. Random (N seed) e oracolo anche sul test set, solo descrittivi. Confronto delle
distribuzioni di score_norm e Jaccard con il leave-one-out del corpus.

Hard-fail prima di guardare il test set: config non congelata, lista di stopword diversa da quella congelata, test set
modificato rispetto al tag, cartella di output gia' esistente (il test set si guarda una volta sola: per rifare la run
serve un run-id nuovo e una motivazione in docs/decisions.md).

PROTOCOLLO (2026-10-10, voce 112): `--protocol loo` (default) = leave-one-out sui 20 esercizi De Bari: per ogni
esercizio i candidati sono i 59 del corpus piu' gli altri 19 esercizi De Bari (78), indice BM25 RIFITTATO su quel pool
(stessa configurazione congelata), random e oracolo sullo stesso pool; si conta quanti vicini vengono dal test set.
`--protocol fixed59` = protocollo originale (indice congelato sui 59 candidati del corpus, run testset_2026-10-04_stop2).
Le fasce di score_norm usano i cut-off congelati sul LOO del corpus (58 candidati): con 78 candidati sono descrittive.

Uso:
    python retrieval/run_testset.py [--run-id ID] [--seeds 20] [--protocol loo|fixed59]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_retrieval as ar
import corpus_loader as cl
from keyword_retriever import KeywordRetriever
from random_retriever import RandomRetriever
from text_preprocessing import STOPWORDS_PATH, PreprocessConfig

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "config_bm25.yaml"
TOP_K = 3


def load_frozen_config() -> dict:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    if not cfg.get("frozen"):
        raise SystemExit(f"{CONFIG_PATH.name}: configurazione non congelata")
    sha = hashlib.sha256(STOPWORDS_PATH.read_bytes()).hexdigest()
    if sha != cfg["preprocessing"]["stopwords_sha256"]:
        raise SystemExit("lista di stopword diversa da quella congelata")
    tag = cfg["provenienza"]["testset_tag"]
    if subprocess.run(["git", "diff", "--quiet", tag, "--", *ar.TESTSET_PATHS], cwd=ROOT).returncode != 0:
        raise SystemExit(f"il test set e' cambiato rispetto al tag {tag}")
    return cfg


def band(score_norm: float, tax: dict) -> str:
    if score_norm < tax["cutoff_basso_medio"]:
        return "basso"
    return "medio" if score_norm < tax["cutoff_medio_alto"] else "alto"


def describe(values: list[float]) -> dict:
    a = np.array(values)
    return {"n": len(a), "media": float(a.mean()), "min": float(a.min()), "q1": float(np.percentile(a, 25)),
            "mediana": float(np.median(a)), "q3": float(np.percentile(a, 75)), "max": float(a.max())}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--protocol", choices=("loo", "fixed59"), default="loo")
    args = ap.parse_args()

    cfg = load_frozen_config()
    run_id = args.run_id or f"testset_{dt.date.today().isoformat()}_{ar.git('rev-parse', '--short', 'HEAD')}"
    out = ar.RESULTS_DIR / run_id
    if out.exists():
        raise SystemExit(f"{out} esiste gia': il test set si guarda una volta sola (usa un run-id nuovo e motivalo)")

    candidates, queries = cl.load_all()
    qnames = {q["id"]: cl.class_names(q["diagram_apollon_json"]) for q in queries}
    names = {c["id"]: cl.class_names(c["diagram_apollon_json"]) for c in candidates} | qnames
    test_ids = set(qnames)
    r_cfg, p_cfg, tax = cfg["retriever"], cfg["preprocessing"], cfg["tassonomia_score_norm_top1"]
    frozen = {"stopwords": p_cfg["stopwords"], "stem": p_cfg["stemming"], "k1": r_cfg["k1"], "b": r_cfg["b"]}

    def make_bm25():
        return KeywordRetriever(k1=frozen["k1"], b=frozen["b"], preprocess=PreprocessConfig(frozen["stopwords"],
                                                                                           frozen["stem"]))

    def pool(q):
        """Candidati della query: voce 112 (LOO: corpus + gli altri 19) o protocollo originale (59 del corpus)."""
        if args.protocol == "fixed59":
            return candidates
        out_pool = candidates + [x for x in queries if x["id"] != q["id"]]
        assert q["id"] not in {c["id"] for c in out_pool} and len(out_pool) == len(candidates) + len(queries) - 1
        return out_pool

    fixed = make_bm25().fit(candidates) if args.protocol == "fixed59" else None
    rows = []
    for q in sorted(queries, key=lambda q: q["debari_number"]):
        cand = pool(q)
        top = (fixed or make_bm25().fit(cand)).retrieve(q["description"], TOP_K)
        jac = [cl.jaccard(qnames[q["id"]], names[r.id]) for r in top]
        oracle = sorted((cl.jaccard(qnames[q["id"]], names[c["id"]]) for c in cand), reverse=True)[:TOP_K]
        rows.append({"q": q, "top": top, "jac": jac, "oracle": oracle, "band": band(top[0].score_norm, tax),
                     "issues": [i["tipo"] if isinstance(i, dict) else i for i in q["known_issues"] or []],
                     "from_test": sum(r.id in test_ids for r in top)})

    def means(sel):
        return (statistics.mean(r["jac"][0] for r in sel), statistics.mean(statistics.mean(r["jac"]) for r in sel),
                statistics.mean(r["oracle"][0] for r in sel), statistics.mean(statistics.mean(r["oracle"]) for r in sel))

    def random_means(sel):
        per_seed = []
        for s in range(args.seeds):
            j1, j3 = [], []
            for r in sel:
                top = RandomRetriever(seed=s).fit(pool(r["q"])).retrieve(r["q"]["description"], TOP_K)
                js = [cl.jaccard(qnames[r["q"]["id"]], names[t.id]) for t in top]
                j1.append(js[0]); j3.append(statistics.mean(js))
            per_seed.append((statistics.mean(j1), statistics.mean(j3)))
        return ([x[0] for x in per_seed], [x[1] for x in per_seed])

    subsets = {"20 esercizi": rows, "19 (senza es. 6)": [r for r in rows if r["q"]["debari_number"] != 6]}
    summary_rows = []
    for label, sel in subsets.items():
        j1, j3, o1, o3 = means(sel)
        r1, r3 = random_means(sel)
        from scipy.stats import spearmanr
        rho, p = spearmanr([r["top"][0].score_norm for r in sel], [r["jac"][0] for r in sel])
        summary_rows.append({"insieme": label, "n": len(sel), "bm25_j1": j1, "bm25_j3": j3,
                             "random_j1_mean": statistics.mean(r1), "random_j1_sd": statistics.stdev(r1),
                             "random_j3_mean": statistics.mean(r3), "random_j3_sd": statistics.stdev(r3),
                             "oracolo_j1": o1, "oracolo_j3": o3, "spearman_rho": float(rho), "spearman_p": float(p)})

    # confronto con il LOO del corpus (stessa configurazione congelata)
    loo_rows = ar.loo(candidates, names, ar.bm25_factory(frozen))
    comparison = []
    for label, vals in (("score_norm top-1 LOO", [r["top"][0][2] for r in loo_rows]),
                        ("score_norm top-1 test set", [r["top"][0].score_norm for r in rows]),
                        ("Jaccard top-1 LOO", [r["top"][0][3] for r in loo_rows]),
                        ("Jaccard top-1 test set", [r["jac"][0] for r in rows])):
        comparison.append({"distribuzione": label, **describe(vals)})
    loo_bands = [band(r["top"][0][2], tax) for r in loo_rows]

    out.mkdir(parents=True)
    meta = ar.run_metadata({"config": str(CONFIG_PATH.relative_to(ROOT)), "frozen": frozen, "top_k": TOP_K,
                            "random_seeds": args.seeds, "tassonomia": tax, "protocol": args.protocol,
                            "candidati_per_query": len(pool(queries[0]))})
    (out / "config.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def write_csv(name, data, fields):
        with (out / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            for d in data:
                w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()})

    top_rows = [{"esercizio": r["q"]["id"], "rank": t.rank, "vicino": t.id, "score": t.score, "score_norm": t.score_norm,
                 "jaccard_gt": j, "fascia_top1": r["band"], "known_issues": ";".join(r["issues"]),
                 "vicino_dal_test_set": t.id in test_ids}
                for r in rows for t, j in zip(r["top"], r["jac"])]
    write_csv("testset_top3.csv", top_rows, list(top_rows[0]))
    write_csv("summary.csv", summary_rows, list(summary_rows[0]))
    write_csv("comparison_loo.csv", comparison, list(comparison[0]))

    n_from_test = sum(r["from_test"] for r in rows)
    proto = ("leave-one-out (voce 112): candidati = 59 del corpus + gli altri 19 esercizi De Bari (78), indice BM25 "
             f"rifittato per ogni esercizio; vicini dal test set nei top-{TOP_K}: {n_from_test}/{TOP_K * len(rows)}, "
             f"al rango 1: {sum(r['top'][0].id in test_ids for r in rows)}/{len(rows)}"
             if args.protocol == "loo" else "indice congelato sui 59 candidati del corpus (protocollo originale)")
    L = [f"# Retrieval BM25 sul test set De Bari ({run_id})", "",
         f"Configurazione congelata `{CONFIG_PATH.name}`: {frozen}. Commit `{meta['commit'][:7]}` (working tree "
         f"{'modificato' if meta['working_tree_dirty'] else 'pulito'}), test set `{meta['testset_tag']}` invariato: "
         f"{meta['testset_unchanged_since_tag']}. Jaccard con il ground truth SOLO descrittivo.", "",
         f"Protocollo: {proto}.", "",
         f"Fasce di score_norm del top-1 (cut-off congelati sul LOO): basso < {tax['cutoff_basso_medio']:.4f} <= medio < "
         f"{tax['cutoff_medio_alto']:.4f} <= alto.", "",
         "## Per esercizio", "",
         "| # | Esercizio | top-1 (score_norm, J) | top-2 (score_norm, J) | top-3 (score_norm, J) | fascia | oracolo J@1 | ED | note |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        cells = [f"{t.id} ({t.score_norm:.3f}, {j:.3f})" for t, j in zip(r["top"], r["jac"])]
        note = ", ".join(r["issues"] + (["senza analogo (fascia bassa)"] if r["band"] == "basso" else []))
        L.append(f"| {r['q']['debari_number']} | {r['q']['id']} | {' | '.join(cells)} | {r['band']} | {r['oracle'][0]:.3f} | "
                 f"{r['q']['debari_ed_avg']:.2f} | {note} |")
    L += ["", "## Riepiloghi (BM25, random su " + str(args.seeds) + " seed, oracolo)", "",
          "| Insieme | n | BM25 J@1 | BM25 J@3 | Random J@1 (sd) | Random J@3 (sd) | Oracolo J@1 | Oracolo J@3 | Spearman rho (p) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for s in summary_rows:
        L.append(f"| {s['insieme']} | {s['n']} | {s['bm25_j1']:.3f} | {s['bm25_j3']:.3f} | {s['random_j1_mean']:.3f} "
                 f"({s['random_j1_sd']:.3f}) | {s['random_j3_mean']:.3f} ({s['random_j3_sd']:.3f}) | {s['oracolo_j1']:.3f} | "
                 f"{s['oracolo_j3']:.3f} | {s['spearman_rho']:.2f} ({s['spearman_p']:.3f}) |")
    L += ["", "## Distribuzioni: test set vs leave-one-out del corpus", "",
          "| Distribuzione | n | media | min | q1 | mediana | q3 | max |", "|---|---|---|---|---|---|---|---|"]
    L += [f"| {c['distribuzione']} | {c['n']} | {c['media']:.3f} | {c['min']:.3f} | {c['q1']:.3f} | {c['mediana']:.3f} | "
          f"{c['q3']:.3f} | {c['max']:.3f} |" for c in comparison]
    tb = [r["band"] for r in rows]
    L += ["", f"Fasce — LOO: basso {loo_bands.count('basso')}, medio {loo_bands.count('medio')}, alto {loo_bands.count('alto')}; "
          f"test set: basso {tb.count('basso')}, medio {tb.count('medio')}, alto {tb.count('alto')}."]
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    _set_output(out)
    print(f"Scritto: {out}")
    print("\n".join(L))


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
