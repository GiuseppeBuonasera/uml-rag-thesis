"""
Costruzione dei prompt per le condizioni sperimentali (Passo 3a, 2026-10-05). Nessuna chiamata a un LLM.

Il prompt e' composto da tre blocchi (generation/templates/):
  1. istruzioni di formato  — IDENTICHE alle istruzioni di docs/dati/apollon_format_reference/prompt_template_v4.txt
                               (fonte della baseline, mai modificata; test di identita' byte per byte);
  2. blocco esempi           — l'UNICA parte che cambia tra le condizioni (sparisce in zero_shot);
  3. traccia da risolvere    — la description dell'esercizio.

Condizioni:
  zero_shot  nessun esempio;
  static     i due esempi della baseline (bank loans + AirTravel), nell'ordine del template;
  random     k esempi casuali dal corpus (retrieval/random_retriever.py, seed nella spec), nell'ordine estratto;
  bm25       top-k di retrieval/keyword_retriever.py con la configurazione CONGELATA di retrieval/config_bm25.yaml,
             il piu' simile per ULTIMO (vicino alla traccia);
  oracle     SOLO ANALISI: top-k per Jaccard dei nomi di classe con il ground truth, il piu' simile per ultimo. Usa il
             diagramma della query: non e' una condizione realizzabile in generazione, e' un limite superiore.
  dense      (voce 109) top-k del retriever denso scelto in retrieval/config_dense.yaml (esito della voce 108:
             all-MiniLM-L6-v2 alla revisione fissata, CPU, offline, embedding in cache), il piu' simile per ultimo;
  hybrid     (voce 109) RRF (c = 60) tra BM25 congelato (lo stesso indice di bm25) e il denso, il piu' simile per ultimo;
  oracle_jt  (voce 109) SOLO DIAGNOSTICA: top-k per Jt (Jaccard dei token dei nomi di classe, retrieval/relevance.py)
             con il ground truth della query, pareggi per id, il piu' simile per ultimo. MAI nel Passo 3b.
Tutte le condizioni con esempi del corpus usano gli STESSI candidati di bm25: pool(query) (voce 109, modifica 2).

Query dal CORPUS (pilota, 2026-10-06): se la query e' un esercizio del corpus, la selezione e' leave-one-out con lo
stesso protocollo di retrieval/analyze_retrieval.py: bm25 su un indice RIFITTATO sugli altri 58 record (la query non
entra nelle statistiche IDF / avgdl), random e oracle sugli altri 58; static con la query AirTravel e' rifiutata
(l'esempio 2 coinciderebbe con la query). In ogni caso build() fallisce se la query compare tra i propri esempi.

POOL UNICO (2026-10-10, voce 115, supera la voce 112): leave-one-out su TUTTI gli esercizi (corpus + test set De
Bari, 80): per OGNI query i candidati sono tutti gli altri (79), mai la query stessa; bm25 rifittato su quel pool,
dense / hybrid / random / oracle sullo stesso pool. Le run di sviluppo fatte prima del 2026-10-10 usavano i soli 58
candidati del corpus (protocollo storico, documentato nelle voci delle run).

Formato di uscita (secondo pilota, 2026-10-07): output_format "apollon" (istruzioni v4, esempi JSON) oppure
"plantuml" (istruzioni templates/v4_plantuml_instructions.txt, che cambiano SOLO la parte sul formato; esempi in
PlantUML CANONICO ricavato dal JSON Apollon del Passo 1, generation/plantuml_format.py) oppure "compact" (2026-10-08,
voce 91: istruzioni templates/v4_compact_instructions.txt, che cambiano SOLO la parte sul formato; esempi nel formato
JSON compatto ricavato dal JSON del Passo 1, generation/uml_structure.py, docs/compact_format.md). Il blocco esempi resta
l'unica parte che cambia tra le condizioni dello stesso formato.

FONTE DEL RETRIEVAL (2026-10-11, voce 129): retrieval_source "live" (default) = i retriever girano qui;
"frozen" = bm25, dense, hybrid e random si leggono da data/retrieval_frozen/retrievals_3b.jsonl (prodotto da
retrieval/freeze_retrievals.py con lo STESSO codice, PromptBuilder.hits), con il controllo dello sha256 registrato nel
file .meta.json accanto. Il protocollo del Passo 3b usa "frozen": gli esempi non dipendono piu' dalla macchina (pareggi,
embedding su CPU). Le altre condizioni (zero_shot, static, oracle, oracle_jt) non usano un retriever e sono invariate;
le varianti struct / construct non sono congelate e in modalita' frozen sono rifiutate.

Ogni esempio = description + JSON Apollon, serializzati allo stesso modo in tutte le condizioni. corpus/ e
config_bm25.yaml sono letti e mai scritti. Determinismo: stessa spec + stessa query -> stesso prompt byte per byte.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "retrieval"))
import corpus_loader as cl  # noqa: E402
from keyword_retriever import KeywordRetriever  # noqa: E402
from base import RetrievalResult  # noqa: E402
from random_retriever import RandomRetriever  # noqa: E402
from text_preprocessing import PreprocessConfig  # noqa: E402
import relevance  # noqa: E402  (Jt per oracle_jt, voce 109)

TEMPLATES = Path(__file__).resolve().parent / "templates"
V4_TEMPLATE = ROOT / "docs" / "dati" / "apollon_format_reference" / "prompt_template_v4.txt"
STATIC_DIR = ROOT / "docs" / "dati" / "apollon_format_reference"
BM25_CONFIG = ROOT / "retrieval" / "config_bm25.yaml"
DENSE_CONFIG = ROOT / "retrieval" / "config_dense.yaml"

CONDITIONS = ("zero_shot", "static", "random", "bm25", "oracle", "dense", "hybrid", "oracle_jt",
              "struct", "construct", "struct_construct", "oracle_self", "oracle_partial", "bm25_controllo")
# oracle_partial (voce 163, SOLO ANALISI): come oracle_self, ma la soluzione dell'esempio e' DEGRADATA: si tiene la
# frazione oracle_keep delle classi (scelta deterministica, degrade_diagram) con i loro attributi e le relazioni tra
# classi tenute; la traccia dell'esempio resta quella vera. Misura quanto deve essere simile un esempio per servire.
ORACLE_CONDITIONS = ("oracle_self", "oracle_partial")
# voce 164: esempi aggiunti all'esempio parziale di oracle_partial. "bm25_2" = i 2 esempi bm25 k2 del file congelato
# PRIMA dell'esempio parziale (il piu' simile per ultimo, come nel 3b); "complemento" = dopo l'esempio al 50 % un secondo
# esempio con le classi complementari (le due soluzioni insieme coprono tutte le classi)
ORACLE_EXTRAS = ("nessuno", "bm25_2", "complemento")
# voce 167 (SOLO ANALISI): bm25_controllo = gli stessi esempi di bm25 (file congelato), per i controlli; con
# strip_attributes gli esempi (di bm25_controllo o di oracle_self) perdono tutti gli attributi delle classi non enum
# (classi, relazioni e valori degli enum restano)
STRIP_CONDITIONS = ("oracle_self", "bm25_controllo")
# oracle_self (voce 162, SOLO ANALISI): l'unico esempio e' l'esercizio stesso con la sua soluzione; controllo che misura
# se il modello sa usare il contenuto di un esempio perfetto. Mai nel 3b ne' nei dati dei relatori.
# Blocco esempi (voce 162): "standard" = v5_examples_block.txt; "libero" = senza la frase "They describe other systems:
# do not copy their classes" (v5_examples_block_libero.txt), solo per oracle_self
EXAMPLES_BLOCKS = {"standard": "v5_examples_block.txt", "libero": "v5_examples_block_libero.txt"}
# varianti del retriever della voce 120 (passo 4, voce 121), sul pool unico come bm25, il piu' simile per ultimo:
#   struct            v2: RRF(bm25, BM25 sui nomi di classe dei candidati)
#   construct         v4: bm25 con la spinta ai candidati che mostrano i costrutti segnalati dalla traccia
#   struct_construct  v2 + v4: la spinta dei costrutti applicata a v2
STRUCTURE_CONDITIONS = ("struct", "construct", "struct_construct")
# voce 129: retriever congelati per il Passo 3b (data/retrieval_frozen/retrievals_3b.jsonl)
FROZEN_CONDITIONS = ("bm25", "dense", "hybrid", "random")
RETRIEVAL_SOURCES = ("live", "frozen")
FROZEN_PATH = ROOT / "data" / "retrieval_frozen" / "retrievals_3b.jsonl"
# voce 130: seme della condizione random. "config" = il `seed` del config per tutte le ripetizioni (run storiche);
# "per_esercizio_ripetizione" = random_seed(id dell'esercizio, indice di ripetizione) (Passo 3b)
RANDOM_SEED_MODES = ("config", "per_esercizio_ripetizione")


def random_seed(query_id: str, repetition: int) -> int:
    """Seme della condizione random per esercizio E ripetizione (voce 130): intero a 32 bit dai primi 8 caratteri
    esadecimali di sha256("random|<id>|<r>"). Deterministico, indipendente dalla macchina e dall'ordine delle run."""
    import hashlib
    return int(hashlib.sha256(f"random|{query_id}|{repetition}".encode("utf-8")).hexdigest()[:8], 16)
ANALYSIS_ONLY = {"oracle", "oracle_jt", "oracle_self", "oracle_partial", "bm25_controllo"}


def strip_attributes(diagram: dict) -> dict:
    """Voce 167: copia del diagramma Apollon senza attributi nelle classi non enum (i valori degli enum, salvati come
    attributi del nodo con stereotipo "enumeration", restano); classi, metodi e relazioni invariati."""
    import copy
    out = copy.deepcopy(diagram)
    for n in out.get("nodes", []):
        data = n.get("data") or {}
        if data.get("stereotype") != "enumeration" and "attributes" in data:
            data["attributes"] = []
    return out


def degrade_diagram(diagram: dict, keep: float, seed_id: str, complement: bool = False) -> dict:
    """Voce 163: copia del diagramma Apollon con la frazione `keep` delle classi (almeno 1), scelte in modo
    deterministico (ordine per sha256("<seed_id>|<id del nodo>")), con i loro attributi; restano solo le relazioni e le
    generalizzazioni tra classi tenute. Il resto (layout, id) e' invariato. complement=True (voce 164): le classi NON
    tenute dalla stessa chiamata con complement=False (le due parti insieme coprono tutte le classi)."""
    import copy
    import hashlib
    nodes = diagram.get("nodes", [])
    order = sorted(nodes, key=lambda n: hashlib.sha256(f"{seed_id}|{n['id']}".encode("utf-8")).hexdigest())
    cut = max(1, round(keep * len(nodes)))
    kept = {n["id"] for n in (order[cut:] if complement else order[:cut])}
    out = copy.deepcopy(diagram)
    out["nodes"] = [n for n in out.get("nodes", []) if n["id"] in kept]
    out["edges"] = [e for e in out.get("edges", []) if e.get("source") in kept and e.get("target") in kept]
    return out
SERIALIZATIONS = ("indent2", "compact")
# voce 138: vista degli ESEMPI. "raw" = traccia originale (default, prompt identici a prima); "clean_v1" = tolte le
# frasi elencate in example_view_clean_v1.yaml (istruzioni per lo studente). La traccia della query non cambia mai.
EXAMPLE_VIEWS = ("raw", "clean_v1")
EXAMPLE_VIEW_FILES = {"clean_v1": Path(__file__).resolve().parent / "example_view_clean_v1.yaml"}


def example_view_edits(view: str) -> dict[str, list[str]]:
    """Frasi da togliere per esercizio nella vista indicata (vuoto per "raw")."""
    if view == "raw":
        return {}
    return yaml.safe_load(EXAMPLE_VIEW_FILES[view].read_text(encoding="utf-8")) or {}


def apply_example_view(exercise_id: str, description: str, edits: dict[str, list[str]]) -> str:
    """Toglie le frasi della vista (ognuna deve comparire esattamente una volta) con lo spazio che le separa."""
    out = description
    for sentence in edits.get(exercise_id, []):
        if out.count(sentence) != 1:
            raise ValueError(f"vista degli esempi: in {exercise_id} la frase compare {out.count(sentence)} volte: "
                             f"{sentence[:60]!r}")
        i = out.index(sentence)
        j = i + len(sentence)
        if j < len(out) and out[j] == " ":
            j += 1  # spazio dopo la frase
        elif i > 0 and out[i - 1] == " ":
            i -= 1  # altrimenti lo spazio prima
        out = out[:i] + out[j:]
    return out
OUTPUT_FORMATS = ("apollon", "plantuml", "compact")
INSTRUCTION_TEMPLATES = {"apollon": "v4_instructions.txt", "plantuml": "v4_plantuml_instructions.txt",
                         "compact": "v4_compact_instructions.txt"}
# il compatto riusa la voce di esempio JSON della v4 ("Example n — JSON:")
ITEM_TEMPLATES = {"apollon": "v4_example_item.txt", "plantuml": "v4_plantuml_example_item.txt",
                  "compact": "v4_example_item.txt"}
# Variante delle istruzioni (voce 98): "base" = istruzioni del formato invariate (tutte le run fino al 2026-10-09);
# "targeted" = stesse istruzioni con il blocco congelato di regole aggiuntive (templates/targeted_rules_block.txt, riga
# del verso da templates/targeted_rules_direction.yaml) inserito subito prima dell'ultimo paragrafo ("Your output must
# be ..."), separato da una riga vuota. Nessuna riga esistente cambia.
INSTRUCTION_VARIANTS = ("base", "targeted")
# Versione delle istruzioni (voce 111): "v4" = template v4 (tutte le run fino al 2026-10-09, default finche' la regola
# della voce 111 non adotta v5); "v5" = istruzioni riscritte da zero (templates/v5_<formato>_instructions.txt), traccia
# templates/v5_task.txt con una riga finale per formato, blocco esempi templates/v5_examples_block.txt (frase sugli
# esempi prima di "Examples to follow:", assente in zero-shot), esempi PlantUML nel canonico v5 (ereditarieta' e realizzazione
# nell'intestazione, plantuml_format.apollon_to_plantuml(version="v5")). Solo per PlantUML e compatto. Il blocco esempi e
# le voci degli esempi sono quelli della v4.
INSTRUCTION_VERSIONS = ("v4", "v5", "v5plan", "v5b", "v5c")
# v5plan (voce 126): v5 con la risposta in due parti, PLAN (al piu' 15 righe, citazioni brevi dal testo) e DIAGRAM;
# istruzioni templates/v5plan_<formato>_instructions.txt (v5 con il solo paragrafo OUTPUT FORMAT cambiato), stesso
# blocco esempi e stessi esempi della v5 (che mostrano SOLO diagrammi), riga finale della traccia per il piano
V5PLAN_INSTRUCTION_TEMPLATES = {"plantuml": "v5plan_plantuml_instructions.txt",
                                "compact": "v5plan_compact_instructions.txt"}
V5PLAN_FINAL_LINE = "Now write the PLAN and then the DIAGRAM for this system only."
# v5b (voce 135): SOLO compatto; la v5 con 4 righe cambiate (attributi da elencare tutti, molteplicita' richieste);
# esempi, blocco esempi, traccia e riga finale identici alla v5
V5B_INSTRUCTION_TEMPLATES = {"compact": "v5b_compact_instructions.txt"}
# v5c (voce 150): SOLO compatto; la v5 con 2 righe cambiate ("attributes" obbligatoria in ogni classe non enum, [] se il
# testo non ne da') E gli esempi con "attributes": [] esplicita nelle classi non enum che non ne hanno
# (explicit_attributes); blocco esempi, traccia e riga finale identici alla v5
V5C_INSTRUCTION_TEMPLATES = {"compact": "v5c_compact_instructions.txt"}
V5_FAMILY = ("v5", "v5plan", "v5b", "v5c")
V5_INSTRUCTION_TEMPLATES = {"plantuml": "v5_plantuml_instructions.txt", "compact": "v5_compact_instructions.txt"}
V5_FINAL_LINE = {"plantuml": "Now write the PlantUML diagram for this system only.",
                 "compact": "Now write the compact JSON diagram for this system only."}
TARGETED_FORMATS = ("plantuml", "compact")
LAYOUTS = ("user_only", "system_user")  # system_user disponibile, ma non si usa senza decisione (decisions.md, voce 64)


@dataclass(frozen=True)
class PromptSpec:
    condition: str
    k: int = 3  # ignorato da zero_shot (0) e static (2 esempi fissi)
    seed: int = 0  # solo random
    serialization: str = "compact"
    layout: str = "user_only"
    drop_interactive: bool = True  # toglie la chiave di primo livello "interactive" dagli esempi serializzati
    output_format: str = "apollon"  # "apollon" (JSON) | "plantuml" (convertito in Apollon nel post-processing)
    instructions_variant: str = "base"  # "base" | "targeted" (voce 98)
    instructions_version: str = "v4"  # "v4" | "v5" (voce 111)
    example_view: str = "raw"  # "raw" | "clean_v1" (voce 138)
    examples_block: str = "standard"  # "standard" | "libero" (voce 162, solo oracle_self / oracle_partial)
    oracle_keep: float = 1.0  # voce 163: frazione delle classi tenute nell'esempio di oracle_partial
    oracle_extra: str = "nessuno"  # voce 164: "nessuno" | "bm25_2" (+ 2 esempi bm25) | "complemento" (+ la parte mancante)
    strip_attributes: bool = False  # voce 167: esempi senza attributi (solo oracle_self e bm25_controllo)

    def __post_init__(self):
        if self.strip_attributes and self.condition not in STRIP_CONDITIONS:
            raise ValueError(f"strip_attributes vale solo per {STRIP_CONDITIONS} (voce 167)")
        if self.oracle_extra not in ORACLE_EXTRAS:
            raise ValueError(f"oracle_extra sconosciuto: {self.oracle_extra} (ammessi: {ORACLE_EXTRAS})")
        if self.oracle_extra != "nessuno" and self.condition != "oracle_partial":
            raise ValueError("oracle_extra vale solo per oracle_partial (voce 164)")
        if self.oracle_extra == "complemento" and self.oracle_keep != 0.5:
            raise ValueError("oracle_extra 'complemento' solo con oracle_keep 0.5 (voce 164)")
        if self.examples_block not in EXAMPLES_BLOCKS:
            raise ValueError(f"blocco esempi sconosciuto: {self.examples_block} (ammessi: {tuple(EXAMPLES_BLOCKS)})")
        if self.examples_block != "standard" and self.condition not in ORACLE_CONDITIONS:
            raise ValueError("il blocco esempi 'libero' vale solo per oracle_self / oracle_partial (voci 162-163)")
        if self.condition == "oracle_partial" and not 0 < self.oracle_keep < 1:
            raise ValueError(f"oracle_partial: oracle_keep deve stare tra 0 e 1 escluso, non {self.oracle_keep}")
        if self.condition != "oracle_partial" and self.oracle_keep != 1.0:
            raise ValueError("oracle_keep vale solo per oracle_partial (voce 163)")
        if self.condition not in CONDITIONS:
            raise ValueError(f"condizione sconosciuta: {self.condition}")
        if self.output_format not in OUTPUT_FORMATS:
            raise ValueError(f"formato di uscita sconosciuto: {self.output_format}")
        if self.instructions_variant not in INSTRUCTION_VARIANTS:
            raise ValueError(f"variante delle istruzioni sconosciuta: {self.instructions_variant}")
        if self.instructions_variant == "targeted" and self.output_format not in TARGETED_FORMATS:
            raise ValueError(f"istruzioni mirate solo per {TARGETED_FORMATS}, non per {self.output_format}")
        if self.instructions_version not in INSTRUCTION_VERSIONS:
            raise ValueError(f"versione delle istruzioni sconosciuta: {self.instructions_version}")
        if self.instructions_version in V5_FAMILY and self.output_format not in V5_INSTRUCTION_TEMPLATES:
            raise ValueError(f"istruzioni v5 solo per {tuple(V5_INSTRUCTION_TEMPLATES)}, non per {self.output_format}")
        if self.instructions_version == "v5b" and self.output_format not in V5B_INSTRUCTION_TEMPLATES:
            raise ValueError(f"istruzioni v5b solo per {tuple(V5B_INSTRUCTION_TEMPLATES)}, non per {self.output_format}")
        if self.instructions_version == "v5c" and self.output_format not in V5C_INSTRUCTION_TEMPLATES:
            raise ValueError(f"istruzioni v5c solo per {tuple(V5C_INSTRUCTION_TEMPLATES)}, non per {self.output_format}")
        if self.instructions_version in V5_FAMILY and self.instructions_variant != "base":
            raise ValueError("istruzioni v5: il blocco mirato della voce 98 vale solo per le v4")
        if self.example_view not in EXAMPLE_VIEWS:
            raise ValueError(f"vista degli esempi sconosciuta: {self.example_view} (ammesse: {EXAMPLE_VIEWS})")
        if self.serialization not in SERIALIZATIONS or self.layout not in LAYOUTS:
            raise ValueError(f"serializzazione o layout non validi: {self.serialization}, {self.layout}")


@dataclass
class BuiltPrompt:
    query_id: str
    spec: PromptSpec
    example_ids: list[str]
    instructions: str
    examples_block: str  # "" in zero_shot
    task: str
    text: str = ""
    messages: list[dict] = field(default_factory=list)
    analysis_only: bool = False


def _template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def targeted_block(output_format: str) -> str:
    """Blocco congelato delle istruzioni mirate per un formato (voce 98), senza a capo finale."""
    direction = yaml.safe_load(_template("targeted_rules_direction.yaml"))[output_format]
    return _template("targeted_rules_block.txt").format(generalization_direction=direction).rstrip("\n")


def targeted_instructions(instructions: str, output_format: str) -> str:
    """Istruzioni del formato con il blocco inserito subito prima dell'ultimo paragrafo ("Your output must be ...")."""
    head, sep, last = instructions.rstrip("\n").rpartition("\n\n")
    if not sep or not last.startswith("Your output must be"):
        raise ValueError("istruzioni senza l'ultimo paragrafo atteso ('Your output must be ...')")
    return head + "\n\n" + targeted_block(output_format) + "\n\n" + last + "\n"


def serialize_diagram(diagram: dict, serialization: str, drop_interactive: bool) -> str:
    d = {k: v for k, v in diagram.items() if not (drop_interactive and k == "interactive")}
    if serialization == "compact":
        return json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(d, ensure_ascii=False, indent=2)


# id degli esempi della condizione static (static_examples): una query con uno di questi id non ha la cella static
STATIC_EXAMPLE_IDS = ("STATIC_example_1_bank_loans", "AirTravel")


def explicit_attributes(data: dict) -> dict:
    """Voce 150 (v5c): compatto di un esempio con la chiave "attributes" sempre presente nelle classi non enum (lista
    vuota se la classe non ne ha), subito dopo "name" e "kind"; il resto invariato (stesso ordine delle chiavi)."""
    classes = []
    for c in data["classes"]:
        if c.get("kind") == "enum" or "attributes" in c:
            classes.append(c)
            continue
        out = {k: c[k] for k in ("name", "kind") if k in c}
        out["attributes"] = []
        out.update({k: v for k, v in c.items() if k not in out})
        classes.append(out)
    return {**data, "classes": classes}


def static_examples(candidates_by_id: dict[str, dict]) -> list[dict]:
    """Esempio 1 (bank loans): testo dal template v4, JSON da example_1_bank_loans_v4.json. Esempio 2 (AirTravel): il
    record AirTravel del corpus, il cui JSON coincide con example_2_airtravel_v4.json (verificato qui)."""
    v4 = V4_TEMPLATE.read_text(encoding="utf-8")
    text1 = re.search(r"Example 1 — text:\n(.*?)\nExample 1 — JSON", v4, re.S).group(1).strip()
    ex1 = json.loads((STATIC_DIR / "example_1_bank_loans_v4.json").read_text(encoding="utf-8"))
    ex2_file = json.loads((STATIC_DIR / "example_2_airtravel_v4.json").read_text(encoding="utf-8"))
    air = candidates_by_id["AirTravel"]
    if air["diagram_apollon_json"] != ex2_file:
        raise AssertionError("example_2_airtravel_v4.json non coincide piu' con il record AirTravel del corpus")
    return [{"id": "STATIC_example_1_bank_loans", "description": text1, "diagram_apollon_json": ex1},
            {"id": "AirTravel", "description": air["description"], "diagram_apollon_json": air["diagram_apollon_json"]}]


def load_frozen(path: Path) -> tuple[dict[tuple, list[RetrievalResult]], str]:
    """Legge il file congelato (voce 129) dopo aver verificato lo sha256 registrato nel .meta.json accanto."""
    import hashlib
    meta_path = path.with_suffix(".meta.json")
    if not path.exists() or not meta_path.exists():
        raise SystemExit(f"file congelato o metadati mancanti: {path} (retrieval/freeze_retrievals.py)")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if digest != meta["sha256"]:
        raise SystemExit(f"{path.name}: sha256 {digest} diverso da quello registrato ({meta['sha256']})")
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        key = PromptBuilder.frozen_key(r["query"], r["retriever"], r["k"], r["seed"])
        if key in out:
            raise ValueError(f"riga ripetuta nel file congelato: {key}")
        out[key] = [RetrievalResult(id=i, rank=n, score=s, score_norm=sn)
                    for n, (i, s, sn) in enumerate(zip(r["ids"], r["scores"], r["score_norm"]), start=1)]
    return out, digest


def dense_model() -> tuple[str, str]:
    """(modello, revisione) scelti dalla regola della voce 107 (esito in config_dense.yaml, voce 108)."""
    esito = yaml.safe_load(DENSE_CONFIG.read_text(encoding="utf-8"))["esito"]
    return esito["scelto"], esito["revisione"]


class PromptBuilder:
    POOLS = ("all", "corpus60")

    def __init__(self, candidates: list[dict] | None = None, queries: list[dict] | None = None, dense=None,
                 pool: str = "all", retrieval_source: str = "live", frozen_path: Path | None = None):
        """dense: retriever denso gia' costruito (i test passano embedding finti); None = quello di config_dense.yaml,
        caricato solo alla prima condizione dense / hybrid. retrieval_source: "live" | "frozen" (voce 129)."""
        if candidates is None:
            candidates, queries = cl.load_all()
        else:
            if queries is None:  # pool unico (voce 115): il test set entra sempre tra i candidati
                queries = cl.load_queries()
            cl.check_disjoint(candidates, queries)  # corpus.jsonl senza esercizi del test set (invariato)
        if pool not in self.POOLS:
            raise ValueError(f"pool sconosciuto: {pool} (ammessi: {self.POOLS})")
        # pool (voce 123): "all" = pool unico della voce 115 (default); "corpus60" = solo gli esercizi del corpus come
        # candidati, per QUALUNQUE query (anche De Bari), leave-one-out sulle query del corpus
        self.pool_mode = pool
        self.candidates = candidates
        self.by_id = {c["id"]: c for c in candidates}  # SOLO il corpus (is_corpus_query, esempi statici)
        self.test_queries = list(queries or [])
        self.test_ids = {q["id"] for q in self.test_queries}
        self.all_by_id = {**self.by_id, **{q["id"]: q for q in self.test_queries}}  # esempi: corpus + test set (voce 112)
        cfg = yaml.safe_load(BM25_CONFIG.read_text(encoding="utf-8"))
        if not cfg.get("frozen"):
            raise SystemExit("retrieval/config_bm25.yaml non congelata")
        r, p = cfg["retriever"], cfg["preprocessing"]
        self._bm25_args = {"k1": r["k1"], "b": r["b"], "preprocess": PreprocessConfig(p["stopwords"], p["stemming"])}
        self._loo_bm25: dict[str, KeywordRetriever] = {}  # indice rifittato per query (LOO), corpus e test set
        self.static = static_examples(self.by_id)
        self.instructions = _template("v4_instructions.txt")  # formato apollon (identiche al template v4)
        self.instructions_by_format = {f: _template(t) for f, t in INSTRUCTION_TEMPLATES.items()}
        self.instructions_v5 = {f: _template(t) for f, t in V5_INSTRUCTION_TEMPLATES.items()}
        self.instructions_v5plan = {f: _template(t) for f, t in V5PLAN_INSTRUCTION_TEMPLATES.items()}
        self.instructions_v5b = {f: _template(t) for f, t in V5B_INSTRUCTION_TEMPLATES.items()}
        self.instructions_v5c = {f: _template(t) for f, t in V5C_INSTRUCTION_TEMPLATES.items()}
        self.names = {i: cl.class_names(c["diagram_apollon_json"]) for i, c in self.all_by_id.items()}
        self.tokens = {i: relevance.class_tokens(c["diagram_apollon_json"]) for i, c in self.all_by_id.items()}
        self._dense = dense
        self._dense_fitted = False
        if retrieval_source not in RETRIEVAL_SOURCES:
            raise ValueError(f"fonte del retrieval sconosciuta: {retrieval_source} (ammesse: {RETRIEVAL_SOURCES})")
        self.retrieval_source = retrieval_source
        self.frozen: dict[tuple, list[RetrievalResult]] = {}
        self.frozen_sha256: str | None = None
        if retrieval_source == "frozen":
            if pool != "all":
                raise ValueError("il file congelato e' costruito sul pool unico (pool: all)")
            self.frozen, self.frozen_sha256 = load_frozen(frozen_path or FROZEN_PATH)

    @property
    def dense(self):
        """Retriever denso indicizzato su corpus + test set (l'embedding di un documento non dipende dagli altri); le
        esclusioni si applicano in retrieve() con excluded(query), cosi' i candidati coincidono con pool(query)."""
        if self._dense is None:
            import os
            os.environ.setdefault("HF_HUB_OFFLINE", "1")  # dopo il primo download (voce 107) si lavora offline
            from dense_retriever import DenseRetriever
            self._dense = DenseRetriever(*dense_model())
        if not self._dense_fitted:
            self._dense.fit(self.candidates + self.test_queries)
            self._dense_fitted = True
        return self._dense

    def excluded(self, query: dict) -> set[str]:
        """Candidati NON ammessi per la query: il complemento di pool(query)."""
        allowed = {c["id"] for c in self.pool(query)}
        return {i for i in self.all_by_id if i not in allowed}

    def is_corpus_query(self, query: dict) -> bool:
        return query["id"] in self.by_id

    def pool(self, query: dict) -> list[dict]:
        """Candidati ammessi (leave-one-out sul pool unico, voce 115): tutti gli esercizi (corpus + test set) tranne la
        query stessa."""
        if query["id"] not in self.all_by_id:
            raise ValueError(f"query {query['id']} non presente tra gli esercizi del builder: pool non definito")
        if self.pool_mode == "corpus60":  # voce 123: solo i 60 del corpus, mai la query
            return [c for c in self.candidates if c["id"] != query["id"]]
        return [c for c in self.candidates + self.test_queries if c["id"] != query["id"]]

    def structure_for(self, query: dict, condition: str):
        """Retriever delle varianti della voce 120 indicizzato su pool(query) (rifittato per query, come bm25)."""
        key = (condition, query["id"])
        cache = self.__dict__.setdefault("_structure", {})
        if key not in cache:
            import structure_retrievers as sr
            base = lambda: KeywordRetriever(**self._bm25_args)  # noqa: E731
            make = {"struct": lambda: sr.RRF(base(), sr.StructureBM25()),
                    "construct": lambda: sr.ConstructBoost(base()),
                    "struct_construct": lambda: sr.ConstructBoost(sr.RRF(base(), sr.StructureBM25()))}[condition]
            cache[key] = make().fit(self.pool(query))
        return cache[key]

    def bm25_for(self, query: dict) -> KeywordRetriever:
        """Indice RIFITTATO su pool(query) (la query non entra nelle statistiche IDF / avgdl), per il corpus come in
        retrieval/analyze_retrieval.loo e per il test set in leave-one-out (voce 112)."""
        if query["id"] not in self._loo_bm25:
            self._loo_bm25[query["id"]] = KeywordRetriever(**self._bm25_args).fit(self.pool(query))
        return self._loo_bm25[query["id"]]

    @staticmethod
    def frozen_key(query_id: str, condition: str, k: int, seed: int) -> tuple:
        """Chiave del file congelato: il seme conta solo per random."""
        return (query_id, condition, k, seed if condition == "random" else None)

    def hits(self, query: dict, spec: PromptSpec) -> list[RetrievalResult]:
        """Risultati del retriever della condizione, nell'ordine del retriever (rango 1 = il piu' simile; random:
        ordine di estrazione). Unica fonte sia per select() sia per retrieval/freeze_retrievals.py (voce 129)."""
        c = spec.condition
        if self.retrieval_source == "frozen":
            if c not in FROZEN_CONDITIONS:
                raise ValueError(f"condizione {c} non congelata: retrieval_source frozen vale solo per {FROZEN_CONDITIONS}")
            key = self.frozen_key(query["id"], c, spec.k, spec.seed)
            if key not in self.frozen:
                raise KeyError(f"nel file congelato manca {key}")
            return self.frozen[key]
        if c == "random":
            return RandomRetriever(seed=spec.seed).fit(self.pool(query)).retrieve(query["description"], spec.k)
        if c == "bm25":
            return self.bm25_for(query).retrieve(query["description"], spec.k)
        if c == "dense":
            return self.dense.retrieve(query["description"], spec.k, exclude_ids=self.excluded(query))
        if c == "hybrid":
            from hybrid_retriever import HybridRetriever
            h = HybridRetriever.prefitted(self.bm25_for(query), self.dense, [x["id"] for x in self.pool(query)])
            return h.retrieve(query["description"], spec.k, exclude_ids=self.excluded(query))
        if c in STRUCTURE_CONDITIONS:
            return self.structure_for(query, c).retrieve(query["description"], spec.k, exclude_ids=self.excluded(query))
        raise ValueError(f"la condizione {c} non usa un retriever")

    def select(self, query: dict, spec: PromptSpec) -> list[dict]:
        """Esempi nell'ordine in cui compaiono nel prompt."""
        c = spec.condition
        if c == "zero_shot":
            return []
        if c == "oracle_self":  # voce 162: l'esercizio stesso, solo analisi
            q = self.all_by_id[query["id"]]
            if spec.strip_attributes:  # voce 167: classi e relazioni perfette, nessun attributo
                return [dict(q, view_id=q["id"], diagram_apollon_json=strip_attributes(q["diagram_apollon_json"]))]
            return [q]
        if c == "bm25_controllo":  # voce 167: gli esempi di bm25 (file congelato), eventualmente senza attributi
            hits = self.hits(query, replace(spec, condition="bm25", strip_attributes=False))
            exs = [self.all_by_id[h.id] for h in reversed(hits)]  # il piu' simile per ultimo, come bm25
            if spec.strip_attributes:
                exs = [dict(e, view_id=e["id"], diagram_apollon_json=strip_attributes(e["diagram_apollon_json"]))
                       for e in exs]
            return exs
        if c == "oracle_partial":  # voce 163: l'esercizio stesso con la soluzione degradata, solo analisi
            q = self.all_by_id[query["id"]]
            part = {"id": f"{q['id']}__parziale{round(spec.oracle_keep * 100)}", "view_id": q["id"],
                    "description": q["description"],
                    "diagram_apollon_json": degrade_diagram(q["diagram_apollon_json"], spec.oracle_keep, q["id"])}
            if spec.oracle_extra == "bm25_2":  # voce 164: 2 esempi bm25 (file congelato) prima dell'esempio parziale
                bm = replace(spec, condition="bm25", k=2, examples_block="standard", oracle_keep=1.0, oracle_extra="nessuno")
                return [self.all_by_id[h.id] for h in reversed(self.hits(query, bm))] + [part]
            if spec.oracle_extra == "complemento":  # voce 164: la meta' complementare dopo quella tenuta
                comp = dict(part, id=f"{q['id']}__complemento50",
                            diagram_apollon_json=degrade_diagram(q["diagram_apollon_json"], 0.5, q["id"], complement=True))
                return [part, comp]
            return [part]
        if c == "static":
            if query["id"] in {e["id"] for e in self.static}:
                raise ValueError(f"condizione static con la query {query['id']}: coincide con un esempio statico")
            return list(self.static)
        if c == "random":
            return [self.all_by_id[h.id] for h in self.hits(query, spec)]  # ordine di estrazione
        if c in ("bm25", "dense", "hybrid") or c in STRUCTURE_CONDITIONS:
            return [self.all_by_id[h.id] for h in reversed(self.hits(query, spec))]  # il piu' simile per ultimo
        if c == "oracle_jt":
            qt = relevance.class_tokens(query["diagram_apollon_json"])
            ranked = sorted(self.pool(query), key=lambda x: (-cl.jaccard(qt, self.tokens[x["id"]]), x["id"]))[:spec.k]
            return list(reversed(ranked))
        # oracle (solo analisi)
        qn = cl.class_names(query["diagram_apollon_json"])
        ranked = sorted(self.pool(query), key=lambda x: (-cl.jaccard(qn, self.names[x["id"]]), x["id"]))[:spec.k]
        return list(reversed(ranked))

    @staticmethod
    def render_example(example: dict, spec: PromptSpec) -> str:
        if spec.output_format == "plantuml":
            from plantuml_format import apollon_to_plantuml
            canonical = "v5" if spec.instructions_version in V5_FAMILY else spec.instructions_version
            return apollon_to_plantuml(example["diagram_apollon_json"], version=canonical)
        if spec.output_format == "compact":  # stessa serializzazione dell'Apollon (su una riga con "compact")
            from uml_structure import apollon_to_compact
            data = apollon_to_compact(example["diagram_apollon_json"])
            if spec.instructions_version == "v5c":
                data = explicit_attributes(data)
            return (json.dumps(data, ensure_ascii=False, separators=(",", ":")) if spec.serialization == "compact"
                    else json.dumps(data, ensure_ascii=False, indent=2))
        return serialize_diagram(example["diagram_apollon_json"], spec.serialization, spec.drop_interactive)

    def build(self, query: dict, spec: PromptSpec) -> BuiltPrompt:
        examples = self.select(query, spec)
        if query["id"] in {e["id"] for e in examples} and spec.condition != "oracle_self":  # voce 162: unica eccezione
            raise AssertionError(f"la query {query['id']} compare tra i propri esempi")
        if spec.condition in ORACLE_CONDITIONS and spec.instructions_version not in V5_FAMILY:
            raise ValueError(f"{spec.condition} solo con le istruzioni della famiglia v5 (voci 162-163)")
        item = _template(ITEM_TEMPLATES[spec.output_format])
        edits = example_view_edits(spec.example_view)  # voce 138: solo gli esempi, mai la traccia della query
        items = [item.format(n=i, description=apply_example_view(e.get("view_id", e["id"]), e["description"], edits).strip(),
                             diagram_json=self.render_example(e, spec))
                 for i, e in enumerate(examples, start=1)]
        block = (EXAMPLES_BLOCKS[spec.examples_block] if spec.instructions_version in V5_FAMILY
                 else "v4_examples_block.txt")  # voce 111; blocco "libero" della voce 162
        examples_block = _template(block).format(examples="\n".join(items)) if items else ""
        if spec.instructions_version in V5_FAMILY:
            final = V5PLAN_FINAL_LINE if spec.instructions_version == "v5plan" else V5_FINAL_LINE[spec.output_format]
            task = _template("v5_task.txt").format(description=query["description"].strip(), final_line=final)
        else:
            task = _template("v4_task.txt").format(description=query["description"].strip())
        user = (examples_block + "\n" if examples_block else "") + task
        instructions = (self.instructions_v5[spec.output_format] if spec.instructions_version == "v5"
                        else self.instructions_v5plan[spec.output_format] if spec.instructions_version == "v5plan"
                        else self.instructions_v5b[spec.output_format] if spec.instructions_version == "v5b"
                        else self.instructions_v5c[spec.output_format] if spec.instructions_version == "v5c"
                        else self.instructions_by_format[spec.output_format])
        if spec.instructions_variant == "targeted":
            instructions = targeted_instructions(instructions, spec.output_format)
        text = instructions + "\n" + user
        if spec.layout == "user_only":
            messages = [{"role": "user", "content": text}]
        else:
            messages = [{"role": "system", "content": instructions.rstrip("\n")}, {"role": "user", "content": user}]
        return BuiltPrompt(query_id=query["id"], spec=spec, example_ids=[e["id"] for e in examples],
                           instructions=instructions, examples_block=examples_block, task=task, text=text,
                           messages=messages, analysis_only=spec.condition in ANALYSIS_ONLY)
