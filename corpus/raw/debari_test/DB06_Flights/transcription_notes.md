# Note di trascrizione — De Bari 6: Flights

Fonte immagine: `corpus/raw/debari_test/_images/db06.png` (1383x1025). Ingrandimenti 1.3x di
x 150-1000 / y 240-560 (Airline, Flight, Aircraft) e 1.2x di x 200-1100 / y 540-950 (Aircraft Type,
Pilot, Pilot1-3).

## Elementi esclusi (non di modello)
- Titolo della slide "Flights – solution", logo "SoftEng http://softeng.polito.it", linee arancioni.

## Ambiguità e interpretazioni
1. **Nomi**: "Aircraft Type" → `AircraftType` (regola dei nomi composti); "Pilot1/2/3" invariati. Visibilità
   come disegnata ("- ID" con spazio → `-ID`).
2. **Airline–Aircraft "owns"**: `*` vicino ad Airline (sotto il riquadro, all'inizio della linea) e `*` vicino
   ad Aircraft: molti-a-molti come disegnato (confermato dall'utente il 2026-10-03). Il testo ("an airline
   owns a set of aircrafts") vincola solo il lato Aircraft (un'airline ha più aerei) e non dice quante airline
   possano possedere un aereo, quindi non c'è contraddizione con `*` lato Airline.
3. **Flight–Airport**: due associazioni distinte, "arrives to" (sopra) e "departs from" (sotto), entrambe
   Flight `*` – Airport `1`.
4. **Flight–Pilot "Driven by"**: `2..n` lato Pilot; nessuna molteplicità lato Flight (controllato). `n` è
   normalizzato a `*`.
5. **Aircraft Type–Pilot**: due linee che partono quasi dallo stesso punto del bordo destro di Aircraft Type.
   La linea superiore ("Navigator of", sopra) ha `*` / `*`; quella inferiore ("Copilot of", sotto) ha `*`
   lato Aircraft Type e `1..n` lato Pilot. Attribuzione per posizione: sopra / sotto le due linee.
6. **Aircraft Type–Pilot3 "Captain of"**: `*` lato Aircraft Type, `1` lato Pilot3.
7. **Etichette "Navigator of", "Copilot of", "Captain of"** → RUOLI `Navigator` / `Copilot` / `Captain`
   sull'estremo Pilot / Pilot3 (decisione utente del 2026-10-03: sostantivo + preposizione, nessun triangolo,
   precedente Louvre hasCoach → coach; maiuscola come scritta). Le due associazioni AircraftType–Pilot restano
   due edge distinti nel JSON (verificato: ruoli Navigator e Copilot, molteplicità `*` e `1..*` lato Pilot).
   Le altre etichette sono verbi → associazioni.
8. Attributi senza tipo.

## Analysis.xlsx ("Part 2 - 6")
Classi, membri e relazioni coincidono. Unica discrepanza: la colonna Associations di "Estimated
Difficulty" dice 12, mentre la Given Solution e l'immagine hanno 13 relazioni.
