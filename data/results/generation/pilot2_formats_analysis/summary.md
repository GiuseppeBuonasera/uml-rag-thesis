# Secondo pilota — PlantUML contro JSON vincolato (`pilot2_formats`)

**Esperimento PRELIMINARE** sul corpus (split `corpus`, selezione leave-one-out), mai sul test set: da dichiarare come tale in tesi. Regola di decisione registrata PRIMA delle run (docs/decisions.md, voce 78, approvata nella voce 79) e applicata cosi' com'e' da `experiments/analyze_pilot2.py` (voce 82), ricalcolando tutto dalle risposte grezze (`raw/`).

Analisi eseguita sul commit `22f5adfbe6ce` (con modifiche non committate). GT del corpus: 59 diagrammi, sha256 del contenuto `b400d1dd7954e8a97c88ff604bc47f294e7eca2cb17d9cd7dd680542fd5db5fd` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `01ef9a52fa255f07…`.

Esercizi: Louvre, Sober, StudentAppointment, CardGameApp, ApartmentBuilding, FilmSet; bm25 k=2; 2 ripetizioni; temperature 0.3, top_p 0.95, top_k 64, max_tokens 12288.

Il confronto generalista / coding e' tra modelli di **taglia diversa**: Gemma 4 12B QAT (generalista) contro Qwen2.5-Coder 7B Instruct Q6_K (coding), perche' il 14B non entra in VRAM a 32768 (voci 84-85). Le differenze tra i due modelli non si possono attribuire alla sola specializzazione sul codice.

## Regola di decisione (voce 78), applicata cosi' com'e'

**Esito: scelta la configurazione P-Q**

Passi della scelta:

- S piu' alto (pareggio: S >= 12 - 1): P-G 10, P-Q 12, J-G 9, J-Q 0 → restano P-Q

Vincitrice: **P-Q (strada 1 (PlantUML), Qwen2.5-Coder 7B)**.

### Classifica completa delle configurazioni

Posizione k = vincitrice della stessa regola (pareggio entro 1 risposta dal massimo di S, poi gli spareggi nell'ordine) applicata alle configurazioni non ancora classificate; la soglia minima vale solo per la scelta. J = Jaccard medio dei nomi di classe (risposte valide fino a L3); R = relazioni del GT con stessa coppia e stesso tipo / relazioni del GT (risposte valide); latenza mediana su tutte le risposte. P1 (fuori dalla regola, voce 89) = risposte della strada 1 valide fino a L3 e senza righe scartate.

| posizione | configurazione | S (su 12) | P1 senza righe scartate | troncate | J | R | latenza mediana (s) | decisa da | nota |
|---|---|---|---|---|---|---|---|---|---|
| 1 | P-Q (strada 1 (PlantUML), Qwen2.5-Coder 7B) | 12/12 | 8/12 | 0 | 0.577 | 0.183 | 6.0 | S piu' alto (pareggio: S >= 12 - 1) | scelta |
| 2 | P-G (strada 1 (PlantUML), Gemma 4 12B QAT) | 10/12 | 9/12 | 0 | 0.606 | 0.321 | 9.1 | Jaccard medio dei nomi di classe piu' alto |  |
| 3 | J-G (strada 2 (JSON vincolato), Gemma 4 12B QAT) | 9/12 | — | 0 | 0.582 | 0.123 | 99.1 | S piu' alto (pareggio: S >= 9 - 1) |  |
| 4 | J-Q (strada 2 (JSON vincolato), Qwen2.5-Coder 7B) | 0/12 | — | 0 | — | — | 65.2 | S piu' alto (pareggio: S >= 0 - 1) |  |

Riferimenti in JSON libero (Gemma del primo pilota, J0-Q): sezione "Riferimenti", fuori dalla classifica.

## Metriche secondarie (riportate, fuori dalla regola)

### Validita' per livello

Risposte che superano ciascun livello (cumulativo). Strada 1: P0 = blocco @startuml/@enduml, P1b = parsing tollerante e conversione riusciti (corrisponde a L1), P1 = come P1b senza righe scartate; poi gli stessi L2-L4 della strada 2.

| configurazione | P0 / L0 | P1b / L1 | P1 (solo strada 1) | L2 schema | L3 integrita' | L4 stile | troncate | righe scartate (totale) |
|---|---|---|---|---|---|---|---|---|
| P-G | 10 | 10 | 9 | 10 | 10 | 10 | 0 | 1 |
| P-Q | 12 | 12 | 8 | 12 | 12 | 10 | 0 | 42 |
| J-G | 12 | 12 | — | 12 | 9 | 9 | 0 | — |
| J-Q | 12 | 12 | — | 12 | 0 | 0 | 0 | — |

Esiti di fallimento (`failure`):

- P-G: incomplete_block 2, nessuno (L4) 10
- P-Q: nessuno (L4) 10, style 2
- J-G: integrity 3, nessuno (L4) 9
- J-Q: integrity 12

Per esercizio (livello raggiunto da ciascuna ripetizione; −1 = niente estratto):

| esercizio | P-G | P-Q | J-G | J-Q |
|---|---|---|---|---|
| Louvre | 4 / 4 | 3 / 4 | 4 / 4 | 2 / 2 |
| Sober | 4 / 4 | 4 / 4 | 4 / 4 | 2 / 2 |
| StudentAppointment | 4 / 4 | 4 / 4 | 4 / 4 | 2 / 2 |
| CardGameApp | -1 / 4 | 4 / 4 | 2 / 4 | 2 / 2 |
| ApartmentBuilding | 4 / 4 | 4 / 4 | 4 / 4 | 2 / 2 |
| FilmSet | 4 / -1 | 4 / 3 | 2 / 2 | 2 / 2 |

### Relazioni rispetto al ground truth (risposte valide fino a L3)

Accoppiamento 1:1 per coppia di classi non ordinata (come nel primo pilota, `analyze_pilot.compare_relations`). Verso solo per relazioni dello stesso tipo orientato; molteplicita' per estremo, esclusi generalizzazione e realizzazione, con 'n' -> '*' e '0..*' = '*'.

| configurazione | risposte valide | relazioni risposta | relazioni GT | stessa coppia | stesso tipo | stesso verso (tipi orientati) | comp./aggr.: stesso verso | stesse molteplicita' |
|---|---|---|---|---|---|---|---|---|
| P-G | 10 | 81 | 78 | 30 | 25 | 9/9 | 4/4 | 6/25 |
| P-Q | 12 | 62 | 104 | 25 | 19 | 7/7 | 4/4 | 3/22 |
| J-G | 9 | 67 | 65 | 18 | 8 | 3/4 | 3/4 | 6/18 |
| J-Q | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 | 0/0 |

Tipo diverso con la stessa coppia, P-G (GT -> risposta): ClassUnidirectional -> ClassComposition 4, ClassBidirectional -> ClassInheritance 1

Tipo diverso con la stessa coppia, P-Q (GT -> risposta): ClassUnidirectional -> ClassBidirectional 4, ClassBidirectional -> ClassComposition 2

Tipo diverso con la stessa coppia, J-G (GT -> risposta): ClassUnidirectional -> ClassComposition 5, ClassBidirectional -> ClassUnidirectional 3, ClassBidirectional -> ClassAggregation 2

### Tempi e token

| configurazione | latenza s (min / mediana / max) | token di completamento (min / mediana / max) | prompt reale (min / mediana / max) | token reali / stima cl100k_base (min / mediana / max) | durata totale (min) |
|---|---|---|---|---|---|
| P-G | 4.2 / 9.1 / 10.6 | 102 / 316 / 387 | 2198 / 3066 / 3215 | 1.032 / 1.039 / 1.046 | 1.6 |
| P-Q | 4.3 / 6.0 / 7.7 | 120 / 250 / 363 | 2137 / 2992 / 3149 | 1.010 / 1.012 / 1.014 | 1.2 |
| J-G | 45.5 / 99.1 / 162.0 | 2104 / 4470 / 7632 | 8046 / 12010 / 14672 | 1.195 / 1.222 / 1.239 | 19.7 |
| J-Q | 22.2 / 65.2 / 151.8 | 1217 / 3724 / 8639 | 7806 / 11674 / 14286 | 1.161 / 1.187 / 1.206 | 13.3 |

### Diagnostici (non metriche; non si combinano con i livelli)

Risposte con almeno un diagnostico, tra quelle che superano L1. Strada 1: i diagnostici sul JSON (es. `interactive_present`, layout) riguardano l'Apollon prodotto dal convertitore, non la risposta del modello; solo `extra_text` (testo attorno al blocco PlantUML) riguarda la risposta.

| configurazione | formato della risposta | layout |
|---|---|---|
| P-G | interactive_present n/a (aggiunto dal convertitore) | nessuno |
| P-Q | interactive_present n/a (aggiunto dal convertitore) | nessuno |
| J-G | nessuno | out_of_canvas 1, overlapping_nodes 2 |
| J-Q | nessuno | nessuno |

## Riferimenti (solo descrittivi, fuori dalla regola e dalla classifica)

Configurazioni in Apollon JSON LIBERO (senza response_format), voce 83: completano il confronto 2x2 della strada JSON, per separare l'effetto del modello da quello del vincolo. Stesse metriche delle configurazioni (S = risposte valide fino a L3; J, R e latenza come nella classifica). G-libero viene dal primo pilota: altra run, 3 ripetizioni per esercizio (18 risposte) invece di 2; le proporzioni sono quindi su totali diversi.

| riferimento | modello | run | S | L0 | L1 | L2 | L3 | L4 | troncate | J | R | latenza mediana (s) | stato |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G-libero (primo pilota) | Gemma 4 12B QAT | `pilot_temperature_gemma4-12b-qat`, solo temperature 0.3 | 8/18 (0.44) | 14 | 13 | 12 | 8 | 8 | 3 | 0.705 | 0.250 | 93.1 | completa (18/18) |
| J0-Q | Qwen2.5-Coder 7B | `pilot2_formats__J0-Q` | 1/12 (0.08) | 11 | 11 | 11 | 1 | 0 | 1 | 0.375 | 0.000 | 67.6 | completa (12/12) |

Esiti di fallimento e relazioni (risposte valide fino a L3):

- G-libero (primo pilota): incomplete_json 1, integrity 4, invalid_json 1, nessuno (L4) 8, schema 1, truncated 3; relazioni: stessa coppia 19/48, stesso tipo 12, stesso verso 8/9, stesse molteplicita' 8/16
- J0-Q: integrity 10, style 1, truncated 1; relazioni: stessa coppia 2/13, stesso tipo 0, stesso verso 0/0, stesse molteplicita' 0/2

Prompt identico al primo pilota (sha256 dei messaggi, stesso esercizio):

- J-G: 12/12 risposte
- J-Q: 12/12 risposte
- J0-Q: 12/12 risposte

### Tabella 2x2 della strada JSON: S (risposte valide fino a L3)

| modello | JSON libero | JSON vincolato (schema) |
|---|---|---|
| Gemma 4 12B QAT | 8/18 (0.44) | 9/12 (0.75) |
| Qwen2.5-Coder 7B | 1/12 (0.08) | 0/12 (0.00) |

Gemma libero: primo pilota (18 risposte a temperature 0.3); le altre celle: secondo pilota (12 risposte). Il confronto generalista / coding e' tra modelli di **taglia diversa**: Gemma 4 12B QAT (generalista) contro Qwen2.5-Coder 7B Instruct Q6_K (coding), perche' il 14B non entra in VRAM a 32768 (voci 84-85). Le differenze tra i due modelli non si possono attribuire alla sola specializzazione sul codice. Solo descrittivo: nessun test statistico, n piccoli; una cella vuota (—) e' una run assente. Le celle riportano S anche per le run escluse dalla regola (stato nella tabella sopra o nella classifica).
