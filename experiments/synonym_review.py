"""
Revisione dei sinonimi tra classi del GT e classi delle risposte del 3b (2026-10-18, voce 152). Nessuna chiamata a un
LLM; il modello di embedding e' quello del retriever dense (all-MiniLM-L6-v2 alla revisione fissata, CPU, offline).

1. CANDIDATI (regola fissata prima della revisione): per ogni risposta valida delle run del 3b (54 di valutazione e
   26 di sviluppo, entrambi i formati), le classi del GT e della risposta NON abbinate dal livello rilassato di
   evaluation/element_metrics.py si accoppiano uno a uno (algoritmo ungherese) sulla somiglianza coseno degli
   embedding dei nomi (CamelCase spezzato, minuscole); si tengono le coppie con somiglianza >= SOGLIA. Le coppie si
   raggruppano per esercizio: ogni (esercizio, classe del GT, classe della risposta) si giudica UNA volta.
2. PAGINA DI REVISIONE (cieca rispetto al prompt e al formato: non si mostrano condizione, formato ne' somiglianza):
   per ogni coppia la classe del GT con attributi e relazioni, la classe della risposta con gli attributi e le
   relazioni piu' frequenti nelle risposte che la contengono, le frasi della traccia che citano i due nomi. Giudizi:
   "stessa classe", "classe diversa", "incerto". Salvataggio nel browser (localStorage) ed esportazione in JSON.
3. Le decisioni esportate si convertono in evaluation/synonyms_3b.yaml (passo successivo, con un'altra voce): livello
   di abbinamento "semantico" solo per l'analisi di sensibilita'; la metrica primaria non cambia.

Uso:
    python experiments/synonym_review.py [--out data/results/generation/revisione_sinonimi]
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "experiments"), str(ROOT / "generation"), str(ROOT / "retrieval"), str(ROOT)]
import review_report as rr  # noqa: E402
from evaluation import element_metrics as el  # noqa: E402

OUT = rr.RESULTS / "revisione_sinonimi"
SOGLIA = 0.5
RUNS = ([f"passo3b__{f}-{s}-G26" for f in "PC" for s in ("corpus", "testset")]
        + [f"passo3b_sviluppo__{f}-sviluppo-G26" for f in "PC"])
SHORT = {"ClassBidirectional": "associazione", "ClassUnidirectional": "associazione orientata",
         "ClassComposition": "composizione", "ClassAggregation": "aggregazione", "ClassDependency": "dipendenza",
         "ClassInheritance": "ereditarieta'", "ClassRealization": "realizzazione"}


def split_name(name: str) -> str:
    return " ".join(re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).replace("_", " ").lower().split())


def class_context(diagram: dict, cid: str) -> tuple[list[str], list[str]]:
    """(attributi, relazioni come 'tipo con Classe') di una classe del diagramma."""
    e = el.elements(diagram)
    attrs = list(e["attributes"].get(cid, []))
    rels = []
    for r in e["relations"] + e["generalizations"]:
        if cid in (r["src"], r["tgt"]):
            other = r["tgt"] if r["src"] == cid else r["src"]
            rels.append(f"{SHORT.get(r['type'], r['type'])} con {e['classes'].get(other, '?')}")
    return attrs, rels


def sentences(text: str, names: list[str], k: int = 3) -> list[str]:
    toks = set().union(*(el.tokens(n) for n in names))
    out = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip() and toks & set(el.tokens(s))]
    return out[:k]


def candidates(calls: list[dict], encode, soglia: float = SOGLIA) -> dict:
    """Esercizio -> {(nome GT, nome risposta): {"n": occorrenze, "gt_id", "attrs": Counter, "rels": Counter}}.
    encode: lista di nomi -> matrice di vettori normalizzati (righe)."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    cache: dict[str, np.ndarray] = {}

    def emb(names):
        new = [n for n in dict.fromkeys(names) if n not in cache]
        if new:
            for n, v in zip(new, encode([split_name(x) for x in new])):
                cache[n] = v
        return np.array([cache[n] for n in names])

    out: dict = defaultdict(dict)
    for c in calls:
        if c["v"].level < 3:
            continue
        r, g = el.elements(c["v"].diagram), el.elements(c["gt"])
        cmap = el.match_names(list(r["classes"].items()), list(g["classes"].items()), "relaxed")
        ug = [i for i in g["classes"] if i not in cmap.values() and el.norm(g["classes"][i])]
        ur = [i for i in r["classes"] if i not in cmap and el.norm(r["classes"][i])]
        if not ug or not ur:
            continue
        sim = emb([g["classes"][i] for i in ug]) @ emb([r["classes"][i] for i in ur]).T
        for a, b in zip(*linear_sum_assignment(-sim)):
            if sim[a, b] < soglia:
                continue
            key = (g["classes"][ug[a]], r["classes"][ur[b]])
            rec = out[c["q"]].setdefault(key, {"n": 0, "gt_id": ug[a], "attrs": Counter(), "rels": Counter()})
            rec["n"] += 1
            attrs, rels = class_context(c["v"].diagram, ur[b])
            rec["attrs"].update(attrs)
            rec["rels"].update(rels)
    return out


def unique_ci(names) -> list[str]:
    """Nomi senza duplicati che differiscono solo per maiuscole (tiene il primo, cioe' il piu' frequente)."""
    seen, out = set(), []
    for n in names:
        if el.norm(n) not in seen:
            seen.add(el.norm(n))
            out.append(n)
    return out


def build_items(cands: dict, by_id: dict) -> list[dict]:
    items = []
    for q in sorted(cands):
        gt = by_id[q]["diagram_apollon_json"]
        for (gname, rname), rec in sorted(cands[q].items()):
            gattrs, grels = class_context(gt, rec["gt_id"])
            pid = hashlib.sha256(f"{q}|{gname}|{rname}".encode()).hexdigest()[:12]
            items.append({"id": pid, "esercizio": q, "gt": gname, "risposta": rname, "occorrenze": rec["n"],
                          "gt_attributi": gattrs, "gt_relazioni": grels,
                          "risp_attributi": unique_ci(a for a, _ in rec["attrs"].most_common())[:8],
                          "risp_relazioni": [x for x, _ in rec["rels"].most_common(6)],
                          "frasi": sentences(by_id[q].get("description") or "", [gname, rname])})
    return items


PAGE = """<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revisione sinonimi</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--muted:#5d6675;--line:#d9dde4;--ok:#1e7a46;--bad:#b3261e;--accent:#2f5bd3;--warn:#a15c00}
@media (prefers-color-scheme:dark){:root{--bg:#14171c;--card:#1d2128;--ink:#e6e9ef;--muted:#9aa3b2;--line:#323844;--ok:#5cc28a;--bad:#ff8a80;--accent:#8ab0ff;--warn:#f0b35a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,Segoe UI,Roboto,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
header h1{font-size:16px;margin:0 8px 0 0}button,select{font:inherit;padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink);cursor:pointer}
button:hover{border-color:var(--accent)}main{max-width:1100px;margin:0 auto;padding:16px}
.bar{height:6px;background:var(--line);border-radius:3px;flex:1;min-width:120px}.bar>div{height:100%;background:var(--accent);border-radius:3px}
h2{font-size:15px;margin:22px 0 8px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:10px 0}
.card.d-stessa{border-left:5px solid var(--ok)}.card.d-diversa{border-left:5px solid var(--bad)}.card.d-incerto{border-left:5px solid var(--warn)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media (max-width:700px){.cols{grid-template-columns:1fr}}
.name{font-weight:600;font-size:15px}.lab{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
ul{margin:4px 0;padding-left:18px}.frasi{margin-top:8px;font-size:13px;color:var(--muted)}.frasi q{color:var(--ink)}
.act{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}.act button.on.stessa{background:var(--ok);color:#fff;border-color:var(--ok)}
.act button.on.diversa{background:var(--bad);color:#fff;border-color:var(--bad)}.act button.on.incerto{background:var(--warn);color:#fff;border-color:var(--warn)}
.muted{color:var(--muted)}
</style></head><body>
<header><h1>Revisione sinonimi delle classi</h1>
<span class="muted" id="cnt"></span><div class="bar"><div id="prog" style="width:0"></div></div>
<select id="flt" aria-label="filtro"><option value="tutte">tutte</option><option value="da">da giudicare</option><option value="incerto">incerte</option></select>
<button id="exp">Esporta decisioni (JSON)</button><label class="muted"><input type="file" id="imp" accept=".json" hidden><span style="cursor:pointer;text-decoration:underline">importa</span></label>
</header>
<main><p class="muted">Per ogni coppia: la classe del diagramma di riferimento (sinistra) e quella scritta dal modello (destra) indicano
lo <b>stesso concetto</b>? Giudica sul significato nel contesto dell'esercizio, non sulla somiglianza del nome. Tasti: 1 = stessa,
2 = diversa, 3 = incerto, sulla coppia evidenziata (clic per selezionarla). Le decisioni restano salvate in questo browser;
alla fine premi <b>Esporta</b> e mandami il file.</p><div id="list"></div></main>
<script>
const ITEMS = __DATA__;
const KEY = "sinonimi_3b_v1";
let dec = {}; try { dec = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
let sel = null;
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const li = xs => xs.length ? "<ul>" + xs.map(x => `<li>${esc(x)}</li>`).join("") + "</ul>" : `<p class="muted">nessuno</p>`;
function save(){ try { localStorage.setItem(KEY, JSON.stringify(dec)); } catch (e) {} }
function card(it){
  const d = dec[it.id] || "";
  return `<div class="card ${d ? "d-" + d : ""}" id="c${it.id}" tabindex="0"><div class="cols">
    <div><div class="lab">Diagramma di riferimento</div><div class="name">${esc(it.gt)}</div>
      <div class="lab">attributi</div>${li(it.gt_attributi)}<div class="lab">relazioni</div>${li(it.gt_relazioni)}</div>
    <div><div class="lab">Risposta del modello (in ${it.occorrenze} risposte)</div><div class="name">${esc(it.risposta)}</div>
      <div class="lab">attributi più frequenti</div>${li(it.risp_attributi)}<div class="lab">relazioni più frequenti</div>${li(it.risp_relazioni)}</div></div>
    ${it.frasi.length ? `<div class="frasi">Dalla traccia: ${it.frasi.map(f => `<q>${esc(f)}</q>`).join(" ")}</div>` : ""}
    <div class="act">${[["stessa","1 · stessa classe"],["diversa","2 · classe diversa"],["incerto","3 · incerto"]].map(([v,l]) =>
      `<button class="${v} ${d === v ? "on" : ""}" data-id="${it.id}" data-v="${v}">${l}</button>`).join("")}</div></div>`;
}
function render(){
  const f = document.getElementById("flt").value;
  const groups = {};
  for (const it of ITEMS){
    const d = dec[it.id];
    if (f === "da" && d) continue; if (f === "incerto" && d !== "incerto") continue;
    (groups[it.esercizio] = groups[it.esercizio] || []).push(it);
  }
  document.getElementById("list").innerHTML = Object.entries(groups).map(([q, its]) =>
    `<h2>${esc(q)} <span class="muted">(${its.length})</span></h2>` + its.map(card).join("")).join("") || `<p class="muted">Niente da mostrare.</p>`;
  document.querySelectorAll(".act button").forEach(b => b.onclick = () => set(b.dataset.id, b.dataset.v));
  document.querySelectorAll(".card").forEach(c => c.onclick = () => { sel = c.id.slice(1); document.querySelectorAll(".card").forEach(x => x.style.outline = ""); c.style.outline = "2px solid var(--accent)"; });
  const n = ITEMS.filter(it => dec[it.id]).length;
  document.getElementById("cnt").textContent = `${n} / ${ITEMS.length} giudicate`;
  document.getElementById("prog").style.width = (100 * n / ITEMS.length) + "%";
}
function set(id, v){ dec[id] = dec[id] === v ? undefined : v; if (!dec[id]) delete dec[id]; save(); const y = window.scrollY; render(); window.scrollTo(0, y); }
document.addEventListener("keydown", e => { if (!sel || !["1","2","3"].includes(e.key)) return; set(sel, {"1":"stessa","2":"diversa","3":"incerto"}[e.key]); });
document.getElementById("flt").onchange = render;
document.getElementById("exp").onclick = () => {
  const out = ITEMS.map(it => ({id: it.id, esercizio: it.esercizio, gt: it.gt, risposta: it.risposta, decisione: dec[it.id] || null}));
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify({versione: KEY, decisioni: out}, null, 1)], {type: "application/json"}));
  a.download = "revisione_sinonimi.json"; a.click();
};
document.getElementById("imp").onchange = e => { const f = e.target.files[0]; if (!f) return; f.text().then(t => {
  try { for (const x of JSON.parse(t).decisioni) if (x.decisione) dec[x.id] = x.decisione; save(); render(); } catch (err) { alert("file non valido"); } }); };
render();
</script></body></html>
"""


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--out", default=str(OUT))
    args = a.parse_args(argv)
    import corpus_loader as cl
    from prompt_builder import dense_model
    from dense_retriever import load_sentence_transformer
    by_id = {c["id"]: c for c in cl.load_candidates() + cl.load_queries()}
    gt = {i: c["diagram_apollon_json"] for i, c in by_id.items()}
    calls = [c for r in RUNS for c in rr.load_run(rr.RESULTS / r, {}, gt)]
    model = load_sentence_transformer(*dense_model())
    items = build_items(candidates(calls, lambda xs: model.encode(xs, normalize_embeddings=True)), by_id)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "candidati.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "index.html").write_text(PAGE.replace("__DATA__", json.dumps(items, ensure_ascii=False).replace("</", "<\\/")),
                                    encoding="utf-8")
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(out / "index.html")
    print(f"scritto {out / 'index.html'}: {len(items)} coppie da {len({i['esercizio'] for i in items})} esercizi, "
          f"{sum(i['occorrenze'] for i in items)} occorrenze nelle risposte ({len(calls)} risposte)")
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
