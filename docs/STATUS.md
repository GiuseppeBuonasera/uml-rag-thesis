# Stato del progetto — leggere a inizio sessione

Aggiornato: 2026-10-05 (Passo 3a chiuso: infrastruttura di generazione senza chiamate LLM; Passo 3b BLOCCATO in
attesa dei relatori, domande 8, 9, 11, 14).

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
- **Retriever BM25 (Passo 2, chiuso il 2026-10-05)**: configurazione CONGELATA in `retrieval/config_bm25.yaml`
  (stopword sì, stemming Snowball sì, k1 = 1.5, b = 0.75; scelta solo sul leave-one-out del corpus), con le fasce di
  score_norm del top-1 per la tassonomia (cut-off 0.2893 / 0.3473, terzili LOO). Run versionate in
  `data/results/retrieval/`: `loo_2026-10-04_stop1` (LOO + sensibilità) e `testset_2026-10-04_stop2` (test set,
  guardato una volta sola, + hubness). Nessun LLM usato finora.
- **Infrastruttura di generazione (Passo 3a, chiuso il 2026-10-05)**, pensata per modelli LOCALI via LM Studio (API
  compatibile OpenAI, `http://localhost:1234/v1`): prompt builder (`generation/prompt_builder.py`, istruzioni
  identiche al template v4, condizioni zero_shot / static / random / bm25 / oracle), client (`generation/llm_client.py`:
  Mock, LM Studio, cache su disco), post-processing a livelli L0-L4 (`generation/postprocess.py`), runner con dry run
  (`experiments/run_experiment.py`). Solo prove con client finto e un server HTTP finto: **nessuna chiamata a un LLM
  reale**. Lo smoke test manuale `experiments/smoke_lmstudio.py` (prompt banali) è da eseguire con LM Studio aperto.

## Struttura del repository (2026-10-04)
```
corpus/                 script della pipeline + annotazioni + report (mappa file -> ruolo: corpus/README.md)
  raw/                  models_original/ (45), translated_it/ (15, non versionata), debari_test/ (20, testset-v1)
  processed/            corpus.jsonl, testset_debari.jsonl, apollon/, apollon_debari/
  corrections/, description_exclusions/   annotazioni manuali per esercizio
retrieval/              Passo 2: BM25 (keyword_retriever), random, loader in sola lettura, analisi, test,
                        config_bm25.yaml congelata; dense_retriever.py e hybrid_retriever.py ancora stub
generation/             Passo 3a: templates/ (blocchi del prompt v4), prompt_builder, llm_client, postprocess,
                        sanity_check, test_generation
experiments/            runner (run_experiment.py), configs/*.yaml, mock_responses/ (sintetiche), smoke_lmstudio.py
evaluation/             metriche ancora stub; evaluation/uml-model-4.schema.json in uso
data/results/           output sperimentali (ignorati), tranne data/results/retrieval/<run>/{config.json,summary.md,*.csv};
                        generazione in data/results/generation/<run_id>/ e dry_run/<run_id>/ (ignorati)
docs/                   STATUS.md, decisions.md (con indice), dati/ (debari/, studio2025_it/, apollon_format_reference/),
                        archivio/ (materiale concluso, con README)
```
Nel riordino non è stato spostato nessun file dentro `corpus/`: le note in `raw/` citano i percorsi attuali. I test
restano accanto al modulo (`corpus/test_apollon_convert.py`; Passo 2: `retrieval/test_retrieval.py`; Passo 3a:
`generation/test_generation.py`).

## Comandi (in ordine)
```
# --- corpus di retrieval ---
python corpus/build_manifest.py                      # raw -> corpus.jsonl (corrections, description_exclusions, known_issues)
# --- test set De Bari ---
python corpus/extract_debari.py                      # solo se cambia il PDF: immagini, description.md, metadata.txt
python corpus/build_manifest.py --split debari_test  # raw/debari_test -> testset_debari.jsonl (+ ambiguities, ED da Analysis.xlsx)
# --- comune ---
python corpus/generate_label_classification.py       # solo dopo revisione delle etichette: legge ENTRAMBI i jsonl
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

# --- retrieval (Passo 2): corpus/ in sola lettura ---
python retrieval/test_retrieval.py                   # test (determinismo, no test set tra i candidati, no scritture in corpus/)
python retrieval/analyze_retrieval.py [--run-id ID]  # LOO sul corpus + sensibilita' (NON guarda il test set)
python retrieval/run_testset.py [--run-id ID]        # test set con la config congelata; rifiuta run gia' esistenti
python retrieval/hubness_report.py                   # hubness dai CSV delle due run (solo descrittivo)

# --- generazione (Passo 3a): corpus/ e config_bm25.yaml in sola lettura; nessun LLM reale nei test ---
python generation/test_generation.py                 # prompt, cache, client su server HTTP finto, estrazione, L0-L4, runner
python generation/sanity_check.py                    # 20 GT + 59 corpus + 2 statici attraverso il post-processing
python experiments/run_experiment.py experiments/configs/dryrun_testset.yaml --dry-run   # lunghezze, finestre di contesto
python experiments/run_experiment.py experiments/configs/mock_e2e.yaml   # prova end-to-end con MockClient
python experiments/run_experiment.py <config> --resume                   # riprende una run interrotta (cache)
python experiments/smoke_lmstudio.py --list-models   # MANUALE, con LM Studio aperto; poi --model <id>
# run reali (Passo 3b, BLOCCATO): copiare experiments/configs/lmstudio_template.yaml e sostituire tutti i TODO
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

| Retrieval BM25 (Jaccard dei nomi di classe) | LOO corpus (59) | Test set (20) | Test set senza es. 6 (19) |
|---|---|---|---|
| BM25 J@1 / J@3 | 0.096 / 0.067 | 0.113 / 0.077 | 0.107 / 0.076 |
| Random J@1 (20 seed, media ± sd) | 0.013 ± 0.004 | 0.015 ± 0.009 | 0.015 ± 0.010 |
| Oracolo J@1 / J@3 | 0.132 / 0.099 | 0.148 / 0.105 | 0.144 / 0.105 |
| Spearman score_norm vs Jaccard (top-1) | ρ 0.43 (p 0.001) | ρ 0.49 (p 0.027) | ρ 0.42 (p 0.076) |
| Fasce di score_norm basso / medio / alto | 20 / 19 / 20 | 5 / 8 / 7 | — |
| Candidati distinti al rank 1 (hubness) | 39 su 59 | 17 su 20 query | — |

## Requisiti per la fase di valutazione
- **Ogni metrica va riportata su 20 esercizi e su 19 (senza l'es. 6 Flights)**, per tutte le condizioni, in
  particolare few-shot statico vs retrieval: AirTravel è sia candidato del retrieval sia l'esempio 2 del prompt
  statico (TF-IDF 0.418, 4 classi condivise, Jaccard dei nomi di classe 0.24).
- Il confronto dei nomi deve essere **case-insensitive** (lo è già check_debari).
- Il **Jaccard sui nomi di classe esatti** (pertinenza proxy del Passo 2) è un proxy LESSICALE che favorisce BM25: per
  confrontare BM25 con il retriever dense servirà anche una misura non basata sui nomi esatti.
- Le **fasce di score_norm del test set sono piccole (5 / 8 / 7)**: l'analisi per fascia è principalmente
  descrittiva. La correlazione score_norm–Jaccard **senza l'es. 6 (n = 19) ha bassa potenza statistica**
  (ρ 0.42, p 0.076).
- Conteggi del ground truth = `gt_counts` (dal JSON Apollon); `debari_xlsx_counts` solo per tracciabilità (righe
  2/3 scambiate, 19 operazioni omesse nell'es. 3, classi associative omesse negli es. 10-13, …).
- Gli elementi in `ambiguities` (es. 5, 17) vanno esclusi o trattati a parte; `known_issues` permette di filtrare
  EatAtHome (corpus) e l'es. 6 (test).
- AirTravel ha `used_as_static_example: true`: escluderlo dalle query quando si usa il prompt statico come baseline.
- Il test set non entra mai nel corpus di retrieval (`check_split_separation`); un eventuale leave-one-out sui 20
  De Bari va prima deciso con i relatori.
- **La lunghezza del prompt varia tra le condizioni** (dry run 2026-10-05, token stimati, mediana: zero_shot ~2k,
  static ~7.8k, bm25 k=3 ~11.5k) **e va trattata come covariata nell'analisi**: ogni chiamata registra in
  `manifest.jsonl` caratteri e token del prompt (stimati con tiktoken cl100k_base e, se il server li fornisce, reali).
- La validazione dell'output è a livelli separati L0-L4 (estratto, JSON, schema, integrità, stile); le "istruzioni
  non rispettate" (es. chiave `interactive` presente, testo attorno al JSON, nodi fuori dal canvas o sovrapposti) si
  registrano a parte e non sono errori. L3 verifica id unici in tutto il diagramma e riferimenti coerenti, **non** il
  formato UUID. Una risposta troncata (`finish_reason = length`) si conta separatamente da un JSON sbagliato.
- **Diagnostici, non metriche**: le istruzioni non rispettate sono registrate in due categorie separate, "formato
  della risposta" (`format_issues`: testo attorno al JSON, `interactive`, versione, tipo, ...) e "layout"
  (`layout_issues`: nodi fuori dal canvas, sovrapposti, measured diverso). Non vanno combinate tra loro né con L0-L4
  in un unico punteggio.
- L4 applica style_check dopo SOLO le due riscritture ammesse (elenco chiuso `L4_REWRITES`: metodi nella forma v4
  "nome(parametri): Tipo"; molteplicità "1..n" / "0..n" / "n" → "*"); `validation.csv` registra quante riscritture
  per risposta e i messaggi originali di style_check. **Nella valutazione semantica "1..n" e "1..*" (e "0..n" /
  "0..*", "n" / "*") vanno trattati come equivalenti.**

## Regole attive
### Generali (corpus e test set)
- Si trascrive l'IMMAGINE, mai il testo; contraddizioni → note + correzione proposta (commentata).
- Trascrizione: ingrandire ogni dettaglio incerto (coordinate nelle note); **controllare gli estremi di ogni relazione
  per i nomi di ruolo, oltre alle molteplicità** (sintassi `"molt ruolo"`); `relations_table.md` sempre generata.
- Etichette: verbo = associazione; sostantivo = ruolo (la posizione non conta); triangolo pieno di verso di lettura →
  associazione; "X of" senza triangolo → ruolo con il sostantivo. `CLASSIFICATION` (in
  `generate_label_classification.py`) → json, solo dopo approvazione; mai editare il json a mano.
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
### Generazione (Passo 3)
- **Per uno stesso modello (model_id + quantizzazione), la lunghezza di contesto impostata in LM Studio e `max_tokens`
  sono IDENTICI per tutte le condizioni e tutti i k.** Il runner rifiuta una run i cui valori differiscono da quelli
  di una run già presente dello stesso modello.
- Un client reale parte solo con tutti i metadati del modello in config (model_id, quantizzazione, contesto,
  versione di LM Studio, hardware CPU / GPU / RAM / VRAM, parametri di generazione); nessuna chiave API.
- Prompt: istruzioni identiche al template v4, un solo messaggio utente, esempi compatti senza `interactive`; le
  condizioni differiscono solo nel blocco esempi. Output strutturato (`response_format`) DISATTIVATO.
- Riscritture prima di style_check: solo l'elenco chiuso `L4_REWRITES`; qualunque altra va decisa.
- Nessuna chiamata a un LLM reale nei test automatici; nessuna run sul test set finché il Passo 3b è bloccato.
### Solo test set De Bari
- **Versionamento del ground truth**: il test set è congelato nel tag annotato `testset-v1` (commit `eb4d28b`,
  2026-10-04). Qualsiasi modifica successiva al ground truth (`corpus/raw/debari_test/`, correzioni `DB*`, regole che
  cambiano `testset_debari.jsonl` o `apollon_debari/`) richiede un **commit dedicato**, una **voce in
  `docs/decisions.md`** e un **nuovo tag** (`testset-v2`, `testset-v3`, …). Ogni run sperimentale salva nel proprio
  config il commit e il tag del test set usato.
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
`docs/decisions.md` (log decisioni, canonico, con indice) · `corpus/README.md` (mappa di corpus/) ·
`corpus/apollon_convert.py` (conversione + verifiche, split) · `corpus/generate_label_classification.py` ·
`corpus/build_manifest.py` (split, known_issues, ambiguities, ED) · `corpus/extract_debari.py` · `corpus/check_debari.py`
+ `check_debari_justifications.yaml` · `corpus/leakage_check.py` · `corpus/apply_corrections.py` ·
`corpus/apply_glossary.py` · `corpus/check_translated.py` · `corpus/apollon_limitations.md`.

## In sospeso
1. `.gitignore` riga 10 (`corpus/raw/*`) esclude ancora `corpus/raw/translated_it/`: le 15 cartelle tradotte non sono
   versionate (`models_original/` e `debari_test/` sì). Dipende dalla licenza: vedi "Domande per i relatori", punti 1-2.
2. **SOURCE.md**: `corpus/raw/models_original/SOURCE.md` creato (DOI Zenodo da verificare: versione o concept);
   `corpus/raw/translated_it/SOURCE.md` mancante (licenza da verificare con gli autori). Per `debari_test/` la
   provenienza è in metadata.txt (fonte originale di ogni esercizio + citazione De Bari et al.).

## Domande per i relatori
Raccolte in un'unica sezione (2026-10-04); le prime erano in "In sospeso" dal 2026-10-01.
1. **Esercizi italiani (studio 2025, Garaccione et al., figshare 10.6084/m9.figshare.29492624)**: permesso di usarli
   nel corpus di retrieval e di ridistribuirne le traduzioni; licenza dell'item figshare da verificare con gli autori.
2. **Dove conservare `corpus/raw/translated_it/`** se la licenza non ne permette la pubblicazione: repository
   privato / archivio separato / solo i file derivati necessari alla pipeline (oggi la cartella è esclusa da git).
3. **Ruolo dei 20 esercizi De Bari**: confermare la scelta attuale (test set tenuto fuori dal retrieval, congelato in
   `testset-v1`) e se adottare in aggiunta un leave-one-out (gli altri 19 come candidati del retrieval).
4. **Es. 6 Flights** (TF-IDF 0.418 vs AirTravel, che è anche l'esempio 2 del prompt statico): confermare la scelta di
   tenerlo nel test set e nel retrieval, riportando ogni metrica su 20 e su 19 esercizi.
5. **Formato e convenzioni**: confermare Apollon JSON v4 come target (non PlantUML, a differenza di De Bari et al.) e
   le convenzioni di trascrizione/traduzione (tabella di coerenza sopra), in particolare quelle senza precedenti
   esterni (maiuscolo/minuscolo tipografico, tipi di dominio, completamento dei token tagliati da Analysis.xlsx).
6. **Domini del test set**: sono assegnati dal trascrittore (provvisori) e 4 domini del corpus non hanno esercizi di
   test; confermarli o indicare una fonte.
7. **Analysis.xlsx**: 76 discrepanze classificate come imprecisioni dell'xlsx (es. righe 2/3 scambiate in "Attributes
   + Operations", operazioni omesse nell'es. 3, classi associative non elencate negli es. 10-13): segnalarle agli
   autori di De Bari et al.? Nei confronti con i loro punteggi si usano i conteggi del ground truth (`gt_counts`).
8. **LLM e parametri di generazione**: quale LLM (o quali), temperatura, numero di ripetizioni per cella. Gli
   esperimenti useranno modelli LOCALI via LM Studio: va scelta anche la lunghezza di contesto, identica per tutte le
   condizioni e tutti i k dello stesso modello. **Con k=3 l'unica finestra sicura è 32k; con k=2 la finestra da 16k
   ha un margine di circa 1.700 token nel caso peggiore (bm25: 11.192 di prompt + 3.509 di output = 14.701 su
   16.384), insufficiente se il tokenizer locale è meno efficiente della stima o se il modello indenta il JSON.**
   Dry run del 2026-10-05 (`data/results/generation/dry_run/dryrun_2026-10-05/summary.md`), token stimati con
   tiktoken cl100k_base (approssimazione), 20 esercizi, min / mediana / max:

   | condizione | k | token del prompt |
   |---|---|---|
   | zero_shot | 0 | 1794 / 1951 / 2054 |
   | static | 2 | 7692 / 7849 / 7952 |
   | random | 1 / 2 / 3 | 3450 / 4789 / 7436 — 6146 / 7330 / 10874 — 8218 / 10736 / 15834 |
   | bm25 | 1 / 2 / 3 | 3261 / 4739 / 7188 — 5612 / 8042 / 11192 — 8376 / 11460 / 17256 |
   | oracle (solo analisi) | 1 / 2 / 3 | 2895 / 4013 / 7181 — 4803 / 6606 / 10277 — 6266 / 10208 / 13336 |

   Output stimato dai 20 ground truth: compatto 1387 / 2306 / 3509, indentato 2104 / 3384 / 5056 (esclusi eventuali
   token di ragionamento). Esercizi su 20 per cui prompt + output compatto stanno nella finestra (tra parentesi il
   caso peggiore, prompt massimo + 3509):

   | condizione | k | 8k | 16k | 32k |
   |---|---|---|---|---|
   | zero_shot | 0 | 20 (sì) | 20 (sì) | 20 (sì) |
   | static | 2 | 0 (no) | 20 (sì) | 20 (sì) |
   | random | 1 | 15 (no) | 20 (sì) | 20 (sì) |
   | random | 2 | 2 (no) | 20 (sì) | 20 (sì) |
   | random | 3 | 0 (no) | 18 (no) | 20 (sì) |
   | bm25 | 1 | 15 (no) | 20 (sì) | 20 (sì) |
   | bm25 | 2 | 3 (no) | 20 (sì) | 20 (sì) |
   | bm25 | 3 | 0 (no) | 18 (no) | 20 (sì) |
   | oracle | 1 | 16 (no) | 20 (sì) | 20 (sì) |
   | oracle | 2 | 8 (no) | 20 (sì) | 20 (sì) |
   | oracle | 3 | 0 (no) | 20 (no) | 20 (sì) |

   Con output indentato, a 16k: bm25 k=3 13/20, random k=3 17/20, oracle k=3 18/20.
9. **Baseline few-shot statica**: la baseline few-shot statica deriva dal prompt v3 dello studio 2025 (Garaccione et
   al.), adattato ad Apollon v4 con l'esempio dell'orologio (diagramma a stati) sostituito da AirTravel. Va bene come
   baseline ufficiale, considerando che De Bari et al. usavano PlantUML e un prompt diverso? (Il prompt v3 originale e
   i suoi esempi sono in `docs/dati/studio2025_it/`.) **Aggiunta 2026-10-05**: l'esempio 1 della baseline (bank
   loans) viola le istruzioni del prompt stesso (nomi in italiano con traccia inglese, tipi non normalizzati String /
   Double / DateTime, tipi di ritorno List<...>, molteplicità "N"); per ora resta invariato come eccezione
   documentata. Il confronto pulito sulla pertinenza è **bm25 vs random** (stesso corpus normalizzato), mentre
   **static vs bm25 mescola pertinenza e qualità degli esempi**: valutare se aggiungere una variante
   `static_normalized` (stessi due esercizi, normalizzati come il corpus).
10. **Quasi-duplicati nel leave-one-out** (es. GasStation_KUL / GasStation_TUW nel corpus): ammessi o esclusi come
    vicini recuperabili? **Esito dell'analisi (2026-10-04)**: nel corpus non c'è nessun quasi-duplicato di contenuto.
    GasStation_KUL/TUW è lo stesso caso con modellazioni diverse (Jaccard dei nomi di classe 0.09, TF-IDF 0.23); il
    massimo Jaccard tra due candidati è 0.25. **Proposta**: tenere tutti i candidati, con la tabella del run
    `data/results/retrieval/loo_2026-10-04_stop1` come giustificazione (escludendo GasStation come vicini J@1 passa da
    0.096 a 0.095).
11. **Metriche**: criterio di matching dei nomi per la qualità semantica (esatto, lemma, sinonimi, LLM); qualità
    pragmatica con LLM-as-judge, valutazione umana o un campione valutato a mano.
12. **Tassonomia per l'analisi finale**, da fissare prima di vedere i risultati: difficoltà (`debari_ed_avg`),
    dimensione (`gt_counts`), punteggio normalizzato del top-1 del retrieval; il dominio solo come descrittivo.
13. **Provenienza di `docs/dati/debari/Exercises_solo_testo.pdf`** (8 pagine, solo il testo delle 20 tracce, senza
    soluzioni; testo identico alle `description.md` del test set): è il testo dato agli LLM nello studio De Bari?
14. **Generazione libera oppure vincolata allo schema Apollon?** Con il vincolo la validità sintattica è quasi
    garantita per costruzione e smette di essere una metrica. LM Studio lo supporta su `/v1/chat/completions` con
    `response_format: {"type": "json_schema", ...}` (grammatica di llama.cpp per i GGUF, Outlines per MLX; non tutti
    i modelli, specie sotto i 7B). Nel codice è pronto (`structured_output`) ma DISATTIVATO.

## Prossimi passi
1. ~~Trascrizione De Bari (20 esercizi, test set)~~ — FATTO il 2026-10-04.
2. ~~Retriever BM25, analisi LOO, test set~~ — FATTO il 2026-10-05 (configurazione congelata). Il retriever dense e
   l'hybrid restano da fare (stub), con una misura di pertinenza non basata sui nomi esatti.
3. **Pipeline di generazione**:
   - ~~**3a. Infrastruttura senza chiamate LLM**~~ — FATTO il 2026-10-05 (prompt builder, client LM Studio e
     mock con cache, post-processing L0-L4, runner con dry run). Resta lo smoke test manuale con LM Studio
     (`experiments/smoke_lmstudio.py`: risposta attesa e verifica del seed), da eseguire dall'utente.
   - **3b. Esecuzione degli esperimenti: BLOCCATA** finché i relatori non rispondono alle domande 8 (LLM, parametri,
     finestra di contesto), 9 (baseline statica), 11 (metriche) e 14 (generazione libera o vincolata allo schema).
4. Valutazione (sintattica / semantica / pragmatica), con i requisiti sopra.
