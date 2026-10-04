# Classificazione delle etichette — associazione, ruolo o vincolo

Generata da `corpus/_generate_label_classification.py` da tutte le 203 etichette non vuote (`: testo`) trovate nelle relazioni binarie dei 45 esercizi convertibili (44 originali + CourseManagement).

Categorie: **associazione** (verbo/descrizione del legame, resta in `label`), **ruolo** (nome di come si chiama una classe in quella relazione, va in `sourceRole`/`targetRole` sull'estremo indicato — colonna "Lettura" per verificare l'estremo), **vincolo** (testo di vincolo UML su una generalizzazione, es. `{disjoint,complete}` — non e' un'etichetta di relazione: dal 2026-09-25 estratto automaticamente nel campo `constraints` di corpus.jsonl, mai lasciato nell'edge, vedi `corpus/apollon_convert.py::extract_generalization_constraints`), **qualificatore** (verosimilmente un qualifier UML che Apollon non supporta — resta in `label` per mancanza di un posto migliore), **ruolo_doppio** (caso unico, TileOGame: un'etichetta con DUE nomi di ruolo distinti, uno per estremo — espansa in due righe qui sotto), **dubbio** (nessuna classificazione proposta, in attesa dell'utente).

| Esercizio | Relazione (sorgente) | Etichetta | Classificazione | Estremo proposto | Lettura | Motivazione |
|---|---|---|---|---|---|---|
| AirTravel | `Airport "1"--"0..*" Flight : Source` | Source | ruolo | Airport | Airport è il/la Source di Flight | Nome di ruolo: descrive cosa E' l'Airport per questo Flight (l'aeroporto di partenza), non un verbo che lega le due classi. Coppia con 'Destination' sotto: due relazioni distinte Airport-Flight, distinte dal ruolo dell'Airport in ciascuna. |
| AirTravel | `Airport "1"--"0..*" Flight : Destination` | Destination | ruolo | Airport | Airport è il/la Destination di Flight | Come 'Source' sopra, ma per l'aeroporto di arrivo. |
| AirTravel | `FlightExecution "0..*"-"1" Pilot : Captain` | Captain | ruolo | Pilot | Pilot è il/la Captain di FlightExecution | Nome di ruolo esplicitamente dato come esempio dall'utente: descrive cosa E' il Pilot in questa relazione (il comandante), non un verbo. |
| AirTravel | `FlightExecution "0..*"-"1..2" Pilot : Co-pilot` | Co-pilot | ruolo | Pilot | Pilot è il/la Co-pilot di FlightExecution | Come 'Captain' sopra, per il secondo pilota. |
| BuildingManagement | `WebPortal "1" --> "*" Entry : id` | id | ruolo | Entry | Entry è il/la id di WebPortal | RICLASSIFICATO (2026-09-29, decisione utente — categoria 'qualificatore' abbandonata, era una lettura UML non necessaria): 'id' non e' un qualificatore, e' il nome della proprieta' di navigazione (stessa convenzione di 'profilePicture', 'wheel', ecc. — nomi comuni, non frasi verbali) — targetRole 'id' sull'estremo Entry, label vuoto. Storico: NON piu' spostato su Building (quella correzione 'chiarimento_modellazione' e' stata annullata, BuildingManagement resta fedele all'originale, vedi docs/decisions.md) — il limite (Entry non ha mai un ID esplicito in description.md, solo Building) resta annotato ma non corretto. |
| BuildingManagement | `WebPortal "0..1" --> "1" User : username` | username | ruolo | User | User è il/la username di WebPortal | RICLASSIFICATO (2026-09-29, stessa motivazione di 'id' sopra): targetRole 'username' sull'estremo User, label vuoto. |
| BuildingManagement | `User "1" --> "*" Building : owner` | owner | ruolo | User | User è il/la owner di Building | Nome di ruolo esplicitamente dato come esempio dall'utente: descrive cosa E' lo User per quel Building. |
| BuildingManagement | `User "1" --> "*" Building : author` | author | ruolo | User | User è il/la author di Building | Come 'owner': relazione distinta (Building ha sia un owner sia un author, entrambi User ma ruoli diversi). |
| BuildingManagement | `Building "1" --> "1" Image : profilePicture` | profilePicture | ruolo | Image | Image è il/la profilePicture di Building | Descrive cosa E' l'Image per quel Building (la sua immagine profilo). |
| ClothingCompany | `Product "1"--"*" Order : contains` | contains | associazione | — | — | Verbo che descrive il legame. |
| ClothingCompany | `Category "1"--"*" Product: belongsTo` | belongsTo | associazione | — | — | Verbo (forma passiva). |
| ClothingCompany | `Representative "1"--"*" Order : placedBy` | placedBy | associazione | — | — | Verbo (forma passiva). |
| ClothingCompany | `Product "*"--"*" Country : soldIn` | soldIn | associazione | — | — | Verbo. |
| ClothingCompany | `Representative "*"-"1" Country : responsibleFor` | responsibleFor | associazione | — | — | Frase verbale ('e' responsabile di'), leggibile come frase sull'intera relazione. Confermato dall'utente (STOP 1) nonostante il confine con l'esempio di ruolo 'responsible': qui e' un verbo composto ('responsible-FOR'), non il nome nudo di un ruolo. |
| ClothingCompany | `Order "*"-"1" Customer : orders` | orders | associazione | — | — | Verbo. |
| ClothingCompany | `Country "*"--"*" Customer : resell` | resell | associazione | — | — | Verbo. |
| DestroyBlockGame | `Game "1" *-- "*" Block : blocks` | blocks | ruolo | Block | Block è il/la blocks di Game | Il testo coincide col nome della classe target (plurale): nomina la collezione di Block dal punto di vista di Game. |
| DestroyBlockGame | `Game "1" *-- "1" Paddle : paddle` | paddle | ruolo | Paddle | Paddle è il/la paddle di Game | Coincide col nome della classe target. |
| DestroyBlockGame | `Game "1" *-- "1" Ball : ball` | ball | ruolo | Ball | Ball è il/la ball di Game | Coincide col nome della classe target. |
| DestroyBlockGame | `Game "1" *-- "1..99" Level : levels` | levels | ruolo | Level | Level è il/la levels di Game | Coincide col nome della classe target (plurale). |
| DestroyBlockGame | `Game "1" *-- "*" BlockAssignment : blockAssignments` | blockAssignments | ruolo | BlockAssignment | BlockAssignment è il/la blockAssignments di Game | Coincide col nome della classe target (plurale, camelCase). |
| DestroyBlockGame | `Game "1" --> "0..1" HallOfFameEntry : mostRecentEntry` | mostRecentEntry | ruolo | HallOfFameEntry | HallOfFameEntry è il/la mostRecentEntry di Game | Descrive cosa E' quella HallOfFameEntry per Game (la piu' recente). |
| DestroyBlockGame | `Game "1" -- "*" PlayedGame : game` | game | ruolo | Game | Game è il/la game di PlayedGame | Il testo coincide col nome della classe SOURCE, non del target: si legge 'PlayedGame.game -> il Game di riferimento', quindi il ruolo qualifica l'estremo Game (il lato source di questa riga), non PlayedGame. |
| DestroyBlockGame | `Level "1" -- "*" BlockAssignment : level` | level | ruolo | Level | Level è il/la level di BlockAssignment | Coincide col nome della classe source: 'BlockAssignment.level -> il Level'. |
| DestroyBlockGame | `PlayedGame "1" *-- "*" PlayedBlockAssignment : blocks` | blocks | ruolo | PlayedBlockAssignment | PlayedBlockAssignment è il/la blocks di PlayedGame | Collezione di PlayedBlockAssignment vista da PlayedGame (target). |
| DestroyBlockGame | `Player "1" -- "1" User : player` | player | ruolo | Player | Player è il/la player di User | Coincide col nome della classe source: 'User.player -> il Player legato a quell'account'. |
| DestroyBlockGame | `Player "1" -- "*" PlayedGame : player` | player | ruolo | Player | Player è il/la player di PlayedGame | Come sopra: 'PlayedGame.player -> il Player che ha giocato'. |
| DestroyBlockGame | `Player "1" -- "*" HallOfFameEntry : player` | player | ruolo | Player | Player è il/la player di HallOfFameEntry | Come sopra: 'HallOfFameEntry.player -> il Player'. |
| DestroyBlockGame | `Admin "0..1" -- "1" User : admin` | admin | ruolo | Admin | Admin è il/la admin di User | Coincide col nome della classe source: 'User.admin -> l'Admin'. |
| DestroyBlockGame | `Admin "1" -- "*" Game : admin` | admin | ruolo | Admin | Admin è il/la admin di Game | Come sopra: 'Game.admin -> l'Admin che lo amministra'. |
| DestroyBlockGame | `Block "1" -- "*" PlayedBlockAssignment : block` | block | ruolo | Block | Block è il/la block di PlayedBlockAssignment | Coincide col nome della classe source: 'PlayedBlockAssignment.block -> il Block'. |
| Ebike | `EBike --> Wheel : wheel` | wheel | ruolo | Wheel | Wheel è il/la wheel di EBike | Coincide col nome della classe target. |
| Ebike | `EBike --> Battery : battery` | battery | ruolo | Battery | Battery è il/la battery di EBike | Coincide col nome della classe target. |
| Ebike | `EBike --> Frame : frame` | frame | ruolo | Frame | Frame è il/la frame di EBike | Coincide col nome della classe target. |
| Ebike | `EBike --> DriveSystem : driveSystem` | driveSystem | ruolo | DriveSystem | DriveSystem è il/la driveSystem di EBike | Coincide col nome della classe target. |
| Ebike | `EBike --> Controller : controller` | controller | ruolo | Controller | Controller è il/la controller di EBike | Coincide col nome della classe target. |
| Ebike | `DriveSystem --> Motor : motor` | motor | ruolo | Motor | Motor è il/la motor di DriveSystem | Coincide col nome della classe target. |
| Ebike | `Controller --> Battery : battery` | battery | ruolo | Battery | Battery è il/la battery di Controller | Coincide col nome della classe target. |
| Ebike | `Controller --> State : currentState` | currentState | ruolo | State | State è il/la currentState di Controller | Descrive cosa E' quello State (lo stato corrente). |
| eHome2020 | `Sensor "1" --> "1" Measurement : lastValue` | lastValue | ruolo | Measurement | Measurement è il/la lastValue di Sensor | Descrive cosa E' quella Measurement (l'ultimo valore). |
| EUScienceConnect | `TechnicalReport --\|> Article : {total; disjoint}` | {total; disjoint} | vincolo | — | — | Non e' un'etichetta di associazione: e' un vincolo UML standard ({disjoint,complete} in notazione OCL/UML) su un insieme di generalizzazione, catturato genericamente dal parser come ': label' perche' segue la stessa sintassi testuale. Va gestito come vincolo, non spostato in label ne' in un ruolo. |
| EUScienceConnect | `ResearchInstitution "1"--"*" Person : worksFor` | worksFor | associazione | — | — | Verbo. |
| EUScienceConnect | `Person "*"--"*" PeerReviewedPaper : reviews` | reviews | associazione | — | — | Verbo. |
| EUScienceConnect | `ResearchInstitution "*"--"*" Journal : subscribesTo` | subscribesTo | associazione | — | — | Verbo. |
| EUScienceConnect | `Publisher "1"--"*" Journal : publishes` | publishes | associazione | — | — | Verbo. |
| EUScienceConnect | `ResearchInstitution "1"--"*" TechnicalReport : publishes` | publishes | associazione | — | — | Verbo. |
| Facepage | `PersonalAccount "1"--"*" PersonalPage : administrator` | administrator | ruolo | PersonalAccount | PersonalAccount è il/la administrator di PersonalPage | Descrive cosa E' il PersonalAccount per quella Page (chi la amministra). |
| Facepage | `FriendRequest "*"-"1" PersonalAccount : sender` | sender | ruolo | PersonalAccount | PersonalAccount è il/la sender di FriendRequest | Nome di ruolo esplicitamente dato come esempio dall'utente. |
| Facepage | `FriendRequest "*"-"1" PersonalAccount : receiver` | receiver | ruolo | PersonalAccount | PersonalAccount è il/la receiver di FriendRequest | Come 'sender', relazione distinta (destinatario invece che mittente). |
| FilmSet | `Director "1"--"*" Screenplay : implements` | implements | associazione | — | — | Verbo. |
| FilmSet | `Actor "*"--"*" Screenplay : reads` | reads | associazione | — | — | Verbo. |
| FilmSet | `Film "1"--"0..1" ScreenplayAuthor : MostSuccessful` | MostSuccessful | ruolo | Film | Film è il/la MostSuccessful di ScreenplayAuthor | CORRETTO (2026-09-28, revisione utente di roles_to_review.md): l'estremo giusto e' Film, non ScreenplayAuthor. description.md: 'The name and most successful film of a screenwriter are stored' — e' il FILM ad essere 'il piu' di successo' (di quello screenwriter), non l'autore ad essere 'il piu' di successo'. Lettura corretta: 'Film e' il MostSuccessful di ScreenplayAuthor'. |
| FilmSet | `ScreenplayAuthor "1"--"*" Screenplay : creates` | creates | associazione | — | — | Verbo. |
| FitnessCompanyConan | `Session <\|-- GroupSession : {total; disjoint}` | {total; disjoint} | vincolo | — | — | Vincolo UML su generalizzazione, come EUScienceConnect sopra. |
| FitnessCompanyConan | `Person <\|-- Member : {partial; overlap}` | {partial; overlap} | vincolo | — | — | Vincolo UML su generalizzazione. |
| GameArea | `Shape "*" -- "*" Shape : is_connected_with` | is_connected_with | associazione | — | — | Verbo (auto-relazione). |
| GameArea | `GameArea "1" --> "1" Enemy : finalBoss` | finalBoss | ruolo | Enemy | Enemy è il/la finalBoss di GameArea | Descrive cosa E' quel Enemy per quella GameArea. |
| HelpingHands | `Volunteer *-> "0..*" Date : availableDates` | availableDates | ruolo | Date | Date è il/la availableDates di Volunteer | Descrive cosa sono quelle Date per quel Volunteer (le date disponibili). |
| HelpingHands | `Route "0..1" - "0..*" Item : pickupRoute` | pickupRoute | ruolo | Route | Route è il/la pickupRoute di Item | Coincide (parzialmente) col nome della classe source: 'Item.pickupRoute -> la Route'. |
| HelpingHands | `Route "0..*" -- "0..*" SecondHandArticle : dropOffRoute` | dropOffRoute | ruolo | Route | Route è il/la dropOffRoute di SecondHandArticle | Come sopra, relazione distinta (route di consegna anziche' di ritiro). |
| HotelBookingManagementSystem | `SpecialOffer "*" -- "1" BookingInfo : specialOffers` | specialOffers | ruolo | SpecialOffer | SpecialOffer è il/la specialOffers di BookingInfo | Coincide col nome della classe source (plurale). |
| HotelBookingManagementSystem | `BookingInfo "*" -- "0..5" SpecialOffer : bestOffers` | bestOffers | ruolo | SpecialOffer | SpecialOffer è il/la bestOffers di BookingInfo | Coincide (parzialmente) col nome della classe target: le offerte migliori. |
| Louvre | `Employee "1" -- "0..*" Exhibition : Coordinator` | Coordinator | ruolo | Employee | Employee è il/la Coordinator di Exhibition | Descrive cosa E' quell'Employee per quella Exhibition. |
| Louvre | `Exhibition "0..*" -- "0..1" Location : AssignedLocation` | AssignedLocation | ruolo | Location | Location è il/la AssignedLocation di Exhibition | Coincide (parzialmente) col nome della classe target. |
| Louvre | `Location "0..*" -- "0..*" Room : RoomLocationAssignment` | RoomLocationAssignment | associazione | — | — | Decisione utente (2026-09-27): nome dell'associazione (non un ruolo di una delle due classi), nonostante concateni entrambi i nomi di classe. Resta in 'label'. |
| Louvre | `Employee "0..*" -- "0..1" Employee : hasCoach >` | hasCoach | ruolo | Employee | Employee è il/la coach di Employee | RICLASSIFICATO (2026-09-29, decisione utente): auto-relazione Employee-Employee — senza un ruolo esplicito i due estremi non si distinguono. Ruolo 'coach' (il sostantivo, non la frase verbale 'hasCoach' usata come etichetta) sull'estremo con molteplicita' 0..1 (il dipendente che fa da coach, presente 0 o 1 volta), posizione 'target' nella riga PlantUML (il simbolo finale '>', gia' rimosso dall'etichetta da apollon_convert.py::strip_reading_direction, era solo un marcatore di verso di lettura, non parte del nome). |
| Musicmatic | `Song <\|-- Hit : {total; disjoint}` | {total; disjoint} | vincolo | — | — | Vincolo UML su generalizzazione. |
| Musicmatic | `BusinessUser --\|> User : {total; overlap}` | {total; overlap} | vincolo | — | — | Vincolo UML su generalizzazione. |
| Musicmatic | `RegularUser "1"--"*" Album : compose` | compose | associazione | — | — | Verbo. |
| Musicmatic | `RegularUser "*"--"*" Album : suggestion` | suggestion | ruolo | Album | Album è il/la suggestion di RegularUser | Decisione utente (2026-09-27): descrive cosa E' quell'Album per l'altro RegularUser (un suggerimento), coerente con description.md ('the album of regular users can be turned into a suggestion to other regular users'). Nota per il report: 'Album' e' una classe implicita in questo esercizio — mai dichiarata con 'class Album {...}' nel plantuml.txt sorgente, creata come nodo senza attributi (dichiarazione implicita legale in PlantUML, vedi warning gia' emesso da apollon_convert.py). |
| OnlineTutoringSystem | `User "1" *-- "0..2" TutoringRole : roles` | roles | ruolo | TutoringRole | TutoringRole è il/la roles di User | Coincide col nome della classe target (plurale). |
| OnlineTutoringSystem | `TutoringRequest "1" *-- "*" TutoringSession : allSessions` | allSessions | ruolo | TutoringSession | TutoringSession è il/la allSessions di TutoringRequest | Coincide (parzialmente) col nome della classe target. |
| OnlineTutoringSystem | `TutoringSession "1" --> "0..1" TutoringSession : nextSession` | nextSession | ruolo | TutoringSession | TutoringSession è il/la nextSession di TutoringSession | Auto-relazione (decisione utente 2026-09-28): il nome della classe non puo' disambiguare quale delle due occorrenze porta il ruolo — 'estremo' e' quindi la POSIZIONE letterale nella riga PlantUML ('target' = lato destro della riga sorgente), non un nome di classe. Descrive il ruolo del target (la sessione successiva). |
| OnlineTutoringSystem | `TutoringRequest "1" --> "0..1" TutoringSession : firstSession` | firstSession | ruolo | TutoringSession | TutoringSession è il/la firstSession di TutoringRequest | Descrive il ruolo del target (la prima sessione). |
| School | `Teacher "1"-"0..1" School : Principal` | Principal | ruolo | Teacher | Teacher è il/la Principal di School | Descrive cosa E' quel Teacher per quella School (il preside). |
| SmartHomeAutomationSystem | `SmartHome "1" *-- "0..1" Address : address` | address | ruolo | Address | Address è il/la address di SmartHome | Coincide col nome della classe target. |
| SmartHomeAutomationSystem | `SmartHome "1" *-- "*" Room : rooms` | rooms | ruolo | Room | Room è il/la rooms di SmartHome | Coincide col nome della classe target (plurale). |
| SmartHomeAutomationSystem | `SmartHome "1" *-- "0..1" ActivityLog : log` | log | ruolo | ActivityLog | ActivityLog è il/la log di SmartHome | Coincide (parzialmente) col nome della classe target. |
| SmartHomeAutomationSystem | `User "*" -- "*" SmartHome : owners` | owners | ruolo | User | User è il/la owners di SmartHome | Coincide col nome-concetto della classe source (plurale): gli User che possiedono la casa. |
| SmartHomeAutomationSystem | `Room "1" *-- "*" Sensor : sensors` | sensors | ruolo | Sensor | Sensor è il/la sensors di Room | Coincide col nome della classe target (plurale). |
| SmartHomeAutomationSystem | `Room "1" *-- "*" Actuator : actuators` | actuators | ruolo | Actuator | Actuator è il/la actuators di Room | Coincide col nome della classe target (plurale). |
| SmartHomeAutomationSystem | `ActivityLog "1" *-- "*" SensorReading : recordedReadings` | recordedReadings | ruolo | SensorReading | SensorReading è il/la recordedReadings di ActivityLog | Coincide (parzialmente) col nome della classe target. |
| SmartHomeAutomationSystem | `ActivityLog "1" *-- "*" ControlCommand : recordedCommands` | recordedCommands | ruolo | ControlCommand | ControlCommand è il/la recordedCommands di ActivityLog | Coincide (parzialmente) col nome della classe target. |
| SmartHomeAutomationSystem | `CommandSequence "*" -- "0..1" CommandSequence : nextCommand` | nextCommand | ruolo | CommandSequence | CommandSequence è il/la nextCommand di CommandSequence | Auto-relazione (decisione utente 2026-09-28): 'estremo' e' la posizione letterale ('target' = lato destro della riga sorgente), non un nome di classe — vedi nota su OnlineTutoringSystem/nextSession. Descrive il ruolo del target (il comando successivo). |
| SmartHomeAutomationSystem | `CommandSequence "1" *-- "0..1" ControlCommand : command` | command | ruolo | ControlCommand | ControlCommand è il/la command di CommandSequence | Coincide (parzialmente) col nome della classe target. |
| SmartHomeAutomationSystem | `SensorReading "*" -- "1" Sensor : sensor` | sensor | ruolo | Sensor | Sensor è il/la sensor di SensorReading | Coincide col nome della classe target. |
| SmartHomeAutomationSystem | `ControlCommand "*" -- "1" Actuator : actuator` | actuator | ruolo | Actuator | Actuator è il/la actuator di ControlCommand | Coincide col nome della classe target. |
| SmartHomeAutomationSystem | `AlertRule "1" *-- "0..1" BooleanExpression : precondition` | precondition | ruolo | BooleanExpression | BooleanExpression è il/la precondition di AlertRule | Descrive cosa E' quella Expression per quella AlertRule. |
| SmartHomeAutomationSystem | `AlertRule "1" *-- "*" CommandSequence : actions` | actions | ruolo | CommandSequence | CommandSequence è il/la actions di AlertRule | Descrive cosa sono quelle CommandSequence per quella AlertRule. |
| SmartHomeAutomationSystem | `NotExpression "0..1" -- "1" BooleanExpression : expression` | expression | ruolo | BooleanExpression | BooleanExpression è il/la expression di NotExpression | Coincide col nome-concetto della classe target. |
| SmartHomeAutomationSystem | `BinaryExpression "0..1" -- "1" BooleanExpression : leftExpr` | leftExpr | ruolo | BooleanExpression | BooleanExpression è il/la leftExpr di BinaryExpression | Qualifica QUALE operando (sinistro) tra due relazioni identiche altrimenti. |
| SmartHomeAutomationSystem | `BinaryExpression "0..1" -- "1" BooleanExpression : rightExpr` | rightExpr | ruolo | BooleanExpression | BooleanExpression è il/la rightExpr di BinaryExpression | Come sopra, operando destro. |
| Sober | `Ride <\|-- RideHailing : {total; disjoint}` | {total; disjoint} | vincolo | — | — | Vincolo UML su generalizzazione. |
| Sober | `RideHailing "*"--"1" Customer : LeadCustomer` | LeadCustomer | ruolo | Customer | Customer è il/la LeadCustomer di RideHailing | Descrive cosa E' quel Customer per quella corsa (il cliente principale). |
| Sober | `RideSharing "*"--"1" Customer : Book` | Book | associazione | — | — | Decisione utente (2026-09-27): verbo ('prenotare'), coerente con description.md ('a customer who books 20 uses of the Sober ride-sharing service'). Testo invariato in 'label'. |
| Sober | `Ride "*"-"1" Car : OperatedBy` | OperatedBy | associazione | — | — | Frase verbale passiva. |
| Sober | `Car <\|-- SoberCar : {total; disjoint}` | {total; disjoint} | vincolo | — | — | Vincolo UML su generalizzazione. |
| Sober | `OtherCar "*"--"1" Customer : Owns` | Owns | associazione | — | — | Verbo. |
| TeamSportsScoutingSystem | `ScoutReport "0..1" <--> "0..1" ScoutReport : nextReport` | nextReport | ruolo | ScoutReport | ScoutReport è il/la nextReport di ScoutReport | Auto-relazione (decisione utente 2026-09-28): 'estremo' e' la posizione letterale ('target' = lato destro della riga sorgente), non un nome di classe — vedi nota su OnlineTutoringSystem/nextSession. Descrive il ruolo del target (il report successivo). |
| TileOGame | `TileO "1" *-- "*" Game : games` | games | ruolo | Game | Game è il/la games di TileO | Coincide col nome della classe target (plurale). |
| TileOGame | `Game  "1" *-- "*" Tile : tiles` | tiles | ruolo | Tile | Tile è il/la tiles di Game | Coincide col nome della classe target (plurale). |
| TileOGame | `Game  "1" *-- "*" Connection : connections` | connections | ruolo | Connection | Connection è il/la connections di Game | Coincide col nome della classe target (plurale). |
| TileOGame | `Game  "1" *-- "1" Die : die` | die | ruolo | Die | Die è il/la die di Game | Coincide col nome della classe target. |
| TileOGame | `Game  "1" *- "1" Deck : deck` | deck | ruolo | Deck | Deck è il/la deck di Game | Coincide col nome della classe target. |
| TileOGame | `Game  "1" --> "0..1" Player : currentPlayer` | currentPlayer | ruolo | Player | Player è il/la currentPlayer di Game | Descrive cosa E' quel Player per quel Game (il giocatore corrente). |
| TileOGame | `Game  "1" *-- "2..4" Player : players` | players | ruolo | Player | Player è il/la players di Game | Coincide col nome della classe target (plurale). |
| TileOGame | `Deck  "1" *-- "0..32" ActionCard : cards` | cards | ruolo | ActionCard | ActionCard è il/la cards di Deck | Coincide (genericamente) col concetto della classe target. |
| TileOGame | `Game  "1" --> "0..1" WinTile : winTile` | winTile | ruolo | WinTile | WinTile è il/la winTile di Game | Coincide col nome della classe target. |
| TileOGame | `Tile  "2" -- "0..4" Connection : connections/tiles` | tiles (da 'connections/tiles') | ruolo | Tile | Tile è il/la tiles di Connection | Decisione utente (2026-09-27): caso unico nel corpus — l'etichetta impacchetta due nomi di ruolo distinti, uno per estremo, invece di uno solo. 'tiles' coincide col nome della classe Tile, 'connections' col nome della classe Connection — stessa convenzione gia' usata altrove (es. 'Game *-- Tile : tiles' e 'Game *-- Connection : connections', righe 69-70 dello stesso file). Label vuoto: non e' un'etichetta di associazione, sono due ruoli. |
| TileOGame | `Tile  "2" -- "0..4" Connection : connections/tiles` | connections (da 'connections/tiles') | ruolo | Connection | Connection è il/la connections di Tile | Decisione utente (2026-09-27): caso unico nel corpus — l'etichetta impacchetta due nomi di ruolo distinti, uno per estremo, invece di uno solo. 'tiles' coincide col nome della classe Tile, 'connections' col nome della classe Connection — stessa convenzione gia' usata altrove (es. 'Game *-- Tile : tiles' e 'Game *-- Connection : connections', righe 69-70 dello stesso file). Label vuoto: non e' un'etichetta di associazione, sono due ruoli. |
| TileOGame | `Player "1" --> "0..1" Tile : startingTile` | startingTile | ruolo | Tile | Tile è il/la startingTile di Player | Descrive cosa E' quel Tile per quel Player (la casella di partenza). |
| TileOGame | `Player "0..4" --> "0..1" Tile : currentTile` | currentTile | ruolo | Tile | Tile è il/la currentTile di Player | Descrive cosa E' quel Tile per quel Player (la casella corrente). |
| TileOGame | `Deck  "1" --> "0..1" ActionCard : currentCard` | currentCard | ruolo | ActionCard | ActionCard è il/la currentCard di Deck | Descrive cosa E' quella ActionCard per quel Deck (la carta corrente). |
| TransportCompany | `Planner "1" --"*" Order : creates` | creates | associazione | — | — | Verbo. |
| TruckLogistics | `Assignment "0..1" --> "*" Driver : executes` | executes | associazione | — | — | Verbo. |
| TruckLogistics | `Assignment "*" --> "1" Location : from` | from | ruolo | Location | Location è il/la from di Assignment | Nome di ruolo classico (preposizione sostantivata): l'origine. |
| TruckLogistics | `Assignment "*" --> "1" Location : to` | to | ruolo | Location | Location è il/la to di Assignment | Come 'from': la destinazione (relazione distinta). |
| TruckLogistics | `Vehicle "1" --> "1" VehicleStatus : status` | status | ruolo | VehicleStatus | VehicleStatus è il/la status di Vehicle | Coincide (parzialmente) col nome della classe target. |
| University | `Employee "1" -- "0..1" Faculty : leads >` | leads | associazione | — | — | Frase verbale ('guida'); il simbolo '>' che seguiva l'etichetta nel sorgente e' un marcatore di verso di lettura di PlantUML, non parte del testo — rimosso da apollon_convert.py::strip_reading_direction (2026-09-29), quindi anche dalla chiave di classificazione qui. |
| University | `Lecturer "1..*" -- "1..*" Course : teaches >` | teaches | associazione | — | — | Frase verbale ('insegna'); stessa nota sul marcatore '>' sopra. |
| ApartmentBuilding | `Apartment "1..*" -- "1..*" Person : isOwnedBy` | isOwnedBy | associazione | — | — | Verbo ('è posseduto'), al centro della linea. |
| Bookmaker | `Bet --> Race : race` | race | ruolo | Race | Race è il/la race di Bet | Nome di campo Java = nome della proprieta' di navigazione (stessa convenzione di profilePicture). |
| Bookmaker | `Bet --> Runner : runner` | runner | ruolo | Runner | Runner è il/la runner di Bet | Come 'race'. |
| Bookmaker | `Race --> Runner : winner` | winner | ruolo | Runner | Runner è il/la winner di Race | Come 'race'. |
| Bookmaker | `Runner --> Jockey : jockey` | jockey | ruolo | Jockey | Jockey è il/la jockey di Runner | Come 'race'. |
| Bookmaker | `Runner --> Horse : horse` | horse | ruolo | Horse | Horse è il/la horse di Runner | Come 'race'. |
| CourseManagement | `Course "0..*" -- "1..*" Teacher : Preallocation` | Preallocation | associazione | — | — | Nome di associazione (sostantivo che descrive il legame nel suo complesso), non un ruolo di una delle due classi. |
| CourseManagement | `Teacher "1..2" -- "0..*" Lesson : Allocation` | Allocation | associazione | — | — | Come 'Preallocation': nome dell'associazione. |
| CourseManagement | `Course "1..*" -- "1..*" Participant : Enrolled` | Enrolled | associazione | — | — | Come 'Preallocation'/'Allocation' nello stesso esercizio: nome dell'associazione, non un ruolo. |
| EatAtHome | `Customer "1" -- "0..*" Order : makes >` | makes | associazione | — | — | Verbo ('makes ►', diagramma gia' in inglese). |
| EatAtHome | `Order "*" -- "1..*" Dish : contains >` | contains | associazione | — | — | Verbo ('contains ►'). |
| EatAtHome | `Dish "1" -- "1..*" Ingredient : contains >` | contains | associazione | — | — | Verbo ('contains ►'). |
| ElevatorControl | `ElevatorController ..> Elevator : controls` | controls | associazione | — | — | Verbo ('controlla'), su dipendenza (tratteggiata: verifica visiva dell'autore 2026-10-01, prima trascritta -->). |
| ElevatorControl | `ElevatorController ..> Door : controls` | controls | associazione | — | — | Verbo ('controlla'), su dipendenza. |
| ElevatorControl | `ElevatorController "1" -- "*" Button : communicates` | communicates | associazione | — | — | Verbo ('comunica'), in corsivo al centro della linea. |
| Gym | `Subscription "1..*" -- "0..*" Service : AdditionalServices` | AdditionalServices | ruolo | Service | Service è il/la AdditionalServices di Subscription | Sostantivo ('ServiziAggiuntivi'): regola 'sostantivo = ruolo, la posizione non conta'. |
| Gym | `Subscription "1..*" -- "1..*" Service : BaseServices` | BaseServices | ruolo | Service | Service è il/la BaseServices di Subscription | Come 'AdditionalServices' ('ServiziBase'). |
| MilanLibrary | `Library "1" -- "0..*" ItemTransferRequest : request destination` | request destination | ruolo | Library | Library è il/la request destination di ItemTransferRequest | Approvato dall'utente: ruolo della biblioteca nella richiesta (destinataria), nonostante il testo centrato sulla linea. |
| MilanLibrary | `Library "1" -- "0..*" ItemTransferRequest : request source` | request source | ruolo | Library | Library è il/la request source di ItemTransferRequest | Come 'request destination' (biblioteca mittente). |
| MilanLibrary | `Library o-- "1..*" User : Has` | Has | associazione | — | — | Frase verbale ('possiede'). |
| OilWells | `OnshoreWell --\|> Well : {disjoint, complete}` | {disjoint, complete} | vincolo | — | — | Vincolo UML sull'insieme di generalizzazione (scritto una volta sul tronco comune). |
| OilWells | `OffshoreWell --\|> Well : {disjoint, complete}` | {disjoint, complete} | vincolo | — | — | Come sopra. |
| OilWells | `OffshoreWell "0..1" -- "0..1" Area : location` | location | ruolo | Area | Area è il/la location di OffshoreWell | Decisione utente: 'luogo' e' un sostantivo -> ruolo sull'estremo Area, anche se scritto al centro della linea (la posizione non conta). |
| RepairShops | `RepairShop "1" -- "1..*" Employee : <WorksAt` | WorksAt | associazione | — | — | Verbo ('<Lavora'; '<' = verso di lettura). |
| RepairShops | `RepairShop "1" -- "1" Director : <manages` | manages | associazione | — | — | Verbo ('<dirige'). |
| RepairShops | `RepairShop "1" -- "0..*" Repair : performs>` | performs | associazione | — | — | Verbo ('effettua>'). |
| RepairShops | `Vehicle "1..*" -- "1" Owner : belongsTo>` | belongsTo | associazione | — | — | Verbo ('appartiene>'). |
| ResearchCenter | `Researcher "1..*" -- "1" Area : Belongs to >` | Belongs to | associazione | — | — | Frase verbale ('appartiene a'), non un nome di ruolo. |
| ResearchCenter | `SeniorResearcher "1" -- "1" Team : Leads` | Leads | associazione | — | — | Frase verbale ('guida'); 'Guidato da' sull'altro estremo e' solo la forma passiva, scartata in trascrizione. |
| ResearchCenter | `Team -- Project : Carries out >` | Carries out | associazione | — | — | Frase verbale ('svolge'). |
| Restaurant | `Customer "1..1" -- "0..*" Assignment : books` | books | associazione | — | — | Verbo ('prenota'). |
| Restaurant | `Assignment "0..*" -- "1..*" Table : includes` | includes | associazione | — | — | Verbo ('include'). |
| Restaurant | `Assignment "0..*" -- "0..*" Waiter : serves` | serves | associazione | — | — | Verbo ('serve'). |
| UniversityExams | `Student -- "1" Place : Student_born_in` | Student_born_in | associazione | — | — | Nome dell'associazione ('nato a'), centrato sulla linea. |
| UniversityExams | `Professor -- "1" Place : Prof_born_in` | Prof_born_in | associazione | — | — | Come 'Student_born_in'. |
| UniversityExams | `Faculty "1" -- "1..*" Course : < BelongsTo` | BelongsTo | associazione | — | — | Frase verbale ('< Appartenente'; il '<' e' verso di lettura, rimosso). |
| UniversityExams | `Professor "1..*" -- Course : < Teaches` | Teaches | associazione | — | — | Frase verbale ('< Insegna'). |
| DB01_ProjectManagementSystem | `Project -- Requirement : Input` | Input | associazione | — | — | Decisione utente: nome di ASSOCIAZIONE, non ruolo, perche' ha il triangolo pieno del verso di lettura (◄), che i nomi di ruolo non hanno (anche se 'Input' e' anche un sostantivo). |
| DB01_ProjectManagementSystem | `Project -- System : Output` | Output | associazione | — | — | Come 'Input': triangolo pieno di verso di lettura (►), quindi nome di associazione. |
| DB01_ProjectManagementSystem | `Manager -- Project : Manage` | Manage | associazione | — | — | Verbo con triangolo pieno di verso di lettura (►). |
| DB01_ProjectManagementSystem | `Team -- Project : Execute` | Execute | associazione | — | — | Verbo con triangolo pieno di verso di lettura (◄). |
| DB01_ProjectManagementSystem | `Manager -- Team : Lead` | Lead | associazione | — | — | Verbo al centro della linea. |
| DB02_HollywoodApproach | `Take "1...*" -- "1" Setup : tk_of_stp` | tk_of_stp | associazione | — | — | Nome di relazione al centro della linea ('take of setup'). |
| DB02_HollywoodApproach | `Scene "1" -- "1...*" Setup : stp_for_scn` | stp_for_scn | associazione | — | — | Nome di relazione al centro della linea ('setup for scene'). |
| DB02_HollywoodApproach | `Internal --\|> Scene : {complete, disjoint}` | {complete, disjoint} | vincolo | — | — | Vincolo UML sull'insieme di generalizzazione Internal/External. |
| DB02_HollywoodApproach | `External --\|> Scene : {complete, disjoint}` | {complete, disjoint} | vincolo | — | — | Come sopra. |
| DB02_HollywoodApproach | `External "0...*" -- "1" Location : located` | located | associazione | — | — | Verbo (participio) al centro della linea. |
| DB04_PatientRecordAndSchedulingSystem | `FamilyInsured "1..*" -- "1" Doctor : hasPrimaryCare` | hasPrimaryCare | associazione | — | — | Verbo. |
| DB05_MovieShop | `User "*" --> "1" MovieShop : uses` | uses | associazione | — | — | Verbo. |
| DB05_MovieShop | `MovieShop "1" -- "*" Card : make` | make | associazione | — | — | Verbo. |
| DB05_MovieShop | `MovieShop "1" --> "*" Order : make` | make | associazione | — | — | Verbo. |
| DB05_MovieShop | `Subscriber "1" --> "1" Card : has` | has | associazione | — | — | Verbo. |
| DB05_MovieShop | `Order "*" -- "1..*" MovieBuy : related to` | related to | associazione | — | — | Verbo. |
| DB05_MovieShop | `Subscriber "*" --> "1..*" MovieRent : hire` | hire | associazione | — | — | Verbo. |
| DB06_Flights | `Airline "1" -- "*" Flight : offers` | offers | associazione | — | — | Verbo. |
| DB06_Flights | `Airline "*" -- "*" Aircraft : owns` | owns | associazione | — | — | Verbo. |
| DB06_Flights | `Flight "*" -- "1" Airport : arrives to` | arrives to | associazione | — | — | Verbo. |
| DB06_Flights | `Flight "*" -- "1" Airport : departs from` | departs from | associazione | — | — | Verbo. |
| DB06_Flights | `Aircraft "1" -- "*" Flight : uses` | uses | associazione | — | — | Verbo. |
| DB06_Flights | `Flight -- "2..n" Pilot : Driven by` | Driven by | associazione | — | — | Verbo (passivo). |
| DB06_Flights | `Aircraft "*" -- "1" AircraftType : is of` | is of | associazione | — | — | Verbo. |
| DB06_Flights | `AircraftType "*" -- "*" Pilot : Navigator of` | Navigator of | ruolo | Pilot | Pilot è il/la Navigator di AircraftType | Decisione utente (2026-10-03): 'X of' = sostantivo + preposizione, senza triangolo di verso di lettura -> RUOLO sull'estremo Pilot, testo = il sostantivo con la maiuscola come scritto (precedente Louvre hasCoach -> coach). |
| DB06_Flights | `AircraftType "*" -- "1..n" Pilot : Copilot of` | Copilot of | ruolo | Pilot | Pilot è il/la Copilot di AircraftType | Decisione utente (2026-10-03): 'X of' = sostantivo + preposizione, senza triangolo di verso di lettura -> RUOLO sull'estremo Pilot, testo = il sostantivo con la maiuscola come scritto (precedente Louvre hasCoach -> coach). |
| DB06_Flights | `AircraftType "*" -- "1" Pilot3 : Captain of` | Captain of | ruolo | Pilot3 | Pilot3 è il/la Captain di AircraftType | Decisione utente (2026-10-03): 'X of' = sostantivo + preposizione, senza triangolo di verso di lettura -> RUOLO sull'estremo Pilot3, testo = il sostantivo con la maiuscola come scritto (precedente Louvre hasCoach -> coach). |
| DB08_VeterinaryClinic | `Owner --\|> Person : {DISJOINT, COMPLETE}` | {DISJOINT, COMPLETE} | vincolo | — | — | Vincolo sull'insieme di generalizzazione. |
| DB08_VeterinaryClinic | `Physician --\|> Person : {DISJOINT, COMPLETE}` | {DISJOINT, COMPLETE} | vincolo | — | — | Come sopra. |
| DB09_AutoRepair | `Employee --\|> Person : {Disjoint, Complete}` | {Disjoint, Complete} | vincolo | — | — | Vincolo sull'insieme di generalizzazione (scritto a mano; classi dopo la correzione 'maiuscolo tipografico'). |
| DB09_AutoRepair | `Owner --\|> Person : {Disjoint, Complete}` | {Disjoint, Complete} | vincolo | — | — | Come sopra. |
| DB10_Restaurant | `Client --\|> Person : {OVERLAPPING, COMPLETE}` | {OVERLAPPING, COMPLETE} | vincolo | — | — | Vincolo sull'insieme di generalizzazione. |
| DB10_Restaurant | `Waiter --\|> Person : {OVERLAPPING, COMPLETE}` | {OVERLAPPING, COMPLETE} | vincolo | — | — | Come sopra. |
| DB11_Deliveries | `CUSTOMER --\|> Person : {DISJOINT, COMPLETE}` | {DISJOINT, COMPLETE} | vincolo | — | — | Vincolo sull'insieme di generalizzazione. |
| DB11_Deliveries | `COURIER --\|> Person : {DISJOINT, COMPLETE}` | {DISJOINT, COMPLETE} | vincolo | — | — | Come sopra. |
| DB11_Deliveries | `CUSTOMER "1" -- "*" Package : Sender` | Sender | ruolo | CUSTOMER | CUSTOMER è il/la Sender di Package | Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo CUSTOMER, testo come scritto. |
| DB11_Deliveries | `CUSTOMER "1" -- "*" Package : Recipient` | Recipient | ruolo | CUSTOMER | CUSTOMER è il/la Recipient di Package | Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo CUSTOMER, testo come scritto. |
| DB11_Deliveries | `Package "*" -- "1" DeliveryCenter : Dropoff point` | Dropoff point | ruolo | DeliveryCenter | DeliveryCenter è il/la Dropoff point di Package | Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo DeliveryCenter, testo come scritto. |
| DB13_Factory | `CLIENT --\|> Person : {DISJOINT, COMPLETE}` | {DISJOINT, COMPLETE} | vincolo | — | — | Vincolo sull'insieme di generalizzazione. |
| DB13_Factory | `WORKER --\|> Person : {DISJOINT, COMPLETE}` | {DISJOINT, COMPLETE} | vincolo | — | — | Come sopra. |
| DB13_Factory | `CLIENT "1" -- "*" PURCHASEORDER : Issuer` | Issuer | ruolo | CLIENT | CLIENT è il/la Issuer di PURCHASEORDER | Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo CLIENT, testo come scritto. |
| DB14_BicycleRental | `Reservation "*" -- "1" Bicycle : Actual Rented bike` | Actual Rented bike | ruolo | Bicycle | Bicycle è il/la Actual Rented bike di Reservation | Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo Bicycle, testo come scritto. |
| DB14_BicycleRental | `Reservation "*" -- "1" BicycleModel : Desired Model` | Desired Model | ruolo | BicycleModel | BicycleModel è il/la Desired Model di Reservation | Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo BicycleModel, testo come scritto. |
| DB16_OOBank | `OrganizationalUnit -- "*" Employee : worksFor` | worksFor | associazione | — | — | Verbo al centro della linea. |
| DB16_OOBank | `Employee -- "*" Customer : personalBanker` | personalBanker | ruolo | Employee | Employee è il/la personalBanker di Customer | Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo Employee, testo come scritto. |
| DB16_OOBank | `Customer "1..2" -- "*" Account : accountHolder` | accountHolder | ruolo | Customer | Customer è il/la accountHolder di Account | Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo Customer, testo come scritto. |
| DB18_LibrarySystem | `User "1" -- "1..4" Book : borrow` | borrow | associazione | — | — | Verbo al centro della linea. |

## Totali
- Etichette originali nel PlantUML sorgente: 203 (1 delle quali, TileOGame `connections/tiles`, sdoppiata in 2 righe di ruolo distinte — 204 righe totali in tabella)
- associazione: 74
- ruolo: 109
- vincolo: 21
- qualificatore: 0
- dubbio: 0
