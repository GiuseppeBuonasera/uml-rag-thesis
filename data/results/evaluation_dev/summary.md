# Metriche per elemento sulle run di sviluppo (P / R / F1, abbinamento esatto e rilassato)

Voce 136 di `docs/decisions.md`. SOLO DESCRITTIVO: risposte già salvate, nessuna generazione, nessun esercizio di valutazione; `evaluation/metrics.py`, gli script di analisi e i loro summary.md invariati. Generato da `evaluation/evaluate_dev.py` con `evaluation/element_metrics.py`.

Analisi eseguita sul commit `df38da2bd2bf` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

Definizioni nel modulo: classi abbinate uno a uno (esatto: nome normalizzato; rilassato: poi stesso insieme di token stemmati); attributi dentro le classi abbinate; relazioni strutturali senza verso; generalizzazioni con verso. Macro = media per esercizio (prima sulle ripetizioni); risposta non valida = diagramma vuoto (R 0, F1 0, P esclusa dalla media).

## 1. F1 macro per esercizio, abbinamento RILASSATO (con J e R attuali)

| run | formato | condizione | k | nota | risposte (non valide) | J | F1 classi | F1 attributi | R | F1 relazioni | F1 generalizz. | rho(F1 rel., R) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dev_v5 | PlantUML | bm25 | 3 | v5 | 40 (0) | 0.540 | 0.678 | 0.361 | 0.361 | 0.419 | 0.470 | 0.51 |
| dev_v5 | compatto | bm25 | 3 | v5 | 40 (10) | 0.371 | 0.485 | 0.275 | 0.193 | 0.242 | 0.303 | 0.67 |
| dev_c5indent | compatto | bm25 | 3 | v5 + indentati | 40 (1) | 0.536 | 0.668 | 0.330 | 0.307 | 0.362 | 0.423 | 0.71 |
| dev_v5base | PlantUML | bm25 | 3 | v4 | 40 (0) | 0.532 | 0.673 | 0.353 | 0.321 | 0.395 | 0.228 | 0.57 |
| dev_v5base | compatto | bm25 | 3 | v4 | 40 (5) | 0.452 | 0.576 | 0.257 | 0.210 | 0.316 | 0.381 | 0.59 |
| dev_retrievers | PlantUML | dense | 3 | v4, pool storico | 40 (0) | 0.532 | 0.673 | 0.336 | 0.327 | 0.400 | 0.186 | 0.58 |
| dev_retrievers | PlantUML | hybrid | 3 | v4, pool storico | 40 (0) | 0.543 | 0.678 | 0.362 | 0.330 | 0.385 | 0.316 | 0.66 |
| dev_retrievers | PlantUML | oracle_jt | 3 | v4, pool storico | 40 (0) | 0.543 | 0.677 | 0.338 | 0.324 | 0.412 | 0.102 | 0.66 |
| dev_retrievers | compatto | dense | 3 | v4, pool storico | 40 (4) | 0.476 | 0.604 | 0.276 | 0.256 | 0.327 | 0.409 | 0.60 |
| dev_retrievers | compatto | hybrid | 3 | v4, pool storico | 40 (2) | 0.496 | 0.628 | 0.337 | 0.250 | 0.368 | 0.382 | 0.60 |
| dev_retrievers | compatto | oracle_jt | 3 | v4, pool storico | 40 (2) | 0.481 | 0.613 | 0.294 | 0.244 | 0.346 | 0.377 | 0.66 |
| dev_k | PlantUML | bm25 | 2 | v4, pool storico | 40 (0) | 0.542 | 0.680 | 0.347 | 0.312 | 0.394 | 0.261 | 0.53 |
| dev_k | PlantUML | bm25 | 3 | v4, pool storico | 40 (0) | 0.544 | 0.678 | 0.346 | 0.307 | 0.400 | 0.225 | 0.61 |
| dev_k | PlantUML | bm25 | 5 | v4, pool storico | 40 (0) | 0.548 | 0.684 | 0.346 | 0.298 | 0.393 | 0.265 | 0.64 |
| dev_k | PlantUML | bm25 | 8 | v4, pool storico | 40 (0) | 0.541 | 0.681 | 0.347 | 0.321 | 0.393 | 0.320 | 0.48 |
| dev_k | compatto | bm25 | 2 | v4, pool storico | 40 (5) | 0.457 | 0.579 | 0.259 | 0.210 | 0.327 | 0.347 | 0.56 |
| dev_k | compatto | bm25 | 3 | v4, pool storico | 40 (1) | 0.529 | 0.665 | 0.304 | 0.310 | 0.384 | 0.449 | 0.59 |
| dev_k | compatto | bm25 | 5 | v4, pool storico | 40 (1) | 0.521 | 0.658 | 0.300 | 0.287 | 0.380 | 0.496 | 0.53 |
| dev_k | compatto | bm25 | 8 | v4, pool storico | 40 (3) | 0.495 | 0.626 | 0.297 | 0.270 | 0.351 | 0.399 | 0.57 |
| dev_cindent | compatto | bm25 | 3 | v4 + indentati | 40 (0) | 0.539 | 0.678 | 0.323 | 0.264 | 0.381 | 0.463 | 0.50 |
| dev_cschema | compatto | bm25 | 3 | v4 + schema | 40 (0) | 0.543 | 0.679 | 0.330 | 0.250 | 0.383 | 0.457 | 0.45 |
| dev_cboth | compatto | bm25 | 3 | v4 + entrambi | 40 (0) | 0.528 | 0.671 | 0.324 | 0.284 | 0.390 | 0.464 | 0.51 |
| dev_structP | PlantUML | construct | 3 | v5 | 40 (0) | 0.532 | 0.672 | 0.344 | 0.344 | 0.407 | 0.407 | 0.51 |
| dev_structP | PlantUML | struct | 3 | v5 | 40 (0) | 0.536 | 0.678 | 0.364 | 0.364 | 0.404 | 0.416 | 0.52 |
| dev_structP | PlantUML | struct_construct | 3 | v5 | 40 (0) | 0.534 | 0.678 | 0.335 | 0.349 | 0.394 | 0.446 | 0.45 |
| dev_structC | compatto | construct | 3 | v4 | 40 (0) | 0.545 | 0.682 | 0.319 | 0.276 | 0.397 | 0.463 | 0.53 |
| dev_structC | compatto | struct | 3 | v4 | 40 (0) | 0.530 | 0.671 | 0.305 | 0.278 | 0.375 | 0.458 | 0.45 |
| dev_structC | compatto | struct_construct | 3 | v4 | 40 (0) | 0.530 | 0.670 | 0.304 | 0.273 | 0.367 | 0.427 | 0.45 |
| dev_g26 | PlantUML | bm25 | 3 | v5, 26B | 40 (1) | 0.546 | 0.675 | 0.338 | 0.347 | 0.411 | 0.503 | 0.61 |
| dev_g26 | compatto | bm25 | 3 | v5 + indentati, 26B | 40 (2) | 0.554 | 0.675 | 0.344 | 0.344 | 0.417 | 0.521 | 0.68 |

## 2. Esatto contro rilassato (F1 macro) e precision / recall rilassati

| run | formato | condizione | k | F1 classi es. / ril. | F1 attributi es. / ril. | F1 relazioni es. / ril. | P / R classi | P / R relazioni | P / R generalizz. |
|---|---|---|---|---|---|---|---|---|---|
| dev_v5 | PlantUML | bm25 | 3 | 0.678 / 0.678 | 0.360 / 0.361 | 0.419 / 0.419 | 0.691 / 0.683 | 0.426 / 0.431 | 0.553 / 0.528 |
| dev_v5 | compatto | bm25 | 3 | 0.485 / 0.485 | 0.275 / 0.275 | 0.242 / 0.242 | 0.638 / 0.505 | 0.329 / 0.258 | 0.509 / 0.319 |
| dev_c5indent | compatto | bm25 | 3 | 0.668 / 0.668 | 0.330 / 0.330 | 0.362 / 0.362 | 0.712 / 0.663 | 0.378 / 0.371 | 0.549 / 0.476 |
| dev_v5base | PlantUML | bm25 | 3 | 0.673 / 0.673 | 0.351 / 0.353 | 0.395 / 0.395 | 0.677 / 0.688 | 0.389 / 0.423 | 0.278 / 0.271 |
| dev_v5base | compatto | bm25 | 3 | 0.576 / 0.576 | 0.257 / 0.257 | 0.316 / 0.316 | 0.671 / 0.593 | 0.377 / 0.336 | 0.575 / 0.444 |
| dev_retrievers | PlantUML | dense | 3 | 0.673 / 0.673 | 0.333 / 0.336 | 0.400 / 0.400 | 0.680 / 0.688 | 0.395 / 0.419 | 0.239 / 0.219 |
| dev_retrievers | PlantUML | hybrid | 3 | 0.678 / 0.678 | 0.361 / 0.362 | 0.385 / 0.385 | 0.702 / 0.678 | 0.397 / 0.392 | 0.386 / 0.333 |
| dev_retrievers | PlantUML | oracle_jt | 3 | 0.677 / 0.677 | 0.337 / 0.338 | 0.412 / 0.412 | 0.697 / 0.680 | 0.416 / 0.427 | 0.121 / 0.128 |
| dev_retrievers | compatto | dense | 3 | 0.604 / 0.604 | 0.275 / 0.276 | 0.327 / 0.327 | 0.657 / 0.635 | 0.356 / 0.350 | 0.435 / 0.528 |
| dev_retrievers | compatto | hybrid | 3 | 0.628 / 0.628 | 0.337 / 0.337 | 0.368 / 0.368 | 0.658 / 0.650 | 0.407 / 0.373 | 0.445 / 0.486 |
| dev_retrievers | compatto | oracle_jt | 3 | 0.613 / 0.613 | 0.292 / 0.294 | 0.346 / 0.346 | 0.641 / 0.639 | 0.363 / 0.373 | 0.409 / 0.444 |
| dev_k | PlantUML | bm25 | 2 | 0.680 / 0.680 | 0.347 / 0.347 | 0.394 / 0.394 | 0.685 / 0.697 | 0.389 / 0.417 | 0.370 / 0.295 |
| dev_k | PlantUML | bm25 | 3 | 0.678 / 0.678 | 0.346 / 0.346 | 0.400 / 0.400 | 0.681 / 0.695 | 0.399 / 0.420 | 0.309 / 0.240 |
| dev_k | PlantUML | bm25 | 5 | 0.684 / 0.684 | 0.346 / 0.346 | 0.393 / 0.393 | 0.693 / 0.693 | 0.399 / 0.410 | 0.351 / 0.292 |
| dev_k | PlantUML | bm25 | 8 | 0.681 / 0.681 | 0.344 / 0.347 | 0.393 / 0.393 | 0.693 / 0.687 | 0.395 / 0.411 | 0.402 / 0.337 |
| dev_k | compatto | bm25 | 2 | 0.579 / 0.579 | 0.259 / 0.259 | 0.327 / 0.327 | 0.636 / 0.612 | 0.365 / 0.337 | 0.460 / 0.455 |
| dev_k | compatto | bm25 | 3 | 0.665 / 0.665 | 0.304 / 0.304 | 0.384 / 0.384 | 0.665 / 0.699 | 0.372 / 0.424 | 0.512 / 0.528 |
| dev_k | compatto | bm25 | 5 | 0.658 / 0.658 | 0.300 / 0.300 | 0.380 / 0.380 | 0.671 / 0.672 | 0.395 / 0.390 | 0.588 / 0.542 |
| dev_k | compatto | bm25 | 8 | 0.626 / 0.626 | 0.297 / 0.297 | 0.351 / 0.351 | 0.681 / 0.634 | 0.386 / 0.353 | 0.491 / 0.465 |
| dev_cindent | compatto | bm25 | 3 | 0.678 / 0.678 | 0.322 / 0.323 | 0.381 / 0.381 | 0.690 / 0.685 | 0.386 / 0.393 | 0.556 / 0.540 |
| dev_cschema | compatto | bm25 | 3 | 0.679 / 0.679 | 0.330 / 0.330 | 0.383 / 0.383 | 0.692 / 0.684 | 0.388 / 0.389 | 0.491 / 0.542 |
| dev_cboth | compatto | bm25 | 3 | 0.671 / 0.671 | 0.321 / 0.324 | 0.390 / 0.390 | 0.677 / 0.683 | 0.387 / 0.404 | 0.567 / 0.542 |
| dev_structP | PlantUML | construct | 3 | 0.672 / 0.672 | 0.343 / 0.344 | 0.407 / 0.407 | 0.673 / 0.687 | 0.407 / 0.425 | 0.468 / 0.528 |
| dev_structP | PlantUML | struct | 3 | 0.678 / 0.678 | 0.361 / 0.364 | 0.404 / 0.404 | 0.682 / 0.690 | 0.400 / 0.427 | 0.481 / 0.528 |
| dev_structP | PlantUML | struct_construct | 3 | 0.678 / 0.678 | 0.332 / 0.335 | 0.394 / 0.394 | 0.684 / 0.687 | 0.390 / 0.419 | 0.521 / 0.528 |
| dev_structC | compatto | construct | 3 | 0.682 / 0.682 | 0.317 / 0.319 | 0.397 / 0.397 | 0.684 / 0.696 | 0.404 / 0.407 | 0.513 / 0.540 |
| dev_structC | compatto | struct | 3 | 0.671 / 0.671 | 0.303 / 0.305 | 0.375 / 0.375 | 0.679 / 0.677 | 0.381 / 0.380 | 0.494 / 0.542 |
| dev_structC | compatto | struct_construct | 3 | 0.670 / 0.670 | 0.302 / 0.304 | 0.367 / 0.367 | 0.676 / 0.682 | 0.366 / 0.381 | 0.458 / 0.542 |
| dev_g26 | PlantUML | bm25 | 3 | 0.675 / 0.675 | 0.338 / 0.338 | 0.411 / 0.411 | 0.716 / 0.667 | 0.410 / 0.431 | 0.731 / 0.476 |
| dev_g26 | compatto | bm25 | 3 | 0.675 / 0.675 | 0.344 / 0.344 | 0.417 / 0.417 | 0.729 / 0.659 | 0.418 / 0.433 | 0.722 / 0.507 |

## 3. Relazioni strutturali abbinate (rilassato, micro) e medie micro

| run | formato | condizione | k | abbinate | stesso tipo | stessa famiglia | molteplicità uguali (tutti / espliciti) | verso | generalizz. invertite | F1 micro classi / relazioni | P escluse (relazioni) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dev_v5 | PlantUML | bm25 | 3 | 122 | 0.713 | 0.787 | 0.631 / 0.770 | 1.000 | 0 | 0.670 / 0.409 | 0 |
| dev_v5 | compatto | bm25 | 3 | 73 | 0.603 | 0.767 | 0.575 / 0.689 | 1.000 | 0 | 0.545 / 0.274 | 10 |
| dev_c5indent | compatto | bm25 | 3 | 105 | 0.695 | 0.790 | 0.629 / 0.753 | 1.000 | 0 | 0.668 / 0.367 | 1 |
| dev_v5base | PlantUML | bm25 | 3 | 119 | 0.681 | 0.765 | 0.580 / 0.708 | 1.000 | 14 | 0.665 / 0.382 | 0 |
| dev_v5base | compatto | bm25 | 3 | 96 | 0.438 | 0.583 | 0.396 / 0.528 | 1.000 | 0 | 0.615 / 0.338 | 5 |
| dev_retrievers | PlantUML | dense | 3 | 121 | 0.702 | 0.802 | 0.579 / 0.722 | 1.000 | 14 | 0.662 / 0.397 | 0 |
| dev_retrievers | PlantUML | hybrid | 3 | 112 | 0.732 | 0.821 | 0.603 / 0.750 | 1.000 | 8 | 0.674 / 0.379 | 0 |
| dev_retrievers | PlantUML | oracle_jt | 3 | 123 | 0.699 | 0.772 | 0.581 / 0.715 | 1.000 | 17 | 0.673 / 0.401 | 0 |
| dev_retrievers | compatto | dense | 3 | 99 | 0.505 | 0.636 | 0.505 / 0.638 | 1.000 | 0 | 0.632 / 0.348 | 4 |
| dev_retrievers | compatto | hybrid | 3 | 100 | 0.500 | 0.720 | 0.565 / 0.673 | 1.000 | 0 | 0.630 / 0.362 | 2 |
| dev_retrievers | compatto | oracle_jt | 3 | 104 | 0.481 | 0.635 | 0.380 / 0.500 | 1.000 | 0 | 0.629 / 0.355 | 2 |
| dev_k | PlantUML | bm25 | 2 | 115 | 0.652 | 0.713 | 0.565 / 0.685 | 1.000 | 15 | 0.664 / 0.370 | 0 |
| dev_k | PlantUML | bm25 | 3 | 120 | 0.675 | 0.783 | 0.571 / 0.706 | 1.000 | 10 | 0.667 / 0.384 | 0 |
| dev_k | PlantUML | bm25 | 5 | 113 | 0.699 | 0.814 | 0.593 / 0.736 | 1.000 | 4 | 0.671 / 0.366 | 0 |
| dev_k | PlantUML | bm25 | 8 | 113 | 0.699 | 0.779 | 0.628 / 0.780 | 1.000 | 12 | 0.674 / 0.369 | 0 |
| dev_k | compatto | bm25 | 2 | 94 | 0.415 | 0.617 | 0.436 / 0.594 | 1.000 | 0 | 0.608 / 0.341 | 5 |
| dev_k | compatto | bm25 | 3 | 118 | 0.585 | 0.695 | 0.441 / 0.553 | 1.000 | 0 | 0.669 / 0.388 | 1 |
| dev_k | compatto | bm25 | 5 | 111 | 0.541 | 0.640 | 0.464 / 0.592 | 1.000 | 0 | 0.660 / 0.380 | 1 |
| dev_k | compatto | bm25 | 8 | 101 | 0.574 | 0.653 | 0.460 / 0.596 | 1.000 | 0 | 0.647 / 0.367 | 3 |
| dev_cindent | compatto | bm25 | 3 | 112 | 0.464 | 0.571 | 0.464 / 0.591 | 1.000 | 0 | 0.674 / 0.379 | 0 |
| dev_cschema | compatto | bm25 | 3 | 110 | 0.427 | 0.582 | 0.455 / 0.570 | 1.000 | 0 | 0.672 / 0.380 | 0 |
| dev_cboth | compatto | bm25 | 3 | 115 | 0.504 | 0.617 | 0.491 / 0.614 | 1.000 | 0 | 0.669 / 0.395 | 0 |
| dev_structP | PlantUML | construct | 3 | 118 | 0.686 | 0.763 | 0.614 / 0.763 | 1.000 | 0 | 0.660 / 0.387 | 0 |
| dev_structP | PlantUML | struct | 3 | 120 | 0.733 | 0.800 | 0.621 / 0.768 | 1.000 | 0 | 0.667 / 0.397 | 0 |
| dev_structP | PlantUML | struct_construct | 3 | 117 | 0.709 | 0.778 | 0.598 / 0.753 | 1.000 | 0 | 0.667 / 0.380 | 0 |
| dev_structC | compatto | construct | 3 | 116 | 0.483 | 0.595 | 0.461 / 0.582 | 1.000 | 0 | 0.677 / 0.391 | 0 |
| dev_structC | compatto | struct | 3 | 110 | 0.518 | 0.664 | 0.464 / 0.593 | 1.000 | 0 | 0.667 / 0.379 | 0 |
| dev_structC | compatto | struct_construct | 3 | 110 | 0.500 | 0.673 | 0.423 / 0.541 | 1.000 | 0 | 0.664 / 0.370 | 0 |
| dev_g26 | PlantUML | bm25 | 3 | 118 | 0.737 | 0.831 | 0.653 / 0.802 | 1.000 | 0 | 0.677 / 0.406 | 1 |
| dev_g26 | compatto | bm25 | 3 | 114 | 0.728 | 0.860 | 0.675 / 0.739 | — | 0 | 0.679 / 0.408 | 2 |

## 4. Rispetto a J e R

- Rilassato contro esatto: F1 delle classi +0.000 in media (da +0.000 a +0.000); F1 delle relazioni +0.000 (da +0.000 a +0.000).
- Correlazione per esercizio tra F1 delle relazioni (rilassato) e R, gruppo per gruppo (n = 20): mediana 0.57, da 0.45 a 0.71.
- R è una recall rigida (stessa coppia di nomi esatti E stesso tipo, sulle relazioni del GT); F1 delle relazioni non chiede il tipo e premia anche la precisione (relazioni in più penalizzate).

## 5. Regole passate con F1 delle relazioni (rilassato, macro) al posto di R — SOLO descrittivo

Le funzioni di decisione degli script storici richiamate così come sono, con R sostituita in memoria. Gli esiti registrati in `docs/decisions.md` NON cambiano.

- voce 92, formati (dev_formats): stesso esito (`.pooled.winner` = plantuml; `.pooled.decided_by` = Vc; `.per_model.G.winner` = plantuml)
- voce 94, k (dev_k): stesso esito (`.formats.plantuml.outcome` = k = 2; `.formats.compact.outcome` = STOP: dipende dal modello (Gemma k = 3, Qwen k = 2): decisione dell'utente)
- voce 98, istruzioni mirate (dev_instructions): stesso esito (`.formats.plantuml.adopt` = False; `.formats.plantuml.outcome` = NON adottate; `.formats.compact.adopt` = False)
- voce 111/118, istruzioni v5 (dev_v5): stesso esito (`.formats.plantuml.adopt` = True; `.formats.plantuml.outcome` = v5 ADOTTATA; `.formats.compact.adopt` = False)
- **voce 119/121, validita' del compatto (dev_cindent / cschema / cboth): esito DIVERSO** — `.winner`: both → indent
- voce 121/122, varianti del retriever (dev_struct*): stesso esito (`.winner` = None)
- voce 123/124, compatto v5 + indent e pool (dev_c5indent, dev_poolC): stesso esito (`.A.adopt` = True)
- voce 132/133, modello 26B (dev_g26): stesso esito (`.formats.plantuml.ok` = True; `.formats.compact.ok` = True; `.outcome` = 26B ADOTTATO come modello del Passo 3b (non inferiore in entrambi i formati, stima entro le 30 ore))

Note: la regola di esclusione dei retriever (voce 110) non usa R e non è ricalcolata; dev_k, dev_instructions e dev_retrievers usavano il pool storico di 58 candidati.
