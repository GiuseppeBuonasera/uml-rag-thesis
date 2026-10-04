# Note di trascrizione — De Bari 20: Online Shopping

Fonte immagine: `corpus/raw/debari_test/_images/db20.png` (1383x1319).

## Elementi esclusi (non di modello)
- Cornice del diagramma "class Online Shopping" e "© uml-diagrams.org".

## Ambiguità e interpretazioni
1. **Nomi composti** "Web User" → `WebUser`, "Shopping Cart" → `ShoppingCart` (PascalCase per le classi).
2. **Enumerazioni** «enumeration» UserState {New, Active, Blocked, Banned} e OrderStatus {New, Hold, Shipped,
   Delivered, Closed} → `enum`.
3. **`{id}`** sugli attributi (login_id, id, number): modificatore già gestito, scartato dalla stringa
   visualizzata con warning nel record.
4. **`{ordered, unique}` sugli estremi**: Account–Order (lato Order), Payment–Order (lato Payment),
   ShoppingCart–LineItem e Order–LineItem (lato LineItem, insieme al ruolo `line_item`). Trascritto come scritto
   dentro le virgolette dell'estremo; la regola generale approvata il 2026-10-03 (`split_mult_role`) lo toglie dal
   ruolo e lo registra come warning ("scartato vincolo di estremo"), come i {XOR}.
5. **Tipi di dominio** `Address` (Customer, Account, Order), `Phone` (Customer), `Supplier` (Product) → `string`,
   `Price` (LineItem) → `double`: mappature globali (`DOMAIN_TYPE_MAPPING`, approvate il 2026-10-03), solo in
   posizione di tipo; `Real` → double. **`Supplier`** è probabilmente il riferimento a un'entità non disegnata (un
   fornitore): non si crea una classe, perché si inventerebbe una relazione Product–Supplier che nell'immagine non
   c'è.
6. **Composizioni** (rombo pieno sul contenitore): Customer ◆ Account (`1`/`1`), Account ◆ ShoppingCart
   (`1`/`1`), Account ◆ Order (`1` / `*`). Associazioni: WebUser `0..1` – Customer `1`; WebUser `1` – ShoppingCart
   `0..1`; Account `1` – Payment `0..*`; Payment `*` – Order `1`; ShoppingCart `1` – LineItem `*`; Order `1` –
   LineItem `*`; LineItem `*` – Product `1`.
7. Ruolo `line_item` vicino agli estremi LineItem delle due associazioni (sintassi `"molt ruolo"`).

## Analysis.xlsx ("Part 2 - 20")
Nessuna discrepanza (10 / 28 / 10).
