"""
Leva "validita' del compatto" sull'insieme di sviluppo (docs/decisions.md, voce 119). Scritto e testato PRIMA della run
(sulla sola baseline): da qui la regola (MIN_VC_GAIN, ADOPT_R, MAX_R_LOSS, MAX_VC_LOSS, MAX_M_LOSS, MAX_TRUNCATED,
TIE, SIMPLICITY, admissible, outcome) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Confronta la BASELINE (Gemma 4 12B QAT, JSON compatto, istruzioni v4, bm25 k = 3, pool
unico: data/results/generation/dev_v5base__C-G) con tre varianti, stessi esercizi, esempi e parametri:
  indent  dev_cindent__C-G  esempi del compatto indentati (serialization indent2), generazione libera;
  schema  dev_cschema__C-G  generazione vincolata allo schema JSON del compatto (response_format), esempi su una riga;
  both    dev_cboth__C-G    entrambe.
Metriche di experiments/analyze_instructions.py (V, Vc, J, R su TUTTE le risposte, 0 per le non valide; M primaria).

REGOLA (voce 119), per ciascuna variante, delta = variante - baseline su 40 risposte:
  esclusa se i troncamenti per max_tokens sono 2 o piu' (controllo preliminare come voce 98: 40 risposte, niente
  ragionamento, modello del config; altrimenti non si decide);
  AMMISSIBILE se dM_primaria >= -0,03 E [ (dVc >= +4 E dR >= -0,03) OPPURE (dR >= +0,03 E dVc >= -2) ].
  Esito: tra le ammissibili si sceglie quella con R piu' alto; le ammissibili entro 0,01 dal migliore R sono in parita' e
  vince la piu' semplice (indent < schema < both). Nessuna ammissibile: resta la baseline.
  Le varianti con lo schema (generazione vincolata) restano SUBORDINATE alla domanda 14 per i relatori: se una di esse
  vince, si propone, non si adotta senza la loro risposta.
Riportato fuori regola: confronto con PlantUML v5 (dev_v5__P-G), motivi di invalidita', latenza e token.

Uso:
    python experiments/analyze_compact.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import analyze_dev as ad  # noqa: E402
import analyze_instructions as ai  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
MODEL_ID = "google/gemma-4-12b-qat"
K = 3
BASELINE = "dev_v5base"
VARIANTS = {"indent": "dev_cindent", "schema": "dev_cschema", "both": "dev_cboth"}
REFERENCE_PLANTUML = "dev_v5"  # PlantUML v5, solo descrittivo
OUT_NAME = "dev_compact_analysis"
# --- regola (voce 119): non si modifica senza una nuova voce in docs/decisions.md ---
MIN_VC_GAIN = 4
ADOPT_R = 0.03
MAX_R_LOSS = 0.03
MAX_VC_LOSS = 2
MAX_M_LOSS = 0.03
MAX_TRUNCATED = 1
TIE = 0.01
SIMPLICITY = ("indent", "schema", "both")
EPS = 1e-9


def admissible(base: dict, var: dict) -> dict:
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    dr, dvc, dm = z(var["R"]) - z(base["R"]), var["Vc"] - base["Vc"], z(var["M1"]) - z(base["M1"])
    keeps_m = dm >= -MAX_M_LOSS - EPS
    validity = dvc >= MIN_VC_GAIN and dr >= -MAX_R_LOSS - EPS
    content = dr >= ADOPT_R - EPS and dvc >= -MAX_VC_LOSS
    return {"ok": keeps_m and (validity or content), "dR": dr, "dVc": dvc, "dM1": dm, "keeps_M": keeps_m,
            "validity_gain": validity, "content_gain": content}


def outcome(base_m: dict, var_m: dict[str, dict], excluded: dict[str, str]) -> dict:
    """var_m: variante -> metriche (con 'truncated'); excluded: variante -> motivo (controllo preliminare)."""
    res = {"variants": {}, "winner": None, "tied": []}
    for v in SIMPLICITY:
        if v in excluded:
            res["variants"][v] = {"ok": False, "excluded": excluded[v]}
            continue
        m = var_m[v]
        if m["truncated"] > MAX_TRUNCATED:
            res["variants"][v] = {"ok": False, "excluded": f"{m['truncated']} troncamenti (>= {MAX_TRUNCATED + 1})"}
            continue
        res["variants"][v] = admissible(base_m, m)
    ok = [v for v in SIMPLICITY if res["variants"][v]["ok"]]
    if ok:
        best = max(var_m[v]["R"] for v in ok)
        res["tied"] = [v for v in ok if best - var_m[v]["R"] <= TIE + EPS]
        res["winner"] = res["tied"][0]  # SIMPLICITY e' gia' in ordine di semplicita'
    return res


def fmt(x, nd=3) -> str:
    return ad.fmt(x, nd)


def load(results: Path, prefix: str, gt: dict) -> dict:
    return ai.load_run(results, prefix, "P-G" if prefix == REFERENCE_PLANTUML else "C-G", gt, MODEL_ID, K)


def report(runs: dict[str, dict]) -> tuple[str, dict]:
    """runs: 'baseline' | 'indent' | 'schema' | 'both' | 'plantuml' -> info di load_run."""
    metrics = {k: ai.metrics(x["calls"]) if x["calls"] else None for k, x in runs.items()}
    pre = {k: x["excluded"] for k, x in runs.items() if x["excluded"] and k != "plantuml"}
    L = ["# Insieme di sviluppo — validità del JSON compatto (varianti contro `dev_v5base` C-G, k = 3)", "",
         "Esperimento di SVILUPPO (20 esercizi di sviluppo, pool unico), mai esercizi di valutazione. Gemma 4 12B QAT, "
         "istruzioni v4 del compatto. Regola registrata PRIMA della run (voce 119), applicata da "
         "`experiments/analyze_compact.py`. Le varianti con lo schema restano subordinate alla domanda 14 per i "
         "relatori.", "", provenance.provenance_line(), ""]
    res = None
    if "baseline" in pre:
        L.append(f"**Baseline non utilizzabile**: {pre['baseline']}. Nessuna decisione.")
    else:
        res = outcome(metrics["baseline"], {v: metrics[v] for v in SIMPLICITY if metrics[v]},
                      {v: pre[v] for v in SIMPLICITY if v in pre})
        L += ["## Regola (voce 119), applicata così com'è", "",
              "Ammissibile se dM_primaria >= -0,03 e [(dVc >= +4 e dR >= -0,03) oppure (dR >= +0,03 e dVc >= -2)]; "
              "esclusa con 2 o più troncamenti; tra le ammissibili vince l'R più alto, entro 0,01 la più semplice "
              "(indent < schema < both).", ""]
        for v in SIMPLICITY:
            d = res["variants"][v]
            if "excluded" in d:
                L.append(f"- **{v}**: esclusa ({d['excluded']})")
            else:
                L.append(f"- **{v}**: {'AMMISSIBILE' if d['ok'] else 'non ammissibile'} (dVc {d['dVc']:+d}, dR "
                         f"{d['dR']:+.3f}, dM_primaria {d['dM1']:+.3f}; guadagno di validità "
                         f"{'sì' if d['validity_gain'] else 'no'}, di contenuto {'sì' if d['content_gain'] else 'no'})")
        L += ["", f"**Esito: {'variante ' + res['winner'] + ' (in parità: ' + ', '.join(res['tied']) + ')' if res['winner'] else 'nessuna variante ammissibile: resta la baseline'}.**"
              + (" Subordinata alla domanda 14 (generazione vincolata)." if res["winner"] in ("schema", "both") else "")]
    L += ["", "## Metriche", "",
          "| run | V | Vc | J | R | M primaria | troncate | motivi di invalidità | completamento med | latenza med (s) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    labels = {"baseline": "baseline (dev_v5base C-G)", "indent": "indent (dev_cindent)", "schema": "schema (dev_cschema)",
              "both": "both (dev_cboth)", "plantuml": "riferimento: PlantUML v5 (dev_v5 P-G)"}
    for k in ("baseline", *SIMPLICITY, "plantuml"):
        x, m = runs[k], metrics[k]
        if m is None:
            L.append(f"| {labels[k]} | — | — | — | — | — | — | {x['excluded'] or ''} | — | — |")
            continue
        fails = Counter(c["v"].failure for c in x["calls"] if c["v"].level < 3)
        med = lambda key: statistics.median([c["m"][key] for c in x["calls"] if c["m"].get(key)] or [0])  # noqa: E731
        L.append(f"| {labels[k]} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {fmt(m['J'])} | {fmt(m['R'])} | "
                 f"{fmt(m['M1'])} | {m['truncated']} | {dict(fails) or '—'} | {med('completion_tokens_server'):.0f} | "
                 f"{med('latency_s'):.1f} |")
    return "\n".join(L) + "\n", res


def load_all(results: Path) -> dict[str, dict]:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    runs = {"baseline": load(results, BASELINE, gt), "plantuml": load(results, REFERENCE_PLANTUML, gt)}
    runs.update({v: load(results, prefix, gt) for v, prefix in VARIANTS.items()})
    return runs


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    text, _ = report(load_all(results))
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
