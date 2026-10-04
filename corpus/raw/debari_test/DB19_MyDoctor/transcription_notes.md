# Note di trascrizione — De Bari 19: MyDoctor

Fonte immagine: `corpus/raw/debari_test/_images/db19.png` (1383x1018), testo piccolo (stile Lucidchart).
Ingrandimenti 1.0x di x 30-1360 / y 20-460 e x 220-1360 / y 560-950: tutto leggibile, nessun token completato
dall'xlsx.

## Ambiguità e interpretazioni
1. **Generalizzazioni** Doctor, Patient → User e BloodTest, Consultation, Surgery → Appointment: punta piccola
   piena su un tronco comune (stile Lucidchart), lette come generalizzazioni (gerarchia; anche l'xlsx).
2. **Aggregazioni** (rombo vuoto sul contenitore): Schedule ◇ Office e Schedule ◇ Doctor (i due rombi sono sul
   lato superiore di Schedule), Appointment ◇ Patient (rombo sul lato superiore di Appointment). **Composizione**
   Schedule ◆ Appointment (rombo pieno sul lato destro di Schedule). Nessuna molteplicità.
3. **Tipo `Guid`** (Id di User, Office, Schedule, Appointment) → `string`: mappatura globale dei tipi di dominio
   (`DOMAIN_TYPE_MAPPING`, approvata il 2026-10-03), solo in posizione di tipo.
4. Metodi come scritti, anche con parametri (`CheckOfficeAvailability(startDate: Date, endDate: Date)`).
   Visibilità come disegnata (`- Id`, `+ Login()`).

## Analysis.xlsx ("Part 2 - 19")
Unica discrepanza: il refuso "Patienti" (Age, Address) nell'xlsx.
