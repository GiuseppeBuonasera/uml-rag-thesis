"""
Smoke test MANUALE del server locale di LM Studio (Passo 3a, 2026-10-05). NON fa parte dei test automatici: lo esegue
l'utente con LM Studio aperto e un modello caricato. Solo prompt banali, nessun dato del corpus o del test set.

Uso:
    python experiments/smoke_lmstudio.py --list-models      # GET /v1/models, per leggere l'id esatto
    python experiments/smoke_lmstudio.py --model <id del modello in LM Studio> [--base-url http://localhost:1234/v1]

1. Risposta attesa: prompt che chiede di rispondere {"ok": true}; stampa risposta, modello, finish_reason, token
   riportati dal server e latenza.
2. Verifica del seed: un prompt banale con risposte variabili (inventare il nome di un gatto) inviato due volte con lo
   stesso seed (le risposte devono coincidere) e una volta con un seed diverso, prima con temperature 0.8 (caso
   significativo: senza seed due risposte uguali sono improbabili) e poi con temperature 0 (riportato, ma poco
   informativo: a temperature 0 le risposte tendono a coincidere comunque). Esito: "seed rispettato: si / no".
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "generation"))
from llm_client import GenerationParams, LMStudioClient  # noqa: E402
from postprocess import strip_reasoning  # noqa: E402

PROMPT_OK = 'Reply with exactly this JSON object and nothing else: {"ok": true}'
PROMPT_SEED = "Invent an unusual name for a cat and write one short sentence about it."
SEED, OTHER_SEED = 1234, 98765


def show(res) -> None:
    print(f"risposta      : {res.text!r}")
    print(f"modello       : {res.model}")
    print(f"finish_reason : {res.finish_reason}")
    print(f"token (server): prompt={res.prompt_tokens} completion={res.completion_tokens}")
    print(f"latenza       : {res.latency_s:.2f} s")


def seed_check(client: LMStudioClient, temperature: float) -> str:
    msgs = [{"role": "user", "content": PROMPT_SEED}]
    a = client.generate(msgs, GenerationParams(temperature=temperature, max_tokens=256, seed=SEED)).text
    b = client.generate(msgs, GenerationParams(temperature=temperature, max_tokens=256, seed=SEED)).text
    c = client.generate(msgs, GenerationParams(temperature=temperature, max_tokens=256, seed=OTHER_SEED)).text
    print(f"\n--- seed, temperature {temperature}")
    print(f"seed {SEED} (1): {a!r}")
    print(f"seed {SEED} (2): {b!r}")
    print(f"seed {OTHER_SEED}  : {c!r}")
    print(f"stesso seed -> risposte {'IDENTICHE' if a == b else 'DIVERSE'}; "
          f"seed diverso -> risposta {'uguale' if c == a else 'diversa'}")
    if a != b:
        verdict = "no"
    elif c != a:
        verdict = "si"
    else:
        verdict = "non determinabile (risposta uguale anche con seed diverso)"
    print(f"seed rispettato: {verdict}" + ("" if temperature > 0 else "   [temperature 0: poco informativo]"))
    return verdict


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="")
    ap.add_argument("--base-url", default="http://localhost:1234/v1")
    ap.add_argument("--list-models", action="store_true")
    a = ap.parse_args()
    if a.list_models or not a.model:
        with urllib.request.urlopen(f"{a.base_url.rstrip('/')}/models", timeout=30) as r:
            print(json.dumps(json.loads(r.read().decode("utf-8")), indent=2))
        if not a.model:
            print("\nIndica il modello con --model <id>.")
        return 0
    client = LMStudioClient(model=a.model, base_url=a.base_url, timeout_s=300, retries=1, backoff_s=1.0)

    print("--- 1. risposta attesa {\"ok\": true}")
    res = client.generate([{"role": "user", "content": PROMPT_OK}], GenerationParams(temperature=0.0, max_tokens=512))
    show(res)
    body, had_reasoning = strip_reasoning(res.text)
    try:
        ok = json.loads(body.strip()) == {"ok": True}
    except json.JSONDecodeError:
        ok = False
    print(f"ragionamento  : {'si' if had_reasoning else 'no'}")
    print(f"risposta attesa {{\"ok\": true}}: {'SI' if ok else 'NO'}")

    print("\n--- 2. verifica del seed")
    hot = seed_check(client, 0.8)
    cold = seed_check(client, 0.0)
    print(f"\nRIEPILOGO: seed rispettato (temperature 0.8): {hot}; (temperature 0, poco informativo): {cold}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
