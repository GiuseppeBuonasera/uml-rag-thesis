# Verifiche prima del Passo 3b: compatto v5 + esempi indentati e pool dei soli 60 del corpus (voce 123)

SVILUPPO: 20 esercizi di sviluppo, Gemma 4 12B QAT, bm25 k = 3. Regole registrate PRIMA delle run (voce 123), applicate da `experiments/analyze_pool.py`.

Analisi eseguita sul commit `d79078d009ed` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## A. Compatto: v5 + indent contro v4 + indent (pool unico)

Regola: adottare v5 se (dR >= +0,03 oppure dR_fam >= +0,03) e dVc >= -2 e dM_primaria >= -0,03.

- **v5 ADOTTATA per il compatto** (dR +0.043, dR_fam +0.037, dVc -1, dM_primaria +0.049)

| istruzioni | V | Vc | J | R | R_fam | M primaria | troncate |
|---|---|---|---|---|---|---|---|
| v4 + indent (baseline) | 40/40 | 38/40 | 0.539 | 0.264 | 0.298 | 0.214 | 0 |
| v5 + indent | 39/40 | 37/40 | 0.536 | 0.307 | 0.335 | 0.263 | 0 |

## B. Pool: soli 60 del corpus contro pool unico (configurazione di lavoro)

Regola: pool dei 60 se nel compatto dR >= +0,05 e in PlantUML dR >= -0,03 e in nessun formato dVc < -2.

- **resta il pool unico** (JSON compatto: dR +0.020, dVc -3; PlantUML: dR -0.009, dVc +0)

| formato | pool | V | Vc | J | R | M primaria | R (esercizi con esempi cambiati) | R (esempi invariati) |
|---|---|---|---|---|---|---|---|---|
| PlantUML | unico (80) | 40/40 | 38/40 | 0.540 | 0.361 | 0.317 | 0.393 (12) | 0.299 (8) |
| PlantUML | solo corpus (60) | 40/40 | 38/40 | 0.558 | 0.352 | 0.284 | 0.376 (12) | 0.299 (8) |
| JSON compatto | unico (80) | 40/40 | 38/40 | 0.539 | 0.264 | 0.214 | 0.278 (12) | 0.233 (8) |
| JSON compatto | solo corpus (60) | 40/40 | 35/40 | 0.541 | 0.284 | 0.222 | 0.321 (12) | 0.233 (8) |
