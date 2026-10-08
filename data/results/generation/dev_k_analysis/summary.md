# Insieme di sviluppo — numero di esempi k (`dev_k`)

Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set; versione di configurazione 2 (contesto 32768, max_tokens 4096). Regola registrata PRIMA delle run (docs/decisions.md, voce 94) e applicata cosi' com'e' da `experiments/analyze_k.py`; metriche della voce 92 (J e R su tutte le risposte, 0 per le non valide). Confronto per contenuto, mai per id. La leva vale solo per le condizioni con esempi: sul test set il confronto con random dovra' usare lo stesso k.

Analisi eseguita sul commit `1f185be85aa1`.

## Regola di scelta di k (voce 94), applicata cosi' com'e'

- **PlantUML: k = 2**
- **JSON compatto: STOP: dipende dal modello (Gemma k = 3, Qwen k = 2): decisione dell'utente**

### PlantUML — Gemma 4 12B QAT (40 risposte per k)

Vc(k=2) = 38: ammissibili i k con Vc >= 36; R* = 0.321 tra gli ammissibili; entro 0.03 da R*: k = [2, 3, 5, 8]; scelto il piu' piccolo: **k = 2**.

| k | ammissibile | Vc | V | R | J | R_valide | J_valide | molteplicita' uguali | verso uguale | scarti | troncate | prompt reale (med / max) | completamento med | latenza med (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | si | 38/40 | 40/40 | 0.312 | 0.542 | 0.312 | 0.542 | 45/115 | 21/42 | 7 | 0 | 3078 / 3791 | 256 | 8.6 |
| 3 | si | 40/40 | 40/40 | 0.307 | 0.544 | 0.307 | 0.544 | 47/120 | 19/33 | 0 | 0 | 3691 / 4493 | 261 | 8.4 |
| 5 | si | 38/40 | 40/40 | 0.298 | 0.548 | 0.298 | 0.548 | 47/114 | 27/33 | 3 | 0 | 5032 / 6514 | 250 | 8.2 |
| 8 | si | 40/40 | 40/40 | 0.321 | 0.541 | 0.321 | 0.541 | 53/113 | 26/40 | 0 | 0 | 7422 / 9149 | 246 | 9.5 |

### PlantUML — Qwen2.5-Coder 7B (40 risposte per k)

Vc(k=2) = 38: ammissibili i k con Vc >= 36; R* = 0.156 tra gli ammissibili; entro 0.03 da R*: k = [2, 3, 5]; scelto il piu' piccolo: **k = 2**.

| k | ammissibile | Vc | V | R | J | R_valide | J_valide | molteplicita' uguali | verso uguale | scarti | troncate | prompt reale (med / max) | completamento med | latenza med (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | si | 38/40 | 40/40 | 0.139 | 0.507 | 0.139 | 0.507 | 18/59 | 12/16 | 3 | 0 | 3006 / 3721 | 185 | 6.0 |
| 3 | si | 36/40 | 40/40 | 0.156 | 0.482 | 0.156 | 0.482 | 19/55 | 15/17 | 10 | 0 | 3598 / 4397 | 188 | 6.1 |
| 5 | si | 36/40 | 40/40 | 0.139 | 0.474 | 0.139 | 0.474 | 11/52 | 17/19 | 10 | 0 | 4898 / 6344 | 210 | 6.5 |
| 8 | no | 34/40 | 40/40 | 0.159 | 0.475 | 0.159 | 0.475 | 19/51 | 17/17 | 27 | 0 | 7223 / 8925 | 198 | 7.0 |

### JSON compatto — Gemma 4 12B QAT (40 risposte per k)

Vc(k=2) = 26: ammissibili i k con Vc >= 24; R* = 0.310 tra gli ammissibili; entro 0.03 da R*: k = [3, 5]; scelto il piu' piccolo: **k = 3**.

| k | ammissibile | Vc | V | R | J | R_valide | J_valide | molteplicita' uguali | verso uguale | scarti | troncate | prompt reale (med / max) | completamento med | latenza med (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | si | 26/40 | 35/40 | 0.210 | 0.457 | 0.245 | 0.522 | 24/95 | 42/44 | 12 | 0 | 3577 / 4224 | 467 | 12.4 |
| 3 | si | 34/40 | 39/40 | 0.310 | 0.529 | 0.318 | 0.542 | 31/118 | 44/46 | 9 | 0 | 4293 / 5062 | 552 | 14.5 |
| 5 | si | 39/40 | 39/40 | 0.287 | 0.521 | 0.295 | 0.534 | 31/111 | 50/52 | 0 | 0 | 5812 / 7487 | 650 | 16.3 |
| 8 | si | 32/40 | 37/40 | 0.270 | 0.495 | 0.291 | 0.535 | 30/101 | 44/45 | 16 | 0 | 8584 / 10548 | 598 | 17.2 |

### JSON compatto — Qwen2.5-Coder 7B (40 risposte per k)

Vc(k=2) = 16: ammissibili i k con Vc >= 14; R* = 0.151 tra gli ammissibili; entro 0.03 da R*: k = [2, 3, 8]; scelto il piu' piccolo: **k = 2**.

| k | ammissibile | Vc | V | R | J | R_valide | J_valide | molteplicita' uguali | verso uguale | scarti | troncate | prompt reale (med / max) | completamento med | latenza med (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | si | 16/40 | 34/40 | 0.131 | 0.434 | 0.156 | 0.511 | 14/59 | 17/19 | 61 | 0 | 3508 / 4148 | 524 | 13.7 |
| 3 | si | 14/40 | 33/40 | 0.131 | 0.421 | 0.167 | 0.510 | 10/62 | 20/21 | 56 | 0 | 4205 / 4963 | 610 | 14.9 |
| 5 | si | 17/40 | 38/40 | 0.114 | 0.434 | 0.119 | 0.456 | 15/57 | 13/14 | 92 | 0 | 5686 / 7293 | 590 | 15.2 |
| 8 | si | 21/40 | 37/40 | 0.151 | 0.440 | 0.164 | 0.476 | 16/59 | 15/17 | 47 | 0 | 8415 / 10304 | 566 | 15.2 |

## Andamento per fascia di score_norm (solo descrittivo)

R / Vc per fascia (risposte per cella: esercizi della fascia x 2 ripetizioni).

| formato | modello | fascia | k=2: R / Vc | k=3: R / Vc | k=5: R / Vc | k=8: R / Vc |
|---|---|---|---|---|---|---|
| PlantUML | Gemma 4 12B QAT | basso | 0.167 / 12/14 | 0.158 / 14/14 | 0.158 / 13/14 | 0.183 / 14/14 |
| PlantUML | Gemma 4 12B QAT | medio | 0.485 / 14/14 | 0.485 / 14/14 | 0.432 / 13/14 | 0.470 / 14/14 |
| PlantUML | Gemma 4 12B QAT | alto | 0.260 / 12/12 | 0.250 / 12/12 | 0.290 / 12/12 | 0.290 / 12/12 |
| JSON compatto | Gemma 4 12B QAT | basso | 0.083 / 8/14 | 0.200 / 9/14 | 0.183 / 13/14 | 0.125 / 10/14 |
| JSON compatto | Gemma 4 12B QAT | medio | 0.303 / 9/14 | 0.462 / 14/14 | 0.409 / 14/14 | 0.439 / 11/14 |
| JSON compatto | Gemma 4 12B QAT | alto | 0.240 / 9/12 | 0.240 / 11/12 | 0.250 / 12/12 | 0.220 / 11/12 |
| PlantUML | Qwen2.5-Coder 7B | basso | 0.075 / 14/14 | 0.075 / 12/14 | 0.075 / 13/14 | 0.100 / 13/14 |
| PlantUML | Qwen2.5-Coder 7B | medio | 0.205 / 12/14 | 0.250 / 13/14 | 0.227 / 12/14 | 0.242 / 12/14 |
| PlantUML | Qwen2.5-Coder 7B | alto | 0.130 / 12/12 | 0.130 / 11/12 | 0.100 / 11/12 | 0.120 / 9/12 |
| JSON compatto | Qwen2.5-Coder 7B | basso | 0.083 / 7/14 | 0.100 / 6/14 | 0.042 / 8/14 | 0.075 / 12/14 |
| JSON compatto | Qwen2.5-Coder 7B | medio | 0.212 / 5/14 | 0.167 / 4/14 | 0.189 / 3/14 | 0.295 / 7/14 |
| JSON compatto | Qwen2.5-Coder 7B | alto | 0.080 / 4/12 | 0.120 / 4/12 | 0.100 / 6/12 | 0.050 / 2/12 |

## Fallimenti per configurazione e k

- P-G, k=2: nessuno (L4) 40
- P-G, k=3: nessuno (L4) 40
- P-G, k=5: nessuno (L4) 40
- P-G, k=8: nessuno (L4) 40
- C-G, k=2: incomplete_json 3, invalid_json 2, nessuno (L4) 35
- C-G, k=3: invalid_json 1, nessuno (L4) 39
- C-G, k=5: invalid_json 1, nessuno (L4) 39
- C-G, k=8: invalid_json 3, nessuno (L4) 37
- P-Q, k=2: nessuno (L4) 36, style 4
- P-Q, k=3: nessuno (L4) 34, style 6
- P-Q, k=5: nessuno (L4) 36, style 4
- P-Q, k=8: nessuno (L4) 35, style 5
- C-Q, k=2: invalid_json 6, nessuno (L4) 29, style 5
- C-Q, k=3: invalid_json 7, nessuno (L4) 32, style 1
- C-Q, k=5: invalid_json 2, nessuno (L4) 33, style 5
- C-Q, k=8: invalid_json 3, nessuno (L4) 34, style 3
