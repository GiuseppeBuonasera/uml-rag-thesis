# Quali esempi aiutano? (analisi descrittiva, voce 120 passo 1)

Risposte di sviluppo di Gemma 4 12B QAT con istruzioni v4 (dev_k, dev_retrievers, dev_v5base). R per risposta (0 se non valida). Spearman tra gli SCARTI dalla media dello stesso esercizio e formato (toglie la difficoltà dell'esercizio). Solo descrittivo: nessuna decisione.

Analisi eseguita sul commit `2b74319a3f11` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

| formato | risposte | jt_query | coverage | quality | size | debari | k |
|---|---|---|---|---|---|---|---|
| plantuml | 320 | +0.02 (p 0.670) | +0.05 (p 0.352) | -0.09 (p 0.109) | -0.08 (p 0.153) | +0.08 (p 0.149) | -0.03 (p 0.601) |
| compact | 320 | -0.07 (p 0.195) | +0.22 (p 0.000) | -0.04 (p 0.442) | +0.19 (p 0.001) | -0.02 (p 0.749) | +0.15 (p 0.006) |

Proprietà: jt_query = somiglianza dei nomi di classe tra GT della query ed esempi; coverage = quota dei tipi di relazione della query presenti negli esempi; quality = completezza del GT degli esempi (molteplicità e tipi degli attributi); size = relazioni per esempio; debari = quota di esempi De Bari; k = numero di esempi. Un rho positivo vuol dire che, a parità di esercizio, risposte con valori più alti hanno R più alto.
