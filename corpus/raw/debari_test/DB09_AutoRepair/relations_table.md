# Tabella delle relazioni — DB09_AutoRepair

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (10 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| EMPLOYEE | PERSON | generalizzazione | — | — | — | — | {Disjoint, Complete} |
| OWNER | PERSON | generalizzazione | — | — | — | — | {Disjoint, Complete} |
| EMPLOYEE | SERVICE | associazione | 1 | * | — | — | — |
| OWNER | CAR | associazione | 1 | * | — | — | — |
| SERVICE | CAR | associazione | * | 1 | — | — | — |
| SERVICE | PARTACC | associazione | 1 | 1...* | — | — | — |
| CAR | CARMODEL | associazione | * | 1 | — | — | — |
| CARMODEL | MAKE | associazione | * | 1 | — | — | — |
| PARTACC | PARTTYPE | associazione | * | 1 | — | — | — |
| CARMODEL | PARTTYPE | associazione | * | * | — | — | — |

## Totali
- Classi: 9
- Relazioni: 10
