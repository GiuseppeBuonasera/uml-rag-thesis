# Tabella delle relazioni — DB02_HollywoodApproach

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (5 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Take | Setup | associazione | 1...* | 1 | — | — | tk_of_stp |
| Scene | Setup | associazione | 1 | 1...* | — | — | stp_for_scn |
| Internal | Scene | generalizzazione | — | — | — | — | {complete, disjoint} |
| External | Scene | generalizzazione | — | — | — | — | {complete, disjoint} |
| External | Location | associazione | 0...* | 1 | — | — | located |

## Totali
- Classi: 6
- Relazioni: 5
