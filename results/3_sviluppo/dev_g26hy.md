# Passo 2 rifatto con il retriever hybrid — `dev_g26hy` contro bm25 (stessa configurazione)

SVILUPPO: 20 esercizi × 2 ripetizioni, Gemma 4 26B A4B QAT, configurazione di lavoro del 3b (PlantUML v5, compatto v5 + esempi indentati, vista clean_v1, file congelato). Baseline bm25 k = 3 ricostruita da dev_g26 e dev_g26ev (prompt identici). Regola registrata PRIMA della run (voce 140), applicata da `experiments/analyze_hybrid26.py`.

Analisi eseguita sul commit `8d5001f7b182` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Regola (voce 140)

Hybrid resta nel 3b se, in entrambi i formati, dF1_relazioni ≥ −0.03, dR ≥ −0.03, dVc ≥ −2, meno di 2 troncamenti.

- **PlantUML: non inferiore** (dF1_relazioni -0.002, dR +0.000, dVc +0, troncate 0)
- **JSON compatto: non inferiore** (dF1_relazioni -0.011, dR -0.011, dVc +4, troncate 0)

**Esito: hybrid RESTA nel 3b (non inferiore a bm25 in entrambi i formati)**

## Metriche (40 risposte per cella)

| formato | retriever | V | Vc | J | R | M primaria | F1 classi | F1 relazioni | F1 generalizz. | esempi De Bari | troncate | token (med) | latenza (med, s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PlantUML | bm25 | 39 | 39 | 0.550 | 0.338 | 0.305 | 0.679 | 0.412 | 0.511 | 22 % | 1 | 217.5 | 15.3 |
| PlantUML | hybrid | 40 | 39 | 0.554 | 0.338 | 0.317 | 0.690 | 0.410 | 0.566 | 28 % | 0 | 205 | 15.1 |
| JSON compatto | bm25 | 38 | 36 | 0.560 | 0.344 | 0.288 | 0.682 | 0.418 | 0.525 | 22 % | 0 | 593 | 38.5 |
| JSON compatto | hybrid | 40 | 40 | 0.543 | 0.332 | 0.278 | 0.681 | 0.408 | 0.484 | 28 % | 0 | 636.5 | 39.1 |

## Per esercizio (F1 relazioni, rilassato; media delle 2 ripetizioni)

| esercizio | PlantUML bm25 → hybrid | JSON compatto bm25 → hybrid |
|---|---|---|
| AlphaInsurance | 0.250 → 0.273 | 0.267 → 0.303 |
| Boeing | 0.692 → 0.593 | 0.665 → 0.522 |
| Bookmaker | 0.769 → 0.801 | 0.769 → 0.769 |
| BusTransportationManagementSystem | 0.000 → 0.000 | 0.000 → 0.000 |
| ClothingCompany | 0.838 → 0.882 | 0.875 → 0.875 |
| EUScienceConnect | 0.412 → 0.235 | 0.500 → 0.284 |
| Ebike | 0.750 → 0.750 | 0.728 → 0.750 |
| Facepage | 0.413 → 0.333 | 0.200 → 0.182 |
| FitnessCompanyConan | 0.600 → 0.600 | 0.523 → 0.600 |
| HelpingHands | 0.000 → 0.091 | 0.000 → 0.098 |
| HomeForTheElderly | 0.163 → 0.157 | 0.077 → 0.151 |
| HospitalHouseMD | 0.358 → 0.390 | 0.422 → 0.446 |
| InsuranceCompany | 0.500 → 0.667 | 0.500 → 0.536 |
| Musicmatic | 0.619 → 0.558 | 0.641 → 0.665 |
| OilWells | 0.472 → 0.619 | 0.857 → 0.667 |
| PizzaDeliveryWithEntertainment | 0.625 → 0.500 | 0.533 → 0.533 |
| ProjectManagement | 0.276 → 0.286 | 0.267 → 0.267 |
| Restaurant | 0.000 → 0.000 | 0.000 → 0.000 |
| TruckLogistics | 0.321 → 0.348 | 0.308 → 0.333 |
| eHome2020 | 0.188 → 0.118 | 0.236 → 0.174 |

- PlantUML: hybrid meglio in 9 esercizi, peggio in 7, pari negli altri.

- JSON compatto: hybrid meglio in 9 esercizi, peggio in 5, pari negli altri.
