"""
Ricalcolo DESCRITTIVO delle metriche per elemento (evaluation/element_metrics.py, voce 136) sulle risposte gia'
salvate delle run di sviluppo. Nessuna generazione, nessun esercizio di valutazione; evaluation/metrics.py, gli script
di analisi e i loro summary.md non si toccano.

1. Per run, formato e condizione (e k): P / R / F1 macro per esercizio e micro, per classi, attributi, relazioni
   strutturali e generalizzazioni, con abbinamento esatto e rilassato; risposte escluse dalla media della precision;
   qualita' delle relazioni abbinate (tipo, famiglia, molteplicita', verso); generalizzazioni invertite.
2. Confronto con le metriche attuali: J contro F1 delle classi, R contro recall e F1 delle relazioni; correlazione di
   Spearman per esercizio tra F1 delle relazioni (rilassato) e R.
3. Regole passate ricalcolate con F1 delle relazioni (rilassato, macro) AL POSTO di R: le funzioni di decisione degli
   script storici si richiamano cosi' come sono, sostituendo R solo in memoria. SOLO descrittivo: gli esiti registrati
   in docs/decisions.md restano quelli.

Uscita: data/results/evaluation_dev/summary.md, metrics.csv, per_exercise.csv.

Uso:
    python evaluation/evaluate_dev.py
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "experiments"), str(ROOT / "generation"), str(ROOT / "retrieval")]
from evaluation import element_metrics as el  # noqa: E402
from evaluation import metrics as em  # noqa: E402

GEN = ROOT / "data" / "results" / "generation"
OUT = ROOT / "data" / "results" / "evaluation_dev"
M12, M26 = "google/gemma-4-12b-qat", "google/gemma-4-26b-a4b-qat"
# (run, configurazione, modello, nota): le run di sviluppo indicate dall'utente, piu' dev_g26 (passo 2, voce 133)
RUNS = (("dev_v5", "P-G", M12, "v5"), ("dev_v5", "C-G", M12, "v5"), ("dev_c5indent", "C-G", M12, "v5 + indentati"),
        ("dev_v5base", "P-G", M12, "v4"), ("dev_v5base", "C-G", M12, "v4"),
        ("dev_retrievers", "P-G", M12, "v4, pool storico"), ("dev_retrievers", "C-G", M12, "v4, pool storico"),
        ("dev_k", "P-G", M12, "v4, pool storico"), ("dev_k", "C-G", M12, "v4, pool storico"),
        ("dev_cindent", "C-G", M12, "v4 + indentati"), ("dev_cschema", "C-G", M12, "v4 + schema"),
        ("dev_cboth", "C-G", M12, "v4 + entrambi"),
        ("dev_structP", "P-G", M12, "v5"), ("dev_structC", "C-G", M12, "v4"),
        ("dev_g26", "P-G", M26, "v5, 26B"), ("dev_g26", "C-G", M26, "v5 + indentati, 26B"))
SHORT = {"classes": "classi", "attributes": "attributi", "relations": "relazioni", "generalizations": "generalizz."}


def load_groups() -> list[dict]:
    import analyze_instructions as ai
    import run_experiment as rx
    from prompt_builder import cl
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    groups = []
    for run, conf, model, note in RUNS:
        cfg = json.loads((GEN / f"{run}__{conf}" / "config.json").read_text(encoding="utf-8"))["config"]
        info = ai.load_run(GEN, run, conf, gt, model, None, config_version=rx.config_version(cfg))
        if info["excluded"] and not info["excluded"].startswith("incompleta"):
            raise SystemExit(f"{run}__{conf}: {info['excluded']}")
        keyset = sorted({(c["m"]["condition"], c["m"]["k"]) for c in info["calls"]})
        for cond, k in keyset:
            calls = [c for c in info["calls"] if (c["m"]["condition"], c["m"]["k"]) == (cond, k)]
            groups.append({"run": run, "conf": conf, "format": "PlantUML" if conf.startswith("P") else "compatto",
                           "cond": cond, "k": k, "note": note, "calls": calls})
    return groups


def spearman(xs, ys):
    from scipy.stats import spearmanr
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3 or len({p[0] for p in pairs}) < 2 or len({p[1] for p in pairs}) < 2:
        return None
    return float(spearmanr([p[0] for p in pairs], [p[1] for p in pairs])[0])


def evaluate(groups: list[dict]) -> None:
    for g in groups:
        g["agg"] = el.aggregate(g["calls"])
        core = em.core_metrics(g["calls"])
        g["J"], g["R"] = core["J"], core["R"]
        f1_q = el.per_exercise(g["calls"], "relaxed", "relations", "F1")
        r_q = {q: em.core_metrics([c for c in g["calls"] if c["q"] == q])["R"] for q in f1_q}
        g["per_q"] = {q: (f1_q[q], r_q[q]) for q in f1_q}
        g["rho_F1rel_R"] = spearman(list(f1_q.values()), [r_q[q] for q in f1_q])


# --- regole passate con F1 al posto di R -----------------------------------------------------------------------------

def _decisions(res, path=""):
    out = {}
    if isinstance(res, dict):
        for k, v in res.items():
            p = f"{path}.{k}"
            if k in ("adopt", "winner", "decided_by", "outcome", "ok") and not isinstance(v, dict):
                out[p] = v
            elif isinstance(v, dict):
                out.update(_decisions(v, p))
    return out


def past_rules() -> list[dict]:
    """Ogni regola storica che usa R, richiamata due volte: con R (deve dare l'esito registrato) e con R := F1 macro
    delle relazioni strutturali (rilassato). Le funzioni degli script non cambiano: si sostituisce solo
    metrics.core_metrics (e il suo alias analyze_dev.metrics) per la durata del calcolo."""
    import analyze_compact as ac
    import analyze_dev as ad
    import analyze_g26 as ag
    import analyze_instructions as ai
    import analyze_k as ak
    import analyze_pool as apo
    import analyze_struct as ast
    import analyze_v5 as av
    from prompt_builder import cl
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    rules = (("voce 92, formati (dev_formats)", lambda: ad.report({n: ad.load_configuration(GEN, n, gt, m) for n, m in
                                                                     ad.expected_model_ids().items()}, ad.bands())),
             ("voce 94, k (dev_k)", lambda: ak.report({n: ak.load_configuration(GEN, n, gt, m) for n, m in
                                                     ak.expected_model_ids().items()}, ad.bands())),
             ("voce 98, istruzioni mirate (dev_instructions)", lambda: ai.report(ai.load_pairs(GEN))),
             ("voce 111/118, istruzioni v5 (dev_v5)", lambda: av.report(av.load_pairs(GEN))),
             ("voce 119/121, validita' del compatto (dev_cindent / cschema / cboth)", lambda: ac.report(ac.load_all(GEN))),
             ("voce 121/122, varianti del retriever (dev_struct*)", lambda: ast.report(ast.load_all(GEN))),
             ("voce 123/124, compatto v5 + indent e pool (dev_c5indent, dev_poolC)", lambda: apo.report(apo.load_all(GEN))),
             ("voce 132/133, modello 26B (dev_g26)", lambda: ag.report(ag.load_all(GEN))))
    original, alias = em.core_metrics, ad.metrics

    def with_f1(calls):
        m = original(calls)
        m["R"] = el.aggregate(calls)["relaxed"]["relations"]["macro"]["F1"] if calls else None
        return m

    out = []
    for name, fn in rules:
        with contextlib.redirect_stdout(io.StringIO()):
            base = _decisions(fn()[1])
            em.core_metrics, ad.metrics = with_f1, with_f1
            try:
                alt = _decisions(fn()[1])
            finally:
                em.core_metrics, ad.metrics = original, alias
        changed = {k: (base[k], alt.get(k)) for k in base if base[k] != alt.get(k)}
        out.append({"rule": name, "base": base, "alt": alt, "changed": changed})
    return out


# --- report ----------------------------------------------------------------------------------------------------------

def f(x, nd=3) -> str:
    return "—" if x is None else f"{x:.{nd}f}"


def label(g) -> str:
    return f"{g['run']} {g['conf']} {g['cond']} k={g['k']}"


def write(groups: list[dict], rules: list[dict]) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for g in groups:
        a = g["agg"]
        base = {"run": g["run"], "configurazione": g["conf"], "formato": g["format"], "condizione": g["cond"], "k": g["k"],
                "nota": g["note"], "risposte": a["n"], "non_valide": a["invalid"], "J": g["J"], "R": g["R"],
                "rho_F1rel_R": g["rho_F1rel_R"]}
        for lv in el.LEVELS:
            for t in el.TYPES:
                for kind in ("macro", "micro"):
                    for m in ("P", "R", "F1"):
                        base[f"{lv}_{t}_{kind}_{m}"] = a[lv][t][kind][m]
                base[f"{lv}_{t}_P_escluse"] = a[lv][t]["p_excluded"]
            for k, v in a[lv]["quality"].items():
                base[f"{lv}_rel_{k}"] = v
        rows.append(base)
    with (OUT / "metrics.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in rows)
    with (OUT / "per_exercise.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["gruppo", "esercizio", "F1_relazioni_rilassato", "R"])
        for g in groups:
            for q, (fv, rv) in g["per_q"].items():
                w.writerow([label(g), q, None if fv is None else round(fv, 4), None if rv is None else round(rv, 4)])

    import provenance
    L = ["# Metriche per elemento sulle run di sviluppo (P / R / F1, abbinamento esatto e rilassato)", "",
         "Voce 136 di `docs/decisions.md`. SOLO DESCRITTIVO: risposte già salvate, nessuna generazione, nessun esercizio "
         "di valutazione; `evaluation/metrics.py`, gli script di analisi e i loro summary.md invariati. Generato da "
         "`evaluation/evaluate_dev.py` con `evaluation/element_metrics.py`.", "", provenance.provenance_line(), "",
         "Definizioni nel modulo: classi abbinate uno a uno (esatto: nome normalizzato; rilassato: poi stesso insieme di "
         "token stemmati); attributi dentro le classi abbinate; relazioni strutturali senza verso; generalizzazioni con "
         "verso. Macro = media per esercizio (prima sulle ripetizioni); risposta non valida = diagramma vuoto (R 0, F1 0, "
         "P esclusa dalla media).", "",
         "## 1. F1 macro per esercizio, abbinamento RILASSATO (con J e R attuali)", "",
         "| run | formato | condizione | k | nota | risposte (non valide) | J | F1 classi | F1 attributi | R | "
         "F1 relazioni | F1 generalizz. | rho(F1 rel., R) |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in groups:
        a = g["agg"]["relaxed"]
        L.append(f"| {g['run']} | {g['format']} | {g['cond']} | {g['k']} | {g['note']} | {g['agg']['n']} "
                 f"({g['agg']['invalid']}) | {f(g['J'])} | {f(a['classes']['macro']['F1'])} | "
                 f"{f(a['attributes']['macro']['F1'])} | {f(g['R'])} | {f(a['relations']['macro']['F1'])} | "
                 f"{f(a['generalizations']['macro']['F1'])} | {f(g['rho_F1rel_R'], 2)} |")
    L += ["", "## 2. Esatto contro rilassato (F1 macro) e precision / recall rilassati", "",
          "| run | formato | condizione | k | F1 classi es. / ril. | F1 attributi es. / ril. | F1 relazioni es. / ril. | "
          "P / R classi | P / R relazioni | P / R generalizz. |", "|---|---|---|---|---|---|---|---|---|---|"]
    for g in groups:
        e, r = g["agg"]["exact"], g["agg"]["relaxed"]
        pr = lambda t: f"{f(r[t]['macro']['P'])} / {f(r[t]['macro']['R'])}"  # noqa: E731
        L.append(f"| {g['run']} | {g['format']} | {g['cond']} | {g['k']} | {f(e['classes']['macro']['F1'])} / "
                 f"{f(r['classes']['macro']['F1'])} | {f(e['attributes']['macro']['F1'])} / "
                 f"{f(r['attributes']['macro']['F1'])} | {f(e['relations']['macro']['F1'])} / "
                 f"{f(r['relations']['macro']['F1'])} | {pr('classes')} | {pr('relations')} | {pr('generalizations')} |")
    L += ["", "## 3. Relazioni strutturali abbinate (rilassato, micro) e medie micro", "",
          "| run | formato | condizione | k | abbinate | stesso tipo | stessa famiglia | molteplicità uguali (tutti / "
          "espliciti) | verso | generalizz. invertite | F1 micro classi / relazioni | P escluse (relazioni) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in groups:
        r = g["agg"]["relaxed"]
        q = r["quality"]
        L.append(f"| {g['run']} | {g['format']} | {g['cond']} | {g['k']} | {q['matched']} | {f(q['same_type'])} | "
                 f"{f(q['same_family'])} | {f(q['mult_all'])} / {f(q['mult_explicit'])} | {f(q['direction'])} | "
                 f"{q['inv_generalizations']} | {f(r['classes']['micro']['F1'])} / {f(r['relations']['micro']['F1'])} | "
                 f"{r['relations']['p_excluded']} |")
    import statistics as st
    rhos = [g["rho_F1rel_R"] for g in groups if g["rho_F1rel_R"] is not None]
    gain = [g["agg"]["relaxed"]["classes"]["macro"]["F1"] - g["agg"]["exact"]["classes"]["macro"]["F1"] for g in groups]
    gain_r = [g["agg"]["relaxed"]["relations"]["macro"]["F1"] - g["agg"]["exact"]["relations"]["macro"]["F1"] for g in groups]
    L += ["", "## 4. Rispetto a J e R", "",
          f"- Rilassato contro esatto: F1 delle classi +{st.mean(gain):.3f} in media (da +{min(gain):.3f} a "
          f"+{max(gain):.3f}); F1 delle relazioni +{st.mean(gain_r):.3f} (da +{min(gain_r):.3f} a +{max(gain_r):.3f}).",
          f"- Correlazione per esercizio tra F1 delle relazioni (rilassato) e R, gruppo per gruppo (n = 20): mediana "
          f"{st.median(rhos):.2f}, da {min(rhos):.2f} a {max(rhos):.2f}.",
          "- R è una recall rigida (stessa coppia di nomi esatti E stesso tipo, sulle relazioni del GT); F1 delle "
          "relazioni non chiede il tipo e premia anche la precisione (relazioni in più penalizzate).", "",
          "## 5. Regole passate con F1 delle relazioni (rilassato, macro) al posto di R — SOLO descrittivo", "",
          "Le funzioni di decisione degli script storici richiamate così come sono, con R sostituita in memoria. Gli "
          "esiti registrati in `docs/decisions.md` NON cambiano.", ""]
    for rr in rules:
        if rr["changed"]:
            L.append(f"- **{rr['rule']}: esito DIVERSO** — " + "; ".join(f"`{k}`: {v[0]} → {v[1]}"
                                                                         for k, v in rr["changed"].items()))
        else:
            L.append(f"- {rr['rule']}: stesso esito (" + "; ".join(f"`{k}` = {v}" for k, v in list(rr["base"].items())[:3])
                     + ")")
    L += ["", "Note: la regola di esclusione dei retriever (voce 110) non usa R e non è ricalcolata; dev_k, "
          "dev_instructions e dev_retrievers usavano il pool storico di 58 candidati."]
    text = "\n".join(L) + "\n"
    (OUT / "summary.md").write_text(text, encoding="utf-8")
    return text


def main() -> int:
    groups = load_groups()
    evaluate(groups)
    rules = past_rules()
    text = write(groups, rules)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
