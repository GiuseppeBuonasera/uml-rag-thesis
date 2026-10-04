# Tabella delle relazioni — DB07_BankSystem

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (5 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Customer | Account | associazione | 1 | 0..* | — | — | — |
| InvestmentAccount | Stock | associazione | — | 0..* | — | — | — |
| StockOrder | Stock | associazione | — | 1 | — | — | — |
| InvestmentAccount | Account | generalizzazione | — | — | — | — | — |
| SavingAccount | Account | generalizzazione | — | — | — | — | — |

## Totali
- Classi: 6
- Relazioni: 5
