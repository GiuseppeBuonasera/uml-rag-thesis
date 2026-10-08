"""
Visualizzatore del secondo pilota (2026-10-08): una pagina HTML unica e autonoma (nessuna risorsa esterna, nessuno
script) con, per ciascuno dei 6 esercizi, la traccia, il ground truth in PlantUML canonico e, per ogni configurazione
(P-G, P-Q, J-G, J-Q e il riferimento J0-Q) e ripetizione, la risposta grezza del modello, il livello raggiunto, le
righe scartate e gli errori.

Solo lettura: nessuna chiamata a un LLM, nessuna generazione. Le run si caricano con le stesse funzioni di
experiments/analyze_pilot2.py (stessa validazione del runner, stessa esclusione delle run di un altro modello), quindi
livelli ed errori coincidono con il summary.md. Scrive solo
data/results/generation/pilot2_formats_analysis/viewer.html (NON versionato: .gitignore versiona solo summary.md).

Uso:
    python experiments/render_pilot2.py [--results-dir data/results/generation]
"""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "generation"))
import analyze_pilot2 as a2  # noqa: E402
from plantuml_format import apollon_to_plantuml  # noqa: E402
from prompt_builder import cl  # noqa: E402

CONFIGS = (*a2.CONFIGURATIONS, *a2.REFERENCE_CONFIGURATIONS)
LEVEL_LABEL = {-1: "niente estratto", 0: "L0", 1: "L1 / P1b", 2: "L2", 3: "L3", 4: "L4"}

CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1b;--muted:#6b6b66;--card:#ffffff;--line:#e2e1dc;--code:#f3f2ee;
--ok:#1f7a4d;--ok-bg:#e3f3ea;--warn:#8a5a00;--warn-bg:#fbefd5;--bad:#a1271d;--bad-bg:#fbe4e1;--acc:#2f5fa7}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--fg:#e9e8e3;--muted:#9c9b95;
--card:#1f1f1d;--line:#34332f;--code:#262624;--ok:#7fd1a4;--ok-bg:#1c3328;--warn:#e8c06a;--warn-bg:#3a2f15;
--bad:#f19a90;--bad-bg:#3d1f1c;--acc:#8fb3ef}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 64px}h1{font-size:1.5rem;margin:0 0 4px}
h2{font-size:1.25rem;margin:40px 0 8px;padding-top:8px;border-top:1px solid var(--line)}h3{font-size:1.05rem;margin:20px 0 8px}
p.note,.muted{color:var(--muted)}a{color:var(--acc)}nav a{margin-right:12px;white-space:nowrap}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:.92rem}th,td{border:1px solid var(--line);
padding:4px 8px;text-align:left;vertical-align:top}th{background:var(--code)}
.wrap{overflow-x:auto}pre{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:10px;
overflow:auto;max-height:520px;font:12.5px/1.45 ui-monospace,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
.desc{white-space:pre-wrap;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:10px 12px}
.badge{display:inline-block;border-radius:10px;padding:0 8px;font-size:.82rem;font-weight:600}
.ok{color:var(--ok);background:var(--ok-bg)}.warn{color:var(--warn);background:var(--warn-bg)}
.bad{color:var(--bad);background:var(--bad-bg)}
details{background:var(--card);border:1px solid var(--line);border-radius:6px;margin:6px 0;padding:6px 10px}
summary{cursor:pointer;font-weight:600}summary .muted{font-weight:400}ul{margin:6px 0;padding-left:20px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media (max-width:820px){.grid{grid-template-columns:1fr}}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def badge(level: int, truncated: bool) -> str:
    cls = "ok" if level >= 3 else "warn" if level >= 1 else "bad"
    extra = " · troncata" if truncated else ""
    return f'<span class="badge {cls}">{esc(LEVEL_LABEL.get(level, level))}{extra}</span>'


def call_block(name: str, c: dict) -> str:
    v, m = c["v"], c["m"]
    head = (f"{esc(name)} · r{m['repetition']} {badge(v.level, v.truncated)} <span class=\"muted\">"
            f"failure: {esc(v.failure or 'nessuno')} · finish_reason: {esc(m.get('finish_reason'))} · "
            f"{esc(m.get('completion_tokens_server'))} token · {esc(m.get('latency_s'))} s</span>")
    parts = []
    disc = getattr(v, "discarded_lines", None)
    if disc:
        parts.append(f"<h4>Righe scartate ({len(disc)})</h4><ul>" + "".join(f"<li><code>{esc(d)}</code></li>"
                                                                           for d in disc) + "</ul>")
    errs = [(lv, x) for lv, msgs in v.errors.items() for x in (msgs if isinstance(msgs, list) else [msgs])]
    if errs:
        parts.append(f"<h4>Errori ({len(errs)})</h4><ul>" + "".join(f"<li><b>{esc(lv)}</b>: {esc(x)}</li>"
                                                                    for lv, x in errs) + "</ul>")
    if v.style_raw and v.level >= 4:
        parts.append("<h4>Messaggi di stile prima delle riscritture ammesse (L4 superato)</h4><ul>" +
                     "".join(f"<li>{esc(x)}</li>" for x in v.style_raw) + "</ul>")
    diag = sorted(v.format_issues) + sorted(v.layout_issues)
    if diag:
        parts.append(f"<p class=\"muted\">Diagnostici (non metriche): {esc(', '.join(diag))}</p>")
    parts.append(f"<h4>Risposta grezza ({len(c['raw']['text'])} caratteri)</h4><pre>{esc(c['raw']['text'])}</pre>")
    return f"<details><summary>{head}</summary>{''.join(parts)}</details>"


def build_html(results: Path) -> str:
    cands = {c["id"]: c for c in cl.load_candidates()}
    gt = {k: c["diagram_apollon_json"] for k, c in cands.items()}
    models = a2.expected_model_ids()
    infos = {n: a2.load_configuration(results, n, gt, models[n]) for n in CONFIGS}
    cfg = next((i["cfg"] for i in infos.values() if i["cfg"]), None)
    import yaml
    queries = (cfg or yaml.safe_load(a2.PILOT2_CONFIG.read_text(encoding="utf-8")))["query_ids"]

    H = ["<!doctype html><html lang=\"it\"><head><meta charset=\"utf-8\">",
         "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
         "<title>Secondo pilota: risposte</title>", f"<style>{CSS}</style></head><body><main>",
         "<h1>Secondo pilota — risposte per esercizio</h1>",
         "<p class=\"note\">Esperimento PRELIMINARE sul corpus (leave-one-out), mai il test set. Pagina generata da "
         "<code>experiments/render_pilot2.py</code> in sola lettura dalle risposte grezze (<code>raw/</code>), con la "
         "stessa validazione del runner e di <code>analyze_pilot2.py</code>. Valida per la regola (S) = livello "
         "&ge; 3. J0-Q è un riferimento descrittivo, fuori dalla regola (voce 83). Strada 1: livello 1 = P1b "
         "(parsing tollerante e conversione riusciti, anche con righe scartate).</p>"]
    # riepilogo
    H += ["<h2 id=\"riepilogo\">Riepilogo</h2><div class=\"wrap\"><table><tr><th>configurazione</th><th>modello</th>"
          "<th>formato</th><th>S</th><th>stato</th></tr>"]
    for n, i in infos.items():
        m = i["metrics"]
        fmt = "PlantUML" if n.startswith("P") else ("JSON libero" if n == "J0-Q" else "JSON vincolato")
        s = f"{m['S']}/{m['n']}" if m else "—"
        H.append(f"<tr><td><b>{esc(n)}</b></td><td>{esc(a2.MODEL_NAME[n[-1]])}</td><td>{fmt}</td>"
                 f"<td>{esc(s)}</td><td>{esc(i['excluded'] or 'completa')}</td></tr>")
    H.append("</table></div>")
    H.append("<nav>" + "".join(f'<a href="#{esc(q)}">{esc(q)}</a>' for q in queries) + "</nav>")

    for q in queries:
        c0 = cands[q]
        H += [f"<h2 id=\"{esc(q)}\">{esc(q)}</h2>",
              f"<p class=\"muted\">dominio: {esc(c0.get('domain'))} · <a href=\"#riepilogo\">torna al riepilogo</a></p>",
              "<h3>Livelli per configurazione e ripetizione</h3><div class=\"wrap\"><table><tr><th>configurazione</th>"
              "<th>r0</th><th>r1</th></tr>"]
        for n, i in infos.items():
            cs = sorted((c for c in i["calls"] if c["q"] == q), key=lambda c: c["m"]["repetition"])
            cells = [badge(c["v"].level, c["v"].truncated) for c in cs] or ["—", "—"]
            H.append(f"<tr><td>{esc(n)}</td>" + "".join(f"<td>{x}</td>" for x in cells) + "</tr>")
        H += ["</table></div>", "<div class=\"grid\"><div><h3>Traccia</h3>",
              f"<div class=\"desc\">{esc(c0.get('description') or '')}</div></div>",
              "<div><h3>Ground truth (PlantUML canonico)</h3>",
              f"<pre>{esc(apollon_to_plantuml(gt[q]))}</pre></div></div>", "<h3>Risposte</h3>"]
        for n, i in infos.items():
            cs = sorted((c for c in i["calls"] if c["q"] == q), key=lambda c: c["m"]["repetition"])
            if not cs:
                H.append(f"<p class=\"muted\">{esc(n)}: nessuna risposta ({esc(i['excluded'] or '—')})</p>")
            H += [call_block(n, c) for c in cs]
    H.append("</main></body></html>")
    return "\n".join(H) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default=str(a2.RESULTS))
    a = ap.parse_args(argv)
    results = Path(a.results_dir)
    out = results / a2.OUT_NAME
    out.mkdir(parents=True, exist_ok=True)
    (out / "viewer.html").write_text(build_html(results), encoding="utf-8")
    print(f"scritto {out / 'viewer.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
