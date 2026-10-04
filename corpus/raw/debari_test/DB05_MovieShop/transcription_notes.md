# Note di trascrizione — De Bari 5: Movie-Shop

Fonte immagine: `corpus/raw/debari_test/_images/db05.png` (1383x1046). Ingrandimenti 1.3x/1.0x di
x 60-820 / y 200-620 (User, Subscriber, Card), x 60-1260 / y 600-960 (Movie-Rent, Movie-Buy, linee
in basso), x 640-1260 / y 240-600 (Movie-Shop, Order, Movie).

## Elementi esclusi (non di modello)
- Titolo della slide "Movie-Shop: solution" e linee decorative arancioni.

## Ambiguità e interpretazioni
1. **Nomi con trattino → PascalCase**: "Movie-Shop" → `MovieShop`, "Movie-Rent" → `MovieRent`,
   "Movie-Buy" → `MovieBuy`; attributi "data prestito" → `dataPrestito`, "prezzo-vendita" →
   `prezzoVendita`.
2. **Attributi in italiano, tradotti** (decisione utente del 2026-10-03, meccanismo di `translated_it`):
   `plantuml_it.txt` è la trascrizione fedele dell'immagine, `glossary.json` è il glossario locale (unito a
   `translated_it/glossary_shared.json`, stesso termine = stessa traduzione) e `plantuml.txt` è generato da
   `apply_glossary.py`. Le traduzioni partono dalle letture di Analysis.xlsx: Nome → name, Cognome →
   surname, telefono → phone, indirizzo → address, Stato → status, Prezzo → price. Dove l'xlsx semplifica,
   la traduzione è fedele: "data prestito" → `loanDate` (xlsx: date) e "prezzo-vendita" → `sellingPrice`
   (xlsx: Price-Sell), con la giustificazione in check_debari. Valori enum tradotti: presente → present,
   da ordinare → to order. `check_translated.py --debari`: OK.
3. **Tre enumerazioni inline** (`+type: {DVD, VHS}`, `+Stato {in,out}` senza i due punti,
   `+Stato: {presente, da ordinare}`): trascritte come disegnate in `plantuml_it.txt` e convertite dalla
   convenzione approvata, sul testo tradotto, in enumerazioni separate `MovieType`, `MovieRentStatus`,
   `MovieBuyStatus` (correzioni attive `chiarimento_modellazione` in `corpus/corrections/DB05_MovieShop.yaml`).
4. **Navigabilità** (punta aperta): uses → MovieShop, has → Card, make → Order, hire → MovieRent,
   User → MovieBuy; trascritte con `-->`. MovieShop–Card "make" e Order–MovieBuy "related to" senza punta.
5. **`*` in grassetto a sinistra di Subscriber** (circa x 165, y 495): attribuito all'estremo Subscriber di
   Subscriber → MovieRent ("hire"), per la regola dell'estremo più vicino (decisione utente del 2026-10-03).
   L'estremo User di User → MovieBuy resta senza molteplicità. **Indizio contrario**: lo stesso grassetto del
   `1..*` vicino a Movie-Buy, che è sulla linea User → MovieBuy. Registrato nel campo `ambiguities` del
   record (`corpus/ambiguities.yaml`), così in valutazione l'elemento può essere escluso o trattato a parte.
6. Aggregazione MovieShop ◇ — Movie: MovieShop `1`, Movie `*`.
7. Etichette uses, make (x2), has, related to, hire: verbi → nomi di associazione (proposta).
   Nessun nome di ruolo sugli estremi.

## Analysis.xlsx ("Part 2 - 5")
Classi e relazioni coincidono (8 classi dell'immagine, 11 relazioni). Le discrepanze residue sono le 3
enumerazioni della convenzione (Classes: 8 nell'xlsx, 11 nel ground truth) e le due traduzioni fedeli
loanDate / sellingPrice contro date / Price-Sell dell'xlsx (punto 2).
