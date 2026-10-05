"""
Controllo di sanita' del post-processing (Passo 3a, 2026-10-05): i JSON di riferimento, serializzati come se fossero la
risposta di un modello, devono superare L0-L4. Insiemi: 20 ground truth del test set, 59 JSON del corpus di retrieval,
2 esempi statici della baseline.

Eccezione documentata (decisions.md, voce 64): l'esempio statico 1 (bank loans) e' la baseline dello studio 2025 e resta
invariato. NON e' escluso: deve fallire L4 con ESATTAMENTE le violazioni elencate in EXPECTED_EX1 (tipi non normalizzati,
molteplicita' "N"), e il suo inventario di nomi italiani e di tipi di ritorno List<...> (che style_check non rileva) deve
coincidere con quello atteso. Qualsiasi violazione non elencata, o elencata e assente, fa fallire il controllo.

Uso:  python generation/sanity_check.py      (exit code 1 se il controllo fallisce)
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import postprocess as pp  # noqa: E402
from prompt_builder import STATIC_DIR, cl  # noqa: E402

EX1_FILE = STATIC_DIR / "example_1_bank_loans_v4.json"
_T = "non e' ne' un tipo primitivo ammesso ne' una classe/enum dichiarata in questo diagramma"
EXPECTED_EX1_STYLE = sorted([
    f"output: tipo 'String' dell'attributo '+ Nome : String' {_T} (classe Banca)",
    f"output: tipo 'String' dell'attributo '+ Nome : String' {_T} (classe Cliente)",
    f"output: tipo 'String' dell'attributo '+ Cognome : String' {_T} (classe Cliente)",
    f"output: tipo 'String' dell'attributo '+ CodiceFiscale : String' {_T} (classe Cliente)",
    f"output: tipo 'Double' dell'attributo '+ Ammontare : Double' {_T} (classe Prestito)",
    f"output: tipo 'DateTime' dell'attributo '+ DataInizio : DateTime' {_T} (classe Prestito)",
    f"output: tipo 'DateTime' dell'attributo '+ DataFine : DateTime' {_T} (classe Prestito)",
    "output: edge 3d4fee86-77da-5478-a7ad-381693ec5aba ha sourceMultiplicity='N', molteplicita' 'n' non normalizzata a '*'",
    "output: edge 1798385c-d0a2-5245-aaba-4215aa153799 ha sourceMultiplicity='N', molteplicita' 'n' non normalizzata a '*'",
    "output: edge f1315235-70fd-5179-9e42-754b30f0f9f1 ha targetMultiplicity='N', molteplicita' 'n' non normalizzata a '*'",
])
# nomi in italiano con traccia in inglese (style_check non li rileva: inventario esatto)
EXPECTED_EX1_NAMES = {
    "classes": ["Banca", "Cliente", "Prestito"],
    "attributes": ["+ Ammontare : Double", "+ CodiceFiscale : String", "+ Cognome : String", "+ DataFine : DateTime",
                   "+ DataInizio : DateTime", "+ Nome : String", "+ Nome : String", "+ Rata : double",
                   "+ Stipendio : double"],
}
# tipi di ritorno collezione (style_check non controlla i tipi di ritorno)
EXPECTED_EX1_COLLECTION_RETURNS = ["Banca: + GetPrestitiCliente(CodiceFiscale:string):List<Prestito>",
                                   "Banca: + SearchPrestiti(CodiceFiscale:string):List<Prestito>"]


def as_model_output(diagram: dict) -> str:
    """Serializzazione compatta, come risposta pulita di un modello (con interactive, se il JSON lo ha)."""
    return json.dumps(diagram, ensure_ascii=False, separators=(",", ":"))


def ex1_inventory(d: dict) -> dict:
    return {
        "classes": sorted(n["data"]["name"] for n in d["nodes"]),
        "attributes": sorted(a["name"] for n in d["nodes"] for a in n["data"]["attributes"]),
        "collection_returns": sorted(f"{n['data']['name']}: {m['name']}" for n in d["nodes"]
                                     for m in n["data"]["methods"] if "<" in m["name"]),
    }


def check_set(label: str, items: list[tuple[str, dict]]) -> tuple[list[str], Counter, Counter]:
    failures, fmt, lay = [], Counter(), Counter()
    for item_id, diagram in items:
        v = pp.validate_response(as_model_output(diagram), "stop")
        fmt.update(v.format_issues.keys())
        lay.update(v.layout_issues.keys())
        if v.level != 4:
            failures.append(f"{label}/{item_id}: livello {v.level}, {v.failure}: {v.errors}")
        if v.style_raw:
            failures.append(f"{label}/{item_id}: style_check originale non vuoto: {v.style_raw}")
        if v.l4_rewrites:
            failures.append(f"{label}/{item_id}: riscritture L4 inattese su un riferimento: {v.l4_rewrites}")
    return failures, fmt, lay


def main() -> int:
    candidates, queries = cl.load_all()
    gt = [(q["id"], q["diagram_apollon_json"]) for q in queries]
    corpus = [(c["id"], c["diagram_apollon_json"]) for c in candidates]
    ex1 = json.loads(EX1_FILE.read_text(encoding="utf-8"))
    ex2 = cl.load_all()[0]
    ex2 = [("AirTravel", c["diagram_apollon_json"]) for c in ex2 if c["id"] == "AirTravel"]
    ok = True
    for label, items, expected_n in (("test_set", gt, 20), ("corpus", corpus, 59), ("static_ex2", ex2, 1)):
        fails, fmt, lay = check_set(label, items)
        status = "OK" if not fails and len(items) == expected_n else "FALLITO"
        ok &= status == "OK"
        print(f"{label:10s} {len(items):3d} JSON -> {status}; diagnostici formato: {dict(sorted(fmt.items()))}, "
              f"layout: {dict(sorted(lay.items()))}")
        for f in fails:
            print("   ", f)

    v = pp.validate_response(as_model_output(ex1), "stop")
    got_style = sorted(v.errors.get("L4", []))
    inv = ex1_inventory(ex1)
    problems = []
    if v.level != 3 or v.failure != "style":
        problems.append(f"atteso fallimento a L4 (livello 3 superato), ottenuto livello {v.level} {v.failure}")
    if got_style != EXPECTED_EX1_STYLE:
        problems.append(f"violazioni di stile non attese: {sorted(set(got_style) - set(EXPECTED_EX1_STYLE))}; "
                        f"attese e assenti: {sorted(set(EXPECTED_EX1_STYLE) - set(got_style))}")
    if sorted(v.style_raw) != EXPECTED_EX1_STYLE:
        problems.append("style_check originale diverso dalle violazioni attese")
    if v.l4_rewrites:  # "N" maiuscola non e' tra le riscritture ammesse
        problems.append(f"riscritture L4 inattese: {v.l4_rewrites}")
    if inv["classes"] != EXPECTED_EX1_NAMES["classes"] or inv["attributes"] != EXPECTED_EX1_NAMES["attributes"]:
        problems.append(f"inventario dei nomi diverso da quello atteso: {inv}")
    if inv["collection_returns"] != EXPECTED_EX1_COLLECTION_RETURNS:
        problems.append(f"tipi di ritorno collezione diversi: {inv['collection_returns']}")
    print(f"static_ex1   1 JSON -> {'OK' if not problems else 'FALLITO'} (eccezione documentata: {len(got_style)} "
          f"violazioni L4 attese, 3 classi e 9 attributi con nomi italiani, 2 tipi di ritorno List<...>); "
          f"diagnostici formato: {sorted(v.format_issues)}, layout: {sorted(v.layout_issues)}")
    for p in problems:
        print("   ", p)
    ok &= not problems
    print("SANITY CHECK:", "OK" if ok else "FALLITO")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
