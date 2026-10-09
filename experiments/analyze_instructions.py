"""
Analisi della leva "istruzioni mirate" sull'insieme di sviluppo (docs/decisions.md, voci 96-99). Scritto e testato
PRIMA della run (anche sulla baseline esistente): da qui la regola (ADOPT_M, ADOPT_R, MAX_R_LOSS, MAX_VC_LOSS, adopt,
outcome) e la metrica M non si modificano senza una nuova voce.

Nessuna chiamata a un LLM. Confronta, per formato, la BASELINE (risposte di Gemma 4 12B QAT a k = 3 di
data/results/generation/dev_k__P-G e dev_k__C-G, versione di configurazione 2) con il TRATTAMENTO
(data/results/generation/dev_instructions__P-G e __C-G: stessi parametri, stessi esercizi, stessi esempi, istruzioni con
il blocco congelato). Tutto si ricalcola dalle risposte grezze con la validazione e le metriche di
experiments/analyze_dev.py (V, Vc, J e R su TUTTE le risposte, 0 per le non valide; voce 92) e con il ground truth
ATTUALE del corpus (dopo la correzione di eHome2020, voce 99). Scrive solo
data/results/generation/dev_instructions_analysis/summary.md.

METRICA M (voce 98): relazioni accoppiate come in analyze_pilot.compare_relations (1:1 per coppia di classi, prima lo
stesso tipo), molteplicita' normalizzate (n -> *, 0..* = *), esclusi gli estremi di generalizzazione e realizzazione:
- M primaria  = estremi del GT con molteplicita' ESPLICITA (non vuota) per cui la risposta ha la stessa molteplicita',
  su tutti gli estremi espliciti del GT di TUTTE le risposte (una risposta non valida, o una relazione non trovata,
  conta 0);
- M secondaria = lo stesso su TUTTI gli estremi del GT (un estremo vuoto nel GT e' uguale solo se vuoto anche nella
  risposta).

REGOLA DI ADOZIONE (invariata, voce 98), per ciascun formato, delta = trattamento - baseline su 40 risposte:
  adottare se (dM_primaria >= 0,05 OPPURE dR >= 0,03) E dR >= -0,03 E dVc >= -2.
  Controllo preliminare: baseline e trattamento completi (40 risposte), senza ragionamento, del modello del config;
  altrimenti quel formato non si decide. Se l'esito e' diverso tra i formati si adotta per il formato in cui passa e lo
  si segnala.
Riportati ma fuori dalla regola: verso, tipi, J, scarti, troncamenti, token e latenza; tabelle di confusione
(molteplicita', tipi, verso) per baseline e trattamento; classi e generalizzazioni in piu' rispetto al GT.

Uso:
    python experiments/analyze_instructions.py [--results-dir data/results/generation]
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
import analyze_pilot as ap  # noqa: E402  (edges, class_names, norm_mult)
import plantuml_postprocess as ppu  # noqa: E402
import run_experiment as rx  # noqa: E402
from prompt_builder import cl  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
CONFIG = ROOT / "experiments" / "configs" / "dev_instructions.yaml"
BASELINE_PREFIX, TREATMENT_PREFIX, BASELINE_K = "dev_k", "dev_instructions", 3
OUT_NAME = "dev_instructions_analysis"
CONFIGURATIONS = {"P-G": "plantuml", "C-G": "compact"}
FORMAT_NAME = ad.FORMAT_NAME
NO_MULT = ("ClassInheritance", "ClassRealization")
ORIENTED = ("ClassInheritance", "ClassRealization", "ClassComposition", "ClassAggregation", "ClassUnidirectional",
            "ClassDependency")
SHORT = {"ClassBidirectional": "associazione", "ClassUnidirectional": "unidirezionale", "ClassInheritance":
         "generalizzazione", "ClassRealization": "realizzazione", "ClassAggregation": "aggregazione",
         "ClassComposition": "composizione", "ClassDependency": "dipendenza"}
# --- regola (voce 98): non si modifica senza una nuova voce in docs/decisions.md ---
ADOPT_M = 0.05  # dM_primaria >= 0,05 ...
ADOPT_R = 0.03  # ... oppure dR >= 0,03
MAX_R_LOSS = 0.03  # e dR >= -0,03
MAX_VC_LOSS = 2  # e dVc >= -2 (su 40)
EPS = 1e-9


# --- caricamento ----------------------------------------------------------------------------------------------------


def load_run(results: Path, prefix: str, name: str, gt: dict[str, dict], model_id: str, k: int | None = None) -> dict:
    """Una run (baseline o trattamento) ristretta al k indicato; stato: esclusa o no, con il motivo."""
    fmt = CONFIGURATIONS[name]
    run_dir = results / f"{prefix}__{name}"
    info = {"name": f"{prefix}__{name}", "format": fmt, "calls": [], "excluded": None, "level_mismatch": 0}
    if not (run_dir / "config.json").exists():
        info["excluded"] = f"non eseguita (nessun config.json in {run_dir.name}/)"
        return info
    saved = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    cfg, prov = saved["config"], saved.get("provenance", {})
    if (cfg.get("model_metadata") or {}).get("model_id") != model_id:
        info["excluded"] = f"run di {(cfg.get('model_metadata') or {}).get('model_id')}, non di {model_id}"
        return info
    if rx.config_version(cfg) != 2:
        info["excluded"] = f"versione di configurazione {rx.config_version(cfg)}, attesa 2"
        return info
    version = prov.get("plantuml_postprocess_version", ppu.DEFAULT_VERSION)
    mpath = run_dir / "manifest.jsonl"
    manifest = [json.loads(x) for x in mpath.read_text(encoding="utf-8").splitlines() if x] if mpath.exists() else []
    manifest = [m for m in manifest if k is None or m["k"] == k]
    expected = len(cfg["query_ids"]) * cfg.get("repetitions", 1)
    for m in manifest:
        raw = json.loads((run_dir / "raw" / f"{m['call_id']}.json").read_text(encoding="utf-8"))
        v = ad.validate(fmt, raw["text"], raw["finish_reason"], m["call_id"], version)
        info["level_mismatch"] += v.level != m.get("level")
        info["calls"].append({"m": m, "raw": raw, "v": v, "gt": gt[m["query_id"]], "q": m["query_id"],
                              "r": m["repetition"], "format": fmt, "model": "G"})
    if any(m.get("reasoning_field") or m.get("reasoning_markers_in_content") for m in manifest):
        info["excluded"] = "fermata per ragionamento (stop_on_reasoning)"
    elif len(manifest) < expected:
        info["excluded"] = f"incompleta ({len(manifest)}/{expected} risposte): riprenderla con --resume"
    return info


# --- metriche -------------------------------------------------------------------------------------------------------


def match(resp: dict, gt: dict) -> tuple[list, list, list]:
    """Accoppiamento 1:1 per coppia di classi come analyze_pilot.compare_relations (prima lo stesso tipo).
    Ritorna (coppie (risposta, GT), relazioni del GT non accoppiate, relazioni della risposta non accoppiate)."""
    r_edges, g_edges = ap.edges(resp), ap.edges(gt)
    pairs = []
    for pair in sorted({e["pair"] for e in r_edges} & {e["pair"] for e in g_edges}, key=sorted):
        rs = [e for e in r_edges if e["pair"] == pair]
        gs = [e for e in g_edges if e["pair"] == pair]
        for same_type in (True, False):
            for r in list(rs):
                g = next((g for g in gs if (g["type"] == r["type"]) == same_type), None)
                if g is not None:
                    pairs.append((r, g))
                    rs.remove(r)
                    gs.remove(g)
    mg, mr = {id(g) for _, g in pairs}, {id(r) for r, _ in pairs}
    return pairs, [g for g in g_edges if id(g) not in mg], [r for r in r_edges if id(r) not in mr]


def gt_ends(g: dict) -> list[tuple[str, str]]:
    """Estremi (chiave, molteplicita' normalizzata) di una relazione del GT; vuoto per generalizzazione / realizzazione."""
    if g["type"] in NO_MULT:
        return []
    if "_self" in g["mult"]:
        return [("_src", g["mult"]["_self"][0]), ("_tgt", g["mult"]["_self"][1])]
    return [(g["src"], g["mult"][g["src"]]), (g["tgt"], g["mult"][g["tgt"]])]


def resp_mult(r: dict, key: str) -> str:
    if "_self" in r["mult"]:
        return r["mult"]["_self"][0 if key == "_src" else 1]
    return r["mult"].get(key, "")


def multiplicity_counts(c: dict) -> Counter:
    """Per una risposta: estremi del GT (espliciti e tutti) e quanti hanno la stessa molteplicita' nella risposta."""
    out = Counter()
    if c["v"].level >= 3:  # le relazioni del GT sono gli STESSI oggetti dell'accoppiamento (accoppiate + non accoppiate)
        pairs, missing, _ = match(c["v"].diagram, c["gt"])
        gt_edges = [(g, r) for r, g in pairs] + [(g, None) for g in missing]
    else:
        gt_edges = [(g, None) for g in ap.edges(c["gt"])]
    for g, r in gt_edges:
        for key, gm in gt_ends(g):
            same = r is not None and resp_mult(r, key) == gm
            out["all"] += 1
            out["all_same"] += same
            if gm:
                out["explicit"] += 1
                out["explicit_same"] += same
    return out


def metrics(calls: list[dict]) -> dict:
    m = ad.metrics(calls)
    mc = Counter()
    for c in calls:
        mc += multiplicity_counts(c)
    rel = m["relations"]
    m.update({"M1": mc["explicit_same"] / mc["explicit"] if mc["explicit"] else None,
              "M2": mc["all_same"] / mc["all"] if mc["all"] else None, "mult_counts": mc,
              "type_rate": rel["same_type"] / rel["same_pair"] if rel["same_pair"] else None,
              "dir": f"{rel['same_direction']}/{rel['directional_same_type']}",
              "discards": sum(len(getattr(c["v"], "discarded_lines", [])) + len(getattr(c["v"], "compact_issues", []))
                              for c in calls)})
    return m


# --- regola ---------------------------------------------------------------------------------------------------------


def adopt(base: dict, treat: dict) -> dict:
    """Regola di adozione della voce 98 per un formato (metriche su 40 risposte ciascuna)."""
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    dm, dr, dvc = z(treat["M1"]) - z(base["M1"]), z(treat["R"]) - z(base["R"]), treat["Vc"] - base["Vc"]
    gain = dm >= ADOPT_M - EPS or dr >= ADOPT_R - EPS
    keeps_r, keeps_vc = dr >= -MAX_R_LOSS - EPS, dvc >= -MAX_VC_LOSS
    return {"adopt": gain and keeps_r and keeps_vc, "dM1": dm, "dR": dr, "dVc": dvc, "gain": gain,
            "keeps_R": keeps_r, "keeps_Vc": keeps_vc}


def outcome(pairs: dict[str, tuple[dict, dict]]) -> dict:
    """pairs: formato -> (info baseline, info trattamento)."""
    out = {"formats": {}, "note": None}
    for f, (b, t) in pairs.items():
        excluded = {x["name"]: x["excluded"] for x in (b, t) if x["excluded"]}
        if excluded:
            out["formats"][f] = {"adopt": None, "excluded": excluded,
                                 "outcome": "STOP: formato non decidibile (controllo preliminare)"}
            continue
        d = adopt(metrics(b["calls"]), metrics(t["calls"]))
        d["outcome"] = "ADOTTATE" if d["adopt"] else "NON adottate"
        d["excluded"] = {}
        out["formats"][f] = d
    decided = {f: d["adopt"] for f, d in out["formats"].items() if d["adopt"] is not None}
    if len(set(decided.values())) > 1:
        out["note"] = ("esito diverso tra i formati: le istruzioni mirate si adottano solo per "
                       + ", ".join(FORMAT_NAME[f] for f, a in decided.items() if a) + " (voce 98)")
    return out


# --- report ---------------------------------------------------------------------------------------------------------


def confusion(calls: list[dict]) -> dict:
    """Tabelle di confusione (solo risposte valide): molteplicita' per estremo, tipi, verso; classi e generalizzazioni
    in piu' rispetto al GT."""
    mult, types, inv, inv_tot = Counter(), Counter(), Counter(), Counter()
    extra_cls = extra_gen = 0
    for c in calls:
        if c["v"].level < 3:
            continue
        pairs, _, _ = match(c["v"].diagram, c["gt"])
        for r, g in pairs:
            types[(SHORT[g["type"]], SHORT[r["type"]])] += 1
            if g["type"] not in NO_MULT and r["type"] not in NO_MULT:
                for key, gm in gt_ends(g):
                    mult[(gm or "(vuoto)", resp_mult(r, key) or "(vuoto)")] += 1
            if r["type"] == g["type"] and g["type"] in ORIENTED:
                inv_tot[SHORT[g["type"]]] += 1
                inv[SHORT[g["type"]]] += (r["src"], r["tgt"]) != (g["src"], g["tgt"])
        extra_cls += len(ap.class_names(c["v"].diagram) - ap.class_names(c["gt"]))
        g_inh = {(e["src"], e["tgt"]) for e in ap.edges(c["gt"]) if e["type"] == "ClassInheritance"}
        extra_gen += sum((e["src"], e["tgt"]) not in g_inh for e in ap.edges(c["v"].diagram)
                         if e["type"] == "ClassInheritance")
    return {"mult": mult, "types": types, "inv": inv, "inv_tot": inv_tot, "extra_cls": extra_cls, "extra_gen": extra_gen}


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def report(pairs: dict[str, tuple[dict, dict]]) -> tuple[str, dict]:
    res = outcome(pairs)
    L = ["# Insieme di sviluppo — istruzioni mirate (`dev_instructions` contro `dev_k`, k = 3)", "",
         "Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set. Gemma 4 12B QAT, versione di "
         "configurazione 2, bm25 k = 3. Baseline: risposte a k = 3 di `dev_k`; trattamento: `dev_instructions` (stessi "
         "prompt salvo il blocco congelato della voce 98). Regola registrata PRIMA della run (voce 98) e applicata cosi' "
         "com'e' da `experiments/analyze_instructions.py`; ground truth attuale del corpus (eHome2020 corretto, voce 99). "
         "Confronto per contenuto, mai per id.", "",
         f"Analisi eseguita sul commit `{ad.git('rev-parse', 'HEAD')[:12] or '?'}`"
         f"{' (con modifiche non committate)' if ad.git('status', '--porcelain') else ''}."]
    mism = {x["name"]: x["level_mismatch"] for p in pairs.values() for x in p if x["level_mismatch"]}
    if mism:
        L.append(f"**ATTENZIONE**: livello ricalcolato diverso dal manifest in {mism} risposte.")
    L += ["", "## Regola di adozione (voce 98), applicata cosi' com'e'", "",
          "Adottare se (dM_primaria >= 0,05 OPPURE dR >= 0,03) E dR >= -0,03 E dVc >= -2 (delta = trattamento - "
          "baseline, 40 risposte per parte).", ""]
    for f, d in res["formats"].items():
        if d["adopt"] is None:
            L.append(f"- **{FORMAT_NAME[f]}: {d['outcome']}**")
            L += [f"  - esclusa {n}: {why}" for n, why in d["excluded"].items()]
            continue
        L.append(f"- **{FORMAT_NAME[f]}: istruzioni mirate {d['outcome']}** (dM_primaria {d['dM1']:+.3f}, dR "
                 f"{d['dR']:+.3f}, dVc {d['dVc']:+d}; guadagno {'si' if d['gain'] else 'no'}, R mantenuto "
                 f"{'si' if d['keeps_R'] else 'no'}, Vc mantenuto {'si' if d['keeps_Vc'] else 'no'})")
    if res["note"]:
        L.append(f"- nota: {res['note']}")

    L += ["", "## Metriche per formato: baseline contro trattamento", "",
          "M primaria: estremi del GT con molteplicita' esplicita; M secondaria: tutti gli estremi del GT. J, R, M su tutte "
          "le risposte (0 per le non valide); J_valide e R_valide sulle sole valide.", "",
          "| formato | parte | V | Vc | J | R | M primaria | M secondaria | J_valide | R_valide | stesso tipo (coppie "
          "accoppiate) | verso uguale | scarti | troncate | prompt med | completamento med | latenza med (s) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f, (b, t) in pairs.items():
        for label, x in (("baseline", b), ("istruzioni mirate", t)):
            if not x["calls"]:
                L.append(f"| {FORMAT_NAME[f]} | {label} | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |")
                continue
            m = metrics(x["calls"])
            med = lambda key: statistics.median([c["m"][key] for c in x["calls"] if c["m"].get(key)] or [0])  # noqa
            mc = m["mult_counts"]
            L.append(f"| {FORMAT_NAME[f]} | {label} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {fmt(m['J'])} | "
                     f"{fmt(m['R'])} | {fmt(m['M1'])} ({mc['explicit_same']}/{mc['explicit']}) | {fmt(m['M2'])} "
                     f"({mc['all_same']}/{mc['all']}) | {fmt(m['J_valid'])} | {fmt(m['R_valid'])} | "
                     f"{fmt(m['type_rate'])} | {m['dir']} | {m['discards']} | {m['truncated']} | "
                     f"{med('prompt_tokens_server'):.0f} | {med('completion_tokens_server'):.0f} | {med('latency_s'):.1f} |")

    for f, (b, t) in pairs.items():
        if not b["calls"] or not t["calls"]:
            continue
        cb, ct = confusion(b["calls"]), confusion(t["calls"])
        L += ["", f"## Tabelle di confusione — {FORMAT_NAME[f]} (risposte valide)", "",
              "### Molteplicita' per estremo (GT -> risposta), i casi piu' frequenti", "",
              "| GT -> risposta | baseline | istruzioni mirate |", "|---|---|---|"]
        # a parita' di conteggio, ordine per chiave: senza, l'ordine dipendeva dall'insieme (hash variabile tra processi)
        keys = sorted(set(cb["mult"]) | set(ct["mult"]), key=lambda k: (-(cb["mult"][k] + ct["mult"][k]), k))[:16]
        L += [f"| {a!r} -> {r!r}{'' if a == r else ' (errore)'} | {cb['mult'][(a, r)]} | {ct['mult'][(a, r)]} |"
              for a, r in keys]
        L += ["", "### Tipi di relazione (GT -> risposta, coppie accoppiate)", "",
              "| GT -> risposta | baseline | istruzioni mirate |", "|---|---|---|"]
        keys = sorted(set(cb["types"]) | set(ct["types"]), key=lambda k: (-(cb["types"][k] + ct["types"][k]), k))
        L += [f"| {a} -> {r} | {cb['types'][(a, r)]} | {ct['types'][(a, r)]} |" for a, r in keys]
        L += ["", "### Verso (stesso tipo orientato): invertite / totale", "",
              "| tipo | baseline | istruzioni mirate |", "|---|---|---|"]
        for ty in sorted(set(cb["inv_tot"]) | set(ct["inv_tot"])):
            L.append(f"| {ty} | {cb['inv'][ty]}/{cb['inv_tot'][ty]} | {ct['inv'][ty]}/{ct['inv_tot'][ty]} |")
        L += ["", f"Classi in piu' rispetto al GT: baseline {cb['extra_cls']}, istruzioni mirate {ct['extra_cls']}; "
              f"generalizzazioni in piu' (assenti dal GT): baseline {cb['extra_gen']}, istruzioni mirate {ct['extra_gen']}."]
    return "\n".join(L) + "\n", res


def load_pairs(results: Path) -> dict[str, tuple[dict, dict]]:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    out = {}
    for name, f in CONFIGURATIONS.items():
        model_id = rx.resolve_configuration(cfg, name)["model_metadata"]["model_id"]
        out[f] = (load_run(results, BASELINE_PREFIX, name, gt, model_id, BASELINE_K),
                  load_run(results, TREATMENT_PREFIX, name, gt, model_id))
    return out


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    text, _ = report(load_pairs(results))
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
