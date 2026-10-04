# Tabella delle relazioni — DB11_Deliveries

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (9 relazioni binarie, 1 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| CUSTOMER | Person | generalizzazione | — | — | — | — | {DISJOINT, COMPLETE} |
| COURIER | Person | generalizzazione | — | — | — | — | {DISJOINT, COMPLETE} |
| CUSTOMER | Package | associazione | 1 | * | — | — | Sender |
| CUSTOMER | Package | associazione | 1 | * | — | — | Recipient |
| CUSTOMER | DeliveryCenter | associazione | * | 1 | — | — | — |
| COURIER | DeliveryCenter | associazione | * | 1 | — | — | — |
| Package | DeliveryCenter | associazione | * | 1 | — | — | Dropoff point |
| Package | DeliveryCenter | associazione | * | * | — | — | — |
| PackageDeliveryCenter | Package, DeliveryCenter | classe associativa | — | — | — | — | approssimata con 2 associazioni semplici (vedi apollon_conversion_warnings) |
| COURIER | Package | associazione | 1 | * | — | — | — |

## Totali
- Classi: 6
- Relazioni: 10
