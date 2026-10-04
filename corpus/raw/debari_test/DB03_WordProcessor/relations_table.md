# Tabella delle relazioni — DB03_WordProcessor

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (8 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Document | Page | composizione | 1 | 1..* | — | — | — |
| Page | Trimming | aggregazione | 1 | 0..1 | — | — | — |
| Page | Character | aggregazione | 1 | 0..* | — | — | — |
| Page | Table | aggregazione | 1 | 0..* | — | — | — |
| Page | Picture | aggregazione | 1 | 0..* | — | — | — |
| Table | Cell | composizione | 1 | 1..* | — | — | — |
| Cell | Character | aggregazione | 1 | 0..* | — | — | — |
| Cell | Picture | aggregazione | 1 | 0..* | — | — | — |

## Totali
- Classi: 7
- Relazioni: 8
