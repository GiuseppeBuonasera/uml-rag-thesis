"""
Test di evaluation/element_metrics.py (voce 136) su casi costruiti a mano, uno per regola. Script, non pytest; lo
richiama anche evaluation/test_metrics.py.

Uso:
    python evaluation/test_element_metrics.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evaluation import element_metrics as el  # noqa: E402


def D(classes: dict, edges: list = ()) -> dict:
    """classes: nome -> lista di attributi; edges: (tipo, src, tgt, mult_src, mult_tgt)."""
    nodes = [{"id": f"n_{name}", "data": {"name": name, "attributes": [{"name": f"+ {a} : string"} for a in attrs]}}
             for name, attrs in classes.items()]
    es = [{"source": f"n_{s}", "target": f"n_{t}", "type": ty, "data": {"sourceMultiplicity": ms, "targetMultiplicity": mt}}
          for ty, s, t, ms, mt in edges]
    return {"nodes": nodes, "edges": es}


def call(resp, gt, q="Q", r=0, level=4):
    return {"v": SimpleNamespace(level=level, diagram=resp), "gt": gt, "q": q, "r": r}


def check_class_matching() -> None:
    gt = D({"ReservationSlot": [], "Customer": [], "OrderItem": []})
    resp = D({"reservation_slot": [], "ReservationSlots": [], "Client": [], "ItemsOrder": []})
    ex = el.compare(resp, gt, "exact")["counts"]["classes"]
    rx = el.compare(resp, gt, "relaxed")["counts"]["classes"]
    # esatto: solo reservation_slot = ReservationSlot (normalizzazione); rilassato: + ItemsOrder = OrderItem (stessi
    # token stemmati); ReservationSlots resta FP (ReservationSlot gia' abbinata, uno a uno); Client != Customer
    assert (ex["tp"], ex["fp"], ex["fn"]) == (1, 3, 2), ex
    assert (rx["tp"], rx["fp"], rx["fn"]) == (2, 2, 1), rx
    # pareggio: due classi della risposta con gli stessi token di una sola del GT -> vince la prima per nome
    m = el.match_names([("a", "ItemsOrder"), ("b", "OrderItems")], [("g", "OrderItem")], "relaxed")
    assert m == {"a": "g"}, m  # stessi token {item, order}: vince "itemsorder", che precede "orderitems"
    print("  OK  classi: esatto (normalizzazione), rilassato (token stemmati), uno a uno, pareggi per nome; niente sinonimi")


def check_attributes() -> None:
    gt = D({"Order": ["DeliveryDate", "total"], "Customer": ["name"]})
    resp = D({"Order": ["deliveryDates", "Total", "notes"], "Buyer": ["name"]})
    ex = el.compare(resp, gt, "exact")["counts"]["attributes"]
    rx = el.compare(resp, gt, "relaxed")["counts"]["attributes"]
    # esatto: Total = total; rilassato: + deliveryDates = DeliveryDate; "name" di Buyer non conta (classe non abbinata)
    assert (ex["tp"], ex["fp"], ex["fn"]) == (1, 3, 2), ex
    assert (rx["tp"], rx["fp"], rx["fn"]) == (2, 2, 1), rx
    assert el.attribute_name({"name": "- id : int"}) == "id" and el.attribute_name("+ tags : string[]") == "tags"
    print("  OK  attributi: solo dentro classi abbinate, esatto e rilassato, visibilita' e tipo ignorati")


def check_relations_and_generalizations() -> None:
    gt = D({"Order": [], "Line": [], "Customer": [], "Person": []},
           [("ClassComposition", "Line", "Order", "*", "1"), ("ClassBidirectional", "Customer", "Order", "1", "*"),
            ("ClassInheritance", "Customer", "Person", "", "")])
    resp = D({"Order": [], "Line": [], "Customer": [], "Person": []},
             [("ClassComposition", "Order", "Line", "1", "*"),       # verso invertito: abbinata (senza verso), verso diverso
              ("ClassUnidirectional", "Order", "Customer", "0..*", "1"),  # tipo diverso ma stessa famiglia, mult uguali
              ("ClassInheritance", "Person", "Customer", "", "")])   # generalizzazione invertita
    res = el.compare(resp, gt, "exact")
    c, q = res["counts"], res["quality"]
    assert (c["relations"]["tp"], c["relations"]["fp"], c["relations"]["fn"]) == (2, 0, 0)
    assert (c["generalizations"]["tp"], c["generalizations"]["fp"], c["generalizations"]["fn"]) == (0, 1, 1)
    assert q["inv_generalizations"] == 1 and q["matched"] == 2 and q["same_type"] == 1 and q["same_family"] == 2
    # molteplicita' per estremo: composizione Line * / Order 1 contro Order 1 / Line * -> 2 uguali; associazione
    # Customer 1 / Order * contro Order 0..* (= *) / Customer 1 -> 2 uguali
    assert (q["ends"], q["ends_same"]) == (4, 4), q
    assert (q["oriented"], q["same_direction"]) == (1, 0), q
    # relazione con un estremo non abbinato: FP e FN
    resp2 = D({"Order": [], "Client": []}, [("ClassBidirectional", "Client", "Order", "1", "*")])
    gt2 = D({"Order": [], "Customer": []}, [("ClassBidirectional", "Customer", "Order", "1", "*")])
    c2 = el.compare(resp2, gt2, "relaxed")["counts"]["relations"]
    assert (c2["tp"], c2["fp"], c2["fn"]) == (0, 1, 1)
    print("  OK  relazioni strutturali senza verso (tipo, famiglia, molteplicita' per estremo, verso a parte); "
          "generalizzazioni con verso, invertite contate a parte")


def check_invalid_and_prf() -> None:
    gt = D({"A": ["x"], "B": []}, [("ClassBidirectional", "A", "B", "1", "*")])
    e = el.evaluate_call(call(None, gt, level=1))["relaxed"]["scores"]
    assert e["classes"] == {"P": None, "R": 0.0, "F1": 0.0} and e["relations"]["F1"] == 0.0
    assert e["generalizations"] == {"P": None, "R": None, "F1": None}  # nessuna generalizzazione da nessuna parte
    assert el.prf({"tp": 0, "fp": 2, "fn": 0}) == {"P": 0.0, "R": None, "F1": 0.0}  # GT senza elementi, risposta con
    p = el.prf({"tp": 2, "fp": 1, "fn": 1})
    assert abs(p["P"] - 2 / 3) < 1e-12 and abs(p["F1"] - 2 / 3) < 1e-12
    print("  OK  risposta non valida = diagramma vuoto (R 0, F1 0, P non definita); casi limite di P / R / F1")


def check_aggregation_and_determinism() -> None:
    gt = D({"A": [], "B": [], "C": [], "D": []})
    good, half = D({"A": [], "B": [], "C": [], "D": []}), D({"A": [], "B": []})
    calls = [call(good, gt, "Q1", 0), call(half, gt, "Q1", 1), call(None, gt, "Q2", 0, level=0), call(good, gt, "Q2", 1)]
    agg = el.aggregate(calls)["exact"]["classes"]
    # Q1: F1 1 e 2/3 -> 5/6; Q2: 0 e 1 -> 1/2; macro = (5/6 + 1/2) / 2 = 2/3
    assert abs(agg["macro"]["F1"] - 2 / 3) < 1e-12, agg
    # micro: TP 4+2+0+4 = 10, FP 0, FN 0+2+4+0 = 6 -> P 1, R 10/16
    assert agg["micro"]["P"] == 1.0 and abs(agg["micro"]["R"] - 10 / 16) < 1e-12
    assert agg["p_excluded"] == 1 and el.aggregate(calls)["invalid"] == 1
    # determinismo: stesso risultato con nodi e archi in ordine diverso
    gt = D({"Order": ["a", "b"], "Line": [], "Customer": []},
           [("ClassComposition", "Line", "Order", "*", "1"), ("ClassBidirectional", "Customer", "Order", "1", "*")])
    resp = D({"orders": ["A"], "Line": [], "Customer": [], "Lines": []},
             [("ClassBidirectional", "orders", "Line", "1", "*"), ("ClassBidirectional", "Customer", "orders", "1", "*")])
    ref = el.compare(resp, gt, "relaxed")
    rng = random.Random(7)
    for _ in range(20):
        r2 = {"nodes": rng.sample(resp["nodes"], len(resp["nodes"])), "edges": rng.sample(resp["edges"], len(resp["edges"]))}
        g2 = {"nodes": rng.sample(gt["nodes"], len(gt["nodes"])), "edges": rng.sample(gt["edges"], len(gt["edges"]))}
        assert el.compare(r2, g2, "relaxed") == ref
    print("  OK  medie macro per esercizio (prima le ripetizioni) e micro, precision esclusa per le non valide; "
          "risultato indipendente dall'ordine di nodi e archi")


def run_all() -> None:
    print("Metriche per elemento (voce 136):")
    check_class_matching()
    check_attributes()
    check_relations_and_generalizations()
    check_invalid_and_prf()
    check_aggregation_and_determinism()


if __name__ == "__main__":
    run_all()
    print("Tutti i test delle metriche per elemento sono passati.")
