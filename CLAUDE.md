
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

## Stato (aggiornato al 2026-10-19; dettagli in `docs/STATUS.md`)

- **Passo 1 chiuso**: corpus di retrieval con 60 esercizi (45 originali + 15 tradotti dall'italiano), tutti
  convertiti in Apollon v4; test set De Bari con 20 esercizi (traccia estratta dal PDF, diagramma trascritto
  dall'immagine), congelato nel tag `testset-v1`. **Pool unico** (voce 115): per ogni query i candidati del retrieval
  sono tutti gli altri 79 esercizi. Ruoli (tag `evalset-v1`): **54 di valutazione** (34 corpus + 20 De Bari) e **26 di
  sviluppo** (20 del dev set + 6 dei piloti), `corpus/roles.yaml`.
- **Passo 2 chiuso**: BM25 congelato in `retrieval/config_bm25.yaml`; dense (MiniLM) e hybrid (RRF) implementati;
  esempi del 3b congelati in `data/retrieval_frozen/retrievals_3b.jsonl` (voce 129). Dense tolto dal 3b (voce 144).
- **Passo 3a chiuso**: generazione con modelli locali via LM Studio (prompt builder, client con cache,
  post-processing, runner `experiments/run_experiment.py`, batch e notebook `notebooks/passo3b.ipynb`).
- **Passo 3b completato** (2026-10-13; sui 26 di sviluppo il 2026-10-18, voce 151): Gemma 4 26B A4B QAT, 6 condizioni
  (zero_shot, static k2, random k3, bm25 k2 / k3, hybrid k3) × 3 ripetizioni × 2 formati (PlantUML, JSON compatto).
  Risultati ESPLORATIVI (visti prima dello script di analisi, voce 154): il retrieval non batte gli esempi casuali;
  gli esempi aiutano soprattutto nel compatto. Leve v5b e v5c sugli scheletri non adottate (voci 148, 153, 155).
- **Controlli solo analisi (2026-10-20, voci 162-165)**: con l'esercizio stesso come esempio la completezza passa da
  circa 0,43 a 0,76 (PlantUML): il modello sa usare un esempio vicino. Un esempio serve (guadagno >= 0,05) solo con
  somiglianza dei nomi di classe di circa 0,4-0,56 o piu'; nel pool nessuna coppia supera 0,4, quindi il limite del
  retrieval nel 3b e' il corpus. Esempi lontani accanto a uno vicino non fanno danno; un esempio completo vale piu' di
  due meta'. Esempi senza attributi causano gli scheletri (voce 169): compatto 28 % -> 91 %, PlantUML 2 % -> 19 %.
  Nel compatto (voci 170-171) le stesse conclusioni: rispetto a esempi casuali la soglia di utilita' e' al 50 %.
- **Prossimi passi**: l'analisi statistica del 3b la fanno i relatori con un loro script (voce 158; schema della
  voce 156): il repo fornisce i dati (`experiments/export_3b.py --unico`, `experiments/difficulty_3b.py`) nel formato
  da concordare (tipo di F1, colonne, esercizi); revisione dei sinonimi scartata (voce 160); analisi esplorative
  raccolte nel report condiviso con i relatori (voce 161). Domande ai relatori 8, 11, 14 e 16 chiuse
  (voce 159): modello e parametri scelti dall'utente; metriche = script dei relatori; generazione libera; nessun
  secondo modello.

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
  - `results/` — risultati raccolti da consultare (copie, generata da `experiments/build_results.py`)
  - `docs/` — note, decisioni, materiale di riferimento (`dati/`), archivio (`archivio/`)

## Note per l'agente

- Leggere `docs/STATUS.md` a inizio sessione (stato, comandi, regole attive, prossimi passi).
- Quando implementi un componente nuovo, aggiungi anche un test minimo o un piccolo
  script di verifica accanto al modulo (es. `retrieval/test_retrieval.py`).
- Tieni traccia delle scelte di design importanti in questo file o in
  `docs/decisions.md`, non solo nei commit.
- Non inventare dati sperimentali: se manca un dataset o un corpus reale, segnalarlo
  esplicitamente invece di simulare risultati.
