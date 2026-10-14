# Decisioni di design

Registro delle scelte tecniche importanti nel tempo, con motivazione.
Aggiornare ogni volta che si prende una decisione rilevante (es. cambio di
formato diagrammi, scelta del modello di embedding, metrica di valutazione).

## Indice delle voci

Generato il 2026-10-04 dai titoli delle voci (data + titolo, in ordine cronologico). Le voci sottostanti
non sono state modificate.

1. 2026-09-22 — Formato di output dei diagrammi: Apollon JSON (non PlantUML)
2. 2026-09-22 — Riorganizzazione di docs/dati/
3. 2026-09-22 — Convertitore PlantUML -> Apollon JSON per i 45 diagrammi di riferimento
4. 2026-09-23 — Revisione del convertitore PlantUML -> Apollon: due bug corretti, round-trip aggiunto, materiale mal etichettato corretto
5. 2026-09-23 — Passaggio da Apollon v3 a v4 come formato di output
6. 2026-09-24 — Riorganizzazione docs/dati/: identificato lo studio di provenienza corretto per ciascun file
7. 2026-09-24 — Blocco 2 — docs/dati/README.md riscritto per la nuova struttura
8. 2026-09-24 — Blocco 3 — corretto il lato del rombo in aggregazione/composizione
9. 2026-09-24 — Blocco 4 — leakage: AirTravel è sia esempio statico nel prompt sia esercizio del corpus
10. 2026-09-25 — Traduzione dei 15 esercizi italiani di studio2025_it: avviata, pilota su CourseManagement
11. 2026-09-25 — Render inglese, controllo JSON compilato, normalizzazione tipo bool
12. 2026-09-25 — corpus/raw/models -> corpus/raw/models_original (rinomina osservata, non fatta da me)
13. 2026-09-25 — FASE 1 — Normalizzazioni automatiche applicate a tutto il corpus
14. 2026-09-25 — FASE 2 — Classificazione delle etichette (associazione vs ruolo): STOP 1
15. 2026-09-25 — Risposte STOP 1: vincoli, qualificatori, responsibleFor, colonna "lettura"
16. 2026-09-27 — Risoluzione dei 4 dubbi residui di label_classification.md
17. 2026-09-28 — Revisione di roles_to_review.md e applicazione della classificazione al convertitore
18. 2026-09-28 — FASE 3 STOP 2/STOP 3 — correzioni di contenuto applicate, meccanismo corpus/corrections/, FASE 4 (stile + diff report) e FASE 5 (leakage)
19. 2026-09-29 — Nuova categoria "chiarimento di modellazione" + 3 nuovi tipi di correzione (change_edge_type, remove_label, set_role) — caso Boeing
20. 2026-09-29 — 3 ulteriori chiarimenti di modellazione su AirTravel
21. 2026-09-29 — BuildingManagement — diagramma incompleto rispetto a description.md, 5 chiarimenti di modellazione + nuovo tipo `add_line` + esclusione paragrafo di consegna dal testo indicizzato
22. 2026-09-29 — Annullamento delle correzioni di BuildingManagement — fedeltà all'originale
23. 2026-09-29 — Riclassificazioni: fine della categoria "qualificatore", auto-relazione Louvre "coach", rimozione del marcatore di verso di lettura PlantUML ('>'/'<')
24. 2026-09-30 — Traduzione Gruppo A (es. 2-5): Hospital, ResearchCenter, MilanLibrary, Bookmaker
25. 2026-09-30 — Gruppo A — esito revisione parziale
26. 2026-09-30 — Gruppo A — chiusura
27. 2026-09-30 — Riconciliazione conteggi label_classification (nessuna modifica ai dati)
28. 2026-09-30 — Traduzione Gruppo B (es. 6-9): UniversityExams, Restaurant, ElevatorControl, RealEstateAgency
29. 2026-09-30 — Gruppo B — chiusura
30. 2026-10-01 — Gruppo B — correzioni dopo verifica visiva dell'autore + controllo nomi di ruolo
31. 2026-10-01 — Regola: verbi vicino agli estremi = nome di associazione, non ruoli
32. 2026-10-01 — Traduzione Gruppo C (es. 10-12): OilWells, RepairShops; es. 12 Palestra ESCLUSO
33. 2026-10-01 — Gruppo C — decisioni; regole "sostantivo = ruolo" e "classe associativa senza nome"
34. 2026-10-01 — Gruppo C chiuso (Gym approvato)
35. 2026-10-01 — Gruppo D (es. 13-15) — trascrizione, in attesa di revisione
36. 2026-10-01 — Gruppo D chiuso — decisioni utente; traduzione dei 15 esercizi italiani completata
37. 2026-10-01 — EatAtHome — due alternative: confermato "lasciamo cosi'"
38. 2026-10-01 — Note dei diagrammi negli altri 14 esercizi tradotti — solo verifica, nessuna modifica
39. 2026-10-02 — Test set De Bari — FASE 1: split corpus / debari_test (refactoring senza cambi di comportamento)
40. 2026-10-02 — Test set De Bari — FASE 2: estrazione (STOP A, in attesa di approvazione)
41. 2026-10-02 — Test set De Bari — STOP A approvato; nuove regole e costrutti
42. 2026-10-02 — Test set De Bari — FASE 4: corpus/check_debari.py
43. 2026-10-02 — Test set De Bari — Gruppo DB-A (es. 1-5): trascrizione, in attesa di revisione (STOP)
44. 2026-10-03 — Test set De Bari — Gruppo DB-A chiuso: decisioni utente e pipeline ufficiale
45. 2026-10-03 — Test set De Bari — Gruppo DB-B (es. 6-10): trascrizione, in attesa di revisione (STOP)
46. 2026-10-03 — Test set De Bari — Gruppo DB-B chiuso; eccezione "maiuscolo tipografico"
47. 2026-10-03 — Test set De Bari — Gruppo DB-C (es. 11-15): trascrizione, in attesa di revisione (STOP)
48. 2026-10-03 — Test set De Bari — Gruppo DB-C chiuso: decisioni utente e pipeline ufficiale
49. 2026-10-03 — Test set De Bari — Gruppo DB-D (es. 16-20): trascrizione, in attesa di revisione (STOP)
50. 2026-10-03 — Test set De Bari — Gruppo DB-D chiuso; trascrizione dei 20 esercizi completata
51. 2026-10-03 — Test set De Bari — FASE 5: leakage (STOP B, in attesa di decisione)
52. 2026-10-04 — Test set De Bari — STOP B: es. 6 Flights resta nel test set e nel retrieval (opzione a)
53. 2026-10-04 — Test set De Bari — FASE 6: chiusura
54. 2026-10-04 — Tag `testset-v1`: test set De Bari congelato
55. 2026-10-04 — Riordino del repository prima del Passo 2; provenienza della baseline statica
56. 2026-10-04 — Il commit c161bab non è una versione testset-v2
57. 2026-10-04 — Passo 2 — FASE 1: retriever BM25, baseline random, test
58. 2026-10-04 — Passo 2 — FASE 2: analisi leave-one-out sul corpus (STOP 1, configurazione NON ancora congelata)
59. 2026-10-04 — Passo 2 — STOP 1 approvato: configurazione BM25 congelata, fasce di score_norm, .gitignore
60. 2026-10-04 — Passo 2 — FASE 3: BM25 congelato sul test set (STOP 2)
61. 2026-10-05 — Passo 2 — hubness del retrieval (solo descrittivo)
62. 2026-10-05 — Passo 2 chiuso; Passo 3 diviso in 3a (infrastruttura) e 3b (esperimenti, bloccata)
63. 2026-10-05 — Passo 3a — FASE 1: template a blocchi e prompt builder (STOP 1, in attesa di approvazione)
64. 2026-10-05 — Passo 3a — STOP 1 approvato: differenze dal template v4, formato dei prompt
65. 2026-10-05 — Passo 3a — FASI 2 e 3: client LM Studio, post-processing L0-L4, runner (STOP 2, in attesa di approvazione)
66. 2026-10-05 — Passo 3a — STOP 2 approvato e chiusura: riscritture L4, diagnostici separati, verifica del seed, contesto e max_tokens identici per modello
67. 2026-10-06 — Vocabolario cl100k_base versionato: stima dei token senza download
68. 2026-10-06 — Censimento degli sha256 su file e regole `-text` in .gitattributes
69. 2026-10-06 — Gemma 4 12B QAT: ragionamento, parametri espliciti, metadati enable_thinking
70. 2026-10-06 — Licenza di Gemma 4 confermata: Apache 2.0
71. 2026-10-06 — Primo smoke test con Gemma 4 12B QAT: ragionamento attivo, smoke test corretto
72. 2026-10-06 — Secondo smoke test con Gemma 4 12B QAT: seed non rispettato, riproducibilità a livello di analisi
73. 2026-10-06 — smoke_lmstudio.py --save: prova versionata (.txt + .json) senza copia-incolla
74. 2026-10-06 — Output degli smoke test 1 e 2 incollati; temperature 0 deterministico nello smoke 2; metadati del template Gemma
75. 2026-10-06 — Pilota sulla temperatura (solo corpus): selezione, config e regola di decisione registrate PRIMA della run (STOP 1)
76. 2026-10-06 — Pilota: primo tentativo fallito (contesto 8192), token reali di Gemma 4, controllo del contesto caricato nel runner
77. 2026-10-06 — Pilota, FASE 3 (STOP 2): la regola della voce 75 non decide (troppi troncamenti)
78. 2026-10-07 — Secondo pilota (solo corpus): PlantUML contro JSON vincolato, Qwen2.5-Coder 14B; regola di decisione PRIMA della run (STOP 1)
79. 2026-10-07 — Secondo pilota — STOP 1 approvato: esempi PlantUML canonici, regola auto_v1, regola di decisione con classifica completa, schema di generazione
80. 2026-10-07 — Smoke test di Qwen2.5-Coder 14B: risposta attesa, nessun ragionamento, seed come Gemma
81. 2026-10-07 — Repository spostato fuori da OneDrive; remote superflui rimossi
82. 2026-10-07 — Secondo pilota: script di analisi (analyze_pilot2.py) scritto PRIMA delle run
83. 2026-10-07 — Secondo pilota: configurazione di RIFERIMENTO J0-Q (Qwen, Apollon JSON libero), registrata PRIMA della run
84. 2026-10-07 — Qwen2.5-Coder 14B scartato: non regge 32768 di contesto sulla RTX 4070 12 GB
85. 2026-10-07 — Qwen2.5-Coder 7B Instruct Q6_K come modello da coding; confronto tra modelli di taglia diversa
86. 2026-10-07 — Smoke test di Qwen2.5-Coder 7B Instruct: risposta attesa, nessun ragionamento, seed come Gemma e il 14B
87. 2026-10-08 — Gemma 4 12B QAT: impostazioni di caricamento (Flash Attention, KV cache) del primo pilota
88. 2026-10-08 — Secondo pilota, STOP 2: la regola della voce 78 sceglie P-Q (Qwen2.5-Coder 7B, PlantUML)
89. 2026-10-08 — Secondo pilota, decisioni dello STOP 2: strada PlantUML adottata, entrambi i modelli, post-processing PlantUML v2, analisi v2 descrittiva
90. 2026-10-08 — Struttura comune, espansore unico e formato JSON compatto (FASE 1, STOP 1)
91. 2026-10-08 — Strada "JSON compatto" (FASE 2): istruzioni, post-processing C0-C2, schema disattivato, runner
92. 2026-10-08 — Insieme di sviluppo e confronto dei formati PlantUML / JSON compatto (FASE 3, STOP 2): selezione, config, metriche e regola PRIMA delle run
93. 2026-10-08 — Versione di configurazione 2: max_tokens 4096, contesto 32768 (STOP 1 della leva k)
94. 2026-10-08 — Leva "numero di esempi k" sull'insieme di sviluppo (FASE 2, STOP 2): config, calibrazione, regola PROPOSTA, analisi PRIMA delle run
95. 2026-10-08 — Dopo la leva k: solo Gemma 4 12B QAT, k di lavoro = 3, configurazione di lavoro (supera la voce 89 sui modelli)
96. 2026-10-09 — Leva "istruzioni mirate", FASE 1 (STOP 1): analisi degli errori di Gemma a k = 3 (solo descrittiva)
97. 2026-10-09 — Leva "istruzioni mirate", FASE 2 (STOP 2): blocco di regole di modellazione aggiuntive (PROPOSTA)
98. 2026-10-09 — Istruzioni mirate: blocco DEFINITIVO congelato, metrica M e regola di adozione (PRIMA della run)
99. 2026-10-09 — Correzione del GT di eHome2020: lato del rombo della composizione Apartment / Room
100. 2026-10-09 — Report grafico di revisione delle generazioni (experiments/review_report.py)
101. 2026-10-09 — Istruzioni mirate, STOP 3: la regola della voce 98 NON le adotta in nessuno dei due formati
102. 2026-10-09 — Runbook in notebook, registro automatico delle esecuzioni e storico ricostruito
103. 2026-10-09 — Istruzioni mirate chiuse: blocco fuori dalla pipeline, configurazione di lavoro invariata, nessuna iterazione
104. 2026-10-09 — Test e controlli di sanità: lettura dei GT del test set solo per verificare il codice
105. 2026-10-09 — Rigenerazione dei 5 report versionati con il GT corretto di eHome2020: nessun esito cambia
106. 2026-10-09 — Riga di provenienza automatica nei report: commit e impronta del GT
107. 2026-10-09 — Retriever denso e ibrido: APPROVATA (FASE 1, STOP 1), solo retrieval sul corpus, test set escluso
108. 2026-10-09 — Retriever denso e ibrido: implementazione, analisi LOO sul corpus ed esito della regola (FASE 2-3, STOP 2)
109. 2026-10-09 — Retriever come fattore sperimentale: controllo di funzionamento sul dev set e run oracolo — APPROVATA (STOP A)
110. 2026-10-09 — Controllo di funzionamento dei retriever e run oracolo: esecuzione ed esito (STOP B)
111. 2026-10-10 — Istruzioni v5 riscritte da zero, metriche corrette e regola di adozione — STOP A (prima della run)
112. 2026-10-10 — Test set De Bari in leave-one-out: ogni esercizio usa gli altri 19 come candidati — DECISIONE e implementazione
113. 2026-10-10 — Insieme unico dei 79 esercizi: leave-one-out su tutti, valutazione principale sui 53 mai usati per decidere — DECISIONE, piano PROPOSTO
114. 2026-10-10 — Cruise recuperato: associazione ternaria riscritta con tre associazioni binarie (opzione b)
115. 2026-10-10 — Pool unico: per ogni query (sviluppo e valutazione) tutti gli altri 79 esercizi
116. 2026-10-10 — Pulizia del codice del corpus: percorsi condivisi e classificazione delle etichette come dati
117. 2026-10-10 — Insieme di valutazione congelato (ruoli) e dichiarazione delle contaminazioni, prima della run v5
118. 2026-10-10 — Leva v5: esecuzione ed esito (STOP B)
119. 2026-10-10 — Leva "validità del JSON compatto": esempi indentati e generazione vincolata
120. 2026-10-10 — Varianti del retriever che usano il diagramma dei candidati: piano e parametri fissati prima
121. 2026-10-10 — Compatto con esempi indentati e passo 4 delle varianti del retriever (regola prima della run)
122. 2026-10-10 — Varianti del retriever, passo 4: esito (nessuna entra nel 3b)
123. 2026-10-11 — Verifiche prima del 3b: compatto v5 + indent e pool dei soli 60 (regole prima delle run)
124. 2026-10-11 — Verifiche prima del 3b: esito (v5 adottata per il compatto, resta il pool unico)
125. 2026-10-11 — Leva "thinking" di Gemma sul dev set: chiusa (cicli di autoverifica allo smoke test)
126. 2026-10-11 — Leva "piano breve" (istruzioni v5plan) sul dev set: regola e config registrate prima della run
127. 2026-10-11 — Riproducibilità prima del 3b: clone pulito, ambiente dedicato, metriche congelate in evaluation/metrics.py
128. 2026-10-11 — Qualità del ground truth per sorgente (solo descrittivo, limiti da citare in tesi)
129. 2026-10-11 — Retrieval pronto per il 3b: pool unico negli script, esempi congelati, analisi descrittiva sui 26 di sviluppo, domanda 4
130. 2026-10-11 — Seme della condizione random per esercizio e ripetizione; proposta sulla domanda 4; analisi pertinenza-qualità entro esercizio nel piano del 3b
131. 2026-10-12 — Gemma 4 26B A4B QAT come modello del 3b: prova di fattibilità (STOP)
132. 2026-10-12 — Controllo del 26B sul dev set (regola registrata prima della run), config del 3b e notebook di esecuzione
133. 2026-10-12 — Controllo del 26B: esito (Gemma 4 26B A4B QAT adottato come modello del 3b)
134. 2026-10-12 — Confronto visivo nel notebook: ground truth, PlantUML e JSON compatto affiancati
135. 2026-10-12 — Leva "attributi del compatto" (istruzioni v5b): testi, metrica e regola registrati prima della run
136. 2026-10-12 — Metriche standard P / R / F1 per tipo di elemento (esatto e rilassato): ricalcolo sul dev set e proposta per il 3b
137. 2026-10-12 — Qualità degli esempi che il 3b mostrerà (solo descrittivo)
138. 2026-10-12 — Leva "esempi senza istruzioni per lo studente" (vista clean_v1): testi e regola registrati prima della run
139. 2026-10-12 — Leva "esempi senza istruzioni per lo studente": esito (clean_v1 adottata per il 3b)
140. 2026-10-12 — Passo 2 rifatto con il retriever hybrid (26B, configurazione attuale): regola registrata prima della run
141. 2026-10-12 — Passo 2 con hybrid: esito (hybrid resta nel 3b)
142. 2026-10-12 — Passo 2 rifatto con il retriever dense (26B, configurazione attuale): regola registrata prima della run
143. 2026-10-12 — Passo 2 con dense: esito (inferiore a bm25 nel compatto, di poco: decide l'utente)
144. 2026-10-12 — Decisione dell'utente: il retriever dense esce dal Passo 3b
145. 2026-10-12 — Strumento di confronto visivo bm25 / hybrid / ground truth (solo lettura)
146. 2026-10-13 — Leva v5b (attributi del compatto): riallineata alla configurazione attuale e alle metriche nuove, regola prima della run
147. 2026-10-13 — Leva "piano breve" (v5plan): chiusa senza adozione
148. 2026-10-13 — Leva v5b: esito (NON adottata); risposte senza attributi del compatto lasciate come limite
149. 2026-10-13 — Avvio del 3b prima delle risposte dei relatori (rischio di rifacimento accettato, nessuna lettura dei risultati prima dello script di analisi)
150. 2026-10-14 — Leva v5c ("attributes" sempre presente nel compatto): regola e config registrate PRIMA della run

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

### [2026-10-04] Riordino del repository prima del Passo 2; provenienza della baseline statica
- **Mappa vecchio percorso → nuovo percorso** (spostamenti con `git mv`, la storia è conservata; le citazioni nelle
  voci precedenti di questo file restano quelle storiche):
  - `corpus/_generate_label_classification.py` → `corpus/generate_label_classification.py` (passo permanente della
    pipeline: il prefisso `_` lo faceva sembrare uno script una tantum)
  - `corpus/_generate_roles_to_review.py` → `docs/archivio/_generate_roles_to_review.py` (non più eseguibile da lì)
  - `corpus/roles_to_review.md` → `docs/archivio/roles_to_review.md`
  - `docs/dati/apollon_format_reference/legacy_v3/prompt.docx` → `docs/dati/studio2025_it/prompt_v3_originale.docx`
  - `docs/dati/apollon_format_reference/legacy_v3/diagram_example_1.json` →
    `docs/dati/studio2025_it/prompt_v3_esempio1_bank_loans.json`
  - `docs/dati/apollon_format_reference/legacy_v3/diagram_example_2.json` →
    `docs/dati/studio2025_it/prompt_v3_esempio2_orologio.json`
  - `data/results/Exercises.pdf` (ignorato) → `docs/dati/debari/Exercises_solo_testo.pdf` (tracciato)
- **Eliminati**: `_debari_descs_cache.json` (tracciato, 0 byte, nessun uso); `data/results/Analysis.xlsx` (ignorato,
  copia identica, stesso sha256, di `docs/dati/debari/Analysis.xlsx`).
- **Nessuno spostamento dentro `corpus/`** (decisione utente): 19 note di trascrizione in `corpus/raw/` (congelate; il
  test set in `testset-v1`) citano i percorsi attuali di `corrections/`, `description_exclusions/`, `ambiguities.yaml`,
  `check_debari_report.md`, `apollon_limitations.md` e `diff_report.md`. Al posto della riorganizzazione:
  `corpus/README.md` con la tabella file → ruolo e l'ordine dei comandi. I test restano accanto al modulo; quelli del
  Passo 2 andranno in `retrieval/test_retrieval.py`.
- **Correzione importante**: la baseline few-shot statica (`prompt_template_v4.txt`) deriva dal **prompt v3 dello
  studio 2025** (Garaccione et al., item figshare 10.6084/m9.figshare.29492624; autore nei metadati del .docx:
  Giacomo Garaccione), adattato ad Apollon v4 con l'esempio dell'orologio (diagramma a stati) sostituito da
  AirTravel. **Non deriva da De Bari et al.**, che generavano PlantUML con un prompt diverso. Nei documenti
  correnti l'unica frase che la attribuiva a De Bari era la domanda 9 per i relatori in STATUS.md, ora
  riformulata; le voci storiche di questo file non sono state riscritte.
- **`Exercises_solo_testo.pdf`**: confrontato con le 20 `description.md` del test set senza modificarle: nessuna
  differenza testuale (a meno di spazi, a capo e marcatori di elenco; le differenze di sola spaziatura non sono
  rilevabili, perché il PDF perde gli spazi a fine riga). Quindi non serve `testset-v2`. Provenienza aggiunta alle
  domande per i relatori.
- **Verifica**: pipeline completa su entrambi gli split; gli 81 output (`corpus.jsonl`, `testset_debari.jsonl`, 59 +
  20 JSON Apollon) sono byte-identici agli sha256 salvati prima del riordino. Test, check_translated, check_debari e
  leakage invariati. Report rigenerati identici, tranne la riga di `label_classification.md` che cita il nome del
  generatore.

### [2026-10-04] Il commit c161bab non è una versione testset-v2
- Il commit `c161bab` ("testset-v2 in formato .json") contiene solo documentazione e NON costituisce una versione
  `testset-v2` del ground truth: il test set resta `testset-v1` (tag su `eb4d28b`, pubblicato).

### [2026-10-04] Passo 2 — FASE 1: retriever BM25, baseline random, test
- Nuovi moduli in `retrieval/` (gli stub `dense_retriever.py` e `hybrid_retriever.py` restano invariati):
  `base.py` (interfaccia `Retriever.fit / retrieve(query_text, k, exclude_ids)` → `RetrievalResult(id, rank, score,
  score_norm)`, ordinamento per punteggio decrescente con tie-break per id), `corpus_loader.py` (SOLA LETTURA: candidati =
  i 59 record convertiti di corpus.jsonl, query = i 20 del test set; hard-fail se un record del test set è tra i
  candidati; Jaccard dei nomi di classe normalizzati per l'analisi), `text_preprocessing.py` (minuscole, token
  `[^\W_]+`, stopword da lista FISSA `retrieval/stopwords_en.txt` = le 318 di scikit-learn 1.8.0 copiate nel repo,
  stemming Snowball inglese), `keyword_retriever.py` (riscritto: BM25Okapi di rank_bm25, k1 / b configurabili),
  `random_retriever.py` (seed + sha256 della query, riproducibile), `test_retrieval.py` (script, accanto al modulo).
- **score_norm** = score / punteggio BM25 della query contro sé stessa trattata come documento, con la stessa formula e
  le statistiche del corpus (IDF, avgdl), quindi definito anche per query fuori indice; non limitato a 1; 0 se la
  query non ha termini noti. Verificato a mano su un esempio (0.775).
- **Indicizzato solo `description`**; il diagramma non entra mai nel ranking (solo in analisi).
- Dipendenze fissate: `rank-bm25==0.2.2`, `snowballstemmer==3.1.1` (Python puro, nessun download; NLTK scartato perché
  scarica risorse a runtime).
- Test (tutti verdi): loader e hard-fail di disgiunzione, tokenizzazione, determinismo (anche invertendo l'ordine dei
  record), exclude_ids, tie-break, ognuno dei 59 candidati recupera sé stesso al rank 1, nessun id del test set mai
  restituito (BM25 e random, k = tutti), random riproducibile, score_norm a mano, nessuna scrittura in `corpus/` (sha256
  di 715 file prima e dopo).

### [2026-10-04] Passo 2 — FASE 2: analisi leave-one-out sul corpus (STOP 1, configurazione NON ancora congelata)
- `retrieval/analyze_retrieval.py` → `data/results/retrieval/<run_id>/` (config.json con commit, stato del working tree,
  tag del test set e verifica che il test set sia invariato dal tag; summary.md; sensitivity.csv; variants.csv;
  near_duplicates.csv; loo_top3.csv). Run `loo_2026-10-04_stop1` (commit c161bab, working tree modificato).
- **Metodo LOO**: per ogni candidato l'indice è rifittato sugli altri 58 (la query non entra in IDF / avgdl, come le query
  del test set); `exclude_ids` serve solo alle varianti. Pertinenza proxy: Jaccard dei nomi dei nodi Apollon
  normalizzati, solo in analisi. Il test set non viene letto (solo controllo di disgiunzione).
- **Risultati** (default: stopword sì, stemming sì, k1 = 1.5, b = 0.75): J@1 0.096 e J@3 0.067 contro random 0.013 ± 0.004
  e 0.013 ± 0.002 (20 seed) e oracolo 0.132 e 0.099; Spearman tra score_norm e Jaccard del top-1 ρ = 0.43 (p = 0.001).
  I Jaccard assoluti sono bassi perché il corpus è eterogeneo: il massimo Jaccard tra due candidati qualsiasi è 0.25.
- **Sensibilità** (48 configurazioni, differenze appaiate con il default, criterio ±2 errori standard): nessuna
  configurazione è significativamente migliore del default (al massimo Δ J@1 +0.002); togliere le stopword e/o lo
  stemming peggiora in modo significativo in 29 configurazioni su 36. Proposta: congelare il default.
- **Quasi-duplicati** (solo elenco, la politica è la domanda 10): GasStation_KUL/TUW (stesso caso per nome; Jaccard
  0.09, TF-IDF 0.23) più le coppie in cima alle due distribuzioni (Jaccard ≥ 0.25: HospitalHouseMD/TreatmentPlans,
  TransportCompany/RepairShops, ClothingCompany/SellingGoods; TF-IDF ≥ 0.25: ProjectManagement/ResearchCenter,
  TransportCompany/TruckLogistics). Escludendo GasStation come vicini: J@1 0.095; escludendo tutte le coppie: 0.071
  (calo in parte circolare: le coppie sono scelte proprio per Jaccard alto). Senza EatAtHome (query e candidato): J@1
  0.092, J@3 0.062.

### [2026-10-04] Passo 2 — STOP 1 approvato: configurazione BM25 congelata, fasce di score_norm, .gitignore
- **Configurazione congelata** in `retrieval/config_bm25.yaml`: stopword sì (lista fissa), stemming sì
  (snowballstemmer, Porter2), k1 = 1.5, b = 0.75 (epsilon 0.25 di default), con commit `c161bab` (working tree
  modificato), tag `testset-v1` (`eb4d28b`) e sha256 della lista di stopword. **Motivazione**: valori standard (default di
  rank_bm25); nessuna delle 48 varianti è significativamente migliore (differenze appaiate entro 2 errori standard); il
  preprocessing completo è significativamente migliore delle varianti ridotte (29 configurazioni su 36). Scelta solo sul
  LOO del corpus.
- **Fasce di score_norm del top-1 per la tassonomia** (domanda 12), fissate PRIMA di guardare il test set e scritte nella
  stessa config: terzili della distribuzione LOO (59 valori, ricalcolati sui valori non arrotondati, numpy.percentile
  lineare). Cut-off **0.28929044** (basso | medio) e **0.34729671** (medio | alto); intervalli basso < c1 ≤ medio < c2 ≤
  alto; nel LOO 20 / 19 / 20. Non si cambiano dopo la FASE 3.
- **.gitignore**: di `data/results/retrieval/<run>/` si versionano `config.json`, `summary.md` e `*.csv`; il resto no
  (verificato con `git check-ignore`).
- **Quasi-duplicati**: nessun quasi-duplicato di contenuto; proposta per i relatori di tenere tutti i candidati (domanda
  10 aggiornata in STATUS.md).
- **Requisito della valutazione** (STATUS.md): il Jaccard sui nomi di classe esatti è un proxy lessicale che favorisce
  BM25; per il confronto con il dense servirà anche una misura non basata sui nomi esatti.

### [2026-10-04] Passo 2 — FASE 3: BM25 congelato sul test set (STOP 2)
- `retrieval/run_testset.py`: legge SOLO la configurazione congelata; hard-fail se la config non è `frozen`, se le
  stopword non hanno lo sha256 congelato, se il test set è cambiato rispetto a `testset-v1`, o se la cartella di output
  esiste già (il test set si guarda una volta sola). Run `testset_2026-10-04_stop2`, eseguita una volta, senza modifiche
  alla configurazione dopo i risultati. Test `check_frozen_config_and_bands`.
- **Risultati** (Jaccard con il ground truth solo descrittivo): 20 esercizi J@1 0.113 e J@3 0.077 contro random 0.015 ±
  0.009 e 0.014 ± 0.005 (20 seed) e oracolo 0.148 e 0.105; Spearman tra score_norm e Jaccard del top-1 ρ = 0.49 (p =
  0.027). Senza l'es. 6: J@1 0.107, J@3 0.076, ρ = 0.42 (p = 0.076).
- **Distribuzioni simili al LOO**: score_norm del top-1 con mediana 0.319 contro 0.311, Jaccard del top-1 con mediana
  0.077 contro 0.071. Fasce sul test set: basso 5 (es. 3, 8, 14, 15, 17: "senza analogo"), medio 8, alto 7; nel LOO 20 /
  19 / 20.
- Es. 6 Flights (known_issues): top-1 AirTravel con score_norm 0.643 (il più alto del test set) e Jaccard 0.235, pari
  all'oracolo. Es. 2 Hollywood → FilmSet (score_norm 0.322, stesso dominio) ma Jaccard 0: esempio concreto del limite
  lessicale del proxy.

### [2026-10-05] Passo 2 — hubness del retrieval (solo descrittivo)
- `retrieval/hubness_report.py` legge solo i CSV delle due run (`loo_2026-10-04_stop1/loo_top3.csv`,
  `testset_2026-10-04_stop2/testset_top3.csv`), senza rifare il retrieval né toccare la configurazione congelata; scrive
  `hubness.csv` e la sezione "Hubness" del `summary.md` della run del test set.
- **Esito: nessun hub marcato.** Candidati distinti al rank 1: 39 su 59 nel LOO, 17 sulle 20 query del test set;
  massimo al rank 1: 4 volte nel LOO (Facepage), 3 sul test set (ClothingCompany, per Furniture, Factory e Online
  Shopping). Nei top-3 il massimo è 9 nel LOO (University; atteso uniforme 3.0) e 5 sul test set (SellingGoods; atteso
  1.0). Candidati mai nei top-3: 5 nel LOO, 26 sul test set. ClothingCompany e SellingGoods, entrambi di vendita
  generica, sono i vicini ricorrenti degli esercizi De Bari di tipo commerciale.

### [2026-10-05] Passo 2 chiuso; Passo 3 diviso in 3a (infrastruttura) e 3b (esperimenti, bloccata)
- STOP 2 approvato. In STATUS.md: stato, comandi del retrieval in ordine, contatori del retrieval (LOO, test set, test set
  senza es. 6), requisiti della valutazione (fasce del test set piccole, 5 / 8 / 7, quindi analisi per fascia
  principalmente descrittiva; correlazione senza l'es. 6 con n = 19 a bassa potenza statistica).
- **Prossimo passo, 3. pipeline di generazione**: **3a** infrastruttura senza chiamate LLM (prompt builder con
  condizioni zero-shot / statico / retrieval, client con cache su disco, post-processing con validazione riusando
  `apollon_convert` in sola lettura); **3b** esecuzione degli esperimenti, BLOCCATA finché i relatori non rispondono
  alle domande 8 (LLM e parametri), 9 (baseline statica) e 11 (metriche). Dense e hybrid restano stub.

### [2026-10-05] Passo 3a — FASE 1: template a blocchi e prompt builder (STOP 1, in attesa di approvazione)
- Contesto: modelli LOCALI via LM Studio (API OpenAI-compatibile). Nessuna chiamata a LLM in questa fase.
- `generation/templates/`: `v4_instructions.txt` (le prime 69 righe di `prompt_template_v4.txt`, fino a "no markdown
  code fences.", identiche byte per byte; il v4 non è modificato), `v4_examples_block.txt` (intestazione "Examples to
  follow:" + segnaposto), `v4_example_item.txt` ("Example N — text: / Example N — JSON:" con il JSON inline),
  `v4_task.txt` ("Here is the textual description of the system to be modeled:" + traccia).
- Diff rispetto al v4, solo nel blocco esempi: l'intestazione perde il rimando ai "file separati"; "JSON: see file …"
  diventa il JSON inline; la nota sull'esempio 2 (storia v3 / orologio) è omessa (proposta).
- `generation/prompt_builder.py`: condizioni zero_shot, static, random, bm25 (config congelata), oracle (solo analisi);
  testo = istruzioni + blocco esempi + traccia; verificato su DB06 che istruzioni e traccia sono identiche in tutte le
  condizioni e che il prompt è deterministico.
- Verifiche: il JSON statico di AirTravel coincide con il record del corpus; la descrizione differisce solo per gli a
  capo (stesse parole), quindi lo statico usa il record del corpus e AirTravel si serializza uguale in ogni condizione.
- **Trovati**: (1) tutti i JSON (corpus, test set, esempi statici) hanno la chiave di primo livello `interactive`,
  mentre le istruzioni v4 dicono "No other top-level fields are allowed"; (2) l'esempio statico 1 (bank loans) ha nomi
  in italiano (Banca, Cliente, Prestito, CodiceFiscale…) con traccia in inglese, tipi non normalizzati (String, Double,
  DateTime, List<Prestito>) e molteplicità "N": non passa lo style check (L4).
- Costi in token (cl100k_base di tiktoken 0.14.0, approssimazione): istruzioni 1.708; JSON di un esempio del corpus in
  media 4.189 (indentato) contro 2.818 (compatto, −33%); prompt DB06: zero_shot 1.914, static 10.354, bm25 k=3 18.818.

### [2026-10-05] Passo 3a — STOP 1 approvato: differenze dal template v4, formato dei prompt
- Contesto: gli esperimenti useranno modelli LOCALI tramite LM Studio (API compatibile OpenAI, default
  `http://localhost:1234/v1`).
- **Tutte le differenze tra il prompt generato e `prompt_template_v4.txt`** (che non è modificato; le istruzioni,
  righe 1-69, restano identiche byte per byte, verificato dai test):
  1. intestazione degli esempi: "Examples to follow (full descriptions and matching JSON are provided as separate
     files alongside this prompt — example_1_bank_loans_v4.json and example_2_airtravel_v4.json):" diventa
     "Examples to follow:" (niente più rimando ai file separati);
  2. "Example N — JSON: see file …" diventa il JSON dell'esempio inserito nel testo, in serializzazione compatta e
     senza la chiave `interactive`;
  3. la nota sull'esempio 2 (storia v3 / esempio dell'orologio, convenzione della classe associativa) è **omessa**;
  4. la descrizione dell'esempio 2 (AirTravel) è presa dal record del corpus: stesse parole del template, a capo
     diversi; così AirTravel si serializza uguale in tutte le condizioni;
  5. la traccia da risolvere è inserita nel testo dopo "Here is the textual description of the system to be
     modeled:" (nel v4 la riga è l'ultima e la traccia veniva accodata);
  6. nelle condizioni diverse da static cambia il contenuto del blocco esempi (zero_shot: blocco assente,
     intestazione compresa; random / bm25 / oracle: k esempi dal corpus normalizzato, numerati da 1).
- Formato: **un solo messaggio utente** (layout `user_only`, default; `system_user` resta disponibile ma non si usa
  senza decisione), **serializzazione compatta**, `drop_interactive` per tutti gli esempi di tutte le condizioni.
- Ordine degli esempi: bm25 e oracle il più simile per ultimo; static l'ordine del template; random l'ordine di
  estrazione.
- `interactive` in output: lo schema lo ammette come facoltativo, quindi presenza o assenza NON è un errore; si
  registra a parte come "istruzione non rispettata", fuori dai livelli L0-L4.
- Esempio bank loans: invariato (baseline studio 2025), eccezione documentata. Nel controllo di sanità non è escluso:
  si verifica contro un elenco ESPLICITO delle violazioni attese; una violazione non elencata fa fallire il
  controllo. Domanda 9 per i relatori estesa (bm25 vs random come confronto pulito sulla pertinenza; variante
  `static_normalized` da valutare).
- Lunghezza del prompt come covariata: caratteri e token (stimati e, se forniti dal server, reali) di ogni chiamata in
  `manifest.jsonl`; annotato nei requisiti della valutazione di STATUS.md.
- Id: il template v4 usa come esempio un UUID non valido ("a1b2c3d4-e5f6-4890-81h2-i3j4k5l6m7n8"); le istruzioni non
  si toccano. `verify_apollon_json` NON impone il formato UUID (controlla id di nodo unici, id dei membri unici per
  nodo, source/target esistenti, dimensioni positive, almeno 2 punti per edge); L3 aggiunge l'unicità degli id in
  tutto il diagramma, chiesta dalle istruzioni, e la protezione da strutture malformate, senza modificare
  `apollon_convert`.
- `PromptSpec`: default `serialization="compact"`, `layout="user_only"` (il nome provvisorio `single_user` è
  rinominato), `drop_interactive=True`.

### [2026-10-05] Passo 3a — FASI 2 e 3: client LM Studio, post-processing L0-L4, runner (STOP 2, in attesa di approvazione)
- **`generation/llm_client.py`**: `GenerationParams` (temperature, top_p, max_tokens, seed, structured_output),
  `GenerationResult` (testo, finish_reason, modello, parametri, ripetizione, latenza, token del server, cached).
  `MockClient` (risposte da dizionario o da `<id>.txt`); `LMStudioClient` (POST `{base_url}/chat/completions`, solo
  urllib, nessuna chiave API; timeout; retry con backoff esponenziale su errori di rete, timeout, 5xx e 429; gli
  altri 4xx falliscono subito); `CachedClient` (cache su disco, chiave = sha256 di messaggi, modello, parametri,
  ripetizione). Il seed è tra i parametri che LM Studio dichiara supportati; se il server lo rispetta lo dirà lo
  smoke test (due chiamate identiche con temperature 0.7).
- **Output strutturato**: secondo la documentazione di LM Studio (pagine "Structured Output" e "Chat Completions"
  della compatibilità OpenAI) si attiva con `response_format: {"type": "json_schema", "json_schema": {"name",
  "strict", "schema"}}`; per i GGUF usa il campionamento a grammatica di llama.cpp, per MLX Outlines; non tutti i
  modelli lo supportano (specie sotto i 7B). Implementato con `evaluation/uml-model-4.schema.json`, DISATTIVATO di
  default; domanda 14 per i relatori. Non è stato provato contro un server reale.
- **`generation/postprocess.py`**: rimozione dei blocchi di ragionamento (`<think>`, `<thinking>`, `<reasoning>`;
  anche senza tag di apertura o non chiusi), estrazione (risposta intera, blocco ```, oggetto {...} bilanciato) e
  livelli cumulativi L0 estratto / L1 JSON / L2 schema / L3 integrità / L4 stile. Esito `failure`: no_json,
  truncated (finish_reason = length), incomplete_json (oggetto non chiuso senza troncamento dichiarato),
  invalid_json, not_object, schema, integrity, style. Istruzioni non rispettate a parte: interactive_present,
  extra_text, version_not_4_2_0, type_not_class_diagram, node_type_not_class, out_of_canvas, overlapping_nodes,
  measured_mismatch, empty_method_name.
- **Conflitti tra `style_check` e le istruzioni v4** (trovati leggendo il codice, `apollon_convert` non modificato):
  (a) le istruzioni danno per i metodi la forma "methodName(parameters): ReturnType", senza "+ ", mentre
  style_check vuole "+ "; (b) le istruzioni ammettono la molteplicità "1..n", style_check la segnala. **Proposta
  (da approvare)**: L4 = style_check su una copia in cui queste due forme sono riscritte nella forma del corpus
  ("+ " davanti al metodo, "..n" → "..*"); i messaggi grezzi di style_check si registrano comunque (`style_raw`).
  style_check non controlla i tipi di ritorno dei metodi (es. List<...>) né i bounds / le sovrapposizioni.
- **`generation/sanity_check.py`**: 20 ground truth, 59 JSON del corpus e AirTravel superano L0-L4 con style_check
  grezzo vuoto; l'unica istruzione non rispettata è `interactive` (in tutti). Bank loans fallisce L4 con esattamente
  le 10 violazioni attese (7 tipi String / Double / DateTime, 3 molteplicità "N"); inventario esatto di 3 classi e 9
  attributi con nomi italiani e 2 tipi di ritorno List<Prestito>.
- **`experiments/run_experiment.py`** + `experiments/configs/` (`dryrun_testset.yaml`, `mock_e2e.yaml`,
  `lmstudio_template.yaml`): output in `data/results/generation/<run_id>/` (config.json con commit, tag testset-v1,
  sha256 di config_bm25.yaml, versioni; prompts/, raw/, parsed/, validation.csv, manifest.jsonl, cache/); rifiuta
  la sovrascrittura, `--resume` riprende saltando le chiamate registrate e usando la cache; con il client lmstudio
  rifiuta di partire se mancano client.model, generation.{temperature, top_p, max_tokens, seed} o i metadati
  (model_id, quantization, context_length, lmstudio_version, hardware cpu / gpu / ram_gb / vram_gb). Ripetizione r:
  seed + r se il seed è impostato. `--dry-run` scrive `data/results/generation/dry_run/<run_id>/` (CSV + summary.md
  con lunghezze dei prompt, token di output stimati dai 20 ground truth compatti e indentati, finestre 8k / 16k /
  32k).
- **`experiments/smoke_lmstudio.py`**: smoke test MANUALE (prompt `{"ok": true}`, nessun dato del corpus o del test
  set); lo esegue l'utente con LM Studio aperto.
- Run mock (`mock_e2e`, 3 esercizi × 5 condizioni × 2 ripetizioni = 30 chiamate, risposte sintetiche): DB01 L4,
  DB06 fallisce L3 (id duplicato) con ragionamento e fence rimossi, DB13 troncata. Test:
  `generation/test_generation.py` (prompt, cache, server HTTP finto, estrazione, livelli, runner; nessun LLM reale).
- `requirements.txt`: `tiktoken==0.14.0` fissato (scarica la codifica cl100k_base al primo uso).

### [2026-10-05] Passo 3a — STOP 2 approvato e chiusura: riscritture L4, diagnostici separati, verifica del seed, contesto e max_tokens identici per modello
- **L4 approvato**, con un elenco CHIUSO di riscritture prima di style_check (`L4_REWRITES` in
  `generation/postprocess.py`), applicate a una copia del diagramma:
  1. `method_v4_form`: metodo nella forma del template v4 "nome(parametri): Tipo" (o "nome(parametri)"), senza
     "+ " → forma del corpus "+ nome(parametri) : Tipo";
  2. `multiplicity_n`: molteplicità esattamente "1..n" / "0..n" / "n" → "1..*" / "0..*" / "*" ("N" maiuscola, "1..N",
     "2..n" ecc. NON sono riscritte e restano violazioni).
  Qualunque altra riscrittura richiede una decisione esplicita. `validation.csv` registra per risposta il numero di
  riscritture (`l4_rewrites_total`, `l4_rewrites` per tipo) e i messaggi originali di style_check (`style_raw`,
  `style_raw_count`). In STATUS.md, per la valutazione semantica: "1..n" e "1..*" equivalenti.
- **Istruzioni non rispettate** in due categorie separate: "formato della risposta" (`format_issues`: extra_text,
  interactive_present, version_not_4_2_0, type_not_class_diagram, node_type_not_class, empty_method_name) e
  "layout" (`layout_issues`: out_of_canvas, overlapping_nodes, measured_mismatch). Sono diagnostici, non metriche di
  qualità: non si combinano tra loro né con L0-L4 in un unico punteggio. Se la struttura è troppo malformata per i
  controlli, `format_issues` contiene `unchecked`.
- **Smoke test**: `experiments/smoke_lmstudio.py` aggiunge la verifica del seed: un prompt banale con risposte
  variabili (il nome di un gatto) inviato due volte con lo stesso seed e una volta con un seed diverso, a temperature
  0.8 (caso significativo) e a temperature 0 (riportato, poco informativo). Esito "seed rispettato: si / no / non
  determinabile" (non determinabile = risposta uguale anche con seed diverso). Provato solo contro il server finto
  dei test, per verificare che lo script funzioni; l'esito reale lo darà l'esecuzione dell'utente.
- **Regola metodologica**: per uno stesso modello (model_id + quantizzazione) la lunghezza di contesto impostata in
  LM Studio e `max_tokens` sono identici per tutte le condizioni e tutti i k. Dentro una config sono unici per
  costruzione; tra config diverse il runner confronta la nuova run con le `config.json` delle run presenti nella
  cartella dei risultati e rifiuta di partire se differiscono (`inconsistent_runs`, testato). Domanda 8 per i
  relatori estesa con le tabelle del dry run e la nota sulle finestre (k=3: solo 32k sicura; k=2 a 16k: margine di
  circa 1.700 token nel caso peggiore, bm25 11.192 + 3.509 = 14.701 su 16.384).
- **Verifica dello stato dopo l'interruzione della sessione** (git status): mancavano solo i nuovi default di
  `PromptSpec` e la voce 64 di questo file, rifatti; il resto del Passo 3a FASE 1 (template, prompt builder, voce 63)
  e tutto il Passo 2 (commit 8db2c2c) erano presenti. `data/results/generation/stop1_db06/` (ignorata da git)
  contiene i prompt d'esempio della FASE 1 nel formato PRECEDENTE (indentato, con `interactive`): non più
  rappresentativi.
- **Passo 3a chiuso.** Passo 3b bloccato sulle domande 8, 9, 11 e 14.

### [2026-10-06] Vocabolario cl100k_base versionato: stima dei token senza download
- Contesto: su un clone pulito `tiktoken.get_encoding("cl100k_base")` scarica il vocabolario da
  openaipublic.blob.core.windows.net al primo uso; offline o con il download bloccato `run_experiment.py` e
  `test_generation.py` fallivano (HTTPError 403 nell'ambiente dell'utente). Stessa regola delle stopword: niente
  download a runtime.
- `generation/tokenizer/cl100k_base.tiktoken` (1.681.126 byte, copia del file ufficiale già in cache in questa
  macchina) con `cl100k_base.tiktoken.sha256` = `223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7`,
  uguale all'`expected_hash` di tiktoken 0.14.0 (`tiktoken_ext/openai_public.py`).
- `generation/token_estimate.py` costruisce l'Encoding esplicitamente (`tiktoken.Encoding` con il vocabolario dal
  file, `pat_str` e token speciali copiati da tiktoken 0.14.0) e verifica lo sha256 a ogni caricamento: se non
  coincide, errore. Scelto al posto di `TIKTOKEN_CACHE_DIR` perché non dipende dal nome di cache interno di tiktoken
  (sha1 dell'URL) né da variabili d'ambiente. `count_tokens` usa `disallowed_special=()`: un eventuale
  "<|endoftext|>" nel testo si conta come testo invece di dare errore (nessun effetto sui prompt attuali).
  `run_experiment.py` usa questo modulo e registra in `config.json` il percorso e lo sha256 del vocabolario.
- `.gitattributes` (nuovo): `generation/tokenizer/* -text`. Con `core.autocrlf=true` un checkout Windows
  convertirebbe gli a capo e lo sha256 non coinciderebbe; verificato su un clone usa e getta nello scratchpad (il file
  resta LF e lo sha256 coincide).
- Test (`check_tokenizer_offline` in `generation/test_generation.py`): connessioni di rete rifiutate e
  `TIKTOKEN_CACHE_DIR` vuota; verifica gli id di "hello world" ([15339, 1917]), che le istruzioni v4 contino 1.708
  token come riportato, che la cache resti vuota e che un vocabolario con a capo CRLF sia rifiutato.
- Conteggi invariati: la dry run rifatta con la rete bloccata produce `dry_run.csv` (220 righe) e `summary.md`
  identici byte per byte a quelli del 2026-10-05; le tabelle della domanda 8 restano valide.
- Trovato nel verificare: lo stesso problema di a capo riguarda `retrieval/stopwords_en.txt` (sha256 nella config
  congelata): su un clone Windows pulito non coincide. Risolto nella voce 68.
- `generation/tokenizer/README.md`: fonte, versione di tiktoken, sha256, licenza, motivo della presenza nel repo.

### [2026-10-06] Censimento degli sha256 su file e regole `-text` in .gitattributes
- Contesto: su un clone Windows pulito (`core.autocrlf=true`) `retrieval/stopwords_en.txt` usciva con CRLF, lo sha256
  diventava `eb190297…` invece di `5be3f507…` e `run_testset.py` rifiutava la configurazione congelata ("lista di
  stopword diversa da quella congelata"). Approvato: `retrieval/stopwords_en.txt -text`, più un censimento di tutti
  gli sha256 calcolati su file.
- **Censimento** (ricerca di sha256 / hashlib in tutto il repository):

  | file | dove è registrato lo sha256 | regola `-text` | verificato su clone CRLF |
  |---|---|---|---|
  | `retrieval/stopwords_en.txt` | `retrieval/config_bm25.yaml` (`stopwords_sha256`), riverificato da `run_testset.load_frozen_config` (anche in `test_retrieval.py`) | sì | sì |
  | `generation/tokenizer/cl100k_base.tiktoken` | `generation/tokenizer/cl100k_base.tiktoken.sha256`, riverificato da `generation/token_estimate.py` | sì (cartella) | sì |
  | `generation/tokenizer/cl100k_base.tiktoken.sha256` | è il file che contiene l'hash; letto con split, robusto agli a capo, ma `sha256sum -c` richiede LF | sì (cartella) | sì |
  | `retrieval/config_bm25.yaml` | `config.json` delle run di generazione (`provenance.config_bm25_sha256`, `run_experiment.py`); registrato come provenienza, non riverificato | sì | sì (sha256 `d6dfa722…` uguale al checkout attuale) |

  Hash che NON richiedono la regola:
  - stesso checkout, prima/dopo: `snapshot_corpus()` in `retrieval/test_retrieval.py` e `generation/test_generation.py`
    ("nessuna scrittura in corpus/"); la baseline degli 81 output del Passo 1 (`baseline_riordino.sha256`, solo
    nello scratchpad di sessione, fuori dal repository) è anch'essa un confronto sullo stesso checkout;
  - hash di contenuti in memoria, non di file: `prompt_sha256` nel manifest e chiave della cache
    (`llm_client.cache_key`, sui messaggi), ordine di `retrieval/random_retriever.py` (seed + testo della query); i
    template e le descrizioni si leggono con `read_text`, che normalizza gli a capo;
  - controllo del test set contro il tag `testset-v1` in `run_testset.py`: usa `git diff`, che tiene conto della
    conversione degli a capo (oggi `corpus.jsonl` è CRLF nel checkout e il controllo passa);
  - `data/results/retrieval/*/config.json`: nessuno sha256 registrato.
- Verifica: clone di appoggio con `core.autocrlf=false` (indice LF come il repository) in cui sono committate SOLO lì
  le modifiche di lavoro, poi clone con `core.autocrlf=true`: i quattro file sopra escono LF, `sha256sum -c` OK,
  `run_testset.load_frozen_config()` accetta la configurazione, `token_estimate` carica il vocabolario,
  `test_retrieval.py` e `test_generation.py` passano. Il repository vero non è stato toccato (nessun commit).
- Nota: `.gitattributes` vale per i checkout successivi; un clone esistente con i file già in CRLF va ricreato o
  riallineato (STATUS.md, regole della generazione). Il checkout attuale dell'utente ha i quattro file già LF.

### [2026-10-06] Gemma 4 12B QAT: ragionamento, parametri espliciti, metadati enable_thinking
- Contesto: modello scelto dall'utente per lo smoke test e il pilota, Gemma 4 12B QAT in LM Studio
  (lmstudio.ai/models/google/gemma-4-12b-qat). Secondo la pagina del modello: "Enable Thinking" attivo di default,
  marcatori di ragionamento `<|channel>thought` … `<channel|>`, parametri consigliati temperature 1, top_k 64, top_p
  0.95, repeat penalty 1. Il GGUF di riferimento (lmstudio-community/gemma-4-12B-it-QAT-GGUF) è Q4_0.
- **Ragionamento nel testo** (`generation/postprocess.py`): `REASONING_MARKERS` (nome → apertura, chiusura) con
  `<think>`, `<thinking>`, `<reasoning>` e `gemma4_channel_thought` (`<|channel>\s*thought` … `<channel|>`). Per ogni
  marcatore: blocchi completi rimossi; chiusura senza apertura → si scarta ciò che precede; apertura mai chiusa → si
  scarta ciò che segue (ragionamento troncato: con finish_reason = length l'esito è "truncated", altrimenti
  "no_json"). `reasoning_markers(text)` elenca i marcatori presenti (manifest e smoke test).
- **Ragionamento in un campo separato** (`generation/llm_client.py`): LM Studio può restituirlo in
  `reasoning_content` (impostazione "separate reasoning_content and content in API responses" in App Settings >
  Developer, attiva di default secondo le note di LM Studio); si legge anche `reasoning`. Va in
  `GenerationResult.reasoning_text` (quindi nel raw della run) e mai in `text`: l'estrazione del JSON usa solo
  `text` (test: un JSON valido presente SOLO nel ragionamento non viene estratto). Token del ragionamento da
  `usage.completion_tokens_details.reasoning_tokens` se il server li fornisce (`reasoning_tokens_source = server`),
  altrimenti stimati con cl100k_base (`stima_cl100k`). Manifest: `reasoning_field`, `reasoning_chars`,
  `reasoning_tokens`, `reasoning_tokens_source`, `reasoning_markers_in_content`, `content_empty`.
- **Metadati obbligatori**: `enable_thinking` (booleano, come impostato in LM Studio; "TODO" o un valore non
  booleano fanno rifiutare la run). Per Gemma 4 la quantizzazione si registra come "QAT (q4_0)".
- **Parametri sempre espliciti**: `GenerationParams.top_k` aggiunto; `LMStudioClient` invia sempre temperature,
  top_p, top_k, max_tokens e seed (tutti elencati come supportati nella pagina "Chat Completions" della
  compatibilità OpenAI di LM Studio) e rifiuta la richiesta se uno è None. Un parametro dichiarato non supportato
  in `client.unsupported_params` non si invia e si registra (`params_not_sent`); i valori inviati sono in
  `request_params` (raw e manifest). Il runner richiede generation.{temperature, top_p, top_k, max_tokens, seed}
  senza segnaposto. Effetto collaterale: top_k entra nella chiave della cache (nessuna run reale esistente).
- `experiments/smoke_lmstudio.py`: stampa i parametri inviati, i marcatori di ragionamento nel testo e l'eventuale
  campo separato (caratteri, token); il confronto del seed usa il testo senza ragionamento; invia top_k = 40 e
  top_p = 1.0 espliciti (solo per lo smoke test).
- Config: `lmstudio_template.yaml` aggiornato (top_k, enable_thinking, unsupported_params);
  `gemma4_12b_qat_template.yaml` nuovo, con i dati noti (model_id, quantizzazione) e TODO per il resto (il runner lo
  rifiuta finché restano TODO).
- **Licenza**: l'utente ha chiesto di annotare che Gemma 4 è soggetto ai Gemma Terms of Use; le fonti verificate
  indicano invece Apache 2.0 (blog ufficiale Google Open Source, marzo 2026, "Gemma 4: Expanding the Gemmaverse with
  Apache 2.0"; scheda Hugging Face del GGUF: `apache-2.0`). Annotato in STATUS.md ("Modelli") come Apache 2.0, da
  confermare dall'utente.
- Test: casi Gemma 4 nell'estrazione (blocco completo, senza apertura, con fence, troncato con e senza
  finish_reason = length); server finto con `reasoning_content` (token dal server, stimati, solo ragionamento con
  contenuto vuoto); parametri None rifiutati senza inviare la richiesta; `unsupported_params`; metadati
  enable_thinking; run lmstudio completa sul server finto con ragionamento separato nel raw e nel manifest.

### [2026-10-06] Licenza di Gemma 4 confermata: Apache 2.0
- L'utente conferma: Gemma 4 è distribuito con licenza Apache 2.0 (blog ufficiale Google Open Source, "Gemma 4:
  Expanding the Gemmaverse with Apache 2.0", pubblicato giovedì 2 aprile 2026, data verificata sulla pagina
  dall'utente; il /2026/03/ dell'URL è il percorso di Blogger, non la data di pubblicazione; primi modelli
  Gemma sotto una licenza approvata da OSI). Il riferimento ai Gemma Terms of Use della richiesta precedente era
  errato: valevano per Gemma 1-3. Corregge la voce 69, dove la licenza era indicata come "da confermare".
- STATUS.md, sezione "Modelli": Apache 2.0 con le fonti (blog Google Open Source, scheda Hugging Face del GGUF
  `lmstudio-community/gemma-4-12B-it-QAT-GGUF`).

### [2026-10-06] Primo smoke test con Gemma 4 12B QAT: ragionamento attivo, smoke test corretto
- **Esito del primo smoke test** (eseguito dall'utente con LM Studio, Gemma 4 12B QAT, "Enable Thinking" attivo come
  da default): il server restituisce il ragionamento nel campo separato `reasoning_content`, 947-1021 token per
  risposta; nel test del seed le risposte erano VUOTE perché max_tokens si esauriva nel ragionamento. Lo script ha
  concluso "seed rispettato: no", che è sbagliato: con risposte vuote il seed non è valutabile. Il rispetto del seed
  resta quindi NON verificato.
- **Correzioni a `experiments/smoke_lmstudio.py`**:
  1. per ogni chiamata del test del seed stampa finish_reason e token di completamento;
  2. `seed_verdict`: se una risposta (tolto il ragionamento) è vuota o ha finish_reason = length l'esito è "non
     valutabile (risposte vuote o troncate)", mai "si" o "no";
  3. se c'è ragionamento (campo separato o marcatori nel testo) stampa un avviso incorniciato: "RAGIONAMENTO ATTIVO:
     disattiva Enable Thinking nelle impostazioni del modello in LM Studio (My Models), poi ricarica il modello",
     dopo la chiamata interessata e di nuovo nel riepilogo;
  4. il test del seed usa max_tokens = 512 (sufficiente per la frase richiesta senza ragionamento) e stampa i
     parametri inviati.
- Test (`check_smoke` in `generation/test_generation.py`, server finto): risposte vuote con ragionamento e
  finish_reason = length → entrambi gli esiti "non valutabile" e avviso presente; testo che dipende dal seed → "si"
  e nessun avviso; `seed_verdict` su casi costruiti (si, no, non determinabile, vuote, troncate, solo ragionamento).
- Prossimo passo dell'utente: disattivare Enable Thinking, ricaricare il modello e rieseguire lo smoke test; nei
  metadati delle run `enable_thinking` andrà registrato di conseguenza.

### [2026-10-06] Secondo smoke test con Gemma 4 12B QAT: seed non rispettato, riproducibilità a livello di analisi
- **Configurazione** (riferita dall'utente): Gemma 4 12B QAT in LM Studio, Enable Thinking SPENTO nelle impostazioni
  del modello e modello ricaricato; contesto 32768; modello interamente in VRAM su NVIDIA RTX 4070 12 GB (9,9 / 12
  GB dedicata, 0,2 GB condivisa).
- **Esiti** (riferiti dall'utente):
  - ragionamento assente: nessun `reasoning_content`, nessun marcatore nel testo;
  - `{"ok": true}` corretto, 6 token di completamento, latenza 2,42 s;
  - **seed NON rispettato**: a temperature 0.8 lo stesso seed dà risposte diverse;
  - a temperature 0 quasi deterministico ma non del tutto: con il seed diverso stesso testo salvo uno spazio mancante.
- **Prova**: `docs/smoke_tests/2026-10-06_google-gemma-4-12b-qat_smoke2.txt` (versionato; `data/results/` è ignorata
  da git tranne le run del retrieval; nome iniziale `2026-10-06_gemma4-12b-qat_smoke2.txt`, rinominato con `git mv`
  per allinearlo alla convenzione di `--save`, voce 73). Prova MANUALE, senza .json: contiene configurazione ed esiti;
  l'output integrale del terminale va INCOLLATO dall'utente al posto del segnaposto: non è stato ricostruito, perché
  non disponibile in questa sessione. Il primo smoke test (voce 71) ha la sua prova manuale
  `2026-10-06_google-gemma-4-12b-qat_smoke1.txt`, anch'essa con segnaposto per l'output.
- **Conseguenze**:
  - STATUS.md, regole della generazione: il seed non garantisce la riproducibilità con LM Studio; la riproducibilità è
    garantita a livello di ANALISI (risposte grezze in `raw/` e in cache), non di generazione;
  - `experiments/configs/gemma4_12b_qat_template.yaml`: contesto 32768, `enable_thinking: false`, GPU RTX 4070 12
    GB, `vram_gb: 12`, `vram_used` (9,9 GB dedicata + 0,2 GB condivisa con 32k). Restano TODO: id del modello, versione
    di LM Studio, CPU, RAM e parametri di generazione;
  - domanda 8: opzioni (a) temperature 0, 1 ripetizione per cella e controllo di riproducibilità su un sottoinsieme
    ripetuto (PROPOSTA PRINCIPALE), (b) temperature 0.2-0.3 con 3+ ripetizioni (costo triplo, variabilità misurata);
  - domanda 15 (nuova): ragionamento spento negli esperimenti principali (token di output, tempi, variabilità,
    confrontabilità tra modelli), con l'opzione di un esperimento aggiuntivo con ragionamento acceso. Il Passo 3b
    resta bloccato anche su questa domanda.

### [2026-10-06] smoke_lmstudio.py --save: prova versionata (.txt + .json) senza copia-incolla
- Contesto: la prova del secondo smoke test dipendeva dal copia-incolla dell'output (file smoke2 con segnaposto, lo
  completa l'utente con l'output originale). Approvata l'opzione `--save`.
- `python experiments/smoke_lmstudio.py --model <id> --save` scrive in `docs/smoke_tests/`:
  - `<data>_<id-modello>_smokeN.txt`: intestazione (data/ora con fuso, base_url, id del modello, versione dello
    script `SCRIPT_VERSION` e sha256 del file dello script, nome del .json) + output completo del terminale (catturato
    mentre viene stampato);
  - `<stesso nome>.json`: esiti strutturati, confrontabili tra modelli: risposta attesa sì/no, presenza di
    ragionamento (campo, caratteri, token e loro fonte, marcatori nel testo), esito del seed per ciascuna temperatura,
    e per ogni chiamata seed, risposta senza ragionamento, finish_reason, token di prompt e di completamento, latenza,
    parametri inviati e non inviati, modello riportato dal server.
- Numerazione: N progressivo per data e id del modello (il primo numero libero dopo il massimo esistente, contando sia
  i .txt sia i .json); scrittura in creazione esclusiva (`open(..., "x")`): un file esistente non si sovrascrive mai.
  L'id del modello diventa un nome di file sostituendo i caratteri diversi da lettere, cifre, ".", "_" e "-" con
  "-" (es. `google/gemma-4-12b-qat` → `google-gemma-4-12b-qat`).
- **Prove manuali allineate alla convenzione** (2026-10-06): `2026-10-06_gemma4-12b-qat_smoke2.txt` rinominato con
  `git mv` in `2026-10-06_google-gemma-4-12b-qat_smoke2.txt`; creato `2026-10-06_google-gemma-4-12b-qat_smoke1.txt`
  per il primo smoke test (ragionamento attivo, voce 71). Entrambi iniziano con "PROVA MANUALE (output incollato
  dall'utente), non generata da --save", dichiarano che non c'è il .json e riportano modello, data e impostazioni
  (smoke1: Enable Thinking attivo; smoke2: spento, contesto 32768); l'output lo incolla l'utente al posto del
  segnaposto. Verificato con `next_paths` sulla cartella reale: il prossimo salvataggio automatico di oggi per
  `google/gemma-4-12b-qat` è `..._smoke3.txt` / `.json`.
- Se una chiamata fallisce (es. server irraggiungibile) la prova si salva comunque, con l'errore nel .json e il
  traceback nel .txt; lo script esce con codice 1.
- Test (`check_smoke` in `generation/test_generation.py`, cartella temporanea e server finto): .txt con intestazione
  e output completo, .json con gli esiti attesi (non valutabile + ragionamento; seed rispettato → "si"), numerazione
  che salta i numeri occupati anche dal solo .json, file di un altro modello ignorato, file esistente intatto, prova
  salvata anche con il server irraggiungibile. I test non scrivono in `docs/smoke_tests/`.

### [2026-10-06] Output degli smoke test 1 e 2 incollati; temperature 0 deterministico nello smoke 2; metadati del template Gemma
- **Prove completate**: in `docs/smoke_tests/2026-10-06_google-gemma-4-12b-qat_smoke1.txt` e `..._smoke2.txt` il
  segnaposto è sostituito con l'output fornito dall'utente, copiato alla lettera; le osservazioni sono in "Note di
  lettura", nell'intestazione, fuori dal blocco dell'output.
- **Smoke 1** (ragionamento attivo, script precedente alla voce 71): `{"ok": true}` corretto anche con il
  ragionamento (130 token di completamento, 120 di ragionamento, latenza 4,70 s); nel test del seed 947 e 1021 token
  di `reasoning_content`, una sola risposta non vuota su sei. Con lo script attuale entrambi gli esiti sarebbero
  "non valutabile".
- **Smoke 2 — correzione della voce 72**: la voce 72 (dal riassunto dell'utente) diceva "a temperature 0 quasi
  deterministico ma non del tutto: con il seed diverso stesso testo salvo uno spazio mancante". L'output mostra invece
  che lo script ha concluso "non determinabile (risposta uguale anche con seed diverso)", esito che `seed_verdict`
  restituisce SOLO se le tre stringhe (tolto il ragionamento) sono identiche; con uno spazio di differenza avrebbe
  restituito "si". La riga stampata è la `repr` della stessa stringa confrontata, quindi la parola unita "onlywhen"
  non era nella risposta: è quasi certamente un artefatto del copia-incolla dal terminale (a capo automatico nel
  punto dello spazio). Lo stesso artefatto compare nella terza risposta a temperature 0.8, dove non cambia l'esito
  (le due risposte con lo stesso seed sono diverse comunque). **Conclusione corretta**: a temperature 0 le tre
  risposte sono identiche e il seed non ha effetto; a temperature 0.8 il seed non è rispettato. Aggiornati STATUS.md
  (regola sulla riproducibilità e domanda 8); la proposta (a) della domanda 8 resta, perché un prompt breve non
  dimostra il determinismo sui prompt lunghi degli esperimenti.
- **Template `experiments/configs/gemma4_12b_qat_template.yaml`** (completati i TODO che non sono parametri di
  generazione):
  - `client.model`: `google/gemma-4-12b-qat`;
  - `lmstudio_version`: `0.4.25+1`, rilevata dall'installazione (`LM Studio.exe`, ProductVersion 0.4.25.0; voce di
    disinstallazione "LM Studio 0.4.25+1"); `lms version` riporta solo il commit della CLI (69d945a);
  - `hardware.cpu`: AMD Ryzen 7 7800X3D 8-Core Processor (8 core, 16 thread), rilevata dal sistema;
  - `hardware.ram_gb`: **32**, rilevata dal sistema (32 GB di moduli installati; 33.463.476.224 byte visibili al
    sistema). L'utente aveva indicato 16 GB: registrato il valore rilevato, **da confermare**;
  - restano TODO `run_id` e i parametri di generazione (temperature, top_p, top_k, max_tokens), da decidere con il
    pilota: il runner continua a rifiutare il template.

### [2026-10-06] Pilota sulla temperatura (solo corpus): selezione, config e regola di decisione registrate PRIMA della run (STOP 1)
- **Scopo**: scegliere tra le opzioni della domanda 8, (a) temperature 0 con 1 ripetizione per cella e (b) temperature
  0.3 con 3 ripetizioni, con dati misurati su esercizi del CORPUS, MAI del test set; prima verifica che Gemma 4 12B
  QAT regga il compito. **Esperimento preliminare**, da dichiarare come tale in tesi. I dati del pilota non entrano
  nei risultati del Passo 3b.
- **Query dal corpus** (`generation/prompt_builder.py`, `experiments/run_experiment.py` con `split: corpus`): per
  una query del corpus la selezione è leave-one-out con lo stesso protocollo di `retrieval/analyze_retrieval.loo`:
  bm25 su un indice RIFITTATO sugli altri 58 record con la config congelata (la query non entra nelle statistiche
  IDF / avgdl); random e oracle sugli altri 58; static con la query AirTravel rifiutata. `build()` fallisce se la
  query compare tra i propri esempi. Verificato: per le 59 query il top-3 bm25 e lo score_norm coincidono con
  `data/results/retrieval/loo_2026-10-04_stop1/loo_top3.csv`.
- **Regola di selezione** (deterministica, `experiments/select_pilot.py`): candidati = i 59 record convertiti senza
  known_issues (escluso solo EatAtHome); fascia = score_norm del top-1 bm25 LOO con i cut-off congelati (basso <
  0.2893 <= medio < 0.3473 <= alto; conteggi ricalcolati 20 / 19 / 20, uguali a quelli congelati); dimensione =
  numero totale di elementi del diagramma di riferimento dai conteggi `apollon_counts` (classi + interfacce +
  enumerazioni + attributi + operazioni + valori di enumerazione + relazioni); per fascia il più piccolo e il più
  grande, a parità ordine per id (nessuna parità agli estremi). Esito:

  | fascia | ruolo | esercizio | score_norm top-1 | dimensione | ground truth compatto (token stimati) |
  |---|---|---|---|---|---|
  | basso | piccolo | Louvre | 0.2356 | 20 | 1.724 |
  | basso | grande | HotelBookingManagementSystem | 0.1982 | 73 | 6.525 |
  | medio | piccolo | StudentAppointment | 0.3034 | 12 | 1.308 |
  | medio | grande | TeamSportsScoutingSystem | 0.3215 | 57 | 4.318 |
  | alto | piccolo | ApartmentBuilding | 0.4264 | 10 | 841 |
  | alto | grande | SmartHomeAutomationSystem | 0.3536 | 71 | 7.145 |

- **Config** `experiments/configs/pilot_temperature.yaml`: bm25, k = 2, temperature [0.0, 0.3], 3 ripetizioni per
  entrambe (servono anche a misurare la variabilità a temperature 0), top_p 0.95 e top_k 64 IDENTICI per le due
  temperature (valori raccomandati nella scheda del modello), max_tokens 8192, seed 42 + r, contesto 32768,
  enable_thinking false, `stop_on_reasoning: true` (la run si ferma, dopo aver salvato la chiamata, se in una
  risposta compare ragionamento). 6 × 2 × 3 = 36 generazioni. Prompt stimati (cl100k_base): 6.626 / 9.069 / 11.279
  token (min / mediana / max), quindi prompt + max_tokens <= 19.471 < 32.768.
- **REGOLA DI DECISIONE** (registrata prima della run; non si modifica dopo aver visto i dati). Per ciascuna
  temperatura T in {0, 0.3}, sulle sue 18 risposte (6 esercizi × 3 ripetizioni):
  - V(T) = numero di risposte che superano L0-L3 (livello >= 3);
  - J(T) = media, sulle risposte che superano L1, del Jaccard dei nomi di classe (normalizzati come
    `corpus_loader.class_names`, case-insensitive) tra la risposta e il diagramma di riferimento dell'esercizio;
  - **controllo preliminare**: se una delle due temperature tronca PIÙ di 1 risposta su 18 (`failure = truncated`,
    cioè finish_reason = length), oppure se la run è stata fermata per ragionamento, oppure se per una temperatura
    nessuna risposta supera L1 (J non definito): si segnala e ci si ferma PRIMA di decidere;
  - **opzione (a)** se V(0) >= V(0.3) **e** J(0) >= J(0.3) − 0.05;
  - **altrimenti opzione (b)**.
  La regola è descrittiva (n = 18 per temperatura, nessun test statistico). Variabilità tra ripetizioni, livelli
  L4, diagnostici di formato e di layout, tempi e token si riportano ma non entrano nella regola.
- **Rischio segnalato allo STOP 1**: i due esercizi grandi hanno un ground truth vicino o oltre max_tokens = 8192
  (SmartHomeAutomationSystem 7.145 token compatto, 10.232 indentato; HotelBookingManagementSystem 6.525 / 9.186). Se
  il modello indenta il JSON o lo produce più lungo del riferimento, fino a 6 risposte per temperatura possono essere
  troncate e il controllo preliminare fermerebbe la decisione. Questi due esercizi sono più grandi di qualunque
  ground truth del test set (massimo 3.509 compatto, 5.056 indentato). Proposta all'utente: max_tokens 12288
  (prompt max del pilota 11.279 + 12.288 = 23.567; nel Passo 3b con k = 3, prompt max 17.256 + 12.288 = 29.544 <
  32.768, compatibile con la regola "contesto e max_tokens identici per modello"). Il config resta a 8192 finché
  l'utente non decide.
- **Versionamento** (`.gitignore`): per le run di generazione si versionano `config.json`, `manifest.jsonl`,
  `validation.csv`, `summary.md` e `raw/`; non `prompts/` (rigenerabili), `parsed/` (derivati da raw), `cache/`
  (duplicato di raw); esclusi `mock_*` e `dry_run/`. Motivo: il seed non è rispettato (voci 72 e 74), quindi le
  risposte grezze sono l'unica base per riprodurre l'analisi. Verificato con `git check-ignore --no-index`.
- Template Gemma: RAM 32 GB confermata (anche dalla memoria GPU condivisa di Windows, 15,6 GB, circa metà della RAM).
- Test (`generation/test_generation.py`): per tutte le 59 query del corpus e 6 condizioni / k nessun esempio con
  l'id della query né del test set; bm25 LOO identico al Passo 2; static con AirTravel rifiutata; selezione
  deterministica uguale ai `query_ids` del config; config valida (36 chiamate, parametri identici tra temperature);
  run con MockClient sullo split corpus con temperature multiple e arresto quando compare ragionamento.
- **MODIFICHE DELLO STOP 1, decise dall'utente PRIMA della run** (nessuna generazione eseguita, nessun dato visto;
  la tabella e il config di sopra sono la versione iniziale, sostituita da questa):
  1. **max_tokens = 12288** nel config del pilota, ed è il valore da usare anche nel **Passo 3b per Gemma 4 12B QAT**
     (regola "contesto e max_tokens identici per modello"; annotato anche nel template
     `gemma4_12b_qat_template.yaml`). max_tokens è un **TETTO** alla lunghezza della risposta, non riserva contesto:
     la generazione si ferma prima se il modello conclude, e prompt + risposta devono comunque stare nei 32.768 token
     di contesto (pilota: prompt max 11.842 + 12.288 = 24.130; Passo 3b con k = 3: prompt max 17.256 + 12.288 =
     29.544, stime cl100k_base).
  2. **Selezione ristretta agli esercizi in scala con il test set**: si escludono i candidati il cui ground truth
     compatto (senza `interactive`, stima cl100k_base) supera il massimo del test set, **3.509 token**. Motivo: il
     pilota deve essere rappresentativo del test set; HotelBookingManagementSystem (6.525) e
     SmartHomeAutomationSystem (7.145) erano fuori scala. Del test set si legge solo la dimensione dei ground truth.
     Esclusi 14 candidati (AirTravel 4.082, DestroyBlockGame 4.749, Gym 3.714, Hospital 4.064,
     HotelBookingManagementSystem 6.525, Kinepolis 3.842, LabTracker 4.454, MilanLibrary 5.067, OnlineTutoringSystem
     4.186, SmartHomeAutomationSystem 7.145, TeamSportsScoutingSystem 4.318, TileOGame 4.859, TransportCompany
     3.596, TreatmentPlans 3.730); restano 15 / 16 / 13 candidati nelle fasce basso / medio / alto. Gli esclusi
     restano utilizzabili come ESEMPI recuperati (il filtro riguarda solo le query del pilota). Stessa regola per il
     resto (2 per fascia, piccolo e grande per dimensione, EatAtHome escluso, ordine per id; nessuna parità agli
     estremi). **Nuova selezione**:

     | fascia | ruolo | esercizio | score_norm top-1 | dimensione | GT compatto (token) | prompt (token stimati) |
     |---|---|---|---|---|---|---|
     | basso | piccolo | Louvre | 0.2356 | 20 | 1.724 | 11.279 |
     | basso | grande | Sober | 0.2522 | 56 | 3.479 | 8.495 |
     | medio | piccolo | StudentAppointment | 0.3034 | 12 | 1.308 | 6.626 |
     | medio | grande | CardGameApp | 0.2894 | 47 | 3.450 | 11.842 |
     | alto | piccolo | ApartmentBuilding | 0.4264 | 10 | 841 | 6.860 |
     | alto | grande | FilmSet | 0.4095 | 47 | 3.401 | 11.357 |

     Il rischio di troncamento segnalato sopra non vale più: il ground truth più lungo indentato è 5.187 token
     (CardGameApp), sotto il tetto di 12.288.
  La regola di decisione resta invariata.

### [2026-10-06] Pilota: primo tentativo fallito (contesto 8192), token reali di Gemma 4, controllo del contesto caricato nel runner
- **Primo tentativo fallito** (resta come traccia): alla prima chiamata del pilota LM Studio ha risposto HTTP 400
  `exceed_context_size_error` (n_prompt_tokens 14672, n_ctx 8192): il modello era caricato con contesto 8192, non
  32768 come nel config. Il runner si è fermato prima di scrivere la chiamata nel manifest; restano `config.json`
  (provenance.started_at 2026-10-06T13:36:26, il primo tentativo) e il prompt della chiamata. L'utente ha impostato
  in LM Studio Context Length 32768 (come default del modello) e ha ripreso con `--resume`: le 36 chiamate sono nel
  manifest. Il `config.json` del pilota non contiene il contesto letto dal server (il controllo sotto non esisteva
  ancora); la run non è stata toccata.
- **Token reali vs stima**: il tokenizer di Gemma 4 conta più di cl100k_base. Sui 6 prompt distinti del pilota il
  rapporto token del server / stima è 1,195-1,239 (media 1,219), quindi +20-24% (14.672 reali contro 11.842 stimati
  per CardGameApp). `experiments/context_budget.py` (sola lettura del manifest) applica il fattore massimo ai prompt
  del Passo 3b: con max_tokens 12288 e contesto 32768 **non ci sta bm25 k=3** (1 esercizio su 20, 900 token oltre) e
  random k=3 ha solo 862 token di margine. Tabelle e opzioni (max_tokens più basso, motivato dai ground truth del
  test set, oppure contesto più alto, con la VRAM da misurare) nella domanda 8 di STATUS.md. **Nessuna decisione
  presa**: decide l'utente. Nota per l'opzione "max_tokens più basso": il pilota usa 12288 e la regola "identico per
  modello" farebbe rifiutare le run del 3b con un altro valore, quindi servirebbe un'eccezione dichiarata per il
  pilota. Il fattore è misurato sui prompt; applicarlo agli output (ground truth) è un'analogia.
- **Controllo del contesto caricato** (`experiments/run_experiment.py`, `LMStudioClient.loaded_context`): secondo la
  documentazione di LM Studio ("List your models", REST API nativa) `GET /api/v1/models` riporta per ogni modello
  `loaded_instances[].config.context_length` (contesto con cui l'istanza è caricata, oltre a `parallel` e altri
  parametri di caricamento) e `max_context_length` (massimo del modello, NON quello caricato). Prima della prima
  chiamata il runner confronta il contesto dell'istanza caricata con `model_metadata.context_length`: se non coincide
  o il modello non è caricato non parte e non crea la cartella della run; se l'endpoint non risponde stampa un avviso
  ben visibile e chiede conferma ("si"; input non interattivo, EOF o altra risposta → non parte), oppure parte con
  `--accept-unverified-context`. Esito in `config.json` (`provenance.server_context`: contesti, parallel,
  max_context_length, verified) e, a ogni `--resume`, in `server_checks.jsonl` (versionato) perché `config.json`
  non si riscrive. Non verificato contro LM Studio reale (solo server finto).
- Test (`generation/test_generation.py`, server finto con `GET /api/v1/models`): contesto uguale → parte e lo
  registra; 8192 o modello non caricato → non parte; endpoint assente → avviso, conferma "si" accettata, "no" ed EOF
  rifiutati, `--accept-unverified-context` registrato; run lmstudio rifiutata senza creare la cartella con contesto
  diverso, poi eseguita e ripresa con l'esito in `server_checks.jsonl`.
- Aggiunta (2026-10-06, durante l'analisi esplorativa del pilota): un'esecuzione dei test è fallita una volta
  perché `GET /api/v1/models` verso il server finto non ha risposto (non riprodotto in 12 esecuzioni successive).
  `loaded_context()` ora riprova come `generate()`: retry con backoff su errori di rete, timeout e 5xx; nessun retry
  su 404 e sugli altri 4xx (endpoint assente → avviso e conferma, come prima).

### [2026-10-06] Pilota, FASE 3 (STOP 2): la regola della voce 75 non decide (troppi troncamenti)
- `experiments/analyze_pilot.py` ricalcola tutto dalle risposte grezze (`raw/`) con `generation/postprocess.py` e
  scrive `summary.md` nella cartella della run (versionato). Test delle funzioni di analisi su dati sintetici in
  `generation/test_generation.py` (regola: a, b, STOP; confronto delle relazioni).
- **Validità** (18 risposte per temperatura; livelli cumulativi L0 / L1 / L2 / L3 / L4; troncate):
  temperature 0: 8 / 6 / 6 / 5 / 5, troncate 6; temperature 0.3: 14 / 13 / 12 / 8 / 8, troncate 3. Solo
  ApartmentBuilding arriva a L4 in tutte e sei le risposte. I fallimenti non troncati sono errori di sintassi del
  modello (parentesi sbagliate come `]]`, `]}]`, `"var}`, un `</pre>` finale): le risposte classificate
  `incomplete_json` hanno le graffe sbilanciate per questi errori, non sono tagliate. A L3: relazioni che puntano a
  nodi inesistenti e id duplicati; a L2 una chiave `isAbstract` fuori da `data`.
- **Troncamenti**: le 9 risposte arrivate al tetto (12.288 token, 23-30 mila caratteri) hanno 9-14 nodi, come il
  ground truth, ma 45-80 relazioni contro 7-13: il modello continua a produrre relazioni fino al tetto.
- **Regola della voce 75, applicata così com'è**: V(0) = 5, V(0.3) = 8; J(0) = 0,786 (6 risposte L1), J(0.3) = 0,620
  (13 risposte L1); troncate 6 e 3, entrambe oltre la soglia di 1 su 18. **Esito: STOP, nessuna decisione**
  (controllo preliminare). La regola non è stata modificata.
- **Variabilità**: a temperature 0 le ripetizioni r1 e r2 sono identiche byte per byte in 5 esercizi su 6 e r0
  differisce sempre (ipotesi non verificata: cache del prompt di LM Studio dalla seconda chiamata in poi); a 0.3
  nessuna coppia identica.
- **Tempi**: latenza 36,7-289,6 s per generazione (mediana 81,8 s a temperature 0, 93,1 s a 0.3); 109.881 e 92.023
  token di completamento; 76 minuti in tutto.
- **ESPLORATIVO, non usato per decidere**:
  - relazioni (risposte L1, accoppiamento 1:1 per coppia di classi): temperature 0, 15 coppie in comune su 27
    relazioni del GT, 9 con lo stesso tipo, verso uguale 3/6 tra i tipi orientati (composizione / aggregazione 3/6),
    molteplicità uguali 5/15; temperature 0.3, 32 su 110, 19, 10/13 (5/6), 10/25. Scambi di tipo più frequenti:
    associazione bidirezionale → aggregazione o unidirezionale, unidirezionale → composizione. ApartmentBuilding a
    temperature 0 conferma il caso segnalato dall'utente: Jaccard delle classi 1,0 ma 3 relazioni su 9 di tipo
    diverso, 3 composizioni su 6 con il verso invertito, molteplicità uguali 5/9;
  - calibrazione dei token di prompt (36 chiamate, 6 prompt distinti): server / stima cl100k_base min 1,195,
    mediana 1,222, max 1,239. Le tabelle della domanda 8 (STATUS.md) usano già il massimo 1,239 (voce 76);
  - id: 31 risposte su 36 riusano lo schema non valido del template v4 (frammento `-4890-81h2-`), 17/18 a
    temperature 0 e 14/18 a 0.3; 1 usa la forma UUID con caratteri non esadecimali, 3 altri formati, 1 non
    classificabile. Solo descrittivo (L3 non richiede UUID, voce 64).
- **ESPLORATIVO (aggiunto dopo lo STOP 2, stessi dati, nessuna nuova generazione): i cicli sono legati al prompt o
  agli esempi?** Sezione "Risposte troncate (cicli di relazioni)" del summary.md, con una tabella per risposta.
  - Le 9 troncate stanno solo nei 4 esercizi con il prompt più lungo (token reali >= 10.150: CardGameApp 14.672,
    FilmSet 14.067, Louvre 13.870, Sober 10.150); i 2 esercizi con il prompt più corto (ApartmentBuilding 8.233,
    StudentAppointment 8.046) non troncano mai. Mediane, troncate contro non troncate: prompt 14.067 contro 10.150,
    esempi 8.663 contro 5.543 token e 36 contro 22 relazioni.
  - **Lunghezza del prompt e dimensione degli esempi non si possono separare** con questi dati: il prompt è fatto
    quasi tutto dagli esempi e ci sono solo 6 configurazioni di prompt (una per esercizio). Gli esercizi che troncano
    hanno esempi con 22-38 relazioni, quelli che non troncano 14-17. MilanLibrary (5.067 token, 23 relazioni, escluso
    come query perché fuori scala) è tra gli esempi di FilmSet e Louvre.
  - La dimensione del ground truth non spiega da sola i cicli: Louvre ha un GT piccolo (1.724 token, 7 relazioni) e
    un prompt lungo, e tronca.
  - Nelle troncate le relazioni ripetono le stesse coppie (sorgente, destinazione): coppie distinte / relazioni
    scritte in mediana 0,24 (1,00 nelle non troncate). È un ciclo sulle relazioni, non un diagramma più grande.
  - Classi copiate dagli esempi e assenti dal GT: solo "Vehicle" in Sober (da TruckLogistics), sia in 2 troncate sia
    in 3 non troncate: nessun legame evidente con i cicli.
  - A parità di prompt la troncatura dipende anche da temperatura e ripetizione (es. FilmSet 3/3 a temperature 0,
    0/3 a 0.3; Sober 0/3 a 0, 2/3 a 0.3).
  - Limiti: 6 configurazioni, nessun test statistico. Per separare i due fattori servirebbe un esperimento che vari
    la lunghezza del prompt a parità di esempi, o gli esempi a parità di lunghezza.
- In attesa di decisione dell'utente sul seguito: nessuna modifica a regola, config o prompt.

### [2026-10-07] Secondo pilota (solo corpus): PlantUML contro JSON vincolato, Qwen2.5-Coder 14B; regola di decisione PRIMA della run (STOP 1)
- **Decisione di fondo (dell'utente)**: Apollon v4 è il FORMATO DI CONSEGNA, non parte del compito; è legittimo che il
  codice produca id, coordinate e riferimenti in modo deterministico. Due strade a confronto: **strada 1** PlantUML
  (esempi e risposta in PlantUML, conversione in Apollon con il convertitore della tesi) e **strada 2** Apollon JSON
  con generazione vincolata allo schema. Esperimento PRELIMINARE, solo corpus (stessi 6 esercizi del primo pilota,
  selezione leave-one-out), mai il test set.
- **Modelli**: Gemma 4 12B QAT e **Qwen2.5-Coder 14B Instruct** (GGUF Q4_K_M, fonte ufficiale). Perché il 14B: taglia
  simile a Gemma 12B, quindi il confronto generalista / coding non è falsato dalla dimensione; sta nei 12 GB di VRAM
  solo con la KV cache quantizzata Q4 (K e V) e Flash Attention, con contesto 32768 (massimo del GGUF: "Currently,
  only vLLM supports YARN", scheda del modello). I dati di VRAM dello smoke test di Qwen NON sono ancora disponibili
  (nessuno smoke test di Qwen in `docs/smoke_tests/`): da registrare dopo lo smoke test. Parametri raccomandati da
  Qwen (generation_config.json): temperature 0.7, top_p 0.8, top_k 20, repetition_penalty 1.05; nel pilota NON si
  usano: temperature 0.3, top_p 0.95, top_k 64 per entrambi i modelli.
- **Metadati obbligatori nuovi** per tutti i template e i config: `kv_cache_quant` e `flash_attention` (booleano).
  Per Gemma i valori del primo pilota non sono noti: chiesti all'utente (nei config restano TODO e il runner rifiuta
  P-G / J-G finché mancano). Il config storico del primo pilota non è stato modificato (run conclusa). All'avvio il
  runner confronta anche Flash Attention se `GET /api/v1/models` la riporta nella config dell'istanza caricata; la
  quantizzazione della KV cache non è esposta dall'API e resta un metadato dichiarato.
- **Strada 1, template** `generation/templates/v4_plantuml_instructions.txt`: dal template v4 cambiano solo le parti sul
  formato di uscita (ruolo di esperto PlantUML; struttura @startuml / @enduml; dichiarazioni di classe, abstract,
  interface, enum con "+ nome : tipo" e "+ metodo(parametri) : Tipo"; riga di relazione con molteplicità e ruolo tra
  virgolette e nome di associazione dopo i due punti; operatori PlantUML al posto dei tipi Apollon con la stessa
  semantica; vietati skinparam, note, package, title); tolte le parti solo Apollon (id, coordinate, dimensioni,
  handle, punti, campi degli edge). Restano identiche le righe sulla scelta del tipo di relazione (riformulate con gli
  operatori), sulle molteplicità e le linee guida di modellazione. Aggiunte due righe di sintassi richieste dal parser:
  nomi di classe di una parola, ogni classe usata in una relazione va dichiarata.
- **Strada 1, esempi — PROPOSTA (da approvare)**: il diagram_plantuml del corpus (versione corretta) ha una sintassi
  disomogenea (attributi "String Title", visibilità "-", 107 ruoli + 1 doppio scritti dopo i due punti come i 74 nomi
  di associazione, distinti solo da label_classification.json): non è coerente con le istruzioni né con una regola
  automatica. Proposta: esempi in **PlantUML CANONICO** (`generation/plantuml_format.py`), ricavato in modo
  deterministico dal JSON Apollon del Passo 1 (= diagram_plantuml corretto passato dalla pipeline con la
  classificazione), nella sola sintassi del template.
- **Strada 1, regola automatica delle etichette `auto_v1` — PROPOSTA (da approvare)**: (a) testo dopo i due punti =
  nome di associazione; (b) testo tra virgolette a un estremo = "molteplicità ruolo" se la prima parola ha forma di
  molteplicità (solo cifre, `*`, `.`, `,`, `n`/`N`), altrimenti è tutto ruolo senza molteplicità; (c) vincoli {…} sulle
  generalizzazioni come nel Passo 1. Il runner rifiuta P-G / P-Q finché la regola non è approvata
  (`APPROVED_LABEL_RULES` vuoto).
- **Strada 1, post-processing** `generation/plantuml_postprocess.py` (corpus/ in sola lettura): livelli P0 blocco
  trovato, P1b parsing tollerante riuscito (righe scartate contate e registrate), P1 senza righe scartate, poi
  conversione con le funzioni del convertitore e gli STESSI L2-L4 della strada 2 (`postprocess.check_l2_l4`).
- **Controllo di sanità** (`generation/plantuml_sanity_check.py`, 79 diagrammi = 59 corpus + 20 test set, come
  risposte generate con la regola `auto_v1`): (A) diagram_plantuml così com'è: 79/79 a L4, 0 righe scartate, 28
  diagrammi diversi dal Passo 1, tutte le differenze sono **106 ruoli rimasti nome di associazione** (testo dopo i
  due punti); (B) PlantUML canonico: 79/79 a L4 e **contenuto identico al Passo 1 in 79 casi su 79**. Durante la
  verifica la definizione di "forma di molteplicità" è stata allargata per la grafia "0..1*" di HomeForTheElderly.
- **Strada 2, schema** `generation/schemas/apollon_v4_generation.schema.json` (da `generation/make_generation_schema.py`;
  lo schema ufficiale non è modificato): $ref espansi in linea (llama.cpp: "Nested $refs are broken"; lo schema
  ufficiale ha OrthogonalEdgeData → IPoint), stesso insieme di documenti accettati; **maxItems = 39** sugli edges = 3 ×
  13, massimo di relazioni nei 44 ground truth selezionabili (HelpingHands). Tutti i 79 ground truth (anche il test
  set, massimo 27) sono validi con lo schema di generazione.
- **Il vincolo è applicato durante la generazione?** Documentazione di LM Studio (Structured Output): "For GGUF
  models: utilize llama.cpp's grammar-based sampling APIs" (MLX: Outlines); "Not all models are capable of structured
  output, particularly LLMs below 7B parameters". La conversione JSON Schema → grammatica di llama.cpp supporta
  min/maxItems, $ref locali, additionalProperties, pattern (^…$), enum; NON supporta i $ref annidati (risolto
  espandendoli). Quindi struttura di primo livello, tipi di nodo / edge, punti e tetto sugli edges sono imposti dal
  campionamento. **Limite**: lo schema ufficiale lascia libero il contenuto di `data` dei nodi (attributi, metodi,
  nome) e i campi di `data` degli edge diversi da `points`: lì il vincolo non agisce (proposta da valutare: uno
  schema di generazione più stretto su `data`; non applicata).
- **Calibrazione dei token**: Gemma, prompt JSON: 1,195-1,239 (voce 76). Per Qwen e per i prompt PlantUML non ci sono
  ancora token reali: `experiments/calibrate_tokens.py` invia i 12 prompt del pilota (6 esercizi × 2 formati) con
  max_tokens = 1 e salva l'esito in `docs/smoke_tests/`. Margine offline (stime cl100k_base): prompt massimo 11.842
  (JSON) e 3.115 (PlantUML); con max_tokens 12288 e contesto 32768 si sta dentro finché il fattore resta sotto 1,729
  (JSON) e 6,57 (PlantUML).
- **Config** `experiments/configs/pilot2_formats.yaml`: bm25, k = 2, temperature 0.3 (valore di lavoro), top_p 0.95,
  top_k 64, max_tokens 12288, contesto 32768, 2 ripetizioni; configurazioni P-G, P-Q, J-G, J-Q (48 generazioni); il
  runner esegue una configurazione per volta (`--configuration`) e verifica all'avvio contesto e Flash Attention del
  modello caricato. Stime cl100k_base: prompt PlantUML 2.108 / 2.958 / 3.115 (min / mediana / max) e ground truth
  PlantUML canonico 81-414 token; prompt JSON 6.626 / 9.887 / 11.842 e ground truth 841-3.479.
- **REGOLA DI DECISIONE (PROPOSTA allo STOP 1; diventa definitiva con l'approvazione, PRIMA della run; non si
  modifica dopo aver visto i dati)**. Per ogni configurazione C (12 risposte):
  - **S(C)** = risposte che arrivano a un Apollon valido fino a L3, su 12. Strada 1: P0 + P1b (parsing riuscito, anche
    con righe scartate) + conversione + L2 + L3. Strada 2: L0-L3.
  - **Controllo preliminare**: una configurazione che non si può eseguire (es. il server rifiuta response_format) o
    fermata per ragionamento è esclusa e segnalata; se ne restano meno di 2, ci si ferma senza decidere.
  - **Soglia minima**: se il massimo di S è sotto 6/12, nessuna configurazione passa al Passo 3b; si segnala e ci si
    ferma.
  - **Scelta**: la configurazione con S più alto; strada e modello si scelgono INSIEME (la configurazione), non
    separatamente.
  - **Pareggio** = configurazioni entro 1 risposta su 12 dal massimo di S. Tra queste, nell'ordine: (1) meno
    troncamenti; (2) Jaccard medio dei nomi di classe con il GT più alto (risposte valide fino a L3); (3) accordo
    sulle relazioni più alto (relazioni del GT con stessa coppia di classi e stesso tipo, sul totale delle relazioni
    del GT delle risposte valide); (4) latenza mediana più bassa. Se ancora pari: strada 1 (PlantUML: prompt e output
    circa 10 volte più corti) e, a parità di strada, Gemma (già verificato nel primo pilota).
  - Riportate ma fuori dalla regola: P1 (senza righe scartate), L4, diagnostici, verso e molteplicità delle relazioni,
    token. Riferimento esterno solo descrittivo: primo pilota, Gemma in Apollon libero a temperature 0.3, V = 8/18
    (0,44) fino a L3.
  - Nota di lettura: nella strada 1 L2 e L3 sono quasi garantiti dal convertitore una volta superato il parsing, nella
    strada 2 lo schema garantisce la struttura ma non i riferimenti (L3): S misura cose diverse nelle due strade, ed è
    proprio la grandezza che interessa (Apollon valido consegnabile).
- **Durata stimata** (non misurata): P-G e P-Q circa 3-6 minuti ciascuna (prompt ~3k token, risposte ~200-500
  token); J-G circa 20-30 minuti (mediana di 93 s per generazione a 0.3 nel primo pilota; il vincolo può rallentare
  il campionamento); J-Q circa 15-30 minuti (14B, KV cache Q4). Totale circa 45-70 minuti più i cambi di modello.
- **Correzione rifatta** (la versione di ieri sera non era più nel codice): con l'endpoint dei modelli assente,
  `check_server_context` controllava che l'input fosse un terminale PRIMA di usare la funzione di conferma, anche
  quando i test ne iniettavano una: con lo stdin rediretto i test fallivano. Ora il controllo vale solo per `input`.
- Nota operativa: all'inizio della sessione del 2026-10-07 parte del lavoro su questo pilota non era più su disco
  (file nuovi assenti, file modificati tornati alla versione precedente, script dello scratchpad spariti); è stato
  rifatto con lo stesso contenuto e gli stessi controlli (stessi esiti, stesso sha256 dello schema di generazione).

### [2026-10-07] Secondo pilota — STOP 1 approvato: esempi PlantUML canonici, regola auto_v1, regola di decisione con classifica completa, schema di generazione
- Approvazioni dell'utente sulle proposte della voce 78, date PRIMA di qualsiasi generazione del secondo pilota (nessun
  dato visto):
  1. **Esempi in PlantUML CANONICO** (`generation/plantuml_format.py`), ricavati in modo deterministico dal JSON
     Apollon del Passo 1: approvati. Motivo: controllo di sanità B, contenuto identico al Passo 1 in 79 casi su 79.
  2. **Regola automatica delle etichette `auto_v1`**: approvata così com'è. `experiments/run_experiment.py`:
     `APPROVED_LABEL_RULES = ("auto_v1",)`; `experiments/configs/pilot2_formats.yaml`: `plantuml_label_rule: auto_v1`.
     Qualunque altra regola resta rifiutata dal runner (test). Docstring di `generation/plantuml_postprocess.py`:
     "PROPOSTA" → "APPROVATA".
  3. **Regola di decisione della voce 78**: approvata e DEFINITIVA, con un'aggiunta: l'analisi riporta sempre la
     **classifica completa delle quattro configurazioni** (S, troncamenti, criteri di spareggio), non solo la
     vincitrice. Implementata in `experiments/analyze_pilot2.py` (voce 82).
  4. **Schema di generazione** (`generation/schemas/apollon_v4_generation.schema.json`, `maxItems` 39 sugli edges,
     `$ref` espansi): approvato. **Limite annotato**: il contenuto di `data` dei nodi (nome, attributi, metodi) e i
     campi di `data` degli edge diversi da `points` restano liberi, quindi lì il vincolo non agisce; nessuno schema più
     stretto su `data`.

### [2026-10-07] Smoke test di Qwen2.5-Coder 14B: risposta attesa, nessun ragionamento, seed come Gemma
- Smoke test eseguito dall'utente con `--save`: `docs/smoke_tests/2026-10-07_qwen-qwen2.5-coder-14b_smoke1.txt` e
  `.json` (script 2026-10-06.3). Id del modello in LM Studio: **`qwen/qwen2.5-coder-14b`**.
- Esiti (dal .json): risposta attesa `{"ok": true}` **SI** (6 token di completamento, latenza 2,68 s); **nessun
  ragionamento** (né campo separato né marcatori); a temperature 0.8 il **seed NON è rispettato** (seed 1234 due volte
  → due risposte diverse); a temperature 0 le tre risposte (due con seed 1234, una con 98765) sono **identiche**, quindi
  il seed non ha effetto ("non determinabile").
- **Stesso comportamento di Gemma 4 12B QAT** (voci 72 e 74): la regola sulla riproducibilità (riproducibilità
  garantita a livello di ANALISI, con le risposte grezze versionate, non di generazione; seed inviato e registrato
  comunque) vale per entrambi i modelli. Come per Gemma, un prompt breve non dimostra il determinismo a temperature 0
  sui prompt lunghi degli esperimenti.
- Config: `model_id` e `client.model` = `qwen/qwen2.5-coder-14b` in `experiments/configs/qwen25coder14b_template.yaml`
  e nel modello Q di `experiments/configs/pilot2_formats.yaml`. J-Q non ha più TODO (il runner e
  `calibrate_tokens.py` accettano il client); P-Q è sbloccato anche dalla regola `auto_v1` (voce 79).
- Ancora da registrare: la **VRAM usata** da Qwen con contesto 32768 (`hardware.vram_used`, fornita dall'utente;
  campo descrittivo, non obbligatorio per il runner).

### [2026-10-07] Repository spostato fuori da OneDrive; remote superflui rimossi
- **Spostamento**: da `C:\Users\peppe\OneDrive\Desktop\uml-rag-thesis` a `C:\Progetti\uml-rag-thesis`, fatto
  dall'utente. **Motivo**: si sospetta che la sincronizzazione di OneDrive abbia causato le due perdite di lavoro
  registrate di recente:
  - **5 ottobre, STOP 2 del Passo 3a**: mancavano i nuovi default di `PromptSpec` e la voce 64 di questo file, poi
    rifatti;
  - **7 ottobre, FASE 1 del secondo pilota**: mancavano i moduli PlantUML, il template e lo script dello schema, e
    alcuni file erano tornati alla versione del giorno prima (nota operativa della voce 78; rifatti con gli stessi
    controlli e lo stesso sha256 dello schema).
  La chat di lavoro precedente è andata persa con lo spostamento; il contesto è stato ricostruito da CLAUDE.md,
  STATUS.md e da questo file.
- **Verifiche nel nuovo percorso** (2026-10-07): `git status` pulito a parte i due file dello smoke test di Qwen;
  dopo `git fetch` `main` = `origin/main` = `ff0449e` (anche `git ls-remote`); sha256 invariati rispetto ai valori
  registrati per `retrieval/stopwords_en.txt` (`5be3f507…`), `generation/tokenizer/cl100k_base.tiktoken`
  (`223921b7…`), `retrieval/config_bm25.yaml` (`d6dfa722…`) e lo schema di generazione (`e35a19c7…`); tag
  `testset-v1` presente; `generation/test_generation.py` passa nel nuovo percorso.
- **Remote**: rimossi su richiesta dell'utente `git@github.com-GiuseppeBuonasera/uml-rag-thesis.git` (remote il cui
  nome era un URL SSH) e `rag-uml-thesis-start`, entrambi verso lo stesso repository GitHub. Resta solo `origin`
  (`https://github.com/GiuseppeBuonasera/uml-rag-thesis.git`, fetch e push).

### [2026-10-07] Secondo pilota: script di analisi (analyze_pilot2.py) scritto PRIMA delle run
- `experiments/analyze_pilot2.py`, scritto e testato prima di qualsiasi generazione del secondo pilota. **Da qui in
  poi la regola nel codice (funzioni `decide` / `pick`, `TIEBREAKS`, costanti `MIN_S` = 6, `TIE_WINDOW` = 1,
  `MIN_INCLUDED` = 2) non si modifica senza una nuova voce in questo file.**
- Legge in sola lettura `data/results/generation/pilot2_formats__<C>/` (C = P-G, P-Q, J-G, J-Q) e ricalcola tutto dalle
  risposte grezze (`raw/`) con la stessa validazione del runner (strada 1 `plantuml_postprocess`, strada 2
  `postprocess`); segnala se il livello ricalcolato differisce da quello del manifest e se le run non sono omogenee
  (esercizi, k, ripetizioni, parametri di generazione). Scrive solo
  `data/results/generation/pilot2_formats_analysis/summary.md` (versionato dalla regola di `.gitignore` sui
  `summary.md`).
- **Regola della voce 78, come implementata**:
  - S = risposte con livello >= 3 (strada 1: P0 + P1b + conversione + L2 + L3; strada 2: L0-L3);
  - troncamento = `finish_reason = length` (in entrambe le strade);
  - J = media del Jaccard dei nomi di classe con il GT sulle risposte valide fino a L3 (stesse funzioni del primo
    pilota, `analyze_pilot.class_names` e `corpus_loader.jaccard`); R = somma delle relazioni con stessa coppia e
    stesso tipo / somma delle relazioni del GT, sulle risposte valide (accoppiamento 1:1 di
    `analyze_pilot.compare_relations`); latenza mediana su tutte le 12 risposte;
  - pareggio = S >= max(S) − 1; spareggi applicati in sequenza, ognuno tiene solo le migliori: meno troncamenti,
    J più alto, R più alto, latenza mediana più bassa, strada 1, Gemma. Un valore non definito (J o R senza risposte
    valide) perde. Uguaglianza tra valori reali con tolleranza 1e-9;
  - soglia: miglior S < 6/12 → nessuna configurazione passa al Passo 3b; meno di 2 configurazioni eseguibili → STOP.
- **Lettura operativa di "configurazione che non si può eseguire"** (la voce 78 non la dettaglia): run assente
  (nessun `config.json`) oppure **incompleta** (meno risposte del previsto nel manifest: è il caso del server che
  rifiuta `response_format` alla prima chiamata, ma anche di una run interrotta, che va ripresa con `--resume` prima
  dell'analisi). Esclusa anche la run fermata per ragionamento. Le metriche delle escluse, se ci sono risposte, si
  riportano comunque.
- **Classifica completa** (aggiunta della voce 79): posizione k = vincitrice della stessa regola (pareggio entro 1 e
  spareggi) applicata alle configurazioni non ancora classificate, con il criterio che l'ha decisa; le escluse in
  fondo con il motivo. La soglia minima vale solo per la scelta: la classifica si riporta anche quando ci si ferma.
  Conseguenza da tenere presente: per la finestra di pareggio una configurazione con S più basso di 1 può precedere
  una con S più alto (es. meno troncamenti).
- Metriche secondarie (fuori dalla regola): livelli cumulativi P0 / L0, P1b / L1, P1 (solo strada 1), L2, L3, L4,
  troncate e righe scartate; esiti di fallimento; livello per esercizio e ripetizione; relazioni (stessa coppia,
  stesso tipo, verso dei tipi orientati e di composizione / aggregazione, molteplicità, scambi di tipo); latenza,
  token di completamento e di prompt, rapporto token reali / stima; diagnostici di formato e di layout. Nella strada 1
  i diagnostici sul JSON (es. `interactive_present`, presente in tutte le risposte convertite) riguardano l'Apollon
  prodotto dal convertitore, non la risposta del modello: annotato nel report.
- Test (`check_analyze_pilot2` in `generation/test_generation.py`, dati finti): nessun pareggio; pareggio vinto da S −
  1 per meno troncamenti; spareggi decisi da J, R, latenza, strada 1, Gemma; S − 2 fuori dal pareggio; J non definito
  che perde; miglior S 5/12 (STOP, classifica riportata) e 6/12 (passa); due configurazioni mancanti (si decide) e
  tre (STOP); end-to-end su run finte con risposte = ground truth (PlantUML canonico / JSON compatto): una assente, una
  fermata per ragionamento, una con una risposta troncata (vince P-G per meno troncamenti con 12 contro 11), poi una
  incompleta (11/12, STOP).

### [2026-10-07] Secondo pilota: configurazione di RIFERIMENTO J0-Q (Qwen, Apollon JSON libero), registrata PRIMA della run
- **Decisione dell'utente**, registrata prima di qualsiasi generazione del secondo pilota (nessun dato visto): si
  aggiunge la configurazione **J0-Q** = Qwen2.5-Coder 14B, **Apollon JSON LIBERO** (senza `response_format`), stessi 6
  esercizi, bm25 k = 2, temperature 0.3, top_p 0.95, top_k 64, max_tokens 12288, contesto 32768, 2 ripetizioni (12
  generazioni). È l'equivalente per Qwen di Gemma in JSON libero a temperature 0.3 del primo pilota.
- **Solo descrittiva**: NON entra nella regola della voce 78, che resta invariata (né in S, né nel pareggio, né nella
  classifica; `CONFIGURATIONS` di `analyze_pilot2.py` resta P-G, P-Q, J-G, J-Q).
- **Motivo**: completa il confronto 2x2 della strada JSON (Gemma / Qwen x libero / vincolato), così si separa l'effetto
  del modello da quello del vincolo. Le celle: Gemma libero = primo pilota a 0.3; Gemma vincolato = J-G; Qwen libero
  = J0-Q; Qwen vincolato = J-Q.
- **Stesso prompt** (verificato prima della run): per i 6 esercizi i messaggi costruiti oggi per J0-Q, per J-Q e per
  il primo pilota sono identici (sha256 dei messaggi uguale a `prompt_sha256` del manifest del primo pilota; test in
  `check_pilot2`). J0-Q e J-Q differiscono SOLO per il vincolo.
- **Differenze dichiarate rispetto a Gemma libero** (riferimento del primo pilota): altra run (2026-10-06), 3
  ripetizioni per esercizio (18 risposte a 0.3, seed 42-44) invece di 2 (12 risposte, seed 42-43); le proporzioni di S
  sono su totali diversi. Nessun test statistico.
- **Config** (`experiments/configs/pilot2_formats.yaml`): `J0-Q: {model: Q, output_format: apollon}` (senza
  `structured_output` né `response_schema`); run_id `pilot2_formats__J0-Q`. **Nessuna modifica al codice di
  generazione**: `resolve_configuration` già produce `structured_output: false` e il client invia `response_format`
  solo con `structured_output` attivo (test: corpo della richiesta di J0-Q senza `response_format`). Stesso modello,
  contesto e max_tokens di J-Q: il controllo "contesto e max_tokens identici per modello" del runner è soddisfatto.
- **Analisi** (`experiments/analyze_pilot2.py`; `decide`, `pick`, `TIEBREAKS` e le costanti della regola NON sono
  cambiati): nuova sezione "Riferimenti", dopo le metriche secondarie e fuori dalla classifica, con J0-Q e Gemma libero
  del primo pilota (`pilot_temperature_gemma4-12b-qat`, solo le risposte a temperature 0.3, validate con la stessa
  funzione della strada 2) e le stesse metriche (S, L0-L4, troncate, J, R, latenza mediana, esiti di fallimento,
  relazioni); controllo del prompt (sha256 dei messaggi di J-G, J-Q e J0-Q contro il primo pilota, esercizio per
  esercizio, con avviso "PROMPT DIVERSI"); **tabella 2x2 di S** (righe Gemma / Qwen, colonne JSON libero / vincolato,
  S/n con la proporzione). Sui dati reali il riferimento di Gemma dà S = 8/18, come V(0.3) nel summary del primo
  pilota, nessun livello ricalcolato diverso dal manifest.
- Test (`check_pilot2`, `check_analyze_pilot2`): 5 configurazioni (48 + 12 generazioni), J0-Q senza vincolo e con gli
  stessi modello e metadati di J-Q; prompt identici tra primo pilota, J0-Q e J-Q; con riferimenti assenti e presenti la
  decisione e la classifica non cambiano e J0-Q non compare tra le righe della classifica; primo pilota finto filtrato a
  temperature 0.3 (18 risposte su 36); prompt diverso segnalato; celle della 2x2 (anche vuote).

### [2026-10-07] Qwen2.5-Coder 14B scartato: non regge 32768 di contesto sulla RTX 4070 12 GB
- **Esito** (misurato dall'utente in LM Studio, durante la calibrazione dei token): con il 14B (Q4_K_M, KV cache Q4,
  Flash Attention) caricato a contesto 32768 la **lettura del prompt crolla a circa 90-110 token/s** (es. 8.111 token
  in 87 s) e cala ancora man mano che il prompt cresce. Interpretazione dell'utente: la memoria del contesto non sta
  più in VRAM. A 8192 il modello starebbe in VRAM, ma i prompt reali superano 8192 token (**9.861 token** misurati in
  calibrazione), e la regola "contesto identico per modello" con le finestre della domanda 8 richiede 32768.
- **Decisione**: il 14B non si usa. Il template `experiments/configs/qwen25coder14b_template.yaml` resta nel
  repository come traccia, con l'intestazione "NON USATO: non entra in VRAM a 32768". Restano validi come traccia anche
  lo smoke test del 14B (voce 80, `docs/smoke_tests/2026-10-07_qwen-qwen2.5-coder-14b_smoke1.*`) e la configurazione
  di riferimento J0-Q (voce 83), che ora usa il 7B.
- **File lasciati dal 14B**: nessuno. Verificato il 2026-10-07: in `docs/smoke_tests/` non c'è nessun file
  `..._calibrationN.json` (la calibrazione non è arrivata al salvataggio, che avviene alla fine), e in
  `data/results/generation/` non c'è nessuna cartella `pilot2_formats__*`. I numeri sopra (8.111 token in 87 s, 9.861
  token) sono quindi riferiti dall'utente.
- **Prova**: `docs/smoke_tests/2026-10-07_qwen-qwen2.5-coder-14b_lmstudio-log_manuale.txt`, PROVA MANUALE con
  l'estratto del registro di LM Studio (calibrazione J-Q interrotta, contesto 32768, Flash Attention attiva, KV cache
  Q4), versionata insieme agli altri smoke test. L'estratto lo incolla l'utente al posto del segnaposto: finché il
  segnaposto è presente, il file non è la prova dell'esito e i numeri restano solo riferiti.
- **Protezione nell'analisi** (`experiments/analyze_pilot2.py`, `load_configuration` con `expected_model_id` ed
  `expected_model_ids()`): `main` legge il `model_id` di ogni configurazione dal config attuale
  (`pilot2_formats.yaml`). Una run il cui `config.json` riporta un altro `model_id`, ad esempio una run del 14B
  rimasta su disco, NON si usa: la configurazione risulta non eseguita, con il motivo "traccia NON usata". La regola
  della voce 78 (`decide`, `pick`, `TIEBREAKS`, costanti) non è cambiata. Nota: run del 14B e del 7B avrebbero lo
  stesso `run_id` (`pilot2_formats__J-Q`, ...), e il runner non sovrascrive una cartella esistente; se in futuro
  comparisse una cartella del 14B, andrebbe spostata a mano (es. in `pilot2_formats__J-Q__14b/`) prima della run del 7B.

### [2026-10-07] Qwen2.5-Coder 7B Instruct Q6_K come modello da coding; confronto tra modelli di taglia diversa
- **Nuovo modello da coding** (decisione dell'utente): **Qwen2.5-Coder 7B Instruct**, file **Q6_K** da
  lmstudio-community (huggingface.co/lmstudio-community/Qwen2.5-Coder-7B-Instruct-GGUF), modello originale non
  modificato.
- **Template** `experiments/configs/qwen25coder7b_template.yaml`: quantizzazione Q6_K, `source`
  `lmstudio-community/Qwen2.5-Coder-7B-Instruct-GGUF` (campo nuovo, descrittivo, non obbligatorio per il runner),
  contesto 32768, max_tokens 12288, `flash_attention: true`, **`kv_cache_quant: F16`** (nessuna quantizzazione della
  cache), `enable_thinking: false` (il modello non ha ragionamento), hardware come gli altri. **`client.model`,
  `model_id` e `vram_used` restano TODO fino allo smoke test** dell'utente; con i TODO il runner rifiuta P-Q, J-Q e
  J0-Q e `calibrate_tokens.py` rifiuta J-Q.
- **Secondo pilota** (`experiments/configs/pilot2_formats.yaml`): il modello Q diventa il 7B, con gli stessi metadati del
  template (verificato da un test). Le configurazioni P-Q, J-Q e J0-Q restano con gli stessi parametri (bm25 k = 2,
  temperature 0.3, top_p 0.95, top_k 64, max_tokens 12288, contesto 32768, 2 ripetizioni); regola della voce 78
  invariata.
- **Il confronto generalista / coding è ora tra modelli di TAGLIA DIVERSA** (Gemma 4 12B QAT contro Qwen2.5-Coder 7B),
  mentre la scelta del 14B (voce 78) serviva proprio a confrontare taglie simili. Va dichiarato nell'analisi e in
  tesi: le differenze tra i due modelli non si possono attribuire alla sola specializzazione sul codice. Anche le
  quantizzazioni sono diverse (QAT q4_0 contro Q6_K) e così la KV cache (da confermare per Gemma, TODO). In
  `analyze_pilot2.py` la nota `SIZE_NOTE` compare in testa al report e sotto la tabella 2x2; il nome del modello Q nel
  report è "Qwen2.5-Coder 7B".
- **Da rifare per il 7B**: smoke test (id, risposta attesa, ragionamento, comportamento del seed, VRAM con contesto
  32768) e calibrazione dei token. Fino allo smoke test la regola sulla riproducibilità (voci 72, 74 e 80) si dà per
  valida anche per il 7B, ma non è verificata.
- Test (`check_pilot2`, `check_analyze_pilot2`): metadati del modello Q uguali al template del 7B (Q6_K, KV F16,
  Flash Attention, contesto 32768, max_tokens 12288); P-Q, J-Q e J0-Q rifiutati finché l'id è TODO; template del 14B
  segnato come non usato; run di un altro modello scartata dall'analisi; nota sulle taglie nel report.

### [2026-10-07] Smoke test di Qwen2.5-Coder 7B Instruct: risposta attesa, nessun ragionamento, seed come Gemma e il 14B
- Smoke test eseguito dall'utente con `--save`: `docs/smoke_tests/2026-10-07_qwen2.5-coder-7b-instruct_smoke1.txt` e
  `.json` (script 2026-10-06.3). Id del modello in LM Studio: **`qwen2.5-coder-7b-instruct`**, uguale a quello riportato
  dal server nelle risposte.
- **L'id esposto da LM Studio non contiene l'editore** (a differenza di `google/gemma-4-12b-qat` e
  `qwen/qwen2.5-coder-14b`): da solo non dice quale GGUF è caricato. La fonte è nel campo `source` dei metadati
  (`lmstudio-community/Qwen2.5-Coder-7B-Instruct-GGUF`, file Q6_K), **confermata dall'utente in My Models**.
- Esiti (dal .json): risposta attesa `{"ok": true}` **SI** (6 token di completamento, latenza 2,52 s); **nessun
  ragionamento** (né campo separato né marcatori); a temperature 0.8 il **seed NON è rispettato** (seed 1234 due volte
  → due risposte con lo stesso inizio ma diverse, 35 e 34 token); a temperature 0 le tre risposte (due con seed 1234,
  una con 98765) sono **identiche**, quindi il seed non ha effetto ("non determinabile").
- **Stesso comportamento di Gemma 4 12B QAT e del 14B** (voci 72, 74 e 80): la regola sulla riproducibilità
  (riproducibilità garantita a livello di ANALISI, con le risposte grezze versionate; seed inviato e registrato
  comunque) vale ora verificata anche per il 7B. Come per gli altri, un prompt breve non dimostra il determinismo a
  temperature 0 sui prompt lunghi degli esperimenti.
- Config: `model_id` e `client.model` = `qwen2.5-coder-7b-instruct` in
  `experiments/configs/qwen25coder7b_template.yaml` e nel modello Q di `experiments/configs/pilot2_formats.yaml`, con
  l'annotazione sull'editore. P-Q, J-Q e J0-Q non hanno più TODO: il runner e `calibrate_tokens.py` accettano il
  client (test). Resta da registrare `hardware.vram_used` (dopo la calibrazione; campo descrittivo, non obbligatorio).

### [2026-10-08] Gemma 4 12B QAT: impostazioni di caricamento (Flash Attention, KV cache) del primo pilota
- **Dato dell'utente**: Gemma 4 12B QAT è caricato in LM Studio con **Flash Attention = true**, **K cache = F16**, **V
  cache = F16** (KV cache non quantizzata). Sono le stesse impostazioni del primo pilota e non sono mai cambiate.
- **Config**: `kv_cache_quant: F16` (K e V F16, stessa convenzione del 7B) e `flash_attention: true` in
  `experiments/configs/gemma4_12b_qat_template.yaml` e nel modello G di `experiments/configs/pilot2_formats.yaml`.
  P-G e J-G non hanno più TODO: il runner e `calibrate_tokens.py` accettano il client (test). All'avvio il runner
  confronta Flash Attention con quella dell'istanza caricata, se LM Studio la riporta; la quantizzazione della KV
  cache non è esposta dall'API e resta un metadato dichiarato (voce 78).
- **Primo pilota**: il suo `config.json` (run conclusa) e `experiments/configs/pilot_temperature.yaml` non contengono
  questi campi, perché sono precedenti ai metadati di caricamento (voce 78); non si modificano. Per il primo pilota
  il valore resta quello dichiarato qui, non registrato nella run.
- **Confronto tra i modelli del secondo pilota**: KV cache F16 per entrambi (Gemma e Qwen2.5-Coder 7B), Flash Attention
  attiva per entrambi; restano diverse taglia e quantizzazione dei pesi (QAT q4_0 contro Q6_K, voce 85).
- Il test sui valori fittizi del client J-G (`kv_cache_quant` F16, `flash_attention` false, solo per costruire la
  richiesta) è sostituito dal config reale.

### [2026-10-08] Secondo pilota, STOP 2: la regola della voce 78 sceglie P-Q (Qwen2.5-Coder 7B, PlantUML)
- `python experiments/analyze_pilot2.py` sulle cinque run committate (`48f3763` Qwen 7B: J-Q, J0-Q, P-Q; `58896d0`
  Gemma: J-G, P-G), tutte complete (12/12), nessun ragionamento, livelli ricalcolati uguali al manifest, run omogenee.
  Report: `data/results/generation/pilot2_formats_analysis/summary.md` (analisi sul commit `58896d0`).
- **Regola della voce 78, applicata così com'è**: soglia superata (miglior S 12/12 >= 6); **scelta P-Q** con S = 12/12,
  senza pareggio (la seconda, P-G, ha 10/12, fuori dalla finestra di 1).
- **Classifica completa**:

  | posizione | configurazione | S | troncate | J | R | latenza mediana (s) | decisa da |
  |---|---|---|---|---|---|---|---|
  | 1 | P-Q (PlantUML, Qwen2.5-Coder 7B) | 12/12 | 0 | 0,577 | 0,183 | 6,0 | S più alto |
  | 2 | P-G (PlantUML, Gemma 4 12B QAT) | 10/12 | 0 | 0,606 | 0,321 | 9,1 | Jaccard (pari con J-G su S e troncate) |
  | 3 | J-G (JSON vincolato, Gemma) | 9/12 | 0 | 0,582 | 0,123 | 99,1 | S più alto |
  | 4 | J-Q (JSON vincolato, Qwen 7B) | 0/12 | 0 | — | — | 65,2 | S più alto |

- **Riferimenti e 2x2 (solo descrittivi)**: S in JSON libero / vincolato: Gemma 8/18 (0,44, primo pilota) / 9/12
  (0,75); Qwen 7B 1/12 (0,08, J0-Q) / 0/12. Prompt JSON identici al primo pilota in 12/12 risposte per J-G, J-Q e J0-Q.
  Taglie diverse (voce 85): la differenza tra i modelli non è attribuibile alla sola specializzazione sul codice.
- **Metriche secondarie**: nessuna risposta troncata nelle quattro configurazioni (contro 3/18 di Gemma in JSON libero
  nel primo pilota). Strada 1 circa 10 volte più veloce (latenza mediana 6-9 s contro 65-99 s) con prompt di circa 3
  mila token contro 12 mila. Relazioni scritte / relazioni del GT sulle risposte valide: P-G 81/78, P-Q 62/104, J-G
  67/65. Scambi di tipo più frequenti: P-G unidirezionale → composizione (4); P-Q unidirezionale → bidirezionale (4);
  J-G unidirezionale → composizione (5).
- **Errori tipici, strada 1 (PlantUML)**:
  - P-G: 2 risposte senza `@enduml` (CardGameApp r0, FilmSet r1; finish_reason = stop, circa 330 token: il modello
    chiude il diagramma senza la riga finale) → nessun blocco, P0 fallito; 1 riga scartata (`class MandatorySoloRound
    --|> SoloRound`, dichiarazione e generalizzazione sulla stessa riga).
  - P-Q: **sintassi stile Java** `class X extends Y { ... }`, non riconosciuta dal parser: 42 righe scartate in 4
    risposte (P1 pulite 8/12). Le risposte restano valide fino a L3 (P1b, come previsto dalla regola), ma **perdono
    contenuto**: Sober r0 29 righe scartate, di cui 20 attributi / metodi e 4 generalizzazioni (RideHailing,
    RideSharing → TaxiService; SelfDrivingCar, RegisteredCar → Vehicle); CardGameApp r0 e r1 3 generalizzazioni
    ciascuna (JackRound, SoloRound → Round; MandatorySoloRound → SoloRound). 2 risposte ferme a L3 per tipi di
    attributo che citano classi non dichiarate (`Person` in FilmSet r1, `Piece` / `Piece[]` in Louvre r0). Diagrammi
    con poche relazioni (CardGameApp 3 su 13 del GT in entrambe le ripetizioni).
- **Errori tipici, strada 2 (JSON)**:
  - J-G: 3 risposte ferme a L2 per integrità: relazioni che puntano a id di nodo inesistenti, con id inventati a
    schema ripetuto (es. `e2e2e2e2-e2e2-…`), e id duplicati a schema (`a0b0c0d0-…`, `a1b1c1d1-…`); nessun id copiato
    dagli esempi (0/440). Metodi senza `+ ` (`compareHeight(other: Card): ComparisonResult`), recuperati dalla
    riscrittura ammessa di L4.
  - J-Q (12/12 ferme a L2) e J0-Q (10 ferme a L2): **id copiati dagli esempi del prompt** (J-Q: 4 risposte su 12, 111
    id distinti su 329; J0-Q: 7 su 12, 149 su 313), quindi id duplicati e relazioni verso nodi che non esistono nella
    risposta; id ricavati dai nomi dei campi, ripetuti tra nodi e membri (`studentId`, `email`, `name`); riuso dell'id
    non valido del template v4 (`a1b2c3d4-e5f6-4890-81h2-i3j4k5l6m7n8`). Lo schema non può imporre unicità e
    riferimenti (L3): per questo il vincolo non aiuta Qwen. J0-Q scrive il JSON dentro un blocco ```json (11/12,
    estratto correttamente).
- **Da notare per la decisione** (fatti, nessuna proposta di modifica della regola): S conta come valide le risposte
  della strada 1 con righe scartate (P1b), come stabilito nella voce 78, e non misura la qualità. La vincitrice P-Q ha
  S massimo ma J e R più bassi di P-G (0,577 contro 0,606; 0,183 contro 0,321) e perde contenuto con la sintassi
  `extends`.
- **STOP 2**: in attesa della decisione dell'utente sul seguito; nessuna modifica a regola, config, prompt o codice.

### [2026-10-08] Secondo pilota, decisioni dello STOP 2: strada PlantUML adottata, entrambi i modelli, post-processing PlantUML v2, analisi v2 descrittiva
- **Decisioni dell'utente sullo STOP 2** (voce 88):
  - l'esito della regola della voce 78 resta registrato così com'è (vince **P-Q**), con il limite emerso: **S conta
    anche le risposte con righe scartate** (P-Q: 42 righe in 4 risposte, contenuto perso);
  - **strada PlantUML adottata**; la strada "Apollon completo scritto dal modello" è **chiusa** come risultato del
    pilota (J-G 9/12, J-Q 0/12; errori di integrità che lo schema non può impedire);
  - modelli per il seguito: **ENTRAMBI** (Gemma 4 12B QAT e Qwen2.5-Coder 7B).
- **Post-processing PlantUML v2** (`generation/plantuml_postprocess.py`, parametro `version`; `corpus/apollon_convert.py`
  NON modificato: le correzioni riscrivono il testo della risposta prima del parser):
  - intestazioni `class X extends Y` e `class X implements A, B` (anche `abstract class` / `interface`, con o senza
    corpo `{ }` sulla stessa riga, anche con contenuto): l'intestazione diventa `class X ...` e si aggiungono in fondo
    al blocco `X --|> Y` e `X ..|> A`; conteggi in `syntax_rewrites` (intestazioni, extends, implements), colonna di
    `validation.csv`;
  - `@startuml` senza `@enduml` con finish_reason diverso da `length`: il blocco arriva fino alla fine del testo, con il
    diagnostico di formato `enduml_mancante` (con `length` resta `truncated`);
  - versioni: `pilot2_v1` (analisi originale del secondo pilota) e **`v2`, default per le run nuove**; il runner
    registra `plantuml_postprocess_version` nella provenienza. Verificato: con `pilot2_v1` i livelli ricalcolati
    coincidono con il manifest in 24/24 risposte PlantUML. Resta scartata la riga di P-G `class MandatorySoloRound
    --|> SoloRound` (dichiarazione e relazione sulla stessa riga). **Decisione dell'utente (punto 0 approvato)**: resta
    scartata, perché non è sintassi PlantUML standard ed è un caso isolato; **nessun'altra correzione basata sulle
    risposte del pilota**: le prossime eventuali si valutano sull'insieme di sviluppo.
- **Report del secondo pilota** (`experiments/analyze_pilot2.py`, solo presentazione; regola, numeri e criteri invariati,
  verificato con un diff del summary): `interactive_present` riportato come "n/a (aggiunto dal convertitore)" per P-*;
  colonna **P1** (valide fino a L3 e senza righe scartate) nella classifica: P-Q 8/12, P-G 9/12.
- **Analisi v2, SOLO DESCRITTIVA** (`python experiments/analyze_pilot2.py --postprocess v2` →
  `data/results/generation/pilot2_formats_analysis_v2/summary.md`, accanto all'originale invariata): stesse risposte
  salvate, nessuna nuova generazione; sezione "Risposte cambiate rispetto all'analisi originale". Esiti:
  - P-G: 2 risposte senza `@enduml` passano da −1 a L4 → **S 12/12**, P1 11/12, J 0,603, R 0,317;
  - P-Q: 3 + 3 + 4 intestazioni `extends` riscritte (CardGameApp r0, r1; Sober r0), righe scartate da 42 a 2, S
    invariato 12/12, P1 10/12, relazioni scritte da 62 a 72;
  - con la v2 la regola, riapplicata solo per descrivere l'effetto, darebbe **P-G** (pari con P-Q su S e troncate,
    Jaccard più alto). **L'esito valido resta P-Q (voce 88)**; la differenza va riportata in tesi come effetto del
    post-processing, non come risultato del pilota.
- Test (`check_plantuml`, `check_analyze_pilot2`): extends / implements (eredità multipla, interfacce, corpo sulla
  riga), conteggi, `pilot2_v1` che scarta le stesse righe di prima, blocco senza `@enduml` (stop → L4 con diagnostico;
  length → troncata), versione sconosciuta rifiutata; colonna P1 e `interactive_present` n/a nel report; analisi v2 in
  una cartella a parte senza modificare il summary originale.

### [2026-10-08] Struttura comune, espansore unico e formato JSON compatto (FASE 1, STOP 1)
- **Motivazione (misura dell'utente sui 79 diagrammi)**: nell'Apollon completo circa il 49% dei token sono UUID e il 24%
  layout; con id per nome e senza layout la mediana scende da 2.445 a 669 token (−72%). Gli UUID sono anche la causa
  degli errori principali della strada JSON del secondo pilota (id copiati dagli esempi, duplicati, relazioni verso
  nodi inesistenti, voce 88). Apollon resta il formato di consegna. Di qui un terzo formato di uscita, il JSON
  compatto, con id per nome e senza layout, espanso dal codice.
- **Struttura comune** (`generation/uml_structure.py`): classi in ordine (nome, tipo class / abstract / interface /
  enum, attributi e metodi nella forma del corpus, valori per gli enum), relazioni in ordine (tipo Apollon, estremi per
  nome con la convenzione di Apollon, molteplicità, ruoli, etichetta), vincoli di generalizzazione (solo da PlantUML:
  Apollon non li rappresenta). **Nessuna logica duplicata** (`corpus/apollon_convert.py` in sola lettura): la resa di
  attributi, metodi, tipi e molteplicità esiste solo in `build_apollon_json`; perciò dal PlantUML la struttura si
  ricava dall'Apollon costruito dal convertitore (`structure_from_parsed`), e l'**espansore unico** (`expand`)
  ricostruisce gli input del convertitore (ParsedClass e relazioni con un operatore canonico per tipo, verificato
  contro `relationship_kind` all'import) e richiama `build_apollon_json`: stessi id deterministici, layout, punti e
  adattamento al canvas del Passo 1.
- **Percorso PlantUML** (`generation/plantuml_postprocess.py`): con il post-processing **v2** passa da lettura →
  struttura → espansore (`plantuml_to_structure`, `plantuml_to_apollon`); con **pilot2_v1** resta la costruzione
  diretta di prima, per l'analisi originale del secondo pilota. Verificato contro la versione committata (`b1fecc5`)
  sulle 24 risposte PlantUML del pilota, in entrambe le versioni: diagramma, livello e riga di validazione identici
  (48/48).
- **Formato JSON compatto**: specifica in `docs/compact_format.md` (PROPOSTA, con un esempio completo dal corpus,
  TruckLogistics, e un frammento per i costrutti mancanti; entrambi espansi fino a L4, verificato dai test). Chiavi:
  `classes` / `relations`; classe `name`, `kind` (omesso per class), `attributes`, `methods` (stringhe "+ nome : tipo",
  "+ nome(parametri) : Tipo"), `values` per gli enum; relazione `type` (nomi brevi: association, unidirectional,
  inheritance, realization, aggregation, composition, dependency), `source`, `target`, `label`,
  `sourceMultiplicity`, `targetMultiplicity`, `sourceRole`, `targetRole`; chiavi vuote omesse; nessun id né
  metadato. Convertitori: `apollon_to_compact` (esempi del prompt) e `compact_to_apollon` (risposta → struttura →
  Apollon); `from_compact` è stretto (chiavi o tipi non previsti, nomi ripetuti → errore); la validazione a livelli
  delle risposte (C0-C2, scarti contati) è della FASE 2.
- **Controllo di sanità** (`generation/compact_sanity_check.py`, 79 diagrammi, nessun LLM):
  - a. PlantUML canonico → post-processing v2 (struttura → espansore): **identico al Passo 1 in 57/79, identico salvo
    gli id dei metodi in 22/79** (148 id di metodo su 155), nessun'altra differenza;
  - b. Apollon del Passo 1 → compatto → (testo) → struttura → espansore: **stesso esito** (57 + 22, 148 id), nessun'altra
    differenza;
  - **unica differenza, spiegata**: nel Passo 1 l'id di un metodo nasce dalla firma GREZZA del PlantUML trascritto
    (`stable_id("<modello>:method:<classe>:<firma grezza>:<i>")`, es. `getRideNr()`), mentre struttura, compatto e
    Apollon conservano la firma RESA (`+ getRideNr()`): la firma grezza non è ricostruibile. Verificato su tutti i 155
    metodi: l'id del Passo 1 si ottiene dalla firma grezza in 155/155; firma grezza uguale a quella resa in 7 casi (gli
    unici id che coincidono). Gli id restano deterministici e uguali per tutte le strade nuove (stesso espansore);
    contenuto, layout, punti e tutti gli altri id coincidono;
  - c. token (cl100k_base, serializzazione su una riga, senza `interactive`): Apollon completo mediana **2.445**, massimo
    7.145; JSON compatto mediana **338**, massimo 960; rapporto mediano 0,143 (min 0,100, max 0,174), cioè −86%.
    Rispetto alla misura dell'utente (669, solo id per nome e senza layout) il compatto toglie anche gli id di
    attributi, metodi e relazioni, i metadati e le chiavi vuote.
- Test (`check_uml_structure` in `generation/test_generation.py`): Apollon ↔ struttura ↔ compatto, normalizzazioni del
  convertitore, determinismo, chiavi vuote, compatti non validi rifiutati, riferimento rotto rifiutato, vincoli da
  PlantUML conservati, esempi della specifica uguali al corpus e a L4, esito del controllo di sanità (57 + 22, 148 id,
  mediana 338, massimo 960).
- **STOP 1**: in attesa di approvazione della struttura, dei nomi delle chiavi e del formato di attributi e metodi
  (`docs/compact_format.md`, "Punti da approvare"), e dell'eccezione sugli id dei metodi. Nessuna chiamata a un LLM.
- **Decisioni dello STOP 1 (utente)**:
  1. struttura comune ed espansore unico: **approvati**;
  2. id dei metodi: **eccezione approvata** (gli id sono etichette interne; contenuto, layout e altri id identici).
     **Condizione**, scritta in STATUS.md tra i requisiti della valutazione: le metriche confrontano gli elementi sempre
     per contenuto (nomi, firme, tipi), mai per id;
  3. formato compatto: approvate le chiavi di Apollon per molteplicità, ruoli ed etichetta, le chiavi vuote e
     `kind: "class"` omessi (il post-processing accetta anche le chiavi vuote presenti), gli enum con `values`, attributi
     e metodi come stringhe `"+ nome : tipo"`, i tipi di relazione con nomi brevi (**elenco chiuso** di sette valori,
     nella specifica e nelle istruzioni);
  4. **verso delle relazioni per RUOLO** (modifica): non `source` / `target` con il verso di Apollon (sorgente = parte),
     controintuitivo e causa delle composizioni invertite del primo pilota. Chiavi adottate: composizione e
     aggregazione `whole` / `part` con `wholeMultiplicity`, `partMultiplicity`, `wholeRole`, `partRole` (più `label`);
     generalizzazione e realizzazione `child` / `parent` (nient'altro); associazione, unidirezionale e dipendenza
     `source` / `target` con le chiavi di Apollon. L'espansore converte nel verso di Apollon (parte → sorgente, tutto →
     destinazione; figlia → sorgente, madre → destinazione). Le chiavi di un'altra famiglia presenti ma vuote sono
     ammesse come le altre chiavi vuote; con un valore non sono conformi.
- **Dopo la modifica** (`docs/compact_format.md` riscritta, esempi aggiornati e verificati dai test): controllo b sui 79
  diagrammi **invariato** (identico in 57, identico salvo gli id dei metodi in 22 con 148 id, nessun'altra
  differenza); controllo a invariato; token del compatto **invariati**: mediana 338, massimo 960 (caratteri mediana da
  1.546 a 1.542). `read_compact` ha ora due modalità: stretta (esempi, controlli) e tollerante (risposte del modello:
  ogni elemento non conforme scartato o chiave ignorata, con categoria e dettaglio, nulla riparato o inventato).

### [2026-10-08] Strada "JSON compatto" (FASE 2): istruzioni, post-processing C0-C2, schema disattivato, runner
- **Istruzioni** `generation/templates/v4_compact_instructions.txt`: dal template v4 cambiano SOLO le parti sul formato
  (come per PlantUML, voce 78): ruolo di esperto del formato compatto; struttura di primo livello `classes` /
  `relations`; voce di classe (`name`, `kind`, `attributes`, `methods`, `values`) al posto di id, posizione,
  dimensioni e `data`; voce di relazione con l'**elenco chiuso** dei sette tipi e le chiavi per famiglia (`whole` /
  `part`, `child` / `parent`, `source` / `target`) al posto di id, handle e punti; regole di scelta del tipo
  riformulate con i nuovi nomi e le chiavi di ruolo; righe tolte: id univoci, coordinate, canvas. **Identiche** (salvo
  i nomi dei tipi e "edge" → "relation"): tipi semplici degli attributi e notazione `tipo[]`, molteplicità, linee guida
  di modellazione (righe 61-67 della v4; verificato da un test). Esempi: voce `v4_example_item.txt` della v4
  ("Example n — JSON:") con il compatto del Passo 1 su una riga (`prompt_builder`, `output_format: "compact"`); stessi
  esempi recuperati degli altri formati.
- **Post-processing** `generation/compact_postprocess.py`: stessa estrazione di `postprocess.py` (ragionamento tolto,
  risposta intera / blocco ``` / oggetto bilanciato); livelli **C0** JSON trovato, **C1** JSON valido (oggetto), **C2b**
  conversione tollerante riuscita (`read_compact(strict=False)`, almeno una classe), **C2** conforme alla specifica
  (nessuno scarto); poi espansore unico e GLI STESSI L2-L4. Ogni scarto o chiave ignorata è registrato con categoria e
  dettaglio (`compact_issues`, conteggio per categoria in `validation.csv`); nulla viene riparato o inventato; le
  chiavi vuote presenti sono ammesse. Le normalizzazioni dell'espansore (tipi noti, visibilità → `+`, molteplicità
  `n` → `*`) sono contate a parte (`normalizations`). Troncamento come in `postprocess.py`. Diagnostico di formato
  della risposta: solo `extra_text` (il resto dell'Apollon lo produce l'espansore). Sui 79 ground truth passati come
  risposte (anche in un blocco ```json): 79/79 a L4, C2 senza scarti, nessuna normalizzazione.
- **Schema per la generazione vincolata** `generation/schemas/compact_generation.schema.json` (da
  `python generation/compact_postprocess.py`): niente `$ref`, `anyOf` per le tre famiglie di relazione,
  `additionalProperties: false`, `maxItems` 39 sulle relazioni come lo schema Apollon (voce 78); i 79 ground truth sono
  validi. **DISATTIVATO**: nessuna config lo usa (verificato da un test); si proverà dopo. Come per lo schema Apollon,
  non vincola i riferimenti per nome.
- **Runner**: ramo `output_format: "compact"` (validazione con `compact_postprocess`), provenienza
  `compact_format_spec`. **Calibrazione**: `calibrate_tokens.py --formats` (default apollon e plantuml, invariato per il
  secondo pilota).
- Test (`check_compact`): istruzioni e righe identiche alla v4, esempi compatti uguali al Passo 1 e agli esempi degli
  altri formati, livelli e fallimenti (ragionamento, fence, troncamento, JSON incompleto, oggetto non compatto, nessuna
  classe, nessun JSON), scarti per categoria e normalizzazioni su una risposta disordinata, schema (aggiornato, 79 GT
  validi, nessuna config lo usa), ramo del runner con MockClient.

### [2026-10-08] Insieme di sviluppo e confronto dei formati PlantUML / JSON compatto (FASE 3, STOP 2): selezione, config, metriche e regola PRIMA delle run
- **Insieme di sviluppo** (`experiments/select_dev.py`, deterministico; solo CORPUS, query in leave-one-out, test set mai
  toccato): candidati del primo pilota (59 convertiti, esclusi EatAtHome e i 14 fuori scala rispetto al test set) → 44;
  **PROPOSTA: esclusi i 6 esercizi dei piloti** (il post-processing v2 è nato dalle loro risposte, voce 89: l'insieme di
  sviluppo deve esserne indipendente) → 38 (basso 13, medio 14, alto 11). Quote per fascia di score_norm proporzionali
  con il metodo dei resti più grandi: **7 / 7 / 6**; dentro la fascia, quantili equispaziati di dimensione (posizioni
  floor((i + 0,5) · n / k) sull'ordine per dimensione e id). Con i piloti inclusi nessuno dei 6 verrebbe comunque scelto
  (cambierebbero 3 esercizi della fascia media). Esercizi (fascia, dimensione, GT Apollon compatto in token):
  basso — Boeing (22, 1.641), OilWells (22, 1.500), Restaurant (23, 1.568), EUScienceConnect (29, 2.374),
  HomeForTheElderly (35, 2.764), HelpingHands (43, 3.347), Bookmaker (50, 3.149);
  medio — BusTransportationManagementSystem (21, 1.388), FitnessCompanyConan (27, 2.167), Facepage (32, 2.622),
  Musicmatic (32, 2.595), AlphaInsurance (34, 2.651), ClothingCompany (38, 2.488), PizzaDeliveryWithEntertainment (45,
  3.098); alto — ProjectManagement (16, 1.742), HospitalHouseMD (18, 1.503), InsuranceCompany (22, 1.723),
  TruckLogistics (27, 2.196), Ebike (34, 2.583), eHome2020 (36, 2.618).
- **Config** `experiments/configs/dev_formats.yaml`: P-G, P-Q (PlantUML, post-processing v2), C-G, C-Q (JSON compatto,
  generazione libera); stessi modelli e metadati del secondo pilota (Gemma 4 12B QAT; Qwen2.5-Coder 7B Q6_K); bm25 k =
  2, temperature 0.3, top_p 0.95, top_k 64, max_tokens 12288, contesto 32768, 2 ripetizioni: 4 × 40 = **160
  generazioni**. Prompt stimati (cl100k_base) min / mediana / max: PlantUML 2.187 / 2.970 / 3.689; compatto 2.556 /
  3.471 / 4.116 (Apollon completo, per confronto: 6.731 / 8.651 / 13.132); output dei GT: PlantUML 142 / 203 / 442,
  compatto 207 / 333 / 532.
- **Calibrazione prima delle run** (chiamate reali con max_tokens = 1, una per modello): `calibrate_tokens.py
  experiments/configs/dev_formats.yaml --configuration C-G --formats plantuml compact` e lo stesso con C-Q.
- **Stima della durata** (non misurata; dalle latenze del secondo pilota, P-G mediana 9,1 s e P-Q 6,0 s con prompt di
  circa 3 mila token, e dall'output del compatto circa 1,6 volte quello PlantUML): P-G circa 5-8 minuti, P-Q 3-5, C-G
  7-11, C-Q 5-8; calibrazioni circa 1-2 minuti per modello; totale circa 25-35 minuti di generazione più i cambi di
  modello.
- **METRICHE DI SVILUPPO (registrate prima delle run; le metriche semantiche definitive restano da decidere con i
  relatori, domanda 11)**, per configurazione e per formato, sempre per CONTENUTO e mai per id (requisito di STATUS.md):
  - validità: **V** = risposte valide fino a L3; **Vc** = valide fino a L3 e senza scarti (P1 per PlantUML, C2 per il
    compatto); troncamenti; righe scartate / scarti per categoria; normalizzazioni;
  - **J** = Jaccard medio dei nomi di classe con il GT (risposte valide fino a L3);
  - relazioni (`analyze_pilot.compare_relations`, accoppiamento 1:1 per coppia di classi): **R** = relazioni del GT con
    stessa coppia e stesso tipo / relazioni del GT; stessa coppia / relazioni del GT; **verso** uguale / relazioni dello
    stesso tipo orientato (e a parte per composizione / aggregazione); **molteplicità** uguali / confrontate;
  - token di prompt e di completamento reali, latenza (mediana, min, max), durata.
- **REGOLA DI CONFRONTO (PROPOSTA allo STOP 2; diventa definitiva con l'approvazione, PRIMA delle run)**. Per ciascun
  formato F, sulle 80 risposte (2 modelli × 20 esercizi × 2 ripetizioni):
  - controllo preliminare: una configurazione non eseguibile, incompleta o fermata per ragionamento → STOP senza
    decidere; più di 2 troncamenti su 40 in una configurazione → segnalato (non blocca);
  - (1) **validità**: se |V(compatto) − V(PlantUML)| ≥ 4 (5 punti percentuali), vince il formato con V più alto;
  - (2) altrimenti **R**: se la differenza è ≥ 0,03, vince R più alto;
  - (3) altrimenti **J**: se la differenza è ≥ 0,03, vince J più alto;
  - (4) altrimenti **Vc**: se la differenza è ≥ 4, vince Vc più alto;
  - (5) altrimenti **pareggio pieno → PlantUML** (strada già adottata, voce 89: senza un vantaggio misurato non si cambia).
  - **Coerenza tra i modelli**: la stessa regola si applica a ciascun modello (40 risposte per formato, soglie 2
    risposte per V e Vc, 0,03 per R e J); se i vincitori per Gemma e per Qwen sono diversi l'esito è "dipende dal
    modello": si riporta e ci si ferma per una decisione, senza scelta automatica.
  - Riportati ma fuori dalla regola: confronto appaiato per (esercizio, modello, ripetizione) (valida in un formato e
    non nell'altro, nei due versi), verso e molteplicità, token, latenze, scarti, normalizzazioni; per fascia di
    score_norm, solo descrittivo. Nessun test statistico (n piccoli).
- **STOP 2**: in attesa di approvazione di insieme di sviluppo (piloti esclusi o inclusi), config, metriche, regola e
  soglie. Proposta: scrivere e testare lo script di analisi dell'insieme di sviluppo PRIMA delle run, come per il
  secondo pilota (voce 82).
- **Decisioni dello STOP 2 (utente)**:
  1. insieme di sviluppo **approvato, con i 6 esercizi dei piloti ESCLUSI** (il post-processing v2 è nato dalle loro
     risposte);
  2. config `experiments/configs/dev_formats.yaml` **approvata**;
  3. regola approvata con due modifiche:
     a. **ordine dei criteri: 1) Vc, 2) R, 3) J, 4) V, 5) pareggio pieno → PlantUML**, stesse soglie (Vc e V ≥ 4
        risposte su 80; R e J ≥ 0,03; per modello 2 risposte su 40 e 0,03). Motivo: nel secondo pilota contare come
        valide le risposte con contenuto scartato ha falsato l'esito (P-Q);
     b. **J e R su TUTTE le risposte**, con 0 per quelle che non arrivano a L3 (per R: 0 relazioni ritrovate, mentre le
        relazioni del GT contano al denominatore). Motivo: evitare l'effetto di selezione (riferimento Gemma libero: J
        0,705 su sole 8 valide). Le versioni sulle sole valide restano tra le metriche secondarie;
     coerenza tra i modelli e controllo preliminare **approvati** come proposti;
  4. script di analisi PRIMA delle run, testato su dati finti.
- **REGOLA DEFINITIVA** (sostituisce la proposta sopra; non si modifica dopo aver visto i dati): controllo preliminare
  (configurazione non eseguita, incompleta o fermata per ragionamento → STOP; più di 2 troncamenti su 40 segnalati);
  per formato sulle 80 risposte, il primo criterio con differenza ≥ soglia decide: **Vc (4), R (0,03), J (0,03), V (4)**;
  altrimenti **PlantUML**; la stessa regola per modello (soglie 2 / 0,03 / 0,03 / 2): vincitori diversi → **"dipende dal
  modello"**, STOP per decisione dell'utente; altrimenti decide il confronto sulle 80 risposte (se diverso dal vincitore
  comune dei due modelli lo si segnala, senza cambiare l'esito: caso non previsto dalla proposta, applicata alla
  lettera).
- **Script** `experiments/analyze_dev.py` (scritto e testato PRIMA delle run): legge `dev_formats__<C>` in sola
  lettura e ricalcola tutto dalle risposte grezze (PlantUML con la versione del post-processing registrata nella
  provenienza, v2; compatto con `compact_postprocess`); scarta le run di un altro modello; scrive
  `data/results/generation/dev_formats_analysis/summary.md` con l'esito, le tabelle dei criteri (80 risposte e per
  modello), metriche per configurazione (V, Vc, J, R, J e R sulle valide, troncate, latenza), livelli, fallimenti,
  scarti e normalizzazioni, relazioni (coppia, tipo, verso, molteplicità), confronto appaiato, fasce di score_norm,
  token e latenze. **Da qui la regola nel codice (`CRITERIA`, soglie, `TIE_WINNER`, `MAX_TRUNCATED`, `decide`,
  `outcome`, `metrics`) non si modifica senza una nuova voce.**
- Test (`check_analyze_dev`): ciascun criterio che decide (anche con la soglia esatta in virgola mobile), pareggio a ogni
  criterio fino al pareggio pieno → PlantUML, soglie per modello, R non definito = 0; J e R con 0 per le non valide
  (e denominatore su tutte le relazioni del GT); "dipende dal modello"; configurazione incompleta (STOP); troncamenti
  segnalati senza bloccare; run finte con 160 risposte (Vc 80 contro 74 → PlantUML per Vc; Gemma pari → pareggio pieno);
  run di un altro modello scartata; costanti della regola.

### [2026-10-08] Versione di configurazione 2: max_tokens 4096, contesto 32768 (STOP 1 della leva k)
- **Dati misurati** nell'insieme di sviluppo (voce 92, raw delle run `dev_formats__*`): risposta più lunga 537 token in
  PlantUML (P-G) e 1.094 nel compatto (C-G); prompt reale massimo con k = 2: 4.224 (C-G). Fattori di calibrazione
  misurati (token reali / stima cl100k_base), massimo per modello: Gemma 1,239, Qwen 7B 1,206 (prompt Apollon dei
  piloti); sui formati attuali con k = 2: Gemma 1,046 (PlantUML) e 1,039 (compatto), Qwen 1,014 e 1,011.
- **Dry run dei prompt** (20 esercizi dell'insieme di sviluppo, bm25 in leave-one-out; stima cl100k_base min / mediana /
  max e massimo moltiplicato per il fattore prudente del modello):

  | formato | k | stima | max × 1,239 (Gemma) | max × 1,206 (Qwen) |
  |---|---|---|---|---|
  | PlantUML | 2 | 2.187 / 2.970 / 3.689 | 4.571 | 4.449 |
  | PlantUML | 3 | 2.778 / 3.563 / 4.365 | 5.408 | 5.264 |
  | PlantUML | 5 | 4.043 / 4.860 / 6.307 | 7.814 | 7.606 |
  | PlantUML | 8 | 5.688 / 7.186 / 8.880 | 11.002 | 10.709 |
  | compatto | 2 | 2.556 / 3.471 / 4.116 | 5.100 | 4.964 |
  | compatto | 3 | 3.295 / 4.168 / 4.931 | 6.110 | 5.947 |
  | compatto | 5 | 4.802 / 5.654 / 7.256 | 8.990 | 8.751 |
  | compatto | 8 | 6.713 / 8.372 / 10.259 | **12.711** | 12.372 |

- **Decisione dell'utente**: versione di configurazione 2 con **max_tokens 4096** (3,7 volte la risposta più lunga
  misurata) e **contesto 32768** (invariato, già verificato in VRAM per entrambi i modelli), uguali per entrambi i
  modelli, tutti i formati e tutti i k. Non si scende a 25.600 (proposto come minimo con il 50% di margine): non serve
  VRAM ai modelli attuali e non basterebbe comunque per il Qwen 14B. Con 16384 il caso peggiore prudente (12.711 +
  4.096 = 16.807) non ci stava.
- **Margine nel caso peggiore** (k = 8, compatto, Gemma; prompt massimo + max_tokens contro 32768): con il fattore
  prudente 1,239 fabbisogno 16.807, margine 15.961 token (**95%** del fabbisogno, 49% del contesto libero); con il
  fattore del formato 1,039 fabbisogno 14.755, margine 18.013 (**122%**, 55% del contesto libero).
- **Versione di configurazione** (`experiments/run_experiment.py`): chiave di primo livello `config_version` (assente =
  1). Le run esistenti (piloti, `dev_formats`) sono la versione 1 (32768 / 12288) e restano intatte; i config nuovi
  dichiarano `config_version: 2`. Il controllo "contesto e max_tokens identici per modello" confronta ora solo le run
  con lo stesso (model_id, quantizzazione, config_version) (`model_key`, `inconsistent_runs`); il runner salva la
  chiave in `config.json` con il resto del config. Test: stessa versione con valori diversi rifiutata, versione diversa
  ammessa, run vecchie senza chiave = versione 1; le 4 configurazioni di `dev_k.yaml` non sono bloccate dalle run
  esistenti. I template del Passo 3b (`gemma4_12b_qat_template.yaml`, `qwen25coder7b_template.yaml`) NON sono stati
  modificati (restano 12288): da decidere quando si sblocca il 3b.
- **Qwen2.5-Coder 14B Q4_K_M a contesto 16384 in 12 GB (solo stima, nessuna azione)**: 48 strati, 8 teste KV, dimensione
  128 → KV cache F16 192 KiB per token; pesi circa 9,0 GB (dimensione del GGUF, da verificare in My Models); buffer di
  calcolo circa 0,7 GB. KV F16 3,2 GB → circa 12,9 GB (non ci sta); KV Q8_0 1,7 GB → circa 11,4 GB (al limite); KV Q4_0
  0,9 GB → circa 10,6 GB (probabilmente sì, margine circa 1 GB). Coerente con l'osservazione a 32768 con KV Q4 (circa
  11,5 GB più la memoria del desktop: trabocca, voce 84). Da misurare, non verificata.

### [2026-10-08] Leva "numero di esempi k" sull'insieme di sviluppo (FASE 2, STOP 2): config, calibrazione, regola PROPOSTA, analisi PRIMA delle run
- **Config** `experiments/configs/dev_k.yaml` (versione di configurazione 2): stessi 20 esercizi e stessi modelli di
  `dev_formats.yaml`, bm25 con **k = 2, 3, 5, 8**, formati PlantUML (v2) e compatto, temperature 0.3, top_p 0.95, top_k
  64, max_tokens 4096, contesto 32768, 2 ripetizioni; anche k = 2 si rigenera (stessi parametri per tutte le
  condizioni). Configurazioni P-G, C-G, P-Q, C-Q da 160 generazioni ciascuna: **640** in tutto, un modello per volta.
- **Calibrazione** prima delle run, una per modello, con il caso peggiore: `calibrate_tokens.py` usa ora il k PIÙ ALTO
  della config (8; per le config con un solo k nulla cambia) e registra k e versione nell'esito.
- **Stima della durata** (non misurata; dalle latenze di `dev_formats` a k = 2, mediane P-G 7,6 s, C-G 12,1, P-Q 5,8, C-Q
  13,3, più 1-4 s di lettura del prompt in più a k = 8): P-G circa 20-28 minuti, C-G 30-40, P-Q 16-22, C-Q 33-42;
  totale circa 1 h 45 - 2 h 15, più circa 2-3 minuti di calibrazione per modello e i cambi di modello. Un ciclo fino al
  tetto di 4096 token costa circa 2 minuti per risposta.
- **REGOLA DI SCELTA DI k (PROPOSTA allo STOP 2; diventa definitiva con l'approvazione, PRIMA delle run)**, per ciascun
  formato e ciascun modello separatamente, 40 risposte per k (20 esercizi × 2 ripetizioni); metriche della voce 92 (Vc =
  valide fino a L3 e senza scarti; R = relazioni del GT con stessa coppia e stesso tipo su TUTTE le risposte, 0 per le
  non valide):
  0. controllo preliminare: configurazione (formato, modello) completa (160 risposte, tutti i k), non fermata per
     ragionamento, del modello del config; altrimenti quel formato non si decide (STOP per il formato; l'altro formato
     si decide comunque). Più di 2 troncamenti su 40 per un k: segnalato, non blocca;
  1. **k ammissibili**: Vc(k) ≥ Vc(2) − 2 (k = 2 sempre ammissibile);
  2. **R\*** = il miglior R tra i k ammissibili (R non definito = 0);
  3. **k scelto = il più piccolo k ammissibile con R(k) ≥ R\* − 0,02** (soglia inclusa; a parità di qualità, meno
     token) — **portata a 0,03 allo STOP 2, vedi sotto**;
  4. per formato: stesso k per Gemma e per Qwen → quello è il k del formato; k diversi → **"dipende dal modello"**,
     STOP e decisione dell'utente. I due formati possono avere k diversi.
  Riportati ma fuori dalla regola, per ogni k: V, J (su tutte le risposte e sulle sole valide), R sulle valide,
  molteplicità corrette, verso delle relazioni, scarti, troncamenti, token di prompt e di completamento, latenza;
  andamento di R e Vc per fascia di score_norm (solo descrittivo).
- **Script** `experiments/analyze_k.py` (scritto e testato PRIMA delle run): riusa senza modificarle validazione e
  metriche di `analyze_dev.py`; legge `dev_k__<C>` in sola lettura, scarta le run di un altro modello, scrive
  `data/results/generation/dev_k_analysis/summary.md`. Test (`check_k`): versione di configurazione, config, calibrazione
  con k = 8, regola (ammissibili per Vc, R entro 0,02 con la soglia inclusa in virgola mobile, il più piccolo, R non
  definito, "dipende dal modello", formato non decidibile mentre l'altro si decide, troncamenti segnalati), run finte.
- **Nota**: la leva k vale solo per le condizioni con esempi (bm25, random, oracle); quando si arriverà al test set il
  confronto con random dovrà usare lo stesso k.
- **STOP 2**: in attesa di approvazione di config, regola e soglie (Vc − 2 su 40, R entro 0,02). Nessuna chiamata a un
  LLM.
- **Decisioni dello STOP 2 (utente)**: config, calibrazione e regola **approvate**, con una modifica: **tolleranza su R =
  0,03** (non 0,02). Motivo: con 40 risposte per k la variabilità di R è di qualche centesimo; la regola sceglie il k
  più piccolo entro la tolleranza, quindi una soglia più larga è conservativa (preferisce meno esempi salvo guadagni
  chiari) ed è coerente con la soglia di R della voce 92. Tolleranza su Vc = 2 risposte su 40: approvata.
  **Regola definitiva**: k ammissibili con Vc(k) ≥ Vc(2) − 2; R\* = miglior R tra gli ammissibili; k scelto = il più
  piccolo ammissibile con R(k) ≥ R\* − 0,03; stesso k per i due modelli → k del formato, altrimenti "dipende dal
  modello". Aggiornati `experiments/analyze_k.py` (`R_TOLERANCE = 0.03`) e i test (`check_k`: soglia 0,03 inclusa in
  virgola mobile, k escluso appena fuori soglia). **Da qui la regola nel codice non si modifica senza una nuova voce.**

### [2026-10-08] Dopo la leva k: solo Gemma 4 12B QAT, k di lavoro = 3, configurazione di lavoro (supera la voce 89 sui modelli)
- **Fonte dei dati**: `data/results/generation/dev_k_analysis/summary.md` (commit `3017a8c`), insieme di sviluppo (20
  esercizi del corpus, leave-one-out), MAI il test set; 40 risposte per formato, modello e k.
- **Esito della regola della voce 94, applicata così com'è**: PlantUML **k = 2** (Gemma k = 2: R\* 0,321 a k = 8, tutti
  i k entro 0,03; Qwen k = 2); JSON compatto **"dipende dal modello"** (Gemma k = 3, Qwen k = 2).
- **Decisioni dell'utente**:
  1. **Modello per il seguito: SOLO Gemma 4 12B QAT** (supera la voce 89, che teneva entrambi i modelli). Motivazione
     (dati di sviluppo): R di Gemma più alto a ogni k e in entrambi i formati — PlantUML 0,298-0,321, compatto
     0,210-0,310 — contro Qwen2.5-Coder 7B 0,139-0,159 in PlantUML e 0,114-0,151 nel compatto (il minimo di Gemma supera
     il massimo di Qwen); validità con PlantUML equivalente (V 40/40 per entrambi a ogni k; Vc Gemma 38-40, Qwen
     34-38); nel compatto Qwen ha decine di scarti a ogni k (61, 56, 92, 47 per k = 2, 3, 5, 8; Gemma 12, 9, 0, 16). Le run
     e le analisi di Qwen (secondo pilota, `dev_formats`, `dev_k`) restano come risultato documentato: modello da coding
     valutato e scartato. Domanda aggiunta per i relatori (STATUS.md, domanda 16): se desiderano comunque un secondo
     modello sul test set (costo basso con PlantUML).
  2. **k di lavoro = 3 per entrambi i formati.** Con Gemma: PlantUML Vc 40/40, R 0,307 (entro 0,03 dal migliore, 0,321 a
     k = 8); compatto Vc 34/40, R 0,310 contro 26/40 e 0,210 a k = 2. **Nota di trasparenza**: per PlantUML la regola
     della voce 94 sceglie k = 2 (Vc 38/40, R 0,312); k = 3 è una scelta dell'utente che usa lo stesso k nei due formati,
     resta entro la tolleranza su R e ha Vc 40 contro 38. Per il Passo 3b si tiene **anche k = 2**, per il confronto con
     la baseline statica a parità di esempi (la statica ha 2 esempi).
- **Risultati di sviluppo da annotare** (solo descrittivi, Gemma salvo dove indicato):
  - **verso delle relazioni** (stesso verso sulle relazioni dello stesso tipo orientato) molto migliore nel compatto,
    circa 95% a ogni k (42/44, 44/46, 50/52, 44/45), che in PlantUML (21/42, 19/33, 27/33, 26/40: 50-82%); le chiavi di
    ruolo whole / part e child / parent (voce 90) sembrano funzionare;
  - **molteplicità corrette solo nel 25-47% dei casi** a ogni k (PlantUML 39-47%, compatto 25-30%; Qwen 16-37%): è la
    prossima leva.
- **Configurazione di lavoro** (STATUS.md): Gemma 4 12B QAT, versione di configurazione 2 (contesto 32768, max_tokens
  4096), temperature 0.3, top_p 0.95, top_k 64, bm25, **k = 3**, formati PlantUML e JSON compatto. La temperatura resta il
  valore di lavoro dei piloti (domanda 8 aperta).

### [2026-10-09] Leva "istruzioni mirate", FASE 1 (STOP 1): analisi degli errori di Gemma a k = 3 (solo descrittiva)
- **Dati**: risposte di Gemma 4 12B QAT a k = 3 di `dev_k` (P-G 40, tutte valide fino a L3; C-G 40, 39 valide),
  insieme di sviluppo, mai il test set; sola lettura dei raw. Relazioni accoppiate per coppia di classi come in
  `analyze_pilot.compare_relations` (1:1, prima lo stesso tipo); molteplicità normalizzate (n → *, 0..* = *). Script di
  analisi nello scratchpad (non versionato). Il punto 0 della richiesta (solo Gemma, k = 3, configurazione di lavoro)
  era già registrato nella voce 95.
- **Molteplicità** (per estremo, relazioni accoppiate esclusi generalizzazione e realizzazione): uguali 137/240 in
  PlantUML e 104/236 nel compatto. Molti scarti vengono da estremi **vuoti nel GT** che il modello riempie, come chiedono
  le istruzioni ("always specified"): 46 in PlantUML e 48 nel compatto (es. Ebike controller-battery, Bookmaker
  bettor-bet); escludendoli, uguali 137/194 (71%) e 104/188 (55%). Errori veri più frequenti (GT → risposta):
  `*` → `1..*` (18 e 28; es. Boeing acquisition-contract, AlphaInsurance report-estimator), `*` → `1` (19 e 18; es.
  ClothingCompany representative-country, Boeing contract-airline), `0..1` → `1` (6 e 5; es. AlphaInsurance
  customer-broker), `1` → `1..*` / `*` (4 e 13). Molteplicità scambiate tra i due estremi: rare (2 e 6 su 85 e 80
  relazioni con valori diversi ai due estremi).
- **Tipi di relazione** (stessa coppia): stesso tipo 108/156 in PlantUML e 109/158 nel compatto. Confusioni più
  frequenti: associazione o unidirezionale → **composizione** (12 + 9 in PlantUML, 18 + 13 nel compatto; es.
  FitnessCompanyConan center-room, EUScienceConnect publisher-journal, Ebike ebike-frame); unidirezionale →
  associazione (13 e 8); **generalizzazione → associazione** (9 in PlantUML, es. FitnessCompanyConan member-person e
  trainer-person). Tra le relazioni senza corrispondente nel GT le composizioni sono 22 in PlantUML e 48 nel compatto.
- **Verso** (stesso tipo orientato): PlantUML **10 generalizzazioni invertite** (solo nel verso sbagliato) più una
  risposta con le generalizzazioni scritte in entrambi i versi (Facepage r0); il modello scrive `Superclasse --|>
  Sottoclasse` (es. FitnessCompanyConan `Person --|> Trainer`, Musicmatic `Song --|> Single`, TruckLogistics `Vehicle
  --|> Truck`). Compatto: **0 generalizzazioni invertite su 40** (le chiavi child / parent della voce 90 funzionano).
  Composizioni invertite: 2/6 e 2/5, tutte in eHome2020, dove però è il **GT a sembrare sbagliato** (`Room "2..*" *--
  "1" Apartment`: rombo sulla stanza, mentre le molteplicità dicono che un appartamento ha due o più stanze; la risposta
  scrive `Apartment "1" *-- "2..*" Room`). Da verificare sull'immagine originale; nessuna correzione fatta.
- **Altri errori**: classi del GT mancanti 101 in PlantUML e 91 nel compatto (circa 2,5 per risposta), classi in più
  122 e 124, in gran parte nomi diversi per lo stesso concetto (es. AlphaInsurance InsurancePolicy contro Policy): il
  confronto sui nomi esatti le conta due volte e trascina le relazioni (196 e 185 relazioni del GT senza la coppia nella
  risposta). Generalizzazioni del GT mancanti 59/76 in PlantUML (comprese le 10 invertite e quelle con una classe
  assente) e 33/73 nel compatto. Attributi ripetuti nelle sottoclassi invece che nella superclasse: 0 in entrambi i
  formati (non è un problema).

### [2026-10-09] Leva "istruzioni mirate", FASE 2 (STOP 2): blocco di regole di modellazione aggiuntive (PROPOSTA)
- **Blocco** `generation/templates/targeted_rules_block.txt` (13 righe; circa 395-400 token cl100k_base, istruzioni da
  1.192 a 1.585 token in PlantUML e da 1.378 a 1.779 nel compatto): regole GENERALI di modellazione UML, una per
  ciascuna categoria più frequente della voce 96, nessuna indicazione specifica degli esercizi di sviluppo:
  1. **molteplicità** lette dalla formulazione del testo, estremo per estremo ("exactly one" → 1; "at most one", "may
     have a", "optionally" → 0..1; "one or more", "at least one" → 1..*; "zero or more", plurale senza minimo → *), con
     la regola del limite inferiore ("1..*" solo se il testo richiede almeno uno, "1" solo se sempre esattamente uno,
     "0..1" se può mancare) e il significato della molteplicità accanto a una classe;
  2. **composizione / aggregazione / associazione**: composizione solo se la parte non esiste senza il tutto e
     appartiene a un solo tutto; aggregazione se la parte esiste da sola o è condivisa; associazione semplice quando il
     testo dice solo che due cose sono collegate ("has", "is assigned to", "manages", "works for", "uses");
  3. **generalizzazione**: "is a", "is a kind of", "can be either" → generalizzazione, non associazione; superclasse
     comune quando più classi condividono attributi o relazioni, attributi comuni solo nella superclasse;
  4. **verso della generalizzazione**: l'unica riga che cambia tra i formati (`targeted_rules_direction.yaml`):
     PlantUML `"Subclass --|> Superclass" (e.g. "Guitar --|> Instrument"), never "Superclass --|> Subclass"`; compatto
     `"child" ... subclass, "parent" ... superclass, e.g. {"type": "inheritance", "child": "Guitar", "parent":
     "Instrument"}`. Esempio generico verificato: né "Guitar" né "Instrument" compaiono come classe o nel testo dei 79
     esercizi (59 del corpus, 20 del test set); "Animal", la prima scelta, è stato scartato perché è una classe del test
     set (DB08_VeterinaryClinic).
- **Punto fisso di inserimento**: subito prima dell'ultimo paragrafo delle istruzioni ("Your output must be ..."),
  separato da una riga vuota; nessuna riga esistente è modificata (verificato con un diff: solo righe aggiunte, 12 + la
  riga vuota). Il blocco è identico nei due formati salvo la riga del verso. Il collegamento al prompt builder (variante
  di istruzioni) si farà nella FASE 3, dopo l'approvazione.
- **Se adottato**: il blocco andrà applicato a TUTTE le condizioni del Passo 3b (zero-shot, statico, random,
  retrieval), perché le condizioni devono differire solo nel blocco degli esempi; di conseguenza il prompt della
  baseline statica non sarà più identico a quello dello studio 2025 (Garaccione et al.): aggiunto alla domanda 9 per i
  relatori (STATUS.md).
- **Punti aperti per la FASE 3** (dalla voce 96): definizione della metrica M sugli estremi del GT con molteplicità
  ESPLICITA (circa il 20% degli estremi del GT è vuoto e il modello li riempie come chiedono le istruzioni), con la
  versione su tutti gli estremi tra le secondarie; verifica sull'immagine del verso della composizione di eHome2020
  (`Room "2..*" *-- "1" Apartment` nel GT).
- **STOP 2**: in attesa di approvazione del testo del blocco e del punto di inserimento. Nessuna chiamata a un LLM.

### [2026-10-09] Istruzioni mirate: blocco DEFINITIVO congelato, metrica M e regola di adozione (PRIMA della run)
- **Modifica approvata allo STOP 2**: dalla regola sulla generalizzazione è **eliminata** la frase "Introduce a common
  superclass when two or more classes share the same attributes or the same relationships" (con il suo seguito "and
  put the shared attributes only in the superclass", che senza la prima parte resterebbe senza soggetto). Restano il
  trigger lessicale ("is a" / "is a kind of" / "can be either" → generalizzazione) e la regola del verso. **Motivo**:
  nessuna evidenza nella FASE 1 di superclassi implicite mancanti (attributi ripetuti nelle sottoclassi: 0 in
  PlantUML, 0 nel compatto, voce 96) e rischio di classi inventate. Tutto il resto (molteplicità, criterio composizione
  / associazione, esempio, punto di inserimento) come approvato.
- **Blocco definitivo** (`generation/templates/targeted_rules_block.txt`, 11 righe; `{generalization_direction}` è la
  riga di `targeted_rules_direction.yaml` del formato):

  ```
  ADDITIONAL MODELING RULES
  Multiplicities — read them from the wording of the text, separately for each end of every relationship. The multiplicity next to a class says how many instances of THAT class are linked to one instance of the other class:
  - "exactly one", "each ... belongs to one", "a single" -> "1"
  - "at most one", "may have a", "optionally", "can be assigned to a" -> "0..1"
  - "one or more", "at least one" -> "1..*"
  - "zero or more", "may have several", "can have many", or a plural with no stated minimum -> "*"
  Use "1..*" only when the text states that at least one is required, otherwise use "*"; use "1" only when exactly one is always required, and "0..1" when it may be missing.
  Relationship types:
  - Use composition only when the part cannot exist without its whole and belongs to exactly one whole (deleting the whole deletes its parts); use aggregation when the part can exist on its own or be shared. If the text only says that two things are related ("has", "is assigned to", "manages", "works for", "uses"), use a plain association, not a composition.
  - When the text says that an X "is a", "is a kind of" or "can be either" a Y, model a generalization from the subclasses to the superclass, not an association.
  {generalization_direction}
  ```
  Riga del verso, PlantUML: `- In PlantUML the arrow of a generalization points from the subclass to the superclass:
  write "Subclass --|> Superclass" (e.g. "Guitar --|> Instrument"), never "Superclass --|> Subclass".`; compatto: `- In
  "inheritance" and "realization", "child" is always the subclass (or the implementing class) and "parent" the
  superclass (or the interface), e.g. {"type": "inheritance", "child": "Guitar", "parent": "Instrument"}.`
- **sha256** (file con a capo LF, protetti con `-text` in `.gitattributes` come da voce 68):
  `targeted_rules_block.txt` = `211d70938f1ee7a162c41ca0221a69adb86f1cc32ef2ca3117eab9326fcc8b91`;
  `targeted_rules_direction.yaml` = `5b4f93fca515efefe9f99207bc86b6ad8db69f51b4b1c3c2b603807551bd108a`; blocco reso
  (UTF-8, senza a capo finale) PlantUML `1e3d96e723e53be16b41de9b5c5f1311b68b7605dc199dbbe985c4b94072a5ee`, compatto
  `4bcdd9a2740d877f6c57aec9968f7f5a25615a26dff8db7e7a4928c2e74f2a05` (il runner registra lo sha256 del blocco reso
  nella provenienza delle run con istruzioni mirate). Verificati dai test.
- **Esempio**: nuovamente verificato che né "Guitar" né "Instrument" compaiono come classe o nel testo di uno qualsiasi
  dei 79 esercizi (corpus e test set) e che non ne derivano.
- **Prompt** (`generation/prompt_builder.py`): `PromptSpec.instructions_variant` "base" (default: tutti i prompt
  esistenti invariati; verificato: i prompt di `dev_k` a k = 3 ricostruiti coincidono con il `prompt_sha256` del
  manifest in 20/20 per formato) o "targeted" (blocco inserito subito prima dell'ultimo paragrafo, "Your output must be
  ...", separato da una riga vuota; solo per PlantUML e compatto). Il runner legge `prompt.instructions_variant`.
  **Diff baseline / trattamento**: solo il blocco (11 righe) più una riga vuota, nessuna riga tolta o cambiata, in
  20/20 prompt per formato a k = 3.
- **Budget dei token** (stima cl100k_base, 20 esercizi, k = 3): blocco 365 token in PlantUML e 373 nel compatto; prompt
  PlantUML da 2.778 / 3.563 / 4.365 a 3.143 / 3.928 / 4.730 (min / mediana / max), compatto da 3.295 / 4.169 / 4.931 a
  3.668 / 4.542 / 5.304. Caso peggiore con il fattore prudente 1,239: 6.572 + 4.096 = 10.668 su 32.768.
- **Decisione metodologica**: se il blocco viene adottato, si applica **identico a TUTTE le condizioni del Passo 3b**
  (zero-shot, statico, random, retrieval); la baseline statica diventa **"ispirata a De Bari"** e non più una replica
  esatta del prompt dello studio 2025; lo scostamento va dichiarato in tesi e segnalato ai relatori (domanda 9,
  STATUS.md).
- **Metrica M** (concordata): relazioni accoppiate come in `analyze_pilot.compare_relations`, molteplicità
  normalizzate (n → *, 0..* = *), esclusi gli estremi di generalizzazione e realizzazione. **M primaria** = estremi del
  GT con molteplicità ESPLICITA per cui la risposta ha la stessa molteplicità, su tutti gli estremi espliciti del GT di
  TUTTE le risposte (risposta non valida o relazione non trovata = 0); **M secondaria** = lo stesso su tutti gli estremi
  del GT.
- **REGOLA DI ADOZIONE (invariata, registrata PRIMA della run)**: per ciascun formato, con delta = trattamento −
  baseline su 40 risposte, **adottare se (dM_primaria ≥ 0,05 OPPURE dR ≥ 0,03) E dR ≥ −0,03 E dVc ≥ −2**. Controllo
  preliminare: baseline e trattamento completi, senza ragionamento, del modello del config, altrimenti il formato non
  si decide. Se l'esito è diverso tra i formati si adotta per il formato in cui passa e lo si segnala.
- **Esperimento** (`experiments/configs/dev_instructions.yaml`): Gemma 4 12B QAT, versione di configurazione 2, bm25
  k = 3, formati PlantUML e compatto, `instructions_variant: targeted`, 2 ripetizioni, **80 generazioni**; identica alla
  baseline (risposte a k = 3 di `dev_k`) in esercizi, esempi, parametri e seed (42, 43). **Script**
  `experiments/analyze_instructions.py`, scritto e testato PRIMA della run, anche sulla baseline reale: Gemma a k = 3
  con il GT attuale, PlantUML V 40, Vc 40, J 0,544, R 0,307, M primaria 0,282 (137/486), M secondaria 0,248 (137/552);
  compatto V 39, Vc 34, J 0,529, R 0,310, M primaria 0,214 (104/486), M secondaria 0,188 (104/552). Test
  (`check_instructions`): sha256 del blocco, variante base invariata, diff solo del blocco, config, regola con soglie
  incluse, M su un caso costruito, trattamento identico alla baseline (non adottato), trattamento perfetto per un
  formato (adottato, esito diverso segnalato), trattamento incompleto (non decidibile). **Da qui la regola e M nel
  codice non si modificano senza una nuova voce.**

### [2026-10-09] Correzione del GT di eHome2020: lato del rombo della composizione Apartment / Room
- **Verifica sull'immagine originale** (`corpus/raw/models_original/eHome2020/extramaterial/eHome2020.jpg`): il rombo
  pieno della composizione sta su **Wohnung (Apartment)**, con molteplicità 1, e il lato **Raum (Room)** ha 2..*;
  description.md: "An apartment has an address and consists of at least two rooms". Il PlantUML trascritto aveva `Room
  "2..*" *-- "1" Apartment` (rombo su Room): errore di trascrizione confermato (emerso dall'analisi degli errori, voce
  96).
- **Correzione** con il processo consueto (`corpus/corrections/eHome2020.yaml`, `replace_line`, categoria
  `correzione_errore`): `Apartment "1" *-- "2..*" Room`; molteplicità invariate, cambia solo il tutto della composizione.
  Rigenerati `corpus.jsonl`, `processed/apollon/eHome2020.json` e `diff_report.md` (da 618 a 619 differenze). Verificato
  con gli sha256 di tutto `corpus/` prima e dopo: cambiano solo questi file e la correzione nuova; in `corpus.jsonl`
  cambia solo il record eHome2020 (campi `diagram_plantuml`, `corrections_applied`, `diagram_apollon_json`). Tutte le
  suite di test e i controlli di sanità verdi. Il test set e il tag `testset-v1` non sono toccati. Documentata in
  `corpus/README.md`.
- **Effetto sui confronti**: a k = 3 eHome2020 non è mai tra gli esempi recuperati per i 20 esercizi di sviluppo (né
  nella baseline reale: 0 chiamate su 80), quindi i prompt della baseline e del trattamento non cambiano; cambia solo il
  GT di eHome2020 come esercizio. Metriche della baseline `dev_k` Gemma k = 3 ricalcolate con lo stesso script: V, Vc, J,
  R e M **invariati**; cambia solo il verso (composizioni: 2 in più con il verso giusto per formato; verso uguale
  PlantUML da 19/33 a 21/33, compatto da 44/46 a 46/46). A k = 5 e k = 8 eHome2020 era un esempio per Ebike nelle run di
  `dev_k` (con il GT vecchio): fatto storico, run e `dev_k_analysis/summary.md` non toccati (rigenerare quel report ora
  cambierebbe le cifre di eHome2020 come esercizio: va dichiarato se lo si rigenera).

### [2026-10-09] Report grafico di revisione delle generazioni (experiments/review_report.py)
- **Scopo**: rivedere visivamente le risposte già salvate rispetto al GT. Pagina HTML unica e autonoma (SVG incorporati
  come immagini `data:`, nessuna risorsa esterna, nessuno script), apribile offline. Solo lettura: nessuna modifica a
  post-processing, validatori o metriche; validazione come il runner (`analyze_dev.validate`, PlantUML con la versione
  registrata nella provenienza; `postprocess.validate_response` per l'Apollon completo).
- **Rendering**: GT e risposte valide → struttura comune (`uml_structure.structure_from_apollon`) → espansore → PlantUML
  canonico (`plantuml_format.apollon_to_plantuml`) → SVG con `plantuml.jar` locale (una sola JVM per tutti i diagrammi)
  e `!pragma layout smetana` (niente Graphviz, niente server online). Classi colorate: verde = nel GT, arancione = in più.
  Jar: `.tools/plantuml-old.jar` = PlantUML **1.2023.0**, sha256
  `0404edcf0af28e5b409bc17aa59ad8b05051f47347377749c46c8018135d0dec`, compatibile con Java 8 (installato: 1.8.0_421);
  non versionato (`.tools/` è in `.gitignore`), dettagli in STATUS.md. `.tools/plantuml.jar` (più recente, sha256
  `5e1ecfa8…`) richiede Java 11 e qui non parte.
- **Confronto** (funzioni esistenti, non riscritte): classi con `analyze_pilot.class_names`; relazioni con
  `analyze_instructions.match` (accoppiamento 1:1 di `compare_relations`), `gt_ends`, `resp_mult`; categorie: corretta /
  tipo sbagliato / direzione invertita / molteplicità diverse / mancante / in più. Metriche per risposta V, Vc, J, R, M
  (stesse definizioni delle analisi, 0 per le non valide); indice con le medie per esercizio e condizione. Risposte non
  valide: niente diagramma, testo grezzo e livello raggiunto.
- **Verifica** su `dev_k` Gemma k = 3 (`--runs dev_k__P-G dev_k__C-G --filter k=3 --name dev_k_gemma_k3`): 80 risposte
  (1 non valida), 99 diagrammi resi su 99 (20 GT + 79 risposte valide), rendering 4,4 s, HTML 3,59 MB (SVG medio 25 KB),
  nessun errore di sintassi. I conteggi delle relazioni letti dall'HTML coincidono con `compare_relations` ricalcolato
  dalle risposte grezze in 80/80 schede (stessa coppia, stesso tipo, mancanti, in più; a campione Boeing, Facepage e
  TruckLogistics); R aggregato dalla pagina 0,307 (PlantUML) e 0,310 (compatto), uguale a `dev_k_analysis`. Il verso
  differisce da `dev_k_analysis` solo per eHome2020, per la correzione del GT (voce 99). Test: `check_review`.

### [2026-10-09] Istruzioni mirate, STOP 3: la regola della voce 98 NON le adotta in nessuno dei due formati
- **Run** `dev_instructions__P-G` e `__C-G` (80 generazioni, 2026-10-09 12:50-13:07, Gemma 4 12B QAT caricato con `lms
  load google/gemma-4-12b-qat -c 32768 --parallel 4 --gpu max`, impostazioni salvate del modello; contesto e Flash
  Attention verificati dal runner; nessun ragionamento, nessuna risposta troncata). Provenienza: commit `3017a8c` con
  modifiche NON committate (`worktree_dirty: true`: le modifiche di queste voci non erano ancora committate, per
  richiesta dell'utente), `instructions_variant: targeted`, sha256 del blocco reso come nella voce 98. Report:
  `data/results/generation/dev_instructions_analysis/summary.md`; baseline = `dev_k` Gemma k = 3, GT corretto (voce 99).
- **Esito della regola (applicata meccanicamente)**:

  | formato | V | Vc | J | R | M primaria | M secondaria | dM_primaria | dR | dVc | esito |
  |---|---|---|---|---|---|---|---|---|---|---|
  | PlantUML base / mirate | 40 / 40 | 40 / 40 | 0,544 / 0,551 | 0,307 / 0,312 | 0,282 / 0,284 | 0,248 / 0,254 | +0,002 | +0,006 | 0 | **non adottate** (nessun guadagno) |
  | compatto base / mirate | 39 / 39 | 34 / 34 | 0,529 / 0,520 | 0,310 / 0,273 | 0,214 / 0,222 | 0,188 / 0,196 | +0,008 | −0,037 | 0 | **non adottate** (nessun guadagno e R peggiora di oltre 0,03) |

- **Che cosa è cambiato** (tabelle di confusione, solo descrittive, n = 40 per parte):
  - **errore `*` → `1..*`** (il bersaglio principale della regola sul limite inferiore): da 18 a 13 in PlantUML e **da
    28 a 6 nel compatto**; ma M primaria sale di poco (+1 e +4 estremi) perché crescono altri errori, soprattutto nel
    compatto (`1` → vuoto da 6 a 10, `*` → vuoto da 4 a 8, `1` → `*` da 6 a 9);
  - **generalizzazioni** in PlantUML: accoppiate come generalizzazione da 27 a 34, rese come associazione da 9 a 4; ma
    il **verso resta sbagliato** (invertite 12/27 → 13/34): la riga del verso non ha corretto la convenzione della
    freccia. Nel compatto il verso era già giusto (0/40 → 0/40);
  - **composizione**: la regola NON ha ridotto l'uso eccessivo; associazione → composizione 12 → 12 in PlantUML e 18 → 22
    nel compatto; nel compatto le associazioni accoppiate come associazione scendono da 63 a 47, ed è la causa del calo
    di R;
  - **errori nuovi**: generalizzazioni in più (assenti dal GT) da 33 a 36 in PlantUML e da 23 a 29 nel compatto; classi
    in più quasi invariate (122 → 120, 124 → 119); scarti del compatto da 9 a 15; risposte del compatto più lunghe
    (completamento mediano 552 → 632 token, latenza 14,5 → 18,8 s).
- Conseguenza secondo le voci 97-98: il blocco NON entra nelle condizioni del Passo 3b e il prompt statico resta quello
  dello studio 2025 adattato (la nota alla domanda 9 resta condizionata all'adozione). In attesa della decisione
  dell'utente sul seguito (lo STOP 3 non decide altro).

### [2026-10-09] Runbook in notebook, registro automatico delle esecuzioni e storico ricostruito
- **Registro** `experiments/run_log.py` → `data/results/run_log.jsonl` (**versionato**: eccezione aggiunta in
  `.gitignore`). Ogni esecuzione da riga di comando di `run_experiment.py`, `calibrate_tokens.py`, `analyze_pilot.py`,
  `analyze_pilot2.py`, `analyze_dev.py`, `analyze_k.py`, `analyze_instructions.py`, `select_pilot.py`, `select_dev.py`,
  `review_report.py`, `retrieval/analyze_retrieval.py` e `retrieval/run_testset.py` scrive due righe con lo stesso id:
  inizio (timestamp, comando completo, commit, flag di modifiche non committate, `--resume`, sha256 di
  `config_bm25.yaml`, dei template e del blocco delle istruzioni in `generation/templates/` e di ogni .yaml del comando)
  e fine (durata, status "ok" / "exit <codice>" / "interrupted" / "error: <tipo>", messaggio di uscita, output
  dichiarato con `set_output`). Solo logging: il registro si aggancia al punto d'ingresso `__main__` (i test che chiamano
  `main()` non scrivono nel registro), rilancia sempre l'eccezione o il `SystemExit` originale, e un errore di scrittura
  produce solo un avviso. `RUN_LOG_PATH` sposta il registro (usato dai test). Test: `check_run_log`.
- **Storico** `docs/runbook_history.md`: comando, data, commit, cartella e voce per ogni run fatta prima del registro.
  Run di generazione: **tutte e 17 verificate** (il config attuale risolto con la stessa `--configuration` è identico a
  quello salvato nella run); riprese con `--resume` da `server_checks.jsonl` (pilot2 P-G e J-G) o da decisions.md (primo
  pilota). **Ricostruiti, non verificati**: le calibrazioni (la `--configuration` digitata non è registrata; ogni
  configurazione dello stesso modello dà lo stesso calcolo), gli smoke test 1-2 di Gemma (prove manuali), la calibrazione
  interrotta del 14B, le run del retrieval (`--run-id` dedotto dal nome).
- **Notebook** `notebooks/runbook.ipynb` (generato senza output; 28 celle): setup e verifica dell'ambiente (versioni,
  plantuml.jar, git, LM Studio in sola lettura) → test e controlli di sanità → retrieval → selezioni → esperimenti di
  sviluppo (una sezione per esperimento: pilota temperatura, pilota 2, dev_formats, dev_k, dev_instructions) → analisi
  → report grafico → Passo 3b. Helper `run(cmd)`: lancia `python <cmd>` dalla radice, mostra l'output in streaming e
  registra eventi `notebook_start` / `notebook_end` (in più alle righe dello script). Sicurezze: `ESEGUI_GENERAZIONI =
  False` (le celle con l'LLM stampano il comando); rifiuto se la cartella di output esiste, salvo `--resume`;
  `SBLOCCA_TESTSET = False` (la sezione 3b non fa nulla) e `run()` rifiuta FUORI dalla sezione 3b ogni comando che
  produce risultati sul test set (`retrieval/run_testset.py`, `retrieval/hubness_report.py`, config con `split:
  testset`, compreso `mock_e2e.yaml`, che non ha `split` e quindi usa il test set). **Eccezione dichiarata**: le suite di
  test e i controlli di sanità leggono i ground truth del test set solo per verificare il codice, come dal Passo 1.
  Le analisi riscrivono i `summary.md` versionati.
- **nbstripout**: `python -m nbstripout --install --attributes .gitattributes` (riga `*.ipynb filter=nbstripout` in
  `.gitattributes`; la configurazione del filtro sta in `.git/config`, da ripetere su ogni clone). Aggiunti a
  `requirements.txt`: nbformat, nbclient, nbstripout (installati: 5.11.1, 0.11.0, nbstripout).
- **Verifica "Run All"** (nbclient, interruttori a False, copia eseguita nello scratchpad, notebook versionato senza
  output): completato in 131 s senza errori; test e controlli di sanità verdi; retrieval storico rifiutato (cartella
  esistente); nessuna generazione, calibrazione o chiamata all'LLM (solo i comandi stampati); sezione 3b bloccata; `raw/`
  intatti (1.006 file, sha256 invariati), nessuna cartella di run nuova. Le analisi rigenerate differiscono dai report
  versionati SOLO per la riga del commit e per gli effetti della correzione di eHome2020 (voce 99): colonna del verso in
  `dev_formats_analysis` e `dev_k_analysis` (14 righe di `dev_k`, solo quella colonna, verificato), colonna esplorativa
  "token degli esempi" di ApartmentBuilding nel primo pilota (eHome2020 è tra i suoi esempi). I report versionati sono
  stati riportati alla versione del commit dopo la verifica (quelli storici restano com'erano); rigenerarli va deciso e
  dichiarato.
- **Trovati e corretti durante la verifica**: (1) le tabelle di confusione di `analyze_instructions.py` avevano un
  ordinamento instabile a parità di conteggio (dipendeva dall'hash delle stringhe, variabile tra processi): aggiunta la
  chiave come spareggio (solo presentazione; regola e M invariati; verificato identico con tre `PYTHONHASHSEED`), e il
  report `dev_instructions_analysis` è stato rigenerato (numeri invariati); (2) il primo "Run All" ha registrato il
  notebook come `notebooks/notebooks/runbook.ipynb` (percorso relativo risolto da `notebooks/`): corretto con il
  percorso assoluto; le **30 righe** già scritte con `script: notebooks/notebooks/runbook.ipynb` (eventi
  `notebook_start` / `notebook_end` del primo "Run All", 2026-10-09 13:17-13:19) restano INVARIATE: il registro è
  append-only e non si corregge a posteriori; il percorso giusto è `notebooks/runbook.ipynb`.
- **Verifica dal terminale**: `python experiments/analyze_k.py` e `python experiments/analyze_pilot2.py` scrivono le
  due righe attese (commit, modifiche non committate, 10 file di configurazione con sha256, esito "ok", output
  `.../summary.md`); `analyze_pilot2` identico salvo la riga del commit, `analyze_k` identico salvo la riga del commit e
  la colonna del verso (eHome2020).

### [2026-10-09] Istruzioni mirate chiuse: blocco fuori dalla pipeline, configurazione di lavoro invariata, nessuna iterazione
- **STOP 3 approvato dall'utente**: istruzioni mirate NON adottate per nessun formato (esito meccanico della regola,
  voce 101).
- **Il blocco non entra nella pipeline.** `generation/templates/targeted_rules_block.txt` e
  `targeted_rules_direction.yaml` restano nel repository, congelati con i loro sha256 (voce 98), SOLO come
  documentazione dell'esperimento; la variante `instructions_variant: targeted` resta disponibile nel codice per
  riprodurre `dev_instructions`, ma nessun config di lavoro la usa.
- **Configurazione di lavoro invariata** (STATUS.md): Gemma 4 12B QAT, versione di configurazione 2 (contesto 32768,
  max_tokens 4096), temperature 0.3, top_p 0.95, top_k 64, bm25 k = 3 (più k = 2 nel Passo 3b), formati PlantUML e JSON
  compatto, **prompt senza il blocco** (`instructions_variant: base`).
- **Domanda 9**: decade lo scostamento annunciato nella voce 97 (blocco applicato a tutte le condizioni): il prompt della
  baseline statica resta quello attuale, cioè il prompt v3 dello studio 2025 (Garaccione et al.) adattato ad Apollon
  v4 come descritto nella domanda 9; nessuno scostamento in più da dichiarare. (Nota di precisione: la richiesta
  dell'utente parlava del prompt "di De Bari"; secondo la domanda 9 e la voce 55 la baseline statica deriva dallo
  studio 2025, non da De Bari et al., che usavano PlantUML e un prompt diverso.)
- **Nessuna iterazione sul blocco**: niente varianti successive valutate sullo stesso insieme di sviluppo, per non
  adattare il prompt ai 20 esercizi di sviluppo. Un'eventuale ripresa della leva richiede un insieme di valutazione
  diverso e una nuova voce.

### [2026-10-09] Test e controlli di sanità: lettura dei GT del test set solo per verificare il codice
- Le suite di test (`corpus/test_apollon_convert.py`, `retrieval/test_retrieval.py`, `generation/test_generation.py`) e i
  controlli di sanità (`generation/sanity_check.py`, `plantuml_sanity_check.py`, `compact_sanity_check.py`) leggono i
  ground truth del test set De Bari **solo per verificare il codice** (conversione PlantUML ↔ Apollon, validazione contro
  lo schema, struttura comune e formato compatto, separazione degli split). Restano come sono (decisione dell'utente).
- **Nessuna generazione, metrica o output del modello sul test set prima del Passo 3b.** Nel runbook
  (`notebooks/runbook.ipynb`) i comandi che producono risultati sul test set sono eseguibili solo dalla sezione 3b con
  `SBLOCCA_TESTSET = True` (voce 102); le uniche esecuzioni già fatte sul test set sono quelle del retrieval del Passo 2
  (`testset_2026-10-04_stop2`, voce 60), che non coinvolgono un modello generativo.

### [2026-10-09] Rigenerazione dei 5 report versionati con il GT corretto di eHome2020: nessun esito cambia
- **Rigenerati** (comandi da terminale, registrati in `data/results/run_log.jsonl`): `analyze_pilot.py`,
  `analyze_pilot2.py`, `analyze_pilot2.py --postprocess v2`, `analyze_dev.py`, `analyze_k.py`. In testa a ciascun
  `summary.md` una nota "Rigenerato il 2026-10-09 dopo la correzione del GT di eHome2020 (voce 99; rigenerazione: voce
  105)" con il dettaglio di ciò che cambia (la nota è aggiunta dopo la generazione: una nuova rigenerazione la toglie).
- **Che cosa cambia** (confronto con la versione committata, esclusa la riga "Analisi eseguita sul commit ..."):
  - `pilot_temperature_gemma4-12b-qat`: solo la colonna esplorativa "esempi: token" di ApartmentBuilding, 4.382 → 4.379 (7
    righe), perché eHome2020 è tra i suoi esempi e la dimensione si ricalcola dal corpus attuale;
  - `pilot2_formats_analysis` e `pilot2_formats_analysis_v2`: nessun numero (eHome2020 non è tra gli esercizi);
  - `dev_formats_analysis`: solo le colonne del verso nella tabella delle relazioni, +2 per configurazione (stesso
    verso P-G 26/43 → 28/43, P-Q 14/16 → 16/16, C-G 44/46 → 46/46, C-Q 13/16 → 15/16; composizione / aggregazione 4/6 →
    6/6, 0/2 → 2/2, 4/6 → 6/6, 2/4 → 4/4);
  - `dev_k_analysis`: solo la colonna "verso uguale" (14 righe): PlantUML Gemma 21/42 → 23/42, 19/33 → 21/33, 27/33 →
    29/33, 26/40 → 28/40 (k = 2, 3, 5, 8); PlantUML Qwen 12/16 → 13/16, 15/17 → 17/17 (k = 2, 3); compatto Gemma 42/44 →
    44/44, 44/46 → 46/46, 50/52 → 52/52, 44/45 → 45/45; compatto Qwen 17/19 → 19/19, 20/21 → 21/21, 13/14 → 14/14, 15/17 →
    17/17.
- **Esiti delle regole pre-registrate: TUTTI invariati** (verificato riga per riga): voce 75 (primo pilota: STOP per
  troncamenti), voce 78 (secondo pilota: P-Q e classifica completa), voce 92 (`dev_formats`: esito, tabelle dei criteri
  e vincitori per modello; il verso non entra nella regola), voce 94 (`dev_k`: PlantUML k = 2, compatto "dipende dal
  modello", k scelto per ogni formato e modello identico; colonne della regola, ammissibile / Vc / R, invariate). Nessuno
  STOP.
- **Effetto sulle cifre descrittive della voce 95** (non modificata): con il GT corretto il verso delle relazioni nel
  compatto con Gemma è **100%** a ogni k (44/44, 46/46, 52/52, 45/45; prima 95-98%) e in PlantUML va dal **55% all'88%**
  (prima 50-82%). La conclusione della voce 95 (verso molto migliore nel compatto) è confermata.

### [2026-10-09] Riga di provenienza automatica nei report: commit e impronta del GT
- `experiments/provenance.py`: `provenance_line()` scrive in testa ai report "Analisi eseguita sul commit `<hash>` (con
  modifiche non committate). GT del corpus: 59 diagrammi, sha256 del contenuto `<impronta>` (JSON canonico dei
  `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `<16 cifre>…`".
  L'impronta è lo sha256 del JSON canonico (chiavi ordinate, separatori compatti, UTF-8) di {id: diagramma} dei record
  del corpus: non dipende dagli a capo del checkout (lo sha256 dei byte del file invece sì, voce 68, ed è riportato solo
  per informazione). Impronta attuale (GT con eHome2020 corretto): `b400d1dd7954e8a97c88ff604bc47f294e7eca2cb17d9cd7dd680542fd5db5fd`.
- Usata da `analyze_pilot.py`, `analyze_pilot2.py`, `analyze_dev.py`, `analyze_k.py`, `analyze_instructions.py`,
  `review_report.py` e `retrieval/analyze_retrieval.py` (al posto della vecchia riga del commit, che si ripeteva in ogni
  script). **Sostituisce le note manuali** "Rigenerato … dopo la correzione del GT di eHome2020" della voce 105: i 6 report
  di analisi sono stati rigenerati (registrati nel registro delle esecuzioni) e, salvo la riga di provenienza e la nota
  tolta, sono identici riga per riga alla versione precedente (verificato). La run del retrieval
  `loo_2026-10-04_stop1` NON è stata rigenerata (ricreerebbe la cartella della run): la riga comparirà nelle run nuove.
- Test (`check_provenance`): impronta indipendente dall'ordine dei record e dagli a capo (corpus riletto in CRLF),
  sensibile a una modifica del GT; riga con commit e numero di diagrammi. Suite della generazione e del retrieval verdi.

### [2026-10-09] Retriever denso e ibrido: APPROVATA (FASE 1, STOP 1), solo retrieval sul corpus, test set escluso
- **Perimetro**: implementazione e valutazione SOLO come retriever, in leave-one-out sul corpus (59 query, stesse
  esclusioni della valutazione di BM25, voci 57-59); nessuna generazione; il test set NON si tocca (nemmeno per il solo
  retrieval). BM25 resta congelato (`retrieval/config_bm25.yaml`).
- **1a. Lunghezza dei testi** (campo `description`, lo stesso indicizzato da BM25; tokenizer reali scaricati da Hugging
  Face, solo i file del tokenizer e dei metadati, nessun peso): vocabolario BERT (all-MiniLM-L6-v2, bge-small-en-v1.5,
  e5-small-v2, nomic-embed-text-v1.5) mediana 289 token, massimo 814; **53 descrizioni su 59 superano 128 token, 37
  superano 256, 12 superano 512**; vocabolario ModernBERT mediana 297, massimo 798. Quindi all-MiniLM-L6-v2 (limite 256)
  troncherebbe in silenzio **37 testi su 59 (63%)**, i modelli a 512 token **12 su 59 (20%)**, i modelli a 8192 nessuno.
  (Il minimo di 128 misurato con il tokenizer di all-MiniLM è un artefatto del padding attivo nel suo `tokenizer.json`;
  i conteggi sopra 128 non ne dipendono.)
- **1b. Modelli candidati (3)**, dati letti dai metadati del repository alla revisione indicata (il numero di parametri
  è derivato dalla dimensione dei pesi float32):

  | modello | revisione HF | licenza | pesi | parametri (circa) | limite di token | prefissi | testi troncati | ruolo |
  |---|---|---|---|---|---|---|---|---|
  | `sentence-transformers/all-MiniLM-L6-v2` | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` | Apache-2.0 | 91 MB | 22,7 M (6 strati, 384) | 256 | nessuno | 37/59 | riferimento classico |
  | `BAAI/bge-small-en-v1.5` | `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` | MIT | 133 MB | 33 M (12 strati, 384) | 512 | istruzione solo per query brevi verso passaggi lunghi ("Represent this sentence for searching relevant passages: "); qui query e documenti sono testi dello stesso tipo, quindi **nessun prefisso** | 12/59 | piccolo, 512 token |
  | `Alibaba-NLP/gte-modernbert-base` | `e7f32e3c00f91d699e8c43b53106206bcc72bb22` | Apache-2.0 | 298 MB | 149 M (22 strati, 768) | 8192 | nessuno | 0/59 | contesto lungo senza codice remoto |

  Tutti in inglese (il corpus è in inglese). **Scartati**: `nomic-ai/nomic-embed-text-v1.5` (8192 token ma richiede
  `trust_remote_code`, cioè l'esecuzione di codice scaricato dal repository: rischio e riproducibilità peggiore);
  `nomic-ai/modernbert-embed-base` (8192, nessun codice remoto, ma 596 MB e prefissi obbligatori: doppione più pesante
  del gte); `intfloat/e5-small-v2` (stessa taglia e stesso limite di bge-small, prefissi "query: " / "passage: "
  obbligatori: non aggiunge un caso diverso).
  **Vincoli di esecuzione**: calcolo su CPU (`device="cpu"`); `sentence-transformers` con versione fissata in
  requirements.txt (insieme a `transformers` ≥ 4.48, richiesto dall'architettura ModernBERT), da installare nella FASE 2
  (oggi non installato; nota: l'ambiente ha già un conflitto `torchaudio` 2.6 / `torch` 2.10 segnalato da pip, da
  controllare all'installazione); revisione del modello passata in modo esplicito (`revision=<hash>`) e registrata nei
  risultati; dopo il primo download esecuzione con `HF_HUB_OFFLINE=1`; pesi nella cache di Hugging Face dell'utente,
  MAI in git. Embedding normalizzati e **similarità coseno esatta con numpy** (59 documenti); **proposta: togliere
  `faiss-cpu` da requirements.txt** (non installato e non necessario). Testo indicizzato: `description`, lo stesso di
  BM25, senza stopword né stemming. Troncamento: nessun spezzettamento; i testi troncati si contano e si riportano per
  ogni modello.
- **1c. Ibrido (proposta principale)**: **Reciprocal Rank Fusion** tra BM25 congelato e il modello denso scelto, costante
  standard **60**: punteggio(d) = 1 / (60 + rango_BM25(d)) + 1 / (60 + rango_denso(d)), ranghi da 1 sull'ordinamento
  completo dei 58 candidati della query (leave-one-out); parità risolta per id. Nessun parametro da tarare.
  **Alternativa scartata**: combinazione pesata α · score_BM25_norm + (1 − α) · coseno, che richiederebbe di tarare α (e la
  normalizzazione degli score, su scale diverse) sugli stessi 59 esercizi su cui poi si valuta: rischio di adattamento
  al corpus e nessun insieme separato per la taratura.
- **1d. Misure di pertinenza** (sui diagrammi GT di query ed esempio recuperato; **nessun embedding**, né del modello
  valutato né di altri):
  - **J** = Jaccard dei nomi di classe esatti normalizzati (`corpus_loader.class_names`, minuscole e soli caratteri
    alfanumerici): la misura del Passo 2 per BM25, per confronto diretto;
  - **Jt (principale)** = Jaccard dei TOKEN dei nomi di classe: CamelCase spezzato (`ReservationSlot` → reservation,
    slot), minuscole, stemming Snowball inglese (lo stesso stemmer di `retrieval/text_preprocessing.py`); misura
    "morbida" che riconosce nomi parzialmente uguali (`InsurancePolicy` / `Policy`);
  - **S** = similarità del profilo strutturale (descrittiva): vettore dei conteggi (classi, attributi, metodi, e
    relazioni per ciascuno dei 7 tipi Apollon), similarità = 1 − distanza L1 tra le proporzioni dei tipi di relazione,
    più il rapporto min / max del numero di classi; non usa il vocabolario, quindi è neutra rispetto a BM25.
  Nota: J e Jt sono misure lessicali sui nomi del GT e possono favorire BM25 (le descrizioni contengono spesso i nomi
  delle classi); il confronto TRA modelli densi non ne risente. Pertinenza a k = media della misura sui primi k
  recuperati, mediata sulle 59 query (come J@k del Passo 2).
- **1e. Analisi previste** (descrittive, leave-one-out sul corpus): J, Jt e S a k = 1, 2, 3 per BM25, ciascun modello
  denso, l'ibrido (RRF con ciascun denso, descrittivo; quello ufficiale è con il denso scelto), il retriever casuale (20
  seed, media ± deviazione standard) e l'oracolo (massimo raggiungibile, solo riferimento); sovrapposizione dei top-3 tra
  BM25 e ciascun denso (media di |∩| / 3, quota di query con lo stesso top-1); hubness per ciascun retriever (candidati
  distinti al rango 1 e massima frequenza di un candidato nei top-3, come `retrieval/hubness_report.py`); esempi
  qualitativi: le 3 query con la sovrapposizione minima tra BM25 e il denso scelto, con i titoli recuperati; numero di
  testi troncati per modello.
- **1f. Regola di scelta del modello denso (PROPOSTA, da approvare PRIMA dei calcoli)**: dipende SOLO dalla pertinenza sul
  corpus. (1) Si sceglie il modello con il **Jt@3 più alto** (k = 3 è il k di lavoro, voce 95); (2) **pareggio** =
  modelli entro **0,01** dal migliore Jt@3: tra questi vince il **più piccolo** (numero di parametri: MiniLM < bge-small <
  gte-modernbert). Nessun altro criterio (troncamenti, velocità, hubness si riportano soltanto). Il modello scelto entra
  nell'ibrido RRF e, più avanti, nelle generazioni sull'insieme di sviluppo (con una regola a parte).
- **Dopo l'approvazione** (non ora): FASE 2, implementazione di `retrieval/dense_retriever.py` e `hybrid_retriever.py`
  con test su embedding finti (nessun download durante la suite); FASE 3, calcoli, scelta meccanica, report; STOP 2.
- **STOP 1**: proposta registrata prima di implementare (nessun retriever implementato, nessun peso scaricato).
- **APPROVATA (2026-10-09)**, con queste precisazioni (vincolanti):
  1. **Ruolo delle misure**: J, Jt e S servono SOLO a scegliere il modello denso (regola 1f invariata). Il confronto BM25
     / denso / ibrido NON si decide su queste misure (lessicali, favoriscono BM25 per costruzione): si deciderà con le
     generazioni sull'insieme di sviluppo, con una regola scritta prima delle run, in un passo successivo.
  2. **Intervallo bootstrap al 95%** (1000 ricampionamenti delle 59 query con reinserimento, seme fisso 0, percentili
     2,5 e 97,5) della differenza appaiata di Jt@3 tra i due migliori modelli densi e tra il denso scelto e BM25. Solo
     descrittivo: la regola non cambia.
  3. **Pareggi di coseno**: ordinamento per id crescente, come BM25 (`base.rank_results`). **Cache degli embedding del
     corpus** su disco, con nome del modello e revisione nel nome del file, fuori da git.
  4. **Ambiente**: versioni registrate PRIMA dell'installazione: torch 2.10.0, torchaudio 2.6.0+cu124, torchvision
     0.25.0, tokenizers 0.23.3, huggingface_hub 2.2.0 (installato il 2026-10-09 per leggere i tokenizer della FASE 1),
     numpy 2.2.6, scipy 1.16.3, scikit-learn 1.8.0; transformers e sentence-transformers assenti; Python 3.12.10.
     L'installazione di sentence-transformers NON deve cambiare torch (se pip ci prova: stop e segnalazione).
     torchaudio non è usato dal progetto: il conflitto si segnala in STATUS.md, non si risolve toccando torch.
  5. **requirements.txt**: tolto `faiss-cpu`; `sentence-transformers` e `transformers` (>= 4.48) fissati alle versioni
     installate.
  Poi FASE 2 (implementazione e test con embedding finti) e FASE 3 (download alle revisioni fissate, esecuzione offline,
  analisi, regola meccanica), STOP 2.

### [2026-10-09] Retriever denso e ibrido: implementazione, analisi LOO sul corpus ed esito della regola (FASE 2-3, STOP 2)
- **Ambiente** (precisazione 4 della voce 107): `pip install sentence-transformers==6.1.0 transformers==5.19.0`; torch
  INVARIATO (2.10.0, build CPU), nessun tentativo di pip di cambiarlo (verificato prima con `--dry-run`); effetti
  collaterali: huggingface_hub 2.2.0 -> 1.33.0 (richiesto da transformers 5), più httpx, safetensors 0.8.0, typer, rich.
  torchaudio 2.6.0+cu124 (non usato) non si carica con torch 2.10 e transformers 5.19 lo importa se installato: il
  retriever denso lo dichiara non disponibile SOLO nel proprio processo (`_disable_broken_torchaudio`), senza toccare
  l'ambiente; conflitto segnalato in STATUS.md, non risolto. requirements.txt: `faiss-cpu` tolto,
  `sentence-transformers==6.1.0` e `transformers==5.19.0` fissati.
- **Codice (FASE 2)**: `retrieval/dense_retriever.py` (interfaccia di `base.py`; coseno esatto numpy su embedding
  normalizzati; `revision` esplicita, `device="cpu"`, `trust_remote_code=False`; parità per id; cache su disco in
  `data/cache/embeddings/<modello>@<revisione[:12]>.npz`, indicizzata dallo sha256 del testo, fuori da git);
  `retrieval/hybrid_retriever.py` (RRF, c = 60, ranghi sui candidati non esclusi, score_norm = score / (2 / 61));
  `retrieval/relevance.py` (J, Jt, S; S = media di 1 − distanza di variazione totale tra le proporzioni dei 7 tipi di
  relazione e del rapporto min / max del numero di classi); `retrieval/config_dense.yaml` (modelli, revisioni, regola);
  `retrieval/download_dense_models.py` (download unico, solo i file PyTorch: niente ONNX / OpenVINO / TF);
  `retrieval/analyze_dense.py` (offline, `HF_HUB_OFFLINE=1` obbligatorio). Test in `retrieval/test_retrieval.py` con
  embedding finti (nessun download, sentence-transformers mai importato): cache per modello e revisione, parità per id,
  RRF a mano, misure a mano, regola, bootstrap, sovrapposizione, hubness. Suite del retrieval e della generazione verdi.
- **Esecuzione (FASE 3)**: download alle revisioni fissate (92, 135, 302 MB nella cache di Hugging Face dell'utente),
  poi analisi offline: run `data/results/retrieval/dense_2026-10-09_22f5adf/` (summary.md, config.json, relevance.csv,
  top3.csv, hubness.csv). Rieseguita una seconda volta (la prima si era fermata DOPO aver scritto i file, sulla stampa
  in console di "−" in cp1252; corretto): `relevance.csv` e `top3.csv` identici byte per byte. Il test set NON è stato
  letto (solo `load_candidates`). Controllo di coerenza: BM25 riproduce la run congelata (J@1 0,096, J@3 0,067).
- **Risultati (LOO, 59 query)**, Jt@3: casuale 0,018 ± 0,002; BM25 0,083; all-MiniLM-L6-v2 0,0697; gte-modernbert-base
  0,0685; bge-small-en-v1.5 0,0683; ibrido RRF (BM25 + MiniLM) 0,081; oracolo 0,120. J@1: BM25 0,096, MiniLM 0,087, bge
  0,073, gte 0,067, ibrido 0,093. S è poco discriminante (casuale 0,61, tutti i retriever 0,64-0,67, oracolo 0,90).
- **Esito della regola (meccanico)**: i tre modelli sono entro 0,0014 di Jt@3, quindi **tutti in parità** (soglia
  0,01) e vince il più piccolo: **`sentence-transformers/all-MiniLM-L6-v2` @ `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`**.
  Bootstrap al 95% (1000 ricampionamenti, seme 0, descrittivo): MiniLM − gte-modernbert +0,0012 [−0,0044, +0,0066];
  MiniLM − BM25 −0,0137 [−0,0212, −0,0063]. **Da notare**: la scelta la decide di fatto il criterio di parità (i modelli
  non si distinguono con questa misura), e MiniLM tronca 37 descrizioni su 59 a 256 token (vede solo l'inizio del
  testo). Che i densi stiano sotto BM25 su J e Jt è atteso (misure lessicali, voce 107 precisazione 1) e NON decide il
  confronto tra retriever, che resta alle generazioni sull'insieme di sviluppo con una regola da scrivere prima.
- **Descrittivo**: sovrapposizione dei top-3 con BM25 0,41 (MiniLM), 0,44 (bge), 0,36 (gte); stesso top-1 46%, 46%,
  36%. Hubness: gte concentra molto (TransportCompany 17 volte nei top-3 e 8 al rango 1; 15 candidati mai nei top-3),
  MiniLM 2 mai nei top-3, BM25 5. Tempi su CPU (8 thread) per le 59 descrizioni: MiniLM circa 1 s, bge circa 2,8 s, gte
  circa 105 s (1,8 s per testo).
- **STOP 2**: in attesa dell'utente. Nessuna generazione; nessuna modifica a BM25, al prompt o alla configurazione di
  lavoro (voce 95).
- **STOP 2 APPROVATO (2026-10-09)**. Modello denso: **all-MiniLM-L6-v2, scelto per spareggio** (i tre densi sono in
  pareggio su Jt@3; bootstrap MiniLM − gte [−0,0044; +0,0066]).

### [2026-10-09] Retriever come fattore sperimentale: controllo di funzionamento sul dev set e run oracolo — APPROVATA (STOP A)
- **Decisione metodologica**: il tipo di retriever è un **fattore sperimentale** (domanda di ricerca), non un parametro
  da tarare. **BM25, MiniLM (all-MiniLM-L6-v2 @ `1110a243`, voce 108) e ibrido RRF entrano TUTTI nel Passo 3b** come
  condizioni a confronto. Sull'insieme di sviluppo **non si sceglie un vincitore**: solo un controllo di funzionamento.
- **Configurazione** (`experiments/configs/dev_retrievers.yaml`): Gemma 4 12B QAT, versione di configurazione 2
  (contesto 32768, max_tokens 4096), temperatura 0,3, top_p 0,95, top_k 64, k = 3, formati PlantUML (P-G) e compatto
  (C-G), 2 ripetizioni, gli stessi 20 esercizi di sviluppo (voce 92), prompt SENZA blocco di istruzioni mirate (voce
  100). Condizioni nuove del prompt builder: `dense` (MiniLM; il più simile per ultimo, come bm25), `hybrid` (RRF c = 60
  tra BM25 congelato rifittato senza la query e MiniLM; il più simile per ultimo), `oracle_jt` (vedi sotto). La
  condizione `oracle` esistente (Jaccard esatto, voce del Passo 3a) resta invariata e non si usa qui. Totale 3 condizioni
  × 2 formati × 20 × 2 = **240 generazioni**. **Baseline** = run di Gemma a k = 3 di `dev_k` (bm25, stessi parametri,
  esercizi ed esempi), ricalcolata con il GT corretto.
- **Regola di ESCLUSIONE (per formato)**: MiniLM o l'ibrido sono **esclusi dal Passo 3b in quel formato** se, rispetto a
  BM25 k = 3 (baseline):
  - **Vc peggiora di più di 4 su 40** (Vc(retriever) < Vc(BM25) − 4, cioè una perdita di 5 o più risposte), oppure
  - compare **anche un solo troncamento per max_tokens** (finish_reason `length`) o **un prompt oltre il budget di
    contesto**.
  **Nessun criterio su R, J o M**: le differenze sono attese piccole e verranno valutate nel 3b. Controllo preliminare
  (come voce 98): baseline e condizione complete (40 risposte per formato), senza ragionamento, del modello del config;
  altrimenti quel formato non si decide e lo si segnala.
- **Run ORACOLO** (`oracle_jt`): sceglie i k = 3 esempi con **Jt massimo** (voce 107: Jaccard dei token dei nomi di
  classe) rispetto al GT della query, in leave-one-out (gli altri 58 candidati), **pareggi per id crescente**, il più
  simile per ultimo. **Solo diagnostica, MAI nel 3b** (usa il GT della query). Interpretazione fissata prima:
  - se **R(oracolo) − R(BM25) < 0,03 in entrambi i formati** → "la qualità del retrieval non è il collo di bottiglia con
    questo corpus e questo modello";
  - se **≥ 0,03 in almeno un formato** → "un retrieval migliore avrebbe margine"; si riporta il valore senza trarne
    scelte per il 3b.
- **Prima delle run (dopo il via)**: lunghezza dei prompt per dense, hybrid e oracle_jt con `context_budget.py` (massimo
  rispetto al budget); diff dei prompt con la baseline su 1 esercizio per formato e per condizione (devono differire
  SOLO negli esempi recuperati); verifica che l'oracolo non recuperi mai la query e rispetti il leave-one-out; script di
  analisi (riuso di `analyze_k.py` / `analyze_instructions.py`) testato sulla baseline PRIMA delle run.
- **Analisi prevista**: tabella per formato e retriever (BM25 baseline, MiniLM, ibrido, oracolo) con V, Vc, J, R, M
  primaria e verso; esito della regola di esclusione; interpretazione dell'oracolo secondo la regola; esempi recuperati
  in comune con BM25 per esercizio; report grafico con `review_report.py` per le tre condizioni nuove.
- **Esecuzione su CPU del denso durante le run**: gli embedding di MiniLM sono in cache (`data/cache/embeddings/`),
  il modello gira offline su CPU (la GPU resta a LM Studio).
- **STOP A**: proposta registrata prima del codice e delle run.
- **APPROVATA (2026-10-09) con due modifiche** (vincolanti, prevalgono sul testo sopra):
  1. **Troncamenti**: un retriever è escluso in quel formato se i troncamenti per max_tokens sono **2 o più**; con **1
     solo** troncamento non è escluso, ma la risposta si riporta e si allega nel report. Invariati: **anche un solo
     prompt oltre il budget di contesto → esclusione**; criterio Vc (perdita di più di 4 su 40 → esclusione).
  2. **Esclusioni dei candidati (verificato)**: nelle run `dev_k` BM25 esclude **SOLO la query stessa**
     (`PromptBuilder.bm25_for`: indice rifittato su `pool(query)` = i 59 candidati convertiti meno la query, nessun
     `exclude_ids`; Cruise, non convertito, e il test set non sono mai candidati per nessuna condizione). `dense`,
     `hybrid` e `oracle_jt` usano **esattamente lo stesso `pool(query)`** (58 candidati): nessuna differenza con BM25.
     Il controllo prima delle run lo verifica di nuovo sugli esempi effettivamente scelti.

### [2026-10-09] Controllo di funzionamento dei retriever e run oracolo: esecuzione ed esito (STOP B)
- **Codice**: condizioni `dense`, `hybrid`, `oracle_jt` in `generation/prompt_builder.py` (il più simile per ultimo;
  candidati = `pool(query)`, gli stessi di bm25; il denso è quello di `config_dense.yaml`, caricato su CPU e offline
  solo alla prima condizione densa; `oracle_jt` analysis_only); `HybridRetriever.prefitted`; provenienza del runner
  con `config_dense.yaml` (sha256) e modello denso@revisione; `experiments/context_budget.py --config` (bilancio dei
  prompt di un config dell'insieme di sviluppo, senza leggere il test set); `experiments/check_dev_retrievers.py`
  (controlli prima delle run); `experiments/analyze_retrievers.py` (regola della voce 109, testata sulla sola baseline
  PRIMA delle run: metriche della baseline identiche a quelle di `dev_instructions_analysis`);
  `experiments/review_report.py`: la condizione entra nell'etichetta delle risposte e c'è il filtro `cond=` (con più
  retriever nella stessa run le risposte erano indistinguibili). Test: `check_retrievers` in
  `generation/test_generation.py` (embedding finti, nessun download). Suite verdi.
- **Controlli prima delle run** (tutti passati): prompt più lungo stimato 5.359 token reali (C-G, dense, Facepage)
  contro un budget di 28.672 (fattore server / stima 1,044 dai manifest di `dev_k`); i prompt bm25 k = 3 ricostruiti
  hanno lo stesso sha256 di `dev_k` (20/20 per formato); dense, hybrid e oracle_jt differiscono dalla baseline SOLO nel
  blocco esempi (20/20 per formato e condizione, diff su AlphaInsurance); su tutte le 59 query del corpus la query non
  è mai tra gli esempi, i candidati sono gli stessi 58 di bm25, oracle_jt = top-3 per Jt, e bm25 / dense / hybrid
  coincidono con i top-3 del LOO della voce 108. Esempi in comune con bm25 sul dev set: dense 26/60, hybrid 39/60,
  oracle_jt 32/60.
- **Run**: `dev_retrievers__P-G` e `__C-G`, 120 + 120 generazioni, tutte `stop`, nessun ragionamento, nessuna
  ripresa necessaria. 4 risposte per formato vengono dalla cache perché il prompt è IDENTICO a quello di `dev_k` (stessi
  esempi nello stesso ordine: HospitalHouseMD con oracle_jt, ProjectManagement con hybrid, 2 ripetizioni ciascuno):
  sono le risposte della baseline, come atteso a parità di richiesta e seme. **Caricamento del modello**: Gemma 4 12B
  QAT caricato da me con `lms load google/gemma-4-12b-qat --context-length 32768 --gpu max` (nessun modello era
  caricato); impostazioni salvate di LM Studio per il modello: contesto 32768, cache K e V F16, ragionamento spento;
  **Flash Attention NON verificabile** dai log né dall'API (il config la dichiara attiva come nella baseline).
- **Esito della regola di esclusione (voce 109)**: **nessuna esclusione**. PlantUML: dense dVc −1, hybrid dVc 0;
  compatto: dense dVc +1, hybrid dVc +1; nessun troncamento, nessun prompt oltre il budget. **BM25, MiniLM e ibrido
  entrano tutti nel Passo 3b in entrambi i formati.**
- **Oracolo (solo diagnostica)**: R(oracolo) − R(BM25) = PlantUML +0,017, compatto −0,065 → **"la qualità del
  retrieval non è il collo di bottiglia con questo corpus e questo modello"** (interpretazione fissata prima).
- **Descrittivo, fuori dalla regola** (2 ripetizioni, temperatura 0,3: differenze di pochi centesimi possono essere
  rumore): PlantUML R 0,307 (BM25) / 0,327 (MiniLM) / 0,330 (ibrido) / 0,324 (oracolo); compatto R 0,310 / 0,256 /
  0,250 / 0,244, con J e (per l'oracolo) Vc più bassi (30/40). Nel compatto tutti i retriever diversi da BM25 hanno R
  più basso di 0,05-0,07: da tenere presente nel 3b, dove il confronto si farà sul test set. Report:
  `data/results/generation/dev_retrievers_analysis/summary.md`; report grafico (non versionato):
  `data/results/generation/dev_retrievers_review/index.html`.
- **STOP B**: in attesa dell'utente. Nessuna modifica alla configurazione di lavoro (voce 95).

### [2026-10-10] Istruzioni v5 riscritte da zero, metriche corrette e regola di adozione — STOP A (prima della run)
- **Decisione**: il prompt NON è vincolato a replicare lo studio 2025. Le istruzioni si possono riscrivere liberamente;
  la condizione static diventa "istruzioni correnti + 2 esempi fissi". **La domanda 9 è superata.** I file v4 restano
  nel repo come storico (e restano il default finché la regola sotto non adotta v5).
- **FASE 0 (verifica dei dati, corpus, 59 diagrammi)**: tipi di relazione associazione 354, ereditarietà 142,
  composizione 66, unidirezionale 54, aggregazione 14, dipendenza 2 (realizzazione 0); molteplicità sui 980 estremi
  delle relazioni non di generalizzazione: '1' 390, '*' 171, '0..*' 165, vuote 77, '0..1' 74, '1..*' 56, '1..1' 19, più
  27 valori rari; attributi per classe: mediana 1. **"215 classi su 575 senza attributi" vale nel formato compatto**:
  le 35 enumerazioni hanno `values` e non `attributes`; sui diagrammi Apollon le classi senza attributi sono 180
  (180 + 35 = 215). Semantica delle molteplicità del compatto **confermata** (non opposta): in Boeing AirplaneModel
  (source) "1" / Airplane (target) "0..*" = ogni aereo ha un modello, un modello ha molti aerei;
  `sourceMultiplicity` = quanti oggetti della classe source per UN oggetto della target.
- **File nuovi**: `generation/templates/v5_compact_instructions.txt` e `v5_plantuml_instructions.txt` (testo esatto
  dell'utente, LF), `v5_task.txt` (traccia v4 + riga finale per formato: "Now write the PlantUML diagram for this system
  only." / "Now write the compact JSON diagram for this system only."), congelati con lo sha256 (`check_v5`) e `-text`
  in `.gitattributes`: compatto `613140dd…71f2`, PlantUML `7eb1038c…de9a`, traccia `3b774b1a…34f2`.
  `generation/plantuml_format.apollon_to_plantuml(version="v5")`: generalizzazione e realizzazione SOLO
  nell'intestazione ("class X extends Y implements A, B", anche abstract class / interface), mai come righe;
  composizione / aggregazione con il tutto a sinistra (come già nella v4); il canonico v4 resta invariato (default).
  `PromptSpec.instructions_version` "v4" (default) | "v5" (solo PlantUML e compatto, non combinabile con il blocco
  mirato della voce 98); `prompt.instructions_version` nei config; `experiments/configs/dev_v5.yaml` (Gemma, bm25
  k = 3, P-G e C-G, 2 ripetizioni, 80 generazioni, uguale a `dev_k` salvo la versione delle istruzioni);
  `experiments/analyze_v5.py` (regola sotto).
- **Post-processing**: il v2 basta, nessuna v3. Legge `extends` / `implements` (anche `abstract class`, `interface X
  extends Y`, più genitori separati da virgola, corpo sulla stessa riga) con il verso giusto e continua ad accettare le
  righe `--|>` / `..|>` (anche miste alle intestazioni). **Round-trip** Apollon → PlantUML v5 → Apollon sui 59
  diagrammi del corpus: 59/59 a L4, contenuto identico, 142 `extends` riletti (nessuna generalizzazione del corpus ha
  etichette, molteplicità o ruoli, né più di un genitore; nessuna realizzazione); casi sintetici con implements,
  interface extends e righe miste: identici.
- **Metriche (nessuna generazione)**: `analyze_pilot.norm_mult`: '1..1' → '1' ('0..n' → '*' era già coperto).
  **M della baseline dev_k Gemma k = 3 prima / dopo: invariata** (PlantUML 137/486 = 0,282; compatto 104/486 = 0,214):
  i 6 estremi '1..1' dei GT del dev set (ProjectManagement 2 relazioni, Restaurant 1) stanno in relazioni mai ritrovate
  dalle risposte. Rigenerati i 7 report di analisi (`pilot_temperature`, `pilot2_formats_analysis` e `_v2`,
  `dev_formats`, `dev_k`, `dev_instructions`, `dev_retrievers`): **identici salvo la riga di provenienza** (nuovo
  commit `366ed7a`): nessun esito di regole passate cambia. **R_fam** (secondaria, riportata): come R, con associazione
  e unidirezionale nello stesso tipo. **Generalizzazioni invertite** riportate a parte (generalizzazioni del GT
  accoppiate con figlia e madre scambiate). Baseline v4: R_fam PlantUML 0,344, compatto 0,347; generalizzazioni
  invertite PlantUML 12/27, compatto 0/40.
- **REGOLA DI ADOZIONE (registrata PRIMA della run)**, per formato, delta = v5 − v4 (baseline dev_k Gemma k = 3, GT
  corretto, metriche corrette), 40 risposte per parte: **adottare v5 se [dR ≥ +0,03 OPPURE dR_fam ≥ +0,03 OPPURE (solo
  PlantUML) generalizzazioni invertite ridotte almeno della metà] E dVc ≥ −2 E dM_primaria ≥ −0,03.** Dimezzate = v5 ≤
  v4 / 2 con v4 > 0 (baseline 12 → soglia 6). Controllo preliminare come voce 98 (40 risposte, niente ragionamento,
  modello del config). Riportati fuori regola: classi, generalizzazioni e composizioni in più, token di output,
  latenza, scarti, tabelle di confusione. **Se v5 è adottata in un formato, diventa la configurazione di lavoro per
  TUTTE le condizioni di quel formato** (zero-shot, static, random, bm25, dense, hybrid).
- **Controlli (STOP A)**: prompt v5 di ProjectManagement per entrambi i formati consegnati interi all'utente; diff con
  la v4 su tutti i 20 esercizi: cambiano solo istruzioni, riga finale della traccia e, in PlantUML, le intestazioni
  degli esempi con le generalizzazioni (158 intestazioni, 158 righe `--|>` tolte, 37 righe vuote spostate); esempi del
  compatto identici; prompt v4 ancora identici a quelli di `dev_k` (20/20 per formato). Token stimati (cl100k) v4 → v5:
  PlantUML mediana 3.563 → 3.275 (−258), massimo 4.365 → 4.143; compatto 4.168 → 3.824 (−345), massimo 4.931 → 4.586;
  istruzioni da sole: PlantUML 1.192 → 958, compatto 1.378 → 1.022. Script di analisi testato sulla baseline. Suite
  verdi.
- **Punti del testo da segnalare (NON modificati)**: (1) l'ultima frase delle istruzioni ("The examples below show ...")
  resta anche in zero-shot, dove non ci sono esempi; (2) nel compatto la regola 4 chiede le molteplicità per ogni
  relazione salvo inheritance e realization, quindi anche per dependency, ma l'elenco delle chiavi di "dependency" non
  le prevede (il parser le accetta comunque); nel PlantUML la dipendenza è esclusa dalla regola 4. Nessun punto è
  incompatibile con il parser o con il formato compatto.
- **STOP A**: proposta e controlli consegnati prima della run.
- **STOP A APPROVATO (2026-10-10) con tre correzioni ai testi v5**, applicate e ricongelate PRIMA della run:
  1. la frase "The examples below show the format and the modeling style. They describe other systems: do not copy
     their classes." passa dalle istruzioni al nuovo `generation/templates/v5_examples_block.txt`, subito prima di
     "Examples to follow:" (riga vuota in mezzo); in zero-shot non compare (il blocco esempi v4 resta invariato);
  2. compatto, regola 4: "(every relation except inheritance, realization and dependency)";
  3. entrambi i formati, regola 1: "A simple value (a name, a date, an amount) is an attribute, not a class."
  Nuovi sha256 (`check_v5`, `-text`): compatto `ae014366…dfaa`, PlantUML `1e7421b8…a6e`, blocco esempi `11107dff…66ff`,
  traccia invariata `3b774b1a…34f2`. **Controlli rapidi ripetuti, tutti passati**: diff v4 → v5 sui 20 esercizi =
  istruzioni, frase del blocco esempi (+1 riga e +1 riga vuota per prompt), riga finale della traccia e, in PlantUML,
  158 intestazioni con 158 righe `--|>` tolte (righe vuote spostate); prompt v4 ancora identici a `dev_k` (20/20 per
  formato); round-trip v5 invariato (59/59); zero-shot v5 senza la frase. Token stimati v5: PlantUML mediana 3.272,
  massimo 4.140; compatto mediana 3.823, massimo 4.585. Segnalazione (1) e (2) dello STOP A risolte dalle correzioni.
- **Limite noto**: gli esempi del corpus (GT) a volte non rispettano le regole v5 (attributi senza tipo, etichette con
  spazi, aggregazioni dove la regola 3 indicherebbe associazione); restano come sono perché sono il GT con cui si
  valuta.
- **Run avviata e INTERROTTA su richiesta dell'utente (2026-10-10)**: modello caricato con `lms load
  google/gemma-4-12b-qat --context-length 32768 --gpu max -y`, verificato con `lms ps` (contesto 32768), comando e
  uscita in `data/results/generation/dev_v5_model_load.log`; `dev_v5__P-G` fermata dopo 1 risposta su 40, `dev_v5__C-G`
  non avviata. Il registro delle esecuzioni ha una riga di inizio senza fine (processo terminato). Da riprendere con
  `--resume` (P-G), poi C-G, analisi e report grafico.

### [2026-10-10] Test set De Bari in leave-one-out: ogni esercizio usa gli altri 19 come candidati — DECISIONE e implementazione
- **Decisione dell'utente**: i 20 esercizi De Bari restano TUTTI il test set (20 esercizi valutati), ma per ciascuna
  query del test set i candidati del retrieval sono i 59 esercizi del corpus **più gli altri 19 esercizi De Bari**
  (78 candidati), mai la query stessa: lo stesso protocollo leave-one-out già usato per il corpus. Risponde alla
  domanda 3 per i relatori. Scartati: split fisso 10/10 (10 soli esercizi valutati: potenza troppo bassa) e due metà
  alternate (20 valutati ma 69 candidati invece di 78).
- **Motivazione**: gli esercizi De Bari hanno lo stile e la fonte del test set; con il LOO entrano nel retrieval senza
  perdere esercizi valutati. Il test set è ancora "pulito": nessuna generazione fatta, solo la run di retrieval BM25
  `testset_2026-10-04_stop2` (che con il nuovo protocollo diventa storica).
- **Controllo di quasi-duplicati tra i 20 (fatto, solo lettura)**: TF-IDF delle descrizioni (idf comune a corpus e test
  set) sulle 190 coppie: massimo 0,219 (DB12_Furniture - DB13_Factory), poi 0,214 (DB07_BankSystem - DB16_OOBank);
  nessuna coppia ≥ 0,25 (soglia dei quasi-duplicati del Passo 2), mediana 0,028. Jaccard dei nomi di classe del GT:
  massimo 0,25 (DB04_PatientRecordAndSchedulingSystem - DB19_MyDoctor). **Nessuna esclusione necessaria.** Da notare:
  il vicino più simile di un esercizio De Bari è in mediana PIÙ simile nel corpus (TF-IDF 0,151) che tra gli altri De
  Bari (0,121): il vantaggio "stesso stile" non è lessicale.
- **Piano di implementazione (PROPOSTA, da approvare prima del codice)**:
  1. `retrieval/corpus_loader.py`: l'invariante passa da "nessun esercizio De Bari tra i candidati" a "la query non è
     mai tra i propri candidati"; `corpus.jsonl` resta senza esercizi De Bari (controllo invariato sul file); il pool
     di una query del test set si costruisce a runtime (59 + 19).
  2. `generation/prompt_builder.py`: `pool(query)` per una query del test set = corpus + gli altri 19; bm25 RIFITTATO
     su quel pool (come per il corpus); dense indicizzato su 79 con esclusione della query; hybrid e random sullo
     stesso pool. **Le query del corpus (insieme di sviluppo) restano con i soli 58 candidati del corpus**: le scelte
     già fatte restano confrontabili e il GT del test set non entra nelle run di sviluppo.
  3. Test: i controlli "nessun id del test set restituito" diventano "la query non restituisce mai se stessa; una query
     del corpus non restituisce mai un esercizio De Bari"; nuovo controllo che ogni query De Bari abbia esattamente 78
     candidati.
  4. Invariati: BM25 congelato (i parametri non dipendono dall'indice), formati, k, retriever, regole già registrate.
     Nuovo tag `testset-v2` sul commit che introduce il protocollo (contenuto del test set invariato).
  5. Da aggiornare: CLAUDE.md e STATUS.md ("test set mai nel retrieval" → "test set in LOO"), domanda 3 risolta,
     domanda 4 (DB06_Flights / AirTravel) resta. Una nuova run descrittiva di retrieval sul test set con il protocollo
     LOO sostituirà `testset_2026-10-04_stop2` come riferimento.
- **Piano APPROVATO e implementato (2026-10-10)**:
  - `generation/prompt_builder.py`: `pool(query)` = gli altri 58 del corpus per una query del corpus; 59 + gli altri
    19 per una query del test set (errore se il builder non ha le query del test set); bm25 sempre RIFITTATO su
    `pool(query)` (tolto l'indice fisso sui 59); dense indicizzato su corpus + test set con le esclusioni di
    `excluded(query)`; esempi cercati in `all_by_id` (corpus + test set); il divieto di esempi del test set vale ora
    solo per le query del corpus (build() fallisce). `corpus_loader.check_disjoint` invariato: `corpus.jsonl` resta senza
    esercizi del test set.
  - `retrieval/run_testset.py`: `--protocol loo` (default, voce 112) | `fixed59` (originale). Verificato che `fixed59`
    riproduce byte per byte `testset_2026-10-04_stop2` (`testset_top3.csv` e `summary.csv`; run temporanea cancellata).
  - Test: ogni query del test set ha esattamente 78 candidati (corpus + gli altri 19), mai sé stessa, indice bm25 sullo
    stesso insieme; una query del corpus esclude tutti gli esercizi De Bari e un esempio De Bari per una query del
    corpus fa fallire build(); un builder senza test set rifiuta una query del test set. Suite della generazione e del
    retrieval verdi; `check_dev_retrievers.py`: prompt dell'insieme di sviluppo INVARIATI (bm25 identico a `dev_k`
    20/20 per formato; bm25 / dense / hybrid identici ai top-3 del LOO della voce 108).
- **Run descrittiva di retrieval sul test set con il nuovo protocollo**: `data/results/retrieval/testset_2026-10-10_loo/`
  (sostituisce `testset_2026-10-04_stop2` come riferimento; quella resta come storico). Vicini dal test set nei top-3:
  17/60, al rango 1: 5/20; top-1 cambiato rispetto al protocollo a 59 candidati in 5 esercizi su 20. BM25 J@1 0,106
  (prima 0,113), J@3 0,085 (prima 0,077); oracolo J@1 0,159 (prima 0,148), J@3 0,121 (prima 0,105); random J@3 0,015.
  Fasce di score_norm del top-1: basso 4, medio 7, alto 9 (prima 5 / 8 / 7). Solo descrittivo.
- **Da fare al prossimo commit**: tag `testset-v2` sul commit che introduce il protocollo (il contenuto del test set non
  cambia; `testset-v1` resta il riferimento del contenuto).

### [2026-10-10] Insieme unico dei 79 esercizi: leave-one-out su tutti, valutazione principale sui 53 mai usati per decidere — DECISIONE, piano PROPOSTO
- **Decisione dell'utente** (sostituisce l'impostazione della voce 112 per il Passo 3b): un solo insieme di 79 esercizi
  (59 del corpus + 20 De Bari). Per ogni query i candidati del retrieval sono **tutti gli altri 78** (leave-one-out;
  il retrieval non ha parametri da imparare, quindi il LOO equivale alla cross-validation con il pool più grande).
  Scartata l'estrazione casuale di 10 esercizi a ogni giro (più rumore, semi da fissare, nessun vantaggio sul LOO).
- **Ruoli** (campo `role`):
  - `sviluppo` = i **26** esercizi su cui il modello ha già generato e su cui sono state prese decisioni: i 20
    dell'insieme di sviluppo (voce 92) e i 6 dei piloti (ApartmentBuilding, CardGameApp, FilmSet, Louvre, Sober,
    StudentAppointment);
  - `valutazione` = i **53** mai usati come query di generazione (33 del corpus + 20 De Bari): valutazione PRINCIPALE.
  Analisi secondarie: i 20 De Bari a parte (confronto con De Bari et al. sul loro GT); i 26 di sviluppo riportati a
  parte come esplorativi. Tutti i 79 possono fare da ESEMPIO (candidati) per qualunque query.
- **Campo `source`**: `golden` (Golden UML Modelset, 44), `translated_it` (15), `debari` (20).
- **Piano di implementazione (PROPOSTA)**:
  1. `corpus/build_exercises.py` (nuovo): genera `corpus/processed/exercises.jsonl` (79 record) dai due file del Passo 1
     (`corpus.jsonl`, `testset_debari.jsonl`), che restano INVARIATI come uscite della pipeline e come base delle
     analisi già fatte; campi comuni + `source` + `role` (+ i campi De Bari dove esistono). Le cartelle `raw/` restano
     separate (fonti e licenze diverse, percorsi citati dalle note e dal tag `testset-v1`).
  2. `retrieval/corpus_loader.load_exercises()`; nel prompt builder un parametro di protocollo del pool: `all` (78
     candidati per ogni query, per il Passo 3b) e `corpus` (protocollo delle run di sviluppo: 58 candidati del corpus
     per le query del corpus), così le run di sviluppo restano riproducibili e la run v5 si confronta con `dev_k` alle
     stesse condizioni. Nei config: `pool: all | corpus` (default `corpus` per i config esistenti).
  3. Test: 79 record, id unici, 26 + 53, ogni query ha 78 candidati con `pool: all`, mai sé stessa; con `pool: corpus`
     i prompt di sviluppo sono identici a quelli di `dev_k` (sha256).
  4. Congelamento: tag `evalset-v1` sul commit che introduce `exercises.jsonl` (contenuto dei 53 da non modificare
     dopo aver visto risultati di generazione).
  5. Documenti: CLAUDE.md, STATUS (domande 3 e 4 da riformulare per i relatori), corpus/README.md.

### [2026-10-10] Cruise recuperato: associazione ternaria riscritta con tre associazioni binarie (opzione b)
- **Decisione dell'utente**: l'associazione ternaria Guest / Ticket / Cruise (diamante `<> diamond`, senza equivalente
  in Apollon v4, motivo dell'esclusione di Cruise dal Passo 1) è sostituita da due associazioni binarie con Ticket
  come centro: `Ticket "*" -- "1" Cruise` ("Several tickets are issued for each cruise. A ticket belongs to exactly one
  cruise") e `Ticket "*" -- "0..1" Guest` ("A guest can have any number of tickets"; lato Guest 0..1 dall'estremo
  Guest della ternaria originale), più `Guest "*" -- "*" Cruise` ("A cruise has several guests, and each guest can
  participate in several cruises"). **Opzione (b)** dell'utente (dopo una prima scelta (a) senza l'associazione
  diretta): l'associazione Guest - Cruise è nel testo ma **gli autori non l'hanno disegnata** (nell'originale passava
  per la ternaria); dichiarato nella correzione. Perso il vincolo "only one ticket per cruise" per ospite: annotato in
  `known_issues.yaml` (`ternary_association_decomposed`, nuovo codice in `build_manifest.KNOWN_ISSUE_CODES`).
- **Implementazione**: `corpus/corrections/Cruise.yaml` (4 `remove_line` del diamante, 3 `add_line`; `corpus/raw/`
  intatto). Pipeline rieseguita: `build_manifest.py` (60 record) e `apollon_convert.py`: **60/60 convertiti**, 0
  etichette non classificate, 0 violazioni di schema, 0 discrepanze di round-trip, 0 violazioni di stile;
  `test_apollon_convert.py` verde. **Solo il record Cruise e `processed/apollon/Cruise.json` cambiano** (gli altri 59
  record di `corpus.jsonl`, i 59 JSON Apollon e tutto il test set sono identici byte per byte, verificato).
- **Effetto sul retrieval (da decidere)**: Cruise entra nel pool dei candidati e cambia le statistiche IDF di BM25.
  Cruise non compare mai tra gli esempi recuperati per le 20 query di sviluppo, ma l'ordine o un esempio cambiano in
  1 esercizio con k = 2, 3, 5 (Bookmaker a k = 3: OilWells, University, HomeForTheElderly → University, OilWells,
  HomeForTheElderly) e in 3 con k = 8; nel LOO del corpus 3 query su 59 hanno un top-3 diverso dal Passo 2. Le run di
  sviluppo non sono quindi più riproducibili byte per byte con il pool a 60. **Deciso nella voce 115** (pool unico).

### [2026-10-10] Pool unico: per ogni query (sviluppo e valutazione) tutti gli altri 79 esercizi
- **Decisione dell'utente** (supera il pool della voce 112 e l'opzione `pool: corpus` della voce 113; scartato anche il
  pool di sviluppo congelato a 59 proposto dopo la voce 114): con il leave-one-out ogni query vede già tutti gli
  esercizi tranne sé stessa, quindi un solo protocollo per tutto: **80 esercizi** (60 del corpus, Cruise compreso, +
  20 De Bari) e per **ogni** query i candidati sono **gli altri 79**. Vale per lo sviluppo e per il Passo 3b.
- **Conseguenze dichiarate**:
  - le run di sviluppo fatte fino al 2026-10-09 (piloti, `dev_formats`, `dev_k`, `dev_instructions`,
    `dev_retrievers`) usavano i 58 candidati del corpus: restano valide come storico, con il loro protocollo, ma non sono
    più riproducibili con il codice attuale (`experiments/check_dev_retrievers.py` segnato come STORICO);
  - con il pool unico gli esempi bm25 k = 3 cambiano in **12 dei 20** esercizi di sviluppo (11 hanno almeno un esempio
    De Bari, 13 esempi De Bari su 60; Cruise mai);
  - negli esperimenti di sviluppo compaiono come esempi anche esercizi di valutazione: accettato (nel 3b fanno da
    esempi comunque; la valutazione guarda solo le risposte alle query).
- **Leva v5 (modifica della regola della voce 111)**: la baseline non è più `dev_k` ma una **v4 rigenerata con il pool
  unico**: `experiments/configs/dev_v5base.yaml` (run `dev_v5base__P-G` / `__C-G`, 80 generazioni), uguale a
  `dev_v5.yaml` salvo `instructions_version: v4`; `experiments/analyze_v5.py` confronta `dev_v5` con `dev_v5base`
  (regola e soglie invariate). Totale 160 generazioni. La run `dev_v5__P-G` interrotta (1 risposta, pool da 58) è stata
  tolta dai risultati (copia nello scratchpad della sessione). Budget: prompt più lungo stimato 5.149 token reali
  (v4, compatto) contro 28.672.
- **Codice**: `generation/prompt_builder.py`: `pool(query)` = tutti gli esercizi (corpus + test set) tranne la query; il
  test set si carica sempre (anche quando non è passato); tolto il divieto di esempi De Bari per le query del corpus.
  `experiments/select_pilot.py` (e quindi `select_dev.py`): la selezione storica si riproduce con il protocollo del Passo
  2 (59 candidati senza Cruise, LOO sugli altri 58), `HISTORICAL_EXCLUDED`. `experiments/context_budget.py --config`
  usa il pool unico. Test: ogni query (80) ha esattamente 79 candidati, mai sé stessa, indice bm25 sullo stesso insieme;
  sul pool storico bm25 riproduce `loo_top3.csv` del Passo 2; controlli di sanità PlantUML e compatto su 80 diagrammi
  (Cruise a L4, identico al Passo 1 nei due percorsi); loader con 60 candidati. Suite di corpus, retrieval e generazione
  verdi.
- **Da rivedere nella fase del retrieval** (non toccato ora): gli script di analisi del retrieval sul solo corpus
  (`analyze_retrieval.py`, `analyze_dense.py`) e `run_testset.py` usano ancora i loro pool (60 del corpus; 79 per il
  test set); le run di riferimento versionate restano quelle già fatte.

### [2026-10-10] Pulizia del codice del corpus: percorsi condivisi e classificazione delle etichette come dati
- **A. `corpus/paths.py`** (nuovo, modulo leggero): cartelle raw/ per fonte, file processati (`corpus.jsonl`,
  `testset_debari.jsonl`, `apollon/`, `apollon_debari/`), `SPLITS`, `DEBARI_ID_RE` e `read_jsonl`. Usato da
  `build_manifest`, `apollon_convert`, `diff_report`, `leakage_check`, `generate_label_classification`,
  `check_translated`, `apply_glossary`, `retrieval/corpus_loader`, `experiments/provenance` e dai controlli di sanità
  PlantUML e compatto. Toglie le copie dei percorsi (corpus.jsonl era scritto in 7 file), i due `SPLITS`, la copia
  della regex degli id De Bari e 6 letture JSONL duplicate; i nomi dei moduli (`OUT_PATH`, `CORPUS_JSONL`, …)
  restano come alias. **Corretta una fragilità**: `generate_label_classification.py` leggeva e scriveva con percorsi
  relativi alla cartella di lancio (funzionava solo dalla radice); ora funziona da qualunque cartella (provato).
- **B. `corpus/label_classification.yaml`** (nuovo): le 207 classificazioni approvate, prima dizionario
  `CLASSIFICATION` di 483 righe dentro il generatore (ora 214 righe invece di 677); stesso contenuto, stesso ordine,
  commenti di gruppo conservati; voce ripetuta → errore. Coerente con correzioni ed esclusioni, già in YAML. Emerse 4
  voci approvate non più usate (Boeing "part of" ×2, TruckLogistics "driver" ×2: etichette tolte o cambiate dalle
  correzioni di contenuto), innocue: il generatore le ignora; lasciate come storico.
- **Verifica (tutto identico)**: pipeline rieseguita per intero; sha256 identici per gli 80 JSON Apollon,
  `corpus.jsonl`, `testset_debari.jsonl`, `label_classification.json` / `.md` e `check_debari_report.md`; output di
  `leakage_check` e `check_translated` (--all, --debari) identici; `diff_report.md` identico tra lo script vecchio e il
  nuovo (cambia solo rispetto al commit precedente, perché ora contiene le correzioni di Cruise, voce 114, che non
  era stato rigenerato). Nuovo test `check_paths_and_label_yaml`; suite di corpus, retrieval e generazione e controlli
  di sanità verdi.
- **Non fatto (scelta)**: nessuna divisione di `apollon_convert.py` (1.355 righe, cuore congelato del Passo 1); tolte
  solo importazioni rimaste inutilizzate.

### [2026-10-10] Insieme di valutazione congelato (ruoli) e dichiarazione delle contaminazioni, prima della run v5
- **Ruoli (implementa la voce 113 per la parte del corpus)**: `corpus/roles.yaml`, GENERATO da `corpus/build_roles.py`
  (non si modifica a mano; `--check` verifica che sia aggiornato), una riga per ciascuno degli 80 esercizi con `id`,
  `source` (golden / translated_it / debari) e `role`. **sviluppo = 26** (i 20 di `dev_k.yaml` + i 6 dei piloti, gli
  esercizi già usati come query di generazione: 21 golden + 5 translated_it); **valutazione = 54** (33 del corpus +
  Cruise + 20 De Bari: 24 golden con Cruise, 10 translated_it, 20 debari). Conteggi verificati dallo script (hard-fail) e
  dal test `check_roles`. `corpus/paths.py`: `ROLES_YAML`, `load_roles()`. Da notare: AirTravel (esempio 2 del prompt
  statico) è di valutazione; la condizione static la rifiuta già come query (voce del Passo 3a).
- **Blocco nel runner**: `experiments/run_experiment.check_query_roles` rifiuta una run REALE che usi come query un
  esercizio di valutazione, salvo i config del Passo 3b marcati `passo: 3b`; dry run e client finto non bloccati (non
  producono risposte di un modello). Test: query di valutazione rifiutata, corpus intero rifiutato (34 di valutazione),
  query di sviluppo e pilota ammesse, `passo: 3b` ammesso, client finto ammesso. I test del runner che simulano il 3b
  sul test set sono marcati `passo: 3b`.
- **Congelamento**: tag `evalset-v1` sul commit che introduce i ruoli (lo crea l'utente). Il tag `testset-v2` (voce 112)
  esiste in locale sul commit afb522d ma non è ancora su GitHub.
- **Verifica delle regole v5 sui soli 26 di sviluppo (descrittiva)**: le statistiche che hanno motivato le regole v5
  sono state ricalcolate sui 26 esercizi di sviluppo e confrontate con i 60 del corpus:

  | | 26 di sviluppo | 60 del corpus | 34 del corpus di valutazione |
  |---|---|---|---|
  | associazione | 60% | 57% | 55% |
  | generalizzazione | 21% | 22% | 23% |
  | composizione | 3% | 10% | 15% |
  | unidirezionale | 16% | 8% | 4% |
  | aggregazione | 0% (1) | 2% | 3% |
  | molteplicità '1' / '*' / '0..*' / vuota / '0..1' / '1..*' | 37 / 20 / 20 / 13 / 6 / 3% | 39 / 18 / 17 / 8 / 8 / 6% | 40 / 16 / 16 / 5 / 9 / 7% |
  | '*' + '0..*' | 39% | 35% | 32% |
  | attributi per classe (mediana; senza attributi) | 1; 32% | 1; 33% | 1; 33% |

  **Stesse conclusioni** (associazione tipo dominante, composizione minoritaria, '*' / '0..*' frequenti, mediana di 1
  attributo): le regole v5 sarebbero state le stesse usando solo i 26 di sviluppo. **Mitigazione registrata**. Differenze
  da notare: nello sviluppo la composizione è ancora più rara (3%), l'unidirezionale e le molteplicità vuote più
  frequenti.
- **Dichiarazioni (contaminazioni note, da riportare in tesi)**:
  1. le regole delle istruzioni v5 (voce 111) sono state progettate con le statistiche del GT dell'**intero corpus**,
     compresi i 33 esercizi (34 con Cruise, recuperato dopo) ora di valutazione; il controllo sopra mostra che sui soli
     26 di sviluppo le conclusioni non cambiano;
  2. la scelta del modello denso (voce 108) è avvenuta in leave-one-out sull'**intero corpus** (59 query, quindi anche
     esercizi ora di valutazione); l'esito è un pareggio risolto per spareggio sul modello più piccolo, e nessun
     parametro è stato tarato;
  3. dal pool unico (voce 115), nelle run di sviluppo compaiono **come esempi** esercizi di valutazione, De Bari
     compresi (con k = 3 in 11 dei 20 esercizi di sviluppo c'è almeno un esempio De Bari): la valutazione guarda solo le
     risposte alle query, ma il modello di sviluppo ha "visto" quei diagrammi come esempi;
  4. l'analisi a parte sui 20 De Bari **non è alla pari** con De Bari et al.: nei nostri prompt per un esercizio De Bari
     possono comparire come esempi gli altri 19 esercizi De Bari (stesso stile e stessa fonte), mentre nel loro studio
     nessun esempio De Bari era nel prompt.

### [2026-10-10] Leva v5: esecuzione ed esito (STOP B)
- **Run** (pool unico, voce 115; Gemma 4 12B QAT caricato con il comando fisso, `lms ps` registrato in
  `data/results/generation/dev_v5_model_load.log`, contesto 32768): `dev_v5base__P-G` / `__C-G` (v4) e `dev_v5__P-G` /
  `__C-G` (v5), 4 × 40 = **160 generazioni**, tutte `stop`, nessuna dalla cache, nessun ragionamento; query = i 20 di
  sviluppo (controllo dei ruoli della voce 117 superato). **Latenze NON confrontabili**: durante parte della run la GPU
  era condivisa con un altro programma (un gioco), con circa 10 token/s invece di 35-40 (baseline compatta mediana
  39,7 s, v5 10,8 s); non cambia modello né parametri.
- **Esito della regola della voce 111 (meccanico)**:
  - **PlantUML: v5 ADOTTATA** — dR +0,040, dR_fam +0,037, generalizzazioni invertite 16/32 → 0/40 (dimezzate); dVc −2
    (ammesso, limite incluso), dM_primaria +0,037;
  - **JSON compatto: v5 NON adottata (resta v4)** — dR −0,017, dR_fam −0,023, nessun guadagno; dVc −6 (oltre il
    limite di −2); dM_primaria +0,016.
  Effetto (voce 111): da qui **PlantUML usa le istruzioni v5 in tutte le condizioni**, il **compatto resta con le v4**.
- **Descrittivo**: PlantUML v5 J 0,540 (v4 0,532), R 0,361 (0,321), M primaria 0,317 (0,280), verso 47/47 (24/40),
  generalizzazioni in più 20 (35); compatto v5 V 30/40 (35/40), Vc 27/40 (33/40), J 0,371 (0,452), R 0,193 (0,210),
  composizioni in più 29 (85). Le risposte compatte non valide sono errori di sintassi JSON del modello (parentesi
  sbagliate o non chiuse con finish_reason `stop`): 5 in v4, 10 in v5. Report: `dev_v5_analysis/summary.md`, report
  grafico (non versionato) `dev_v5_review/index.html`.
- **DA SEGNALARE (non decide nulla qui): effetto del pool unico sulla baseline compatta.** Confrontando la baseline v4
  col pool unico (`dev_v5base`) con quella storica a 58 candidati (`dev_k`, k = 3), per i **12 esercizi i cui esempi sono
  cambiati** (11 con almeno un esempio De Bari): **compatto R 0,366 → 0,208 (−0,159 in media)**, PlantUML 0,323 → 0,360
  (+0,036); per gli 8 esercizi con gli stessi esempi la differenza è rumore (−0,017 / −0,004). Validità della baseline
  compatta: 39/40 (`dev_k`) → 35/40. Ipotesi da verificare: gli esempi De Bari (attributi quasi tutti senza tipo, nomi in
  maiuscolo, molte relazioni senza nome) peggiorano il compatto. Da discutere prima del Passo 3b (pool unico, voce 115).

### [2026-10-10] Leva "validità del JSON compatto": esempi indentati e generazione vincolata — regola registrata PRIMA della run
- **Motivo**: il compatto (istruzioni v4, pool unico) ha 5-10 risposte su 40 non valide per errori di sintassi JSON
  (parentesi sbagliate o non chiuse con finish_reason `stop`) e R più basso del PlantUML v5 (voce 118). Una riparazione
  meccanica delle parentesi, provata sulle 16 risposte non valide di `dev_k`, `dev_v5base` e `dev_v5`, recupera 9 risposte
  a L4 ma quasi tutte con R = 0 (tronca le relazioni): scartata.
- **Varianti** (tre config, configurazione C-G, tutto il resto come `dev_v5base.yaml` C-G: Gemma 4 12B QAT, config v2,
  bm25 k = 3, pool unico, istruzioni v4 del compatto):
  - `dev_cindent.yaml` (**indent**): esempi del compatto serializzati indentati (`serialization: indent2`, stesso
    contenuto; oggi una sola riga lunga), generazione libera; prompt più lunghi (massimo stimato 6.259 token reali,
    budget 28.672);
  - `dev_cschema.yaml` (**schema**): generazione vincolata allo schema `generation/schemas/compact_generation.schema.json`
    (response_format di LM Studio; schema preparato nella voce 91 e finora disattivato), prompt identici alla baseline
    (40/40 sha256);
  - `dev_cboth.yaml` (**both**): entrambe.
  Baseline: `dev_v5base__C-G` (già generata). 3 × 40 = 120 generazioni.
- **REGOLA** (experiments/analyze_compact.py), per variante, delta = variante − baseline su 40 risposte: esclusa con 2 o
  più troncamenti per max_tokens; controllo preliminare come voce 98; **ammissibile se dM_primaria ≥ −0,03 e [(dVc ≥ +4
  e dR ≥ −0,03) oppure (dR ≥ +0,03 e dVc ≥ −2)]**; tra le ammissibili vince l'R più alto; entro 0,01 dal migliore vince
  la più semplice (indent < schema < both); nessuna ammissibile → resta la baseline. Le varianti con lo schema
  (generazione vincolata) restano **subordinate alla domanda 14** per i relatori: se vincono si propongono, non si
  adottano senza la loro risposta. Fuori regola: confronto con PlantUML v5 (`dev_v5__P-G`), motivi di invalidità,
  token, latenza.
- Test: `check_compact_lever` (config uguali alla baseline salvo la variante, esempi indentati con lo stesso contenuto,
  regola sulle soglie e sulla parità); il test "nessun config usa lo schema del compatto" ammette solo `dev_cschema` e
  `dev_cboth`. Script testato sulla sola baseline prima della run.
- **ESITO (2026-10-10, run `dev_cindent__C-G`, `dev_cschema__C-G`, `dev_cboth__C-G`, 120 generazioni, tutte `stop`, nessun
  troncamento; Gemma ricaricato con il comando fisso, GPU libera per la maggior parte della run)**: **tutte e tre le
  varianti AMMISSIBILI**; vince **both** (R più alto, nessuna altra entro 0,01), **subordinata alla domanda 14**
  (generazione vincolata).

  | run | V | Vc | J | R | M primaria | completamento med |
  |---|---|---|---|---|---|---|
  | baseline (dev_v5base C-G) | 35/40 | 33/40 | 0,452 | 0,210 | 0,156 | 542 |
  | indent | **40/40** | 38/40 | 0,539 | 0,264 | 0,214 | 778 |
  | schema | **40/40** | **40/40** | 0,543 | 0,250 | 0,202 | 736 |
  | both | **40/40** | **40/40** | 0,528 | **0,284** | **0,233** | 794 |
  | (riferimento) PlantUML v5 | 40/40 | 38/40 | 0,540 | 0,361 | 0,317 | 218 |

  Gli esempi indentati da soli eliminano già tutte le risposte non valide (40/40) e alzano R di +0,054, senza dipendere
  dalla domanda 14. Il compatto resta sotto PlantUML v5 (R 0,284 contro 0,361) e produce risposte circa 3,5 volte più
  lunghe. Report: `dev_compact_analysis/summary.md`; report grafico (non versionato) `dev_compact_review/index.html`.
  **Da decidere** (non previsto dalla regola): cosa usare per il compatto finché la domanda 14 non ha risposta.

### [2026-10-10] Varianti del retriever che usano il diagramma dei candidati — piano APPROVATO, parametri fissati PRIMA dei calcoli
- **Decisione dell'utente**: provare tutte le modifiche proposte, come **varianti separate e combinabili** (per attribuire
  gli effetti), lasciando BM25 congelato come baseline. Le varianti 2, 4, 5 e 2s / 2d usano il **diagramma dei
  candidati** (lecito: del diagramma della query non si usa nulla; da dichiarare in tesi: non è più un retrieval solo
  testuale). Niente alias scritti a mano (costo, soggettività, rischio di adattamento agli esercizi di valutazione, che
  sono anche candidati): misura a supporto, l'88% dei token dei nomi di classe di un esercizio compare già nella sua
  traccia (mediana 86% dei nomi interi), quindi il problema è il vocabolario tra esercizi diversi, affrontato in modo
  automatico (2s, 2d).
- **Passi**: (1) analisi a costo zero, sulle generazioni di sviluppo già fatte, delle proprietà degli esempi associate a
  risposte migliori; (2) implementazione con test; (3) valutazione del solo retrieval in leave-one-out sugli 80
  esercizi (pool di 79), descrittiva; (4) generazioni di sviluppo solo per le varianti scelte allo STOP dopo il passo 3,
  con una regola scritta prima; nel 3b al massimo una variante accanto a BM25 e MiniLM; (5) allineamento degli script di
  analisi del retrieval al pool unico.
- **Varianti e parametri (fissati ora, non si tarano)**. Base = BM25 congelato sulla descrizione (`config_bm25.yaml`).
  Combinazione con la base sempre per **RRF, c = 60** (come l'ibrido, voce 107), salvo dove indicato.
  - **2 struttura (BM25)**: secondo indice BM25 (k1 1,5, b 0,75, stesso preprocessing congelato) i cui documenti sono i
    token dei nomi di classe del diagramma del candidato (CamelCase spezzato, come `relevance.name_tokens`); query =
    descrizione della query. Finale = RRF(BM25 descrizione, BM25 struttura).
  - **2s struttura + sinonimi WordNet**: come 2, con i token dei nomi di classe espansi con i lemmi del **primo
    significato nominale** di WordNet (parole composte spezzate); WordNet via nltk, versione fissata, dati scaricati una
    volta e poi offline.
  - **2d struttura densa**: coseno MiniLM (voce 108) tra la descrizione della query e il testo dei nomi di classe del
    candidato (token minuscoli separati da virgole). Finale = RRF(BM25 descrizione, struttura densa).
  - **3 diversità (MMR)** sulla base: λ = 0,7; rilevanza = score BM25 normalizzato min-max sul pool; somiglianza tra
    candidati = Jt tra i loro nomi di classe; si scelgono i k esempi uno alla volta.
  - **4 costrutti**: segnali nella descrizione della query (espressioni regolari fissate ora) — ereditarietà: "is a
    (kind|type) of", "kinds of", "types of", "either … or", "can be (a|an|either)", "subclass", "special(ized|
    ization|kind)", "is a specific"; parte-tutto: "consist(s) of", "composed of", "made (up )?of", "part of",
    "contain(s)", "comprise(s)". Ranking dei costrutti = numero di costrutti segnalati presenti nel candidato
    (generalizzazione; composizione o aggregazione), parità per rango BM25. Finale = RRF(BM25, costrutti); senza segnali
    = BM25.
  - **5 qualità**: qualità del candidato q = 1 − (quota di relazioni non di generalizzazione senza entrambe le
    molteplicità + quota di attributi senza tipo) / 2; finale = score_norm BM25 × q (nessun RRF).
  - **6 MiniLM a pezzi**: descrizione divisa in pezzi di al più 256 token del tokenizer di MiniLM (senza
    sovrapposizione), media degli embedding normalizzati dei pezzi, poi rinormalizzata.
- **Misure del passo 3** (descrittive, nessun embedding): J, Jt, S a k = 1, 2, 3 (voce 107), **copertura dei tipi** (quota
  dei tipi di relazione del GT della query presenti in almeno uno dei 3 esempi), hubness. **Attenzione**: le varianti
  2 / 2s / 2d confrontano la traccia con i nomi di classe dei candidati, e J / Jt misurano i nomi di classe: sono
  favorite per costruzione (come BM25 sulle misure lessicali, voce 107). Il giudizio vero è delle generazioni (passo 4).
- **Passo 1 (fatto, `experiments/analyze_examples.py`, `data/results/generation/dev_examples_analysis/summary.md`)**: 640
  risposte di sviluppo di Gemma con istruzioni v4 (dev_k, dev_retrievers, dev_v5base); Spearman tra gli scarti dalla
  media dello stesso esercizio e formato. **PlantUML**: nessuna proprietà degli esempi associata alla qualità (tutti i
  |rho| ≤ 0,09, p ≥ 0,1). **Compatto**: copertura dei tipi di relazione della query **+0,22 (p < 0,001)**, dimensione
  degli esempi +0,19 (p 0,001), numero di esempi +0,15 (p 0,006); somiglianza dei nomi di classe −0,07 (n.s.), qualità
  del GT −0,04 (n.s.), quota De Bari −0,02 (n.s.). Indizio a favore della variante 4 (costrutti), non della 2.
- **Passo 2 (fatto)**: `retrieval/structure_retrievers.py` (StructureBM25 con opzione sinonimi, StructureDense, RRF, MMR,
  ConstructBoost, QualityWeighted), `DenseRetriever(chunk_tokens=...)` con cache separata (`..._chunk256.npz`); nltk
  3.10.3 + WordNet 3.0 (torch invariato; dati scaricati una volta). Test `check_structure_retrievers` (dati finti).
- **Passo 3 (fatto, `retrieval/analyze_variants.py`, run `data/results/retrieval/variants_2026-10-10_2b74319/`)**, LOO
  sugli 80 (pool di 79):

  | retriever | J@3 | Jt@3 | S@3 | copertura@3 | ∩ top-3 con bm25 | mai nei top-3 |
  |---|---|---|---|---|---|---|
  | bm25 | 0,078 | 0,096 | 0,666 | 0,877 | 1,00 | 10 |
  | dense (MiniLM) | 0,060 | 0,075 | 0,640 | 0,874 | 0,40 | 8 |
  | hybrid | 0,070 | 0,088 | 0,653 | 0,886 | 0,64 | 6 |
  | v2 struttura BM25 | 0,084 | 0,106 | 0,660 | 0,873 | 0,72 | 8 |
  | v2s + sinonimi | 0,081 | 0,104 | 0,652 | 0,873 | 0,69 | 7 |
  | v2d struttura densa | 0,080 | 0,099 | 0,659 | 0,884 | 0,66 | 12 |
  | v3 MMR | 0,076 | 0,094 | 0,668 | 0,886 | 0,95 | 9 |
  | v4 costrutti | 0,059 | 0,075 | 0,645 | **0,912** | 0,70 | 11 |
  | v5 qualità | 0,070 | 0,089 | 0,667 | 0,881 | 0,81 | 17 |
  | v6 MiniLM a pezzi | 0,063 | 0,077 | 0,649 | 0,894 | 0,42 | 7 |

  v2 / v2s migliorano J e Jt di poco (come atteso per costruzione); v4 ha la copertura dei tipi più alta (la proprietà
  associata alla qualità nel compatto al passo 1); v3 quasi uguale a bm25; v5 concentra gli esempi (17 candidati mai
  nei top-3); v6 poco diverso da MiniLM. Solo descrittivo: la scelta di cosa generare allo STOP.

### [2026-10-10] Configurazione di lavoro del compatto (esempi indentati) e passo 4 delle varianti del retriever — regola registrata PRIMA della run
- **Decisione dell'utente sul compatto** (voce 119, esito "both" subordinato alla domanda 14): **opzione (a)**, finché la
  domanda 14 non ha risposta il compatto usa le istruzioni v4 con gli **esempi indentati** (`serialization: indent2`,
  variante "indent", ammissibile e indipendente dalla domanda 14); se i relatori approvano la generazione vincolata si
  passa a "both" (stesso config + schema). **Configurazione di lavoro**: PlantUML istruzioni v5 (voce 118); compatto
  istruzioni v4 + esempi indentati; pool unico; Gemma 4 12B QAT, config v2, k = 3.
- **Passo 4 delle varianti del retriever (voce 120)**: condizioni nuove del prompt builder (`STRUCTURE_CONDITIONS`):
  `struct` (v2: RRF(bm25, BM25 sui nomi di classe dei candidati)), `construct` (v4: spinta ai costrutti segnalati dalla
  traccia), `struct_construct` (v2 + v4: ConstructBoost(RRF(bm25, struttura))); indici rifittati su `pool(query)`;
  identiche ai top-3 del passo 3 (0 differenze su 80 per struct e construct). Config `dev_structP.yaml` (P-G, uguale a
  `dev_v5.yaml` salvo le condizioni) e `dev_structC.yaml` (C-G, uguale a `dev_cindent.yaml` salvo le condizioni): 3 × 2 ×
  20 × 2 = **240 generazioni**. Baseline bm25 già generate con la stessa configurazione: `dev_v5__P-G`,
  `dev_cindent__C-G`.
- **REGOLA** (`experiments/analyze_struct.py`): una variante **entra nel Passo 3b** (accanto a bm25 e MiniLM) se **in
  entrambi i formati** dR ≥ −0,03, dVc ≥ −2, dM_primaria ≥ −0,03 e meno di 2 troncamenti (controllo preliminare come voce
  98), **e in almeno un formato dR ≥ +0,03**; tra quelle che entrano vince la media di dR sui due formati più alta, entro
  0,01 la più semplice (construct < struct < struct_construct); nessuna → nel 3b restano bm25 e MiniLM.
- **Controlli prima della run**: con il codice attuale i prompt bm25 delle baseline si riproducono identici (sha256 ed
  esempi, 60/60 per formato); i prompt delle varianti differiscono dalla baseline SOLO negli esempi (60/60); esempi in
  comune con bm25 (su 60): struct 43, construct 43, struct_construct 31; prompt più lungo stimato 4.620 token (P-G) e
  7.260 (C-G, esempi indentati) contro un budget di 28.672. Test `check_struct_lever`; script testato sulle sole baseline.

### [2026-10-10] Varianti del retriever, passo 4: esito (nessuna entra nel 3b)
- **Run**: `dev_structP__P-G` e `dev_structC__C-G`, 240 generazioni, tutte `stop`, nessun troncamento; Gemma ricaricato con
  il comando fisso (log in `dev_v5_model_load.log`). Analisi `experiments/analyze_struct.py`,
  `data/results/generation/dev_struct_analysis/summary.md`; report grafico (non versionato) `dev_struct_review/index.html`.
- **Esito della regola della voce 121 (meccanico)**: **nessuna variante entra nel Passo 3b**; nel 3b restano bm25 e MiniLM
  (**correzione, voce 123**: e l'ibrido, ammesso dalla voce 110).

  | formato | retriever | V | Vc | R | M primaria |
  |---|---|---|---|---|---|
  | PlantUML | bm25 (baseline) | 40 | 38 | 0,361 | 0,317 |
  | PlantUML | v4 costrutti | 40 | 39 | 0,344 | 0,298 |
  | PlantUML | v2 struttura | 40 | 39 | 0,364 | 0,307 |
  | PlantUML | v2 + v4 | 40 | 38 | 0,349 | 0,288 |
  | compatto | bm25 (baseline) | 40 | 38 | 0,264 | 0,214 |
  | compatto | v4 costrutti | 40 | 37 | 0,276 | 0,220 |
  | compatto | v2 struttura | 40 | 38 | 0,278 | 0,210 |
  | compatto | v2 + v4 | 40 | 36 | 0,273 | 0,191 |

  Tutte le differenze di R sono entro ±0,02 (rumore, con 2 ripetizioni); nessuna variante peggiora oltre le soglie, ma
  nessuna raggiunge +0,03 in un formato. Coerente con l'oracolo (voce 110) e con l'analisi del passo 1 (voce 120): in
  PlantUML gli esempi contano poco; nel compatto la copertura dei tipi era associata alla qualità, ma la spinta ai
  costrutti (v4) la migliora poco (0,912 contro 0,877) e non si traduce in un guadagno misurabile.
- **Per la tesi**: usare il diagramma dei candidati (nomi di classe, costrutti) non migliora le generazioni rispetto a
  bm25 su questo corpus e con questo modello: risultato negativo da riportare. Il codice resta nel repository.

### [2026-10-11] Due verifiche prima del Passo 3b: compatto v5 + esempi indentati e pool dei soli 60 del corpus — regole registrate PRIMA delle run
- **Run** (Gemma 4 12B QAT, config v2, bm25 k = 3, 2 ripetizioni, 20 esercizi di sviluppo; 120 generazioni):
  1. `dev_c5indent__C-G` (`dev_c5indent.yaml`): compatto con istruzioni **v5 + esempi indentati**, pool unico.
     Baseline `dev_cindent__C-G` (v4 + esempi indentati, stesso pool).
  2. `dev_poolC__C-G` e 3. `dev_poolC__P-G` (`dev_poolC.yaml`): configurazione di lavoro di ciascun formato (compatto v4
     + indent; PlantUML v5) con il **pool dei soli 60 del corpus** (nessun esempio De Bari; LOO sulle query del corpus).
     Baseline `dev_cindent__C-G` e `dev_v5__P-G` (pool unico).
- **Codice**: opzione di config `pool: all | corpus60` (default `all`, invariato), `PromptBuilder(pool=...)`: con
  `corpus60` i candidati di qualunque query sono i 60 del corpus meno la query (59 per una query del corpus, 60 per una De
  Bari); una configurazione può precisare le proprie chiavi di prompt (`configurations.<nome>.prompt`, usato da
  `dev_poolC` per avere v5 in P-G e v4 + indent in C-G). Test `check_pool_lever`.
- **Controlli prima delle run**: baseline riprodotte dal codice attuale (sha256, 20/20 per ciascuna); run 1: esempi
  identici alla baseline 20/20, differenze solo nelle istruzioni, nella frase del blocco esempi e nella riga finale della
  traccia (20/20); run 2 e 3: prompt identici alla baseline fuori dagli esempi (20/20), nessun esempio De Bari e mai la
  query tra i propri esempi; esempi diversi in **12 esercizi** (Boeing, Bookmaker, ClothingCompany, EUScienceConnect,
  Ebike, Facepage, FitnessCompanyConan, HelpingHands, HospitalHouseMD, InsuranceCompany, OilWells, Restaurant), gli
  stessi 12 cambiati dal pool unico rispetto a `dev_k`; 8 invariati.
- **REGOLA A** (compatto v5): adottare v5 per il compatto se **(dR ≥ +0,03 OPPURE dR_fam ≥ +0,03) E dVc ≥ −2 E
  dM_primaria ≥ −0,03**. Se adottata diventa la configurazione di lavoro del compatto, e "both" diventa v5 + indent +
  schema (sempre subordinato alla domanda 14).
- **REGOLA B** (pool): il Passo 3b usa il pool dei soli 60 del corpus se **nel compatto dR(corpus60 − all) ≥ +0,05 E in
  PlantUML dR ≥ −0,03 E in nessuno dei due formati dVc < −2**; altrimenti resta il pool unico. Si riporta anche R
  separato per i 12 esercizi con esempi cambiati e per gli 8 invariati.
- **Interazione**: se A e B cambiano entrambi la configurazione, la combinazione (v5 del compatto con il pool dei 60)
  NON si testa qui: si registra come combinazione per il 3b e si dichiara.
- **Se vince il pool dei 60 (conseguenze da registrare)**: per le query De Bari i candidati sono i 60 del corpus (nessun
  altro De Bari); sparisce la contaminazione 3 della voce 117 per quanto riguarda gli esempi De Bari nelle run di
  sviluppo, e l'analisi sui 20 De Bari torna alla pari con De Bari et al. (contaminazione 4); le run di sviluppo fatte
  con il pool unico restano valide come storico.
- **Ibrido nel 3b (chiarimento)**: l'ibrido **NON è escluso**. La voce 110 lo ammette al 3b (nessuna esclusione dalla
  regola) e nessuna decisione successiva lo ha tolto; nella voce 122 la frase "nel 3b restano bm25 e MiniLM" è
  un'imprecisione di chi scrive: va letta "nel 3b restano bm25, MiniLM e l'ibrido (voce 110); nessuna delle varianti della
  voce 120 si aggiunge". Una sua eventuale esclusione è una decisione da prendere esplicitamente.
- **GPU**: le run si eseguono con la GPU libera (nessun altro programma), annotato nel log di caricamento.

### [2026-10-11] Verifiche prima del 3b: esito delle regole A e B
- **Run**: `dev_c5indent__C-G`, `dev_poolC__C-G`, `dev_poolC__P-G`, 120 generazioni, tutte `stop`, nessuna dalla cache,
  **GPU libera** (annotato in `dev_v5_model_load.log`). Analisi `experiments/analyze_pool.py`,
  `data/results/generation/dev_pool_analysis/summary.md`; report grafico (non versionato) `dev_pool_review/index.html`.
- **REGOLA A (meccanica): v5 ADOTTATA per il compatto** — dR +0,043, dR_fam +0,037, dVc −1, dM_primaria +0,049 (v4 + indent:
  R 0,264, Vc 38/40; v5 + indent: R 0,307, Vc 37/40, V 39/40). **Nuova configurazione di lavoro del compatto: istruzioni
  v5 + esempi indentati**; "both" diventa v5 + indent + schema (subordinato alla domanda 14).
- **REGOLA B (meccanica): resta il POOL UNICO** — compatto dR(corpus60 − all) +0,020 (< +0,05) e dVc −3 (< −2);
  PlantUML dR −0,009, dVc 0. Per i 12 esercizi con esempi diversi tra i due pool: PlantUML R 0,393 (unico) contro 0,376
  (60); compatto 0,278 contro 0,321; per gli 8 invariati R identico nei due pool (stessi prompt: 0,299 e 0,233).
  Le conseguenze previste per il pool dei 60 NON si applicano: restano le contaminazioni 3 e 4 della voce 117.
- **Da notare**: con gli esempi indentati l'effetto del pool sul compatto è piccolo (+0,043 sui 12 esercizi cambiati),
  molto lontano dal −0,159 osservato con gli esempi su una riga (voce 118): quel calo era legato soprattutto alla
  fragilità del compatto su una riga, non agli esempi De Bari in sé.
- **Configurazione di lavoro per il 3b**: PlantUML istruzioni v5; compatto istruzioni v5 + esempi indentati (con lo schema,
  "both", se la domanda 14 sarà positiva); pool unico (79 candidati per query); retriever bm25, MiniLM e ibrido (voce
  110; correzione della voce 123); Gemma 4 12B QAT, config v2, k = 3.

### [2026-10-11] Leva "thinking" di Gemma sul dev set — regola e config registrate PRIMA delle generazioni
- **Obiettivo**: misurare se accendere il ragionamento nativo di Gemma 4 12B QAT (stesso modello e quantizzazione, finora
  SPENTO, voce 87 e domanda 15) migliora i diagrammi. Test set ed esercizi di valutazione non toccati.
- **Meccanismo (FASE 1, verificato prima di questa voce con richieste di prova su un prompt banale, nessun esercizio)**:
  il parametro per richiesta **`reasoning_effort`** dell'API di LM Studio accende il ragionamento: testo in
  `reasoning_content`, separato dal contenuto, `usage.completion_tokens_details.reasoning_tokens` dal server. I livelli
  `low` / `medium` / `high` si comportano allo stesso modo (356-357 token di ragionamento sullo stesso prompt; è un
  interruttore), `none` lo spegne. Ignorati: `chat_template_kwargs.enable_thinking`, `enable_thinking`, `reasoning`.
  **L'impostazione salvata del modello (`enableThinking: false`) NON si tocca**: nessun ripristino necessario.
  Si usa `reasoning_effort: "high"` (equivalente agli altri livelli, scelto come valore esplicito).
- **Config `dev_think.yaml`**: identica alla configurazione di lavoro salvo il ragionamento: P-G istruzioni v5, C-G
  istruzioni v5 + esempi indentati (voce 124), bm25 k = 3, pool unico, 20 esercizi di sviluppo × 2 ripetizioni × 2
  formati = **80 generazioni**; temperatura 0,3, top_p 0,95, top_k 64, seme invariati; `thinking: true`;
  **max_tokens 8192** (ragionamento + risposta) → **versione di configurazione 3** (contesto 32768, max_tokens 8192), perché
  il runner impone contesto e max_tokens uguali tra run dello stesso modello e della stessa versione. Baseline:
  `dev_v5__P-G` e `dev_c5indent__C-G` (versione 2, max_tokens 4096: nessuna loro risposta è stata troncata, quindi il
  limite più basso non le ha penalizzate).
- **REGOLA**, per formato (delta = thinking − baseline, 40 risposte): **adottare il thinking se (dR ≥ +0,03 OPPURE dR_fam ≥
  +0,03) E dVc ≥ −2 E dM_primaria ≥ −0,03 E meno di 2 troncamenti E meno di 2 risposte con contenuto vuoto.**
  **Costo** (fuori dalla regola, obbligatorio nel report): mediana e massimo dei token di ragionamento, latenza mediana
  thinking contro baseline, stima delle ore del Passo 3b con il thinking (circa 2.300 generazioni). **Se la leva è
  adottata e la stima supera 30 ore, non si decide da soli**: si propone ai relatori su quali condizioni del 3b usarla.
- **Implementazione (prima delle generazioni)**: `GenerationParams.reasoning_effort` (inviato solo se impostato; chiave di
  cache invariata senza, verificato), `thinking: true` nel config → `reasoning_effort: "high"` (`THINKING_EFFORT`),
  `should_stop_on_reasoning` (stop disattivato SOLO con `thinking: true`; config normali invariati); ragionamento salvato
  nel raw (`reasoning_text`, `reasoning_tokens`), validazione solo sul contenuto; `analyze_instructions.load_run` accetta
  la versione di configurazione attesa (default 2, invariato); `experiments/analyze_think.py`; config `dev_think.yaml`
  (budget: prompt più lungo stimato 5.556 token + 8.192 contro un contesto di 32.768). Test `check_thinking`.
- **SMOKE TEST (FASE 1): FALLITO → STOP** (2 chiamate, Boeing P-G e Restaurant C-G, risultati fuori da data/results, nella
  cartella di lavoro della sessione): in entrambi il ragionamento consuma **tutti gli 8.192 token** (8.189 di
  ragionamento), **contenuto vuoto**, finish_reason `length`, circa 210-225 s per chiamata. Il ragionamento è separato
  correttamente (`reasoning_content`, nessun marcatore nel contenuto), ma **entra in un ciclo di autoverifica**
  ("*Wait, …*" ripetuto): Boeing 411 righe di cui 110 distinte (la stessa relazione ripetuta 40 volte), Restaurant 469
  righe di cui 395 distinte, con lo stesso schema di ricontrollo. Le 80 generazioni NON sono state lanciate.
  L'impostazione salvata del modello non è stata toccata (ragionamento spento per tutte le altre run).
- **Sotto-voce (2026-10-11, decisione dell'utente dopo lo smoke test fallito): UN SOLO tentativo, poi chiusura se
  fallisce.** La regola di adozione resta invariata per il resto.
  - **Trattamento**: ragionamento acceso con `reasoning_effort: "low"` (accettato da LM Studio: nello smoke del meccanismo
    `low` funzionava come gli altri livelli) **e temperatura 1,0**; altri parametri invariati (top_p 0,95, top_k 64, seme),
    max_tokens 8192, versione di configurazione 3. Config `dev_think.yaml` aggiornato (`thinking: low`, temperatura 1,0).
  - **Controllo nuovo**: temperatura 1,0 SENZA ragionamento, stessi config (versione 3, max_tokens 8192): `dev_temp1.yaml`,
    per separare l'effetto della temperatura da quello del ragionamento.
  - La **regola di adozione** si applica al trattamento contro la baseline attuale (temperatura 0,3, nessun ragionamento:
    `dev_v5__P-G`, `dev_c5indent__C-G`). Nel report: (a) trattamento contro baseline, (b) controllo contro baseline,
    (c) trattamento contro controllo = effetto del solo ragionamento. **Se il trattamento è adottato, la nuova
    configurazione cambia SIA il ragionamento SIA la temperatura**: va dichiarato.
  - **Smoke test**: 4 chiamate (Boeing e Restaurant, PlantUML e compatto) con il trattamento. **Criterio fissato ora**: la
    leva si CHIUDE (opzione 4: ragionamento spento in tutta la pipeline, risultato negativo registrato, nessuna run da 80)
    se anche UNA risposta ha contenuto vuoto, finish_reason `length` o un **ciclo evidente** nel ragionamento, definito
    come: righe distinte / righe totali < 0,6 OPPURE una stessa riga di almeno 20 caratteri ripetuta 5 o più volte (righe
    non vuote, spazi ai bordi tolti). Se passa: 80 generazioni del trattamento + 80 del controllo.
- **SMOKE TEST DEL TRATTAMENTO (low + temperatura 1,0): criterio violato → LEVA CHIUSA (opzione 4).** 4 chiamate (Boeing
  e Restaurant, PlantUML e compatto; risultati nella cartella di lavoro della sessione, non in data/results; eseguito con
  la GPU CONDIVISA con un altro programma, che pesa solo sulla latenza, non sui criteri):

  | chiamata | finish | livello | ragionamento (token) | righe distinte / totali | riga più ripetuta (n) | latenza |
  |---|---|---|---|---|---|---|
  | C-G Boeing | stop | 4 | 6.288 | 284 / 304 (0,93) | `- sourceMultiplicity: "1", targetMultiplicity: "*"` (**5**) | 194 s |
  | C-G Restaurant | stop | 4 | 6.760 | 370 / 387 (0,96) | 3 | 199 s |
  | P-G Boeing | stop | 4 | 5.198 | 249 / 272 (0,92) | 3 | 132 s |
  | P-G Restaurant | stop | 4 | 7.169 | 401 / 444 (0,90) | `Waiter "1" -- "*" Customer : serves` (**8**) | 204 s |

  Due risposte su quattro violano la clausola "una riga di almeno 20 caratteri ripetuta 5 o più volte": criterio
  applicato meccanicamente, la leva si chiude. **Da notare (non cambia l'esito)**: con temperatura 1,0 e `low` il ciclo
  grave del primo smoke test sparisce (tutte e quattro le risposte finiscono, `stop`, a L4, rapporto di righe distinte
  0,90-0,96); le ripetizioni rimaste sono righe di bozza riprese più volte durante l'autoverifica. **Costo**: 5.200-7.200
  token di ragionamento e 130-200 s per generazione (con la GPU condivisa; anche a velocità piena circa 40 token/s, cioè
  2-3 minuti): il Passo 3b (circa 2.300 generazioni) richiederebbe **oltre 80 ore**, molto oltre la soglia di 30.
- **Conseguenze**: **ragionamento SPENTO in tutta la pipeline** (nessun config attivo ha `thinking`; l'impostazione salvata
  di LM Studio non è mai stata toccata); la risposta sperimentale alla domanda 15 è "spento". Le run da 80 (trattamento e
  controllo) NON sono state lanciate; `dev_think.yaml` e `dev_temp1.yaml` restano come documentazione, insieme al codice
  (`reasoning_effort`, `thinking`, `analyze_think.py`), che non cambia nulla per i config senza `thinking`.

### [2026-10-11] Leva "piano breve" (istruzioni v5plan) sul dev set — regola e config registrate PRIMA delle generazioni
- **Obiettivo**: misurare se chiedere al modello un piano breve, ancorato al testo, PRIMA del diagramma migliora i
  diagrammi (ragionamento esplicito nel contenuto, a costo contenuto, dopo la chiusura della leva thinking, voce 125).
  **Un solo tentativo**: nessuna iterazione sul testo delle istruzioni dopo aver visto i risultati. Test set ed esercizi di
  valutazione non toccati.
- **Testi (congelati, sha256 nel test `check_plan`)**: `generation/templates/v5plan_plantuml_instructions.txt` e
  `v5plan_compact_instructions.txt` = istruzioni v5 del formato con il **solo paragrafo OUTPUT FORMAT sostituito**: la
  risposta ha esattamente due parti, `PLAN:` (al più 15 righe, una per classe `- Name: citazione breve` e una per
  relazione `- Relationship A - B: tipo, molteplicità in A, molteplicità in B: citazione breve`, citazioni di al più 10
  parole; solo ciò che il testo sostiene) e `DIAGRAM:`. **Adattamento dichiarato**: la frase del DIAGRAM riprende quella
  della v5 di ciascun formato (PlantUML: un solo blocco da @startuml a @enduml, solo dichiarazioni di classe e relazioni;
  compatto: un solo oggetto JSON nel formato indicato), senza recinti Markdown e niente dopo. Riga finale della traccia:
  "Now write the PLAN and then the DIAGRAM for this system only." Blocco esempi ed esempi recuperati **identici alla
  v5**: gli esempi mostrano **SOLO diagrammi** (nessun piano di esempio).
- **Post-processing** (`generation/plan_split.py`): si valida e si misura **solo la parte dopo il marcatore `DIAGRAM`**
  (prima riga che inizia con DIAGRAM, con eventuale `**` o `#`); il piano si salva a parte (`plans/<call_id>.txt`), nel
  manifest `plan_marker_found`, `plan_lines`, `plan_chars`. Senza marcatore si valida l'intera risposta e il caso si conta.
  Le run non v5plan sono invariate (verificato nel test).
- **Config `dev_plan.yaml`**: identico alle baseline salvo `prompt.instructions_version: v5plan` (verificato: config
  risolti uguali in tutto il resto; prompt diversi solo nelle istruzioni e nella riga finale, 20/20 per formato). P-G
  PlantUML, C-G compatto con esempi indentati, bm25 k = 3, pool unico, temperatura 0,3, top_p 0,95, top_k 64, seme 42,
  max_tokens 4096, **versione di configurazione 2**, ragionamento spento; 20 esercizi di sviluppo × 2 ripetizioni × 2
  formati = **80 generazioni**. Baseline: `dev_v5__P-G` e `dev_c5indent__C-G`.
- **REGOLA**, per formato (delta = piano − baseline, 40 risposte; metriche sul solo diagramma): **adottare v5plan se (dR ≥
  +0,03 OPPURE dR_fam ≥ +0,03) E dVc ≥ −2 E dM_primaria ≥ −0,03 E meno di 2 troncamenti E latenza mediana ≤ 2,5 × quella
  della baseline**, latenza **misurata con la GPU libera**. **Se adottata in un formato, v5plan diventa la configurazione
  di lavoro di quel formato per TUTTE le condizioni del 3b.** Nel report, fuori dalla regola: marcatore mancante, token di
  output, stima delle ore del 3b (circa 2.300 generazioni), coerenza piano-diagramma, 3 esempi in cui il piano migliora R
  e 3 in cui peggiora. Implementazione: `experiments/analyze_plan.py` (costanti e `adopt`, testati prima della run).
- **SMOKE TEST (FASE 1): superato** (2 chiamate, Boeing P-G e Restaurant C-G, risultati nella cartella di lavoro della
  sessione, non in data/results; GPU CONDIVISA con un altro programma, latenze non rappresentative): entrambe `stop`,
  livello 4, marcatore trovato (P-G "DIAGRAM" senza i due punti, gestito), piano di 11 righe (522 e 589 caratteri),
  diagramma valido senza testo dopo. **Osservazioni (non cambiano i testi, un solo tentativo)**: il modello copia
  letteralmente il segnaposto `- Class Name: …`; in P-G le righe di relazione del piano omettono tipo e molteplicità.
  Il primo fatto rompe il conteggio delle classi del piano in `analyze_plan.plan_classes` (metrica di coerenza, fuori
  dalla regola): restituisce "name" → correzione del solo parser da approvare prima della FASE 2.

### [2026-10-11] Riproducibilità prima del Passo 3b — nessuna modifica a dati, GT o configurazione
- **Clone pulito**: le suite devono girare su un clone fresco da GitHub, dove mancano le parti non versionate.
  - **nltk / WordNet**: usato SOLO dalla variante 2s del retriever (`retrieval/structure_retrievers.py`, voce 120, non
    entrata nel 3b, voce 122). L'import era già pigro (dentro `wordnet_expand`); aggiunti `wordnet_missing()` (nltk non
    installato oppure dati WordNet non scaricati) e un errore chiaro con le istruzioni in `wordnet_expand`. In
    `retrieval/test_retrieval.py` i due controlli della 2s vengono SALTATI con un messaggio se manca qualcosa; nessun
    download a runtime. `requirements.txt`: `nltk==3.10.3` come riga commentata, dipendenza OPZIONALE documentata
    (installazione e `python -m nltk.downloader wordnet` a mano).
  - **`corpus/raw/translated_it/`** (non versionata, licenza): in `corpus/test_apollon_convert.py` il decoratore
    `needs_translated` SALTA con un messaggio i test che la leggono (oggi solo `check_shared_type_glossary`, l'unico
    che falliva sul clone); tutti gli altri girano. Documentato in `corpus/README.md`.
  - **Prova eseguita** (2026-10-11): clone da GitHub (`ec59fb4`, l'ultimo commit pubblicato) con sopra le modifiche
    NON committate del working tree (file modificati e nuovi non ignorati: lo stato che il repo avrà dopo il commit),
    in una cartella temporanea; ambiente virtuale NUOVO (Python 3.12.10) da `requirements.txt`. Esito: **quattro suite
    verdi** (corpus, retrieval, generazione e la nuova delle metriche), con i due salti attesi (glossario condiviso;
    variante 2s, nltk non installato). Senza versioni fissate pip ha installato versioni più recenti di quelle delle
    run (torch 2.14.1, numpy 2.5.4, pandas 3.0.6, scikit-learn 1.9.1, openai 3.29.0, …): le suite passano lo stesso,
    comprese le 12 analisi ricalcolate identiche. Seconda prova con un altro ambiente nuovo da `requirements-lock.txt`
    sullo stesso clone: installazione senza errori, quattro suite verdi (la 2s qui gira: nltk è nel lock e i dati
    WordNet sono nella cartella utente di nltk di questo PC). I modelli densi non servono alle suite (i test non
    caricano sentence-transformers).
- **Ambiente**: tutte le run fino a oggi usavano il Python 3.12.10 di Microsoft Store con i pacchetti nel sito utente
  (nessun ambiente virtuale). `requirements-lock.txt` = `pip freeze` di quell'ambiente (131 pacchetti attivi), con una sola
  modifica a mano dichiarata nell'intestazione: `torchaudio==2.6.0+cu124` commentato (build CUDA non su PyPI, mai
  importato, incompatibile con torch 2.10.0: conflitto già nei "Limiti noti"). Il lock contiene anche pacchetti di
  altri progetti presenti nel sito utente (es. ultralytics, wandb, opencv): lasciati, perché il lock descrive
  l'ambiente reale delle run. **Il 3b si esegue in un ambiente virtuale dedicato `.venv` creato dal lock**: procedura
  in docs/STATUS.md, sezione "Ambiente della tesi".
- **Metriche congelate per il 3b**: `evaluation/metrics.py` (prima conteneva solo funzioni segnaposto mai usate) ora
  contiene, SPOSTATE senza modifiche, le funzioni di `analyze_pilot.py` (norm, class_names, norm_mult, edges,
  compare_relations), `analyze_dev.py` (is_valid, is_clean, metrics → `core_metrics`: V, Vc, J, R),
  `analyze_instructions.py` (match, gt_ends, resp_mult, multiplicity_counts, metrics → `multiplicity_metrics`: M
  primaria e secondaria, verso; confusion: generalizzazioni invertite, classi e generalizzazioni in più) e
  `analyze_v5.py` (r_fam, extra_compositions, all_metrics), con le costanti. Gli script storici le **riesportano con
  gli stessi nomi** (stessi oggetti, non copie), quindi tutti i chiamanti (`ap.edges`, `ad.metrics`, `ai.confusion`,
  `av.all_metrics`, …) restano invariati. Jaccard resta in `retrieval/corpus_loader.py`, riesportato.
  **Test** `evaluation/test_metrics.py`: riesportazioni; un esempio calcolato a mano; ricalcolo delle **12 analisi
  versionate** (pilota, pilota 2 e la sua v2, formati, k, istruzioni, v5, compatto, pool, retriever, struttura,
  esempi) su una copia temporanea dei soli file versionati delle run: ogni summary.md rigenerato è **identico riga per
  riga** a quello versionato, salvo la riga di provenienza. Verificato anche prima dello spostamento: con il codice
  precedente le stesse 12 analisi erano già identiche, e prima e dopo coincidono. La valutazione semantica (livello 2)
  andrà nello stesso pacchetto, in un compito separato.
- **Backup**: promemoria per l'utente in docs/STATUS.md (copia PRIVATA di `corpus/raw/translated_it/`, mai nel repo).

### [2026-10-11] Qualità del ground truth per sorgente — SOLO DESCRITTIVO (nessuna modifica a dati, GT o configurazione)
- **Scopo**: documentare, da citare come limiti in tesi, quanto il GT delle tre sorgenti è disomogeneo. Nessun dato è
  stato cambiato; i numeri sono calcolati sui `diagram_apollon_json` e sulle `description` attuali di
  `corpus/processed/corpus.jsonl` e `testset_debari.jsonl` (80 esercizi), sorgente da `corpus/roles.yaml`.
- **Definizioni**: attributi = attributi delle classi non enumerazione, "senza tipo" se non contengono `:`; estremi =
  i due estremi delle relazioni che non sono generalizzazione o realizzazione, "vuoto" se la molteplicità è vuota;
  associazioni = bidirezionali e unidirezionali, "senza nome" se l'etichetta è vuota.

  | sorgente | esercizi | attributi senza tipo | estremi con molteplicità vuota | associazioni senza nome | ... e senza ruoli | tracce con indicazioni per lo studente |
  |---|---|---|---|---|---|---|
  | Golden UML Modelset (`golden`) | 45 | 2 / 586 (0,3%), 2 esercizi | 39 / 812 (4,8%), 4 esercizi | 314 / 339 (92,6%) | 251 / 339 (74,0%) | 6 (+1 dubbia) |
  | tradotti dall'italiano (`translated_it`) | 15 | 3 / 167 (1,8%), 2 esercizi | 38 / 186 (20,4%), 6 esercizi | 57 / 78 (73,1%) | 46 / 78 (59,0%) | 0 |
  | test set De Bari (`debari`) | 20 | 187 / 264 (70,8%), 13 esercizi | 44 / 252 (17,5%), 9 esercizi | 79 / 103 (76,7%) | 65 / 103 (63,1%) | 1 |

- **Tracce con indicazioni per lo studente** (ricerca per parole chiave, poi lettura delle frasi trovate: NON
  esaustiva; esclusi i domini in cui "student" è un concetto del sistema, es. School, OnlineTutoringSystem):
  golden: FitnessCompanyConan ("you can consider address as atomic", "You can assume that…", sviluppo), GameArea
  ("Ignore the visibilities.", valutazione), GasStation_TUW ("Model the following situation using a UML class
  diagram…", valutazione), Musicmatic ("asked you to create a UML class diagram", "You can assume…", sviluppo),
  PizzaDeliveryWithEntertainment ("asks you to design the UML class diagram", sviluppo), SellingGoods (esercizio a
  passi: "This exercise teaches you…", "create a class diagram for the use case described in STEP 1…", "revise your
  model", valutazione); dubbia Menso ("For the sake of this case, we assume that…", ipotesi di modellazione, valutazione);
  De Bari: DB18_LibrarySystem ("The exercise id to design a class structure…", valutazione). Le uniche esclusioni di
  testo già applicate restano quelle di BuildingManagement e InsuranceCompany (`corpus/description_exclusions/`).
- **Lettura** (per la tesi): (1) il test set De Bari ha in gran parte attributi SENZA tipo (trascritti dalle immagini
  così come sono, non inventati; già nei "Limiti noti"), mentre il corpus li ha quasi sempre: un modello che segue gli
  esempi del corpus scrive tipi che il GT del test set non ha (le metriche J, R, M non guardano gli attributi, una
  futura metrica sugli attributi sì); (2) molteplicità vuote in circa un estremo su cinque nei tradotti e nel test set
  contro il 5% del golden: M primaria conta solo gli estremi espliciti, M secondaria anche quelli vuoti (voce 98), e
  gli esempi recuperati da sorgenti diverse insegnano abitudini diverse; (3) le associazioni sono quasi tutte senza
  nome in tutte le sorgenti (il golden ancora di più): i nomi di associazione non sono un criterio affidabile per una
  metrica; (4) poche tracce contengono istruzioni rivolte allo studente, che entrano nel prompt come parte della
  traccia della query o degli esempi; sono lasciate come sono (nessuna modifica dopo il congelamento).

### [2026-10-11] Retrieval pronto per il Passo 3b — nessuna nuova scelta, nessuna generazione
- **Premessa**: le scelte del retrieval sono chiuse (voci 105-110, 115, 122, 124): bm25 congelato, dense = MiniLM alla
  revisione fissata, hybrid = RRF c = 60, k = 3 (+ bm25 k = 2), pool unico (80 esercizi, 79 candidati per query). Qui si
  allinea il codice, si congela l'output e si descrive. Gli esercizi di valutazione sono usati SOLO come candidati e per
  costruire il file congelato: nessuna misura di pertinenza con uno di loro come query.
- **1. Pool unico negli script del Passo 2** (`corpus_loader.POOLS`, `load_pool`, `pool_queries`):
  - `analyze_retrieval.py`, `analyze_dense.py`: `--pool all80` (default) = 80 esercizi, 79 candidati per query,
    pertinenza SOLO sulle 26 query di sviluppo (quasi-duplicati solo per coppie con un esercizio di sviluppo);
    `--pool corpus59` = protocollo storico (59 candidati del corpus, Cruise escluso perché allora non convertito).
  - `run_testset.py`: `--protocol all80` (default: 60 + gli altri 19 De Bari) che si **rifiuta senza
    `--consenti-valutazione`** (i 20 De Bari sono di valutazione: si esegue dopo il 3b); `loo` (78) e `fixed59` restano
    i protocolli storici sui 59 senza Cruise. Non eseguito.
  - `hubness_report.py`: pool ricavato dal config.json delle run (storiche → corpus59), `--pool` per forzarlo.
  - **Riproduzione byte per byte** (`retrieval/check_protocols.py`, lento): loo_2026-10-04_stop1 (4 CSV identici,
    summary.md salvo run id, commit e riga di provenienza), dense_2026-10-09_22f5adf (3 CSV identici, summary.md salvo
    run id, provenienza e tempi), hubness di testset_2026-10-04_stop2 (CSV e summary.md identici). Nella suite
    (`check_pool_protocols`, secondi): top-3 di loo_stop1, testset_2026-10-04_stop2 (fixed59) e testset_2026-10-10_loo
    (loo) riprodotti (solo id e punteggi, nessuna pertinenza ricalcolata sul test set). Run versionate invariate.
- **2. File congelato degli esempi** (`retrieval/freeze_retrievals.py`): `data/retrieval_frozen/retrievals_3b.jsonl`
  (versionato, 400 righe = 80 query × {bm25 k = 2, bm25 k = 3, dense k = 3, hybrid k = 3, random k = 3}), sha256
  `6857259af6263cf69b81151f5424a371f5450397778e15e57c9235c1c0625bd5`; accanto `retrievals_3b.meta.json` con sha256 del
  file, commit, modello e revisione del denso (all-MiniLM-L6-v2 @ 1110a243…, CPU), versioni dei pacchetti, sha256 del
  CONTENUTO della cache degli embedding (vettori float32 degli 80 testi), dei config, di corpus.jsonl /
  testset_debari.jsonl / roles.yaml e del GT degli 80. Prodotto con lo STESSO codice del prompt builder
  (`PromptBuilder.hits`, estratto da `select()` senza cambiarne l'esito); con la stessa cache, due esecuzioni → stesso
  file byte per byte.
  - **Deriva osservata del denso (il motivo del file congelato)**: la prima versione del file (sha256 `b547aa63…`) e
    quella finale hanno gli STESSI esempi in tutte le 400 righe, ma 34 righe dense differiscono nel punteggio di al più
    1,2e-7 (un'unità in float32): nel frattempo le verifiche dei protocolli storici avevano ricalcolato gli embedding
    in lotti diversi e riscritto la cache. Il margine minimo del denso tra il 3° e il 4° candidato è 3,9e-4
    (GasStation_KUL; 4 query sotto 1e-3), dentro i top-3 4,7e-5 (ClothingCompany): migliaia di volte la deriva vista,
    quindi esempi stabili su questa macchina; su un'altra (CPU, librerie) la deriva può essere maggiore, ed è per questo
    che il 3b legge il file. Lo sha256 del file .npz della cache non è un'impronta stabile (l'archivio si riscrive):
    nei metadati c'è lo sha256 del contenuto.
  - **Random**: seme 0, quello dei config. Il runner passa a PromptSpec il `seed` del config, **uguale per tutte le
    ripetizioni**: gli esempi casuali cambiano tra esercizi (sha256 di seme e traccia) ma NON tra ripetizioni. Si
    congela il comportamento attuale; esempi casuali diversi per ripetizione sarebbero una scelta nuova (da decidere con
    la domanda 8 sulle ripetizioni).
  - **Prompt builder**: `retrieval_source: frozen` (bm25 / dense / hybrid / random dal file, sha256 verificato,
    chiave mancante → errore; struct / construct non congelate → rifiutate; solo con il pool unico). Runner: chiave di
    config `retrieval_source`, sha256 del file nella provenienza; **un config `passo: 3b` con condizioni di retrieval
    è rifiutato senza `retrieval_source: frozen`** (client finti esclusi, come per i ruoli); i template
    `gemma4_12b_qat_template.yaml` e `lmstudio_template.yaml` hanno `retrieval_source: frozen`.
  - **Identità dei prompt** (`generation/check_frozen.py`, denso reale; rieseguita sul file finale): 26 esercizi di sviluppo × 2 configurazioni
    di lavoro (P-G v5; C-G v5 + esempi indentati) × 5 condizioni = **260/260 prompt congelato = dal vivo** (sha256 dei
    messaggi come nel runner); **200/200 prompt dei manifest** di dev_v5 (P-G, C-G), dev_c5indent (C-G), dev_v5base (P-G,
    C-G) riprodotti dal file. dev_retrievers, dev_k e dev_instructions NON sono confrontabili: pool storico di 58 (i
    loro esempi coincidono con il file solo in 8-16 risposte su 40). Nella suite (`check_frozen`, senza denso reale):
    giro completo con embedding finti, bm25 / random dal file = dal vivo per i 26, 160 prompt dei manifest, rifiuti,
    provenienza, guardia del 3b.
  - **Pareggi esatti di punteggio** (ordinamento per id, come sempre): bm25 k = 2 e 3 e dense k = 3: **nessuno**;
    hybrid k = 3: **9 query con un pareggio dentro i top-3** (cambia solo l'ordine nel prompt: AirTravel, Boeing,
    DB07_BankSystem, DB09_AutoRepair, GasStation_TUW, LabTracker, RealEstateAgency, RepairShops, TransportCompany) e
    **2 al confine 3/4** (cambia l'esempio scelto: DB10_Restaurant, SellingGoods). Sono pareggi STRUTTURALI della RRF
    (ranghi scambiati, es. 1+2 contro 2+1: somme identiche), risolti per id in modo deterministico; tra macchine diverse
    il punto fragile resta il denso (coseno in float32 su CPU), da cui dipendono anche i ranghi dell'ibrido. Il file
    congelato toglie questa dipendenza dal 3b.
- **3. Analisi descrittiva sui 26 di sviluppo** (`retrieval/analyze_dev80.py`, run
  `data/results/retrieval/dev80_2026-10-11_ec59fb4/`, esempi dal file congelato):
  - Jt@3: bm25 0,092, hybrid 0,084, dense 0,070, random (seme 0) 0,023, random 20 semi 0,018 ± 0,004, oracolo 0,134
    (J@3: 0,077 / 0,066 / 0,055 / 0,018 / 0,014 / 0,112). Misure lessicali che favoriscono bm25 (voce 107).
    analyze_dense.py con `--pool all80` dà gli stessi valori (controllo incrociato).
  - Sovrapposizione dei top-3 (media |∩| / 3): bm25-dense 0,36, bm25-hybrid 0,58, dense-hybrid 0,62; con random ≤ 0,08.
  - Hubness (78 posti): candidati distinti 48 (bm25), 52 (dense), 48 (hybrid), 51 (random); massimo 4 (MilanLibrary),
    6 (DB14_BicycleRental), 5 (EatAtHome), 4.
  - Esempi De Bari tra i recuperati: 15 / 25 / 20 / 19 su 78 (bm25 / dense / hybrid / random), in 13 / 18 / 15 / 14
    query su 26; esempi di valutazione: 56 / 62 / 58 / 48 su 78 (contaminazione dichiarata nella voce 117).
  - Pertinenza contro qualità (26 gruppi di generazioni esistenti di Gemma a k = 3, run × configurazione ×
    condizione, 20 esercizi, Spearman tra Jt@3 degli esempi usati e R medio): **PlantUML rho da +0,23 a +0,50, mediana
    +0,33, positivi 10/10**; **JSON compatto da −0,01 a +0,29, mediana +0,13, positivi 13/14** (oracle_jt, diagnostica,
    a parte). Solo descrittivo: n = 20, gruppi non indipendenti, difficoltà dell'esercizio come confondente. Scatter
    `scatter_plantuml.png` e `scatter_compact.png` (versionati: eccezione aggiunta in .gitignore).
  - **PREVISTA, dopo il 3b** (non ora): la stessa analisi sui 54 di valutazione con gli esempi del file congelato e le
    run del 3b (n = 54; a parte 34 del corpus e 20 De Bari, e 19 senza DB06_Flights); `analyze_dev80.py --insieme
    valutazione` si rifiuta senza `--dopo-3b`.
- **4. Domanda 4 (DB06_Flights / AirTravel), stato e proposta per i relatori**: vedi docs/STATUS.md, domanda 4
  (aggiornata). Fatti nuovi dal file congelato: i due esercizi, ENTRAMBI di valutazione, sono l'uno il top-1
  dell'altro per bm25 (score_norm 0,645 e 0,544), dense e hybrid (in hybrid per AirTravel a pari punteggio con Boeing);
  AirTravel è anche l'esempio 2 del prompt statico, quindi per DB06_Flights il quasi-duplicato è presente in TUTTE le
  condizioni con esempi tranne random, e per AirTravel la condizione static non è definita (l'esempio coinciderebbe con
  la query: il builder la rifiuta).

### [2026-10-11] Decisioni dopo il report della voce 129 (approvato) — registrate PRIMA di qualsiasi run del Passo 3b
- **1. Condizione random: seme diverso per esercizio E ripetizione** (decisione dell'utente). Motivo: la condizione
  stima l'effetto ATTESO di esempi casuali; con lo stesso seme le ripetizioni misurerebbero sempre lo stesso sorteggio
  (voce 129: il runner passava a tutte le ripetizioni il `seed` del config).
  - **Funzione** (`generation/prompt_builder.random_seed`): `seme(id, r) = int(sha256("random|<id esercizio>|<r>")
    [primi 8 caratteri esadecimali], 16)`, cioè un intero a 32 bit deterministico, con r = indice di ripetizione (0, 1,
    2, …). Il RandomRetriever resta invariato: l'estrazione dipende da sha256(seme, traccia della query) sul pool
    ordinato per id.
  - **Runner**: chiave di config `random_seed` = `config` (default, comportamento storico: il `seed` del config per
    tutte le ripetizioni) | `per_esercizio_ripetizione` (seme(id, r) per la ripetizione r). Un config `passo: 3b` con la
    condizione random deve usare `per_esercizio_ripetizione` (rifiutato altrimenti; client finti esclusi, come per le
    altre guardie); i template del 3b lo impostano.
  - **File congelato**: si rigenera SOLO la parte random di `data/retrieval_frozen/retrievals_3b.jsonl` (80 esercizi ×
    ripetizioni 0, 1, 2 con il seme(id, r); le ripetizioni sono 3 come indicato dall'utente: se il 3b ne usera' di piu',
    vanno aggiunte, e una chiave mancante e' un errore, mai un'estrazione dal vivo); bm25 / dense / hybrid devono restare
    byte per byte identici (verificato, sotto). Nuovo sha256 nel `.meta.json`.
  - **Run di sviluppo**: restano storiche con il seme unico del config (seme 0 per tutte le ripetizioni); nessuna run di
    sviluppo usava la condizione random con generazioni, quindi nessun risultato esistente cambia.
- **2. Domanda 4 (DB06_Flights / AirTravel)**: adottata come PROPOSTA da portare ai relatori quella del report della
  voce 129: nessuna esclusione; risultati sui 54 di valutazione e sui 52 senza la coppia (De Bari su 20 e 19);
  confronto appaiato static contro retrieval su 53 (AirTravel non ha la cella static), con controllo su 52; la coppia
  come caso di studio qualitativo. Testo in docs/STATUS.md, domanda 4.
- **3. Piano di analisi del 3b: relazione pertinenza–qualità anche ENTRO esercizio** (da riportare nel protocollo):
  - TRA esercizi (già prevista, voce 129): per condizione e formato, Spearman tra Jt@3 degli esempi e R medio delle
    ripetizioni, un punto per esercizio;
  - ENTRO esercizio (nuova): per ogni esercizio e formato, scarti di Jt@3 e di R dalla media DELL'ESERCIZIO tra le
    condizioni di retrieval (bm25 k = 3, dense, hybrid, random; bm25 k = 2 a parte), poi correlazione (Spearman) sugli
    scarti messi insieme (un punto per esercizio × condizione); si riportano anche n, il numero di esercizi in cui le
    condizioni recuperano esempi con Jt@3 diverso (quelli che danno informazione) e lo scatter degli scarti.
  - **Nel testo della tesi**: la correlazione TRA esercizi può riflettere la DIFFICOLTA' dell'esercizio (esercizi con
    analoghi nel pool tendono ad avere GT più convenzionali e risposte migliori qualunque esempio si mostri) e non
    l'effetto del retrieval; quella ENTRO esercizio toglie questa componente, perché confronta esempi diversi per lo
    stesso esercizio. Entrambe restano descrittive (nessuna inferenza causale).
- **Esecuzione (2026-10-11)**:
  - `prompt_builder.random_seed`, `RANDOM_SEED_MODES`; runner: `random_seed` nel config, piano con il seme per
    ripetizione, guardia `check_retrieval_source` estesa a random; template del 3b con `random_seed:
    per_esercizio_ripetizione` (e il `seed` del config annotato: non usato da random).
  - `retrieval/freeze_retrievals.py --solo-random`: righe bm25 / dense / hybrid copiate TALI E QUALI (nessun ricalcolo
    del denso) e verificate byte per byte (320 righe identiche, controllo anche indipendente su una copia del file
    precedente); 240 righe random (80 × 3, campo `repetition`), 240 semi distinti, in tutti gli 80 esercizi le 3
    estrazioni sono diverse. Nuovo sha256 `2e08b93a69200e0f4e0d48a19aef9fbb05713cc3bef948b3fafddb3621c3f63d` (560
    righe); il precedente (`6857259a…`, voce 129) è nel campo `storia` del `.meta.json`; metadati del denso, delle
    versioni e dei pareggi invariati (si riferiscono alle righe non random).
  - `generation/check_frozen.py`: 364/364 prompt dal file = dal vivo (26 × 2 configurazioni × (4 condizioni + random
    nelle 3 ripetizioni)); 200/200 prompt dei manifest di sviluppo invariati. `analyze_dev80.py`: random = media delle 3
    estrazioni (Jt@3 0,018, come la media su 20 semi 0,018 ± 0,004; il seme 0 dava 0,023); sovrapposizione, hubness e
    provenienza di random sulla ripetizione 0; nel piano PREVISTO l'analisi entro esercizio. Test `check_frozen`
    aggiornato (seme, piano del runner con le due modalità, guardia, template).

### [2026-10-12] Gemma 4 26B A4B QAT come modello del Passo 3b — prova di fattibilità (STOP, nessuna decisione)
- **Richiesta dell'utente**: usare `google/gemma-4-26b-a4b-qat` (LM Studio) al posto di Gemma 4 12B QAT nel 3b. La scelta
  del modello fa parte della domanda 8 ai relatori. Tutte le leve del dev set (formato, k, istruzioni v5, esempi
  indentati, temperatura, ragionamento spento) sono state decise sul 12B: con il 26B vanno almeno verificate.
- **Modello** (da LM Studio, `GET /api/v1/models`): MoE 26B-A4B (circa 4 miliardi di parametri attivi per token, 8
  esperti), Q4_0 (QAT), 15,63 GB, contesto massimo 262144, visione, ragionamento "on" di default. Già scaricato.
- **Caricamento**: con contesto 32768 LM Studio stima 17,6 GiB di VRAM per il caricamento completo (la RTX 4070 ne ha
  12): `lms load google/gemma-4-26b-a4b-qat --context-length 32768 --gpu 0.5 -y` (stima 9,6 GiB; misurati circa 9,6 GB
  del modello, 11,0 GB con il desktop, e circa 14,8 GB di RAM per i processi di LM Studio), flash attention attiva, KV
  cache sulla GPU, parallel 4. La scelta automatica di LM Studio metterebbe tutto in GPU (17,6 GiB su 12, memoria
  condivisa): esclusa.
- **Ragionamento**: acceso di default (257 token di ragionamento per "17 × 23"); `reasoning_effort: "none"` per
  richiesta lo spegne (0 token). **Runner**: `thinking: none` nel config invia `reasoning_effort: "none"` e, a
  differenza di `thinking: true` / livello, lascia ATTIVO `stop_on_reasoning` (`run_experiment.thinking_on`; test in
  `check_thinking`). Per il 12B nulla cambia (ragionamento già spento nelle impostazioni salvate).
- **Prova (2 generazioni, cartella di lavoro della sessione, non in data/results)**: configurazione di lavoro (P-G:
  PlantUML v5 = dev_v5; C-G: compatto v5 + esempi indentati = dev_c5indent; bm25 k = 3, pool unico, temperatura 0,3,
  max_tokens 4096) con il solo modello cambiato e `thinking: none`; GPU libera.

  | chiamata | finish | livello | token di output | ragionamento | latenza 26B | latenza 12B (stesso formato) |
  |---|---|---|---|---|---|---|
  | P-G Boeing | stop | 4 | 228 | 0 | 16,9 s | Boeing 5,9-7,8 s; mediana del formato 8,0 s |
  | C-G Restaurant | stop | 4 | 569 | 0 | 38,9 s | mediana del formato 17,7 s |

  Il 26B è circa **2,2 volte più lento** del 12B (parte degli esperti gira su CPU). Stima grezza, da 2 chiamate, per
  circa 2.300 generazioni del 3b: circa **18 ore** contro circa 8 col 12B.
- **Proposta per il passo 2 (da approvare, NON eseguito)**: controllo sul dev set con la configurazione di lavoro (20
  esercizi × 2 ripetizioni × 2 formati = 80 generazioni) contro le baseline dev_v5__P-G e dev_c5indent__C-G, con la
  regola registrata PRIMA della run. Proposta di regola (non inferiorità): il 26B diventa il modello del 3b se, in
  ENTRAMBI i formati, dR ≥ −0,03 E dVc ≥ −2 E dM_primaria ≥ −0,03 E meno di 2 troncamenti E stima del 3b ≤ 30 ore
  (soglia della voce 125); si riportano anche J, R_fam, generalizzazioni invertite, elementi in più e latenze. Se
  passa in un solo formato, decide l'utente. Le leve non si ritarano sul 26B (resterebbe sullo stesso dev set).
- Al termine della prova il 26B resta caricato; per tornare al 12B: `lms unload --all` e
  `lms load google/gemma-4-12b-qat --context-length 32768 --gpu max -y` (comando di dev_v5_model_load.log).

### [2026-10-12] Controllo del 26B sul dev set e config del Passo 3b — regola e disegno registrati PRIMA di qualsiasi run
- **Approvazione**: l'utente ha approvato la proposta del passo 2 della voce 131 ("perfetto") e chiesto un notebook che
  esegua sia il controllo del 26B sia il 3b, con lo stato della generazione visibile.
- **Passo 2, controllo del 26B** (`experiments/configs/dev_g26.yaml`, run `dev_g26__P-G` e `dev_g26__C-G`): la
  configurazione di lavoro con il solo modello cambiato. P-G: PlantUML, istruzioni v5, serializzazione compact (=
  dev_v5__P-G); C-G: compatto, istruzioni v5, esempi indentati (= dev_c5indent__C-G); bm25 k = 3 dal file congelato
  (prompt identici a quelli delle baseline, voce 129); 20 esercizi di sviluppo × 2 ripetizioni × 2 formati = **80
  generazioni**; temperatura 0,3, top_p 0,95, top_k 64, seme 42, contesto 32768, max_tokens 4096 (versione di
  configurazione 2); `thinking: none` (voce 131) con stop_on_reasoning; caricamento `--gpu 0.5`.
  - **REGOLA** (`experiments/analyze_g26.py`, scritto e testato prima della run, sulle sole baseline), per formato,
    delta = 26B − 12B su 40 risposte: **il 26B diventa il modello del 3b se, in ENTRAMBI i formati, dR ≥ −0,03 E dVc
    ≥ −2 E dM_primaria ≥ −0,03 E meno di 2 troncamenti, E la stima del 3b è ≤ 30 ore**. Stima: per formato, latenza
    mediana del 26B in questa run × generazioni del 3b di quel formato (1.131), sommate (prudente: zero_shot e static
    hanno prompt più corti). Se passa in un solo formato, decide l'utente. Riportati fuori regola: J, R_fam,
    generalizzazioni invertite, classi / generalizzazioni / composizioni in più, token, latenze. Le leve NON si ritarano.
- **Passo 3b** (`experiments/configs/passo3b.yaml`, run `passo3b__<formato>-<split>-<modello>`):
  - query: i **54 esercizi di valutazione** (corpus/roles.yaml, tag evalset-v1): 34 del corpus (split `corpus`) e 20 De
    Bari (split `testset`), elencati nel config; i 26 di sviluppo NON si generano (già usati per decidere);
  - condizioni: zero_shot, static, random k = 3, bm25 k = 2 e 3, dense k = 3, hybrid k = 3 (**k per condizione**,
    nuova possibilità del runner: `k: {bm25: [2, 3], random: [3], dense: [3], hybrid: [3]}`);
  - **cella static di AirTravel non definita** (l'esempio statico coinciderebbe con la query, voce 130): il runner la
    salta e la registra in `config.json` (`celle_saltate`), le analisi la trattano come mancante (confronto appaiato
    static contro retrieval su 53);
  - 3 ripetizioni; esempi dal file congelato; random con seme per esercizio e ripetizione; `passo: 3b`;
  - formati: P (PlantUML, v5, compact) e C (compatto, v5, indent2), come nel passo 2;
  - **modello**: configurazioni per il 26B (`-G26`) e per il 12B (`-G12`); si esegue quella indicata dall'esito del
    passo 2 (o dalla decisione dell'utente);
  - generazioni: 2 formati × (34 × 7 × 3 − 3 + 20 × 7 × 3) = 2 × 1.131 = **2.262**;
  - il 3b resta **bloccato** finché i relatori non rispondono (domande 8, 11, 14, 16) e finché lo script di analisi del
    3b non è scritto e testato: il notebook ha un interruttore apposito, a False.
- **Runner** (nessun effetto sulle config esistenti): `k` può essere una mappa condizione → lista; una configurazione
  può precisare `split` e `query_ids`; la cella static di una query che coincide con un esempio statico si salta e si
  registra. **Esecuzione in background**: `experiments/run_batch.py` esegue in sequenza una lista di (config,
  configurazione) con `--resume` (riprende dove si era fermato), scrive log e stato in `data/results/batch/<nome>/`;
  `experiments/progress.py` legge i manifest mentre la run gira (fatte / attese, livelli, troncamenti, latenza,
  stima del tempo residuo). Notebook: `notebooks/passo3b.ipynb`.
- **Esecuzione (2026-10-12)**: runner (`ks_for`, `skipped_cells`, configurazioni con `split` / `query_ids`,
  `celle_saltate` nella provenienza), `prompt_builder.STATIC_EXAMPLE_IDS`, `experiments/analyze_g26.py`,
  `experiments/run_batch.py`, `experiments/progress.py`, config `dev_g26.yaml` e `passo3b.yaml`, notebook
  `notebooks/passo3b.ipynb`. Verificato: dev_g26 ha la configurazione delle baseline salvo modello, `thinking: none` e
  file congelato, e i suoi 80 prompt sono identici a quelli dei manifest di dev_v5__P-G e dev_c5indent__C-G; passo3b
  pianifica 711 + 420 = 1.131 generazioni per formato e modello sui 54 di valutazione (static di AirTravel saltata) e
  ogni cella si costruisce dal file congelato; dry run del 3b per il 26B: prompt da circa 1.100 (zero_shot) a 6.500
  token (dense k = 3), dentro il contesto di 32768 con max_tokens 4096; regola di analyze_g26 provata sulle soglie e
  su una run simulata (baseline copiate: ADOTTATO, stima circa 8 ore); batch con client finto: ripresa, arresto su
  errore, avvio in background e stato. Notebook eseguito per intero con gli interruttori a False: controlli superati
  (26B caricato a 32768), nessuna generazione. Test `check_3b_and_batch`. Nessuna run del passo 2 né del 3b eseguita.

### [2026-10-12] Controllo di Gemma 4 26B A4B QAT sul dev set: esito della regola della voce 132
- **Esecuzione**: batch `passo2_g26` dal notebook `notebooks/passo3b.ipynb` (kernel `.venv`), 80 generazioni, dalle
  01:39 alle 02:20 del 2026-10-12 (41 minuti), GPU libera, 26B caricato con `--gpu 0.5`; nessuna risposta con
  ragionamento. Run `dev_g26__P-G` e `dev_g26__C-G`; analisi `data/results/generation/dev_g26_analysis/summary.md`.
- **Regola applicata così com'è** (`experiments/analyze_g26.py`):

  | formato | dR | dVc | dM_primaria | troncate | esito |
  |---|---|---|---|---|---|
  | PlantUML | −0,014 (0,361 → 0,347) | +1 (38 → 39) | 0,000 (0,317) | 1 | non inferiore |
  | JSON compatto | +0,037 (0,307 → 0,344) | −1 (37 → 36) | +0,016 (0,263 → 0,280) | 0 | non inferiore |

  Stima del 3b: **16,8 ore** (soglia 30). **Esito: Gemma 4 26B A4B QAT ADOTTATO come modello del Passo 3b**
  (configurazioni `-G26` di `passo3b.yaml`, `MODELLO = "G26"` nel notebook).
- **Fuori regola**: J 0,540 → 0,546 (PlantUML), 0,536 → 0,554 (compatto); R_fam 0,386 → 0,378 e 0,335 → 0,386; meno
  elementi in più col 26B (classi 115 → 94 e 101 → 81, generalizzazioni 20 → 12 e 16 → 13, composizioni 43 → 28 e 37
  → 12); generalizzazioni invertite 0 in entrambi; latenza mediana 8,0 → 15,7 s (PlantUML) e 17,7 → 37,8 s (compatto).
- **Risposte non valide del 26B (3 su 80)**: PlantUML `HelpingHands__bm25__k3__r1` troncata a 4096 token (230 s) per
  un **ciclo di ripetizione** (la riga `H2SLocation "1" -- "*" DistributionCenter : has` ripetuta 276 volte);
  compatto `HelpingHands__bm25__k3__r1` (JSON incompleto, finish `stop`) e `HomeForTheElderly__bm25__k3__r0` (JSON non
  valido). Nel 3b i cicli di ripetizione vanno contati e riportati (un troncamento costa circa 4 minuti).
- Il 3b resta bloccato per le domande ai relatori (8, 11, 14, 16) e per lo script di analisi del 3b da scrivere e
  testare prima delle run. La scelta del modello va comunque portata ai relatori con la domanda 8.

### [2026-10-12] Confronto visivo nel notebook (richiesta dell'utente), solo lettura
- `experiments/compare_view.py`: per un esercizio e una ripetizione (e, nel 3b, una condizione e un k) mostra nel
  notebook la pagina di `experiments/review_report.py` ristretta a quell'esercizio: ground truth e una risposta per run
  (es. dev_g26__P-G e dev_g26__C-G, piu' le baseline del 12B), stesso rendering per tutti (PlantUML canonico → SVG con
  plantuml.jar, classi verdi nel GT e arancioni in piu'), metriche per risposta e relazioni classificate. Nessuna logica
  nuova: validazione, rendering e confronto sono quelli del report di revisione (voce 100). Pagine salvate in
  `data/results/generation/confronti/` (non versionate). `review_report.build` ora trova anche gli esercizi De Bari
  (servono per le run del 3b sullo split testset). Notebook `passo3b.ipynb`, sezione 6 (un esercizio) e sezione 7 (report completo di una o piu' run, aperto nel browser: `review_report.py --runs ... --name ...`). Test `check_compare_view`.

### [2026-10-12] Leva "attributi del compatto" (istruzioni v5b) — testi, metrica e regola registrati PRIMA delle generazioni
- **Osservazione** (revisione visiva del passo 2, voce 133, fuori regola): il 26B nel JSON compatto omette TUTTI gli
  attributi in 10 risposte valide su 38 (12B: 2 su 39; 26B in PlantUML: 0 su 39), sempre sugli stessi esercizi
  (AlphaInsurance, Boeing, Ebike, ProjectManagement in entrambe le ripetizioni; HospitalHouseMD e InsuranceCompany in
  una), benché gli esempi del prompt abbiano 8-23 attributi; in quelle risposte ha molteplicità solo il 55 % delle
  relazioni (79 % nelle altre). Nessuna perdita nella pipeline: gli attributi del testo sono tutti nel diagramma. Le
  metriche J, R, M non guardano gli attributi, quindi la regola della voce 132 non poteva vederlo. Causa probabile: le
  istruzioni v5 del compatto dicono "Omit if there are none" e "A class may have no attributes" e indicano le
  molteplicità come chiavi "optional" (in contrasto con la regola 4, che le chiede sempre).
- **Decisione dell'utente**: sistemare le istruzioni. È una leva nuova sull'insieme di sviluppo, già usato per le leve
  precedenti (dichiarato); **un solo tentativo**: nessuna iterazione sul testo dopo aver visto i risultati.
- **Testo** (`generation/templates/v5b_compact_instructions.txt`, congelato con sha256 nel test): la v5 del compatto
  con **4 righe** cambiate e nient'altro: (riga 10) "Omit if there are none" → "List every attribute that the text
  states or clearly implies for the class; leave out the key only for a class that has none in the text"; (righe 15 e
  17) le molteplicità passano da chiavi "optional" a chiavi richieste di association / unidirectional e composition /
  aggregation; (riga 25, regola 2) "only those stated or clearly implied by the text. A class may have no attributes"
  → "write all those stated or clearly implied by the text, for every class; a class has no attributes only when the
  text gives none for it" (resta "Do not add classes, attributes or generalizations just to make the diagram
  richer"). Esempi, traccia e riga finale identici alla v5. **PlantUML invariato** (v5): lì il problema non c'è.
- **Metrica nuova sugli attributi** (`evaluation/metrics.py`, aggiunta: le metriche esistenti non cambiano). Nomi
  normalizzati come quelli delle classi (minuscole, solo alfanumerici; tipo e visibilità ignorati); classi non enum.
  - **A (richiamo)**: attributi del GT presenti nella classe con lo stesso nome della risposta / attributi del GT,
    sommati su TUTTE le risposte (0 per le non valide), come R;
  - **A_prec (precisione)**: attributi della risposta presenti nella classe omonima del GT / attributi della risposta
    (risposte valide);
  - **scheletri**: risposte valide senza nessun attributo per un esercizio il cui GT ne ha.
- **Config** `experiments/configs/dev_g26b.yaml` (run `dev_g26b__C-G`): identico a `dev_g26.yaml` C-G salvo
  `instructions_version: v5b`; 26B, 20 esercizi di sviluppo × 2 ripetizioni = **40 generazioni**. Baseline:
  `dev_g26__C-G` (26B, v5).
- **REGOLA** (`experiments/analyze_v5b.py`, scritto e testato prima della run, sulla sola baseline), delta = v5b − v5
  su 40 risposte: **adottare v5b per il compatto se (scheletri ≤ metà di quelli della baseline OPPURE dA ≥ +0,05) E
  dA_prec ≥ −0,05 E dR ≥ −0,03 E dVc ≥ −2 E dM_primaria ≥ −0,03 E meno di 2 troncamenti.** Se adottata: il compatto
  del 3b usa v5b (configurazioni C-* di `passo3b.yaml`); se no, resta v5. Riportati: J, R_fam, elementi in più,
  molteplicità presenti, token e latenza.
- **Smoke test** (2 chiamate, cartella di lavoro della sessione): Boeing r0 e Restaurant r0 nel compatto v5b, per
  verificare che la risposta sia valida e che le istruzioni nuove non rompano il formato. Poi STOP; le 40 generazioni
  solo dopo il via dell'utente.
- **REVISIONE PRIMA DELLA RUN (decisione dell'utente, 2026-10-12): la leva gira su un SOTTOINSIEME**, per vedere se il
  miglioramento è uniforme; sostituisce config, regola e smoke test sopra.
  - **Esercizi** (8 × 2 ripetizioni = **16 generazioni**, `experiments/configs/dev_g26b.yaml`, run `dev_g26b__C-G`):
    i 6 con almeno una risposta della baseline senza nessun attributo (AlphaInsurance, Boeing, Ebike, HospitalHouseMD,
    InsuranceCompany, ProjectManagement; per ProjectManagement il GT non ha attributi: serve da controllo contro gli
    attributi inventati) + **2 di controllo** che gli attributi li scrivevano bene, scelti con una regola: i due con A
    più alto nella baseline, pareggi per id (EUScienceConnect 0,682; Facepage 0,667, a pari merito con Musicmatic e
    PizzaDeliveryWithEntertainment).
  - **Metriche della baseline sul sottoinsieme** (dev_g26__C-G, gli stessi 16 esercizi × ripetizioni): scheletri 8
    (AlphaInsurance 2, Boeing 2, Ebike 2, HospitalHouseMD 1, InsuranceCompany 1).
  - **REGOLA** (`experiments/analyze_v5b.py`), confronto appaiato sugli stessi 16 (esercizio, ripetizione): **adottare
    v5b per il compatto del 3b se: scheletri ≤ 4 (almeno dimezzati) E, sui 2 esercizi di controllo, dA ≥ −0,05 e
    dA_prec ≥ −0,05 E, sulle 16 risposte, dR ≥ −0,03, dM_primaria ≥ −0,03, dVc ≥ −1 e meno di 2 troncamenti.**
    Riportati per esercizio: attributi della risposta, A, A_prec, R, molteplicità presenti; per ProjectManagement gli
    attributi aggiunti (nessuna soglia).
  - **Limite dichiarato**: la decisione si prende su 8 esercizi scelti guardando la baseline (per costruzione gli
    scheletri tendono a migliorare anche per caso: i 2 di controllo e la ripetizione appaiata servono a vederlo); i
    restanti 12 esercizi di sviluppo non sono provati con v5b.
  - **Smoke test**: 1 chiamata (Boeing r0, v5b) per verificare il formato; poi STOP.
- **SOSPESA (decisione dell'utente, 2026-10-12)**: sistemate le istruzioni, NESSUNA generazione (nemmeno lo smoke
  test) finché non è implementato il sistema delle metriche. Fatto: `generation/templates/v5b_compact_instructions.txt`
  (sha256 `838de1a19d4990d063bcd76df25f96fad8815807afb0573cca9998d65215fce6`, senza conversione degli a capo in
  .gitattributes), versione `v5b` nel prompt builder (solo compatto; verificato senza modello: rispetto alla v5
  cambiano solo le 4 righe delle istruzioni, esempi e traccia identici; rifiutata per PlantUML), config
  `experiments/configs/dev_g26b.yaml` (16 generazioni, differisce dalla baseline solo per istruzioni ed esercizi),
  metrica degli attributi in `evaluation/metrics.py` (`attribute_names`, `attribute_counts`, `attribute_metrics`;
  le metriche precedenti non cambiano), bozza di `experiments/analyze_v5b.py` NON ancora testata. Prima della run,
  metrica degli attributi e regola vanno riallineate al sistema delle metriche (con una nota in questa voce o una
  voce nuova), poi lo script si testa sulla sola baseline.

### [2026-10-12] Metriche standard P / R / F1 per tipo di elemento — ricalcolo descrittivo sul dev set e PROPOSTA per il 3b
- **Riferimenti**: Chen et al. (MODELS 2023) e Chen, Shen, He (2024), P / R / F1 per classi, attributi, associazioni e
  generalizzazioni; Yang et al. (2022), abbinamento esatto e rilassato. Nessuna generazione; solo risposte già salvate
  delle run di sviluppo; esercizi di valutazione non toccati; `evaluation/metrics.py` NON modificato in questo compito
  (contiene ancora le funzioni sugli attributi aggiunte con la voce 135, da riallineare); nessun embedding, nessuna
  soglia.
- **Modulo** `evaluation/element_metrics.py` (definizioni complete nel docstring):
  - elementi: classi (tutti i nodi); attributi (nodi non enumerazione; nome senza visibilità e tipo); relazioni
    strutturali (associazione, unidirezionale, composizione, aggregazione, dipendenza, insieme); generalizzazioni
    (ereditarietà + realizzazione);
  - classi abbinate uno a uno, deterministico (pareggi per nome normalizzato, poi nome): ESATTO = nome normalizzato
    come oggi; RILASSATO = prima gli esatti, poi lo stesso insieme di token (CamelCase spezzato, minuscole, Snowball,
    come Jt), niente altro; attributi solo dentro classi abbinate (esatto: nome normalizzato; rilassato: poi stessi
    token); relazioni strutturali abbinate se gli estremi sono abbinati, SENZA verso (prima lo stesso tipo);
    generalizzazioni CON verso, le invertite contate a parte;
  - per tipo e livello TP / FP / FN, P / R / F1; macro per esercizio (prima le ripetizioni) e micro; **risposta non
    valida = diagramma vuoto: recall 0, F1 0, precision non definita ed esclusa dalla media della precision** (il
    numero di risposte escluse si riporta); P non definita senza elementi nella risposta, R senza elementi nel GT, F1 = 0
    se TP = 0 e almeno una parte ne ha, non definita se nessuna;
  - sulle relazioni abbinate: stesso tipo, stessa famiglia (associazione = unidirezionale), molteplicità uguali per
    estremo (norm_mult attuale; tutti gli estremi e quelli espliciti del GT), stesso verso per i tipi orientati.
  - Test `evaluation/test_element_metrics.py` (richiamato da `evaluation/test_metrics.py`): casi a mano per ogni regola
    (nomi quasi uguali, verso invertito, generalizzazione invertita, risposta non valida, pareggi, attributi in classi
    non abbinate, medie macro e micro) e determinismo (stesso risultato con nodi e archi in ordine diverso).
- **Ricalcolo** (`evaluation/evaluate_dev.py`, `data/results/evaluation_dev/summary.md`, `metrics.csv`,
  `per_exercise.csv`, versionati): 30 gruppi (run × formato × condizione × k) di dev_v5, dev_c5indent, dev_v5base,
  dev_retrievers, dev_k, dev_cindent / cschema / cboth, dev_structP / C, più dev_g26 (passo 2). Risultati principali:
  - **il livello rilassato, come definito, coincide con l'esatto**: 0 classi abbinate solo dal rilassato in tutte le
    risposte (F1 classi e relazioni identici; attributi al più +0,005 in micro). Le classi che restano non abbinate
    differiscono per una parola in più o in meno (Bus / BusVehicle, Customer / HungryCustomer, Company /
    InsuranceCompany, Car / PassengerCar, Volunteer / VolunteerDriver: coppie frequenti in tutte le run), non per
    lo stesso insieme di token in ordine o forma diversi;
  - F1 delle relazioni (rilassato, macro) contro R per esercizio: Spearman mediana 0,57 (da 0,45 a 0,71 nei 30
    gruppi). F1 relazioni è in genere più alta di R (non chiede il tipo) ma penalizza le relazioni in più;
  - esempi: 26B PlantUML F1 classi 0,675, relazioni 0,411, generalizzazioni 0,503; 12B PlantUML v5 0,678 / 0,419 /
    0,470; compatto 26B 0,675 / 0,417 / 0,521 contro 12B v5 + indentati 0,668 / 0,362 / 0,423. Sulle relazioni
    abbinate il 26B ha più tipi giusti (0,737 PlantUML, 0,728 compatto) e molteplicità esplicite uguali (0,802 /
    0,739);
  - **regole passate con F1 delle relazioni al posto di R** (funzioni di decisione degli script richiamate così come
    sono, R sostituita solo in memoria): stesso esito per formati (92), k (94), istruzioni mirate (98), v5 (111/118),
    varianti del retriever (121/122), compatto v5 + indent e pool (123/124), 26B (132/133); **diverso solo per la
    validità del compatto (119/121): vincerebbe "indent" invece di "both"** (che peraltro era subordinata alla domanda
    14; la configurazione di lavoro usa già "indent"). SOLO descrittivo: gli esiti registrati restano.
- **PROPOSTA per il 3b (per i relatori)**: metrica PRIMARIA = F1 macro per esercizio delle relazioni strutturali,
  abbinamento rilassato; SECONDARIE = F1 classi e F1 generalizzazioni (rilassato), R rigida (continuità con il dev
  set), tipo e molteplicità sulle relazioni abbinate; DESCRITTIVE = attributi, livello esatto, medie micro; correzione
  di Holm sulle secondarie. **Da segnalare insieme alla proposta**: sul dev set il livello rilassato come definito è
  identico all'esatto, quindi la scelta "rilassato" non cambia nulla in pratica; i casi che sfuggono sono di
  inclusione di token (una parola in più), che la regola esclude di proposito ("niente altro"): estenderla (es. un
  nome contenuto nell'altro) sarebbe una decisione nuova, da discutere con i relatori insieme all'abbinamento con
  embedding.
- **Limiti da annotare**: unica soluzione di riferimento per esercizio; abbinamento uno a uno (scomposizioni e fusioni
  di classi penalizzate); attributi rumorosi (stili diversi del GT: De Bari quasi senza tipi, voce 128); sinonimi non
  riconosciuti dal livello rilassato (es. Client / Customer).
- **Rimandati, da riprendere con i relatori**: abbinamento con embedding, distanza di Nikiforova, qualità intrinseca
  del diagramma, valutazione umana.

### [2026-10-12] Qualità degli esempi che il 3b mostrerà — SOLO DESCRITTIVO
- **Domanda dell'utente**: il corpus si può rendere più leggibile al modello? Vincolo: il GT è il riferimento della
  valutazione (congelato, evalset-v1 / testset-v2) e non si modifica; si può cambiare solo COME un esercizio viene
  mostrato quando fa da esempio. Prima di qualsiasi leva, analisi descrittiva degli esempi del file congelato
  (`retrieval/analyze_example_quality.py`, `data/results/retrieval/examples_quality_2026-10-12_8d5001f/`): si guarda
  solo il GT degli esempi, mai quello della query.
- **Risultati, query di VALUTAZIONE** (54; random: le 3 ripetizioni insieme, quindi la quota di query è gonfiata):
  - **istruzioni per lo studente** (7 esercizi della voce 128): 7-10 % degli esempi; query con almeno un esempio così:
    bm25 k = 3 27,8 %, hybrid 22,2 %, dense 18,5 %, bm25 k = 2 14,8 %;
  - **attributi senza tipo**: 16-20 % degli attributi degli esempi con bm25, hybrid e random, ma **31,5 % con dense**,
    che recupera più De Bari (38,3 % degli esempi contro 21-24 %); query con almeno un esempio con oltre metà degli
    attributi senza tipo: dense 63,0 %, bm25 k = 3 33,3 %, hybrid 38,9 %;
  - **molteplicità vuote**: 7-8 % degli estremi, uniformi tra i retriever;
  - esempi senza attributi: 2,5-4,9 %.
  Sviluppo (26): stesso quadro (dense 32,1 % di esempi De Bari, 26,6 % di attributi senza tipo).
- **Lettura**: (1) circa un quarto delle query di valutazione con bm25 k = 3 avrà nel prompt almeno un esempio con
  istruzioni rivolte allo studente; (2) **la qualità degli esempi non è uniforme tra i retriever**: dense mostra più
  esempi De Bari e quasi il doppio di attributi senza tipo. Sul dev set lo stile dei De Bari non viene copiato nelle
  risposte (attributi senza tipo ≤ 2 %), ma nel confronto tra retriever del 3b la provenienza e la completezza degli
  esempi vanno riportate come covariate descrittive (insieme al numero di esempi De Bari, proposta precedente).
- Nessuna decisione: retriever e file congelato invariati. Leva candidata, se l'utente la vuole: togliere le
  istruzioni per lo studente dalle tracce mostrate come ESEMPIO (GT, traccia della query e retrieval invariati),
  registrata e provata come le altre.

### [2026-10-12] Leva "esempi senza istruzioni per lo studente" (vista clean_v1) — registrata PRIMA delle generazioni
- **Origine**: voce 137 (circa un quarto delle query di valutazione con bm25 k = 3 ha nel prompt un esempio con
  istruzioni rivolte allo studente). Richiesta dell'utente di preparare la leva. **Un solo tentativo**; dev set già
  usato per le leve precedenti (dichiarato).
- **Intervento** (`generation/example_view_clean_v1.yaml`, congelato con sha256 nel test): quando un esercizio compare
  come ESEMPIO, dalla sua traccia si tolgono **11 frasi in 6 esercizi** (BankAccount 1, GasStation_TUW 1, GameArea 3,
  Musicmatic 1, PizzaDeliveryWithEntertainment 2, SellingGoods 3). L'elenco della voce 128 (ricerca per parole chiave,
  non esaustiva) è stato riletto su tutte le 80 tracce con criteri più larghi (verbi all'imperativo, "class diagram",
  "UML"...) PRIMA di qualsiasi generazione: aggiunte "Create a suitable class diagram from the given informal
  description." (BankAccount), "Use at least one role name and at least one association name." (GameArea) e
  "Afterwards, he will use the UML class diagram to ask programmers to implement the app." (Pizza…). **Regola di scelta**: si toglie una frase solo se dà istruzioni sul
  compito, sullo strumento o sulla cornice dell'esercizio e non dice nulla del sistema da modellare; si tiene ogni
  frase con informazione di dominio, anche in seconda persona o all'imperativo, comprese quelle che identificano il
  sistema ("Generate a class diagram of an EBike…", "Design an information system for managing a gym", "Create a
  database for a factory…", "Design a system for a movie-shop…"; restano intatti FitnessCompanyConan, con i suoi vincoli
  "you can assume…", DB18_LibrarySystem, la cui unica frase "exercise" dice qual è il sistema, e Menso; in GameArea
  resta "Write down the classes game element, shape, object and opponent…", che elenca le classi; in SellingGoods
  restano i passi STEP 1-4, dove "you" è il titolare dell'azienda). Solo rimozione di frasi intere, nessuna riscrittura.
  **Invariati**: GT, traccia della QUERY, retrieval e file congelato (il retrieval usa le descrizioni originali).
- **Implementazione**: `PromptSpec.example_view` = `raw` (default, prompt identici a prima) | `clean_v1`; chiave di
  config `prompt.example_view`; ogni frase deve comparire esattamente una volta (altrimenti errore); sha256 del file
  nella provenienza delle run.
- **Portata nel 3b** (file congelato): query di valutazione toccate 16/54 con bm25 k = 3, 8 con k = 2, 14 hybrid, 9
  dense, 24 random (3 ripetizioni insieme). File congelato: sha256
  `756ce36bfdde20fe82e20dafc5d9ada48c97fcbdb6e121fb8c1ec05c23e323f0`.
- **Prova sul dev set** (`experiments/configs/dev_g26ev.yaml`, run `dev_g26ev__P-G` e `__C-G`): le **8 query
  dell'insieme di sviluppo toccate con bm25 k = 3** (AlphaInsurance, ClothingCompany, Facepage, FitnessCompanyConan,
  Musicmatic, PizzaDeliveryWithEntertainment, Restaurant, eHome2020) × 2 ripetizioni × 2 formati = **32 generazioni**,
  26B, configurazione di lavoro (PlantUML v5; compatto v5 + esempi indentati) con la sola vista clean_v1. Baseline:
  `dev_g26__P-G` / `__C-G` sulle stesse 8 query.
- **REGOLA** (`experiments/analyze_exview.py`, scritto e testato prima della run), per formato, confronto appaiato su
  16 risposte: **adottare clean_v1 (per tutte le condizioni del 3b) se, in ENTRAMBI i formati, dF1_relazioni ≥ −0,03
  (F1 macro delle relazioni strutturali, abbinamento rilassato, voce 136) E dR ≥ −0,03 E dVc ≥ −1 E meno di 2
  troncamenti.** È una regola di NON INFERIORITÀ: la pulizia è giustificata a priori (le frasi tolte non descrivono il
  sistema), la prova serve a escludere che peggiori. Se passa in un solo formato, decide l'utente. Riportati: F1 di
  classi e generalizzazioni, J, token, latenza e il dettaglio per esercizio.
- **STOP** prima delle generazioni: la prova parte solo con il via dell'utente.

### [2026-10-12] Leva "esempi senza istruzioni per lo studente": esito della regola della voce 138
- **Esecuzione**: batch `leva_exview` dal notebook `notebooks/passo3b.ipynb` (sezione 3 bis, kernel `.venv`), 32
  generazioni dalle 13:21 alle 13:37 del 2026-10-12, 26B caricato con `--gpu 0.5`; 32/32 valide (livello 4), nessun
  troncamento, nessun ragionamento. Run `dev_g26ev__P-G` e `__C-G`; analisi
  `data/results/generation/dev_g26ev_analysis/summary.md`.
- **Regola applicata così com'è** (`experiments/analyze_exview.py`), 16 risposte per formato, contro dev_g26 sulle
  stesse 8 query:

  | formato | dF1_relazioni | dR | dVc | troncate | esito |
  |---|---|---|---|---|---|
  | PlantUML | +0,002 (0,439 → 0,441) | −0,019 (0,487 → 0,468) | 0 | 0 | non inferiore |
  | JSON compatto | +0,003 (0,406 → 0,409) | 0,000 (0,455) | 0 | 0 | non inferiore |

  **Esito: vista `clean_v1` ADOTTATA per tutte le condizioni del 3b**: `experiments/configs/passo3b.yaml` ha
  `prompt.example_view: clean_v1` (le configurazioni di sviluppo restano `raw`).
- **Fuori regola**: J +0,011 / +0,014, F1 classi +0,008 / +0,017, F1 generalizzazioni +0,020 / +0,010 (PlantUML /
  compatto), token di output un po' meno (242 contro 254; 660 contro 688). Per esercizio le differenze vanno nei due
  sensi (es. AlphaInsurance PlantUML 0,345 → 0,250, compatto 0,174 → 0,267): effetto complessivo nullo, come atteso da
  una pulizia; Restaurant ha F1 delle relazioni 0 in tutte e quattro le celle (da guardare a parte, indipendente dalla
  leva).
- **Limite dichiarato**: provata solo con bm25 k = 3 e su 8 esercizi; nel 3b si applica anche a static (nessun esempio
  toccato), random, dense e hybrid.
- **Obbligatoria nel 3b** (2026-10-12): il runner rifiuta un config `passo: 3b` con condizioni che mostrano esempi
  senza `prompt.example_view: clean_v1` (client finti esclusi, come per le altre guardie); i template
  `gemma4_12b_qat_template.yaml` e `lmstudio_template.yaml` la impostano. Le run di sviluppo storiche restano `raw`.

### [2026-10-12] Passo 2 rifatto con il retriever hybrid — config e regola registrate PRIMA delle generazioni
- **Richiesta dell'utente**: rifare il controllo sul dev set con le scelte attuali e il retriever hybrid. Motivo: gli
  unici confronti tra retriever con generazioni (voci 109-110) sono con il 12B, le istruzioni v4 e il pool storico di
  58; con la configurazione attuale dense e hybrid non sono mai stati provati, e l'utente valuta se usare nel 3b il solo
  bm25. Dev set già usato per le leve precedenti (dichiarato).
- **Trattamento** (`experiments/configs/dev_g26hy.yaml`, run `dev_g26hy__P-G` e `__C-G`): configurazione di lavoro
  del 3b sui 20 esercizi di sviluppo × 2 ripetizioni × 2 formati = **80 generazioni**: 26B (`thinking: none`, `--gpu
  0.5`), PlantUML v5 e compatto v5 + esempi indentati, vista degli esempi `clean_v1` (voce 139), pool unico, esempi dal
  file congelato, **condizione hybrid** k = 3 (RRF di bm25 e MiniLM), temperatura 0,3, max_tokens 4096. La v5b del
  compatto NON è inclusa (non provata né adottata, voce 135).
- **Baseline** (nessuna generazione): bm25 k = 3 con la stessa configurazione, ricostruita da run esistenti con prompt
  **identici** (verificato con lo sha256 dei messaggi): le 8 query toccate dalla pulizia da `dev_g26ev`, le altre 12 da
  `dev_g26` (per loro la vista clean_v1 non cambia il prompt). Hybrid sceglie esempi diversi da bm25 in 18 query su 20.
- **REGOLA** (`experiments/analyze_hybrid26.py`, scritta e testata prima della run sulla sola baseline), per formato,
  delta = hybrid − bm25 su 40 risposte: **hybrid resta nel 3b se, in ENTRAMBI i formati, dF1_relazioni ≥ −0,03 (F1
  macro delle relazioni strutturali, abbinamento rilassato, voce 136) E dR ≥ −0,03 E dVc ≥ −2 E meno di 2
  troncamenti.** Altrimenti **decide l'utente** se toglierlo (ed eventualmente dense, che non è provato qui) dal 3b. È
  una regola di non inferiorità: non sceglie il retriever migliore (lo farà il 3b sui 54 di valutazione), dice solo se
  hybrid regge con la configurazione attuale. Riportati: F1 di classi e generalizzazioni, J, M primaria, quota di
  esempi De Bari, token, latenza, dettaglio per esercizio, e un confronto descrittivo per esercizio (Spearman).
- **STOP** prima delle generazioni: la run parte dal notebook (sezione 3 ter) con il via dell'utente.

### [2026-10-12] Passo 2 con il retriever hybrid: esito della regola della voce 140
- **Esecuzione**: batch `passo2_hybrid` dal notebook (sezione 3 ter), 80 generazioni dalle 13:55 alle 14:32 del
  2026-10-12, 26B con `--gpu 0.5`; 80/80 valide (livello 4), nessun troncamento, nessun ragionamento. Run
  `dev_g26hy__P-G` e `__C-G`; analisi `data/results/generation/dev_g26hy_analysis/summary.md`.
- **Regola applicata così com'è** (`experiments/analyze_hybrid26.py`), 40 risposte per formato, contro bm25 con la
  stessa configurazione (baseline ricostruita da dev_g26 e dev_g26ev, prompt identici):

  | formato | dF1_relazioni | dR | dVc | troncate | esito |
  |---|---|---|---|---|---|
  | PlantUML | −0,002 (0,412 → 0,410) | 0,000 (0,338) | 0 (39) | 0 | non inferiore |
  | JSON compatto | −0,011 (0,418 → 0,408) | −0,011 (0,344 → 0,332) | +4 (36 → 40) | 0 | non inferiore |

  **Esito: hybrid RESTA nel 3b.**
- **Fuori regola**: hybrid ha tutte le risposte valide (40/40 in entrambi i formati; bm25 39 e 38) e nel compatto più
  risposte senza scarti (Vc 40 contro 36); in PlantUML F1 delle generalizzazioni più alta (0,566 contro 0,511) e M
  primaria +0,012; nel compatto F1 delle generalizzazioni più bassa (0,484 contro 0,525). Esempi De Bari 28 % contro
  22 %. Per esercizio: hybrid meglio in 9 e peggio in 7 (PlantUML), meglio in 9 e peggio in 5 (compatto); differenze
  grandi nei due sensi (EUScienceConnect 0,41 → 0,24 e 0,50 → 0,28; OilWells PlantUML 0,47 → 0,62, compatto 0,86 →
  0,67). In sintesi: con la configurazione attuale hybrid e bm25 sono equivalenti sul dev set.
- **Da guardare a parte**: Restaurant e BusTransportationManagementSystem hanno F1 delle relazioni 0 con entrambi i
  retriever e in entrambi i formati (indipendente dal retriever).
- Dense non è stato provato con la configurazione attuale.

### [2026-10-12] Passo 2 rifatto con il retriever dense — config e regola registrate PRIMA delle generazioni
- **Richiesta dell'utente** dopo l'esito di hybrid (voce 141): provare anche dense con la configurazione attuale.
- **Trattamento** (`experiments/configs/dev_g26de.yaml`, run `dev_g26de__P-G` e `__C-G`): identico a `dev_g26hy.yaml`
  salvo la condizione, **dense** k = 3 (all-MiniLM-L6-v2 alla revisione fissata, dal file congelato); 20 esercizi ×
  2 ripetizioni × 2 formati = **80 generazioni**. Dense sceglie esempi diversi da bm25 in 20 query su 20 (da hybrid in
  17) e il 37 % dei suoi esempi è De Bari (bm25 22 %, voce 137).
- **Baseline**: la stessa bm25 della voce 140 (dev_g26 + dev_g26ev, prompt identici).
- **REGOLA** (`experiments/analyze_dense26.py`, che riusa `scores` e `keeps` di `analyze_hybrid26.py` senza
  modificarli), identica a quella di hybrid: **dense resta nel 3b se, in ENTRAMBI i formati, dF1_relazioni ≥ −0,03 E
  dR ≥ −0,03 E dVc ≥ −2 E meno di 2 troncamenti**; altrimenti decide l'utente. Riportati anche il confronto con hybrid
  (descrittivo) e la quota di esempi De Bari.
- **STOP** prima delle generazioni: la run parte dal notebook (sezione 3 quater) con il via dell'utente.

### [2026-10-12] Passo 2 con il retriever dense: esito della regola della voce 142
- **Esecuzione**: batch `passo2_dense` dal notebook (sezione 3 quater), 80 generazioni dalle 15:01 alle 15:41 del
  2026-10-12, 26B con `--gpu 0.5`; vista `clean_v1` verificata nei prompt inviati; nessun ragionamento. PlantUML 40/40
  valide; compatto 37/40 valide (HelpingHands r1 e Musicmatic r1 JSON non valido, HomeForTheElderly r1 non nel formato
  compatto) e 1 risposta valida con scarti (HospitalHouseMD r0). Run `dev_g26de__P-G` e `__C-G`; analisi
  `data/results/generation/dev_g26de_analysis/summary.md`.
- **Regola applicata così com'è** (`experiments/analyze_dense26.py`, funzioni di `analyze_hybrid26.py`), 40 risposte
  per formato, contro bm25 con la stessa configurazione:

  | formato | dF1_relazioni | dR | dVc | troncate | esito |
  |---|---|---|---|---|---|
  | PlantUML | −0,019 (0,412 → 0,393) | −0,014 (0,338 → 0,324) | +1 (39 → 40) | 0 | non inferiore |
  | JSON compatto | **−0,034** (0,418 → 0,384) | **−0,037** (0,344 → 0,307) | 0 (36) | 1 | **inferiore** |

  **Esito: dense inferiore a bm25 nel JSON compatto (di poco oltre la soglia di 0,03): DECIDE L'UTENTE** se toglierlo
  dal 3b.
- **Fuori regola**: confronto a tre (bm25 / hybrid / dense), F1 delle relazioni PlantUML 0,412 / 0,410 / 0,393,
  compatto 0,418 / 0,408 / 0,384; F1 classi compatto 0,682 / 0,681 / 0,643; esempi De Bari 22 / 28 / 37 %. Per
  esercizio dense è meglio in 8 e peggio in 9 (PlantUML), meglio in 7 e peggio in 7 (compatto): la perdita nel
  compatto viene in buona parte dalle 3 risposte non valide (che valgono 0; es. Musicmatic 0,641 → 0,308) e da pochi
  esercizi (Musicmatic, OilWells, Boeing, EUScienceConnect).

### [2026-10-12] Decisione dell'utente: il retriever dense esce dal Passo 3b
- **Decisione**: dopo l'esito della voce 143 (dense inferiore a bm25 nel JSON compatto, dF1_relazioni −0,034 e dR
  −0,037 contro una soglia di −0,03; non inferiore in PlantUML), l'utente toglie dense dal 3b. Il consiglio era di
  tenerlo (scarto al limite, dovuto in parte a 3 risposte non valide; il confronto tra retriever è una domanda della
  tesi): la decisione resta dell'utente ed è registrata così.
- **Conseguenze**: `experiments/configs/passo3b.yaml` con le condizioni zero_shot, static, random k = 3, bm25 k = 2 e 3,
  hybrid k = 3; **969 generazioni per formato, 1.938 in totale** (prima 2.262), circa 14,5 ore col 26B. Il confronto
  tra retriever nel 3b diventa **bm25 contro hybrid** (keyword contro combinazione keyword + denso); il denso puro resta
  documentato dai risultati di sviluppo (voci 107-110, 143). File congelato invariato: contiene ancora le righe dense
  (non usate). La regola del passo 2 (`analyze_g26.py`, voce 132) usava 1.131 generazioni per formato: già applicata,
  non si ricalcola.
- **Da dichiarare in tesi**: la scelta è di risorse e di prestazioni sul dev set (20 esercizi), non un risultato sul
  set di valutazione; la Fase 2 del progetto prevedeva tre varianti di retrieval (keyword, dense, hybrid).

### [2026-10-12] Strumento di confronto visivo bm25 / hybrid / ground truth — richiesta dell'utente, solo lettura
- `experiments/compare_retrievers.py` genera `data/results/generation/confronto_bm25_hybrid/index.html` (non
  versionata, circa 5,5 MB, autonoma: SVG incorporati, nessuna risorsa esterna): per i 20 esercizi di sviluppo, i 2
  formati e le 2 ripetizioni, GT | bm25 | hybrid affiancati, con le risposte del 26B nella configurazione di lavoro con
  esempi puliti (bm25 ricostruito come nella voce 140: dev_g26ev per le 8 query toccate, dev_g26 per le altre;
  hybrid: dev_g26hy). Per risposta: livello, F1 di relazioni / classi / generalizzazioni (rilassato,
  evaluation/element_metrics.py), R, J, M (review_report.response_metrics), relazioni classificate
  (review_report.classify_relations), esempi del prompt; scheda Indice con l'F1 delle relazioni medio per esercizio e
  retriever (coerente con `analyze_hybrid26.py`, verificato nel test). Nessuna logica nuova: rendering, validazione e
  confronto sono quelli del report di revisione. Notebook `passo3b.ipynb`, sezione 6 bis. Test
  `check_compare_retrievers`.

### [2026-10-13] Leva v5b (attributi del compatto): riallineamento e regola definitiva — registrati PRIMA della run
- **Motivo**: la leva della voce 135 era sospesa in attesa del sistema delle metriche (ora `evaluation/element_metrics.py`,
  voce 136); nel frattempo la vista degli esempi `clean_v1` è stata adottata (voce 139). Il problema intanto si è
  ripresentato in tutte le run del 26B nel JSON compatto (risposte valide senza nessun attributo: bm25 8/38, hybrid
  7/40, dense 11/37; PlantUML 0 in tutte), sempre sugli stessi esercizi. Decisione dell'utente: provarla prima del 3b.
- **Invariati dalla voce 135**: testo `generation/templates/v5b_compact_instructions.txt` (sha256 `838de1a1…`), gli 8
  esercizi (AlphaInsurance, Boeing, Ebike, HospitalHouseMD, InsuranceCompany, ProjectManagement + i 2 di controllo
  EUScienceConnect e Facepage), 2 ripetizioni, **16 generazioni**, solo compatto.
- **Cambiato**: `experiments/configs/dev_g26b.yaml` ora ha anche `example_view: clean_v1` (configurazione di lavoro
  attuale); la **baseline** è bm25 + clean_v1 sugli stessi 8 esercizi, ricostruita come nella voce 140 (AlphaInsurance
  e Facepage da dev_g26ev, gli altri 6 da dev_g26: prompt identici). Baseline: **7 scheletri su 16** risposte
  (AlphaInsurance 1, Boeing 2, Ebike 2, HospitalHouseMD 1, InsuranceCompany 1).
- **Metriche** (tutte da `evaluation/element_metrics.py`, abbinamento rilassato, macro per esercizio): attributi
  (P / R / F1), relazioni (F1); più R e M primaria (metrics.py) e Vc. **Scheletro** = risposta valida senza nessun
  attributo per un esercizio il cui GT ne ha (contato con `element_metrics.elements`).
- **REGOLA** (`experiments/analyze_v5b.py`, riscritto e testato prima della run sulla sola baseline; sostituisce la
  regola della voce 135): **adottare v5b per il compatto del 3b se: scheletri ≤ 3 (almeno dimezzati) E, sui 2 esercizi
  di controllo, d(recall attributi) ≥ −0,05 e d(precision attributi) ≥ −0,05 E, sulle 16 risposte, dF1_relazioni ≥
  −0,03, dR ≥ −0,03, dM_primaria ≥ −0,03, dVc ≥ −1 e meno di 2 troncamenti.** Se adottata, le configurazioni C-* di
  `passo3b.yaml` usano `instructions_version: v5b`. Riportati: F1 attributi, molteplicità presenti, attributi aggiunti
  per ProjectManagement (GT senza attributi), dettaglio per esercizio.
- **Limite dichiarato**: 8 esercizi scelti guardando la baseline; provata con bm25; i restanti 12 esercizi non provati.
- **STOP** prima delle generazioni: parte dal notebook (sezione 3 quinquies) con il via dell'utente.

### [2026-10-13] Leva "piano breve" (v5plan, voce 126): chiusa senza adozione
- Fatta solo la FASE 1 (testi, 2 chiamate di prova riuscite) sul 12B; la FASE 2 (80 generazioni) non è mai stata
  eseguita, e nel frattempo il modello del 3b è diventato il 26B. Su proposta dell'assistente e con l'accordo
  dell'utente, la leva si chiude **senza adozione** prima del 3b: nessun indizio forte di beneficio, costo maggiore
  (risposte più lunghe in ogni generazione). Il 3b usa le istruzioni v5 (PlantUML) e v5 o v5b (compatto, voce 146).
  Codice, testi e config (`v5plan`, `dev_plan.yaml`, `analyze_plan.py`) restano come documentazione.

### [2026-10-13] Leva v5b: esito — NON adottata; risposte senza attributi lasciate come limite dichiarato
- **Run**: `dev_g26b__C-G`, 16/16 generazioni, nessun troncamento; analisi `experiments/analyze_v5b.py` (regola della
  voce 146) in `data/results/generation/dev_g26b_analysis/summary.md`.
- **Esito: v5b NON adottata, il compatto del 3b resta v5.** Scheletri 7 → 8 (soglia ≤ 3). Le altre condizioni erano
  rispettate: dF1_relazioni −0,004, dR +0,007, dM_primaria +0,021, dVc 0, controlli invariati (attributi P e R 0,674).
  Per esercizio gli scheletri si spostano invece di sparire (Boeing ed Ebike migliorano, AlphaInsurance,
  HospitalHouseMD e InsuranceCompany peggiorano): variabilità del modello, non effetto delle istruzioni. Molteplicità
  presenti 0,74 → 0,88; token in mediana 499 → 611.
- **Analisi descrittiva successiva (solo dev set, run del compatto col 26B: dev_g26, dev_g26ev, dev_g26hy, dev_g26de,
  dev_g26b; 137 risposte valide con GT dotato di attributi)**: 27 dei 35 scheletri (77 %) hanno nel prompt almeno un
  esempio con metà o più delle classi senza attributi, contro 43 su 102 (42 %) delle risposte con attributi; quota
  media di classi senza attributi negli esempi 0,34 contro 0,21. Ipotesi: nel compatto le chiavi vuote si omettono,
  quindi l'esempio mostra la classe come `{"name": "X"}` e il modello copia la forma dalla prima classe in poi (in
  PlantUML, con gli stessi esempi, nessuno scheletro). Correlazione su risposte non indipendenti, non una prova.
- **Decisione dell'utente**: nessuna ulteriore leva (proposte e non adottate: schema JSON con `attributes`
  obbligatoria, legato alla domanda 14; chiave vuota esplicita negli esempi). Il fenomeno resta come **limite
  dichiarato del formato compatto** e come materiale per la fase 5 (qualità degli esempi recuperati → output); nel 3b
  si conta con la definizione di scheletro della voce 146.

### [2026-10-13] Avvio del 3b prima delle risposte dei relatori — decisione dell'utente
- **Cosa**: il 3b (`experiments/configs/passo3b.yaml`, Gemma 4 26B A4B QAT, 4 run `passo3b__{P,C}-{corpus,testset}-G26`,
  **1.938 generazioni**, circa 14,5 ore) si avvia dal notebook (sezione 4, `SBLOCCA_3B = True`) sul commit `485fd0f`.
  Dry run superato: 609 + 360 per formato, tutti i prompt entro il contesto di 32768 token.
- **Configurazione congelata**: PlantUML v5; compatto v5 + esempi indentati (v5b non adottata, voce 148); vista
  `clean_v1` (voce 139); esempi dal file congelato (voce 129); condizioni zero_shot, static, random (seme per esercizio
  e ripetizione), bm25 k = 2 e 3, hybrid k = 3 (dense tolto, voce 144); 3 ripetizioni; temperatura 0,3, top_p 0,95,
  top_k 64; contesto 32768, max_tokens 4096; ragionamento spento (`thinking: none`).
- **Rischio accettato dall'utente**: le domande 8 (modello, campionamento, ripetizioni) e 14 (generazione libera o
  vincolata) sono ancora aperte; se i relatori rispondono diversamente, il 3b si rifà (circa 14,5 ore). Le domande 11
  (metriche) e 16 (secondo modello) non toccano queste generazioni.
- **Regola di non lettura**: nessuno guarda i risultati del 3b (manifest, risposte, metriche, report di revisione)
  finché lo script di analisi del 3b non è scritto, testato su dati simulati e registrato in una voce. La cella di stato
  del notebook mostra solo l'avanzamento (conteggi), non le metriche.

### [2026-10-14] Leva v5c ("attributes" sempre presente nel compatto) — regola e config registrate PRIMA della run
- **Motivo**: le risposte del compatto senza nessun attributo (scheletri) restano dopo la v5b (voce 148). **Dichiarazione**:
  la leva nasce DOPO che l'utente ha visto i risultati del 3b prima dello script di analisi (deroga alla voce 149, su
  sua richiesta esplicita, 2026-10-13/14). Nel 3b gli scheletri del compatto sono circa 20 con zero_shot e static e
  36-45 con random, bm25 e hybrid (PlantUML: 11 in zero_shot, 0-3 con gli esempi): conferma l'ipotesi della voce 148
  (forma `{"name": "X"}` copiata dagli esempi con classi vuote). La leva si prova SOLO sul dev set.
- **Cosa cambia (solo compatto)**: istruzioni `generation/templates/v5c_compact_instructions.txt` (sha256
  `383ad1e8…`) = la v5 con 2 righe cambiate ("attributes" obbligatoria in ogni classe non enum, `[]` solo se il testo
  non dà attributi per quella classe; "attributes" esclusa dalle chiavi vuote da omettere) **e** esempi del prompt
  con `"attributes": []` esplicita nelle classi non enum che non ne hanno (`prompt_builder.explicit_attributes`, chiave
  subito dopo name e kind). Regole di modellazione invariate (anche "A class may have no attributes"). Le chiavi vuote
  nella risposta sono ammesse dal post-processing (`read_compact`), quindi Vc non cambia per costruzione.
- **Config** `experiments/configs/dev_g26c.yaml`: identico a `dev_g26.yaml` C-G salvo istruzioni v5c e vista
  `clean_v1`; 20 esercizi di SVILUPPO × 2 ripetizioni = **40 generazioni** (circa 25 minuti col 26B). **Baseline**: v5 +
  clean_v1 ricostruita come nella voce 140 (dev_g26ev per le 8 query toccate dalla pulizia, dev_g26 per le altre),
  prompt identici ai manifest (verificato dal test): 40 risposte, **7 scheletri**, F1 relazioni 0,418, R 0,344, M
  primaria 0,288, Vc 36, attributi R 0,350 e P 0,426.
- **REGOLA** (`experiments/analyze_v5c.py`, testato prima della run sulla sola baseline): **adottare v5c per il compatto
  del 3b se scheletri ≤ 3 E, sulle 40 risposte, d(recall attributi) ≥ 0, d(precision attributi) ≥ −0,05,
  dF1_relazioni ≥ −0,03, dR ≥ −0,03, dM_primaria ≥ −0,03, dVc ≥ −2 e meno di 2 troncamenti.** Metriche e scheletri
  con le definizioni della voce 146 (element_metrics rilassato, macro per esercizio). Riportati anche la quota di
  classi senza attributi, le molteplicità presenti, i token e il dettaglio per esercizio.
- **Se adottata**: le configurazioni C-* di `passo3b.yaml` passano a `instructions_version: v5c` e la parte compatta del
  3b si rifà (969 generazioni, circa 10 ore) in run nuove; le run compatte v5 restano come documentazione. PlantUML
  invariato.
- **Limiti dichiarati**: secondo tentativo sullo stesso dev set per lo stesso problema (rischio di adattamento al dev
  set); leva motivata anche dai risultati del 3b visti in anticipo.
- **STOP** prima delle generazioni: parte dal notebook (sezione 3 sexies) con il via dell'utente.
