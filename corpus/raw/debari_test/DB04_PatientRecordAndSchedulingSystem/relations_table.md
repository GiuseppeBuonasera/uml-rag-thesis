# Tabella delle relazioni — DB04_PatientRecordAndSchedulingSystem

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (7 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| FamilyInsured | Patient | associazione | 1 | 1..* | — | — | — |
| FamilyInsured | Doctor | associazione | 1..* | 1 | — | — | hasPrimaryCare |
| Patient | Appointment | associazione | 1 | 0..* | — | — | — |
| Patient | Visit | associazione | 1 | 0..* | — | — | — |
| Visit | Appointment | associazione | 0..! | 0..1 | — | — | — |
| Doctor | Visit | associazione | 1 | 1..* | — | — | — |
| Visit | Perscription | associazione | 1 | 0..* | — | — | — |

## Totali
- Classi: 6
- Relazioni: 7
