"""
Test del retrieval (Passo 2, 2026-10-04), nello stile di corpus/test_apollon_convert.py: script, non pytest.

Uso:
    python retrieval/test_retrieval.py
"""

from __future__ import annotations

import hashlib
import math
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml

import analyze_dense as ad
import corpus_loader as cl
import relevance as rv
from base import RetrievalResult, Retriever, rank_results
from dense_retriever import DenseRetriever, cache_path
from hybrid_retriever import HybridRetriever, rrf_scores
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
    assert len(candidates) == 60, len(candidates)  # Cruise recuperato (voce 114)
    assert all(c["diagram_apollon_json"] is not None for c in candidates)
    assert "Cruise" in {c["id"] for c in candidates}
    assert len(queries) == 20 and all(cl.DEBARI_ID_RE.match(q["id"]) for q in queries)
    assert all(q["gt_counts"] and q["debari_ed_avg"] is not None for q in queries)
    for leak in ({"id": queries[0]["id"]}, {"id": "Shop", "split": "debari_test"}, {"id": "DB99_X"}):
        try:
            cl.check_disjoint(candidates + [leak], queries)
            assert False, f"doveva fallire: {leak}"
        except AssertionError as e:
            assert "test set" in str(e), e
    print("  OK  loader: 60 candidati convertiti (Cruise compreso, voce 114), 20 query; un id del test set tra i candidati -> hard-fail")


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



class FakeEncoder:
    """Embedding finto e deterministico (bag of words con hash sha256 su 64 dimensioni): nessun modello, nessun
    download. Conta i testi codificati per verificare la cache."""

    def __init__(self):
        self.calls = 0

    def __call__(self, texts):
        self.calls += len(texts)
        out = np.zeros((len(texts), 64), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in re.findall(r"[a-z]+", t.lower()):
                out[i, int(hashlib.sha256(w.encode()).hexdigest(), 16) % 64] += 1
        return out


def check_dense_fake(candidates) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        enc = FakeEncoder()
        d = DenseRetriever("org/model-x", "a" * 40, encoder=enc, cache_dir=Path(tmp)).fit(candidates)
        assert enc.calls == len(candidates)
        path = cache_path("org/model-x", "a" * 40, Path(tmp))
        assert path.exists() and path.name == "org__model-x@aaaaaaaaaaaa.npz", path
        misses = [c["id"] for c in candidates if d.retrieve(c["description"], 1)[0].id != c["id"]]
        assert not misses, misses
        q = candidates[7]["description"]
        a = d.retrieve(q, 10, exclude_ids={candidates[7]["id"]})
        assert candidates[7]["id"] not in {r.id for r in a} and [r.rank for r in a] == list(range(1, 11))
        assert all(-1 - 1e-6 <= r.score <= 1 + 1e-6 and r.score == r.score_norm for r in a)
        b = DenseRetriever("org/model-x", "a" * 40, encoder=FakeEncoder(), cache_dir=Path(tmp)).fit(
            list(reversed(candidates))).retrieve(q, 10, exclude_ids={candidates[7]["id"]})
        assert a == b, "stesso risultato con l'ordine dei record invertito"
        # cache: un secondo retriever con la stessa cache non ricalcola nulla; un testo nuovo si', solo quello
        enc2 = FakeEncoder()
        d2 = DenseRetriever("org/model-x", "a" * 40, encoder=enc2, cache_dir=Path(tmp)).fit(candidates)
        assert enc2.calls == 0 and d2.encoded_texts == 0
        d2.retrieve("a brand new query about zebras", 3)
        assert enc2.calls == 1
        # revisione diversa -> file di cache diverso, ricalcolo completo
        enc3 = FakeEncoder()
        DenseRetriever("org/model-x", "b" * 40, encoder=enc3, cache_dir=Path(tmp)).fit(candidates)
        assert enc3.calls == len(candidates) and len(list(Path(tmp).glob("*.npz"))) == 2
    # parita' di coseno: testi identici -> id crescente
    docs = [{"id": "z", "description": "library book loan"}, {"id": "m", "description": "library book loan"},
            {"id": "a", "description": "car engine wheel"}]
    tied = DenseRetriever("f", "0" * 40, encoder=FakeEncoder(), cache_dir=None).fit(docs).retrieve("library book", 3)
    assert [r.id for r in tied][:2] == ["m", "z"] and math.isclose(tied[0].score, tied[1].score), tied
    try:
        DenseRetriever("f", "0" * 40, encoder=lambda ts: np.zeros((len(ts), 4)), cache_dir=None).fit(docs)
        assert False, "embedding nullo doveva fallire"
    except ValueError:
        pass
    assert "sentence_transformers" not in sys.modules, "i test non devono caricare sentence-transformers"
    print("  OK  denso con embedding finti: auto-recupero al rank 1, exclude_ids, ordine dei record, cache per "
          "modello e revisione (nessun ricalcolo), parita' per id; sentence-transformers mai importato")


class _Fixed(Retriever):
    """Retriever finto con un ordinamento fisso."""

    def __init__(self, order):
        self.order = order

    def fit(self, records):
        return self

    def retrieve(self, query_text, k, exclude_ids=()):
        kept = [i for i in self.order if i not in set(exclude_ids)]
        return [RetrievalResult(i, r, 0.0, 0.0) for r, i in enumerate(kept[:k], start=1)]


def check_hybrid_rrf(candidates) -> None:
    s = rrf_scores([["a", "b", "c"], ["b", "c", "a"]])
    assert math.isclose(s["a"], 1 / 61 + 1 / 63) and math.isclose(s["b"], 1 / 62 + 1 / 61)
    docs = [{"id": i, "description": i} for i in "abc"]
    h = HybridRetriever(_Fixed(["a", "b", "c"]), _Fixed(["b", "c", "a"])).fit(docs)
    assert [r.id for r in h.retrieve("q", 3)] == ["b", "a", "c"]
    # esclusione PRIMA dei ranghi: senza b, a e' primo per entrambi -> score_norm 1
    top = HybridRetriever(_Fixed(["a", "b", "c"]), _Fixed(["b", "a", "c"])).fit(docs).retrieve("q", 3, exclude_ids={"b"})
    assert [r.id for r in top] == ["a", "c"] and math.isclose(top[0].score_norm, 1.0), top
    # parita' di RRF -> id crescente
    tie = HybridRetriever(_Fixed(["x", "y"]), _Fixed(["y", "x"])).fit([{"id": "x"}, {"id": "y"}])
    assert [r.id for r in tie.retrieve("q", 2)] == ["x", "y"]
    # ibrido reale (BM25 + denso finto) sul corpus: deterministico e senza la query esclusa
    q = candidates[3]
    hy = HybridRetriever(KeywordRetriever(), DenseRetriever("f", "0" * 40, encoder=FakeEncoder(), cache_dir=None))
    r1 = hy.fit(candidates).retrieve(q["description"], 3, exclude_ids={q["id"]})
    assert q["id"] not in {r.id for r in r1} and r1 == hy.retrieve(q["description"], 3, exclude_ids={q["id"]})
    print("  OK  ibrido RRF (c = 60): punteggi a mano, esclusione prima dei ranghi, score_norm, parita' per id")


def check_relevance_measures(candidates) -> None:
    assert rv.name_tokens("HTTPRequestLog2") == ["http", "request", "log", "2"]
    assert rv.name_tokens("ReservationSlot") == ["reservation", "slot"] and rv.name_tokens("Car_Park") == ["car", "park"]

    def diagram(names, edges=()):
        return {"nodes": [{"data": {"name": n}} for n in names], "edges": [{"type": t} for t in edges]}

    a = diagram(["InsurancePolicy", "Customer"], ["ClassBidirectional", "ClassInheritance"])
    b = diagram(["Policy", "Customers", "Agent", "Office"], ["ClassBidirectional"])
    ta, tb = rv.class_tokens(a), rv.class_tokens(b)
    assert len(ta) == 3 and len(ta & tb) == 2, (ta, tb)  # policy e customer(s) coincidono dopo lo stemming
    assert cl.jaccard(ta, tb) == 2 / 5
    # S = 1/2 * [(1 - 1/2 * (|0.5 - 1| + |0.5 - 0|)) + 2/4] = 1/2 * (0.5 + 0.5) = 0.5
    assert math.isclose(rv.structural_similarity(a, b), 0.5)
    assert math.isclose(rv.structural_similarity(a, a), 1.0)
    assert math.isclose(rv.structural_similarity(diagram(["A"]), diagram(["B"])), 1.0)  # nessuna relazione in entrambi
    rel = rv.Relevance(candidates)
    c0 = candidates[0]["id"]
    assert rel.measure(c0, c0) == {"J": 1.0, "Jt": 1.0, "S": 1.0}
    assert all(0 <= v <= 1 for c in candidates for v in rel.measure(c0, c["id"]).values())
    print("  OK  pertinenza: token CamelCase + Snowball (Jt), profilo strutturale (S) su esempi a mano, J/Jt/S in [0, 1]")


def check_dense_analysis_helpers() -> None:
    params = {"A": 100, "B": 30, "C": 20}
    assert ad.choose_model({"A": 0.30, "B": 0.295, "C": 0.25}, params, 0.01) == ("B", ["B", "A"])
    assert ad.choose_model({"A": 0.30, "B": 0.28, "C": 0.25}, params, 0.01) == ("A", ["A"])
    assert ad.choose_model({"A": 0.30, "B": 0.29, "C": 0.29}, params, 0.01) == ("C", ["C", "B", "A"])  # 0,01 incluso
    diff = np.array([0.1, -0.05, 0.2, 0.0, 0.05, 0.1])
    m, lo, hi = ad.bootstrap_ci(diff, 1000, 0, 0.95)
    assert (m, lo, hi) == ad.bootstrap_ci(diff, 1000, 0, 0.95) and lo <= m <= hi and math.isclose(m, diff.mean())
    assert np.allclose(ad.bootstrap_ci(np.full(5, 0.2), 1000, 0, 0.95)[1:], (0.2, 0.2))
    a = [{"query": "q1", "top": ["x", "y", "z"]}, {"query": "q2", "top": ["x", "w", "v"]}]
    b = [{"query": "q1", "top": ["x", "z", "k"]}, {"query": "q2", "top": ["u", "t", "s"]}]
    mean, same1, inter = ad.overlap(a, b)
    assert inter == [2, 0] and math.isclose(mean, 1 / 3) and same1 == 0.5
    h = ad.hubness(a, ["k", "s", "v", "w", "x", "y", "z"])
    assert h["distinti_rank1"] == 1 and h["max_rank1"] == 2 and h["max_top3_id"] == "x" and h["mai_top3"] == 2
    cfg = yaml.safe_load(ad.CONFIG_DENSE.read_text(encoding="utf-8"))
    assert len(cfg["modelli"]) == 3 and all(re.fullmatch(r"[0-9a-f]{40}", m["revisione"]) for m in cfg["modelli"])
    assert cfg["ibrido"]["costante"] == 60 and cfg["regola_di_scelta"]["pareggio_entro"] == 0.01
    assert cfg["regola_di_scelta"]["misura"] == "Jt@3" and cfg["embedding"]["device"] == "cpu"
    print("  OK  regola di scelta (pareggio entro 0,01 -> piu' piccolo), bootstrap riproducibile, sovrapposizione, "
          "hubness, config_dense.yaml")



def _diagram(names, edges=(), attrs=None):
    """Diagramma minimo: nodi con nomi (e attributi), relazioni (tipo, i, j, molt. sorgente, molt. destinazione)."""
    nodes = [{"id": f"n{i}", "data": {"name": n, "attributes": [{"name": a} for a in (attrs or {}).get(n, [])]}}
             for i, n in enumerate(names)]
    return {"nodes": nodes, "edges": [{"type": t, "source": f"n{a}", "target": f"n{b}",
                                       "data": {"sourceMultiplicity": sm, "targetMultiplicity": tm}}
                                      for t, a, b, sm, tm in edges]}


def check_structure_retrievers() -> None:
    """Varianti della voce 120 su dati finti (nessun download): struttura BM25 (+ sinonimi WordNet), struttura densa,
    RRF, MMR, costrutti, qualita', MiniLM a pezzi."""
    import structure_retrievers as sr
    recs = [
        {"id": "shop", "description": "a store sells goods", "diagram_apollon_json": _diagram(
            ["Customer", "PurchaseOrder"], [("ClassBidirectional", 0, 1, "1", "*")], {"Customer": ["+ name : string"]})},
        {"id": "zoo", "description": "animals live in cages", "diagram_apollon_json": _diagram(
            ["Animal", "Cage"], [("ClassBidirectional", 0, 1, "", "")], {"Animal": ["+ name"]})},
        {"id": "fleet", "description": "vehicles are owned by companies", "diagram_apollon_json": _diagram(
            ["Vehicle", "Car", "Truck"], [("ClassInheritance", 1, 0, "", ""), ("ClassInheritance", 2, 0, "", "")])},
        {"id": "plant", "description": "a factory is organised in departments", "diagram_apollon_json": _diagram(
            ["Factory", "Department"], [("ClassComposition", 1, 0, "*", "1")])},
    ]
    # 2: la traccia si confronta con i NOMI DI CLASSE dei candidati, non con la loro descrizione
    top = sr.StructureBM25().fit(recs).retrieve("Each customer places a purchase order", 2)
    assert top[0].id == "shop", top
    assert sr.StructureBM25().fit(recs).retrieve("customer order", 4, exclude_ids={"shop"})[0].id != "shop"
    # 2s: sinonimi WordNet del primo significato nominale (customer -> client)
    assert "client" in sr.wordnet_expand(["customer"]) and sr.wordnet_expand(["xyzzyq"]) == ["xyzzyq"]
    assert sr.StructureBM25(synonyms=True).fit(recs).retrieve("every client buys things", 1)[0].id == "shop"
    # 2d: testo dei nomi di classe e retrieval denso (embedding finti)
    assert sr.StructureDense.document(recs[0]) == "customer, purchase order"
    sd = sr.StructureDense(DenseRetriever("f", "0" * 40, encoder=FakeEncoder(), cache_dir=None)).fit(recs)
    assert sd.retrieve("purchase order of a customer", 1)[0].id == "shop"
    # RRF: due retriever fissi
    rrf = sr.RRF(_Fixed(["a", "b", "c"]), _Fixed(["b", "c", "a"])).fit([{"id": i} for i in "abc"])
    assert [r.id for r in rrf.retrieve("q", 3)] == ["b", "a", "c"]
    # 3: MMR; lam = 1 -> l'ordine della base; lam < 1 -> evita il quasi-doppione
    dup = [{"id": "a", "description": "x", "diagram_apollon_json": _diagram(["Customer", "Order"])},
           {"id": "b", "description": "x", "diagram_apollon_json": _diagram(["Customer", "Order", "Item"])},
           {"id": "c", "description": "x", "diagram_apollon_json": _diagram(["Plane", "Pilot"])},
           {"id": "d", "description": "x", "diagram_apollon_json": _diagram(["Ship", "Port"])}]

    class _Scored(_Fixed):
        def retrieve(self, query_text, k, exclude_ids=()):
            sc = {"a": 3.0, "b": 2.9, "c": 2.8, "d": 1.0}
            kept = [i for i in self.order if i not in set(exclude_ids)]
            return [RetrievalResult(i, r, sc[i], sc[i]) for r, i in enumerate(kept[:k], start=1)]

    # rilevanza min-max: a 1, b 0,95, c 0,9, d 0; al secondo passo b paga la somiglianza con a (Jt 2/3)
    assert [r.id for r in sr.MMR(_Scored(list("abcd")), lam=1.0).fit(dup).retrieve("q", 3)] == ["a", "b", "c"]
    assert [r.id for r in sr.MMR(_Scored(list("abcd"))).fit(dup).retrieve("q", 3)] == ["a", "c", "b"]
    assert "a" not in [r.id for r in sr.MMR(_Scored(list("abcd"))).fit(dup).retrieve("q", 3, exclude_ids={"a"})]
    # 4: segnali dei costrutti e spinta ai candidati che li mostrano
    assert sr.cued_constructs("A vehicle can be either a car or a truck.") == {"inheritance"}
    assert sr.cued_constructs("An order consists of several lines") == {"part"}
    assert sr.cued_constructs("Customers buy products.") == set()
    assert sr.has_constructs(recs[2]["diagram_apollon_json"]) == {"inheritance"}
    assert sr.has_constructs(recs[3]["diagram_apollon_json"]) == {"part"}
    base_order = ["shop", "zoo", "plant", "fleet"]
    cb = sr.ConstructBoost(_Fixed(base_order)).fit(recs)
    assert [r.id for r in cb.retrieve("Customers buy products.", 4)] == base_order  # nessun segnale: la base
    boosted = [r.id for r in cb.retrieve("A vehicle can be either a car or a truck.", 4)]
    assert boosted.index("fleet") < base_order.index("fleet"), boosted
    # 5: qualita' del GT e pesatura
    assert sr.gt_quality(recs[0]["diagram_apollon_json"]) == 1.0
    assert sr.gt_quality(recs[1]["diagram_apollon_json"]) == 0.0  # molteplicita' mancanti e attributo senza tipo
    qw = sr.QualityWeighted(_Scored(["a", "b", "c"]))
    qrec = [{"id": "a", "description": "x", "diagram_apollon_json": recs[1]["diagram_apollon_json"]},
            {"id": "b", "description": "x", "diagram_apollon_json": recs[0]["diagram_apollon_json"]},
            {"id": "c", "description": "x", "diagram_apollon_json": recs[0]["diagram_apollon_json"]}]
    assert [r.id for r in qw.fit(qrec).retrieve("q", 3)][0] == "b"
    # 6: MiniLM a pezzi (embedding finti: pezzi di parole), cache separata
    with tempfile.TemporaryDirectory() as tmp:
        ch = DenseRetriever("org/m", "a" * 40, encoder=FakeEncoder(), cache_dir=Path(tmp), chunk_tokens=3)
        assert ch.split_text("one two three four five") == ["one two three", "four five"]
        assert ch.cache.path.name == "org__m@aaaaaaaaaaaa_chunk3.npz"
        v = ch.encode(["one two three four five"])[0]
        a, b = FakeEncoder()(["one two three"])[0], FakeEncoder()(["four five"])[0]
        m = a / np.linalg.norm(a) + b / np.linalg.norm(b)
        assert np.allclose(v, m / np.linalg.norm(m), atol=1e-6)
    assert "sentence_transformers" not in sys.modules
    print("  OK  varianti della voce 120 su dati finti: struttura BM25 (+ sinonimi WordNet), struttura densa, RRF, "
          "MMR (diversita'), costrutti (segnali e spinta), qualita' del GT, MiniLM a pezzi con cache separata")


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
    check_dense_fake(candidates)
    check_hybrid_rrf(candidates)
    check_relevance_measures(candidates)
    check_dense_analysis_helpers()
    check_structure_retrievers()
    assert snapshot_corpus() == before, "il codice del retrieval ha scritto in corpus/"
    print(f"  OK  nessuna scrittura in corpus/ ({len(before)} file, sha256 invariati)")
    print("\nTutti i test del retrieval sono passati.")


if __name__ == "__main__":
    main()
