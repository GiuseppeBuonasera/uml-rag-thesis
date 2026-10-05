"""
Test del retrieval (Passo 2, 2026-10-04), nello stile di corpus/test_apollon_convert.py: script, non pytest.

Uso:
    python retrieval/test_retrieval.py
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import corpus_loader as cl
from base import rank_results
from keyword_retriever import KeywordRetriever
from random_retriever import RandomRetriever
from text_preprocessing import PreprocessConfig, load_stopwords, tokenize

ROOT = Path(__file__).resolve().parent.parent


def snapshot_corpus() -> dict[str, str]:
    """sha256 di ogni file sotto corpus/ (esclusa la cache di Python): per verificare che nulla venga scritto."""
    out = {}
    for p in sorted((ROOT / "corpus").rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            out[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def check_loader(candidates, queries) -> None:
    assert len(candidates) == 59, len(candidates)
    assert all(c["diagram_apollon_json"] is not None for c in candidates)
    assert "Cruise" not in {c["id"] for c in candidates}
    assert len(queries) == 20 and all(cl.DEBARI_ID_RE.match(q["id"]) for q in queries)
    assert all(q["gt_counts"] and q["debari_ed_avg"] is not None for q in queries)
    for leak in ({"id": queries[0]["id"]}, {"id": "Shop", "split": "debari_test"}, {"id": "DB99_X"}):
        try:
            cl.check_disjoint(candidates + [leak], queries)
            assert False, f"doveva fallire: {leak}"
        except AssertionError as e:
            assert "test set" in str(e), e
    print("  OK  loader: 59 candidati convertiti (no Cruise), 20 query; un id del test set tra i candidati -> hard-fail")


def check_tokenize() -> None:
    assert tokenize("The photo_url, of Pets!", PreprocessConfig(False, False)) == ["the", "photo", "url", "of", "pets"]
    assert tokenize("The photo_url, of Pets!", PreprocessConfig(True, False)) == ["photo", "url", "pets"]
    assert tokenize("The photo_url, of Pets!", PreprocessConfig(True, True)) == ["photo", "url", "pet"]
    assert len(load_stopwords()) == 318 and "the" in load_stopwords()
    print("  OK  tokenizzazione: minuscole, '_' separa, stopword fisse (318), stemming Snowball")


def check_determinism_and_exclude(candidates) -> None:
    q = candidates[7]["description"]
    a = KeywordRetriever().fit(candidates).retrieve(q, 10)
    b = KeywordRetriever().fit(list(reversed(candidates))).retrieve(q, 10)
    assert a == b, "stessi input -> stessi output, indipendentemente dall'ordine dei record"
    excluded = {a[0].id, a[1].id}
    c = KeywordRetriever().fit(candidates).retrieve(q, 10, exclude_ids=excluded)
    assert not excluded & {r.id for r in c} and [r.rank for r in c] == list(range(1, 11))
    # tie-break per id: punteggi uguali -> id crescente
    tied = rank_results([("b", 1.0, 0.5), ("a", 1.0, 0.5), ("c", 2.0, 1.0)], 3)
    assert [r.id for r in tied] == ["c", "a", "b"]
    print("  OK  determinismo (anche con ordine dei record invertito), exclude_ids, tie-break per id")


def check_self_retrieval(candidates) -> None:
    retriever = KeywordRetriever().fit(candidates)
    misses = [(c["id"], retriever.retrieve(c["description"], 1)[0].id) for c in candidates
              if retriever.retrieve(c["description"], 1)[0].id != c["id"]]
    assert not misses, f"record che non recuperano se' stessi al rank 1: {misses}"
    print(f"  OK  ognuno dei {len(candidates)} candidati, non escluso, recupera se' stesso al rank 1")


def check_no_test_ids(candidates, queries) -> None:
    for retriever in (KeywordRetriever().fit(candidates), RandomRetriever(seed=3).fit(candidates)):
        for q in queries:
            got = {r.id for r in retriever.retrieve(q["description"], len(candidates))}
            assert len(got) == len(candidates) and not got & {x["id"] for x in queries}, q["id"]
    print("  OK  nessun id del test set restituito (BM25 e random, k = tutti i candidati, 20 query)")


def check_random(candidates) -> None:
    q = candidates[0]["description"]
    r1 = RandomRetriever(seed=5).fit(candidates).retrieve(q, 5)
    r2 = RandomRetriever(seed=5).fit(list(reversed(candidates))).retrieve(q, 5)
    r3 = RandomRetriever(seed=6).fit(candidates).retrieve(q, 5)
    assert r1 == r2 and [x.id for x in r1] != [x.id for x in r3]
    ex = {r1[0].id}
    assert not ex & {x.id for x in RandomRetriever(seed=5).fit(candidates).retrieve(q, 58, exclude_ids=ex)}
    print("  OK  random riproducibile con lo stesso seed, diverso con seed diverso, exclude_ids rispettato")


def check_score_norm_by_hand() -> None:
    """3 documenti di 2 token, k1=1.5, b=0.75, query 'apple' (1 token, df=1):
    idf = ln(3 - 1 + 0.5) - ln(1 + 0.5) = ln(2.5/1.5); avgdl = 2
    score(d1)  = idf * 1*2.5 / (1 + 1.5*(0.25 + 0.75*2/2)) = idf * 2.5/2.5   = idf
    self_score = idf * 1*2.5 / (1 + 1.5*(0.25 + 0.75*1/2)) = idf * 2.5/1.9375
    score_norm = 1.9375 / 2.5 = 0.775"""
    docs = [{"id": "d1", "description": "apple banana"}, {"id": "d2", "description": "cherry date"},
            {"id": "d3", "description": "egg fig"}]
    r = KeywordRetriever(1.5, 0.75, PreprocessConfig(False, False)).fit(docs).retrieve("apple", 1)[0]
    idf = math.log(2.5 / 1.5)
    assert r.id == "d1" and math.isclose(r.score, idf) and math.isclose(r.score_norm, 0.775), r
    # fuori indice: termine assente dal corpus -> self_score 0 -> score_norm 0
    assert KeywordRetriever(preprocess=PreprocessConfig(False, False)).fit(docs).retrieve("zebra", 1)[0].score_norm == 0.0
    print("  OK  score_norm su esempio calcolato a mano (0.775); query senza termini noti -> 0")


def check_frozen_config_and_bands() -> None:
    """config_bm25.yaml congelata e coerente (stopword con lo sha256 congelato, test set invariato dal tag);
    fasce: basso < c1 <= medio < c2 <= alto."""
    import run_testset as rt
    cfg = rt.load_frozen_config()
    tax = cfg["tassonomia_score_norm_top1"]
    c1, c2 = tax["cutoff_basso_medio"], tax["cutoff_medio_alto"]
    assert c1 < c2 and cfg["retriever"]["k1"] == 1.5 and cfg["retriever"]["b"] == 0.75
    assert [rt.band(x, tax) for x in (c1 - 1e-9, c1, c2 - 1e-9, c2)] == ["basso", "medio", "medio", "alto"]
    print("  OK  config BM25 congelata e verificata; fasce di score_norm con i cut-off congelati")


def main() -> None:
    before = snapshot_corpus()
    candidates, queries = cl.load_all()
    print("Retrieval (Passo 2):")
    check_loader(candidates, queries)
    check_tokenize()
    check_determinism_and_exclude(candidates)
    check_self_retrieval(candidates)
    check_no_test_ids(candidates, queries)
    check_random(candidates)
    check_score_norm_by_hand()
    check_frozen_config_and_bands()
    assert snapshot_corpus() == before, "il codice del retrieval ha scritto in corpus/"
    print(f"  OK  nessuna scrittura in corpus/ ({len(before)} file, sha256 invariati)")
    print("\nTutti i test del retrieval sono passati.")


if __name__ == "__main__":
    main()
