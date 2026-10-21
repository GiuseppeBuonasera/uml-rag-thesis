# Varianti del retriever: generazioni di sviluppo (passo 4, voci 120-121)

SVILUPPO: 20 esercizi di sviluppo, pool unico, k = 3, Gemma 4 12B QAT, configurazione di lavoro di ciascun formato (PlantUML v5; compatto v4 con esempi indentati). Baseline bm25: `dev_v5__P-G`, `dev_cindent__C-G`. Regola registrata PRIMA della run (voce 121), applicata da `experiments/analyze_struct.py`.

Analisi eseguita sul commit `2b74319a3f11` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Regola (voce 121)

Entra nel 3b se in entrambi i formati dR >= -0,03, dVc >= -2, dM_primaria >= -0,03 e meno di 2 troncamenti, e in almeno un formato dR >= +0,03; tra quelle che entrano vince la media di dR più alta, entro 0,01 la più semplice (construct < struct < struct_construct).

- **v4 costrutti** (non entra): PlantUML: dR -0.017, dVc +1, dM -0.019, troncate 0; JSON compatto: dR +0.011, dVc -1, dM +0.006, troncate 0
- **v2 struttura** (non entra): PlantUML: dR +0.003, dVc +1, dM -0.010, troncate 0; JSON compatto: dR +0.014, dVc +0, dM -0.004, troncate 0
- **v2 + v4** (non entra): PlantUML: dR -0.011, dVc +0, dM -0.029, troncate 0; JSON compatto: dR +0.009, dVc -2, dM -0.023, troncate 0

**Esito: nessuna variante entra: nel 3b restano bm25 e MiniLM.**

## Metriche

| formato | retriever | V | Vc | J | R | M primaria | troncate |
|---|---|---|---|---|---|---|---|
| PlantUML | bm25 (baseline) | 40/40 | 38/40 | 0.540 | 0.361 | 0.317 | 0 |
| PlantUML | v4 costrutti | 40/40 | 39/40 | 0.532 | 0.344 | 0.298 | 0 |
| PlantUML | v2 struttura | 40/40 | 39/40 | 0.536 | 0.364 | 0.307 | 0 |
| PlantUML | v2 + v4 | 40/40 | 38/40 | 0.534 | 0.349 | 0.288 | 0 |
| JSON compatto | bm25 (baseline) | 40/40 | 38/40 | 0.539 | 0.264 | 0.214 | 0 |
| JSON compatto | v4 costrutti | 40/40 | 37/40 | 0.545 | 0.276 | 0.220 | 0 |
| JSON compatto | v2 struttura | 40/40 | 38/40 | 0.530 | 0.278 | 0.210 | 0 |
| JSON compatto | v2 + v4 | 40/40 | 36/40 | 0.530 | 0.273 | 0.191 | 0 |
