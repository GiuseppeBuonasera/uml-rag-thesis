# Controllo "esempi senza attributi" — SOLO ANALISI

54 esercizi di validazione, Gemma 4 26B A4B QAT, configurazione del 3b, 1 ripetizione. A = esercizio stesso con classi e relazioni perfette e nessun attributo (blocco libero); B = gli esempi bm25 k3 del 3b senza attributi (blocco standard). Regola registrata PRIMA della run (voce 167), applicata da `experiments/analyze_oracle_attr.py`.

Analisi eseguita sul commit `1816fc31ce77` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Esito B (causa degli scheletri)

- **PlantUML: la forma vuota degli esempi CAUSA gli scheletri** (scheletri B 0.19 contro 3b bm25 k3 0.02; d = +0.170, Wilcoxon p 0.003, 53 esercizi)
- **JSON compatto: la forma vuota degli esempi CAUSA gli scheletri** (scheletri B 0.91 contro 3b bm25 k3 0.28; d = +0.623, Wilcoxon p 0.000, 53 esercizi)

## Metriche (media per esercizio)

| formato | esempi | scheletri | attributi R | attributi P | attributi F1 | completezza | non valide |
|---|---|---|---|---|---|---|---|
| PlantUML | A: esercizio stesso senza attributi | 0.21 | 0.346 | 0.504 | 0.355 | 0.610 | 0.00 |
| PlantUML | esercizio stesso con attributi | 0.00 | 0.696 | 0.753 | 0.704 | 0.760 | 0.00 |
| PlantUML | B: bm25 k3 senza attributi | 0.19 | 0.324 | 0.431 | 0.324 | 0.422 | 0.00 |
| PlantUML | bm25 k3 del 3b (con attributi) | 0.02 | 0.346 | 0.387 | 0.347 | 0.434 | 0.00 |
| JSON compatto | A: esercizio stesso senza attributi | 0.49 | 0.242 | 0.553 | 0.249 | 0.516 | 0.00 |
| JSON compatto | esercizio stesso con attributi | 0.15 | 0.499 | 0.642 | 0.509 | 0.635 | 0.00 |
| JSON compatto | B: bm25 k3 senza attributi | 0.91 | 0.031 | 0.348 | 0.032 | 0.308 | 0.00 |
| JSON compatto | bm25 k3 del 3b (con attributi) | 0.28 | 0.309 | 0.404 | 0.294 | 0.411 | 0.01 |

## Variante A: quanta parte degli attributi viene dal testo

- PlantUML: recall degli attributi senza attributi nell'esempio / con attributi = 0.50
- JSON compatto: recall degli attributi senza attributi nell'esempio / con attributi = 0.48

Scheletro = risposta valida senza nessun attributo per un GT che ne ha (non valide escluse, riportate a parte); completezza come la voce 162.
