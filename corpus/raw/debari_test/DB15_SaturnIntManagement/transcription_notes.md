# Note di trascrizione — De Bari 15: Saturn Int. Management

Fonte immagine: `corpus/raw/debari_test/_images/db15.png` (1383x607). Ingrandimento 0.9x di
x 80-1340 / y 20-560.

## Ambiguità e interpretazioni
1. **Immagine tagliata in alto**: il riquadro "car park" ha il bordo superiore tagliato, ma il nome è
   leggibile. Il riquadro non ha attributi né operazioni visibili (sotto il nome c'è un comparto vuoto). Non ci
   sono altri tagli: nessun token completato dall'xlsx.
2. **Intestazioni tutte in minuscolo** ("car park", "card reader", "guest card", "staff card", "barrier",
   "signal", "card", "access"). I nomi di classe composti seguono la convenzione per le classi (PascalCase):
   `CarPark`, `CardReader`, `GuestCard`, `StaffCard` in `plantuml.txt`. Per la regola **"minuscolo tipografico"**
   (approvata il 2026-10-03, simmetrica al maiuscolo) anche le classi a una parola vanno in PascalCase
   (`Barrier`, `Signal`, `Card`, `Access`), tramite `corpus/corrections/DB15_SaturnIntManagement.yaml`
   (`plantuml.txt` fedele: `barrier`, `signal`, `card`, `access`). Operazioni invariate:
   "insert staff card()" → `insertStaffCard()`, "show success message()" → `showSuccessMessage()`, "show fail
   message()" → `showFailMessage()`, "eject card()" → `ejectCard()`, "set last access()" → `setLastAccess()`.
3. **Aggregazioni** (rombo vuoto sul contenitore): CarPark ◇ Barrier (`2..*` lato barrier), CarPark ◇
   CardReader (`2..*` lato card reader), CardReader ◇ GuestCard (`*` tra il rombo e guest card, più vicino a
   guest card, attribuito a quell'estremo), CardReader ◇ Signal (senza molteplicità).
4. **Dipendenza** Barrier ..> Signal (linea tratteggiata con punta aperta) → `..>`.
5. GuestCard `*` – Card `1`; StaffCard e Access → Card (generalizzazioni).
6. Nessun attributo; nessuna etichetta né ruolo.

## Analysis.xlsx ("Part 2 - 15")
Nessuna discrepanza (8 / 6 / 8).
