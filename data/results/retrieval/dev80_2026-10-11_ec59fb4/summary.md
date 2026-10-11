# Retrieval sui 26 esercizi di sviluppo, pool unico (dev80_2026-10-11_ec59fb4)

Voci 129 e 130 di `docs/decisions.md`. SOLO DESCRITTIVO, nessuna scelta. Esempi dal file congelato `data/retrieval_frozen/retrievals_3b.jsonl` (sha256 `2e08b93a69200e0f…`); 80 esercizi, 79 candidati per query; misure solo sulle 26 query di sviluppo (gli esercizi di valutazione sono solo candidati).

Analisi eseguita sul commit `ec59fb4a4f26` (con modifiche non committate). GT del corpus: 80 diagrammi, sha256 del contenuto `db5c04002ae13f82e688adae5edac1fdbcbcf3101632a332b25a87a4df9a3d94` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## 1. Pertinenza (media sulle 26 query della media dei primi k)

| Retriever | J@1 | J@2 | J@3 | Jt@1 | Jt@2 | Jt@3 | S@1 | S@2 | S@3 |
|---|---|---|---|---|---|---|---|---|---|
| bm25 | 0.094 | 0.090 | 0.077 | 0.115 | 0.110 | 0.092 | 0.683 | 0.699 | 0.687 |
| dense | 0.079 | 0.067 | 0.055 | 0.099 | 0.082 | 0.070 | 0.636 | 0.659 | 0.658 |
| hybrid | 0.098 | 0.077 | 0.066 | 0.120 | 0.095 | 0.084 | 0.669 | 0.668 | 0.666 |
| random (le 3 estrazioni del 3b, media) | 0.016 | 0.012 | 0.013 | 0.024 | 0.017 | 0.018 | 0.596 | 0.615 | 0.627 |
| random (20 semi: media ± sd) | 0.015 ± 0.007 | 0.014 ± 0.005 | 0.014 ± 0.004 | 0.020 ± 0.009 | 0.018 ± 0.005 | 0.018 ± 0.004 | 0.633 ± 0.035 | 0.627 ± 0.027 | 0.628 ± 0.024 |
| oracolo (massimo per misura) | 0.139 | 0.124 | 0.112 | 0.167 | 0.148 | 0.134 | 0.950 | 0.940 | 0.933 |

J e Jt sono misure lessicali sui nomi del GT e favoriscono BM25 per costruzione (voce 107): non decidono il confronto tra retriever, che si fa con le generazioni.

## 2. Sovrapposizione dei top-3

Random: ripetizione 0 (seme random_seed(id, 0), voce 130); lo stesso per le sezioni 3 e 4.

| A | B | media \|∩\| / 3 | stesso top-1 | query con ∩ = 0 | query con ∩ = 3 |
|---|---|---|---|---|---|
| bm25 | dense | 0.359 | 9/26 | 4 | 0 |
| bm25 | hybrid | 0.577 | 14/26 | 2 | 3 |
| bm25 | random | 0.038 | 0/26 | 23 | 0 |
| dense | hybrid | 0.615 | 14/26 | 1 | 3 |
| dense | random | 0.064 | 0/26 | 21 | 0 |
| hybrid | random | 0.038 | 0/26 | 23 | 0 |

## 3. Hubness (26 query, 78 posti per retriever, 80 candidati possibili)

| Retriever | distinti nei top-3 | mai recuperati (su 80) | massimo nei top-3 | distribuzione (volte: n. candidati) |
|---|---|---|---|---|
| bm25 | 48 | 32 | 4 (MilanLibrary) | 1: 28, 2: 13, 3: 4, 4: 3 |
| dense | 52 | 28 | 6 (DB14_BicycleRental) | 1: 34, 2: 13, 3: 4, 6: 1 |
| hybrid | 48 | 32 | 5 (EatAtHome) | 1: 28, 2: 13, 3: 5, 4: 1, 5: 1 |
| random | 52 | 28 | 4 (Menso) | 1: 32, 2: 16, 3: 2, 4: 2 |

## 4. Da dove vengono gli esempi (contaminazioni dichiarate nella voce 117)

| Retriever | esempi De Bari (su 78) | query con almeno un De Bari | esempi di valutazione (su 78) | query con almeno uno di valutazione |
|---|---|---|---|---|
| bm25 | 15 | 13/26 | 56 | 26/26 |
| dense | 25 | 18/26 | 62 | 26/26 |
| hybrid | 20 | 15/26 | 58 | 26/26 |
| random | 13 | 12/26 | 51 | 24/26 |

## 5. Pertinenza degli esempi contro qualità delle risposte (generazioni esistenti)

Gemma 4 12B QAT, k = 3, 20 esercizi di sviluppo × 2 ripetizioni per gruppo. x = Jt@3 degli esempi effettivamente usati (manifest), y = R medio per esercizio (0 per le risposte non valide). Spearman per gruppo (n = 20), SOLO descrittivo: i gruppi non sono indipendenti (stessi esercizi, spesso stessi esempi) e la difficoltà dell'esercizio confonde la relazione. Scatter: `scatter_plantuml.png`, `scatter_compact.png`.

| Run | conf. | condizione | pool | istruzioni | Jt@3 medio | R medio | rho (p) |
|---|---|---|---|---|---|---|---|
| dev_c5indent | C-G | bm25 | all | v5 | 0.096 | 0.312 | 0.189 (0.425) |
| dev_cboth | C-G | bm25 | all | v4 | 0.096 | 0.274 | 0.097 (0.685) |
| dev_cindent | C-G | bm25 | all | v4 | 0.096 | 0.260 | 0.073 (0.761) |
| dev_cschema | C-G | bm25 | all | v4 | 0.096 | 0.250 | 0.108 (0.649) |
| dev_instructions | C-G | bm25 | corpus58 (storico) | v4 | 0.087 | 0.272 | 0.165 (0.487) |
| dev_k | C-G | bm25 | corpus58 (storico) | v4 | 0.087 | 0.317 | 0.290 (0.215) |
| dev_poolC | C-G | bm25 | corpus60 | v4 | 0.087 | 0.286 | 0.141 (0.553) |
| dev_retrievers | C-G | dense | corpus58 (storico) | v4 | 0.072 | 0.262 | -0.005 (0.982) |
| dev_retrievers | C-G | hybrid | corpus58 (storico) | v4 | 0.085 | 0.262 | 0.100 (0.675) |
| dev_retrievers | C-G | oracle_jt (diagnostica) | corpus58 (storico) | v4 | 0.126 | 0.239 | -0.195 (0.410) |
| dev_structC | C-G | construct | all | v4 | 0.080 | 0.271 | 0.212 (0.369) |
| dev_structC | C-G | struct | all | v4 | 0.114 | 0.276 | 0.113 (0.637) |
| dev_structC | C-G | struct_construct | all | v4 | 0.090 | 0.271 | 0.206 (0.383) |
| dev_v5 | C-G | bm25 | all | v5 | 0.096 | 0.195 | 0.179 (0.451) |
| dev_v5base | C-G | bm25 | all | v4 | 0.096 | 0.215 | 0.110 (0.645) |
| dev_instructions | P-G | bm25 | corpus58 (storico) | v4 | 0.087 | 0.313 | 0.301 (0.197) |
| dev_k | P-G | bm25 | corpus58 (storico) | v4 | 0.087 | 0.294 | 0.466 (0.038) |
| dev_poolC | P-G | bm25 | corpus60 | v5 | 0.087 | 0.345 | 0.333 (0.151) |
| dev_retrievers | P-G | dense | corpus58 (storico) | v4 | 0.072 | 0.310 | 0.248 (0.291) |
| dev_retrievers | P-G | hybrid | corpus58 (storico) | v4 | 0.085 | 0.315 | 0.313 (0.179) |
| dev_retrievers | P-G | oracle_jt (diagnostica) | corpus58 (storico) | v4 | 0.126 | 0.311 | 0.219 (0.354) |
| dev_structP | P-G | construct | all | v5 | 0.080 | 0.343 | 0.487 (0.030) |
| dev_structP | P-G | struct | all | v5 | 0.114 | 0.364 | 0.227 (0.335) |
| dev_structP | P-G | struct_construct | all | v5 | 0.090 | 0.349 | 0.498 (0.026) |
| dev_v5 | P-G | bm25 | all | v5 | 0.096 | 0.356 | 0.329 (0.156) |
| dev_v5base | P-G | bm25 | all | v4 | 0.096 | 0.315 | 0.411 (0.071) |

- PlantUML: rho per gruppo (senza oracle_jt) da +0.23 a +0.50, mediana +0.33; positivi 10/10.

- JSON compatto: rho per gruppo (senza oracle_jt) da -0.01 a +0.29, mediana +0.13; positivi 13/14.

## PREVISTA: la stessa analisi sui 54 esercizi di valutazione (dopo il Passo 3b, non ora)

- Query: i 54 esercizi di valutazione (34 del corpus + 20 De Bari), esempi dal file congelato (stesso sha256).
- Sezioni 1-4 identiche (pertinenza, sovrapposizione, hubness, provenienza degli esempi) sulle 54 query;
- sezione 5 sulle run del 3b, TRA esercizi: per formato e condizione (bm25 k = 2 e 3, dense, hybrid, random), Spearman tra Jt@3 degli esempi e R medio delle ripetizioni, un punto per esercizio (n = 54; a parte 34 del corpus e 20 De Bari, e 19 senza DB06_Flights); scatter come qui. Random: Jt@3 e R per ripetizione (ogni ripetizione ha la sua estrazione, voce 130), poi media.
- sezione 5 bis, ENTRO esercizio (voce 130): per ogni esercizio e formato, scarti di Jt@3 e di R dalla media dell'esercizio tra le condizioni di retrieval (bm25 k = 3, dense, hybrid, random; bm25 k = 2 a parte), poi Spearman sugli scarti messi insieme (un punto per esercizio × condizione); si riportano n, gli esercizi in cui le condizioni recuperano esempi con Jt@3 diverso e lo scatter degli scarti.
- Lettura: la correlazione TRA esercizi può riflettere la difficoltà dell'esercizio (esercizi con analoghi nel pool tendono ad avere GT più convenzionali e risposte migliori qualunque esempio si mostri) e non l'effetto del retrieval; quella ENTRO esercizio toglie questa componente, confrontando esempi diversi per lo stesso esercizio. Entrambe solo descrittive.
- Si esegue SOLO dopo le run del 3b (`--insieme valutazione --dopo-3b`), senza cambiare nulla del retrieval.
