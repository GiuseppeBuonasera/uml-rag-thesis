"""
Test mirato sul Bug 3 (lato del rombo invertito in aggregazione/composizione,
corretto il 2026-09-24, vedi docs/decisions.md) e sulla convenzione generale
source/target per ciascun tipo di edge. Non e' un test esaustivo del modulo — copre
i casi esplicitamente richiesti in revisione, uno per ciascuna forma di operatore
PlantUML per aggregazione/composizione.

Uso:
    python corpus/test_apollon_convert.py
"""

from __future__ import annotations

import apollon_convert as ac


def make_diagram(op: str, source_mult: str, target_mult: str):
    classes = {
        "Order": ac.ParsedClass("Order", "class"),
        "Line": ac.ParsedClass("Line", "class"),
    }
    relationships = [
        {
            "kind": "binary",
            "source": "Order",
            "source_mult": source_mult,
            "op": op,
            "target_mult": target_mult,
            "target": "Line",
            "label": "",
            "raw": f'Order "{source_mult}" {op} "{target_mult}" Line',
        }
    ]
    diagram, warnings = ac.build_apollon_json("test-order-line", classes, relationships)
    assert not warnings, f"warning inattesi per op={op!r}: {warnings}"
    assert len(diagram["edges"]) == 1
    return diagram["edges"][0], {n["id"]: n["data"]["name"] for n in diagram["nodes"]}


def check_container_is_target(op: str, edge_type: str) -> None:
    """'Order "1" op "*" Line' — Order e' il contenitore (a sinistra
    dell'operatore), Line la parte. Il contenitore deve finire come TARGET
    dell'edge, con la propria molteplicita' ("1") come targetMultiplicity, e la
    parte come SOURCE con la propria molteplicita' ("*") come sourceMultiplicity."""
    edge, name_by_id = make_diagram(op, source_mult="1", target_mult="*")
    source_name = name_by_id[edge["source"]]
    target_name = name_by_id[edge["target"]]
    assert edge["type"] == edge_type, f"op={op!r}: atteso type={edge_type!r}, trovato {edge['type']!r}"
    assert source_name == "Line", f"op={op!r}: atteso source='Line' (la parte), trovato {source_name!r}"
    assert target_name == "Order", f"op={op!r}: atteso target='Order' (il contenitore), trovato {target_name!r}"
    assert edge["data"]["sourceMultiplicity"] == "*", (
        f"op={op!r}: sourceMultiplicity attesa '*' (quella di Line/parte), "
        f"trovata {edge['data']['sourceMultiplicity']!r}"
    )
    assert edge["data"]["targetMultiplicity"] == "1", (
        f"op={op!r}: targetMultiplicity attesa '1' (quella di Order/contenitore), "
        f"trovata {edge['data']['targetMultiplicity']!r}"
    )
    print(f"  OK  Order \"1\" {op} \"*\" Line  ->  source=Line(*) target=Order(1)  [{edge_type}]")


def check_role_parsing() -> None:
    """Sintassi '\"molteplicita' ruolo\"' introdotta il 2026-09-25 per gli
    esercizi tradotti (es. '+responsabile' su un estremo in CourseManagement).
    Usa il parser reale (parse_plantuml), non un dizionario costruito a mano,
    per testare anche split_mult_role e il regex REL_RE insieme."""
    text = '@startuml\nclass Course {\n}\nclass InternalTeacher {\n}\nCourse "0..n" -- "1 responsible" InternalTeacher\n@enduml\n'
    classes, relationships, warnings, unsupported = ac.parse_plantuml(text)
    assert not unsupported, unsupported
    assert not warnings, warnings
    r = relationships[0]
    assert r["source_mult"] == "0..n" and r["source_role"] == "", r
    assert r["target_mult"] == "1" and r["target_role"] == "responsible", r

    diagram, build_warnings = ac.build_apollon_json("test-role", classes, relationships)
    assert not build_warnings, build_warnings
    edge = diagram["edges"][0]
    name_by_id = {n["id"]: n["data"]["name"] for n in diagram["nodes"]}
    assert name_by_id[edge["source"]] == "Course"
    assert name_by_id[edge["target"]] == "InternalTeacher"
    assert edge["data"]["sourceRole"] == "", edge["data"]
    assert edge["data"]["targetRole"] == "responsible", edge["data"]
    assert edge["data"]["sourceMultiplicity"] == "0..n"
    assert edge["data"]["targetMultiplicity"] == "1"

    # round_trip_check deve accorgersi se il ruolo finisse sull'estremo sbagliato
    problems = ac.round_trip_check("test-role", classes, relationships, diagram)
    assert not problems, problems

    # una molteplicita' senza ruolo (i 45 file originali) deve continuare a dare
    # source_role/target_role vuoti, non una regressione sui dati esistenti
    text_no_role = '@startuml\nclass A {\n}\nclass B {\n}\nA "0..1" -- "1..*" B\n@enduml\n'
    _, rels_no_role, _, _ = ac.parse_plantuml(text_no_role)
    assert rels_no_role[0]["source_role"] == "" and rels_no_role[0]["target_role"] == ""

    print('  OK  Course "0..n" -- "1 responsible" InternalTeacher  ->  targetRole="responsible"')


def main() -> None:
    print("Ruoli per estremo (sintassi '\"molteplicita' ruolo\"'):")
    check_role_parsing()
    print()
    print("Composizione - il contenitore (Order) deve finire come target, qualunque")
    print("forma dell'operatore usi il PlantUML sorgente per indicarlo:")
    # 'Order "1" *-- "*" Line': il simbolo '*' e' adiacente a Order (sinistra) ->
    # Order e' il contenitore, come richiesto esplicitamente in revisione.
    check_container_is_target("*--", "ClassComposition")
    check_container_is_target("*-", "ClassComposition")
    check_container_is_target("*-->", "ClassComposition")
    check_container_is_target("*->", "ClassComposition")

    print("\nAggregazione - stessa logica, simbolo 'o' invece di '*':")
    check_container_is_target("o--", "ClassAggregation")
    check_container_is_target("o-", "ClassAggregation")

    print("\nForma con il simbolo sulla destra ('Order \"1\" --o \"*\" Line'): qui e'")
    print("Line (a destra) ad avere il simbolo adiacente, quindi Line e' il")
    print("contenitore -> Line deve finire come target, Order come source.")
    edge, name_by_id = make_diagram("--o", source_mult="1", target_mult="*")
    source_name, target_name = name_by_id[edge["source"]], name_by_id[edge["target"]]
    assert source_name == "Order" and target_name == "Line", (
        f"'--o': atteso source=Order/target=Line (Line e' il contenitore in questa forma), "
        f"trovato source={source_name!r} target={target_name!r}"
    )
    assert edge["data"]["sourceMultiplicity"] == "1" and edge["data"]["targetMultiplicity"] == "*"
    print(f'  OK  Order "1" --o "*" Line  ->  source=Order(1) target=Line(*)  [ClassAggregation]')

    edge, name_by_id = make_diagram("--*", source_mult="1", target_mult="*")
    source_name, target_name = name_by_id[edge["source"]], name_by_id[edge["target"]]
    assert source_name == "Order" and target_name == "Line"
    assert edge["data"]["sourceMultiplicity"] == "1" and edge["data"]["targetMultiplicity"] == "*"
    print(f'  OK  Order "1" --* "*" Line  ->  source=Order(1) target=Line(*)  [ClassComposition]')

    print("\nTutti i test sono passati.")


if __name__ == "__main__":
    main()
