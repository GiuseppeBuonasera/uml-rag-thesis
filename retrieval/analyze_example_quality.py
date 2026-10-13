"""
Qualita' degli ESEMPI che il Passo 3b mostrera' (2026-10-12, voce 137). SOLO DESCRITTIVO: nessuna generazione,
nessuna misura con il GT della query (gli esercizi di valutazione restano solo candidati e query del file congelato).

Per ogni retriever del file congelato data/retrieval_frozen/retrievals_3b.jsonl (bm25 k = 2 e 3, dense, hybrid,
random nelle 3 ripetizioni) e per le query di valutazione (54) e di sviluppo (26), si guardano gli esempi recuperati:
- traccia con istruzioni per lo studente (elenco della voce 128, letto a mano: 7 esercizi + 1 dubbio);
- attributi senza tipo (quota sugli attributi degli esempi) ed esempi con piu' della meta' degli attributi senza tipo;
- molteplicita' vuote (quota sugli estremi delle relazioni che le prevedono);
- esempi senza nessun attributo; esempi De Bari.
Per ogni proprieta': quota di posti (esempi) e quota di query con almeno un esempio interessato.

Uso:
    python retrieval/analyze_example_quality.py [--run-id ID]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "retrieval"), str(ROOT / "generation"), str(ROOT / "experiments"), str(ROOT / "corpus")]
import paths  # noqa: E402

RESULTS_DIR = ROOT / "data" / "results" / "retrieval"
FROZEN = ROOT / "data" / "retrieval_frozen" / "retrievals_3b.jsonl"
# voce 128: tracce con indicazioni rivolte allo studente (lette a mano); Menso dubbia (ipotesi di modellazione)
STUDENT_INSTRUCTIONS = ("FitnessCompanyConan", "GameArea", "GasStation_TUW", "Musicmatic",
                        "PizzaDeliveryWithEntertainment", "SellingGoods", "DB18_LibrarySystem")
DOUBTFUL = ("Menso",)
NO_MULT = ("ClassInheritance", "ClassRealization", "ClassDependency")
CONDITIONS = (("bm25", 2), ("bm25", 3), ("dense", 3), ("hybrid", 3), ("random", 3))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def example_profile(diagram: dict) -> dict:
    attrs = [a.get("name", "") if isinstance(a, dict) else str(a) for n in diagram.get("nodes", [])
             if (n.get("data") or {}).get("stereotype") != "enumeration"
             for a in (n["data"].get("attributes") or [])]
    ends = [(e.get("data") or {}).get(k) for e in diagram.get("edges", []) if e["type"] not in NO_MULT
            for k in ("sourceMultiplicity", "targetMultiplicity")]
    untyped = sum(":" not in a for a in attrs)
    return {"attrs": len(attrs), "untyped": untyped, "ends": len(ends), "empty_ends": sum(not x for x in ends)}


def analyze() -> tuple[list[dict], dict]:
    recs = {r["id"]: r for r in paths.read_jsonl(paths.CORPUS_JSONL) + paths.read_jsonl(paths.TESTSET_JSONL)}
    prof = {i: example_profile(r["diagram_apollon_json"]) for i, r in recs.items()}
    roles = paths.load_roles()
    rows_frozen = [json.loads(x) for x in FROZEN.read_text(encoding="utf-8").splitlines() if x.strip()]
    out = []
    for role in ("valutazione", "sviluppo"):
        for cond, k in CONDITIONS:
            sel = [r for r in rows_frozen if r["retriever"] == cond and r["k"] == k and roles[r["query"]]["role"] == role]
            slots = [e for r in sel for e in r["ids"]]
            flags = {
                "istruzioni_studente": lambda e: e in STUDENT_INSTRUCTIONS,
                "istruzioni_dubbie": lambda e: e in DOUBTFUL,
                "attributi_senza_tipo_oltre_meta": lambda e: prof[e]["attrs"] > 0 and prof[e]["untyped"] / prof[e]["attrs"] > 0.5,
                "senza_attributi": lambda e: prof[e]["attrs"] == 0,
                "debari": lambda e: roles[e]["source"] == "debari",
            }
            row = {"ruolo_query": role, "retriever": cond, "k": k, "righe": len(sel), "posti": len(slots),
                   "quota_attributi_senza_tipo": sum(prof[e]["untyped"] for e in slots) / max(sum(prof[e]["attrs"] for e in slots), 1),
                   "quota_molteplicita_vuote": sum(prof[e]["empty_ends"] for e in slots) / max(sum(prof[e]["ends"] for e in slots), 1)}
            for name, fn in flags.items():
                row[f"posti_{name}"] = sum(fn(e) for e in slots) / len(slots)
                row[f"query_{name}"] = len({r["query"] for r in sel if any(fn(e) for e in r["ids"])}) / len({r["query"] for r in sel})
            out.append(row)
    corpus_ref = {"quota_attributi_senza_tipo": sum(p["untyped"] for p in prof.values()) / sum(p["attrs"] for p in prof.values()),
                  "quota_molteplicita_vuote": sum(p["empty_ends"] for p in prof.values()) / sum(p["ends"] for p in prof.values()),
                  "esercizi_istruzioni_studente": len(STUDENT_INSTRUCTIONS)}
    return out, corpus_ref


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args(argv)
    rows, ref = analyze()
    run_id = args.run_id or f"examples_quality_{dt.date.today().isoformat()}_{git('rev-parse', '--short', 'HEAD')}"
    out = RESULTS_DIR / run_id
    out.mkdir(parents=True, exist_ok=True)
    with (out / "summary.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in rows)
    pct = lambda x: f"{100 * x:.1f} %"  # noqa: E731
    L = [f"# Qualità degli esempi che il 3b mostrerà ({run_id})", "",
         "Voce 137 di `docs/decisions.md`. SOLO DESCRITTIVO: esempi del file congelato "
         "`data/retrieval_frozen/retrievals_3b.jsonl`; si guarda solo il GT degli ESEMPI, mai quello della query. Random: "
         "le 3 ripetizioni insieme.", "",
         f"Riferimento, tutti gli 80 esercizi: attributi senza tipo {pct(ref['quota_attributi_senza_tipo'])}, molteplicità "
         f"vuote {pct(ref['quota_molteplicita_vuote'])}; tracce con istruzioni per lo studente: "
         f"{ref['esercizi_istruzioni_studente']} esercizi (+ Menso, dubbia).", "",
         "| query | retriever | k | esempi | con istruzioni per lo studente: esempi / query | attributi senza tipo | esempi con oltre metà "
         "attributi senza tipo: esempi / query | molteplicità vuote | esempi senza attributi: esempi / query | De Bari: esempi / query |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['ruolo_query']} | {r['retriever']} | {r['k']} | {r['posti']} | "
                 f"{pct(r['posti_istruzioni_studente'])} / {pct(r['query_istruzioni_studente'])} | "
                 f"{pct(r['quota_attributi_senza_tipo'])} | {pct(r['posti_attributi_senza_tipo_oltre_meta'])} / "
                 f"{pct(r['query_attributi_senza_tipo_oltre_meta'])} | {pct(r['quota_molteplicita_vuote'])} | "
                 f"{pct(r['posti_senza_attributi'])} / {pct(r['query_senza_attributi'])} | {pct(r['posti_debari'])} / "
                 f"{pct(r['query_debari'])} |")
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(out)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
