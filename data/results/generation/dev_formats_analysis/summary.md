# Insieme di sviluppo — PlantUML contro JSON compatto (`dev_formats`)

Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set. Regola registrata PRIMA delle run (docs/decisions.md, voce 92) e applicata cosi' com'e' da `experiments/analyze_dev.py`, ricalcolando tutto dalle risposte grezze. Metriche di sviluppo: le metriche semantiche definitive restano da decidere con i relatori. Confronto per contenuto, mai per id. Modelli di taglia diversa (Gemma 4 12B QAT, Qwen2.5-Coder 7B, voce 85).

Analisi eseguita sul commit `366ed7a1e7af` (con modifiche non committate). GT del corpus: 59 diagrammi, sha256 del contenuto `b400d1dd7954e8a97c88ff604bc47f294e7eca2cb17d9cd7dd680542fd5db5fd` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `01ef9a52fa255f07…`.
Post-processing PlantUML: v2.

## Regola di confronto (voce 92), applicata cosi' com'e'

**Esito: vince il formato PlantUML**

### Sulle 80 risposte per formato (2 modelli x 20 esercizi x 2 ripetizioni)

| criterio | PlantUML | compatto | compatto − PlantUML | soglia (80 risposte) |
|---|---|---|---|---|
| Vc (valide fino a L3 senza scarti) | 73 | 42 | -31 | 4 |

Vincitore: **PlantUML** (deciso da: Vc).

### Gemma 4 12B QAT (40 risposte per formato)

| criterio | PlantUML | compatto | compatto − PlantUML | soglia (40 risposte) |
|---|---|---|---|---|
| Vc (valide fino a L3 senza scarti) | 37 | 29 | -8 | 2 |

Vincitore: **PlantUML** (deciso da: Vc).

### Qwen2.5-Coder 7B (40 risposte per formato)

| criterio | PlantUML | compatto | compatto − PlantUML | soglia (40 risposte) |
|---|---|---|---|---|
| Vc (valide fino a L3 senza scarti) | 36 | 13 | -23 | 2 |

Vincitore: **PlantUML** (deciso da: Vc).

## Metriche per configurazione

J e R della regola su TUTTE le risposte (0 per le non valide); J_valide e R_valide solo sulle valide (secondarie).

| configurazione | V | Vc | J | R | J_valide | R_valide | troncate | latenza mediana (s) |
|---|---|---|---|---|---|---|---|---|
| P-G | 40/40 | 37/40 | 0.528 | 0.287 | 0.528 | 0.287 | 0 | 7.6 |
| P-Q | 40/40 | 36/40 | 0.516 | 0.151 | 0.516 | 0.151 | 0 | 5.8 |
| C-G | 34/40 | 29/40 | 0.424 | 0.207 | 0.498 | 0.253 | 0 | 12.1 |
| C-Q | 33/40 | 13/40 | 0.425 | 0.111 | 0.515 | 0.134 | 0 | 13.3 |

### Livelli, fallimenti, scarti e normalizzazioni

Livelli cumulativi: P0 / C0 trovato, P1b / C2b convertito (= L1), L2, L3, L4; pulite = P1 o C2 (senza scarti).

| configurazione | trovato | convertito | L2 | L3 | L4 | pulite (L3 e senza scarti) | scarti (totale) |
|---|---|---|---|---|---|---|---|
| P-G | 40 | 40 | 40 | 40 | 40 | 37 | 16 |
| P-Q | 40 | 40 | 40 | 40 | 36 | 36 | 5 |
| C-G | 36 | 34 | 34 | 34 | 34 | 29 | 6 |
| C-Q | 40 | 33 | 33 | 33 | 29 | 13 | 74 |
- P-G: fallimenti nessuno (L4) 40; righe scartate piu' frequenti "'}'" 4, "'class OnshoreWell --|> Well {'" 2, "'+ surfaceExtension : float'" 2, "'class OffshoreWell --|> Well {'" 2, "'+ installationYear : int'" 2
- P-Q: fallimenti nessuno (L4) 36, style 4; righe scartate piu' frequenti '\'PickupVehicle "0..*" VolunteerDriver : assigned to\'' 1, '\'H2SEmployee "0..*" DeliveryDriver : arranges delivery with\'' 1, '\'BusinessUser "1..*" Song\'' 1, '\'Order "0..*" EntertainmentOrder : includes\'' 1, '\'HungryCustomer "0..*" Order : makes\'' 1
- C-G: fallimenti incomplete_json 4, invalid_json 2, nessuno (L4) 34; scarti del compatto chiavi di verso di un'altra famiglia (relazione scartata) 4, chiave di relazione non prevista (ignorata) 2
- C-Q: fallimenti invalid_json 7, nessuno (L4) 29, style 4; scarti del compatto chiave di classe non prevista (ignorata) 56, relazione verso una classe non dichiarata (scartata) 10, chiave di relazione non prevista (ignorata) 8; normalizzazioni metodi 2

### Relazioni (risposte valide fino a L3)

| configurazione | relazioni GT (tutte le risposte) | stessa coppia | stesso tipo | stesso verso (tipi orientati) | comp./aggr.: stesso verso | stesse molteplicita' |
|---|---|---|---|---|---|---|
| P-G | 352 | 145 | 101 | 28/43 | 6/6 | 37/109 |
| P-Q | 352 | 79 | 53 | 16/16 | 2/2 | 17/60 |
| C-G | 352 | 124 | 73 | 46/46 | 6/6 | 25/87 |
| C-Q | 352 | 75 | 39 | 15/16 | 4/4 | 11/60 |

### Confronto appaiato (stesso esercizio, modello e ripetizione; solo descrittivo)

| modello | criterio | entrambe | solo PlantUML | solo compatto | nessuna |
|---|---|---|---|---|---|
| Gemma 4 12B QAT | Vc | 26 | 11 | 3 | 0 |
| Gemma 4 12B QAT | V | 34 | 6 | 0 | 0 |
| Qwen2.5-Coder 7B | Vc | 13 | 23 | 0 | 4 |
| Qwen2.5-Coder 7B | V | 33 | 7 | 0 | 0 |

### Per fascia di score_norm (solo descrittivo)

| formato | fascia | risposte | Vc | V | J | R |
|---|---|---|---|---|---|---|
| PlantUML | basso | 28 | 24 | 28 | 0.467 | 0.108 |
| PlantUML | medio | 28 | 25 | 28 | 0.603 | 0.330 |
| PlantUML | alto | 24 | 24 | 24 | 0.492 | 0.205 |
| JSON compatto | basso | 28 | 14 | 23 | 0.389 | 0.079 |
| JSON compatto | medio | 28 | 14 | 23 | 0.462 | 0.227 |
| JSON compatto | alto | 24 | 14 | 21 | 0.421 | 0.165 |

### Token e latenze

| configurazione | prompt reale (min / mediana / max) | completamento (min / mediana / max) | latenza s (min / mediana / max) | durata (min) |
|---|---|---|---|---|
| P-G | 2261 / 3078 / 3791 | 150 / 246 / 537 | 5.1 / 7.6 / 14.3 | 5.5 |
| P-Q | 2216 / 3006 / 3721 | 87 / 190 / 413 | 3.7 / 5.8 / 9.7 | 4.0 |
| C-G | 2623 / 3577 / 4224 | 201 / 465 / 1094 | 6.1 / 12.1 / 25.9 | 8.6 |
| C-Q | 2585 / 3508 / 4148 | 228 / 554 / 1008 | 6.7 / 13.3 / 22.6 | 9.5 |
