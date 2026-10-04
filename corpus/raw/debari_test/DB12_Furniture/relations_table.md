# Tabella delle relazioni — DB12_Furniture

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (5 relazioni binarie, 2 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Piece | Line | associazione | * | 1 | — | — | — |
| Piece | Component | associazione | * | 1..* | — | — | — |
| PieceComponent | Piece, Component | classe associativa | — | — | — | — | approssimata con 2 associazioni semplici (vedi apollon_conversion_warnings) |
| Piece | Order | associazione | * | * | — | — | — |
| PieceOrder | Piece, Order | classe associativa | — | — | — | — | approssimata con 2 associazioni semplici (vedi apollon_conversion_warnings) |
| Component | ComponentType | associazione | * | 1 | — | — | — |
| Order | Store | associazione | * | 1 | — | — | — |

## Totali
- Classi: 8
- Relazioni: 7
