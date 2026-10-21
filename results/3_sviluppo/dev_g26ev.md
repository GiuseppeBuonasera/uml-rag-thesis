# Leva "esempi senza istruzioni per lo studente" (vista clean_v1) — `dev_g26ev` contro `dev_g26`

SVILUPPO: le 8 query toccate dalla vista con bm25 k = 3, × 2 ripetizioni, Gemma 4 26B A4B QAT, configurazione di lavoro. Regola registrata PRIMA della run (voce 138), applicata da `experiments/analyze_exview.py`.

Analisi eseguita sul commit `8d5001f7b182` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Regola (voce 138)

In entrambi i formati: dF1_relazioni ≥ −0.03, dR ≥ −0.03, dVc ≥ −1, meno di 2 troncamenti.

- **PlantUML: non inferiore** (dF1_relazioni +0.002, dR -0.019, dVc +0, troncate 0)
- **JSON compatto: non inferiore** (dF1_relazioni +0.003, dR +0.000, dVc +0, troncate 0)

**Esito: clean_v1 ADOTTATA per tutte le condizioni del 3b (non inferiore in entrambi i formati)**

## Metriche (16 risposte per cella)

| formato | vista | V | Vc | J | R | F1 classi | F1 relazioni | F1 generalizz. | troncate | token (med) | latenza (med, s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PlantUML | raw | 16 | 16 | 0.642 | 0.487 | 0.763 | 0.439 | 0.740 | 0 | 253.5 | 16.7 |
| PlantUML | clean_v1 | 16 | 16 | 0.653 | 0.468 | 0.771 | 0.441 | 0.760 | 0 | 242.5 | 15.9 |
| JSON compatto | raw | 16 | 16 | 0.644 | 0.455 | 0.761 | 0.406 | 0.783 | 0 | 688 | 42.1 |
| JSON compatto | clean_v1 | 16 | 16 | 0.658 | 0.455 | 0.778 | 0.409 | 0.793 | 0 | 659.5 | 40.7 |

## Per esercizio (F1 relazioni, rilassato; media delle 2 ripetizioni)

| esercizio | PlantUML raw → clean_v1 | JSON compatto raw → clean_v1 |
|---|---|---|
| AlphaInsurance | 0.345 → 0.250 | 0.174 → 0.267 |
| ClothingCompany | 0.875 → 0.838 | 0.824 → 0.875 |
| Facepage | 0.364 → 0.413 | 0.350 → 0.200 |
| FitnessCompanyConan | 0.600 → 0.600 | 0.545 → 0.523 |
| Musicmatic | 0.552 → 0.619 | 0.641 → 0.641 |
| PizzaDeliveryWithEntertainment | 0.607 → 0.625 | 0.533 → 0.533 |
| Restaurant | 0.000 → 0.000 | 0.000 → 0.000 |
| eHome2020 | 0.170 → 0.188 | 0.181 → 0.236 |
