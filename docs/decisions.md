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

### [2026-09-29] Nuova categoria "chiarimento di modellazione" + 3 nuovi tipi
### di correzione (change_edge_type, remove_label, set_role) — caso Boeing

**1. Definizione della categoria e differenza da "correzione di errore"**

Tutte le correzioni fin qui (26, vedi voce precedente) erano **correzioni di
errore**: il PlantUML sorgente contraddiceva esplicitamente `description.md`
(un refuso di ortografia, una molteplicità in contrasto con un numero
scritto nel testo, una relazione duplicata senza riscontro testuale). Un
**chiarimento di modellazione** è diverso: il PlantUML sorgente non è
"sbagliato" in senso stretto — è una scelta di modellazione valida ma meno
precisa/ricca di quella che `description.md` descrive esplicitamente a
parole. Due casi tipici:
- un'etichetta testuale (`: label`) usata al posto di un costrutto UML più
  preciso che il testo implica (es. un'associazione semplice dove il testo
  descrive chiaramente un rapporto whole-part con etichetta "part of" — il
  costrutto giusto è la composizione, non un'etichetta che lo dice a
  parole);
- un ruolo o una relazione descritti in `description.md` con termini
  specifici (es. "mother"/"daughter") che nel diagramma non hanno alcun
  riscontro strutturale, nemmeno errato — semplicemente non erano stati
  modellati.

Marcata nel campo `category` di ogni operazione YAML
(`corpus/corrections/<id>.yaml`): `correzione_errore` (default, se omesso) o
`chiarimento_modellazione`. `corpus/apply_corrections.py` antepone
`[correzione_errore]`/`[chiarimento_modellazione]` a ogni voce di
`corrections_applied`; `corpus/diff_report.py` smista sulla base di questo
tag in due sezioni separate del report.

**2. Le 5 operazioni su Boeing** (`corpus/corrections/Boeing.yaml`), tutte
`category: chiarimento_modellazione`:

| # | Relazione | Prima | Dopo | Frase di `description.md` |
|---|---|---|---|---|
| 1 | Acquisition–Contract | associazione semplice, etichetta `part of` | `ClassComposition`, Contract = contenitore | "a single contract may consist of several acquisitions of airplanes" |
| 2 | Acquisition–Contract | (segue da #1) | etichetta `part of` rimossa | ridondante: il tipo composizione lo esprime già |
| 3 | Airplane–Acquisition | etichetta `part of` | etichetta rimossa, tipo invariato (associazione semplice) | "Each acquisition of an airplane has further specific details" — l'acquisizione *ha* dettagli sull'aereo, non lo contiene; l'aereo non è "parte di" l'acquisizione |
| 4 | Airplane–Acquisition | molteplicità lato Acquisition `0..1` | `1` | "they are only built on demand, meaning that first a sales agreement is made with a customer, before the airplane is actually built" (il caso "demo versions... out of scope" è esplicitamente fuori scope nel testo, non modellato) |
| 5 | Airline–Airline (auto-relazione) | nessun ruolo sui due estremi | `mother` sull'estremo `0..1`, `daughter` sull'estremo `0..*` | "main airlines often have a low cost daughter airline company. Boeing therefore keep track... of the mother-daughter relationships between airline companies" |

**3. Tre nuovi tipi di correzione** (`corpus/apply_corrections.py`), tutti
identificano la relazione per `(class_a, class_b, label)` — non per testo
grezzo della riga come `remove_line`/`replace_line` — così la correzione
resta leggibile senza dover scrivere a mano la sintassi degli operatori
PlantUML:
- **`change_edge_type`**: cambia il tipo di relazione. Per
  `aggregation`/`composition` richiede `container` (nome classe): il
  convertitore lo mette sempre come target dell'edge (vedi
  `apollon_convert.py::relationship_kind`), quindi qui basta scegliere
  l'operatore con `*`/`o` adiacente al lato giusto della riga — nessuno
  scambio manuale di classi o molteplicità, la riga viene ricostruita dai
  campi già parsati.
- **`remove_label`**: svuota l'etichetta di una relazione, lasciando
  tipo/molteplicità invariati.
- **`set_role`** — **non uno dei due tipi originariamente richiesti,
  aggiunto perché necessario per l'operazione #5 su Boeing**: Airline–Airline
  è un'**auto-associazione** (`class_a == class_b == "Airline"`), quindi
  l'estremo su cui assegnare un ruolo non può essere individuato per nome
  di classe (stesso problema già risolto per le 3 auto-relazioni di
  `label_classification.json`, dove l'estremo è codificato per posizione
  `"source"`/`"target"` nella riga PlantUML). Per `set_role` si è scelto un
  meccanismo diverso, più leggibile in un file di correzione: l'estremo si
  individua dalla sua **molteplicità attuale** (es. `endpoint_mult: "0..1"`
  → ruolo `mother`), che deve comparire su un solo estremo — fallisce
  esplicitamente se la molteplicità è ambigua (assente o presente su
  entrambi gli estremi).

Tutti e tre falliscono esplicitamente (`ValueError`) se la relazione
indicata non è individuabile in modo univoco — stessa filosofia delle
operazioni precedenti. 6 nuovi test in `corpus/test_apollon_convert.py`
(3 casi positivi + verifica dei fallimenti per container/molteplicità non
trovati o ambigui).

**4. Totali aggiornati**: **31 correzioni** (26 correzioni di errore + 5
chiarimenti di modellazione) su 15 esercizi. Pipeline completa rieseguita:
45/46 diagrammi convertiti (Cruise escluso, invariato), 0 etichette non
classificate, 0 violazioni di schema, 0 problemi di integrità, 0
discrepanze di round-trip, 0 violazioni di stile, `CourseManagement: OK`.
`corpus/diff_report.md`: 585 differenze su 9 categorie (era 8 — "Chiarimenti
di modellazione" ora sezione separata da "Correzioni di contenuto —
errori").

### [2026-09-29] 3 ulteriori chiarimenti di modellazione su AirTravel

Aggiunti a `corpus/corrections/AirTravel.yaml` (`category:
chiarimento_modellazione`, stessa categoria introdotta col caso Boeing sopra):

| # | Relazione | Prima | Dopo | Frase di `description.md` |
|---|---|---|---|---|
| 1 | Airplane–Airport | nessun ruolo sull'estremo Airport | ruolo `homeAirport` sull'estremo Airport (`0..1`, invariato) | "Each aircraft can have a home airport" |
| 2 | Airplane–FlightExecution | molteplicità lato Airplane `0..1` | `1` | "An aircraft performs several flights" — ogni esecuzione di volo è sempre eseguita da esattamente un aereo, mai zero |
| 3 | Flight–FlightExecution | molteplicità lato Flight `0..1` | `1` | "An aircraft performs several flights, the flight number and date of which are stored" — ogni esecuzione appartiene sempre a esattamente un volo |

L'operazione #1 usa `set_role` (identificazione dell'estremo Airport tramite
la sua molteplicità attuale `0..1`, non ambigua qui perché Airplane–Airport
non è un'auto-relazione — stesso meccanismo del caso Boeing, riusato senza
modifiche al codice). Le operazioni #2 e #3 usano il `replace_line`
generico, non richiedono un tipo di correzione nuovo.

**Totali aggiornati**: **34 correzioni** (26 errori + 8 chiarimenti di
modellazione: 5 Boeing + 3 AirTravel) su 16 esercizi. Pipeline rieseguita
per intero: 45/46 convertiti, 0 errori a ogni livello (schema, integrità,
round-trip, stile), `CourseManagement: OK`. `example_2_airtravel_v4.json`
rigenerato dalla pipeline e riverificato **byte-identico** al corpus (le
molteplicità/ruolo erano cambiati, l'esempio era rimasto alla versione
precedente). `corpus/diff_report.md`: 588 differenze su 9 categorie (3 in
più nella sezione "Chiarimenti di modellazione": 5 → 8).

### [2026-09-29] BuildingManagement — diagramma incompleto rispetto a
### description.md, 5 chiarimenti di modellazione + nuovo tipo `add_line` +
### esclusione paragrafo di consegna dal testo indicizzato

**Diagnosi**: revisione approfondita di BuildingManagement ha mostrato che il
diagramma PlantUML sorgente è **incompleto** rispetto a `description.md`, non
solo impreciso — mancavano relazioni intere (Entry irraggiungibile da
Building, nessuna collezione generale di immagini), non solo cardinalità
sbagliate. Tutte e 5 le proposte sono state approvate e applicate
(`corpus/corrections/BuildingManagement.yaml`, `category:
chiarimento_modellazione`):

| # | Relazione | Prima | Dopo | Frase di `description.md` |
|---|---|---|---|---|
| 1 | User–Building `author` | relazione duplicata di `owner` (era stata solo **rimossa** allo STOP 2 — revisione: andava **spostata**, non eliminata) | **User→Comment**, ruolo `author` sull'estremo User (`1`), Comment `*` | "comment on other users' buildings" |
| 2 | WebPortal–Entry `id` (qualificatore) | qualificatore su **Entry** (che non ha mai un ID nel testo) | **WebPortal→Building**, stesso qualificatore `id` | "provides a catalog of buildings" + "A building has a unique ID" |
| 3 | Building–EntryGroup | **nessuna relazione** (EntryGroup esisteva già, composto da Entry, ma irraggiungibile da Building) | **aggiunta** `Building "1" -- "1" EntryGroup` | "add additional entries to the buildings" |
| 4 | Building–Image | solo `profilePicture` (`1`), nessuna collezione generale | **aggiunta** `Building "1" -- "*" Image`, `profilePicture` invariata | "each building has a number of images, one of which is used as a profile photo" |
| 5 | WebPortal–User `username` | molteplicità **invertite** (`WebPortal "0..1"` / `User "1"` — un portale con esattamente 1 utente) | `WebPortal "1" --> "*" User` | "Visitors can register with a web portal as a user with a unique user name" (unicità *all'interno* di un portale → un portale ha molti utenti) |

`corpus/label_classification.json`/`.md` aggiornati di conseguenza: la voce
qualificatore per l'operazione #2 è stata rinominata da chiave
`(BuildingManagement, WebPortal, -->, Entry, id)` a `(..., Building, id)` in
`corpus/_generate_label_classification.py` (il convertitore fallisce se una
label non è classificata per la sua chiave esatta — la rinomina era
necessaria, non opzionale).

**Nuovo tipo di correzione — `add_line`** (`corpus/apply_corrections.py`):
serviva per i punti #3 e #4, che richiedono relazioni **assenti dal
sorgente**, non solo da correggere — nessuna delle operazioni esistenti
(`rename_token`/`remove_line`/`replace_line`/`change_edge_type`/
`remove_label`/`set_role`) può inserire una riga che non esiste. Campo:
`line` (la riga di relazione da aggiungere, inserita prima di `@enduml` se
presente). Fallisce se la riga è **già presente** (stesso principio
hard-fail, in direzione opposta: un `add_line` che troverebbe la riga già lì
non è più la correzione per cui era stata scritta). Un test dedicato in
`corpus/test_apollon_convert.py` (posizionamento prima di `@enduml` +
fallimento su riga duplicata).

**Nuovo meccanismo — esclusione di paragrafi da `description.md`**
(`corpus/clean_description.py`, `corpus/description_exclusions/<id>.yaml`):
stesso principio di `apply_corrections.py` (dato dichiarativo, mai scritto
su `corpus/raw/`, hard-fail se il paragrafo non è trovato) ma applicato al
testo di `description.md` invece che al PlantUML — chiamato da
`build_manifest.py` subito dopo la lettura di `description.md`, prima di
scrivere il campo `description` di `corpus.jsonl`. Tracciabilità nel nuovo
campo `description_exclusions_applied` del record. Applicato **solo** a
BuildingManagement: il paragrafo finale "Create a UML class diagram based on
the project description. Assign the use cases to the corresponding actors.
For the evaluation of the task, 10 meaningful use cases are sufficient. Use
the concepts of generalization and, if possible, model meaningful
relationships between the individual use cases." è una consegna per lo
studente, non un requisito di dominio — esclusa dal testo che il retriever
indicizzerà.

**SellingGoods — limite noto, NON modificato**: ha istruzioni metodologiche
intrecciate in tutto il testo (struttura a `STEP 1`–`STEP 4`, con frasi come
"First, create a class diagram for the use case described in STEP 1, and add
attributes, event types, non-default FSMs and constraints if necessary. For
each step, revise your model...") — non un singolo paragrafo isolabile come
in BuildingManagement. Un'esclusione meccanica per paragrafo non risolverebbe
il problema (l'istruzione è distribuita, non concentrata) — servirebbe una
revisione strutturale diversa, fuori scope qui. Lasciata invariata, segnalata
come limite noto.

**Limite generale del dataset**: i diagrammi di riferimento originali
(`corpus/raw/models_original/`) possono essere **incompleti**, non solo
imprecisi, rispetto alle loro `description.md` — relazioni intere mancanti,
non solo cardinalità/etichette sbagliate. Sono stati corretti **solo i casi
emersi durante la revisione svolta finora**, non un audit sistematico di
tutti i 45 esercizi per completezza strutturale. Esercizi con correzioni di
questo tipo (`category: chiarimento_modellazione`) ad oggi: **AirTravel**
(3 correzioni), **Boeing** (5), **BuildingManagement** (5). Gli altri 42
esercizi non sono stati riesaminati con lo stesso livello di dettaglio per
completezza strutturale — non è da assumere che siano privi di lacune
analoghe.

**Pipeline rieseguita per intero**: 45/46 convertiti (Cruise escluso,
invariato), **38 correzioni** (26 errori + 8 chiarimenti Boeing/AirTravel +
5 chiarimenti BuildingManagement, di cui 1 sostituiva la vecchia correzione
"remove author": netto 34 - 1 + 5 = 38), 1 paragrafo escluso da
`description.md`, 0 etichette non classificate, 0 violazioni di schema, 0
problemi di integrità, 0 discrepanze di round-trip, 0 violazioni di stile,
`CourseManagement: OK`. `example_2_airtravel_v4.json` riverificato
byte-identico al corpus (nessuna modifica ad AirTravel in questo giro).
`corpus/diff_report.md`: 592 differenze su 9 categorie.

### [2026-09-29] Annullamento delle correzioni di BuildingManagement — fedeltà
### all'originale

**Decisione utente**: `corpus/corrections/BuildingManagement.yaml` va **svuotato**
di ogni correzione di contenuto — sia la rimozione di `author` dello STOP 2
(2026-09-28) sia i 5 chiarimenti di modellazione della voce precedente
(2026-09-29). Il diagramma Apollon di BuildingManagement deve derivare
**esattamente** da `corpus/raw/models_original/BuildingManagement/plantuml.txt`,
senza alcuna relazione aggiunta/rimossa/modificata e senza alcuna
molteplicità corretta. Verificato: `diagram_plantuml` in `corpus.jsonl` è ora
**byte-identico** (dopo `.strip()`) al `plantuml.txt` originale.

**Cosa resta invariato**:
- `corpus/description_exclusions/BuildingManagement.yaml` (il paragrafo di
  consegna finale escluso dal testo indicizzato) — riguarda il testo per il
  retriever, non il diagramma, non tocca `plantuml.txt`.
- La classificazione delle etichette globali (`corpus/label_classification.json`),
  che si applica a tutto il corpus: `owner` e `author` restano ruoli
  sull'estremo User verso Building (molteplicità 1/*, come nell'originale —
  la relazione `author` era gia' presente in `plantuml.txt`, la correzione
  STOP 2 l'aveva solo *rimossa*, quindi ripristinarla è sufficiente perché
  ricompaia come ruolo, nessuna nuova voce di classificazione necessaria);
  `profilePicture` resta ruolo sull'estremo Image; `id` e `username` restano
  qualificatori (testo in `label`). **Unica correzione necessaria** alla
  classificazione: la chiave del qualificatore `id` è tornata da
  `(WebPortal, -->, Building, id)` a `(WebPortal, -->, Entry, id)` in
  `corpus/_generate_label_classification.py` — il target originale nel
  PlantUML è `Entry`, non `Building` (lo spostamento era esso stesso una
  delle correzioni annullate).

**Limiti noti del dataset per BuildingManagement — annotati, NON corretti**
(quelli che le correzioni annullate provavano a colmare):
- **Entry non collegate agli edifici**: `EntryGroup` esiste (composta da
  `Entry`) ma nessuna relazione la collega a `Building` — gli entry sono
  strutturalmente irraggiungibili da un edificio, nonostante
  description.md dica "add additional entries to the buildings".
- **Commenti senza autore**: `Building --> Comment` esiste, ma nessuna
  relazione collega `Comment` a un `User` autore, nonostante description.md
  dica "comment on other users' buildings".
- **Nessuna relazione WebPortal–Building**: il qualificatore `id` è
  sull'estremo `Entry` (che non ha mai un ID nel testo), non su `Building`
  (che ce l'ha esplicitamente: "A building has a unique ID") — manca quindi
  una relazione diretta WebPortal–Building nonostante "provides a catalog of
  buildings".
- **Building con una sola immagine**: solo `profilePicture` (`1`), nessuna
  collezione generale di immagini, nonostante "each building has a number of
  images".
- **WebPortal–User `username` con molteplicità sospette**: `WebPortal
  "0..1"` / `User "1"` (un portale con esattamente 1 utente) non corrisponde
  al senso di "Visitors can register with a web portal as a user with a
  unique user name" (un portale ha molti utenti).

**Totali aggiornati** (contati direttamente da `corrections_applied` in
`corpus.jsonl`, non a mente — corregge anche un errore aritmetico nelle voci
precedenti, che riportavano "26 errori" invece di 25): **33 correzioni** (25
errori + 8 chiarimenti di modellazione: 5 Boeing + 3 AirTravel —
BuildingManagement non contribuisce più) su 15 esercizi (era 16). Pipeline
rieseguita per intero: 45/46
convertiti (Cruise escluso, invariato), 0 etichette non classificate, 0
violazioni di schema, 0 problemi di integrità, 0 discrepanze di round-trip,
0 violazioni di stile, `CourseManagement: OK`, `example_2_airtravel_v4.json`
riverificato byte-identico. `corpus/diff_report.md`: 588 differenze su 9
categorie (tornato al valore di prima dei 5 chiarimenti BuildingManagement,
meno le differenze introdotte da quelli).

### [2026-09-29] Riclassificazioni: fine della categoria "qualificatore",
### auto-relazione Louvre "coach", rimozione del marcatore di verso di
### lettura PlantUML ('>'/'<')

**1-2. BuildingManagement `id`/`username`: da qualificatore a ruolo.**
Decisione utente: non serviva la lettura UML "qualifier" — `id` e
`username` sono semplicemente il nome della proprietà di navigazione,
stessa convenzione già in uso per `profilePicture`/`wheel`/ecc. Entrambe
riclassificate `ruolo` in `corpus/_generate_label_classification.py`:
`WebPortal→Entry` targetRole `id`, `WebPortal→User` targetRole `username`,
label svuotato in entrambi i casi. **La categoria "qualificatore" ha ora 0
voci** — lasciata documentata nel convertitore (`apollon_convert.py::apply_label_classification`,
`if tipo in ("associazione", "qualificatore", "vincolo")`) e nel generatore,
non rimossa dal codice, per un futuro caso reale che non si presti alla
stessa lettura come ruolo.

**3. Louvre `hasCoach >` (auto-relazione Employee-Employee): da associazione
a ruolo.** Senza un ruolo esplicito i due estremi di un'auto-relazione non
si distinguono (stesso principio già applicato alle 3 auto-relazioni di
FASE 2). Ruolo `coach` — **non** `hasCoach`: il nome del ruolo è il
sostantivo, non la frase verbale usata come etichetta — sull'estremo con
molteplicità `0..1` (posizione `target` nella riga PlantUML), label
svuotato. Questo ha richiesto un'estensione al formato dati: la voce
`"ruolo"` di `CLASSIFICATION` accetta ora, oltre alla forma esistente
(stringa = solo l'estremo, il testo del ruolo coincide con l'etichetta),
anche un dict `{"estremo": ..., "testo": ...}` quando il nome del ruolo deve
differire dall'etichetta originale — retrocompatibile, tutte le altre voci
`"ruolo"` esistenti restano invariate (stringa semplice).

**4. Rimozione del marcatore di verso di lettura PlantUML.** Verificato:
`hasCoach >` (Louvre), `leads >` e `teaches >` (University) finivano
**letteralmente** nel JSON compilato con il carattere `>` finale — il
simbolo indica solo in che verso leggere l'etichetta (`A -- B : verbo >` si
legge "A verbo B"), non fa parte del nome. Nuova funzione
`apollon_convert.py::strip_reading_direction()`, chiamata da
`parse_plantuml` su ogni etichetta estratta (rimuove un `' >'`/`' <'`
finale o un `'< '`/`'> '` iniziale, con esattamente uno spazio — verificato
che non ci sono altri casi nel corpus con spaziatura diversa). Le chiavi di
`label_classification.json`/`.py` per questi 3 casi sono state aggiornate
di conseguenza (senza il marcatore): `leads`/`teaches` restano
`associazione` (non sono auto-relazioni, nessun bisogno di un ruolo).
Verificato **esaustivamente** su tutti i 45 JSON compilati: nessun
carattere `>`/`<` residuo in `label`/`sourceRole`/`targetRole` su nessun
edge. Nuovo test in `corpus/test_apollon_convert.py::check_strip_reading_direction`.

**Pipeline rieseguita per intero**: 45/46 convertiti (Cruise escluso,
invariato), 0 etichette non classificate, 0 violazioni di schema, 0
problemi di integrità, 0 discrepanze di round-trip, 0 violazioni di stile,
`CourseManagement: OK`, `example_2_airtravel_v4.json` riverificato
byte-identico. `label_classification.json`: 122 voci (associazione 28,
ruolo 88, vincolo 7, qualificatore 0, dubbio 0). `corpus/diff_report.md`:
591 differenze su 9 categorie.

### [2026-09-30] Traduzione Gruppo A (es. 2-5): Hospital, ResearchCenter, MilanLibrary, Bookmaker

- **Glossario condiviso** `corpus/raw/translated_it/glossary_shared.json` (Nome, nome, Data,
  Cognome, cognome, Cliente, cliente, Persona, Utente, Editore): `apply_glossary.load_merged_glossary`
  unisce condiviso + locale e fallisce se lo stesso termine ha traduzioni diverse. `check_translated.py`,
  `generate_relations_table.py`, `apply_glossary.py` usano tutti la stessa funzione.
  `load_term_glossary` ora applica anche chiavi a frase (parole con spazio singolo, es. etichetta
  "Appartiene a"); chiavi con altra punteggiatura restano solo di riferimento.
- **Cartelle in inglese** (id corpus = nome cartella): Hospital, ResearchCenter, MilanLibrary, Bookmaker.
- **Tipi non standard mappati dal glossario** (il formato ammette solo primitivi/classi dichiarate):
  MilanLibrary `Number`->`int`, `Calendar`->`datetime` (da confermare).
- **Inferenza dichiarata**: Bookmaker `accettaScommessa(sc : Scommettitore, s : Scommess...` e' troncato
  nell'immagine, completato con `Scommessa` (vedi transcription_notes).
- **Classificazione etichette NON applicata**: proposte in `corpus/label_proposals_gruppoA.md` (chiavi
  inglesi). `corpus.jsonl` e i JSON Apollon dei 4 esercizi sono stati generati con le proposte iniettate
  *solo in memoria* (0 errori a ogni livello): `python corpus/apollon_convert.py` da solo fallisce finche'
  le proposte non sono approvate e portate in `_generate_label_classification.py`.
- **Leakage** (nuovo `corpus/leakage_check.py`, TF-IDF): tutti < 0.4; max ResearchCenter vs
  ProjectManagement 0.273, MilanLibrary vs De Bari 18 0.141, Hospital vs De Bari 4 0.115.
- Render generati con `.tools/plantuml-old.jar` (Java 8), non verificati contro l'immagine.

### [2026-09-30] Gruppo A — esito revisione parziale
- **Etichette approvate** (label_proposals_gruppoA.md, incluse request destination/source come ruoli su
  Library): portate in `CLASSIFICATION` di `_generate_label_classification.py`. NON rigenerati
  `label_classification.md/.json` (attesa chiusura revisione visiva): fino ad allora `apollon_convert.py`
  fallisce sulle 11 etichette dei 4 esercizi (corpus.jsonl/JSON attuali dei 4 sono provvisori).
- **Tipi non standard** `Number`->`int`, `Calendar`->`datetime` approvati, spostati in `glossary_shared.json`.
- **REGOLA (tutti gli esercizi)**: `plantuml_it.txt` trascrive l'IMMAGINE, mai il testo. Se l'immagine
  contraddice il testo: trascrivere l'immagine, annotare in `transcription_notes.md`, proporre una
  correzione (commentata) in `corpus/corrections/<id>.yaml`; decide l'utente.
  - Hospital: ripristinato il rombo su `PersonaleMedico` (come nell'immagine); proposta di inversione
    in `corpus/corrections/Hospital.yaml` (non attiva).
  - Bookmaker `accettaScommessa`: trascritto solo il leggibile (`... s : Scommess..`, parentesi non chiusa);
    `Scommess`->`Bet` nel glossario; proposta di completamento in `corpus/corrections/Bookmaker.yaml`
    (non attiva). `style_check` segnalera' il metodo (manca ")") finche' non si decide.
- `.tools/` era gia' nel `.gitignore`.

### [2026-09-30] Gruppo A — chiusura
- **Hospital**: ingrandimento 6x di `es02.png` (x 560-720, y 620-710): il vertice del rombo tocca `RepartoConStaff`
  (opzione b). La lettura a bassa risoluzione "rombo su PersonaleMedico" era errata; `plantuml_it.txt` ripristinato a
  `RepartoConStaff "1" o-- "1..n" PersonaleMedico`, `corpus/corrections/Hospital.yaml` vuoto, render rigenerati.
- **Bookmaker**: correzione attiva (`correzione_errore`, "nome troncato nell'immagine"): `acceptBet(sc : Bettor, s : Bet..`
  -> `acceptBet(sc : Bettor, s : Bet)`. Nessuna deroga a `style_check`.
- Rigenerati `label_classification.md/.json` (133 voci JSON = 32 associazione + 93 ruolo + 1 ruolo_doppio + 7 vincolo; 95 istanze di ruolo; 134 righe nel .md, vedi riconciliazione sotto) e pipeline
  completa: 49/50 convertiti (Cruise escluso), 34 correzioni, 0 etichette non classificate, 0 errori di schema,
  integrita', round-trip, stile; test OK; `check_translated` 5/5; `example_2_airtravel_v4.json` identico.

### [2026-09-30] Riconciliazione conteggi label_classification (nessuna modifica ai dati)
Tre unita' di misura diverse erano state mescolate:
- **Voci JSON** (una per etichetta, chiave esercizio/source/op/target/label): **133** = 32 associazione + 93 ruolo
  + 1 ruolo_doppio (TileOGame `connections/tiles`) + 7 vincolo + 0 qualificatore.
- **Righe del .md / contatore stampato dallo script**: **134** = 133 + 1, perche' il ruolo_doppio e' espanso in 2 righe
  (e il contatore "ruolo" conta le istanze). Da qui "32 + 95 + 7 = 134".
- **Istanze di ruolo**: **95** = 93 + 2 (ruolo_doppio).

Perche' 95 e non 97: le 97 istanze attese sono quelle del dict `CLASSIFICATION` (137 voci, 97 istanze di ruolo:
87 + 2 ex-qualificatori `id`/`username` + `hasCoach` + 7 Gruppo A). Il generatore emette pero' solo le voci la cui
relazione esiste nel PlantUML *corretto*; 4 voci del dict non lo sono, per correzioni approvate e ancora attive:
| Voce del dict | Tipo | Motivo dell'assenza |
|---|---|---|
| TruckLogistics `Driver --> Vehicle : driver` | ruolo | rimossa (`remove_line`, STOP 2) |
| TruckLogistics `Vehicle --> Driver : driver` | ruolo | riscritta come `Vehicle "*" -- "0..1 driver" Driver` (ruolo nella sintassi tra virgolette, non piu' un'etichetta) |
| Boeing `Acquisition -- Contract : part of` | associazione | `remove_label` (chiarimento di modellazione) |
| Boeing `Airplane -- Acquisition : part of` | associazione | `remove_label` (chiarimento di modellazione) |

Quindi: ruoli 97 - 2 = 95; associazioni 34 - 2 = 32; voci 137 - 4 = 133. Il ruolo `driver` di TruckLogistics resta nel
diagramma finale (targetRole su Driver), solo non passa da `label_classification.json`. BuildingManagement `author`,
ripristinato con l'annullamento delle correzioni, e' tra le voci emesse. Le 4 voci orfane restano nel dict (innocue).

### [2026-09-30] Traduzione Gruppo B (es. 6-9): UniversityExams, Restaurant, ElevatorControl, RealEstateAgency
- Cartelle/id: `UniversityExams` (non "University", gia' usato da un esercizio originale), `Restaurant`,
  `ElevatorControl`, `RealEstateAgency`.
- Regola "trascrivere l'immagine" applicata: refusi/troncamenti trascritti fedelmente (`sttring`, `d..`, `sting`,
  `kay`), mappati su se stessi nel glossario; correzioni proposte COMMENTATE in `corpus/corrections/`
  (UniversityExams, Restaurant, RealEstateAgency). Nessuna attiva.
- Ingrandimenti su es. 6 (tre zone) e su es. 8 (le due frecce "controlla"): coordinate in transcription_notes.
  Es. 8: freccia verso Porta tratteggiata (`..>`); verso Ascensore trascritta continua (`-->`) ma NON distinguibile
  con certezza (un solo buco nella linea).
- Es. 6: nota/commento sulla classe Persona esclusa, nessuna generalizzazione (decisione utente).
- Proposte aperte (non applicate): etichette in `corpus/label_proposals_gruppoB.md` (10, tutte associazione);
  tipo `currency -> double` nel glossario condiviso; estendere `normalize_multiplicity` a `N` maiuscola (es. 9).
- Glossario condiviso: spostati i termini ormai comuni a piu' esercizi (Corso, Studente, Numero, numero, tipo,
  telefono, durata, DataNascita/dataNascita, codice/Codice, citta/Citta) — nessun conflitto.
- Stato pipeline: senza le proposte `apollon_convert.py` fallisce (10 etichette non classificate; stile: `d..`,
  `sttring`, `sting`, `currency`). Con proposte iniettate SOLO in memoria: 53/54 convertiti, 0 errori a ogni
  livello, test OK, check_translated 9/9. `corpus.jsonl`/JSON dei 4 esercizi sono provvisori (run in memoria).
- Restaurant/description.md: "who serve customers" -> "who wait on customers" per un falso positivo lessicale del
  controllo "residuo italiano" (`serve` e' sia italiano sia inglese).
- Leakage: tutto < 0.4 (max UniversityExams vs University 0.231, Restaurant vs De Bari 10 Restaurant 0.183).

### [2026-09-30] Gruppo B — chiusura
- **Regola (utente): mai modificare i dati per far passare un controllo.** Ripristinato "who serve customers" in
  Restaurant/description.md; il falso positivo si corregge nel controllo: `check_translated.ENGLISH_HOMOGRAPHS`
  (whitelist di parole valide in inglese che coincidono con chiavi italiane del glossario, oggi solo `serve`;
  aggiunte caso per caso con l'esercizio che le motiva). Test: `check_english_homograph_whitelist`.
- Correzioni attivate (`correzione_errore`): UniversityExams `d..`->`date`, `sttring`->`string`; Restaurant
  `sting`->`string`; RealEstateAgency `kay`->`key`.
- Regole globali approvate: `currency -> double` nel glossario condiviso dei tipi; `normalize_multiplicity` estesa a
  `N` maiuscola (`N`, `x..N` -> `*`), usata anche da `style_check` e `diff_report`. Test: `check_shared_type_glossary`,
  casi `N` in `check_multiplicity_normalization`.
- Etichette approvate (10, tutte associazione) portate in `CLASSIFICATION`. ElevatorControl "controls" verso
  Elevator resta `-->` con nota di incertezza, salvo diversa indicazione dopo verifica visiva.
- Pipeline ufficiale completa: 53/54 convertiti (Cruise escluso), 38 correzioni, `label_classification.json`
  143 voci (42 associazione + 93 ruolo + 1 ruolo_doppio + 7 vincolo; 95 istanze di ruolo), 0 etichette non
  classificate, 0 errori di schema/integrita'/round-trip/stile, test OK, check_translated 9/9, diff_report 607
  differenze; `example_2_airtravel_v4.json` identico.

### [2026-10-01] Gruppo B — correzioni dopo verifica visiva dell'autore + controllo nomi di ruolo
- **ElevatorControl**: entrambe le frecce "controlla" sono tratteggiate (verifica visiva dell'autore); la freccia
  verso Ascensore, prima trascritta `-->`, diventa `..>` in `plantuml_it.txt` (correzione di trascrizione, non di
  dato). Aggiornati transcription_notes, relations_table, render, e la chiave in `CLASSIFICATION`
  (`ElevatorController ..> Elevator : controls`, sempre associazione).
- **UniversityExams**: classe associativa `Iscritto_a` tradotta `EnrolledIn` (prima `Enrollment`); termine solo
  nel glossario dell'esercizio. `description.md` non contiene il nome della classe: invariata.
- **Controllo nomi di ruolo agli estremi** (es. 1-9, ingrandimenti 1.8-2.2x a quadranti + 2x a quadranti di
  es06): in UniversityExams **nessun nome di ruolo trovato** vicino alle classi (solo le 4 etichette gia'
  trascritte e le molteplicita'); nessuna modifica. Testi in posizione di ruolo trovati altrove: es. 3
  "Guida" (estremo RicercatoreSenior) e "Guidato da" (estremo Team), es. 4 "Possiede" (estremo Utente), es. 5
  i 5 nomi minuscoli (gia' ruoli via classificazione). Elenco completo nel messaggio di revisione; nessuna
  modifica in attesa di decisione utente.
- **relations_table.md**: colonne "Ruolo estremo A" e "Ruolo estremo B" sempre presenti ("—" se vuote) al posto
  della colonna unica "Ruoli". Rigenerate per ora solo UniversityExams ed ElevatorControl.
- **Procedura gruppi C e D**: controllare gli estremi di ogni relazione per i nomi di ruolo, oltre alle
  molteplicita'.
- Pipeline NON rieseguita: finche' non si rigenerano `label_classification.json` e la pipeline, la chiave
  ElevatorControl `..>` Elevator risulta non classificata nel json attuale.

### [2026-10-01] Regola: verbi vicino agli estremi = nome di associazione, non ruoli
- **Regola (utente)**: un verbo scritto vicino all'estremo di una relazione è il nome dell'associazione letto in
  un verso, non un nome di ruolo. Un verbo e la sua forma nel verso opposto (es. "Guida" / "Guidato da") sono la
  stessa associazione: si trascrive una sola etichetta, non due.
- Applicata: ResearchCenter "Guida"/"Guidato da" e MilanLibrary "Possiede" restano nomi di associazione
  (classificazione invariata). UniversityExams: nessun ruolo da aggiungere (verificato dall'utente).

### [2026-10-01] Traduzione Gruppo C (es. 10-12): OilWells, RepairShops; es. 12 Palestra ESCLUSO
- **Es. 12 Palestra escluso** (decisione utente presa in anticipo): la classe senza nome (Numero : Integer,
  Frequenza : String, classe associativa sulla relazione Scheda–Esercizio) non riceve un nome univoco dalla
  traccia. La frase pertinente è "Ad ogni cliente è associata una scheda – per la sala pesi – che definisce gli
  esercizi da compiere, il numero di ripetizioni e la frequenza": descrive gli attributi, non nomina la classe.
  Nessun file creato per es. 12.
- `strip_reading_direction` esteso ai marcatori attaccati alla parola ("<Lavora", "effettua>"), stereotipi
  `<<...>>` esclusi; test aggiunto. Nessuna etichetta esistente cambia (0 non classificate nella run).
- es. 11: "<Lavora" -> "Lavora" (etichetta e nome della classe associativa, decisione utente).
- Proposte aperte: etichette in `corpus/label_proposals_gruppoC.md` (2 vincoli, 5 associazioni); correzione
  commentata in `corpus/corrections/RepairShops.yaml` (`string{1..*}` -> `string[]`).
- Glossario condiviso: spostati Area, Superficie, anniServizio (comuni a piu' esercizi), nessun conflitto.
- Pipeline: senza proposte fallisce su 7 etichette non classificate; con proposte in memoria 55/56 convertiti,
  0 errori, test OK, check_translated 11/11. corpus.jsonl/JSON dei 2 esercizi provvisori.
- Leakage: tutto < 0.4 (max RepairShops vs TransportCompany 0.210, vs De Bari 9 Auto Repair 0.157).

### [2026-10-01] Gruppo C — decisioni; regole "sostantivo = ruolo" e "classe associativa senza nome"
- **Regola (utente): un'etichetta che è un sostantivo è un ruolo, anche se scritta al centro della linea** (la
  posizione non conta). Applicata a OilWells "location" (da "luogo"): ruolo sull'estremo Area, label vuoto
  (lettura "Area è il location di OffshoreWell"). Completa la regola precedente: verbo = nome di associazione.
- Approvate le altre 6 etichette (2 vincoli OilWells, 4 associazioni RepairShops), portate in `CLASSIFICATION`.
- RepairShops: correzione attiva (`correzione_errore`) `phoneNumbers : string{1..*}` -> `string[]`.
- **Convenzione meccanica (utente): una classe associativa senza nome nell'immagine si chiama concatenando le due
  classi che collega** (es. `SchedaEsercizio` / `WorkoutPlanExercise`). È una convenzione, non un nome ricavato
  dal contenuto; va dichiarata nelle transcription_notes. Applicata a es. 12 Palestra, quindi **Palestra non è più
  escluso**: creato come `Gym` con la procedura standard (la voce precedente che lo escludeva è superata).
- Gym: etichette "ServiziAggiuntivi"/"ServiziBase" proposte come ruoli sull'estremo Service (sostantivi), in
  attesa di approvazione.

### [2026-10-01] Gruppo C chiuso (Gym approvato)
- Ruoli Gym approvati (AdditionalServices, BaseServices sull'estremo Service) e portati in `CLASSIFICATION`;
  `corpus/label_proposals_gruppoC.md` rimosso.
- Classificazione rigenerata ufficialmente: 152 voci JSON (46 associazione + 96 ruolo + 1 ruolo_doppio +
  9 vincolo; 98 istanze di ruolo). Pipeline ufficiale, nessuna voce solo in memoria: 56/57 convertiti
  (Cruise escluso), 39 correzioni, 9 vincoli di generalizzazione, 0 etichette non classificate, 0 errori di
  schema/integrita'/round-trip/stile, test OK, check_translated 12/12, diff_report 616 differenze,
  `example_2_airtravel_v4.json` identico.

### [2026-10-01] Gruppo D (es. 13-15) — trascrizione, in attesa di revisione
- Id: es. 13 Eat@Home = `EatAtHome`, es. 14 Compagnia di assicurazioni = `InsuranceCompany`, es. 15
  Appartamento e Palazzo = `ApartmentBuilding`.
- es. 13 (diagramma gia' in inglese, decisione utente): `plantuml_it.txt` copia fedele, glossario identita';
  `Currency` -> `double` aggiunto al glossario condiviso (accanto a `currency`). Note escluse; Ingredient
  ("alternativa" secondo una nota) trascritta come disegnata.
- es. 13 `status : enum{...}` inline: non rappresentabile, style check fallisce. Proposta commentata in
  `corpus/corrections/EatAtHome.yaml`: (a) enum separata (serve estendere le correzioni con un'op a blocco) o
  (b) `replace_line` -> `status : string`. Non applicata.
- es. 14: Compagnia–Contratto senza molteplicita' (verificato), `ImportoAssicurato` senza tipo: trascritti cosi'.
  "Furto" vs testo "rischi diversi": contraddizione dubbia, `rename_token` commentato in
  `corpus/corrections/InsuranceCompany.yaml`.
- es. 15: `+` davanti ai nomi di classe = visibilita' dello strumento, non trascritta; "e' posseduto" -> `isOwnedBy`.
- Etichette proposte (4 associazioni) in `corpus/label_proposals_gruppoD.md`, non applicate.
- `leakage_check.py`: aggiunta opzione `--vs <id>` per riportare il punteggio verso un esercizio specifico
  (richiesta utente: es. 15 vs House anche sotto soglia). ApartmentBuilding vs House = 0.024.
- Pipeline ufficiale: fallisce su 4 etichette non classificate + 1 errore di stile (EatAtHome enum). Run
  provvisoria in memoria con le proposte: resta solo l'errore di stile EatAtHome (dato, in attesa di decisione).
  check_translated 15/15, test OK, diff_report 617. Leakage: tutto < 0.4.

### [2026-10-01] Gruppo D chiuso — decisioni utente; traduzione dei 15 esercizi italiani completata
- Etichette approvate (4 associazioni: EatAtHome makes/contains/contains, ApartmentBuilding isOwnedBy), portate in
  `CLASSIFICATION`; `corpus/label_proposals_gruppoD.md` rimosso.
- **Convenzione meccanica (utente): enum inline -> enumerazione separata `<Classe><Attributo>`** con i valori
  originali invariati (anche con spazi) e l'attributo tipizzato con la nuova enumerazione. Applicata a EatAtHome:
  `Order.status : enum{...}` -> `status : OrderStatus` + `enum OrderStatus {placed, in preparation, in delivery,
  delivered, canceled}`. Correzioni attive in `corpus/corrections/EatAtHome.yaml`, categoria
  `chiarimento_modellazione` (il diagramma non e' sbagliato, cambia solo la notazione).
- **Nuova operazione di correzione `add_block`** (`corpus/apply_corrections.py`, ora 8 operazioni): aggiunge una
  dichiarazione multi-riga di classe/enum prima di `@enduml`; hard-fail se il blocco non e' esattamente una
  dichiarazione chiusa (1 classe, 0 relazioni) o se il nome e' gia' dichiarato. Test
  `check_corrections_add_block`.
- **EatAtHome contiene due alternative** di modellazione degli ingredienti: gli attributi `ingredients` /
  `allergen_information` di Dish e la classe `Ingredient` (disegnata in grigio, "alternativa" secondo una nota
  dell'autore che chiede di rimuovere gli attributi in quel caso). Entrambe mantenute per fedelta' all'immagine.
- InsuranceCompany "Furto" vs testo "rischi diversi": **caso dubbio, nessuna correzione**; il `rename_token`
  resta commentato in `corpus/corrections/InsuranceCompany.yaml`.
- InsuranceCompany, frasi di consegna ("We are interested in describing the problem domain, ... We produce a class
  diagram."): **separabili** (un unico tratto contiguo senza contenuto di dominio) -> caso BuildingManagement,
  escluse con `corpus/description_exclusions/InsuranceCompany.yaml`. Poiche' l'esclusione e' a meta' riga,
  `clean_description.apply_exclusions` ora ripulisce spazi doppi / a inizio-fine riga (BuildingManagement
  verificato invariato; test `check_description_exclusion_mid_line`). description.md non modificato.
- **Limite generale: la visibilita' di attributi e metodi non e' conservata** (sempre `+` nel JSON Apollon;
  25 membri `-` in 4 esercizi). Documentato in `corpus/apollon_limitations.md` §9.
- Pipeline ufficiale, nessuna voce solo in memoria: 59/60 convertiti (Cruise escluso), 41 correzioni, 2 esclusioni
  di paragrafi, `label_classification.json` 156 voci (50 associazione + 98 ruolo + 9 vincolo; ruolo_doppio su 2
  righe), 0 etichette non classificate, 0 errori schema/round-trip/stile, warning 27, test OK, check_translated
  15/15, diff_report 618, `example_2_airtravel_v4.json` invariato. Leakage Gruppo D tutto < 0.4
  (max InsuranceCompany vs AlphaInsurance 0.192; ApartmentBuilding vs House 0.024).

### [2026-10-01] EatAtHome — due alternative: confermato "lasciamo cosi'"
- Proposta di applicarne una sola (nota su Ingredient: "in that case REMOVE ingredients and allergens from the
  dish class") valutata e **scartata dall'utente**: il diagramma resta con entrambe le alternative (attributi
  `ingredients`/`allergen_information` su Dish e classe `Ingredient`), come da voce del Gruppo D. Nessuna
  correzione aggiunta, nessuna nuova operazione.
- **Precisazione (stesso giorno)**: il diagramma contiene **due alternative** di modellazione degli
  ingredienti: gli attributi `ingredients`/`allergen_information` di Dish e la classe `Ingredient`. La nota
  sull'immagine dice di **non tenerle insieme**. Sono state mantenute entrambe **per fedeltà all'immagine,
  come scelta consapevole dell'autore**, senza nessuna modifica al diagramma. Ne segue che le note dei
  diagrammi non sono sempre semplici commenti: alcune contengono istruzioni di modellazione (verifica sugli
  altri 14 esercizi nella voce successiva).
- **Limite noto**: aggiunta la §10 in `corpus/apollon_limitations.md` e la voce in `docs/STATUS.md`.
- **Filtrabilità**: nuovo file dati `corpus/known_issues.yaml` (`{id: [codici]}`), letto da
  `corpus/build_manifest.py`. Ogni record di `corpus.jsonl` ha il campo `known_issues` (lista vuota se
  l'esercizio non ha problemi noti) e EatAtHome ha `["two_alternative_models"]`. I codici ammessi sono in
  `KNOWN_ISSUE_CODES`; un codice sconosciuto, un id inesistente, una lista vuota o un codice duplicato fanno
  fallire la pipeline. Il file non tocca né il diagramma né la descrizione. Test:
  `check_known_issues_validation`.

### [2026-10-01] Note dei diagrammi negli altri 14 esercizi tradotti — solo verifica, nessuna modifica
- Ho controllato le immagini sorgente (`corpus/raw/translated_it/_images/es01..es15.png`, tranne es13), non
  solo le transcription_notes.
- **Solo es. 6 UniversityExams** ha una nota, e contiene un'istruzione di modellazione: propone una
  soluzione alternativa con una classe `Persona` che generalizza Studente e Professore, con l'attributo
  `dataNascita` e l'associazione `nato_a` verso Luogo ("verrà presentata nella prossima esercitazione"). Era
  già stata esclusa per decisione utente (transcription_notes, punto 1), quindi nel corpus c'è solo la
  soluzione disegnata, senza alternative.
- Gli altri 13 esercizi non hanno note. `{disjoint, complete}` in es. 10 OilWells è un vincolo di
  generalizzazione già trascritto, non una nota.

### [2026-10-02] Test set De Bari — FASE 1: split corpus / debari_test (refactoring senza cambi di comportamento)
- Obiettivo del passo: i 20 esercizi di `docs/dati/debari/Exercises.pdf` portati in Apollon v4 con la stessa
  pipeline del corpus, come **test set tenuto fuori dal retrieval** (ground truth di De Bari et al.).
- `corpus/apollon_convert.py`: il corpo di `main()` diventa `convert_split(jsonl_path, out_dir)`; CLI
  `--split corpus|debari_test` (default `corpus` = comportamento storico). `debari_test` legge/scrive
  `corpus/processed/testset_debari.jsonl` e `corpus/processed/apollon_debari/`.
- `corpus/build_manifest.py`: stessa CLI. Split `debari_test`: raw `corpus/raw/debari_test/`, uscita
  `testset_debari.jsonl`, nessun esempio statico; campi extra `split: "debari_test"`, `debari_number` (dal
  prefisso `DBNN_` dell'id), `debari_title` (campo `name` di metadata.txt). I record del corpus **non** hanno
  campi nuovi (byte-identità).
- **Invarianti hard-fail** (`check_split_separation`, `check_apollon_dir_separation`): un id in entrambi gli split
  (cartelle raw o jsonl), un id `DBNN_`/tag `debari_test`/`split: debari_test` nel corpus, un record De Bari senza
  split o con id fuori formato, un JSON Apollon nella cartella dell'altro split. `known_issues.yaml` si valida
  sull'unione degli id dei due split.
- `corpus/generate_relations_table.py --english`: per esercizi già in inglese legge `plantuml.txt`, nessun
  glossario, colonne IT omesse (`build_table` estratta da `main`).
- `.gitignore`: eccezioni `!corpus/raw/debari_test/`, `!corpus/processed/testset_debari.jsonl`,
  `!corpus/processed/apollon_debari/` (verificato con `git check-ignore`).
- Test: `check_split_separation`, `check_debari_record_fields`, `check_relations_table_english`,
  `check_convert_split_paths`.
- **Verifica byte-identità**: sha256 salvati prima del refactoring (corpus.jsonl, 59 JSON in
  `processed/apollon/`, `example_2_airtravel_v4.json`), ricontrollati dopo la pipeline completa: identici. Le 15
  `relations_table.md` tradotte rigenerate: identiche. Pipeline corpus: 59/60, 0 errori, test OK,
  check_translated 15/15, diff_report 618.

### [2026-10-02] Test set De Bari — FASE 2: estrazione (STOP A, in attesa di approvazione)
- `corpus/extract_debari.py` scrive in `corpus/raw/debari_test/`: `_images/dbNN.png` (20 immagini, pypdf; le 10
  `.jp2` convertite in PNG con Pillow), e per ogni esercizio `description.md`, `metadata.txt` e
  `extraction_notes.md` (generato). Non scrive mai `plantuml.txt` (FASE 3). Lo script è idempotente.
- **Immagini verificate una per una** aprendole, non per ordine o nome file: titolo e classi coerenti con la
  traccia e con la colonna "Given Solution" del foglio "Part 2 - N" (letto per nome; i fogli 16 e 17 sono solo in
  posizione invertita, il contenuto corrisponde al nome). Le classi coincidono in tutti i 20 casi, a meno delle
  differenze elencate nel report STOP A.
- Testo: `leakage_check.load_debari` (stessa segmentazione del leakage); `Source:` e `Reference Solution:`
  esclusi. Righe del PDF ricomposte in un paragrafo per riga, con gli elementi puntati come `- `. Regola di a capo
  nella docstring dello script; i 5 casi ambigui sono stati verificati sul PDF renderizzato (`pdftoppm`): 2 sono a
  capo di impaginazione su righe giustificate (`FORCE_JOIN`, es. 15 e 19), 3 sono a capo veri. I due spazi a
  fine riga nel testo estratto segnano la fine di un paragrafo.
- **Artefatti di estrazione corretti** (`TEXT_FIXES`/`SOURCE_FIXES`, ciascuno verificato sul rendering,
  hard-fail se assente): `wor k`, `sce ne`, `Approach” .`, `physicia n`, `owner -less`, `Hi -Key-Ah`,
  `account number ;`, `a ttached`, `w hich`; nelle fonti `Changin g`, `Models ,`, `us ing`. Gli spazi doppi
  (`made  up`, `address  and`, `number  and`) sono ridotti a uno.
- **Non corretti perché presenti nel PDF**: `ordered .` (es. 5) e `rented- Each` (es. 14), confermati sul rendering,
  oltre ai refusi dell'originale (`appointement`, `ammount`, `weigth`, `followig`, `Bycicle`, `id to design`).
- Id `DBNN_<NomePascalCase>`; nessuna collisione esatta con il corpus. Solo `DB10_Restaurant` ha lo stesso
  suffisso di `Restaurant` (segnalato dallo script). Proposta: `DB14_BicycleRental` (id corretto) con
  `debari_title` originale "Bycicle Rental".
- `metadata.txt`: `name` = titolo originale; `citation` = autori e titolo del paper da CLAUDE.md (la venue non è
  nel repo, non inventata) più il numero dell'esercizio; `domain` dal vocabolario del corpus (proposta).
- Dipendenze aggiunte a `requirements.txt`: `pypdf`, `pillow` (già usati ma non elencati), `openpyxl` (installato).

### [2026-10-02] Test set De Bari — STOP A approvato; nuove regole e costrutti
- **Regola (utente): parti illeggibili o tagliate dell'immagine → si completano da Analysis.xlsx**, annotando
  in transcription_notes OGNI token completato e la fonte. Se l'xlsx non copre il punto → STOP e domanda.
  Primo caso, es. 4 (tagliato a destra): `Appointment` e `Medication` dall'xlsx. `Perscripti…` → `Perscription`
  (decisione utente: si completa il prefisso visibile con il suo refuso; rename → Prescription proposto
  commentato). `NumberRe…` → `NumberRe` come visibile (decisione utente: l'xlsx `Number` non copre il prefisso).
  Il taglio non tocca molteplicità né ruoli (le linee arrivano sul lato sinistro, visibile).
- **Convenzione (utente): nomi con spazi / '-' / '/' → PascalCase** (classi, attributi, metodi): si tolgono i
  separatori, maiuscola sulla prima lettera di ogni parola successiva, il resto resta come scritto
  ("Work Product" → `WorkProduct`, "data prestito" → `dataPrestito`, "Part/Acc" → `PartAcc`). Underscore e
  MAIUSCOLO invariati, "Pilot1" invariato. Precedente: `ControlloreAscensore` nei tradotti. Ogni
  ricomposizione è annotata. Motivo tecnico: `parse_attribute` legge "Percent Complete" come attributo
  `Complete` di tipo `Percent`.
- `DB14_BicycleRental` approvato (`debari_title` "Bycicle Rental" invariato). Domini approvati come
  **PROVVISORI**, assegnati dal trascrittore e non dalla fonte: riga `domain_note` in ogni metadata.txt.
- Es. 16: il testo del libro nell'immagine è escluso come nota. L'auto-associazione di OrganizationalUnit
  **non ha rombo** (verificato con ingrandimento 3x): associazione con ruolo "subdivision" (`*`) e `0..1`. La
  voce xlsx "Composition (OrganizationalUnit - Subdivision)" va classificata da check_debari come imprecisione
  dell'xlsx (conteggi dell'es. 16 non più allineati al ground truth).
- **`<<interface>>` (decisione utente: implementato subito)**: prima `interface X {` non era riconosciuto e
  il blocco veniva scartato con un semplice warning. Ora `CLASS_HEADER_RE` accetta `interface X` e
  `class X <<interface>>` → kind `interface` → `stereotype: "interface"` nel JSON Apollon (valore ammesso
  da ClassStereotype.ts); `..|>` resta ClassRealization. Uno stereotipo diverso da interface/enum dà un
  warning. **Ogni riga PlantUML non riconosciuta è ora un errore** in `convert_split` (prima era un
  warning; nel corpus erano 0). Test `check_interface_stereotype`. Corpus byte-identico.

### [2026-10-02] Test set De Bari — FASE 4: corpus/check_debari.py
- Confronto indipendente del ground truth (plantuml.txt + correzioni attive, riparsato) con Analysis.xlsx:
  "Given Solution" di "Part 2 - N" (letto per nome) per classi / membri / relazioni (nomi normalizzati:
  minuscole, solo alfanumerici), e "Estimated Difficulty" per Classes / Attributes+Operations / Associations
  (valori in cache) e per AVG ED.
- Le discrepanze non si correggono: ognuna va classificata in `corpus/check_debari_justifications.yaml`
  (errore_trascrizione | imprecisione_xlsx | convenzione | refuso_immagine). Lo script fallisce se resta una
  discrepanza non giustificata o una giustificazione orfana. Report generato in `corpus/check_debari_report.md`.
- Nel record De Bari (build_manifest) entrano `debari_xlsx_counts`, `debari_ed` (ED 1-3) e `debari_ed_avg`,
  presi dall'xlsx senza ricalcolarli.
- Test `check_debari_xlsx_comparison`; `check_debari_record_fields` esteso.

### [2026-10-02] Test set De Bari — Gruppo DB-A (es. 1-5): trascrizione, in attesa di revisione (STOP)
- 5 `plantuml.txt` + `transcription_notes.md` + `relations_table.md` (generata con `--english`). Etichette
  proposte in `corpus/label_proposals_debari_DB-A.md` (17: 15 associazioni + 2 vincoli), NON in
  CLASSIFICATION.
- Correzioni: `DB05_MovieShop.yaml` ATTIVE (3 enum inline → MovieType / MovieRentStato / MovieBuyStato,
  convenzione già approvata). `DB04` (Perscription, Temeperature, `0..!`) e `DB02` (`1...*` / `0...*`)
  proposte COMMENTATE.
- Proposte di costrutti nuovi: operazioni senza parentesi nel terzo comparto → `Nome()` (es. 1, applicato
  in via provvisoria); tipi `Real` → double e `Text` → string (es. 2, NON applicato: lo style check ufficiale
  fallisce senza questa mappatura).
- Dubbi aperti: `*` isolato nell'es. 3; `*` in grassetto nell'es. 5 (attribuzione provvisoria all'estremo
  Subscriber di "hire"); attributi in italiano nell'es. 5 (xlsx tradotto).
- **Run provvisoria** (in memoria, etichette proposte + Real/Text iniettate, output solo nello scratchpad):
  5/5 convertiti, 0 errori di schema / integrità / round-trip / stile / etichette, 67 warning (65 "senza
  tipo", 2 vincoli). Senza la mappatura Real/Text: 4 errori di stile sull'es. 2.
- check_debari: 5 esercizi, tutte le discrepanze giustificate. DB01 senza discrepanze. Righe 2 e 3 di
  "Attributes + Operations" scambiate nell'xlsx (35 = 12 + 23 è l'es. 3). L'xlsx omette 19 operazioni
  dell'es. 3. Refusi dell'xlsx "Extenal" / "Externals".
- Corpus byte-identico dopo ogni passo.

### [2026-10-03] Test set De Bari — Gruppo DB-A chiuso: decisioni utente e pipeline ufficiale
- **Etichette DB-A approvate** e portate in `CLASSIFICATION` (15 associazioni + 2 vincoli);
  `_generate_label_classification.py` legge ora anche `testset_debari.jsonl` (stesso json, id DBNN_ non
  collidono). Es. 1: Input/Output/Manage/Execute sono nomi di ASSOCIAZIONE perché hanno il triangolo pieno
  del verso di lettura, che i ruoli non hanno (motivazione registrata nella classificazione).
  `label_classification.json`: 173 voci. `label_proposals_debari_DB-A.md` rimosso.
- **Regola generale: `Real` → `double`, `Text` → `string`** in `TYPE_NORMALIZATION`, accanto a Number → int.
  Solo le grafie maiuscole: `text` è un nome di attributo nel corpus (InsuranceCompany `text : string`) e
  `apply_glossary.normalize_types` sostituisce per parola intera. Verificato che rigenerare i 15
  `plantuml.txt` tradotti dà testo identico. Test esteso.
- **Regola generale: molteplicità con tre punti** (`1...*`) → `1..*` in `normalize_multiplicity`, con warning
  nel record (in `build_apollon_json`). Nessuna correzione per esercizio: `corrections/DB02_*.yaml`
  rimosso. Test esteso.
- **Operazioni senza parentesi** nel comparto operazioni → `Nome()` (stessa lettura dell'xlsx).
- **Nomi composti di attributi e metodi**: confermata la regola già applicata, uguale per tutti gli
  esercizi: separatori tolti, prima parola come scritta, maiuscola sulle successive (`PercentComplete`,
  `InitiateProject()`, ma `dataPrestito`). Precedente: nel corpus convertito i nomi composti sono 180
  PascalCase e 177 camelCase, e ognuno segue la propria fonte.
- **Es. 4**: le 3 correzioni sono attive (Perscription → Prescription, Temeperature → Temperature,
  `0..!` → `0..1`). **Revisione della decisione dello STOP A**: `NumberRe…` → `Number` dall'xlsx (vale la
  regola del completamento); la lettura probabile `NumberRefills` è annotata. check_debari: 0 discrepanze.
- **Es. 3**: il `*` isolato non è trascritto. Tutti e 4 i rami dell'aggregazione di Page hanno già la
  propria molteplicità: è un residuo senza estremo.
- **Es. 5**: il `*` in grassetto resta sull'estremo Subscriber di "hire" (regola dell'estremo più vicino).
  **Nuovo campo `ambiguities`** nei record del test set (da `corpus/ambiguities.yaml`, validato: {elemento,
  letture_alternative, scelta, motivazione}), con questo caso e l'indizio contrario.
- **Es. 5 tradotto** con il meccanismo di translated_it: `plantuml_it.txt` (immagine) + `glossary.json`
  (dalle letture dell'xlsx; traduzione fedele dove l'xlsx semplifica: loanDate, sellingPrice; valori enum
  present / to order) → `plantuml.txt` (`apply_glossary.py`). Enum della convenzione: MovieType,
  MovieRentStatus, MovieBuyStatus. Nuovo `check_translated.py --debari` (JSON in `apollon_debari/`): OK.
- **Conteggi per l'analisi**: `apollon_convert.apollon_counts` calcola dal JSON Apollon trascritto il campo
  `gt_counts` (classi, classi astratte, interfacce, enum, attributi, operazioni, valori enum, relazioni per
  tipo); solo record del test set. I conteggi dell'xlsx (`debari_xlsx_counts`) restano solo per
  tracciabilità.
- **ED 1-3**: nel file non c'è una seconda copia indipendente ("Part 1" e "Part 2 - Tot" contengono
  punteggi), quindi lo scambio non si può verificare direttamente. Indizi contrari allo scambio: nelle
  righe 2-3 Classes e Associations corrispondono al ground truth (è scambiata solo la cella "Attributes +
  Operations"); le formule AVG puntano alla propria riga; le ED seguono la complessità (es. 2 = 2/1/1 con
  12 attributi e 0 operazioni, es. 3 = 5/5/4 con 35 membri e composizioni).
- `build_manifest --split debari_test` salta, segnalandoli, gli esercizi senza `plantuml.txt` (trascrizione
  a gruppi).
- **Pipeline ufficiale DB-A**: 5/5 convertiti, 0 errori di schema / integrità / round-trip / stile, 0
  etichette non classificate, 70 warning; check_translated --debari 1/1; check_debari OK; test OK; corpus
  byte-identico.

### [2026-10-03] Test set De Bari — Gruppo DB-B (es. 6-10): trascrizione, in attesa di revisione (STOP)
- 5 `plantuml.txt` + `transcription_notes.md` + `relations_table.md` (`--english`). Etichette proposte in
  `corpus/label_proposals_debari_DB-B.md` (7 associazioni, 3 ruoli proposti, 6 vincoli), NON in
  CLASSIFICATION: la pipeline ufficiale del test set resta quella di DB-A (5 record) finché non arriva
  l'approvazione.
- Es. 9 (scritto a mano): separatori incerti e lettere illeggibili completati da Analysis.xlsx (CAR_KM,
  ADM_DATE da "AOM - DATE", FINISH_DATE, CURRENT_PRICE), ogni token annotato. `1...*` normalizzato
  automaticamente.
- Es. 10: due classi associative senza nome → `INGREDIENTDISH`, `DISHMeal` (convenzione di concatenazione).
- Punti aperti: "Navigator of" / "Copilot of" / "Captain of" (es. 6), ruolo o associazione; regola
  "MAIUSCOLO invariato" applicata ai nomi scritti a mano o in maiuscolo (CARMODEL, PARTACC, DISHMeal).
- **Run provvisoria** (etichette proposte in memoria, output solo nello scratchpad): 10/10 convertiti, 0
  errori di schema / integrità / round-trip / stile / etichette.
- check_debari: 10 esercizi, tutte le discrepanze giustificate. Es. 8 e 9 senza discrepanze. Imprecisioni
  dell'xlsx: es. 6 Associations 12 contro le 13 relazioni della sua stessa Given Solution; es. 7 conteggi
  5 / 7 contro 7 / 5; es. 10 Given Solution senza le 2 classi associative né i loro attributi.
- Corpus byte-identico.

### [2026-10-03] Test set De Bari — Gruppo DB-B chiuso; eccezione "maiuscolo tipografico"
- **Etichette DB-B approvate** e portate in `CLASSIFICATION` (189 voci). Es. 6: "Navigator of" / "Copilot of"
  / "Captain of" sono RUOLI `Navigator` / `Copilot` / `Captain` sull'estremo Pilot / Pilot3 ("X of" =
  sostantivo + preposizione, senza triangolo; precedente Louvre hasCoach → coach; maiuscola come scritta).
  Verificato che le due associazioni AircraftType–Pilot restano due edge distinti nel JSON.
- Es. 6, "owns" `*`–`*`: confermato come disegnato. Il testo vincola solo il lato Aircraft, quindi non c'è
  contraddizione.
- **Eccezione alla regola "MAIUSCOLO invariato" (utente)**: se un diagramma, o una categoria di elementi al
  suo interno (es. le intestazioni di classe), è interamente in maiuscolo, il maiuscolo è TIPOGRAFICO:
  classi → PascalCase (confini di parola dall'xlsx), attributi → minuscolo con i separatori come scritti.
  Resta invariato quando è informativo: acronimi e diagrammi a grafia mista in cui solo alcuni nomi sono
  maiuscoli. `plantuml.txt` resta fedele all'immagine; la normalizzazione passa da
  `corrections/<id>.yaml` (rename_token, categoria chiarimento_modellazione, motivo "maiuscolo
  tipografico"), tracciata in `corrections_applied`.
  - **Acronimi riconosciuti** (approvati): ID, SSN, VAT, NIN, TIN, SMS, DVD, VHS, ASCII. NON acronimi (→
    minuscolo): KM, NO, FAX, TAX. Nei composti l'acronimo resta maiuscolo (TAX_ID → tax_ID; SERIAL_NO →
    serial_no; CAR_KM → car_km).
  - Es. 9 (interamente maiuscolo): 9 classi → Person, Employee, Owner, Service, Car, PartAcc, CarModel, Make,
    PartType; 11 attributi → minuscolo; ID invariato (20 correzioni).
  - Es. 10 (grafia mista, decisione utente "solo classi"): INGREDIENT / DISH / TABLE → Ingredient / Dish /
    Table, classi associative IngredientDish / DishMeal; attributi invariati (5 correzioni).
  - Es. 11 e 13: NON applicata in automatico; proposta caso per caso allo STOP DB-C.
- **Pipeline ufficiale DB-A + DB-B**: 10/10 convertiti, 0 errori di schema / integrità / round-trip / stile,
  0 etichette non classificate, 130 warning; check_translated --debari 1/1; check_debari OK (10 esercizi).

### [2026-10-03] Test set De Bari — Gruppo DB-C (es. 11-15): trascrizione, in attesa di revisione (STOP)
- 5 `plantuml.txt` + `transcription_notes.md` + `relations_table.md`. Etichette proposte in
  `corpus/label_proposals_debari_DB-C.md` (4 vincoli, 6 ruoli: Sender, Recipient, Dropoff point, Issuer,
  Actual Rented bike, Desired Model), NON in CLASSIFICATION: la pipeline ufficiale resta a 10 record.
- Classi associative senza nome per concatenazione: PackageDeliveryCenter (11), PieceComponent e PieceOrder
  (12), PRODUCTPURCHASEORDER (13).
- `check_debari.py`: il parser dell'xlsx accetta "Association (A - B) 1" (numero dopo la parentesi, es. 11) e
  "Client. Name" (punto attaccato alla classe, es. 14); DB-A/B invariati.
- Differenza sul conteggio delle relazioni dovuta al collegamento della classe associativa (il ground truth
  lo conta, l'xlsx no): classificata come **convenzione** (ancora condivisa `count_assoc_class`), anche per gli
  es. 10, 12, 13, che prima erano "imprecisione_xlsx".
- Punti aperti: maiuscolo degli es. 11 e 13 (proposta caso per caso); nomi tutti in minuscolo nell'es. 15
  (carPark …); vincoli testuali dell'es. 14 non trascritti (costrutto nuovo).
- **Run provvisoria** (etichette proposte in memoria): 15/15 convertiti, 0 errori. check_debari: 15 esercizi,
  tutte le discrepanze giustificate (es. 15 senza discrepanze; es. 14 solo il refuso "BycicleModel" dell'xlsx).
- Corpus byte-identico.

### [2026-10-03] Test set De Bari — Gruppo DB-C chiuso: decisioni utente e pipeline ufficiale
- **Etichette DB-C approvate** come ruoli, con il testo come scritto (Sender e Recipient su CUSTOMER, Dropoff
  point su DeliveryCenter, Issuer su CLIENT, Actual Rented bike su Bicycle, Desired Model su BicycleModel),
  più 4 vincoli. `label_classification.json`: 199 voci.
- **La regola del maiuscolo tipografico si applica SOLO ALLA LETTERA** (decisione utente): serve una
  categoria INTERAMENTE in maiuscolo. Es. 11 (2 intestazioni maiuscole su 5) ed es. 13 (tutte tranne Person;
  attributi tutti tranne Quantity) non la soddisfano: TUTTO INVARIATO, nessuna estensione caso per caso.
- **Regola simmetrica "minuscolo tipografico"** (decisione utente): una categoria interamente in minuscolo
  → classi in PascalCase, via corrections con motivazione, `plantuml.txt` fedele, operazioni invariate. Es. 15:
  Barrier, Signal, Card, Access (4 correzioni). **Correzione dell'applicazione precedente**: "car park" &
  co. sono nomi di classe con spazi, e per le classi la convenzione è PascalCase anche sulla prima parola
  (CarPark, CardReader, GuestCard, StaffCard, direttamente in `plantuml.txt`); la regola "prima parola come
  scritta" vale per attributi e metodi. Verifica sul corpus: 0 diagrammi con classi tutte minuscole, 0
  con classi tutte maiuscole, 0 con attributi tutti maiuscoli.
- **Es. 14, vincoli testuali ESCLUSI**, come i `{XOR}` di FilmSet e TransportCompany: trascritti come note
  attaccate alla classe (`note "..." as N1` + `N1 .. Reservation`). `parse_plantuml` scarta ora anche una
  relazione con una nota come estremo, con un warning che riporta il testo della nota (prima `N1` sarebbe
  diventata una classe implicita). Nel corpus non esiste questa forma: byte-identico. Test
  `check_note_on_single_class`. Niente enum, niente campo nuovo.
- **Pipeline ufficiale DB-A..C**: 15/15 convertiti, 0 errori di schema / integrità / round-trip / stile, 0
  etichette non classificate, 192 warning; check_translated --debari 1/1; check_debari OK (15 esercizi);
  test OK; corpus byte-identico.
- Creata in `docs/STATUS.md` la **tabella di coerenza delle regole corpus / test set** (richiesta utente; prima
  non esisteva).

### [2026-10-03] Test set De Bari — Gruppo DB-D (es. 16-20): trascrizione, in attesa di revisione (STOP)
- 5 `plantuml.txt` + `transcription_notes.md` + `relations_table.md`. Etichette proposte in
  `corpus/label_proposals_debari_DB-D.md` (2 associazioni, 2 ruoli: personalBanker, accountHolder), NON in
  CLASSIFICATION: la pipeline ufficiale resta a 15 record. I ruoli vicino agli estremi (subdivision, manager,
  line_item) sono scritti direttamente con la sintassi `"molt ruolo"`.
- Es. 16: auto-associazione senza rombo con ruolo `subdivision`; testo del libro escluso come nota.
- Es. 17: frecce piene identiche → ambiguità generalizzazione / associazione registrata in
  `corpus/ambiguities.yaml`, con lettura provvisoria come l'xlsx; Contract in corsivo → `abstract class`; Phone e
  DoubleTransfer non collegati (trascritti isolati).
- Es. 18: `interface User`; `List<X>` → `X[]` con correzioni attive (convenzione multi-valore già approvata).
- Costrutti nuovi proposti: tipi non primitivi non dichiarati (`Guid` es. 19; `Address`, `Phone`, `Price`,
  `Supplier` es. 20); `{ordered, unique}` sugli estremi (es. 20), che oggi il parser leggerebbe come nome di
  ruolo.
- **Run provvisoria** (etichette, tipi e `{ordered, unique}` tolto dal ruolo, tutto in memoria): 20/20
  convertiti, 0 errori. check_debari: 20 esercizi, tutte le discrepanze giustificate (es. 20 senza discrepanze).
- Corpus byte-identico.

### [2026-10-03] Test set De Bari — Gruppo DB-D chiuso; trascrizione dei 20 esercizi completata
- **Etichette DB-D approvate**: worksFor e borrow sono associazioni; personalBanker (estremo Employee) e
  accountHolder (estremo Customer) sono ruoli. `label_classification.json`: 203 voci.
- **Regola generale, tipi di dominio**: `Guid`, `Address`, `Phone`, `Supplier` → string; `Price` → double. Mappature
  globali come Number / Calendar / currency, applicate SOLO in posizione di tipo e SOLO con queste maiuscole. Sono
  in una tabella separata, `DOMAIN_TYPE_MAPPING`: `apply_glossary.normalize_types` sostituisce per parola intera e
  non deve toccarle (address / phone / price sono nomi di attributo in 22 esercizi). Non si applicano se il
  diagramma dichiara una classe con quel nome: SmartHomeAutomationSystem dichiara `Address`, ma non lo usa come
  tipo. Verifiche: corpus byte-identico; i 15 tradotti + DB05 rigenerati sono identici; test
  `check_domain_types_and_end_constraints`. Niente "tipo esterno". Es. 20: `Supplier` è probabilmente
  un'entità non disegnata, e non si crea una classe (si inventerebbe una relazione).
- **Regola generale, vincoli di estremo** `{ordered, unique}`: `split_mult_role` li toglie dal testo
  dell'estremo (non sono né molteplicità né ruolo) e `parse_plantuml` li registra come warning ("scartato
  vincolo di estremo"), come i {XOR}. Casi nel corpus: 0 (le uniche `{` tra virgolette sono le note {XOR}).
- **Es. 17 confermato**: Data/SMS → Option sono generalizzazioni; Client/Option → Contract sono associazioni
  navigabili (voce in ambiguities.yaml). Phone e Double Transfer restano isolati: le generalizzazioni dell'xlsx
  sono imprecisione dell'xlsx. Contract è `abstract class`. Le due linee tratteggiate BasicContract/Option →
  Contract sono `..|>` → ClassRealization, come le realizzazioni tratteggiate dell'es. 18 (verificato nel JSON).
- **Pipeline ufficiale, 20/20**: 0 errori di schema / integrità / round-trip / stile, 0 etichette non
  classificate, 215 warning, 12 vincoli di generalizzazione; check_translated --debari 1/1; check_debari OK (20
  esercizi, tutte le discrepanze giustificate); test OK; corpus byte-identico.

### [2026-10-03] Test set De Bari — FASE 5: leakage (STOP B, in attesa di decisione)
- `corpus/leakage_check.py` esteso (senza opzioni il comportamento è invariato: ApartmentBuilding vs House resta
  0.024). `--debari-test`: bersagli dai 20 record di `testset_debari.jsonl` (descrizioni pulite) invece che dal
  testo grezzo del PDF. `--prompt`: indicizza anche gli esempi few-shot del prompt statico
  (`prompt_template_v4.txt`: PROMPT_example_1_bank_loans, PROMPT_example_2_airtravel) come pool separato. TF-IDF
  invariato (stop words inglesi, sublinear_tf, idf comune), soglia 0.4. Test `check_leakage_prompt_examples`.
- Esito (`--debari-test --prompt --all-debari`): **un solo caso sopra soglia: es. 6 Flights vs AirTravel = 0.418**,
  sia verso il record del corpus sia verso l'esempio 2 del prompt statico (stesso testo). Tutti gli altri top-1
  sono < 0.4 (massimo successivo: es. 7 Bank System vs BankAccount 0.332).
- Coppie richieste (sempre riportate, con `--vs`): 6 vs AirTravel 0.418 (anche vs prompt 0.418); 7 vs bank loans
  0.090 (vs BankAccount 0.332); 16 vs bank loans 0.095 (vs BankAccount 0.323); 10 vs Restaurant 0.177; 18 vs
  MilanLibrary 0.144; 9 vs RepairShops 0.159; 4 vs Hospital 0.118, vs HospitalHouseMD 0.210.
- Nessuna esclusione automatica: decisione utente allo STOP B.

### [2026-10-04] Test set De Bari — STOP B: es. 6 Flights resta nel test set e nel retrieval (opzione a)
- **Decisione utente**: l'es. 6 resta nel test set; AirTravel resta candidato legittimo del retrieval per l'es. 6;
  nessuna esclusione.
- **Motivazione**: è una sovrapposizione di dominio sotto la soglia di duplicato (TF-IDF 0.418, appena sopra la
  soglia di attenzione 0.4; 4 classi condivise su 17, Jaccard dei nomi di classe 0.24). Escludere AirTravel dal
  retrieval penalizzerebbe il RAG proprio dove dovrebbe aiutare (recuperare un esempio dello stesso dominio è lo
  scopo del retrieval). Escludere l'es. 6 dal test set ridurrebbe la confrontabilità con De Bari et al. (stessi 20
  esercizi, stessi punteggi di Analysis.xlsx).
- **Tracciabilità**: `known_issues` dell'es. 6 con una voce strutturata `{tipo: domain_overlap_static_example,
  altro_esercizio: AirTravel, tfidf: 0.418, tfidf_soglia: 0.4, classi_condivise: [Airline, Airport, Flight, Pilot],
  n_classi_condivise: 4, jaccard_nomi_classe: 0.2353, nota}`. Classi condivise e Jaccard sono ricalcolati dai JSON
  Apollon (DB06_Flights.json, AirTravel.json; confronto case-insensitive: 4/17 = 0.2353, cioè 0.24 a 2 decimali,
  coincide con il valore indicato dall'utente). L'esempio 2 del prompt ha le stesse classi del record AirTravel.
  `known_issues.yaml` accetta ora anche voci strutturate (dizionario con `tipo`); le voci a stringa restano
  invariate (corpus byte-identico). Il test verifica la coerenza dei numeri con i JSON.
- **Requisito della valutazione** (in STATUS.md): ogni metrica va riportata su 20 esercizi e su 19 (senza l'es. 6),
  per tutte le condizioni, in particolare few-shot statico vs retrieval.

### [2026-10-04] Test set De Bari — FASE 6: chiusura
- `build_manifest.py --split debari_test` richiede ora tutti e 20 gli esercizi trascritti (prima, durante la
  trascrizione a gruppi, saltava quelli senza `plantuml.txt`).
- **Pipeline completa su entrambi gli split** (ordine in STATUS.md): corpus 59/60 (Cruise escluso), test set
  20/20; 0 errori di schema / integrità / round-trip / stile, 0 righe non riconosciute, 0 etichette non
  classificate (`label_classification.json`: 203 voci = 74 associazioni, 109 ruoli + 2 righe di ruolo doppio, 21
  vincoli); test OK; check_translated 15/15 (corpus) e 1/1 (--debari); diff_report 618; check_debari OK (84
  discrepanze, tutte giustificate: 76 imprecisione_xlsx, 8 convenzione); leakage: solo es. 6 sopra soglia
  (deciso, opzione a). **Corpus byte-identico** agli sha256 salvati prima della FASE 1 (corpus.jsonl, 59 JSON
  Apollon, example_2_airtravel_v4.json).
- **Test set**: 150 classi (1 astratta) + 1 interfaccia + 5 enumerazioni, 264 attributi, 47 operazioni, 167
  relazioni (93 associazioni bidirezionali, 10 unidirezionali, 37 generalizzazioni, 16 aggregazioni, 6
  composizioni, 4 realizzazioni, 1 dipendenza); 40 correzioni su 6 esercizi; 2 ambiguità (es. 5, 17); 1
  known_issue (es. 6); ED medio 2.8.
- **Domini** (provvisori per il test set): vocabolario di 13 domini, conteggi corpus / test in STATUS.md. Il test
  set non copre Insurance, Personal Activities, Research, Social Networks.

### [2026-10-04] Tag `testset-v1`: test set De Bari congelato
- Tag annotato `testset-v1` sul commit `eb4d28b` ("Test set De Bari congelato prima degli esperimenti"): i 20
  esercizi De Bari (ground truth in `corpus/raw/debari_test/`, `corpus/processed/testset_debari.jsonl`,
  `corpus/processed/apollon_debari/`) sono congelati prima degli esperimenti. Il push del tag lo fa l'utente.
- Da qui vale la regola di versionamento registrata in `docs/STATUS.md` (Regole attive, "Solo test set De Bari"):
  ogni modifica successiva al ground truth richiede un commit dedicato, una voce in questo file e un nuovo tag
  (`testset-v2`, …); ogni run sperimentale salva nel proprio config il commit e il tag del test set usato.
