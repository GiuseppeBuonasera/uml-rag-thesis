# Tabella delle relazioni — DB20_OnlineShopping

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (10 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| WebUser | Customer | associazione | 0..1 | 1 | — | — | — |
| WebUser | ShoppingCart | associazione | 1 | 0..1 | — | — | — |
| Customer | Account | composizione | 1 | 1 | — | — | — |
| Account | ShoppingCart | composizione | 1 | 1 | — | — | — |
| Account | Order | composizione | 1 | * | — | {ordered, unique} | — |
| Account | Payment | associazione | 1 | 0..* | — | — | — |
| Payment | Order | associazione | * | 1 | {ordered, unique} | — | — |
| ShoppingCart | LineItem | associazione | 1 | * | — | {ordered, unique} line_item | — |
| Order | LineItem | associazione | 1 | * | — | {ordered, unique} line_item | — |
| LineItem | Product | associazione | * | 1 | — | — | — |

## Totali
- Classi: 10
- Relazioni: 10
