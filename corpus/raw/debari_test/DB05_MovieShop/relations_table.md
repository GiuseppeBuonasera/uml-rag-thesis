# Tabella delle relazioni — DB05_MovieShop

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (11 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| User | MovieShop | associazione | * | 1 | — | — | uses |
| MovieShop | Card | associazione | 1 | * | — | — | make |
| MovieShop | Order | associazione | 1 | * | — | — | make |
| Subscriber | Card | associazione | 1 | 1 | — | — | has |
| MovieShop | Movie | aggregazione | 1 | * | — | — | — |
| Order | MovieBuy | associazione | * | 1..* | — | — | related to |
| Subscriber | MovieRent | associazione | * | 1..* | — | — | hire |
| User | MovieBuy | associazione | — | 1..* | — | — | — |
| Subscriber | User | generalizzazione | — | — | — | — | — |
| MovieRent | Movie | generalizzazione | — | — | — | — | — |
| MovieBuy | Movie | generalizzazione | — | — | — | — | — |

## Totali
- Classi: 8
- Relazioni: 11
