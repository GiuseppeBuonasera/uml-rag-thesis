# Note di trascrizione — De Bari 7: Bank System

Fonte immagine: `corpus/raw/debari_test/_images/db07.png` (1383x969). Ingrandimento 1.0x di
x 60-1050 / y 280-900.

## Elementi esclusi (non di modello)
- Titolo della slide "Bank solution", linee arancioni.
- **Residui grafici**: piccoli archi sotto InvestmentAccount (circa x 245 e x 370, y 655) e sopra Stock
  (circa x 240, y 750). Non sono linee che collegano classi (probabili tagli di linee rimosse), quindi non
  sono trascritti.

## Ambiguità e interpretazioni
1. **Icone degli attributi** (lucchetto + rombo blu, stile Rational Rose) = attributi privati → `-`.
2. **Customer–Account**: punta di freccia su entrambi gli estremi → `<-->`; Customer `1`, Account `0..*`.
3. **InvestmentAccount → Stock**: freccia verso Stock, `0..*` lato Stock, nessuna molteplicità lato
   InvestmentAccount.
4. **StockOrder → Stock**: freccia verso Stock, `1` lato Stock.
5. Tipi `String`, `Double`, `Integer` normalizzati dalla tabella dei tipi. Nessuna etichetta, nessun ruolo.

## Analysis.xlsx ("Part 2 - 7")
Classi, membri e relazioni coincidono. I conteggi di "Estimated Difficulty" (5 attributi+operazioni, 7
associazioni) non corrispondono alla Given Solution né all'immagine (7 e 5).
