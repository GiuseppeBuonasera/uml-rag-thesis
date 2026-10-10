"""
Bilancio del contesto per il Passo 3b con i token REALI (2026-10-06). Nessuna chiamata a un LLM; legge un manifest
in sola lettura.

1. Fattore di correzione: per ogni prompt distinto del manifest (prompt_sha256), rapporto tra i token di prompt
   riportati dal server (tokenizer reale del modello) e la stima cl100k_base. Si riportano min / media / max; le
   proiezioni usano il MASSIMO (stima prudente).
2. Prompt del Passo 3b: i 20 esercizi del test set x condizione x k (come la dry run), token stimati x fattore.
3. Contro il contesto: prompt reale stimato + max_tokens <= contesto? Per condizione e k: esercizi che ci stanno e
   caso peggiore, con il margine.
4. Output del test set: ground truth compatti e indentati x fattore (riferimento per un max_tokens piu' basso), e il
   max_tokens massimo compatibile con il contesto per ogni condizione e k.

Modalita' --config (2026-10-09, voce 109): bilancio di un config dell'insieme di SVILUPPO (split corpus): i prompt
sono quelli degli esercizi del config, per ogni configurazione (formato) x condizione x k, con il contesto e il
max_tokens del config; il fattore e' il massimo sui manifest indicati con --manifest (ripetibile). Il test set NON si
legge in questa modalita'.

Uso:
    python experiments/context_budget.py [--manifest data/results/generation/<run>/manifest.jsonl]
                                         [--context 32768] [--max-tokens 12288] [--out file.md]
    python experiments/context_budget.py --config experiments/configs/dev_retrievers.yaml \
        --manifest data/results/generation/dev_k__P-G/manifest.jsonl --manifest data/results/generation/dev_k__C-G/manifest.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
from prompt_builder import PromptBuilder, PromptSpec, cl, serialize_diagram  # noqa: E402
from token_estimate import count_tokens  # noqa: E402

DEFAULT_MANIFEST = ROOT / "data" / "results" / "generation" / "pilot_temperature_gemma4-12b-qat" / "manifest.jsonl"
CONDITIONS = (("zero_shot", (0,)), ("static", (2,)), ("random", (1, 2, 3)), ("bm25", (1, 2, 3)), ("oracle", (1, 2, 3)))


def correction_factors(manifest: Path) -> dict:
    """Rapporti server / stima per prompt distinto (le ripetizioni dello stesso prompt contano una volta)."""
    by_prompt = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        if m.get("prompt_tokens_server") and m.get("prompt_tokens_est"):
            by_prompt[m["prompt_sha256"]] = (m["query_id"], m["prompt_tokens_est"], m["prompt_tokens_server"])
    if not by_prompt:
        raise SystemExit(f"{manifest}: nessuna chiamata con i token di prompt del server")
    ratios = [srv / est for _, est, srv in by_prompt.values()]
    return {"n_prompts": len(by_prompt), "min": min(ratios), "mean": statistics.mean(ratios), "max": max(ratios),
            "rows": sorted(by_prompt.values())}


def budget(factor: float, context: int, max_tokens: int) -> tuple[list[dict], dict]:
    candidates, queries = cl.load_all()
    builder = PromptBuilder(candidates, queries)
    rows = []
    for cond, ks in CONDITIONS:
        for k in ks:
            est = [count_tokens(builder.build(q, PromptSpec(cond, k=k)).text) for q in queries]
            real = [round(e * factor) for e in est]
            worst = max(real)
            rows.append({"condition": cond, "k": k, "est_max": max(est), "real_med": statistics.median(real),
                         "real_max": worst, "fit": sum(r + max_tokens <= context for r in real), "n": len(real),
                         "margin": context - (worst + max_tokens), "max_tokens_allowed": context - worst})
    gt_c = [count_tokens(serialize_diagram(q["diagram_apollon_json"], "compact", True)) for q in queries]
    gt_i = [count_tokens(serialize_diagram(q["diagram_apollon_json"], "indent2", True)) for q in queries]
    out = {"compact_max": max(gt_c), "indent_max": max(gt_i), "compact_max_real": round(max(gt_c) * factor),
           "indent_max_real": round(max(gt_i) * factor)}
    return rows, out


def report(manifest: Path, context: int, max_tokens: int) -> str:
    f = correction_factors(manifest)
    rows, out = budget(f["max"], context, max_tokens)
    L = [f"# Bilancio del contesto per il Passo 3b (token reali da `{manifest.relative_to(ROOT).as_posix()}`)", "",
         f"Fattore di correzione server / stima cl100k_base su {f['n_prompts']} prompt distinti: min "
         f"{f['min']:.3f}, media {f['mean']:.3f}, **max {f['max']:.3f}** (usato nelle proiezioni, prudente).", "",
         "| esercizio | stima cl100k_base | token reali (server) | rapporto |", "|---|---|---|---|"]
    L += [f"| {qid} | {est} | {srv} | {srv / est:.3f} |" for qid, est, srv in f["rows"]]
    L += ["", f"## Prompt del Passo 3b (20 esercizi del test set) + max_tokens {max_tokens} contro contesto {context}",
          "", "Token reali stimati = stima cl100k_base x fattore massimo. Margine = contesto - (prompt peggiore + "
          "max_tokens); negativo = non ci sta.", "",
          "| condizione | k | prompt reale stimato (mediana / max) | esercizi che stanno | margine nel caso peggiore | "
          "max_tokens massimo compatibile |", "|---|---|---|---|---|---|"]
    for r in rows:
        flag = "" if r["margin"] >= 0 else " **NON CI STA**"
        L.append(f"| {r['condition']} | {r['k']} | {r['real_med']:.0f} / {r['real_max']} | {r['fit']}/{r['n']} | "
                 f"{r['margin']}{flag} | {r['max_tokens_allowed']} |")
    L += ["", "## Output del test set (riferimento per max_tokens)", "",
          f"Ground truth massimo: compatto {out['compact_max']} (stima) -> ~{out['compact_max_real']} reali; indentato "
          f"{out['indent_max']} -> ~{out['indent_max_real']} reali (fattore massimo, applicato per analogia: il "
          "fattore è misurato sui prompt, non sulle risposte)."]
    return "\n".join(L) + "\n"


def report_config(config: Path, manifests: list[Path]) -> str:
    """Bilancio dei prompt di un config dell'insieme di sviluppo (split corpus, solo i suoi query_ids)."""
    import yaml
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    if cfg.get("split") != "corpus":
        raise SystemExit("--config solo per lo split corpus (insieme di sviluppo): il test set non si legge qui")
    contexts = {cfg["models"][c["model"]]["model_metadata"]["context_length"] for c in cfg["configurations"].values()}
    assert len(contexts) == 1, contexts
    context, max_tokens = contexts.pop(), cfg["generation"]["max_tokens"]
    fs = [correction_factors(m) for m in manifests]
    factor = max(f["max"] for f in fs)
    candidates = cl.load_candidates()
    builder = PromptBuilder(candidates)  # pool unico (voce 115): corpus + test set
    queries = [c for c in candidates if c["id"] in set(cfg["query_ids"])]
    assert len(queries) == len(cfg["query_ids"])
    p = cfg.get("prompt", {})
    L = [f"# Bilancio del contesto per `{config.relative_to(ROOT).as_posix()}`", "",
         f"Fattore server / stima cl100k_base: **max {factor:.3f}** su "
         + ", ".join(f"`{m.relative_to(ROOT).as_posix()}` ({f['n_prompts']} prompt, max {f['max']:.3f})"
                     for m, f in zip(manifests, fs))
         + f". Contesto {context}, max_tokens {max_tokens}: budget del prompt = {context - max_tokens}.", "",
         "| configurazione | condizione | k | prompt reale stimato (mediana / max) | esercizio peggiore | entro il budget | "
         "margine |", "|---|---|---|---|---|---|---|"]
    worst_all = 0
    for name, conf in cfg["configurations"].items():
        for cond in cfg["conditions"]:
            for k in cfg["k"]:
                spec = PromptSpec(cond, k=k, serialization=p.get("serialization", "compact"),
                                  layout=p.get("layout", "user_only"), drop_interactive=p.get("drop_interactive", True),
                                  output_format=conf["output_format"],
                                  instructions_variant=p.get("instructions_variant", "base"),
                                  instructions_version=p.get("instructions_version", "v4"))
                real = {q["id"]: round(count_tokens(builder.build(q, spec).text) * factor) for q in queries}
                wid = max(real, key=lambda i: (real[i], i))
                worst_all = max(worst_all, real[wid])
                fit = sum(v + max_tokens <= context for v in real.values())
                L.append(f"| {name} | {cond} | {k} | {statistics.median(real.values()):.0f} / {real[wid]} | {wid} | "
                         f"{fit}/{len(real)} | {context - max_tokens - real[wid]} |")
    L += ["", f"Prompt più lungo stimato: **{worst_all}** token reali, budget {context - max_tokens} "
          f"({'entro il budget' if worst_all + max_tokens <= context else '**OLTRE IL BUDGET**'})."]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", action="append")
    ap.add_argument("--context", type=int, default=32768)
    ap.add_argument("--max-tokens", type=int, default=12288)
    ap.add_argument("--config", help="config dell'insieme di sviluppo (split corpus): bilancio dei suoi prompt")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    manifests = [Path(m) for m in (a.manifest or [str(DEFAULT_MANIFEST)])]
    if a.config:
        text = report_config(Path(a.config).resolve(), [m.resolve() for m in manifests])
    else:
        text = report(manifests[0], a.context, a.max_tokens)
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
