# Note di trascrizione — De Bari 10: Restaurant

Fonte immagine: `corpus/raw/debari_test/_images/db10.png` (1383x909). Ingrandimento 0.85x di
x 60-1340 / y 60-600.

## Ambiguità e interpretazioni
1. **Classi associative senza nome** (riquadri con intestazione vuota, linea tratteggiata verso la linea di
   associazione): convenzione approvata "concatenazione delle due classi collegate", nell'ordine della
   relazione: `INGREDIENTDISH` {Quantity} su INGREDIENT–DISH, `DISHMeal` {Times_Served} su DISH–Meal in
   `plantuml.txt`, poi `IngredientDish` / `DishMeal` con le correzioni del punto 2.
2. **Maiuscolo tipografico, solo classi** (eccezione approvata il 2026-10-03): diagramma a grafia mista. Le
   intestazioni INGREDIENT, DISH, TABLE sono maiuscolo tipografico e vengono portate a Ingredient, Dish, Table
   (correzioni `corpus/corrections/DB10_Restaurant.yaml`, "maiuscolo tipografico"; `plantuml.txt` resta
   fedele). Gli attributi restano come scritti, perché la categoria è a grafia mista (`Name`/`Unit`/`Stock`
   accanto a `NAME`/`STARTTIME`/`TAX_ID`).
3. **Molteplicità**: INGREDIENT `1..*` – DISH `*`; DISH `*` – Meal `*`; Meal `*` – TABLE `1`; Meal `*` – Client
   `0..1`; Meal `*` – Waiter `1`.
4. **Generalizzazione** Client, Waiter → Person con vincolo `{OVERLAPPING, COMPLETE}` sotto il tronco
   comune: trascritto su entrambe.
5. Attributi senza tipo. Nessuna etichetta né ruolo.

## Analysis.xlsx ("Part 2 - 10")
La Given Solution non elenca le due classi associative senza nome né i loro attributi (Quantity,
Times_Served): da qui tutte le discrepanze (classi 7 vs 9, attributi 15 vs 17, relazioni 7 vs 9).
