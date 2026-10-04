# Tabella delle relazioni — DB01_ProjectManagementSystem

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (7 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Requirement | WorkProduct | generalizzazione | — | — | — | — | — |
| System | WorkProduct | generalizzazione | — | — | — | — | — |
| Project | Requirement | associazione | — | — | — | — | Input |
| Project | System | associazione | — | — | — | — | Output |
| Manager | Project | associazione | — | — | — | — | Manage |
| Team | Project | associazione | — | — | — | — | Execute |
| Manager | Team | associazione | — | — | — | — | Lead |

## Totali
- Classi: 6
- Relazioni: 7
