
## Obiettivo della tesi

Costruire un sistema di generazione di esercizi di modellazione UML che usa RAG per
recuperare dinamicamente coppie (descrizione esercizio, diagramma di riferimento)
semanticamente simili da un corpus indicizzato, iniettandole come few-shot example nel
prompt dell'LLM, al posto di esempi statici scritti a mano.

**Ipotesi centrale**: esempi selezionati dinamicamente via retrieval producono diagrammi
migliori (metriche sintattiche/semantiche/pragmatiche) rispetto a few-shot statico o
zero-shot, specialmente per certe tipologie di esercizio.

## Fasi del progetto

1. **Costruzione del corpus** — raccolta di coppie (descrizione, diagramma UML di
   riferimento), pulizia e indicizzazione.
2. **Componente di retrieval** — tre varianti da confrontare:
   - keyword-based (es. BM25)
   - dense (embedding-based, es. SBERT/SROBERTA)
   - hybrid (combinazione delle due)
3. **Integrazione con LLM(s)** — costruzione del prompt few-shot con gli esempi
   recuperati, generazione del diagramma in **Apollon JSON v4** (formato dell'editor
   Apollon, pacchetto `@tumaet/apollon@5.3.0`, modello wire-format `"4.2.0"`; deciso
   il 2026-09-22 [v3] e aggiornato a v4 il 2026-09-23, vedi `docs/decisions.md` — non
   PlantUML, nonostante il riferimento a De Bari et al./Nguyen et al. che usavano
   PlantUML).
4. **Valutazione sperimentale** — confronto with/without retrieval, su metriche
   sintattiche, semantiche e pragmatiche.
5. **Analisi** — quali tipologie di esercizio beneficiano di più dal retrieval.

## Stato (aggiornato al 2026-10-05; dettagli in `docs/STATUS.md`)

- **Passo 1 chiuso**: corpus di retrieval con 60 esercizi (45 originali + 15 tradotti dall'italiano), 59 convertiti in
  Apollon v4; test set De Bari con 20 esercizi trascritti dalle immagini, tenuto fuori dal retrieval e congelato nel
  tag `testset-v1`.
- **Passo 2 chiuso** (BM25): configurazione congelata in `retrieval/config_bm25.yaml`, analizzata sul leave-one-out
  del corpus e applicata una volta al test set; dense e hybrid ancora da fare.
- **Passo 3a chiuso** (2026-10-05): infrastruttura di generazione per modelli locali via LM Studio (prompt builder,
  client con cache, post-processing L0-L4, runner `experiments/run_experiment.py`), provata solo con client finti.
- **Prossimo passo**: 3b (esperimenti) BLOCCATA in attesa delle risposte dei relatori (domande 8, 9, 11, 14 in
  `docs/STATUS.md`); nel frattempo, smoke test manuale di LM Studio (lo esegue l'utente).

## Relatori e riferimento diretto

- Paper precursore diretto: "Evaluating Large Language Models in Exercises of UML Class
  Diagram Modeling" (De Bari, Garaccione, Coppola, Ardito, Torchiano)

## Gap di ricerca (da tre survey indipendenti)

Nessun lavoro pubblicato combina retrieval dinamico di esempi (in stile RAG) con la
generazione di modelli UML/software. I lavori RAG-per-UML esistenti fanno grounding
(recupero di conoscenza/documentazione), non selezione dinamica di esempi few-shot. Il
retrieval-per-esempi è maturo nella generazione di codice (es. CEDAR) ma inesplorato per
UML.

## Convenzioni tecniche del repo

- Linguaggio: Python (ambiente virtuale dedicato, vedi `requirements.txt`)
- Formato diagrammi generati: Apollon JSON v4 (`@tumaet/apollon@5.3.0`, modello
  `"4.2.0"`; schema in `evaluation/uml-model-4.schema.json`)
- Struttura cartelle:
  - `corpus/raw/` — dati grezzi (esercizi + diagrammi originali; `debari_test/` = test set)
  - `corpus/processed/` — dati puliti/indicizzati (`corpus.jsonl` per il retrieval, `testset_debari.jsonl`)
  - `corpus/` — script della pipeline e annotazioni (mappa in `corpus/README.md`)
  - `retrieval/` — implementazioni keyword / dense / hybrid retriever
  - `generation/` — prompt building e client verso l'LLM
  - `evaluation/` — metriche sintattiche, semantiche, pragmatiche
  - `data/results/` — output sperimentali (metriche, log run)
  - `docs/` — note, decisioni, materiale di riferimento (`dati/`), archivio (`archivio/`)

## Note per l'agente

- Leggere `docs/STATUS.md` a inizio sessione (stato, comandi, regole attive, prossimi passi).
- Quando implementi un componente nuovo, aggiungi anche un test minimo o un piccolo
  script di verifica accanto al modulo (es. `retrieval/test_retrieval.py`).
- Tieni traccia delle scelte di design importanti in questo file o in
  `docs/decisions.md`, non solo nei commit.
- Non inventare dati sperimentali: se manca un dataset o un corpus reale, segnalarlo
  esplicitamente invece di simulare risultati.
