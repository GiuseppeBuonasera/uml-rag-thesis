# Insieme di sviluppo — istruzioni v5 (`dev_v5` contro `dev_v5base` v4, k = 3)

Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set. Gemma 4 12B QAT, versione di configurazione 2, bm25 k = 3, pool unico (voce 115). Baseline: `dev_v5base` (istruzioni v4); trattamento: `dev_v5` (istruzioni v5, riga finale della traccia, esempi PlantUML con l'ereditarietà nell'intestazione). Regola registrata PRIMA della run (voce 111) e applicata così com'è da `experiments/analyze_v5.py`; ground truth attuale del corpus; molteplicità normalizzate ('1..1' = '1'). Confronto per contenuto, mai per id.

Analisi eseguita sul commit `2b74319a3f11` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Regola di adozione (voce 111), applicata così com'è

Adottare v5 se [dR >= +0,03 OPPURE dR_fam >= +0,03 OPPURE (solo PlantUML) generalizzazioni invertite ridotte almeno della metà] E dVc >= -2 E dM_primaria >= -0,03 (delta = v5 - v4, 40 risposte per parte).

- **PlantUML: v5 ADOTTATA** (dR +0.040, dR_fam +0.037, generalizzazioni invertite dimezzate sì; dVc -2, dM_primaria +0.037; guadagno sì, Vc mantenuto sì, M mantenuto sì)
- **JSON compatto: v5 NON adottata (resta v4)** (dR -0.017, dR_fam -0.023, generalizzazioni invertite dimezzate no (criterio solo PlantUML); dVc -6, dM_primaria +0.016; guadagno no, Vc mantenuto no, M mantenuto sì)

## Metriche per formato: v4 (baseline) contro v5

J, R, R_fam, M su tutte le risposte (0 per le non valide). Generalizzazioni invertite: generalizzazioni del GT accoppiate con figlia e madre scambiate / generalizzazioni accoppiate dello stesso tipo.

| formato | istruzioni | V | Vc | J | R | R_fam | M primaria | generalizzazioni invertite | verso uguale | classi in più | generalizzazioni in più | composizioni in più | scarti | troncate | completamento med | latenza med (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PlantUML | v4 (baseline) | 40/40 | 40/40 | 0.532 | 0.321 | 0.349 | 0.280 (136/486) | 16/32 | 24/40 | 120 | 35 | 42 | 0 | 0 | 256 | 22.9 |
| PlantUML | v5 | 40/40 | 38/40 | 0.540 | 0.361 | 0.386 | 0.317 (154/486) | 0/40 | 47/47 | 115 | 20 | 43 | 4 | 0 | 218 | 8.0 |
| JSON compatto | v4 (baseline) | 35/40 | 33/40 | 0.452 | 0.210 | 0.250 | 0.156 (76/486) | 0/32 | 40/40 | 111 | 13 | 85 | 6 | 0 | 542 | 39.7 |
| JSON compatto | v5 | 30/40 | 27/40 | 0.371 | 0.193 | 0.227 | 0.173 (84/486) | 0/24 | 27/27 | 100 | 20 | 29 | 3 | 0 | 354 | 10.8 |

## Tabelle di confusione — PlantUML (risposte valide)

### Molteplicità per estremo (GT -> risposta), i casi più frequenti

| GT -> risposta | v4 | v5 |
|---|---|---|
| '1' -> '1' | 79 | 80 |
| '*' -> '*' | 48 | 67 |
| '(vuoto)' -> '1' (errore) | 33 | 32 |
| '*' -> '1' (errore) | 18 | 20 |
| '*' -> '1..*' (errore) | 18 | 8 |
| '(vuoto)' -> '*' (errore) | 5 | 6 |
| '0..1' -> '1' (errore) | 5 | 5 |
| '1..*' -> '1..*' | 6 | 4 |
| '*' -> '0..1' (errore) | 5 | 3 |
| '(vuoto)' -> '0..1' (errore) | 3 | 4 |
| '0..1' -> '*' (errore) | 3 | 3 |
| '1..*' -> '*' (errore) | 2 | 4 |
| '(vuoto)' -> '1..*' (errore) | 3 | 2 |
| '2..*' -> '2..*' | 2 | 2 |
| '1' -> '*' (errore) | 0 | 3 |
| '(vuoto)' -> '(vuoto)' | 2 | 0 |

### Tipi di relazione (GT -> risposta, coppie accoppiate)

| GT -> risposta | v4 | v5 |
|---|---|---|
| associazione -> associazione | 73 | 80 |
| generalizzazione -> generalizzazione | 32 | 40 |
| associazione -> composizione | 13 | 11 |
| unidirezionale -> associazione | 10 | 9 |
| unidirezionale -> composizione | 10 | 9 |
| composizione -> composizione | 6 | 5 |
| generalizzazione -> associazione | 7 | 1 |
| unidirezionale -> aggregazione | 3 | 4 |
| unidirezionale -> unidirezionale | 2 | 2 |
| associazione -> aggregazione | 2 | 1 |
| composizione -> associazione | 0 | 1 |

### Verso (stesso tipo orientato): invertite / totale

| tipo | v4 | v5 |
|---|---|---|
| composizione | 0/6 | 0/5 |
| generalizzazione | 16/32 | 0/40 |
| unidirezionale | 0/2 | 0/2 |

## Tabelle di confusione — JSON compatto (risposte valide)

### Molteplicità per estremo (GT -> risposta), i casi più frequenti

| GT -> risposta | v4 | v5 |
|---|---|---|
| '1' -> '1' | 43 | 37 |
| '*' -> '*' | 28 | 41 |
| '(vuoto)' -> '1' (errore) | 36 | 14 |
| '*' -> '1' (errore) | 16 | 12 |
| '*' -> '1..*' (errore) | 22 | 0 |
| '1' -> '*' (errore) | 2 | 12 |
| '(vuoto)' -> '*' (errore) | 5 | 8 |
| '1' -> '(vuoto)' (errore) | 8 | 2 |
| '0..1' -> '*' (errore) | 3 | 5 |
| '1' -> '1..*' (errore) | 7 | 0 |
| '1..*' -> '1..*' | 4 | 2 |
| '(vuoto)' -> '1..*' (errore) | 3 | 2 |
| '1..*' -> '*' (errore) | 2 | 3 |
| '(vuoto)' -> '0..1' (errore) | 4 | 0 |
| '*' -> '(vuoto)' (errore) | 4 | 0 |
| '0..1' -> '1' (errore) | 2 | 2 |

### Tipi di relazione (GT -> risposta, coppie accoppiate)

| GT -> risposta | v4 | v5 |
|---|---|---|
| associazione -> associazione | 34 | 41 |
| generalizzazione -> generalizzazione | 32 | 24 |
| associazione -> composizione | 20 | 11 |
| unidirezionale -> associazione | 5 | 12 |
| unidirezionale -> composizione | 14 | 3 |
| associazione -> unidirezionale | 9 | 0 |
| composizione -> composizione | 5 | 3 |
| composizione -> associazione | 0 | 3 |
| unidirezionale -> unidirezionale | 3 | 0 |
| associazione -> aggregazione | 2 | 0 |
| associazione -> dipendenza | 2 | 0 |
| unidirezionale -> aggregazione | 2 | 0 |
| unidirezionale -> generalizzazione | 0 | 1 |

### Verso (stesso tipo orientato): invertite / totale

| tipo | v4 | v5 |
|---|---|---|
| composizione | 0/5 | 0/3 |
| generalizzazione | 0/32 | 0/24 |
| unidirezionale | 0/3 | 0/0 |
