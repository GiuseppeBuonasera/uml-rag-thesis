# Tabella delle relazioni — DB10_Restaurant

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (7 relazioni binarie, 2 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| INGREDIENT | DISH | associazione | 1..* | * | — | — | — |
| INGREDIENTDISH | INGREDIENT, DISH | classe associativa | — | — | — | — | approssimata con 2 associazioni semplici (vedi apollon_conversion_warnings) |
| DISH | Meal | associazione | * | * | — | — | — |
| DISHMeal | DISH, Meal | classe associativa | — | — | — | — | approssimata con 2 associazioni semplici (vedi apollon_conversion_warnings) |
| Meal | TABLE | associazione | * | 1 | — | — | — |
| Meal | Client | associazione | * | 0..1 | — | — | — |
| Meal | Waiter | associazione | * | 1 | — | — | — |
| Client | Person | generalizzazione | — | — | — | — | {OVERLAPPING, COMPLETE} |
| Waiter | Person | generalizzazione | — | — | — | — | {OVERLAPPING, COMPLETE} |

## Totali
- Classi: 9
- Relazioni: 9
