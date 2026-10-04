# Tabella delle relazioni — DB19_MyDoctor

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (9 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Doctor | User | generalizzazione | — | — | — | — | — |
| Patient | User | generalizzazione | — | — | — | — | — |
| Schedule | Office | aggregazione | — | — | — | — | — |
| Schedule | Doctor | aggregazione | — | — | — | — | — |
| Appointment | Patient | aggregazione | — | — | — | — | — |
| Schedule | Appointment | composizione | — | — | — | — | — |
| BloodTest | Appointment | generalizzazione | — | — | — | — | — |
| Consultation | Appointment | generalizzazione | — | — | — | — | — |
| Surgery | Appointment | generalizzazione | — | — | — | — | — |

## Totali
- Classi: 9
- Relazioni: 9
