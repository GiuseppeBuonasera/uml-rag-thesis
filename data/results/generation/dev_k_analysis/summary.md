# Insieme di sviluppo — numero di esempi k (`dev_k`)

Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set; versione di configurazione 2 (contesto 32768, max_tokens 4096). Regola registrata PRIMA delle run (docs/decisions.md, voce 94) e applicata cosi' com'e' da `experiments/analyze_k.py`; metriche della voce 92 (J e R su tutte le risposte, 0 per le non valide). Confronto per contenuto, mai per id. La leva vale solo per le condizioni con esempi: sul test set il confronto con random dovra' usare lo stesso k.

Analisi eseguita sul commit `e9645e208b7f` (con modifiche non committate).

## Regola di scelta di k (voce 94), applicata cosi' com'e'

- **PlantUML: STOP: formato non decidibile (controllo preliminare)**
  - esclusa P-Q: non eseguita (nessun config.json in dev_k__P-Q/)
- **JSON compatto: STOP: formato non decidibile (controllo preliminare)**
  - esclusa C-Q: non eseguita (nessun config.json in dev_k__C-Q/)

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

## Fallimenti per configurazione e k

- P-G, k=2: nessuno (L4) 40
- P-G, k=3: nessuno (L4) 40
- P-G, k=5: nessuno (L4) 40
- P-G, k=8: nessuno (L4) 40
- C-G, k=2: incomplete_json 3, invalid_json 2, nessuno (L4) 35
- C-G, k=3: invalid_json 1, nessuno (L4) 39
- C-G, k=5: invalid_json 1, nessuno (L4) 39
- C-G, k=8: invalid_json 3, nessuno (L4) 37
- P-Q: non eseguita (nessun config.json in dev_k__P-Q/)
- C-Q: non eseguita (nessun config.json in dev_k__C-Q/)
