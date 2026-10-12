"""
Confronto visivo di UN esercizio nel notebook (2026-10-12, voce 134): ground truth, risposta in PlantUML e risposta in
JSON compatto (o qualunque insieme di run) affiancati. Sola lettura, nessuna chiamata a un LLM.

Riusa experiments/review_report.py senza cambiarne la logica: stessa validazione del runner, stesso rendering per tutti
(struttura comune -> PlantUML canonico -> SVG con plantuml.jar locale, layout smetana; classi verdi = presenti nel GT,
arancioni = in piu'), stesse metriche per risposta (V, Vc, J, R, M) e stessa classificazione delle relazioni (corretta,
tipo sbagliato, direzione invertita, molteplicita' diverse, mancante, in piu'). Richiede Java e .tools/plantuml-old.jar.

Uso nel notebook:
    import compare_view as cv
    cv.exercises(["dev_g26__P-G", "dev_g26__C-G"])                  # esercizi disponibili
    cv.show("Boeing", ["dev_g26__P-G", "dev_g26__C-G"], rep=0)       # GT + PlantUML + compatto
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
import review_report as rr  # noqa: E402

RESULTS = rr.RESULTS
OUT = RESULTS / "confronti"  # pagine salvate (non versionate)


def exercises(runs: list[str], results: Path = RESULTS) -> list[str]:
    """Esercizi presenti in TUTTE le run indicate."""
    sets = []
    for run in runs:
        lines = (results / run / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        sets.append({json.loads(x)["query_id"] for x in lines if x})
    return sorted(set.intersection(*sets)) if sets else []


def page(query_id: str, runs: list[str], rep: int = 0, cond: str | None = None, k: int | None = None,
         results: Path = RESULTS, jar: Path = rr.DEFAULT_JAR) -> tuple[str, dict]:
    """Pagina HTML autonoma (quella di review_report) ristretta a un esercizio, una ripetizione e, se indicati, una
    condizione e un k."""
    items = [f"q={query_id}", f"rep={rep}"] + ([f"cond={cond}"] if cond else []) + ([f"k={k}"] if k is not None else [])
    filters = rr.parse_filters(items)
    import corpus_loader as cl
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates() + cl.load_queries()}
    calls = [c for run in runs for c in rr.load_run(results / run, filters, gt)]
    if not calls:
        raise SystemExit(f"nessuna risposta per {query_id} (ripetizione {rep}) nelle run {runs}")
    return rr.build(calls, jar, f"{query_id} · r{rep} · " + ", ".join(runs))


def show(query_id: str, runs: list[str], rep: int = 0, cond: str | None = None, k: int | None = None,
         height: int = 1100, save: bool = True):
    """Mostra la pagina nel notebook (iframe isolato: lo stile della pagina non tocca il notebook) e, se save, la salva
    in data/results/generation/confronti/<esercizio>__r<rep>.html per aprirla nel browser."""
    from IPython.display import HTML
    text, stats = page(query_id, runs, rep, cond, k)
    if save:
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"{query_id}__r{rep}{'__' + cond if cond else ''}{'__k' + str(k) if k is not None else ''}.html"
        path.write_text(text, encoding="utf-8")
        print(f"salvata in {path}")
    if stats["errors"]:
        print("avvisi del rendering:", stats["errors"])
    import warnings
    with warnings.catch_warnings():  # IPython suggerisce IFrame, che pero' vuole un URL: qui serve srcdoc
        warnings.simplefilter("ignore")
        return HTML(f'<iframe srcdoc="{html.escape(text, quote=True)}" style="width:100%;height:{height}px;border:0;'
                    f'background:#fff"></iframe>')
