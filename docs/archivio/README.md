# docs/archivio — materiale concluso, conservato per tracciabilità

File che non fanno più parte della pipeline, spostati qui il 2026-10-04 (riordino del repository prima del
Passo 2) invece di essere eliminati. La loro storia è conservata da git (`git log --follow <file>`).

| File | Percorso originale | Cosa era | Perché è qui |
|---|---|---|---|
| `_generate_roles_to_review.py` | `corpus/_generate_roles_to_review.py` | Script una tantum, sola lettura, che estraeva da `corpus/label_classification.md` le etichette classificate come ruolo da rivedere (criteri A/B/C) | La revisione dei ruoli si è chiusa il 2026-09-28 (vedi `docs/decisions.md`). **Lo script non è più eseguibile da qui**: carica `_generate_label_classification.py` per percorso, dalla propria cartella, e quel file è stato rinominato in `corpus/generate_label_classification.py`; legge inoltre `corpus/label_classification.md` con un percorso relativo alla radice. |
| `roles_to_review.md` | `corpus/roles_to_review.md` | Output dello script sopra: tabella delle etichette-ruolo da rivedere, con i criteri | Documento della revisione del 2026-09-28; le decisioni che ne sono seguite sono in `corpus/generate_label_classification.py` (CLASSIFICATION) e in `docs/decisions.md`. |
