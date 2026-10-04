# Tabella delle relazioni — DB15_SaturnIntManagement

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (8 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| CarPark | barrier | aggregazione | — | 2..* | — | — | — |
| CarPark | CardReader | aggregazione | — | 2..* | — | — | — |
| CardReader | GuestCard | aggregazione | — | * | — | — | — |
| CardReader | signal | aggregazione | — | — | — | — | — |
| barrier | signal | dipendenza | — | — | — | — | — |
| GuestCard | card | associazione | * | 1 | — | — | — |
| StaffCard | card | generalizzazione | — | — | — | — | — |
| access | card | generalizzazione | — | — | — | — | — |

## Totali
- Classi: 8
- Relazioni: 8
