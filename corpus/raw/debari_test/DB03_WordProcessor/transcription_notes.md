# Note di trascrizione — De Bari 3: Word Processor

Fonte immagine: `corpus/raw/debari_test/_images/db03.png` (1383x1035). Ingrandimenti: 1.2x di
x 150-1270 / y 520-640 (rami dell'aggregazione da Page); 1.6x di x 540-1270 / y 760-940 (Cell).

## Elementi esclusi (non di modello)
- Titolo della slide "CD Case Study (3/3)".

## Ambiguità e interpretazioni
1. **Visibilità**: attributi `-`, operazioni `+`, trascritte come disegnate (in Apollon la visibilità
   non è conservata, `apollon_limitations.md` §9). Attributi senza tipo.
2. **Aggregazione ad albero da Page** (rombo vuoto su Page, `1` vicino al rombo): un ramo per Trimming
   (`0..1`), Character (`0..*`), Table (`0..*`), Picture (`0..*`), trascritti come 4 aggregazioni.
3. **`*` isolato, non trascritto** (decisione utente del 2026-10-03): tra il ramo di Trimming e quello di
   Character, sotto la linea orizzontale (circa x 350, y 592 nell'immagine), c'è un `*` non vicino
   all'estremo di nessuna linea. **Tutti e 4 i rami dell'aggregazione di Page hanno già la propria
   molteplicità** (Trimming `0..1`, Character `0..*`, Table `0..*`, Picture `0..*`): è un residuo senza
   estremo.
4. **Table–Cell**: sopra Cell, vicino al rombo pieno di Table, `1` e `1..*` sono sovrapposti (circa
   x 815, y 805). Letto come `1` lato Table (contenitore) e `1..*` lato Cell, coerente con la composizione.
5. **Cell**: rombi vuoti su Cell verso Character (Cell `1`, Character `0..*`) e verso Picture (Cell `1`,
   Picture `0..*`).
6. Nessun nome di ruolo e nessuna etichetta su nessuna relazione (estremi controllati).

## Analysis.xlsx ("Part 2 - 3")
- La Given Solution elenca le operazioni solo per Document: le altre 19 operazioni, leggibili
  nell'immagine, mancano (imprecisione dell'xlsx).
- "Attributes + Operations" = 12, scambiato con l'es. 2: il diagramma ha 12 attributi + 23 operazioni = 35.
