"""
Analisi DESCRITTIVA del retrieval sui 26 esercizi di sviluppo con il pool unico (2026-10-11, voce 129). Nessun LLM,
nessuna scelta: retriever e parametri sono chiusi. Gli esercizi di valutazione entrano SOLO come candidati: nessuna
misura e' calcolata con uno di loro come query.

Esempi: dal file congelato data/retrieval_frozen/retrievals_3b.jsonl (quelli che usera' il 3b; sha256 verificato dal
prompt builder), nell'ordine del retriever.
  1. Pertinenza J / Jt / S @1..3 (retrieval/relevance.py) per bm25, dense, hybrid, random (le 3 estrazioni del 3b, un
     seme per esercizio e ripetizione, voce 130: media; e 20 semi: media e deviazione standard) e oracolo (per misura),
     sulle 26 query. Sovrapposizione, hubness e provenienza degli esempi di random: ripetizione 0.
  2. Sovrapposizione dei top-3 tra retriever (media di |intersezione| / 3, stesso top-1).
  3. Hubness sulle 26 query: candidati distinti, mai recuperati (su 80), massimo e distribuzione delle frequenze.
  4. Esempi De Bari e esempi di valutazione tra i recuperati (contaminazione dichiarata nella voce 117).
  5. Pertinenza contro qualita': per ogni gruppo di generazioni GIA' esistenti di Gemma a k = 3 (run x configurazione x
     condizione, 20 esercizi di sviluppo, 2 ripetizioni), Spearman tra Jt@3 degli esempi EFFETTIVAMENTE usati (dal
     manifest) e R medio delle risposte (evaluation/metrics.py, 0 per le non valide), per formato; scatter PNG.
La stessa analisi sui 54 di valutazione e' PREVISTA dopo le run del Passo 3b (`--insieme valutazione`, che si rifiuta
senza `--dopo-3b`): si riporta qui solo il protocollo.

Uso:
    python retrieval/analyze_dev80.py [--run-id ID] [--seeds 20]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "retrieval"), str(ROOT / "generation"), str(ROOT / "experiments"), str(ROOT)]
import corpus_loader as cl  # noqa: E402
from analyze_dense import hubness, measures_at_k  # noqa: E402
from random_retriever import RandomRetriever  # noqa: E402
from relevance import Relevance  # noqa: E402

RESULTS_DIR = ROOT / "data" / "results" / "retrieval"
GEN = ROOT / "data" / "results" / "generation"
MODEL_ID = "google/gemma-4-12b-qat"
KS = (1, 2, 3)
MEASURES = Relevance.MEASURES
RETRIEVERS = ("bm25", "dense", "hybrid", "random")
RANDOM_REPETITIONS = 3  # estrazioni random del file congelato (voce 130)
# gruppi di generazioni esistenti (Gemma, k = 3, 20 esercizi di sviluppo): (run, configurazione)
RUNS = (("dev_k", "P-G"), ("dev_k", "C-G"), ("dev_instructions", "P-G"), ("dev_instructions", "C-G"),
        ("dev_retrievers", "P-G"), ("dev_retrievers", "C-G"), ("dev_v5base", "P-G"), ("dev_v5base", "C-G"),
        ("dev_v5", "P-G"), ("dev_v5", "C-G"), ("dev_cindent", "C-G"), ("dev_cschema", "C-G"), ("dev_cboth", "C-G"),
        ("dev_c5indent", "C-G"), ("dev_poolC", "P-G"), ("dev_poolC", "C-G"), ("dev_structP", "P-G"),
        ("dev_structC", "C-G"))
FORMAT = {"P-G": "plantuml", "C-G": "compact"}
X_MAX = 0.3  # Jt@3 degli esempi non supera 0,25 in nessun gruppo (controllato in scatter)
# run precedenti al pool unico (voce 115): candidati = gli altri 58 esercizi del corpus (Cruise non convertito); verificato:
# i loro esempi bm25 / dense / hybrid coincidono con il file congelato solo in 8-16 risposte su 40, quelli delle run
# successive in 40 su 40
HISTORICAL_58 = ("dev_k", "dev_instructions", "dev_retrievers")


def pool_label(run: str, cfg: dict) -> str:
    if cfg.get("pool"):
        return cfg["pool"]
    return "corpus58 (storico)" if run in HISTORICAL_58 else "all"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def frozen_rows(queries: list[dict]) -> tuple[dict[str, list[dict]], list[list[dict]], str]:
    """Dal file congelato (k = 3), nell'ordine delle query: retriever -> [{'query', 'top', 'scores'}] (random =
    ripetizione 0) e le righe random di tutte le ripetizioni (voce 130: seme random_seed(id, r))."""
    from prompt_builder import PromptBuilder, random_seed
    b = PromptBuilder(pool="all", retrieval_source="frozen")

    def rows(r, seed_of):
        return [{"query": q["id"], "top": [h.id for h in b.frozen[b.frozen_key(q["id"], r, 3, seed_of(q))]],
                 "scores": [h.score for h in b.frozen[b.frozen_key(q["id"], r, 3, seed_of(q))]]} for q in queries]

    out = {r: rows(r, lambda q: 0) for r in RETRIEVERS if r != "random"}
    reps = [rows("random", lambda q, i=i: random_seed(q["id"], i)) for i in range(RANDOM_REPETITIONS)]
    out["random"] = reps[0]
    return out, reps, b.frozen_sha256


def oracle(universe: list[dict], queries: list[dict], rel: Relevance) -> dict:
    out = {m: {} for m in MEASURES}
    for m in MEASURES:
        best = [sorted((rel.measure(q["id"], c["id"])[m] for c in universe if c["id"] != q["id"]), reverse=True)
                for q in queries]
        for k in KS:
            out[m][k] = statistics.mean(statistics.mean(b[:k]) for b in best)
    return out


def quality_groups(rel: Relevance, dev20: set[str]) -> list[dict]:
    """Per ogni (run, configurazione, condizione) di Gemma a k = 3: per esercizio Jt@3 degli esempi del manifest e R
    medio sulle ripetizioni (evaluation/metrics.core_metrics)."""
    import analyze_instructions as ai
    import run_experiment as rx
    from evaluation import metrics as em
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    groups = []
    for run, conf in RUNS:
        cfg = json.loads((GEN / f"{run}__{conf}" / "config.json").read_text(encoding="utf-8"))["config"]
        info = ai.load_run(GEN, run, conf, gt, MODEL_ID, k=3, config_version=rx.config_version(cfg))
        assert not info["excluded"], (run, conf, info["excluded"])
        for cond in cfg["conditions"]:
            calls = [c for c in info["calls"] if c["m"]["condition"] == cond]
            per_q = {}
            for c in calls:
                per_q.setdefault(c["q"], []).append(c)
            assert set(per_q) == dev20, (run, conf, cond)
            pts = []
            for q in sorted(per_q):
                ex = {tuple(c["m"]["example_ids"]) for c in per_q[q]}
                assert len(ex) == 1, (run, q, ex)  # stessi esempi in tutte le ripetizioni
                jt3 = statistics.mean(rel.measure(q, e)["Jt"] for e in ex.pop())
                pts.append({"query": q, "jt3": jt3, "R": em.core_metrics(per_q[q])["R"] or 0.0})
            groups.append({"run": run, "conf": conf, "format": FORMAT[conf], "condition": cond,
                           "pool": pool_label(run, cfg), "instructions": (cfg.get("prompt") or {}).get(
                               "instructions_version", "v4"), "points": pts})
    return groups


def spearman(xs, ys):
    from scipy.stats import spearmanr
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return float("nan"), float("nan")
    rho, p = spearmanr(xs, ys)
    return float(rho), float(p)


def scatter(groups: list[dict], fmt: str, path: Path) -> None:
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    gs = [g for g in groups if g["format"] == fmt]
    cols = 4
    rows = math.ceil(len(gs) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3.3 * rows), squeeze=False)
    for ax, g in zip(axes.flat, gs):
        x, y = [p["jt3"] for p in g["points"]], [p["R"] for p in g["points"]]
        assert max(x) < X_MAX, (g["run"], max(x))
        ax.scatter(x, y, s=18)
        rho, pv = spearman(x, y)
        ax.set_title(f"{g['run']} {g['condition']}\nrho {rho:+.2f} (p {pv:.2f})", fontsize=9)
        ax.set_xlim(-0.01, X_MAX)  # stessa scala in tutti i pannelli
        ax.set_ylim(-0.02, 1.02)
        ax.set_xlabel("Jt@3 degli esempi", fontsize=8)
        ax.set_ylabel("R medio", fontsize=8)
        ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(gs):]:
        ax.axis("off")
    fig.suptitle(f"Pertinenza degli esempi contro R, {'PlantUML' if fmt == 'plantuml' else 'JSON compatto'} "
                 "(Gemma 4 12B QAT, k = 3, 20 esercizi di sviluppo; solo descrittivo)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130, metadata={"Software": None})
    plt.close(fig)


def fmt3(x: float) -> str:
    return "—" if x != x else f"{x:.3f}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--insieme", choices=("sviluppo", "valutazione"), default="sviluppo")
    ap.add_argument("--dopo-3b", action="store_true", help="solo per --insieme valutazione, dopo le run del 3b")
    ap.add_argument("--out-dir", default=str(RESULTS_DIR))
    args = ap.parse_args(argv)
    if args.insieme == "valutazione":
        raise SystemExit("analisi PREVISTA sui 54 di valutazione: si esegue solo dopo le run del Passo 3b (voce 129); "
                         "da implementare allora sulle run del 3b" if not args.dopo_3b else
                         "insieme di valutazione: da implementare sulle run del Passo 3b (voce 129)")

    universe = cl.load_pool("all80")
    queries = sorted(cl.pool_queries("all80", universe), key=lambda q: q["id"])
    roles = __import__("paths").load_roles()
    debari = {i for i, r in roles.items() if r["source"] == "debari"}
    evaluation = {i for i, r in roles.items() if r["role"] == "valutazione"}
    rel = Relevance(universe)
    ids = sorted(c["id"] for c in universe)
    rows, random_reps, frozen_sha = frozen_rows(queries)

    # 1. pertinenza (random: media delle 3 estrazioni del 3b)
    rel_at = {r: measures_at_k(v, rel) for r, v in rows.items()}
    rep_at = [measures_at_k(v, rel) for v in random_reps]
    rel_at["random"] = {m: {k: statistics.mean(x[m][k] for x in rep_at) for k in KS} for m in MEASURES}
    rnd = []
    for s in range(args.seeds):
        rr = [{"query": q["id"], "top": [h.id for h in RandomRetriever(seed=s).fit(
            [c for c in universe if c["id"] != q["id"]]).retrieve(q["description"], 3)]} for q in queries]
        rnd.append(measures_at_k(rr, rel))
    from prompt_builder import random_seed
    for i, rep in enumerate(random_reps):  # il file congelato coincide con l'estrazione dal vivo (voce 130)
        assert [r["top"] for r in rep] == [
            [h.id for h in RandomRetriever(seed=random_seed(q["id"], i)).fit(
                [c for c in universe if c["id"] != q["id"]]).retrieve(q["description"], 3)] for q in queries], i
    rnd_mean = {m: {k: statistics.mean(x[m][k] for x in rnd) for k in KS} for m in MEASURES}
    rnd_sd = {m: {k: statistics.stdev(x[m][k] for x in rnd) for k in KS} for m in MEASURES}
    orc = oracle(universe, queries, rel)

    # 2. sovrapposizione
    names = list(RETRIEVERS)
    ovl = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            inter = [len(set(x["top"]) & set(y["top"])) for x, y in zip(rows[a], rows[b])]
            ovl.append({"a": a, "b": b, "media_intersezione_su_3": statistics.mean(n / 3 for n in inter),
                        "stesso_top1": sum(x["top"][0] == y["top"][0] for x, y in zip(rows[a], rows[b])),
                        "query_inters_0": inter.count(0), "query_inters_3": inter.count(3)})

    # 3-4. hubness, De Bari, valutazione
    hub, src = {}, {}
    for r, v in rows.items():
        h = hubness(v, ids)
        freq = Counter(Counter(d for x in v for d in x["top"]).values())
        h["distribuzione"] = {n: freq[n] for n in sorted(freq)}
        hub[r] = h
        slots = [d for x in v for d in x["top"]]
        src[r] = {"posti": len(slots), "debari": sum(d in debari for d in slots),
                  "query_con_debari": sum(any(d in debari for d in x["top"]) for x in v),
                  "valutazione": sum(d in evaluation for d in slots),
                  "query_con_valutazione": sum(any(d in evaluation for d in x["top"]) for x in v)}

    # 5. pertinenza contro qualita'
    # le 20 query dell'insieme di sviluppo delle run (voce 92; i 6 piloti non hanno generazioni a k = 3 su questo pool)
    dev20 = set(json.loads((GEN / "dev_v5__P-G" / "config.json").read_text(encoding="utf-8"))["config"]["query_ids"])
    assert len(dev20) == 20 and dev20 <= {q["id"] for q in queries}
    groups = quality_groups(rel, dev20)
    for g in groups:
        g["rho"], g["p"] = spearman([p["jt3"] for p in g["points"]], [p["R"] for p in g["points"]])

    run_id = args.run_id or f"dev80_{dt.date.today().isoformat()}_{git('rev-parse', '--short', 'HEAD')}"
    out = Path(args.out_dir) / run_id
    out.mkdir(parents=True, exist_ok=True)

    def write_csv(name, recs):
        with (out / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(recs[0]), lineterminator="\n")
            w.writeheader()
            w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in recs)

    write_csv("relevance.csv", [{"retriever": r, "misura": m, "k": k, "valore": rel_at[r][m][k]}
                                for r in rel_at for m in MEASURES for k in KS]
              + [{"retriever": f"random ({args.seeds} semi, media)", "misura": m, "k": k, "valore": rnd_mean[m][k]}
                 for m in MEASURES for k in KS]
              + [{"retriever": "oracolo", "misura": m, "k": k, "valore": orc[m][k]} for m in MEASURES for k in KS])
    write_csv("top3.csv", [{"retriever": r, "query": x["query"], "rank": i, "esempio": d, "score": s,
                            "debari": d in debari, "valutazione": d in evaluation, **rel.measure(x["query"], d)}
                           for r, v in rows.items() for x in v for i, (d, s) in enumerate(zip(x["top"], x["scores"]), 1)])
    write_csv("overlap.csv", ovl)
    write_csv("hubness.csv", [{"retriever": r, **{k: v for k, v in h.items() if k != "distribuzione"},
                               "distribuzione": json.dumps(h["distribuzione"])} for r, h in hub.items()])
    write_csv("quality_spearman.csv", [{"run": g["run"], "configurazione": g["conf"], "formato": g["format"],
                                        "condizione": g["condition"], "pool": g["pool"], "istruzioni": g["instructions"],
                                        "n": len(g["points"]), "rho": g["rho"], "p": g["p"],
                                        "jt3_medio": statistics.mean(p["jt3"] for p in g["points"]),
                                        "R_medio": statistics.mean(p["R"] for p in g["points"])} for g in groups])
    write_csv("quality_points.csv", [{"run": g["run"], "configurazione": g["conf"], "condizione": g["condition"],
                                      **p} for g in groups for p in g["points"]])
    for fmt in ("plantuml", "compact"):
        scatter(groups, fmt, out / f"scatter_{fmt}.png")
    meta = {"run_id": run_id, "voce": 129, "commit": git("rev-parse", "HEAD"),
            "working_tree_dirty": bool(git("status", "--porcelain")),
            "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "params": {"pool": "all80", "query": [q["id"] for q in queries], "random_seeds": args.seeds,
                       "file_congelato_sha256": frozen_sha, "gruppi_qualita": [f"{r}__{c}" for r, c in RUNS]}}
    (out / "config.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                                     newline="\n")

    # summary.md
    L = [f"# Retrieval sui 26 esercizi di sviluppo, pool unico ({run_id})", "",
         "Voci 129 e 130 di `docs/decisions.md`. SOLO DESCRITTIVO, nessuna scelta. Esempi dal file congelato "
         f"`data/retrieval_frozen/retrievals_3b.jsonl` (sha256 `{frozen_sha[:16]}…`); 80 esercizi, 79 candidati per "
         "query; misure solo sulle 26 query di sviluppo (gli esercizi di valutazione sono solo candidati).", "",
         __import__("provenance").provenance_line({c["id"]: c["diagram_apollon_json"] for c in universe}), "",
         "## 1. Pertinenza (media sulle 26 query della media dei primi k)", "",
         "| Retriever | J@1 | J@2 | J@3 | Jt@1 | Jt@2 | Jt@3 | S@1 | S@2 | S@3 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in RETRIEVERS:
        label = "random (le 3 estrazioni del 3b, media)" if r == "random" else r
        L.append(f"| {label} | " + " | ".join(fmt3(rel_at[r][m][k]) for m in MEASURES for k in KS) + " |")
    L.append(f"| random ({args.seeds} semi: media ± sd) | " + " | ".join(
        f"{rnd_mean[m][k]:.3f} ± {rnd_sd[m][k]:.3f}" for m in MEASURES for k in KS) + " |")
    L.append("| oracolo (massimo per misura) | " + " | ".join(fmt3(orc[m][k]) for m in MEASURES for k in KS) + " |")
    L += ["", "J e Jt sono misure lessicali sui nomi del GT e favoriscono BM25 per costruzione (voce 107): non decidono il "
          "confronto tra retriever, che si fa con le generazioni.", "",
          "## 2. Sovrapposizione dei top-3", "",
          "Random: ripetizione 0 (seme random_seed(id, 0), voce 130); lo stesso per le sezioni 3 e 4.", "",
          "| A | B | media \\|∩\\| / 3 | stesso top-1 | query con ∩ = 0 | query con ∩ = 3 |", "|---|---|---|---|---|---|"]
    L += [f"| {o['a']} | {o['b']} | {o['media_intersezione_su_3']:.3f} | {o['stesso_top1']}/26 | {o['query_inters_0']} | "
          f"{o['query_inters_3']} |" for o in ovl]
    L += ["", "## 3. Hubness (26 query, 78 posti per retriever, 80 candidati possibili)", "",
          "| Retriever | distinti nei top-3 | mai recuperati (su 80) | massimo nei top-3 | distribuzione (volte: n. candidati) |",
          "|---|---|---|---|---|"]
    L += [f"| {r} | {h['distinti_top3']} | {h['mai_top3']} | {h['max_top3']} ({h['max_top3_id']}) | "
          + ", ".join(f"{n}: {c}" for n, c in h["distribuzione"].items()) + " |" for r, h in hub.items()]
    L += ["", "## 4. Da dove vengono gli esempi (contaminazioni dichiarate nella voce 117)", "",
          "| Retriever | esempi De Bari (su 78) | query con almeno un De Bari | esempi di valutazione (su 78) | query con "
          "almeno uno di valutazione |", "|---|---|---|---|---|"]
    L += [f"| {r} | {s['debari']} | {s['query_con_debari']}/26 | {s['valutazione']} | {s['query_con_valutazione']}/26 |"
          for r, s in src.items()]
    L += ["", "## 5. Pertinenza degli esempi contro qualità delle risposte (generazioni esistenti)", "",
          "Gemma 4 12B QAT, k = 3, 20 esercizi di sviluppo × 2 ripetizioni per gruppo. x = Jt@3 degli esempi "
          "effettivamente usati (manifest), y = R medio per esercizio (0 per le risposte non valide). Spearman per "
          "gruppo (n = 20), SOLO descrittivo: i gruppi non sono indipendenti (stessi esercizi, spesso stessi esempi) e "
          "la difficoltà dell'esercizio confonde la relazione. Scatter: `scatter_plantuml.png`, `scatter_compact.png`.",
          "", "| Run | conf. | condizione | pool | istruzioni | Jt@3 medio | R medio | rho (p) |",
          "|---|---|---|---|---|---|---|---|"]
    for g in sorted(groups, key=lambda g: (g["format"], g["run"], g["condition"])):
        note = " (diagnostica)" if g["condition"] == "oracle_jt" else ""
        L.append(f"| {g['run']} | {g['conf']} | {g['condition']}{note} | {g['pool']} | {g['instructions']} | "
                 f"{statistics.mean(p['jt3'] for p in g['points']):.3f} | "
                 f"{statistics.mean(p['R'] for p in g['points']):.3f} | {fmt3(g['rho'])} ({fmt3(g['p'])}) |")
    for fmt in ("plantuml", "compact"):
        rhos = [g["rho"] for g in groups if g["format"] == fmt and g["condition"] != "oracle_jt" and g["rho"] == g["rho"]]
        L.append("")
        L.append(f"- {'PlantUML' if fmt == 'plantuml' else 'JSON compatto'}: rho per gruppo (senza oracle_jt) da "
                 f"{min(rhos):+.2f} a {max(rhos):+.2f}, mediana {statistics.median(rhos):+.2f}; positivi "
                 f"{sum(r > 0 for r in rhos)}/{len(rhos)}.")
    L += ["", "## PREVISTA: la stessa analisi sui 54 esercizi di valutazione (dopo il Passo 3b, non ora)", "",
          "- Query: i 54 esercizi di valutazione (34 del corpus + 20 De Bari), esempi dal file congelato (stesso sha256).",
          "- Sezioni 1-4 identiche (pertinenza, sovrapposizione, hubness, provenienza degli esempi) sulle 54 query;",
          "- sezione 5 sulle run del 3b, TRA esercizi: per formato e condizione (bm25 k = 2 e 3, dense, hybrid, random), "
          "Spearman tra Jt@3 degli esempi e R medio delle ripetizioni, un punto per esercizio (n = 54; a parte 34 del "
          "corpus e 20 De Bari, e 19 senza DB06_Flights); scatter come qui. Random: Jt@3 e R per ripetizione (ogni "
          "ripetizione ha la sua estrazione, voce 130), poi media.",
          "- sezione 5 bis, ENTRO esercizio (voce 130): per ogni esercizio e formato, scarti di Jt@3 e di R dalla media "
          "dell'esercizio tra le condizioni di retrieval (bm25 k = 3, dense, hybrid, random; bm25 k = 2 a parte), poi "
          "Spearman sugli scarti messi insieme (un punto per esercizio × condizione); si riportano n, gli esercizi in "
          "cui le condizioni recuperano esempi con Jt@3 diverso e lo scatter degli scarti.",
          "- Lettura: la correlazione TRA esercizi può riflettere la difficoltà dell'esercizio (esercizi con analoghi "
          "nel pool tendono ad avere GT più convenzionali e risposte migliori qualunque esempio si mostri) e non "
          "l'effetto del retrieval; quella ENTRO esercizio toglie questa componente, confrontando esempi diversi per "
          "lo stesso esercizio. Entrambe solo descrittive.",
          "- Si esegue SOLO dopo le run del 3b (`--insieme valutazione --dopo-3b`), senza cambiare nulla del retrieval."]
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    _set_output(out)
    print(f"scritto {out}")
    return 0


def _set_output(path) -> None:
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
