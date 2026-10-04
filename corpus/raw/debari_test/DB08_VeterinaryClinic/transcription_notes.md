# Note di trascrizione — De Bari 8: Veterinary Clinic

Fonte immagine: `corpus/raw/debari_test/_images/db08.png` (1383x919). Ingrandimento 0.9x di
x 40-1260 / y 60-480 (Animal, Breed, Condition, Appointment).

## Ambiguità e interpretazioni
1. **Nomi** come scritti, anche in MAIUSCOLO (`NAME`, `COMMON_NAME`, `SCI_NAME`, `DATE`, `TIME`, `PHONE`);
   underscore invariati.
2. **Molteplicità**: Animal `*` – Breed `1`; Breed `*` – Condition `*`; Animal `1` – Appointment `*`;
   Condition `*` – Appointment `*` (linea dal basso di Condition all'alto di Appointment); Appointment `*` –
   Physician `1`; Animal `1..*` – Owner `0..1` (linea lunga dal lato sinistro di Animal).
3. **Generalizzazione** Owner, Physician → Person con vincolo `{DISJOINT, COMPLETE}`, scritto sotto il tronco
   comune → trascritto su entrambe (convenzione OilWells).
4. Owner e Physician senza attributi (riquadri vuoti). Attributi senza tipo. Nessuna etichetta né ruolo.

## Analysis.xlsx ("Part 2 - 8")
Nessuna discrepanza (7 / 11 / 8).
