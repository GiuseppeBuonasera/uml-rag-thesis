# UML RAG Thesis

Sistema di generazione di esercizi di modellazione UML basato su LLM con
retrieval-augmented example selection (RAG per selezione dinamica di esempi few-shot).

Vedi [`CLAUDE.md`](./CLAUDE.md) per il contesto completo del progetto (obiettivo,
fasi, relatori, convenzioni tecniche).

## Struttura

```
corpus/
  raw/            dati grezzi (esercizi + diagrammi di riferimento)
  processed/      dati puliti e indicizzati
retrieval/        retriever keyword / dense / hybrid
generation/       prompt building + client LLM
evaluation/       metriche sintattiche/semantiche/pragmatiche
notebooks/        esplorazione e analisi risultati
data/results/     output sperimentali
docs/             note e bibliografia
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # su Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Stato del progetto

- [x] Costruzione corpus — prima versione: 45 esercizi (`corpus/raw/models/`),
      indicizzati in `corpus/processed/corpus.jsonl`, diagrammi convertiti in Apollon
      JSON (`corpus/apollon_convert.py`, con approssimazioni note da rivedere, vedi
      `docs/decisions.md`)
- [ ] Retrieval keyword (BM25)
- [ ] Retrieval dense
- [ ] Retrieval hybrid
- [ ] Integrazione LLM + prompt few-shot dinamico
- [ ] Pipeline di valutazione
- [ ] Analisi per tipologia di esercizio
