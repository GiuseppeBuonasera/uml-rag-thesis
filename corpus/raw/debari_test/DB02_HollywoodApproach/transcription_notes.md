# Note di trascrizione — De Bari 2: Hollywood Approach

Fonte immagine: `corpus/raw/debari_test/_images/db02.png` (1383x952). Ingrandimenti: 2.5x di
x 900-1200 / y 360-530 (Take-Setup, molteplicità e "tk_of_stp"); 1.4x di x 200-1000 / y 500-810
(Scene, Internal, External, vincolo, "located").

## Elementi esclusi (non di modello)
- Titolo della slide "Solution 1: ... use conceptual modeling diagrams (UML)!!!", barra di navigazione
  della slide (in basso a destra).
- Filigrana "Visual Paradigm for UML Community Edition [not for commercial use]" (in alto a sinistra).

## Ambiguità e interpretazioni
1. **Molteplicità con tre punti**: l'immagine scrive `1...*` (Take, Setup verso Scene) e `0...*`
   (External), notazione non UML, trascritte come disegnate in `plantuml.txt`. Sono normalizzate a `..`
   da `normalize_multiplicity`, con un warning nel record (regola generale approvata il 2026-10-03, come
   'n' → '*'; nessuna correzione per esercizio).
2. **Tipi `Real` e `Text`**: `Real` → `double`, `Text` → `string` (regola generale in `TYPE_NORMALIZATION`,
   approvata il 2026-10-03, accanto a Number → int dei tradotti).
3. **Vincolo `{complete, disjoint}`** sul gruppo di generalizzazione Internal/External → Scene:
   trascritto su entrambe le generalizzazioni (stessa sintassi di OilWells), poi estratto nel campo
   `constraints` dal convertitore.
4. **Etichette** "tk_of_stp", "stp_for_scn", "located" al centro della linea, non vicino a un estremo:
   proposte come nomi di associazione. Nessun nome di ruolo sugli estremi (controllati: solo
   molteplicità).

## Analysis.xlsx ("Part 2 - 2")
- Refusi nell'xlsx: "Extenal" (Generalization) e "Externals" (Association): imprecisione dell'xlsx.
- "Attributes + Operations" = 35 (`=12+23`) ma il diagramma ha 12 attributi e 0 operazioni: il valore è
  scambiato con quello dell'es. 3 (imprecisione dell'xlsx, vedi `corpus/check_debari_report.md`).
