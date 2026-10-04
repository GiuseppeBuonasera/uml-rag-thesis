# Stato del progetto — leggere a inizio sessione

Aggiornato: 2026-10-04 (fine del Passo 1: test set De Bari).

## Stato
- **Corpus di retrieval** (`corpus/processed/corpus.jsonl`, 60 record): 45 esercizi originali
  (`corpus/raw/models_original/`, Golden UML Modelset) + 15 esercizi italiani tradotti (`corpus/raw/translated_it/`,
  tag `translated_it`). 59/60 convertiti in Apollon v4 (Cruise escluso: diamante n-ario). **Byte-identico** agli
  sha256 salvati prima del Passo 1 (corpus.jsonl, 59 JSON in `processed/apollon/`, `example_2_airtravel_v4.json`).
- **Test set De Bari** (`corpus/processed/testset_debari.jsonl`, 20 record, split `debari_test`, MAI nel
  retrieval): i 20 esercizi di `docs/dati/debari/Exercises.pdf`, trascritti dalle immagini "Reference Solution"
  (`corpus/raw/debari_test/`), 20/20 convertiti (`corpus/processed/apollon_debari/`). Ground truth con cui De Bari
  et al. hanno valutato (Analysis.xlsx).
- Pipeline **verde su entrambi gli split, 0 errori** (2026-10-04): schema / integrità / round-trip / stile, 0 righe
  PlantUML non riconosciute, 0 etichette non classificate; test OK; check_translated 15/15 + 1/1 (--debari);
  check_debari OK; separazione degli split verificata (hard-fail).

## Comandi (in ordine)
```
# --- corpus di retrieval ---
python corpus/build_manifest.py                      # raw -> corpus.jsonl (corrections, description_exclusions, known_issues)
# --- test set De Bari ---
python corpus/extract_debari.py                      # solo se cambia il PDF: immagini, description.md, metadata.txt
python corpus/build_manifest.py --split debari_test  # raw/debari_test -> testset_debari.jsonl (+ ambiguities, ED da Analysis.xlsx)
# --- comune ---
python corpus/_generate_label_classification.py      # solo dopo revisione delle etichette: legge ENTRAMBI i jsonl
python corpus/apollon_convert.py                     # corpus -> Apollon v4 (fallisce se etichetta non classificata)
python corpus/apollon_convert.py --split debari_test # test set -> Apollon v4 (+ gt_counts)
python corpus/test_apollon_convert.py
python corpus/check_translated.py --all              # 15 tradotti del corpus
python corpus/check_translated.py --debari           # esercizi De Bari tradotti (es. 5)
python corpus/diff_report.py                         # solo corpus
python corpus/check_debari.py                        # test set vs Analysis.xlsx (discrepanze giustificate)
python corpus/leakage_check.py --debari-test --prompt --all-debari   # leakage test set vs corpus + prompt statico
python corpus/leakage_check.py <id>... [--vs <id>]   # forma storica (tradotti vs corpus e PDF De Bari)
# per un esercizio: apply_glossary.py <cartella> ; generate_relations_table.py [--english] <cartella>
# render: java -jar .tools/plantuml-old.jar -charset UTF-8 -tpng file.puml   (Java 8)
```

## Contatori
| | Corpus | Test set De Bari |
|---|---|---|
| Record / convertiti | 60 / 59 | 20 / 20 |
| Correzioni attive | 41 (20 esercizi) | 40 (6 esercizi) |
| Esclusioni di paragrafi | 2 | 0 |
| Warning di conversione | 27 | 215 (in gran parte "attributo senza tipo") |
| Vincoli di generalizzazione | 9 | 12 |
| known_issues | 1 (EatAtHome) | 1 (es. 6 Flights) |
| ambiguities | — | 2 (es. 5, 17) |
| Classi / attributi / operazioni / relazioni (`gt_counts`) | — | 150 (+1 interfaccia, +5 enum) / 264 / 47 / 167 |
| ED medio (Analysis.xlsx) | — | 2.8 |

- `label_classification.json`: **203 voci** = 74 associazioni + 109 ruoli (+2 righe di ruolo doppio) + 21 vincoli
  (corpus + test set).
- check_debari: 84 discrepanze rispetto ad Analysis.xlsx, tutte giustificate (76 imprecisione_xlsx, 8
  convenzione); diff_report (corpus): 618.
- Leakage (TF-IDF, soglia 0.4): tradotti tutti sotto soglia; test set: solo es. 6 Flights vs AirTravel 0.418 →
  resta nel test set e nel retrieval (decisione STOP B, `known_issues`).

## Requisiti per la fase di valutazione
- **Ogni metrica va riportata su 20 esercizi e su 19 (senza l'es. 6 Flights)**, per tutte le condizioni, in
  particolare few-shot statico vs retrieval: AirTravel è sia candidato del retrieval sia l'esempio 2 del prompt
  statico (TF-IDF 0.418, 4 classi condivise, Jaccard dei nomi di classe 0.24).
- Il confronto dei nomi deve essere **case-insensitive** (lo è già check_debari).
- Conteggi del ground truth = `gt_counts` (dal JSON Apollon); `debari_xlsx_counts` solo per tracciabilità (righe
  2/3 scambiate, 19 operazioni omesse nell'es. 3, classi associative omesse negli es. 10-13, …).
- Gli elementi in `ambiguities` (es. 5, 17) vanno esclusi o trattati a parte; `known_issues` permette di filtrare
  EatAtHome (corpus) e l'es. 6 (test).
- AirTravel ha `used_as_static_example: true`: escluderlo dalle query quando si usa il prompt statico come baseline.
- Il test set non entra mai nel corpus di retrieval (`check_split_separation`); un eventuale leave-one-out sui 20
  De Bari va prima deciso con i relatori.

## Regole attive
### Generali (corpus e test set)
- Si trascrive l'IMMAGINE, mai il testo; contraddizioni → note + correzione proposta (commentata).
- Trascrizione: ingrandire ogni dettaglio incerto (coordinate nelle note); **controllare gli estremi di ogni relazione
  per i nomi di ruolo, oltre alle molteplicità** (sintassi `"molt ruolo"`); `relations_table.md` sempre generata.
- Etichette: verbo = associazione; sostantivo = ruolo (la posizione non conta); triangolo pieno di verso di lettura →
  associazione; "X of" senza triangolo → ruolo con il sostantivo. `CLASSIFICATION` (in
  `_generate_label_classification.py`) → json, solo dopo approvazione; mai editare il json a mano.
- Correzioni: `corpus/corrections/<id>.yaml` (8 op, hard-fail, categoria correzione_errore | chiarimento_modellazione),
  mai su `raw/`. Proposte non attive restano commentate. Esclusioni da description: `corpus/description_exclusions/`.
- File dati per esercizio: `corpus/known_issues.yaml` (codici o voci strutturate con `tipo`) → `known_issues`;
  `corpus/ambiguities.yaml` (solo test set) → `ambiguities`. Mai editare i jsonl a mano.
- Mai modificare i dati per far passare un controllo: si corregge il controllo.
- Convenzioni meccaniche: classe associativa senza nome = concatenazione delle due classi; enum inline →
  enumerazione `<Classe><Attributo>`; tipo multi-valore `tipo[]` (anche `List<X>` → `X[]`); molteplicità `n` → `*`,
  `...` → `..` (warning); operazioni senza parentesi → `Nome()`.
- Nomi con spazi / '-' / '/': CLASSI in PascalCase (CarPark, WorkProduct); ATTRIBUTI e METODI con la prima parola come
  scritta e la maiuscola sulle successive (PercentComplete, dataPrestito, insertStaffCard()); underscore invariati.
- **Maiuscolo / minuscolo tipografico**, solo alla lettera: una categoria (diagramma, intestazioni, attributi)
  INTERAMENTE maiuscola → classi PascalCase (confini di parola dall'xlsx), attributi minuscolo con i separatori come
  scritti; INTERAMENTE minuscola → classi PascalCase. Via corrections ("maiuscolo/minuscolo tipografico"),
  `plantuml.txt` fedele. Invariato se informativo: acronimi ID, SSN, VAT, NIN, TIN, SMS, DVD, VHS, ASCII (non lo sono
  KM, NO, FAX, TAX) e grafia mista.
- Tipi: Number → int, Calendar → datetime, currency → double (glossario dei tradotti); Real → double, Text → string
  (`TYPE_NORMALIZATION`); tipi di dominio Guid / Address / Phone / Supplier → string, Price → double
  (`DOMAIN_TYPE_MAPPING`: solo in posizione di tipo, solo maiuscola, mai se il diagramma dichiara la classe omonima).
- Note e vincoli testuali ({XOR}, OCL informale, anche su una sola classe) e vincoli di estremo `{ordered, unique}` →
  esclusi, con warning in `apollon_conversion_warnings`.
- `interface X` / `class X <<interface>>` → stereotype "interface"; ogni riga PlantUML non riconosciuta è un errore.
- Traduzione: `glossary_shared.json` + `glossary.json` locale (stesso termine = stessa traduzione, conflitto = errore).
### Solo test set De Bari
- Parti illeggibili o tagliate → completate da Analysis.xlsx, ogni token annotato con la fonte; se l'xlsx non copre il
  punto → STOP e domanda.
- Discrepanze contro Analysis.xlsx mai corrette: classificate in `corpus/check_debari_justifications.yaml`.
- Domini PROVVISORI (assegnati dal trascrittore, `domain_note` in metadata.txt).

## Coerenza delle regole corpus / test set (2026-10-04)
| Regola | Corpus (originali + tradotti) | Test set De Bari | Casi nel corpus |
|---|---|---|---|
| Trascrivere l'immagine, mai il testo; contraddizioni → correzione commentata | sì | sì | — |
| Verbo = associazione, sostantivo = ruolo (posizione irrilevante) | sì | sì | — |
| Triangolo pieno di verso di lettura → associazione | sì (EatAtHome "makes ►") | sì (es. 1) | — |
| "X of" senza triangolo → ruolo con il sostantivo | sì (Louvre hasCoach → coach) | sì (es. 6) | — |
| Classe associativa senza nome → concatenazione delle due classi | sì (Gym) | sì (es. 10-13) | 1 |
| Enum inline → enumerazione `<Classe><Attributo>` | sì (EatAtHome) | sì (es. 5) | 1 |
| Tipo multi-valore `tipo[]` (anche `List<X>`) | sì (RepairShops, HelpingHands) | sì (es. 18) | 2 |
| Tipi: Number → int, Calendar → datetime, currency → double (glossario) | sì | sì | tradotti |
| Tipi: Real → double, Text → string (`TYPE_NORMALIZATION`) | sì (regola generale) | sì (es. 2) | 0 |
| Tipi di dominio Guid/Address/Phone/Supplier → string, Price → double (solo posizione di tipo) | sì (regola generale) | sì (es. 19, 20) | 0 (Address è classe in SmartHome: protetta) |
| Vincoli di estremo `{ordered, unique}` → tolti dal ruolo con warning | sì (regola generale) | sì (es. 20) | 0 |
| Molteplicità `n` → `*`, `...` → `..` | sì | sì (es. 2, 9) | n: sì; `...`: 0 |
| Nomi composti: classi PascalCase, membri "prima parola come scritta" | sì (ControlloreAscensore) | sì | tradotti |
| Operazioni senza parentesi → `Nome()` | sì (regola generale) | sì (es. 1) | 0 |
| Maiuscolo / minuscolo tipografico (solo alla lettera) + acronimi | sì (regola generale) | sì (es. 9, 10, 15) | 0 |
| Parti illeggibili / tagliate → completate da Analysis.xlsx | n/a (nessun xlsx) | sì (es. 4, 9) | — |
| Attributi in italiano → glossario (translated_it) | sì | sì (es. 5) | 15 tradotti |
| Note / vincoli testuali → esclusi con warning | sì ({XOR} FilmSet, TransportCompany) | sì (es. 14) | 2 |
| `interface` → stereotype "interface"; riga non riconosciuta = errore | sì | sì (es. 18) | 0 |
| `known_issues` (file dati; codici o voci strutturate) | sì | sì | 1 (EatAtHome) |
| `ambiguities` (file dati), `gt_counts` dal JSON | no (solo test) | sì | — |
| Confronto dei nomi case-insensitive in valutazione | sì | sì | — |

## Domini (vocabolario del corpus; test set PROVVISORIO)
| Dominio | Corpus | Test set | Totale |
|---|---|---|---|
| Business Services | 3 | 4 | 7 |
| Education | 7 | 1 | 8 |
| Financial Services | 1 | 2 | 3 |
| Healthcare | 5 | 3 | 8 |
| Insurance | 2 | 0 | 2 |
| Leisure and Recreation | 9 | 2 | 11 |
| Logistics | 6 | 2 | 8 |
| Manufacturing | 6 | 2 | 8 |
| Media and Publishing | 6 | 2 | 8 |
| Personal Activities | 3 | 0 | 3 |
| Research | 3 | 0 | 3 |
| Sales | 8 | 2 | 10 |
| Social Networks | 1 | 0 | 1 |
| **Totale** | **60** | **20** | **80** |

## Limiti noti
- Visibilità di attributi e metodi non conservata (sempre `+`, `corpus/apollon_limitations.md` §9); EatAtHome con due
  modellazioni alternative (§10); diagrammi talvolta incompleti rispetto al testo (annotati, non completati: es.
  test set 17 Phone/DoubleTransfer isolati).
- Test set: 215 warning, in gran parte attributi senza tipo nelle immagini (non inventati).

## File chiave
`docs/decisions.md` (log decisioni, canonico) · `corpus/apollon_convert.py` (conversione + verifiche, split) ·
`corpus/build_manifest.py` (split, known_issues, ambiguities, ED) · `corpus/extract_debari.py` · `corpus/check_debari.py`
+ `check_debari_justifications.yaml` · `corpus/leakage_check.py` · `corpus/apply_corrections.py` ·
`corpus/apply_glossary.py` · `corpus/check_translated.py` · `corpus/apollon_limitations.md`.

## In sospeso
1. `.gitignore` riga 10 (`corpus/raw/*`) esclude ancora `corpus/raw/translated_it/`: le 15 cartelle tradotte non sono
   versionate (`models_original/` e `debari_test/` sì). Decisione utente pendente.
2. **SOURCE.md**: `corpus/raw/models_original/SOURCE.md` creato (DOI da verificare: versione o concept);
   `corpus/raw/translated_it/SOURCE.md` mancante (licenza da verificare con gli autori). Per `debari_test/`
   provenienza in metadata.txt (fonte originale di ogni esercizio + citazione De Bari et al.).
3. **Domande per i relatori**: permesso per gli esercizi italiani; conferma del ruolo dei 20 De Bari (oggi test set
   tenuto fuori dal retrieval; leave-one-out non adottato); conferma delle scelte di formato e delle convenzioni.
4. `corpus/apollon_limitations.md` §8 riporta ancora i conteggi del corpus a 46/45 (prima della traduzione): da
   aggiornare a 60/59.

## Prossimi passi
1. ~~Trascrizione De Bari (20 esercizi, test set)~~ — FATTO il 2026-10-04.
2. **Retriever** (keyword BM25 / dense / hybrid) sul corpus di retrieval (60 record; Cruise senza JSON Apollon),
   con query = description.md dei 20 esercizi del test set.
3. Generazione LLM (prompt few-shot con esempi recuperati vs statico vs zero-shot).
4. Valutazione (sintattica / semantica / pragmatica), con i requisiti sopra.
