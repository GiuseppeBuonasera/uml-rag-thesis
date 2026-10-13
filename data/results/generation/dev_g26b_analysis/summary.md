# Leva "attributi del compatto" (istruzioni v5b) — `dev_g26b__C-G` contro v5 (stessa configurazione)

SVILUPPO, sottoinsieme di 8 esercizi × 2 ripetizioni (6 con risposte senza attributi + 2 di controllo), Gemma 4 26B A4B QAT, compatto con esempi indentati, vista clean_v1, bm25 k = 3 (file congelato). Baseline v5 ricostruita da dev_g26 e dev_g26ev (prompt identici). Regola registrata PRIMA della run (voce 146), applicata da `experiments/analyze_v5b.py`.

Analisi eseguita sul commit `8d5001f7b182` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Regola (voce 146)

Scheletri ≤ 3; sui 2 di controllo d(recall attributi) ≥ −0.05 e d(precision attributi) ≥ −0.05; sulle 16 risposte dF1_relazioni ≥ −0.03, dR ≥ −0.03, dM_primaria ≥ −0.03, dVc ≥ −1, meno di 2 troncamenti.

- scheletri: 7 → **8**
- controllo (EUScienceConnect, Facepage): recall attributi 0.674 → 0.674 (d +0.000), precision attributi 0.674 → 0.674 (d +0.000)
- 16 risposte: dF1_relazioni -0.004, dR +0.007, dM_primaria +0.021, dVc +0, troncate 0

**Esito: v5b NON adottata (il compatto resta v5)**

## Metriche (16 risposte per parte; element_metrics rilassato, macro)

| istruzioni | V | Vc | J | R | M primaria | F1 classi | F1 relazioni | attributi P | attributi R | attributi F1 | scheletri | molteplicità presenti | troncate | token (med) | latenza (med, s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v5 (baseline) | 16 | 15 | 0.568 | 0.353 | 0.271 | 0.714 | 0.444 | 0.436 | 0.218 | 0.226 | 7 | 0.739 | 0 | 499 | 33.7 |
| v5b | 16 | 15 | 0.557 | 0.360 | 0.292 | 0.705 | 0.440 | 0.393 | 0.207 | 0.208 | 8 | 0.883 | 0 | 610.5 | 35.6 |

## Per esercizio (attributi della risposta sommati sulle 2 ripetizioni; metriche medie)

| esercizio | ruolo | attributi GT | attributi v5 | attributi v5b | scheletri v5 → v5b | attributi F1 v5 → v5b | F1 relazioni v5 → v5b |
|---|---|---|---|---|---|---|---|
| AlphaInsurance | senza attributi in v5 | 13 | 9 | 0 | 1 → 2 | 0.136 → 0.000 | 0.267 → 0.315 |
| Boeing | senza attributi in v5 | 10 | 0 | 9 | 2 → 1 | 0.000 → 0.105 | 0.665 → 0.615 |
| Ebike | senza attributi in v5 | 9 | 0 | 4 | 2 → 1 | 0.000 → 0.000 | 0.728 → 0.728 |
| HospitalHouseMD | senza attributi in v5 | 3 | 9 | 0 | 1 → 2 | 0.000 → 0.000 | 0.422 → 0.433 |
| InsuranceCompany | senza attributi in v5 | 8 | 2 | 0 | 1 → 2 | 0.100 → 0.000 | 0.500 → 0.500 |
| ProjectManagement | GT senza attributi | 0 | 0 | 0 | 0 → 0 | — → — | 0.267 → 0.267 |
| EUScienceConnect | controllo | 11 | 22 | 22 | 0 → 0 | 0.682 → 0.682 | 0.500 → 0.461 |
| Facepage | controllo | 12 | 24 | 24 | 0 → 0 | 0.667 → 0.667 | 0.200 → 0.200 |
