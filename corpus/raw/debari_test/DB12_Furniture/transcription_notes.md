# Note di trascrizione — De Bari 12: Furniture

Fonte immagine: `corpus/raw/debari_test/_images/db12.png` (1383x896).

## Ambiguità e interpretazioni
1. **Due classi associative senza nome**, entrambe con l'attributo `Quantity`: su Piece–Component →
   `PieceComponent`, su Piece–Order → `PieceOrder` (convenzione di concatenazione, nell'ordine delle
   relazioni).
2. **Molteplicità**: Piece `*` – Line `1`; Piece `*` – Component `1..*`; Piece `*` – Order `*` (linea con
   gomito dal lato destro di Piece); Component `*` – ComponentType `1`; Order `*` – Store `1`.
3. Il testo dice che Line ha un nome ("each with a different name"), ma nel diagramma Line ha solo l'attributo
   `Type`: incompletezza del diagramma, non corretta (si trascrive l'immagine).
4. `FAX` (Store) è in maiuscolo in un diagramma a grafia mista: invariato.
5. Attributi senza tipo. Nessuna etichetta né ruolo.

## Analysis.xlsx ("Part 2 - 12")
La Given Solution e i conteggi non includono le due classi associative né i loro attributi.
