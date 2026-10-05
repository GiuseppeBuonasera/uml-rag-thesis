"""
Genera corpus/label_classification.md e corpus/label_classification.json (nato come script
una tantum nella FASE 2, 2026-09-25; dal test set De Bari e' un passo permanente della
pipeline e legge entrambi gli split; rinominato da _generate_label_classification.py il
2026-10-04). Le voci di CLASSIFICATION si aggiungono solo dopo la conferma dell'utente; il
convertitore legge il json, non questo script.

Ogni riga: (esercizio, relazione, testo_etichetta, classificazione, estremo
proposto, lettura, motivazione). classificazione in {associazione, ruolo, vincolo,
qualificatore, dubbio}.
- "vincolo": testo come "{total; disjoint}" non e' un'etichetta di relazione, e' un
  vincolo UML su un insieme di generalizzazione — dal 2026-09-25 estratto
  automaticamente da corpus/apollon_convert.py::extract_generalization_constraints
  nel campo "constraints" di corpus.jsonl, mai lasciato nell'edge (decisione utente,
  STOP 1).
- "qualificatore": categoria RISERVATA MA ATTUALMENTE INUTILIZZATA (0 voci,
  dal 2026-09-29) — usata fino ad allora per BuildingManagement id/username,
  letti come un "qualifier" UML (attributo che discrimina l'accesso lungo
  l'associazione, es. WebPortal[id] -> Entry). Riclassificati come "ruolo"
  (decisione utente, 2026-09-29): non serviva una lettura UML cosi'
  specifica — "id"/"username" sono semplicemente il nome della proprieta' di
  navigazione, stessa convenzione di "profilePicture"/"wheel", quindi vanno
  in sourceRole/targetRole come ogni altro ruolo. La categoria resta
  documentata (non rimossa dal convertitore) per un futuro caso reale di
  qualifier che non si presti alla stessa lettura.
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
        "ruolo", "target",
        "RICLASSIFICATO (2026-09-29, decisione utente — categoria "
        "'qualificatore' abbandonata, era una lettura UML non necessaria): "
        "'id' non e' un qualificatore, e' il nome della proprieta' di "
        "navigazione (stessa convenzione di 'profilePicture', 'wheel', ecc. "
        "— nomi comuni, non frasi verbali) — targetRole 'id' sull'estremo "
        "Entry, label vuoto. Storico: NON piu' spostato su Building (quella "
        "correzione 'chiarimento_modellazione' e' stata annullata, "
        "BuildingManagement resta fedele all'originale, vedi docs/decisions.md) "
        "— il limite (Entry non ha mai un ID esplicito in description.md, "
        "solo Building) resta annotato ma non corretto."
    ),
    ("BuildingManagement", "WebPortal", "-->", "User", "username"): (
        "ruolo", "target",
        "RICLASSIFICATO (2026-09-29, stessa motivazione di 'id' sopra): "
        "targetRole 'username' sull'estremo User, label vuoto."
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
    ("Louvre", "Employee", "--", "Employee", "hasCoach"): (
        "ruolo", {"estremo": "target", "testo": "coach"},
        "RICLASSIFICATO (2026-09-29, decisione utente): auto-relazione "
        "Employee-Employee — senza un ruolo esplicito i due estremi non si "
        "distinguono. Ruolo 'coach' (il sostantivo, non la frase verbale "
        "'hasCoach' usata come etichetta) sull'estremo con molteplicita' "
        "0..1 (il dipendente che fa da coach, presente 0 o 1 volta), "
        "posizione 'target' nella riga PlantUML (il simbolo finale '>', "
        "gia' rimosso dall'etichetta da "
        "apollon_convert.py::strip_reading_direction, era solo un "
        "marcatore di verso di lettura, non parte del nome)."
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
    ("University", "Employee", "--", "Faculty", "leads"): (
        "associazione", None,
        "Frase verbale ('guida'); il simbolo '>' che seguiva l'etichetta nel "
        "sorgente e' un marcatore di verso di lettura di PlantUML, non parte "
        "del testo — rimosso da apollon_convert.py::strip_reading_direction "
        "(2026-09-29), quindi anche dalla chiave di classificazione qui."
    ),
    ("University", "Lecturer", "--", "Course", "teaches"): (
        "associazione", None,
        "Frase verbale ('insegna'); stessa nota sul marcatore '>' sopra."
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
    # --- Gruppo A traduzione (es. 2-5), proposte APPROVATE dall'utente (2026-09-30), chiavi in inglese ---
    ("ResearchCenter", "Researcher", "--", "Area", "Belongs to"): (
        "associazione", None, "Frase verbale ('appartiene a'), non un nome di ruolo."
    ),
    ("ResearchCenter", "SeniorResearcher", "--", "Team", "Leads"): (
        "associazione", None, "Frase verbale ('guida'); 'Guidato da' sull'altro estremo e' solo la forma passiva, scartata in trascrizione."
    ),
    ("ResearchCenter", "Team", "--", "Project", "Carries out"): (
        "associazione", None, "Frase verbale ('svolge')."
    ),
    ("MilanLibrary", "Library", "--", "ItemTransferRequest", "request destination"): (
        "ruolo", "Library",
        "Approvato dall'utente: ruolo della biblioteca nella richiesta (destinataria), nonostante il testo centrato sulla linea."
    ),
    ("MilanLibrary", "Library", "--", "ItemTransferRequest", "request source"): (
        "ruolo", "Library", "Come 'request destination' (biblioteca mittente)."
    ),
    ("MilanLibrary", "Library", "o--", "User", "Has"): (
        "associazione", None, "Frase verbale ('possiede')."
    ),
    ("Bookmaker", "Bet", "-->", "Race", "race"): (
        "ruolo", "Race", "Nome di campo Java = nome della proprieta' di navigazione (stessa convenzione di profilePicture)."
    ),
    ("Bookmaker", "Bet", "-->", "Runner", "runner"): ("ruolo", "Runner", "Come 'race'."),
    ("Bookmaker", "Race", "-->", "Runner", "winner"): ("ruolo", "Runner", "Come 'race'."),
    ("Bookmaker", "Runner", "-->", "Jockey", "jockey"): ("ruolo", "Jockey", "Come 'race'."),
    ("Bookmaker", "Runner", "-->", "Horse", "horse"): ("ruolo", "Horse", "Come 'race'."),
    # --- Gruppo B traduzione (es. 6-9), APPROVATE dall'utente (2026-09-30): tutte associazione ---
    ("UniversityExams", "Student", "--", "Place", "Student_born_in"): ("associazione", None, "Nome dell'associazione ('nato a'), centrato sulla linea."),
    ("UniversityExams", "Professor", "--", "Place", "Prof_born_in"): ("associazione", None, "Come 'Student_born_in'."),
    ("UniversityExams", "Faculty", "--", "Course", "BelongsTo"): ("associazione", None, "Frase verbale ('< Appartenente'; il '<' e' verso di lettura, rimosso)."),
    ("UniversityExams", "Professor", "--", "Course", "Teaches"): ("associazione", None, "Frase verbale ('< Insegna')."),
    ("Restaurant", "Customer", "--", "Assignment", "books"): ("associazione", None, "Verbo ('prenota')."),
    ("Restaurant", "Assignment", "--", "Table", "includes"): ("associazione", None, "Verbo ('include')."),
    ("Restaurant", "Assignment", "--", "Waiter", "serves"): ("associazione", None, "Verbo ('serve')."),
    ("ElevatorControl", "ElevatorController", "..>", "Elevator", "controls"): ("associazione", None, "Verbo ('controlla'), su dipendenza (tratteggiata: verifica visiva dell'autore 2026-10-01, prima trascritta -->)."),
    ("ElevatorControl", "ElevatorController", "..>", "Door", "controls"): ("associazione", None, "Verbo ('controlla'), su dipendenza."),
    ("ElevatorControl", "ElevatorController", "--", "Button", "communicates"): ("associazione", None, "Verbo ('comunica'), in corsivo al centro della linea."),
    # --- Gruppo C traduzione (es. 10-11), APPROVATE dall'utente (2026-10-01) ---
    ("OilWells", "OnshoreWell", "--|>", "Well", "{disjoint, complete}"): ("vincolo", None, "Vincolo UML sull'insieme di generalizzazione (scritto una volta sul tronco comune)."),
    ("OilWells", "OffshoreWell", "--|>", "Well", "{disjoint, complete}"): ("vincolo", None, "Come sopra."),
    ("OilWells", "OffshoreWell", "--", "Area", "location"): (
        "ruolo", "Area",
        "Decisione utente: 'luogo' e' un sostantivo -> ruolo sull'estremo Area, anche se scritto al centro della linea (la posizione non conta)."
    ),
    ("RepairShops", "RepairShop", "--", "Employee", "WorksAt"): ("associazione", None, "Verbo ('<Lavora'; '<' = verso di lettura)."),
    ("RepairShops", "RepairShop", "--", "Director", "manages"): ("associazione", None, "Verbo ('<dirige')."),
    ("RepairShops", "RepairShop", "--", "Repair", "performs"): ("associazione", None, "Verbo ('effettua>')."),
    ("RepairShops", "Vehicle", "--", "Owner", "belongsTo"): ("associazione", None, "Verbo ('appartiene>')."),
    # --- Gym (es. 12), APPROVATE dall'utente (2026-10-01) ---
    ("Gym", "Subscription", "--", "Service", "AdditionalServices"): ("ruolo", "Service", "Sostantivo ('ServiziAggiuntivi'): regola 'sostantivo = ruolo, la posizione non conta'."),
    ("Gym", "Subscription", "--", "Service", "BaseServices"): ("ruolo", "Service", "Come 'AdditionalServices' ('ServiziBase')."),
    # --- Gruppo D traduzione (es. 13-15), APPROVATE dall'utente (2026-10-01): tutte associazione ---
    ("EatAtHome", "Customer", "--", "Order", "makes"): ("associazione", None, "Verbo ('makes ►', diagramma gia' in inglese)."),
    ("EatAtHome", "Order", "--", "Dish", "contains"): ("associazione", None, "Verbo ('contains ►')."),
    ("EatAtHome", "Dish", "--", "Ingredient", "contains"): ("associazione", None, "Verbo ('contains ►')."),
    ("ApartmentBuilding", "Apartment", "--", "Person", "isOwnedBy"): ("associazione", None, "Verbo ('è posseduto'), al centro della linea."),
    # --- Test set De Bari, Gruppo DB-A (es. 1-5), APPROVATE dall'utente (2026-10-03) ---
    ("DB01_ProjectManagementSystem", "Project", "--", "Requirement", "Input"): (
        "associazione", None,
        "Decisione utente: nome di ASSOCIAZIONE, non ruolo, perche' ha il triangolo pieno del verso di "
        "lettura (◄), che i nomi di ruolo non hanno (anche se 'Input' e' anche un sostantivo)."
    ),
    ("DB01_ProjectManagementSystem", "Project", "--", "System", "Output"): ("associazione", None, "Come 'Input': triangolo pieno di verso di lettura (►), quindi nome di associazione."),
    ("DB01_ProjectManagementSystem", "Manager", "--", "Project", "Manage"): ("associazione", None, "Verbo con triangolo pieno di verso di lettura (►)."),
    ("DB01_ProjectManagementSystem", "Team", "--", "Project", "Execute"): ("associazione", None, "Verbo con triangolo pieno di verso di lettura (◄)."),
    ("DB01_ProjectManagementSystem", "Manager", "--", "Team", "Lead"): ("associazione", None, "Verbo al centro della linea."),
    ("DB02_HollywoodApproach", "Take", "--", "Setup", "tk_of_stp"): ("associazione", None, "Nome di relazione al centro della linea ('take of setup')."),
    ("DB02_HollywoodApproach", "Scene", "--", "Setup", "stp_for_scn"): ("associazione", None, "Nome di relazione al centro della linea ('setup for scene')."),
    ("DB02_HollywoodApproach", "External", "--", "Location", "located"): ("associazione", None, "Verbo (participio) al centro della linea."),
    ("DB02_HollywoodApproach", "Internal", "--|>", "Scene", "{complete, disjoint}"): ("vincolo", None, "Vincolo UML sull'insieme di generalizzazione Internal/External."),
    ("DB02_HollywoodApproach", "External", "--|>", "Scene", "{complete, disjoint}"): ("vincolo", None, "Come sopra."),
    ("DB04_PatientRecordAndSchedulingSystem", "FamilyInsured", "--", "Doctor", "hasPrimaryCare"): ("associazione", None, "Verbo."),
    ("DB05_MovieShop", "User", "-->", "MovieShop", "uses"): ("associazione", None, "Verbo."),
    ("DB05_MovieShop", "MovieShop", "--", "Card", "make"): ("associazione", None, "Verbo."),
    ("DB05_MovieShop", "MovieShop", "-->", "Order", "make"): ("associazione", None, "Verbo."),
    ("DB05_MovieShop", "Subscriber", "-->", "Card", "has"): ("associazione", None, "Verbo."),
    ("DB05_MovieShop", "Order", "--", "MovieBuy", "related to"): ("associazione", None, "Verbo."),
    ("DB05_MovieShop", "Subscriber", "-->", "MovieRent", "hire"): ("associazione", None, "Verbo."),
    # --- Test set De Bari, Gruppo DB-B (es. 6-10), APPROVATE dall'utente (2026-10-03) ---
    ("DB06_Flights", "Airline", "--", "Flight", "offers"): ("associazione", None, "Verbo."),
    ("DB06_Flights", "Airline", "--", "Aircraft", "owns"): ("associazione", None, "Verbo."),
    ("DB06_Flights", "Flight", "--", "Airport", "arrives to"): ("associazione", None, "Verbo."),
    ("DB06_Flights", "Flight", "--", "Airport", "departs from"): ("associazione", None, "Verbo."),
    ("DB06_Flights", "Aircraft", "--", "Flight", "uses"): ("associazione", None, "Verbo."),
    ("DB06_Flights", "Flight", "--", "Pilot", "Driven by"): ("associazione", None, "Verbo (passivo)."),
    ("DB06_Flights", "Aircraft", "--", "AircraftType", "is of"): ("associazione", None, "Verbo."),
    ("DB06_Flights", "AircraftType", "--", "Pilot", "Navigator of"): ("ruolo", {"estremo": "Pilot", "testo": "Navigator"}, "Decisione utente (2026-10-03): 'X of' = sostantivo + preposizione, senza triangolo di verso di lettura -> RUOLO sull'estremo Pilot, testo = il sostantivo con la maiuscola come scritto (precedente Louvre hasCoach -> coach)."),
    ("DB06_Flights", "AircraftType", "--", "Pilot", "Copilot of"): ("ruolo", {"estremo": "Pilot", "testo": "Copilot"}, "Decisione utente (2026-10-03): 'X of' = sostantivo + preposizione, senza triangolo di verso di lettura -> RUOLO sull'estremo Pilot, testo = il sostantivo con la maiuscola come scritto (precedente Louvre hasCoach -> coach)."),
    ("DB06_Flights", "AircraftType", "--", "Pilot3", "Captain of"): ("ruolo", {"estremo": "Pilot3", "testo": "Captain"}, "Decisione utente (2026-10-03): 'X of' = sostantivo + preposizione, senza triangolo di verso di lettura -> RUOLO sull'estremo Pilot3, testo = il sostantivo con la maiuscola come scritto (precedente Louvre hasCoach -> coach)."),
    ("DB08_VeterinaryClinic", "Owner", "--|>", "Person", "{DISJOINT, COMPLETE}"): ("vincolo", None, "Vincolo sull'insieme di generalizzazione."),
    ("DB08_VeterinaryClinic", "Physician", "--|>", "Person", "{DISJOINT, COMPLETE}"): ("vincolo", None, "Come sopra."),
    ("DB09_AutoRepair", "Employee", "--|>", "Person", "{Disjoint, Complete}"): ("vincolo", None, "Vincolo sull'insieme di generalizzazione (scritto a mano; classi dopo la correzione 'maiuscolo tipografico')."),
    ("DB09_AutoRepair", "Owner", "--|>", "Person", "{Disjoint, Complete}"): ("vincolo", None, "Come sopra."),
    ("DB10_Restaurant", "Client", "--|>", "Person", "{OVERLAPPING, COMPLETE}"): ("vincolo", None, "Vincolo sull'insieme di generalizzazione."),
    ("DB10_Restaurant", "Waiter", "--|>", "Person", "{OVERLAPPING, COMPLETE}"): ("vincolo", None, "Come sopra."),
    # --- Test set De Bari, Gruppo DB-C (es. 11-15), APPROVATE dall'utente (2026-10-03) ---
    ("DB11_Deliveries", "CUSTOMER", "--|>", "Person", "{DISJOINT, COMPLETE}"): ("vincolo", None, "Vincolo sull'insieme di generalizzazione."),
    ("DB11_Deliveries", "COURIER", "--|>", "Person", "{DISJOINT, COMPLETE}"): ("vincolo", None, "Come sopra."),
    ("DB11_Deliveries", "CUSTOMER", "--", "Package", "Sender"): ("ruolo", {"estremo": "CUSTOMER", "testo": "Sender"}, "Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo CUSTOMER, testo come scritto."),
    ("DB11_Deliveries", "CUSTOMER", "--", "Package", "Recipient"): ("ruolo", {"estremo": "CUSTOMER", "testo": "Recipient"}, "Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo CUSTOMER, testo come scritto."),
    ("DB11_Deliveries", "Package", "--", "DeliveryCenter", "Dropoff point"): ("ruolo", {"estremo": "DeliveryCenter", "testo": "Dropoff point"}, "Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo DeliveryCenter, testo come scritto."),
    ("DB13_Factory", "CLIENT", "--|>", "Person", "{DISJOINT, COMPLETE}"): ("vincolo", None, "Vincolo sull'insieme di generalizzazione."),
    ("DB13_Factory", "WORKER", "--|>", "Person", "{DISJOINT, COMPLETE}"): ("vincolo", None, "Come sopra."),
    ("DB13_Factory", "CLIENT", "--", "PURCHASEORDER", "Issuer"): ("ruolo", {"estremo": "CLIENT", "testo": "Issuer"}, "Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo CLIENT, testo come scritto."),
    ("DB14_BicycleRental", "Reservation", "--", "Bicycle", "Actual Rented bike"): ("ruolo", {"estremo": "Bicycle", "testo": "Actual Rented bike"}, "Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo Bicycle, testo come scritto."),
    ("DB14_BicycleRental", "Reservation", "--", "BicycleModel", "Desired Model"): ("ruolo", {"estremo": "BicycleModel", "testo": "Desired Model"}, "Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo BicycleModel, testo come scritto."),
    # --- Test set De Bari, Gruppo DB-D (es. 16-20), APPROVATE dall'utente (2026-10-03) ---
    ("DB16_OOBank", "OrganizationalUnit", "--", "Employee", "worksFor"): ("associazione", None, "Verbo al centro della linea."),
    ("DB16_OOBank", "Employee", "--", "Customer", "personalBanker"): ("ruolo", {"estremo": "Employee", "testo": "personalBanker"}, "Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo Employee, testo come scritto."),
    ("DB16_OOBank", "Customer", "--", "Account", "accountHolder"): ("ruolo", {"estremo": "Customer", "testo": "accountHolder"}, "Decisione utente (2026-10-03): sostantivo senza triangolo -> RUOLO sull'estremo Customer, testo come scritto."),
    ("DB18_LibrarySystem", "User", "--", "Book", "borrow"): ("associazione", None, "Verbo al centro della linea."),
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
    # test set De Bari (2026-10-03): stesse regole di classificazione, stesso file json
    # (gli id DBNN_ non collidono con il corpus, vedi build_manifest.check_split_separation)
    debari_path = Path("corpus/processed/testset_debari.jsonl")
    if debari_path.exists():
        corpus += [json.loads(l) for l in debari_path.read_text(encoding="utf-8").splitlines() if l.strip()]
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
        f"Generata da `corpus/generate_label_classification.py` da tutte le "
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
                # normalmente il testo del ruolo e' l'etichetta stessa (endpoint_or_list
                # e' solo l'estremo, una stringa); un dict {"estremo","testo"} permette
                # un testo diverso dall'etichetta originale — caso Louvre 'hasCoach' ->
                # ruolo 'coach' (2026-09-29): il nome del ruolo e' il sostantivo, non la
                # frase verbale usata come etichetta della relazione.
                if isinstance(endpoint_or_list, dict):
                    estremo_raw, ruolo_testo = endpoint_or_list["estremo"], endpoint_or_list["testo"]
                else:
                    estremo_raw, ruolo_testo = endpoint_or_list, label
                entry["estremo"] = resolve_position(estremo_raw, src, tgt)
                entry["testo"] = ruolo_testo
                endpoint_str = resolve_endpoint_name(estremo_raw, src, tgt)
                lettura = lettura_ruolo(estremo_raw, ruolo_testo, src, tgt)
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
