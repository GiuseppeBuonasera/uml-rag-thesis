"""
Genera corpus/label_classification.md e corpus/label_classification.json (nato come script
una tantum nella FASE 2, 2026-09-25; dal test set De Bari e' un passo permanente della
pipeline e legge entrambi gli split; rinominato da _generate_label_classification.py il
2026-10-04). Le voci di CLASSIFICATION si aggiungono solo dopo la conferma dell'utente; il
convertitore legge il json, non questo script.

Ogni riga: (esercizio, relazione, testo_etichetta, classificazione, estremo
proposto, lettura, motivazione). classificazione in {associazione, ruolo, vincolo,
qualificatore, dubbio}.
- "vincolo": testo come "{total; disjoint}" non e' un'etichetta di relazione, e' un
  vincolo UML su un insieme di generalizzazione — dal 2026-09-25 estratto
  automaticamente da corpus/apollon_convert.py::extract_generalization_constraints
  nel campo "constraints" di corpus.jsonl, mai lasciato nell'edge (decisione utente,
  STOP 1).
- "qualificatore": categoria RISERVATA MA ATTUALMENTE INUTILIZZATA (0 voci,
  dal 2026-09-29) — usata fino ad allora per BuildingManagement id/username,
  letti come un "qualifier" UML (attributo che discrimina l'accesso lungo
  l'associazione, es. WebPortal[id] -> Entry). Riclassificati come "ruolo"
  (decisione utente, 2026-09-29): non serviva una lettura UML cosi'
  specifica — "id"/"username" sono semplicemente il nome della proprieta' di
  navigazione, stessa convenzione di "profilePicture"/"wheel", quindi vanno
  in sourceRole/targetRole come ogni altro ruolo. La categoria resta
  documentata (non rimossa dal convertitore) per un futuro caso reale di
  qualifier che non si presti alla stessa lettura.
- "ruolo" ha una colonna aggiuntiva "lettura": una frase
  "<Classe dell'estremo scelto> e' il/la <ruolo> di <altra classe>", per permettere
  la verifica dell'estremo scelto senza dover rileggere ogni riga PlantUML.
- "ruolo_doppio" (caso unico, TileOGame "connections/tiles", decisione utente
  2026-09-27): un'etichetta puo', in casi eccezionali, impacchettare DUE nomi di
  ruolo distinti (uno per estremo) invece di uno solo. Il formato lo rappresenta
  come lista di sotto-assegnazioni {testo, estremo}, invece di forzare un singolo
  (estremo, testo) come per "ruolo" — non e' una regola generale sul carattere '/',
  e' il dato specifico di questa singola relazione.
"""

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import apollon_convert as ac
import paths  # percorsi condivisi (voce 116)

# (id, source, op, target, label) -> (classificazione, estremo_proposto, motivazione)
LABEL_CLASSIFICATION_YAML = Path(__file__).parent / "label_classification.yaml"


def load_classification(path: Path = LABEL_CLASSIFICATION_YAML) -> dict:
    """(id, source, op, target, label) -> (classificazione, estremo_proposto, motivazione), dai DATI di
    label_classification.yaml (voce 116; prima dizionario CLASSIFICATION in questo file), nello stesso ordine."""
    entries = yaml.safe_load(path.read_text(encoding="utf-8"))
    out = {}
    for e in entries:
        key = (e["esercizio"], e["sorgente"], e["operatore"], e["destinazione"], e["etichetta"])
        if key in out:
            raise ValueError(f"{path.name}: voce ripetuta {key}")
        out[key] = (e["classificazione"], e["estremo"], e["motivazione"])
    return out


CLASSIFICATION = load_classification()


def resolve_endpoint_name(estremo: str, src: str, tgt: str) -> str:
    """'estremo' e' di norma un nome di classe; per le auto-relazioni (dove il nome
    non basta a disambiguare le due occorrenze) e' invece la posizione letterale
    'source'/'target' nella riga PlantUML originale. Ritorna sempre il nome di
    classe effettivo, per la visualizzazione in label_classification.md."""
    if estremo in ("source", "target"):
        return src if estremo == "source" else tgt
    return estremo


def resolve_position(estremo: str, src: str, tgt: str) -> str:
    """Inverso di resolve_endpoint_name: da 'estremo' (nome di classe o gia'
    posizione) alla posizione 'source'/'target' — quella che il convertitore usa
    davvero per scegliere source_role vs target_role sulla relazione PARSATA (prima
    dello scambio di relationship_kind)."""
    if estremo in ("source", "target"):
        return estremo
    if estremo == src:
        return "source"
    if estremo == tgt:
        return "target"
    raise ValueError(f"estremo {estremo!r} non corrisponde ne' a source={src!r} ne' a target={tgt!r}")


def lettura_ruolo(estremo: str, role_text: str, src: str, tgt: str) -> str:
    endpoint_name = resolve_endpoint_name(estremo, src, tgt)
    altra_classe = tgt if endpoint_name == src else src
    return f"{endpoint_name} è il/la {role_text} di {altra_classe}"


def main() -> None:
    # percorsi indipendenti dalla cartella da cui si lancia lo script (prima erano relativi alla radice, voce 116)
    corpus = paths.read_jsonl(paths.CORPUS_JSONL)
    # test set De Bari (2026-10-03): stesse regole di classificazione, stesso file json
    # (gli id DBNN_ non collidono con il corpus, vedi build_manifest.check_split_separation)
    if paths.TESTSET_JSONL.exists():
        corpus += paths.read_jsonl(paths.TESTSET_JSONL)
    rows = []
    for rec in corpus:
        if not rec.get("diagram_plantuml"):
            continue
        classes, rels, warn, unsup = ac.parse_plantuml(rec["diagram_plantuml"])
        if unsup:
            continue
        for r in rels:
            if r["kind"] == "binary" and r["label"]:
                rows.append((rec["id"], r["source"], r["op"], r["target"], r["label"], r["raw"]))

    missing = [row for row in rows if row[:5] not in CLASSIFICATION]
    if missing:
        print(f"ATTENZIONE: {len(missing)} righe non classificate:")
        for row in missing:
            print(" ", row)
        raise SystemExit(1)

    md_lines = [
        "# Classificazione delle etichette — associazione, ruolo o vincolo",
        "",
        f"Generata da `corpus/generate_label_classification.py` da tutte le "
        f"{len(rows)} etichette non vuote (`: testo`) trovate nelle relazioni binarie "
        "dei 45 esercizi convertibili (44 originali + CourseManagement).",
        "",
        "Categorie: **associazione** (verbo/descrizione del legame, resta in "
        "`label`), **ruolo** (nome di come si chiama una classe in quella "
        "relazione, va in `sourceRole`/`targetRole` sull'estremo indicato — "
        "colonna \"Lettura\" per verificare l'estremo), **vincolo** (testo di "
        "vincolo UML su una generalizzazione, es. `{disjoint,complete}` — non "
        "e' un'etichetta di relazione: dal 2026-09-25 estratto automaticamente "
        "nel campo `constraints` di corpus.jsonl, mai lasciato nell'edge, vedi "
        "`corpus/apollon_convert.py::extract_generalization_constraints`), "
        "**qualificatore** (verosimilmente un qualifier UML che Apollon non "
        "supporta — resta in `label` per mancanza di un posto migliore), "
        "**ruolo_doppio** (caso unico, TileOGame: un'etichetta con DUE nomi di "
        "ruolo distinti, uno per estremo — espansa in due righe qui sotto), "
        "**dubbio** (nessuna classificazione proposta, in attesa dell'utente).",
        "",
        "| Esercizio | Relazione (sorgente) | Etichetta | Classificazione | Estremo proposto | Lettura | Motivazione |",
        "|---|---|---|---|---|---|---|",
    ]
    counts = {"associazione": 0, "ruolo": 0, "vincolo": 0, "qualificatore": 0, "ruolo_doppio_righe": 0, "dubbio": 0}
    n_labels_originali = len(rows)
    json_entries = []

    for row in rows:
        eid, src, op, tgt, label, raw = row
        classification, endpoint_or_list, motivation = CLASSIFICATION[row[:5]]
        raw_escaped = raw.replace("|", "\\|")
        entry = {"esercizio": eid, "source": src, "op": op, "target": tgt, "label": label, "tipo": classification}

        if classification == "ruolo_doppio":
            entry["ruoli"] = [
                {"estremo": resolve_position(sub["estremo"], src, tgt), "testo": sub["testo"]}
                for sub in endpoint_or_list
            ]
            for sub in endpoint_or_list:
                counts["ruolo"] += 1
                counts["ruolo_doppio_righe"] += 1
                lettura = lettura_ruolo(sub["estremo"], sub["testo"], src, tgt)
                md_lines.append(
                    f"| {eid} | `{raw_escaped}` | {sub['testo']} (da '{label}') | ruolo | "
                    f"{resolve_endpoint_name(sub['estremo'], src, tgt)} | {lettura} | {motivation} |"
                )
        else:
            counts[classification] += 1
            if classification == "ruolo":
                # normalmente il testo del ruolo e' l'etichetta stessa (endpoint_or_list
                # e' solo l'estremo, una stringa); un dict {"estremo","testo"} permette
                # un testo diverso dall'etichetta originale — caso Louvre 'hasCoach' ->
                # ruolo 'coach' (2026-09-29): il nome del ruolo e' il sostantivo, non la
                # frase verbale usata come etichetta della relazione.
                if isinstance(endpoint_or_list, dict):
                    estremo_raw, ruolo_testo = endpoint_or_list["estremo"], endpoint_or_list["testo"]
                else:
                    estremo_raw, ruolo_testo = endpoint_or_list, label
                entry["estremo"] = resolve_position(estremo_raw, src, tgt)
                entry["testo"] = ruolo_testo
                endpoint_str = resolve_endpoint_name(estremo_raw, src, tgt)
                lettura = lettura_ruolo(estremo_raw, ruolo_testo, src, tgt)
            else:
                endpoint_str, lettura = "—", "—"
            md_lines.append(
                f"| {eid} | `{raw_escaped}` | {label} | {classification} | {endpoint_str} | {lettura} | {motivation} |"
            )

        json_entries.append(entry)

    md_lines.append("")
    md_lines.append("## Totali")
    md_lines.append(
        f"- Etichette originali nel PlantUML sorgente: {n_labels_originali} "
        f"(1 delle quali, TileOGame `connections/tiles`, sdoppiata in 2 righe di "
        f"ruolo distinte — {n_labels_originali - 1 + counts['ruolo_doppio_righe']} righe totali in tabella)"
    )
    for k in ("associazione", "ruolo", "vincolo", "qualificatore", "dubbio"):
        md_lines.append(f"- {k}: {counts[k]}")

    md_path = paths.CORPUS_DIR / "label_classification.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Scritto: {md_path}")
    print(counts)

    json_path = paths.CORPUS_DIR / "label_classification.json"
    json_path.write_text(json.dumps(json_entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scritto: {json_path} ({len(json_entries)} voci)")


if __name__ == "__main__":
    main()
