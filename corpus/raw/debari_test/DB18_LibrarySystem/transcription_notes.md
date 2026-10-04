# Note di trascrizione — De Bari 18: Library System

Fonte immagine: `corpus/raw/debari_test/_images/db18.png` (1383x1119). Ingrandimento 1.0x di
x 80-980 / y 420-1070.

## Elementi esclusi (non di modello)
- Griglia di sfondo e icone "−" di compressione dei riquadri (draw.io).

## Ambiguità e interpretazioni
1. **`<<interface>>` User** → `interface User` (stereotype "interface" nel JSON, gestione implementata il
   2026-10-02). Under_aged e Adult → User con linee **tratteggiate** e triangolo vuoto → realizzazione (`..|>`).
2. **Tipi generici** `List<Borrow>` (User.borrow_his) e `List<Book>` (Library.Books): trascritti come scritti in
   `plantuml.txt` e portati a `Borrow[]` / `Book[]` dalla convenzione multi-valore già approvata (`tipo[]`), con le
   correzioni attive `chiarimento_modellazione` in `corpus/corrections/DB18_LibrarySystem.yaml`.
3. **Aggregazioni** (rombo vuoto sul contenitore): User ◇ Borrow (rombo su User), Library ◇ Book (rombo su
   Library); nessuna molteplicità.
4. **Borrow → Book**: linea continua con freccia → associazione navigabile (`-->`); Analysis.xlsx la chiama
   "Dependencies".
5. **User–Book "borrow"**: User `1`, Book `1..4` (il limite di 4 libri del testo), verbo → associazione.
6. Visibilità `-` come disegnata; tipi String, int, Date normalizzati.

## Analysis.xlsx ("Part 2 - 18")
Discrepanze: le realizzazioni chiamate "Generalization" e la linea continua Borrow → Book chiamata
"Dependencies" (punti 1 e 4).
