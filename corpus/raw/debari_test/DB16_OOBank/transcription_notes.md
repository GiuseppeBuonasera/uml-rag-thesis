# Note di trascrizione — De Bari 16: OOBank

Fonte immagine: `corpus/raw/debari_test/_images/db16.png` (1383x839). Ingrandimenti 1.8x di
x 360-1000 / y 100-450 e x 360-1010 / y 380-670; 3x di x 370-800 / y 160-280 (auto-associazione).

## Elementi esclusi (non di modello)
- Testo del libro (soluzionario Lethbridge-Laganière) incluso nell'immagine, escluso come nota (decisione utente
  dello STOP A): intestazione "E5.20 p. 189 Adding generalizations or interfaces to a class diagram.
  a)*Bank account management system: See 5.21e for a related problem." e, sotto il diagramma, "The distinction
  between AccountType and Account is important (...) The following are some variations:".

## Ambiguità e interpretazioni
1. **Auto-associazione di OrganizationalUnit**: SENZA rombo (verificato con ingrandimento 3x), estremo `*` con il
   ruolo "subdivision" (sopra) ed estremo `0..1` → `OrganizationalUnit "0..1" -- "* subdivision" OrganizationalUnit`.
   Analysis.xlsx ne fa una classe "Subdivision" in composizione: imprecisione dell'xlsx (decisione utente dello
   STOP A), con conteggi xlsx non allineati al ground truth.
2. **OrganizationalUnit–Employee**: due linee. "worksFor" (linea in alto, `*` lato Employee, nessuna molteplicità
   lato OrganizationalUnit, verbo → associazione) e "manager" (`0..1` lato OrganizationalUnit, `0..1 manager` lato
   Employee: nome di ruolo vicino all'estremo Employee, sintassi `"molt ruolo"`).
3. **Employee–Customer "personalBanker"**: linea dal basso di Employee al basso di Customer, `*` lato Customer,
   nessuna molteplicità lato Employee; sostantivo proposto come ruolo sull'estremo Employee.
4. **Customer–Account "accountHolder"**: Customer `1..2`, Account `*`; sostantivo proposto come ruolo sull'estremo
   Customer.
5. AccountType–Account e Branch–Account: `*` lato Account, nessuna molteplicità sull'altro estremo. CreditCard
   `1..*` – CreditCardAccount (nessuna molteplicità lato CreditCardAccount).
6. Generalizzazioni: Employee, Customer → Person; Branch → OrganizationalUnit; ChequingAccount, MortgageAccount,
   CreditCardAccount → Account.
7. Attributi senza tipo. OrganizationalUnit, Employee, Customer e ChequingAccount senza attributi.

## Analysis.xlsx ("Part 2 - 16")
Discrepanze: la classe "Subdivision" (punto 1) e il conteggio delle associazioni (13 nell'xlsx contro le 14
relazioni della sua stessa Given Solution e dell'immagine).
