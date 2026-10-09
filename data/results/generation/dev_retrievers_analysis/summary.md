# Insieme di sviluppo — controllo di funzionamento dei retriever e run oracolo (`dev_retrievers` contro `dev_k`, k = 3)

Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set. Gemma 4 12B QAT, versione di configurazione 2, k = 3, prompt senza blocco di istruzioni mirate. Il tipo di retriever è un FATTORE sperimentale del Passo 3b: qui NON si sceglie un vincitore, si applica solo la regola di esclusione registrata PRIMA delle run (voce 109) da `experiments/analyze_retrievers.py`. Ground truth attuale del corpus; confronto per contenuto, mai per id.

Analisi eseguita sul commit `22f5adfbe6ce` (con modifiche non committate). GT del corpus: 59 diagrammi, sha256 del contenuto `b400d1dd7954e8a97c88ff604bc47f294e7eca2cb17d9cd7dd680542fd5db5fd` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `01ef9a52fa255f07…`.

## Regola di esclusione (voce 109), applicata così com'è

Escluso dal 3b in quel formato se Vc peggiora di più di 4 su 40, oppure se i troncamenti per max_tokens sono 2 o più (1 solo: riportato e allegato), oppure con anche un solo prompt oltre il budget di contesto (prompt + max_tokens 4096 > 32768). Nessun criterio su R, J o M.

- PlantUML, MiniLM (dense): **ammesso** al 3b (dVc -1, troncamenti 0, prompt oltre il budget 0)
- PlantUML, ibrido RRF (hybrid): **ammesso** al 3b (dVc +0, troncamenti 0, prompt oltre il budget 0)
- JSON compatto, MiniLM (dense): **ammesso** al 3b (dVc +1, troncamenti 0, prompt oltre il budget 0)
- JSON compatto, ibrido RRF (hybrid): **ammesso** al 3b (dVc +1, troncamenti 0, prompt oltre il budget 0)

## Run oracolo (solo diagnostica, MAI nel 3b)

- R(oracolo) − R(BM25): PlantUML +0.017, JSON compatto -0.065.
- **Interpretazione (fissata prima): la qualità del retrieval non è il collo di bottiglia con questo corpus e questo modello (R(oracolo) − R(BM25) < 0.03 in entrambi i formati).**

## Metriche per formato e retriever

J, R, M su tutte le risposte (0 per le non valide); M primaria: estremi del GT con molteplicità esplicita; verso: relazioni dello stesso tipo orientato con lo stesso verso.

| formato | retriever | V | Vc | J | R | M primaria | verso uguale | troncate | prompt med (server) | completamento med | latenza med (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PlantUML | BM25 (baseline dev_k) | 40/40 | 40/40 | 0.544 | 0.307 | 0.282 (137/486) | 21/33 | 0 | 3691 | 261 | 8.4 |
| PlantUML | MiniLM (dense) | 40/40 | 39/40 | 0.532 | 0.327 | 0.288 (140/486) | 22/36 | 0 | 3581 | 242 | 8.0 |
| PlantUML | ibrido RRF (hybrid) | 40/40 | 40/40 | 0.543 | 0.330 | 0.278 (135/486) | 34/42 | 0 | 3695 | 250 | 7.6 |
| PlantUML | oracolo Jt (solo diagnostica) | 40/40 | 40/40 | 0.543 | 0.324 | 0.294 (143/486) | 15/36 | 0 | 3676 | 253 | 7.8 |
| JSON compatto | BM25 (baseline dev_k) | 39/40 | 34/40 | 0.529 | 0.310 | 0.214 (104/486) | 46/46 | 0 | 4293 | 552 | 14.5 |
| JSON compatto | MiniLM (dense) | 36/40 | 35/40 | 0.476 | 0.256 | 0.200 (97/486) | 55/55 | 0 | 4173 | 600 | 15.2 |
| JSON compatto | ibrido RRF (hybrid) | 38/40 | 35/40 | 0.496 | 0.250 | 0.233 (113/486) | 45/45 | 0 | 4214 | 515 | 13.9 |
| JSON compatto | oracolo Jt (solo diagnostica) | 38/40 | 30/40 | 0.481 | 0.244 | 0.163 (79/486) | 45/45 | 0 | 4230 | 494 | 13.5 |

## Esempi recuperati in comune con BM25 (per esercizio, su 3)

### PlantUML

| esercizio | MiniLM (dense) | ibrido RRF (hybrid) | oracolo Jt (solo diagnostica) |
|---|---|---|---|
| AlphaInsurance | 2 | 2 | 2 |
| Boeing | 1 | 2 | 2 |
| Bookmaker | 0 | 0 | 0 |
| BusTransportationManagementSystem | 2 | 2 | 2 |
| ClothingCompany | 2 | 2 | 1 |
| Ebike | 1 | 1 | 2 |
| eHome2020 | 2 | 2 | 1 |
| EUScienceConnect | 1 | 1 | 3 |
| Facepage | 2 | 3 | 2 |
| FitnessCompanyConan | 1 | 3 | 1 |
| HelpingHands | 0 | 2 | 1 |
| HomeForTheElderly | 0 | 0 | 1 |
| HospitalHouseMD | 2 | 3 | 3 |
| InsuranceCompany | 1 | 2 | 2 |
| Musicmatic | 1 | 2 | 3 |
| OilWells | 2 | 3 | 0 |
| PizzaDeliveryWithEntertainment | 1 | 2 | 2 |
| ProjectManagement | 3 | 3 | 2 |
| Restaurant | 1 | 2 | 1 |
| TruckLogistics | 1 | 2 | 1 |
| **totale** | 26/60 | 39/60 | 32/60 |

### JSON compatto

| esercizio | MiniLM (dense) | ibrido RRF (hybrid) | oracolo Jt (solo diagnostica) |
|---|---|---|---|
| AlphaInsurance | 2 | 2 | 2 |
| Boeing | 1 | 2 | 2 |
| Bookmaker | 0 | 0 | 0 |
| BusTransportationManagementSystem | 2 | 2 | 2 |
| ClothingCompany | 2 | 2 | 1 |
| Ebike | 1 | 1 | 2 |
| eHome2020 | 2 | 2 | 1 |
| EUScienceConnect | 1 | 1 | 3 |
| Facepage | 2 | 3 | 2 |
| FitnessCompanyConan | 1 | 3 | 1 |
| HelpingHands | 0 | 2 | 1 |
| HomeForTheElderly | 0 | 0 | 1 |
| HospitalHouseMD | 2 | 3 | 3 |
| InsuranceCompany | 1 | 2 | 2 |
| Musicmatic | 1 | 2 | 3 |
| OilWells | 2 | 3 | 0 |
| PizzaDeliveryWithEntertainment | 1 | 2 | 2 |
| ProjectManagement | 3 | 3 | 2 |
| Restaurant | 1 | 2 | 1 |
| TruckLogistics | 1 | 2 | 1 |
| **totale** | 26/60 | 39/60 | 32/60 |

