# Insieme di sviluppo — istruzioni mirate (`dev_instructions` contro `dev_k`, k = 3)

Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set. Gemma 4 12B QAT, versione di configurazione 2, bm25 k = 3. Baseline: risposte a k = 3 di `dev_k`; trattamento: `dev_instructions` (stessi prompt salvo il blocco congelato della voce 98). Regola registrata PRIMA della run (voce 98) e applicata cosi' com'e' da `experiments/analyze_instructions.py`; ground truth attuale del corpus (eHome2020 corretto, voce 99). Confronto per contenuto, mai per id.

Analisi eseguita sul commit `366ed7a1e7af` (con modifiche non committate). GT del corpus: 59 diagrammi, sha256 del contenuto `b400d1dd7954e8a97c88ff604bc47f294e7eca2cb17d9cd7dd680542fd5db5fd` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `01ef9a52fa255f07…`.

## Regola di adozione (voce 98), applicata cosi' com'e'

Adottare se (dM_primaria >= 0,05 OPPURE dR >= 0,03) E dR >= -0,03 E dVc >= -2 (delta = trattamento - baseline, 40 risposte per parte).

- **PlantUML: istruzioni mirate NON adottate** (dM_primaria +0.002, dR +0.006, dVc +0; guadagno no, R mantenuto si, Vc mantenuto si)
- **JSON compatto: istruzioni mirate NON adottate** (dM_primaria +0.008, dR -0.037, dVc +0; guadagno no, R mantenuto no, Vc mantenuto si)

## Metriche per formato: baseline contro trattamento

M primaria: estremi del GT con molteplicita' esplicita; M secondaria: tutti gli estremi del GT. J, R, M su tutte le risposte (0 per le non valide); J_valide e R_valide sulle sole valide.

| formato | parte | V | Vc | J | R | M primaria | M secondaria | J_valide | R_valide | stesso tipo (coppie accoppiate) | verso uguale | scarti | troncate | prompt med | completamento med | latenza med (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PlantUML | baseline | 40/40 | 40/40 | 0.544 | 0.307 | 0.282 (137/486) | 0.248 (137/552) | 0.544 | 0.307 | 0.692 | 21/33 | 0 | 0 | 3691 | 261 | 8.4 |
| PlantUML | istruzioni mirate | 40/40 | 40/40 | 0.551 | 0.312 | 0.284 (138/486) | 0.254 (140/552) | 0.551 | 0.312 | 0.705 | 25/38 | 0 | 0 | 4057 | 250 | 8.0 |
| JSON compatto | baseline | 39/40 | 34/40 | 0.529 | 0.310 | 0.214 (104/486) | 0.188 (104/552) | 0.542 | 0.318 | 0.690 | 46/46 | 9 | 0 | 4293 | 552 | 14.5 |
| JSON compatto | istruzioni mirate | 39/40 | 34/40 | 0.520 | 0.273 | 0.222 (108/486) | 0.196 (108/552) | 0.534 | 0.280 | 0.636 | 49/49 | 15 | 0 | 4669 | 632 | 18.8 |

## Tabelle di confusione — PlantUML (risposte valide)

### Molteplicita' per estremo (GT -> risposta), i casi piu' frequenti

| GT -> risposta | baseline | istruzioni mirate |
|---|---|---|
| '1' -> '1' | 79 | 77 |
| '*' -> '*' | 49 | 51 |
| '(vuoto)' -> '1' (errore) | 33 | 35 |
| '*' -> '1' (errore) | 19 | 18 |
| '*' -> '1..*' (errore) | 18 | 13 |
| '(vuoto)' -> '*' (errore) | 7 | 8 |
| '0..1' -> '1' (errore) | 6 | 6 |
| '1..*' -> '1..*' | 6 | 6 |
| '*' -> '0..1' (errore) | 4 | 5 |
| '(vuoto)' -> '0..1' (errore) | 4 | 3 |
| '(vuoto)' -> '1..*' (errore) | 2 | 2 |
| '1' -> '*' (errore) | 2 | 2 |
| '1..*' -> '*' (errore) | 2 | 2 |
| '2..*' -> '2..*' | 2 | 2 |
| '0..1' -> '*' (errore) | 2 | 1 |
| '0..1' -> '0..1' | 1 | 2 |

### Tipi di relazione (GT -> risposta, coppie accoppiate)

| GT -> risposta | baseline | istruzioni mirate |
|---|---|---|
| associazione -> associazione | 75 | 72 |
| generalizzazione -> generalizzazione | 27 | 34 |
| unidirezionale -> associazione | 13 | 13 |
| associazione -> composizione | 12 | 12 |
| unidirezionale -> composizione | 9 | 10 |
| generalizzazione -> associazione | 9 | 4 |
| composizione -> composizione | 6 | 3 |
| unidirezionale -> aggregazione | 3 | 2 |
| associazione -> aggregazione | 2 | 2 |
| composizione -> associazione | 0 | 2 |
| composizione -> aggregazione | 0 | 1 |
| unidirezionale -> unidirezionale | 0 | 1 |

### Verso (stesso tipo orientato): invertite / totale

| tipo | baseline | istruzioni mirate |
|---|---|---|
| composizione | 0/6 | 0/3 |
| generalizzazione | 12/27 | 13/34 |
| unidirezionale | 0/0 | 0/1 |

Classi in piu' rispetto al GT: baseline 122, istruzioni mirate 120; generalizzazioni in piu' (assenti dal GT): baseline 33, istruzioni mirate 36.

## Tabelle di confusione — JSON compatto (risposte valide)

### Molteplicita' per estremo (GT -> risposta), i casi piu' frequenti

| GT -> risposta | baseline | istruzioni mirate |
|---|---|---|
| '1' -> '1' | 58 | 54 |
| '*' -> '*' | 39 | 47 |
| '(vuoto)' -> '1' (errore) | 37 | 33 |
| '*' -> '1' (errore) | 18 | 18 |
| '*' -> '1..*' (errore) | 28 | 6 |
| '1' -> '(vuoto)' (errore) | 6 | 10 |
| '1' -> '*' (errore) | 6 | 9 |
| '*' -> '(vuoto)' (errore) | 4 | 8 |
| '1' -> '1..*' (errore) | 7 | 3 |
| '1..*' -> '1..*' | 5 | 5 |
| '(vuoto)' -> '*' (errore) | 3 | 5 |
| '(vuoto)' -> '0..1' (errore) | 4 | 4 |
| '(vuoto)' -> '1..*' (errore) | 4 | 4 |
| '0..1' -> '1' (errore) | 5 | 3 |
| '*' -> '0..1' (errore) | 3 | 4 |
| '0..1' -> '*' (errore) | 3 | 3 |

### Tipi di relazione (GT -> risposta, coppie accoppiate)

| GT -> risposta | baseline | istruzioni mirate |
|---|---|---|
| associazione -> associazione | 63 | 47 |
| generalizzazione -> generalizzazione | 40 | 40 |
| associazione -> composizione | 18 | 22 |
| unidirezionale -> composizione | 13 | 13 |
| unidirezionale -> associazione | 8 | 6 |
| associazione -> unidirezionale | 5 | 8 |
| composizione -> composizione | 5 | 6 |
| associazione -> dipendenza | 2 | 2 |
| unidirezionale -> aggregazione | 2 | 2 |
| unidirezionale -> unidirezionale | 1 | 3 |
| associazione -> aggregazione | 1 | 2 |

### Verso (stesso tipo orientato): invertite / totale

| tipo | baseline | istruzioni mirate |
|---|---|---|
| composizione | 0/5 | 0/6 |
| generalizzazione | 0/40 | 0/40 |
| unidirezionale | 0/1 | 0/3 |

Classi in piu' rispetto al GT: baseline 124, istruzioni mirate 119; generalizzazioni in piu' (assenti dal GT): baseline 23, istruzioni mirate 29.
