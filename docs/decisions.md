# Decisioni di design

Registro delle scelte tecniche importanti nel tempo, con motivazione.
Aggiornare ogni volta che si prende una decisione rilevante (es. cambio di
formato diagrammi, scelta del modello di embedding, metrica di valutazione).

## Formato

### [Data] Titolo della decisione
- Contesto:
- Opzioni considerate:
- Decisione presa:
- Motivazione:

### [2026-09-22] Formato di output dei diagrammi: Apollon JSON (non PlantUML)
- Contesto: CLAUDE.md era contraddittorio — la Fase 3 indicava PlantUML ("da
  confermare"), mentre le Convenzioni tecniche indicavano "pollon" ed
  `evaluation/metrics.py` assumeva già validazione PlantUML. Il materiale in
  `docs/dati/` (prompt.docx, diagram_example_*.json) è in formato Apollon
  (https://apollon.ase.in.tum.de), non PlantUML.
- Opzioni considerate: PlantUML (coerente col corpus raw già raccolto) vs Apollon JSON
  (coerente col prompt/esempi già preparati).
- Decisione presa: Apollon JSON come formato di output target per generazione e
  valutazione.
- Motivazione: scelta dell'utente/relatori, materiale di prompting già preparato in
  questo formato.
- Conseguenze aperte:
  - I 45 diagrammi di riferimento in `corpus/raw/models/*/plantuml.txt` sono ancora
    solo in PlantUML. Serve un convertitore PlantUML -> Apollon JSON (o annotazione
    manuale) prima di poterli usare come few-shot example nel formato finale.
    `corpus/processed/corpus.jsonl` ha il campo `diagram_apollon_json: null` in attesa.
  - `evaluation/metrics.py` va aggiornato per validare/confrontare Apollon JSON invece
    di (o in aggiunta a) PlantUML.
  - CLAUDE.md Fase 3 aggiornato di conseguenza.

### [2026-09-22] Riorganizzazione di docs/dati/
- Contesto: `docs/dati/` conteneva alla rinfusa il vero corpus (45 cartelle
  `models/*`), un pacchetto di baseline di uno studio precedente (15 esercizi IT x 4
  LLM + valutazioni), materiale sul formato Apollon, e una raccolta esterna di tracce
  senza soluzioni.
- Decisione presa:
  - `models/` spostato in `corpus/raw/models/` (è il corpus RAG, non materiale di
    supporto in `docs/`).
  - Resto di `docs/dati/` riorganizzato in `debari_baseline/`,
    `apollon_format_reference/`, `external_exercise_pool/` — vedi
    `docs/dati/README.md` per il dettaglio di cosa contiene ciascuna.
  - Aggiunto `corpus/build_manifest.py` che genera `corpus/processed/corpus.jsonl`
    (un record per esercizio: descrizione, diagramma, dominio, source, tag) con
    self-check (id univoci, nessuna descrizione/diagramma vuoto).
- Motivazione: separare corpus di retrieval da materiale di riferimento; evitare che il
  pacchetto di baseline (contiene anche un diagramma a stati, fuori scope) venga
  confuso con dati few-shot; avere un unico punto di ingresso indicizzabile per il
  retrieval.
- Nota: il pacchetto `debari_baseline/` non va usato come corpus few-shot. Se in futuro
  serve come set di valutazione, va filtrato (solo class diagram) e verificato che non
  ci sia overlap con il corpus di retrieval.

### [2026-09-22] Convertitore PlantUML -> Apollon JSON per i 45 diagrammi di riferimento
- Contesto: dopo la decisione di usare Apollon JSON come formato target, i 45 diagrammi
  di riferimento in `corpus/raw/models/` erano ancora solo in PlantUML
  (`diagram_apollon_json: null` nel manifest).
- Decisione presa: scritto `corpus/apollon_convert.py`. Schema Apollon verificato
  leggendo i sorgenti del pacchetto npm `@ls1intum/apollon@3.4.6` (non dedotto dagli
  esempi soltanto) — confermati come tipi di elemento validi "Class", "AbstractClass",
  "Enumeration" (valori di enum modellati come "ClassAttribute" di proprietà
  dell'Enumeration). Per le relazioni si è seguita la convenzione imposta da
  `prompt.docx` (non lo schema nativo, che avrebbe anche "ClassInheritance"): tutto
  mappato su "ClassBidirectional" / "ClassAggregation" / "ClassComposition",
  ereditarietà come "ClassBidirectional" con `name: "is-a"` — per restare coerenti col
  formato che il prompt chiede effettivamente all'LLM di produrre.
- Layout (bounds/path) calcolato con una griglia deterministica semplice: non
  rispecchia un layout "originale" (il PlantUML testuale non lo specifica comunque).
- Approssimazioni esplicite (non semantica esatta), loggate per record in
  `apollon_conversion_warnings`:
  - "classe associativa" PlantUML (`(A,B) .. C`) → due associazioni semplici C-A e C-B,
    entrambe molteplicità "1" (12 casi).
  - 2 vincoli XOR (`note "{XOR}" as N`, in FilmSet e TransportCompany) scartati: nessun
    costrutto Apollon equivalente documentato, non inventato.
  - Alcune classi (`ResearchGroupMember` in ProjectManagement, `Album` in Musicmatic)
    sono usate in una relazione ma mai dichiarate esplicitamente con
    `class X {...}` nel PlantUML sorgente: create come placeholder senza attributi,
    con warning. **Correzione (2026-09-23)**: questo non è un bug nei dati — in
    PlantUML la dichiarazione implicita di una classe tramite uso in una relazione è
    legale, quindi creare il placeholder è il comportamento corretto. La frase
    originale qui ("bug nei dati originali") era sbagliata, segnalato in revisione.
- Verificato: 45/45 diagrammi convertiti, 0 problemi di integrità referenziale
  (`verify_apollon_json`, eseguito automaticamente da `apollon_convert.py`), 29 warning
  totali (tutti riconducibili ai casi sopra).
- Conseguenza aperta: questi Apollon JSON sono generati automaticamente con
  approssimazioni note, non annotazioni manuali validate. Prima di usarli in
  valutazioni che assumono correttezza semantica al 100% (es. come "ground truth" per
  metriche semantiche), vanno rivisti a campione o interamente a mano. **Vedi anche la
  voce del 2026-09-23 sotto**: questa decisione conteneva due bug reali, corretti.

### [2026-09-23] Revisione del convertitore PlantUML -> Apollon: due bug corretti, round-trip aggiunto, materiale mal etichettato corretto
- Contesto: revisione esterna del codice (senza accesso ai 45 `plantuml.txt`, esclusi
  da `.gitignore` — testata su un PlantUML scritto ad hoc) ha trovato due bug reali
  nella prima versione di `corpus/apollon_convert.py`, verificati poi sui dati veri.
- **Bug 1 (parsing attributi)**: `parse_attribute` assumeva solo la sintassi Java
  `Tipo nome`, non gestiva `nome : Tipo` (piu' comune in PlantUML) ne' toglieva i
  prefissi di visibilita' `+-#~`. Impatto reale confermato: `Ebike` e `University` (23
  righe attributo su 2/45 modelli) usano `nome : Tipo` — i loro attributi erano
  scritti in modo invertito/corrotto nel JSON (es. `University.json`, che l'utente
  aveva aperto e notato qualcosa di strano). Corretto: `parse_attribute` ora gestisce
  entrambe le sintassi, toglie visibilita' e modificatori `{static}`/`{abstract}`.
- **Bug 2 (molteplicita' invertite)**: `relationship_kind` scambiava source/target per
  `--o`/`-o` e `--*`/`-*` (per mettere l'aggregatore/contenitore come "source"), ma le
  molteplicita' restavano legate ai nomi delle variabili originali invece di seguire
  lo scambio. Impatto reale confermato: `School` (`Student "10..31"-o"1" ClassGroup` →
  usciva "ClassGroup 10..31 -> Student 1", invertito) e `House`
  (`Basement "0..1" -* "1" House`, stesso problema). Corretto: `relationship_kind` ora
  ritorna un flag `swapped` esplicito, e chi lo chiama scambia classi e molteplicita'
  insieme, mai l'una senza l'altra.
- Perche' non si erano visti prima: `verify_apollon_json` controllava solo l'integrita'
  referenziale (id, owner, bounds), non la correttezza semantica — "45/45, 0 problemi"
  era compatibile con entrambi i bug. Aggiunta `round_trip_check`: confronta il
  contenuto semantico (attributi con nome+tipo, molteplicita' per estremo) tra quanto
  estratto dal PlantUML originale e quanto risulta nel JSON convertito, **senza
  riusare la logica di `relationship_kind`** (per non validare un bug con la stessa
  funzione che lo ha causato). Eseguita automaticamente da `apollon_convert.py`, fa
  fallire la build se trova discrepanze.
- Altre correzioni allo stesso giro (meno gravi, segnalate nella stessa revisione):
  - Classe associativa: le due associazioni approssimate C-A/C-B ora hanno
    molteplicita' vuote invece di "1"/"1" fisse — quel "1" era un'informazione
    inventata, non presente nel PlantUML sorgente.
  - Attributi senza tipo nel sorgente: non si inventa piu' un default `"string"`, il
    nome resta senza tipo (`"+ nome"`).
  - `<> diamond` in Cruise (costrutto n-ario nativo di PlantUML, nessun equivalente
    Apollon documentato): prima diventava una classe fittizia "diamond"; ora l'intero
    modello Cruise viene escluso dalla conversione (`diagram_apollon_json: null`),
    invece di inventare un elemento.
  - `size` del diagramma: se il layout a griglia eccede l'area 0-1600 x 0-780 imposta
    da `prompt.docx` per le coordinate, ora viene scalato proporzionalmente per
    rientrarci (`fit_to_canvas`) — prima poteva restare fuori da quei limiti,
    contraddicendo il prompt che accompagna gli stessi esempi.
  - Testo "bug nei dati originali" nella voce del 2026-09-22 corretto: la
    dichiarazione implicita di classe in PlantUML e' legale, non un errore.
- Verificato dopo le correzioni: 44/45 diagrammi convertiti (Cruise escluso), 0
  problemi di integrità referenziale, **0 discrepanze di round-trip**, ricontrollato a
  mano su `University` (attributi), `School` e `House` (molteplicità) confrontando
  l'output con il PlantUML sorgente riga per riga.
- Punto ancora aperto, non un bug: l'ereditarietà modellata come `ClassBidirectional`
  con `name: "is-a"` (invece del tipo nativo Apollon `ClassInheritance`) resta la
  scelta fatta per coerenza col prompt, ma in Apollon quella relazione non viene
  disegnata come una vera ereditarietà (niente triangolo). Da discutere con i
  relatori, non ancora deciso.
- **Errore separato trovato durante la stessa revisione, in `docs/dati/README.md` (non
  nel convertitore)**: `docs/dati/external_exercise_pool/data.pdf` era descritto come
  "tracce senza diagrammi di riferimento" — falso. Verificato aprendo il PDF: 20
  esercizi in inglese con soluzioni di riferimento complete (diagrammi delle classi,
  citati da fonti reali: Learning UML di Sinan Si Alhir, lavoro di De Giacomo, UML
  Fundamentals di Cachia, SoftEng Politecnico di Torino, silvae86.github.io,
  uml-diagrams.org, altri). Trovato anche che `debari_baseline/Exercises.pdf` era
  byte-identico a questo stesso file (verificato con hash), quindi mal etichettato
  come "versione PDF di Exercises.docx" (che invece è tutt'altro documento, i 15
  esercizi italiani). Corretto: il duplicato rimosso da `debari_baseline/`, il file
  rinominato in `uml_class_diagram_exercises_with_solutions.pdf` e la descrizione
  riscritta in `docs/dati/README.md`. È un candidato serio per espandere il corpus (20
  coppie descrizione+diagramma in più), ma le soluzioni sono immagini: la trascrizione
  in PlantUML/Apollon JSON non è ancora stata fatta.

### [2026-09-23] Passaggio da Apollon v3 a v4 come formato di output
- Contesto: la decisione del 2026-09-22 fissava Apollon v3 (`elements`/`relationships`
  con `owner`/`bounds`, ereditarietà come associazione `ClassBidirectional` chiamata
  "is-a" per mancanza di un tipo nativo). v4 (`@tumaet/apollon`, pacchetto npm
  successore di `@ls1intum/apollon`) è più compatto e ha tipi di relazione nativi.
- Decisione presa: passare al modello wire-format v4 (`"version": "4.2.0"`,
  pacchetto `@tumaet/apollon@5.3.0`). Verificato leggendo i sorgenti reali (non
  dedotto), inclusi TypeScript non compilati su GitHub, non solo lo schema JSON:
  - `library/lib/types/nodes/NodeProps.ts`: un nodo classe è `"type": "class"`
    sempre (non esistono più nodi "AbstractClass"/"Enumeration" separati come in
    v3); la distinzione sta in `data.isAbstract` (bool) e `data.stereotype`
    (`"interface"` | `"enumeration"`, da `ClassStereotype.ts`). Attributi e metodi
    sono dentro `data.attributes`/`data.methods` come `{id, name}`, non più elementi
    separati con `owner`.
  - `library/lib/edges/EdgeProps.ts`: `edge.data` ha `sourceMultiplicity`,
    `targetMultiplicity`, `sourceRole`, `targetRole`, `label`, `points` (coordinate
    assolute, niente più `bounds` separato per l'edge).
  - `library/lib/nodes/wrappers/DefaultNodeWrapper.tsx` (enum `HandleId`): i punti di
    aggancio centrali sono `"top"`/`"right"`/`"bottom"`/`"left"` (letterali, minuscoli).
  - `dist/versionConverter-*.js` (bundle compilato): versione corrente del modello
    `"4.2.0"`.
  - Schema JSON ufficiale pubblicato: `@tumaet/apollon/schema/uml-model-4.schema.json`,
    copiato in `evaluation/uml-model-4.schema.json` per validazione automatica.
  - **Non verificato nei sorgenti** (nessun file di marker/arrowhead trovato in tempo
    utile): quale estremo di `ClassInheritance`/`ClassRealization` porta il triangolo
    nell'editor. Assunta la convenzione UML standard (source=figlio,
    target=superclasse/interfaccia), coerente con tutto il resto della pipeline. **Da
    confermare aprendo diagrammi convertiti nell'editor Apollon online** — non ancora
    fatto, vedi "conseguenze aperte" sotto.
- Vantaggio concreto per la tesi: tipi di relazione nativi (`ClassInheritance`,
  `ClassRealization`, `ClassUnidirectional`, `ClassDependency`, oltre a
  `ClassAggregation`/`ClassComposition`/`ClassBidirectional` già presenti in v3) —
  l'ereditarietà non è più un'associazione con un nome convenzionale, è un tipo a sé,
  quindi le metriche di valutazione potranno distinguerla da una semplice
  associazione senza euristiche sul campo `name`.
- `corpus/apollon_convert.py` riscritto: il parser PlantUML resta invariato (agnostico
  rispetto al formato di output), riscritta solo la parte finale (`build_apollon_json`
  produce `nodes`/`edges` invece di `elements`/`relationships`). Aggiunto un terzo
  livello di verifica oltre a `verify_apollon_json` (integrità referenziale) e
  `round_trip_check` (contenuto semantico): `validate_against_schema`, che valida
  ogni diagramma contro lo schema JSON ufficiale con la libreria `jsonschema`
  (aggiunta a `requirements.txt`).
- Verificato dopo la riscrittura: 44/45 diagrammi convertiti (Cruise ancora escluso,
  stesso motivo di prima — costrutto diamante n-ario senza equivalente), **0
  violazioni di schema, 0 problemi di integrità referenziale, 0 discrepanze di
  round-trip**.
- Conseguenze aperte (non ancora fatte):
  - **Verifica visiva**: aprire 3-4 diagrammi convertiti nell'editor Apollon online
    per confermare che il rendering (in particolare il triangolo di
    `ClassInheritance`) sia quello atteso — punto sopra non verificato nei sorgenti.
  - Il prompt (`docs/dati/apollon_format_reference/prompt.docx`) descrive ancora il
    formato v3 in dettaglio e va riscritto per v4; i due esempi few-shot del prompt
    (prestiti bancari, orologio digitale) vanno rifatti in v4 — l'orologio è tra
    l'altro un diagramma a stati, andrebbe sostituito con un vero esempio di
    diagramma delle classi.
  - Il "few-shot statico" di baseline per il confronto sperimentale sarà quindi il
    prompt di De Bari **adattato al v4**, non quello originale identico. Scelta
    necessaria per un confronto equo (stesso formato con/senza retrieval), ma va
    dichiarata esplicitamente in tesi come limite/nota metodologica. I punteggi in
    `docs/dati/debari_baseline/Analysis.xlsx` restano utilizzabili come riferimento
    perché valutano i diagrammi nel merito, non il formato di serializzazione.

    **Correzione (2026-09-24)**: questo paragrafo confondeva due studi distinti.
    `prompt.docx` (e i due esempi v3, ed `Exercises.docx` con i 15 esercizi
    italiani) **non sono di De Bari et al.** — sono del secondo studio del 2025
    (confermato via figshare DOI 10.6084/m9.figshare.29492624, vedi voce
    successiva). `Analysis.xlsx` **è** di De Bari, ma valuta i 20 esercizi in
    inglese del PDF (ora `docs/dati/debari/Exercises.pdf`), non i 15 esercizi
    italiani di `Exercises.docx`. Quindi: il "few-shot statico" costruito
    adattando `prompt.docx` al v4 è una baseline del **secondo studio**, non di
    De Bari; i punteggi di `Analysis.xlsx` non sono direttamente confrontabili con
    quel few-shot perché valutano un set di esercizi diverso. Se serve una
    baseline comparabile ai punteggi di `Analysis.xlsx`, va costruita sui 20
    esercizi del PDF di De Bari, non sui 15 italiani.
  - `evaluation/metrics.py` menziona ancora "validità PlantUML" tra le metriche
    sintattiche: da aggiornare per riferirsi alla validazione contro
    `uml-model-4.schema.json`.

### [2026-09-24] Riorganizzazione docs/dati/: identificato lo studio di provenienza corretto per ciascun file
- Contesto: le voci precedenti (2026-09-22, 2026-09-23) avevano già separato il
  corpus (`corpus/raw/models/`) dal resto, ma raggruppavano insieme materiale di
  **due studi distinti** sotto lo stesso nome fuorviante (`debari_baseline/`):
  - Il PDF da 20 esercizi in inglese con soluzioni di riferimento
    (`external_exercise_pool/uml_class_diagram_exercises_with_solutions.pdf`) e
    `debari_baseline/Analysis.xlsx` sono lo **stesso studio** (De Bari et al.):
    verificato aprendo entrambi i file — i 20 fogli "Part 2 - N" di `Analysis.xlsx`
    corrispondono agli esercizi del PDF (es. "Part 2 - 1" cita la classe "Work
    Product" = esercizio 1 "Project Management System"; "Part 2 - 2" cita "Take"
    con attributi `nbr`/`filmed_meters`/`reel` = esercizio 2 "Hollywood Approach";
    "Part 2 - 3" cita "Document"/"numberofpages"/"User" = esercizio 3 "Word
    Processor" — controllo diretto sul contenuto XML dei fogli, non solo sui nomi).
  - `debari_baseline/Exercises.docx` (15 esercizi in italiano) e
    `debari_baseline/Exercises/` (60 screenshot ChatGPT/DeepSeek/Gemini/Qwen)
    appartengono a un **secondo studio, del 2025, non di De Bari**. Verificato
    tramite l'item figshare DOI 10.6084/m9.figshare.29492624 ("A comparison of
    different Large Language Models for the generation of UML class diagrams -
    Appendix"): contiene esattamente `prompt.docx` (22.4 KB), `diagram (1).json`
    (9.9 KB), `diagram (2).json` (6.3 KB), `Exercises.docx` (3.2 MB) e
    `Exercises.zip` (17.1 MB) — dimensioni pressoché identiche (byte-per-byte per i
    primi quattro) ai file locali corrispondenti. Non ho scaricato/estratto
    `Exercises.zip` per un confronto byte-a-byte dei singoli screenshot (non
    verificabile da qui in modo diretto): la conferma si basa sulla corrispondenza
    di dimensione del file compresso nel suo complesso (17.1 MB vs 19 MB
    decompressi localmente, rapporto plausibile per PNG) più la corrispondenza
    esatta degli altri quattro file dello stesso item. Va detto esplicitamente: non
    è una verifica byte-a-byte del contenuto di `Exercises.zip`.
- Decisione presa: nuova struttura in `docs/dati/` che riflette la provenienza reale:
  - `debari/` — `Exercises.pdf` (rinominato da `uml_class_diagram_exercises_with_solutions.pdf`)
    + `Analysis.xlsx`. Materiale dello studio di De Bari et al.
  - `studio2025_it/` — `Exercises.docx` (15 esercizi italiani). Materiale del secondo
    studio (2025).
  - `apollon_format_reference/legacy_v3/` — `prompt.docx`,
    `diagram_example_1.json`, `diagram_example_2.json`: anche questi fanno parte
    dello stesso item figshare del secondo studio (sono il prompt/esempi v3
    originali), tenuti come riferimento storico del formato precedente.
  - Eliminati: `docs/dati/external_exercise_pool/` (cartella svuotata dallo
    spostamento), `docs/dati/apollon_format_reference/prompt_template.txt`
    (estrazione testuale rovinata di `prompt.docx`, ridondante — l'originale resta
    in `legacy_v3/`), `docs/dati/debari_baseline/Exercises/` (60 screenshot, 19 MB,
    non usati in nessuno script della pipeline — rimossi perché reperibili
    integralmente sul figshare item sopra, DOI citato in `docs/dati/README.md`).
  - Spostamenti fatti con `git mv` per mantenere la storia.
- Verificato dopo la riorganizzazione: nessun riferimento residuo ai vecchi percorsi
  in file `.py`/`.md`/`.txt` del repository (grep mirato, eseguito su tutto il
  repository escluso `.git/`) al di fuori delle voci storiche di questo stesso file
  di decisioni (lasciate intenzionalmente, non riscritte) e di `docs/dati/README.md`
  (riscritto nella voce successiva). `corpus/build_manifest.py` e
  `corpus/apollon_convert.py` rieseguiti senza errori (44/45 diagrammi, 0 violazioni
  su tutti e tre i controlli) — non usano percorsi sotto `docs/dati/`, quindi lo
  spostamento non li riguarda direttamente, ma la riesecuzione conferma che nulla si
  è rotto.
- Punto aperto, non deciso qui: se e come usare `debari/` (i 20 esercizi con
  soluzione) nella pipeline — vedi la voce successiva per il ruolo previsto (test
  set) e la domanda aperta sul leave-one-out.

### [2026-09-24] Blocco 2 — docs/dati/README.md riscritto per la nuova struttura
- Contesto: la voce precedente (Blocco 1) ha spostato i file; questa voce riguarda
  solo la documentazione.
- Decisione presa: `docs/dati/README.md` riscritto da zero seguendo la nuova
  struttura (`debari/`, `studio2025_it/`, `apollon_format_reference/legacy_v3/`),
  con il ruolo previsto di ciascuna cartella dichiarato esplicitamente (in
  particolare: `debari/` come **test set**, non corpus few-shot — punto aperto sul
  leave-one-out, da discutere con i relatori).
- La correzione alla voce del 2026-09-23 che confondeva i due studi (vedi sopra,
  "Correzione (2026-09-24)" inline in quella voce) è parte di questo stesso blocco:
  non cancellata, corretta esplicitamente sul posto come richiesto.
- Verificato: nessun'altra menzione errata di "15 esercizi italiani" associata ad
  `Analysis.xlsx` trovata nel resto del repository (stesso grep del Blocco 1).

### [2026-09-24] Blocco 3 — corretto il lato del rombo in aggregazione/composizione
- Contesto: revisione ha verificato `library/lib/utils/edgeUtils.ts`
  (`getEdgeMarkerStyles`) di `@tumaet/apollon`: per **tutti** i tipi di relazione
  delle classi il marcatore grafico (triangolo, rombo, freccia) è sempre su
  `markerEnd`, mai su `markerStart`. Per `ClassInheritance`/`ClassRealization` e
  `ClassUnidirectional`/`ClassDependency` la convenzione già in uso era corretta
  (target = superclasse/interfaccia o lato della freccia). Per
  `ClassAggregation`/`ClassComposition` **non lo era**: il contenitore/aggregatore
  finiva come `source`, mentre il rombo (quindi il ruolo "contenitore") deve stare
  sul `target`.
- Decisione presa: `relationship_kind` corretta — per `AGGREGATION_OPS` lo scambio
  scatta su `("o--", "o-")` invece che su `("--o", "-o")` (e specularmente per
  `COMPOSITION_OPS` con `*`), cosicché il contenitore finisca sempre come `target`,
  qualunque sia la forma dell'operatore PlantUML usata per indicarlo. Le
  molteplicità sono scambiate insieme alle classi, come già richiesto dal fix del
  Bug 2 (2026-09-23) — nessuna regressione su quel fix.
- `prompt_template_v4.txt` corretto: le righe su `ClassComposition`/
  `ClassAggregation` ora dicono esplicitamente `"target" = the whole/container`,
  `"source" = the part`.
- `example_1_bank_loans_v4.json` ed `example_2_airtravel_v4.json` rigenerati **con
  la pipeline** (funzioni di `corpus/apollon_convert.py`, non trascritti a mano) —
  vedi `docs/dati/README.md` per dove vivono.
- Aggiunto `corpus/test_apollon_convert.py`: un test mirato che copre
  `Order "1" *-- "*" Line` (e le forme `*-`, `*-->`, `*->`, `o--`, `o-`, `--o`,
  `--*`), verificando esplicitamente quale classe finisce come `source`/`target` e
  con quale molteplicità. **Nota**: per `--o`/`--*` (simbolo adiacente al lato
  destro della riga PlantUML, cioè a `Line` in quell'esempio) l'esito atteso è
  l'opposto rispetto a `*--`/`o--` (Line come contenitore/target, non Order) — è la
  stessa regola di posizione del simbolo applicata in modo coerente, non
  un'eccezione; documentato nei commenti del test per evitare ambiguità.
- `round_trip_check` esteso: oltre a nomi/tipi di attributi e molteplicità per
  nome-classe (controllo già presente, agnostico rispetto a chi è source/target),
  ora verifica esplicitamente **quale classe è il contenitore** per aggregazione/
  composizione — con una funzione (`_expected_container`) scritta apposta senza
  richiamare `relationship_kind`, per non validare un eventuale bug futuro con la
  stessa funzione che lo causerebbe (stesso principio del fix precedente).
- Verificato dopo la correzione: `corpus/test_apollon_convert.py` — tutti i casi
  passano. Pipeline completa rieseguita: 44/45 diagrammi, **0 violazioni di
  schema, 0 problemi di integrità, 0 discrepanze di round-trip** (incluso il nuovo
  controllo sul contenitore). Controllo esplicito richiesto su `AirTravel`: nel
  JSON convertito, l'edge `ClassAggregation` tra Airline e Airplane ha
  `source=Airplane (0..*)`, `target=Airline (0..1)`; l'edge `ClassComposition` tra
  PassengerPlane e SeatCategory ha `source=SeatCategory (0..*)`,
  `target=PassengerPlane (0..1)` — Airline e PassengerPlane sono i contenitori, ora
  correttamente come `target`.
- Punto ancora non verificato (non un bug, un limite di questo ambiente): il
  rendering effettivo nell'editor Apollon online. La convenzione qui applicata
  viene dal codice sorgente (`getEdgeMarkerStyles`), non da uno screenshot
  dell'editor in azione.

### [2026-09-24] Blocco 4 — leakage: AirTravel è sia esempio statico nel prompt sia esercizio del corpus
- Contesto: `docs/dati/apollon_format_reference/example_2_airtravel_v4.json` (secondo
  esempio few-shot del prompt v4, sostituisce l'orologio digitale — vedi voce
  2026-09-23) è una copia diretta di `corpus/processed/apollon/AirTravel.json`,
  cioè lo stesso identico esercizio `AirTravel` presente nel corpus indicizzato in
  `corpus/processed/corpus.jsonl`. Se si valuta il sistema chiedendo di generare il
  diagramma per la traccia "AirTravel" usando come baseline il prompt few-shot
  statico che include AirTravel come esempio, il confronto è viziato: il modello
  vedrebbe (parte del)la risposta corretta nel prompt stesso.
- Decisione presa: aggiunto il campo `used_as_static_example` (booleano) a ogni
  record di `corpus/processed/corpus.jsonl`, scritto da
  `corpus/build_manifest.py` (non aggiunto a mano al file JSONL) tramite la
  costante `STATIC_EXAMPLE_IDS = {"AirTravel"}` definita in quello script. Solo il
  record `AirTravel` ha `used_as_static_example: true`; tutti gli altri 44 hanno
  `false`. `build_manifest.py::verify` include ora un controllo che fa fallire la
  build se l'insieme dei record flaggati non coincide esattamente con
  `STATIC_EXAMPLE_IDS`.
- **Cosa questo campo non fa**: non esclude automaticamente AirTravel da nessuna
  pipeline di valutazione — quella logica non esiste ancora (fase di valutazione
  non implementata). È solo un marcatore nei dati, da usare esplicitamente quando
  si scriverà il codice di valutazione con few-shot statico (filtrare
  `used_as_static_example == False` prima di campionare le query di test).
  Documentato qui perché sia visibile prima che qualcuno costruisca quella
  pipeline dimenticandoselo.
- Verificato: `corpus/build_manifest.py` rieseguito, stampa
  "Esempi few-shot statici (used_as_static_example=true): ['AirTravel']";
  controllo diretto sul JSONL prodotto conferma un solo record con
  `used_as_static_example: true` (AirTravel) e tutti gli altri 44 con `false`.
  Pipeline completa (`build_manifest.py` + `apollon_convert.py`) rieseguita dopo la
  modifica: 44/45 diagrammi, 0 violazioni su tutti e tre i controlli.

### [2026-09-25] Traduzione dei 15 esercizi italiani di studio2025_it: avviata, pilota su CourseManagement
- Contesto: `docs/dati/studio2025_it/Exercises.docx` contiene 15 esercizi in
  italiano con diagramma delle classi di riferimento (immagine), non ancora
  parte di `corpus/raw/`. Obiettivo: tradurli e aggiungerli al corpus nello
  stesso formato dei 45 esistenti.
- Preparazione: immagini estratte da `word/media/` del docx e associate
  all'esercizio corretto per posizione nel documento (non per nome del file
  immagine, che non segue l'ordine — verificato aprendo le immagini, non
  assunto dai nomi). Salvate in `corpus/raw/translated_it/_images/esNN.png`
  (N=1..15; esclusi i 2 esempi del prompt, "Prestiti bancari" e "Orologio
  digitale", che nel docx sono `image1.png`/`image2.png`).
- Classificazione: 13/15 immagini chiaramente diagrammi delle classi; 2 con
  ambiguità segnalate e risolte con l'utente prima di procedere (non decise
  autonomamente): l'esercizio 8 (Ascensore, frecce aperte "controlla"/
  "comunica" → mappate rispettivamente a `-->`/`..>`) e altre note minori,
  gestite caso per caso quando si arriverà a quegli esercizi.
- Pilota: `corpus/raw/translated_it/CourseManagement/` (Esercizio 1, "Sistema
  di gestione Corsi"). File prodotti: `description_it.md` (originale
  italiano, copiato senza modifiche — incluse le punteggiature mancanti nel
  sorgente, verificate nell'XML del docx, non corrette), `plantuml_it.txt`
  (trascrizione in italiano), `transcription_notes.md`, `render_it.png`
  (PlantUML locale — scaricato `plantuml-1.2023.0.jar`, l'ultima release non
  gira sul Java 8 disponibile sul sistema, errore di versione del bytecode),
  `glossary.json`, `description.md` (traduzione), `plantuml.txt` (generato da
  `corpus/apply_glossary.py`, non a mano), `metadata.txt`.
- **Due errori di trascrizione trovati dall'utente confrontando l'immagine col
  render, non da un controllo automatico**: (1) mancava l'aggregazione
  Corso—Lezione (rombo su Corso, molteplicità "1"/"1..n"); (2) la relazione
  "Iscritto" Corso—Partecipante era stata trascritta come aggregazione, è
  un'associazione semplice ("1..n"/"1..n"). Causa: linee che si incrociano
  nella zona centrale del diagramma, seguite male una prima volta. Corretti in
  `plantuml_it.txt`, non solo nel JSON derivato — vedi
  `transcription_notes.md` del pilota per il dettaglio. **Lezione per gli
  esercizi successivi**: non dichiarare corrispondenza con l'immagine senza
  che sia stata verificata da chi ha l'immagine sotto gli occhi; per questo da
  ora ogni esercizio produce `relations_table.md` (vedi sotto) come base per
  la revisione, invece di un'affermazione di equivalenza nel testo.
- **Nomi di ruolo per estremo** (nuova sintassi PlantUML per questo dialetto):
  un'immagine può mostrare un nome di ruolo su un estremo specifico di
  un'associazione (es. "+responsabile" su `DocenteInterno`), distinto da un
  nome di associazione centrato sulla linea (es. "Preallocazione") — i 45 file
  originali non distinguono i due casi, li trattano entrambi come etichetta
  `: testo`. Introdotta la sintassi `"molteplicità ruolo"` dentro le
  virgolette di un estremo (es. `"1 responsabile"`); `apollon_convert.py`
  (`split_mult_role`) la parsa separando molteplicità e ruolo, che viaggiano
  insieme nello scambio source/target di `relationship_kind` (mai l'uno senza
  l'altra) e finiscono in `edge.data.sourceRole`/`targetRole` nel JSON v4 (già
  previsti dallo schema, prima sempre vuoti). Verificato che nessuno dei 45
  file originali ha uno spazio dentro le virgolette di una molteplicità
  (scansione dedicata), quindi il loro parsing non cambia. Aggiunto un test
  dedicato in `corpus/test_apollon_convert.py` e un controllo nel round-trip.
- **Normalizzazione delle molteplicità**: PlantUML accetta sia lo stile "n"
  (`0..n`, `1..n`, `n`) sia lo stile "*" (`0..*`, `1..*`, `*`); l'immagine
  sorgente usa lo stile "n". Convenzione: `plantuml_it.txt` resta fedele
  all'immagine (stile "n"), `plantuml.txt` (inglese, quello che entra
  davvero nella pipeline/nei pochi-shot) usa lo stile "*", più comune nella
  letteratura UML in inglese e già prevalente nei 45 file originali del
  corpus. Normalizzazione fatta da `apply_glossary.py`
  (`normalize_multiplicities`), non da `apollon_convert.py` (che resta
  agnostico e accetta entrambi gli stili in lettura, invariato).
  `check_translated.py` aggiornato per trattare le due notazioni come
  equivalenti nel confronto IT/EN.
- **Nuova regola per tutti gli esercizi successivi**: dopo ogni trascrizione,
  generare `relations_table.md` con `corpus/generate_relations_table.py`
  (riparsando `plantuml_it.txt`, mai scritta a mano) — una riga per relazione
  con classe A/B, tipo, molteplicità per lato, ruoli, etichetta, più i totali.
  È la base su cui viene fatta la revisione prima di procedere con l'esercizio
  successivo.
- Verificato dopo le correzioni: `corpus/check_translated.py` OK;
  `corpus/test_apollon_convert.py` OK (incluso il nuovo test sui ruoli);
  pipeline completa (`build_manifest.py` + `apollon_convert.py`, ora estesa a
  leggere anche `corpus/raw/translated_it/`) — 46 record, 45/46 convertiti
  (Cruise sempre escluso), **0 violazioni** su schema/integrità/round-trip.
  Controllo leakage (TF-IDF + coseno) di `CourseManagement` contro i 45
  esercizi del corpus e i 20 di De Bari: top-1 = School (0.23), nessuna
  somiglianza preoccupante.
- Non ancora fatto: gli altri 14 esercizi (in attesa di conferma sul pilota
  corretto); verifica visiva del rendering dei ruoli nell'editor Apollon
  online (stesso limite ambientale già segnalato per il resto del formato v4).

### [2026-09-25] Render inglese, controllo JSON compilato, normalizzazione tipo bool
- Contesto: due aggiunte richieste dopo la correzione del pilota, applicate
  retroattivamente a `CourseManagement` e da ripetere per gli esercizi
  successivi.
- **`render_en.png`**: generato da `plantuml.txt` (inglese) con lo stesso
  `plantuml-1.2023.0.jar` locale usato per `render_it.png`, accanto ad esso in
  `corpus/raw/translated_it/<Nome>/`.
- **`relations_table.md` con nomi EN**: `corpus/generate_relations_table.py`
  ora carica anche `glossary.json` e aggiunge le colonne "Classe A (EN)" /
  "Classe B (EN)" (traduzione via `apply_glossary.apply_glossary`, non
  riparsando `plantuml.txt` — la corrispondenza esatta IT/EN è già garantita
  da `check_translated.py`).
- **Nuovo controllo in `check_translated.py`** (5°, oltre ai 4 già presenti):
  nessun termine italiano residuo in
  `corpus/processed/apollon/<id>.json` — il JSON che finisce davvero nella
  pipeline/nei pochi-shot, non solo in `plantuml.txt`. Controlla nomi di
  nodo/attributo/metodo ed etichette/ruoli degli edge. Motivazione: un bug
  nella conversione PlantUML → Apollon potrebbe introdurre o lasciar passare
  un residuo italiano che il controllo su `plantuml.txt` da solo non
  vedrebbe.
- **Normalizzazione tipo `bool` → `boolean`**: PlantUML accetta entrambe le
  grafie; l'immagine sorgente di `CourseManagement` usa `bool`
  (`VideoBeam : bool`). Convenzione: `plantuml_it.txt` resta fedele
  all'immagine, `plantuml.txt` normalizza a `boolean` (fatto da
  `apply_glossary.normalize_types`, stesso principio della normalizzazione
  delle molteplicità). `time` non viene toccato — è già un tipo valido,
  aggiunto esplicitamente all'elenco dei tipi ammessi in
  `prompt_template_v4.txt` (prima mancava, nonostante fosse già usato in 5
  attributi nei 45 esercizi originali del corpus).
- **Scansione dei tipi usati nei 45 esercizi originali** (richiesta, non
  applicata — solo segnalazione): oltre ai 7 tipi ammessi dal prompt
  (string, int, float, double, boolean, date, time — 257/129/11/43/24/36/5
  occorrenze), risultano fuori elenco: `DateTime` (12 occorrenze, distinto da
  `date`), `Long` (3), `Integer` (2, sinonimo di `int`). Il resto dei "fuori
  elenco" (~35 voci, quasi tutte con 1 occorrenza) sono in realtà tipi
  enum/classe legittimi usati come tipo di attributo (es. `Suit`, `DayOfWeek`,
  `RoomType`), non violazioni della regola "tipi semplici" — più 3 voci che
  sono artefatti di parsing di sintassi non standard in `TileOGame`
  (`Ebike` ha anche un attributo con tipo vuoto: `steel` senza tipo dichiarato
  nel sorgente). Nessuna correzione applicata ai 45 file, come richiesto.
- Verificato dopo le modifiche: `corpus/check_translated.py` OK (5/5
  controlli); `corpus/test_apollon_convert.py` OK; pipeline completa — 46
  record, 45/46 convertiti, 0 violazioni su schema/integrità/round-trip.

### [2026-09-25] corpus/raw/models -> corpus/raw/models_original (rinomina osservata, non fatta da me)
- Contesto: `corpus/raw/models/` risulta rinominata in
  `corpus/raw/models_original/` direttamente sul filesystem (visibile
  dall'IDE dell'utente, non da git — `corpus/raw/*` è gitignored, quindi git
  non registra questo cambio). Non è un'operazione che ho eseguito io in
  questa o nelle sessioni precedenti.
- Decisione presa: adattare `corpus/build_manifest.py` (`RAW_DIRS`) al nuovo
  nome invece di rinominare di nuovo o di crearne una copia — la lettura
  resta read-only, nessuno script scrive mai in `models_original/`. Il nome
  stesso ("_original") rende esplicito che è la sorgente immutabile, in
  linea con l'istruzione esplicita di questo giro di lavoro ("mai modificare
  i plantuml.txt originali").
- Verificato: `corpus/build_manifest.py` rieseguito, legge correttamente i
  45 esercizi da `models_original/`.

### [2026-09-25] FASE 1 — Normalizzazioni automatiche applicate a tutto il corpus
- Contesto: obiettivo dichiarato di portare tutti i diagrammi (44 originali +
  tradotti) a un JSON Apollon v4 uniforme. Le normalizzazioni erano finora
  fatte solo per la pipeline di traduzione (`apply_glossary.py`, testuali, su
  `plantuml.txt`); ora sono in `corpus/apollon_convert.py`, applicate a ogni
  diagramma convertito, indipendentemente dalla provenienza.
- **Tipi**: `TYPE_NORMALIZATION` — String→string, Int/Integer→int,
  Double→double, Float→float, Boolean/bool→boolean, Date→date, Time→time,
  DateTime→datetime, Long→long. Un tipo non in tabella (nome di classe/enum
  del diagramma, es. `Suit`, `RoomType`) resta invariato. Attributi senza
  tipo nel sorgente restano senza tipo (non se ne inventa uno) ma generano
  un warning elencato in `apollon_conversion_warnings` (2 casi nel corpus:
  `Frame.steel` in Ebike, `SensorController.id` in eHome2020). `datetime` e
  `long` aggiunti all'elenco dei tipi ammessi in `prompt_template_v4.txt`
  (mancavano, pur essendo già nel corpus).
- **Metodi**: `parse_method_signature` — formato unico
  `+ nome(parametri) : tipo` (o `+ nome(parametri)` senza tipo di ritorno se
  assente nel sorgente, mai inventato). Gestisce sia `Tipo nome()` (stile
  Java, tipo di ritorno prima) sia `nome():Tipo` (tipo dopo, con o senza
  spazio prima dei due punti). Il prefisso di visibilità originale
  (`+-#~`), quando presente, non viene preservato: sostituito sempre con
  `+`, stessa convenzione già in uso per gli attributi in questo modulo fin
  dalla prima versione (non una scelta nuova, resa esplicita ora che si
  applica anche ai metodi).
- **Molteplicità**: `normalize_multiplicity` (n→\*, 0..n→0..\*, 1..n→1..\*)
  applicata direttamente in `add_edge`, quindi a ogni edge del JSON finale,
  incluse le due relazioni derivate dalla reificazione delle classi
  associative (sotto). `apply_glossary.py` non duplica più questa logica:
  importa `apollon_convert.normalize_multiplicity` e
  `apollon_convert.TYPE_NORMALIZATION`, così `plantuml.txt` (l'artefatto
  testuale intermedio della pipeline di traduzione) e il JSON finale non
  possono disallinearsi sui tipi/molteplicità normalizzati.
- **Reificazione delle classi associative** (`reify_association_classes`):
  sostituisce l'approssimazione precedente (due edge a molteplicità sempre
  vuota, in uso dal 2026-09-24). Per `A "ma" -- "mb" B` con `(A,B) .. C`:
  rimuove l'edge A-B, crea A–C (A lato "1", C lato "mb") e C–B (C lato "ma",
  B lato "1") — molteplicità derivate da quelle reali dell'associazione
  base, non inventate. Se A-B non esiste nel sorgente o non ha molteplicità
  esplicite, quelle di C restano vuote con un warning. Applicata in
  `main()` tra `parse_plantuml` e `build_apollon_json`, così
  `round_trip_check` verifica anche le relazioni reificate (nessuna
  eccezione nel suo codice per questo caso). **Nessun warning di
  reificazione emesso sui 45 esercizi**: ogni classe associativa del corpus
  ha trovato un'associazione base con molteplicità esplicite — verificato
  non solo assenza di errori ma il contenuto esatto per i due casi guida:
  AirTravel (`FlightExecution "1" → Ticket "0..*"`,
  `Ticket "0..*" → Passenger "1"`, nessun edge diretto
  FlightExecution–Passenger) e University (`ResearchAssociate "1" →
  Participation "0..*"`, `Participation "1..*" → Project "1"`).
- Ogni regola ha un test dedicato in `corpus/test_apollon_convert.py`
  (`check_type_normalization`, `check_multiplicity_normalization`,
  `check_method_normalization`, `check_reification` — il caso AirTravel
  richiesto esplicitamente — `check_reification_missing_base`,
  `check_edge_always_has_all_data_fields`). Il vecchio test sui ruoli
  aggiornato per aspettarsi la molteplicità normalizzata nell'output JSON
  (il valore parsato dal sorgente resta non normalizzato, solo l'edge
  finale lo è).
- `round_trip_check` esteso: normalizza la molteplicità attesa prima del
  confronto (altrimenti "0..n" nel sorgente non avrebbe mai coincisco con
  "0..\*" nell'output); normalizza il tipo atteso degli attributi allo
  stesso modo; aggiunto un confronto sui metodi (assente prima — nessun
  controllo di round-trip esisteva sui metodi, gap pre-esistente colmato
  qui). Il confronto sui metodi riusa `parse_method_signature` (la stessa
  funzione sotto test, non una verifica indipendente come per il resto):
  limite noto, compensato dai casi hardcoded in
  `check_method_normalization`.
- Verificato dopo l'implementazione: pipeline completa rieseguita — 45/46
  diagrammi convertiti (Cruise sempre escluso), **0 violazioni** su
  schema/integrità/round-trip, warning totali scesi da 27 a 8 (spariti i 19
  warning "classe associativa approssimata", rimasti solo i 2 vincoli XOR
  scartati, le 2 classi placeholder legittime, i 2 attributi senza tipo, e
  Cruise escluso). `corpus/test_apollon_convert.py` — tutti i test passano.

### [2026-09-25] FASE 2 — Classificazione delle etichette (associazione vs ruolo): STOP 1
- Contesto: in Apollon v4 un edge ha sia `label` (nome dell'intera
  associazione) sia `sourceRole`/`targetRole` (nome di ruolo per estremo,
  finora usati solo per gli esercizi tradotti). Nei 44 esercizi originali,
  ogni etichetta `: testo` del PlantUML sorgente finisce oggi in `label`,
  indipendentemente dal fatto che semanticamente sia un nome di associazione
  o un nome di ruolo di una delle due classi.
- Estratte e classificate **tutte le 126 etichette non vuote** del corpus
  (44 originali + CourseManagement) con uno script dedicato
  (`corpus/_generate_label_classification.py`, non parte della pipeline
  permanente), che genera `corpus/label_classification.md`. Nessuna
  applicata al codice in questo passo — solo analisi, in attesa di
  conferma.
- Risultato: 84 ruolo, 29 associazione, 7 **vincolo**, 6 dubbio.
- **Categoria emersa durante l'analisi, non prevista nelle istruzioni
  originali**: "vincolo". 7 etichette (es. `{total; disjoint}`,
  `{partial; overlap}` su relazioni di generalizzazione in EUScienceConnect,
  FitnessCompanyConan, Musicmatic, Sober) non sono affatto etichette di
  relazione — sono vincoli UML standard su un insieme di generalizzazione
  (notazione OCL/UML `{disjoint,complete}` ecc.), catturati genericamente
  dal parser come `: label` perché seguono la stessa sintassi testuale.
  Segnalata come categoria a parte invece di forzarla in
  "associazione"/"ruolo": nessuna delle due sarebbe corretta, e "dubbio"
  avrebbe nascosto che in realtà QUI la natura del testo è chiara (è
  proprio un caso diverso), solo non gestibile con le due categorie
  proposte.
- 6 casi "dubbio", segnalati non decisi: `BuildingManagement` `id`/
  `username` (sospetto attributo mal posizionato più che etichetta di
  relazione), `Louvre` `RoomLocationAssignment` (composita, poco chiara),
  `Musicmatic` `suggestion` (sostantivo isolato, ruolo o associazione non
  determinabile con sicurezza), `Sober` `Book` (verbo o refuso), `TileOGame`
  `connections/tiles` (sembra unire due nomi di ruolo con "/").
- Punto di confine segnalato esplicitamente (non "dubbio", ma degno di nota):
  `ClothingCompany` `responsibleFor` — classificato "associazione" (frase
  verbale), ma vicino all'esempio "responsible" che l'utente stesso ha dato
  come caso di ruolo.
- **Non ancora fatto, in attesa della conferma dell'utente** (STOP 1):
  nessuna correzione applicata al convertitore o ai dati. Dopo conferma, la
  classificazione va congelata in `corpus/label_classification.json` (dato,
  non regole codificate) e letta da `apollon_convert.py` per instradare
  ogni etichetta verso `label` o `sourceRole`/`targetRole` di conseguenza.

### [2026-09-25] Risposte STOP 1: vincoli, qualificatori, responsibleFor, colonna "lettura"
- Contesto: risposte dell'utente alla FASE 2. **Non è stata applicata la
  classificazione ruolo/associazione al convertitore** — resta esplicitamente
  in sospeso, come richiesto ("Non applicare ancora la classificazione"). Le
  quattro decisioni sotto invece sì, perché complete e non condizionate ai 4
  dubbi ancora aperti.
- **Vincoli di generalizzazione (`{total; disjoint}` ecc.)**: implementato
  `apollon_convert.py::extract_generalization_constraints`. Rimossi da
  qualunque edge (in realtà erano già scartati in silenzio da
  `build_apollon_json`, che forza `label=""` per `ClassInheritance`/
  `ClassRealization` — la funzione li cattura PRIMA che vengano scartati,
  invece di perderli senza traccia) e salvati in un nuovo campo
  `constraints` di ogni record in `corpus.jsonl` (lista di
  `{generalizzazione: "Figlio extends Genitore", vincoli: "{...}"}`, figlio/
  genitore derivati da `relationship_kind`, non dalla posizione testuale
  source/target). Un warning per ogni vincolo estratto, elencato in
  `apollon_conversion_warnings`. Test dedicato
  (`check_generalization_constraints`) con il caso reale EUScienceConnect.
  Verificato: **7/7 vincoli estratti correttamente** (EUScienceConnect,
  FitnessCompanyConan ×2, Musicmatic ×2, Sober ×2), 0 errori sulla pipeline
  completa (45/46 convertiti, 0 violazioni su schema/integrità/round-trip).
- **BuildingManagement `id`/`username`**: riclassificati da "dubbio" a nuova
  categoria **"qualificatore"** (non prevista nelle istruzioni originali,
  introdotta su indicazione dell'utente) — verosimilmente un qualifier UML
  (es. `WebPortal[id] -> Entry`), non un nome di associazione né di ruolo.
  Restano in `label` per mancanza di un posto migliore: **Apollon non
  supporta i qualificatori UML**, nessun campo dedicato nello schema
  ufficiale né nell'editor (verificato nei sorgenti durante la migrazione a
  v4, non ri-controllato ora — coerente con l'assenza di un tipo
  "qualifier" in `DiagramEdgeType`/`DiagramNodeType` dello schema letto il
  2026-09-23). Nessuna modifica al convertitore: comportamento identico a
  prima (finiscono in `label`), cambia solo la classificazione nel report.
- **ClothingCompany `responsibleFor`**: confermato "associazione" (frase
  verbale), nonostante il confine con l'esempio di ruolo "responsible" dato
  dall'utente in precedenza.
- **Gli altri 4 dubbi** (Louvre `RoomLocationAssignment`, Musicmatic
  `suggestion`, Sober `Book`, TileOGame `connections/tiles`): lasciati
  "dubbio", in attesa — l'utente li risolverà direttamente.
- **Colonna "lettura"** aggiunta a `corpus/label_classification.md` per
  tutte le 84 righe "ruolo": frase
  `"<Classe dell'estremo scelto> è il/la <ruolo> di <altra classe>"`,
  generata automaticamente da `corpus/_generate_label_classification.py`
  (non scritta a mano), per permettere la verifica degli estremi scelti
  senza dover rileggere ogni riga PlantUML.
- **Riferimenti a `corpus/raw/models/` aggiornati** a
  `corpus/raw/models_original/` in `README.md`,
  `corpus/apollon_convert.py` (docstring) e `docs/dati/README.md` — tutti
  documenti che descrivono lo stato ATTUALE del repository. Le voci
  precedenti di questo file (`docs/decisions.md`) NON sono state riscritte:
  sono un log datato, accurate per come stavano le cose quando sono state
  scritte (la cartella si chiamava davvero `models/` a quelle date) — la
  voce del 2026-09-25 sulla rinomina resta il punto di riferimento per il
  cambio di nome. `CLAUDE.md` non menziona `models/` esplicitamente (solo
  `corpus/raw/` in generale): nessuna modifica necessaria.
- Nota aperta, non affrontata qui: il resto del contenuto sostanziale delle
  voci di stato in `README.md` (conteggi, checklist) non è stato
  aggiornato oltre al riferimento di percorso — riflette ancora lo stato
  del 2026-09-24, non le modifiche di FASE 1/2 di oggi. Non richiesto in
  questo giro, segnalato per completezza.

### [2026-09-27] Risoluzione dei 4 dubbi residui di label_classification.md
- Contesto: per ciascuno dei 4 casi rimasti "dubbio" ho estratto (senza
  modificare nulla) la riga di `label_classification.md`, le righe di
  `plantuml.txt` con le dichiarazioni delle classi coinvolte, le frasi di
  `description.md` pertinenti, e se l'etichetta coincidesse col nome di una
  classe. L'utente ha deciso sulla base di questi elementi:
- **Louvre `RoomLocationAssignment`** (`Location -- Room`) → **associazione**.
  Concatena i nomi di entrambe le classi, ma è il nome del legame nel suo
  complesso, non il ruolo di una delle due. Resta in `label`, nessuna
  modifica al testo.
- **Musicmatic `suggestion`** (`RegularUser -- Album`) → **ruolo**
  sull'estremo `Album`. Motivato da description.md: "the album of regular
  users can be turned into a suggestion to other regular users". **Nota**:
  `Album` non è mai dichiarata come classe nel `plantuml.txt` di questo
  esercizio (verificato: nessun `class Album {...}`) — è un placeholder
  creato per uso implicito in una relazione, legale in PlantUML (stesso
  meccanismo già noto per altri esercizi, es. `ResearchGroupMember` in
  ProjectManagement). Segnalato esplicitamente nella motivazione della riga,
  come richiesto.
- **Sober `Book`** (`RideSharing -- Customer`) → **associazione** (verbo
  "prenotare"). Motivato da description.md: "a customer who books 20 uses
  of the Sober ride-sharing service". Testo invariato in `label`.
- **TileOGame `connections/tiles`** (`Tile -- Connection`) → **due ruoli
  distinti**, uno per estremo, `label` vuoto: `tiles` sull'estremo `Tile`,
  `connections` sull'estremo `Connection`. Caso unico nel corpus: un'unica
  etichetta impacchettava due nomi di ruolo invece di uno. **Decisione
  esplicita dell'utente sul formato**: non generalizzare il carattere "/"
  come regola di parsing (nessun altro caso nel corpus ne ha bisogno) — va
  gestito come dato specifico di questa singola relazione. Il formato dati
  di `corpus/_generate_label_classification.py` è stato esteso per
  supportarlo: una classificazione può ora essere `"ruolo_doppio"` con una
  lista di `{testo, estremo}` invece di un singolo `(estremo, testo)` — usata
  finora da un solo caso, non un meccanismo generale già sfruttato altrove.
- **Colonna "lettura"**: generata automaticamente anche per le nuove righe
  "ruolo" (incluse le due di TileOGame). Nota: per Musicmatic l'utente aveva
  scritto a mano "Album è **la** suggestion di RegularUser"; lo script
  genera uniformemente "è il/la" per tutte le righe (placeholder non
  risolto per genere) per coerenza con le altre 84 — non corretto qui perché
  l'utente ha esplicitamente detto di voler rivedere l'intera colonna
  "lettura" prima di qualunque applicazione, quindi non ha senso risolvere
  il genere riga per riga adesso.
- Risultato in `corpus/label_classification.md`: **31 associazione, 87
  ruolo (85 singoli + 2 dal caso doppio di TileOGame), 7 vincolo, 2
  qualificatore, 0 dubbio** — tutti i 126 casi originali (127 righe in
  tabella, per lo sdoppiamento) ora hanno una classificazione.
- **Non ancora applicato**: nessuna modifica al convertitore né a
  `corpus/label_classification.json`. L'utente rivede prima la colonna
  "lettura" di tutte le 87 righe "ruolo" (era il punto esplicitamente
  rimandato nella risposta precedente, non ancora affrontato).

### [2026-09-28] Revisione di roles_to_review.md e applicazione della
### classificazione al convertitore
- Contesto: l'utente ha revisionato tutte le 67 righe incluse in
  `corpus/roles_to_review.md` (criteri A-E) più le 20 escluse come ovvie.
  Decisioni:
- **CORREZIONE — FilmSet `MostSuccessful`**: l'estremo giusto è `Film`, non
  `ScreenplayAuthor` (errore nella prima classificazione). Motivazione da
  `description.md`: "The name and most successful film of a screenwriter
  are stored" — è il *film* a essere "il più di successo" (di quello
  screenwriter), non l'autore. Lettura corretta: "Film è il MostSuccessful
  di ScreenplayAuthor". Corretto in `CLASSIFICATION`
  (`corpus/_generate_label_classification.py`) e rigenerato
  `label_classification.md`/`.json`.
- **Auto-associazioni** (`OnlineTutoringSystem.nextSession`,
  `SmartHomeAutomationSystem.nextCommand`, `TeamSportsScoutingSystem.nextReport`
  — tutte relazioni di una classe con se stessa): per queste il nome della
  classe non può disambiguare quale delle due occorrenze porta il ruolo.
  **Decisione sul formato dati**: l'"estremo" per questi 3 casi non è più un
  nome di classe ma la **posizione letterale** nella riga PlantUML
  sorgente, `"source"` o `"target"` (`"target"` = lato destro della riga,
  scelto per tutti e 3 i casi — il ruolo descrive sempre "l'elemento
  successivo"). `corpus/_generate_label_classification.py` ha guadagnato
  due funzioni per questo: `resolve_endpoint_name` (posizione → nome di
  classe, per la visualizzazione in `label_classification.md`) e
  `resolve_position` (nome di classe o posizione → posizione, per
  `label_classification.json`, che è quello che il convertitore consuma
  davvero). Aggiunto un test dedicato
  (`test_apollon_convert.py::check_label_classification_auto_association`)
  che verifica esplicitamente che il ruolo finisca su `targetRole`, mai su
  `sourceRole`, per un'auto-relazione.
- **Tutte le altre righe di `roles_to_review.md` e le 20 escluse come
  ovvie**: approvate senza modifiche.
- **`corpus/label_classification.json` creato**: `corpus/_generate_label_classification.py`
  ora scrive, oltre al `.md`, un file dati (126 voci, una per ogni
  etichetta binaria non vuota del corpus) con lo schema
  `{esercizio, source, op, target, label, tipo, estremo?, testo?, ruoli?}`
  — `estremo` è sempre una posizione (`"source"`/`"target"`), mai un nome
  di classe, cioè già risolto da `resolve_position`. Il convertitore legge
  **questo file**, non un dizionario codificato nello script.
- **`corpus/apollon_convert.py` aggiornato**: nuove funzioni
  `load_label_classification()` (carica e cache-a il JSON) e
  `apply_label_classification(model_id, relationships, classification)`,
  chiamata in `main()` subito dopo `parse_plantuml` e **prima** di
  `extract_generalization_constraints`/`reify_association_classes`. Per
  ogni relazione binaria con etichetta non vuota: `associazione`/
  `qualificatore`/`vincolo` → nessuna modifica (il vincolo resta gestito da
  `extract_generalization_constraints`, che deve girare prima); `ruolo`/
  `ruolo_doppio` → l'etichetta viene spostata in `sourceRole`/`targetRole`
  sull'estremo indicato e `label` viene svuotato. **`round_trip_check` non
  ha richiesto alcuna modifica**: confronta già `r["label"]`/
  `r["source_role"]`/`r["target_role"]` letti dal dizionario di relazione,
  che a questo punto sono già stati mutati da `apply_label_classification`
  — è quindi già "classification-aware" per costruzione, senza bisogno di
  duplicare la logica di classificazione al suo interno.
- **Fallimento esplicito su etichetta non classificata**: se una relazione
  binaria ha un'etichetta non vuota assente da `label_classification.json`,
  `apply_label_classification` la riporta in una lista `missing` (non
  solleva subito un'eccezione, per poter accumulare — stesso stile già in
  uso per schema/integrità/round-trip); `main()` somma tutte le occorrenze
  in `total_missing_labels` e fa fallire l'intera esecuzione con un
  `assert` se il totale non è zero, stampando ogni etichetta mancante prima
  di fallire. Nessuna congettura silenziosa per un'etichetta nuova non
  ancora vista da un umano.
- **Rigenerazione completa eseguita** (`build_manifest.py` →
  `apollon_convert.py` → `test_apollon_convert.py` →
  `check_translated.py --all`): 45/46 diagrammi convertiti (Cruise ancora
  escluso, costrutto diamante), **0 etichette non classificate, 0
  violazioni di schema, 0 problemi di integrità, 0 discrepanze di
  round-trip**, `CourseManagement: OK`. Relazioni finali di AirTravel e
  CourseManagement mostrate all'utente (ruoli `Source`/`Destination` su
  Airport-Flight, `Captain`/`Co-pilot` su FlightExecution-Pilot,
  `responsible` su Course-InternalTeacher; le relazioni reificate
  FlightExecution-Ticket-Passenger restano correttamente senza ruoli).
- **Limite segnalato esplicitamente, non aggirato**: non è disponibile
  Node.js/npm in questo ambiente, quindi l'"import check" richiesto (un
  test che importi davvero un JSON convertito nel pacchetto
  `@tumaet/apollon`) non è mai stato scritto e non può essere eseguito né
  verificato qui — `tools/apollon_import_check` non esiste. Restano gli
  altri tre livelli di verifica realmente eseguibili (schema, integrità
  referenziale, round-trip semantico), tutti a 0 errori. Da fare quando
  sarà disponibile un ambiente Node.

#### FASE 3 — annotazioni da valutare (NON applicate in questo giro)
- **BuildingManagement `author`**: relazione `User -> Building` senza un
  riscontro testuale individuato in `description.md` — da valutare
  l'eventuale rimozione (o va cercato meglio il testo che la giustifica).
- **HotelBookingManagementSystem `bestOffers`**: `description.md` dice
  "five best special offers", che suggerisce una molteplicità `0..5` sul
  lato `SpecialOffer`; nel `plantuml.txt` sorgente la molteplicità `0..5`
  è invece sul lato `BookingInfo` — probabile errore di trascrizione da
  verificare contro il diagramma originale.
- **TruckLogistics `driver`**: risultano due associazioni `Driver-Vehicle`
  con la stessa etichetta ma molteplicità incompatibili tra loro — quasi
  certamente un duplicato/errore di trascrizione, da controllare contro il
  PlantUML/immagine originali.

### [2026-09-28] FASE 3 STOP 2/STOP 3 — correzioni di contenuto applicate,
### meccanismo corpus/corrections/, FASE 4 (stile + diff report) e FASE 5
### (leakage)

**Meccanismo delle correzioni** (`corpus/apply_corrections.py`,
`corpus/corrections/<id>.yaml`, dipendenza nuova: `pyyaml`, aggiunta a
`requirements.txt`): ogni correzione di contenuto (refuso di nome, riga di
relazione errata/duplicata) è dichiarata come DATO in un file YAML per
esercizio, mai codificata a mano nello script. Applicata da
`corpus/build_manifest.py` subito dopo aver letto `plantuml.txt`, PRIMA che il
testo diventi il campo `diagram_plantuml` di `corpus.jsonl` — `corpus/raw/`
non viene mai scritto. Tre operazioni: `rename_token` (confine di parola,
tutto il testo), `remove_line`, `replace_line` (match esatto dopo strip).
Fallisce esplicitamente (`ValueError`) se il testo bersaglio non è trovato —
nessuna correzione si applica "a caso" o resta silenziosamente inapplicata.
L'elenco delle correzioni effettivamente applicate (con motivazione) finisce
nel campo `corrections_applied` di ciascun record, ed è anche la prima
sezione di `corpus/diff_report.md` (sotto).

**26 correzioni applicate su 15 esercizi** (STOP 2, revisione utente di
`roles_to_review.md`/tabelle a/b/c):
- **TransportCompany**: `Sting`→`String`, `VerhicleType`→`VehicleType` (enum
  già esistente coi 4 valori corretti, non un tipo esterno mancante),
  `RefrigiratedTruck`→`RefrigeratedTruck`, `Milage`→`Mileage` (variante
  ortografica accettata ma incoerente con `description.md`, che usa
  "mileage").
- **BuildingManagement**: rimossa la relazione duplicata `User->Building :
  author` (nessun riscontro testuale distinto da `owner`).
- **HotelBookingManagementSystem**: `bestOffers` — molteplicità `0..5`
  spostata dal lato `BookingInfo` al lato `SpecialOffer` ("the five best
  special offers"), senza introdurre un `1` non richiesto dal testo.
- **TruckLogistics**: le due relazioni `Driver-Vehicle : driver`
  incompatibili unificate in una sola, `Vehicle "*" -- "0..1 driver"
  Driver` — ruolo instradato con la sintassi `"molteplicità ruolo"`
  (`split_mult_role`), non con `label_classification.json` (non c'è più un
  `: label` testuale).
- **University**: `ResearchAssociate`→`ResearchAssistant` (tutte le
  occorrenze — il testo usa sempre "research assistant (RA)").
- **AirTravel**: `Nmae`→`Name`, `Enterainment`→`Entertainment`; cardinalità
  `Airport-Flight` (Source/Destination) `0..1`→`1`, `Captain` `0..1`→`1`,
  `Co-pilot` `0..2`→`1..2`, `SeatCategory-Ticket` `0..1`→`1` (lato
  SeatCategory) — tutte con riscontro testuale esplicito ("One pilot...",
  "one or two...", "a departure airport and a destination airport", "Each
  ticket is for a specific seat category"). **Respinta**: la molteplicità
  speculare `PassengerPlane-SeatCategory` (`0..1` lato PassengerPlane)
  resta invariata — il testo non lo dice esplicitamente.
- **Facepage**: `CoversionRate`→`ConversionRate`.
- **FilmSet**: `AssistentName`→`AssistantName`.
- **Musicmatic**: `lenght`→`length`.
- **PizzaDeliveryWithEntertainment**: `LinkedInAccout`→`LinkedInAccount`.
- **TileOGame**: `tunrsUntilActive`→`turnsUntilActive`.
- **AlphaInsurance**: `calculateCompenstationSum`→`calculateCompensationSum`.
- **Boeing**: `AirPlaneId`→`AirplaneId` (refuso di capitalizzazione, la
  classe è `Airplane`), `NegotiatedPice`→`NegotiatedPrice`.
- **ProjectManagement**: `WorkPackage-ResearchGroup` `0..1`→`1` (via la
  classe associativa `WorkPackageLeader` — la correzione sulla relazione
  BASE si propaga correttamente attraverso `reify_association_classes` alle
  due relazioni derivate, verificato).
- **SellingGoods**: `Order-OrderLine` `0..*`→`1..*` ("orders consist of one
  or more order lines").

**Refuso trovato ma NON applicato** (utente, STOP 2 punto a): Sober
`Top3AccidentHotSports()` — possibile refuso di "HotSpots", ma nessuna frase
di `description.md` lo giustifica (metodo senza alcun riscontro testuale) —
troppo incerto per una correzione.

**Metodo di ricerca refusi (item a)**: installato `pyspellchecker` (offline,
via pip) solo per questa analisi una tantum — NON aggiunto a
`requirements.txt`, non è una dipendenza della pipeline; per rieseguire la
stessa scansione in futuro, reinstallare con `pip install pyspellchecker`.
Ogni identificatore del corpus è stato spezzato in parole (camelCase-split)
e confrontato col dizionario; una parola non riconosciuta la cui correzione
suggerita è a edit-distance 1 e di lunghezza simile è stata proposta come
refuso candidato, poi verificata a mano contro `description.md` prima di
essere proposta (non applicata automaticamente).

**FASE 4 — controllo di stile** (`corpus/apollon_convert.py::style_check`,
integrato in `main()` come quarto livello di verifica dopo schema/integrità/
round-trip, stesso stile: accumula e fa fallire l'intera esecuzione se non
zero): tipi di attributo ammessi (primitivo normalizzato, notazione `Tipo[]`,
o classe/enum dichiarata nello stesso diagramma), formato `+ nome(...) :
tipo` per ogni metodo, nessuna molteplicità con `n` letterale residua,
nessun campo `data.*` mancante su un edge. **0 violazioni su 45 diagrammi**
dopo le correzioni.

**FASE 4 — `corpus/diff_report.py`** (nuovo script, sola lettura):
genera `corpus/diff_report.md`, le differenze tra PlantUML sorgente e JSON
Apollon finale raggruppate per causa (non per esercizio): correzioni di
contenuto (26), normalizzazione tipi negli attributi (430) e nei metodi (6),
normalizzazione molteplicità `n`→`*` (0 residue, atteso), classificazione
etichette→ruolo (83), reificazione di classe associativa (21), vincoli di
generalizzazione estratti (7), modificatori/default di attributi (6 — i 4
`{frozen}` di Sober + i 2 `{static} const ... =` di TileOGame).

**FASE 4 — `example_2_airtravel_v4.json` rigenerato** dalla pipeline
corrente (era rimasto alla versione pre-normalizzazione-tipi/pre-fix-Nmae di
FASE 1) e verificato **byte-per-byte identico** a
`corpus/processed/apollon/AirTravel.json`.

**FASE 5 — controllo di leakage ProjectManagement/FilmSet vs De Bari**
(richiesto perché i nomi sono superficialmente simili a due dei 20 esercizi
De Bari): letto `docs/dati/debari/Exercises.pdf` (20 esercizi, titoli e testo
completi). Risultato: **nessuna leakage reale**, per contenuto (non solo per
nome):
- **ProjectManagement** (corpus) vs **"1. Project Management System"** (De
  Bari): il nostro parla di Dipartimenti/Gruppi di ricerca/Ricercatori/Work
  Package/Servizi (dominio accademico); De Bari #1 parla di WorkProduct/
  Requirement/System/Manager/Team (dominio genionale di project management
  software, fonte *Learning UML* di Sinan Si Alhir) — entità completamente
  diverse, nessuna sovrapposizione oltre al nome della cartella.
- **FilmSet** (corpus) vs **"2. Hollywood Approach"** (De Bari): il nostro
  parla di Director/Actor/Screenplay/ScreenplayAuthor/Genre/Employee
  (autorship e personale di produzione); De Bari #2 parla di Scene/Setup/
  Take/Internal/External/Location (logistica di ripresa fisica, fonte *
  Formalization of UML Class Diagrams in First Order Logic* di De Giacomo) —
  entità completamente diverse.

Nessuna azione necessaria: i due esercizi possono restare nel corpus di
retrieval senza rischio di leakage con il test set De Bari.

**Dubbi FASE 3 — non corretti, annotati come limiti noti del dataset**
(decisione utente, STOP 2/3: non correggere senza aggiungere/modificare
relazioni, fuori scope di una "correzione di cardinalità"):
- **HospitalHouseMD**: "Patients are assigned one or more doctors" non ha
  una relazione diretta Patient-Doctor nel diagramma (solo indiretta via
  `Diagnosis`, che collega 1 Patient + 1 Doctor + 1 Illness per record) —
  correggerlo richiederebbe aggiungere una relazione diretta, non solo
  cambiare una molteplicità esistente.
- **TreatmentPlans**: "Every single examination is of only one type" — la
  corrispondenza esatta tra `AdvisedExamination`/`FreeExamination` e
  `ExaminationType`/`AdvisedExaminationType` non è univoca dalla sola frase
  (manca l'analogo `FreeExaminationType`) — rischio concreto di applicare
  la correzione al legame sbagliato.
- **Cruise**: già escluso dalla conversione Apollon (costrutto diamante
  n-ario `<> diamond` non supportato) — "a ticket belongs to exactly one
  cruise" passa da una relazione ternaria (Guest/Ticket/Cruise), non da un
  edge binario correggibile con lo stesso meccanismo delle altre correzioni.

**Pipeline rieseguita per intero dopo tutte le correzioni**: `build_manifest.py`
→ `apollon_convert.py` → `test_apollon_convert.py` → `check_translated.py
--all`. Risultato: 45/46 convertiti (Cruise escluso, invariato), 26
correzioni applicate, 0 etichette non classificate, 0 violazioni di schema,
0 problemi di integrità, 0 discrepanze di round-trip, **0 violazioni di
stile**, `CourseManagement: OK`.

**Riconciliazione 87 vs 83 "ruoli da etichette" in `diff_report.md`**
(richiesta utente dopo STOP 3): dei 87 ruoli di `label_classification.json`,
3 sono legittimamente scomparsi dal PlantUML corrente perché le relazioni
che li portavano sono state rimosse/riscritte dalle correzioni approvate
(`BuildingManagement User->Building:author` rimossa; le due
`TruckLogistics Driver-Vehicle:driver` unificate in una relazione senza più
un'etichetta testuale — il ruolo ora vive nella sintassi `"molteplicità
ruolo"`, non in `label_classification.json`). Il quarto scarto (87-3-1=83
invece di 84) **non era un problema dei dati**: era un bug di
`corpus/diff_report.py`, che contava una voce `ruolo_doppio` (TileOGame
`connections/tiles`, ancora presente invariata nel diagramma) come 1 sola
occorrenza invece di 2 (non la espandeva in `tiles`+`connections` come fa
`_generate_label_classification.py`). Corretto: `diff_report.py` ora
espande anche `ruolo_doppio` in piu' righe — il conteggio corretto e' **84**
(87 - 3 rimosse da correzioni), rigenerato e verificato.
