"""
Converte i diagrammi di riferimento PlantUML in corpus/processed/corpus.jsonl nel
formato di output scelto per il progetto: **Apollon v4** (modello wire-format
"4.2.0", pacchetto npm @tumaet/apollon@5.3.0). Sostituisce la conversione verso
Apollon v3 usata fino al 2026-09-23 — vedi docs/decisions.md per il perche' del
cambio ("classi astratte/enum come nodo unico con isAbstract/stereotype invece di
elementi separati con owner", "tipi di relazione nativi come ClassInheritance invece
di un'associazione chiamata 'is-a'", "schema JSON ufficiale pubblicato per validare").

Schema v4 confermato leggendo i sorgenti (non dedotto), non solo lo schema JSON
pubblicato ma anche il codice TypeScript che lo implementa:
- schema JSON ufficiale: @tumaet/apollon/schema/uml-model-4.schema.json (copiato in
  evaluation/uml-model-4.schema.json, usato per la validazione strutturale — vedi
  validate_against_schema). Campi di primo livello richiesti: version, id, title,
  type, nodes, edges, assessments.
- library/lib/types/nodes/NodeProps.ts: un nodo "class" ha in "data" i campi name,
  attributes (lista di {id, name}), methods (lista di {id, name, isAbstract?}),
  stereotype opzionale ("interface" | "enumeration", da
  library/lib/types/nodes/enums/ClassStereotype.ts), isAbstract opzionale a livello
  di classe. Non esistono nodi "AbstractClass"/"Enumeration" separati come in v3:
  restano tutti "type": "class", la distinzione e' dentro "data".
- library/lib/edges/EdgeProps.ts: un edge ha in "data" i campi points (lista di
  {x,y} — assoluti, niente piu' "bounds" separato come in v3), sourceMultiplicity,
  targetMultiplicity, sourceRole, targetRole, label.
- library/lib/nodes/wrappers/DefaultNodeWrapper.tsx (enum HandleId): i punti di
  aggancio centrali di ciascun lato sono letteralmente "top" / "right" / "bottom" /
  "left" (ne esistono altri piu' fini per il trascinamento manuale nell'editor, non
  necessari per una generazione programmatica).
- versionConverter-*.js (bundle compilato): versione corrente del modello = "4.2.0".
- library/lib/utils/edgeUtils.ts (getEdgeMarkerStyles, verificato il 2026-09-24): il
  marcatore grafico (triangolo per inheritance/realization, rombo bianco/nero per
  aggregation/composition, freccia per unidirectional/dependency) e' SEMPRE su
  markerEnd — mai su markerStart — per ogni tipo di relazione delle classi. Questo
  fissa in modo definitivo, per tutti i tipi, quale estremo (source o target) deve
  ricevere quale ruolo semantico: vedi il docstring di relationship_kind per la
  convenzione risultante per ciascun tipo. **Corretto un bug**: una prima versione
  di questo modulo (fino al 2026-09-23) metteva il contenitore/aggregatore come
  "source" per ClassAggregation/ClassComposition — sbagliato, deve essere "target".

Punto ancora NON verificato nei sorgenti: il rendering effettivo nell'editor Apollon
non e' stato controllato visivamente (nessun ambiente browser/JS disponibile qui).
La convenzione sopra e' dedotta dal codice sorgente (getEdgeMarkerStyles), non da
uno screenshot dell'editor in azione — **da confermare aprendo qualche diagramma
convertito nell'editor Apollon online**.

Nomi di ruolo per estremo (source_role/target_role, aggiunto il 2026-09-25 per gli
esercizi tradotti in corpus/raw/translated_it/, vedi docs/decisions.md): un estremo
di relazione puo' avere, tra virgolette, solo la molteplicita' (invariato) oppure
"molteplicita' ruolo" separati da uno spazio (es. `"1 responsabile"`) — vedi
split_mult_role. Nessuno dei 45 file di corpus/raw/models_original/ ha uno spazio dentro le
virgolette di una molteplicita' (verificato con una scansione dedicata), quindi
questa estensione non cambia il parsing dei 45 esistenti. Il ruolo viaggia insieme
alla molteplicita' nello scambio source/target di relationship_kind (mai l'uno senza
l'altra, stesso principio del fix del Bug 2) e finisce in edge.data.sourceRole /
targetRole nel JSON v4.

Limiti noti (vedi anche i "apollon_conversion_warnings" scritti per ciascun record):
- Il costrutto "classe associativa" di PlantUML, es. "(A,B) .. C", non ha un
  equivalente diretto in Apollon: approssimato con due relazioni semplici verso i
  due partecipanti (ClassBidirectional, molteplicita' vuote perche' non ricavabili
  dal testo). La relazione A-B originale, se presente nel sorgente, resta comunque
  tra le relazioni convertite.
- I due casi di vincolo XOR (`note "{XOR}" as N`) non sono rappresentati: nessun
  costrutto equivalente documentato, scartati con un warning.
- Il costrutto "diamante" n-ario nativo di PlantUML (es. "<> diamond" in Cruise) non
  ha equivalente v4 documentato: il modello viene escluso dalla conversione
  (diagram_apollon_json resta None).
- Le classi usate in una relazione ma mai dichiarate con "class X {...}" sono create
  come nodi senza attributi — legale in PlantUML, non un errore nei dati.
- Il layout (position/width/height) e' calcolato con una griglia semplice
  deterministica, non rispecchia un layout originale (il PlantUML testuale non lo
  specifica). Scalato per rientrare nell'area 0-1600 x 0-780 se necessario.

Verifica a piu' livelli, ciascuno con uno scopo diverso:
1. validate_against_schema: conformita' strutturale allo schema JSON ufficiale
   (campi presenti, tipi, enum validi). Non valida il contenuto di "data" (lo schema
   stesso lo lascia libero).
2. verify_apollon_json: integrita' referenziale interna (id univoci, source/target
   degli edge che esistono davvero, dimensioni positive).
3. round_trip_check: contenuto SEMANTICO — nomi/tipi di attributi e molteplicita'
   per estremo — confrontato tra il PlantUML originale e il JSON prodotto, scritta
   senza riusare la logica di relationship_kind (per non validare un bug con la
   stessa funzione che lo ha causato — cosi' erano passati inosservati due bug reali
   nella versione precedente di questo script, trovati in revisione il 2026-09-23).

Uso:
    python corpus/build_manifest.py
    python corpus/apollon_convert.py
"""

from __future__ import annotations

import json
import math
import re
import uuid
from pathlib import Path

NAMESPACE = uuid.UUID("a5f3d2b0-6b8e-4e6a-9b1f-9b7f6f6b0a11")  # namespace fisso per id riproducibili

CORPUS_JSONL = Path(__file__).parent / "processed" / "corpus.jsonl"
APOLLON_OUT_DIR = Path(__file__).parent / "processed" / "apollon"
SCHEMA_PATH = Path(__file__).parent.parent / "evaluation" / "uml-model-4.schema.json"

MODEL_VERSION = "4.2.0"
MAX_CANVAS_WIDTH = 1600
MAX_CANVAS_HEIGHT = 780

# --- Riconoscimento delle relazioni --------------------------------------------

OPS = [
    "<|--", "--|>", "<|-", "-|>", "..|>", "<|..",  # ereditarieta' / realizzazione
    "<-->", "*-->", "*->", "-->", "<--",  # associazioni dirette/bidirezionali
    "..>", "<..",  # dipendenza
    "*--", "--*", "o--", "--o", "*-", "-*", "--", "..", "-o", "o-", "-", ".",
]
_OPS_ALT = "|".join(re.escape(o) for o in sorted(OPS, key=len, reverse=True))
REL_RE = re.compile(
    r'^\s*([\w]+)\s*(?:"([^"]*)")?\s*'
    r"(" + _OPS_ALT + r')\s*'
    r'(?:"([^"]*)")?\s*([\w]+)\s*(?::\s*(.*))?\s*$'
)
ASSOC1_RE = re.compile(r"^\s*(\w+)\s*\.{1,2}\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*$")
ASSOC2_RE = re.compile(r"^\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*\.{1,2}\s*(\w+)\s*$")
NOTE_RE = re.compile(r"^note\b.*\bas\s+(\w+)", re.IGNORECASE)
CLASS_HEADER_RE = re.compile(
    r"^(abstract\s+class|class|enum)\s+(\w+)(?:\s*<<\w+>>)?\s*(\{)?\s*(\})?\s*$"
)
DIAMOND_RE = re.compile(r"^<>\s+(\w+)\s*$")

INHERITANCE_OPS = {"<|--", "--|>", "<|-", "-|>"}
REALIZATION_OPS = {"..|>", "<|.."}
AGGREGATION_OPS = {"o--", "--o", "-o", "o-"}
COMPOSITION_OPS = {"*--", "--*", "*-", "-*", "*-->", "*->"}
DIRECTED_OPS = {"-->", "<--"}
DEPENDENCY_OPS = {"..>", "<.."}


def stable_id(seed: str) -> str:
    return str(uuid.uuid5(NAMESPACE, seed))


# --- Normalizzazioni FASE 1 (2026-09-25, vedi docs/decisions.md) -----------------
# Applicate a TUTTO il corpus (44 originali + tradotti), non solo alla pipeline di
# traduzione: prima erano fatte solo da apply_glossary.py per plantuml.txt degli
# esercizi tradotti; ora sono qui, in un unico punto, per ogni diagramma convertito.

TYPE_NORMALIZATION = {
    "string": "string", "String": "string",
    "int": "int", "Int": "int", "Integer": "int", "integer": "int",
    "double": "double", "Double": "double",
    "float": "float", "Float": "float",
    "boolean": "boolean", "Boolean": "boolean", "bool": "boolean", "Bool": "boolean",
    "date": "date", "Date": "date",
    "time": "time", "Time": "time",
    "datetime": "datetime", "DateTime": "datetime", "Datetime": "datetime",
    "long": "long", "Long": "long",
}


def normalize_type_token(t: str) -> str:
    """Tipi noti (attributi e tipi di ritorno dei metodi) normalizzati a una grafia
    unica. Un tipo non in questa tabella e' presumibilmente il nome di una classe o
    enum del diagramma (es. 'Suit', 'RoomType'): resta invariato, non e' compito di
    questa funzione deciderlo — vedi il report di corpus/apollon_convert.py per
    l'elenco di cosa e' stato normalizzato e cosa no.

    Notazione 'Tipo[]' per attributi multi-valore (FASE 3, 2026-09-28, caso reale:
    HelpingHands 'ItemCategory[] neededCategories', dove ItemCategory e' un enum
    regolarmente dichiarato nel diagramma): il tipo base viene normalizzato come al
    solito, il suffisso '[]' e' preservato invariato — non esiste un costrutto
    Apollon dedicato per attributi multi-valore, questa e' solo una convenzione
    testuale nel nome visualizzato (vedi anche prompt_template_v4.txt)."""
    if t.endswith("[]"):
        return f"{normalize_type_token(t[:-2])}[]"
    return TYPE_NORMALIZATION.get(t, t)


def normalize_multiplicity(m: str) -> str:
    """'n' -> '*': 'n' -> '*', '0..n' -> '0..*', '1..n' -> '1..*'. Applicata a ogni
    molteplicita' scritta in un edge, qualunque sia la sua provenienza (relazione
    diretta o classe associativa reificata)."""
    if not m:
        return m
    # 'N' maiuscola (es. RealEstateAgency, 2026-09-30) trattata come 'n'
    if m in ("n", "N"):
        return "*"
    if m.endswith(("..n", "..N")):
        return m[:-1] + "*"
    return m


def parse_method_signature(raw: str) -> str:
    """Formato unico '+ nome(parametri) : tipo' (o '+ nome(parametri)' se non c'e'
    un tipo di ritorno nel sorgente — mai inventato). Gestisce sia 'Tipo nome()'
    (stile Java, tipo di ritorno prima) sia 'nome() : Tipo' / 'nome():Tipo' (tipo di
    ritorno dopo, con o senza spazio prima dei due punti). Il prefisso di
    visibilita' originale (+-#~), se presente, viene tolto e sostituito con '+' —
    stessa convenzione gia' in uso per gli attributi in questo modulo (vedi
    parse_attribute/build_apollon_json), non una scelta nuova: la visibilita'
    originale non viene preservata nel JSON ne' qui ne' per gli attributi."""
    s = raw.strip()
    if s and s[0] in "+-#~":
        s = s[1:].strip()

    close_idx = s.rfind(")")
    if close_idx == -1:
        return f"+ {s}"  # forma anomala, nessuna parentesi: lasciata cosi' com'e'
    open_idx = s.rfind("(", 0, close_idx)
    if open_idx == -1:
        return f"+ {s}"

    before = s[:open_idx].strip()
    params = s[open_idx + 1 : close_idx]
    after = s[close_idx + 1 :].strip()

    if after:
        ret_type = after.lstrip(":").strip()
        name = before
    else:
        parts = before.rsplit(None, 1)
        if len(parts) == 2:
            ret_type, name = parts
        else:
            ret_type, name = "", before

    if ret_type:
        return f"+ {name}({params}) : {normalize_type_token(ret_type)}"
    return f"+ {name}({params})"


def split_mult_role(raw: str) -> tuple[str, str]:
    """Il testo tra virgolette di un estremo puo' essere solo la molteplicita'
    (es. '0..n', invariato rispetto a prima) oppure molteplicita' + nome di ruolo
    separati da spazio (es. '1 responsabile') — sintassi introdotta il 2026-09-25
    per gli esercizi tradotti (vedi docs/decisions.md), dove l'immagine sorgente
    mostra un nome di ruolo su un estremo specifico, distinto da un'etichetta
    sull'intera associazione. Nessuno dei 45 file originali del corpus ha uno
    spazio dentro le virgolette di una molteplicita' (verificato), quindi il
    parsing dei 45 esistenti non cambia comportamento."""
    raw = raw.strip()
    if not raw:
        return "", ""
    parts = raw.split(None, 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return parts[0], ""


def strip_reading_direction(label: str) -> str:
    """Rimuove un marcatore di verso di lettura PlantUML (' >' o ' <' finale,
    '< '/'> ' iniziale) da un'etichetta di relazione — 2026-09-29, casi reali:
    Louvre 'hasCoach >', University 'leads >'/'teaches >'. Il simbolo indica
    solo in che verso leggere l'etichetta (es. 'A -- B : verb >' si legge
    "A verb B"), non fa parte del nome — senza questa pulizia finiva
    letteralmente nel JSON finale (label/ruolo con un '>' appeso).

    Esteso il 2026-10-01 (es. 11 Officine: '<Lavora', '<dirige', 'effettua>',
    'appartiene>'): il marcatore puo' essere attaccato alla parola, senza spazio.
    Doppi '<<'/'>>' (stereotipi) non vengono toccati."""
    label = label.strip()
    if label.endswith((" >", " <")):
        return label[:-2].rstrip()
    if label.startswith(("< ", "> ")):
        return label[2:].lstrip()
    if len(label) > 1 and label[-1] in "<>" and label[-2] not in "<>-":
        return label[:-1].rstrip()
    if len(label) > 1 and label[0] in "<>" and label[1] not in "<>":
        return label[1:].lstrip()
    return label


# --- Parsing del PlantUML (invariato: agnostico rispetto al formato di output) ---


class ParsedClass:
    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind  # "class" | "abstract class" | "enum"
        self.attributes: list[tuple[str, str]] = []  # (nome, tipo) — tipo vuoto per i valori enum
        # Parallela a self.attributes (stesso indice): {"default": str|None,
        # "modifiers": list[str]} — modificatori {static}/{abstract}/{frozen}/
        # const e valore di default "= x", aggiunta FASE 3 (2026-09-28) per non
        # perderli in silenzio (vedi parse_attribute). Sempre un dict, mai
        # assente, anche per i valori enum (default=None, modifiers=[]).
        self.attribute_extras: list[dict] = []
        self.methods: list[str] = []
        self.placeholder = False  # referenziata in una relazione ma mai dichiarata (legale in PlantUML)


_ATTR_MODIFIER_RE = re.compile(r"\{([^}]*)\}")


def parse_attribute(line: str) -> tuple[str, str, dict]:
    """Gestisce sia 'Tipo nome' (stile Java) sia 'nome : Tipo' (stile PlantUML piu'
    comune), rimuove il prefisso di visibilita' (+-#~).

    FASE 3 (2026-09-28, caso reale: Sober 'Int CustNr {frozen}', TileOGame
    '{static} const int SpareConnectionPieces = 32'): i modificatori UML tra
    graffe ({static}/{abstract}/{frozen}/...), la parola chiave informale 'const'
    (non standard PlantUML, ma usata cosi' in questo corpus) e un valore di
    default '= valore' NON vengono piu' silenziosamente scartati o, peggio,
    fatti collassare nel nome/tipo per errore (bug precedente: senza gestire
    '=', 'int SpareConnectionPieces = 32' veniva interpretato con
    rsplit(None,1) risultando in nome='32', tipo='int SpareConnectionPieces =').
    Sono ora estratti esplicitamente e ritornati nel terzo elemento della tupla
    (extra['modifiers'], extra['default']) — il chiamante (parse_plantuml) li
    salva in ParsedClass.attribute_extras; build_apollon_json li rende in un
    warning esplicito (nessun campo JSON Apollon rappresenta i modificatori)."""
    s = line.strip()
    if s and s[0] in "+-#~":
        s = s[1:].strip()

    modifiers: list[str] = []

    def _collect(m: re.Match) -> str:
        for tok in re.split(r"[,\s]+", m.group(1).strip()):
            tok = tok.strip().lower()
            if tok:
                modifiers.append(tok)
        return " "

    s = _ATTR_MODIFIER_RE.sub(_collect, s)
    s = re.sub(r"\s+", " ", s).strip()

    if s.startswith("const "):
        s = s[len("const "):].strip()
        modifiers.append("const")

    default = None
    if "=" in s:
        s, _, default_raw = s.partition("=")
        s = s.strip()
        default = default_raw.strip()

    if ":" in s:
        name, _, typ = s.partition(":")
        name, typ = name.strip(), typ.strip()
    else:
        parts = s.rsplit(None, 1)
        if len(parts) == 2:
            typ, name = parts[0], parts[1]
        else:
            typ, name = "", s

    return name, typ, {"default": default, "modifiers": modifiers}


def parse_plantuml(text: str) -> tuple[dict[str, ParsedClass], list[dict], list[str], list[str]]:
    """Ritorna (classi, relazioni, warning, costrutti_non_supportati). Se
    costrutti_non_supportati non e' vuoto, il modello va escluso dalla conversione."""
    classes: dict[str, ParsedClass] = {}
    relationships: list[dict] = []
    warnings: list[str] = []
    unsupported: list[str] = []
    notes: set[str] = set()

    current: ParsedClass | None = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("@"):
            continue

        if current is not None:
            if line == "}":
                current = None
                continue
            if current.kind == "enum":
                current.attributes.append((line, ""))
                current.attribute_extras.append({"default": None, "modifiers": []})
            elif "(" in line:
                current.methods.append(line)
            else:
                name, typ, extra = parse_attribute(line)
                current.attributes.append((name, typ))
                current.attribute_extras.append(extra)
            continue

        m = CLASS_HEADER_RE.match(line)
        if m:
            kind, name, has_open, has_close = m.groups()
            pc = ParsedClass(name, kind)
            classes[name] = pc
            if has_open and not has_close:
                current = pc
            continue

        diamond_m = DIAMOND_RE.match(line)
        if diamond_m:
            unsupported.append(
                f"costrutto diamante n-ario '{line}' senza equivalente Apollon documentato"
            )
            continue

        note_m = NOTE_RE.match(line)
        if note_m:
            notes.add(note_m.group(1))
            continue

        assoc_m = ASSOC1_RE.match(line) or ASSOC2_RE.match(line)
        if assoc_m:
            g = assoc_m.groups()
            if ASSOC1_RE.match(line):
                label, a, b = g
            else:
                a, b, label = g
            if label in notes:
                warnings.append(
                    f"scartato vincolo/nota '{label}' su ({a},{b}): nessun costrutto Apollon "
                    "equivalente documentato"
                )
                continue
            relationships.append({"kind": "assoc_class", "assoc": label, "a": a, "b": b, "raw": line})
            continue

        m = REL_RE.match(line)
        if m:
            src, src_mult_raw, op, tgt_mult_raw, tgt, label = m.groups()
            src_mult, src_role = split_mult_role(src_mult_raw or "")
            tgt_mult, tgt_role = split_mult_role(tgt_mult_raw or "")
            relationships.append(
                {
                    "kind": "binary",
                    "source": src,
                    "source_mult": src_mult,
                    "source_role": src_role,
                    "op": op,
                    "target_mult": tgt_mult,
                    "target_role": tgt_role,
                    "target": tgt,
                    "label": strip_reading_direction(label or ""),
                    "raw": line,
                }
            )
            continue

        warnings.append(f"riga non riconosciuta e ignorata: {line!r}")

    if unsupported:
        return classes, relationships, warnings, unsupported

    referenced = set()
    for r in relationships:
        if r["kind"] == "binary":
            referenced.add(r["source"])
            referenced.add(r["target"])
        else:
            referenced.add(r["a"])
            referenced.add(r["b"])
            referenced.add(r["assoc"])
    for name in referenced:
        if name not in classes:
            pc = ParsedClass(name, "class")
            pc.placeholder = True
            classes[name] = pc
            warnings.append(
                f"classe '{name}' non ha una dichiarazione esplicita 'class {name} {{...}}' nel "
                "PlantUML sorgente (dichiarazione implicita tramite uso in una relazione, valida "
                "in PlantUML): creata come nodo senza attributi"
            )

    return classes, relationships, warnings, unsupported


def reify_association_classes(relationships: list[dict]) -> tuple[list[dict], list[str]]:
    """FASE 1 punto 4 (2026-09-25): per ogni classe associativa '(A,B) .. C' (o
    'C .. (A,B)'), rimuove l'edge binario A-B se presente nel sorgente e lo
    sostituisce con due edge le cui molteplicita' sono DERIVATE da quelle
    dell'associazione base, non inventate: A--C (A lato '1', C lato = la
    molteplicita' che B aveva nell'associazione base) e C--B (C lato = la
    molteplicita' che A aveva nell'associazione base, B lato '1'). Se
    l'associazione base A-B non esiste nel sorgente, o non ha molteplicita'
    esplicite, le molteplicita' di C restano vuote e viene emesso un warning
    invece di inventarle. Sostituisce la precedente approssimazione (due edge a
    molteplicita' sempre vuota) in uso fino al 2026-09-25, vedi docs/decisions.md."""
    warnings: list[str] = []
    result = list(relationships)
    assoc_entries = [r for r in result if r["kind"] == "assoc_class"]

    for assoc in assoc_entries:
        a, b, c = assoc["a"], assoc["b"], assoc["assoc"]
        result.remove(assoc)

        base_idx = None
        for i, r in enumerate(result):
            if r["kind"] == "binary" and {r["source"], r["target"]} == {a, b}:
                base_idx = i
                break

        if base_idx is None:
            ma = mb = ""
            warnings.append(
                f"classe associativa '{c}': nessuna associazione base {a}-{b} trovata nel "
                "sorgente PlantUML, molteplicita' delle relazioni reificate lasciate vuote"
            )
        else:
            base = result.pop(base_idx)
            if base["source"] == a:
                ma, mb = base["source_mult"], base["target_mult"]
            else:
                ma, mb = base["target_mult"], base["source_mult"]
            if not ma and not mb:
                warnings.append(
                    f"classe associativa '{c}': l'associazione base {a}-{b} non ha "
                    "molteplicita' esplicite nel sorgente, molteplicita' delle relazioni "
                    "reificate lasciate vuote"
                )

        result.append(
            {
                "kind": "binary", "source": a, "target": c, "op": "--",
                "source_mult": "1", "target_mult": mb,
                "source_role": "", "target_role": "", "label": "",
                "raw": f"(reificazione classe associativa '{c}' su {a}-{b}) {a}--{c}",
            }
        )
        result.append(
            {
                "kind": "binary", "source": c, "target": b, "op": "--",
                "source_mult": ma, "target_mult": "1",
                "source_role": "", "target_role": "", "label": "",
                "raw": f"(reificazione classe associativa '{c}' su {a}-{b}) {c}--{b}",
            }
        )

    return result, warnings


def relationship_kind(op: str) -> tuple[str, bool, bool]:
    """Ritorna (edge_type, swapped, no_label_no_mult) usando i tipi NATIVI Apollon v4
    (non piu' un'associazione chiamata 'is-a' come nel v3): ClassInheritance,
    ClassRealization, ClassAggregation, ClassComposition, ClassUnidirectional,
    ClassDependency, ClassBidirectional.

    swapped=True significa: il lato che deve comparire come "source" nell'edge e'
    il TARGET originale della riga PlantUML. Chi chiama deve scambiare insieme
    classi e molteplicita' — mai l'una senza l'altra (era il Bug 2 della versione
    precedente di questo script).

    Convenzione per ciascun tipo, verificata leggendo
    library/lib/utils/edgeUtils.ts (getEdgeMarkerStyles) di @tumaet/apollon: il
    marcatore grafico (triangolo/rombo/freccia) e' SEMPRE su markerEnd, cioe'
    sull'estremo "target", per ogni tipo di relazione delle classi. Quindi:
    - ClassInheritance / ClassRealization: target = superclasse/interfaccia,
      source = sottoclasse/classe che implementa (il triangolo sta sul target).
    - ClassUnidirectional / ClassDependency: target = il lato verso cui punta la
      freccia originale in PlantUML (la freccia sta sul target).
    - ClassAggregation / ClassComposition: target = il CONTENITORE/aggregatore
      (il rombo sta sul target, non sul source — occhio, e' l'opposto di quello
      che ci si aspetterebbe leggendo "il contenitore e' la fonte della
      relazione"; corretto il 2026-09-24 dopo che una prima versione di questa
      funzione metteva il contenitore come source).
    """
    if op in INHERITANCE_OPS:
        return "ClassInheritance", op in ("<|--", "<|-"), True
    if op in REALIZATION_OPS:
        return "ClassRealization", op == "<|..", True
    if op in AGGREGATION_OPS:
        # 'o' adiacente al lato sinistro (source originale) -> il contenitore e'
        # a sinistra, ma deve finire come TARGET -> va scambiato.
        return "ClassAggregation", op in ("o--", "o-"), False
    if op in COMPOSITION_OPS:
        # stessa logica, con '*' al posto di 'o'
        return "ClassComposition", op in ("*--", "*-", "*-->", "*->"), False
    if op in DIRECTED_OPS:
        return "ClassUnidirectional", op == "<--", False
    if op in DEPENDENCY_OPS:
        return "ClassDependency", op == "<..", False
    return "ClassBidirectional", False, False


CONSTRAINT_RE = re.compile(r"^\{.*\}$")


def extract_generalization_constraints(relationships: list[dict]) -> list[dict]:
    """FASE 2 (2026-09-25, decisione dell'utente su label_classification.md): un
    testo come '{total; disjoint}' o '{partial; overlap}' su una relazione di
    ereditarieta'/realizzazione NON e' un'etichetta di relazione — e' un vincolo
    UML standard su un insieme di generalizzazione (notazione OCL/UML
    {disjoint,complete} ecc.), emerso durante la classificazione delle etichette
    (7 casi nel corpus, categoria "vincolo" non prevista nelle istruzioni
    originali della FASE 2). build_apollon_json forza gia' a "" il label di
    ClassInheritance/ClassRealization (convenzione precedente), quindi questi
    vincoli erano gia' assenti dall'edge finale — semplicemente scartati senza
    essere salvati da nessuna parte. Questa funzione li cattura esplicitamente
    PRIMA che vengano scartati, per esporli in un campo a se' (corpus.jsonl,
    campo "constraints"), invece di perderli in silenzio."""
    constraints = []
    for r in relationships:
        if r["kind"] != "binary":
            continue
        if r["op"] not in INHERITANCE_OPS and r["op"] not in REALIZATION_OPS:
            continue
        label = r["label"].strip()
        if not label or not CONSTRAINT_RE.match(label):
            continue
        _edge_type, swapped, _ = relationship_kind(r["op"])
        child, parent = (r["target"], r["source"]) if swapped else (r["source"], r["target"])
        constraints.append({"generalizzazione": f"{child} extends {parent}", "vincoli": label})
    return constraints


LABEL_CLASSIFICATION_PATH = Path(__file__).parent / "label_classification.json"
_LABEL_CLASSIFICATION_CACHE: dict[tuple[str, str, str, str, str], dict] | None = None


def load_label_classification() -> dict[tuple[str, str, str, str, str], dict]:
    global _LABEL_CLASSIFICATION_CACHE
    if _LABEL_CLASSIFICATION_CACHE is None:
        if not LABEL_CLASSIFICATION_PATH.exists():
            raise SystemExit(
                f"{LABEL_CLASSIFICATION_PATH} non trovato: esegui prima "
                "corpus/_generate_label_classification.py"
            )
        entries = json.loads(LABEL_CLASSIFICATION_PATH.read_text(encoding="utf-8"))
        _LABEL_CLASSIFICATION_CACHE = {
            (e["esercizio"], e["source"], e["op"], e["target"], e["label"]): e for e in entries
        }
    return _LABEL_CLASSIFICATION_CACHE


def apply_label_classification(
    model_id: str, relationships: list[dict], classification: dict[tuple[str, str, str, str, str], dict]
) -> list[tuple[str, str, str, str, str]]:
    """FASE 2 (2026-09-28, decisione utente su label_classification.md/.json): ogni
    etichetta binaria non vuota e' o un'ASSOCIAZIONE/QUALIFICATORE (resta in
    "label", invariato) o un VINCOLO di generalizzazione (no-op qui: gia' estratto
    da extract_generalization_constraints, che deve girare PRIMA di questa
    funzione — il label viene comunque azzerato piu' avanti per gli archi di
    ereditarieta'/realizzazione da relationship_kind's no_label_no_mult) o un
    RUOLO/RUOLO_DOPPIO (spostato in sourceRole/targetRole sull'estremo indicato
    dalla classificazione, "source"/"target" — posizione letterale nella riga
    PlantUML originale, non un nome di classe, per non ambiguita' sulle
    auto-relazioni — label azzerato).

    Va chiamata PRIMA di reify_association_classes: le relazioni binarie "base"
    di una classe associativa vengono rimosse dalla reificazione, quindi la loro
    classificazione (se un'etichetta era li' presente) smette semplicemente di
    essere rilevante — comportamento gia' corretto, non serve gestirlo qui.

    Ritorna la lista delle chiavi (esercizio, source, op, target, label) non
    presenti in classification: il chiamante decide come fallire (l'assenza di
    classificazione per un'etichetta reale non e' un warning recuperabile, e' un
    errore di dati da correggere in corpus/_generate_label_classification.py)."""
    missing: list[tuple[str, str, str, str, str]] = []
    for r in relationships:
        if r["kind"] != "binary" or not r["label"]:
            continue
        key = (model_id, r["source"], r["op"], r["target"], r["label"])
        entry = classification.get(key)
        if entry is None:
            missing.append(key)
            continue

        tipo = entry["tipo"]
        # "qualificatore" e' una categoria riservata ma attualmente inutilizzata
        # (0 voci in label_classification.json dal 2026-09-29: gli unici 2 casi,
        # BuildingManagement id/username, sono stati riclassificati come "ruolo" —
        # non serviva una lettura UML cosi' specifica). Tenuta qui, non rimossa,
        # per un futuro caso reale che non si presti alla stessa lettura.
        if tipo in ("associazione", "qualificatore", "vincolo"):
            continue
        if tipo == "ruolo":
            sub_roles = [{"estremo": entry["estremo"], "testo": entry["testo"]}]
        elif tipo == "ruolo_doppio":
            sub_roles = entry["ruoli"]
        else:
            raise ValueError(f"{model_id}: tipo di classificazione sconosciuto {tipo!r} per {key}")

        for sub in sub_roles:
            field = "source_role" if sub["estremo"] == "source" else "target_role"
            if r[field]:
                raise ValueError(
                    f"{model_id}: conflitto, {field} gia' valorizzato ('{r[field]}') per "
                    f"'{r['raw']}' — la classificazione vuole scriverci '{sub['testo']}'"
                )
            r[field] = sub["testo"]
        r["label"] = ""

    return missing


# --- Layout ------------------------------------------------------------------

ROW_GAP = 60
COL_GAP = 60
CLASS_WIDTH = 220
HEADER_H = 40
MEMBER_H = 30
MARGIN = 40


def layout_classes(classes: dict[str, ParsedClass]) -> dict[str, dict]:
    """Griglia semplice e deterministica: non rispecchia un layout originale (il
    PlantUML testuale non lo specifica)."""
    names = list(classes.keys())
    ncols = max(1, math.ceil(math.sqrt(len(names))))

    positions: dict[str, dict] = {}
    x = MARGIN
    y = MARGIN
    row_h = 0
    col = 0
    for name in names:
        pc = classes[name]
        n_members = len(pc.attributes) + len(pc.methods)
        height = HEADER_H + max(n_members, 0) * MEMBER_H
        if n_members == 0:
            height = HEADER_H
        positions[name] = {"x": x, "y": y, "width": CLASS_WIDTH, "height": height}
        row_h = max(row_h, height)
        col += 1
        x += CLASS_WIDTH + COL_GAP
        if col >= ncols:
            col = 0
            x = MARGIN
            y += row_h + ROW_GAP
            row_h = 0
    return positions


def edge_direction(from_center: tuple[float, float], to_center: tuple[float, float]) -> str:
    dx = to_center[0] - from_center[0]
    dy = to_center[1] - from_center[1]
    if abs(dx) >= abs(dy):
        return "right" if dx >= 0 else "left"
    return "bottom" if dy >= 0 else "top"


def touch_point(box: dict, handle: str) -> tuple[float, float]:
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    if handle == "right":
        return box["x"] + box["width"], cy
    if handle == "left":
        return box["x"], cy
    if handle == "bottom":
        return cx, box["y"] + box["height"]
    return cx, box["y"]  # top


def fit_to_canvas(nodes: list[dict], edges: list[dict], max_x: float, max_y: float) -> tuple[float, float]:
    """Il prompt impone coordinate positive tra 0 e 1600 (x) / 0 e 780 (y). Se il
    layout a griglia eccede quell'area, scala tutto proporzionalmente (mai verso
    l'alto). Per diagrammi con molte classi puo' produrre riquadri piccoli: e' il
    compromesso del vincolo di canvas fisso del prompt, non un bug di questa funzione."""
    scale = min(MAX_CANVAS_WIDTH / max_x, MAX_CANVAS_HEIGHT / max_y, 1.0)
    if scale >= 1.0:
        return max_x, max_y

    for n in nodes:
        n["position"]["x"] *= scale
        n["position"]["y"] *= scale
        n["width"] *= scale
        n["height"] *= scale
        n["measured"]["width"] *= scale
        n["measured"]["height"] *= scale
    for e in edges:
        for p in e["data"]["points"]:
            p["x"] *= scale
            p["y"] *= scale

    return max_x * scale, max_y * scale


# --- Costruzione del JSON Apollon v4 --------------------------------------------


def build_apollon_json(model_id: str, classes: dict[str, ParsedClass], relationships: list[dict]):
    positions = layout_classes(classes)
    nodes: list[dict] = []
    node_by_class: dict[str, dict] = {}
    class_ids: dict[str, str] = {}
    warnings: list[str] = []

    for name, pc in classes.items():
        node_id = stable_id(f"{model_id}:class:{name}")
        class_ids[name] = node_id
        box = positions[name]

        attributes = []
        for i, (attr_name, attr_type) in enumerate(pc.attributes):
            attr_id = stable_id(f"{model_id}:attr:{name}:{attr_name}:{i}")
            extra = pc.attribute_extras[i] if i < len(pc.attribute_extras) else {"default": None, "modifiers": []}
            default = extra.get("default")

            if pc.kind == "enum":
                display = attr_name
            elif attr_type:
                display = f"+ {attr_name} : {normalize_type_token(attr_type)}"
            else:
                display = f"+ {attr_name}"  # nessun tipo nel sorgente: non se ne inventa uno
                warnings.append(f"attributo '{attr_name}' della classe '{name}' senza tipo dichiarato nel sorgente")
            if default and pc.kind != "enum":
                display += f" = {default}"

            if extra.get("modifiers"):
                warnings.append(
                    f"attributo '{attr_name}' della classe '{name}' ha modificatori "
                    f"{extra['modifiers']} non rappresentabili in Apollon (nessun campo JSON "
                    "corrispondente per gli attributi, a differenza dei metodi che hanno "
                    "isAbstract): scartati dalla stringa visualizzata, riportati qui invece "
                    "di essere persi in silenzio"
                )
            attributes.append({"id": attr_id, "name": display})

        methods = []
        for i, method_sig in enumerate(pc.methods):
            method_id = stable_id(f"{model_id}:method:{name}:{method_sig}:{i}")
            methods.append({"id": method_id, "name": parse_method_signature(method_sig)})

        data: dict = {"name": name, "attributes": attributes, "methods": methods}
        if pc.kind == "abstract class":
            data["isAbstract"] = True
        elif pc.kind == "enum":
            data["stereotype"] = "enumeration"

        node = {
            "id": node_id,
            "type": "class",
            "position": {"x": box["x"], "y": box["y"]},
            "width": box["width"],
            "height": box["height"],
            "measured": {"width": box["width"], "height": box["height"]},
            "data": data,
        }
        nodes.append(node)
        node_by_class[name] = node

    edges: list[dict] = []

    def add_edge(edge_type, source_name, target_name, label, source_mult, target_mult, source_role="", target_role=""):
        if source_name not in class_ids or target_name not in class_ids:
            warnings.append(f"relazione scartata, classe mancante: {source_name} -> {target_name}")
            return
        source_mult = normalize_multiplicity(source_mult)
        target_mult = normalize_multiplicity(target_mult)
        source_box, target_box = positions[source_name], positions[target_name]
        s_center = (source_box["x"] + source_box["width"] / 2, source_box["y"] + source_box["height"] / 2)
        t_center = (target_box["x"] + target_box["width"] / 2, target_box["y"] + target_box["height"] / 2)
        s_handle = edge_direction(s_center, t_center)
        t_handle = edge_direction(t_center, s_center)
        p1 = touch_point(source_box, s_handle)
        p2 = touch_point(target_box, t_handle)
        edge_id = stable_id(f"{model_id}:rel:{source_name}:{target_name}:{edge_type}:{label}:{len(edges)}")
        edges.append(
            {
                "id": edge_id,
                "source": class_ids[source_name],
                "target": class_ids[target_name],
                "type": edge_type,
                "sourceHandle": s_handle,
                "targetHandle": t_handle,
                "data": {
                    "points": [{"x": p1[0], "y": p1[1]}, {"x": p2[0], "y": p2[1]}],
                    "label": label,
                    "sourceMultiplicity": source_mult,
                    "targetMultiplicity": target_mult,
                    "sourceRole": source_role,
                    "targetRole": target_role,
                },
            }
        )

    for r in relationships:
        if r["kind"] == "binary":
            edge_type, swapped, no_label_no_mult = relationship_kind(r["op"])
            if swapped:
                eff_src, eff_tgt = r["target"], r["source"]
                src_mult, tgt_mult = r["target_mult"], r["source_mult"]
                src_role, tgt_role = r.get("target_role", ""), r.get("source_role", "")
            else:
                eff_src, eff_tgt = r["source"], r["target"]
                src_mult, tgt_mult = r["source_mult"], r["target_mult"]
                src_role, tgt_role = r.get("source_role", ""), r.get("target_role", "")
            label = "" if no_label_no_mult else r["label"]
            if no_label_no_mult:
                src_mult = tgt_mult = ""
                src_role = tgt_role = ""
            add_edge(edge_type, eff_src, eff_tgt, label, src_mult, tgt_mult, src_role, tgt_role)
        else:
            # Le classi associative vanno reificate PRIMA di chiamare questa funzione
            # (vedi reify_association_classes, FASE 1 2026-09-25) — se se ne trova
            # ancora una qui e' un bug del chiamante, non un caso da gestire.
            warnings.append(
                f"BUG: relazione di tipo '{r['kind']}' non reificata arrivata a "
                "build_apollon_json — chiama reify_association_classes prima di "
                f"questa funzione. Ignorata: {r}"
            )

    max_x = max((n["position"]["x"] + n["width"] for n in nodes), default=200) + MARGIN
    max_y = max((n["position"]["y"] + n["height"] for n in nodes), default=200) + MARGIN
    max_x, max_y = fit_to_canvas(nodes, edges, max_x, max_y)

    diagram = {
        "version": MODEL_VERSION,
        "id": model_id,
        "title": model_id,
        "type": "ClassDiagram",
        "nodes": nodes,
        "edges": edges,
        "assessments": {},
        "interactive": {"elements": {}, "relationships": {}},
    }
    return diagram, warnings


# --- Verifica --------------------------------------------------------------------

_SCHEMA_CACHE = None


def validate_against_schema(diagram: dict, model_id: str) -> list[str]:
    """Conformita' strutturale allo schema JSON ufficiale Apollon v4. Non valida il
    contenuto di "data" (lo schema stesso lo lascia intenzionalmente libero)."""
    global _SCHEMA_CACHE
    import jsonschema

    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(_SCHEMA_CACHE)
    return [f"{model_id}: schema — {e.message} (percorso: {list(e.absolute_path)})" for e in validator.iter_errors(diagram)]


def verify_apollon_json(diagram: dict, model_id: str) -> list[str]:
    """Integrita' referenziale interna (id univoci, source/target esistenti,
    dimensioni positive) — non correttezza semantica, vedi round_trip_check."""
    problems = []
    node_ids = {n["id"] for n in diagram["nodes"]}
    if len(node_ids) != len(diagram["nodes"]):
        problems.append(f"{model_id}: id di nodo duplicati")
    for n in diagram["nodes"]:
        if n["width"] <= 0 or n["height"] <= 0:
            problems.append(f"{model_id}: dimensioni non positive per il nodo {n['data'].get('name')}")
        member_ids = [m["id"] for m in n["data"].get("attributes", []) + n["data"].get("methods", [])]
        if len(member_ids) != len(set(member_ids)):
            problems.append(f"{model_id}: id di membro duplicati nel nodo {n['data'].get('name')}")
    for e in diagram["edges"]:
        if e["source"] not in node_ids or e["target"] not in node_ids:
            problems.append(f"{model_id}: edge {e['id']} referenzia un nodo inesistente")
        if len(e["data"]["points"]) < 2:
            problems.append(f"{model_id}: edge {e['id']} ha meno di 2 punti nel path")
    return problems


def _v4_attribute_to_tuple(name: str) -> tuple[str, str, str]:
    """(nome, tipo, default) dalla stringa visualizzata '+ nome : tipo = valore'
    (default e tipo opzionali) — default esteso FASE 3 (2026-09-28) per
    verificare in round-trip anche i valori di default preservati da
    parse_attribute, non solo nome/tipo."""
    s = name[2:] if name.startswith("+ ") else name
    default = ""
    if " = " in s:
        s, _, default_raw = s.partition(" = ")
        default = default_raw.strip()
    if " : " in s:
        nm, _, tp = s.partition(" : ")
        return nm.strip(), tp.strip(), default
    return s.strip(), "", default


def _expected_container(op: str, source: str, target: str) -> str:
    """Deriva il nome della classe "contenitore" (aggregatore/whole) per
    aggregazione/composizione direttamente dalla posizione del simbolo 'o'/'*'
    nell'operatore PlantUML originale — SENZA passare da relationship_kind, per un
    controllo di round-trip davvero indipendente dalla funzione sotto test."""
    if op in ("o--", "o-", "*--", "*-", "*-->", "*->"):
        return source  # simbolo adiacente al lato sinistro della riga originale
    return target  # "--o","-o","--*","-*": simbolo adiacente al lato destro


def round_trip_check(model_id: str, classes: dict[str, ParsedClass], relationships: list[dict], diagram: dict) -> list[str]:
    """Confronta il CONTENUTO SEMANTICO tra il PlantUML originale e il JSON v4
    prodotto, senza riusare relationship_kind (per non validare un eventuale bug con
    la stessa funzione che lo ha causato)."""
    problems = []
    name_by_id = {n["id"]: n["data"]["name"] for n in diagram["nodes"]}

    attrs_by_class: dict[str, list[tuple[str, str]]] = {}
    methods_by_class: dict[str, list[str]] = {}
    is_enum_by_class: dict[str, bool] = {}
    for n in diagram["nodes"]:
        is_enum = n["data"].get("stereotype") == "enumeration"
        is_enum_by_class[n["data"]["name"]] = is_enum
        if is_enum:
            attrs_by_class[n["data"]["name"]] = sorted((a["name"], "", "") for a in n["data"]["attributes"])
        else:
            attrs_by_class[n["data"]["name"]] = sorted(_v4_attribute_to_tuple(a["name"]) for a in n["data"]["attributes"])
        methods_by_class[n["data"]["name"]] = sorted(m["name"] for m in n["data"]["methods"])

    for name, pc in classes.items():
        if pc.placeholder:
            continue
        if pc.kind == "enum":
            expected = sorted((n, "", "") for n, _ in pc.attributes)
        else:
            expected = []
            for i, (n, t) in enumerate(pc.attributes):
                extra = pc.attribute_extras[i] if i < len(pc.attribute_extras) else {}
                expected.append((n, normalize_type_token(t), (extra or {}).get("default") or ""))
            expected = sorted(expected)
        got = attrs_by_class.get(name)
        if got is None:
            problems.append(f"{model_id}: classe '{name}' non trovata nel JSON convertito")
        elif got != expected:
            problems.append(
                f"{model_id}: attributi di '{name}' non coincidono — originale={expected} convertito={got}"
            )

        expected_methods = sorted(parse_method_signature(m) for m in pc.methods)
        got_methods = methods_by_class.get(name, [])
        if got_methods != expected_methods:
            problems.append(
                f"{model_id}: metodi di '{name}' non coincidono — originale={expected_methods} convertito={got_methods}"
            )

    out_edges = list(diagram["edges"])
    used_idx: set[int] = set()
    for r in relationships:
        if r["kind"] != "binary":
            continue
        pair = {r["source"], r["target"]}
        no_label = r["op"] in INHERITANCE_OPS or r["op"] in REALIZATION_OPS
        expected_label = "" if no_label else r["label"]
        candidate_idx = None
        for i, e in enumerate(out_edges):
            if i in used_idx:
                continue
            e_pair = {name_by_id.get(e["source"]), name_by_id.get(e["target"])}
            if e_pair == pair and e["data"]["label"] == expected_label:
                candidate_idx = i
                break
        if candidate_idx is None:
            problems.append(f"{model_id}: relazione originale '{r['raw']}' non trovata nel JSON convertito")
            continue
        used_idx.add(candidate_idx)
        if no_label:
            continue  # molteplicita' forzate vuote per convenzione, niente da confrontare
        e = out_edges[candidate_idx]
        expected = {
            r["source"]: normalize_multiplicity(r["source_mult"]),
            r["target"]: normalize_multiplicity(r["target_mult"]),
        }
        got = {
            name_by_id.get(e["source"]): e["data"]["sourceMultiplicity"],
            name_by_id.get(e["target"]): e["data"]["targetMultiplicity"],
        }
        if expected != got:
            problems.append(
                f"{model_id}: molteplicita' errate per '{r['raw']}' — attese {expected}, ottenute {got}"
            )

        expected_roles = {r["source"]: r.get("source_role", ""), r["target"]: r.get("target_role", "")}
        got_roles = {
            name_by_id.get(e["source"]): e["data"]["sourceRole"],
            name_by_id.get(e["target"]): e["data"]["targetRole"],
        }
        if expected_roles != got_roles:
            problems.append(
                f"{model_id}: ruoli errati per '{r['raw']}' — attesi {expected_roles}, ottenuti {got_roles}"
            )

        if r["op"] in AGGREGATION_OPS or r["op"] in COMPOSITION_OPS:
            expected_container = _expected_container(r["op"], r["source"], r["target"])
            got_container = name_by_id.get(e["target"])
            if got_container != expected_container:
                problems.append(
                    f"{model_id}: contenitore errato per '{r['raw']}' — atteso '{expected_container}' "
                    f"come target dell'edge, trovato '{got_container}'"
                )

    return problems


ALLOWED_PRIMITIVE_TYPES = set(TYPE_NORMALIZATION.values())
_EDGE_DATA_FIELDS = ("points", "label", "sourceMultiplicity", "targetMultiplicity", "sourceRole", "targetRole")


def style_check(diagram: dict, model_id: str) -> list[str]:
    """Controllo di stile FASE 4 (2026-09-28, STOP 3): a differenza di
    round_trip_check (contenuto semantico vs PlantUML sorgente), questo verifica
    la FORMA del JSON gia' prodotto, indipendentemente dal sorgente — tipi
    ammessi (primitivi normalizzati o classe/enum dichiarata nello stesso
    diagramma), formato '+ nome(...) : tipo' per i metodi, nessuna molteplicita'
    con 'n' letterale residua (avrebbe dovuto essere normalizzata a '*' da
    normalize_multiplicity), nessun campo data mancante su un edge."""
    problems = []
    declared_names = {n["data"]["name"] for n in diagram["nodes"]}

    for n in diagram["nodes"]:
        cname = n["data"]["name"]
        is_enum = n["data"].get("stereotype") == "enumeration"
        for a in n["data"].get("attributes", []):
            nm = a["name"]
            if is_enum:
                if nm.startswith("+ ") or " : " in nm:
                    problems.append(f"{model_id}: valore enum '{nm}' non e' un nome nudo (classe {cname})")
                continue
            if not nm.startswith("+ "):
                problems.append(f"{model_id}: attributo '{nm}' non inizia con '+ ' (classe {cname})")
                continue
            body = nm[2:].split(" = ", 1)[0]
            if " : " in body:
                _, _, typ = body.partition(" : ")
                base_type = typ[:-2] if typ.endswith("[]") else typ
                if base_type not in ALLOWED_PRIMITIVE_TYPES and base_type not in declared_names:
                    problems.append(
                        f"{model_id}: tipo '{typ}' dell'attributo '{nm}' non e' ne' un tipo primitivo "
                        f"ammesso ne' una classe/enum dichiarata in questo diagramma (classe {cname})"
                    )
        for m in n["data"].get("methods", []):
            nm = m["name"]
            if not nm.startswith("+ ") or "(" not in nm or ")" not in nm:
                problems.append(f"{model_id}: metodo '{nm}' non rispetta il formato '+ nome(...) : tipo' (classe {cname})")

    for e in diagram["edges"]:
        for field in _EDGE_DATA_FIELDS:
            if field not in e["data"]:
                problems.append(f"{model_id}: edge {e['id']} senza il campo data.{field}")
        for mult_field in ("sourceMultiplicity", "targetMultiplicity"):
            mult = e["data"].get(mult_field, "")
            if mult in ("n", "N") or mult.endswith(("..n", "..N")):
                problems.append(
                    f"{model_id}: edge {e['id']} ha {mult_field}={mult!r}, molteplicita' 'n' non normalizzata a '*'"
                )

    return problems


# --- Main ----------------------------------------------------------------------


def main() -> None:
    if not CORPUS_JSONL.exists():
        raise SystemExit(f"{CORPUS_JSONL} non trovato: esegui prima corpus/build_manifest.py")
    if not SCHEMA_PATH.exists():
        raise SystemExit(f"{SCHEMA_PATH} non trovato: scarica uml-model-4.schema.json da @tumaet/apollon")

    label_classification = load_label_classification()
    records = [json.loads(line) for line in CORPUS_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]

    APOLLON_OUT_DIR.mkdir(parents=True, exist_ok=True)
    total_warnings = 0
    total_problems = 0
    total_roundtrip_problems = 0
    total_schema_problems = 0
    total_constraints = 0
    total_missing_labels = 0
    total_style_problems = 0
    skipped: list[str] = []

    for record in records:
        model_id = record["id"]
        classes, relationships, parse_warnings, unsupported = parse_plantuml(record["diagram_plantuml"])

        if unsupported:
            skipped.append(model_id)
            record["diagram_apollon_json"] = None
            record["diagram_format"] = "plantuml"
            record["constraints"] = []
            record["apollon_conversion_warnings"] = [
                f"modello escluso dalla conversione Apollon: {u}" for u in unsupported
            ]
            out_path = APOLLON_OUT_DIR / f"{model_id}.json"
            out_path.unlink(missing_ok=True)
            continue

        missing_labels = apply_label_classification(model_id, relationships, label_classification)
        if missing_labels:
            total_missing_labels += len(missing_labels)
            print(f"[ERRORE CLASSIFICAZIONE] {model_id}: etichette non classificate: {missing_labels}")

        constraints = extract_generalization_constraints(relationships)
        constraint_warnings = [
            f"vincolo di generalizzazione '{c['vincoli']}' su {c['generalizzazione']} spostato nel "
            "campo 'constraints' del record (non e' un'etichetta di relazione, non finisce nell'edge)"
            for c in constraints
        ]
        total_constraints += len(constraints)

        relationships, reify_warnings = reify_association_classes(relationships)
        diagram, build_warnings = build_apollon_json(model_id, classes, relationships)
        schema_problems = validate_against_schema(diagram, model_id)
        problems = verify_apollon_json(diagram, model_id)
        roundtrip_problems = round_trip_check(model_id, classes, relationships, diagram)
        style_problems = style_check(diagram, model_id)

        warnings = parse_warnings + constraint_warnings + reify_warnings + build_warnings
        total_warnings += len(warnings)
        total_problems += len(problems)
        total_roundtrip_problems += len(roundtrip_problems)
        total_schema_problems += len(schema_problems)
        total_style_problems += len(style_problems)

        record["diagram_apollon_json"] = diagram
        record["diagram_apollon_model_version"] = MODEL_VERSION
        record["constraints"] = constraints
        record["apollon_conversion_warnings"] = warnings

        out_path = APOLLON_OUT_DIR / f"{model_id}.json"
        out_path.write_text(json.dumps(diagram, ensure_ascii=False, indent=2), encoding="utf-8")

        if schema_problems:
            print(f"[ERRORE SCHEMA] {model_id}: {schema_problems}")
        if problems:
            print(f"[ERRORE INTEGRITA'] {model_id}: {problems}")
        if roundtrip_problems:
            print(f"[ERRORE ROUND-TRIP] {model_id}: {roundtrip_problems}")
        if style_problems:
            print(f"[ERRORE STILE] {model_id}: {style_problems}")

    CORPUS_JSONL.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8"
    )

    assert total_missing_labels == 0, f"{total_missing_labels} etichette non classificate rilevate, vedi sopra"
    assert total_schema_problems == 0, f"{total_schema_problems} violazioni dello schema rilevate, vedi sopra"
    assert total_problems == 0, f"{total_problems} problemi di integrita' rilevati, vedi sopra"
    assert total_roundtrip_problems == 0, f"{total_roundtrip_problems} problemi di round-trip rilevati, vedi sopra"
    assert total_style_problems == 0, f"{total_style_problems} problemi di stile rilevati, vedi sopra"

    converted = len(records) - len(skipped)
    print(f"Convertiti {converted}/{len(records)} diagrammi in Apollon v{MODEL_VERSION} (esclusi: {skipped or 'nessuno'}).")
    print(f"Vincoli di generalizzazione estratti in corpus.jsonl (campo 'constraints'): {total_constraints}")
    print(f"Warning totali (approssimazioni/costrutti non gestiti): {total_warnings}")
    print("Classificazione etichette (corpus/label_classification.json): 0 etichette non classificate")
    print("Validazione schema JSON ufficiale: 0 violazioni")
    print("Round-trip semantico (attributi + molteplicita' per estremo): 0 discrepanze")
    print("Controllo di stile (tipi ammessi, formato metodi, niente 'n' letterale, campi data completi): 0 violazioni")
    print(f"JSON Apollon scritti in {APOLLON_OUT_DIR}")
    print("corpus.jsonl aggiornato con diagram_apollon_json + apollon_conversion_warnings")


if __name__ == "__main__":
    main()
