"""
Ruoli degli 80 esercizi (2026-10-10, voci 113 e 117): genera corpus/roles.yaml, una riga per esercizio con la fonte e
il ruolo. Nessuna chiamata a un LLM; legge solo i file del Passo 1 e i config che definiscono gli esercizi gia' usati.

- source: golden (Golden UML Modelset, corpus/raw/models_original/), translated_it (corpus/raw/translated_it/),
          debari (test set De Bari, corpus/raw/debari_test/);
- role:   sviluppo    = gli esercizi gia' usati come QUERY di generazione (i 20 dell'insieme di sviluppo, voce 92,
                        experiments/configs/dev_k.yaml, e i 6 dei piloti, experiments/configs/pilot_temperature.yaml e
                        pilot2_formats.yaml): su di loro sono state prese decisioni;
          valutazione = tutti gli altri (valutazione principale del Passo 3b).
Il file generato si congela con il tag evalset-v1: dopo aver visto risultati di generazione sugli esercizi di valutazione
i ruoli non si cambiano. experiments/run_experiment.py rifiuta una run reale che usi come query un esercizio di
valutazione, salvo i config del Passo 3b marcati `passo: 3b`.

Uso:
    python corpus/build_roles.py            # scrive corpus/roles.yaml
    python corpus/build_roles.py --check    # verifica che corpus/roles.yaml sia quello che lo script genererebbe
"""

from __future__ import annotations

import sys

import yaml

import paths

CONFIGS = paths.ROOT / "experiments" / "configs"
DEV_CONFIG = CONFIGS / "dev_k.yaml"
PILOT_CONFIGS = (CONFIGS / "pilot_temperature.yaml", CONFIGS / "pilot2_formats.yaml")
EXPECTED = {"sviluppo": 26, "valutazione": 54}


def used_as_query() -> set[str]:
    ids = set(yaml.safe_load(DEV_CONFIG.read_text(encoding="utf-8"))["query_ids"])
    for cfg in PILOT_CONFIGS:
        ids |= set(yaml.safe_load(cfg.read_text(encoding="utf-8"))["query_ids"])
    return ids


def source_of(record: dict, split: str) -> str:
    if split == "debari_test":
        return "debari"
    return "translated_it" if "translated_it" in (record.get("tags") or []) else "golden"


def build() -> str:
    used = used_as_query()
    rows = []
    for split in ("corpus", "debari_test"):
        for r in paths.read_jsonl(paths.SPLITS[split][1]):
            rows.append({"id": r["id"], "source": source_of(r, split),
                         "role": "sviluppo" if r["id"] in used else "valutazione"})
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)) or not used <= set(ids):
        raise SystemExit(f"id ripetuti o query di sviluppo sconosciute: {sorted(used - set(ids))}")
    counts = {k: sum(r["role"] == k for r in rows) for k in EXPECTED}
    if counts != EXPECTED:
        raise SystemExit(f"conteggi dei ruoli {counts} diversi da quelli attesi {EXPECTED}")
    header = ("# Ruoli degli 80 esercizi (voci 113 e 117), GENERATO da corpus/build_roles.py: non modificare a mano.\n"
              "# sviluppo = gia' usati come query di generazione (20 di sviluppo + 6 dei piloti); valutazione = gli altri.\n"
              "# Congelato con il tag evalset-v1.\n")
    return header + yaml.safe_dump(rows, allow_unicode=True, sort_keys=False, width=120)


def main() -> None:
    text = build()
    if "--check" in sys.argv:
        if paths.ROLES_YAML.read_text(encoding="utf-8") != text:
            raise SystemExit(f"{paths.ROLES_YAML} diverso da quello generato: rigenerarlo (e motivarlo) o verificare")
        print(f"{paths.ROLES_YAML.name}: aggiornato")
        return
    paths.ROLES_YAML.write_text(text, encoding="utf-8", newline="\n")
    rows = yaml.safe_load(text)
    for role in EXPECTED:
        by_source = {s: sum(r["role"] == role and r["source"] == s for r in rows)
                     for s in ("golden", "translated_it", "debari")}
        print(f"{role}: {sum(by_source.values())} {by_source}")
    print(f"Scritto: {paths.ROLES_YAML}")


if __name__ == "__main__":
    main()
