# Formato JSON compatto dei diagrammi delle classi — specifica (PROPOSTA, STOP 1 del 2026-10-08)

Terzo formato di uscita del modello, accanto a PlantUML e all'Apollon completo. **Apollon v4 resta il formato di
consegna**: il compatto si espande in Apollon completo con l'espansore unico (`generation/uml_structure.py`), lo
stesso del percorso PlantUML, che genera id deterministici, layout e punti. Motivazione e decisione: `docs/decisions.md`,
voce 90.

Codice: `uml_structure.to_compact` / `from_compact` (struttura comune <-> compatto), `apollon_to_compact` (esempi del
prompt), `compact_to_apollon` (risposta -> Apollon). Controllo: `python generation/compact_sanity_check.py`.

## Regole

- Un oggetto con due chiavi: `"classes"` (obbligatoria) e `"relations"` (lista, eventualmente vuota o assente).
  Nessun'altra chiave: **niente** `version`, `id`, `title`, `type`, `assessments`, `interactive`, posizioni, dimensioni,
  handle, punti, id di attributi / metodi / relazioni.
- **L'id di una classe è il suo nome**: i nomi delle classi sono unici; le relazioni si riferiscono alle classi per nome.
- Le chiavi vuote si omettono (stringhe vuote, liste vuote); `"kind"` si omette quando vale `"class"`.
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

| chiave | valore |
|---|---|
| `type` | `association` (ClassBidirectional), `unidirectional` (ClassUnidirectional), `inheritance` (ClassInheritance), `realization` (ClassRealization), `aggregation` (ClassAggregation), `composition` (ClassComposition), `dependency` (ClassDependency) |
| `source`, `target` | nomi di classi dichiarate in `classes` |
| `label` | nome dell'associazione (verbo), facoltativo |
| `sourceMultiplicity`, `targetMultiplicity` | molteplicità degli estremi (`1`, `0..1`, `*`, `1..*`, ...), facoltative |
| `sourceRole`, `targetRole` | nomi di ruolo degli estremi (sostantivi), facoltativi |

**Verso** (convenzione di Apollon, la stessa dell'Apollon completo):
- `inheritance` / `realization`: `source` = sottoclasse / classe che implementa, `target` = superclasse / interfaccia;
  nessuna etichetta, molteplicità o ruolo (l'espansore li toglierebbe);
- `composition` / `aggregation`: `source` = la PARTE, `target` = il TUTTO (il rombo è sul target);
- `unidirectional` / `dependency`: `target` = il lato verso cui punta la freccia;
- `association`: verso libero (bidirezionale).

### Cosa fa l'espansore con il contenuto

Attributi e metodi passano per le stesse funzioni del convertitore del Passo 1 (`parse_attribute`,
`normalize_type_token`, `parse_method_signature`): i tipi noti si normalizzano (`String` → `string`, `Real` →
`double`, ...), il prefisso di visibilità diventa sempre `+`, le molteplicità `n` diventano `*`. Per i diagrammi del
corpus e del test set il giro Apollon → compatto → Apollon è identico (salvo gli id dei metodi, vedi la voce 90).
Nelle risposte del modello queste normalizzazioni saranno contate e riportate a parte (FASE 2).

**Vincoli di generalizzazione** (`{disjoint, complete}`): Apollon non li rappresenta, quindi il compatto non li porta
(come nell'Apollon del Passo 1, dove stanno nel campo `constraints` del manifest).

## Esempio completo (TruckLogistics, corpus)

Indentato per leggibilità; negli esempi del prompt è serializzato su una riga (`separators=(",", ":")`), come l'Apollon
compatto. Diagramma: 8 classi (un enum), 9 relazioni (unidirezionali con etichetta e ruoli, una composizione,
un'associazione con ruolo, tre generalizzazioni). Token (cl100k_base, serializzazione su una riga): Apollon completo
2.196, compatto 328. Il blocco qui sotto, riletto, coincide con `apollon_to_compact` del diagramma del corpus, e
l'espansione arriva a L4 (verificato; lo stesso per il frammento successivo).

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
    {"type": "composition", "source": "Vehicle", "target": "Location",
     "sourceMultiplicity": "1", "targetMultiplicity": "1"},
    {"type": "association", "source": "Vehicle", "target": "Driver",
     "sourceMultiplicity": "*", "targetMultiplicity": "0..1", "targetRole": "driver"},
    {"type": "inheritance", "source": "Truck", "target": "Vehicle"},
    {"type": "inheritance", "source": "PassengerCar", "target": "Vehicle"},
    {"type": "inheritance", "source": "Transporter", "target": "Vehicle"},
    {"type": "unidirectional", "source": "Vehicle", "target": "VehicleStatus",
     "sourceMultiplicity": "1", "targetMultiplicity": "1", "targetRole": "status"}
  ]
}
```

Frammento per i costrutti assenti dall'esempio (classe astratta, interfaccia, metodi, realizzazione, aggregazione,
dipendenza):

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
    {"type": "inheritance", "source": "CardPayment", "target": "Payment"},
    {"type": "realization", "source": "CardPayment", "target": "Refundable"},
    {"type": "aggregation", "source": "Payment", "target": "Order", "sourceMultiplicity": "0..*", "targetMultiplicity": "1"},
    {"type": "dependency", "source": "Order", "target": "Wallet"}
  ]
}
```

## Punti da approvare (STOP 1)

1. Nomi delle chiavi: `classes` / `relations`; `name`, `kind`, `attributes`, `methods`, `values`; `type`, `source`,
   `target`, `label`, `sourceMultiplicity`, `targetMultiplicity`, `sourceRole`, `targetRole` (le ultime cinque come
   nell'Apollon, per non cambiare il lessico delle istruzioni v4).
2. Nomi brevi dei tipi di relazione (`association`, `unidirectional`, ...) al posto dei tipi Apollon (`ClassBidirectional`,
   ...).
3. Chiavi vuote omesse e `kind` omesso per `class` (meno token; il parser accetta anche le chiavi presenti e vuote).
4. Enum con `values` invece di `attributes`.
5. Attributi e metodi come stringhe nella forma del corpus (`"+ nome : tipo"`), non come oggetti `{name, type}`.
