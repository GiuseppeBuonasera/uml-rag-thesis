# Tabella delle relazioni — DB13_Factory

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (8 relazioni binarie, 1 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| CLIENT | Person | generalizzazione | — | — | — | — | {DISJOINT, COMPLETE} |
| WORKER | Person | generalizzazione | — | — | — | — | {DISJOINT, COMPLETE} |
| WORKER | SKILL | associazione | * | * | — | — | — |
| WORKER | MACHINE | associazione | * | * | — | — | — |
| MACHINE | PRODUCT_TYPE | associazione | 1 | * | — | — | — |
| PRODUCT_TYPE | PRODUCT | associazione | 1 | * | — | — | — |
| CLIENT | PURCHASEORDER | associazione | 1 | * | — | — | Issuer |
| PRODUCT | PURCHASEORDER | associazione | * | * | — | — | — |
| PRODUCTPURCHASEORDER | PRODUCT, PURCHASEORDER | classe associativa | — | — | — | — | approssimata con 2 associazioni semplici (vedi apollon_conversion_warnings) |

## Totali
- Classi: 9
- Relazioni: 9
