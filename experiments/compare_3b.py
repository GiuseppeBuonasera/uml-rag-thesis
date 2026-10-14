"""
Confronto visivo di alcuni esercizi del 3b in tutte le condizioni (2026-10-14). Sola lettura: nessuna chiamata a un
LLM, nessuna metrica nuova.

Una pagina HTML autonoma (nessuna risorsa esterna; diagrammi SVG incorporati) che, per gli esercizi scelti, mette
accanto al diagramma di riferimento le risposte di Gemma 4 26B A4B QAT nelle sei condizioni del 3b (zero_shot, static
k2, random k3, bm25 k2, bm25 k3, hybrid k3), per formato (PlantUML / compatto) e ripetizione. Per ogni risposta:
diagramma (classi verdi = nel GT, arancioni = in piu'), metriche (F1 relazioni, classi, attributi con abbinamento
rilassato; R, J, M; scheletro), relazioni classificate, esempi del prompt con la loro somiglianza all'esercizio (Jt =
Jaccard dei token dei nomi di classe dei due GT, retrieval/relevance.py). Indice: F1 delle relazioni medio sulle 3
ripetizioni per esercizio, formato e condizione.

Rendering, validazione e classificazione: experiments/review_report.py; F1: evaluation/element_metrics.py.
Richiede Java e .tools/plantuml-old.jar.

Con piu' di SVG_INLINE_MAX esercizi (o --esercizi tutti, i 54 di valutazione) i diagrammi non si incorporano: si
scrivono come file in <out>/svg/ e la pagina li carica solo quando li mostra (pagina leggera; la cartella va tenuta
insieme a index.html).

Uso:
    python experiments/compare_3b.py --esercizi Gym RealEstateAgency [--out data/results/generation/confronto_3b]
    python experiments/compare_3b.py --esercizi tutti --out data/results/generation/confronto_3b_tutti
"""

from __future__ import annotations

import argparse
import base64
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "experiments"), str(ROOT / "generation"), str(ROOT / "retrieval"), str(ROOT)]
import review_report as rr  # noqa: E402
import compare_retrievers as cr  # noqa: E402
from evaluation import element_metrics as el  # noqa: E402
from evaluation import metrics as em  # noqa: E402

GEN = rr.RESULTS
OUT = GEN / "confronto_3b"
MODEL = "G26"
FORMATS = {"P": "PlantUML", "C": "JSON compatto"}
SPLITS = ("corpus", "testset")
CONDITIONS = (("zero_shot", 0), ("static", 2), ("random", 3), ("bm25", 2), ("bm25", 3), ("hybrid", 3))
SVG_INLINE_MAX = 10  # oltre, diagrammi come file separati


def evaluation_ids() -> list[str]:
    """I 54 esercizi di valutazione del 3b (elenchi di experiments/configs/passo3b.yaml)."""
    import yaml
    ev = yaml.safe_load((ROOT / "experiments" / "configs" / "passo3b.yaml").read_text(encoding="utf-8"))["elenchi"]
    return ev["valutazione_corpus"] + ev["valutazione_debari"]


def label(cond: str, k: int) -> str:
    return cond if cond == "zero_shot" else f"{cond} k{k}"


def load_calls(ids: list[str], results: Path = GEN) -> dict:
    """(formato, etichetta della condizione) -> risposte degli esercizi scelti, dalle quattro run del 3b."""
    import corpus_loader as cl
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates() + cl.load_queries()}
    unknown = sorted(set(ids) - set(gt))
    if unknown:
        raise SystemExit(f"esercizi sconosciuti: {unknown}")
    out = {}
    for f in FORMATS:
        for split in SPLITS:
            for c in rr.load_run(results / f"passo3b__{f}-{split}-{MODEL}", {"q": set(ids)}, gt):
                out.setdefault((f, label(c["m"]["condition"], c["m"]["k"])), []).append(c)
    return out


def build(calls: dict, jar: Path = rr.DEFAULT_JAR, svg_dir: Path | None = None) -> tuple[str, dict]:
    """svg_dir: se data, i diagrammi si scrivono li' come file (svg/<chiave>.svg) invece di incorporarli."""
    import corpus_loader as cl
    from relevance import Relevance
    from prompt_builder import static_examples
    recs = cl.load_candidates() + cl.load_queries()
    by_id = {c["id"]: c for c in recs}
    rel = Relevance(recs + static_examples(by_id)[:1])  # anche il primo esempio fisso di static (non nel pool)
    labels = [label(c, k) for c, k in CONDITIONS]
    exercises = sorted({c["q"] for v in calls.values() for c in v})
    sources, data = {}, {"exercises": {}, "formats": FORMATS, "conditions": labels}
    for q in exercises:
        sources[f"gt__{q}"] = rr.colored_plantuml(by_id[q]["diagram_apollon_json"], q, None)
        data["exercises"][q] = {"description": by_id[q].get("description") or "", "cells": {},
                                "split": "De Bari" if q in {x["id"] for x in cl.load_queries()} else "corpus"}
    for (f, lab), cs in calls.items():
        for c in cs:
            key = f"{f}__{lab.replace(' ', '_')}__{c['q']}__r{c['r']}"
            d = cr.describe(c)
            d["F1attr"] = el.evaluate_call(c)["relaxed"]["scores"]["attributes"]["F1"]
            d["skeleton"] = bool(em.attribute_counts(c)["skeleton"])
            d["text"] = c["raw"]["text"]  # testo esatto del modello (PlantUML o JSON compatto)
            d["examples"] = [[e, rel.measure(c["q"], e)["Jt"]] for e in c["m"]["example_ids"]]
            if c["v"].level >= 3:
                try:
                    sources[key] = rr.colored_plantuml(c["v"].diagram, c["m"]["call_id"], rr.ap.class_names(c["gt"]))
                except rr.us.StructureError:
                    pass
            d["svg"] = key
            data["exercises"][c["q"]]["cells"].setdefault(f, {}).setdefault(f"r{c['r']}", {})[lab] = d
    svgs, errors = rr.render_svgs(sources, jar)
    if svg_dir is None:
        data["svgs"] = {k: "data:image/svg+xml;base64," + base64.b64encode(v.encode("utf-8")).decode()
                        for k, v in svgs.items()}
    else:
        svg_dir.mkdir(parents=True, exist_ok=True)
        for k, v in svgs.items():
            (svg_dir / f"{k}.svg").write_text(v, encoding="utf-8")
        data["svgs"] = {k: f"{svg_dir.name}/{k}.svg" for k in svgs}
    index = []
    for q in exercises:
        row = {"q": q}
        for f in FORMATS:
            for lab in labels:
                vals = [d[lab]["F1rel"] for d in data["exercises"][q]["cells"].get(f, {}).values()
                        if lab in d and d[lab]["F1rel"] is not None]
                row[f"{f}__{lab}"] = statistics.mean(vals) if vals else None
        index.append(row)
    data["index"] = index
    stats = {"exercises": len(exercises), "responses": sum(len(v) for v in calls.values()), "diagrams": len(sources),
             "svgs": len(svgs), "errors": errors}
    return PAGE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")), stats


PAGE = """<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Confronto 3b</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--muted:#5d6675;--line:#d9dde4;--ok:#1e7a46;--bad:#b3261e;--accent:#2f5bd3;--warn:#a15c00}
@media (prefers-color-scheme:dark){:root{--bg:#14171c;--card:#1d2128;--ink:#e6e9ef;--muted:#9aa3b2;--line:#323844;--ok:#5cc28a;--bad:#ff8a80;--accent:#8ab0ff;--warn:#f0b35a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,Segoe UI,Roboto,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
header h1{font-size:16px;margin:0 12px 0 0}select,button{font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink)}
button{cursor:pointer}button:hover{border-color:var(--accent)}.tabs button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
main{padding:16px;max-width:2200px;margin:0 auto}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,440px),1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;min-width:0}.card.gt{border-color:var(--accent)}
.card h3{margin:0 0 6px;font-size:15px;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.diagram{background:#fff;border-radius:6px;overflow:auto;max-height:60vh;border:1px solid var(--line)}.diagram img{display:block;max-width:100%;height:auto;cursor:zoom-in}
.diagram.full img{max-width:none;cursor:zoom-out}
.m{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.chip{border:1px solid var(--line);border-radius:12px;padding:1px 8px;font-size:12px}
.chip.best{border-color:var(--ok);color:var(--ok);font-weight:600}.chip.bad{border-color:var(--bad);color:var(--bad)}
details{margin-top:6px}summary{cursor:pointer;color:var(--muted)}ul.rel{margin:6px 0;padding-left:18px;font-size:12.5px}
li.corretta{color:var(--ok)}li.err{color:var(--bad)}li.extra{color:var(--warn)}pre{white-space:pre-wrap;font-size:12px;background:var(--bg);padding:8px;border-radius:6px;max-height:300px;overflow:auto}
.legend span{display:inline-block;padding:0 6px;border-radius:4px;margin-right:6px;color:#111;font-size:12px}
.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}
tbody tr{cursor:pointer}tbody tr:hover{background:var(--bg)}td.win{color:var(--ok);font-weight:600}.muted{color:var(--muted)}
.desc{white-space:pre-wrap;font-size:13px;max-height:260px;overflow:auto}
</style></head><body>
<header><h1>Confronto 3b: GT e sei condizioni</h1>
<span class="tabs"><button id="tabView" class="on">Confronto</button> <button id="tabIndex">Indice</button></span>
<select id="selQ" aria-label="esercizio"></select><select id="selF" aria-label="formato"></select><select id="selR" aria-label="ripetizione"></select>
<button id="prev" title="esercizio precedente (←)">◀</button><button id="next" title="esercizio successivo (→)">▶</button>
<span class="legend"><span style="background:#D8F0DF">classe nel GT</span><span style="background:#FBD9B5">classe in più</span></span>
<span class="muted" id="where"></span></header>
<main><section id="view"></section><section id="index" hidden></section></main>
<script>
const D = __DATA__;
const Q = Object.keys(D.exercises), F = Object.keys(D.formats), C = D.conditions;
const $ = id => document.getElementById(id);
const f3 = x => x === null || x === undefined ? "—" : (+x).toFixed(2);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const img = key => D.svgs[key] ? `<div class="diagram"><img alt="diagramma" loading="lazy" src="${D.svgs[key]}"></div>` : `<p class="muted">diagramma non disponibile</p>`;
const CATS = ["corretta","tipo sbagliato","direzione invertita","molteplicita' diverse","mancante","in piu'"];
function fill(sel, items, labels){ sel.innerHTML = items.map(v => `<option value="${esc(v)}">${esc(labels ? labels[v] : v)}</option>`).join(""); }
fill($("selQ"), Q); fill($("selF"), F, D.formats);
function reps(){ const c = D.exercises[$("selQ").value].cells[$("selF").value] || {}; return Object.keys(c).sort(); }
function syncReps(keep){ const r = reps(); const old = $("selR").value; fill($("selR"), r); if (keep && r.includes(old)) $("selR").value = old; }
function card(title, d, best){
  if (!d) return `<div class="card"><h3>${esc(title)}</h3><p class="muted">cella non definita (static: l'esercizio è uno dei due esempi fissi)</p></div>`;
  const chip = (lab, key) => `<span class="chip ${d[key] !== null && best[key] !== null && d[key] >= best[key] - 1e-9 ? "best" : ""}">${lab} ${f3(d[key])}</span>`;
  let h = `<div class="card"><h3><span>${esc(title)}</span><span><span class="chip ${d.level >= 3 ? "" : "bad"}">livello ${d.level}${d.failure ? " · " + esc(d.failure) : ""}</span>` +
          (d.skeleton ? ` <span class="chip bad">scheletro</span>` : "") + `</span></h3>`;
  h += `<div class="m">${chip("F1 relazioni", "F1rel")}${chip("F1 classi", "F1cls")}${chip("F1 attributi", "F1attr")}${chip("R", "R")}${chip("J", "J")}${chip("M", "M")}</div>`;
  h += d.level >= 3 ? img(d.svg) : `<p class="muted">Risposta non valida: testo grezzo</p><pre>${esc(d.raw)}</pre>`;
  const counts = CATS.map(c => [c, d.relations.filter(r => r[0] === c).length]).filter(x => x[1]);
  h += `<details><summary>Relazioni: ${counts.map(x => x[0] + " " + x[1]).join(", ") || "nessuna"}</summary><ul class="rel">` +
       d.relations.map(r => `<li class="${r[0] === "corretta" ? "corretta" : r[0] === "in piu'" ? "extra" : "err"}">${esc(r[0])}: ${esc(r[1])}</li>`).join("") + `</ul></details>`;
  h += `<details><summary>Testo scritto dal modello (${esc(D.formats[$("selF").value])})</summary><pre>${esc(d.text)}</pre></details>`;
  h += d.examples.length ? `<details><summary>Esempi nel prompt (${d.examples.length}; somiglianza Jt al GT)</summary><p>${d.examples.map(([e, j]) => `${esc(e)} <span class="muted">(${f3(j)})</span>`).join(" · ")}</p></details>` : `<p class="muted">nessun esempio nel prompt</p>`;
  return h + `</div>`;
}
function render(){
  const q = $("selQ").value, f = $("selF").value, r = $("selR").value;
  const cell = ((D.exercises[q].cells[f] || {})[r]) || {};
  const best = {};
  for (const k of ["F1rel", "F1cls", "F1attr", "R", "J", "M"]){
    const vs = C.map(c => cell[c] && cell[c][k]).filter(v => v !== null && v !== undefined);
    best[k] = vs.length ? Math.max(...vs) : null;
  }
  $("where").textContent = `${Q.indexOf(q) + 1} / ${Q.length} · ${D.exercises[q].split}`;
  $("view").innerHTML = `<div class="grid"><div class="card gt"><h3><span>Ground truth</span><span class="chip">${esc(q)}</span></h3>${img("gt__" + q)}
    <details><summary>Traccia dell'esercizio</summary><div class="desc">${esc(D.exercises[q].description)}</div></details></div>
    ${C.map(c => card(c, cell[c], best)).join("")}</div>
    <p class="muted">In verde le metriche migliori tra le sei condizioni per questa ripetizione.</p>`;
  document.querySelectorAll(".diagram img").forEach(i => i.onclick = () => i.parentElement.classList.toggle("full"));
  try { localStorage.setItem("cmp3b_pos", JSON.stringify({q, f, r})); } catch (e) {}
}
function renderIndex(){
  let h = `<div class="card"><h3>F1 delle relazioni per esercizio (media delle 3 ripetizioni, abbinamento rilassato)</h3><div class="tablewrap"><table><thead><tr><th>esercizio</th>`;
  for (const f of F) h += C.map(c => `<th>${esc(D.formats[f])}<br>${esc(c)}</th>`).join("");
  h += `</tr></thead><tbody>`;
  for (const row of D.index){
    h += `<tr data-q="${esc(row.q)}"><td>${esc(row.q)}</td>`;
    for (const f of F){
      const vs = C.map(c => row[f + "__" + c]).filter(v => v !== null);
      const mx = vs.length ? Math.max(...vs) : null;
      h += C.map(c => { const v = row[f + "__" + c]; return `<td class="${v !== null && mx !== null && v >= mx - 1e-9 ? "win" : ""}">${f3(v)}</td>`; }).join("");
    }
    h += `</tr>`;
  }
  h += `</tbody></table></div><p class="muted">Clic su una riga per aprire il confronto. In verde la condizione migliore per esercizio e formato.</p></div>`;
  $("index").innerHTML = h;
  document.querySelectorAll("#index tbody tr").forEach(tr => tr.onclick = () => { $("selQ").value = tr.dataset.q; syncReps(true); show("view"); });
}
function show(which){ $("view").hidden = which !== "view"; $("index").hidden = which !== "index";
  $("tabView").classList.toggle("on", which === "view"); $("tabIndex").classList.toggle("on", which === "index"); if (which === "view") render(); }
function step(d){ const i = (Q.indexOf($("selQ").value) + d + Q.length) % Q.length; $("selQ").value = Q[i]; syncReps(true); render(); }
$("selQ").onchange = () => { syncReps(true); render(); }; $("selF").onchange = () => { syncReps(true); render(); }; $("selR").onchange = render;
$("prev").onclick = () => step(-1); $("next").onclick = () => step(1);
$("tabView").onclick = () => show("view"); $("tabIndex").onclick = () => show("index");
document.addEventListener("keydown", e => { if (e.target.tagName === "SELECT") return; if (e.key === "ArrowLeft") step(-1); if (e.key === "ArrowRight") step(1); });
try { const p = JSON.parse(localStorage.getItem("cmp3b_pos") || "null"); if (p && Q.includes(p.q)) { $("selQ").value = p.q; if (F.includes(p.f)) $("selF").value = p.f; syncReps(false); $("selR").value = p.r; } else syncReps(false); } catch (e) { syncReps(false); }
renderIndex(); render();
</script></body></html>
"""


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--esercizi", nargs="+", required=True,
                   help="id degli esercizi di valutazione da confrontare, oppure 'tutti' (i 54 di valutazione)")
    a.add_argument("--out", default=str(OUT))
    args = a.parse_args(argv)
    ids = evaluation_ids() if args.esercizi == ["tutti"] else args.esercizi
    out = Path(args.out)
    text, stats = build(load_calls(ids), svg_dir=out / "svg" if len(ids) > SVG_INLINE_MAX else None)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(text, encoding="utf-8")
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(out / "index.html")
    print(f"scritto {out / 'index.html'} ({len(text) / 1e6:.1f} MB): esercizi {stats['exercises']}, risposte "
          f"{stats['responses']}, diagrammi {stats['svgs']}/{stats['diagrams']}" +
          (f"; avvisi: {stats['errors']}" if stats["errors"] else ""))
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
