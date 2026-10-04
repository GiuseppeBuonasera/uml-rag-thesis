# Tabella delle relazioni — DB16_OOBank

Generata da `corpus/generate_relations_table.py --english` a partire da `plantuml.txt` (14 relazioni binarie, 0 classi associative).

| Classe A | Classe B | Tipo | Molt. A | Molt. B | Ruolo estremo A | Ruolo estremo B | Etichetta |
|---|---|---|---|---|---|---|---|
| Employee | Person | generalizzazione | — | — | — | — | — |
| Customer | Person | generalizzazione | — | — | — | — | — |
| OrganizationalUnit | OrganizationalUnit | associazione | 0..1 | * | — | subdivision | — |
| OrganizationalUnit | Employee | associazione | — | * | — | — | worksFor |
| OrganizationalUnit | Employee | associazione | 0..1 | 0..1 | — | manager | — |
| Employee | Customer | associazione | — | * | — | — | personalBanker |
| Branch | OrganizationalUnit | generalizzazione | — | — | — | — | — |
| Customer | Account | associazione | 1..2 | * | — | — | accountHolder |
| AccountType | Account | associazione | — | * | — | — | — |
| Branch | Account | associazione | — | * | — | — | — |
| ChequingAccount | Account | generalizzazione | — | — | — | — | — |
| MortgageAccount | Account | generalizzazione | — | — | — | — | — |
| CreditCardAccount | Account | generalizzazione | — | — | — | — | — |
| CreditCard | CreditCardAccount | associazione | 1..* | — | — | — | — |

## Totali
- Classi: 11
- Relazioni: 14
