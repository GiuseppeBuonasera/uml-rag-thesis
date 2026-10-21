"""
Raccoglie i risultati trovati finora nella cartella `results/` della radice del repo (richiesta dell'utente, 2026-10-21)
e costruisce i due Excel per esercizio. COPIA i file (non li sposta): gli script continuano a leggere `data/results/`.
Si rilancia quando arrivano nuove run.

Contenuto di results/:
  1_passo3b/            passo3b_completezza.xlsx (completezza dei relatori per prompt, esercizi ordinati per
                        difficolta' Flesch-Kincaid e per grandezza), file dei relatori, export zip, CSV
  2_controlli_oracle/   controlli_f1.xlsx (F1 dei controlli, stesso ordinamento) e sommari (voci 162-169)
  3_sviluppo/           sommari delle analisi di sviluppo (piloti e dev set, voci fino alla 151)
  README.md             indice

Uso:
    python experiments/build_results.py [--out results]
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / p) for p in ("experiments", "generation", "retrieval", "")]
import compare_3b as c3  # noqa: E402
import difficulty_3b as dif  # noqa: E402
import review_report as rr  # noqa: E402
from evaluation import element_metrics as el  # noqa: E402

GEN = ROOT / "data" / "results" / "generation"
ANALISI = GEN / "analisi_3b"
SRC = ANALISI / "evaluation_summary-2.xlsx"
CONDS = [c3.label(a, k) for a, k in c3.CONDITIONS]
FMTS = {"P": ("plantuml", "PlantUML"), "C": ("compatto", "JSON compatto")}
TYPES = ("classes", "attributes", "relations", "generalizations")
SPLITS = ("corpus", "testset")
XLSX_3B = "1_passo3b/passo3b_completezza.xlsx"
XLSX_CTRL = "2_controlli_oracle/controlli_f1.xlsx"
XLSX_RANK = "classifica_run.xlsx"
# versioni precedenti, tolte da results/ (restano in data/results/): l'Excel sostituito dai due file sopra e le tabelle
# F1 per fascia di difficolta' (nostra F1, script temporaneo), sostituite dai fogli ordinati per difficolta'
OLD_OUTPUTS = ("1_passo3b/esercizi_difficolta.xlsx",
               *[f"1_passo3b/f1_{a}_per_{b}.csv" for a in ("classi", "relazioni") for b in ("fk", "size")])
# controlli oracle (voci 162-169): (formati, etichetta della colonna, prefisso della run, filtro su condizione e k)
CONTROLS = [
    ("PC", "3b zero_shot (riferimento)", "passo3b__{F}-{s}-G26", {"cond": {"zero_shot"}}),
    ("PC", "3b bm25 k3 (riferimento)", "passo3b__{F}-{s}-G26", {"cond": {"bm25"}, "k": {"3"}}),
    ("PC", "esercizio stesso (blocco standard)", "oracle_self__{F}-{s}-standard", {}),
    ("PC", "esercizio stesso (blocco libero)", "oracle_self__{F}-{s}-libero", {}),
    ("PC", "parziale 25 %", "oracle_partial__{F}-{s}-25", {}),
    ("PC", "parziale 50 %", "oracle_partial__{F}-{s}-50", {}),
    ("PC", "parziale 75 %", "oracle_partial__{F}-{s}-75", {}),
    ("PC", "meta' + 2 bm25", "oracle_mix__{F}-{s}-diluito", {}),
    ("PC", "due meta'", "oracle_mix__{F}-{s}-complemento", {}),
    ("PC", "esercizio stesso senza attributi", "oracle_attr_self__{F}-{s}", {}),
    ("PC", "bm25 k3 senza attributi", "oracle_attr_bm25__{F}-{s}", {}),
]
# (sorgente, destinazione relativa a results/)
COPIES = [
    (SRC, "1_passo3b/evaluation_summary_relatori.xlsx"),
    (GEN / "export_3b" / "passo3b_risultati.zip", "1_passo3b/passo3b_risultati.zip"),
    (ANALISI / "difficolta.csv", "1_passo3b/difficolta.csv"),
    *[(GEN / f"{n}_analysis" / "summary.md", f"2_controlli_oracle/{n}.md")
      for n in ("oracle_self", "oracle_partial", "oracle_mix", "oracle_attr", "oracle_partial_compatto",
                "oracle_mix_compatto")],
]
# ordinamento decrescente (piu' difficile in alto) sulla colonna; la grandezza per prima perche' e' la difficolta'
# dominante (Spearman con la completezza circa −0,45 contro circa −0,2 di Flesch-Kincaid sui 54, README_valutazioni 1.4)
ORDERS = {"grandezza": 3, "Flesch-Kincaid": 2}


def development_copies() -> list[tuple[Path, str]]:
    return [(d / "summary.md", f"3_sviluppo/{d.name.removesuffix('_analysis')}.md")
            for d in sorted(GEN.glob("*_analysis")) if d.name.startswith(("dev_", "pilot2_")) and (d / "summary.md").exists()]


def complete(d: Path) -> bool:
    """Run conclusa: tante righe nel manifest quante generazioni previste dalla sua config (le run in corso restano fuori)."""
    if not (d / "manifest.jsonl").exists():
        return False
    if d.name.startswith("passo3b"):  # concluso (voce 151); AirTravel non ha static, quindi il conteggio non torna
        return True
    cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))["config"]
    expected = len(cfg["query_ids"]) * cfg["repetitions"] * sum(len(cfg["k"].get(c, [0])) for c in cfg["conditions"])
    with open(d / "manifest.jsonl", encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip()) >= expected


def ordered(rows: list[tuple], by: str) -> list[tuple]:
    """rows = (esercizio, insieme, Flesch-Kincaid, size); decrescente sulla difficolta' scelta, a parita' sull'altra
    difficolta', poi per nome."""
    j = ORDERS[by]
    other = 5 - j
    return sorted(rows, key=lambda r: (-r[j], -r[other], r[0]))


def f1_mean(x: dict) -> float | None:
    s = el.evaluate_call(x)["relaxed"]["scores"]
    v = [s[t]["F1"] for t in TYPES if s[t]["F1"] is not None]
    return st.mean(v) if v else None


def control_values(gt: dict, results: Path = GEN, runs: list | None = None) -> tuple[dict, list[str], dict]:
    """(esercizio, formato, colonna) -> F1 medio sulle quattro tipologie (media delle ripetizioni valide)."""
    f1, missing, invalid = {}, [], defaultdict(int)
    for formats, label, prefix, flt in (CONTROLS if runs is None else runs):
        for F in formats:
            dirs = [results / prefix.format(F=F, s=s) for s in SPLITS]
            absent = [d.name for d in dirs if not complete(d)]
            if absent:  # una colonna entra solo con tutte le sue run concluse (corpus e De Bari)
                missing += absent
                continue
            acc = defaultdict(list)
            for d in dirs:
                for x in rr.load_run(d, flt, gt):
                    if x["v"].level < 3:  # risposte non valide ESCLUSE dalla media
                        invalid[(F, label)] += 1
                        continue
                    v = f1_mean(x)
                    if v is not None:
                        acc[x["q"]].append(v)
            for q, v in acc.items():
                f1[(q, F, label)] = st.mean(v)
    return f1, missing, invalid


class Book:
    """Fogli per esercizio con due righe di intestazione (gruppi per formato) e righe di media in fondo."""

    def __init__(self):
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        self.wb = Workbook()
        self.wb.remove(self.wb.active)
        self.FN, self.BOLD = Font(name="Arial", size=10), Font(name="Arial", size=10, bold=True)
        self.HB = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        self.DARK, self.MID = PatternFill("solid", start_color="2F5496"), PatternFill("solid", start_color="5B7BC0")
        self.KEY = PatternFill("solid", start_color="C00000")
        self.THIN = Side(style="thin", color="BFBFBF")
        self.Alignment, self.Border, self.Font = Alignment, Border, Font
        self.CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

    def sheet(self, title: str, rows: list, by: str, groups: list, values: dict, fmt: str, means: list) -> None:
        """groups = [(intestazione, colore, chiave del formato, [colonne])]; values[(esercizio, chiave, colonna)];
        means = [(etichetta, None | insieme)] righe di media in fondo."""
        from openpyxl.utils import get_column_letter
        ws = self.wb.create_sheet(title)
        A, B = self.Alignment, self.Border

        def hdr(r, col, v, f):
            x = ws.cell(row=r, column=col, value=v)
            x.font, x.fill, x.alignment = self.HB, f, self.CENTER
            x.border = B(left=self.THIN, right=self.THIN, top=self.THIN, bottom=self.THIN)
        hdr(1, 1, "Esercizio", self.DARK); ws.merge_cells("A1:A2")
        hdr(1, 2, "Insieme", self.DARK); ws.merge_cells("B1:B2")
        hdr(1, 3, f"Difficoltà (ordinati per {by}, decrescente)", self.DARK); ws.merge_cells("C1:D1")
        hdr(2, 3, "Flesch-Kincaid", self.KEY if by == "Flesch-Kincaid" else self.MID)
        hdr(2, 4, "Grandezza (classi + relazioni)", self.KEY if by == "grandezza" else self.MID)
        col, cols = 5, []
        for head, fill, key, names in groups:
            hdr(1, col, head, fill)
            ws.merge_cells(start_row=1, start_column=col, end_row=1, end_column=col + len(names) - 1)
            for k, name in enumerate(names):
                hdr(2, col + k, name, self.MID)
                cols.append((col + k, key, name))
            col += len(names)
        for i, (e, r, f, sz) in enumerate(ordered(rows, by), 3):
            ws.cell(row=i, column=1, value=e).font = self.FN
            ws.cell(row=i, column=2, value=r).font = self.FN
            x = ws.cell(row=i, column=3, value=f); x.font = self.FN; x.number_format = "0.00"
            x = ws.cell(row=i, column=4, value=sz); x.font = self.FN; x.alignment = A(horizontal="center")
            for j, key, name in cols:
                v = values.get((e, key, name))
                y = ws.cell(row=i, column=j, value=None if v is None else round(v, 4))
                y.font, y.number_format, y.alignment = self.FN, fmt, A(horizontal="center")
            for j in range(1, col):
                ws.cell(row=i, column=j).border = B(bottom=self.THIN)
        last = len(rows) + 2
        for m, (label, group) in enumerate(means, 1):
            ws.cell(row=last + m, column=1, value=label).font = self.BOLD
            for j in range(3, col):
                L = get_column_letter(j)
                f = (f"=AVERAGE({L}3:{L}{last})" if group is None
                     else f'=AVERAGEIF($B$3:$B${last},"{group}",{L}3:{L}{last})')
                z = ws.cell(row=last + m, column=j, value=f)
                z.font, z.alignment = self.BOLD, A(horizontal="center")
                z.number_format = "0.00" if j == 3 else "0.0" if j == 4 else fmt
        for L, w in zip("ABCD", (38, 13, 14, 16)):
            ws.column_dimensions[L].width = w
        for j in range(5, col):
            ws.column_dimensions[get_column_letter(j)].width = 12
        ws.row_dimensions[1].height = 32
        ws.row_dimensions[2].height = 58
        ws.freeze_panes = "E3"
        ws.auto_filter.ref = f"A2:{get_column_letter(col - 1)}{last}"

    def notes(self, lines: list[str], out: Path) -> None:
        n = self.wb.create_sheet("Note")
        n.column_dimensions["A"].width = 150
        for i, t in enumerate(lines, 1):
            x = n.cell(row=i, column=1, value=t)
            x.font = self.Font(name="Arial", size=10, bold=not t.startswith(" "))
            x.alignment = self.Alignment(wrap_text=True, vertical="top")
        out.parent.mkdir(parents=True, exist_ok=True)
        self.wb.save(out)


def exercise_rows():
    import yaml
    from prompt_builder import cl
    c, q = cl.load_all()
    by = {x["id"]: x for x in c + q}
    gt = {i: x["diagram_apollon_json"] for i, x in by.items()}
    roles = {r["id"]: r["role"] for r in yaml.safe_load((ROOT / "corpus" / "roles.yaml").read_text(encoding="utf-8"))}
    rows = {}
    for i in roles:
        e = el.elements(gt[i])
        rows[i] = (i, roles[i], round(dif.flesch_kincaid(by[i]["description"]), 2),
                   len(e["classes"]) + len(e["relations"]) + len(e["generalizations"]))
    return rows, gt


DIFF_NOTE = ("Difficoltà: Flesch-Kincaid Grade Level della traccia (textstat 0.7.4; più alto = più difficile) e grandezza "
             "= classi + relazioni del GT, generalizzazioni comprese. Un foglio per ciascun ordinamento (decrescente: il "
             "più difficile in alto); la colonna usata per ordinare ha l'intestazione rossa. Primo foglio: la GRANDEZZA, "
             "difficoltà dominante (Spearman con la completezza circa −0,45 contro circa −0,2 di Flesch-Kincaid sui 54); "
             "a parità di valore decide l'altra difficoltà, poi il nome dell'esercizio.")


def build_3b(out: Path, rows: dict) -> dict:
    import pandas as pd
    from openpyxl.styles import PatternFill
    ids = [r for i, r in rows.items() if i != "AirTravel"]
    df = pd.read_excel(SRC)
    assert len(df) == 2874 and set(df["status"]) == {"ok"}
    inval = df[df["V"] == 0]
    acc = defaultdict(list)
    for r in df.itertuples():
        acc.setdefault((r.esercizio, r.formato, r.condizione_k), [])
        if r.V == 1:  # risposte non valide ESCLUSE dalla media
            acc[(r.esercizio, r.formato, r.condizione_k)].append(float(r.completeness))
    vals = {k: st.mean(v) for k, v in acc.items() if v}
    partial = sorted((k, len(v)) for k, v in acc.items() if len(v) < 3)
    bk = Book()
    REL = PatternFill("solid", start_color="7F6000")
    groups = [(f"Completezza totale (relatori, %) — {fl}", REL, fn, CONDS) for fn, fl in FMTS.values()]
    means = [("Media (tutti gli esercizi)", None), ("Media (solo validazione)", "valutazione"),
             ("Media (solo sviluppo)", "sviluppo")]
    for by in ORDERS:
        bk.sheet(f"Per {by}", ids, by, groups, vals, "0.00", means)
    bk.notes([
        "Passo 3b: completezza dello strumento dei relatori per esercizio, prompt e formato (Gemma 4 26B A4B QAT, 3 ripetizioni).",
        "  " + DIFF_NOTE,
        "  completeness = elementi del GT ritrovati (classi + attributi + associazioni) / elementi del GT, in percentuale; è una RECALL: non penalizza gli elementi in più. Le associazioni comprendono le generalizzazioni.",
        "  Prompt: zero_shot; static k2 (bank loans + AirTravel); random k3; bm25 k2 e k3; hybrid k3. AirTravel escluso (non ha la condizione static): 79 esercizi.",
        f"  RISPOSTE NON VALIDE ESCLUSE: le {len(inval)} risposte non valide per il nostro post-processing (V = 0) non entrano nelle medie; ogni cella è la media delle sole ripetizioni valide.",
        "  Celle con meno di 3 ripetizioni valide: " + "; ".join(f"{e} / {f} / {c}: {k} su 3" for (e, f, c), k in partial) + ".",
        "  Insieme: 'valutazione' = esercizi dell'analisi principale (53 senza AirTravel); 'sviluppo' = i 26 usati per le scelte di configurazione (voce 151).",
        "  Fonte: evaluation_summary_relatori.xlsx (2026-10-19). Generato da experiments/build_results.py.",
    ], out)
    return {"rows": len(ids), "invalid": len(inval)}


def build_controls(out: Path, rows: dict, gt: dict) -> dict:
    from openpyxl.styles import PatternFill
    ids = [r for r in rows.values() if r[1] == "valutazione"]
    f1, missing, invalid = control_values(gt)
    fill = PatternFill("solid", start_color="385723")
    groups = [(f"F1 medio 4 tipologie — {FMTS[F][1]}", fill, F, [lab for fs, lab, _, _ in CONTROLS if F in fs])
              for F in FMTS]
    bk = Book()
    for by in ORDERS:
        bk.sheet(f"Per {by}", ids, by, groups, f1, "0.000", [("Media (54 esercizi)", None)])
    bk.notes([
        "Controlli SOLO ANALISI (voci 162-169): F1 per esercizio, 54 esercizi di validazione, 1 ripetizione (Gemma 4 26B A4B QAT).",
        "  " + DIFF_NOTE,
        "  F1 = media degli F1 di classi, attributi, relazioni e generalizzazioni (evaluation/element_metrics.py, abbinamento rilassato; tipologie assenti sia nel GT sia nella risposta escluse). Metrica NOSTRA: lo strumento dei relatori non ha valutato queste run.",
        "  Colonne '3b ... (riferimento)': media delle 3 ripetizioni del passo 3b, per confronto.",
        "  esercizio stesso = il diagramma di riferimento dell'esercizio come unico esempio (voce 162; blocco standard = testo degli esempi del 3b, libero = 'mostra il formato e lo stile').",
        "  parziale X % = solo X % delle classi dell'esercizio stesso, con le relazioni tra quelle classi (voce 163).",
        "  meta' + 2 bm25 = meta' dell'esercizio stesso + i 2 esempi bm25 k2; due meta' = le due meta' complementari come due esempi (voci 164-165); nel compatto dalla voce 170.",
        "  senza attributi = esempi con classi e relazioni ma attributi tolti (valori degli enum e metodi restano): esercizio stesso, oppure gli esempi bm25 k3 del 3b (voci 167 e 169).",
        "  Risposte non valide escluse: " + ("; ".join(f"{FMTS[F][1]} / {lab}: {k}" for (F, lab), k in invalid.items() if k) or "nessuna") + ".",
        ("  Run non ancora presenti (colonne vuote): " + ", ".join(missing) + "." if missing else "  Tutte le run dei controlli presenti."),
        "  Generato da experiments/build_results.py.",
    ], out)
    return {"rows": len(ids), "missing": missing}


# classifica di tutte le run (54 di validazione): i 6 prompt del 3b e i controlli oracle (senza i duplicati "riferimento")
RANK_RUNS = [("PC", f"3b {c3.label(a, k)}", "passo3b__{F}-{s}-G26",
              {"cond": {a}, "k": {str(k)}} if k else {"cond": {a}}) for a, k in c3.CONDITIONS] + CONTROLS[2:]


def build_ranking(out: Path, rows: dict, gt: dict) -> dict:
    """Graduatoria delle run per F1 medio sui 54, con la media sulla meta' piu' difficile e su quella piu' facile degli
    esercizi (27 + 27), un foglio per difficolta' (Flesch-Kincaid, grandezza)."""
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    ids = [r for r in rows.values() if r[1] == "valutazione"]
    f1, missing, invalid = control_values(gt, runs=RANK_RUNS)
    runs = [(F, lab) for fs, lab, _, _ in RANK_RUNS for F in fs if any(k[1:] == (F, lab) for k in f1)]
    bk = Book()
    HB, FN, BOLD = bk.HB, bk.FN, bk.BOLD
    fills = {"3b": PatternFill("solid", start_color="DDEBF7"), "controllo": PatternFill("solid", start_color="E2EFDA")}
    THIN = Side(style="thin", color="BFBFBF")
    heads = ["Posizione", "Run", "Formato", "Tipo", "Esercizi", "F1 tutti (54)", "F1 metà più difficile (27)",
             "F1 metà più facile (27)", "Facile − difficile", "Posizione tra i difficili", "Posizione tra i facili"]
    result = {}
    for by in ORDERS:
        order = [r[0] for r in ordered(ids, by)]
        half = len(order) // 2
        hard, easy = set(order[:half]), set(order[half:])
        table = []
        for F, lab in runs:
            v = {q: f1[(q, F, lab)] for q in order if (q, F, lab) in f1}
            m = lambda qs: st.mean(v[q] for q in qs if q in v) if any(q in v for q in qs) else None  # noqa: E731
            table.append({"run": lab, "F": FMTS[F][1], "tipo": "3b" if lab.startswith("3b ") else "controllo",
                          "n": len(v), "all": m(order), "hard": m(hard), "easy": m(easy)})
        table.sort(key=lambda t: -t["all"])
        for key in ("hard", "easy"):
            for i, t in enumerate(sorted(table, key=lambda t: -t[key]), 1):
                t["pos_" + key] = i
        ws = bk.wb.create_sheet(f"Per {by}")
        for j, h in enumerate(heads, 1):
            c = ws.cell(row=1, column=j, value=h)
            c.font, c.fill, c.alignment = HB, bk.DARK, bk.CENTER
        for i, t in enumerate(table, 1):
            vals = [i, t["run"], t["F"], t["tipo"], t["n"], t["all"], t["hard"], t["easy"],
                    t["easy"] - t["hard"], t["pos_hard"], t["pos_easy"]]
            for j, x in enumerate(vals, 1):
                c = ws.cell(row=i + 1, column=j, value=round(x, 4) if isinstance(x, float) else x)
                c.font, c.fill = (BOLD if j == 6 else FN), fills[t["tipo"]]
                c.border = Border(bottom=THIN)
                c.alignment = Alignment(horizontal="left" if j in (2, 3, 4) else "center")
                if isinstance(x, float):
                    c.number_format = "+0.000;-0.000" if j == 9 else "0.000"
        for j, w in enumerate((10, 36, 15, 11, 10, 13, 16, 16, 13, 13, 13), 1):
            ws.column_dimensions[get_column_letter(j)].width = w
        ws.row_dimensions[1].height = 45
        ws.freeze_panes = "C2"
        ws.auto_filter.ref = f"A1:{get_column_letter(len(heads))}{len(table) + 1}"
        j = ORDERS[by]
        result[by] = (min(r[j] for r in ids if r[0] in hard), max(r[j] for r in ids if r[0] in easy))
    bk.notes([
        "Graduatoria di tutte le run sui 54 esercizi di validazione (Gemma 4 26B A4B QAT): i 6 prompt del passo 3b e i controlli oracle (solo analisi, voci 162-169).",
        "  Ordine: F1 sui 54 esercizi, decrescente. 'Posizione tra i difficili / facili' = posizione della run se la graduatoria si facesse solo su quella metà.",
        "  F1 = media degli F1 di classi, attributi, relazioni e generalizzazioni (evaluation/element_metrics.py, abbinamento rilassato), prima sulle ripetizioni valide di ogni esercizio (3 nel 3b, 1 nei controlli), poi sugli esercizi: ogni esercizio pesa uguale. Metrica NOSTRA: lo strumento dei relatori ha valutato solo il 3b.",
        f"  Metà più difficile / più facile: i 54 esercizi ordinati per difficoltà decrescente e divisi a metà (27 + 27). Flesch-Kincaid: metà difficile da {result['Flesch-Kincaid'][0]:.2f} in su, metà facile fino a {result['Flesch-Kincaid'][1]:.2f}. Grandezza (classi + relazioni del GT): metà difficile da {result['grandezza'][0]} elementi in su, metà facile fino a {result['grandezza'][1]}. A parità di valore decide l'altra difficoltà, poi il nome dell'esercizio. Primo foglio: la grandezza, difficoltà dominante.",
        "  Colore: azzurro = prompt del 3b (configurazioni reali); verde = controlli oracle, in cui l'esempio contiene la soluzione dell'esercizio, intera o in parte (non utilizzabili in un sistema reale: misurano un tetto).",
        "  static k2 ha 53 esercizi: AirTravel è uno dei due esempi fissi, quindi non ha questa condizione. Parziale e misti: PlantUML (voci 163-165) e compatto (voce 170).",
        "  Risposte non valide escluse: " + ("; ".join(f"{FMTS[F][1]} / {lab}: {k}" for (F, lab), k in invalid.items() if k) or "nessuna") + ".",
        ("  Run non ancora presenti: " + ", ".join(missing) + "." if missing else "  Tutte le run presenti."),
        "  Generato da experiments/build_results.py.",
    ], out)
    return {"runs": len(runs), "halves": result}


README = """# Risultati raccolti

Cartella generata da `experiments/build_results.py` (copie: gli originali restano in `data/results/`).
**Riassunto delle valutazioni: [`README_valutazioni.md`](README_valutazioni.md)** (scritto a mano, non rigenerato).
Tutti i risultati sono ESPLORATIVI (voce 154): l'analisi statistica la fanno i relatori con il loro script (voce 158).
Modello: Gemma 4 26B A4B QAT (LM Studio), istruzioni v5, temperatura 0,3.

## classifica_run.xlsx — graduatoria di tutte le run
I 6 prompt del 3b e i controlli oracle sui 54 di validazione, per F1 medio, con la media sulla meta' piu' difficile e
su quella piu' facile degli esercizi (fogli "Per grandezza" e "Per Flesch-Kincaid").

In tutti gli Excel il primo foglio ordina per GRANDEZZA, la difficolta' dominante (Spearman con la completezza circa
−0,45 contro circa −0,2 di Flesch-Kincaid); il secondo per Flesch-Kincaid.

## 1_passo3b — il passo 3b (79 esercizi, 6 prompt x 2 formati x 3 ripetizioni = 2.874 risposte)
- `passo3b_completezza.xlsx`: completezza dello strumento dei relatori per esercizio e prompt (PlantUML e compatto);
  foglio "Per grandezza" e foglio "Per Flesch-Kincaid" (esercizi ordinati per difficolta'); Note.
- `evaluation_summary_relatori.xlsx`: il file prodotto dallo strumento dei relatori (2026-10-19).
- `passo3b_risultati.zip`: tutte le risposte in JSON e PlantUML (sviluppo e validazione), i GT in PlantUML, i testi.
- `difficolta.csv`: difficolta' degli esercizi (Flesch-Kincaid e grandezza).

## 2_controlli_oracle — controlli solo analisi (54 di validazione, 1 ripetizione)
- `controlli_f1.xlsx`: F1 per esercizio di tutti i controlli, stesso ordinamento (grandezza, Flesch-Kincaid).
- `oracle_self.md` (voce 162): l'esercizio stesso come esempio.
- `oracle_partial.md` (voce 163): solo una parte delle classi dell'esercizio stesso: quanto deve essere simile un esempio.
- `oracle_mix.md` (voci 164-165): esempio vicino + esempi lontani; due meta' complementari.
- `oracle_attr.md` (voci 167 e 169): esempi senza attributi.
- `oracle_partial_compatto.md`, `oracle_mix_compatto.md` (voci 170-171): parziale e misti nel compatto.

## 3_sviluppo — analisi di sviluppo (piloti e dev set, fino alla voce 151)
Sommari delle prove usate per scegliere formato, istruzioni, k, retriever e modello.

Le decisioni e i numeri commentati sono in `docs/decisions.md`; lo stato in `docs/STATUS.md`.
"""


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--out", default=str(ROOT / "results"))
    args = a.parse_args(argv)
    out = Path(args.out)
    skipped = []
    for src, dst in COPIES + development_copies():
        if not src.exists():
            skipped.append(dst)
            continue
        (out / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out / dst)
    for old in OLD_OUTPUTS:
        (out / old).unlink(missing_ok=True)
    rows, gt = exercise_rows()
    i3 = build_3b(out / XLSX_3B, rows)
    ic = build_controls(out / XLSX_CTRL, rows, gt)
    ir = build_ranking(out / XLSX_RANK, rows, gt)
    print(f"{XLSX_RANK}: {ir['runs']} run")
    (out / "README.md").write_text(README, encoding="utf-8")
    print(f"scritto in {out}: {XLSX_3B} ({i3['rows']} esercizi, {i3['invalid']} non valide escluse), "
          f"{XLSX_CTRL} ({ic['rows']} esercizi)")
    if skipped:
        print("non ancora disponibili:", ", ".join(skipped))
    if ic["missing"]:
        print("run dei controlli mancanti (colonne vuote):", ", ".join(ic["missing"]))
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
