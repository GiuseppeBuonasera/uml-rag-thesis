# Passo 2 rifatto con il retriever dense — `dev_g26de` contro bm25 (stessa configurazione)

SVILUPPO: 20 esercizi × 2 ripetizioni, Gemma 4 26B A4B QAT, configurazione di lavoro del 3b (vista clean_v1, file congelato). Baseline bm25 della voce 140. Regola registrata PRIMA della run (voce 142), applicata da `experiments/analyze_dense26.py` con le funzioni di `analyze_hybrid26.py`.

Analisi eseguita sul commit `8d5001f7b182` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Regola (voce 142)

Dense resta nel 3b se, in entrambi i formati, dF1_relazioni ≥ −0.03, dR ≥ −0.03, dVc ≥ −2, meno di 2 troncamenti.

- **PlantUML: non inferiore** (dF1_relazioni -0.019, dR -0.014, dVc +1, troncate 0)
- **JSON compatto: INFERIORE** (dF1_relazioni -0.034, dR -0.037, dVc +0, troncate 1)

**Esito: dense inferiore a bm25 in JSON compatto: DECIDE L'UTENTE se toglierlo dal 3b**

## Metriche (40 risposte per cella; hybrid solo descrittivo)

| formato | retriever | V | Vc | J | R | M primaria | F1 classi | F1 relazioni | F1 generalizz. | esempi De Bari | troncate | token (med) | latenza (med, s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PlantUML | bm25 | 39 | 39 | 0.550 | 0.338 | 0.305 | 0.679 | 0.412 | 0.511 | 22 % | 1 | 217.5 | 15.3 |
| PlantUML | hybrid | 40 | 39 | 0.554 | 0.338 | 0.317 | 0.690 | 0.410 | 0.566 | 28 % | 0 | 205 | 15.1 |
| PlantUML | dense | 40 | 40 | 0.560 | 0.324 | 0.317 | 0.697 | 0.393 | 0.502 | 37 % | 0 | 208.5 | 13.6 |
| JSON compatto | bm25 | 38 | 36 | 0.560 | 0.344 | 0.288 | 0.682 | 0.418 | 0.525 | 22 % | 0 | 593 | 38.5 |
| JSON compatto | hybrid | 40 | 40 | 0.543 | 0.332 | 0.278 | 0.681 | 0.408 | 0.484 | 28 % | 0 | 636.5 | 39.1 |
| JSON compatto | dense | 37 | 36 | 0.519 | 0.307 | 0.259 | 0.643 | 0.384 | 0.484 | 37 % | 1 | 633 | 37.5 |

## Per esercizio (F1 relazioni, rilassato; media delle 2 ripetizioni)

| esercizio | PlantUML bm25 → dense | JSON compatto bm25 → dense |
|---|---|---|
| AlphaInsurance | 0.250 → 0.352 | 0.267 → 0.273 |
| Boeing | 0.692 → 0.593 | 0.665 → 0.522 |
| Bookmaker | 0.769 → 0.769 | 0.769 → 0.813 |
| BusTransportationManagementSystem | 0.000 → 0.000 | 0.000 → 0.000 |
| ClothingCompany | 0.838 → 0.875 | 0.875 → 0.875 |
| EUScienceConnect | 0.412 → 0.235 | 0.500 → 0.333 |
| Ebike | 0.750 → 0.708 | 0.728 → 0.728 |
| Facepage | 0.413 → 0.191 | 0.200 → 0.200 |
| FitnessCompanyConan | 0.600 → 0.573 | 0.523 → 0.600 |
| HelpingHands | 0.000 → 0.143 | 0.000 → 0.053 |
| HomeForTheElderly | 0.163 → 0.160 | 0.077 → 0.080 |
| HospitalHouseMD | 0.358 → 0.413 | 0.422 → 0.472 |
| InsuranceCompany | 0.500 → 0.536 | 0.500 → 0.411 |
| Musicmatic | 0.619 → 0.467 | 0.641 → 0.308 |
| OilWells | 0.472 → 0.571 | 0.857 → 0.661 |
| PizzaDeliveryWithEntertainment | 0.625 → 0.479 | 0.533 → 0.517 |
| ProjectManagement | 0.276 → 0.286 | 0.267 → 0.267 |
| Restaurant | 0.000 → 0.000 | 0.000 → 0.000 |
| TruckLogistics | 0.321 → 0.333 | 0.308 → 0.348 |
| eHome2020 | 0.188 → 0.181 | 0.236 → 0.222 |

- PlantUML: dense meglio in 8 esercizi, peggio in 9, pari negli altri.

- JSON compatto: dense meglio in 7 esercizi, peggio in 7, pari negli altri.
