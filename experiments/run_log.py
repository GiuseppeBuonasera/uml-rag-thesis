"""
Registro automatico delle esecuzioni (2026-10-09, voce 102): ogni script della pipeline, quando e' lanciato da riga di
comando, appende DUE righe a data/results/run_log.jsonl (versionato): una all'inizio e una alla fine, con lo stesso
`id`. Solo logging: nessun cambiamento al comportamento degli script (un errore del registro produce un avviso su
stderr e basta; i test, che chiamano main() direttamente, non scrivono nel registro).

Campi: event (start / end), id, timestamp, script, argv e comando completo, cwd, commit git e flag "working tree
sporco", resume (--resume nel comando), sha256 dei file di configurazione usati (config_bm25.yaml, template e blocco
delle istruzioni in generation/templates/, ogni .yaml / .yml del comando), output (cartella o file prodotto, se lo
script la dichiara con set_output); alla fine: durata in secondi, status ("ok", "exit <codice>", "interrupted"
(KeyboardInterrupt), "error: <tipo>") e il messaggio di uscita di SystemExit, se testuale.

Uso negli script:
    if __name__ == "__main__":
        with run_log.logged(__file__):
            sys.exit(main())
e, dove l'uscita e' nota, run_log.set_output(percorso) dentro main() (nessun effetto se il registro non e' attivo).
Percorso del registro: RUN_LOG_PATH (variabile d'ambiente) o data/results/run_log.jsonl.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = ROOT / "data" / "results" / "run_log.jsonl"
ALWAYS = (ROOT / "retrieval" / "config_bm25.yaml",)
TEMPLATES = ROOT / "generation" / "templates"
_active: dict | None = None


def log_path() -> Path:
    return Path(os.environ.get("RUN_LOG_PATH") or DEFAULT_LOG)


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


def config_hashes(argv: list[str]) -> dict[str, str]:
    """sha256 dei file di configurazione: sempre config_bm25 e i template delle istruzioni, piu' i .yaml del comando."""
    files = [*ALWAYS, *sorted(TEMPLATES.glob("*")), *(Path(a) for a in argv if a.endswith((".yaml", ".yml")))]
    out = {}
    for f in files:
        p = f if f.is_absolute() else (Path.cwd() / f)
        if p.is_file():
            out[_rel(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _write(entry: dict) -> None:
    try:
        path = log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:  # il registro non deve mai cambiare l'esito dello script
        print(f"[run_log] avviso: registro non scritto ({e})", file=sys.stderr)


def set_output(path) -> None:
    """Dichiara la cartella o il file prodotto dall'esecuzione in corso (nessun effetto senza registro attivo)."""
    if _active is not None:
        _active["output"] = _rel(Path(path))


@contextlib.contextmanager
def logged(script: str, argv: list[str] | None = None, event_prefix: str = ""):
    """Scrive la riga di inizio, esegue il blocco, scrive la riga di fine con durata e status; rilancia sempre
    l'eccezione o il SystemExit originale (comportamento invariato)."""
    global _active
    argv = list(sys.argv if argv is None else argv)
    started = time.time()
    entry = {"event": f"{event_prefix}start", "id": uuid.uuid4().hex, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "script": _rel(Path(script)), "argv": argv, "command": " ".join(["python", *argv]),
             "cwd": str(Path.cwd()), "commit": _git("rev-parse", "HEAD"),
             "worktree_dirty": bool(_git("status", "--porcelain")), "resume": "--resume" in argv,
             "config_sha256": config_hashes(argv), "output": None}
    _active = entry
    _write(entry)
    status, message = "ok", None
    try:
        yield entry
    except SystemExit as e:
        code = e.code
        status = "ok" if code in (0, None) else f"exit {code if isinstance(code, int) else 1}"
        message = code if isinstance(code, str) else None
        raise
    except KeyboardInterrupt:
        status = "interrupted"
        raise
    except BaseException as e:
        status = f"error: {type(e).__name__}"
        message = str(e)[:500]
        raise
    finally:
        _active = None
        _write({"event": f"{event_prefix}end", "id": entry["id"], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "script": entry["script"], "command": entry["command"], "output": entry["output"],
                "duration_s": round(time.time() - started, 3), "status": status, "message": message})
