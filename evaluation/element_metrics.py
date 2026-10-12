"""
Metriche standard per tipo di elemento: precision, recall e F1 con abbinamento ESATTO e RILASSATO (2026-10-12, voce
136). Riferimenti: Chen et al. (MODELS 2023) e Chen, Shen, He (2024) per P / R / F1 su classi, attributi, associazioni
e generalizzazioni; Yang et al. (2022) per i due livelli di abbinamento (esatto e rilassato).

Solo regole deterministiche: nessun embedding, nessuna soglia. evaluation/metrics.py (metriche congelate J, R, M...)
NON e' toccato: questo modulo si affianca.

ELEMENTI (dal diagramma Apollon v4):
- classi: tutti i nodi (classi, classi astratte, interfacce, enumerazioni);
- attributi: gli attributi dei nodi non enumerazione (nome = parte prima dei due punti, senza visibilita'; i
  valori delle enumerazioni e i metodi non contano);
- relazioni strutturali: associazione, unidirezionale, composizione, aggregazione, dipendenza;
- generalizzazioni: ereditarieta' e realizzazione (source = figlia, target = madre).

ABBINAMENTO DELLE CLASSI, uno a uno e deterministico (pareggi risolti per nome normalizzato, poi per nome originale):
- ESATTO: stesso nome normalizzato (minuscole, solo alfanumerici: la normalizzazione di metrics.norm);
- RILASSATO: prima gli abbinamenti esatti, poi le classi rimaste con lo stesso INSIEME di token del nome (CamelCase
  spezzato, minuscole, stemming Snowball inglese: gli stessi token di Jt, retrieval/relevance.py). Niente altro.
ATTRIBUTI: abbinati solo dentro coppie di classi abbinate; esatto = stesso nome normalizzato; rilassato = prima gli
esatti, poi lo stesso insieme di token stemmati. Gli attributi di classi non abbinate sono FP (risposta) o FN (GT).
RELAZIONI STRUTTURALI: abbinate se le classi ai due estremi sono abbinate, SENZA guardare il verso (come Chen et al.);
a parita' di coppia di classi, prima le relazioni dello stesso tipo, poi le altre (uno a uno).
GENERALIZZAZIONI: abbinate se figlia e madre sono abbinate, CON il verso; quelle con figlia e madre scambiate si
contano a parte (inv_generalizations) e restano FP e FN.

PER RISPOSTA, tipo di elemento e livello: TP, FP, FN; P = TP / (TP + FP), R = TP / (TP + FN), F1 = 2PR / (P + R).
- Risposta NON valida (livello < 3) = diagramma vuoto: TP = FP = 0, quindi recall 0 e F1 0 (se il GT ha elementi di
  quel tipo), precision NON DEFINITA ed esclusa dalla media della precision (il numero di risposte escluse si riporta).
- P non definita se la risposta non ha elementi di quel tipo; R non definita se non ne ha il GT; F1 = 0 se TP = 0 e
  almeno una delle due parti ha elementi; F1 non definita se nessuna delle due ne ha (esclusa dalle medie).
MEDIE: macro per esercizio (prima la media sulle ripetizioni dello stesso esercizio, poi la media sugli esercizi;
valori non definiti esclusi) e micro (TP, FP, FN sommati su tutte le risposte).
QUALITA' DELLE RELAZIONI ABBINATE (strutturali): stesso tipo; stessa famiglia (associazione = unidirezionale);
molteplicita' uguali per estremo (metrics.norm_mult), su tutti gli estremi e sui soli estremi espliciti del GT;
stesso verso per i tipi orientati (composizione, aggregazione, unidirezionale, dipendenza) a parita' di tipo.
"""

from __future__ import annotations

import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "retrieval"))
sys.path.insert(0, str(ROOT))
from evaluation.metrics import norm, norm_mult  # noqa: E402
from relevance import name_tokens  # noqa: E402
from text_preprocessing import _stemmer  # noqa: E402

LEVELS = ("exact", "relaxed")
TYPES = ("classes", "attributes", "relations", "generalizations")
STRUCTURAL = ("ClassBidirectional", "ClassUnidirectional", "ClassComposition", "ClassAggregation", "ClassDependency")
GENERALIZATION = ("ClassInheritance", "ClassRealization")
ORIENTED = ("ClassUnidirectional", "ClassComposition", "ClassAggregation", "ClassDependency")
FAMILY = {"ClassBidirectional": "association", "ClassUnidirectional": "association"}
VISIBILITY = re.compile(r"^[\s+\-#~]+")


def tokens(name: str) -> frozenset[str]:
    """Insieme dei token stemmati di un nome (come Jt): `ReservationSlot` -> {reserv, slot}."""
    return frozenset(_stemmer().stemWords(name_tokens(name)))


def attribute_name(raw) -> str:
    text = raw.get("name", "") if isinstance(raw, dict) else str(raw)
    return VISIBILITY.sub("", text.split(":")[0]).strip()


# --- estrazione degli elementi ---------------------------------------------------------------------------------------


def elements(diagram: dict | None) -> dict:
    """Classi (id -> nome), attributi (id -> nomi), relazioni strutturali e generalizzazioni (liste di dict)."""
    out = {"classes": {}, "attributes": {}, "relations": [], "generalizations": []}
    if not diagram:
        return out
    for n in diagram.get("nodes", []) or []:
        data = n.get("data") or {}
        out["classes"][n["id"]] = data.get("name", "")
        if data.get("stereotype") != "enumeration":
            out["attributes"][n["id"]] = [a for a in (attribute_name(x) for x in data.get("attributes", []) or []) if norm(a)]
    for e in diagram.get("edges", []) or []:
        if e.get("source") not in out["classes"] or e.get("target") not in out["classes"]:
            continue
        d = e.get("data") or {}
        rec = {"type": e.get("type"), "src": e["source"], "tgt": e["target"],
               "src_mult": norm_mult(d.get("sourceMultiplicity")), "tgt_mult": norm_mult(d.get("targetMultiplicity"))}
        if rec["type"] in STRUCTURAL:
            out["relations"].append(rec)
        elif rec["type"] in GENERALIZATION:
            out["generalizations"].append(rec)
    return out


# --- abbinamento -----------------------------------------------------------------------------------------------------


def _pair_by_key(resp: list[tuple[str, str]], gt: list[tuple[str, str]], key) -> list[tuple[str, str]]:
    """resp, gt: liste di (id, nome). Abbina uno a uno gli elementi con la stessa chiave, nell'ordine (nome normalizzato,
    nome, id): deterministico."""
    order = lambda x: (norm(x[1]), x[1], x[0])  # noqa: E731
    groups_r, groups_g = {}, {}
    for x in sorted(resp, key=order):
        groups_r.setdefault(key(x[1]), []).append(x[0])
    for x in sorted(gt, key=order):
        groups_g.setdefault(key(x[1]), []).append(x[0])
    pairs = []
    for k in sorted(set(groups_r) & set(groups_g), key=lambda k: str(sorted(k)) if isinstance(k, frozenset) else str(k)):
        pairs += list(zip(groups_r[k], groups_g[k]))
    return pairs


def match_names(resp: list[tuple[str, str]], gt: list[tuple[str, str]], level: str) -> dict[str, str]:
    """id della risposta -> id del GT. Esatto: stesso nome normalizzato; rilassato: poi stesso insieme di token."""
    resp = [x for x in resp if norm(x[1])]
    gt = [x for x in gt if norm(x[1])]
    mapping = dict(_pair_by_key(resp, gt, norm))
    if level == "relaxed":
        rest_r = [x for x in resp if x[0] not in mapping]
        used = set(mapping.values())
        rest_g = [x for x in gt if x[0] not in used]
        mapping.update(_pair_by_key(rest_r, rest_g, tokens))
    return mapping


def compare(resp_diagram: dict | None, gt_diagram: dict, level: str) -> dict:
    """Conteggi per una risposta e un livello: per tipo TP / FP / FN, piu' la qualita' delle relazioni abbinate."""
    r, g = elements(resp_diagram), elements(gt_diagram)
    cmap = match_names(list(r["classes"].items()), list(g["classes"].items()), level)
    out = {t: Counter() for t in TYPES}
    out["classes"].update(tp=len(cmap), fp=len(r["classes"]) - len(cmap), fn=len(g["classes"]) - len(cmap))
    # attributi: dentro le classi abbinate
    ra = sum(len(v) for v in r["attributes"].values())
    ga = sum(len(v) for v in g["attributes"].values())
    tp = 0
    for rid, gid in cmap.items():
        ri = [(f"{rid}#{i}", a) for i, a in enumerate(r["attributes"].get(rid, []))]
        gi = [(f"{gid}#{i}", a) for i, a in enumerate(g["attributes"].get(gid, []))]
        tp += len(match_names(ri, gi, level))
    out["attributes"].update(tp=tp, fp=ra - tp, fn=ga - tp)
    # relazioni strutturali: coppia non ordinata di classi abbinate, prima lo stesso tipo
    quality = Counter()
    mapped = [dict(e, msrc=cmap.get(e["src"]), mtgt=cmap.get(e["tgt"])) for e in r["relations"]]
    pairs = []
    for key in sorted({frozenset((e["src"], e["tgt"])) for e in g["relations"]}, key=lambda k: sorted(k)):
        gs = [e for e in g["relations"] if frozenset((e["src"], e["tgt"])) == key]
        rs = [e for e in mapped if e["msrc"] and e["mtgt"] and frozenset((e["msrc"], e["mtgt"])) == key
              and not e.get("_used")]
        for same in (True, False):
            for ge in list(gs):
                re_ = next((x for x in rs if not x.get("_used") and (x["type"] == ge["type"]) == same), None)
                if re_ is not None:
                    re_["_used"] = True
                    gs.remove(ge)
                    pairs.append((re_, ge))
    tp = len(pairs)
    out["relations"].update(tp=tp, fp=len(r["relations"]) - tp, fn=len(g["relations"]) - tp)
    for re_, ge in pairs:
        quality["matched"] += 1
        quality["same_type"] += re_["type"] == ge["type"]
        quality["same_family"] += FAMILY.get(re_["type"], re_["type"]) == FAMILY.get(ge["type"], ge["type"])
        if ge["src"] == ge["tgt"]:  # relazione su se stessa: estremi per posizione
            ends = [(ge["src_mult"], re_["src_mult"]), (ge["tgt_mult"], re_["tgt_mult"])]
        else:
            rm = {re_["msrc"]: re_["src_mult"], re_["mtgt"]: re_["tgt_mult"]}
            ends = [(ge["src_mult"], rm.get(ge["src"], "")), (ge["tgt_mult"], rm.get(ge["tgt"], ""))]
        for gm, rmult in ends:
            quality["ends"] += 1
            quality["ends_same"] += gm == rmult
            if gm:
                quality["ends_explicit"] += 1
                quality["ends_explicit_same"] += gm == rmult
        if re_["type"] == ge["type"] and ge["type"] in ORIENTED:
            quality["oriented"] += 1
            quality["same_direction"] += (re_["msrc"], re_["mtgt"]) == (ge["src"], ge["tgt"])
    # generalizzazioni: figlia e madre abbinate, con il verso; le invertite a parte
    gkeys = [(e["src"], e["tgt"]) for e in g["generalizations"]]
    rkeys = [(cmap.get(e["src"]), cmap.get(e["tgt"])) for e in r["generalizations"]]
    left_g, tp = list(gkeys), 0
    left_r = []
    for k in rkeys:
        if None not in k and k in left_g:
            left_g.remove(k)
            tp += 1
        else:
            left_r.append(k)
    inverted = 0
    for k in left_r:
        if None not in k and (k[1], k[0]) in left_g:
            left_g.remove((k[1], k[0]))
            inverted += 1
    out["generalizations"].update(tp=tp, fp=len(rkeys) - tp, fn=len(gkeys) - tp)
    quality["inv_generalizations"] = inverted
    return {"counts": out, "quality": quality}


# --- P / R / F1 e medie ----------------------------------------------------------------------------------------------


def prf(c: Counter) -> dict:
    tp, fp, fn = c["tp"], c["fp"], c["fn"]
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    if tp + fp + fn == 0:
        f1 = None
    elif tp == 0:
        f1 = 0.0
    else:
        f1 = 2 * p * r / (p + r)
    return {"P": p, "R": r, "F1": f1}


def evaluate_call(c: dict) -> dict:
    """Per una risposta (dict delle analisi: v, gt, q, r): livello -> {counts, quality, scores}."""
    diagram = c["v"].diagram if c["v"].level >= 3 else None
    out = {}
    for level in LEVELS:
        res = compare(diagram, c["gt"], level)
        res["scores"] = {t: prf(res["counts"][t]) for t in TYPES}
        out[level] = res
    return out


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None


def aggregate(calls: list[dict]) -> dict:
    """Medie macro per esercizio e micro, per livello e tipo; qualita' delle relazioni abbinate (micro); risposte
    escluse dalla media della precision (precision non definita: risposte non valide o senza elementi del tipo)."""
    ev = [(c["q"], c, evaluate_call(c)) for c in calls]
    out = {"n": len(calls), "invalid": sum(c["v"].level < 3 for c in calls)}
    for level in LEVELS:
        lv = {}
        for t in TYPES:
            by_q = {}
            for q, _, e in ev:
                by_q.setdefault(q, []).append(e[level]["scores"][t])
            macro = {m: _mean(_mean(s[m] for s in v) for v in by_q.values()) for m in ("P", "R", "F1")}
            micro = Counter()
            for _, _, e in ev:
                micro += e[level]["counts"][t]
            lv[t] = {"macro": macro, "micro": prf(micro), "counts": micro,
                     "p_excluded": sum(e[level]["scores"][t]["P"] is None for _, _, e in ev)}
        qual = Counter()
        for _, _, e in ev:
            qual += e[level]["quality"]
        rate = lambda a, b: qual[a] / qual[b] if qual[b] else None  # noqa: E731
        lv["quality"] = {"same_type": rate("same_type", "matched"), "same_family": rate("same_family", "matched"),
                         "mult_all": rate("ends_same", "ends"), "mult_explicit": rate("ends_explicit_same", "ends_explicit"),
                         "direction": rate("same_direction", "oriented"), "inv_generalizations": qual["inv_generalizations"],
                         "matched": qual["matched"]}
        out[level] = lv
    return out


def per_exercise(calls: list[dict], level: str = "relaxed", t: str = "relations", m: str = "F1") -> dict[str, float | None]:
    """Esercizio -> media sulle ripetizioni della metrica (per le correlazioni per esercizio)."""
    by_q = {}
    for c in calls:
        by_q.setdefault(c["q"], []).append(evaluate_call(c)[level]["scores"][t][m])
    return {q: _mean(v) for q, v in sorted(by_q.items())}
