# Note di trascrizione — De Bari 14: Bycicle Rental

Fonte immagine: `corpus/raw/debari_test/_images/db14.png` (1383x746).

## Vincoli testuali — ESCLUSI dal modello (decisione utente del 2026-10-03)
Due vincoli testuali (OCL informale) scritti accanto alle classi:
- `{Return_Day >= Pickup_Day}` sopra Reservation: vincolo tra due attributi della stessa classe;
- `{type should be in [road, mountain, bmx or hybrid]}` sotto BicycleModel: insieme chiuso di valori per
  l'attributo Type.

Sono trattati come i vincoli `{XOR}` di FilmSet e TransportCompany: trascritti in `plantuml.txt` come note
attaccate alla classe (`note "..." as N1` + `N1 .. Reservation`) e scartati dal convertitore, con un warning
in `apollon_conversion_warnings` che riporta il testo. Niente enum (nell'immagine l'attributo Type non ha tipo
enumerativo) e niente campo nuovo nel record.

## Ambiguità e interpretazioni
1. **Etichette oblique lungo le linee** "Actual Rented bike" (Reservation–Bicycle) e "Desired Model"
   (Reservation–BicycleModel): sintagmi nominali → ruoli sull'estremo Bicycle / BicycleModel con il testo come
   scritto (approvati).
2. **Molteplicità**: Client `1` – Reservation `*`; Reservation `*` – Store `1`; Reservation `*` – Bicycle `1`;
   Reservation `*` – BicycleModel `1`; Bicycle `*` – BicycleModel `1`.
3. Attributi come scritti (`Nin`, `Tin`, `Pickup_Day`, `No_Gears`), senza tipo. Nin e Tin sono acronimi scritti
   con l'iniziale maiuscola: non si normalizza, perché il diagramma è a grafia mista e non interamente maiuscolo.
4. Id dell'esercizio `DB14_BicycleRental` (titolo originale "Bycicle Rental").

## Analysis.xlsx ("Part 2 - 14")
Unica discrepanza: il refuso "BycicleModel" nella relazione Bicycle–BicycleModel dell'xlsx.
