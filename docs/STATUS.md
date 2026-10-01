# Stato del progetto — leggere a inizio sessione

Aggiornato: 2026-10-01.

## Stato
- Corpus: 45 esercizi originali (`corpus/raw/models_original/`) + **15 esercizi italiani tradotti** (`corpus/raw/translated_it/`,
  tag `translated_it`) = 60 record in `corpus.jsonl`.
- Pipeline **verde, 0 errori, senza deroghe** (2026-10-01): 59/60 convertiti (Cruise escluso, originale), 41 correzioni,
  2 esclusioni di paragrafi, `label_classification.json` 156 voci (50 associazione + 98 ruolo + 9 vincolo), test OK,
  `check_translated` 15/15, diff_report 618.

## Esercizi italiani (Exercises.docx, studio 2025) — traduzione COMPLETATA, Gruppi A-D chiusi
| es. | id | note |
|---|---|---|
| 1 | CourseManagement | pilota |
| 2-5 | Hospital, ResearchCenter, MilanLibrary, Bookmaker | Bookmaker: 1 correzione (metodo troncato) |
| 6-9 | UniversityExams, Restaurant, ElevatorControl, RealEstateAgency | refusi corretti (UniversityExams 2, Restaurant 1, RealEstateAgency 1); es. 6 nota su Persona esclusa |
| 10-12 | OilWells, RepairShops, Gym | RepairShops `string{1..*}`→`string[]`; Gym classe associativa senza nome = `WorkoutPlanExercise` |
| 13-15 | EatAtHome, InsuranceCompany, ApartmentBuilding | EatAtHome enum→`OrderStatus` (2 correzioni) e due alternative mantenute; InsuranceCompany frasi di consegna escluse, "Furto" dubbio non corretto |

- **Esclusi: nessuno** (es. 12 inizialmente escluso, poi recuperato con la convenzione sulla classe senza nome).
- Esclusi solo elementi non di modello: note/commenti nei diagrammi (es. 6, 13), frasi di consegna (es. 14).
- **Convenzioni introdotte** (dettagli in `docs/decisions.md`): trascrivere l'immagine, mai il testo; verbo = nome di
  associazione, sostantivo = ruolo (la posizione non conta); classe associativa senza nome = concatenazione delle due
  classi; enum inline → enumerazione separata `<Classe><Attributo>`; glossario condiviso (stesso termine = stessa
  traduzione); tipi Number→int, Calendar→datetime, currency/Currency→double; molteplicità `n`/`N`→`*`; `<`/`>` di
  lettura rimossi; tipo multi-valore `tipo[]`; id in inglese PascalCase.
- **Limiti noti**: visibilità di attributi/metodi non conservata (sempre `+`, `corpus/apollon_limitations.md` §9);
  diagrammi talvolta incompleti rispetto al testo (annotati nelle transcription_notes, non completati).
- Leakage (TF-IDF, soglia 0.4): nessun esercizio tradotto sopra soglia.

## Comandi (in ordine)
```
python corpus/_generate_label_classification.py   # solo dopo revisione: rigenera label_classification.md/.json
python corpus/build_manifest.py                   # raw -> corpus.jsonl (corrections + description_exclusions)
python corpus/apollon_convert.py                  # -> Apollon v4 JSON (fallisce se etichetta non classificata)
python corpus/test_apollon_convert.py
python corpus/check_translated.py --all
python corpus/diff_report.py
python corpus/leakage_check.py <id>... [--vs <id>]  # TF-IDF vs corpus e De Bari (soglia 0.4)
# per un esercizio tradotto: apply_glossary.py <cartella> ; generate_relations_table.py <cartella>
# render: java -jar .tools/plantuml-old.jar -charset UTF-8 -tpng file.puml   (Java 8)
```

## Regole attive
- `plantuml_it.txt` trascrive l'IMMAGINE, mai il testo; contraddizioni → note + correzione proposta (commentata).
- Trascrizione: ingrandire ogni dettaglio incerto (coordinate nelle note); **controllare gli estremi di ogni relazione per i nomi di ruolo, oltre alle molteplicità** (sintassi `"molt ruolo"`); un verbo vicino a un estremo è il nome dell'associazione letto in un verso, non un ruolo (forma opposta = stessa associazione, una sola etichetta); `relations_table.md` ha sempre le colonne "Ruolo estremo A/B".
- Normalizzazione tipi/molteplicità/metodi in `apollon_convert.py`; modificatori/default attributo gestiti; `>`/`<` di lettura rimossi.
- Etichette: `CLASSIFICATION` (in `_generate_label_classification.py`, chiavi in INGLESE) → json; associazione / ruolo / ruolo_doppio / vincolo; convertitore fallisce se non classificata. Mai editare il json a mano.
- Correzioni: `corpus/corrections/<id>.yaml` (8 op incl. `add_block`, hard-fail, categoria correzione_errore|chiarimento_modellazione); mai su `raw/`. Proposte non attive restano commentate (es. InsuranceCompany).
- Esclusione da description (anche a meta' riga): `corpus/description_exclusions/` se il tratto e' separabile, altrimenti limite noto (SellingGoods).
- Classi associative `(A, B) .. C` → reificate con molteplicità derivate.
- Mai modificare i dati per far passare un controllo: si corregge il controllo (es. whitelist `ENGLISH_HOMOGRAPHS`).
- Etichette: verbo = nome di associazione; sostantivo = ruolo (la posizione non conta). Classe associativa senza nome = concatenazione delle due classi collegate; enum inline → enumerazione `<Classe><Attributo>` (convenzioni meccaniche).
- Traduzione: `glossary_shared.json` + `glossary.json` locale (stesso termine = stessa traduzione, conflitto = errore); cartelle e id in inglese; tipi ammessi solo primitivi/classi (Number→int, Calendar→datetime, currency→double); molteplicità `n`/`N` → `*`.

## File chiave
`docs/decisions.md` (log decisioni, canonico) · `corpus/apollon_convert.py` (conversione + 4 verifiche) · `corpus/apply_corrections.py` · `corpus/apply_glossary.py` · `corpus/check_translated.py` · `corpus/apollon_limitations.md`.

## Prossimi passi
1. Trascrizione De Bari (20 esercizi, test set). 2. Retriever (keyword/dense/hybrid). 3. Generazione LLM. 4. Valutazione.
