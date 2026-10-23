# UML RAG Thesis

Generazione di diagrammi delle classi UML (formato **Apollon JSON v4**) con un LLM, in cui gli esempi few-shot del
prompt sono **recuperati dinamicamente** (RAG: keyword, dense, hybrid) da un corpus di coppie
(descrizione dell'esercizio, diagramma di riferimento), invece di essere esempi statici.

- Contesto completo (obiettivo, ipotesi, fasi, riferimenti, convenzioni): [`CLAUDE.md`](./CLAUDE.md)
- Stato attuale, comandi, regole e prossimi passi: [`docs/STATUS.md`](./docs/STATUS.md)
- Cronologia delle decisioni: [`docs/decisions.md`](./docs/decisions.md)
- **Risultati raccolti e riassunto delle valutazioni**: [`results/README.md`](./results/README.md) e
  [`results/README_valutazioni.md`](./results/README_valutazioni.md)

## Stato

| Passo | Stato |
|---|---|
| 1. Corpus | chiuso: 60 esercizi di retrieval + 20 De Bari; 54 di validazione e 26 di sviluppo (`corpus/roles.yaml`) |
| 2. Retrieval | chiuso: BM25 (congelato), dense (MiniLM), hybrid (RRF); esempi del 3b congelati in `data/retrieval_frozen/` |
| 3a. Generazione | chiuso: prompt, client LM Studio con cache, post-processing, runner e batch |
| 3b. Esperimento | **completato**: Gemma 4 26B A4B QAT, 6 prompt × 2 formati (PlantUML, JSON compatto) × 3 ripetizioni su 80 esercizi (2.874 risposte) |
| 4-5. Valutazione e analisi | **analisi statistica sul solo 3b** (script dei relatori); controlli oracle descrittivi, negli sviluppi futuri |

**Perimetro dell'analisi statistica** (voce 172 di `docs/decisions.md`): riguarda **solo il passo 3b**, con i 54
esercizi di validazione come analisi principale e i 26 di sviluppo come secondaria, e usa le metriche dello strumento
dei relatori. I **controlli oracle** (esempi costruiti dalla soluzione dell'esercizio, voci 162-171) sono **esclusi**
dall'analisi statistica: nella tesi vanno negli **sviluppi futuri**, come descrizione di cosa servirebbe perché il
retrieval di esempi funzioni.

Risultati dell'analisi statistica del 3b (schema dei relatori, voci 173-174; `experiments/stats_3b.py`,
`results/1_passo3b/analisi_statistica_*.xlsx`), dopo la correzione di Holm:
- **nessuna differenza tra prompt dello stesso formato**: bm25 e hybrid non battono gli esempi casuali, quelli fissi né
  zero_shot, quindi l'ipotesi centrale non è confermata;
- **il formato conta**: PlantUML è meglio del JSON compatto;
- **la difficoltà che conta è la grandezza del diagramma** (Spearman circa −0,45), non la leggibilità del testo
  (Flesch-Kincaid mai significativo).

Analisi principale sui 53 esercizi di validazione; i 79 (con i 26 di sviluppo, su cui è stata tarata la
configurazione) come robustezza: stesse conclusioni. Dettagli in
[`results/README_valutazioni.md`](./results/README_valutazioni.md), sezione 1.7.

## Struttura
```
corpus/                 pipeline di costruzione del corpus e del test set (vedi corpus/README.md)
  raw/                  sorgenti: models_original/ (45), translated_it/ (15, non versionata), debari_test/ (20)
  processed/            corpus.jsonl, testset_debari.jsonl, apollon/, apollon_debari/
  roles.yaml            ruoli degli 80 esercizi (54 di validazione, 26 di sviluppo)
retrieval/              BM25 (config_bm25.yaml), dense, hybrid, baseline random, analisi e test
generation/             prompt (template v5), client LLM (LM Studio, mock, cache), post-processing PlantUML / JSON
                        compatto -> Apollon v4, test
experiments/            runner (run_experiment.py), batch, configs/, analisi delle run, esportazione per i relatori
                        (export_3b.py), difficoltà (difficulty_3b.py), raccolta dei risultati (build_results.py)
evaluation/             metriche (validità, metriche per elemento P/R/F1) + schema Apollon v4
notebooks/passo3b.ipynb avvio e stato dei batch, confronti visivi
data/results/           output sperimentali (run di generazione: config, manifest, risposte grezze, sommari)
results/                risultati raccolti da consultare (Excel, export, sommari; generata da build_results.py)
  1_passo3b/            il 3b: base dell'analisi statistica
  2_controlli_oracle/   controlli oracle: sviluppi futuri, esclusi dall'analisi statistica
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
compatibile OpenAI, default `http://localhost:1234/v1`, nessuna chiave API). Modello del 3b:
`lms load google/gemma-4-26b-a4b-qat --context-length 32768 --gpu 0.5 -y`. Prova del server:
`python experiments/smoke_lmstudio.py --list-models`, poi `--model <id>`.

Test (da lanciare dopo ogni modifica): `python corpus/test_apollon_convert.py`, `python retrieval/test_retrieval.py`,
`python generation/test_generation.py`, `python evaluation/test_metrics.py`.
