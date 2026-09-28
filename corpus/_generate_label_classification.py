"""
Script una tantum per generare corpus/label_classification.md (FASE 2, 2026-09-25).
Non fa parte della pipeline permanente (non e' referenziato da altri moduli): la
classificazione va poi congelata in corpus/label_classification.json dopo la
conferma dell'utente, e quel file, non questo script, sara' letto dal convertitore
per instradare le etichette "ruolo".

Ogni riga: (esercizio, relazione, testo_etichetta, classificazione, estremo
proposto, lettura, motivazione). classificazione in {associazione, ruolo, vincolo,
qualificatore, dubbio}.
- "vincolo": testo come "{total; disjoint}" non e' un'etichetta di relazione, e' un
  vincolo UML su un insieme di generalizzazione — dal 2026-09-25 estratto
  automaticamente da corpus/apollon_convert.py::extract_generalization_constraints
  nel campo "constraints" di corpus.jsonl, mai lasciato nell'edge (decisione utente,
  STOP 1).
- "qualificatore": (BuildingManagement id/username, decisione utente STOP 1) un
  nome che nel diagramma UML originale e' verosimilmente un "qualifier" (attributo
  che discrimina l'accesso lungo l'associazione, es. WebPortal[id] -> Entry) — un
  costrutto UML che Apollon non supporta affatto (nessun campo dedicato nello
  schema/nell'editor). Restano in "label" per mancanza di un posto migliore dove
  metterli, non perche' siano un nome di associazione vero e proprio.
- "ruolo" ha una colonna aggiuntiva "lettura": una frase
  "<Classe dell'estremo scelto> e' il/la <ruolo> di <altra classe>", per permettere
  la verifica dell'estremo scelto senza dover rileggere ogni riga PlantUML.
- "ruolo_doppio" (caso unico, TileOGame "connections/tiles", decisione utente
  2026-09-27): un'etichetta puo', in casi eccezionali, impacchettare DUE nomi di
  ruolo distinti (uno per estremo) invece di uno solo. Il formato lo rappresenta
  come lista di sotto-assegnazioni {testo, estremo}, invece di forzare un singolo
  (estremo, testo) come per "ruolo" — non e' una regola generale sul carattere '/',
  e' il dato specifico di questa singola relazione.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import apollon_convert as ac

# (id, source, op, target, label) -> (classificazione, estremo_proposto, motivazione)
CLASSIFICATION = {
    ("AirTravel", "Airport", "--", "Flight", "Source"): (
        "ruolo", "Airport",
        "Nome di ruolo: descrive cosa E' l'Airport per questo Flight (l'aeroporto di "
        "partenza), non un verbo che lega le due classi. Coppia con 'Destination' "
        "sotto: due relazioni distinte Airport-Flight, distinte dal ruolo "
        "dell'Airport in ciascuna."
    ),
    ("AirTravel", "Airport", "--", "Flight", "Destination"): (
        "ruolo", "Airport",
        "Come 'Source' sopra, ma per l'aeroporto di arrivo."
    ),
    ("AirTravel", "FlightExecution", "-", "Pilot", "Captain"): (
        "ruolo", "Pilot",
        "Nome di ruolo esplicitamente dato come esempio dall'utente: descrive cosa "
        "E' il Pilot in questa relazione (il comandante), non un verbo."
    ),
    ("AirTravel", "FlightExecution", "-", "Pilot", "Co-pilot"): (
        "ruolo", "Pilot",
        "Come 'Captain' sopra, per il secondo pilota."
    ),
    ("Boeing", "Airplane", "--", "Acquisition", "part of"): (
        "associazione", None,
        "Frase verbale che descrive il legame ('e' parte di'), leggibile come frase "
        "sull'intera relazione, non un nome che qualifica una delle due classi."
    ),
    ("Boeing", "Acquisition", "--", "Contract", "part of"): (
        "associazione", None, "Come sopra."
    ),
    ("BuildingManagement", "WebPortal", "-->", "Entry", "id"): (
        "qualificatore", None,
        "Decisione utente (STOP 1): verosimilmente un qualificatore UML "
        "(WebPortal[id] -> Entry), non un nome di associazione ne' di ruolo. "
        "Apollon non supporta i qualificatori (nessun campo dedicato in schema o "
        "editor): resta in 'label' per mancanza di un posto migliore, segnalato qui "
        "e in docs/decisions.md come limite noto del formato."
    ),
    ("BuildingManagement", "WebPortal", "-->", "User", "username"): (
        "qualificatore", None, "Come 'id' sopra."
    ),
    ("BuildingManagement", "User", "-->", "Building", "owner"): (
        "ruolo", "User",
        "Nome di ruolo esplicitamente dato come esempio dall'utente: descrive cosa "
        "E' lo User per quel Building."
    ),
    ("BuildingManagement", "User", "-->", "Building", "author"): (
        "ruolo", "User",
        "Come 'owner': relazione distinta (Building ha sia un owner sia un author, "
        "entrambi User ma ruoli diversi)."
    ),
    ("BuildingManagement", "Building", "-->", "Image", "profilePicture"): (
        "ruolo", "Image",
        "Descrive cosa E' l'Image per quel Building (la sua immagine profilo)."
    ),
    ("ClothingCompany", "Product", "--", "Order", "contains"): ("associazione", None, "Verbo che descrive il legame."),
    ("ClothingCompany", "Category", "--", "Product", "belongsTo"): ("associazione", None, "Verbo (forma passiva)."),
    ("ClothingCompany", "Representative", "--", "Order", "placedBy"): ("associazione", None, "Verbo (forma passiva)."),
    ("ClothingCompany", "Product", "--", "Country", "soldIn"): ("associazione", None, "Verbo."),
    ("ClothingCompany", "Representative", "-", "Country", "responsibleFor"): (
        "associazione", None,
        "Frase verbale ('e' responsabile di'), leggibile come frase sull'intera "
        "relazione. Confermato dall'utente (STOP 1) nonostante il confine con "
        "l'esempio di ruolo 'responsible': qui e' un verbo composto "
        "('responsible-FOR'), non il nome nudo di un ruolo."
    ),
    ("ClothingCompany", "Order", "-", "Customer", "orders"): ("associazione", None, "Verbo."),
    ("ClothingCompany", "Country", "--", "Customer", "resell"): ("associazione", None, "Verbo."),
    ("DestroyBlockGame", "Game", "*--", "Block", "blocks"): (
        "ruolo", "Block", "Il testo coincide col nome della classe target (plurale): nomina la collezione di Block dal punto di vista di Game."
    ),
    ("DestroyBlockGame", "Game", "*--", "Paddle", "paddle"): ("ruolo", "Paddle", "Coincide col nome della classe target."),
    ("DestroyBlockGame", "Game", "*--", "Ball", "ball"): ("ruolo", "Ball", "Coincide col nome della classe target."),
    ("DestroyBlockGame", "Game", "*--", "Level", "levels"): ("ruolo", "Level", "Coincide col nome della classe target (plurale)."),
    ("DestroyBlockGame", "Game", "*--", "BlockAssignment", "blockAssignments"): (
        "ruolo", "BlockAssignment", "Coincide col nome della classe target (plurale, camelCase)."
    ),
    ("DestroyBlockGame", "Game", "-->", "HallOfFameEntry", "mostRecentEntry"): (
        "ruolo", "HallOfFameEntry", "Descrive cosa E' quella HallOfFameEntry per Game (la piu' recente)."
    ),
    ("DestroyBlockGame", "Game", "--", "PlayedGame", "game"): (
        "ruolo", "Game",
        "Il testo coincide col nome della classe SOURCE, non del target: si legge "
        "'PlayedGame.game -> il Game di riferimento', quindi il ruolo qualifica "
        "l'estremo Game (il lato source di questa riga), non PlayedGame."
    ),
    ("DestroyBlockGame", "Level", "--", "BlockAssignment", "level"): (
        "ruolo", "Level",
        "Coincide col nome della classe source: 'BlockAssignment.level -> il Level'."
    ),
    ("DestroyBlockGame", "PlayedGame", "*--", "PlayedBlockAssignment", "blocks"): (
        "ruolo", "PlayedBlockAssignment", "Collezione di PlayedBlockAssignment vista da PlayedGame (target)."
    ),
    ("DestroyBlockGame", "Player", "--", "User", "player"): (
        "ruolo", "Player",
        "Coincide col nome della classe source: 'User.player -> il Player legato a quell'account'."
    ),
    ("DestroyBlockGame", "Player", "--", "PlayedGame", "player"): (
        "ruolo", "Player", "Come sopra: 'PlayedGame.player -> il Player che ha giocato'."
    ),
    ("DestroyBlockGame", "Player", "--", "HallOfFameEntry", "player"): (
        "ruolo", "Player", "Come sopra: 'HallOfFameEntry.player -> il Player'."
    ),
    ("DestroyBlockGame", "Admin", "--", "User", "admin"): (
        "ruolo", "Admin", "Coincide col nome della classe source: 'User.admin -> l'Admin'."
    ),
    ("DestroyBlockGame", "Admin", "--", "Game", "admin"): (
        "ruolo", "Admin", "Come sopra: 'Game.admin -> l'Admin che lo amministra'."
    ),
    ("DestroyBlockGame", "Block", "--", "PlayedBlockAssignment", "block"): (
        "ruolo", "Block", "Coincide col nome della classe source: 'PlayedBlockAssignment.block -> il Block'."
    ),
    ("Ebike", "EBike", "-->", "Wheel", "wheel"): ("ruolo", "Wheel", "Coincide col nome della classe target."),
    ("Ebike", "EBike", "-->", "Battery", "battery"): ("ruolo", "Battery", "Coincide col nome della classe target."),
    ("Ebike", "EBike", "-->", "Frame", "frame"): ("ruolo", "Frame", "Coincide col nome della classe target."),
    ("Ebike", "EBike", "-->", "DriveSystem", "driveSystem"): ("ruolo", "DriveSystem", "Coincide col nome della classe target."),
    ("Ebike", "EBike", "-->", "Controller", "controller"): ("ruolo", "Controller", "Coincide col nome della classe target."),
    ("Ebike", "DriveSystem", "-->", "Motor", "motor"): ("ruolo", "Motor", "Coincide col nome della classe target."),
    ("Ebike", "Controller", "-->", "Battery", "battery"): ("ruolo", "Battery", "Coincide col nome della classe target."),
    ("Ebike", "Controller", "-->", "State", "currentState"): ("ruolo", "State", "Descrive cosa E' quello State (lo stato corrente)."),
    ("eHome2020", "Sensor", "-->", "Measurement", "lastValue"): (
        "ruolo", "Measurement", "Descrive cosa E' quella Measurement (l'ultimo valore)."
    ),
    ("EUScienceConnect", "TechnicalReport", "--|>", "Article", "{total; disjoint}"): (
        "vincolo", None,
        "Non e' un'etichetta di associazione: e' un vincolo UML standard "
        "({disjoint,complete} in notazione OCL/UML) su un insieme di "
        "generalizzazione, catturato genericamente dal parser come ': label' "
        "perche' segue la stessa sintassi testuale. Va gestito come vincolo, non "
        "spostato in label ne' in un ruolo."
    ),
    ("EUScienceConnect", "ResearchInstitution", "--", "Person", "worksFor"): ("associazione", None, "Verbo."),
    ("EUScienceConnect", "Person", "--", "PeerReviewedPaper", "reviews"): ("associazione", None, "Verbo."),
    ("EUScienceConnect", "ResearchInstitution", "--", "Journal", "subscribesTo"): ("associazione", None, "Verbo."),
    ("EUScienceConnect", "Publisher", "--", "Journal", "publishes"): ("associazione", None, "Verbo."),
    ("EUScienceConnect", "ResearchInstitution", "--", "TechnicalReport", "publishes"): ("associazione", None, "Verbo."),
    ("Facepage", "PersonalAccount", "--", "PersonalPage", "administrator"): (
        "ruolo", "PersonalAccount", "Descrive cosa E' il PersonalAccount per quella Page (chi la amministra)."
    ),
    ("Facepage", "FriendRequest", "-", "PersonalAccount", "sender"): (
        "ruolo", "PersonalAccount",
        "Nome di ruolo esplicitamente dato come esempio dall'utente."
    ),
    ("Facepage", "FriendRequest", "-", "PersonalAccount", "receiver"): (
        "ruolo", "PersonalAccount", "Come 'sender', relazione distinta (destinatario invece che mittente)."
    ),
    ("FilmSet", "Director", "--", "Screenplay", "implements"): ("associazione", None, "Verbo."),
    ("FilmSet", "Actor", "--", "Screenplay", "reads"): ("associazione", None, "Verbo."),
    ("FilmSet", "Film", "--", "ScreenplayAuthor", "MostSuccessful"): (
        "ruolo", "Film",
        "CORRETTO (2026-09-28, revisione utente di roles_to_review.md): l'estremo "
        "giusto e' Film, non ScreenplayAuthor. description.md: 'The name and most "
        "successful film of a screenwriter are stored' — e' il FILM ad essere 'il "
        "piu' di successo' (di quello screenwriter), non l'autore ad essere "
        "'il piu' di successo'. Lettura corretta: 'Film e' il MostSuccessful di "
        "ScreenplayAuthor'."
    ),
    ("FilmSet", "ScreenplayAuthor", "--", "Screenplay", "creates"): ("associazione", None, "Verbo."),
    ("FitnessCompanyConan", "Session", "<|--", "GroupSession", "{total; disjoint}"): (
        "vincolo", None, "Vincolo UML su generalizzazione, come EUScienceConnect sopra."
    ),
    ("FitnessCompanyConan", "Person", "<|--", "Member", "{partial; overlap}"): (
        "vincolo", None, "Vincolo UML su generalizzazione."
    ),
    ("GameArea", "Shape", "--", "Shape", "is_connected_with"): ("associazione", None, "Verbo (auto-relazione)."),
    ("GameArea", "GameArea", "-->", "Enemy", "finalBoss"): (
        "ruolo", "Enemy", "Descrive cosa E' quel Enemy per quella GameArea."
    ),
    ("HelpingHands", "Volunteer", "*->", "Date", "availableDates"): (
        "ruolo", "Date", "Descrive cosa sono quelle Date per quel Volunteer (le date disponibili)."
    ),
    ("HelpingHands", "Route", "-", "Item", "pickupRoute"): (
        "ruolo", "Route", "Coincide (parzialmente) col nome della classe source: 'Item.pickupRoute -> la Route'."
    ),
    ("HelpingHands", "Route", "--", "SecondHandArticle", "dropOffRoute"): (
        "ruolo", "Route", "Come sopra, relazione distinta (route di consegna anziche' di ritiro)."
    ),
    ("HotelBookingManagementSystem", "SpecialOffer", "--", "BookingInfo", "specialOffers"): (
        "ruolo", "SpecialOffer", "Coincide col nome della classe source (plurale)."
    ),
    ("HotelBookingManagementSystem", "BookingInfo", "--", "SpecialOffer", "bestOffers"): (
        "ruolo", "SpecialOffer", "Coincide (parzialmente) col nome della classe target: le offerte migliori."
    ),
    ("Louvre", "Employee", "--", "Exhibition", "Coordinator"): (
        "ruolo", "Employee", "Descrive cosa E' quell'Employee per quella Exhibition."
    ),
    ("Louvre", "Exhibition", "--", "Location", "AssignedLocation"): (
        "ruolo", "Location", "Coincide (parzialmente) col nome della classe target."
    ),
    ("Louvre", "Location", "--", "Room", "RoomLocationAssignment"): (
        "associazione", None,
        "Decisione utente (2026-09-27): nome dell'associazione (non un ruolo di una "
        "delle due classi), nonostante concateni entrambi i nomi di classe. Resta in "
        "'label'."
    ),
    ("Louvre", "Employee", "--", "Employee", "hasCoach >"): (
        "associazione", None,
        "Frase verbale ('ha un coach'); il simbolo finale '>' e' un marcatore di "
        "verso di lettura di PlantUML, non parte del testo semantico."
    ),
    ("Musicmatic", "Song", "<|--", "Hit", "{total; disjoint}"): ("vincolo", None, "Vincolo UML su generalizzazione."),
    ("Musicmatic", "BusinessUser", "--|>", "User", "{total; overlap}"): ("vincolo", None, "Vincolo UML su generalizzazione."),
    ("Musicmatic", "RegularUser", "--", "Album", "compose"): ("associazione", None, "Verbo."),
    ("Musicmatic", "RegularUser", "--", "Album", "suggestion"): (
        "ruolo", "Album",
        "Decisione utente (2026-09-27): descrive cosa E' quell'Album per l'altro "
        "RegularUser (un suggerimento), coerente con description.md ('the album of "
        "regular users can be turned into a suggestion to other regular users'). "
        "Nota per il report: 'Album' e' una classe implicita in questo esercizio — "
        "mai dichiarata con 'class Album {...}' nel plantuml.txt sorgente, creata "
        "come nodo senza attributi (dichiarazione implicita legale in PlantUML, "
        "vedi warning gia' emesso da apollon_convert.py)."
    ),
    ("OnlineTutoringSystem", "User", "*--", "TutoringRole", "roles"): (
        "ruolo", "TutoringRole", "Coincide col nome della classe target (plurale)."
    ),
    ("OnlineTutoringSystem", "TutoringRequest", "*--", "TutoringSession", "allSessions"): (
        "ruolo", "TutoringSession", "Coincide (parzialmente) col nome della classe target."
    ),
    ("OnlineTutoringSystem", "TutoringSession", "-->", "TutoringSession", "nextSession"): (
        "ruolo", "target",
        "Auto-relazione (decisione utente 2026-09-28): il nome della classe non "
        "puo' disambiguare quale delle due occorrenze porta il ruolo — 'estremo' e' "
        "quindi la POSIZIONE letterale nella riga PlantUML ('target' = lato destro "
        "della riga sorgente), non un nome di classe. Descrive il ruolo del "
        "target (la sessione successiva)."
    ),
    ("OnlineTutoringSystem", "TutoringRequest", "-->", "TutoringSession", "firstSession"): (
        "ruolo", "TutoringSession", "Descrive il ruolo del target (la prima sessione)."
    ),
    ("School", "Teacher", "-", "School", "Principal"): (
        "ruolo", "Teacher", "Descrive cosa E' quel Teacher per quella School (il preside)."
    ),
    ("SmartHomeAutomationSystem", "SmartHome", "*--", "Address", "address"): ("ruolo", "Address", "Coincide col nome della classe target."),
    ("SmartHomeAutomationSystem", "SmartHome", "*--", "Room", "rooms"): ("ruolo", "Room", "Coincide col nome della classe target (plurale)."),
    ("SmartHomeAutomationSystem", "SmartHome", "*--", "ActivityLog", "log"): ("ruolo", "ActivityLog", "Coincide (parzialmente) col nome della classe target."),
    ("SmartHomeAutomationSystem", "User", "--", "SmartHome", "owners"): (
        "ruolo", "User", "Coincide col nome-concetto della classe source (plurale): gli User che possiedono la casa."
    ),
    ("SmartHomeAutomationSystem", "Room", "*--", "Sensor", "sensors"): ("ruolo", "Sensor", "Coincide col nome della classe target (plurale)."),
    ("SmartHomeAutomationSystem", "Room", "*--", "Actuator", "actuators"): ("ruolo", "Actuator", "Coincide col nome della classe target (plurale)."),
    ("SmartHomeAutomationSystem", "ActivityLog", "*--", "SensorReading", "recordedReadings"): (
        "ruolo", "SensorReading", "Coincide (parzialmente) col nome della classe target."
    ),
    ("SmartHomeAutomationSystem", "ActivityLog", "*--", "ControlCommand", "recordedCommands"): (
        "ruolo", "ControlCommand", "Coincide (parzialmente) col nome della classe target."
    ),
    ("SmartHomeAutomationSystem", "CommandSequence", "--", "CommandSequence", "nextCommand"): (
        "ruolo", "target",
        "Auto-relazione (decisione utente 2026-09-28): 'estremo' e' la posizione "
        "letterale ('target' = lato destro della riga sorgente), non un nome di "
        "classe — vedi nota su OnlineTutoringSystem/nextSession. Descrive il ruolo "
        "del target (il comando successivo)."
    ),
    ("SmartHomeAutomationSystem", "CommandSequence", "*--", "ControlCommand", "command"): (
        "ruolo", "ControlCommand", "Coincide (parzialmente) col nome della classe target."
    ),
    ("SmartHomeAutomationSystem", "SensorReading", "--", "Sensor", "sensor"): ("ruolo", "Sensor", "Coincide col nome della classe target."),
    ("SmartHomeAutomationSystem", "ControlCommand", "--", "Actuator", "actuator"): ("ruolo", "Actuator", "Coincide col nome della classe target."),
    ("SmartHomeAutomationSystem", "AlertRule", "*--", "BooleanExpression", "precondition"): (
        "ruolo", "BooleanExpression", "Descrive cosa E' quella Expression per quella AlertRule."
    ),
    ("SmartHomeAutomationSystem", "AlertRule", "*--", "CommandSequence", "actions"): (
        "ruolo", "CommandSequence", "Descrive cosa sono quelle CommandSequence per quella AlertRule."
    ),
    ("SmartHomeAutomationSystem", "NotExpression", "--", "BooleanExpression", "expression"): (
        "ruolo", "BooleanExpression", "Coincide col nome-concetto della classe target."
    ),
    ("SmartHomeAutomationSystem", "BinaryExpression", "--", "BooleanExpression", "leftExpr"): (
        "ruolo", "BooleanExpression", "Qualifica QUALE operando (sinistro) tra due relazioni identiche altrimenti."
    ),
    ("SmartHomeAutomationSystem", "BinaryExpression", "--", "BooleanExpression", "rightExpr"): (
        "ruolo", "BooleanExpression", "Come sopra, operando destro."
    ),
    ("Sober", "Ride", "<|--", "RideHailing", "{total; disjoint}"): ("vincolo", None, "Vincolo UML su generalizzazione."),
    ("Sober", "RideHailing", "--", "Customer", "LeadCustomer"): (
        "ruolo", "Customer", "Descrive cosa E' quel Customer per quella corsa (il cliente principale)."
    ),
    ("Sober", "RideSharing", "--", "Customer", "Book"): (
        "associazione", None,
        "Decisione utente (2026-09-27): verbo ('prenotare'), coerente con "
        "description.md ('a customer who books 20 uses of the Sober ride-sharing "
        "service'). Testo invariato in 'label'."
    ),
    ("Sober", "Ride", "-", "Car", "OperatedBy"): ("associazione", None, "Frase verbale passiva."),
    ("Sober", "Car", "<|--", "SoberCar", "{total; disjoint}"): ("vincolo", None, "Vincolo UML su generalizzazione."),
    ("Sober", "OtherCar", "--", "Customer", "Owns"): ("associazione", None, "Verbo."),
    ("TeamSportsScoutingSystem", "ScoutReport", "<-->", "ScoutReport", "nextReport"): (
        "ruolo", "target",
        "Auto-relazione (decisione utente 2026-09-28): 'estremo' e' la posizione "
        "letterale ('target' = lato destro della riga sorgente), non un nome di "
        "classe — vedi nota su OnlineTutoringSystem/nextSession. Descrive il ruolo "
        "del target (il report successivo)."
    ),
    ("TileOGame", "TileO", "*--", "Game", "games"): ("ruolo", "Game", "Coincide col nome della classe target (plurale)."),
    ("TileOGame", "Game", "*--", "Tile", "tiles"): ("ruolo", "Tile", "Coincide col nome della classe target (plurale)."),
    ("TileOGame", "Game", "*--", "Connection", "connections"): ("ruolo", "Connection", "Coincide col nome della classe target (plurale)."),
    ("TileOGame", "Game", "*--", "Die", "die"): ("ruolo", "Die", "Coincide col nome della classe target."),
    ("TileOGame", "Game", "*-", "Deck", "deck"): ("ruolo", "Deck", "Coincide col nome della classe target."),
    ("TileOGame", "Game", "-->", "Player", "currentPlayer"): ("ruolo", "Player", "Descrive cosa E' quel Player per quel Game (il giocatore corrente)."),
    ("TileOGame", "Game", "*--", "Player", "players"): ("ruolo", "Player", "Coincide col nome della classe target (plurale)."),
    ("TileOGame", "Deck", "*--", "ActionCard", "cards"): ("ruolo", "ActionCard", "Coincide (genericamente) col concetto della classe target."),
    ("TileOGame", "Game", "-->", "WinTile", "winTile"): ("ruolo", "WinTile", "Coincide col nome della classe target."),
    ("TileOGame", "Tile", "--", "Connection", "connections/tiles"): (
        "ruolo_doppio",
        [
            {"testo": "tiles", "estremo": "Tile"},
            {"testo": "connections", "estremo": "Connection"},
        ],
        "Decisione utente (2026-09-27): caso unico nel corpus — l'etichetta "
        "impacchetta due nomi di ruolo distinti, uno per estremo, invece di uno "
        "solo. 'tiles' coincide col nome della classe Tile, 'connections' col "
        "nome della classe Connection — stessa convenzione gia' usata altrove "
        "(es. 'Game *-- Tile : tiles' e 'Game *-- Connection : connections', righe "
        "69-70 dello stesso file). Label vuoto: non e' un'etichetta di "
        "associazione, sono due ruoli."
    ),
    ("TileOGame", "Player", "-->", "Tile", "startingTile"): ("ruolo", "Tile", "Descrive cosa E' quel Tile per quel Player (la casella di partenza)."),
    ("TileOGame", "Player", "-->", "Tile", "currentTile"): ("ruolo", "Tile", "Descrive cosa E' quel Tile per quel Player (la casella corrente)."),
    ("TileOGame", "Deck", "-->", "ActionCard", "currentCard"): ("ruolo", "ActionCard", "Descrive cosa E' quella ActionCard per quel Deck (la carta corrente)."),
    ("TransportCompany", "Planner", "--", "Order", "creates"): ("associazione", None, "Verbo."),
    ("TruckLogistics", "Assignment", "-->", "Driver", "executes"): ("associazione", None, "Verbo."),
    ("TruckLogistics", "Assignment", "-->", "Location", "from"): (
        "ruolo", "Location", "Nome di ruolo classico (preposizione sostantivata): l'origine."
    ),
    ("TruckLogistics", "Assignment", "-->", "Location", "to"): (
        "ruolo", "Location", "Come 'from': la destinazione (relazione distinta)."
    ),
    ("TruckLogistics", "Driver", "-->", "Vehicle", "driver"): (
        "ruolo", "Driver", "Coincide col nome della classe source: 'Vehicle.driver -> il Driver che lo guida'."
    ),
    ("TruckLogistics", "Vehicle", "-->", "Driver", "driver"): (
        "ruolo", "Driver", "Coincide col nome della classe target in questa riga (relazione inversa rispetto alla precedente)."
    ),
    ("TruckLogistics", "Vehicle", "-->", "VehicleStatus", "status"): (
        "ruolo", "VehicleStatus", "Coincide (parzialmente) col nome della classe target."
    ),
    ("University", "Employee", "--", "Faculty", "leads >"): (
        "associazione", None, "Frase verbale ('guida'); '>' e' un marcatore di verso di lettura di PlantUML."
    ),
    ("University", "Lecturer", "--", "Course", "teaches >"): (
        "associazione", None, "Frase verbale ('insegna'); '>' e' un marcatore di verso di lettura."
    ),
    ("CourseManagement", "Course", "--", "Teacher", "Preallocation"): (
        "associazione", None, "Nome di associazione (sostantivo che descrive il legame nel suo complesso), non un ruolo di una delle due classi."
    ),
    ("CourseManagement", "Teacher", "--", "Lesson", "Allocation"): (
        "associazione", None, "Come 'Preallocation': nome dell'associazione."
    ),
    ("CourseManagement", "Course", "--", "Participant", "Enrolled"): (
        "associazione", None, "Come 'Preallocation'/'Allocation' nello stesso esercizio: nome dell'associazione, non un ruolo."
    ),
}


def resolve_endpoint_name(estremo: str, src: str, tgt: str) -> str:
    """'estremo' e' di norma un nome di classe; per le auto-relazioni (dove il nome
    non basta a disambiguare le due occorrenze) e' invece la posizione letterale
    'source'/'target' nella riga PlantUML originale. Ritorna sempre il nome di
    classe effettivo, per la visualizzazione in label_classification.md."""
    if estremo in ("source", "target"):
        return src if estremo == "source" else tgt
    return estremo


def resolve_position(estremo: str, src: str, tgt: str) -> str:
    """Inverso di resolve_endpoint_name: da 'estremo' (nome di classe o gia'
    posizione) alla posizione 'source'/'target' — quella che il convertitore usa
    davvero per scegliere source_role vs target_role sulla relazione PARSATA (prima
    dello scambio di relationship_kind)."""
    if estremo in ("source", "target"):
        return estremo
    if estremo == src:
        return "source"
    if estremo == tgt:
        return "target"
    raise ValueError(f"estremo {estremo!r} non corrisponde ne' a source={src!r} ne' a target={tgt!r}")


def lettura_ruolo(estremo: str, role_text: str, src: str, tgt: str) -> str:
    endpoint_name = resolve_endpoint_name(estremo, src, tgt)
    altra_classe = tgt if endpoint_name == src else src
    return f"{endpoint_name} è il/la {role_text} di {altra_classe}"


def main() -> None:
    corpus = [json.loads(l) for l in open("corpus/processed/corpus.jsonl", encoding="utf-8")]
    rows = []
    for rec in corpus:
        if not rec.get("diagram_plantuml"):
            continue
        classes, rels, warn, unsup = ac.parse_plantuml(rec["diagram_plantuml"])
        if unsup:
            continue
        for r in rels:
            if r["kind"] == "binary" and r["label"]:
                rows.append((rec["id"], r["source"], r["op"], r["target"], r["label"], r["raw"]))

    missing = [row for row in rows if row[:5] not in CLASSIFICATION]
    if missing:
        print(f"ATTENZIONE: {len(missing)} righe non classificate:")
        for row in missing:
            print(" ", row)
        raise SystemExit(1)

    md_lines = [
        "# Classificazione delle etichette — associazione, ruolo o vincolo",
        "",
        f"Generata da `corpus/_generate_label_classification.py` da tutte le "
        f"{len(rows)} etichette non vuote (`: testo`) trovate nelle relazioni binarie "
        "dei 45 esercizi convertibili (44 originali + CourseManagement).",
        "",
        "Categorie: **associazione** (verbo/descrizione del legame, resta in "
        "`label`), **ruolo** (nome di come si chiama una classe in quella "
        "relazione, va in `sourceRole`/`targetRole` sull'estremo indicato — "
        "colonna \"Lettura\" per verificare l'estremo), **vincolo** (testo di "
        "vincolo UML su una generalizzazione, es. `{disjoint,complete}` — non "
        "e' un'etichetta di relazione: dal 2026-09-25 estratto automaticamente "
        "nel campo `constraints` di corpus.jsonl, mai lasciato nell'edge, vedi "
        "`corpus/apollon_convert.py::extract_generalization_constraints`), "
        "**qualificatore** (verosimilmente un qualifier UML che Apollon non "
        "supporta — resta in `label` per mancanza di un posto migliore), "
        "**ruolo_doppio** (caso unico, TileOGame: un'etichetta con DUE nomi di "
        "ruolo distinti, uno per estremo — espansa in due righe qui sotto), "
        "**dubbio** (nessuna classificazione proposta, in attesa dell'utente).",
        "",
        "| Esercizio | Relazione (sorgente) | Etichetta | Classificazione | Estremo proposto | Lettura | Motivazione |",
        "|---|---|---|---|---|---|---|",
    ]
    counts = {"associazione": 0, "ruolo": 0, "vincolo": 0, "qualificatore": 0, "ruolo_doppio_righe": 0, "dubbio": 0}
    n_labels_originali = len(rows)
    json_entries = []

    for row in rows:
        eid, src, op, tgt, label, raw = row
        classification, endpoint_or_list, motivation = CLASSIFICATION[row[:5]]
        raw_escaped = raw.replace("|", "\\|")
        entry = {"esercizio": eid, "source": src, "op": op, "target": tgt, "label": label, "tipo": classification}

        if classification == "ruolo_doppio":
            entry["ruoli"] = [
                {"estremo": resolve_position(sub["estremo"], src, tgt), "testo": sub["testo"]}
                for sub in endpoint_or_list
            ]
            for sub in endpoint_or_list:
                counts["ruolo"] += 1
                counts["ruolo_doppio_righe"] += 1
                lettura = lettura_ruolo(sub["estremo"], sub["testo"], src, tgt)
                md_lines.append(
                    f"| {eid} | `{raw_escaped}` | {sub['testo']} (da '{label}') | ruolo | "
                    f"{resolve_endpoint_name(sub['estremo'], src, tgt)} | {lettura} | {motivation} |"
                )
        else:
            counts[classification] += 1
            if classification == "ruolo":
                entry["estremo"] = resolve_position(endpoint_or_list, src, tgt)
                entry["testo"] = label
                endpoint_str = resolve_endpoint_name(endpoint_or_list, src, tgt)
                lettura = lettura_ruolo(endpoint_or_list, label, src, tgt)
            else:
                endpoint_str, lettura = "—", "—"
            md_lines.append(
                f"| {eid} | `{raw_escaped}` | {label} | {classification} | {endpoint_str} | {lettura} | {motivation} |"
            )

        json_entries.append(entry)

    md_lines.append("")
    md_lines.append("## Totali")
    md_lines.append(
        f"- Etichette originali nel PlantUML sorgente: {n_labels_originali} "
        f"(1 delle quali, TileOGame `connections/tiles`, sdoppiata in 2 righe di "
        f"ruolo distinte — {n_labels_originali - 1 + counts['ruolo_doppio_righe']} righe totali in tabella)"
    )
    for k in ("associazione", "ruolo", "vincolo", "qualificatore", "dubbio"):
        md_lines.append(f"- {k}: {counts[k]}")

    md_path = Path("corpus/label_classification.md")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Scritto: {md_path}")
    print(counts)

    json_path = Path("corpus/label_classification.json")
    json_path.write_text(json.dumps(json_entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scritto: {json_path} ({len(json_entries)} voci)")


if __name__ == "__main__":
    main()
