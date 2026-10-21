# Insieme di sviluppo — Gemma 4 26B A4B QAT contro Gemma 4 12B QAT (configurazione di lavoro)

SVILUPPO: 20 esercizi, pool unico, bm25 k = 3 (file congelato), temperatura 0,3, ragionamento spento, 2 ripetizioni. Baseline 12B: dev_v5__P-G (PlantUML v5) e dev_c5indent__C-G (compatto v5 + esempi indentati). Regola registrata PRIMA della run (voce 132), applicata da `experiments/analyze_g26.py`.

Analisi eseguita sul commit `8d5001f7b182` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Regola (voce 132)

Il 26B diventa il modello del 3b se, in entrambi i formati, dR >= -0,03 e dVc >= -2 e dM_primaria >= -0,03 e meno di 2 troncamenti, e la stima del 3b e' <= 30 ore (latenza mediana del 26B × 1.131 generazioni per formato).

- **PlantUML: non inferiore** (dR -0.014, dVc +1, dM_primaria +0.000, troncate 1)
- **JSON compatto: non inferiore** (dR +0.037, dVc -1, dM_primaria +0.016, troncate 0)
- Stima del 3b con il 26B: **16.8 ore** (soglia 30)

**Esito: 26B ADOTTATO come modello del Passo 3b (non inferiore in entrambi i formati, stima entro le 30 ore)**

## Metriche (40 risposte per cella)

| formato | modello | V | Vc | J | R | R_fam | M primaria | generalizzazioni invertite | classi in più | generalizzazioni in più | composizioni in più | troncate | token di output (med) | latenza (med, s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PlantUML | 12B | 40 | 38 | 0.540 | 0.361 | 0.386 | 0.317 | 0 | 115 | 20 | 43 | 0 | 217.5 | 8.0 |
| PlantUML | 26B | 39 | 39 | 0.546 | 0.347 | 0.378 | 0.317 | 0 | 94 | 12 | 28 | 1 | 214 | 15.7 |
| JSON compatto | 12B | 39 | 37 | 0.536 | 0.307 | 0.335 | 0.263 | 0 | 101 | 16 | 37 | 0 | 671 | 17.7 |
| JSON compatto | 26B | 38 | 36 | 0.554 | 0.344 | 0.386 | 0.280 | 0 | 81 | 13 | 12 | 0 | 621 | 37.8 |
