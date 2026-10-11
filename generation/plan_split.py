"""
Risposte con il "piano breve" (istruzioni v5plan, voce 126): PLAN prima, poi DIAGRAM. Il post-processing e la
validazione lavorano SOLO sulla parte che segue il marcatore "DIAGRAM:"; il piano si salva a parte. Se il marcatore manca
si valida l'intera risposta e il caso si conta (`found = False`). Per le risposte delle altre istruzioni non si usa.

Marcatore: la prima riga che inizia (dopo spazi ed eventuale enfasi Markdown `**` o `#`) con "DIAGRAM", seguita o no da
":" e da `**`; il diagramma comincia subito dopo il marcatore (sulla stessa riga o nelle successive).
"""

from __future__ import annotations

import re

MARKER_RE = re.compile(r"^[ \t]*(?:\*\*|#+[ \t]*)?DIAGRAM[ \t]*:?[ \t]*(?:\*\*)?[ \t]*", re.M)
PLAN_LABEL_RE = re.compile(r"^[ \t]*(?:\*\*|#+[ \t]*)?PLAN[ \t]*:?[ \t]*(?:\*\*)?[ \t]*", re.M)


def split_plan(text: str) -> tuple[str, str, bool]:
    """(piano, diagramma, marcatore trovato). Senza marcatore: ("", testo intero, False)."""
    text = text or ""
    m = MARKER_RE.search(text)
    if not m:
        return "", text, False
    plan = PLAN_LABEL_RE.sub("", text[:m.start()], count=1).strip()
    return plan, text[m.end():].lstrip("\n"), True


def plan_lines(plan: str) -> list[str]:
    return [x.strip() for x in plan.splitlines() if x.strip()]
