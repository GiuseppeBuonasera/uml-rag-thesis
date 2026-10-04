"""
Costruisce corpus/processed/corpus.jsonl a partire da corpus/raw/models_original/
(sorgente immutabile, mai scritta da nessuno script — vedi RAW_DIRS) e
corpus/raw/translated_it/ (esercizi tradotti dall'italiano, vedi
docs/decisions.md — Fase 1/2 traduzione studio2025_it).

Ogni cartella <Nome>/ in una delle due directory deve contenere:
  description.md   - traccia testuale dell'esercizio (obbligatorio)
  metadata.txt      - campi "chiave: valore" (name, language, tags, domain, source,
                       citation, contact) (obbligatorio)
  plantuml.txt       - diagramma di riferimento in PlantUML (obbligatorio)
  extramaterial/     - materiale extra facoltativo (ignorato dal manifest)

Le cartelle in corpus/raw/translated_it/ hanno anche file aggiuntivi
(description_it.md, plantuml_it.txt, transcription_notes.md, glossary.json,
render_it.png) non letti da questo script — servono solo per la tracciabilità
della traduzione, vedi corpus/apply_glossary.py e corpus/check_translated.py.

Correzioni di contenuto (FASE 3, 2026-09-28, vedi docs/decisions.md): subito
dopo aver letto plantuml.txt, questo script applica le eventuali correzioni
dichiarate in corpus/corrections/<id>.yaml (corpus/apply_corrections.py) —
refusi di nomi, relazioni duplicate/errate da rimuovere o correggere. Il testo
CORRETTO e' quello che finisce nel campo "diagram_plantuml" di corpus.jsonl;
corpus/raw/models_original/<id>/plantuml.txt NON viene mai toccato. L'elenco
delle correzioni effettivamente applicate (con motivazione) finisce nel campo
"corrections_applied" del record, per tracciabilita' — vuoto se l'esercizio
non ha un file corrections/<id>.yaml.

Esclusioni di paragrafi da description.md (2026-09-29, vedi docs/decisions.md
e corpus/clean_description.py): stesso principio, ma sul testo di
description.md invece che su plantuml.txt — dichiarate in
corpus/description_exclusions/<id>.yaml, tracciate nel campo
"description_exclusions_applied".

Problemi noti (2026-10-01, vedi docs/decisions.md): corpus/known_issues.yaml
associa a un id una lista di codici (KNOWN_ISSUE_CODES), riportata nel campo
"known_issues" del record (lista vuota se l'id non compare) per filtrare gli
esercizi negli esperimenti. Non modifica diagramma ne' descrizione. Codice
sconosciuto o id inesistente -> errore.

Il diagramma target finale è Apollon JSON (vedi docs/decisions.md): questo script
scrive solo il PlantUML originale (diagram_apollon_json resta a None). La conversione
in Apollon JSON è un passo successivo, vedi corpus/apollon_convert.py — va eseguito
dopo questo script (e riscrive corpus.jsonl aggiungendo diagram_apollon_json e
apollon_conversion_warnings).

Split (2026-10-02, vedi docs/decisions.md): con --split debari_test lo script
legge corpus/raw/debari_test/ (i 20 esercizi di De Bari et al., TEST SET tenuto
fuori dal retrieval) e scrive corpus/processed/testset_debari.jsonl, con i campi
extra "split", "debari_number" (1-20, dal prefisso DBNN_ della cartella) e
"debari_title" (titolo originale, campo name di metadata.txt). Hard-fail se un id
compare in entrambi gli split, o se un JSON Apollon e' nella cartella sbagliata.

Uso:
    python corpus/build_manifest.py                       # split corpus (default)
    python corpus/apollon_convert.py
    python corpus/build_manifest.py --split debari_test   # test set De Bari
    python corpus/apollon_convert.py --split debari_test
"""

import json
import re
from pathlib import Path

import yaml

import apply_corrections as ac_corr
import clean_description as cd

RAW_DIRS = [
    # Rinominata da "models" a "models_original" (2026-09-25, cambio fatto
    # direttamente sul filesystem, non da questo script — corpus/raw/* e' fuori da
    # git, quindi git non lo mostra) per segnalare che e' la sorgente immutabile:
    # nessuno script deve MAI scrivere qui, solo leggere. Le correzioni passano dal
    # convertitore (corpus/apollon_convert.py) o da corpus/corrections/, vedi
    # docs/decisions.md.
    Path(__file__).parent / "raw" / "models_original",
    Path(__file__).parent / "raw" / "translated_it",
]
OUT_PATH = Path(__file__).parent / "processed" / "corpus.jsonl"

# Test set De Bari (2026-10-02): mai nel corpus di retrieval, vedi SPLITS e check_split_separation.
DEBARI_RAW_DIR = Path(__file__).parent / "raw" / "debari_test"
DEBARI_OUT_PATH = Path(__file__).parent / "processed" / "testset_debari.jsonl"
DEBARI_ID_RE = re.compile(r"^DB(\d{2})_[A-Z][A-Za-z0-9]*$")

REQUIRED_METADATA_FIELDS = ["name", "language", "tags", "domain", "source", "citation", "contact"]
REQUIRED_FILES = ["description.md", "metadata.txt", "plantuml.txt"]

# Esercizi del corpus usati anche come esempio few-shot statico nel prompt
# (docs/dati/apollon_format_reference/example_*_v4.json). Vanno esclusi dalle query
# di valutazione quando si usa quel prompt come baseline statica, per evitare
# leakage — vedi docs/decisions.md, voce sul Blocco 4 (2026-09-24).
STATIC_EXAMPLE_IDS = {"AirTravel"}

# split -> (cartelle raw, jsonl di uscita, esempi few-shot statici)
SPLITS = {
    "corpus": (RAW_DIRS, OUT_PATH, STATIC_EXAMPLE_IDS),
    "debari_test": ([DEBARI_RAW_DIR], DEBARI_OUT_PATH, set()),
}

# Problemi noti per esercizio, vedi corpus/known_issues.yaml.
KNOWN_ISSUES_PATH = Path(__file__).parent / "known_issues.yaml"
KNOWN_ISSUE_CODES = {
    # il diagramma contiene due modellazioni alternative dello stesso concetto,
    # mantenute entrambe per fedelta' all'immagine (EatAtHome)
    "two_alternative_models",
    # sovrapposizione di dominio con un esempio del prompt statico che e' anche nel corpus di retrieval
    # (test set De Bari es. 6 vs AirTravel, decisione utente STOP B 2026-10-04)
    "domain_overlap_static_example",
}


def validate_known_issues(data: object, known_ids: set[str]) -> dict[str, list]:
    """Valida il contenuto di known_issues.yaml: {id esistente: [voci]}. Una voce e' un codice ammesso
    (stringa, forma storica: EatAtHome) oppure un dizionario con il codice in "tipo" e i dettagli
    misurati (2026-10-04, es. 6 De Bari); il record riporta la voce cosi' com'e'."""
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("known_issues.yaml: atteso un dizionario {id: [codici]}")
    for model_id, codes in data.items():
        if model_id not in known_ids:
            raise ValueError(f"known_issues.yaml: id inesistente nel corpus: {model_id!r}")
        if not isinstance(codes, list) or not codes:
            raise ValueError(f"known_issues.yaml: {model_id}: attesa una lista non vuota di codici")
        bad = [c for c in codes if isinstance(c, dict) and not isinstance(c.get("tipo"), str)]
        if bad:
            raise ValueError(f"known_issues.yaml: {model_id}: voce strutturata senza 'tipo': {bad}")
        tipi = [c["tipo"] if isinstance(c, dict) else c for c in codes]
        unknown = [c for c in tipi if c not in KNOWN_ISSUE_CODES]
        if unknown:
            raise ValueError(f"known_issues.yaml: {model_id}: codici sconosciuti {unknown}")
        if len(set(tipi)) != len(tipi):
            raise ValueError(f"known_issues.yaml: {model_id}: codici duplicati {tipi}")
    return data


# Ambiguita' di lettura dell'immagine (2026-10-03, solo test set De Bari): lista di
# {elemento, letture_alternative, scelta, motivazione} per esercizio, nel campo "ambiguities" del
# record, cosi' in valutazione un elemento ambiguo puo' essere escluso o trattato a parte.
AMBIGUITIES_PATH = Path(__file__).parent / "ambiguities.yaml"
AMBIGUITY_FIELDS = {"elemento", "letture_alternative", "scelta", "motivazione"}


def validate_ambiguities(data: object, known_ids: set[str]) -> dict[str, list[dict]]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("ambiguities.yaml: atteso un dizionario {id: [ambiguita']}")
    for model_id, items in data.items():
        if model_id not in known_ids:
            raise ValueError(f"ambiguities.yaml: id inesistente nel test set: {model_id!r}")
        if not isinstance(items, list) or not items:
            raise ValueError(f"ambiguities.yaml: {model_id}: attesa una lista non vuota")
        for item in items:
            if not isinstance(item, dict) or set(item) != AMBIGUITY_FIELDS:
                raise ValueError(f"ambiguities.yaml: {model_id}: campi attesi {sorted(AMBIGUITY_FIELDS)}, trovati {item}")
            if not isinstance(item["letture_alternative"], list) or not item["letture_alternative"]:
                raise ValueError(f"ambiguities.yaml: {model_id}: letture_alternative deve essere una lista non vuota")
    return data


def load_ambiguities(known_ids: set[str]) -> dict[str, list[dict]]:
    if not AMBIGUITIES_PATH.exists():
        return {}
    return validate_ambiguities(yaml.safe_load(AMBIGUITIES_PATH.read_text(encoding="utf-8")), known_ids)


def load_known_issues(known_ids: set[str]) -> dict[str, list[str]]:
    if not KNOWN_ISSUES_PATH.exists():
        return {}
    data = yaml.safe_load(KNOWN_ISSUES_PATH.read_text(encoding="utf-8"))
    return validate_known_issues(data, known_ids)


def parse_metadata(text: str) -> dict:
    fields = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def count_requirements(description: str) -> int:
    # Le description.md dei modelli sono elenchi di frasi/requisiti, una per riga.
    return len([line for line in description.splitlines() if line.strip()])


def build_record(model_dir: Path, split: str = "corpus") -> dict:
    missing = [f for f in REQUIRED_FILES if not (model_dir / f).exists()]
    if missing:
        raise ValueError(f"{model_dir.name}: file mancanti {missing}")

    description = (model_dir / "description.md").read_text(encoding="utf-8").strip()
    metadata_raw = (model_dir / "metadata.txt").read_text(encoding="utf-8")
    plantuml = (model_dir / "plantuml.txt").read_text(encoding="utf-8").strip()
    metadata = parse_metadata(metadata_raw)

    tags = [t.strip() for t in metadata.get("tags", "").split(",") if t.strip()]

    corrections = ac_corr.load_corrections(model_dir.name)
    plantuml, corrections_applied = ac_corr.apply_corrections(model_dir.name, plantuml, corrections)

    exclusions = cd.load_exclusions(model_dir.name)
    description, description_exclusions_applied = cd.apply_exclusions(model_dir.name, description, exclusions)

    record = {
        "id": model_dir.name,
        "name": metadata.get("name") or model_dir.name,
        "language": metadata.get("language") or None,
        "domain": metadata.get("domain") or None,
        "source": metadata.get("source") or None,
        "citation": metadata.get("citation") or None,
        "contact": metadata.get("contact") or None,
        "tags": tags,
        "translated": "translated_it" in tags,
        "description": description,
        "description_exclusions_applied": description_exclusions_applied,
        "n_requirements": count_requirements(description),
        "diagram_format": "plantuml",
        "diagram_plantuml": plantuml,
        "corrections_applied": corrections_applied,
        "diagram_apollon_json": None,  # TODO: conversione PlantUML -> Apollon JSON
        "has_extramaterial": (model_dir / "extramaterial").is_dir(),
        "raw_dir": str(model_dir.relative_to(Path(__file__).parent.parent)).replace("\\", "/"),
        "used_as_static_example": model_dir.name in SPLITS[split][2],
    }
    if split == "debari_test":
        m = DEBARI_ID_RE.match(model_dir.name)
        if not m:
            raise ValueError(f"{model_dir.name}: id del test set De Bari non nel formato DBNN_<NomePascalCase>")
        record["split"] = "debari_test"
        record["debari_number"] = int(m.group(1))
        record["debari_title"] = metadata.get("name") or None
        record.update(debari_difficulty()[record["debari_number"]])
    return record


DEBARI_XLSX = Path(__file__).parent.parent / "docs" / "dati" / "debari" / "Analysis.xlsx"
_DEBARI_DIFFICULTY: dict[int, dict] | None = None


def debari_difficulty() -> dict[int, dict]:
    """Foglio "Estimated Difficulty" di Analysis.xlsx (valori in cache, data_only: le somme tipo
    '=10+7' sono gia' valutate): per esercizio i tre conteggi di De Bari et al. e la media delle tre
    stime di difficolta' ED 1-3 (1 = facile, 5 = difficile). Servono all'analisi finale; i conteggi
    sono quelli dell'xlsx, NON ricalcolati sul ground truth (il confronto e' in check_debari.py)."""
    global _DEBARI_DIFFICULTY
    if _DEBARI_DIFFICULTY is None:
        import openpyxl

        ws = openpyxl.load_workbook(DEBARI_XLSX, data_only=True)["Estimated Difficulty"]
        rows = [r for r in ws.iter_rows(values_only=True) if isinstance(r[1], (int, float))]
        _DEBARI_DIFFICULTY = {
            int(r[1]): {
                "debari_xlsx_counts": {"classes": int(r[2]), "attributes_operations": int(r[3]),
                                       "associations": int(r[4])},
                "debari_ed": [r[5], r[6], r[7]],
                "debari_ed_avg": round((r[5] + r[6] + r[7]) / 3, 4),
            }
            for r in rows
        }
        if sorted(_DEBARI_DIFFICULTY) != list(range(1, 21)):
            raise ValueError(f"Estimated Difficulty: attesi esercizi 1-20, trovati {sorted(_DEBARI_DIFFICULTY)}")
    return _DEBARI_DIFFICULTY


def list_model_dirs(raw_dirs: list[Path], required: bool = True) -> list[Path]:
    model_dirs: list[Path] = []
    for raw_dir in raw_dirs:
        if not raw_dir.is_dir():
            if required:
                raise SystemExit(f"Cartella non trovata: {raw_dir}")
            continue
        # le cartelle che iniziano con "_" (es. _images/) non sono esercizi:
        # sono materiale condiviso (immagini sorgente per la trascrizione)
        model_dirs.extend(
            sorted(p for p in raw_dir.iterdir() if p.is_dir() and not p.name.startswith("_"))
        )
    return model_dirs


def split_ids(split: str) -> set[str]:
    """Id di uno split: cartelle raw + record del jsonl gia' scritto (se esiste)."""
    raw_dirs, out_path, _ = SPLITS[split]
    ids = {d.name for d in list_model_dirs(raw_dirs, required=False)}
    if out_path.exists():
        ids |= {json.loads(l)["id"] for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip()}
    return ids


def check_split_separation(split: str, records: list[dict], other_ids: set[str]) -> None:
    """Hard-fail se lo split si sovrappone all'altro: test set De Bari mai nel corpus, e viceversa."""
    overlap = sorted({r["id"] for r in records} & other_ids)
    if overlap:
        raise AssertionError(f"split {split}: id presenti anche nell'altro split: {overlap}")
    if split == "corpus":
        leaked = sorted(r["id"] for r in records if DEBARI_ID_RE.match(r["id"])
                        or "debari_test" in r["tags"] or r.get("split") == "debari_test")
        if leaked:
            raise AssertionError(f"esercizi del test set De Bari nel corpus di retrieval: {leaked}")
    else:
        bad = sorted(r["id"] for r in records if r.get("split") != split or not DEBARI_ID_RE.match(r["id"]))
        if bad:
            raise AssertionError(f"record del test set De Bari senza split/id corretti: {bad}")


def check_apollon_dir_separation(corpus_out_dir: Path, debari_out_dir: Path) -> None:
    """Hard-fail se un JSON Apollon del test set e' nella cartella del corpus, o viceversa."""
    corpus_files = {p.stem for p in corpus_out_dir.glob("*.json")}
    debari_files = {p.stem for p in debari_out_dir.glob("*.json")}
    wrong = sorted(f for f in corpus_files if DEBARI_ID_RE.match(f)) + sorted(
        f for f in debari_files if not DEBARI_ID_RE.match(f))
    overlap = sorted(corpus_files & debari_files)
    if wrong or overlap:
        raise AssertionError(f"JSON Apollon nello split sbagliato: {wrong}; in entrambe le cartelle: {overlap}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="raw -> jsonl per uno split.")
    parser.add_argument("--split", choices=sorted(SPLITS), default="corpus",
                        help="corpus (default, corpus di retrieval) o debari_test (test set De Bari)")
    split = parser.parse_args().split
    raw_dirs, out_path, _ = SPLITS[split]

    model_dirs = list_model_dirs(raw_dirs)
    if split == "debari_test":
        # trascrizione completata (FASE 6, 2026-10-04): il test set deve avere tutti e 20 gli esercizi
        # trascritti; prima (FASE 3, trascrizione a gruppi) quelli senza plantuml.txt venivano saltati
        pending = [d.name for d in model_dirs if not (d / "plantuml.txt").exists()]
        numbers = sorted(int(DEBARI_ID_RE.match(d.name).group(1)) for d in model_dirs if DEBARI_ID_RE.match(d.name))
        if pending or numbers != list(range(1, 21)):
            raise SystemExit(f"test set De Bari incompleto: esercizi {numbers}, senza plantuml.txt {pending}")
    records = [build_record(d, split) for d in model_dirs]

    other = "debari_test" if split == "corpus" else "corpus"
    check_split_separation(split, records, split_ids(other))
    processed = Path(__file__).parent / "processed"
    check_apollon_dir_separation(processed / "apollon", processed / "apollon_debari")

    # known_issues.yaml copre entrambi gli split: gli id si validano sull'unione
    known_issues = load_known_issues(split_ids(other) | {r["id"] for r in records})
    for record in records:
        record["known_issues"] = list(known_issues.get(record["id"], []))
    if split == "debari_test":
        ambiguities = load_ambiguities({d.name for d in list_model_dirs(raw_dirs)})
        for record in records:
            record["ambiguities"] = list(ambiguities.get(record["id"], []))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    verify(records, split)
    print(f"Scritti {len(records)} record in {out_path}")


def verify(records: list[dict], split: str = "corpus") -> None:
    """Self-check minimo: campi obbligatori popolati, id univoci, nessun testo vuoto."""
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids)), "id duplicati nel corpus"

    missing_domain = [r["id"] for r in records if not r["domain"]]
    missing_source = [r["id"] for r in records if not r["source"]]
    empty_description = [r["id"] for r in records if not r["description"]]
    empty_diagram = [r["id"] for r in records if not r["diagram_plantuml"]]

    if missing_domain:
        print(f"[warn] domain mancante per: {missing_domain}")
    if missing_source:
        print(f"[warn] source mancante per: {missing_source}")
    if empty_description:
        raise AssertionError(f"description vuota per: {empty_description}")
    if empty_diagram:
        raise AssertionError(f"plantuml vuoto per: {empty_diagram}")

    domains = sorted(set(r["domain"] for r in records if r["domain"]))
    print(f"Domini rappresentati ({len(domains)}): {domains}")

    static_example_ids = sorted(r["id"] for r in records if r["used_as_static_example"])
    expected_static = SPLITS[split][2]
    assert set(static_example_ids) == expected_static, (
        f"used_as_static_example non coincide con STATIC_EXAMPLE_IDS: "
        f"trovato {static_example_ids}, atteso {sorted(expected_static)}"
    )
    print(f"Esempi few-shot statici (used_as_static_example=true): {static_example_ids}")

    translated_ids = sorted(r["id"] for r in records if r["translated"])
    print(f"Esercizi tradotti (translated=true, tag 'translated_it'): {translated_ids}")

    n_corrections = sum(len(r["corrections_applied"]) for r in records)
    corrected_ids = sorted(r["id"] for r in records if r["corrections_applied"])
    print(f"Correzioni di contenuto applicate (corpus/corrections/*.yaml): {n_corrections} su {corrected_ids}")

    n_exclusions = sum(len(r["description_exclusions_applied"]) for r in records)
    excluded_ids = sorted(r["id"] for r in records if r["description_exclusions_applied"])
    print(f"Paragrafi esclusi da description.md (corpus/description_exclusions/*.yaml): {n_exclusions} su {excluded_ids}")

    issues = {r["id"]: r["known_issues"] for r in records if r["known_issues"]}
    print(f"Problemi noti (corpus/known_issues.yaml, campo 'known_issues'): {issues}")


if __name__ == "__main__":
    main()
