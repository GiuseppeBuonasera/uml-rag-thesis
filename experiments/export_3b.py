"""
Esportazione dei risultati del 3b per l'analisi statistica (2026-10-16). Sola lettura: nessuna chiamata a un LLM,
nessuna metrica nuova (evaluation/element_metrics.py, evaluation/metrics.py tramite review_report.response_metrics).

Uno zip con, per le quattro run passo3b__{P,C}-{corpus,testset}-G26 (1.938 risposte):
- risposte/<formato>/<split>/<esercizio>/<condizione>_r<ripetizione>.puml: il diagramma VALUTATO in PlantUML canonico
  (plantuml_format.apollon_to_plantuml, versione v5), cioe' la risposta dopo il post-processing e l'espansione in
  Apollon; per le risposte del compatto e' la loro conversione in PlantUML. Risposte non valide: nessun .puml;
- testo_originale/<formato>/<split>/<esercizio>/<condizione>_r<ripetizione>.(puml|json): il testo esatto del modello;
- gt/<esercizio>.puml: i diagrammi di riferimento nello stesso PlantUML canonico;
- risposte.csv: una riga per risposta con condizione, metriche (V, Vc, J, R, M primaria; P / R / F1 e TP / FP / FN per
  classi, attributi, relazioni e generalizzazioni con abbinamento esatto e rilassato), scheletro, token, latenza,
  esempi del prompt e loro somiglianza Jt all'esercizio;
- esercizi.csv: una riga per esercizio (split, dimensioni del GT, parole della traccia);
- LEGGIMI.md: descrizione dei file e delle colonne.

Uso:
    python experiments/export_3b.py [--out data/results/generation/export_3b/passo3b_plantuml.zip]
    python experiments/export_3b.py --insieme sviluppo     # i 26 di sviluppo: export_3b/passo3b_sviluppo_plantuml.zip
    python experiments/export_3b.py --unico                # 54 + 26 in un solo zip: export_3b/passo3b_risultati.zip
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "experiments"), str(ROOT / "generation"), str(ROOT / "retrieval"), str(ROOT)]
import review_report as rr  # noqa: E402
import compare_3b as c3  # noqa: E402
from evaluation import element_metrics as el  # noqa: E402
from evaluation import metrics as em  # noqa: E402
from plantuml_format import apollon_to_plantuml  # noqa: E402

OUT = rr.RESULTS / "export_3b" / "passo3b_plantuml.zip"
OUT_SVILUPPO = rr.RESULTS / "export_3b" / "passo3b_sviluppo_plantuml.zip"
FORMATS = {"P": "plantuml", "C": "compatto"}
SPLITS = {"corpus": "corpus", "testset": "debari"}
# insieme -> (run per formato e split: (prefisso della run, configurazione, nome dello split nell'export))
INSIEMI = {"valutazione": [("passo3b", f"{{f}}-{s}-{c3.MODEL}", n) for s, n in SPLITS.items()],
           "sviluppo": [("passo3b_sviluppo", f"{{f}}-sviluppo-{c3.MODEL}", "sviluppo")]}
TYPES = ("classes", "attributes", "relations", "generalizations")
TYPE_IT = {"classes": "classi", "attributes": "attributi", "relations": "relazioni", "generalizations": "generalizz"}


def cond_name(m: dict) -> str:
    return c3.label(m["condition"], m["k"]).replace(" ", "_")


def insieme_ids(insieme: str) -> list[str]:
    """valutazione: i 54 (passo3b.yaml); sviluppo: i 26 di corpus/roles.yaml (voce 151)."""
    if insieme == "valutazione":
        return c3.evaluation_ids()
    import yaml
    roles = yaml.safe_load((ROOT / "corpus" / "roles.yaml").read_text(encoding="utf-8"))
    return sorted((r["id"] for r in roles if r["role"] == "sviluppo"), key=str.lower)


def rows_and_files(results: Path = rr.RESULTS, insieme: str = "valutazione") -> tuple[list[dict], dict[str, str], list[dict]]:
    import corpus_loader as cl
    from prompt_builder import static_examples
    from relevance import Relevance
    recs = cl.load_candidates() + cl.load_queries()
    by_id = {c["id"]: c for c in recs}
    rel = Relevance(recs + static_examples(by_id)[:1])
    gt = {i: c["diagram_apollon_json"] for i, c in by_id.items()}
    ids = insieme_ids(insieme)
    files, rows = {}, []
    for q in ids:
        files[f"gt/{q}.puml"] = apollon_to_plantuml(gt[q], version="v5")
    for f, fname in FORMATS.items():
        for prefix, conf, sname in INSIEMI[insieme]:
            for c in rr.load_run(results / f"{prefix}__{conf.format(f=f)}", {}, gt):
                m = c["m"]
                base = f"{fname}/{sname}/{c['q']}/{cond_name(m)}_r{c['r']}"
                files[f"testo_originale/{base}.{'puml' if f == 'P' else 'json'}"] = c["raw"]["text"]
                valid = c["v"].level >= 3
                if valid:
                    files[f"risposte/{base}.puml"] = apollon_to_plantuml(c["v"].diagram, version="v5")
                rm = rr.response_metrics(c)
                ev = el.evaluate_call(c)
                jts = [rel.measure(c["q"], e)["Jt"] for e in m["example_ids"]]
                row = {"call_id": m["call_id"], "esercizio": c["q"], "split": sname, "formato": fname,
                       "condizione": m["condition"], "k": m["k"], "condizione_k": c3.label(m["condition"], m["k"]),
                       "ripetizione": c["r"], "livello": c["v"].level, "V": rm["V"], "Vc": rm["Vc"],
                       "troncata": int(bool(c["v"].truncated)), "scheletro": int(em.attribute_counts(c)["skeleton"]),
                       "J": rm["J"], "R": rm["R"], "M1": rm["M"]}
                for level in ("relaxed", "exact"):
                    lv = "ril" if level == "relaxed" else "esa"
                    for t in TYPES:
                        s, k = ev[level]["scores"][t], ev[level]["counts"][t]
                        for mm in ("P", "R", "F1"):
                            row[f"{mm}_{TYPE_IT[t]}_{lv}"] = s[mm]
                        for cc in ("tp", "fp", "fn"):
                            row[f"{cc}_{TYPE_IT[t]}_{lv}"] = k[cc]
                row.update({"token_output": m.get("completion_tokens_server"), "latenza_s": m.get("latency_s"),
                            "esempi": ";".join(m["example_ids"]),
                            "Jt_max_esempi": max(jts) if jts else None,
                            "Jt_medio_esempi": sum(jts) / len(jts) if jts else None,
                            "file_puml": f"risposte/{base}.puml" if valid else ""})
                rows.append(row)
    ex = []
    queries = {x["id"] for x in cl.load_queries()}
    for q in ids:
        e = el.elements(gt[q])
        ex.append({"esercizio": q, "split": "debari" if q in queries else "corpus" if insieme == "valutazione" else "sviluppo",
                   "classi_gt": len(e["classes"]), "attributi_gt": sum(len(v) for v in e["attributes"].values()),
                   "relazioni_gt": len(e["relations"]), "generalizz_gt": len(e["generalizations"]),
                   "parole_traccia": len(re.findall(r"\w+", by_id[q].get("description") or ""))})
    return rows, files, ex


def to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return buf.getvalue()


README_SVILUPPO = """# Risultati del passo 3b sui 26 esercizi di SVILUPPO — analisi SECONDARIA (voce 151)

Stessa configurazione del 3b principale (Gemma 4 26B A4B QAT, 6 condizioni, 3 ripetizioni, 2 formati) sui 26 esercizi
di sviluppo (20 del dev set + 6 dei piloti, tutti del corpus): 936 risposte, nessuna cella saltata. ATTENZIONE: la
configurazione e' stata scelta su questi esercizi misurando bm25; i risultati vanno riportati A PARTE dai 54 di
valutazione (zip passo3b_plantuml.zip), mai sommati nei test della domanda principale. `split` vale `sviluppo`.
Struttura dei file e colonne identiche allo zip dei 54, descritte qui sotto.

"""

README = """# Risultati del passo 3b — esportazione per l'analisi statistica

Gemma 4 26B A4B QAT (LM Studio), 54 esercizi di valutazione (34 del corpus + 20 De Bari), 6 condizioni
(zero_shot, static k2, random k3, bm25 k2, bm25 k3, hybrid k3), 3 ripetizioni, 2 formati di uscita (PlantUML, JSON
compatto): 1.938 risposte. La cella static di AirTravel non esiste (AirTravel e' uno dei due esempi fissi).

## File
- `risposte.csv`: una riga per risposta (1.938 righe). Unita' di analisi consigliata: l'ESERCIZIO (media delle 3
  ripetizioni per esercizio, condizione e formato), con confronti appaiati tra condizioni.
- `esercizi.csv`: una riga per esercizio (54 righe), per stratificazioni e covariate.
- `gt/<esercizio>.puml`: diagramma di riferimento in PlantUML canonico.
- `risposte/<formato>/<split>/<esercizio>/<condizione>_r<rip>.puml`: diagramma valutato, in PlantUML canonico (dopo
  post-processing ed espansione in Apollon). Per il compatto e' la conversione in PlantUML. Assente per le non valide.
- `testo_originale/...`: il testo esatto scritto dal modello (.puml per PlantUML, .json per il compatto).

## Colonne di risposte.csv
- `esercizio`, `split` (corpus / debari), `formato` (plantuml / compatto), `condizione`, `k`, `condizione_k`,
  `ripetizione` (0-2), `call_id`.
- `livello`: livello di validita' raggiunto (>= 3 = valida; -1 = chiamata fallita o testo non estraibile).
- `V` (1 = valida), `Vc` (1 = valida e senza scarti nel post-processing), `troncata` (1 = limite di 4096 token),
  `scheletro` (1 = valida senza nessun attributo per un GT che ne ha).
- `J`: Jaccard dei nomi di classe con il GT. `R`: relazioni del GT ritrovate con stesse due classi e stesso tipo /
  relazioni del GT. `M1`: estremi del GT con molteplicita' esplicita uguale nella risposta / estremi espliciti del GT
  (vuoto se il GT non ne ha). Metriche congelate (evaluation/metrics.py, voce 127).
- `P_<tipo>_<livello>`, `R_<tipo>_<livello>`, `F1_<tipo>_<livello>`: precision, recall, F1 per tipo di elemento
  (classi, attributi, relazioni strutturali, generalizzazioni) con abbinamento rilassato (`ril`) o esatto (`esa`)
  (evaluation/element_metrics.py, voce 136). Relazioni abbinate per coppia di classi, senza tipo ne' verso.
  `tp_`, `fp_`, `fn_`: i conteggi corrispondenti (per medie micro). Vuoto = non definito (es. P senza elementi).
- Una risposta NON valida conta 0 in J, R e nelle recall / F1 (diagramma vuoto); la sua precision e' vuota.
- `token_output`, `latenza_s`: costo della generazione. `esempi`: id degli esempi nel prompt, nell'ordine;
  `Jt_max_esempi`, `Jt_medio_esempi`: somiglianza (token dei nomi di classe) tra il GT dell'esercizio e quelli degli
  esempi. `file_puml`: percorso del diagramma nello zip.

## Metrica primaria proposta
F1 delle relazioni, abbinamento rilassato (`F1_relazioni_ril`), media per esercizio (da confermare, domanda 11).
"""


OUT_UNICO = rr.RESULTS / "export_3b" / "passo3b_risultati.zip"
CARTELLA = {"valutazione": "validazione", "sviluppo": "sviluppo"}

README_UNICO = """# Risultati del passo 3b — tutti gli 80 esercizi (54 di validazione + 26 di sviluppo)

Gemma 4 26B A4B QAT (LM Studio), 6 prompt (zero_shot, static k2, random k3, bm25 k2, bm25 k3, hybrid k3), 3
ripetizioni, 2 formati di uscita (PlantUML, JSON compatto): 2.874 risposte (1.938 sui 54 + 936 sui 26). La cella
static di AirTravel non esiste (AirTravel e' uno dei due esempi fissi).

- `validazione` = i 54 esercizi dell'analisi principale (34 del corpus + 20 De Bari), mai usati per le scelte;
- `sviluppo` = i 26 esercizi su cui e' stata scelta la configurazione (misurando bm25): analisi SECONDARIA, da
  riportare a parte (voce 151).

## Cartelle
- `risposte/puml/<insieme>/<esercizio>/<prompt>_r<rip>.puml`: risposte del formato PlantUML, testo esatto del modello.
- `risposte/json/<insieme>/<esercizio>/<prompt>_r<rip>.puml`: risposte del formato JSON compatto CONVERTITE in
  PlantUML canonico (il diagramma valutato, dopo il post-processing e l'espansione in Apollon). Le poche risposte
  compatte non valide non sono convertibili: restano come `.json`, il testo esatto del modello.
- Le metriche del CSV sono calcolate dopo il post-processing (conversione in Apollon), non su questi file grezzi.
- `gt/<esercizio>.puml`: diagramma di riferimento in PlantUML canonico; `gt/<esercizio>.txt`: traccia dell'esercizio
  (il testo dato al modello).
- `risposte.csv`: una riga per risposta, con le colonne `insieme` (validazione / sviluppo) e `file` (percorso della
  risposta nello zip). `esercizi.csv`: una riga per esercizio, con `insieme`.

"""


def main_unico(out: Path) -> int:
    import corpus_loader as cl
    by_id = {c["id"]: c for c in cl.load_candidates() + cl.load_queries()}
    rows, files, ex = [], {}, []
    for insieme, cart in CARTELLA.items():
        r, f, e = rows_and_files(insieme=insieme)
        for k, v in f.items():
            if k.startswith("gt/"):
                q = k[len("gt/"):-len(".puml")]
                files[k] = v
                files[f"gt/{q}.txt"] = (by_id[q].get("description") or "").strip() + "\n"
            elif k.startswith("testo_originale/") and k.endswith(".puml"):  # PlantUML: testo del modello
                _fmt, _split, q, name = k.split("/")[1:]
                files[f"risposte/puml/{cart}/{q}/{name}"] = v
            elif k.startswith("risposte/compatto/"):  # compatto valido: convertito in PlantUML canonico
                _split, q, name = k.split("/")[2:]
                files[f"risposte/json/{cart}/{q}/{name}"] = v
        for k, v in f.items():  # compatto NON valido: non convertibile, resta il JSON del modello
            if k.startswith("testo_originale/compatto/"):
                _split, q, name = k.split("/")[2:]
                if f"risposte/json/{cart}/{q}/{name[:-5]}.puml" not in files:
                    files[f"risposte/json/{cart}/{q}/{name}"] = v
        for row in r:
            folder = "puml" if row["formato"] == "plantuml" else "json"
            ext = "puml" if row["formato"] == "plantuml" or row["V"] else "json"
            name = cond_name({"condition": row["condizione"], "k": row["k"]})
            row = {"insieme": cart, **row}
            row.pop("file_puml", None)
            row["file"] = f"risposte/{folder}/{cart}/{row['esercizio']}/{name}_r{row['ripetizione']}.{ext}"
            rows.append(row)
        ex += [{"insieme": cart, **x} for x in e]
    missing = [r["file"] for r in rows if r["file"] not in files]
    assert not missing, missing[:3]
    columns = "## Colonne di risposte.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("LEGGIMI.md", README_UNICO + columns + README.split(columns, 1)[1])
        z.writestr("risposte.csv", to_csv(rows))
        z.writestr("esercizi.csv", to_csv(ex))
        for name, text in sorted(files.items()):
            z.writestr(name, text)
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(out)
    n_p = sum(k.startswith("risposte/puml/") for k in files)
    n_j = sum(k.startswith("risposte/json/") and k.endswith(".puml") for k in files)
    n_jr = sum(k.startswith("risposte/json/") and k.endswith(".json") for k in files)
    n_g = sum(k.startswith("gt/") and k.endswith(".puml") for k in files)
    print(f"scritto {out} ({out.stat().st_size / 1e6:.1f} MB): {len(rows)} risposte (PlantUML {n_p} .puml; compatto {n_j} convertite in .puml + {n_jr} non valide in .json), "
          f"{len(ex)} esercizi, {n_g} GT con traccia")
    return 0


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--unico", action="store_true", help="un solo zip con 54 + 26 (export_3b/passo3b_risultati.zip)")
    a.add_argument("--insieme", choices=tuple(INSIEMI), default="valutazione",
                   help="valutazione = i 54 (default); sviluppo = i 26 di sviluppo (analisi secondaria, voce 151)")
    a.add_argument("--out", help="zip di uscita (default: export_3b/passo3b[_sviluppo]_plantuml.zip)")
    args = a.parse_args(argv)
    if args.unico:
        return main_unico(Path(args.out or OUT_UNICO))
    rows, files, ex = rows_and_files(insieme=args.insieme)
    out = Path(args.out or (OUT if args.insieme == "valutazione" else OUT_SVILUPPO))
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("LEGGIMI.md", README if args.insieme == "valutazione" else README_SVILUPPO + README)
        z.writestr("risposte.csv", to_csv(rows))
        z.writestr("esercizi.csv", to_csv(ex))
        for name, text in sorted(files.items()):
            z.writestr(name, text)
    run_log = sys.modules.get("run_log")
    if run_log is not None:
        run_log.set_output(out)
    n_puml = sum(k.startswith("risposte/") for k in files)
    print(f"scritto {out} ({out.stat().st_size / 1e6:.1f} MB): {len(rows)} risposte ({n_puml} diagrammi .puml), "
          f"{len(ex)} esercizi, {sum(k.startswith('gt/') for k in files)} GT")
    return 0


if __name__ == "__main__":
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
