# docs/dati — materiale di riferimento (non corpus RAG)

Questa cartella contiene materiale raccolto/ricevuto che **non fa parte del corpus di
retrieval** (quello vive in `corpus/raw/models/`, vedi sotto). È organizzata per
**studio di provenienza** — due studi distinti erano stati raggruppati per errore
sotto lo stesso nome in una versione precedente di questa cartella, vedi
`docs/decisions.md` (voce 2026-09-24) per i dettagli della verifica.

## Cosa NON c'è più qui

- `models/` (45 esercizi con descrizione + diagramma PlantUML di riferimento) è in
  [`corpus/raw/models/`](../../corpus/raw/models/) — è il corpus primario per il
  retrieval. Vedi `corpus/processed/corpus.jsonl` per la versione indicizzata.

## Cosa c'è qui

### `debari/`
Materiale dello studio **De Bari et al.** ("Evaluating Large Language Models in
Exercises of UML Class Diagram Modeling", il paper precursore diretto di questa
tesi, vedi `CLAUDE.md`):
- `Exercises.pdf` (rinominato da `uml_class_diagram_exercises_with_solutions.pdf`) —
  **20 esercizi in inglese, ciascuno con una soluzione di riferimento completa**
  (diagramma delle classi, come immagine incorporata nel PDF), citati da fonti reali
  e diverse tra loro: *Learning UML* (Sinan Si Alhir), *Formalization of UML Class
  Diagrams in First Order Logic* (De Giacomo), *UML Fundamentals* (Cachia), *Systems
  Analysis and Design in a Changing World* (Satzinger et al.), SoftEng Group
  Politecnico di Torino, silvae86.github.io, uml-diagrams.org, e altre.
- `Analysis.xlsx` — le valutazioni di De Bari et al. sugli stessi 20 esercizi: 23
  fogli, di cui 20 nominati "Part 2 - 1" … "Part 2 - 20", uno per esercizio.
  **Corrispondenza verificata leggendo il contenuto** (non solo i nomi dei fogli):
  "Part 2 - 1" cita la classe "Work Product" (= esercizio 1, "Project Management
  System", che nel PDF ha proprio una classe `Work Product`); "Part 2 - 2" cita
  "Take" con attributi `nbr`/`filmed_meters`/`reel` (= esercizio 2, "Hollywood
  Approach", classe `Take` con `nbr:Integer`/`filmed_meters:Real`/`reel:String`);
  "Part 2 - 3" cita "Document"/"numberofpages"/"User" (= esercizio 3, "Word
  Processor").

**Ruolo previsto**: **test set** — query di valutazione con una baseline di
riferimento già esistente (i punteggi in `Analysis.xlsx`), non corpus few-shot per il
retrieval. **Punto aperto, da discutere con i relatori**: se e come riusare questi 20
esercizi anche come sorgente di esempi per il retrieval (leave-one-out: quando si
valuta l'esercizio N, il corpus di retrieval può contenere gli altri 19 ma non N).
Non ancora deciso — nessuno script della pipeline usa oggi questi file.

### `studio2025_it/`
- `Exercises.docx` — 15 esercizi in **italiano** (+ i 2 esempi in inglese del prompt
  v3, vedi sotto) da un **secondo studio, del 2025, non di De Bari** — verificato
  tramite l'item figshare DOI
  [10.6084/m9.figshare.29492624](https://doi.org/10.6084/m9.figshare.29492624) ("A
  comparison of different Large Language Models for the generation of UML class
  diagrams - Appendix"), che contiene esattamente questo file più `prompt.docx` e i
  due `diagram (N).json` sotto `apollon_format_reference/legacy_v3/`, e uno
  `Exercises.zip` con gli output di 4 LLM sugli stessi 15 esercizi.

  **Non usati al momento in nessuno script della pipeline.** Gli screenshot degli
  output LLM (`es1`…`es15` × ChatGPT/DeepSeek/Gemini/Qwen, 60 file, ~19 MB) sono
  stati rimossi da questo repository perché reperibili integralmente nello stesso
  item figshare sopra (`Exercises.zip`, 17.1 MB) — non riscaricati/riverificati
  byte-a-byte qui, vedi `docs/decisions.md` per il dettaglio di come è stata fatta
  questa verifica (corrispondenza di dimensione, non hash). Almeno un esercizio di
  questo set (l'orologio digitale) è un diagramma a stati, non delle classi — fuori
  scope se il progetto resta sui class diagram. Se in futuro servono come query di
  valutazione aggiuntive, vanno filtrati e va evitata la leakage col corpus di
  retrieval.

### `apollon_format_reference/`
Materiale che definisce il formato di output scelto (Apollon **v4**, vedi
`docs/decisions.md`, 2026-09-23):

**Versione corrente (v4), in uso:**
- `prompt_template_v4.txt` — prompt riscritto per il formato v4 (`nodes`/`edges`,
  tipi di relazione nativi `ClassInheritance`/`ClassRealization`/ecc.), con due
  esempi few-shot completi.
- `example_1_bank_loans_v4.json` — l'esempio "prestiti bancari" (stesso testo
  dell'esempio 1 originale in `legacy_v3/`), ricostruito in v4 tramite le stesse
  funzioni di `corpus/apollon_convert.py` (non trascritto a mano).
- `example_2_airtravel_v4.json` — **sostituisce l'esempio dell'orologio digitale**
  (diagramma a stati, fuori scope). È l'esercizio `AirTravel` del corpus
  (`corpus/raw/models/AirTravel/`); il record corrispondente in
  `corpus/processed/corpus.jsonl` ha `used_as_static_example: true` — va escluso
  dalle query di valutazione quando si usa questo prompt come baseline a few-shot
  statico, per evitare leakage (vedi `docs/decisions.md`, voce sul Blocco 4).

**Versione precedente (v3) e materiale del secondo studio 2025, come riferimento
storico** — in `legacy_v3/`:
- `prompt.docx` — prompt originale per il formato v3 (`elements`/`relationships` con
  `owner`/`bounds`, ereditarietà come associazione chiamata "is-a"). Fa parte dello
  stesso item figshare del secondo studio 2025 (sopra), **non è il prompt di De
  Bari**.
- `diagram_example_1.json`, `diagram_example_2.json` — i due esempi originali in v3
  (il secondo è l'orologio digitale/diagramma a stati).

**Non ancora fatto**: aprire `example_1_bank_loans_v4.json` e
`example_2_airtravel_v4.json` nell'editor Apollon online per una verifica visiva del
rendering di `ClassInheritance`/`ClassRealization`/`ClassAggregation`/
`ClassComposition` — vedi `docs/decisions.md` per il dettaglio di cosa è stato
verificato nei sorgenti e cosa no.

## Nota di scope

Il target di generazione è **Apollon JSON v4** (modello `"4.2.0"`, pacchetto
`@tumaet/apollon@5.3.0`), non PlantUML e non Apollon v3 (vedi `docs/decisions.md`,
voci 2026-09-22 e 2026-09-23). I 44 diagrammi di riferimento in `corpus/raw/models/`
che usano costrutti supportati sono convertiti in Apollon v4 JSON da
[`corpus/apollon_convert.py`](../../corpus/apollon_convert.py). Un modello (`Cruise`)
è escluso: usa un costrutto n-ario nativo di PlantUML (`<> diamond`) senza
equivalente Apollon documentato. Il risultato è in `corpus/processed/corpus.jsonl`
(campo `diagram_apollon_json`, `None` per Cruise) e in
`corpus/processed/apollon/<id>.json`.

**È una conversione automatica con approssimazioni note**, non un'annotazione
manuale — ogni record ha un campo `apollon_conversion_warnings`. Ogni diagramma
convertito passa per tre controlli automatici (schema JSON ufficiale, integrità
referenziale, round-trip semantico col PlantUML originale), tutti a 0 errori sui 44
diagrammi — vedi `docs/decisions.md` per il dettaglio, incluse le approssimazioni
intenzionali che restano (classe associativa, vincoli XOR) e cosa non è ancora stato
verificato (rendering visivo nell'editor).
