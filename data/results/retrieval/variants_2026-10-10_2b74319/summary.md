# Varianti del retriever — leave-one-out sul pool unico (variants_2026-10-10_2b74319)

Voce 120, passo 3: SOLO retrieval, nessuna generazione, descrittivo. 80 query, per ognuna gli altri 79 candidati (voce 115). Misure senza embedding (voce 107); copertura = quota dei tipi di relazione del GT della query presenti nei primi 3 esempi. **v2 / v2s / v2d sono favorite per costruzione su J e Jt** (confrontano la traccia con i nomi di classe dei candidati).

Analisi eseguita sul commit `2b74319a3f11` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

| retriever | J@1 | J@3 | Jt@1 | Jt@3 | S@3 | copertura@3 | ∩ top-3 con bm25 | distinti al rango 1 | max nei top-3 | mai nei top-3 | secondi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bm25 | 0.099 | 0.078 | 0.116 | 0.096 | 0.666 | 0.877 | 1.00 | 54 | 9 | 10 | 19.2 |
| dense (MiniLM) | 0.079 | 0.060 | 0.093 | 0.075 | 0.640 | 0.874 | 0.40 | 48 | 16 | 8 | 0.0 |
| hybrid (RRF bm25 + MiniLM) | 0.092 | 0.070 | 0.112 | 0.088 | 0.653 | 0.886 | 0.64 | 51 | 9 | 6 | 19.1 |
| v2 struttura BM25 | 0.104 | 0.084 | 0.131 | 0.106 | 0.660 | 0.873 | 0.72 | 54 | 11 | 8 | 21.1 |
| v2s struttura + sinonimi | 0.105 | 0.081 | 0.133 | 0.104 | 0.652 | 0.873 | 0.69 | 54 | 10 | 7 | 27.5 |
| v2d struttura densa | 0.099 | 0.080 | 0.118 | 0.099 | 0.659 | 0.884 | 0.66 | 50 | 11 | 12 | 18.9 |
| v3 MMR | 0.099 | 0.076 | 0.116 | 0.094 | 0.668 | 0.886 | 0.95 | 54 | 8 | 9 | 20.5 |
| v4 costrutti | 0.084 | 0.059 | 0.101 | 0.075 | 0.645 | 0.912 | 0.70 | 46 | 14 | 11 | 18.9 |
| v5 qualità | 0.093 | 0.070 | 0.114 | 0.089 | 0.667 | 0.881 | 0.81 | 46 | 12 | 17 | 18.9 |
| v6 MiniLM a pezzi | 0.077 | 0.063 | 0.090 | 0.077 | 0.649 | 0.894 | 0.42 | 50 | 16 | 7 | 0.0 |
