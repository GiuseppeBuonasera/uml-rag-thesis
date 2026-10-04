# Tabella delle relazioni — DB17_PrepaidCellPhone

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (6 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Client | Contract | associazione | — | — | — | — | — |
| Option | Contract | associazione | — | — | — | — | — |
| BasicContract | Contract | dipendenza (realizzazione) | — | — | — | — | — |
| Option | Contract | dipendenza (realizzazione) | — | — | — | — | — |
| Data | Option | generalizzazione | — | — | — | — | — |
| SMS | Option | generalizzazione | — | — | — | — | — |

## Totali
- Classi: 8
- Relazioni: 6
