"""
Selezione DETERMINISTICA degli esercizi del pilota sulla temperatura (2026-10-06). Solo CORPUS, mai il test set.

Regola (dichiarata prima della run, docs/decisions.md voce 75):
1. candidati: i 59 record convertiti del corpus, esclusi quelli con known_issues (solo EatAtHome: due modellazioni
   alternative) e quelli FUORI SCALA rispetto al test set: ground truth in serializzazione compatta (senza
   interactive) piu' lungo del massimo del test set, con la stessa stima tiktoken cl100k_base (3.509 token; STOP 1
   del 2026-10-06: il pilota deve essere rappresentativo del test set). Del test set si legge solo la dimensione
   dei ground truth, mai un risultato;
2. fascia: score_norm del top-1 BM25 in leave-one-out (indice rifittato sugli altri 58 record, config congelata;
   identico a data/results/retrieval/loo_2026-10-04_stop1/loo_top3.csv), con i cut-off congelati di
   retrieval/config_bm25.yaml: basso < 0.2893 <= medio < 0.3473 <= alto;
3. dimensione: numero totale di elementi del diagramma di riferimento, dai conteggi apollon_counts (gli stessi di
   gt_counts del test set): classi + interfacce + enumerazioni + attributi + operazioni + valori di enumerazione +
   relazioni (cio' che il modello deve produrre);
4. per ogni fascia: il PIU' PICCOLO e il PIU' GRANDE; a parita' di dimensione, ordine alfabetico per id (il primo).

Uso:
    python experiments/select_pilot.py      # stampa la tabella e l'elenco da copiare in query_ids
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "corpus"))
from apollon_convert import apollon_counts  # noqa: E402  (sola lettura)
from prompt_builder import BM25_CONFIG, PromptBuilder, cl, serialize_diagram  # noqa: E402
from token_estimate import count_tokens  # noqa: E402

BANDS = ("basso", "medio", "alto")
SIZE_KEYS = ("classes", "interfaces", "enumerations", "attributes", "operations", "enum_values", "relations")


def band(score_norm: float, tax: dict) -> str:
    if score_norm < tax["cutoff_basso_medio"]:
        return "basso"
    return "medio" if score_norm < tax["cutoff_medio_alto"] else "alto"


def gt_tokens(diagram: dict) -> int:
    """Token stimati (cl100k_base) del ground truth compatto senza interactive, come nella dry run."""
    return count_tokens(serialize_diagram(diagram, "compact", True))


def testset_max_gt_tokens() -> int:
    return max(gt_tokens(q["diagram_apollon_json"]) for q in cl.load_queries())


def size(diagram: dict) -> int:
    counts = apollon_counts(diagram)
    return sum(counts[k] for k in SIZE_KEYS)


# Selezione STORICA (pilota 2026-10-06, insieme di sviluppo voce 92): si riproduce con il protocollo del Passo 2, cioe'
# i 59 candidati di allora (Cruise recuperato dopo, voce 114) e il LOO sugli altri 58 del corpus, non con il pool unico
# delle run nuove (voce 115).
HISTORICAL_EXCLUDED = frozenset({"Cruise"})


def historical_top1(builder: PromptBuilder, c: dict):
    from keyword_retriever import KeywordRetriever
    pool = [x for x in builder.candidates if x["id"] != c["id"] and x["id"] not in HISTORICAL_EXCLUDED]
    return KeywordRetriever(**builder._bm25_args).fit(pool).retrieve(c["description"], 1)[0]


def table(builder: PromptBuilder) -> list[dict]:
    """Una riga per candidato storico (59): fascia LOO, score_norm del top-1, dimensione, esclusione."""
    tax = yaml.safe_load(BM25_CONFIG.read_text(encoding="utf-8"))["tassonomia_score_norm_top1"]
    limit = testset_max_gt_tokens()
    rows = []
    for c in [x for x in builder.candidates if x["id"] not in HISTORICAL_EXCLUDED]:
        top1 = historical_top1(builder, c)
        tokens = gt_tokens(c["diagram_apollon_json"])
        rows.append({"id": c["id"], "top1": top1.id, "score_norm": top1.score_norm,
                     "band": band(top1.score_norm, tax), "size": size(c["diagram_apollon_json"]),
                     "gt_tokens": tokens, "known_issues": bool(c.get("known_issues")),
                     "out_of_scale": tokens > limit, "excluded": bool(c.get("known_issues")) or tokens > limit})
    counts = {b: sum(r["band"] == b for r in rows) for b in BANDS}
    if counts != tax["conteggi_loo"]:
        raise AssertionError(f"fasce LOO {counts} diverse da quelle congelate {tax['conteggi_loo']}")
    return rows


def select(builder: PromptBuilder) -> list[dict]:
    rows = [r for r in table(builder) if not r["excluded"]]
    chosen = []
    for b in BANDS:
        in_band = [r for r in rows if r["band"] == b]
        small = min(in_band, key=lambda r: (r["size"], r["id"]))
        large = min(in_band, key=lambda r: (-r["size"], r["id"]))
        chosen += [dict(small, role="piccolo"), dict(large, role="grande")]
    return chosen


def main() -> int:
    candidates, queries = cl.load_all()
    chosen = select(PromptBuilder(candidates, queries))
    print(f"soglia: ground truth compatto <= {testset_max_gt_tokens()} token (massimo del test set)\n")
    print("| fascia | ruolo | id | score_norm top-1 (LOO) | vicino top-1 | dimensione | GT compatto (token) |")
    print("|---|---|---|---|---|---|---|")
    for r in chosen:
        print(f"| {r['band']} | {r['role']} | {r['id']} | {r['score_norm']:.4f} | {r['top1']} | {r['size']} | "
              f"{r['gt_tokens']} |")
    print("\nquery_ids:", [r["id"] for r in chosen])
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102): due righe in data/results/run_log.jsonl
    with run_log.logged(__file__):
        sys.exit(main())
