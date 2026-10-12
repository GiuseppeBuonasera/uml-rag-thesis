"""
Metriche congelate per il Passo 3b (2026-10-11, voce 127): funzioni SPOSTATE senza modifiche da
experiments/analyze_pilot.py, analyze_dev.py, analyze_instructions.py e analyze_v5.py, che ora le riesportano con gli
stessi nomi (gli script storici restano invariati nel comportamento: test in evaluation/test_metrics.py, che ricalcola
tutte le analisi di sviluppo versionate e le confronta cifra per cifra con i loro summary.md).

Tutto per CONTENUTO (nomi di classe normalizzati), mai per id. Una "chiamata" e' un dict con almeno:
  "v"      risultato della validazione (level, diagram, truncated, P1_clean / C2_clean, discarded_lines, compact_issues),
  "gt"     diagramma Apollon v4 di riferimento, "m" riga del manifest (latency_s), "format" plantuml | compact.

Sintattiche (livello 1):
- V  = risposte valide fino a L3 (`is_valid`); Vc = valide fino a L3 e senza scarti, P1 per PlantUML, C2 per il
       compatto (`is_clean`).
Strutturali rispetto al GT (voci 92, 98, 111):
- J  = media del Jaccard dei nomi di classe con il GT su TUTTE le risposte, 0 per le non valide;
- R  = relazioni del GT ritrovate con stessa coppia di classi e stesso tipo / relazioni del GT, sommate su TUTTE le
       risposte (accoppiamento 1:1 per coppia non ordinata, prima lo stesso tipo: `compare_relations`, `match`);
- R_fam = come R, ma associazione e unidirezionale contano come lo stesso tipo;
- M primaria (M1) = estremi del GT con molteplicita' esplicita per cui la risposta ha la stessa molteplicita'
       (normalizzata da `norm_mult`), su tutti gli estremi espliciti del GT di tutte le risposte; M secondaria (M2) =
       lo stesso su tutti gli estremi (vuoto uguale solo a vuoto); esclusi generalizzazione e realizzazione;
- verso: relazioni orientate dello stesso tipo con lo stesso verso (`compare_relations`: same_direction su
       directional_same_type); generalizzazioni invertite (`confusion`: inv / inv_tot);
- classi in piu', generalizzazioni in piu' (`confusion`), composizioni in piu' (`extra_compositions`).
La valutazione semantica (livello 2) andra' in questo stesso pacchetto, in un compito separato.
"""

from __future__ import annotations

import re
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "retrieval"))
from corpus_loader import jaccard  # noqa: E402,F401  (riesportata: Jaccard di due insiemi, 0 se entrambi vuoti)

DIRECTIONAL = {"ClassInheritance", "ClassRealization", "ClassComposition", "ClassAggregation", "ClassUnidirectional",
               "ClassDependency"}
PART_WHOLE = {"ClassComposition", "ClassAggregation"}
NO_MULT = ("ClassInheritance", "ClassRealization")
ORIENTED = ("ClassInheritance", "ClassRealization", "ClassComposition", "ClassAggregation", "ClassUnidirectional",
            "ClassDependency")
SHORT = {"ClassBidirectional": "associazione", "ClassUnidirectional": "unidirezionale", "ClassInheritance":
         "generalizzazione", "ClassRealization": "realizzazione", "ClassAggregation": "aggregazione",
         "ClassComposition": "composizione", "ClassDependency": "dipendenza"}
FAMILY_SWAPS = ("type ClassBidirectional -> ClassUnidirectional", "type ClassUnidirectional -> ClassBidirectional")


# --- nomi e relazioni (da analyze_pilot.py) -------------------------------------------------------------------------


def norm(name) -> str:
    """Normalizzazione dei nomi come corpus_loader.class_names (minuscole, solo alfanumerici)."""
    return re.sub(r"[^0-9a-z]", "", str(name).lower())


def class_names(diagram: dict) -> set[str]:
    try:
        return {norm(n["data"]["name"]) for n in diagram.get("nodes", []) if isinstance(n, dict)}
    except (KeyError, TypeError, AttributeError):
        return set()


def norm_mult(m) -> str:
    """Minuscole, senza spazi; 'n' -> '*' (anche '1..n' -> '1..*', '0..n' -> '*'); '0..*' equivalente a '*';
    '1..1' equivalente a '1' (2026-10-10, voce 111: correzione delle metriche, 19 estremi del GT del corpus)."""
    s = re.sub(r"\s+", "", str(m or "")).lower()
    s = "*" if s == "n" else re.sub(r"\.\.n$", "..*", s)
    return "*" if s == "0..*" else "1" if s == "1..1" else s


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


# --- V, Vc, J, R (da analyze_dev.py, voce 92) -----------------------------------------------------------------------


def is_valid(c: dict) -> bool:
    return c["v"].level >= 3


def is_clean(c: dict) -> bool:
    v = c["v"]
    return is_valid(c) and (v.P1_clean if c["format"] == "plantuml" else v.C2_clean)


def core_metrics(calls: list[dict]) -> dict:
    """Metriche della regola e secondarie su un insieme di risposte (una configurazione, un formato, un modello)."""
    n = len(calls)
    valid = [c for c in calls if is_valid(c)]
    jac = {id(c): jaccard(class_names(c["v"].diagram), class_names(c["gt"])) for c in valid}
    rel = Counter()
    for c in valid:
        rel += compare_relations(c["v"].diagram, c["gt"])
    gt_edges_all = sum(len(c["gt"]["edges"]) for c in calls)
    lat = [c["m"]["latency_s"] for c in calls if c["m"].get("latency_s") is not None]
    return {
        "n": n, "V": len(valid), "Vc": sum(is_clean(c) for c in calls),
        "J": sum(jac.values()) / n if n else None,  # 0 per le non valide
        "R": rel["same_type"] / gt_edges_all if gt_edges_all else None,  # 0 ritrovate per le non valide
        "J_valid": statistics.mean(jac.values()) if valid else None,
        "R_valid": rel["same_type"] / rel["gt_edges"] if rel["gt_edges"] else None,
        "truncated": sum(bool(c["v"].truncated) for c in calls),
        "relations": rel, "gt_edges_all": gt_edges_all,
        "latency_median": statistics.median(lat) if lat else None,
    }


# --- M primaria / secondaria, confusione (da analyze_instructions.py, voce 98) --------------------------------------


def match(resp: dict, gt: dict) -> tuple[list, list, list]:
    """Accoppiamento 1:1 per coppia di classi come compare_relations (prima lo stesso tipo).
    Ritorna (coppie (risposta, GT), relazioni del GT non accoppiate, relazioni della risposta non accoppiate)."""
    r_edges, g_edges = edges(resp), edges(gt)
    pairs = []
    for pair in sorted({e["pair"] for e in r_edges} & {e["pair"] for e in g_edges}, key=sorted):
        rs = [e for e in r_edges if e["pair"] == pair]
        gs = [e for e in g_edges if e["pair"] == pair]
        for same_type in (True, False):
            for r in list(rs):
                g = next((g for g in gs if (g["type"] == r["type"]) == same_type), None)
                if g is not None:
                    pairs.append((r, g))
                    rs.remove(r)
                    gs.remove(g)
    mg, mr = {id(g) for _, g in pairs}, {id(r) for r, _ in pairs}
    return pairs, [g for g in g_edges if id(g) not in mg], [r for r in r_edges if id(r) not in mr]


def gt_ends(g: dict) -> list[tuple[str, str]]:
    """Estremi (chiave, molteplicita' normalizzata) di una relazione del GT; vuoto per generalizzazione / realizzazione."""
    if g["type"] in NO_MULT:
        return []
    if "_self" in g["mult"]:
        return [("_src", g["mult"]["_self"][0]), ("_tgt", g["mult"]["_self"][1])]
    return [(g["src"], g["mult"][g["src"]]), (g["tgt"], g["mult"][g["tgt"]])]


def resp_mult(r: dict, key: str) -> str:
    if "_self" in r["mult"]:
        return r["mult"]["_self"][0 if key == "_src" else 1]
    return r["mult"].get(key, "")


def multiplicity_counts(c: dict) -> Counter:
    """Per una risposta: estremi del GT (espliciti e tutti) e quanti hanno la stessa molteplicita' nella risposta."""
    out = Counter()
    if c["v"].level >= 3:  # le relazioni del GT sono gli STESSI oggetti dell'accoppiamento (accoppiate + non accoppiate)
        pairs, missing, _ = match(c["v"].diagram, c["gt"])
        gt_edges = [(g, r) for r, g in pairs] + [(g, None) for g in missing]
    else:
        gt_edges = [(g, None) for g in edges(c["gt"])]
    for g, r in gt_edges:
        for key, gm in gt_ends(g):
            same = r is not None and resp_mult(r, key) == gm
            out["all"] += 1
            out["all_same"] += same
            if gm:
                out["explicit"] += 1
                out["explicit_same"] += same
    return out


def multiplicity_metrics(calls: list[dict]) -> dict:
    """core_metrics + M primaria (M1) e secondaria (M2), quota di tipi giusti, verso, scarti."""
    m = core_metrics(calls)
    mc = Counter()
    for c in calls:
        mc += multiplicity_counts(c)
    rel = m["relations"]
    m.update({"M1": mc["explicit_same"] / mc["explicit"] if mc["explicit"] else None,
              "M2": mc["all_same"] / mc["all"] if mc["all"] else None, "mult_counts": mc,
              "type_rate": rel["same_type"] / rel["same_pair"] if rel["same_pair"] else None,
              "dir": f"{rel['same_direction']}/{rel['directional_same_type']}",
              "discards": sum(len(getattr(c["v"], "discarded_lines", [])) + len(getattr(c["v"], "compact_issues", []))
                              for c in calls)})
    return m


def confusion(calls: list[dict]) -> dict:
    """Tabelle di confusione (solo risposte valide): molteplicita' per estremo, tipi, verso; classi e generalizzazioni
    in piu' rispetto al GT."""
    mult, types, inv, inv_tot = Counter(), Counter(), Counter(), Counter()
    extra_cls = extra_gen = 0
    for c in calls:
        if c["v"].level < 3:
            continue
        pairs, _, _ = match(c["v"].diagram, c["gt"])
        for r, g in pairs:
            types[(SHORT[g["type"]], SHORT[r["type"]])] += 1
            if g["type"] not in NO_MULT and r["type"] not in NO_MULT:
                for key, gm in gt_ends(g):
                    mult[(gm or "(vuoto)", resp_mult(r, key) or "(vuoto)")] += 1
            if r["type"] == g["type"] and g["type"] in ORIENTED:
                inv_tot[SHORT[g["type"]]] += 1
                inv[SHORT[g["type"]]] += (r["src"], r["tgt"]) != (g["src"], g["tgt"])
        extra_cls += len(class_names(c["v"].diagram) - class_names(c["gt"]))
        g_inh = {(e["src"], e["tgt"]) for e in edges(c["gt"]) if e["type"] == "ClassInheritance"}
        extra_gen += sum((e["src"], e["tgt"]) not in g_inh for e in edges(c["v"].diagram)
                         if e["type"] == "ClassInheritance")
    return {"mult": mult, "types": types, "inv": inv, "inv_tot": inv_tot, "extra_cls": extra_cls, "extra_gen": extra_gen}


# --- R_fam, composizioni in piu', insieme completo (da analyze_v5.py, voce 111) ------------------------------------


def r_fam(m: dict) -> float | None:
    rel = m["relations"]
    return ((rel["same_type"] + sum(rel[k] for k in FAMILY_SWAPS)) / m["gt_edges_all"]) if m["gt_edges_all"] else None


def extra_compositions(calls: list[dict]) -> int:
    """Composizioni della risposta (valide) la cui coppia di classi non e' una composizione nel GT."""
    n = 0
    for c in calls:
        if c["v"].level < 3:
            continue
        gt_comp = {e["pair"] for e in edges(c["gt"]) if e["type"] == "ClassComposition"}
        n += sum(e["pair"] not in gt_comp for e in edges(c["v"].diagram) if e["type"] == "ClassComposition")
    return n


def all_metrics(calls: list[dict]) -> dict:
    """Tutte le metriche del 3b: multiplicity_metrics + R_fam, generalizzazioni invertite, classi / generalizzazioni /
    composizioni in piu', tabelle di confusione."""
    m = multiplicity_metrics(calls)
    conf = confusion(calls)
    m.update({"R_fam": r_fam(m), "inv_gen": conf["inv"]["generalizzazione"],
              "inv_gen_tot": conf["inv_tot"]["generalizzazione"], "extra_cls": conf["extra_cls"],
              "extra_gen": conf["extra_gen"], "extra_comp": extra_compositions(calls), "conf": conf})
    return m

# --- attributi (voce 135, aggiunta: le metriche precedenti non cambiano) ---------------------------------------------


def attribute_names(diagram: dict) -> dict[str, set[str]]:
    """Classe (nome normalizzato) -> nomi normalizzati dei suoi attributi; classi non enum. Il nome dell'attributo e'
    la parte prima dei due punti, senza visibilita' ("+ DeliveryDate : date" -> "deliverydate")."""
    out: dict[str, set[str]] = {}
    for n in diagram.get("nodes", []) or []:
        data = n.get("data") or {}
        if data.get("stereotype") == "enumeration":
            continue
        names = set()
        for a in data.get("attributes", []) or []:
            raw = (a.get("name") if isinstance(a, dict) else str(a)).split(":")[0]
            raw = re.sub(r"^[\s+\-#~]+", "", raw)
            if norm(raw):
                names.add(norm(raw))
        out.setdefault(norm(data.get("name", "")), set()).update(names)
    return out


def attribute_counts(c: dict) -> Counter:
    """Per una risposta: attributi del GT, del GT ritrovati (stessa classe, stesso nome), della risposta e della
    risposta presenti nel GT; skeleton = risposta valida senza attributi per un GT che ne ha."""
    gt = attribute_names(c["gt"])
    out = Counter(gt_attrs=sum(len(v) for v in gt.values()))
    if c["v"].level < 3:
        return out
    resp = attribute_names(c["v"].diagram)
    out["resp_attrs"] = sum(len(v) for v in resp.values())
    out["found"] = sum(len(gt[k] & resp.get(k, set())) for k in gt)
    out["resp_in_gt"] = sum(len(resp[k] & gt.get(k, set())) for k in resp)
    out["skeleton"] = int(out["resp_attrs"] == 0 and out["gt_attrs"] > 0)
    return out


def attribute_metrics(calls: list[dict]) -> dict:
    """A = attributi del GT ritrovati / attributi del GT su TUTTE le risposte (0 per le non valide); A_prec =
    attributi della risposta presenti nel GT / attributi della risposta (risposte valide); scheletri."""
    tot = Counter()
    for c in calls:
        tot += attribute_counts(c)
    return {"A": tot["found"] / tot["gt_attrs"] if tot["gt_attrs"] else None,
            "A_prec": tot["resp_in_gt"] / tot["resp_attrs"] if tot["resp_attrs"] else None,
            "skeletons": tot["skeleton"], "attr_counts": tot}
