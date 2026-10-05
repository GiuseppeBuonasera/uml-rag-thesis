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

Ogni esempio = description + JSON Apollon, serializzati allo stesso modo in tutte le condizioni. corpus/ e
config_bm25.yaml sono letti e mai scritti. Determinismo: stessa spec + stessa query -> stesso prompt byte per byte.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "retrieval"))
import corpus_loader as cl  # noqa: E402
from keyword_retriever import KeywordRetriever  # noqa: E402
from random_retriever import RandomRetriever  # noqa: E402
from text_preprocessing import PreprocessConfig  # noqa: E402

TEMPLATES = Path(__file__).resolve().parent / "templates"
V4_TEMPLATE = ROOT / "docs" / "dati" / "apollon_format_reference" / "prompt_template_v4.txt"
STATIC_DIR = ROOT / "docs" / "dati" / "apollon_format_reference"
BM25_CONFIG = ROOT / "retrieval" / "config_bm25.yaml"

CONDITIONS = ("zero_shot", "static", "random", "bm25", "oracle")
ANALYSIS_ONLY = {"oracle"}
SERIALIZATIONS = ("indent2", "compact")
LAYOUTS = ("user_only", "system_user")  # system_user disponibile, ma non si usa senza decisione (decisions.md, voce 64)


@dataclass(frozen=True)
class PromptSpec:
    condition: str
    k: int = 3  # ignorato da zero_shot (0) e static (2 esempi fissi)
    seed: int = 0  # solo random
    serialization: str = "compact"
    layout: str = "user_only"
    drop_interactive: bool = True  # toglie la chiave di primo livello "interactive" dagli esempi serializzati

    def __post_init__(self):
        if self.condition not in CONDITIONS:
            raise ValueError(f"condizione sconosciuta: {self.condition}")
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


def serialize_diagram(diagram: dict, serialization: str, drop_interactive: bool) -> str:
    d = {k: v for k, v in diagram.items() if not (drop_interactive and k == "interactive")}
    if serialization == "compact":
        return json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(d, ensure_ascii=False, indent=2)


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


class PromptBuilder:
    def __init__(self, candidates: list[dict] | None = None, queries: list[dict] | None = None):
        if candidates is None:
            candidates, queries = cl.load_all()
        else:
            cl.check_disjoint(candidates, queries or [])
        self.candidates = candidates
        self.by_id = {c["id"]: c for c in candidates}
        self.test_ids = {q["id"] for q in (queries or [])}
        cfg = yaml.safe_load(BM25_CONFIG.read_text(encoding="utf-8"))
        if not cfg.get("frozen"):
            raise SystemExit("retrieval/config_bm25.yaml non congelata")
        r, p = cfg["retriever"], cfg["preprocessing"]
        self.bm25 = KeywordRetriever(k1=r["k1"], b=r["b"],
                                     preprocess=PreprocessConfig(p["stopwords"], p["stemming"])).fit(candidates)
        self.static = static_examples(self.by_id)
        self.instructions = _template("v4_instructions.txt")
        self.names = {c["id"]: cl.class_names(c["diagram_apollon_json"]) for c in candidates}

    def select(self, query: dict, spec: PromptSpec) -> list[dict]:
        """Esempi nell'ordine in cui compaiono nel prompt."""
        c = spec.condition
        if c == "zero_shot":
            return []
        if c == "static":
            return list(self.static)
        if c == "random":
            hits = RandomRetriever(seed=spec.seed).fit(self.candidates).retrieve(query["description"], spec.k)
            return [self.by_id[h.id] for h in hits]  # ordine di estrazione
        if c == "bm25":
            hits = self.bm25.retrieve(query["description"], spec.k)
            return [self.by_id[h.id] for h in reversed(hits)]  # il piu' simile per ultimo
        # oracle (solo analisi)
        qn = cl.class_names(query["diagram_apollon_json"])
        ranked = sorted(self.candidates, key=lambda x: (-cl.jaccard(qn, self.names[x["id"]]), x["id"]))[:spec.k]
        return list(reversed(ranked))

    def build(self, query: dict, spec: PromptSpec) -> BuiltPrompt:
        examples = self.select(query, spec)
        leaked = [e["id"] for e in examples if e["id"] in self.test_ids or cl.DEBARI_ID_RE.match(e["id"])]
        if leaked:
            raise AssertionError(f"esercizi del test set tra gli esempi: {leaked}")
        item = _template("v4_example_item.txt")
        items = [item.format(n=i, description=e["description"].strip(),
                             diagram_json=serialize_diagram(e["diagram_apollon_json"], spec.serialization,
                                                            spec.drop_interactive))
                 for i, e in enumerate(examples, start=1)]
        examples_block = _template("v4_examples_block.txt").format(examples="\n".join(items)) if items else ""
        task = _template("v4_task.txt").format(description=query["description"].strip())
        user = (examples_block + "\n" if examples_block else "") + task
        text = self.instructions + "\n" + user
        if spec.layout == "user_only":
            messages = [{"role": "user", "content": text}]
        else:
            messages = [{"role": "system", "content": self.instructions.rstrip("\n")}, {"role": "user", "content": user}]
        return BuiltPrompt(query_id=query["id"], spec=spec, example_ids=[e["id"] for e in examples],
                           instructions=self.instructions, examples_block=examples_block, task=task, text=text,
                           messages=messages, analysis_only=spec.condition in ANALYSIS_ONLY)
