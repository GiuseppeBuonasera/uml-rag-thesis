# corpus/ — dati, pipeline e controlli

Questa cartella contiene il corpus di retrieval, il test set De Bari e gli script che li producono. Gli script
restano tutti qui perché si importano a vicenda dalla stessa cartella. Nessun file è stato spostato nel
riordino del 2026-10-04: le note di trascrizione in `raw/` (congelate, test set in `testset-v1`) citano i percorsi
attuali, che quindi non devono cambiare. Stato e regole: [`docs/STATUS.md`](../docs/STATUS.md); cronologia delle
decisioni: [`docs/decisions.md`](../docs/decisions.md).

## Cartelle
| Cartella | Ruolo |
|---|---|
| `raw/models_original/` | 45 esercizi originali (Golden UML Modelset, vedi `SOURCE.md`): sorgente immutabile |
| `raw/translated_it/` | 15 esercizi italiani tradotti (non versionata: licenza da verificare) |
| `raw/debari_test/` | 20 esercizi De Bari, TEST SET (tag `testset-v1`); nel retrieval solo in leave-one-out per le altre query del test set (voce 112) |
| `processed/` | output generati: `corpus.jsonl`, `testset_debari.jsonl`, `apollon/`, `apollon_debari/` |
| `corrections/` | annotazioni manuali: correzioni di contenuto per esercizio (`<id>.yaml`) |
| `description_exclusions/` | annotazioni manuali: paragrafi esclusi dalle descrizioni (`<id>.yaml`) |

## File
| File | Tipo | Ruolo |
|---|---|---|
| `build_manifest.py` | script di pipeline | raw → `processed/*.jsonl` per uno split (`--split corpus\|debari_test`) |
| `apollon_convert.py` | script di pipeline | PlantUML → Apollon v4 JSON + verifiche (schema, integrità, round-trip, stile) |
| `generate_label_classification.py` | script di pipeline | `CLASSIFICATION` (etichette approvate) → `label_classification.json` / `.md` |
| `apply_corrections.py` | modulo di pipeline | applica `corrections/<id>.yaml` (usato da build_manifest) |
| `clean_description.py` | modulo di pipeline | applica `description_exclusions/<id>.yaml` (usato da build_manifest) |
| `apply_glossary.py` | script di pipeline | esercizi tradotti: `plantuml_it.txt` + glossari → `plantuml.txt` |
| `extract_debari.py` | script di pipeline | PDF De Bari → `raw/debari_test/` (immagini, description.md, metadata.txt) |
| `generate_relations_table.py` | script di supporto | `relations_table.md` di un esercizio (`--english` per il test set) |
| `check_translated.py` | controllo | esercizi tradotti (`--all` corpus, `--debari` test set) |
| `check_debari.py` | controllo | test set contro Analysis.xlsx; scrive `check_debari_report.md` |
| `diff_report.py` | controllo | differenze PlantUML → JSON del corpus; scrive `diff_report.md` |
| `leakage_check.py` | controllo | similarità TF-IDF (tradotti e test set contro corpus e prompt statico) |
| `test_apollon_convert.py` | test | test della pipeline (script, non pytest) |
| `known_issues.yaml` | annotazione manuale | problemi noti per esercizio → campo `known_issues` |
| `ambiguities.yaml` | annotazione manuale | ambiguità di lettura (test set) → campo `ambiguities` |
| `check_debari_justifications.yaml` | annotazione manuale | classificazione delle discrepanze contro Analysis.xlsx |
| `label_classification.json` | file generato | etichette classificate, letto da apollon_convert (non si edita a mano) |
| `label_classification.md` | report generato | versione leggibile della classificazione |
| `diff_report.md` | report generato | da `diff_report.py` |
| `check_debari_report.md` | report generato | da `check_debari.py` |
| `apollon_limitations.md` | documento | limiti di rappresentazione di Apollon v4 rispetto al PlantUML |
| `README.md` | documento | questo file |

## Correzioni successive al Passo 1
| data | esercizio | correzione | voce di docs/decisions.md |
|---|---|---|---|
| 2026-10-09 | eHome2020 | lato del rombo della composizione: `Room "2..*" *-- "1" Apartment` → `Apartment "1" *-- "2..*" Room` (verificato sull'immagine originale) | 99 |

## Ordine dei comandi
Dalla radice del repository:
```
python corpus/build_manifest.py                      # corpus di retrieval
python corpus/build_manifest.py --split debari_test  # test set De Bari
python corpus/generate_label_classification.py       # solo dopo aver approvato nuove etichette
python corpus/apollon_convert.py
python corpus/apollon_convert.py --split debari_test
python corpus/test_apollon_convert.py
python corpus/check_translated.py --all
python corpus/check_translated.py --debari
python corpus/diff_report.py
python corpus/check_debari.py
python corpus/leakage_check.py --debari-test --prompt --all-debari
```
Solo quando servono: `extract_debari.py` (se cambia il PDF), `apply_glossary.py <cartella>` e
`generate_relations_table.py [--english] <cartella>` (per un singolo esercizio).
