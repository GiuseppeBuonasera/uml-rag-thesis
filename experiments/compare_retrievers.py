"""
Strumento di confronto visivo bm25 / hybrid / ground truth (2026-10-12, voce 145). Sola lettura: nessuna chiamata a un
LLM, nessuna metrica nuova.

Una pagina HTML autonoma (nessuna risorsa esterna; i diagrammi sono SVG incorporati) per confrontare, esercizio per
esercizio, il diagramma di riferimento con le risposte di Gemma 4 26B A4B QAT nelle due condizioni di retrieval del
3b, con la configurazione di lavoro (vista degli esempi clean_v1):
- bm25 k = 3: dev_g26ev per le 8 query toccate dalla pulizia, dev_g26 per le altre 12 (prompt identici, voce 140);
- hybrid k = 3: dev_g26hy.
Per ogni esercizio, formato (PlantUML / compatto) e ripetizione: GT | bm25 | hybrid affiancati (classi verdi = nel GT,
arancioni = in piu'), metriche per risposta (validita', F1 di relazioni, classi e generalizzazioni con abbinamento
rilassato, R, J, M), relazioni classificate (corretta, tipo sbagliato, direzione invertita, molteplicita' diverse,
mancante, in piu'), esempi usati nel prompt, traccia dell'esercizio. Indice con F1 delle relazioni medio per retriever.

Rendering, validazione e classificazione: quelli di experiments/review_report.py; F1: evaluation/element_metrics.py.
Richiede Java e .tools/plantuml-old.jar.

Uso:
    python experiments/compare_retrievers.py [--out data/results/generation/confronto_bm25_hybrid]
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "experiments"), str(ROOT / "generation"), str(ROOT / "retrieval"), str(ROOT)]
import review_report as rr  # noqa: E402
from evaluation import element_metrics as el  # noqa: E402

GEN = rr.RESULTS
OUT = GEN / "confronto_bm25_hybrid"
FORMATS = {"P-G": "PlantUML", "C-G": "JSON compatto"}
RETRIEVERS = ("bm25", "hybrid")


def load_calls(results: Path = GEN) -> dict:
    """(retriever, configurazione) -> risposte, con la baseline bm25 ricostruita come nella voce 140."""
    import corpus_loader as cl
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    clean_ids = set(yaml.safe_load((ROOT / "experiments" / "configs" / "dev_g26ev.yaml").read_text(encoding="utf-8"))
                    ["query_ids"])
    out = {}
    for conf in FORMATS:
        raw = [c for c in rr.load_run(results / f"dev_g26__{conf}", {}, gt) if c["q"] not in clean_ids]
        clean = rr.load_run(results / f"dev_g26ev__{conf}", {}, gt)
        out[("bm25", conf)] = raw + clean
        out[("hybrid", conf)] = rr.load_run(results / f"dev_g26hy__{conf}", {}, gt)
    return out


def describe(c: dict) -> dict:
    m = rr.response_metrics(c)
    s = el.evaluate_call(c)["relaxed"]["scores"]
    return {"level": c["v"].level, "failure": c["v"].failure or "", "V": m["V"], "Vc": m["Vc"], "J": m["J"], "R": m["R"],
            "M": m["M"], "F1rel": s["relations"]["F1"], "F1cls": s["classes"]["F1"], "F1gen": s["generalizations"]["F1"],
            "relations": rr.classify_relations(c["v"].diagram if c["v"].level >= 3 else None, c["gt"]),
            "examples": c["m"]["example_ids"], "raw": c["raw"]["text"] if c["v"].level < 3 else ""}


def build(calls: dict, jar: Path = rr.DEFAULT_JAR) -> tuple[str, dict]:
    import corpus_loader as cl
    cands = {c["id"]: c for c in cl.load_candidates()}
    exercises = sorted({c["q"] for v in calls.values() for c in v})
    sources, data = {}, {"exercises": {}, "formats": FORMATS}
    for q in exercises:
        sources[f"gt__{q}"] = rr.colored_plantuml(cands[q]["diagram_apollon_json"], q, None)
        data["exercises"][q] = {"description": cands[q].get("description") or "", "cells": {}}
    for (ret, conf), cs in calls.items():
        for c in cs:
            key = f"{ret}__{conf}__{c['q']}__r{c['r']}"
            d = describe(c)
            if c["v"].level >= 3:
                try:
                    sources[key] = rr.colored_plantuml(c["v"].diagram, c["m"]["call_id"], rr.ap.class_names(c["gt"]))
                except rr.us.StructureError:
                    pass
            d["svg"] = key
            data["exercises"][c["q"]]["cells"].setdefault(conf, {}).setdefault(f"r{c['r']}", {})[ret] = d
    svgs, errors = rr.render_svgs(sources, jar)
    data["svgs"] = {k: base64.b64encode(v.encode("utf-8")).decode() for k, v in svgs.items()}
    # indice: F1 delle relazioni medio sulle ripetizioni, per esercizio, formato e retriever
    index = []
    for q in exercises:
        row = {"q": q}
        for conf in FORMATS:
            for ret in RETRIEVERS:
                vals = [d[ret]["F1rel"] for d in data["exercises"][q]["cells"].get(conf, {}).values()
                        if ret in d and d[ret]["F1rel"] is not None]
                row[f"{conf}__{ret}"] = statistics.mean(vals) if vals else None
        index.append(row)
    data["index"] = index
    stats = {"exercises": len(exercises), "responses": sum(len(v) for v in calls.values()), "diagrams": len(sources),
             "svgs": len(svgs), "errors": errors}
    return PAGE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")), stats


PAGE = """<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Confronto bm25 / hybrid</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--muted:#5d6675;--line:#d9dde4;--ok:#1e7a46;--bad:#b3261e;--accent:#2f5bd3;--warn:#a15c00}
@media (prefers-color-scheme:dark){:root{--bg:#14171c;--card:#1d2128;--ink:#e6e9ef;--muted:#9aa3b2;--line:#323844;--ok:#5cc28a;--bad:#ff8a80;--accent:#8ab0ff;--warn:#f0b35a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,Segoe UI,Roboto,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
header h1{font-size:16px;margin:0 12px 0 0}select,button{font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink)}
button{cursor:pointer}button:hover{border-color:var(--accent)}.tabs button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
main{padding:16px;max-width:1800px;margin:0 auto}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
@media (max-width:1100px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;min-width:0}
.card h3{margin:0 0 6px;font-size:15px;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.diagram{background:#fff;border-radius:6px;overflow:auto;max-height:70vh;border:1px solid var(--line)}.diagram img{display:block;max-width:100%;height:auto;cursor:zoom-in}
.diagram.full img{max-width:none;cursor:zoom-out}
.m{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.chip{border:1px solid var(--line);border-radius:12px;padding:1px 8px;font-size:12px}
.chip.best{border-color:var(--ok);color:var(--ok);font-weight:600}.chip.bad{border-color:var(--bad);color:var(--bad)}
details{margin-top:6px}summary{cursor:pointer;color:var(--muted)}ul.rel{margin:6px 0;padding-left:18px;font-size:12.5px}
li.corretta{color:var(--ok)}li.err{color:var(--bad)}li.extra{color:var(--warn)}pre{white-space:pre-wrap;font-size:12px;background:var(--bg);padding:8px;border-radius:6px;max-height:300px;overflow:auto}
.legend span{display:inline-block;padding:0 6px;border-radius:4px;margin-right:6px;color:#111;font-size:12px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:right}th:first-child,td:first-child{text-align:left}
tbody tr{cursor:pointer}tbody tr:hover{background:var(--bg)}td.win{color:var(--ok);font-weight:600}.muted{color:var(--muted)}
.desc{white-space:pre-wrap;font-size:13px;max-height:260px;overflow:auto}
</style></head><body>
<header><h1>GT · bm25 · hybrid</h1>
<span class="tabs"><button id="tabView" class="on">Confronto</button> <button id="tabIndex">Indice</button></span>
<select id="selQ" aria-label="esercizio"></select><select id="selF" aria-label="formato"></select><select id="selR" aria-label="ripetizione"></select>
<button id="prev" title="esercizio precedente (←)">◀</button><button id="next" title="esercizio successivo (→)">▶</button>
<span class="legend"><span style="background:#D8F0DF">classe nel GT</span><span style="background:#FBD9B5">classe in più</span></span>
<span class="muted" id="where"></span></header>
<main><section id="view"></section><section id="index" hidden></section></main>
<script>
const D = __DATA__;
const Q = Object.keys(D.exercises), F = Object.keys(D.formats);
const $ = id => document.getElementById(id);
const f3 = x => x === null || x === undefined ? "—" : (+x).toFixed(2);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const img = key => D.svgs[key] ? `<div class="diagram"><img alt="diagramma" src="data:image/svg+xml;base64,${D.svgs[key]}"></div>` : `<p class="muted">diagramma non disponibile</p>`;
const CATS = ["corretta","tipo sbagliato","direzione invertita","molteplicita' diverse","mancante","in piu'"];
function fill(sel, items, labels){ sel.innerHTML = items.map(v => `<option value="${esc(v)}">${esc(labels ? labels[v] : v)}</option>`).join(""); }
fill($("selQ"), Q); fill($("selF"), F, D.formats);
function reps(){ const c = D.exercises[$("selQ").value].cells[$("selF").value] || {}; return Object.keys(c).sort(); }
function syncReps(keep){ const r = reps(); const old = $("selR").value; fill($("selR"), r); if (keep && r.includes(old)) $("selR").value = old; }
function card(title, d, other){
  if (!d) return `<div class="card"><h3>${title}</h3><p class="muted">risposta assente</p></div>`;
  const better = (a, b) => a !== null && b !== null && b !== undefined && a > b + 1e-9;
  const chip = (lab, v, o) => `<span class="chip ${better(v, o) ? "best" : ""}">${lab} ${f3(v)}</span>`;
  const o = other || {};
  let h = `<div class="card"><h3><span>${title}</span><span class="chip ${d.level >= 3 ? "" : "bad"}">livello ${d.level}${d.failure ? " · " + esc(d.failure) : ""}</span></h3>`;
  h += `<div class="m">${chip("F1 relazioni", d.F1rel, o.F1rel)}${chip("F1 classi", d.F1cls, o.F1cls)}${chip("F1 generalizz.", d.F1gen, o.F1gen)}${chip("R", d.R, o.R)}${chip("J", d.J, o.J)}${chip("M", d.M, o.M)}</div>`;
  h += d.level >= 3 ? img(d.svg) : `<p class="muted">Risposta non valida: testo grezzo</p><pre>${esc(d.raw)}</pre>`;
  const counts = CATS.map(c => [c, d.relations.filter(r => r[0] === c).length]).filter(x => x[1]);
  h += `<details><summary>Relazioni: ${counts.map(x => x[0] + " " + x[1]).join(", ") || "nessuna"}</summary><ul class="rel">` +
       d.relations.map(r => `<li class="${r[0] === "corretta" ? "corretta" : r[0] === "in piu'" ? "extra" : "err"}">${esc(r[0])}: ${esc(r[1])}</li>`).join("") + `</ul></details>`;
  h += `<details><summary>Esempi nel prompt (${d.examples.length})</summary><p>${d.examples.map(esc).join(" · ")}</p></details></div>`;
  return h;
}
function render(){
  const q = $("selQ").value, f = $("selF").value, r = $("selR").value;
  const cell = ((D.exercises[q].cells[f] || {})[r]) || {};
  $("where").textContent = `${Q.indexOf(q) + 1} / ${Q.length}`;
  $("view").innerHTML = `<div class="grid"><div class="card"><h3><span>Ground truth</span><span class="chip">${esc(q)}</span></h3>${img("gt__" + q)}
    <details><summary>Traccia dell'esercizio</summary><div class="desc">${esc(D.exercises[q].description)}</div></details></div>
    ${card("bm25", cell.bm25, cell.hybrid)}${card("hybrid", cell.hybrid, cell.bm25)}</div>`;
  document.querySelectorAll(".diagram img").forEach(i => i.onclick = () => i.parentElement.classList.toggle("full"));
  try { localStorage.setItem("cmp_pos", JSON.stringify({q, f, r})); } catch (e) {}
}
function renderIndex(){
  const cols = F.flatMap(f => ["bm25", "hybrid"].map(r => [f, r]));
  let h = `<div class="card"><h3>F1 delle relazioni per esercizio (media delle ripetizioni, abbinamento rilassato)</h3><table><thead><tr><th>esercizio</th>` +
    cols.map(([f, r]) => `<th>${esc(D.formats[f])}<br>${r}</th>`).join("") + `</tr></thead><tbody>`;
  const wins = {};
  for (const row of D.index){
    h += `<tr data-q="${esc(row.q)}"><td>${esc(row.q)}</td>`;
    for (const [f, r] of cols){
      const v = row[f + "__" + r], o = row[f + "__" + (r === "bm25" ? "hybrid" : "bm25")];
      const win = v !== null && o !== null && v > o + 1e-9;
      if (win) wins[f + r] = (wins[f + r] || 0) + 1;
      h += `<td class="${win ? "win" : ""}">${f3(v)}</td>`;
    }
    h += `</tr>`;
  }
  h += `</tbody><tfoot><tr><td class="muted">esercizi in cui vince</td>` + cols.map(([f, r]) => `<td>${wins[f + r] || 0}</td>`).join("") + `</tr></tfoot></table>
    <p class="muted">Clic su una riga per aprire il confronto. In verde il retriever con F1 più alto nell'esercizio e formato.</p></div>`;
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
try { const p = JSON.parse(localStorage.getItem("cmp_pos") || "null"); if (p && Q.includes(p.q)) { $("selQ").value = p.q; if (F.includes(p.f)) $("selF").value = p.f; syncReps(false); $("selR").value = p.r; } else syncReps(false); } catch (e) { syncReps(false); }
renderIndex(); render();
</script></body></html>
"""


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--out", default=str(OUT))
    args = a.parse_args(argv)
    text, stats = build(load_calls())
    out = Path(args.out)
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
