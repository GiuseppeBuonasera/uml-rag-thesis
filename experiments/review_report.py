"""
Report grafico di revisione delle generazioni (2026-10-09): una pagina HTML statica e autonoma (SVG incorporati come
immagini data:, nessuna risorsa esterna, nessuno script) per rivedere le risposte gia' salvate confrontandole con il
ground truth. Solo lettura: nessuna chiamata a un LLM, nessuna modifica a post-processing, validatori o metriche.

Per ogni run indicata (cartelle di data/results/generation/): validazione con la stessa funzione del runner
(analyze_dev.validate: PlantUML con la versione del post-processing registrata nella provenienza, compatto,
Apollon completo con postprocess.validate_response). Rendering: TUTTO passa per la struttura comune
(generation/uml_structure.py): GT e risposte valide -> structure_from_apollon -> espansore -> PlantUML canonico
(plantuml_format.apollon_to_plantuml) -> SVG con plantuml.jar in locale e `!pragma layout smetana` (niente Graphviz,
niente server). Stesso motore e stesso stile per GT, PlantUML e compatto.

Confronto con il GT (funzioni gia' in uso, non riscritte): classi con analyze_pilot.class_names; relazioni con
analyze_instructions.match (accoppiamento 1:1 per coppia di classi di analyze_pilot.compare_relations), gt_ends e
resp_mult. Classificazione di ogni relazione: corretta / tipo sbagliato / direzione invertita (stesso tipo orientato) /
molteplicita' diverse (stesso tipo e verso) / mancante (nel GT, senza coppia nella risposta) / in piu'. Metriche per
risposta: V (valida fino a L3), Vc (valida e senza scarti), J (Jaccard dei nomi di classe), R (relazioni del GT con
stessa coppia e stesso tipo / relazioni del GT), M (estremi del GT con molteplicita' esplicita uguale, voce 98); 0 per
le risposte non valide, come nelle analisi.

Uso:
    python experiments/review_report.py --runs dev_k__P-G dev_k__C-G --filter k=3 [--name dev_k_k3]
        [--out DIR] [--plantuml-jar .tools/plantuml-old.jar]
Filtri: k=<int>, rep=<int>, q=<id esercizio>, cond=<condizione> (ripetibili). Uscita: data/results/generation/<nome>_review/index.html
(non versionata: .gitignore esclude i file delle cartelle dei risultati salvo summary.md e simili).
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
sys.path.insert(0, str(ROOT / "experiments"))
import analyze_dev as ad  # noqa: E402  (validazione: stessa del runner)
import analyze_instructions as ai  # noqa: E402  (match, gt_ends, resp_mult, multiplicity_counts)
import analyze_pilot as ap  # noqa: E402  (class_names)
import plantuml_postprocess as ppu  # noqa: E402
import postprocess as pp  # noqa: E402
import render_pilot2 as rp  # noqa: E402  (CSS, esc)
import uml_structure as us  # noqa: E402
from plantuml_format import apollon_to_plantuml  # noqa: E402
from prompt_builder import cl  # noqa: E402
import provenance  # noqa: E402  (riga di provenienza, voce 106)

RESULTS = ROOT / "data" / "results" / "generation"
DEFAULT_JAR = ROOT / ".tools" / "plantuml-old.jar"
GREEN, ORANGE = "#D8F0DF", "#FBD9B5"
REL_CATEGORIES = ("corretta", "tipo sbagliato", "direzione invertita", "molteplicita' diverse", "mancante", "in piu'")
CLASS_LINE = re.compile(r"^(abstract class|class|interface|enum) (\w+) (\{.*)$")
EXTRA_CSS = """
.diagrams{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:8px;flex:1 1 360px;max-width:100%}
.card img{max-width:100%;height:auto;background:#fff;border-radius:4px}
.card h4{margin:0 0 6px}.metrics{font-size:.85rem;color:var(--muted);margin:4px 0}
.rel li{font-size:.85rem}.rel .corretta{color:var(--ok)}.rel .err{color:var(--bad)}
.legend span{display:inline-block;padding:0 6px;border-radius:4px;margin-right:6px;color:#111}
"""


# --- caricamento ----------------------------------------------------------------------------------------------------


def parse_filters(items: list[str]) -> dict:
    out = {}
    for it in items or []:
        key, _, val = it.partition("=")
        if key not in ("k", "rep", "q", "cond") or not val:
            raise SystemExit(f"filtro non valido {it!r}: usare k=<int>, rep=<int>, q=<id>, cond=<condizione>")
        out.setdefault(key, set()).add(val)
    return out


def keep(m: dict, filters: dict) -> bool:
    return (("k" not in filters or str(m.get("k")) in filters["k"]) and
            ("rep" not in filters or str(m.get("repetition")) in filters["rep"]) and
            ("q" not in filters or m.get("query_id") in filters["q"]) and
            ("cond" not in filters or m.get("condition") in filters["cond"]))


def load_run(run_dir: Path, filters: dict, gt: dict[str, dict]) -> list[dict]:
    saved = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    cfg, prov = saved["config"], saved.get("provenance", {})
    fmt = (cfg.get("prompt") or {}).get("output_format", "apollon")
    version = prov.get("plantuml_postprocess_version", ppu.DEFAULT_VERSION)
    calls = []
    for line in (run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        m = json.loads(line)
        if not keep(m, filters):
            continue
        raw = json.loads((run_dir / "raw" / f"{m['call_id']}.json").read_text(encoding="utf-8"))
        v = (pp.validate_response(raw["text"], raw["finish_reason"]) if fmt == "apollon"
             else ad.validate(fmt, raw["text"], raw["finish_reason"], m["call_id"], version))
        cond = f"{run_dir.name} {m.get('condition')} k={m.get('k')}"  # condizione: piu' retriever nella stessa run (voce 109)
        calls.append({"m": m, "raw": raw, "v": v, "gt": gt[m["query_id"]], "q": m["query_id"], "r": m["repetition"],
                      "format": fmt, "cond": cond, "version": version if fmt == "plantuml" else ""})
    return calls


# --- confronto con il GT (funzioni esistenti) -----------------------------------------------------------------------


def classify_relations(resp: dict | None, gt: dict) -> list[tuple[str, str]]:
    """(categoria, descrizione) per ogni relazione del GT e per quelle in piu' della risposta."""
    def desc(e):
        ms = e["mult"]["_self"] if "_self" in e["mult"] else (e["mult"].get(e["src"], ""), e["mult"].get(e["tgt"], ""))
        mult = f", {ms[0] or '·'} / {ms[1] or '·'}" if any(ms) else ""
        return f"{e['src']} → {e['tgt']} ({ai.SHORT[e['type']]}{mult})"

    if resp is None:
        return [("mancante", desc(g)) for g in ap.edges(gt)]
    pairs, missing, extra = ai.match(resp, gt)
    out = []
    for r, g in pairs:
        if r["type"] != g["type"]:
            cat = "tipo sbagliato"
        elif g["type"] in ai.ORIENTED and (r["src"], r["tgt"]) != (g["src"], g["tgt"]):
            cat = "direzione invertita"
        elif any(ai.resp_mult(r, key) != gm for key, gm in ai.gt_ends(g)):
            cat = "molteplicita' diverse"
        else:
            cat = "corretta"
        out.append((cat, f"GT {desc(g)} — risposta {desc(r)}" if cat != "corretta" else desc(g)))
    out += [("mancante", desc(g)) for g in missing]
    out += [("in piu'", desc(r)) for r in extra]
    return out


def response_metrics(c: dict) -> dict:
    """Le stesse definizioni di analyze_dev.metrics e analyze_instructions (0 per le non valide), su una risposta."""
    valid = c["v"].level >= 3
    gt_edges = len(c["gt"]["edges"])
    j = cl.jaccard(ap.class_names(c["v"].diagram), ap.class_names(c["gt"])) if valid else 0.0
    r = ap.compare_relations(c["v"].diagram, c["gt"])["same_type"] / gt_edges if valid and gt_edges else 0.0
    mc = ai.multiplicity_counts(c)
    return {"V": int(valid), "Vc": int(ad.is_clean(c)) if c["format"] != "apollon" else int(valid), "J": j, "R": r,
            "M": mc["explicit_same"] / mc["explicit"] if mc["explicit"] else None}


# --- rendering ------------------------------------------------------------------------------------------------------


def colored_plantuml(diagram: dict, model_id: str, gt_names: set[str] | None) -> str:
    """Diagramma -> struttura comune -> espansore -> PlantUML canonico, con le classi colorate (verde = nel GT,
    arancione = in piu') e il layout smetana."""
    st = us.structure_from_apollon(diagram)
    text = apollon_to_plantuml(us.expand(st, model_id)[0])
    lines = []
    for line in text.splitlines():
        m = CLASS_LINE.match(line)
        if m and gt_names is not None:
            color = GREEN if ap.norm(m.group(2)) in gt_names else ORANGE
            line = f"{m.group(1)} {m.group(2)} {color} {m.group(3)}"
        lines.append(line)
    return "\n".join(lines).replace("@startuml", "@startuml\n!pragma layout smetana", 1)


def render_svgs(sources: dict[str, str], jar: Path) -> tuple[dict[str, str], list[str]]:
    """Un'unica JVM: scrive i .puml in una cartella temporanea e li rende in SVG. Ritorna (nome -> svg, errori)."""
    out, errors = {}, []
    with tempfile.TemporaryDirectory(prefix="review_puml_") as tmp:
        tmp = Path(tmp)
        for name, text in sources.items():
            (tmp / f"{name}.puml").write_text(text, encoding="utf-8")
        proc = subprocess.run(["java", "-jar", str(jar), "-charset", "UTF-8", "-tsvg", str(tmp)],
                              capture_output=True, text=True)
        if proc.returncode not in (0, 200):  # 200: almeno un diagramma con errori, gli altri sono comunque resi
            errors.append(f"plantuml.jar: codice {proc.returncode}: {proc.stderr.strip()[:300]}")
        for name in sources:
            svg = tmp / f"{name}.svg"
            if svg.exists() and b"Syntax Error" not in svg.read_bytes()[:20000]:
                out[name] = svg.read_text(encoding="utf-8")
            else:
                errors.append(f"{name}: SVG non prodotto (errore di sintassi PlantUML)")
    return out, errors


def img(svg: str) -> str:
    return f'<img alt="diagramma" src="data:image/svg+xml;base64,{base64.b64encode(svg.encode("utf-8")).decode()}">'


# --- pagina ---------------------------------------------------------------------------------------------------------


def fmt(x) -> str:
    return "—" if x is None else (f"{x:.2f}" if isinstance(x, float) else str(x))


def build(calls: list[dict], jar: Path, title: str) -> tuple[str, dict]:
    t0 = time.time()
    cands = {c["id"]: c for c in cl.load_candidates()}
    queries = sorted({c["q"] for c in calls})
    conds = sorted({c["cond"] for c in calls})
    for c in calls:
        c["metrics"] = response_metrics(c)
        c["relations"] = classify_relations(c["v"].diagram if c["v"].level >= 3 else None, c["gt"])
    sources = {}
    for q in queries:
        sources[f"gt__{q}"] = colored_plantuml(cands[q]["diagram_apollon_json"], q, None)
    undrawable = []
    for i, c in enumerate(calls):
        if c["v"].level >= 3:
            try:
                sources[f"r{i}"] = colored_plantuml(c["v"].diagram, c["m"]["call_id"], ap.class_names(c["gt"]))
            except us.StructureError as e:  # non dovrebbe accadere per una risposta valida fino a L3
                undrawable.append(f"{c['cond']} {c['m']['call_id']}: {e}")
    svgs, errors = render_svgs(sources, jar)
    render_s = time.time() - t0

    H = ["<!doctype html><html lang=\"it\"><head><meta charset=\"utf-8\">",
         "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
         f"<title>{rp.esc(title)}</title>", f"<style>{rp.CSS}{EXTRA_CSS}</style></head><body><main>",
         f"<h1>Revisione delle generazioni — {rp.esc(title)}</h1>",
         "<p class=\"note\">Pagina generata da <code>experiments/review_report.py</code> in sola lettura dalle risposte "
         "grezze; validazione come il runner; rendering: struttura comune → espansore → PlantUML canonico → SVG "
         "(plantuml.jar locale, layout smetana). Metriche per risposta: V, Vc, J, R, M come nelle analisi (0 per le "
         "non valide). Confronto per contenuto, mai per id.</p>",
         f"<p class=\"note\">{rp.esc(provenance.provenance_line()).replace('`', '')}</p>",
         f"<p class=\"legend\"><span style=\"background:{GREEN}\">classe presente nel GT</span>"
         f"<span style=\"background:{ORANGE}\">classe in più rispetto al GT</span></p>"]
    # indice
    H += ["<h2 id=\"indice\">Indice</h2><div class=\"wrap\"><table><tr><th>esercizio</th>" +
          "".join(f"<th>{rp.esc(cnd)}<br><span class=\"muted\">V / Vc / J / R / M</span></th>" for cnd in conds) + "</tr>"]
    for q in queries:
        cells = []
        for cnd in conds:
            ms = [c["metrics"] for c in calls if c["q"] == q and c["cond"] == cnd]
            if not ms:
                cells.append("<td>—</td>")
                continue
            avg = {k: statistics.mean(x[k] for x in ms if x[k] is not None) if any(x[k] is not None for x in ms)
                   else None for k in ("V", "Vc", "J", "R", "M")}
            cells.append("<td>" + " / ".join(fmt(float(avg[k]) if avg[k] is not None else None)
                                             for k in ("V", "Vc", "J", "R", "M")) + "</td>")
        H.append(f"<tr><td><a href=\"#{rp.esc(q)}\">{rp.esc(q)}</a></td>{''.join(cells)}</tr>")
    H.append("</table></div>")

    for q in queries:
        gt = cands[q]["diagram_apollon_json"]
        H += [f"<h2 id=\"{rp.esc(q)}\">{rp.esc(q)}</h2>",
              "<p class=\"muted\"><a href=\"#indice\">torna all'indice</a></p>",
              f"<details><summary>Testo dei requisiti</summary><div class=\"desc\">"
              f"{rp.esc(cands[q].get('description') or '')}</div></details>",
              "<div class=\"diagrams\"><div class=\"card\"><h4>Ground truth</h4>" +
              (img(svgs[f'gt__{q}']) if f"gt__{q}" in svgs else "<p class=\"muted\">GT non disegnabile</p>") +
              "</div></div>"]
        H.append("<div class=\"diagrams\">")
        for i, c in enumerate(calls):
            if c["q"] != q:
                continue
            v, mt = c["v"], c["metrics"]
            head = (f"<h4>{rp.esc(c['cond'])} · r{c['r']} {rp.badge(v.level, v.truncated)}</h4>"
                    f"<p class=\"metrics\">V {mt['V']} · Vc {mt['Vc']} · J {fmt(mt['J'])} · R {fmt(mt['R'])} · M "
                    f"{fmt(mt['M'])} · livello {v.level}{' · fallimento ' + rp.esc(v.failure) if v.failure else ''}"
                    f"{' · post-processing ' + c['version'] if c['version'] else ''}</p>")
            body = []
            if v.level >= 3:
                body.append(img(svgs[f"r{i}"]) if f"r{i}" in svgs else "<p class=\"muted\">diagramma non disegnabile</p>")
                missing = sorted(ap.class_names(c["gt"]) - ap.class_names(v.diagram))
                body.append(f"<p class=\"metrics\">Classi del GT mancanti: {rp.esc(', '.join(missing) or 'nessuna')}</p>")
            else:
                body.append(f"<p class=\"metrics\">Risposta non valida (livello {v.level}, {rp.esc(v.failure)}): testo "
                            f"grezzo</p><pre>{rp.esc(c['raw']['text'])}</pre>")
            counts = {cat: sum(1 for k, _ in c["relations"] if k == cat) for cat in REL_CATEGORIES}
            rel = "".join(f"<li class=\"{'corretta' if k == 'corretta' else 'err'}\">{rp.esc(k)}: {rp.esc(d)}</li>"
                          for cat in REL_CATEGORIES for k, d in c["relations"] if k == cat)
            body.append("<details><summary>Relazioni: " + ", ".join(f"{k} {n}" for k, n in counts.items() if n) +
                        f"</summary><ul class=\"rel\">{rel}</ul></details>")
            H.append(f"<div class=\"card\">{head}{''.join(body)}</div>")
        H.append("</div>")
    H.append("</main></body></html>")
    stats = {"render_s": render_s, "diagrams": len(sources), "svgs": len(svgs), "errors": errors + undrawable,
             "responses": len(calls), "invalid": sum(c["v"].level < 3 for c in calls)}
    return "\n".join(H) + "\n", stats


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--runs", nargs="+", required=True, help="cartelle in data/results/generation/")
    a.add_argument("--filter", nargs="*", default=[], help="k=<int> rep=<int> q=<id> cond=<condizione> (ripetibili)")
    a.add_argument("--name", help="nome del report (default: unione dei nomi delle run e dei filtri)")
    a.add_argument("--out", help="cartella di output (default: data/results/generation/<nome>_review/)")
    a.add_argument("--plantuml-jar", default=str(DEFAULT_JAR))
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    filters = parse_filters(args.filter)
    jar = Path(args.plantuml_jar)
    if not jar.exists():
        raise SystemExit(f"plantuml.jar non trovato: {jar} (vedi docs/STATUS.md, 'Rendering dei diagrammi')")
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    calls = []
    for run in args.runs:
        calls += load_run(Path(args.results_dir) / run, filters, gt)
    if not calls:
        raise SystemExit("nessuna risposta con questi filtri")
    name = args.name or "+".join(args.runs) + ("_" + "_".join(f"{k}{'-'.join(sorted(v))}"
                                                               for k, v in sorted(filters.items())) if filters else "")
    out = Path(args.out) if args.out else Path(args.results_dir) / f"{name}_review"
    page, stats = build(calls, jar, name)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    _set_output(out / "index.html")
    print(f"scritto {out / 'index.html'} ({(out / 'index.html').stat().st_size / 1e6:.2f} MB); risposte "
          f"{stats['responses']} (non valide {stats['invalid']}); diagrammi {stats['svgs']}/{stats['diagrams']}; "
          f"rendering {stats['render_s']:.1f} s")
    for e in stats["errors"]:
        print("  non disegnato:", e)
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
