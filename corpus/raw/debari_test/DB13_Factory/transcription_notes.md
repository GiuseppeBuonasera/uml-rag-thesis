# Note di trascrizione — De Bari 13: Factory

Fonte immagine: `corpus/raw/debari_test/_images/db13.png` (1379x873).

## Ambiguità e interpretazioni
1. **Maiuscolo, tutto invariato** (decisione utente del 2026-10-03): intestazioni tutte in MAIUSCOLO tranne
   `Person`, attributi tutti in MAIUSCOLO tranne `Quantity` della classe associativa. Nessuna categoria è
   INTERAMENTE in maiuscolo, quindi la regola del maiuscolo tipografico non si applica (vale solo alla lettera,
   senza estensioni caso per caso).
2. "PURCHASE ORDER" → `PURCHASEORDER` (regola dei nomi composti); classe associativa senza nome (`Quantity`,
   linea tratteggiata su PRODUCT–PURCHASE ORDER) → `PRODUCTPURCHASEORDER` (concatenazione).
3. **Molteplicità**: WORKER `*` – SKILL `*`; WORKER `*` – MACHINE `*` (linea con gomito); MACHINE `1` –
   PRODUCT_TYPE `*`; PRODUCT_TYPE `1` – PRODUCT `*`; CLIENT `1` – PURCHASE ORDER `*` con "Issuer" in verticale
   lungo la linea (ruolo `Issuer` sull'estremo CLIENT, approvato); PRODUCT `*` – PURCHASE ORDER `*` con la classe
   associativa.
4. Generalizzazione CLIENT, WORKER → Person con `{DISJOINT, COMPLETE}`, trascritto su entrambe.
5. Il testo chiede "a list of his skills" e il nome con first e last name: nel diagramma sono WORKER–SKILL e
   FIRSTNAME/SURNAME su Person. Coerente, nessuna correzione.
6. Attributi senza tipo.

## Analysis.xlsx ("Part 2 - 13")
La Given Solution e i conteggi non includono la classe associativa né il suo attributo.
