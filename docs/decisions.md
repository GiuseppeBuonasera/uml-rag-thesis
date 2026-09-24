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
