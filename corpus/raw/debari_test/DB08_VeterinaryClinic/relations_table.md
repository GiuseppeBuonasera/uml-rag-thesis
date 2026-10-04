# Tabella delle relazioni — DB08_VeterinaryClinic

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (8 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Animal | Breed | associazione | * | 1 | — | — | — |
| Breed | Condition | associazione | * | * | — | — | — |
| Animal | Appointment | associazione | 1 | * | — | — | — |
| Condition | Appointment | associazione | * | * | — | — | — |
| Appointment | Physician | associazione | * | 1 | — | — | — |
| Animal | Owner | associazione | 1..* | 0..1 | — | — | — |
| Owner | Person | generalizzazione | — | — | — | — | {DISJOINT, COMPLETE} |
| Physician | Person | generalizzazione | — | — | — | — | {DISJOINT, COMPLETE} |

## Totali
- Classi: 7
- Relazioni: 8
