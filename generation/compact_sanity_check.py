"""
Controllo di sanita' della struttura comune e del formato JSON compatto (2026-10-08, FASE 1), sui 79 diagrammi
convertiti (59 del corpus + 20 del test set; del test set si usa solo il ground truth, per verificare il codice:
nessun risultato sperimentale). Nessuna chiamata a un LLM.

  a. PlantUML CANONICO (plantuml_format.apollon_to_plantuml) -> post-processing PlantUML v2 (lettura -> struttura ->
     espansore unico): Apollon IDENTICO al Passo 1 (JSON uguale, id e coordinate compresi), 79/79;
  b. Apollon del Passo 1 -> JSON compatto -> (serializzato e riletto) -> struttura -> espansore: IDENTICO, 79/79;
  c. token (vocabolario cl100k_base del repository): Apollon completo compatto (senza interactive, come negli esempi
     del prompt) contro JSON compatto, mediana e massimo.

Si raccolgono TUTTE le differenze (percorsi JSON) e si classificano: nessuna differenza viene nascosta. Unica
differenza attesa e spiegata (STOP 1, 2026-10-08): gli id dei METODI. Nel Passo 1 build_apollon_json ricava l'id di un
metodo dalla firma GREZZA del PlantUML trascritto (stable_id("<modello>:method:<classe>:<firma grezza>:<i>"), es.
"getRideNr()"), mentre struttura, JSON compatto e Apollon conservano solo la firma RESA ("+ getRideNr()"): la firma
grezza non e' ricostruibile, quindi l'id cambia quando le due grafie differiscono (148 metodi su 155). Gli id restano
deterministici e uguali per tutte le strade nuove (stesso espansore). Esito: "identico" e "identico salvo gli id dei
metodi" riportati separatamente.

Uso:  python generation/compact_sanity_check.py
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plantuml_postprocess as ppu  # noqa: E402
import uml_structure as us  # noqa: E402
from plantuml_format import apollon_to_plantuml  # noqa: E402
from prompt_builder import serialize_diagram  # noqa: E402
from token_estimate import count_tokens  # noqa: E402

ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "corpus"))
import paths  # noqa: E402  (percorsi condivisi, voce 116)

JSONL = (paths.CORPUS_JSONL, paths.TESTSET_JSONL)


def compact_text(data: dict) -> str:
    """Serializzazione del JSON compatto negli esempi del prompt (come serialize_diagram 'compact')."""
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


METHOD_ID = re.compile(r"^\$\.nodes\[\d+\]\.data\.methods\[\d+\]\.id$")


def differences(a, b, path="$") -> list[str]:
    """Tutti i percorsi JSON in cui a e b differiscono."""
    if type(a) is not type(b):
        return [f"{path} (tipo {type(a).__name__} contro {type(b).__name__})"]
    if isinstance(a, dict):
        out = []
        for k in list(a) + [k for k in b if k not in a]:
            out += [f"{path}.{k} (presente solo da una parte)"] if k not in a or k not in b else \
                differences(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{path} (lunghezza {len(a)} contro {len(b)})"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, f"{path}[{i}]")]
    return [] if a == b else [path]


def classify(rid: str, diffs: list[str], out: dict, key: str) -> None:
    other = [d for d in diffs if not METHOD_ID.match(d)]
    if not diffs:
        out[f"{key}_identical"] += 1
    elif not other:
        out[f"{key}_method_ids_only"] += 1
        out[f"{key}_method_ids"] += len(diffs)
    else:
        out[f"{key}_other"].append((rid, other[:5], len(other)))


def load_records() -> list[dict]:
    recs = [r for p in JSONL for r in paths.read_jsonl(p)]
    return [r for r in recs if r.get("diagram_apollon_json")]


def run() -> dict:
    records = load_records()
    out = {"n": len(records), "tokens_full": [], "tokens_compact": [], "chars_full": [], "chars_compact": [],
           "methods_total": sum(len(n["data"].get("methods", [])) for r in records
                                for n in r["diagram_apollon_json"]["nodes"])}
    for key in ("a", "b"):
        out.update({f"{key}_identical": 0, f"{key}_method_ids_only": 0, f"{key}_method_ids": 0, f"{key}_other": []})
    for r in records:
        ref = r["diagram_apollon_json"]
        mid = ref["id"]
        # a. PlantUML canonico -> struttura -> espansore (post-processing v2, come le run nuove)
        v = ppu.validate_plantuml_response(apollon_to_plantuml(ref), "stop", mid, "v2")
        classify(r["id"], differences(v.diagram, ref) if v.diagram is not None else [f"nessun diagramma ({v.failure})"],
                 out, "a")
        # b. Apollon -> compatto -> testo -> compatto -> struttura -> espansore
        compact = us.apollon_to_compact(ref)
        text = compact_text(compact)
        produced, _ = us.compact_to_apollon(json.loads(text), mid)
        classify(r["id"], differences(produced, ref), out, "b")
        # c. token
        full = serialize_diagram(ref, "compact", True)
        out["tokens_full"].append(count_tokens(full))
        out["tokens_compact"].append(count_tokens(text))
        out["chars_full"].append(len(full))
        out["chars_compact"].append(len(text))
    return out


def main() -> int:
    s = run()
    for key, label in (("a", "a. PlantUML canonico -> struttura -> espansore (post-processing v2)"),
                       ("b", "b. Apollon -> JSON compatto -> struttura -> espansore")):
        print(f"{label}: identico al Passo 1 in {s[f'{key}_identical']}/{s['n']}; identico salvo gli id dei metodi in "
              f"{s[f'{key}_method_ids_only']} ({s[f'{key}_method_ids']} id di metodo diversi su {s['methods_total']} "
              f"metodi); altre differenze in {len(s[f'{key}_other'])}")
        for rid, other, n in s[f"{key}_other"]:
            print(f"     {rid}: {n} differenze, es. {other}")
    tf, tc = s["tokens_full"], s["tokens_compact"]
    ratios = [c / f for c, f in zip(tc, tf)]
    print(f"c. token (cl100k_base), mediana / massimo: Apollon completo {statistics.median(tf):.0f} / {max(tf)}; "
          f"JSON compatto {statistics.median(tc):.0f} / {max(tc)}; compatto / completo mediana "
          f"{statistics.median(ratios):.3f} (min {min(ratios):.3f}, max {max(ratios):.3f}); caratteri mediana "
          f"{statistics.median(s['chars_full']):.0f} -> {statistics.median(s['chars_compact']):.0f}")
    ok = all(s[f"{k}_identical"] + s[f"{k}_method_ids_only"] == s["n"] and not s[f"{k}_other"] for k in "ab")
    print("COMPACT SANITY CHECK:", "OK" if ok else "FALLITO", f"(attesi: a e b identici al Passo 1 in {s['n']}/{s['n']}, "
          "con la sola eccezione dichiarata degli id dei metodi, seme dalla firma grezza del Passo 1)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
