# Limiti di rappresentazione Apollon v4 rispetto al PlantUML originale

Generato manualmente (sola lettura, nessuna modifica ai dati) leggendo
`corpus/processed/corpus.jsonl`, `corpus/label_classification.json` e
`corpus/processed/apollon/*.json` — FASE 4/5, 2026-09-29. Vedi `docs/decisions.md`
per la cronologia delle decisioni citate qui.

**Nota sul rendering visivo**: quanto segue descrive come ogni costrutto PlantUML
è codificato nel JSON Apollon v4 finale (campi dello schema, verificati nei
sorgenti `@tumaet/apollon`). **Il rendering effettivo nell'editor Apollon non è
mai stato verificato visivamente in questo ambiente** (nessun browser/JS
disponibile qui) — dove si dice che un elemento "non è visibile", si intende che
non esiste un campo/costrutto dedicato dello schema per rappresentarlo
distintamente (finisce in un campo testuale generico), non una conferma
visiva del rendering nell'editor fatta da questo assistente.

Verifica visiva nell'editor Apollon eseguita manualmente dall'autore su un
campione (AirTravel, CourseManagement, Boeing, BuildingManagement); import
con la libreria `@tumaet/apollon` 5.3.0 riuscito su tutti i 45 diagrammi
(verifica esterna del 2026-09-29, non eseguita da questo assistente).

---

## 1. Nomi di associazione in `label` (nessun campo dedicato per distinguerli da un ruolo)

Un'etichetta come `contains`/`belongsTo`/`teaches` resta nel campo generico
`edge.data.label` — lo stesso campo userebbe anche un testo di vincolo o un
nome di ruolo se non fossero stati smistati altrove (vedi §2, §6). Nulla nello
schema distingue "questo è un nome di associazione" da un qualunque altro
testo libero sull'edge.

**28 occorrenze, 11 esercizi:**

| Esercizio | Relazione | Etichetta |
|---|---|---|
| ClothingCompany | Product -- Order | `contains` |
| ClothingCompany | Category -- Product | `belongsTo` |
| ClothingCompany | Representative -- Order | `placedBy` |
| ClothingCompany | Product -- Country | `soldIn` |
| ClothingCompany | Representative - Country | `responsibleFor` |
| ClothingCompany | Order - Customer | `orders` |
| ClothingCompany | Country -- Customer | `resell` |
| EUScienceConnect | ResearchInstitution -- Person | `worksFor` |
| EUScienceConnect | Person -- PeerReviewedPaper | `reviews` |
| EUScienceConnect | ResearchInstitution -- Journal | `subscribesTo` |
| EUScienceConnect | Publisher -- Journal | `publishes` |
| EUScienceConnect | ResearchInstitution -- TechnicalReport | `publishes` |
| FilmSet | Director -- Screenplay | `implements` |
| FilmSet | Actor -- Screenplay | `reads` |
| FilmSet | ScreenplayAuthor -- Screenplay | `creates` |
| GameArea | Shape -- Shape (auto-relazione) | `is_connected_with` |
| Louvre | Location -- Room | `RoomLocationAssignment` |
| Musicmatic | RegularUser -- Album | `compose` |
| Sober | RideSharing -- Customer | `Book` |
| Sober | Ride - Car | `OperatedBy` |
| Sober | OtherCar -- Customer | `Owns` |
| TransportCompany | Planner -- Order | `creates` |
| TruckLogistics | Assignment --> Driver | `executes` |
| University | Employee -- Faculty | `leads` |
| University | Lecturer -- Course | `teaches` |
| CourseManagement | Course -- Teacher | `Preallocation` |
| CourseManagement | Teacher -- Lesson | `Allocation` |
| CourseManagement | Course -- Participant | `Enrolled` |

## 2. Vincoli di generalizzazione (spostati in `constraints`, mai nell'edge)

Un testo come `{total; disjoint}` su una relazione di ereditarietà/realizzazione
non è un'etichetta — è un vincolo UML standard su un insieme di
generalizzazione. `apollon_convert.py::extract_generalization_constraints`
lo estrae **prima** che venga scartato e lo scrive nel campo `constraints` del
record `corpus.jsonl` (mai nell'edge: gli edge di tipo `ClassInheritance`/
`ClassRealization` hanno sempre `label: ""`). Apollon non ha un costrutto
dedicato per i vincoli su generalizzazione: chi consuma `corpus.jsonl` deve
leggere `constraints` separatamente dal diagramma per non perdere questa
informazione.

**7 occorrenze, 4 esercizi:**

| Esercizio | Generalizzazione | Vincolo |
|---|---|---|
| EUScienceConnect | TechnicalReport extends Article | `{total; disjoint}` |
| FitnessCompanyConan | GroupSession extends Session | `{total; disjoint}` |
| FitnessCompanyConan | Member extends Person | `{partial; overlap}` |
| Musicmatic | Hit extends Song | `{total; disjoint}` |
| Musicmatic | BusinessUser extends User | `{total; overlap}` |
| Sober | RideHailing extends Ride | `{total; disjoint}` |
| Sober | SoberCar extends Car | `{total; disjoint}` |

## 3. Verso di lettura PlantUML (`>`/`<`) rimosso

PlantUML permette di annotare il verso di lettura di un'etichetta (`A -- B :
verbo >` si legge "A verbo B"). Il simbolo non fa parte del nome — se non
rimosso, finiva letteralmente nel testo di `label`/`role` del JSON finale
(bug corretto il 2026-09-29, `apollon_convert.py::strip_reading_direction`).
Apollon non ha un costrutto per il verso di lettura: l'informazione è
semplicemente scartata (non c'è un modo equivalente di rappresentarla).

**3 occorrenze, 2 esercizi:**

| Esercizio | Relazione | Etichetta originale | Dopo la pulizia |
|---|---|---|---|
| Louvre | Employee -- Employee (auto-relazione) | `hasCoach >` | ruolo `coach` (vedi §6) |
| University | Employee -- Faculty | `leads >` | associazione `leads` |
| University | Lecturer -- Course | `teaches >` | associazione `teaches` |

## 4. Classi associative reificate

Il costrutto PlantUML `(A,B) .. C` (classe associativa: una relazione che ha
essa stessa attributi) non ha equivalente diretto in Apollon. Approssimato
con due relazioni binarie derivate, `A--C` e `C--B`, con molteplicità
**derivate** (mai inventate) da quelle della relazione base A-B quando
presente nel sorgente (`apollon_convert.py::reify_association_classes`). Si
perde il **vincolo di unicità**: con la classe associativa esiste al più un
C per ogni coppia (A, B); con la reificazione no. Il resto del significato è
conservato.

**21 occorrenze, 18 esercizi** (riga PlantUML originale esatta, per
verificare il conteggio):

| Esercizio | Riga PlantUML originale |
|---|---|
| AirTravel | `(FlightExecution, Passenger) . Ticket` |
| AlphaInsurance | `(ClaimCase,Estimator) .. Report` |
| CelO | `Registration .. (Attendee,Event)` |
| CelO | `(Event,CheckListTask)..TaskStatus` |
| ClothingCompany | `Product . (Manufacturer,Country)` |
| EUScienceConnect | `Author .. (Article,Person)` |
| Facepage | `Privilege .. (PersonalAccount,PersonalPage)` |
| HomeForTheElderly | `Proposal .. (Bed,Person)` |
| House | `JobLog .. (House,Company)` |
| LabTracker | `(Lab,Requisition) .. Appointment` |
| Musicmatic | `Track .. (Hit,Album)` |
| PizzaDeliveryWithEntertainment | `(PizzaRestaurant,Entertainer) .. Employment` |
| ProjectManagement | `(ResearchGroup,Researcher) .. ResearchGroupMember` |
| ProjectManagement | `(WorkPackage,ResearchGroup) .. WorkPackageLeader` |
| School | `TeacherAssignment .. (Teacher,School)` |
| Sightseeing | `(Visitor,GuidedTour) .. Discount` |
| Sober | `Involved .. (Car,Accident)` |
| StudentAppointment | `(Student,Course) .. CourseSubscription` |
| StudentAppointment | `(Course,Assistant) .. TeachingAssistant` |
| TreatmentPlans | `(TreatmentPlan,ExaminationType) .. AdvisedExaminationType` |
| University | `(ResearchAssistant, Project) .. Participation` |

## 5. Modificatori `{static}`/`{abstract}`/`{frozen}`/`const` rimossi dagli attributi

Lo schema Apollon v4 non ha un campo dedicato per i modificatori di
attributo (a differenza dei metodi, che hanno `isAbstract` opzionale). Un
modificatore come `{frozen}` o la parola chiave informale `const` viene
riconosciuto da `parse_attribute` ma **non può comparire** nel formato di
output `+ nome : tipo = valore` — è quindi scartato dalla stringa
visualizzata e riportato invece in un warning esplicito
(`apollon_conversion_warnings`), mai perso in silenzio. Il valore di default
(`= valore`), quando presente, **è** invece preservato nella stringa.

**6 occorrenze, 2 esercizi:**

| Esercizio | Attributo | Modificatori rimossi | Default preservato |
|---|---|---|---|
| Sober | Ride.RideNr | `frozen` | — |
| Sober | Customer.CustNr | `frozen` | — |
| Sober | Car.CarNr | `frozen` | — |
| Sober | Accident.AccNr | `frozen` | — |
| TileOGame | Game.SpareConnectionPieces | `static`, `const` | `32` |
| TileOGame | Game.NumberOfActionCards | `static`, `const` | `32` |

## 6. Qualificatori trasformati in ruoli

Apollon non ha un costrutto per i "qualifier" UML (l'attributo tra parentesi
quadre che discrimina l'accesso lungo un'associazione, es. `WebPortal[id] ->
Entry`). I 2 casi individuati nel corpus (BuildingManagement) erano stati
inizialmente classificati come una categoria a parte ("qualificatore",
testo lasciato in `label`); il 2026-09-29 riclassificati come **ruolo**
(decisione utente: non serviva una lettura UML così specifica, sono
semplicemente il nome della proprietà di navigazione) — ora in
`sourceRole`/`targetRole`, label vuoto. La categoria "qualificatore" resta
riservata nel convertitore ma con **0 voci attive**.

**2 occorrenze, 1 esercizio:**

| Esercizio | Relazione | Prima | Dopo |
|---|---|---|---|
| BuildingManagement | WebPortal → Entry | qualificatore `id` in label | targetRole `id`, label vuoto |
| BuildingManagement | WebPortal → User | qualificatore `username` in label | targetRole `username`, label vuoto |

## 7. Classi implicite (mai dichiarate esplicitamente)

Una classe usata in una relazione o come partecipante di una classe
associativa ma mai dichiarata con `class X { ... }` è legale in PlantUML —
creata come nodo senza attributi (`pc.placeholder = True`). Non è un errore
di trascrizione, ma il nodo Apollon risultante è "vuoto" (nessun attributo,
nessun metodo) mentre nel testo della `description.md` la classe ha un
ruolo concettuale preciso.

**2 occorrenze, 2 esercizi:**

| Esercizio | Classe implicita | Contesto |
|---|---|---|
| Musicmatic | Album | mai dichiarata; riferita solo come partecipante della relazione `RegularUser -- Album : compose` |
| ProjectManagement | ResearchGroupMember | è la classe associativa reificata di `(ResearchGroup,Researcher)` — mai dichiarata con attributi propri |

## 8. Esercizi esclusi dalla conversione, e motivo

Conteggi aggiornati al 2026-10-04 (prima: "1 esercizio su 46, 45 convertiti", cioè 45 originali + il pilota
CourseManagement, prima della traduzione degli altri 14 esercizi italiani):

| Split | Record | Convertiti | Esclusi |
|---|---|---|---|
| Corpus di retrieval (`corpus.jsonl`: 45 originali + 15 tradotti) | 60 | 59 | 1 (Cruise) |
| Test set De Bari (`testset_debari.jsonl`) | 20 | 20 | 0 |

| Esercizio | Costrutto non supportato | Motivo |
|---|---|---|
| Cruise | `<> diamond` (diamante n-ario nativo PlantUML) | Nessun costrutto Apollon v4 documentato equivalente a un'associazione n-aria — il modello è escluso per intero (`diagram_apollon_json: null`), non approssimato |

## 9. Visibilità di attributi e metodi non conservata (sempre `+`)

(Aggiunto 2026-10-01, decisione utente: limite generale.) `parse_attribute` e
`parse_method_signature` tolgono il prefisso di visibilità originale (`+ - # ~`) e
il nome visualizzato in Apollon inizia sempre con `+ `. Nel corpus attuale i
membri non pubblici sono 25 (tutti `-`, privati) in 4 esercizi: ApartmentBuilding
(`-getNumeroPiani()`), MilanLibrary, RealEstateAgency, RepairShops. L'informazione
resta solo in `diagram_plantuml` di `corpus.jsonl`.

## 10. Due modellazioni alternative nello stesso diagramma (EatAtHome)

(Aggiunto il 2026-10-01 per decisione dell'utente. È un limite del dato, non del formato
Apollon.) Il diagramma di EatAtHome (es. 13) modella gli ingredienti in due modi: con gli
attributi `ingredients` e `allergen_information` di `Dish`, e con la classe `Ingredient`.
Nell'immagine `Ingredient` è disegnata in grigio, e una nota dell'autore dice di non tenere
insieme le due soluzioni: "alternative to keeping ingredients and allergen as strings. note:
in that case REMOVE ingredients and allergens from the dish class". Per fedeltà all'immagine
le due alternative sono state mantenute entrambe, come scelta consapevole, e il diagramma non
è stato modificato. La nota non è rappresentabile, perché le note sono escluse dalla
trascrizione. Il record di EatAtHome in `corpus.jsonl` ha quindi
`known_issues: ["two_alternative_models"]` (da `corpus/known_issues.yaml`), così l'esercizio
si può filtrare negli esperimenti, per esempio escluderlo dagli esempi few-shot o dalle query
di valutazione.

---

## Tabella riassuntiva

| # | Tipo di costrutto | Occorrenze | Esercizi coinvolti | Come è gestito |
|---|---|---|---|---|
| 1 | Nomi di associazione in `label` | 28 | 11 | Testo libero in `edge.data.label`, nessun campo dedicato che li distingua da un ruolo o da un'etichetta generica |
| 2 | Vincoli di generalizzazione | 7 | 4 | Estratti in `corpus.jsonl.constraints`, mai lasciati nell'edge (`ClassInheritance`/`ClassRealization` hanno sempre `label: ""`) |
| 3 | Verso di lettura PlantUML (`>`/`<`) | 3 | 2 | Rimosso dall'etichetta (`strip_reading_direction`), informazione scartata (nessun equivalente Apollon) |
| 4 | Classi associative reificate | 21 | 18 | Approssimate con 2 relazioni binarie derivate (molteplicità mai inventate); si perde il vincolo di unicità: con la classe associativa esiste al più un C per ogni coppia (A, B), con la reificazione no — il resto del significato è conservato |
| 5 | Modificatori attributo (`static`/`abstract`/`frozen`/`const`) | 6 | 2 | Scartati dalla stringa visualizzata, riportati in `apollon_conversion_warnings` (mai persi in silenzio); il default (`= valore`), quando presente, è preservato |
| 6 | Qualificatori → ruolo | 2 | 1 | Riclassificati come ruolo (`sourceRole`/`targetRole`); categoria "qualificatore" riservata ma con 0 voci attive |
| 7 | Classi implicite (mai dichiarate) | 2 | 2 | Nodo creato senza attributi/metodi (legale in PlantUML, non un errore) |
| 8 | Esercizi esclusi | 1 modello (1 costrutto) su 60 del corpus; 0 su 20 del test set | 1 | Intero modello escluso dalla conversione (`diagram_apollon_json: null`), non approssimato |
| 9 | Visibilità non pubblica (`-`) | 25 | 4 | Prefisso rimosso, sempre `+ ` nel JSON; conservata solo in `diagram_plantuml` |
| 10 | Due modellazioni alternative nello stesso diagramma | 1 | 1 (EatAtHome) | Entrambe mantenute (fedeltà all'immagine); segnalato con `known_issues: ["two_alternative_models"]` in `corpus.jsonl` |
