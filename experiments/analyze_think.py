"""
Leva "thinking" di Gemma sull'insieme di sviluppo (docs/decisions.md, voce 125). Scritto e testato PRIMA delle
generazioni (sulle sole baseline): da qui la regola (costanti, adopt, outcome) non si modifica senza una nuova voce.

Nessuna chiamata a un LLM. Per formato confronta la BASELINE senza ragionamento (dev_v5__P-G; dev_c5indent__C-G, versione
di configurazione 2) con il TRATTAMENTO con ragionamento (dev_think__P-G / __C-G, versione 3: max_tokens 8192), stessa
configurazione di lavoro. Metriche di experiments/analyze_v5.py (V, Vc, J, R, R_fam, M primaria, generalizzazioni
invertite, classi / generalizzazioni / composizioni in piu') calcolate SOLO sul contenuto finale (il ragionamento e' nel
raw, a parte).

REGOLA (voce 125), per formato, delta = thinking - baseline su 40 risposte:
  adottare il thinking se (dR >= +0,03 OPPURE dR_fam >= +0,03) E dVc >= -2 E dM_primaria >= -0,03
  E meno di 2 troncamenti E meno di 2 risposte con contenuto vuoto.
COSTO (fuori dalla regola, obbligatorio): mediana e massimo dei token di ragionamento, latenza mediana thinking contro
baseline, stima delle ore del Passo 3b con il thinking (circa 2.300 generazioni); se la leva e' adottata e la stima supera
30 ore non si decide da soli (si propone ai relatori su quali condizioni del 3b usarla).
Qualitativo: 3 esercizi in cui il thinking migliora R e 3 in cui peggiora, con un estratto del ragionamento.

Uso:
    python experiments/analyze_think.py [--results-dir data/results/generation]
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
import analyze_dev as ad  # noqa: E402
import analyze_instructions as ai  # noqa: E402
import analyze_pilot as ap  # noqa: E402
import analyze_v5 as av  # noqa: E402  (all_metrics: R_fam, generalizzazioni invertite, elementi in piu')
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
MODEL_ID = "google/gemma-4-12b-qat"
K = 3
FORMATS = {"plantuml": ("P-G", "dev_v5", 2), "compact": ("C-G", "dev_c5indent", 2)}
TREATMENT = ("dev_think", 3)
CONTROL = ("dev_temp1", 3)  # sotto-voce della voce 125: temperatura 1,0 senza ragionamento
OUT_NAME = "dev_think_analysis"
GENERATIONS_3B = 2300
# --- regola (voce 125): non si modifica senza una nuova voce in docs/decisions.md ---
ADOPT_R = 0.03
ADOPT_R_FAM = 0.03
MAX_VC_LOSS = 2
MAX_M_LOSS = 0.03
MAX_TRUNCATED = 1
MAX_EMPTY = 1
HOURS_LIMIT = 30
# ciclo evidente nel ragionamento (sotto-voce della voce 125, criterio di chiusura della leva)
CYCLE_DISTINCT_RATIO = 0.6
CYCLE_MIN_CHARS = 20
CYCLE_MIN_REPEAT = 5
EPS = 1e-9


def adopt(base: dict, treat: dict, truncated: int, empty: int) -> dict:
    z = lambda x: 0.0 if x is None else x  # noqa: E731
    dr, drf = z(treat["R"]) - z(base["R"]), z(treat["R_fam"]) - z(base["R_fam"])
    dvc, dm = treat["Vc"] - base["Vc"], z(treat["M1"]) - z(base["M1"])
    gain = dr >= ADOPT_R - EPS or drf >= ADOPT_R_FAM - EPS
    ok = gain and dvc >= -MAX_VC_LOSS and dm >= -MAX_M_LOSS - EPS and truncated <= MAX_TRUNCATED and empty <= MAX_EMPTY
    return {"adopt": ok, "dR": dr, "dR_fam": drf, "dVc": dvc, "dM1": dm, "truncated": truncated, "empty": empty,
            "gain": gain}


def cycle(reasoning: str) -> dict:
    """Ciclo evidente: righe distinte / totali < 0,6 oppure una stessa riga di almeno 20 caratteri ripetuta 5 o piu'
    volte (righe non vuote, spazi ai bordi tolti)."""
    lines = [x.strip() for x in (reasoning or "").splitlines() if x.strip()]
    from collections import Counter
    counts = Counter(x for x in lines if len(x) >= CYCLE_MIN_CHARS)
    top, n = (counts.most_common(1)[0] if counts else ("", 0))
    ratio = len(set(lines)) / len(lines) if lines else 1.0
    return {"cycle": ratio < CYCLE_DISTINCT_RATIO or n >= CYCLE_MIN_REPEAT, "lines": len(lines),
            "distinct": len(set(lines)), "ratio": ratio, "max_repeat": n, "top_line": top}


def hours_3b(latencies: list[float], n: int = GENERATIONS_3B) -> float:
    """Ore stimate del 3b: latenza mediana per generazione x numero di generazioni."""
    return statistics.median(latencies) * n / 3600 if latencies else float("nan")


def r_call(c: dict) -> float:
    n = len(c["gt"]["edges"])
    return 0.0 if c["v"].level < 3 or not n else ap.compare_relations(c["v"].diagram, c["gt"])["same_type"] / n


def load_all(results: Path) -> dict:
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    data = {}
    for f, (name, base, ver) in FORMATS.items():
        data[f] = {"base": ai.load_run(results, base, name, gt, MODEL_ID, K, config_version=ver),
                   "think": ai.load_run(results, TREATMENT[0], name, gt, MODEL_ID, K, config_version=TREATMENT[1]),
                   "control": ai.load_run(results, CONTROL[0], name, gt, MODEL_ID, K, config_version=CONTROL[1])}
    return data


def excerpt(text: str, n: int = 420) -> str:
    t = " ".join((text or "").split())
    return (t[:n] + " …") if len(t) > n else t


def report(data: dict) -> tuple[str, dict]:
    res = {"formats": {}, "hours_3b": None}
    L = ["# Insieme di sviluppo — ragionamento di Gemma acceso (`dev_think` contro la configurazione di lavoro)", "",
         "SVILUPPO: 20 esercizi di sviluppo, pool unico, bm25 k = 3, Gemma 4 12B QAT; ragionamento acceso per richiesta "
         "(`reasoning_effort`), max_tokens 8192 (versione 3). Metriche SOLO sul contenuto finale. Regola registrata PRIMA "
         "delle generazioni (voce 125), applicata da `experiments/analyze_think.py`.", "", provenance.provenance_line(),
         "", "## Regola (voce 125)", "",
         "Adottare se (dR >= +0,03 oppure dR_fam >= +0,03) e dVc >= -2 e dM_primaria >= -0,03 e meno di 2 troncamenti "
         "e meno di 2 risposte vuote.", ""]
    think_lat, base_lat, rtok = [], [], []
    rows = []
    for f, d in data.items():
        pre = [x["excluded"] for k, x in d.items() if x["excluded"] and k != "control"]
        if pre:
            res["formats"][f] = None
            L.append(f"- **{ad.FORMAT_NAME[f]}: non decidibile** ({'; '.join(pre)})")
            continue
        mb, mt = av.all_metrics(d["base"]["calls"]), av.all_metrics(d["think"]["calls"])
        empty = sum(bool(c["m"].get("content_empty")) for c in d["think"]["calls"])
        res["formats"][f] = a = adopt(mb, mt, mt["truncated"], empty)
        L.append(f"- **{ad.FORMAT_NAME[f]}: thinking {'ADOTTATO' if a['adopt'] else 'NON adottato'}** (dR {a['dR']:+.3f}, "
                 f"dR_fam {a['dR_fam']:+.3f}, dVc {a['dVc']:+d}, dM_primaria {a['dM1']:+.3f}, troncate {a['truncated']}, "
                 f"vuote {a['empty']})")
        tl = [c["m"]["latency_s"] for c in d["think"]["calls"]]
        bl = [c["m"]["latency_s"] for c in d["base"]["calls"]]
        rt = [c["m"].get("reasoning_tokens") or 0 for c in d["think"]["calls"]]
        think_lat += tl
        base_lat += bl
        rtok += rt
        rows.append((f, mb, mt, empty, statistics.median(bl), statistics.median(tl), statistics.median(rt), max(rt)))
    L += ["", "## Metriche (solo contenuto finale)", "",
          "| formato | ragionamento | V | Vc | J | R | R_fam | M primaria | generalizzazioni invertite | classi in più | "
          "composizioni in più | troncate | vuote |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f, mb, mt, empty, *_ in rows:
        mc = av.all_metrics(data[f]["control"]["calls"]) if data[f]["control"]["calls"] else None
        for lab, m, e in (("spento, 0,3 (baseline)", mb, 0), ("spento, 1,0 (controllo)", mc, 0),
                          ("acceso low, 1,0 (trattamento)", mt, empty)):
            if m is None:
                L.append(f"| {ad.FORMAT_NAME[f]} | {lab} | — | — | — | — | — | — | — | — | — | — | — |")
                continue
            L.append(f"| {ad.FORMAT_NAME[f]} | {lab} | {m['V']}/{m['n']} | {m['Vc']}/{m['n']} | {ad.fmt(m['J'])} | "
                     f"{ad.fmt(m['R'])} | {ad.fmt(m['R_fam'])} | {ad.fmt(m['M1'])} | {m['inv_gen']}/{m['inv_gen_tot']} | "
                     f"{m['extra_cls']} | {m['extra_comp']} | {m['truncated']} | {e} |")
    if rows:
        L += ["", "## Confronti (delta di R / R_fam / Vc / M primaria)", "",
              "| formato | (a) trattamento − baseline | (b) controllo − baseline | (c) trattamento − controllo (solo "
              "ragionamento) |", "|---|---|---|---|"]
        for f, mb, mt, *_ in rows:
            mc = av.all_metrics(data[f]["control"]["calls"]) if data[f]["control"]["calls"] else None
            dl = lambda x, y: (f"{x['R'] - y['R']:+.3f} / {x['R_fam'] - y['R_fam']:+.3f} / {x['Vc'] - y['Vc']:+d} / "  # noqa: E731
                               f"{(x['M1'] or 0) - (y['M1'] or 0):+.3f}") if x and y else "—"
            L.append(f"| {ad.FORMAT_NAME[f]} | {dl(mt, mb)} | {dl(mc, mb)} | {dl(mt, mc)} |")
        res["hours_3b"] = h = hours_3b(think_lat)
        L += ["", "## Costo", "",
              "| formato | token di ragionamento (mediana / massimo) | latenza mediana senza / con (s) |", "|---|---|---|"]
        L += [f"| {ad.FORMAT_NAME[f]} | {rm:.0f} / {rx_} | {bl:.1f} / {tl:.1f} |" for f, _, _, _, bl, tl, rm, rx_ in rows]
        L += ["", f"Stima del Passo 3b con il ragionamento: {GENERATIONS_3B} generazioni × latenza mediana "
              f"{statistics.median(think_lat):.1f} s ≈ **{h:.1f} ore** (senza: {hours_3b(base_lat):.1f} ore)."]
        if any(a and a["adopt"] for a in res["formats"].values()) and h > HOURS_LIMIT:
            L.append(f"**Leva adottata e stima oltre {HOURS_LIMIT} ore: non si decide da soli, si propone ai relatori su "
                     "quali condizioni del 3b usarla.**")
    # confusione e qualitativo
    for f, d in data.items():
        if res["formats"].get(f) is None:
            continue
        cb, ct = ai.confusion(d["base"]["calls"]), ai.confusion(d["think"]["calls"])
        L += ["", f"## Tabelle di confusione — {ad.FORMAT_NAME[f]}", "", "| tipi (GT -> risposta) | spento | acceso |",
              "|---|---|---|"]
        keys = sorted(set(cb["types"]) | set(ct["types"]), key=lambda k: (-(cb["types"][k] + ct["types"][k]), k))[:10]
        L += [f"| {a} -> {r} | {cb['types'][(a, r)]} | {ct['types'][(a, r)]} |" for a, r in keys]
        L += ["", "| molteplicità (GT -> risposta) | spento | acceso |", "|---|---|---|"]
        keys = sorted(set(cb["mult"]) | set(ct["mult"]), key=lambda k: (-(cb["mult"][k] + ct["mult"][k]), k))[:10]
        L += [f"| {a!r} -> {r!r} | {cb['mult'][(a, r)]} | {ct['mult'][(a, r)]} |" for a, r in keys]
        rb, rt_ = {}, {}
        for c in d["base"]["calls"]:
            rb.setdefault(c["q"], []).append(r_call(c))
        for c in d["think"]["calls"]:
            rt_.setdefault(c["q"], []).append(r_call(c))
        diff = sorted(((statistics.mean(rt_[q]) - statistics.mean(rb[q]), q) for q in rb if q in rt_))
        L += ["", f"### Esempi qualitativi — {ad.FORMAT_NAME[f]} (R medio per esercizio, estratto del ragionamento della "
              "prima ripetizione)", ""]
        by_q = {c["q"]: c for c in sorted(d["think"]["calls"], key=lambda c: -c["r"])}
        for lab, sel in (("migliora", diff[::-1][:3]), ("peggiora", diff[:3])):
            for dd, q in sel:
                L.append(f"- **{lab}: {q}** (R {statistics.mean(rb[q]):.2f} → {statistics.mean(rt_[q]):.2f}, "
                         f"{dd:+.2f}): «{excerpt(by_q[q]['raw'].get('reasoning_text', ''))}»")
    return "\n".join(L) + "\n", res


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    results = Path(args.results_dir)
    text, _ = report(load_all(results))
    out = results / OUT_NAME
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(text, encoding="utf-8")
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(out / "summary.md")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    print(f"scritto in {out / 'summary.md'}")
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
