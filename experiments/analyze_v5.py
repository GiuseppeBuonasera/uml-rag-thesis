"""
Analisi delle istruzioni v5 sull'insieme di sviluppo (docs/decisions.md, voce 111). Scritto e testato PRIMA della run
(sulla sola baseline): da qui la regola (ADOPT_R, ADOPT_R_FAM, INV_FACTOR, MAX_VC_LOSS, MAX_M_LOSS, adopt, outcome) e le
metriche R_fam e generalizzazioni invertite non si modificano senza una nuova voce.

Nessuna chiamata a un LLM. Per formato confronta la BASELINE v4 (Gemma 4 12B QAT, bm25 k = 3 di
data/results/generation/dev_v5base__P-G e __C-G, pool unico della voce 115; prima: dev_k) con il TRATTAMENTO v5 (dev_v5__P-G e __C-G: stessi parametri, esercizi ed
esempi, istruzioni v5). Validazione e metriche di experiments/analyze_instructions.py (V, Vc, J, R su TUTTE le risposte,
0 per le non valide; M primaria con le molteplicita' normalizzate di analyze_pilot.norm_mult, '1..1' = '1' dalla voce
111), ground truth ATTUALE del corpus. Scrive solo data/results/generation/dev_v5_analysis/summary.md.

METRICHE NUOVE (voce 111):
- R_fam (secondaria): come R, ma associazione e unidirezionale contano come lo stesso tipo (relazioni del GT accoppiate a
  una relazione della risposta con la stessa coppia di classi e lo stesso tipo o lo scambio associazione <->
  unidirezionale, su tutte le relazioni del GT di tutte le risposte);
- generalizzazioni invertite: generalizzazioni del GT accoppiate a una generalizzazione della risposta con figlia e madre
  scambiate (risposte valide). R non guarda il verso, quindi si riportano a parte.

REGOLA DI ADOZIONE (voce 111), per formato, delta = v5 - v4 su 40 risposte per parte:
  adottare v5 se [dR >= +0,03 OPPURE dR_fam >= +0,03 OPPURE (solo PlantUML) generalizzazioni invertite ridotte almeno
  della meta' (v5 <= v4 / 2, con v4 > 0)] E dVc >= -2 E dM_primaria >= -0,03.
  Controllo preliminare: baseline e trattamento completi (40 risposte), senza ragionamento, del modello del config;
  altrimenti quel formato non si decide.
Se v5 e' adottata in un formato, diventa la configurazione di lavoro per TUTTE le condizioni di quel formato.
Riportati fuori regola: classi in piu', generalizzazioni in piu', composizioni in piu', token di output, latenza,
scarti, tabelle di confusione.

Uso:
    python experiments/analyze_v5.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import analyze_dev as ad  # noqa: E402
import analyze_instructions as ai  # noqa: E402  (caricamento, metriche, confusione: riuso, nessuna modifica)
import analyze_pilot as ap  # noqa: E402
import run_experiment as rx  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
CONFIG = ROOT / "experiments" / "configs" / "dev_v5.yaml"
BASELINE_PREFIX, TREATMENT_PREFIX, K = "dev_v5base", "dev_v5", 3  # voce 115
OUT_NAME = "dev_v5_analysis"
CONFIGURATIONS = {"P-G": "plantuml", "C-G": "compact"}
FORMAT_NAME = ad.FORMAT_NAME
FAMILY_SWAPS = ("type ClassBidirectional -> ClassUnidirectional", "type ClassUnidirectional -> ClassBidirectional")
# --- regola (voce 111): non si modifica senza una nuova voce in docs/decisions.md ---
ADOPT_R = 0.03
ADOPT_R_FAM = 0.03
INV_FACTOR = 0.5  # generalizzazioni invertite: v5 <= v4 * 0,5 (solo PlantUML, con v4 > 0)
MAX_VC_LOSS = 2
MAX_M_LOSS = 0.03
EPS = 1e-9


# --- metriche -------------------------------------------------------------------------------------------------------


def r_fam(m: dict) -> float | None:
    rel = m["relations"]
    return ((rel["same_type"] + sum(rel[k] for k in FAMILY_SWAPS)) / m["gt_edges_all"]) if m["gt_edges_all"] else None


def extra_compositions(calls: list[dict]) -> int:
    """Composizioni della risposta (valide) la cui coppia di classi non e' una composizione nel GT."""
    n = 0
    for c in calls:
        if c["v"].level < 3:
            continue
        gt_comp = {e["pair"] for e in ap.edges(c["gt"]) if e["type"] == "ClassComposition"}
        n += sum(e["pair"] not in gt_comp for e in ap.edges(c["v"].diagram) if e["type"] == "ClassComposition")
    return n


def all_metrics(calls: list[dict]) -> dict:
    m = ai.metrics(calls)
    conf = ai.confusion(calls)
    m.update({"R_fam": r_fam(m), "inv_gen": conf["inv"]["generalizzazione"],
              "inv_gen_tot": conf["inv_tot"]["generalizzazione"], "extra_cls": conf["extra_cls"],
              "extra_gen": conf["extra_gen"], "extra_comp": extra_compositions(calls), "conf": conf})
    return m


# --- regola ---------------------------------------------------------------------------------------------------------


def adopt(base: dict, treat: dict, fmt: str) -> dict:
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    dr, drf = z(treat["R"]) - z(base["R"]), z(treat["R_fam"]) - z(base["R_fam"])
    dm, dvc = z(treat["M1"]) - z(base["M1"]), treat["Vc"] - base["Vc"]
    inv = fmt == "plantuml" and base["inv_gen"] > 0 and treat["inv_gen"] <= base["inv_gen"] * INV_FACTOR + EPS
    gain = dr >= ADOPT_R - EPS or drf >= ADOPT_R_FAM - EPS or inv
    keeps_vc, keeps_m = dvc >= -MAX_VC_LOSS, dm >= -MAX_M_LOSS - EPS
    return {"adopt": gain and keeps_vc and keeps_m, "dR": dr, "dR_fam": drf, "dM1": dm, "dVc": dvc, "inv_halved": inv,
            "gain": gain, "keeps_Vc": keeps_vc, "keeps_M": keeps_m}


def outcome(pairs: dict[str, tuple[dict, dict]]) -> dict:
    out = {"formats": {}}
    for f, (b, t) in pairs.items():
        excluded = {x["name"]: x["excluded"] for x in (b, t) if x["excluded"]}
        if excluded:
            out["formats"][f] = {"adopt": None, "excluded": excluded,
                                 "outcome": "STOP: formato non decidibile (controllo preliminare)"}
            continue
        d = adopt(all_metrics(b["calls"]), all_metrics(t["calls"]), f)
        d["outcome"] = "v5 ADOTTATA" if d["adopt"] else "v5 NON adottata (resta v4)"
        d["excluded"] = {}
        out["formats"][f] = d
    return out


# --- report ---------------------------------------------------------------------------------------------------------


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def report(pairs: dict[str, tuple[dict, dict]]) -> tuple[str, dict]:
    res = outcome(pairs)
    L = ["# Insieme di sviluppo — istruzioni v5 (`dev_v5` contro `dev_v5base` v4, k = 3)", "",
         "Esperimento di SVILUPPO sul corpus (20 esercizi, leave-one-out), mai sul test set. Gemma 4 12B QAT, versione di "
         "configurazione 2, bm25 k = 3, pool unico (voce 115). Baseline: `dev_v5base` (istruzioni v4); trattamento: `dev_v5` "
         "(istruzioni v5, riga finale della traccia, esempi PlantUML con l'ereditarietà nell'intestazione). Regola "
         "registrata PRIMA della run (voce 111) e applicata così com'è da `experiments/analyze_v5.py`; ground truth "
         "attuale del corpus; molteplicità normalizzate ('1..1' = '1'). Confronto per contenuto, mai per id.", "",
         provenance.provenance_line()]
    mism = {x["name"]: x["level_mismatch"] for p in pairs.values() for x in p if x["level_mismatch"]}
    if mism:
        L.append(f"**ATTENZIONE**: livello ricalcolato diverso dal manifest in {mism} risposte.")
    L += ["", "## Regola di adozione (voce 111), applicata così com'è", "",
          "Adottare v5 se [dR >= +0,03 OPPURE dR_fam >= +0,03 OPPURE (solo PlantUML) generalizzazioni invertite ridotte "
          "almeno della metà] E dVc >= -2 E dM_primaria >= -0,03 (delta = v5 - v4, 40 risposte per parte).", ""]
    for f, d in res["formats"].items():
        if d["adopt"] is None:
            L.append(f"- **{FORMAT_NAME[f]}: {d['outcome']}**")
            L += [f"  - esclusa {n}: {why}" for n, why in d["excluded"].items()]
            continue
        L.append(f"- **{FORMAT_NAME[f]}: {d['outcome']}** (dR {d['dR']:+.3f}, dR_fam {d['dR_fam']:+.3f}, "
                 f"generalizzazioni invertite dimezzate {'sì' if d['inv_halved'] else 'no'}"
                 f"{'' if f == 'plantuml' else ' (criterio solo PlantUML)'}; dVc {d['dVc']:+d}, dM_primaria "
                 f"{d['dM1']:+.3f}; guadagno {'sì' if d['gain'] else 'no'}, Vc mantenuto "
                 f"{'sì' if d['keeps_Vc'] else 'no'}, M mantenuto {'sì' if d['keeps_M'] else 'no'})")

    L += ["", "## Metriche per formato: v4 (baseline) contro v5", "",
          "J, R, R_fam, M su tutte le risposte (0 per le non valide). Generalizzazioni invertite: generalizzazioni del GT "
          "accoppiate con figlia e madre scambiate / generalizzazioni accoppiate dello stesso tipo.", "",
          "| formato | istruzioni | V | Vc | J | R | R_fam | M primaria | generalizzazioni invertite | verso uguale | "
          "classi in più | generalizzazioni in più | composizioni in più | scarti | troncate | completamento med | "
          "latenza med (s) |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f, (b, t) in pairs.items():
        for label, x in (("v4 (baseline)", b), ("v5", t)):
            if not x["calls"]:
                L.append(f"| {FORMAT_NAME[f]} | {label} |" + " — |" * 15)
                continue
            m = all_metrics(x["calls"])
            med = lambda key: statistics.median([c["m"][key] for c in x["calls"] if c["m"].get(key)] or [0])  # noqa
            mc = m["mult_counts"]
            L.append(f"| {FORMAT_NAME[f]} | {label} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {fmt(m['J'])} | "
                     f"{fmt(m['R'])} | {fmt(m['R_fam'])} | {fmt(m['M1'])} ({mc['explicit_same']}/{mc['explicit']}) | "
                     f"{m['inv_gen']}/{m['inv_gen_tot']} | {m['dir']} | {m['extra_cls']} | {m['extra_gen']} | "
                     f"{m['extra_comp']} | {m['discards']} | {m['truncated']} | {med('completion_tokens_server'):.0f} | "
                     f"{med('latency_s'):.1f} |")

    for f, (b, t) in pairs.items():
        if not b["calls"] or not t["calls"]:
            continue
        cb, ct = ai.confusion(b["calls"]), ai.confusion(t["calls"])
        L += ["", f"## Tabelle di confusione — {FORMAT_NAME[f]} (risposte valide)", "",
              "### Molteplicità per estremo (GT -> risposta), i casi più frequenti", "",
              "| GT -> risposta | v4 | v5 |", "|---|---|---|"]
        keys = sorted(set(cb["mult"]) | set(ct["mult"]), key=lambda k: (-(cb["mult"][k] + ct["mult"][k]), k))[:16]
        L += [f"| {a!r} -> {r!r}{'' if a == r else ' (errore)'} | {cb['mult'][(a, r)]} | {ct['mult'][(a, r)]} |"
              for a, r in keys]
        L += ["", "### Tipi di relazione (GT -> risposta, coppie accoppiate)", "", "| GT -> risposta | v4 | v5 |",
              "|---|---|---|"]
        keys = sorted(set(cb["types"]) | set(ct["types"]), key=lambda k: (-(cb["types"][k] + ct["types"][k]), k))
        L += [f"| {a} -> {r} | {cb['types'][(a, r)]} | {ct['types'][(a, r)]} |" for a, r in keys]
        L += ["", "### Verso (stesso tipo orientato): invertite / totale", "", "| tipo | v4 | v5 |", "|---|---|---|"]
        for ty in sorted(set(cb["inv_tot"]) | set(ct["inv_tot"])):
            L.append(f"| {ty} | {cb['inv'][ty]}/{cb['inv_tot'][ty]} | {ct['inv'][ty]}/{ct['inv_tot'][ty]} |")
    return "\n".join(L) + "\n", res


def load_pairs(results: Path) -> dict[str, tuple[dict, dict]]:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    out = {}
    for name, f in CONFIGURATIONS.items():
        model_id = rx.resolve_configuration(cfg, name)["model_metadata"]["model_id"]
        out[f] = (ai.load_run(results, BASELINE_PREFIX, name, gt, model_id, K),
                  ai.load_run(results, TREATMENT_PREFIX, name, gt, model_id))
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
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(path)


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
