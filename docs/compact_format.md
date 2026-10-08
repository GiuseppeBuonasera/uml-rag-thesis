# Formato JSON compatto dei diagrammi delle classi — specifica

Approvata allo STOP 1 (2026-10-08, voce 90 di `docs/decisions.md`), con le chiavi di verso per ruolo.

Terzo formato di uscita del modello, accanto a PlantUML e all'Apollon completo. **Apollon v4 resta il formato di
consegna**: il compatto si espande in Apollon completo con l'espansore unico (`generation/uml_structure.py`), lo
stesso del percorso PlantUML, che genera id deterministici, layout e punti.

Codice: `uml_structure.to_compact` / `read_compact` / `from_compact` (struttura comune <-> compatto),
`apollon_to_compact` (esempi del prompt), `compact_to_apollon` (compatto -> Apollon). Post-processing delle risposte:
`generation/compact_postprocess.py`. Controllo: `python generation/compact_sanity_check.py`.

## Regole

- Un oggetto con due chiavi: `"classes"` (obbligatoria) e `"relations"` (lista, eventualmente vuota o assente).
  Nessun'altra chiave: **niente** `version`, `id`, `title`, `type`, `assessments`, `interactive`, posizioni, dimensioni,
  handle, punti, id di attributi / metodi / relazioni.
- **L'id di una classe è il suo nome**: i nomi delle classi sono unici; le relazioni si riferiscono alle classi per nome.
- Le chiavi vuote si omettono (stringhe vuote, liste vuote); `"kind"` si omette quando vale `"class"`. Le chiavi vuote
  presenti sono comunque accettate.
- Ordine: l'ordine delle classi e delle relazioni è quello dell'Apollon (l'espansore lo usa per layout e id).

### Classe

| chiave | valore |
|---|---|
| `name` | nome della classe (una parola, PascalCase come nel corpus) |
| `kind` | `"class"` (default, omesso), `"abstract"`, `"interface"`, `"enum"` |
| `attributes` | lista di stringhe `"+ nome : tipo"` (stessa forma del corpus e dell'Apollon); `"+ nome"` se il tipo manca; `"+ nome : tipo = valore"` per un valore di default |
| `methods` | lista di stringhe `"+ nome(parametri) : Tipo"` oppure `"+ nome(parametri)"` |
| `values` | solo per `kind: "enum"`: lista dei valori (al posto di `attributes`; un enum non ha metodi) |

### Relazione

`type` appartiene a un **elenco chiuso** di sette valori, divisi in tre famiglie. Le chiavi degli estremi dicono il
RUOLO di ciascuna classe; le chiavi ammesse dipendono dalla famiglia.

| famiglia | `type` (tipo Apollon) | estremi (obbligatori) | chiavi facoltative |
|---|---|---|---|
| tutto / parte | `composition` (ClassComposition), `aggregation` (ClassAggregation) | `whole` = il tutto, `part` = la parte | `label`, `wholeMultiplicity`, `partMultiplicity`, `wholeRole`, `partRole` |
| figlia / madre | `inheritance` (ClassInheritance), `realization` (ClassRealization) | `child` = sottoclasse o classe che implementa, `parent` = superclasse o interfaccia | nessuna |
| associazioni | `association` (ClassBidirectional), `unidirectional` (ClassUnidirectional), `dependency` (ClassDependency) | `source`, `target` (per `unidirectional` e `dependency`: `target` = lato verso cui punta la freccia; per `association` il verso è libero) | `label`, `sourceMultiplicity`, `targetMultiplicity`, `sourceRole`, `targetRole` |

- `label` = nome dell'associazione (verbo); i ruoli (`...Role`) sono sostantivi sull'estremo; le molteplicità sono
  `1`, `0..1`, `*`, `1..*`, ...
- Una relazione con le chiavi di un'altra famiglia (es. `source` / `target` su una `composition`) non è conforme.
- L'espansore converte nel verso di Apollon: tutto / parte → sorgente = parte, destinazione = tutto (il rombo è sul
  target); figlia / madre → sorgente = figlia, destinazione = madre; associazioni invariate.

### Cosa fa l'espansore con il contenuto

Attributi e metodi passano per le stesse funzioni del convertitore del Passo 1 (`parse_attribute`,
`normalize_type_token`, `parse_method_signature`): i tipi noti si normalizzano (`String` → `string`, `Real` →
`double`, ...), il prefisso di visibilità diventa sempre `+`, le molteplicità `n` diventano `*`. Per i diagrammi del
corpus e del test set il giro Apollon → compatto → Apollon è identico (salvo gli id dei metodi, voce 90). Nelle
risposte del modello queste normalizzazioni si contano e si riportano a parte (`compact_postprocess.py`).

**Vincoli di generalizzazione** (`{disjoint, complete}`): Apollon non li rappresenta, quindi il compatto non li porta
(come nell'Apollon del Passo 1, dove stanno nel campo `constraints` del manifest).

## Esempio completo (TruckLogistics, corpus)

Indentato per leggibilità; negli esempi del prompt è serializzato su una riga (`separators=(",", ":")`), come l'Apollon
compatto. Diagramma: 8 classi (un enum), 9 relazioni (unidirezionali con etichetta e ruoli, una composizione,
un'associazione con ruolo, tre generalizzazioni). Token (cl100k_base, serializzazione su una riga): Apollon completo
2.196, compatto 328. Il blocco qui sotto coincide con `apollon_to_compact` del diagramma del corpus e l'espansione
arriva a L4 (verificato dai test; lo stesso per il frammento successivo).

```json
{
  "classes": [
    {"name": "Assignment", "attributes": ["+ date : date"]},
    {"name": "Location", "attributes": ["+ address : string"]},
    {"name": "Driver", "attributes": ["+ firstName : string", "+ lastName : string"]},
    {"name": "Vehicle", "attributes": ["+ vehicleNumber : int"]},
    {"name": "Truck", "attributes": ["+ tonnage : double"]},
    {"name": "PassengerCar", "attributes": ["+ seats : int"]},
    {"name": "Transporter"},
    {"name": "VehicleStatus", "kind": "enum", "values": ["READY", "ASSIGNMENT", "MAINTENANCE"]}
  ],
  "relations": [
    {"type": "unidirectional", "source": "Assignment", "target": "Driver", "label": "executes",
     "sourceMultiplicity": "0..1", "targetMultiplicity": "*"},
    {"type": "unidirectional", "source": "Assignment", "target": "Location",
     "sourceMultiplicity": "*", "targetMultiplicity": "1", "targetRole": "from"},
    {"type": "unidirectional", "source": "Assignment", "target": "Location",
     "sourceMultiplicity": "*", "targetMultiplicity": "1", "targetRole": "to"},
    {"type": "composition", "whole": "Location", "part": "Vehicle", "wholeMultiplicity": "1", "partMultiplicity": "1"},
    {"type": "association", "source": "Vehicle", "target": "Driver",
     "sourceMultiplicity": "*", "targetMultiplicity": "0..1", "targetRole": "driver"},
    {"type": "inheritance", "child": "Truck", "parent": "Vehicle"},
    {"type": "inheritance", "child": "PassengerCar", "parent": "Vehicle"},
    {"type": "inheritance", "child": "Transporter", "parent": "Vehicle"},
    {"type": "unidirectional", "source": "Vehicle", "target": "VehicleStatus",
     "sourceMultiplicity": "1", "targetMultiplicity": "1", "targetRole": "status"}
  ]
}
```

Frammento per i costrutti assenti dall'esempio (classe astratta, interfaccia, metodi, realizzazione, aggregazione con
ruolo, dipendenza):

```json
{
  "classes": [
    {"name": "Payment", "kind": "abstract", "attributes": ["+ amount : double"], "methods": ["+ pay() : boolean"]},
    {"name": "Refundable", "kind": "interface", "methods": ["+ refund(amount : double)"]},
    {"name": "CardPayment", "attributes": ["+ cardNumber : string"]},
    {"name": "Order"},
    {"name": "Wallet"}
  ],
  "relations": [
    {"type": "inheritance", "child": "CardPayment", "parent": "Payment"},
    {"type": "realization", "child": "CardPayment", "parent": "Refundable"},
    {"type": "aggregation", "whole": "Order", "part": "Payment", "wholeMultiplicity": "1",
     "partMultiplicity": "0..*", "partRole": "payments"},
    {"type": "dependency", "source": "Order", "target": "Wallet"}
  ]
}
```
