"""
Stato di avanzamento delle generazioni (2026-10-12, voce 132), in sola lettura: legge i manifest delle run mentre
girano (il runner aggiunge una riga per chiamata) e lo stato del batch (experiments/run_batch.py).

Per ogni run: chiamate fatte / attese (dal piano del runner, celle saltate escluse), livelli di validita', troncamenti,
risposte con ragionamento, latenza mediana, ultima chiamata. In totale: percentuale e stima del tempo residuo (chiamate
mancanti × latenza mediana delle chiamate fatte, per run; per le run non ancora iniziate la mediana globale).

Uso:
    python experiments/progress.py <nome del batch>
    (dal notebook: print(progress.report(nome)) oppure progress.watch(nome))
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
import run_batch  # noqa: E402


def expected_calls(config: str, configuration: str | None) -> int:
    import run_experiment as rx
    cfg = rx.resolve_configuration(yaml.safe_load(run_batch.resolve(config).read_text(encoding="utf-8")), configuration)
    candidates, test_queries = rx.cl.load_all()
    queries = test_queries if cfg.get("split", "testset") == "testset" else candidates
    return len(rx.plan(cfg, queries))


def run_status(out: Path, expected: int) -> dict:
    mpath = out / "manifest.jsonl"
    rows = [json.loads(x) for x in mpath.read_text(encoding="utf-8").splitlines() if x] if mpath.exists() else []
    lat = [r["latency_s"] for r in rows if r.get("latency_s") is not None and not r.get("cached")]
    return {"run": out.name, "fatte": len(rows), "attese": expected,
            "livelli": dict(sorted(Counter(r["level"] for r in rows).items())),
            "valide_L3": sum(r["level"] >= 3 for r in rows),
            "troncate": sum(r.get("finish_reason") == "length" for r in rows),
            "ragionamento": sum(bool(r.get("reasoning_field") or r.get("reasoning_markers_in_content")) for r in rows),
            "latenza_mediana": statistics.median(lat) if lat else None,
            "ultima": rows[-1]["timestamp"] if rows else None}


def status(name: str) -> dict:
    d = run_batch.BATCH_DIR / name
    st = json.loads((d / "stato.json").read_text(encoding="utf-8"))
    results = Path(st.get("risultati") or run_batch.RESULTS)
    runs = []
    for item in st["runs"]:
        out = run_batch.run_dir(item["config"], item["configurazione"], results)
        runs.append({**run_status(out, expected_calls(item["config"], item["configurazione"])),
                     "esito": item["esito"]})
    lats = [r["latenza_mediana"] for r in runs if r["latenza_mediana"]]
    glob = statistics.median(lats) if lats else None
    remaining = sum(max(r["attese"] - r["fatte"], 0) * (r["latenza_mediana"] or glob or 0) for r in runs)
    done, total = sum(r["fatte"] for r in runs), sum(r["attese"] for r in runs)
    return {"nome": name, "pid": st.get("pid"), "vivo": run_batch.alive(st.get("pid")) and st.get("finito") is None,
            "avviato": st.get("avviato"), "finito": st.get("finito"), "corrente": st.get("corrente"),
            "fatte": done, "attese": total, "residuo_s": remaining if glob else None, "runs": runs,
            "stop_richiesto": (d / "STOP").exists()}


def hms(s: float | None) -> str:
    if s is None:
        return "—"
    s = int(s)
    return f"{s // 3600} h {s % 3600 // 60:02d} min"


def report(name: str) -> str:
    s = status(name)
    pct = 100 * s["fatte"] / s["attese"] if s["attese"] else 0.0
    bar = "#" * int(pct // 2.5) + "." * (40 - int(pct // 2.5))
    state = ("IN CORSO" if s["vivo"] else "FINITO" if s["finito"] else "FERMO (processo non attivo: rilanciare per "
             "riprendere)")
    L = [f"Batch {name}: {state}{' — STOP richiesto' if s['stop_richiesto'] else ''} (pid {s['pid']}, avviato "
         f"{s['avviato']}{', finito ' + s['finito'] if s['finito'] else ''})",
         f"[{bar}] {s['fatte']}/{s['attese']} ({pct:.1f} %), tempo residuo stimato {hms(s['residuo_s'])}"
         + (f", run corrente {s['corrente']}" if s["corrente"] else ""), "",
         f"{'run':<34} {'fatte':>11} {'valide':>7} {'tronc.':>6} {'ragion.':>7} {'lat. med.':>9}  livelli  esito"]
    for r in s["runs"]:
        lat = f"{r['latenza_mediana']:.1f} s" if r["latenza_mediana"] else "—"
        L.append(f"{r['run']:<34} {r['fatte']:>5}/{r['attese']:<5} {r['valide_L3']:>7} {r['troncate']:>6} "
                 f"{r['ragionamento']:>7} {lat:>9}  {r['livelli']}  {r['esito']}")
    return "\n".join(L)


def watch(name: str, every_s: int = 60, max_minutes: int = 60) -> None:
    """Aggiorna lo stato nel notebook ogni every_s secondi, finche' il batch gira (al massimo max_minutes)."""
    import time
    from IPython.display import clear_output
    for _ in range(max(1, max_minutes * 60 // every_s)):
        clear_output(wait=True)
        text = report(name)
        print(text)
        if "IN CORSO" not in text.splitlines()[0]:
            break
        time.sleep(every_s)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(report(sys.argv[1]))
