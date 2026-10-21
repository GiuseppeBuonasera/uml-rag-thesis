# Controllo "esercizio stesso come esempio" (oracle_self) — SOLO ANALISI

54 esercizi di validazione, Gemma 4 26B A4B QAT, configurazione del 3b; unico esempio = l'esercizio stesso con la sua soluzione. Varianti: `standard` ("do not copy their classes" nel blocco esempi) e `libero` (senza). Regola di lettura registrata PRIMA della run (voce 162), applicata da `experiments/analyze_oracle_self.py`.

Analisi eseguita sul commit `ffb0c03e769d` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Esito (regola della voce 162, variante libero)

- **PlantUML: uso PARZIALE del contenuto di un esempio perfetto** (completezza libero 0.760, standard 0.746)
- **JSON compatto: uso PARZIALE del contenuto di un esempio perfetto** (completezza libero 0.635, standard 0.639)

## Metriche (media per esercizio)

| formato | prompt | completezza | precision | copia quasi esatta | J nomi | F1 classi | F1 attributi | F1 relazioni | F1 generalizz. | non valide |
|---|---|---|---|---|---|---|---|---|---|---|
| PlantUML | libero | 0.760 | 0.791 | 13% | 0.817 | 0.887 | 0.704 | 0.712 | 0.775 | 0 |
| PlantUML | standard | 0.746 | 0.771 | 17% | 0.818 | 0.889 | 0.649 | 0.702 | 0.762 | 0 |
| PlantUML | 3b bm25 | 0.434 | 0.482 | 0% | 0.495 | 0.646 | 0.347 | 0.432 | 0.252 | 0 |
| PlantUML | 3b zero_shot | 0.423 | 0.476 | 0% | 0.482 | 0.631 | 0.328 | 0.426 | 0.256 | 1 |
| JSON compatto | libero | 0.635 | 0.715 | 9% | 0.721 | 0.824 | 0.509 | 0.646 | 0.624 | 0 |
| JSON compatto | standard | 0.639 | 0.696 | 6% | 0.725 | 0.826 | 0.507 | 0.645 | 0.672 | 0 |
| JSON compatto | 3b bm25 | 0.411 | 0.495 | 0% | 0.478 | 0.629 | 0.294 | 0.440 | 0.253 | 1 |
| JSON compatto | 3b zero_shot | 0.371 | 0.488 | 0% | 0.431 | 0.573 | 0.297 | 0.369 | 0.179 | 2 |

Effetto della frase "do not copy their classes" = libero − standard; riferimento = 3b, stessi esercizi, media delle 3 ripetizioni. Completezza = elementi del riferimento ritrovati (classi + attributi + relazioni + generalizzazioni) / elementi del riferimento; copia quasi esatta = completezza e precision >= 0,90.
