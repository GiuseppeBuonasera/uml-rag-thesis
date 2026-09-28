"""
Test mirato sul Bug 3 (lato del rombo invertito in aggregazione/composizione,
corretto il 2026-09-24, vedi docs/decisions.md), sulla convenzione generale
source/target per ciascun tipo di edge, e sulle normalizzazioni FASE 1
(2026-09-25): tipi, metodi, molteplicita', reificazione delle classi
associative. Non e' un test esaustivo del modulo — copre i casi esplicitamente
richiesti in revisione.

Uso:
    python corpus/test_apollon_convert.py
"""

from __future__ import annotations

import apollon_convert as ac
import apply_corrections as ac_corr


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
    # normalizzata da "0..n" (FASE 1, 2026-09-25) — il source_mult del parse resta
    # "0..n" (asserito sopra), solo l'output JSON e' normalizzato
    assert edge["data"]["sourceMultiplicity"] == "0..*"
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


def check_type_normalization() -> None:
    cases = [
        ("String", "string"), ("Int", "int"), ("Integer", "int"), ("integer", "int"),
        ("Double", "double"), ("Float", "float"), ("Boolean", "boolean"), ("bool", "boolean"),
        ("Bool", "boolean"), ("Date", "date"), ("Time", "time"), ("DateTime", "datetime"),
        ("Long", "long"),
    ]
    for src, expected in cases:
        got = ac.normalize_type_token(src)
        assert got == expected, f"normalize_type_token({src!r}) = {got!r}, atteso {expected!r}"
    # un tipo che e' il nome di una classe/enum del diagramma resta invariato
    assert ac.normalize_type_token("Suit") == "Suit"
    assert ac.normalize_type_token("RoomType") == "RoomType"
    print("  OK  tipi noti normalizzati (String->string, Int->int, ...); nomi di classe/enum invariati")


def check_multiplicity_normalization() -> None:
    cases = [("n", "*"), ("0..n", "0..*"), ("1..n", "1..*"), ("0..1", "0..1"), ("*", "*"), ("", "")]
    for src, expected in cases:
        got = ac.normalize_multiplicity(src)
        assert got == expected, f"normalize_multiplicity({src!r}) = {got!r}, atteso {expected!r}"
    print("  OK  molteplicita' normalizzate (n->*, 0..n->0..*, 1..n->1..*)")


def check_method_normalization() -> None:
    cases = [
        ("Double calculateCompenstationSum()", "+ calculateCompenstationSum() : double"),
        ("Compare compare(Card)", "+ compare(Card) : Compare"),  # Compare e' un enum del diagramma, invariato
        ("commandDriveSystem()", "+ commandDriveSystem()"),
        ("nextInspection() : Date", "+ nextInspection() : date"),
        ("+ AddPrestito(prestito:Prestito):void", "+ AddPrestito(prestito:Prestito) : void"),
        ("+ toString():String", "+ toString() : string"),
        ("- IncrementaOre()", "+ IncrementaOre()"),  # visibilita' originale non preservata, stessa scelta degli attributi
        ("SearchPrestiti(CodiceFiscale:string):List<Prestito>", "+ SearchPrestiti(CodiceFiscale:string) : List<Prestito>"),
    ]
    for src, expected in cases:
        got = ac.parse_method_signature(src)
        assert got == expected, f"parse_method_signature({src!r}) = {got!r}, atteso {expected!r}"
    print("  OK  metodi canonicalizzati ('Tipo nome()' e 'nome():Tipo' -> '+ nome(...) : tipo')")


def check_reification() -> None:
    """Test esplicitamente richiesto: AirTravel, FlightExecution '1' -- '0..*'
    Ticket '0..*' -- '1' Passenger, nessun edge diretto FlightExecution-Passenger."""
    classes = {
        "FlightExecution": ac.ParsedClass("FlightExecution", "class"),
        "Passenger": ac.ParsedClass("Passenger", "class"),
        "Ticket": ac.ParsedClass("Ticket", "class"),
    }
    relationships = [
        {
            "kind": "binary", "source": "FlightExecution", "source_mult": "0..*", "source_role": "",
            "op": "--", "target_mult": "0..*", "target_role": "", "target": "Passenger", "label": "",
            "raw": 'FlightExecution "0..*"--"0..*" Passenger',
        },
        {"kind": "assoc_class", "assoc": "Ticket", "a": "FlightExecution", "b": "Passenger", "raw": "(FlightExecution, Passenger) . Ticket"},
    ]
    reified, warnings = ac.reify_association_classes(relationships)
    assert not warnings, warnings
    assert all(r["kind"] == "binary" for r in reified)
    assert len(reified) == 2, reified

    diagram, build_warnings = ac.build_apollon_json("test-reify", classes, reified)
    assert not build_warnings, build_warnings
    name_by_id = {n["id"]: n["data"]["name"] for n in diagram["nodes"]}
    pairs = {
        (name_by_id[e["source"]], name_by_id[e["target"]]): (e["data"]["sourceMultiplicity"], e["data"]["targetMultiplicity"])
        for e in diagram["edges"]
    }
    assert pairs.get(("FlightExecution", "Ticket")) == ("1", "0..*"), pairs
    assert pairs.get(("Ticket", "Passenger")) == ("0..*", "1"), pairs
    assert ("FlightExecution", "Passenger") not in pairs and ("Passenger", "FlightExecution") not in pairs, (
        "l'edge diretto FlightExecution-Passenger doveva essere rimosso dalla reificazione"
    )

    problems = ac.round_trip_check("test-reify", classes, reified, diagram)
    assert not problems, problems
    print("  OK  AirTravel: FlightExecution(1)--Ticket(0..*), Ticket(0..*)--Passenger(1), nessun edge diretto")


def check_reification_missing_base() -> None:
    """Se l'associazione base A-B non esiste nel sorgente, le molteplicita' di C
    restano vuote e viene emesso un warning invece di inventarle."""
    relationships = [
        {"kind": "assoc_class", "assoc": "C", "a": "A", "b": "B", "raw": "(A, B) . C"},
    ]
    reified, warnings = ac.reify_association_classes(relationships)
    assert len(warnings) == 1 and "nessuna associazione base" in warnings[0], warnings
    by_pair = {(r["source"], r["target"]): (r["source_mult"], r["target_mult"]) for r in reified}
    assert by_pair[("A", "C")] == ("1", ""), by_pair
    assert by_pair[("C", "B")] == ("", "1"), by_pair
    print("  OK  classe associativa senza base A-B: molteplicita' di C vuote + warning, non inventate")


def check_edge_always_has_all_data_fields() -> None:
    edge, _ = make_diagram("--", source_mult="1", target_mult="*")
    for field in ("points", "label", "sourceMultiplicity", "targetMultiplicity", "sourceRole", "targetRole"):
        assert field in edge["data"], f"campo '{field}' mancante in edge.data"
    print("  OK  ogni edge ha sempre tutti i campi data (anche vuoti)")


def check_generalization_constraints() -> None:
    """Decisione utente su label_classification.md (STOP 1, 2026-09-25): un testo
    '{total; disjoint}' su una generalizzazione non e' un'etichetta, va estratto in
    un campo a se' e MAI lasciato nell'edge. Caso reale: EUScienceConnect,
    'TechnicalReport --|> Article : {total; disjoint}' (TechnicalReport e' il
    figlio/sottoclasse, Article il genitore/superclasse)."""
    relationships = [
        {
            "kind": "binary", "source": "TechnicalReport", "source_mult": "", "source_role": "",
            "op": "--|>", "target_mult": "", "target_role": "", "target": "Article",
            "label": "{total; disjoint}", "raw": "TechnicalReport --|> Article : {total; disjoint}",
        },
        {
            "kind": "binary", "source": "A", "source_mult": "1", "source_role": "",
            "op": "--", "target_mult": "*", "target_role": "", "target": "B",
            "label": "normalAssociation", "raw": "A -- B : normalAssociation",
        },
    ]
    constraints = ac.extract_generalization_constraints(relationships)
    assert len(constraints) == 1, constraints
    assert constraints[0]["vincoli"] == "{total; disjoint}", constraints
    assert constraints[0]["generalizzazione"] == "TechnicalReport extends Article", constraints

    classes = {
        "TechnicalReport": ac.ParsedClass("TechnicalReport", "class"),
        "Article": ac.ParsedClass("Article", "class"),
        "A": ac.ParsedClass("A", "class"),
        "B": ac.ParsedClass("B", "class"),
    }
    diagram, warnings = ac.build_apollon_json("test-constraint", classes, relationships)
    assert not warnings, warnings
    for e in diagram["edges"]:
        assert e["data"]["label"] != "{total; disjoint}", "il vincolo non deve MAI comparire nell'edge"
    print("  OK  '{total; disjoint}' estratto in constraints (TechnicalReport extends Article), mai nell'edge")


def check_label_classification_auto_association() -> None:
    """Decisione utente (2026-09-28): per un'auto-relazione (stessa classe a
    entrambi gli estremi, es. OnlineTutoringSystem TutoringSession->TutoringSession
    ': nextSession') il nome di classe non puo' disambiguare quale delle due
    occorrenze porta il ruolo — la classificazione usa percio' la POSIZIONE
    letterale nella riga PlantUML ('target' = estremo destro della riga sorgente),
    non un nome di classe. Verifica che apply_label_classification instradi il
    ruolo su targetRole (mai sourceRole) in questo caso, usando una classificazione
    sintetica (non il file reale) per isolare il test."""
    relationships = [
        {
            "kind": "binary", "source": "TutoringSession", "source_mult": "1", "source_role": "",
            "op": "-->", "target_mult": "0..1", "target_role": "", "target": "TutoringSession",
            "label": "nextSession", "raw": 'TutoringSession "1" --> "0..1" TutoringSession : nextSession',
        },
    ]
    classification = {
        ("test-auto-assoc", "TutoringSession", "-->", "TutoringSession", "nextSession"): {
            "tipo": "ruolo", "estremo": "target", "testo": "nextSession",
        },
    }
    missing = ac.apply_label_classification("test-auto-assoc", relationships, classification)
    assert not missing, missing
    r = relationships[0]
    assert r["label"] == "", r
    assert r["source_role"] == "", r
    assert r["target_role"] == "nextSession", r

    classes = {"TutoringSession": ac.ParsedClass("TutoringSession", "class")}
    diagram, build_warnings = ac.build_apollon_json("test-auto-assoc", classes, relationships)
    assert not build_warnings, build_warnings
    edge = diagram["edges"][0]
    assert edge["data"]["sourceRole"] == "", edge["data"]
    assert edge["data"]["targetRole"] == "nextSession", edge["data"]
    print('  OK  auto-relazione "nextSession": ruolo instradato su targetRole (mai sourceRole)')


def check_label_classification_ruolo_doppio_and_missing() -> None:
    """ruolo_doppio (caso unico TileOGame, Tile--Connection): entrambi gli estremi
    ricevono un ruolo distinto dalla stessa etichetta originale. Verifica anche il
    fallimento esplicito (lista 'missing' non vuota) per un'etichetta assente dalla
    classificazione — il convertitore deve rifiutarsi di indovinare."""
    relationships = [
        {
            "kind": "binary", "source": "Tile", "source_mult": "*", "source_role": "",
            "op": "--", "target_mult": "*", "target_role": "", "target": "Connection",
            "label": "connections/tiles", "raw": 'Tile "*" -- "*" Connection : connections/tiles',
        },
    ]
    classification = {
        ("test-doppio", "Tile", "--", "Connection", "connections/tiles"): {
            "tipo": "ruolo_doppio",
            "ruoli": [{"estremo": "source", "testo": "tiles"}, {"estremo": "target", "testo": "connections"}],
        },
    }
    missing = ac.apply_label_classification("test-doppio", relationships, classification)
    assert not missing, missing
    r = relationships[0]
    assert r["label"] == "", r
    assert r["source_role"] == "tiles", r
    assert r["target_role"] == "connections", r

    unclassified = [
        {
            "kind": "binary", "source": "X", "source_mult": "", "source_role": "",
            "op": "--", "target_mult": "", "target_role": "", "target": "Y",
            "label": "etichettaSconosciuta", "raw": "X -- Y : etichettaSconosciuta",
        },
    ]
    missing = ac.apply_label_classification("test-missing", unclassified, {})
    assert missing == [("test-missing", "X", "--", "Y", "etichettaSconosciuta")], missing
    print("  OK  ruolo_doppio instrada entrambi gli estremi; etichetta non classificata riportata come 'missing'")


def check_attribute_modifiers_const_default() -> None:
    """FASE 3 (2026-09-28): {static}/{abstract}/{frozen}/const e default '= x' non
    devono piu' essere persi in silenzio ne', peggio, far collassare nome/tipo
    (bug reale trovato in TileOGame: 'const int SpareConnectionPieces = 32' senza
    questa gestione produceva nome='32', tipo='const int SpareConnectionPieces =').
    Casi reali usati come test: Sober 'Int CustNr {frozen}', TileOGame
    '{static} const int SpareConnectionPieces = 32'."""
    name, typ, extra = ac.parse_attribute("Int CustNr {frozen}")
    assert (name, typ) == ("CustNr", "Int"), (name, typ)
    assert extra == {"default": None, "modifiers": ["frozen"]}, extra

    name, typ, extra = ac.parse_attribute("{static} const int SpareConnectionPieces = 32")
    assert (name, typ) == ("SpareConnectionPieces", "int"), (name, typ)
    assert extra["default"] == "32", extra
    assert extra["modifiers"] == ["static", "const"], extra

    # nessun modificatore/default: comportamento invariato rispetto a prima
    name, typ, extra = ac.parse_attribute("String Name")
    assert (name, typ) == ("Name", "String"), (name, typ)
    assert extra == {"default": None, "modifiers": []}, extra

    name, typ, extra = ac.parse_attribute("name : Type")
    assert (name, typ) == ("name", "Type"), (name, typ)

    # round-trip end-to-end: il default deve comparire nella stringa d'attributo
    # e sopravvivere a round_trip_check
    classes = {"Game": ac.ParsedClass("Game", "class")}
    classes["Game"].attributes = [("SpareConnectionPieces", "int")]
    classes["Game"].attribute_extras = [{"default": "32", "modifiers": ["static", "const"]}]
    diagram, build_warnings = ac.build_apollon_json("test-modifiers", classes, [])
    assert any("modificatori" in w for w in build_warnings), build_warnings
    attr_name = diagram["nodes"][0]["data"]["attributes"][0]["name"]
    assert attr_name == "+ SpareConnectionPieces : int = 32", attr_name
    problems = ac.round_trip_check("test-modifiers", classes, [], diagram)
    assert not problems, problems
    print("  OK  '{static} const int X = 32' e 'Int Y {frozen}' -> nome/tipo/default corretti, modificatori riportati (mai persi in silenzio)")


def check_array_notation_type() -> None:
    """FASE 3 (2026-09-28, caso reale HelpingHands 'ItemCategory[] neededCategories',
    dove ItemCategory e' un enum regolarmente dichiarato): il tipo base viene
    normalizzato, il suffisso '[]' preservato."""
    assert ac.normalize_type_token("String[]") == "string[]"
    assert ac.normalize_type_token("ItemCategory[]") == "ItemCategory[]"  # non e' un tipo noto, invariato
    assert ac.normalize_type_token("int") == "int"  # invariato, nessuna regressione senza '[]'
    print("  OK  notazione 'Tipo[]' per attributi multi-valore: tipo base normalizzato, '[]' preservato")


def check_corrections_rename_token() -> None:
    plantuml = 'class Order {\n    Sting Comment\n}\n'
    corrected, applied = ac_corr.apply_corrections(
        "test-corr", plantuml, [{"type": "rename_token", "from": "Sting", "to": "String", "reason": "refuso"}]
    )
    assert "String Comment" in corrected and "Sting" not in corrected, corrected
    assert len(applied) == 1 and "Sting" in applied[0] and "String" in applied[0], applied
    print("  OK  rename_token: 'Sting' -> 'String' in tutto il testo")


def check_corrections_remove_and_replace_line() -> None:
    plantuml = (
        'User "1" --> "*" Building : owner\n'
        'User "1" --> "*" Building : author\n'
    )
    corrected, applied = ac_corr.apply_corrections(
        "test-corr",
        plantuml,
        [{"type": "remove_line", "match": 'User "1" --> "*" Building : author', "reason": "duplicato"}],
    )
    assert corrected.strip() == 'User "1" --> "*" Building : owner', corrected
    assert len(applied) == 1

    plantuml2 = 'BookingInfo "0..5" -- "*" SpecialOffer : bestOffers\n'
    corrected2, applied2 = ac_corr.apply_corrections(
        "test-corr",
        plantuml2,
        [{
            "type": "replace_line",
            "match": 'BookingInfo "0..5" -- "*" SpecialOffer : bestOffers',
            "replacement": 'BookingInfo "*" -- "0..5" SpecialOffer : bestOffers',
            "reason": "lato sbagliato",
        }],
    )
    assert corrected2.strip() == 'BookingInfo "*" -- "0..5" SpecialOffer : bestOffers', corrected2
    print("  OK  remove_line rimuove solo la riga indicata; replace_line la sostituisce")


def check_corrections_fail_if_not_found() -> None:
    """Nessuna correzione deve applicarsi silenziosamente se il testo bersaglio non
    c'e' piu' (sorgente cambiato, o errore nella correzione stessa)."""
    for op in (
        {"type": "rename_token", "from": "NonEsiste", "to": "X", "reason": "r"},
        {"type": "remove_line", "match": "riga inesistente", "reason": "r"},
        {"type": "replace_line", "match": "riga inesistente", "replacement": "x", "reason": "r"},
    ):
        try:
            ac_corr.apply_corrections("test-corr", "class A {}\n", [op])
            assert False, f"doveva fallire per {op}"
        except ValueError:
            pass
    print("  OK  ogni correzione fallisce esplicitamente (ValueError) se il testo bersaglio non e' trovato")


def main() -> None:
    print("FASE 1 — normalizzazioni automatiche:")
    check_type_normalization()
    check_multiplicity_normalization()
    check_method_normalization()
    check_reification()
    check_reification_missing_base()
    check_edge_always_has_all_data_fields()
    check_generalization_constraints()
    print()
    print("Classificazione etichette (label_classification.json):")
    check_label_classification_auto_association()
    check_label_classification_ruolo_doppio_and_missing()
    print()
    print("FASE 3 — modificatori/const/default attributi e notazione Tipo[]:")
    check_attribute_modifiers_const_default()
    check_array_notation_type()
    print()
    print("FASE 3 — correzioni di contenuto (corpus/corrections/<id>.yaml):")
    check_corrections_rename_token()
    check_corrections_remove_and_replace_line()
    check_corrections_fail_if_not_found()
    print()
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
