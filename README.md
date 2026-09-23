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
      indicizzati in `corpus/processed/corpus.jsonl`, 44/45 diagrammi convertiti in
      **Apollon v4 JSON** (`corpus/apollon_convert.py`; `Cruise` escluso, costrutto
      non supportato). Revisionato il 2026-09-23: due bug reali corretti nella
      conversione (parsing attributi, molteplicità invertite), poi passaggio da
      Apollon v3 a v4 (tipi di relazione nativi come `ClassInheritance`). Ogni
      diagramma è verificato a 3 livelli (schema JSON ufficiale, integrità
      referenziale, round-trip semantico col PlantUML originale), tutti a 0 errori.
      Restano approssimazioni note e la verifica visiva nell'editor Apollon non è
      ancora stata fatta — vedi `docs/decisions.md`
- [ ] Retrieval keyword (BM25)
- [ ] Retrieval dense
- [ ] Retrieval hybrid
- [ ] Integrazione LLM + prompt few-shot dinamico
- [ ] Pipeline di valutazione
- [ ] Analisi per tipologia di esercizio
