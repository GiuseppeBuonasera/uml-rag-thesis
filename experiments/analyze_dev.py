"""
Analisi dell'insieme di sviluppo: confronto dei formati PlantUML e JSON compatto (docs/decisions.md, voce 92; regola
approvata allo STOP 2 del 2026-10-08). Scritto e testato PRIMA delle run: da qui in poi la regola nel codice
(CRITERIA, soglie, TIE_WINNER, decide, outcome) NON si modifica senza una nuova voce in docs/decisions.md.

Nessuna chiamata a un LLM. Legge in sola lettura data/results/generation/dev_formats__<C>/ (C = P-G, P-Q, C-G, C-Q) e
ricalcola tutto dalle risposte grezze (raw/) con la stessa validazione del runner: PlantUML con il post-processing
registrato nella provenienza della run (v2), compatto con generation/compact_postprocess.py. Una run con un model_id
diverso dal config attuale non si usa (come in analyze_pilot2.py). Scrive solo
data/results/generation/dev_formats_analysis/summary.md.

METRICHE (per contenuto, mai per id), per formato su 80 risposte (2 modelli x 20 esercizi x 2 ripetizioni) e per
modello su 40:
- V  = risposte valide fino a L3; Vc = valide fino a L3 e senza scarti (P1 per PlantUML, C2 per il compatto);
- J  = media del Jaccard dei nomi di classe con il GT su TUTTE le risposte, 0 per quelle che non arrivano a L3;
- R  = relazioni del GT ritrovate con stessa coppia di classi e stesso tipo / relazioni del GT, sommate su TUTTE le
       risposte (una risposta che non arriva a L3 ritrova 0 relazioni; le sue relazioni del GT contano al denominatore);
- secondarie: J e R sulle sole valide, stessa coppia, verso, molteplicita', troncamenti, scarti e normalizzazioni,
  token e latenze, confronto appaiato, fasce di score_norm.

REGOLA (voce 92). Controllo preliminare: una configurazione non eseguita, incompleta o fermata per ragionamento -> STOP
senza decidere; piu' di 2 troncamenti su 40 in una configurazione -> segnalato (non blocca). Poi, per formato, i criteri
nell'ordine (vince il primo con differenza >= soglia; soglie sulle 80 risposte, tra parentesi per modello su 40):
  1. Vc >= 4 (2); 2. R >= 0,03 (0,03); 3. J >= 0,03 (0,03); 4. V >= 4 (2); 5. pareggio pieno -> PlantUML.
Coerenza tra i modelli: la stessa regola per ciascun modello; se i vincitori per Gemma e per Qwen sono diversi, l'esito
e' "dipende dal modello" e ci si ferma per una decisione. Altrimenti decide il confronto sulle 80 risposte (se diverso
dal vincitore comune dei due modelli lo si segnala, senza cambiare l'esito).

Uso:
    python experiments/analyze_dev.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import analyze_pilot as ap  # noqa: E402  (nomi di classe, confronto delle relazioni)
import compact_postprocess as cpp  # noqa: E402
import plantuml_postprocess as ppu  # noqa: E402
import run_experiment as rx  # noqa: E402
from prompt_builder import cl  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
CONFIG = ROOT / "experiments" / "configs" / "dev_formats.yaml"
RUN_PREFIX = "dev_formats"
OUT_NAME = "dev_formats_analysis"
CONFIGURATIONS = {"P-G": ("plantuml", "G"), "P-Q": ("plantuml", "Q"), "C-G": ("compact", "G"), "C-Q": ("compact", "Q")}
FORMATS = ("plantuml", "compact")
FORMAT_NAME = {"plantuml": "PlantUML", "compact": "JSON compatto"}
MODEL_NAME = {"G": "Gemma 4 12B QAT", "Q": "Qwen2.5-Coder 7B"}
# --- regola (voce 92): non si modifica senza una nuova voce in docs/decisions.md ---
# (metrica, descrizione, soglia sulle 80 risposte, soglia per modello sulle 40)
CRITERIA = (("Vc", "valide fino a L3 senza scarti", 4, 2),
            ("R", "relazioni del GT ritrovate (stessa coppia e tipo), su tutte le risposte", 0.03, 0.03),
            ("J", "Jaccard dei nomi di classe, su tutte le risposte", 0.03, 0.03),
            ("V", "valide fino a L3", 4, 2))
TIE_WINNER = "plantuml"  # pareggio pieno: la strada gia' adottata (voce 89)
MAX_TRUNCATED = 2  # piu' di 2 troncamenti su 40 in una configurazione: segnalato, non blocca
EPS = 1e-9


# --- caricamento ----------------------------------------------------------------------------------------------------


def validate(fmt: str, text: str, finish_reason: str | None, call_id: str, plantuml_version: str):
    if fmt == "plantuml":
        return ppu.validate_plantuml_response(text, finish_reason, call_id, plantuml_version)
    return cpp.validate_compact_response(text, finish_reason, call_id)


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
        info["excluded"] = (f"non eseguita con il modello del config attuale ({expected_model_id}): la run e' di "
                            f"{run_model}, traccia NON usata")
        return info
    info["cfg"] = cfg
    info["plantuml_version"] = prov.get("plantuml_postprocess_version", ppu.DEFAULT_VERSION)
    info["expected"] = len(cfg["query_ids"]) * cfg.get("repetitions", 1) * len(cfg["conditions"]) * len(cfg["k"])
    mpath = run_dir / "manifest.jsonl"
    manifest = [json.loads(x) for x in mpath.read_text(encoding="utf-8").splitlines() if x] if mpath.exists() else []
    for m in manifest:
        raw = json.loads((run_dir / "raw" / f"{m['call_id']}.json").read_text(encoding="utf-8"))
        v = validate(fmt, raw["text"], raw["finish_reason"], m["call_id"], info["plantuml_version"])
        info["level_mismatch"] += v.level != m.get("level")
        info["calls"].append({"m": m, "raw": raw, "v": v, "gt": gt[m["query_id"]], "q": m["query_id"],
                              "r": m["repetition"], "format": fmt, "model": model})
    if any(m.get("reasoning_field") or m.get("reasoning_markers_in_content") for m in manifest):
        info["excluded"] = "fermata per ragionamento (stop_on_reasoning)"
    elif len(manifest) < info["expected"]:
        info["excluded"] = (f"incompleta ({len(manifest)}/{info['expected']} risposte): non eseguibile, oppure "
                            "interrotta (riprenderla con --resume prima dell'analisi)")
    elif len(manifest) > info["expected"]:
        raise SystemExit(f"{run_dir}: {len(manifest)} risposte nel manifest, attese {info['expected']}")
    return info


# --- metriche -------------------------------------------------------------------------------------------------------


def is_valid(c: dict) -> bool:
    return c["v"].level >= 3


def is_clean(c: dict) -> bool:
    v = c["v"]
    return is_valid(c) and (v.P1_clean if c["format"] == "plantuml" else v.C2_clean)


def metrics(calls: list[dict]) -> dict:
    """Metriche della regola e secondarie su un insieme di risposte (una configurazione, un formato, un modello)."""
    n = len(calls)
    valid = [c for c in calls if is_valid(c)]
    jac = {id(c): cl.jaccard(ap.class_names(c["v"].diagram), ap.class_names(c["gt"])) for c in valid}
    rel = Counter()
    for c in valid:
        rel += ap.compare_relations(c["v"].diagram, c["gt"])
    gt_edges_all = sum(len(c["gt"]["edges"]) for c in calls)
    lat = [c["m"]["latency_s"] for c in calls if c["m"].get("latency_s") is not None]
    return {
        "n": n, "V": len(valid), "Vc": sum(is_clean(c) for c in calls),
        "J": sum(jac.values()) / n if n else None,  # 0 per le non valide
        "R": rel["same_type"] / gt_edges_all if gt_edges_all else None,  # 0 ritrovate per le non valide
        "J_valid": statistics.mean(jac.values()) if valid else None,
        "R_valid": rel["same_type"] / rel["gt_edges"] if rel["gt_edges"] else None,
        "truncated": sum(bool(c["v"].truncated) for c in calls),
        "relations": rel, "gt_edges_all": gt_edges_all,
        "latency_median": statistics.median(lat) if lat else None,
    }


# --- regola (voce 92) -----------------------------------------------------------------------------------------------


def decide(by_format: dict[str, dict], per_model: bool = False) -> dict:
    """Confronto PlantUML / compatto: i criteri nell'ordine; vince il primo con differenza >= soglia."""
    steps = []
    for key, desc, thr_all, thr_model in CRITERIA:
        thr = thr_model if per_model else thr_all
        a, b = by_format["plantuml"][key], by_format["compact"][key]
        a, b = (0.0 if a is None else a), (0.0 if b is None else b)
        diff = b - a  # compatto - PlantUML
        steps.append({"criterion": key, "description": desc, "plantuml": a, "compact": b, "diff": diff,
                      "threshold": thr})
        if abs(diff) >= thr - EPS:
            return {"winner": "compact" if diff > 0 else "plantuml", "decided_by": key, "steps": steps}
    return {"winner": TIE_WINNER, "decided_by": "pareggio pieno", "steps": steps}


def outcome(infos: dict[str, dict]) -> dict:
    """Controllo preliminare, decisione sulle 80 risposte e coerenza tra i modelli."""
    out = {"excluded": {n: i["excluded"] for n, i in infos.items() if i["excluded"]}, "warnings": [],
           "pooled": None, "per_model": {}, "winner": None, "outcome": None, "notes": []}
    for n, i in infos.items():
        t = sum(bool(c["v"].truncated) for c in i["calls"])
        if t > MAX_TRUNCATED:
            out["warnings"].append(f"{n}: {t} risposte troncate su {len(i['calls'])} (soglia di segnalazione: piu' di "
                                   f"{MAX_TRUNCATED})")
    if out["excluded"]:
        out["outcome"] = "STOP: nessuna decisione (controllo preliminare: configurazione esclusa)"
        return out
    calls = [c for i in infos.values() for c in i["calls"]]
    out["pooled"] = decide({f: metrics([c for c in calls if c["format"] == f]) for f in FORMATS})
    for mk in ("G", "Q"):
        out["per_model"][mk] = decide({f: metrics([c for c in calls if c["format"] == f and c["model"] == mk])
                                       for f in FORMATS}, per_model=True)
    winners = {d["winner"] for d in out["per_model"].values()}
    if len(winners) > 1:
        out["outcome"] = "STOP: dipende dal modello (vincitori diversi per Gemma e per Qwen): decisione dell'utente"
        return out
    out["winner"] = out["pooled"]["winner"]
    out["outcome"] = f"vince il formato {FORMAT_NAME[out['winner']]}"
    if winners != {out["winner"]}:
        out["notes"].append(f"il vincitore comune dei due modelli ({FORMAT_NAME[winners.pop()]}) e' diverso da quello "
                            "sulle 80 risposte: segnalato, l'esito resta quello sulle 80 (voce 92)")
    return out


# --- report ---------------------------------------------------------------------------------------------------------


def fmt(x, nd=3) -> str:
    if x is None:
        return "—"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def decision_table(d: dict, n_label: str) -> list[str]:
    L = [f"| criterio | PlantUML | compatto | compatto − PlantUML | soglia ({n_label}) |", "|---|---|---|---|---|"]
    for s in d["steps"]:
        nd = 0 if s["criterion"] in ("V", "Vc") else 3
        L.append(f"| {s['criterion']} ({s['description']}) | {fmt(float(s['plantuml']), nd)} | "
                 f"{fmt(float(s['compact']), nd)} | {s['diff']:+.{nd}f} | {s['threshold']} |")
    L.append(f"\nVincitore: **{FORMAT_NAME[d['winner']]}** (deciso da: {d['decided_by']}).")
    return L


def bands() -> dict[str, str]:
    import select_dev as sd
    from prompt_builder import PromptBuilder
    return {r["id"]: r["band"] for r in sd.select(PromptBuilder(*cl.load_all()))[0]}


def report(infos: dict[str, dict], band_of: dict[str, str] | None = None) -> tuple[str, dict]:
    res = outcome(infos)
    calls = [c for i in infos.values() for c in i["calls"]]
    L = ["# Insieme di sviluppo — PlantUML contro JSON compatto (`dev_formats`)", "",
         "Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set. Regola registrata PRIMA delle "
         "run (docs/decisions.md, voce 92) e applicata cosi' com'e' da `experiments/analyze_dev.py`, ricalcolando tutto "
         "dalle risposte grezze. Metriche di sviluppo: le metriche semantiche definitive restano da decidere con i "
         "relatori. Confronto per contenuto, mai per id. Modelli di taglia diversa (Gemma 4 12B QAT, Qwen2.5-Coder 7B, "
         "voce 85).", "",
         f"Analisi eseguita sul commit `{git('rev-parse', 'HEAD')[:12] or '?'}`"
         f"{' (con modifiche non committate)' if git('status', '--porcelain') else ''}."]
    mism = {n: i["level_mismatch"] for n, i in infos.items() if i["level_mismatch"]}
    if mism:
        L.append(f"**ATTENZIONE**: livello ricalcolato diverso dal manifest in {mism} risposte.")
    versions = {i.get("plantuml_version") for n, i in infos.items() if n.startswith("P") and i["cfg"]}
    if versions:
        L.append(f"Post-processing PlantUML: {', '.join(sorted(v for v in versions if v))}.")

    L += ["", "## Regola di confronto (voce 92), applicata cosi' com'e'", "", f"**Esito: {res['outcome']}**"]
    L += [f"- esclusa {n}: {why}" for n, why in res["excluded"].items()]
    L += [f"- segnalazione: {w}" for w in res["warnings"]]
    L += [f"- nota: {x}" for x in res["notes"]]
    if res["pooled"]:
        L += ["", "### Sulle 80 risposte per formato (2 modelli x 20 esercizi x 2 ripetizioni)", "",
              *decision_table(res["pooled"], "80 risposte")]
        for mk, d in res["per_model"].items():
            L += ["", f"### {MODEL_NAME[mk]} (40 risposte per formato)", "", *decision_table(d, "40 risposte")]

    # metriche per configurazione
    L += ["", "## Metriche per configurazione", "",
          "J e R della regola su TUTTE le risposte (0 per le non valide); J_valide e R_valide solo sulle valide (secondarie).",
          "", "| configurazione | V | Vc | J | R | J_valide | R_valide | troncate | latenza mediana (s) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for n, i in infos.items():
        if not i["calls"]:
            L.append(f"| {n} | — | — | — | — | — | — | — | — |")
            continue
        m = metrics(i["calls"])
        L.append(f"| {n} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {fmt(m['J'])} | {fmt(m['R'])} | "
                 f"{fmt(m['J_valid'])} | {fmt(m['R_valid'])} | {m['truncated']} | {fmt(m['latency_median'], 1)} |")

    L += ["", "### Livelli, fallimenti, scarti e normalizzazioni", "",
          "Livelli cumulativi: P0 / C0 trovato, P1b / C2b convertito (= L1), L2, L3, L4; pulite = P1 o C2 (senza scarti).",
          "", "| configurazione | trovato | convertito | L2 | L3 | L4 | pulite (L3 e senza scarti) | scarti (totale) |",
          "|---|---|---|---|---|---|---|---|"]
    for n, i in infos.items():
        cs = i["calls"]
        if not cs:
            L.append(f"| {n} | — | — | — | — | — | — | — |")
            continue
        disc = sum(len(getattr(c["v"], "discarded_lines", [])) + len(getattr(c["v"], "compact_issues", []))
                   for c in cs)
        L.append(f"| {n} | {sum(c['v'].L0_extracted for c in cs)} | " +
                 " | ".join(str(sum(c["v"].level >= x for c in cs)) for x in range(1, 5)) +
                 f" | {sum(is_clean(c) for c in cs)} | {disc} |")
    for n, i in infos.items():
        if not i["calls"]:
            continue
        fail = Counter(c["v"].failure or "nessuno (L4)" for c in i["calls"])
        issues = Counter(cat for c in i["calls"] for cat, _ in getattr(c["v"], "compact_issues", []))
        disc = Counter(d.split(":", 1)[-1].strip()[:60] for c in i["calls"] for d in getattr(c["v"], "discarded_lines", []))
        norm = Counter()
        for c in i["calls"]:
            norm.update(getattr(c["v"], "normalizations", {}) or {})
        L.append(f"- {n}: fallimenti " + ", ".join(f"{k} {v}" for k, v in sorted(fail.items())) +
                 (f"; scarti del compatto " + ", ".join(f"{k} {v}" for k, v in issues.most_common()) if issues else "") +
                 (f"; righe scartate piu' frequenti " + ", ".join(f"{k!r} {v}" for k, v in disc.most_common(5))
                  if disc else "") +
                 (f"; normalizzazioni " + ", ".join(f"{k} {v}" for k, v in sorted(norm.items())) if norm else ""))

    L += ["", "### Relazioni (risposte valide fino a L3)", "",
          "| configurazione | relazioni GT (tutte le risposte) | stessa coppia | stesso tipo | stesso verso (tipi orientati) "
          "| comp./aggr.: stesso verso | stesse molteplicita' |", "|---|---|---|---|---|---|---|"]
    for n, i in infos.items():
        if not i["calls"]:
            continue
        m = metrics(i["calls"])
        t = m["relations"]
        L.append(f"| {n} | {m['gt_edges_all']} | {t['same_pair']} | {t['same_type']} | "
                 f"{t['same_direction']}/{t['directional_same_type']} | "
                 f"{t['part_whole_same_direction']}/{t['part_whole_same_type']} | {t['same_mult']}/{t['mult_compared']} |")

    # confronto appaiato
    key = {(c["q"], c["model"], c["r"], c["format"]): c for c in calls}
    pairs = Counter()
    for (q, mk, r, f), c in key.items():
        if f != "plantuml" or (q, mk, r, "compact") not in key:
            continue
        o = key[(q, mk, r, "compact")]
        for label, ok in (("Vc", is_clean), ("V", is_valid)):
            a, b = ok(c), ok(o)
            pairs[(mk, label, "entrambe" if a and b else "solo PlantUML" if a else "solo compatto" if b else "nessuna")] += 1
    if pairs:
        L += ["", "### Confronto appaiato (stesso esercizio, modello e ripetizione; solo descrittivo)", "",
              "| modello | criterio | entrambe | solo PlantUML | solo compatto | nessuna |", "|---|---|---|---|---|---|"]
        for mk in ("G", "Q"):
            for label in ("Vc", "V"):
                L.append(f"| {MODEL_NAME[mk]} | {label} | " + " | ".join(
                    str(pairs[(mk, label, x)]) for x in ("entrambe", "solo PlantUML", "solo compatto", "nessuna")) + " |")

    if band_of:
        L += ["", "### Per fascia di score_norm (solo descrittivo)", "",
              "| formato | fascia | risposte | Vc | V | J | R |", "|---|---|---|---|---|---|---|"]
        for f in FORMATS:
            for b in ("basso", "medio", "alto"):
                cs = [c for c in calls if c["format"] == f and band_of.get(c["q"]) == b]
                if cs:
                    m = metrics(cs)
                    L.append(f"| {FORMAT_NAME[f]} | {b} | {m['n']} | {m['Vc']} | {m['V']} | {fmt(m['J'])} | {fmt(m['R'])} |")

    L += ["", "### Token e latenze", "",
          "| configurazione | prompt reale (min / mediana / max) | completamento (min / mediana / max) | latenza s "
          "(min / mediana / max) | durata (min) |", "|---|---|---|---|---|"]
    for n, i in infos.items():
        cs = i["calls"]
        if not cs:
            continue

        def tri(xs, nd=0):
            t = ap.stats3([x for x in xs if x is not None])
            return " / ".join(fmt(float(x) if x is not None else None, nd) for x in t)

        L.append(f"| {n} | {tri(c['m'].get('prompt_tokens_server') for c in cs)} | "
                 f"{tri(c['m'].get('completion_tokens_server') for c in cs)} | "
                 f"{tri((c['m'].get('latency_s') for c in cs), 1)} | "
                 f"{sum(c['m'].get('latency_s') or 0 for c in cs) / 60:.1f} |")
    return "\n".join(L) + "\n", res


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    models = expected_model_ids()
    infos = {n: load_configuration(results, n, gt, models[n]) for n in CONFIGURATIONS}
    text, _ = report(infos, bands())
    out = results / OUT_NAME
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(text, encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    print(f"scritto in {out / 'summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
