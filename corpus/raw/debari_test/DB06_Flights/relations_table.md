# Tabella delle relazioni — DB06_Flights

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (13 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Airline | Flight | associazione | 1 | * | — | — | offers |
| Airline | Aircraft | associazione | * | * | — | — | owns |
| Flight | Airport | associazione | * | 1 | — | — | arrives to |
| Flight | Airport | associazione | * | 1 | — | — | departs from |
| Aircraft | Flight | associazione | 1 | * | — | — | uses |
| Flight | Pilot | associazione | — | 2..n | — | — | Driven by |
| Aircraft | AircraftType | associazione | * | 1 | — | — | is of |
| AircraftType | Pilot | associazione | * | * | — | — | Navigator of |
| AircraftType | Pilot | associazione | * | 1..n | — | — | Copilot of |
| AircraftType | Pilot3 | associazione | * | 1 | — | — | Captain of |
| Pilot1 | Pilot | generalizzazione | — | — | — | — | — |
| Pilot2 | Pilot | generalizzazione | — | — | — | — | — |
| Pilot3 | Pilot | generalizzazione | — | — | — | — | — |

## Totali
- Classi: 9
- Relazioni: 13
