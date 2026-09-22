"""
Costruisce corpus/processed/corpus.jsonl a partire da corpus/raw/models/.

Ogni cartella in corpus/raw/models/<Nome>/ deve contenere:
  description.md   - traccia testuale dell'esercizio (obbligatorio)
  metadata.txt      - campi "chiave: valore" (name, language, tags, domain, source,
                       citation, contact) (obbligatorio)
  plantuml.txt       - diagramma di riferimento in PlantUML (obbligatorio)
  extramaterial/     - materiale extra facoltativo (ignorato dal manifest)

Il diagramma target finale è Apollon JSON (vedi docs/decisions.md), non ancora
disponibile per questi 45 esercizi: il campo diagram_apollon_json resta a None finché
non esiste un convertitore PlantUML -> Apollon o un'annotazione manuale. Non viene
inventato/generato automaticamente qui.

Uso:
    python corpus/build_manifest.py
"""

import json
from pathlib import Path

RAW_MODELS_DIR = Path(__file__).parent / "raw" / "models"
OUT_PATH = Path(__file__).parent / "processed" / "corpus.jsonl"

REQUIRED_METADATA_FIELDS = ["name", "language", "tags", "domain", "source", "citation", "contact"]
REQUIRED_FILES = ["description.md", "metadata.txt", "plantuml.txt"]


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


def build_record(model_dir: Path) -> dict:
    missing = [f for f in REQUIRED_FILES if not (model_dir / f).exists()]
    if missing:
        raise ValueError(f"{model_dir.name}: file mancanti {missing}")

    description = (model_dir / "description.md").read_text(encoding="utf-8").strip()
    metadata_raw = (model_dir / "metadata.txt").read_text(encoding="utf-8")
    plantuml = (model_dir / "plantuml.txt").read_text(encoding="utf-8").strip()
    metadata = parse_metadata(metadata_raw)

    tags = [t.strip() for t in metadata.get("tags", "").split(",") if t.strip()]

    return {
        "id": model_dir.name,
        "name": metadata.get("name") or model_dir.name,
        "language": metadata.get("language") or None,
        "domain": metadata.get("domain") or None,
        "source": metadata.get("source") or None,
        "citation": metadata.get("citation") or None,
        "contact": metadata.get("contact") or None,
        "tags": tags,
        "description": description,
        "n_requirements": count_requirements(description),
        "diagram_format": "plantuml",
        "diagram_plantuml": plantuml,
        "diagram_apollon_json": None,  # TODO: conversione PlantUML -> Apollon JSON
        "has_extramaterial": (model_dir / "extramaterial").is_dir(),
        "raw_dir": str(model_dir.relative_to(Path(__file__).parent.parent)).replace("\\", "/"),
    }


def main() -> None:
    if not RAW_MODELS_DIR.is_dir():
        raise SystemExit(f"Cartella non trovata: {RAW_MODELS_DIR}")

    model_dirs = sorted(p for p in RAW_MODELS_DIR.iterdir() if p.is_dir())
    records = [build_record(d) for d in model_dirs]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    verify(records)
    print(f"Scritti {len(records)} record in {OUT_PATH}")


def verify(records: list[dict]) -> None:
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


if __name__ == "__main__":
    main()
