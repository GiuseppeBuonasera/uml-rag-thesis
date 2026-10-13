# Qualità degli esempi che il 3b mostrerà (examples_quality_2026-10-12_8d5001f)

Voce 137 di `docs/decisions.md`. SOLO DESCRITTIVO: esempi del file congelato `data/retrieval_frozen/retrievals_3b.jsonl`; si guarda solo il GT degli ESEMPI, mai quello della query. Random: le 3 ripetizioni insieme.

Riferimento, tutti gli 80 esercizi: attributi senza tipo 18.9 %, molteplicità vuote 9.2 %; tracce con istruzioni per lo studente: 7 esercizi (+ Menso, dubbia).

| query | retriever | k | esempi | con istruzioni per lo studente: esempi / query | attributi senza tipo | esempi con oltre metà attributi senza tipo: esempi / query | molteplicità vuote | esempi senza attributi: esempi / query | De Bari: esempi / query |
|---|---|---|---|---|---|---|---|---|---|
| valutazione | bm25 | 2 | 108 | 8.3 % / 14.8 % | 18.2 % | 15.7 % / 27.8 % | 8.4 % | 2.8 % / 5.6 % | 24.1 % / 40.7 % |
| valutazione | bm25 | 3 | 162 | 10.5 % / 27.8 % | 17.7 % | 14.2 % / 33.3 % | 7.3 % | 2.5 % / 7.4 % | 21.6 % / 48.1 % |
| valutazione | dense | 3 | 162 | 7.4 % / 18.5 % | 31.5 % | 30.2 % / 63.0 % | 7.2 % | 4.9 % / 14.8 % | 38.3 % / 74.1 % |
| valutazione | hybrid | 3 | 162 | 9.3 % / 22.2 % | 20.2 % | 16.0 % / 38.9 % | 7.1 % | 4.3 % / 13.0 % | 23.5 % / 50.0 % |
| valutazione | random | 3 | 486 | 7.6 % / 46.3 % | 16.2 % | 14.0 % / 77.8 % | 7.6 % | 2.9 % / 22.2 % | 22.2 % / 96.3 % |
| sviluppo | bm25 | 2 | 52 | 11.5 % / 19.2 % | 16.2 % | 13.5 % / 26.9 % | 4.8 % | 1.9 % / 3.8 % | 21.2 % / 42.3 % |
| sviluppo | bm25 | 3 | 78 | 11.5 % / 30.8 % | 13.7 % | 11.5 % / 34.6 % | 5.2 % | 2.6 % / 7.7 % | 19.2 % / 50.0 % |
| sviluppo | dense | 3 | 78 | 12.8 % / 30.8 % | 26.6 % | 25.6 % / 61.5 % | 6.3 % | 0.0 % / 0.0 % | 32.1 % / 69.2 % |
| sviluppo | hybrid | 3 | 78 | 12.8 % / 30.8 % | 22.3 % | 20.5 % / 46.2 % | 5.0 % | 0.0 % / 0.0 % | 25.6 % / 57.7 % |
| sviluppo | random | 3 | 234 | 10.3 % / 50.0 % | 15.0 % | 12.8 % / 69.2 % | 8.5 % | 4.7 % / 30.8 % | 20.5 % / 92.3 % |
