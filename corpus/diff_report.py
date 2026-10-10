"""
Genera corpus/diff_report.md: le differenze tra il PlantUML sorgente e il JSON
Apollon v4 finale, raggruppate per CAUSA (non per esercizio) — FASE 4
(2026-09-28, STOP 3, vedi docs/decisions.md).

Tre categorie di causa, in ordine:
1. "Correzioni di contenuto (errori)" e 2. "Chiarimenti di modellazione" —
   entrambe dal PlantUML VERAMENTE originale (corpus/raw/) al PlantUML
   corretto (corpus.jsonl campo "diagram_plantuml"), tramite
   corpus/corrections/<id>.yaml — vedi corpus/apply_corrections.py. Preso
   direttamente dal campo "corrections_applied" di ciascun record (gia'
   motivato li'), smistato in base al tag "[correzione_errore]"/
   "[chiarimento_modellazione]" che apply_corrections.py antepone a ogni
   voce (campo "category" opzionale di ciascuna operazione YAML, default
   "correzione_errore"). Un "chiarimento di modellazione" (2026-09-28,
   introdotto col caso Boeing) non corregge un errore in senso stretto: il
   PlantUML sorgente non era "sbagliato", ma description.md descrive la
   relazione in modo piu' preciso di quanto disegnato (es. un'associazione
   plain dove il testo implica whole-part, un ruolo non esplicitato su
   un'auto-relazione).
3. Tutte le altre — dal PlantUML corretto al JSON Apollon finale, prodotte da
   corpus/apollon_convert.py: normalizzazione tipi/molteplicita',
   canonicalizzazione metodi, classificazione etichette in ruoli, reificazione
   di classi associative, estrazione di vincoli di generalizzazione,
   modificatori/default di attributi.

Sola lettura: non modifica corpus.jsonl ne' i JSON Apollon, gia' devono
esistere (esegui prima build_manifest.py e apollon_convert.py).

Uso:
    python corpus/diff_report.py
"""

from __future__ import annotations

import re
from pathlib import Path

import apollon_convert as ac
import paths

CORPUS_JSONL = paths.CORPUS_JSONL
OUT_PATH = Path(__file__).parent / "diff_report.md"

CAUSES = [
    "Correzioni di contenuto — errori (corpus/corrections/<id>.yaml)",
    "Chiarimenti di modellazione (corpus/corrections/<id>.yaml)",
    "Normalizzazione tipi primitivi negli attributi",
    "Normalizzazione tipi primitivi nei metodi (tipo di ritorno)",
    "Normalizzazione molteplicita' ('n' -> '*')",
    "Classificazione etichette -> ruolo (sourceRole/targetRole, label svuotato)",
    "Reificazione classe associativa",
    "Vincoli di generalizzazione estratti (campo 'constraints', mai nell'edge)",
    "Modificatori/default di attributi ({static}/{abstract}/{frozen}/const/'=')",
]


def main() -> None:
    records = paths.read_jsonl(CORPUS_JSONL)
    classification = ac.load_label_classification()

    causes: dict[str, list[str]] = {c: [] for c in CAUSES}

    for rec in records:
        model_id = rec["id"]

        for c in rec.get("corrections_applied") or []:
            bucket = CAUSES[1] if c.startswith("[chiarimento_modellazione]") else CAUSES[0]
            causes[bucket].append(f"**{model_id}** — {c}")

        if not rec.get("diagram_plantuml"):
            continue
        classes, rels, _warn, unsupported = ac.parse_plantuml(rec["diagram_plantuml"])
        if unsupported:
            continue

        for cname, pc in classes.items():
            if pc.placeholder:
                continue
            if pc.kind != "enum":
                for attr_name, attr_type in pc.attributes:
                    if not attr_type:
                        continue
                    norm = ac.normalize_type_token(attr_type)
                    if norm != attr_type:
                        causes[CAUSES[2]].append(f"**{model_id}** — `{cname}.{attr_name}` : `{attr_type}` -> `{norm}`")

            for m in pc.methods:
                for old, new in ac.TYPE_NORMALIZATION.items():
                    if old == new:
                        continue
                    if re.search(rf"\b{re.escape(old)}\b", m):
                        causes[CAUSES[3]].append(f"**{model_id}** — metodo `{m.strip()}`: '{old}' -> '{new}'")
                        break

        for r in rels:
            if r["kind"] != "binary":
                continue
            for side, mult in (("source", r.get("source_mult")), ("target", r.get("target_mult"))):
                if mult and ac.normalize_multiplicity(mult) != mult:
                    causes[CAUSES[4]].append(
                        f"**{model_id}** — `{r['raw']}` (lato {side}): `{mult}` -> `{ac.normalize_multiplicity(mult)}`"
                    )
            if r["label"]:
                key = (model_id, r["source"], r["op"], r["target"], r["label"])
                entry = classification.get(key)
                if entry and entry["tipo"] == "ruolo":
                    causes[CAUSES[5]].append(f"**{model_id}** — `{r['raw']}`: label '{r['label']}' -> ruolo su estremo")
                elif entry and entry["tipo"] == "ruolo_doppio":
                    # due sub-ruoli distinti sulla stessa etichetta (caso unico, TileOGame) —
                    # contati singolarmente, non come 1 sola occorrenza, per coincidere col
                    # conteggio di label_classification.md/.json (vedi docs/decisions.md,
                    # riconciliazione 87 vs 83 del 2026-09-28).
                    for sub in entry["ruoli"]:
                        causes[CAUSES[5]].append(
                            f"**{model_id}** — `{r['raw']}`: label '{r['label']}' -> ruolo '{sub['testo']}' "
                            f"su estremo {sub['estremo']}"
                        )

        for a in (r for r in rels if r["kind"] == "assoc_class"):
            causes[CAUSES[6]].append(
                f"**{model_id}** — classe associativa '{a['assoc']}' su {a['a']}-{a['b']}: "
                f"sostituita da {a['a']}--{a['assoc']} e {a['assoc']}--{a['b']} (molteplicita' derivate)"
            )

        for c in rec.get("constraints") or []:
            causes[CAUSES[7]].append(f"**{model_id}** — {c['generalizzazione']}: `{c['vincoli']}`")

        for cname, pc in classes.items():
            if pc.kind == "enum":
                continue
            for i, (attr_name, _attr_type) in enumerate(pc.attributes):
                extra = pc.attribute_extras[i] if i < len(pc.attribute_extras) else {}
                if extra.get("modifiers") or extra.get("default"):
                    causes[CAUSES[8]].append(
                        f"**{model_id}** — `{cname}.{attr_name}`: modificatori={extra.get('modifiers') or []} "
                        f"default={extra.get('default')!r}"
                    )

    lines = [
        "# Diff report — PlantUML sorgente -> JSON Apollon finale",
        "",
        "Generato da `corpus/diff_report.py` (FASE 4, 2026-09-28). Raggruppato per "
        "causa: la prima sezione confronta il PlantUML VERAMENTE originale "
        "(`corpus/raw/`) col PlantUML corretto (`corpus.jsonl.diagram_plantuml`, "
        "dopo `corpus/corrections/<id>.yaml`); tutte le altre confrontano il "
        "PlantUML corretto col JSON Apollon finale, prodotte da "
        "`corpus/apollon_convert.py`.",
        "",
    ]
    for cause in CAUSES:
        items = causes[cause]
        lines.append(f"## {cause} ({len(items)})")
        lines.append("")
        if items:
            lines.extend(f"- {it}" for it in items)
        else:
            lines.append("_Nessuna occorrenza._")
        lines.append("")

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(len(v) for v in causes.values())
    print(f"Scritto: {OUT_PATH} ({total} differenze totali su {len(CAUSES)} categorie)")


if __name__ == "__main__":
    main()
