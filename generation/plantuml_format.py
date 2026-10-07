"""
PlantUML CANONICO per gli esempi della strada 1 (secondo pilota, 2026-10-07). Nessuna chiamata a un LLM.

Il diagram_plantuml del corpus (versione corretta) ha una sintassi disomogenea (attributi alla Java "String Title",
visibilita' "-", ruoli scritti dopo i due punti e distinti dai nomi di associazione solo da
corpus/label_classification.json). Il PlantUML canonico si ottiene in modo deterministico dal diagramma Apollon del
Passo 1 (= diagram_plantuml corretto passato dalla pipeline del Passo 1, con la classificazione delle etichette) e usa
SOLO la sintassi del template v4_plantuml_instructions.txt:

    class Nome {            abstract class Nome {      interface Nome {      enum Nome {
      + attributo : tipo       ...                          ...                 VALORE
      + metodo(p) : Tipo     }                            }                    }
    }
    Sinistra "molt ruolo" OP "molt ruolo" Destra : nomeAssociazione

Operatori (per costruzione di apollon_convert.relationship_kind):
    ClassInheritance  Sotto --|> Sopra          ClassRealization  Classe ..|> Interfaccia
    ClassComposition  Tutto *-- Parte           ClassAggregation  Tutto o-- Parte
    ClassUnidirectional  A --> B                ClassDependency   A ..> B
    ClassBidirectional   A -- B
Tra virgolette a un estremo: molteplicita', poi (dopo uno spazio) il ruolo; un ruolo senza molteplicita' si scrive da
solo. Dopo i due punti: SOLO il nome dell'associazione. Il round-trip (PlantUML canonico -> convertitore con la regola
automatica delle etichette -> Apollon) restituisce lo stesso contenuto del diagramma di partenza: verificato su tutti i
79 diagrammi in generation/plantuml_sanity_check.py.
"""

from __future__ import annotations

OP_BY_TYPE = {  # tipo Apollon -> (operatore, la sorgente Apollon sta a sinistra?)
    "ClassInheritance": ("--|>", True),
    "ClassRealization": ("..|>", True),
    "ClassComposition": ("*--", False),  # Tutto (destinazione Apollon) a sinistra, Parte (sorgente) a destra
    "ClassAggregation": ("o--", False),
    "ClassUnidirectional": ("-->", True),
    "ClassDependency": ("..>", True),
    "ClassBidirectional": ("--", True),
}


def _end(mult: str, role: str) -> str:
    text = " ".join(x for x in (mult or "", role or "") if x)
    return f' "{text}"' if text else ""


def apollon_to_plantuml(diagram: dict) -> str:
    names = {n["id"]: n["data"]["name"] for n in diagram["nodes"]}
    lines = ["@startuml", ""]
    for n in diagram["nodes"]:
        d = n["data"]
        stereo = d.get("stereotype")
        kind = ("interface" if stereo == "interface" else "enum" if stereo == "enumeration"
                else "abstract class" if d.get("isAbstract") else "class")
        members = [a["name"] for a in d.get("attributes", [])] + [m["name"] for m in d.get("methods", [])]
        if members:
            lines.append(f"{kind} {d['name']} {{")
            lines += [f"  {m}" for m in members]
            lines.append("}")
        else:
            lines.append(f"{kind} {d['name']} {{}}")
        lines.append("")
    for e in diagram["edges"]:
        op, src_left = OP_BY_TYPE[e["type"]]
        data = e.get("data") or {}
        s_end = _end(data.get("sourceMultiplicity", ""), data.get("sourceRole", ""))
        t_end = _end(data.get("targetMultiplicity", ""), data.get("targetRole", ""))
        src, tgt = names[e["source"]], names[e["target"]]
        line = f"{src}{s_end} {op}{t_end} {tgt}" if src_left else f"{tgt}{t_end} {op}{s_end} {src}"
        label = data.get("label", "")
        lines.append(line + (f" : {label}" if label else ""))
    lines += ["", "@enduml"]
    return "\n".join(lines)
