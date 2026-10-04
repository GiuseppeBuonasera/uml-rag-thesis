# Tabella delle relazioni — DB18_LibrarySystem

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (6 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Under_aged | User | dipendenza (realizzazione) | — | — | — | — | — |
| Adult | User | dipendenza (realizzazione) | — | — | — | — | — |
| User | Borrow | aggregazione | — | — | — | — | — |
| Borrow | Book | associazione | — | — | — | — | — |
| User | Book | associazione | 1 | 1..4 | — | — | borrow |
| Library | Book | aggregazione | — | — | — | — | — |

## Totali
- Classi: 6
- Relazioni: 6
