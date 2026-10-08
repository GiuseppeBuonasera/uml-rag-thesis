"""
Calibrazione dei token di prompt per un modello (secondo pilota, 2026-10-07). Da lanciare con LM Studio aperto e il
modello caricato: e' una chiamata REALE ma brevissima (max_tokens = 1), senza generazione di diagrammi.

Per ogni esercizio della config e per ciascuno dei due formati (apollon e plantuml) costruisce il prompt del pilota
(bm25, k della config), lo invia con max_tokens = 1 e legge i token di prompt riportati dal server (tokenizer reale del
modello). Calcola il rapporto con la stima cl100k_base (min / mediana / max per formato) e verifica che
prompt reale + max_tokens <= contesto per ogni configurazione dello stesso modello.

Prima della prima chiamata verifica il contesto del modello caricato (come il runner). L'esito si salva in
docs/smoke_tests/<data>_<id-modello>_calibrationN.json (N progressivo, mai sovrascrivere).

k: il PIU' ALTO della config (caso peggiore; voce 94: dev_k.yaml ha k = 2, 3, 5, 8 -> si calibra con k = 8).
Formati: per default apollon e plantuml (secondo pilota); con --formats si sceglie l'elenco, es. per l'insieme di
sviluppo (voce 92) --formats plantuml compact.

Uso:
    python experiments/calibrate_tokens.py experiments/configs/pilot2_formats.yaml --configuration J-Q
    python experiments/calibrate_tokens.py experiments/configs/dev_formats.yaml --configuration C-Q --formats plantuml compact
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "generation"))
import run_experiment as rx  # noqa: E402
from llm_client import GenerationParams  # noqa: E402
from prompt_builder import PromptBuilder, PromptSpec, cl  # noqa: E402
from token_estimate import count_tokens  # noqa: E402

SAVE_DIR = ROOT / "docs" / "smoke_tests"


def next_path(save_dir: Path, date: str, model: str) -> Path:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", model).strip("-") or "modello"
    prefix = f"{date}_{slug}_calibration"
    used = [int(m.group(1)) for p in save_dir.glob(f"{prefix}*") if (m := re.fullmatch(re.escape(prefix) + r"(\d+)\.json", p.name))]
    return save_dir / f"{prefix}{max(used, default=0) + 1}.json"


DEFAULT_FORMATS = ("apollon", "plantuml")


def calibrate(cfg: dict, client, accept_unverified: bool = False, ask=input, formats=DEFAULT_FORMATS) -> dict:
    server_context = rx.check_server_context(client, cfg, accept_unverified, ask)
    candidates, queries = cl.load_all()
    builder = PromptBuilder(candidates, queries)
    gen = cfg["generation"]
    params = GenerationParams(temperature=0.0, top_p=gen["top_p"], top_k=gen["top_k"], max_tokens=1, seed=gen["seed"])
    by_id = {c["id"]: c for c in candidates}
    rows = []
    for fmt in formats:
        for qid in cfg["query_ids"]:
            bp = builder.build(by_id[qid], PromptSpec("bm25", k=max(cfg["k"]), output_format=fmt))
            res = client.generate(bp.messages, params)
            est = count_tokens(bp.text)
            rows.append({"format": fmt, "query_id": qid, "est": est, "real": res.prompt_tokens,
                         "ratio": res.prompt_tokens / est if res.prompt_tokens else None})
    context, max_tokens = cfg["model_metadata"]["context_length"], gen["max_tokens"]
    summary = {}
    for fmt in formats:
        rs = [r for r in rows if r["format"] == fmt and r["ratio"]]
        if not rs:
            summary[fmt] = {"error": "il server non riporta i token di prompt (usage.prompt_tokens)"}
            continue
        worst = max(r["real"] for r in rs)
        summary[fmt] = {"ratio_min": min(r["ratio"] for r in rs), "ratio_median": statistics.median(r["ratio"] for r in rs),
                        "ratio_max": max(r["ratio"] for r in rs), "prompt_real_max": worst,
                        "fits": worst + max_tokens <= context, "margin": context - (worst + max_tokens)}
    return {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "model": client.model, "k": max(cfg["k"]),
            "config_version": cfg.get("config_version", 1),
            "model_metadata": cfg["model_metadata"], "context_length": context, "max_tokens": max_tokens,
            "server_context": server_context, "rows": rows, "summary": summary}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--configuration", required=True, help="configurazione del modello da calibrare (es. J-Q)")
    ap.add_argument("--accept-unverified-context", action="store_true")
    ap.add_argument("--formats", nargs="+", default=list(DEFAULT_FORMATS), choices=["apollon", "plantuml", "compact"])
    ap.add_argument("--save-dir", default=str(SAVE_DIR), help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    cfg = rx.resolve_configuration(yaml.safe_load(Path(a.config).read_text(encoding="utf-8")), a.configuration)
    out = calibrate(cfg, rx.make_client(cfg), a.accept_unverified_context, formats=tuple(a.formats))
    for fmt, s in out["summary"].items():
        print(f"{fmt}: " + (s["error"] if "error" in s else
              f"rapporto reale / stima min {s['ratio_min']:.3f}, mediana {s['ratio_median']:.3f}, max {s['ratio_max']:.3f}; "
              f"prompt reale max {s['prompt_real_max']} + max_tokens {out['max_tokens']} "
              f"{'<=' if s['fits'] else '>'} {out['context_length']} (margine {s['margin']})"))
    save_dir = Path(a.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    path = next_path(save_dir, time.strftime("%Y-%m-%d"), out["model"])
    with path.open("x", encoding="utf-8") as f:  # mai sovrascrivere
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"salvato: {path}")
    return 0 if all(s.get("fits") for s in out["summary"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
