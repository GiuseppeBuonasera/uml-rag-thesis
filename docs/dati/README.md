# docs/dati — materiale di riferimento (non corpus RAG)

Questa cartella contiene materiale raccolto/ricevuto che **non fa parte del corpus di
retrieval** (quello vive in `corpus/raw/models/`, vedi sotto). È tenuto qui come
riferimento per il prompt engineering, la valutazione e possibili estensioni future.

## Cosa NON c'è più qui

- `models/` (45 esercizi con descrizione + diagramma PlantUML di riferimento) è stato
  spostato in [`corpus/raw/models/`](../../corpus/raw/models/) — è il corpus primario
  per il retrieval. Vedi `corpus/processed/corpus.jsonl` per la versione indicizzata
  (generata da `corpus/build_manifest.py`).

## Cosa c'è qui

### `debari_baseline/`
Pacchetto dello studio precedente (replica/baseline in stile De Bari et al.): 15
esercizi in italiano (`Exercises.docx`), le soluzioni generate da 4 LLM diversi
(ChatGPT, DeepSeek, Gemini, Qwen) come screenshot in `Exercises/`, e `Analysis.xlsx`
con le valutazioni.

**Non è corpus few-shot.** È materiale di **benchmark/baseline di un altro studio**:
- almeno un esercizio (l'orologio digitale) è un diagramma a stati, non delle classi —
  fuori scope se il progetto resta sui class diagram.
- se in futuro si vogliono riusare questi 15 esercizi come *query di valutazione* per il
  nostro sistema RAG, vanno filtrati (solo class diagram) e va evitata la leakage: non
  devono comparire anche nel corpus di retrieval usato per generare i loro pochi-shot.

*(Nota: qui c'era anche un `Exercises.pdf`, rimosso — era un duplicato byte-per-byte
male etichettato di `external_exercise_pool/uml_class_diagram_exercises_with_solutions.pdf`,
contenuto completamente diverso da `Exercises.docx`. Vedi sotto.)*

### `apollon_format_reference/`
Materiale che definisce il formato di output scelto (Apollon **v4**, vedi
`docs/decisions.md`, 2026-09-23 — sostituisce Apollon v3):

**Versione corrente (v4), da usare:**
- `prompt_template_v4.txt` — prompt riscritto per il formato v4 (`nodes`/`edges`,
  tipi di relazione nativi `ClassInheritance`/`ClassRealization`/ecc.), con due
  esempi few-shot completi.
- `example_1_bank_loans_v4.json` — l'esempio "prestiti bancari" (stesso testo del
  vecchio `diagram_example_1.json`), ricostruito in v4 tramite le stesse funzioni di
  `corpus/apollon_convert.py` (non trascritto a mano), validato contro
  `evaluation/uml-model-4.schema.json`.
- `example_2_airtravel_v4.json` — **sostituisce l'esempio dell'orologio digitale**
  (che era un diagramma a stati, fuori scope). È l'esercizio `AirTravel` del corpus
  (`corpus/raw/models/AirTravel/`), già convertito in v4 dalla pipeline principale:
  copiato qui, non rigenerato ad hoc.

**Versione precedente (v3), tenuta solo come riferimento storico/di confronto:**
- `prompt.docx` / `prompt_template.txt` — prompt originale per il formato v3
  (`elements`/`relationships` con `owner`/`bounds`, ereditarietà come associazione
  chiamata "is-a").
- `diagram_example_1.json`, `diagram_example_2.json` — i due esempi originali in v3
  (il secondo è l'orologio digitale/diagramma a stati).

**Non ancora fatto** (vedi "conseguenze aperte" in `docs/decisions.md`, voce
2026-09-23): aprire `example_1_bank_loans_v4.json` e `example_2_airtravel_v4.json`
nell'editor Apollon online per una verifica visiva — in particolare per confermare la
direzione del triangolo di `ClassInheritance`, unico dettaglio dello schema v4 non
verificato nei sorgenti (nessun file di marker/arrowhead trovato in tempo utile).

### `external_exercise_pool/`
- `uml_class_diagram_exercises_with_solutions.pdf` (rinominato da `data.pdf` — era
  anche duplicato, per errore, come `Exercises.pdf` in `debari_baseline/`, vedi sopra)
  — **20 esercizi in inglese, ciascuno con una soluzione di riferimento completa**
  (diagramma delle classi, come immagine incorporata nel PDF), citati da fonti
  reali e diverse tra loro: *Learning UML* (Sinan Si Alhir), *Formalization of UML
  Class Diagrams in First Order Logic* (De Giacomo), *UML Fundamentals* (Cachia),
  *Systems Analysis and Design in a Changing World* (Satzinger et al.), SoftEng Group
  Politecnico di Torino, silvae86.github.io, uml-diagrams.org, e altre.

  **Correzione rispetto a una versione precedente di questa nota**: qui era scritto
  che questo file conteneva "solo tracce, senza diagrammi di riferimento" — falso,
  verificato aprendo il PDF pagina per pagina: ha soluzioni complete. È un **candidato
  serio per espandere il corpus** (20 coppie descrizione+diagramma in più, con fonte
  citata), ma il lavoro non è ancora fatto: le soluzioni sono immagini (screenshot/scan
  di diagrammi disegnati con tool diversi), vanno trascritte a mano in PlantUML (o
  direttamente in Apollon JSON) prima di poter entrare in `corpus/raw/`. Nessuna
  trascrizione è stata fatta finora — non ci sono ancora nuovi esempi qui, solo il PDF
  sorgente.

## Nota di scope

Il target di generazione è **Apollon JSON v4** (modello `"4.2.0"`, pacchetto
`@tumaet/apollon@5.3.0`), non PlantUML e non più Apollon v3 (vedi
[`docs/decisions.md`](../decisions.md), voci 2026-09-22 e 2026-09-23). I 44 diagrammi
di riferimento originali in `corpus/raw/models/` che usano costrutti supportati sono
stati convertiti in Apollon v4 JSON da
[`corpus/apollon_convert.py`](../../corpus/apollon_convert.py) (schema verificato
leggendo i sorgenti reali di `@tumaet/apollon`, non dedotto). Un modello (`Cruise`) è
escluso: usa un costrutto n-ario nativo di PlantUML (`<> diamond`) senza equivalente
Apollon documentato, e si è preferito escluderlo piuttosto che inventare una classe
fittizia. Il risultato è in `corpus/processed/corpus.jsonl` (campo
`diagram_apollon_json`, `None` per Cruise) e in `corpus/processed/apollon/<id>.json`.

**È una conversione automatica con approssimazioni note**, non una nuova annotazione
manuale — ogni record ha un campo `apollon_conversion_warnings` che elenca i casi non
gestiti in modo esatto (soprattutto: il costrutto "classe associativa" di PlantUML,
`(A,B) .. C`, approssimato con due associazioni semplici verso i due partecipanti, con
molteplicità lasciate vuote perché non ricavabili in modo affidabile; 2 vincoli XOR
scartati perché non rappresentabili). Una revisione esterna (2026-09-23) ha trovato e
fatto correggere due bug reali nella prima versione del convertitore (parsing degli
attributi in sintassi `nome : Tipo`, e molteplicità scambiate sul lato sbagliato per
`--o`/`--*`), poi si è passati da Apollon v3 a v4 — vedi `docs/decisions.md` per
entrambe le voci. Ogni diagramma convertito passa ora per tre controlli distinti,
tutti eseguiti automaticamente da `corpus/apollon_convert.py` e verificati a 0 errori
sui 44 diagrammi: `validate_against_schema` (conformità strutturale allo schema JSON
ufficiale `evaluation/uml-model-4.schema.json`), `verify_apollon_json` (integrità
referenziale interna) e `round_trip_check` (contenuto semantico — attributi e
molteplicità — confrontato col PlantUML originale). Restano comunque le
approssimazioni intenzionali elencate sopra, e la direzione del triangolo di
`ClassInheritance`/`ClassRealization` nell'editor non è ancora stata verificata
visivamente: da rivedere prima di usare questi diagrammi come few-shot "canonici" in
valutazioni che contano sulla loro esattezza semantica al 100%.
