# UML RAG Thesis

Generazione di diagrammi delle classi UML (formato **Apollon JSON v4**) con un LLM, in cui gli esempi few-shot del
prompt sono **recuperati dinamicamente** (RAG: keyword, dense, hybrid) da un corpus di coppie
(descrizione dell'esercizio, diagramma di riferimento), invece di essere esempi statici. La valutazione usa i 20
esercizi di De Bari et al. come test set.

- Contesto completo (obiettivo, ipotesi, fasi, riferimenti, convenzioni): [`CLAUDE.md`](./CLAUDE.md)
- Stato attuale, comandi, regole e domande aperte: [`docs/STATUS.md`](./docs/STATUS.md)
- Cronologia delle decisioni: [`docs/decisions.md`](./docs/decisions.md)

## Struttura
```
corpus/                 pipeline di costruzione del corpus e del test set (vedi corpus/README.md)
  raw/                  sorgenti: models_original/ (45), translated_it/ (15, non versionata), debari_test/ (20)
  processed/            corpus.jsonl, testset_debari.jsonl, apollon/, apollon_debari/
  corrections/          correzioni di contenuto per esercizio
  description_exclusions/
retrieval/              Passo 2: BM25 congelato (config_bm25.yaml), baseline random, analisi e test;
                        dense / hybrid ancora da implementare
generation/             Passo 3a: prompt (template v4 a blocchi), client LLM (LM Studio locale, mock, cache),
                        post-processing con validazione L0-L4, controllo di sanità e test
experiments/            runner degli esperimenti (dry run, ripresa), configs/, smoke test manuale di LM Studio
evaluation/             metriche (da implementare) + schema Apollon v4 (uml-model-4.schema.json)
data/results/           output sperimentali (ignorati da git, tranne config/summary/CSV delle run in retrieval/);
                        generazione in data/results/generation/
docs/
  STATUS.md, decisions.md
  dati/                 materiale di riferimento: debari/, studio2025_it/, apollon_format_reference/
  archivio/             script e documenti conclusi, conservati per tracciabilità
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate      # su Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Il render dei PlantUML usa `.tools/plantuml-old.jar` (Java 8, non versionato). L'ordine dei comandi della pipeline
è in [`corpus/README.md`](./corpus/README.md) e in `docs/STATUS.md`.

Gli esperimenti di generazione usano modelli locali tramite [LM Studio](https://lmstudio.ai) (server con API
compatibile OpenAI, default `http://localhost:1234/v1`, nessuna chiave API). Prima di una run reale:
`python experiments/smoke_lmstudio.py --list-models`, poi `--model <id>`. Le run reali (Passo 3b) sono bloccate in
attesa delle risposte dei relatori (domande in `docs/STATUS.md`).
