"""
Analisi della leva "numero di esempi k" sull'insieme di sviluppo (docs/decisions.md, voce 94). Scritto e testato
PRIMA delle run; la regola (K_VALUES, BASELINE_K, VC_TOLERANCE, R_TOLERANCE, choose_k, outcome) e' stata APPROVATA allo
STOP 2 (tolleranza su R portata a 0,03 dall'utente): da qui non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Legge in sola lettura data/results/generation/dev_k__<C>/ (C = P-G, C-G, P-Q, C-Q, versione
di configurazione 2) e ricalcola tutto dalle risposte grezze con la stessa validazione e le stesse metriche di
experiments/analyze_dev.py (V, Vc, J e R su TUTTE le risposte con 0 per le non valide; voce 92), importate senza
modificarle. Scrive solo data/results/generation/dev_k_analysis/summary.md.

REGOLA (APPROVATA, voce 94), per ciascun formato e ciascun modello separatamente (40 risposte per k: 20 esercizi x 2
ripetizioni):
  0. controllo preliminare: la configurazione (formato, modello) deve essere completa (160 risposte, tutti i k), non
     fermata per ragionamento e del modello del config; altrimenti quel formato non si decide (STOP per il formato).
     Piu' di 2 troncamenti su 40 per un k: segnalato, non blocca;
  1. k AMMISSIBILI: quelli con Vc(k) >= Vc(2) - 2 (Vc = valide fino a L3 e senza scarti; k = 2 sempre ammissibile);
  2. R* = il miglior R tra i k ammissibili (R non definito = 0);
  3. k scelto = il PIU' PICCOLO k ammissibile con R(k) >= R* - 0,03 (a parita' di qualita', meno token; soglia
     coerente con quella di R della voce 92).
  Per formato: se Gemma e Qwen danno lo stesso k, quello e' il k del formato; se diverso, "dipende dal modello" (STOP,
  decide l'utente). I due formati possono avere k diversi.
Riportati ma fuori dalla regola, per ogni k: V, J (tutte e sole valide), R sulle valide, molteplicita' corrette, verso
delle relazioni, scarti, troncamenti, token di prompt e di completamento, latenza; andamento per fascia di score_norm.
Nota (voce 94): la leva vale solo per le condizioni con esempi; sul test set il confronto con random dovra' usare lo
stesso k.

Uso:
    python experiments/analyze_k.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import analyze_dev as ad  # noqa: E402  (validazione e metriche della voce 92, non modificate)
import plantuml_postprocess as ppu  # noqa: E402
import run_experiment as rx  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402  (riga di provenienza, voce 106)

RESULTS = ROOT / "data" / "results" / "generation"
CONFIG = ROOT / "experiments" / "configs" / "dev_k.yaml"
RUN_PREFIX = "dev_k"
OUT_NAME = "dev_k_analysis"
CONFIGURATIONS = {"P-G": ("plantuml", "G"), "C-G": ("compact", "G"), "P-Q": ("plantuml", "Q"), "C-Q": ("compact", "Q")}
FORMATS = ("plantuml", "compact")
FORMAT_NAME = ad.FORMAT_NAME
MODEL_NAME = ad.MODEL_NAME
# --- regola (voce 94, APPROVATA allo STOP 2): non si modifica senza una nuova voce in docs/decisions.md ---
K_VALUES = (2, 3, 5, 8)
BASELINE_K = 2
VC_TOLERANCE = 2  # Vc(k) >= Vc(2) - 2 risposte su 40
R_TOLERANCE = 0.03  # R(k) >= R* - 0,03 (STOP 2: 0,03, non 0,02)
MAX_TRUNCATED = 2  # piu' di 2 troncamenti su 40 per k: segnalato
EPS = 1e-9


# --- caricamento ----------------------------------------------------------------------------------------------------


def expected_model_ids(config_path: Path = CONFIG) -> dict[str, str]:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return {n: rx.resolve_configuration(cfg, n)["model_metadata"]["model_id"] for n in cfg["configurations"]}


def load_configuration(results: Path, name: str, gt: dict[str, dict], expected_model_id: str | None = None) -> dict:
    fmt, model = CONFIGURATIONS[name]
    run_dir = results / f"{RUN_PREFIX}__{name}"
    info = {"name": name, "format": fmt, "model": model, "cfg": None, "calls": [], "expected": None,
            "excluded": None, "level_mismatch": 0}
    if not (run_dir / "config.json").exists():
        info["excluded"] = f"non eseguita (nessun config.json in {run_dir.name}/)"
        return info
    saved = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    cfg, prov = saved["config"], saved.get("provenance", {})
    if cfg.get("configuration") != name:
        raise SystemExit(f"{run_dir}: config.json riporta la configurazione {cfg.get('configuration')!r}, non {name}")
    run_model = (cfg.get("model_metadata") or {}).get("model_id")
    if expected_model_id is not None and run_model != expected_model_id:
        info["excluded"] = f"run di {run_model}, non del modello del config attuale ({expected_model_id}): traccia NON usata"
        return info
    if sorted(cfg["k"]) != list(K_VALUES):
        raise SystemExit(f"{run_dir}: k della run {cfg['k']} diversi da {list(K_VALUES)}")
    info["cfg"] = cfg
    version = prov.get("plantuml_postprocess_version", ppu.DEFAULT_VERSION)
    info["expected"] = len(cfg["query_ids"]) * cfg.get("repetitions", 1) * len(cfg["conditions"]) * len(cfg["k"])
    mpath = run_dir / "manifest.jsonl"
    manifest = [json.loads(x) for x in mpath.read_text(encoding="utf-8").splitlines() if x] if mpath.exists() else []
    for m in manifest:
        raw = json.loads((run_dir / "raw" / f"{m['call_id']}.json").read_text(encoding="utf-8"))
        v = ad.validate(fmt, raw["text"], raw["finish_reason"], m["call_id"], version)
        info["level_mismatch"] += v.level != m.get("level")
        info["calls"].append({"m": m, "raw": raw, "v": v, "gt": gt[m["query_id"]], "q": m["query_id"],
                              "r": m["repetition"], "k": m["k"], "format": fmt, "model": model})
    if any(m.get("reasoning_field") or m.get("reasoning_markers_in_content") for m in manifest):
        info["excluded"] = "fermata per ragionamento (stop_on_reasoning)"
    elif len(manifest) < info["expected"]:
        info["excluded"] = f"incompleta ({len(manifest)}/{info['expected']} risposte): riprenderla con --resume"
    elif len(manifest) > info["expected"]:
        raise SystemExit(f"{run_dir}: {len(manifest)} risposte nel manifest, attese {info['expected']}")
    return info


# --- regola ---------------------------------------------------------------------------------------------------------


def _r(m: dict) -> float:
    return 0.0 if m["R"] is None else m["R"]


def choose_k(by_k: dict[int, dict]) -> dict:
    """by_k: k -> metriche (analyze_dev.metrics) su 40 risposte di un formato e un modello."""
    base_vc = by_k[BASELINE_K]["Vc"]
    admissible = [k for k in K_VALUES if by_k[k]["Vc"] >= base_vc - VC_TOLERANCE]
    best = max(_r(by_k[k]) for k in admissible)
    within = [k for k in admissible if _r(by_k[k]) >= best - R_TOLERANCE - EPS]
    return {"k": min(within), "admissible": admissible, "excluded": [k for k in K_VALUES if k not in admissible],
            "best_R": best, "within": within, "base_Vc": base_vc}


def outcome(infos: dict[str, dict]) -> dict:
    out = {"formats": {}, "warnings": [], "per_model": {}}
    for n, i in infos.items():
        for k in K_VALUES:
            t = sum(bool(c["v"].truncated) for c in i["calls"] if c["k"] == k)
            if t > MAX_TRUNCATED:
                out["warnings"].append(f"{n}, k={k}: {t} risposte troncate su 40 (soglia di segnalazione: piu' di "
                                       f"{MAX_TRUNCATED})")
    for f in FORMATS:
        names = [n for n, (ff, _) in CONFIGURATIONS.items() if ff == f]
        excluded = {n: infos[n]["excluded"] for n in names if infos[n]["excluded"]}
        if excluded:
            out["formats"][f] = {"k": None, "outcome": "STOP: formato non decidibile (controllo preliminare)",
                                 "excluded": excluded}
            continue
        chosen = {}
        for n in names:
            mk = CONFIGURATIONS[n][1]
            by_k = {k: ad.metrics([c for c in infos[n]["calls"] if c["k"] == k]) for k in K_VALUES}
            out["per_model"][(f, mk)] = dict(choose_k(by_k), by_k=by_k)
            chosen[mk] = out["per_model"][(f, mk)]["k"]
        if len(set(chosen.values())) == 1:
            k = chosen["G"]
            out["formats"][f] = {"k": k, "outcome": f"k = {k}", "excluded": {}}
        else:
            out["formats"][f] = {"k": None, "excluded": {},
                                 "outcome": f"STOP: dipende dal modello (Gemma k = {chosen['G']}, Qwen k = "
                                            f"{chosen['Q']}): decisione dell'utente"}
    return out


# --- report ---------------------------------------------------------------------------------------------------------


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def secondary(calls: list[dict]) -> dict:
    """Metriche fuori dalla regola per un gruppo di risposte (stesso formato, modello e k)."""
    m = ad.metrics(calls)
    rel = m["relations"]
    disc = sum(len(getattr(c["v"], "discarded_lines", [])) + len(getattr(c["v"], "compact_issues", [])) for c in calls)
    med = lambda xs: statistics.median(xs) if xs else None  # noqa: E731
    pt = [c["m"].get("prompt_tokens_server") for c in calls if c["m"].get("prompt_tokens_server")]
    ct = [c["m"].get("completion_tokens_server") for c in calls if c["m"].get("completion_tokens_server")]
    lat = [c["m"].get("latency_s") for c in calls if c["m"].get("latency_s") is not None]
    return {**m, "mult": f"{rel['same_mult']}/{rel['mult_compared']}",
            "dir": f"{rel['same_direction']}/{rel['directional_same_type']}", "discards": disc,
            "prompt_med": med(pt), "prompt_max": max(pt) if pt else None, "compl_med": med(ct),
            "lat_med": med(lat)}


def report(infos: dict[str, dict], band_of: dict[str, str] | None = None) -> tuple[str, dict]:
    res = outcome(infos)
    L = ["# Insieme di sviluppo — numero di esempi k (`dev_k`)", "",
         "Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set; versione di configurazione 2 "
         "(contesto 32768, max_tokens 4096). Regola registrata PRIMA delle run (docs/decisions.md, voce 94) e applicata "
         "cosi' com'e' da `experiments/analyze_k.py`; metriche della voce 92 (J e R su tutte le risposte, 0 per le non "
         "valide). Confronto per contenuto, mai per id. La leva vale solo per le condizioni con esempi: sul test set "
         "il confronto con random dovra' usare lo stesso k.", "",
         provenance.provenance_line()]  # commit e impronta del GT (voce 106)
    mism = {n: i["level_mismatch"] for n, i in infos.items() if i["level_mismatch"]}
    if mism:
        L.append(f"**ATTENZIONE**: livello ricalcolato diverso dal manifest in {mism} risposte.")
    L += ["", "## Regola di scelta di k (voce 94), applicata cosi' com'e'", ""]
    for f in FORMATS:
        r = res["formats"][f]
        L.append(f"- **{FORMAT_NAME[f]}: {r['outcome']}**")
        L += [f"  - esclusa {n}: {why}" for n, why in r["excluded"].items()]
    L += [f"- segnalazione: {w}" for w in res["warnings"]]

    for f in FORMATS:
        for mk in ("G", "Q"):
            d = res["per_model"].get((f, mk))
            if not d:
                continue
            L += ["", f"### {FORMAT_NAME[f]} — {MODEL_NAME[mk]} (40 risposte per k)", "",
                  f"Vc(k=2) = {d['base_Vc']}: ammissibili i k con Vc >= {d['base_Vc'] - VC_TOLERANCE}; R* = "
                  f"{fmt(d['best_R'])} tra gli ammissibili; entro {R_TOLERANCE} da R*: k = {d['within']}; scelto il piu' "
                  f"piccolo: **k = {d['k']}**.", "",
                  "| k | ammissibile | Vc | V | R | J | R_valide | J_valide | molteplicita' uguali | verso uguale | "
                  "scarti | troncate | prompt reale (med / max) | completamento med | latenza med (s) |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
            n = next(n for n, (ff, m) in CONFIGURATIONS.items() if ff == f and m == mk)
            for k in K_VALUES:
                s = secondary([c for c in infos[n]["calls"] if c["k"] == k])
                L.append(f"| {k} | {'si' if k in d['admissible'] else 'no'} | {s['Vc']}/{s['n']} | {s['V']}/{s['n']} | "
                         f"{fmt(s['R'])} | {fmt(s['J'])} | {fmt(s['R_valid'])} | {fmt(s['J_valid'])} | {s['mult']} | "
                         f"{s['dir']} | {s['discards']} | {s['truncated']} | {fmt(s['prompt_med'], 0)} / "
                         f"{fmt(s['prompt_max'])} | {fmt(s['compl_med'], 0)} | {fmt(s['lat_med'], 1)} |")

    if band_of:
        L += ["", "## Andamento per fascia di score_norm (solo descrittivo)", "",
              "R / Vc per fascia (risposte per cella: esercizi della fascia x 2 ripetizioni).", "",
              "| formato | modello | fascia | " + " | ".join(f"k={k}: R / Vc" for k in K_VALUES) + " |",
              "|---|---|---|" + "---|" * len(K_VALUES)]
        for n, i in infos.items():
            if not i["calls"]:
                continue
            for b in ("basso", "medio", "alto"):
                cells = []
                for k in K_VALUES:
                    cs = [c for c in i["calls"] if c["k"] == k and band_of.get(c["q"]) == b]
                    m = ad.metrics(cs) if cs else None
                    cells.append(f"{fmt(m['R'])} / {m['Vc']}/{m['n']}" if m else "—")
                L.append(f"| {FORMAT_NAME[i['format']]} | {MODEL_NAME[i['model']]} | {b} | " + " | ".join(cells) + " |")

    L += ["", "## Fallimenti per configurazione e k", ""]
    for n, i in infos.items():
        if not i["calls"]:
            L.append(f"- {n}: {i['excluded']}")
            continue
        for k in K_VALUES:
            cnt = Counter(c["v"].failure or "nessuno (L4)" for c in i["calls"] if c["k"] == k)
            L.append(f"- {n}, k={k}: " + ", ".join(f"{a} {b}" for a, b in sorted(cnt.items())))
    return "\n".join(L) + "\n", res


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    models = expected_model_ids()
    infos = {n: load_configuration(results, n, gt, models[n]) for n in CONFIGURATIONS}
    text, _ = report(infos, ad.bands())
    out = results / OUT_NAME
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(text, encoding="utf-8")
    _set_output(out / "summary.md")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    print(f"scritto in {out / 'summary.md'}")
    return 0


def _set_output(path) -> None:
    """Registro delle esecuzioni (voce 102): dichiara l'uscita, se lo script e' lanciato da riga di comando."""
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(path)


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102): due righe in data/results/run_log.jsonl
    with run_log.logged(__file__):
        sys.exit(main())
