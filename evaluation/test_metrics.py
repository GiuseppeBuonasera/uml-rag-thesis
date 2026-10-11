"""
Test delle metriche congelate per il 3b (evaluation/metrics.py, voce 127), nello stile degli altri test: script, non
pytest. Nessuna chiamata a un LLM; data/results/ non viene scritto.

1. Le funzioni degli script storici SONO quelle di evaluation/metrics.py (riesportazione, non copie).
2. Un esempio calcolato a mano (J, R, R_fam, M primaria / secondaria, verso, generalizzazioni invertite, classi /
   generalizzazioni / composizioni in piu').
3. Ricalcolo di TUTTE le analisi di sviluppo versionate (pilota, pilota 2 e sue v2, formati, k, istruzioni, v5,
   compatto, pool, retriever, struttura, esempi) su una copia temporanea dei file versionati delle run: ogni summary.md
   rigenerato deve essere identico, riga per riga, a quello versionato (stessa cifra), salvo la riga di provenienza
   (commit e working tree).

Uso:
    python evaluation/test_metrics.py
"""

from __future__ import annotations

import contextlib
import importlib
import io
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "experiments"), str(ROOT / "generation")]
from evaluation import metrics as em  # noqa: E402

RESULTS = ROOT / "data" / "results" / "generation"
PROVENANCE = "Analisi eseguita sul commit"
# (script, argomenti dopo la cartella dei risultati, cartella del summary); None = script senza --results-dir
ANALYSES = (("analyze_pilot", None, "pilot_temperature_gemma4-12b-qat"),
            ("analyze_pilot2", [], "pilot2_formats_analysis"),
            ("analyze_pilot2", ["--postprocess", "v2"], "pilot2_formats_analysis_v2"),
            ("analyze_dev", [], "dev_formats_analysis"),
            ("analyze_k", [], "dev_k_analysis"),
            ("analyze_instructions", [], "dev_instructions_analysis"),
            ("analyze_v5", [], "dev_v5_analysis"),
            ("analyze_compact", [], "dev_compact_analysis"),
            ("analyze_pool", [], "dev_pool_analysis"),
            ("analyze_retrievers", [], "dev_retrievers_analysis"),
            ("analyze_struct", [], "dev_struct_analysis"),
            ("analyze_examples", None, "dev_examples_analysis"))


def check_reexports() -> None:
    import analyze_dev as ad
    import analyze_instructions as ai
    import analyze_pilot as ap
    import analyze_v5 as av
    same = {ap.norm: em.norm, ap.class_names: em.class_names, ap.norm_mult: em.norm_mult, ap.edges: em.edges,
            ap.compare_relations: em.compare_relations, ad.is_valid: em.is_valid, ad.is_clean: em.is_clean,
            ad.metrics: em.core_metrics, ai.match: em.match, ai.gt_ends: em.gt_ends, ai.resp_mult: em.resp_mult,
            ai.multiplicity_counts: em.multiplicity_counts, ai.metrics: em.multiplicity_metrics,
            ai.confusion: em.confusion, av.r_fam: em.r_fam, av.extra_compositions: em.extra_compositions,
            av.all_metrics: em.all_metrics}
    assert all(a is b for a, b in same.items())
    assert (ap.DIRECTIONAL, ap.PART_WHOLE, ai.NO_MULT, ai.ORIENTED, ai.SHORT, av.FAMILY_SWAPS) == (
        em.DIRECTIONAL, em.PART_WHOLE, em.NO_MULT, em.ORIENTED, em.SHORT, em.FAMILY_SWAPS)
    print("  OK  gli script storici riesportano le funzioni di evaluation/metrics.py (stessi oggetti)")


def _diagram(classes, rels) -> dict:
    nodes = [{"id": n, "data": {"name": n}} for n in classes]
    edges = [{"source": s, "target": t, "type": ty, "data": {"sourceMultiplicity": sm, "targetMultiplicity": tm}}
             for s, t, ty, sm, tm in rels]
    return {"nodes": nodes, "edges": edges}


def check_by_hand() -> None:
    gt = _diagram(["Order", "Customer", "Item", "Person"],
                  [("Customer", "Order", "ClassBidirectional", "1", "0..*"),
                   ("Order", "Item", "ClassComposition", "1", "1..n"),
                   ("Customer", "Person", "ClassInheritance", "", ""),
                   ("Order", "Person", "ClassBidirectional", "", "1")])
    resp = _diagram(["order", "Customer", "Item", "Person", "Cart"],
                    [("Customer", "order", "ClassUnidirectional", "1", "*"),  # R_fam si', R no; M: 1 e * uguali
                     ("order", "Item", "ClassComposition", "1", "1..*"),  # R si'; M: 1 e 1..* uguali
                     ("Person", "Customer", "ClassInheritance", "", ""),  # R si', generalizzazione invertita
                     ("Cart", "Item", "ClassComposition", "1", "*")])  # composizione e classe in piu'
    v = lambda d, level=4: SimpleNamespace(level=level, diagram=d, truncated=False, P1_clean=True)  # noqa: E731
    calls = [{"v": v(resp), "gt": gt, "m": {"latency_s": 2.0}, "format": "plantuml"},
             {"v": v(None, level=2), "gt": gt, "m": {"latency_s": 4.0}, "format": "plantuml"}]  # non valida: 0
    m = em.all_metrics(calls)
    assert (m["n"], m["V"], m["Vc"]) == (2, 1, 1)
    assert abs(m["J"] - (4 / 5) / 2) < 1e-12 and abs(m["J_valid"] - 4 / 5) < 1e-12
    assert m["gt_edges_all"] == 8 and m["R"] == 2 / 8 and m["R_valid"] == 2 / 4 and m["R_fam"] == 3 / 8
    # estremi espliciti del GT per risposta: 1, 0..*, 1, 1..n, 1 (Order-Person ha un estremo vuoto) = 5, x 2 risposte
    assert m["mult_counts"]["explicit"] == 10 and m["mult_counts"]["explicit_same"] == 4 and m["M1"] == 4 / 10
    assert m["mult_counts"]["all"] == 12 and m["M2"] == 4 / 12
    assert m["inv_gen"] == 1 and m["inv_gen_tot"] == 1 and m["dir"] == "1/2"  # composizione ok, generalizzazione no
    assert (m["extra_cls"], m["extra_gen"], m["extra_comp"]) == (1, 1, 1) and m["latency_median"] == 3.0
    assert em.norm_mult(" 0..N ") == "*" and em.norm_mult("1..1") == "1" and em.norm_mult(None) == ""
    print("  OK  esempio a mano: V, Vc, J, R, R_fam, M primaria / secondaria, verso, generalizzazioni invertite, "
          "classi / generalizzazioni / composizioni in piu'")


def check_versioned_analyses() -> None:
    """Ogni analisi di sviluppo versionata, rigenerata dai file versionati delle run, coincide con il suo summary.md."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "generation"
        # solo cio' che e' versionato (.gitignore): niente summary.md, prompts/, parsed/, cache/
        shutil.copytree(RESULTS, copy, ignore=shutil.ignore_patterns("summary.md", "prompts", "parsed", "cache"))
        for mod_name, extra, name in ANALYSES:
            mod = importlib.import_module(mod_name)
            out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
            with contextlib.redirect_stdout(out):
                if mod_name == "analyze_pilot":
                    mod.main(["--run", str(copy / name)])
                elif extra is None:  # analyze_examples: percorsi come costanti del modulo
                    old = mod.RESULTS, mod.OUT
                    mod.RESULTS, mod.OUT = copy, copy / name
                    try:
                        mod.main()
                    finally:
                        mod.RESULTS, mod.OUT = old
                else:
                    mod.main(["--results-dir", str(copy), *extra])
            lines = lambda p: [x for x in p.read_text(encoding="utf-8").splitlines() if PROVENANCE not in x]  # noqa: E731
            new, ref = lines(copy / name / "summary.md"), lines(RESULTS / name / "summary.md")
            diff = [i for i, (a, b) in enumerate(zip(new, ref)) if a != b]
            assert new == ref, f"{name}: {len(new)} righe contro {len(ref)}, prima differenza alla riga {diff[:1]}"
    print(f"  OK  {len(ANALYSES)} analisi versionate rigenerate con evaluation/metrics.py: identiche ai summary.md "
          "(salvo la riga di provenienza)")


def main() -> None:
    print("Metriche congelate (voce 127):")
    check_reexports()
    check_by_hand()
    check_versioned_analyses()
    print("Tutti i test delle metriche sono passati.")


if __name__ == "__main__":
    main()
