# Tabella delle relazioni — DB14_BicycleRental

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (5 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Client | Reservation | associazione | 1 | * | — | — | — |
| Reservation | Store | associazione | * | 1 | — | — | — |
| Reservation | Bicycle | associazione | * | 1 | — | — | Actual Rented bike |
| Reservation | BicycleModel | associazione | * | 1 | — | — | Desired Model |
| Bicycle | BicycleModel | associazione | * | 1 | — | — | — |

## Warning del parser
- scartato vincolo/nota 'N1' ('{Return_Day >= Pickup_Day}') su Reservation: nessun costrutto Apollon equivalente documentato
- scartato vincolo/nota 'N2' ('{type should be in [road, mountain, bmx or hybrid]}') su BicycleModel: nessun costrutto Apollon equivalente documentato

## Totali
- Classi: 5
- Relazioni: 5
