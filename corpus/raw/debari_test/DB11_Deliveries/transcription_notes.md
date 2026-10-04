# Note di trascrizione — De Bari 11: Deliveries

Fonte immagine: `corpus/raw/debari_test/_images/db11.png` (1383x1031). Ingrandimento 0.9x di
x 60-1300 / y 280-990.

## Ambiguità e interpretazioni
1. **Maiuscolo misto, tutto invariato** (decisione utente del 2026-10-03): intestazioni `Person`, `Package`,
   `DeliveryCenter` contro `CUSTOMER`, `COURIER`; attributi `VAT`, `NAME`, `PHONE`, `ADDRESS` contro `Id`, `Weight`,
   `Urgency`, `Address`. Nessuna categoria è interamente in maiuscolo, quindi la regola del maiuscolo
   tipografico non si applica (vale solo alla lettera).
2. **Classe associativa senza nome** (attributi DateTimeArrival / DateTimeDeparture, linea tratteggiata sulla
   seconda linea Package–DeliveryCenter) → `PackageDeliveryCenter` (convenzione di concatenazione).
3. **Due linee CUSTOMER–Package** in verticale, con le etichette "Sender" e "Recipient" scritte lungo le linee:
   CUSTOMER `1`, Package `*` su entrambe. Ruoli `Sender` / `Recipient` sull'estremo CUSTOMER (approvati).
4. **Package–DeliveryCenter**: due linee. Quella superiore ha l'etichetta "Dropoff point" (Package `*`,
   DeliveryCenter `1`, ruolo `Dropoff point` sull'estremo DeliveryCenter, approvato); quella inferiore ha la classe
   associativa (Package `*`, DeliveryCenter `*`).
5. CUSTOMER `*` – DeliveryCenter `1` (linea con gomito dal lato destro di CUSTOMER); COURIER `*` –
   DeliveryCenter `1`; COURIER `1` – Package `*` (linea lunga che gira intorno al diagramma, `*` sotto
   Package).
6. Generalizzazione CUSTOMER, COURIER → Person con `{DISJOINT, COMPLETE}`, trascritto su entrambe.
7. Attributi senza tipo.

## Analysis.xlsx ("Part 2 - 11")
La Given Solution non elenca la classe associativa e i suoi attributi; i conteggi dell'xlsx invece li
includono (6 classi, 11 attributi). Il ground truth conta anche il collegamento della classe associativa
come relazione (10 contro 9).
