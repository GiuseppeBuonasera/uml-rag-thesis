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


def check_strip_reading_direction() -> None:
    """Il marcatore di verso di lettura PlantUML (' >' finale, es. 'hasCoach >')
    non fa parte del nome dell'etichetta — casi reali: Louvre 'hasCoach >',
    University 'leads >'/'teaches >' (2026-09-29)."""
    assert ac.strip_reading_direction("hasCoach >") == "hasCoach"
    assert ac.strip_reading_direction("leads >") == "leads"
    assert ac.strip_reading_direction("< manages") == "manages"
    assert ac.strip_reading_direction("no arrow here") == "no arrow here"
    # senza spazio (es. 11 Officine, 2026-10-01); gli stereotipi <<...>> restano invariati
    assert ac.strip_reading_direction("<Lavora") == "Lavora"
    assert ac.strip_reading_direction("effettua>") == "effettua"
    assert ac.strip_reading_direction("<<interface>>") == "<<interface>>"

    text = '@startuml\nclass Employee {}\nEmployee "0..*" -- "0..1" Employee : hasCoach >\n@enduml\n'
    classes, relationships, warnings, unsupported = ac.parse_plantuml(text)
    assert not unsupported, unsupported
    assert relationships[0]["label"] == "hasCoach", relationships[0]

    diagram, build_warnings = ac.build_apollon_json("test-reading-dir", classes, relationships)
    assert not build_warnings, build_warnings
    assert diagram["edges"][0]["data"]["label"] == "hasCoach", diagram["edges"][0]["data"]
    print("  OK  'hasCoach >' -> label 'hasCoach' (il '>' e' solo verso di lettura, non parte del nome)")


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
        ("Long", "long"), ("Real", "double"), ("Text", "string"),  # Real/Text: 2026-10-03
    ]
    for src, expected in cases:
        got = ac.normalize_type_token(src)
        assert got == expected, f"normalize_type_token({src!r}) = {got!r}, atteso {expected!r}"
    # un tipo che e' il nome di una classe/enum del diagramma resta invariato
    assert ac.normalize_type_token("Suit") == "Suit"
    assert ac.normalize_type_token("RoomType") == "RoomType"
    # solo le grafie maiuscole: "text" e' un nome di attributo nel corpus (InsuranceCompany)
    assert ac.normalize_type_token("text") == "text"
    print("  OK  tipi noti normalizzati (String->string, Int->int, ...); nomi di classe/enum invariati")


def check_multiplicity_normalization() -> None:
    # "N" maiuscola aggiunta il 2026-09-30 (RealEstateAgency, regola approvata dall'utente)
    cases = [("n", "*"), ("0..n", "0..*"), ("1..n", "1..*"), ("0..1", "0..1"), ("*", "*"), ("", ""),
             ("N", "*"), ("0..N", "0..*"), ("1..N", "1..*"),
             # tre punti (2026-10-03, De Bari es. 2)
             ("1...*", "1..*"), ("0...*", "0..*"), ("1...n", "1..*")]
    for src, expected in cases:
        got = ac.normalize_multiplicity(src)
        assert got == expected, f"normalize_multiplicity({src!r}) = {got!r}, atteso {expected!r}"
    classes, rels, _, _ = ac.parse_plantuml('@startuml\nclass A\nclass B\nA "1...*" -- "1" B\n@enduml\n')
    diagram, warnings = ac.build_apollon_json("t", classes, rels)
    assert diagram["edges"][0]["data"]["sourceMultiplicity"] == "1..*"
    assert any("tre punti" in w for w in warnings), warnings
    print("  OK  molteplicita' normalizzate (n->*, 0..n->0..*, 1..n->1..*, 1...*->1..* con warning)")


def check_shared_type_glossary() -> None:
    """Regole globali dei tipi non standard nel glossario condiviso (Number->int,
    Calendar->datetime approvati per MilanLibrary; currency->double approvato per
    Restaurant, 2026-09-30): applicati da apply_glossary a ogni esercizio tradotto."""
    from pathlib import Path
    import apply_glossary as ag
    folder = Path(__file__).parent / "raw" / "translated_it" / "Restaurant"
    glossary = ag.load_term_glossary(folder)
    assert glossary["currency"] == "double" and glossary["Number"] == "int" and glossary["Calendar"] == "datetime"
    out = ag.normalize_types(ag.apply_glossary("prezzo: currency", glossary))
    assert out == "price: double", out
    print("  OK  tipi non standard dal glossario condiviso: currency->double, Number->int, Calendar->datetime")


def check_english_homograph_whitelist() -> None:
    """check_translated: gli omografi inglese/italiano (es. 'serve') non sono residui."""
    import check_translated as ct
    assert ct.italian_terms_in_text("t", "waiters who serve customers", ["serve"]) == []
    assert ct.italian_terms_in_text("t", "il cameriere prenota", ["prenota"]) != []
    print("  OK  whitelist omografi ('serve') nel controllo residuo italiano; altri termini ancora segnalati")


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


def check_corrections_change_edge_type() -> None:
    """change_edge_type individua la relazione per (class_a, class_b, label), non
    per testo esatto della riga — caso reale Boeing Acquisition-Contract."""
    plantuml = 'class Acquisition {}\nclass Contract {}\nAcquisition "0..*" -- "1" Contract : part of\n'
    corrected, applied = ac_corr.apply_corrections(
        "test-corr", plantuml,
        [{
            "type": "change_edge_type", "class_a": "Acquisition", "class_b": "Contract",
            "label": "part of", "new_type": "composition", "container": "Contract", "reason": "r",
        }],
    )
    assert 'Acquisition "0..*" --* "1" Contract : part of' in corrected, corrected
    assert len(applied) == 1 and "new_type='composition'" in applied[0], applied

    # il contenitore puo' essere indicato anche se e' l'estremo "source" della riga
    plantuml2 = 'class A {}\nclass B {}\nA "1" -- "0..*" B\n'
    corrected2, _ = ac_corr.apply_corrections(
        "test-corr", plantuml2,
        [{"type": "change_edge_type", "class_a": "A", "class_b": "B", "new_type": "aggregation", "container": "A", "reason": "r"}],
    )
    assert 'A "1" o-- "0..*" B' in corrected2, corrected2

    # container che non corrisponde a nessuno dei due estremi -> fallisce
    try:
        ac_corr.apply_corrections(
            "test-corr", plantuml,
            [{"type": "change_edge_type", "class_a": "Acquisition", "class_b": "Contract", "label": "part of",
              "new_type": "composition", "container": "NonEsiste", "reason": "r"}],
        )
        assert False, "doveva fallire per container inesistente"
    except ValueError:
        pass
    print("  OK  change_edge_type: relazione individuata per (classi, label), contenitore -> operatore corretto")


def check_corrections_remove_label() -> None:
    plantuml = 'class Airplane {}\nclass Acquisition {}\nAirplane "0..1" -- "0..1" Acquisition : part of\n'
    corrected, applied = ac_corr.apply_corrections(
        "test-corr", plantuml,
        [{"type": "remove_label", "class_a": "Airplane", "class_b": "Acquisition", "label": "part of", "reason": "r"}],
    )
    assert 'Airplane "0..1" -- "0..1" Acquisition' in corrected and "part of" not in corrected, corrected
    assert len(applied) == 1
    print("  OK  remove_label: etichetta svuotata, tipo/molteplicita' invariati")


def check_corrections_set_role() -> None:
    """set_role: auto-relazione Airline-Airline, estremo individuato dalla
    molteplicita' (il nome classe non puo' disambiguare un self-loop)."""
    plantuml = 'class Airline {}\nAirline "0..1" -- "0..*" Airline\n'
    corrected, applied = ac_corr.apply_corrections(
        "test-corr", plantuml,
        [{
            "type": "set_role", "class_a": "Airline", "class_b": "Airline",
            "roles": [{"endpoint_mult": "0..1", "role": "mother"}, {"endpoint_mult": "0..*", "role": "daughter"}],
            "reason": "r",
        }],
    )
    assert 'Airline "0..1 mother" -- "0..* daughter" Airline' in corrected, corrected
    assert len(applied) == 1

    # molteplicita' ambigua (stessa su entrambi gli estremi) -> fallisce
    plantuml_ambiguous = 'class Airline {}\nAirline "0..*" -- "0..*" Airline\n'
    try:
        ac_corr.apply_corrections(
            "test-corr", plantuml_ambiguous,
            [{"type": "set_role", "class_a": "Airline", "class_b": "Airline",
              "roles": [{"endpoint_mult": "0..*", "role": "x"}], "reason": "r"}],
        )
        assert False, "doveva fallire per molteplicita' ambigua"
    except ValueError:
        pass
    print("  OK  set_role: ruolo assegnato per molteplicita' su un'auto-relazione, ambiguita' rilevata")


def check_corrections_add_line() -> None:
    """add_line: caso reale BuildingManagement — EntryGroup esisteva gia' nel
    diagramma ma senza alcun collegamento a Building."""
    plantuml = 'class Building {}\nclass EntryGroup {}\n@enduml\n'
    corrected, applied = ac_corr.apply_corrections(
        "test-corr", plantuml,
        [{"type": "add_line", "line": 'Building "1" -- "1" EntryGroup', "reason": "r"}],
    )
    lines = corrected.splitlines()
    assert 'Building "1" -- "1" EntryGroup' in lines, corrected
    assert lines.index('Building "1" -- "1" EntryGroup') < lines.index("@enduml"), (
        "la riga aggiunta deve stare PRIMA di @enduml"
    )
    assert len(applied) == 1

    # riga gia' presente -> fallisce (non si aggiunge due volte silenziosamente)
    try:
        ac_corr.apply_corrections(
            "test-corr", corrected,
            [{"type": "add_line", "line": 'Building "1" -- "1" EntryGroup', "reason": "r"}],
        )
        assert False, "doveva fallire, riga gia' presente"
    except ValueError:
        pass
    print("  OK  add_line: riga aggiunta prima di @enduml; fallisce se gia' presente")


def check_corrections_add_block() -> None:
    """add_block: caso reale EatAtHome — enum inline sostituito da un'enumerazione
    separata <Classe><Attributo> (OrderStatus) dichiarata su piu' righe."""
    plantuml = "class Order {\n  status : enum{placed, delivered}\n}\n@enduml\n"
    block = "enum OrderStatus {\n  placed\n  delivered\n}"
    ops = [
        {"type": "replace_line", "match": "status : enum{placed, delivered}",
         "replacement": "status : OrderStatus", "reason": "r"},
        {"type": "add_block", "block": block, "reason": "r"},
    ]
    corrected, applied = ac_corr.apply_corrections("test-corr", plantuml, ops)
    classes, rels, _w, unsupported = ac.parse_plantuml(corrected)
    assert not unsupported and not rels, corrected
    assert classes["OrderStatus"].kind == "enum", corrected
    assert [a for a, _t in classes["OrderStatus"].attributes] == ["placed", "delivered"], corrected
    assert classes["Order"].attributes == [("status", "OrderStatus")], corrected
    lines = corrected.splitlines()
    assert lines.index("enum OrderStatus {") < lines.index("@enduml"), corrected
    assert len(applied) == 2

    # nome gia' dichiarato -> fallisce
    try:
        ac_corr.apply_corrections("test-corr", corrected, [{"type": "add_block", "block": block, "reason": "r"}])
        assert False, "doveva fallire, OrderStatus gia' dichiarata"
    except ValueError:
        pass
    # blocco che non e' una sola dichiarazione -> fallisce
    for bad in ("enum A {\n  x\n}\nenum B {\n  y\n}", 'A "1" -- "1" B', "enum A {\n  x"):
        try:
            ac_corr.apply_corrections("test-corr", plantuml, [{"type": "add_block", "block": bad, "reason": "r"}])
            assert False, f"doveva fallire: {bad!r}"
        except ValueError:
            pass
    print("  OK  add_block: dichiarazione multi-riga aggiunta prima di @enduml; hard-fail su duplicato/blocco non valido")


def check_description_exclusion_mid_line() -> None:
    """Esclusione a meta' riga (caso InsuranceCompany): niente spazi residui; paragrafo
    assente -> ValueError."""
    import clean_description as cd
    text = "We describe a company.\nWe produce a class diagram. The company issues policies."
    out, applied = cd.apply_exclusions("test-excl", text, ["We produce a class diagram."])
    assert out == "We describe a company.\nThe company issues policies.", repr(out)
    assert len(applied) == 1
    try:
        cd.apply_exclusions("test-excl", text, ["frase inesistente"])
        assert False, "doveva fallire"
    except ValueError:
        pass
    print("  OK  esclusione a meta' riga: nessuno spazio residuo; hard-fail se il testo non c'e'")


def check_known_issues_validation() -> None:
    """known_issues.yaml: voci = codici ammessi (stringa) o dizionari con 'tipo'; id inesistente, codice
    sconosciuto, lista vuota, duplicati, dizionario senza 'tipo' -> ValueError. File reale: EatAtHome
    two_alternative_models; DB06_Flights domain_overlap_static_example con classi condivise e Jaccard
    coerenti con quelli ricalcolati dai JSON Apollon (decisione STOP B, 2026-10-04)."""
    import json
    from pathlib import Path
    import build_manifest as bm
    ids = {"EatAtHome", "Gym"}
    assert bm.validate_known_issues(None, ids) == {}
    ok = {"EatAtHome": ["two_alternative_models"], "Gym": [{"tipo": "domain_overlap_static_example", "x": 1}]}
    assert bm.validate_known_issues(ok, ids) == ok
    for bad in (
        {"Inesistente": ["two_alternative_models"]},
        {"EatAtHome": ["codice_sconosciuto"]},
        {"EatAtHome": []},
        {"EatAtHome": ["two_alternative_models", "two_alternative_models"]},
        {"EatAtHome": [{"x": 1}]},
        {"EatAtHome": [{"tipo": "codice_sconosciuto"}]},
    ):
        try:
            bm.validate_known_issues(bad, ids)
            assert False, f"doveva fallire: {bad}"
        except ValueError:
            pass
    real = bm.load_known_issues(bm.split_ids("corpus") | bm.split_ids("debari_test"))
    assert real["EatAtHome"] == ["two_alternative_models"], real
    db06 = real["DB06_Flights"][0]
    assert db06["tipo"] == "domain_overlap_static_example" and db06["altro_esercizio"] == "AirTravel"
    processed = Path(bm.__file__).parent / "processed"
    a_path, b_path = processed / "apollon_debari" / "DB06_Flights.json", processed / "apollon" / "AirTravel.json"
    if a_path.exists() and b_path.exists():
        names = [{n["data"]["name"].lower(): n["data"]["name"] for n in json.loads(p.read_text(encoding="utf-8"))["nodes"]}
                 for p in (a_path, b_path)]
        shared = sorted(names[0][k] for k in set(names[0]) & set(names[1]))
        jaccard = round(len(shared) / len(set(names[0]) | set(names[1])), 4)
        assert shared == sorted(db06["classi_condivise"]) and len(shared) == db06["n_classi_condivise"], shared
        assert jaccard == db06["jaccard_nomi_classe"], jaccard
    print("  OK  known_issues: codici e voci strutturate; DB06 vs AirTravel coerente con i JSON (4 classi, J=0.2353)")


def _write_exercise(folder, name: str, plantuml: str, tags: str) -> None:
    folder.mkdir(parents=True)
    (folder / "description.md").write_text("A shop sells items.\n", encoding="utf-8")
    (folder / "metadata.txt").write_text(
        f"name: {name}\nlanguage: English\ntags: {tags}\ndomain: Sales\nsource: test\ncitation:\ncontact:\n",
        encoding="utf-8")
    (folder / "plantuml.txt").write_text(plantuml, encoding="utf-8")


def check_split_separation() -> None:
    """Test set De Bari mai nel corpus, e viceversa: id sovrapposti, id DBNN_ o tag debari_test nel
    corpus, record De Bari senza split, JSON Apollon nella cartella sbagliata -> AssertionError."""
    import tempfile
    from pathlib import Path
    import build_manifest as bm

    def fails(fn, *args) -> bool:
        try:
            fn(*args)
            return False
        except AssertionError:
            return True

    corpus_rec = {"id": "Shop", "tags": [], "split": None}
    db_rec = {"id": "DB01_ProjectManagementSystem", "tags": ["debari_test"], "split": "debari_test"}
    bm.check_split_separation("corpus", [corpus_rec], {db_rec["id"]})
    bm.check_split_separation("debari_test", [db_rec], {"Shop"})
    assert fails(bm.check_split_separation, "corpus", [corpus_rec], {"Shop"})
    assert fails(bm.check_split_separation, "corpus", [corpus_rec, db_rec], set())
    assert fails(bm.check_split_separation, "corpus", [{"id": "X", "tags": ["debari_test"]}], set())
    assert fails(bm.check_split_separation, "debari_test", [{**db_rec, "split": None}], set())
    assert fails(bm.check_split_separation, "debari_test", [{**db_rec, "id": "Restaurant"}], set())

    with tempfile.TemporaryDirectory() as tmp:
        c, d = Path(tmp) / "apollon", Path(tmp) / "apollon_debari"
        c.mkdir(); d.mkdir()
        (c / "Shop.json").write_text("{}"); (d / "DB01_X.json").write_text("{}")
        bm.check_apollon_dir_separation(c, d)
        (c / "DB02_Y.json").write_text("{}")
        assert fails(bm.check_apollon_dir_separation, c, d)
    print("  OK  separazione split: id/tag/split/cartelle Apollon sovrapposti -> hard-fail")


def check_debari_record_fields() -> None:
    """build_record(split='debari_test'): split, debari_number dal prefisso DBNN_, debari_title da
    metadata name; id fuori formato -> ValueError. Split corpus: nessun campo extra."""
    import tempfile
    from pathlib import Path
    import build_manifest as bm
    uml = "@startuml\nclass Shop {\n  name : String\n}\n@enduml\n"
    # dentro il repo: raw_dir del record e' relativo alla radice del progetto
    with tempfile.TemporaryDirectory(dir=Path(bm.__file__).parent, prefix="_tmp_test_") as tmp:
        folder = Path(tmp) / "DB07_BankSystem"
        _write_exercise(folder, "Bank System", uml, "debari_test")
        rec = bm.build_record(folder, "debari_test")
        assert (rec["split"], rec["debari_number"], rec["debari_title"]) == ("debari_test", 7, "Bank System"), rec
        assert rec["used_as_static_example"] is False
        # "Estimated Difficulty" dell'xlsx, es. 7: 6 / 5 / 7, ED 1-1-1
        assert rec["debari_xlsx_counts"] == {"classes": 6, "attributes_operations": 5, "associations": 7}, rec
        assert rec["debari_ed_avg"] == 1.0, rec["debari_ed_avg"]
        corpus_rec = bm.build_record(folder, "corpus")
        assert "split" not in corpus_rec and "debari_number" not in corpus_rec
        bad = Path(tmp) / "BankSystem"
        _write_exercise(bad, "Bank System", uml, "debari_test")
        try:
            bm.build_record(bad, "debari_test")
            assert False, "doveva fallire"
        except ValueError:
            pass
    print("  OK  record De Bari: split / debari_number / debari_title; id fuori formato -> errore")


def check_relations_table_english() -> None:
    """generate_relations_table --english: legge plantuml.txt senza glossario, niente colonne IT."""
    import tempfile
    from pathlib import Path
    import generate_relations_table as grt
    uml = '@startuml\nclass Bank\nclass Account\nBank "1" -- "0..* accounts" Account : holds\n@enduml\n'
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp) / "DB07_BankSystem"
        _write_exercise(folder, "Bank System", uml, "debari_test")
        lines = grt.build_table(folder, english=True)
        assert "| Classe A | Classe B | Tipo |" in lines[4], lines[4]
        assert "| Bank | Account | associazione | 1 | 0..* | — | accounts | holds |" in lines, lines
        assert not any("(IT)" in l for l in lines)
    print("  OK  relations_table --english: plantuml.txt, nessun glossario, colonne IT omesse")


def check_convert_split_paths() -> None:
    """apollon_convert.SPLITS: corpus invariato, debari_test su file/cartella separati."""
    from pathlib import Path
    assert ac.SPLITS["corpus"] == (ac.CORPUS_JSONL, ac.APOLLON_OUT_DIR)
    jsonl, out = ac.SPLITS["debari_test"]
    assert jsonl.name == "testset_debari.jsonl" and out.name == "apollon_debari"
    assert jsonl != ac.CORPUS_JSONL and out != ac.APOLLON_OUT_DIR
    print("  OK  split di conversione: corpus -> corpus.jsonl/apollon, debari_test -> testset_debari.jsonl/apollon_debari")


def check_debari_xlsx_comparison() -> None:
    """check_debari: normalizzazione nomi; lettura della Given Solution reale (Part 2 - 1);
    discrepanze per classe/membro/relazione/conteggio su un caso sintetico."""
    import openpyxl
    import build_manifest as bm
    import check_debari as cdb
    assert cdb.norm("Work Product") == cdb.norm("WorkProduct") == "workproduct"
    assert cdb.norm("+Validate()") == "validate" and cdb.norm("Movie-Shop") == "movieshop"
    xs = cdb.xlsx_solution(openpyxl.load_workbook(bm.DEBARI_XLSX, data_only=True), 1)
    assert len(xs["classes"]) == 6 and ("workproduct", "percentcomplete") in xs["members"], xs
    assert ("generalization", frozenset({"workproduct", "requirement"})) in xs["relations"]
    gt = {"classes": {"a", "b"}, "members": {("a", "x")}, "relations": {("association", frozenset({"a", "b"}))},
          "counts": {"classes": 2, "attributes_operations": 1, "associations": 1}}
    xl = {"classes": {"a", "c"}, "members": {("a", "x")}, "relations": {("composition", frozenset({"a", "b"}))}}
    diff = {"debari_xlsx_counts": {"classes": 2, "attributes_operations": 2, "associations": 1}}
    found = cdb.discrepancies(0, gt, xl, diff)
    assert found == [
        "classe solo nell'xlsx: c", "classe solo nel ground truth: b",
        "relazione solo nell'xlsx: composition(a - b)", "relazione solo nel ground truth: association(a - b)",
        "conteggio Attributes + Operations: xlsx 2, ground truth 1",
    ], found
    print("  OK  check_debari: normalizzazione, Given Solution reale, discrepanze classe/relazione/conteggio")


def check_ambiguities_and_apollon_counts() -> None:
    """ambiguities.yaml: campi obbligatori, id del test set, lista non vuota di letture alternative;
    apollon_counts: classi / interfacce / enum / attributi / operazioni / relazioni per tipo dal JSON."""
    import build_manifest as bm
    ok = {"DB05_MovieShop": [{"elemento": "e", "letture_alternative": ["a", "b"], "scelta": "a", "motivazione": "m"}]}
    assert bm.validate_ambiguities(ok, {"DB05_MovieShop"}) == ok
    for bad in ({"DB99_X": ok["DB05_MovieShop"]},
                {"DB05_MovieShop": [{"elemento": "e", "scelta": "a", "motivazione": "m"}]},
                {"DB05_MovieShop": [{**ok["DB05_MovieShop"][0], "letture_alternative": []}]}):
        try:
            bm.validate_ambiguities(bad, {"DB05_MovieShop"})
            assert False, f"doveva fallire: {bad}"
        except ValueError:
            pass
    real_ids = {d.name for d in bm.list_model_dirs([bm.DEBARI_RAW_DIR])}
    assert bm.load_ambiguities(real_ids)["DB05_MovieShop"][0]["scelta"].startswith("estremo Subscriber")
    text = ("@startuml\ninterface I {\n  x : int\n}\nabstract class A {\n  y : int\n  f()\n}\n"
            "enum E {\n  V1\n  V2\n}\nclass B\nB ..|> I\nB --|> A\nA \"1\" -- \"*\" B\n@enduml\n")
    classes, rels, _, _ = ac.parse_plantuml(text)
    diagram, _ = ac.build_apollon_json("t", classes, rels)
    counts = ac.apollon_counts(diagram)
    assert counts == {"classes": 2, "abstract_classes": 1, "interfaces": 1, "enumerations": 1, "attributes": 2,
                      "operations": 1, "enum_values": 2, "relations": 3,
                      "relations_by_type": {"ClassBidirectional": 1, "ClassInheritance": 1,
                                            "ClassRealization": 1}}, counts
    print("  OK  ambiguities.yaml validato; conteggi del ground truth calcolati dal JSON Apollon")


def check_note_on_single_class() -> None:
    """Nota/vincolo testuale attaccato a una sola classe ('N1 .. Reservation', es. 14): nessuna classe
    implicita N1, nessuna relazione, warning con il testo della nota (come i {XOR} su coppie)."""
    text = ('@startuml\nclass Reservation {\n  Pickup_Day\n}\n'
            'note "{Return_Day >= Pickup_Day}" as N1\nN1 .. Reservation\n@enduml\n')
    classes, rels, warnings, unsupported = ac.parse_plantuml(text)
    assert not unsupported and list(classes) == ["Reservation"] and rels == [], (classes, rels)
    assert any("scartato vincolo/nota 'N1'" in w and "Return_Day >= Pickup_Day" in w and "Reservation" in w
               for w in warnings), warnings
    assert not any(w.startswith("riga non riconosciuta") for w in warnings), warnings
    print("  OK  nota su una sola classe: scartata con warning (testo incluso), nessuna classe implicita")


def check_domain_types_and_end_constraints() -> None:
    """Tipi di dominio (2026-10-03): Guid/Address/Phone/Supplier -> string, Price -> double, solo in posizione di
    tipo, solo con la maiuscola, non se il diagramma dichiara la classe omonima; apply_glossary.normalize_types non
    li tocca. Vincolo di estremo '{ordered, unique}': tolto dal ruolo con warning."""
    import apply_glossary as ag
    assert ac.normalize_type_token("Guid") == "string" and ac.normalize_type_token("Price") == "double"
    assert ac.normalize_type_token("Address[]") == "string[]"
    assert ac.normalize_type_token("Address", {"Address"}) == "Address"  # classe dichiarata (SmartHome)
    assert ac.normalize_type_token("address") == "address" and ac.normalize_type_token("phone") == "phone"
    assert ag.normalize_types("Address : Address") == "Address : Address"  # nessuna sostituzione testuale
    text = ("@startuml\nclass A {\n  Address : Address\n  price : Price\n  find() : Supplier\n}\n"
            "class B\nA \"1\" -- \"* {ordered, unique} line_item\" B\nA \"{ordered}\" -- \"0..1\" B\n@enduml\n")
    classes, rels, warnings, _ = ac.parse_plantuml(text)
    assert (rels[0]["target_mult"], rels[0]["target_role"]) == ("*", "line_item"), rels[0]
    assert (rels[1]["source_mult"], rels[1]["source_role"]) == ("", ""), rels[1]
    assert sum("scartato vincolo di estremo" in w for w in warnings) == 2, warnings
    diagram, _ = ac.build_apollon_json("t", classes, rels)
    a = next(n for n in diagram["nodes"] if n["data"]["name"] == "A")["data"]
    assert [x["name"] for x in a["attributes"]] == ["+ Address : string", "+ price : double"], a["attributes"]
    assert a["methods"][0]["name"] == "+ find() : string", a["methods"]
    assert ac.style_check(diagram, "t") == [] and ac.round_trip_check("t", classes, rels, diagram) == []
    classes, rels, _, _ = ac.parse_plantuml("@startuml\nclass Address\nclass H {\n  a : Address\n}\n@enduml\n")
    diagram, _ = ac.build_apollon_json("t", classes, rels)
    h = next(n for n in diagram["nodes"] if n["data"]["name"] == "H")["data"]
    assert h["attributes"][0]["name"] == "+ a : Address", h["attributes"]
    print("  OK  tipi di dominio solo in posizione di tipo (classe omonima rispettata); {ordered, unique} fuori dal ruolo")


def check_leakage_prompt_examples() -> None:
    """leakage_check --prompt: i 2 esempi few-shot del prompt statico estratti da prompt_template_v4.txt;
    --debari-test: 20 record del test set (se testset_debari.jsonl esiste)."""
    import leakage_check as lc
    ex = lc.load_prompt_examples()
    assert sorted(ex) == ["PROMPT_example_1_bank_loans", "PROMPT_example_2_airtravel"], sorted(ex)
    assert ex["PROMPT_example_1_bank_loans"].startswith("Develop an object-oriented application to manage the loans")
    assert "home airport" in ex["PROMPT_example_2_airtravel"]
    if lc.TESTSET_PATH.exists():
        assert all(k.startswith("DB") for k in lc.load_debari_test())
    print("  OK  leakage: esempi del prompt statico (bank loans, AirTravel) estratti dal template")


def check_interface_stereotype() -> None:
    """'interface X {...}' e 'class X <<interface>>' -> kind interface -> stereotype "interface"
    nel JSON Apollon, attributi conservati; '..|>' verso l'interfaccia resta ClassRealization;
    'enum X <<enum>>' invariato; una riga non riconosciuta resta un warning del parser
    (convert_split la tratta come errore)."""
    text = (
        "@startuml\n"
        "interface User {\n  -last_name : String\n}\n"
        "class Shape <<interface>>\n"
        "enum Kind <<enum>> {\n  A\n}\n"
        "class Adult {\n  -id : int\n}\n"
        "Adult ..|> User\n"
        "@enduml\n"
    )
    classes, relationships, warnings, unsupported = ac.parse_plantuml(text)
    assert not unsupported and not warnings, (unsupported, warnings)
    assert classes["User"].kind == "interface" and classes["Shape"].kind == "interface"
    assert classes["Kind"].kind == "enum"
    assert [a for a, _ in classes["User"].attributes] == ["last_name"], classes["User"].attributes
    diagram, _ = ac.build_apollon_json("t", classes, relationships)
    by_name = {n["data"]["name"]: n for n in diagram["nodes"]}
    assert by_name["User"]["data"]["stereotype"] == "interface"
    assert by_name["Shape"]["data"]["stereotype"] == "interface"
    assert by_name["Kind"]["data"]["stereotype"] == "enumeration"
    assert "stereotype" not in by_name["Adult"]["data"]
    assert diagram["edges"][0]["type"] == "ClassRealization", diagram["edges"][0]["type"]
    _, _, warnings, _ = ac.parse_plantuml("@startuml\nfoo bar baz\n@enduml\n")
    assert any(w.startswith("riga non riconosciuta") for w in warnings), warnings
    print("  OK  interface: stereotype \"interface\" nel JSON, attributi conservati, ..|> = ClassRealization")


def main() -> None:
    print("Split corpus / test set De Bari:")
    check_split_separation()
    check_debari_record_fields()
    check_relations_table_english()
    check_convert_split_paths()
    check_interface_stereotype()
    check_note_on_single_class()
    check_domain_types_and_end_constraints()
    check_leakage_prompt_examples()
    check_debari_xlsx_comparison()
    check_ambiguities_and_apollon_counts()
    print()
    print("FASE 1 — normalizzazioni automatiche:")
    check_type_normalization()
    check_multiplicity_normalization()
    check_shared_type_glossary()
    check_english_homograph_whitelist()
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
    check_corrections_change_edge_type()
    check_corrections_remove_label()
    check_corrections_set_role()
    check_corrections_add_line()
    check_corrections_add_block()
    check_description_exclusion_mid_line()
    check_known_issues_validation()
    print()
    print("Marcatore di verso di lettura PlantUML ('>'/'<'):")
    check_strip_reading_direction()
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
