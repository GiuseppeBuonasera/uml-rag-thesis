# Controllo test set De Bari contro Analysis.xlsx

Generato da `corpus/check_debari.py` (non modificare a mano).

## DB01_ProjectManagementSystem

Conteggi ground truth: {'classes': 6, 'attributes_operations': 17, 'associations': 7} — xlsx: {'classes': 6, 'attributes_operations': 17, 'associations': 7}; ED medio 2.3333

Nessuna discrepanza.


## DB02_HollywoodApproach

Conteggi ground truth: {'classes': 6, 'attributes_operations': 12, 'associations': 5} — xlsx: {'classes': 6, 'attributes_operations': 35, 'associations': 5}; ED medio 1.3333

- relazione solo nell'xlsx: association(externals - location) — **imprecisione_xlsx**: l'xlsx scrive 'Externals'; nell'immagine la classe e' 'External' (riquadro in basso al centro).
- relazione solo nell'xlsx: generalization(extenal - scene) — **imprecisione_xlsx**: refuso 'Extenal' nell'xlsx; nell'immagine External --|> Scene.
- relazione solo nel ground truth: association(external - location) — **imprecisione_xlsx**: stessa relazione External-Location 'located', scritta 'Externals' nell'xlsx.
- relazione solo nel ground truth: generalization(external - scene) — **imprecisione_xlsx**: stessa generalizzazione, scritta 'Extenal' nell'xlsx.
- conteggio Attributes + Operations: xlsx 35, ground truth 12 — **imprecisione_xlsx**: valori scambiati tra le righe 2 e 3 di "Estimated Difficulty": la formula '=12+23' dell'es. 2 e' il conteggio dell'es. 3 (12 attributi + 23 operazioni, verificato sul PlantUML), mentre l'es. 2 ha 12 attributi e 0 operazioni (immagine: 6 classi senza operazioni).

## DB03_WordProcessor

Conteggi ground truth: {'classes': 7, 'attributes_operations': 35, 'associations': 8} — xlsx: {'classes': 7, 'attributes_operations': 12, 'associations': 8}; ED medio 4.6667

- membro solo nel ground truth: cell.edit — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: character.bold — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: character.italic — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: character.normal — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: character.underline — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: page.hidefooter — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: page.hideheader — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: page.insertpicture — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: page.inserttable — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: page.newpage — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: picture.delete — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: picture.insert — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: table.insertcolumn — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: table.insertpicture — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: table.insertrow — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: table.newtable — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: trimming.change — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: trimming.display — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- membro solo nel ground truth: trimming.hide — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca le operazioni solo per Document; nell'immagine tutte le classi hanno il comparto operazioni con '+nome()' leggibile (es. Cell: +edit()).
- conteggio Attributes + Operations: xlsx 12, ground truth 35 — **imprecisione_xlsx**: valori scambiati con l'es. 2 in "Estimated Difficulty" (vedi DB02): 12 e' il conteggio dell'es. 2; l'es. 3 ha 12 attributi + 23 operazioni = 35.

## DB04_PatientRecordAndSchedulingSystem

Conteggi ground truth: {'classes': 6, 'attributes_operations': 31, 'associations': 7} — xlsx: {'classes': 6, 'attributes_operations': 31, 'associations': 7}; ED medio 3.3333

Nessuna discrepanza.


## DB05_MovieShop

Conteggi ground truth: {'classes': 11, 'attributes_operations': 18, 'associations': 11} — xlsx: {'classes': 8, 'attributes_operations': 18, 'associations': 11}; ED medio 2.3333

- classe solo nel ground truth: moviebuystatus — **convenzione**: enumerazione separata creata dalla convenzione approvata 'enum inline -> <Classe><Attributo>' (corrections/DB05_MovieShop.yaml); nell'immagine e' l'enum inline di Movie.type.
- classe solo nel ground truth: movierentstatus — **convenzione**: enumerazione separata creata dalla convenzione approvata 'enum inline -> <Classe><Attributo>' (corrections/DB05_MovieShop.yaml); nell'immagine e' l'enum inline di Movie.type.
- classe solo nel ground truth: movietype — **convenzione**: enumerazione separata creata dalla convenzione approvata 'enum inline -> <Classe><Attributo>' (corrections/DB05_MovieShop.yaml); nell'immagine e' l'enum inline di Movie.type.
- membro solo nell'xlsx: moviebuy.pricesell — **imprecisione_xlsx**: l'immagine scrive '+prezzo-vendita' (Movie-Buy, 2a riga), tradotto fedelmente 'sellingPrice'; l'xlsx scrive 'Price-Sell' (calco della parola composta).
- membro solo nell'xlsx: movierent.date — **imprecisione_xlsx**: l'immagine scrive '+data prestito' (Movie-Rent, 2a riga), tradotto fedelmente 'loanDate' (glossary.json, decisione utente 2026-10-03); l'xlsx semplifica in 'date'.
- membro solo nel ground truth: moviebuy.sellingprice — **imprecisione_xlsx**: vedi moviebuy.pricesell.
- membro solo nel ground truth: movierent.loandate — **imprecisione_xlsx**: vedi movierent.date.
- conteggio Classes: xlsx 8, ground truth 11 — **convenzione**: le 8 classi dell'immagine piu' le 3 enumerazioni create dalla convenzione enum inline.

## DB06_Flights

Conteggi ground truth: {'classes': 9, 'attributes_operations': 12, 'associations': 13} — xlsx: {'classes': 9, 'attributes_operations': 12, 'associations': 12}; ED medio 3.6667

- conteggio Associations: xlsx 12, ground truth 13 — **imprecisione_xlsx**: la Given Solution dell'xlsx elenca essa stessa 13 relazioni (10 associazioni + 3 generalizzazioni, con Aircraft Type - Pilot due volte: Navigator of / Copilot of), come l'immagine; il conteggio di "Estimated Difficulty" dice 12.

## DB07_BankSystem

Conteggi ground truth: {'classes': 6, 'attributes_operations': 7, 'associations': 5} — xlsx: {'classes': 6, 'attributes_operations': 5, 'associations': 7}; ED medio 1.0

- conteggio Attributes + Operations: xlsx 5, ground truth 7 — **imprecisione_xlsx**: l'immagine ha 7 attributi (Customer 2, Account 1, SavingAccount 1, Stock 2, StockOrder 1), tutti elencati anche nella Given Solution dell'xlsx; il conteggio di "Estimated Difficulty" dice 5.
- conteggio Associations: xlsx 7, ground truth 5 — **imprecisione_xlsx**: l'immagine ha 5 relazioni (3 associazioni + 2 generalizzazioni), le stesse 5 della Given Solution dell'xlsx; il conteggio di "Estimated Difficulty" dice 7.

## DB08_VeterinaryClinic

Conteggi ground truth: {'classes': 7, 'attributes_operations': 11, 'associations': 8} — xlsx: {'classes': 7, 'attributes_operations': 11, 'associations': 8}; ED medio 2.0

Nessuna discrepanza.


## DB09_AutoRepair

Conteggi ground truth: {'classes': 9, 'attributes_operations': 13, 'associations': 10} — xlsx: {'classes': 9, 'attributes_operations': 13, 'associations': 10}; ED medio 2.6667

Nessuna discrepanza.


## DB10_Restaurant

Conteggi ground truth: {'classes': 9, 'attributes_operations': 17, 'associations': 9} — xlsx: {'classes': 7, 'attributes_operations': 15, 'associations': 7}; ED medio 2.6667

- classe solo nel ground truth: dishmeal — **imprecisione_xlsx**: l'immagine ha due classi associative senza nome (riquadri con intestazione vuota collegati da linea tratteggiata: 'Quantity' su INGREDIENT-DISH, 'Times_Served' su DISH-Meal), nominate per concatenazione (convenzione approvata); la Given Solution dell'xlsx non le elenca, ne' i loro attributi.
- classe solo nel ground truth: ingredientdish — **imprecisione_xlsx**: l'immagine ha due classi associative senza nome (riquadri con intestazione vuota collegati da linea tratteggiata: 'Quantity' su INGREDIENT-DISH, 'Times_Served' su DISH-Meal), nominate per concatenazione (convenzione approvata); la Given Solution dell'xlsx non le elenca, ne' i loro attributi.
- membro solo nel ground truth: dishmeal.timesserved — **imprecisione_xlsx**: l'immagine ha due classi associative senza nome (riquadri con intestazione vuota collegati da linea tratteggiata: 'Quantity' su INGREDIENT-DISH, 'Times_Served' su DISH-Meal), nominate per concatenazione (convenzione approvata); la Given Solution dell'xlsx non le elenca, ne' i loro attributi.
- membro solo nel ground truth: ingredientdish.quantity — **imprecisione_xlsx**: l'immagine ha due classi associative senza nome (riquadri con intestazione vuota collegati da linea tratteggiata: 'Quantity' su INGREDIENT-DISH, 'Times_Served' su DISH-Meal), nominate per concatenazione (convenzione approvata); la Given Solution dell'xlsx non le elenca, ne' i loro attributi.
- relazione solo nel ground truth: association_class(dish - ingredient) — **imprecisione_xlsx**: l'immagine ha due classi associative senza nome (riquadri con intestazione vuota collegati da linea tratteggiata: 'Quantity' su INGREDIENT-DISH, 'Times_Served' su DISH-Meal), nominate per concatenazione (convenzione approvata); la Given Solution dell'xlsx non le elenca, ne' i loro attributi.
- relazione solo nel ground truth: association_class(dish - meal) — **imprecisione_xlsx**: l'immagine ha due classi associative senza nome (riquadri con intestazione vuota collegati da linea tratteggiata: 'Quantity' su INGREDIENT-DISH, 'Times_Served' su DISH-Meal), nominate per concatenazione (convenzione approvata); la Given Solution dell'xlsx non le elenca, ne' i loro attributi.
- conteggio Classes: xlsx 7, ground truth 9 — **imprecisione_xlsx**: l'immagine ha due classi associative senza nome (riquadri con intestazione vuota collegati da linea tratteggiata: 'Quantity' su INGREDIENT-DISH, 'Times_Served' su DISH-Meal), nominate per concatenazione (convenzione approvata); la Given Solution dell'xlsx non le elenca, ne' i loro attributi.
- conteggio Attributes + Operations: xlsx 15, ground truth 17 — **imprecisione_xlsx**: l'immagine ha due classi associative senza nome (riquadri con intestazione vuota collegati da linea tratteggiata: 'Quantity' su INGREDIENT-DISH, 'Times_Served' su DISH-Meal), nominate per concatenazione (convenzione approvata); la Given Solution dell'xlsx non le elenca, ne' i loro attributi.
- conteggio Associations: xlsx 7, ground truth 9 — **convenzione**: il ground truth conta come relazione anche il collegamento della classe associativa ((A, B) .. C); l'xlsx conta solo le generalizzazioni e le associazioni della Given Solution (es. 11: 9 = 2 + 7). Differenza di metodo di conteggio, non di contenuto.

## DB11_Deliveries

Conteggi ground truth: {'classes': 6, 'attributes_operations': 11, 'associations': 10} — xlsx: {'classes': 6, 'attributes_operations': 11, 'associations': 9}; ED medio 3.3333

- classe solo nel ground truth: packagedeliverycenter — **imprecisione_xlsx**: classe associativa senza nome (riquadro con intestazione vuota e linea tratteggiata sulla seconda linea Package-DeliveryCenter, attributi DateTimeArrival / DateTimeDeparture), nominata per concatenazione; la Given Solution non la elenca (i conteggi di "Estimated Difficulty", 6 classi e 11 attributi, invece la includono).
- membro solo nel ground truth: packagedeliverycenter.datetimearrival — **imprecisione_xlsx**: classe associativa senza nome (riquadro con intestazione vuota e linea tratteggiata sulla seconda linea Package-DeliveryCenter, attributi DateTimeArrival / DateTimeDeparture), nominata per concatenazione; la Given Solution non la elenca (i conteggi di "Estimated Difficulty", 6 classi e 11 attributi, invece la includono).
- membro solo nel ground truth: packagedeliverycenter.datetimedeparture — **imprecisione_xlsx**: classe associativa senza nome (riquadro con intestazione vuota e linea tratteggiata sulla seconda linea Package-DeliveryCenter, attributi DateTimeArrival / DateTimeDeparture), nominata per concatenazione; la Given Solution non la elenca (i conteggi di "Estimated Difficulty", 6 classi e 11 attributi, invece la includono).
- relazione solo nel ground truth: association_class(deliverycenter - package) — **imprecisione_xlsx**: classe associativa senza nome (riquadro con intestazione vuota e linea tratteggiata sulla seconda linea Package-DeliveryCenter, attributi DateTimeArrival / DateTimeDeparture), nominata per concatenazione; la Given Solution non la elenca (i conteggi di "Estimated Difficulty", 6 classi e 11 attributi, invece la includono).
- conteggio Associations: xlsx 9, ground truth 10 — **convenzione**: il ground truth conta come relazione anche il collegamento della classe associativa ((A, B) .. C); l'xlsx conta solo le generalizzazioni e le associazioni della Given Solution (es. 11: 9 = 2 + 7). Differenza di metodo di conteggio, non di contenuto.

## DB12_Furniture

Conteggi ground truth: {'classes': 8, 'attributes_operations': 13, 'associations': 7} — xlsx: {'classes': 6, 'attributes_operations': 11, 'associations': 5}; ED medio 2.3333

- classe solo nel ground truth: piececomponent — **imprecisione_xlsx**: due classi associative senza nome (riquadri con intestazione vuota, 'Quantity', linee tratteggiate su Piece-Component e Piece-Order), nominate per concatenazione; la Given Solution e i conteggi dell'xlsx non le includono.
- classe solo nel ground truth: pieceorder — **imprecisione_xlsx**: due classi associative senza nome (riquadri con intestazione vuota, 'Quantity', linee tratteggiate su Piece-Component e Piece-Order), nominate per concatenazione; la Given Solution e i conteggi dell'xlsx non le includono.
- membro solo nel ground truth: piececomponent.quantity — **imprecisione_xlsx**: due classi associative senza nome (riquadri con intestazione vuota, 'Quantity', linee tratteggiate su Piece-Component e Piece-Order), nominate per concatenazione; la Given Solution e i conteggi dell'xlsx non le includono.
- membro solo nel ground truth: pieceorder.quantity — **imprecisione_xlsx**: due classi associative senza nome (riquadri con intestazione vuota, 'Quantity', linee tratteggiate su Piece-Component e Piece-Order), nominate per concatenazione; la Given Solution e i conteggi dell'xlsx non le includono.
- relazione solo nel ground truth: association_class(component - piece) — **imprecisione_xlsx**: due classi associative senza nome (riquadri con intestazione vuota, 'Quantity', linee tratteggiate su Piece-Component e Piece-Order), nominate per concatenazione; la Given Solution e i conteggi dell'xlsx non le includono.
- relazione solo nel ground truth: association_class(order - piece) — **imprecisione_xlsx**: due classi associative senza nome (riquadri con intestazione vuota, 'Quantity', linee tratteggiate su Piece-Component e Piece-Order), nominate per concatenazione; la Given Solution e i conteggi dell'xlsx non le includono.
- conteggio Classes: xlsx 6, ground truth 8 — **imprecisione_xlsx**: due classi associative senza nome (riquadri con intestazione vuota, 'Quantity', linee tratteggiate su Piece-Component e Piece-Order), nominate per concatenazione; la Given Solution e i conteggi dell'xlsx non le includono.
- conteggio Attributes + Operations: xlsx 11, ground truth 13 — **imprecisione_xlsx**: due classi associative senza nome (riquadri con intestazione vuota, 'Quantity', linee tratteggiate su Piece-Component e Piece-Order), nominate per concatenazione; la Given Solution e i conteggi dell'xlsx non le includono.
- conteggio Associations: xlsx 5, ground truth 7 — **convenzione**: il ground truth conta come relazione anche il collegamento della classe associativa ((A, B) .. C); l'xlsx conta solo le generalizzazioni e le associazioni della Given Solution (es. 11: 9 = 2 + 7). Differenza di metodo di conteggio, non di contenuto.

## DB13_Factory

Conteggi ground truth: {'classes': 9, 'attributes_operations': 20, 'associations': 9} — xlsx: {'classes': 8, 'attributes_operations': 19, 'associations': 8}; ED medio 1.6667

- classe solo nel ground truth: productpurchaseorder — **imprecisione_xlsx**: classe associativa senza nome ('Quantity', linea tratteggiata su PRODUCT-PURCHASE ORDER), nominata per concatenazione; la Given Solution e i conteggi dell'xlsx non la includono.
- membro solo nel ground truth: productpurchaseorder.quantity — **imprecisione_xlsx**: classe associativa senza nome ('Quantity', linea tratteggiata su PRODUCT-PURCHASE ORDER), nominata per concatenazione; la Given Solution e i conteggi dell'xlsx non la includono.
- relazione solo nel ground truth: association_class(product - purchaseorder) — **imprecisione_xlsx**: classe associativa senza nome ('Quantity', linea tratteggiata su PRODUCT-PURCHASE ORDER), nominata per concatenazione; la Given Solution e i conteggi dell'xlsx non la includono.
- conteggio Classes: xlsx 8, ground truth 9 — **imprecisione_xlsx**: classe associativa senza nome ('Quantity', linea tratteggiata su PRODUCT-PURCHASE ORDER), nominata per concatenazione; la Given Solution e i conteggi dell'xlsx non la includono.
- conteggio Attributes + Operations: xlsx 19, ground truth 20 — **imprecisione_xlsx**: classe associativa senza nome ('Quantity', linea tratteggiata su PRODUCT-PURCHASE ORDER), nominata per concatenazione; la Given Solution e i conteggi dell'xlsx non la includono.
- conteggio Associations: xlsx 8, ground truth 9 — **convenzione**: il ground truth conta come relazione anche il collegamento della classe associativa ((A, B) .. C); l'xlsx conta solo le generalizzazioni e le associazioni della Given Solution (es. 11: 9 = 2 + 7). Differenza di metodo di conteggio, non di contenuto.

## DB14_BicycleRental

Conteggi ground truth: {'classes': 5, 'attributes_operations': 12, 'associations': 5} — xlsx: {'classes': 5, 'attributes_operations': 12, 'associations': 5}; ED medio 2.6667

- relazione solo nell'xlsx: association(bicycle - byciclemodel) — **imprecisione_xlsx**: refuso 'BycicleModel' nell'xlsx; nell'immagine la classe e' BicycleModel.
- relazione solo nel ground truth: association(bicycle - bicyclemodel) — **imprecisione_xlsx**: stessa relazione Bicycle-BicycleModel, scritta 'BycicleModel' nell'xlsx.

## DB15_SaturnIntManagement

Conteggi ground truth: {'classes': 8, 'attributes_operations': 6, 'associations': 8} — xlsx: {'classes': 8, 'attributes_operations': 6, 'associations': 8}; ED medio 4.3333

Nessuna discrepanza.


## DB16_OOBank

Conteggi ground truth: {'classes': 11, 'attributes_operations': 13, 'associations': 14} — xlsx: {'classes': 11, 'attributes_operations': 13, 'associations': 13}; ED medio 3.0

- classe solo nell'xlsx: subdivision — **imprecisione_xlsx**: nell'immagine 'subdivision' e' il nome di ruolo dell'auto-associazione di OrganizationalUnit (estremo '*', altro estremo '0..1'), SENZA rombo (verificato con ingrandimento 3x); l'xlsx ne fa una classe 'Subdivision' in composizione con OrganizationalUnit. Per questo i conteggi dell'xlsx per l'es. 16 non coincidono con il ground truth.
- relazione solo nell'xlsx: composition(organizationalunit - subdivision) — **imprecisione_xlsx**: nell'immagine 'subdivision' e' il nome di ruolo dell'auto-associazione di OrganizationalUnit (estremo '*', altro estremo '0..1'), SENZA rombo (verificato con ingrandimento 3x); l'xlsx ne fa una classe 'Subdivision' in composizione con OrganizationalUnit. Per questo i conteggi dell'xlsx per l'es. 16 non coincidono con il ground truth.
- relazione solo nel ground truth: association(organizationalunit) — **imprecisione_xlsx**: nell'immagine 'subdivision' e' il nome di ruolo dell'auto-associazione di OrganizationalUnit (estremo '*', altro estremo '0..1'), SENZA rombo (verificato con ingrandimento 3x); l'xlsx ne fa una classe 'Subdivision' in composizione con OrganizationalUnit. Per questo i conteggi dell'xlsx per l'es. 16 non coincidono con il ground truth.
- conteggio Associations: xlsx 13, ground truth 14 — **imprecisione_xlsx**: l'immagine ha 14 relazioni (8 associazioni, inclusa l'auto-associazione, + 6 generalizzazioni) e la Given Solution dell'xlsx ne elenca anch'essa 14; il conteggio di "Estimated Difficulty" dice 13.

## DB17_PrepaidCellPhone

Conteggi ground truth: {'classes': 8, 'attributes_operations': 5, 'associations': 6} — xlsx: {'classes': 8, 'attributes_operations': 5, 'associations': 8}; ED medio 2.3333

- relazione solo nell'xlsx: generalization(doubletransfer - option) — **imprecisione_xlsx**: nell'immagine i riquadri Phone e Double Transfer (in basso a destra) NON sono collegati a nessuna classe: solo Data e SMS hanno la linea verso Option. L'xlsx aggiunge le due generalizzazioni mancanti (lettura del testo, non del diagramma); il ground truth trascrive l'immagine.
- relazione solo nell'xlsx: generalization(option - phone) — **imprecisione_xlsx**: nell'immagine i riquadri Phone e Double Transfer (in basso a destra) NON sono collegati a nessuna classe: solo Data e SMS hanno la linea verso Option. L'xlsx aggiunge le due generalizzazioni mancanti (lettura del testo, non del diagramma); il ground truth trascrive l'immagine.
- conteggio Associations: xlsx 8, ground truth 6 — **imprecisione_xlsx**: nell'immagine i riquadri Phone e Double Transfer (in basso a destra) NON sono collegati a nessuna classe: solo Data e SMS hanno la linea verso Option. L'xlsx aggiunge le due generalizzazioni mancanti (lettura del testo, non del diagramma); il ground truth trascrive l'immagine.

## DB18_LibrarySystem

Conteggi ground truth: {'classes': 6, 'attributes_operations': 10, 'associations': 6} — xlsx: {'classes': 6, 'attributes_operations': 10, 'associations': 6}; ED medio 1.6667

- relazione solo nell'xlsx: dependency(book - borrow) — **imprecisione_xlsx**: nell'immagine Borrow -> Book e' una linea CONTINUA con freccia (associazione navigabile), non tratteggiata; l'xlsx la chiama Dependencies.
- relazione solo nell'xlsx: generalization(adult - user) — **imprecisione_xlsx**: nell'immagine Under_aged e Adult sono collegate a User (<<interface>>) da linee TRATTEGGIATE con triangolo vuoto: realizzazione, non generalizzazione (l'xlsx le chiama Generalization).
- relazione solo nell'xlsx: generalization(underaged - user) — **imprecisione_xlsx**: nell'immagine Under_aged e Adult sono collegate a User (<<interface>>) da linee TRATTEGGIATE con triangolo vuoto: realizzazione, non generalizzazione (l'xlsx le chiama Generalization).
- relazione solo nel ground truth: association(book - borrow) — **imprecisione_xlsx**: nell'immagine Borrow -> Book e' una linea CONTINUA con freccia (associazione navigabile), non tratteggiata; l'xlsx la chiama Dependencies.
- relazione solo nel ground truth: implementation(adult - user) — **imprecisione_xlsx**: nell'immagine Under_aged e Adult sono collegate a User (<<interface>>) da linee TRATTEGGIATE con triangolo vuoto: realizzazione, non generalizzazione (l'xlsx le chiama Generalization).
- relazione solo nel ground truth: implementation(underaged - user) — **imprecisione_xlsx**: nell'immagine Under_aged e Adult sono collegate a User (<<interface>>) da linee TRATTEGGIATE con triangolo vuoto: realizzazione, non generalizzazione (l'xlsx le chiama Generalization).

## DB19_MyDoctor

Conteggi ground truth: {'classes': 9, 'attributes_operations': 20, 'associations': 9} — xlsx: {'classes': 9, 'attributes_operations': 20, 'associations': 9}; ED medio 4.0

- membro solo nell'xlsx: patienti.address — **imprecisione_xlsx**: refuso 'Patienti' nell'xlsx; nell'immagine la classe e' Patient (Age, Address).
- membro solo nell'xlsx: patienti.age — **imprecisione_xlsx**: refuso 'Patienti' nell'xlsx; nell'immagine la classe e' Patient (Age, Address).
- membro solo nel ground truth: patient.address — **imprecisione_xlsx**: refuso 'Patienti' nell'xlsx; nell'immagine la classe e' Patient (Age, Address).
- membro solo nel ground truth: patient.age — **imprecisione_xlsx**: refuso 'Patienti' nell'xlsx; nell'immagine la classe e' Patient (Age, Address).

## DB20_OnlineShopping

Conteggi ground truth: {'classes': 10, 'attributes_operations': 28, 'associations': 10} — xlsx: {'classes': 10, 'attributes_operations': 28, 'associations': 10}; ED medio 4.6667

Nessuna discrepanza.

