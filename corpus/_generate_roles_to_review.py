"""
Script una tantum, sola lettura: estrae da corpus/label_classification.md (in
realta' dalla stessa struttura dati, CLASSIFICATION, per non ridigitare 87 righe)
le righe "ruolo"/"ruolo_doppio" che rientrano in almeno uno di 5 casi (2026-09-28,
richiesta utente), e le scrive in corpus/roles_to_review.md. Non modifica
label_classification.md ne' altri file esistenti.

Criteri (una riga puo' avere piu' lettere):
A. il nome del ruolo non corrisponde (plurale/camelCase compresi) al nome della
   classe dell'estremo scelto — confronto per insiemi di parole normalizzate
   (camelCase separato, minuscolo, 's' finale tolta se la parola ha piu' di 3
   lettere), non per uguaglianza letterale: "specialOffers"~"SpecialOffer" conta
   come corrispondenza (escluso), "recordedReadings"~"SensorReading" no (incluso,
   condivide solo "reading").
B. il ruolo e' sull'estremo di PARTENZA (coda, non punta della freccia) di una
   relazione unidirezionale (op in apollon_convert.DIRECTED_OPS).
C. auto-associazione (stessa classe a entrambi gli estremi).
D. esistono piu' relazioni binarie tra la stessa coppia di classi (non ordinata)
   in quell'esercizio.
E. il ruolo e' su un'aggregazione o composizione (op in AGGREGATION_OPS/
   COMPOSITION_OPS).

Per ogni riga inclusa: lettura, riga di plantuml.txt, frase di description.md piu'
pertinente (punteggio per sovrapposizione di parole col ruolo/le due classi;
"nessuna frase pertinente trovata" se punteggio zero per tutte le frasi — non
inventata).

Uso:
    python corpus/_generate_roles_to_review.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import apollon_convert as ac

spec = importlib.util.spec_from_file_location("gen_label", Path(__file__).parent / "_generate_label_classification.py")
gen_label = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_label)
CLASSIFICATION = gen_label.CLASSIFICATION

CORPUS_JSONL = Path(__file__).parent / "processed" / "corpus.jsonl"


def normwords(s: str) -> set[str]:
    s = re.sub(r"(?<!^)(?=[A-Z])", " ", s)
    s = re.sub(r"[^A-Za-z0-9]+", " ", s)
    words = [w.lower() for w in s.split()]
    return {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words}


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def most_relevant_sentence(description: str, role_text: str, endpoint: str, other: str) -> str:
    """Alcuni description.md hanno una riga per requisito (una frase), altri un
    unico paragrafo con piu' frasi (es. BuildingManagement) — si spezza anche per
    punteggiatura di fine frase, non solo per newline, per non restituire un intero
    paragrafo quando basterebbe una frase."""
    keywords = normwords(role_text) | normwords(endpoint) | normwords(other)
    candidates = []
    for line in description.splitlines():
        line = line.strip()
        if line:
            candidates.extend(s.strip() for s in SENTENCE_SPLIT_RE.split(line) if s.strip())

    best_sentence, best_score = None, 0
    for sentence in candidates:
        score = len(keywords & normwords(sentence))
        if score > best_score:
            best_score, best_sentence = score, sentence
    if best_sentence is None:
        return "(nessuna frase pertinente trovata in description.md)"
    return best_sentence


def lettura(endpoint: str, role_text: str, source: str, target: str) -> str:
    other = target if endpoint == source else source
    return f"{endpoint} è il/la {role_text} di {other}"


def main() -> None:
    records = {r["id"]: r for r in (json.loads(l) for l in CORPUS_JSONL.read_text(encoding="utf-8").splitlines() if l.strip())}

    included = []
    excluded_count = 0

    for rec_id, rec in records.items():
        if not rec.get("diagram_plantuml"):
            continue
        classes, rels, warn, unsup = ac.parse_plantuml(rec["diagram_plantuml"])
        if unsup:
            continue
        binary = [r for r in rels if r["kind"] == "binary"]
        pair_count: dict[frozenset, int] = {}
        for r in binary:
            key = frozenset([r["source"], r["target"]])
            pair_count[key] = pair_count.get(key, 0) + 1

        for r in binary:
            if not r["label"]:
                continue
            key5 = (rec_id, r["source"], r["op"], r["target"], r["label"])
            if key5 not in CLASSIFICATION:
                continue
            classification, endpoint_or_list, _motivation = CLASSIFICATION[key5]
            if classification == "ruolo":
                subs = [{"testo": r["label"], "estremo": endpoint_or_list}]
            elif classification == "ruolo_doppio":
                subs = endpoint_or_list
            else:
                continue

            for sub in subs:
                role_text, endpoint = sub["testo"], sub["estremo"]
                other = r["target"] if endpoint == r["source"] else r["source"]

                crit = []
                if normwords(role_text) != normwords(endpoint):
                    crit.append("A")
                if r["op"] in ac.DIRECTED_OPS:
                    tail = r["source"] if r["op"] == "-->" else r["target"]
                    if endpoint == tail:
                        crit.append("B")
                if r["source"] == r["target"]:
                    crit.append("C")
                if pair_count[frozenset([r["source"], r["target"]])] > 1:
                    crit.append("D")
                if r["op"] in ac.AGGREGATION_OPS or r["op"] in ac.COMPOSITION_OPS:
                    crit.append("E")

                if not crit:
                    excluded_count += 1
                    continue

                included.append(
                    {
                        "esercizio": rec_id,
                        "raw": r["raw"],
                        "role_text": role_text,
                        "endpoint": endpoint,
                        "other": other,
                        "criteri": crit,
                        "lettura": lettura(endpoint, role_text, r["source"], r["target"]),
                        "frase": most_relevant_sentence(rec["description"], role_text, endpoint, other),
                    }
                )

    lines = [
        "# Righe \"ruolo\" da rivedere — criteri A-E",
        "",
        "Estratte (sola lettura, nessuna modifica a label_classification.md) da "
        "corpus/_generate_roles_to_review.py. Criteri: **A** nome ruolo non "
        "corrisponde (plurale/camelCase compresi) al nome della classe "
        "dell'estremo; **B** ruolo sull'estremo di partenza di una freccia "
        "unidirezionale; **C** auto-associazione; **D** più relazioni tra la "
        "stessa coppia di classi; **E** ruolo su aggregazione/composizione.",
        "",
        "| Esercizio | Lettura | Criteri | Riga plantuml.txt | Frase description.md più pertinente |",
        "|---|---|---|---|---|",
    ]
    for x in included:
        raw_escaped = x["raw"].replace("|", "\\|")
        frase_escaped = x["frase"].replace("|", "\\|")
        lines.append(
            f"| {x['esercizio']} | {x['lettura']} | {','.join(x['criteri'])} | `{raw_escaped}` | {frase_escaped} |"
        )

    lines.append("")
    lines.append("## Totali")
    lines.append(f"- Righe \"ruolo\"/\"ruolo_doppio\" esaminate: {len(included) + excluded_count}")
    lines.append(f"- Incluse (almeno un criterio A-E): {len(included)}")
    lines.append(
        f"- Escluse perché ovvie (nome del ruolo = nome della classe dell'estremo, "
        f"nessun altro criterio applicabile): {excluded_count}"
    )

    out_path = Path("corpus/roles_to_review.md")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Scritto: {out_path}")
    print(f"Incluse: {len(included)}, escluse (ovvie): {excluded_count}")


if __name__ == "__main__":
    main()
