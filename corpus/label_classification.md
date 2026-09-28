# Classificazione delle etichette — associazione, ruolo o vincolo

Generata da `corpus/_generate_label_classification.py` da tutte le 126 etichette non vuote (`: testo`) trovate nelle relazioni binarie dei 45 esercizi convertibili (44 originali + CourseManagement).

Categorie: **associazione** (verbo/descrizione del legame, resta in `label`), **ruolo** (nome di come si chiama una classe in quella relazione, va in `sourceRole`/`targetRole` sull'estremo indicato — colonna "Lettura" per verificare l'estremo), **vincolo** (testo di vincolo UML su una generalizzazione, es. `{disjoint,complete}` — non e' un'etichetta di relazione: dal 2026-09-25 estratto automaticamente nel campo `constraints` di corpus.jsonl, mai lasciato nell'edge, vedi `corpus/apollon_convert.py::extract_generalization_constraints`), **qualificatore** (verosimilmente un qualifier UML che Apollon non supporta — resta in `label` per mancanza di un posto migliore), **ruolo_doppio** (caso unico, TileOGame: un'etichetta con DUE nomi di ruolo distinti, uno per estremo — espansa in due righe qui sotto), **dubbio** (nessuna classificazione proposta, in attesa dell'utente).

| Esercizio | Relazione (sorgente) | Etichetta | Classificazione | Estremo proposto | Lettura | Motivazione |
|---|---|---|---|---|---|---|
| AirTravel | `Airport "0..1"--"0..*" Flight : Source` | Source | ruolo | Airport | Airport è il/la Source di Flight | Nome di ruolo: descrive cosa E' l'Airport per questo Flight (l'aeroporto di partenza), non un verbo che lega le due classi. Coppia con 'Destination' sotto: due relazioni distinte Airport-Flight, distinte dal ruolo dell'Airport in ciascuna. |
| AirTravel | `Airport "0..1"--"0..*" Flight : Destination` | Destination | ruolo | Airport | Airport è il/la Destination di Flight | Come 'Source' sopra, ma per l'aeroporto di arrivo. |
| AirTravel | `FlightExecution "0..*"-"0..1" Pilot : Captain` | Captain | ruolo | Pilot | Pilot è il/la Captain di FlightExecution | Nome di ruolo esplicitamente dato come esempio dall'utente: descrive cosa E' il Pilot in questa relazione (il comandante), non un verbo. |
| AirTravel | `FlightExecution "0..*"-"0..2" Pilot : Co-pilot` | Co-pilot | ruolo | Pilot | Pilot è il/la Co-pilot di FlightExecution | Come 'Captain' sopra, per il secondo pilota. |
| Boeing | `Airplane "0..1" -- "0..1" Acquisition : part of` | part of | associazione | — | — | Frase verbale che descrive il legame ('e' parte di'), leggibile come frase sull'intera relazione, non un nome che qualifica una delle due classi. |
| Boeing | `Acquisition "0..*" -- "1" Contract : part of` | part of | associazione | — | — | Come sopra. |
| BuildingManagement | `WebPortal "1" --> "*" Entry : id` | id | qualificatore | — | — | Decisione utente (STOP 1): verosimilmente un qualificatore UML (WebPortal[id] -> Entry), non un nome di associazione ne' di ruolo. Apollon non supporta i qualificatori (nessun campo dedicato in schema o editor): resta in 'label' per mancanza di un posto migliore, segnalato qui e in docs/decisions.md come limite noto del formato. |
| BuildingManagement | `WebPortal "0..1" --> "1" User : username` | username | qualificatore | — | — | Come 'id' sopra. |
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
| HotelBookingManagementSystem | `BookingInfo "0..5" -- "*" SpecialOffer : bestOffers` | bestOffers | ruolo | SpecialOffer | SpecialOffer è il/la bestOffers di BookingInfo | Coincide (parzialmente) col nome della classe target: le offerte migliori. |
| Louvre | `Employee "1" -- "0..*" Exhibition : Coordinator` | Coordinator | ruolo | Employee | Employee è il/la Coordinator di Exhibition | Descrive cosa E' quell'Employee per quella Exhibition. |
| Louvre | `Exhibition "0..*" -- "0..1" Location : AssignedLocation` | AssignedLocation | ruolo | Location | Location è il/la AssignedLocation di Exhibition | Coincide (parzialmente) col nome della classe target. |
| Louvre | `Location "0..*" -- "0..*" Room : RoomLocationAssignment` | RoomLocationAssignment | associazione | — | — | Decisione utente (2026-09-27): nome dell'associazione (non un ruolo di una delle due classi), nonostante concateni entrambi i nomi di classe. Resta in 'label'. |
| Louvre | `Employee "0..*" -- "0..1" Employee : hasCoach >` | hasCoach > | associazione | — | — | Frase verbale ('ha un coach'); il simbolo finale '>' e' un marcatore di verso di lettura di PlantUML, non parte del testo semantico. |
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
| TruckLogistics | `Driver "1..*" --> "*" Vehicle : driver` | driver | ruolo | Driver | Driver è il/la driver di Vehicle | Coincide col nome della classe source: 'Vehicle.driver -> il Driver che lo guida'. |
| TruckLogistics | `Vehicle "0..1" --> "*" Driver : driver` | driver | ruolo | Driver | Driver è il/la driver di Vehicle | Coincide col nome della classe target in questa riga (relazione inversa rispetto alla precedente). |
| TruckLogistics | `Vehicle "1" --> "1" VehicleStatus : status` | status | ruolo | VehicleStatus | VehicleStatus è il/la status di Vehicle | Coincide (parzialmente) col nome della classe target. |
| University | `Employee "1" -- "0..1" Faculty : leads >` | leads > | associazione | — | — | Frase verbale ('guida'); '>' e' un marcatore di verso di lettura di PlantUML. |
| University | `Lecturer "1..*" -- "1..*" Course : teaches >` | teaches > | associazione | — | — | Frase verbale ('insegna'); '>' e' un marcatore di verso di lettura. |
| CourseManagement | `Course "0..*" -- "1..*" Teacher : Preallocation` | Preallocation | associazione | — | — | Nome di associazione (sostantivo che descrive il legame nel suo complesso), non un ruolo di una delle due classi. |
| CourseManagement | `Teacher "1..2" -- "0..*" Lesson : Allocation` | Allocation | associazione | — | — | Come 'Preallocation': nome dell'associazione. |
| CourseManagement | `Course "1..*" -- "1..*" Participant : Enrolled` | Enrolled | associazione | — | — | Come 'Preallocation'/'Allocation' nello stesso esercizio: nome dell'associazione, non un ruolo. |

## Totali
- Etichette originali nel PlantUML sorgente: 126 (1 delle quali, TileOGame `connections/tiles`, sdoppiata in 2 righe di ruolo distinte — 127 righe totali in tabella)
- associazione: 31
- ruolo: 87
- vincolo: 7
- qualificatore: 2
- dubbio: 0
