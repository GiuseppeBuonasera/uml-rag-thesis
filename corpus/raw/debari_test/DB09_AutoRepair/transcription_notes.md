# Note di trascrizione — De Bari 9: Auto Repair (diagramma scritto a mano)

Fonte immagine: `corpus/raw/debari_test/_images/db09.png` (1118x1562). Ingrandimenti 1.5-1.6x di
x 230-640 / y 220-600 (Person, Employee, Owner, vincolo), x 230-860 / y 660-1060 (Service, Car, Part/Acc,
Car Model, Make), x 230-700 / y 1020-1260 (Part Type).

## Elementi esclusi (non di modello)
- Titolo "AutoRepairShop", trattino isolato a destra (circa x 875, y 640).

## Token completati da Analysis.xlsx (regola: parti illeggibili → xlsx)
| Visibile (a mano) | Trascritto | Fonte |
|---|---|---|
| `CAR_ KM` / `CAR- KM` (separatore tra `_` e `-`) | `CAR_KM` | xlsx `Service .Car_Km` |
| `HOURS_SPENT` | `HOURS_SPENT` | leggibile; xlsx `Hours_spent` |
| `AOM - DATE` (prima lettera dopo A ambigua D/O, separatore incerto) | `ADM_DATE` | xlsx `Service .Adm_Date` (e "admission" nel testo) |
| `FINISH - DATE` (separatore incerto) | `FINISH_DATE` | xlsx `Service .Finish_Date` |
| `CURRENT_ PRℓCE` (lettera I con macchia) | `CURRENT_PRICE` | xlsx `Part Type .Current_Price` |

Il maiuscolo dell'immagine è mantenuto ("MAIUSCOLO invariato"); dall'xlsx sono presi solo i caratteri
illeggibili o incerti.

## Ambiguità e interpretazioni
1. **Maiuscolo tipografico** (eccezione approvata il 2026-10-03): il diagramma è interamente in maiuscolo.
   `plantuml.txt` resta fedele all'immagine (`PERSON`, `PARTACC` da "PART/ACC", `CARMODEL`, `PARTTYPE`,
   `CAR_KM`, …). Le correzioni `corpus/corrections/DB09_AutoRepair.yaml` ("maiuscolo tipografico", tracciate in
   `corrections_applied`) portano le classi in PascalCase con i confini di parola dall'xlsx (Person, Employee,
   Owner, Service, Car, PartAcc, CarModel, Make, PartType) e gli attributi in minuscolo con i separatori come
   scritti (name, address, car_km, hours_spent, adm_date, finish_date, plate, color, serial_no, price,
   current_price). Unico acronimo: `ID` resta maiuscolo.
2. **Vincolo** `{Disjoint, Complete}` (parentesi graffe disegnate a mano) tra Employee e Owner, sotto la
   generalizzazione verso Person: trascritto su entrambe.
3. **Molteplicità**: Employee `1` – Service `*`; Owner `1` – Car `*` (l'`1` è disegnato come "ꞁ"); Service `*` –
   Car `1`; Service `1` – Part/Acc `1...*` (tre punti, normalizzato a `1..*` con warning); Car `*` – Car Model
   `1`; Car Model `*` – Make `1`; Part/Acc `*` – Part Type `1` (doppia linea verticale ripassata, una sola
   relazione); Car Model `*` – Part Type `*` (linea con gomito).
4. Car Model senza attributi (riquadro vuoto). Nessuna etichetta né ruolo. Attributi senza tipo.

## Analysis.xlsx ("Part 2 - 9")
Nessuna discrepanza (9 / 13 / 10).
