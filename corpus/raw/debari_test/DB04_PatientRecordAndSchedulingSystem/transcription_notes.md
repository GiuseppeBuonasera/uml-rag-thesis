# Note di trascrizione — De Bari 4: Patient Record and Scheduling System

Fonte immagine: `corpus/raw/debari_test/_images/db04.png` (1383x979). Ingrandimenti: lato destro
x 1050-1383 (classi tagliate); 1.5x di x 700-1150 / y 260-680 (Patient-Visit, Visit-Appointment); 1.3x di
x 150-650 / y 150-560 (FamilyInsured-Patient, FamilyInsured-Doctor).

## Immagine tagliata a destra — token completati da Analysis.xlsx (regola approvata il 2026-10-02)
Il taglio tocca **solo nomi di classe e attributi** di Appointment e Prescription. Molteplicità e
ruoli non sono toccati: tutte le linee arrivano sul lato sinistro dei due riquadri, interamente visibile
(Appointment `0..*` e `0..1`, Prescription `0..*`).

| Visibile | Trascritto | Fonte del completamento |
|---|---|---|
| `Appointme` | `Appointment` | Analysis.xlsx "Part 2 - 4": `Appointment` |
| `Perscripti` | `Perscription` | **decisione utente**: prefisso visibile (con il refuso "Pers-") completato con "-on"; l'xlsx scrive `Prescription` |
| `Medicatior` (ultima lettera tagliata) | `Medication` | Analysis.xlsx: `Prescription .Medication` |
| `NumberRe` | `Number` | Analysis.xlsx: `Prescription .Number` (**decisione utente del 2026-10-03**, che sostituisce quella dello STOP A "trascritto come visibile `NumberRe`": vale la regola del completamento dall'xlsx). **L'immagine mostra però `NumberRe…`, lettura probabile `NumberRefills`** (numero di rinnovi della prescrizione), non verificabile: l'xlsx semplifica o tronca il token |

Date, Time, Reason (Appointment) e Date, Dosage (Prescription) sono interamente visibili.

## Ambiguità e interpretazioni
1. **Nomi con spazi → PascalCase**: "Name of Family Head" → `NameOfFamilyHead`, "Insurance Carrier" →
   `InsuranceCarrier`, "Policy number" → `PolicyNumber`, "Blood Pressure" → `BloodPressure`,
   "Diagnosis Notes" → `DiagnosisNotes`, "Treatment Notes" → `TreatmentNotes`.
2. **Refusi visibili, trascritti come disegnati** e corretti con le correzioni **attive** (approvate il
   2026-10-03) in `corpus/corrections/DB04_PatientRecordAndSchedulingSystem.yaml`: classe `Perscription` →
   `Prescription`, attributo `Temeperature` → `Temperature` (Visit), molteplicità `0..!` → `0..1` sull'estremo
   Visit di Visit–Appointment ("!" al posto di "1").
3. **Linee con interruzioni** vicino ai bordi dei riquadri (Patient–Visit, Visit–Appointment): sono
   artefatti di compressione, non linee tratteggiate. Nel resto del percorso sono continue, quindi
   trascritte come associazioni.
4. FamilyInsured–Patient: il `1` è sovrapposto alla parola "Head" (circa x 420, y 195), ed è letto
   sull'estremo FamilyInsured. FamilyInsured–Doctor: `1..*` lato FamilyInsured, `1` lato Doctor,
   etichetta "hasPrimaryCare" (verbo → associazione, proposta).
5. Attributi senza tipo. Nessun nome di ruolo sugli estremi.

## Analysis.xlsx ("Part 2 - 4")
Con le correzioni attive e `Number` dall'xlsx, nessuna discrepanza residua è attesa; vedi
`corpus/check_debari_report.md`. I conteggi coincidono (6 / 31 / 7).
