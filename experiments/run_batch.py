"""
Esecuzione IN SEQUENZA di una lista di run, pensata per girare in background (2026-10-12, voce 132). Nessuna logica
nuova: per ogni voce (config, configurazione) chiama experiments/run_experiment.py, con --resume se la cartella della
run esiste gia' (riprende dalle chiamate mancanti; le risposte gia' ottenute restano in cache e nel manifest).

Stato e log in data/results/batch/<nome>/:
  stato.json   pid, avvio, elenco delle run, run corrente, esito di ciascuna, fine
  batch.log    output del runner (lo scrive il processo lanciato da launch())
  STOP         se esiste, il batch si ferma PRIMA della run successiva (la run in corso finisce)
Per interrompere subito: stop() termina il processo (le chiamate gia' fatte restano; si riprende rilanciando).

Uso:
    python experiments/run_batch.py <nome> <config>::<configurazione> [...] [--results-dir DIR]
    (dal notebook: launch(nome, [(config, configurazione), ...]) e stop(nome))
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
BATCH_DIR = ROOT / "data" / "results" / "batch"
RESULTS = ROOT / "data" / "results" / "generation"
SEP = "::"


def resolve(config: str) -> Path:
    """Percorso di un config: relativo alla radice del repo se non assoluto (il notebook gira in notebooks/)."""
    p = Path(config)
    return p if p.is_absolute() else ROOT / p


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def run_dir(config: str, configuration: str | None, results: Path = RESULTS) -> Path:
    import run_experiment as rx
    cfg = rx.resolve_configuration(yaml.safe_load(resolve(config).read_text(encoding="utf-8")), configuration)
    return results / cfg["run_id"]


def write_state(d: Path, state: dict) -> None:
    tmp = d / "stato.json.tmp"
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(d / "stato.json")


def run_all(name: str, entries: list[tuple[str, str | None]], results: Path = RESULTS) -> int:
    import run_experiment as rx
    d = BATCH_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "STOP").unlink(missing_ok=True)
    state = {"nome": name, "pid": os.getpid(), "avviato": now(), "risultati": str(results), "corrente": None,
             "runs": [{"config": c, "configurazione": k, "esito": "in attesa"} for c, k in entries], "finito": None}
    write_state(d, state)
    code = 0
    for item in state["runs"]:
        if (d / "STOP").exists():
            item["esito"] = "non avviata (STOP)"
            continue
        out = run_dir(item["config"], item["configurazione"], results)
        argv = [str(resolve(item["config"])), "--results-dir", str(results)]
        if item["configurazione"]:
            argv += ["--configuration", item["configurazione"]]
        if (out / "config.json").exists():
            argv.append("--resume")
        state["corrente"] = out.name
        item.update(esito="in corso", inizio=now())
        write_state(d, state)
        print(f"[{now()}] {out.name}: python experiments/run_experiment.py {' '.join(argv)}", flush=True)
        try:
            rx.main(argv)
            item["esito"] = "completata"
        except SystemExit as e:  # rifiuti del runner (guardie, ragionamento, contesto...): il batch si ferma
            item["esito"] = f"FERMATA: {e}"
            code = 1
        except Exception as e:  # noqa: BLE001 - errore di rete o del server: si registra e ci si ferma
            item["esito"] = f"ERRORE: {type(e).__name__}: {e}"
            code = 1
        item["fine"] = now()
        write_state(d, state)
        print(f"[{now()}] {out.name}: {item['esito']}", flush=True)
        if code:
            break
    state.update(corrente=None, finito=now())
    write_state(d, state)
    return code


def launch(name: str, entries: list[tuple[str, str | None]], results: Path = RESULTS) -> int:
    """Avvia il batch in un processo separato (sopravvive al kernel del notebook); ritorna il pid."""
    d = BATCH_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    st = d / "stato.json"
    if st.exists():
        prev = json.loads(st.read_text(encoding="utf-8"))
        if prev.get("finito") is None and alive(prev.get("pid")):
            raise SystemExit(f"batch {name} gia' in corso (pid {prev['pid']})")
    args = [sys.executable, str(ROOT / "experiments" / "run_batch.py"), name,
            *[f"{c}{SEP}{k or ''}" for c, k in entries], "--results-dir", str(results)]
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
    log = (d / "batch.log").open("a", encoding="utf-8")
    proc = subprocess.Popen(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, creationflags=flags,
                            env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return proc.pid


def alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        import psutil
        return psutil.pid_exists(pid) and psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
    except ImportError:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout
            return str(pid) in out
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def stop(name: str, now_: bool = False) -> str:
    """Ferma il batch: dopo la run corrente (STOP) oppure subito (termina il processo)."""
    d = BATCH_DIR / name
    (d / "STOP").write_text(now(), encoding="utf-8")
    if not now_:
        return "il batch si fermera' alla fine della run in corso"
    pid = json.loads((d / "stato.json").read_text(encoding="utf-8")).get("pid")
    if not alive(pid):
        return "nessun processo in corso"
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        os.kill(pid, 15)
    return f"processo {pid} terminato: si riprende rilanciando lo stesso batch (--resume automatico)"


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("nome")
    a.add_argument("runs", nargs="+", help=f"<config>{SEP}<configurazione> (configurazione vuota se la config non ne ha)")
    a.add_argument("--results-dir", default=str(RESULTS))
    args = a.parse_args(argv)
    entries = [(r.split(SEP)[0], r.split(SEP)[1] or None) if SEP in r else (r, None) for r in args.runs]
    return run_all(args.nome, entries, Path(args.results_dir))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import run_log  # registro delle esecuzioni (voce 102)
    with run_log.logged(__file__):
        sys.exit(main())
