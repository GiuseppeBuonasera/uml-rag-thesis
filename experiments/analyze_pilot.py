"""
Analisi del pilota sulla temperatura (FASE 3, 2026-10-06). Nessuna chiamata a un LLM; corpus/ e la run sono letti in
sola lettura, tranne summary.md della run, che viene (ri)scritto.

Tutto si ricalcola dalle risposte grezze (raw/) con generation/postprocess.py, non da parsed/ o validation.csv.

Sezioni:
- validita': per temperatura, risposte che superano ciascun livello L0-L4, esiti di fallimento, troncamenti;
  diagnostici di formato e di layout a parte;
- variabilita': per esercizio e temperatura, Jaccard medio dei nomi di classe tra coppie di ripetizioni
  (case-insensitive, solo risposte che superano L1) e coppie identiche byte per byte;
- qualita' approssimata: Jaccard dei nomi di classe con il ground truth (solo risposte che superano L1);
- tempi: latenza e token di completamento;
- REGOLA DI DECISIONE della voce 75 di docs/decisions.md, applicata cosi' com'e';
- ESPLORATIVO (non usato per decidere): relazioni rispetto al ground truth, calibrazione dei token, id nello schema
  non valido del template v4.

Uso:
    python experiments/analyze_pilot.py [--run data/results/generation/pilot_temperature_gemma4-12b-qat]
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generation"))
import postprocess as pp  # noqa: E402
from prompt_builder import cl, serialize_diagram  # noqa: E402
from token_estimate import count_tokens  # noqa: E402

DEFAULT_RUN = ROOT / "data" / "results" / "generation" / "pilot_temperature_gemma4-12b-qat"
TEMPERATURES = (0.0, 0.3)
MAX_TRUNCATED = 1  # voce 75: piu' di 1 troncamento su 18 per temperatura -> fermarsi prima di decidere
JACCARD_TOLERANCE = 0.05  # voce 75: J(0) >= J(0.3) - 0.05
DIRECTIONAL = {"ClassInheritance", "ClassRealization", "ClassComposition", "ClassAggregation", "ClassUnidirectional",
               "ClassDependency"}
PART_WHOLE = {"ClassComposition", "ClassAggregation"}
UUID_SHAPE = re.compile(r"^[0-9A-Za-z]{8}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{12}$")
HEX_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
TEMPLATE_FRAGMENT = re.compile(r"-4890-81h2-", re.I)  # dal template v4: "a1b2c3d4-e5f6-4890-81h2-i3j4k5l6m7n8"
# conteggi TESTUALI (valgono anche per le risposte troncate o non decodificabili)
NODE_NAME_RE = re.compile(r'"data"\s*:\s*\{\s*"name"\s*:\s*"([^"]+)"')
EDGE_PAIR_RE = re.compile(r'"source"\s*:\s*"([^"]+)"\s*,\s*"target"\s*:\s*"([^"]+)"')


def norm(name) -> str:
    """Normalizzazione dei nomi come corpus_loader.class_names (minuscole, solo alfanumerici)."""
    return re.sub(r"[^0-9a-z]", "", str(name).lower())


def class_names(diagram: dict) -> set[str]:
    try:
        return {norm(n["data"]["name"]) for n in diagram.get("nodes", []) if isinstance(n, dict)}
    except (KeyError, TypeError, AttributeError):
        return set()


def fmt(x, nd=3) -> str:
    return "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def stats3(xs):
    return (min(xs), statistics.median(xs), max(xs)) if xs else (None, None, None)


# --- caricamento ----------------------------------------------------------------------------------------------------


def load_run(run_dir: Path) -> tuple[dict, list[dict]]:
    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))["config"]
    manifest = [json.loads(x) for x in (run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if x]
    gt = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    calls = []
    for m in manifest:
        raw = json.loads((run_dir / "raw" / f"{m['call_id']}.json").read_text(encoding="utf-8"))
        v = pp.validate_response(raw["text"], raw["finish_reason"])
        calls.append({"m": m, "raw": raw, "v": v, "t": float(m["temperature"]), "q": m["query_id"],
                      "gt": gt[m["query_id"]], "names": class_names(v.diagram) if v.L1_json else None})
    return cfg, calls


# --- regola di decisione (voce 75) ----------------------------------------------------------------------------------


def decision(calls: list[dict], stopped_for_reasoning: bool) -> dict:
    per_t = {}
    for t in TEMPERATURES:
        cs = [c for c in calls if c["t"] == t]
        l1 = [c for c in cs if c["v"].L1_json]
        per_t[t] = {"n": len(cs), "V": sum(c["v"].level >= 3 for c in cs),
                    "truncated": sum(c["v"].failure == "truncated" for c in cs),
                    "J": statistics.mean(cl.jaccard(c["names"], class_names(c["gt"])) for c in l1) if l1 else None,
                    "n_L1": len(l1)}
    reasons = []
    for t, d in per_t.items():
        if d["truncated"] > MAX_TRUNCATED:
            reasons.append(f"temperature {t:g}: {d['truncated']} risposte troncate su {d['n']} (soglia: piu' di "
                           f"{MAX_TRUNCATED})")
        if d["J"] is None:
            reasons.append(f"temperature {t:g}: nessuna risposta supera L1 (J non definito)")
    if stopped_for_reasoning:
        reasons.append("run fermata per ragionamento")
    if reasons:
        return {"per_t": per_t, "outcome": "STOP: nessuna decisione (controllo preliminare)", "reasons": reasons}
    a, b = per_t[0.0], per_t[0.3]
    ok = a["V"] >= b["V"] and a["J"] >= b["J"] - JACCARD_TOLERANCE
    return {"per_t": per_t, "reasons": [],
            "outcome": "opzione (a): temperature 0, 1 ripetizione" if ok else "opzione (b): temperature 0.3, 3 ripetizioni"}


# --- esplorativo: relazioni -----------------------------------------------------------------------------------------


def norm_mult(m) -> str:
    """Esplorativo: minuscole, senza spazi; 'n' -> '*' (anche '1..n' -> '1..*'); '0..*' equivalente a '*'."""
    s = re.sub(r"\s+", "", str(m or "")).lower()
    s = "*" if s == "n" else re.sub(r"\.\.n$", "..*", s)
    return "*" if s == "0..*" else s


def edges(diagram: dict) -> list[dict]:
    """Relazioni con i nomi normalizzati delle classi agli estremi (scarta quelle con estremi non risolvibili)."""
    try:
        names = {n["id"]: norm(n["data"]["name"]) for n in diagram.get("nodes", [])}
    except (KeyError, TypeError, AttributeError):
        return []
    out = []
    for e in diagram.get("edges", []) or []:
        try:
            s, t, d = names[e["source"]], names[e["target"]], e.get("data") or {}
        except (KeyError, TypeError):
            continue
        out.append({"src": s, "tgt": t, "type": e.get("type"), "pair": frozenset((s, t)),
                    "mult": {s: norm_mult(d.get("sourceMultiplicity")), t: norm_mult(d.get("targetMultiplicity"))}
                    if s != t else {"_self": (norm_mult(d.get("sourceMultiplicity")),
                                              norm_mult(d.get("targetMultiplicity")))}})
    return out


def compare_relations(resp: dict, gt: dict) -> Counter:
    """Accoppiamento 1:1 per coppia di classi (non ordinata): prima le relazioni dello stesso tipo, poi le altre."""
    r_edges, g_edges = edges(resp), edges(gt)
    c = Counter(resp_edges=len(r_edges), gt_edges=len(g_edges))
    for pair in {e["pair"] for e in r_edges} & {e["pair"] for e in g_edges}:
        rs = [e for e in r_edges if e["pair"] == pair]
        gs = [e for e in g_edges if e["pair"] == pair]
        matches = []
        for same_type in (True, False):
            for r in list(rs):
                g = next((g for g in gs if (g["type"] == r["type"]) == same_type), None)
                if g is not None:
                    matches.append((r, g))
                    rs.remove(r)
                    gs.remove(g)
        for r, g in matches:
            c["same_pair"] += 1
            if r["type"] == g["type"]:
                c["same_type"] += 1
                if r["type"] in DIRECTIONAL:
                    c["directional_same_type"] += 1
                    c["same_direction"] += (r["src"], r["tgt"]) == (g["src"], g["tgt"])
                if r["type"] in PART_WHOLE:
                    c["part_whole_same_type"] += 1
                    c["part_whole_same_direction"] += (r["src"], r["tgt"]) == (g["src"], g["tgt"])
            else:
                c[f"type {g['type']} -> {r['type']}"] += 1
            if g["type"] not in ("ClassInheritance", "ClassRealization"):
                c["mult_compared"] += 1
                c["same_mult"] += r["mult"] == g["mult"]
    return c


# --- esplorativo: id del template -----------------------------------------------------------------------------------


def id_scheme(c: dict) -> str:
    text = c["raw"]["text"]
    if TEMPLATE_FRAGMENT.search(text):
        return "frammento del template v4 (-4890-81h2-)"
    if not c["v"].L1_json:
        return "non classificabile (JSON non decodificabile)"
    ids = []
    try:
        for n in c["v"].diagram.get("nodes", []):
            ids.append(str(n.get("id")))
            for m in (n.get("data") or {}).get("attributes", []) + (n.get("data") or {}).get("methods", []):
                ids.append(str(m.get("id")))
        ids += [str(e.get("id")) for e in c["v"].diagram.get("edges", [])]
    except (AttributeError, TypeError):
        return "non classificabile (struttura)"
    if ids and all(HEX_UUID.match(i) for i in ids):
        return "UUID validi (esadecimali)"
    if any(UUID_SHAPE.match(i) and not HEX_UUID.match(i) for i in ids):
        return "forma UUID con caratteri non esadecimali"
    return "altro formato"


# --- report ---------------------------------------------------------------------------------------------------------


def loop_rows(calls: list[dict]) -> list[dict]:
    """ESPLORATIVO: per risposta, prompt reale, dimensione degli esempi recuperati e del GT, relazioni prodotte
    (conteggio testuale), coppie (sorgente, destinazione) distinte e classi prese dagli esempi che non sono nel GT."""
    by_id = {c["id"]: c["diagram_apollon_json"] for c in cl.load_candidates()}
    rows = []
    for c in calls:
        m, text = c["m"], c["raw"]["text"]
        ex = [by_id[e] for e in m["example_ids"]]
        pairs = EDGE_PAIR_RE.findall(text)
        names = {norm(n) for n in NODE_NAME_RE.findall(text)}
        ex_names = set().union(*(class_names(d) for d in ex)) if ex else set()
        gt_names = class_names(c["gt"])
        rows.append({"call_id": m["call_id"], "q": c["q"], "t": c["t"], "r": m["repetition"],
                     "truncated": c["v"].truncated, "prompt_real": m["prompt_tokens_server"],
                     "ex_tokens": sum(count_tokens(serialize_diagram(d, "compact", True)) for d in ex),
                     "ex_edges": sum(len(d["edges"]) for d in ex), "ex_ids": m["example_ids"],
                     "gt_tokens": count_tokens(serialize_diagram(c["gt"], "compact", True)),
                     "gt_edges": len(c["gt"]["edges"]), "completion": m["completion_tokens_server"],
                     "edges": len(pairs), "distinct_pairs": len(set(pairs)),
                     "copied": sorted((names & ex_names) - gt_names)})
    return rows


def loop_section(calls: list[dict], queries: list[str]) -> list[str]:
    rows = loop_rows(calls)
    L = ["", "### Risposte troncate (cicli di relazioni): legate al prompt o agli esempi recuperati?", "",
         "Conteggi testuali (valgono anche per le risposte non decodificabili): relazioni = coppie "
         "`\"source\"`/`\"target\"` scritte; coppie distinte = coppie (sorgente, destinazione) diverse; classi dagli "
         "esempi = nomi di classe della risposta presenti negli esempi recuperati e assenti dal GT. Token degli esempi e "
         "del GT: stima cl100k_base del JSON compatto; prompt: token reali dal server.", "",
         "| chiamata | t | troncata | prompt reale | esempi: token / relazioni | GT: token / relazioni | completamento | "
         "relazioni scritte | coppie distinte | classi dagli esempi |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["q"], r["t"], r["r"])):
        L.append(f"| {r['call_id']} | {r['t']:g} | {'SI' if r['truncated'] else 'no'} | {r['prompt_real']} | "
                 f"{r['ex_tokens']} / {r['ex_edges']} | {r['gt_tokens']} / {r['gt_edges']} | {r['completion']} | "
                 f"{r['edges']} | {r['distinct_pairs']} | {', '.join(r['copied']) or '—'} |")
    tr = [r for r in rows if r["truncated"]]
    ok = [r for r in rows if not r["truncated"]]

    def med(rs, k):
        return statistics.median(r[k] for r in rs) if rs else None

    L += ["", "Mediane, troncate contro non troncate:", "",
          "| gruppo | n | prompt reale | token degli esempi | relazioni degli esempi | token del GT | relazioni del GT |"
          " relazioni scritte | coppie distinte / relazioni scritte |", "|---|---|---|---|---|---|---|---|---|"]
    for label, rs in (("troncate", tr), ("non troncate", ok)):
        ratio = statistics.median(r["distinct_pairs"] / r["edges"] for r in rs if r["edges"]) if rs else None
        L.append(f"| {label} | {len(rs)} | {fmt(med(rs, 'prompt_real'), 0)} | {fmt(med(rs, 'ex_tokens'), 0)} | "
                 f"{fmt(med(rs, 'ex_edges'), 0)} | {fmt(med(rs, 'gt_tokens'), 0)} | {fmt(med(rs, 'gt_edges'), 0)} | "
                 f"{fmt(med(rs, 'edges'), 0)} | {fmt(ratio, 2)} |")
    L += ["", "Per esercizio (prompt ed esempi sono gli stessi per le 6 risposte dell'esercizio: cambiano solo "
          "temperatura e ripetizione), in ordine di prompt reale:", "",
          "| esercizio | prompt reale | esempi recuperati | esempi: token / relazioni | GT: token / relazioni | "
          "troncate t = 0 | troncate t = 0.3 |", "|---|---|---|---|---|---|---|"]
    per_q = {}
    for r in rows:
        per_q.setdefault(r["q"], []).append(r)
    for q in sorted(per_q, key=lambda q: -per_q[q][0]["prompt_real"]):
        rs, r0 = per_q[q], per_q[q][0]
        L.append(f"| {q} | {r0['prompt_real']} | {', '.join(r0['ex_ids'])} | {r0['ex_tokens']} / {r0['ex_edges']} | "
                 f"{r0['gt_tokens']} / {r0['gt_edges']} | {sum(r['truncated'] for r in rs if r['t'] == 0.0)}/3 | "
                 f"{sum(r['truncated'] for r in rs if r['t'] == 0.3)}/3 |")
    ordered = sorted(per_q, key=lambda q: -per_q[q][0]["prompt_real"])
    with_tr = [q for q in ordered if any(r["truncated"] for r in per_q[q])]
    without = [q for q in ordered if not any(r["truncated"] for r in per_q[q])]
    min_tr = min(per_q[q][0]["prompt_real"] for q in with_tr) if with_tr else None
    max_no = max(per_q[q][0]["prompt_real"] for q in without) if without else None
    copied_tr = sum(bool(r["copied"]) for r in tr)
    L += ["", "**Sintesi (esplorativa)**:",
          f"- le troncature compaiono solo negli esercizi con il prompt più lungo: {len(with_tr)} esercizi con almeno "
          f"una troncata (prompt reale >= {min_tr}), {len(without)} senza (prompt <= {max_no}). Gli stessi esercizi "
          "hanno anche gli esempi recuperati più grandi (token e relazioni): il prompt è fatto quasi tutto dagli "
          "esempi, quindi **lunghezza del prompt e dimensione degli esempi non si possono separare** con questi dati;",
          "- la dimensione del GT non spiega da sola i cicli: Louvre ha il GT tra i più piccoli e un prompt lungo, e "
          "tronca; StudentAppointment e ApartmentBuilding hanno GT e prompt piccoli e non troncano mai;",
          f"- nelle troncate le relazioni ripetono le stesse coppie (coppie distinte / relazioni scritte in mediana "
          f"{fmt(statistics.median(r['distinct_pairs'] / r['edges'] for r in tr if r['edges']), 2) if tr else '—'}): è "
          "un ciclo sulle relazioni, non un diagramma più grande;",
          f"- classi copiate dagli esempi (presenti negli esempi, assenti dal GT): in {copied_tr} risposte troncate su "
          f"{len(tr)} e in {sum(bool(r['copied']) for r in ok)} non troncate su {len(ok)};",
          "- a parità di prompt (stesso esercizio) la troncatura dipende anche dal campionamento (temperatura, "
          "ripetizione): non è determinata solo dal prompt;",
          f"- limiti: {len(per_q)} configurazioni di prompt distinte, nessun test statistico; servirebbe un "
          "esperimento che vari la lunghezza del prompt a parità di esempi (o il contrario) per separare i due fattori."]
    return L


def report(run_dir: Path) -> str:
    cfg, calls = load_run(run_dir)
    stopped = any(c["m"].get("reasoning_field") or c["m"].get("reasoning_markers_in_content") for c in calls)
    dec = decision(calls, stopped)
    queries = cfg["query_ids"]
    L = [f"# Pilota sulla temperatura — `{cfg['run_id']}`", "",
         "**Esperimento PRELIMINARE** sul corpus (split `corpus`, selezione leave-one-out), mai sul test set: da "
         "dichiarare come tale in tesi. Regola di decisione registrata PRIMA della run (docs/decisions.md, voce 75) e "
         "applicata cosi' com'e'. Generato da `experiments/analyze_pilot.py` dalle risposte grezze (`raw/`).", "",
         f"Modello `{cfg['model_metadata']['model_id']}` ({cfg['model_metadata']['quantization']}), contesto "
         f"{cfg['model_metadata']['context_length']}, enable_thinking {cfg['model_metadata']['enable_thinking']}; "
         f"bm25 k={cfg['k'][0]}; top_p {cfg['generation']['top_p']}, top_k {cfg['generation']['top_k']}, max_tokens "
         f"{cfg['generation']['max_tokens']}; {len(calls)} risposte ({len(queries)} esercizi × "
         f"{len(TEMPERATURES)} temperature × {cfg['repetitions']} ripetizioni). Ragionamento nelle risposte: "
         f"{'SI' if stopped else 'no'}.", ""]

    # validita'
    L += ["## Validita'", "", "Risposte (su 18 per temperatura) che superano ciascun livello (cumulativo).", "",
          "| temperatura | L0 estratto | L1 JSON | L2 schema | L3 integrita' | L4 stile | troncate (length) |",
          "|---|---|---|---|---|---|---|"]
    for t in TEMPERATURES:
        cs = [c for c in calls if c["t"] == t]
        lv = [sum(c["v"].level >= i for c in cs) for i in range(5)]
        L.append(f"| {t:g} | " + " | ".join(str(x) for x in lv) + f" | {sum(c['v'].truncated for c in cs)} |")
    L += ["", "Esiti di fallimento (`failure`) per temperatura:", ""]
    for t in TEMPERATURES:
        cnt = Counter(c["v"].failure or "nessuno (L4)" for c in calls if c["t"] == t)
        L.append(f"- {t:g}: " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items())))
    L += ["", "Per esercizio (livello raggiunto da ciascuna ripetizione, r0 / r1 / r2; −1 = nessun JSON estratto):", "",
          "| esercizio | t = 0 | t = 0.3 |", "|---|---|---|"]
    for q in queries:
        cells = []
        for t in TEMPERATURES:
            cs = sorted((c for c in calls if c["q"] == q and c["t"] == t), key=lambda c: c["m"]["repetition"])
            cells.append(" / ".join(f"{c['v'].level}{' (length)' if c['v'].truncated else ''}" for c in cs))
        L.append(f"| {q} | {cells[0]} | {cells[1]} |")
    trunc = [c for c in calls if c["v"].truncated]
    if trunc:
        L += ["", "Risposte troncate (finish_reason = length): nodi e relazioni scritti prima del tetto (conteggio "
              "testuale delle chiavi `\"type\": \"class\"` e `\"sourceHandle\"`), contro il ground truth:", "",
              "| chiamata | caratteri | nodi | relazioni | GT nodi | GT relazioni |", "|---|---|---|---|---|---|"]
        for c in trunc:
            text = c["raw"]["text"]
            L.append(f"| {c['m']['call_id']} | {len(text)} | {len(re.findall(r'\"type\"\s*:\s*\"class\"', text))} | "
                     f"{len(re.findall(r'\"sourceHandle\"', text))} | {len(c['gt']['nodes'])} | {len(c['gt']['edges'])} |")
    L += ["", "Diagnostici (non metriche; non si combinano con L0-L4): risposte con almeno un diagnostico, tra quelle "
          "che superano L1.", "", "| temperatura | formato della risposta | layout |", "|---|---|---|"]
    for t in TEMPERATURES:
        l1 = [c for c in calls if c["t"] == t and c["v"].L1_json]
        f = Counter(k for c in l1 for k in c["v"].format_issues)
        la = Counter(k for c in l1 for k in c["v"].layout_issues)
        L.append(f"| {t:g} | " + (", ".join(f"{k} {v}" for k, v in sorted(f.items())) or "nessuno") + " | " +
                 (", ".join(f"{k} {v}" for k, v in sorted(la.items())) or "nessuno") + " |")

    # variabilita'
    L += ["", "## Variabilita' tra ripetizioni", "",
          "Jaccard medio dei nomi di classe tra le coppie di ripetizioni (solo coppie in cui entrambe superano L1; "
          "tra parentesi le coppie usate su 3) e coppie identiche byte per byte (testo grezzo, su 3).", "",
          "| esercizio | t = 0: Jaccard tra ripetizioni | t = 0: identiche | t = 0.3: Jaccard tra ripetizioni | "
          "t = 0.3: identiche |", "|---|---|---|---|---|"]
    identical_pairs = {}
    for q in queries:
        cells = []
        for t in TEMPERATURES:
            cs = sorted((c for c in calls if c["q"] == q and c["t"] == t), key=lambda c: c["m"]["repetition"])
            pairs = list(itertools.combinations(cs, 2))
            js = [cl.jaccard(a["names"], b["names"]) for a, b in pairs if a["names"] is not None and b["names"] is not None]
            same_pairs = [f"r{a['m']['repetition']}=r{b['m']['repetition']}" for a, b in pairs
                          if a["raw"]["text"] == b["raw"]["text"]]
            identical_pairs[(q, t)] = same_pairs
            cells += [f"{fmt(statistics.mean(js)) if js else '—'} ({len(js)})",
                      f"{len(same_pairs)}/3" + (f" ({', '.join(same_pairs)})" if same_pairs else "")]
        L.append(f"| {q} | " + " | ".join(cells) + " |")

    r12 = sum(identical_pairs[(q, 0.0)] == ["r1=r2"] for q in queries)
    L += ["", f"A temperature 0 la coppia identica e' r1 = r2 in {r12} esercizi su {len(queries)}; r0 differisce sempre. "
          "Le tre ripetizioni sono consecutive (seed 42, 43, 44, che a temperature 0 non dovrebbero contare). Ipotesi "
          "NON verificata: r0 e' la prima valutazione del prompt, r1 e r2 riusano la cache del prompt di LM Studio "
          "(percorso numerico diverso)."]

    # qualita'
    L += ["", "## Qualita' approssimata: Jaccard dei nomi di classe con il ground truth", "",
          "Solo risposte che superano L1; media per esercizio (tra parentesi le risposte usate su 3).", "",
          "| esercizio | t = 0 | t = 0.3 |", "|---|---|---|"]
    for q in queries:
        cells = []
        for t in TEMPERATURES:
            js = [cl.jaccard(c["names"], class_names(c["gt"])) for c in calls
                  if c["q"] == q and c["t"] == t and c["names"] is not None]
            cells.append(f"{fmt(statistics.mean(js)) if js else '—'} ({len(js)})")
        L.append(f"| {q} | {cells[0]} | {cells[1]} |")

    # tempi
    L += ["", "## Tempi e token di output", "", "| temperatura | latenza s (min / mediana / max) | token di completamento "
          "(min / mediana / max) | totale token di completamento |", "|---|---|---|---|"]
    for t in TEMPERATURES:
        cs = [c for c in calls if c["t"] == t]
        lat = stats3([c["m"]["latency_s"] for c in cs])
        tok = stats3([c["m"]["completion_tokens_server"] for c in cs if c["m"]["completion_tokens_server"]])
        L.append(f"| {t:g} | {lat[0]:.1f} / {lat[1]:.1f} / {lat[2]:.1f} | {tok[0]} / {tok[1]:.0f} / {tok[2]} | "
                 f"{sum(c['m']['completion_tokens_server'] or 0 for c in cs)} |")
    total_s = sum(c["m"]["latency_s"] for c in calls)
    L.append(f"\nDurata complessiva delle generazioni: {total_s / 60:.1f} minuti.")

    # regola
    L += ["", "## Regola di decisione (voce 75), applicata cosi' com'e'", "",
          "| temperatura | V = risposte che superano L0-L3 | J = Jaccard medio con il GT (risposte L1) | risposte L1 | "
          "troncate |", "|---|---|---|---|---|"]
    for t, d in dec["per_t"].items():
        L.append(f"| {t:g} | {d['V']}/{d['n']} | {fmt(d['J'])} | {d['n_L1']} | {d['truncated']} |")
    L += ["", f"**Esito: {dec['outcome']}**"]
    L += [f"- {r}" for r in dec["reasons"]]
    if not dec["reasons"]:
        a, b = dec["per_t"][0.0], dec["per_t"][0.3]
        L.append(f"- V(0) = {a['V']} {'>=' if a['V'] >= b['V'] else '<'} V(0.3) = {b['V']}; J(0) = {fmt(a['J'])} "
                 f"{'>=' if a['J'] >= b['J'] - JACCARD_TOLERANCE else '<'} J(0.3) − {JACCARD_TOLERANCE} = "
                 f"{fmt(b['J'] - JACCARD_TOLERANCE)}")

    # esplorativo
    L += ["", "## ESPLORATIVO — non usato per decidere", "",
          "### Relazioni rispetto al ground truth (risposte che superano L1)", "",
          "Accoppiamento 1:1 per coppia di classi non ordinata (nomi normalizzati, case-insensitive), prima le "
          "relazioni dello stesso tipo. Verso: solo per relazioni dello stesso tipo orientato (in Apollon per "
          "composizione e aggregazione la sorgente e' la parte). Molteplicita': confrontate per estremo di classe "
          "(esclusi generalizzazione e realizzazione), normalizzate: senza spazi, 'n' -> '*', '0..*' = '*'.", "",
          "| temperatura | relazioni risposta | relazioni GT | stessa coppia | stesso tipo | stesso verso (tipi "
          "orientati) | comp./aggr.: stesso verso | stesse molteplicita' |", "|---|---|---|---|---|---|---|---|"]
    swaps_all = {}
    per_q_rel = {}
    for t in TEMPERATURES:
        tot = Counter()
        for c in calls:
            if c["t"] == t and c["v"].L1_json:
                rc = compare_relations(c["v"].diagram, c["gt"])
                tot += rc
                per_q_rel.setdefault((c["q"], t), Counter()).update(rc)
        swaps_all[t] = {k: v for k, v in tot.items() if k.startswith("type ")}
        L.append(f"| {t:g} | {tot['resp_edges']} | {tot['gt_edges']} | {tot['same_pair']} | {tot['same_type']} | "
                 f"{tot['same_direction']}/{tot['directional_same_type']} | "
                 f"{tot['part_whole_same_direction']}/{tot['part_whole_same_type']} | "
                 f"{tot['same_mult']}/{tot['mult_compared']} |")
    for t in TEMPERATURES:
        if swaps_all[t]:
            L.append(f"\nTipo diverso con la stessa coppia, t = {t:g} (GT -> risposta): " +
                     ", ".join(f"{k[5:]} {v}" for k, v in sorted(swaps_all[t].items(), key=lambda x: -x[1])))
    L += ["", "Per esercizio (somma sulle risposte L1): stessa coppia / relazioni GT × risposte L1; stesso tipo; "
          "stesso verso; stesse molteplicita'.", "",
          "| esercizio | t | stessa coppia | relazioni GT (× risposte) | stesso tipo | stesso verso | stesse molt. |",
          "|---|---|---|---|---|---|---|"]
    for q in queries:
        for t in TEMPERATURES:
            rc = per_q_rel.get((q, t))
            if rc is None:
                L.append(f"| {q} | {t:g} | — | — | — | — | — |")
                continue
            L.append(f"| {q} | {t:g} | {rc['same_pair']} | {rc['gt_edges']} | {rc['same_type']} | "
                     f"{rc['same_direction']}/{rc['directional_same_type']} | {rc['same_mult']}/{rc['mult_compared']} |")

    ratios = [c["m"]["prompt_tokens_server"] / c["m"]["prompt_tokens_est"] for c in calls
              if c["m"].get("prompt_tokens_server") and c["m"].get("prompt_tokens_est")]
    lo, med, hi = stats3(ratios)
    L += ["", "### Calibrazione dei token di prompt", "",
          f"Rapporto token reali (server, tokenizer di Gemma 4) / stima cl100k_base su {len(ratios)} chiamate: min "
          f"{lo:.3f}, mediana {med:.3f}, max {hi:.3f}. Le ripetizioni dello stesso prompt hanno lo stesso rapporto (6 "
          "prompt distinti). Uso: ricalcolo delle tabelle della domanda 8 per il Passo 3b "
          "(`experiments/context_budget.py`)."]

    L += loop_section(calls, queries)

    schemes = Counter(id_scheme(c) for c in calls)
    L += ["", "### Id nello schema non valido del template v4 (solo descrittivo)", "",
          "Il template v4 usa come esempio l'id \"a1b2c3d4-e5f6-4890-81h2-i3j4k5l6m7n8\" (non un UUID valido); L3 non "
          "richiede il formato UUID (voce 64). Classificazione per risposta (36):", ""]
    L += [f"- {k}: {v}" for k, v in sorted(schemes.items(), key=lambda x: -x[1])]
    for t in TEMPERATURES:
        n = sum(id_scheme(c).startswith("frammento") for c in calls if c["t"] == t)
        L.append(f"- con il frammento del template, t = {t:g}: {n}/18")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(DEFAULT_RUN))
    a = ap.parse_args(argv)
    run_dir = Path(a.run)
    text = report(run_dir)
    (run_dir / "summary.md").write_text(text, encoding="utf-8")
    _set_output(run_dir / "summary.md")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
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
