# Note di trascrizione — De Bari 17: Prepaid Cell Phone

Fonte immagine: `corpus/raw/debari_test/_images/db17.png` (1383x1121). Ingrandimenti 1.6x di
x 400-980 / y 160-460 e 2.5x di x 400-780 / y 640-760 (punte di freccia).

## Elementi esclusi (non di modello)
- Titolo "Solution:".

## Ambiguità e interpretazioni
1. **Frecce tutte uguali** (DUBBIO, registrato in `corpus/ambiguities.yaml`): le linee continue Client → Contract,
   Option → Contract, Data → Option, SMS → Option e le linee tratteggiate BasicContract/Option → Contract hanno la
   stessa punta piena di draw.io; la notazione non distingue la generalizzazione dall'associazione navigabile.
   Lettura confermata dall'utente il 2026-10-03: Data, SMS → Option = generalizzazione (tronco comune verso
   Option, pattern decorator chiesto dal testo, lettura di Analysis.xlsx); Client, Option → Contract =
   associazioni navigabili (`-->`); le due linee TRATTEGGIATE BasicContract → Contract e Option → Contract =
   realizzazioni (`..|>` → ClassRealization, xlsx: Implementation), trattate come le realizzazioni tratteggiate
   dell'es. 18 (Under_aged/Adult ..|> User). L'unica differenza grafica è la punta (piena qui, triangolo vuoto
   nell'es. 18); il tratteggio verso il supertipo è lo stesso.
2. **Contract in corsivo** → classe astratta (`abstract class`), notazione UML del corsivo (confermato).
3. **Phone e Double Transfer non sono collegati** a nessuna classe: trascritti come classi isolate. Il testo e
   l'xlsx li vorrebbero sottoclassi di Option come Data e SMS; il ground truth trascrive l'immagine (confermato:
   le generalizzazioni dell'xlsx sono un'imprecisione dell'xlsx, come "Subdivision" nell'es. 16).
4. Nomi composti: "Basic Contract" → `BasicContract`, "Double Transfer" → `DoubleTransfer`. Visibilità come
   disegnata; tipi `double`, `int`.
5. Nessuna molteplicità, nessuna etichetta né ruolo.

## Analysis.xlsx ("Part 2 - 17")
Discrepanze: le due generalizzazioni Phone/Double Transfer → Option presenti solo nell'xlsx (punto 3), e quindi
il conteggio delle relazioni (8 contro 6).
