# Leva "attributes sempre presente" (istruzioni v5c) — `dev_g26c__C-G` contro v5 (stessa configurazione)

SVILUPPO: 20 esercizi × 2 ripetizioni, Gemma 4 26B A4B QAT, compatto con esempi indentati, vista clean_v1, bm25 k = 3 (file congelato). v5c = istruzioni con "attributes" obbligatoria nelle classi non enum + esempi con "attributes": [] esplicita. Baseline v5 ricostruita da dev_g26 e dev_g26ev (prompt identici). Regola registrata PRIMA della run (voce 150), applicata da `experiments/analyze_v5c.py`.

Analisi eseguita sul commit `485fd0fd4803` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Regola (voce 150)

Scheletri ≤ 3; sulle 40 risposte d(recall attributi) ≥ 0.0, d(precision attributi) ≥ −0.05, dF1_relazioni ≥ −0.03, dR ≥ −0.03, dM_primaria ≥ −0.03, dVc ≥ −2, meno di 2 troncamenti.

- scheletri: 7 → **2**
- attributi: recall 0.350 → 0.344 (d -0.007), precision 0.426 → 0.379 (d -0.047)
- dF1_relazioni -0.006, dR -0.003, dM_primaria +0.008, dVc +3, troncate 0

**Esito: v5c NON adottata (il compatto resta v5)**

## Metriche (40 risposte per parte; element_metrics rilassato, macro)

| istruzioni | V | Vc | J | R | M primaria | F1 classi | F1 relazioni | attributi P | attributi R | attributi F1 | scheletri | classi senza attributi | molteplicità presenti | troncate | token (med) | latenza (med, s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v5 (baseline) | 38 | 36 | 0.560 | 0.344 | 0.288 | 0.682 | 0.418 | 0.426 | 0.350 | 0.347 | 7 | 0.345 | 0.852 | 0 | 593 | 38.5 |
| v5c | 39 | 39 | 0.540 | 0.341 | 0.296 | 0.675 | 0.413 | 0.379 | 0.344 | 0.345 | 2 | 0.388 | 0.915 | 0 | 626 | 37.8 |

## Per esercizio (attributi della risposta sommati sulle 2 ripetizioni; metriche medie)

| esercizio | attributi GT | attributi v5 | attributi v5c | scheletri v5 → v5c | attributi F1 v5 → v5c | F1 relazioni v5 → v5c |
|---|---|---|---|---|---|---|
| AlphaInsurance | 13 | 9 | 7 | 1 → 0 | 0.136 → 0.000 | 0.267 → 0.227 |
| Boeing | 10 | 0 | 20 | 2 → 0 | 0.000 → 0.100 | 0.665 → 0.445 |
| Bookmaker | 6 | 12 | 6 | 0 → 0 | 0.333 → 0.444 | 0.769 → 0.769 |
| BusTransportationManagementSystem | 8 | 18 | 17 | 0 → 0 | 0.235 → 0.243 | 0.000 → 0.000 |
| ClothingCompany | 22 | 42 | 42 | 0 → 0 | 0.512 → 0.512 | 0.875 → 0.875 |
| EUScienceConnect | 11 | 22 | 22 | 0 → 0 | 0.682 → 0.727 | 0.500 → 0.667 |
| Ebike | 9 | 0 | 0 | 2 → 2 | 0.000 → 0.000 | 0.728 → 0.728 |
| Facepage | 12 | 24 | 24 | 0 → 0 | 0.667 → 0.667 | 0.200 → 0.200 |
| FitnessCompanyConan | 10 | 22 | 22 | 0 → 0 | 0.619 → 0.571 | 0.523 → 0.545 |
| HelpingHands | 15 | 17 | 30 | 0 → 0 | 0.031 → 0.198 | 0.000 → 0.139 |
| HomeForTheElderly | 13 | 13 | 13 | 0 → 0 | 0.115 → 0.115 | 0.077 → 0.083 |
| HospitalHouseMD | 3 | 9 | 6 | 1 → 0 | 0.000 → 0.000 | 0.422 → 0.458 |
| InsuranceCompany | 8 | 2 | 2 | 1 → 0 | 0.100 → 0.000 | 0.500 → 0.500 |
| Musicmatic | 12 | 24 | 24 | 0 → 0 | 0.667 → 0.667 | 0.641 → 0.548 |
| OilWells | 8 | 18 | 18 | 0 → 0 | 0.588 → 0.471 | 0.857 → 0.667 |
| PizzaDeliveryWithEntertainment | 24 | 48 | 48 | 0 → 0 | 0.667 → 0.667 | 0.533 → 0.533 |
| ProjectManagement | 0 | 0 | 0 | 0 → 0 | — → — | 0.267 → 0.276 |
| Restaurant | 12 | 26 | 26 | 0 → 0 | 0.400 → 0.320 | 0.000 → 0.000 |
| TruckLogistics | 7 | 16 | 16 | 0 → 0 | 0.536 → 0.536 | 0.308 → 0.348 |
| eHome2020 | 15 | 28 | 27 | 0 → 0 | 0.310 → 0.315 | 0.236 → 0.244 |
