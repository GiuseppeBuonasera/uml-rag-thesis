"""
Controllo di sanita' della strada 1 (secondo pilota, 2026-10-07): i 79 diagrammi convertiti (59 del corpus + 20 del
test set), passati come se fossero risposte generate, attraverso generation/plantuml_postprocess.py con la regola
AUTOMATICA delle etichette (nessuna label_classification). Due varianti:

  A. diagram_plantuml del record (versione corretta del Passo 1), cosi' com'e';
  B. PlantUML CANONICO (generation/plantuml_format.apollon_to_plantuml) ricavato dal JSON del Passo 1.

Per ciascuna: livello raggiunto (deve essere L4) e differenze di CONTENUTO rispetto al JSON del Passo 1 (nomi, tipo,
attributi e metodi dei nodi; relazioni come multinsieme di (tipo, sorgente, destinazione, molteplicita', ruoli,
etichetta)); id e coordinate non contano (formato di consegna). Del test set si usa solo il ground truth, per verificare
il convertitore: nessun risultato sperimentale.

Uso:  python generation/plantuml_sanity_check.py [--details]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plantuml_postprocess as ppu  # noqa: E402
from plantuml_format import apollon_to_plantuml  # noqa: E402

ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "corpus"))
import paths  # noqa: E402  (percorsi condivisi, voce 116)

JSONL = (paths.CORPUS_JSONL, paths.TESTSET_JSONL)


def node_sig(d: dict) -> dict:
    return {n["data"]["name"]: (n["data"].get("stereotype"), bool(n["data"].get("isAbstract")),
                                tuple(a["name"] for a in n["data"].get("attributes", [])),
                                tuple(m["name"] for m in n["data"].get("methods", []))) for n in d["nodes"]}


def edge_sig(d: dict) -> Counter:
    names = {n["id"]: n["data"]["name"] for n in d["nodes"]}
    out = Counter()
    for e in d["edges"]:
        x = e.get("data") or {}
        out[(e["type"], names[e["source"]], names[e["target"]], x.get("sourceMultiplicity", ""),
             x.get("targetMultiplicity", ""), x.get("sourceRole", ""), x.get("targetRole", ""), x.get("label", ""))] += 1
    return out


def diff(produced: dict, reference: dict) -> dict:
    a, b = node_sig(produced), node_sig(reference)
    ea, eb = edge_sig(produced), edge_sig(reference)
    return {"nodes_only_produced": sorted(set(a) - set(b)), "nodes_only_reference": sorted(set(b) - set(a)),
            "nodes_changed": sorted(k for k in set(a) & set(b) if a[k] != b[k]),
            "edges_only_produced": sorted((ea - eb).elements()), "edges_only_reference": sorted((eb - ea).elements())}


def classify_edge_diff(d: dict) -> Counter:
    """Accoppia le relazioni diverse per (tipo, sorgente, destinazione) e dice che cosa cambia."""
    c = Counter()
    only_ref = list(d["edges_only_reference"])
    for e in d["edges_only_produced"]:
        match = next((r for r in only_ref if r[:3] == e[:3]), None)
        if match is None:
            c["relazione senza corrispondente"] += 1
            continue
        only_ref.remove(match)
        _, _, _, sm, tm, sr, tr, lab = e
        _, _, _, rsm, rtm, rsr, rtr, rlab = match
        if lab and not rlab and (rsr or rtr) and (sm, tm) == (rsm, rtm):
            c["ruolo del Passo 1 rimasto come nome di associazione (testo dopo i due punti)"] += 1
        elif (sm, tm) != (rsm, rtm):
            c["molteplicita' diverse"] += 1
        else:
            c["altro (ruoli / etichetta)"] += 1
    c["relazione senza corrispondente"] += len(only_ref)
    return +c


def run(details: bool = False) -> dict:
    """Esegue le due varianti e restituisce i riepiloghi (usato anche dai test)."""
    records = [r for p in JSONL for r in paths.read_jsonl(p)]
    records = [r for r in records if r.get("diagram_apollon_json")]
    summary = {}
    for variant in ("A", "B"):
        levels, kinds, n_diff, discarded, examples = Counter(), Counter(), 0, 0, []
        for r in records:
            ref = r["diagram_apollon_json"]
            text = r["diagram_plantuml"] if variant == "A" else apollon_to_plantuml(ref)
            v = ppu.validate_plantuml_response(text, "stop", r["id"])
            levels[v.level] += 1
            discarded += len(v.discarded_lines)
            if v.diagram is None:
                examples.append((r["id"], v.failure, v.errors))
                continue
            d = diff(v.diagram, ref)
            if any(d.values()):
                n_diff += 1
                kinds.update(classify_edge_diff(d))
                for k in ("nodes_only_produced", "nodes_only_reference", "nodes_changed"):
                    if d[k]:
                        kinds[k] += len(d[k])
                if details:
                    examples.append((r["id"], {k: v2 for k, v2 in d.items() if v2}))
        summary[variant] = {"n": len(records), "levels": dict(levels), "discarded": discarded, "n_diff": n_diff,
                            "kinds": dict(kinds), "examples": examples}
    return summary


def main(details: bool = False) -> int:
    s = run(details)
    for variant, label in (("A", "A. diagram_plantuml cosi' com'e'"), ("B", "B. PlantUML canonico dal JSON del Passo 1")):
        r = s[variant]
        print(f"{label}: {r['n']} diagrammi; livelli raggiunti {dict(sorted(r['levels'].items()))}; righe scartate "
              f"{r['discarded']}; diagrammi con contenuto diverso dal Passo 1: {r['n_diff']}")
        for k, v in sorted(r["kinds"].items(), key=lambda x: -x[1]):
            print(f"    {v:4d}  {k}")
        for ex in r["examples"][:40 if details else 5]:
            print("    ", ex)
    ok = all(s[x]["levels"].get(4, 0) == s[x]["n"] for x in "AB") and s["B"]["n_diff"] == 0
    print("PLANTUML SANITY CHECK:", "OK" if ok else "FALLITO", "(attesi: tutti a L4 in A e B; B identico al Passo 1)")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--details", action="store_true")
    sys.exit(main(ap.parse_args().details))
