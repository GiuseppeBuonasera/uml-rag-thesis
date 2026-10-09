# Storico delle esecuzioni (ricostruito il 2026-10-09)

Comandi delle run e delle analisi fatte PRIMA del registro automatico (`data/results/run_log.jsonl`, voce 102). Dal
2026-10-09 ogni esecuzione degli script della pipeline si registra da sola; questo file non va più aggiornato a mano.

**Come è stato ricostruito.** Per ogni run di generazione si è confrontato il `config` salvato in
`data/results/generation/<run>/config.json` con il config attuale, risolto con la stessa `--configuration`
(`run_experiment.resolve_configuration`). Le date e i commit vengono dalla `provenance` della run (`started_at`,
`commit`, `worktree_dirty`); le riprese da `server_checks.jsonl` (una riga per ogni `--resume`, dal 2026-10-06) o da
decisions.md. Stato:
- **verificato**: il config attuale risolto è IDENTICO a quello salvato, quindi il comando riproduce esattamente la run;
- **ricostruito, non verificato**: comando dedotto da decisions.md / STATUS.md e dai file prodotti, senza un riscontro
  meccanico completo (il dettaglio non verificato è indicato).

Il percorso del config non è registrato nelle run (è registrato il contenuto): per tutte le run di generazione esiste un
solo config del repository con lo stesso `run_id` di base, e il confronto del contenuto lo conferma.

## Run di generazione

| run (cartella in data/results/generation/) | comando | avvio (provenance) | commit | modifiche non committate | stato | voce |
|---|---|---|---|---|---|---|
| `pilot_temperature_gemma4-12b-qat` | `python experiments/run_experiment.py experiments/configs/pilot_temperature.yaml`, poi lo stesso con `--resume` | 2026-10-06 13:36 (primo tentativo, fallito a contesto 8192); 36 risposte fino alle 14:55 | f171ace | no | verificato (config); la ripresa con `--resume` è da decisions.md (prima di `server_checks.jsonl`) | 75-77 |
| `pilot2_formats__J-Q` | `python experiments/run_experiment.py experiments/configs/pilot2_formats.yaml --configuration J-Q` | 2026-10-07 19:03 | 895a5cb | sì | verificato | 78, 85-86 |
| `pilot2_formats__J0-Q` | `... pilot2_formats.yaml --configuration J0-Q` | 2026-10-07 19:17 | 895a5cb | sì | verificato | 83 |
| `pilot2_formats__P-Q` | `... pilot2_formats.yaml --configuration P-Q` | 2026-10-07 19:31 | 895a5cb | sì | verificato | 78 |
| `pilot2_formats__J-G` | `... pilot2_formats.yaml --configuration J-G`, poi ripresa con `--resume` (1 riga in server_checks.jsonl) | 2026-10-08 03:06; fine 11:01 | 48f3763 | sì | verificato | 78, 87 |
| `pilot2_formats__P-G` | `... pilot2_formats.yaml --configuration P-G`, poi ripresa con `--resume` (1 riga in server_checks.jsonl) | 2026-10-08 10:40; fine 11:09 | 48f3763 | sì | verificato | 78, 87 |
| `dev_formats__P-G` | `python experiments/run_experiment.py experiments/configs/dev_formats.yaml --configuration P-G` | 2026-10-08 13:47 | 0d76c2b | sì | verificato | 92 |
| `dev_formats__C-G` | `... dev_formats.yaml --configuration C-G` | 2026-10-08 13:52 | 0d76c2b | sì | verificato | 92 |
| `dev_formats__P-Q` | `... dev_formats.yaml --configuration P-Q` | 2026-10-08 15:01 | 0d76c2b | sì | verificato | 92 |
| `dev_formats__C-Q` | `... dev_formats.yaml --configuration C-Q` | 2026-10-08 15:05 | 0d76c2b | sì | verificato | 92 |
| `dev_k__P-G` | `python experiments/run_experiment.py experiments/configs/dev_k.yaml --configuration P-G` | 2026-10-08 18:38 | e9645e2 | sì | verificato | 93-95 |
| `dev_k__C-G` | `... dev_k.yaml --configuration C-G` | 2026-10-08 19:02 | e9645e2 | sì | verificato | 93-95 |
| `dev_k__P-Q` | `... dev_k.yaml --configuration P-Q` | 2026-10-08 22:14 | e642465 | sì | verificato | 93-95 |
| `dev_k__C-Q` | `... dev_k.yaml --configuration C-Q` | 2026-10-08 22:32 | e642465 | sì | verificato | 93-95 |
| `dev_instructions__P-G` | `lms load google/gemma-4-12b-qat -c 32768 --parallel 4 --gpu max -y`, poi `python experiments/run_experiment.py experiments/configs/dev_instructions.yaml --configuration P-G` | 2026-10-09 12:50 | 3017a8c | sì | verificato (comandi lanciati dall'agente in questa sessione) | 98, 101 |
| `dev_instructions__C-G` | `... dev_instructions.yaml --configuration C-G` (subito dopo P-G, stesso modello caricato) | 2026-10-09 12:55 | 3017a8c | sì | verificato | 98, 101 |
| `mock_e2e_2026-10-05` (prova con MockClient, non versionata) | `python experiments/run_experiment.py experiments/configs/mock_e2e.yaml` | 2026-10-06 11:50 | a46012e | sì | verificato | 65-66 |

Le run di generazione sono state lanciate dall'utente salvo `dev_instructions` (lanciata dall'agente, voce 101).

## Calibrazioni dei token e smoke test (docs/smoke_tests/)

| file | comando | data | stato | voce |
|---|---|---|---|---|
| `2026-10-06_google-gemma-4-12b-qat_smoke1.txt`, `..._smoke2.txt` | `python experiments/smoke_lmstudio.py --model google/gemma-4-12b-qat` (senza `--save`; prove manuali con l'output incollato) | 2026-10-06 | ricostruito, non verificato (le flag esatte non sono registrate) | 71-74 |
| `2026-10-07_qwen-qwen2.5-coder-14b_smoke1.*` | `python experiments/smoke_lmstudio.py --model qwen/qwen2.5-coder-14b --save` | 2026-10-07 | verificato (intestazione del .txt) | 80 |
| `2026-10-07_qwen-qwen2.5-coder-14b_lmstudio-log_manuale.txt` | `python experiments/calibrate_tokens.py experiments/configs/pilot2_formats.yaml --configuration J-Q` (14B, interrotta) | 2026-10-07 | ricostruito, non verificato (prova manuale, voce 84) | 84 |
| `2026-10-07_qwen2.5-coder-7b-instruct_smoke1.*` | `python experiments/smoke_lmstudio.py --model qwen2.5-coder-7b-instruct --save` | 2026-10-07 | verificato (intestazione del .txt) | 86 |
| `2026-10-07_qwen2.5-coder-7b-instruct_calibration1.json` | `python experiments/calibrate_tokens.py experiments/configs/pilot2_formats.yaml --configuration J-Q` | 2026-10-07 19:03 | ricostruito, non verificato: la configurazione digitata non è registrata (J-Q, P-Q o J0-Q danno lo stesso calcolo: stesso modello, esercizi, k e formati predefiniti apollon e plantuml) | 78 |
| `2026-10-08_google-gemma-4-12b-qat_calibration1.json` | `... pilot2_formats.yaml --configuration J-G` (o P-G, stesso calcolo) | 2026-10-08 03:06 | ricostruito, non verificato (come sopra) | 87 |
| `2026-10-08_google-gemma-4-12b-qat_calibration2.json` | `python experiments/calibrate_tokens.py experiments/configs/dev_formats.yaml --configuration C-G --formats plantuml compact` | 2026-10-08 13:46 | ricostruito, non verificato (configurazione: C-G o P-G, stesso calcolo; formati verificati dal .json) | 92 |
| `2026-10-08_qwen2.5-coder-7b-instruct_calibration1.json` | `... dev_formats.yaml --configuration C-Q --formats plantuml compact` | 2026-10-08 15:01 | ricostruito, non verificato (come sopra) | 92 |
| `2026-10-08_google-gemma-4-12b-qat_calibration3.json` | `python experiments/calibrate_tokens.py experiments/configs/dev_k.yaml --configuration C-G --formats plantuml compact` | 2026-10-08 18:38 | ricostruito, non verificato (configurazione; k = 8 e versione 2 registrati nel .json) | 94 |
| `2026-10-08_qwen2.5-coder-7b-instruct_calibration2.json` | `... dev_k.yaml --configuration C-Q --formats plantuml compact` | 2026-10-08 22:14 | ricostruito, non verificato (come sopra) | 94 |

## Retrieval (data/results/retrieval/)

| run | comando | creata (UTC) | commit | stato | voce |
|---|---|---|---|---|---|
| `loo_2026-10-04_stop1` | `python retrieval/analyze_retrieval.py --run-id loo_2026-10-04_stop1` | 2026-10-04 09:45 | c161bab (modifiche non committate) | ricostruito, non verificato (run-id esplicito dal nome; `--seeds 20` = default, coerente con `random_seeds: 20` del config) | 58-59 |
| `testset_2026-10-04_stop2` | `python retrieval/run_testset.py --run-id testset_2026-10-04_stop2` | 2026-10-04 10:12 | c161bab (modifiche non committate) | ricostruito, non verificato (come sopra); **test set: si guarda una volta sola** | 60 |
| hubness (solo stampa) | `python retrieval/hubness_report.py` | 2026-10-05 | ricostruito, non verificato | 61 |

## Analisi e report (sola lettura delle run)

| report | comando | commit dichiarato nel report | stato | voce |
|---|---|---|---|---|
| `pilot_temperature_gemma4-12b-qat/summary.md` | `python experiments/analyze_pilot.py` | (il report non lo dichiara) | verificato: rigenerato identico il 2026-10-08 (ricognizione della riorganizzazione, poi annullata) | 77 |
| `pilot2_formats_analysis/summary.md` | `python experiments/analyze_pilot2.py` | 58896d0 (con modifiche) | verificato: rigenerato identico il 2026-10-08 salvo la riga del commit | 88-89 |
| `pilot2_formats_analysis_v2/summary.md` | `python experiments/analyze_pilot2.py --postprocess v2` | 58896d0 (con modifiche) | verificato: come sopra | 89 |
| `dev_formats_analysis/summary.md` | `python experiments/analyze_dev.py` | 0d76c2b (con modifiche) | verificato: rigenerato identico salvo la riga del commit (prima della correzione di eHome2020) | 92 |
| `dev_k_analysis/summary.md` | `python experiments/analyze_k.py` | 1f185be | verificato sul comando; rigenerato DOPO la correzione di eHome2020 (voce 99) differisce nel verso di eHome2020 | 94-95 |
| `dev_instructions_analysis/summary.md` | `python experiments/analyze_instructions.py` | 3017a8c (con modifiche) | verificato (lanciato dall'agente) | 101 |
| `dev_k_gemma_k3_review/index.html` (non versionato) | `python experiments/review_report.py --runs dev_k__P-G dev_k__C-G --filter k=3 --name dev_k_gemma_k3` | — | verificato (lanciato dall'agente) | 100 |
| selezioni (solo stampa) | `python experiments/select_pilot.py`; `python experiments/select_dev.py` | — | verificato: l'output coincide con `query_ids` dei config (test) | 75, 92 |

## Pipeline del corpus dopo il Passo 1

| quando | comandi | stato | voce |
|---|---|---|---|
| 2026-10-09 (correzione di eHome2020) | `python corpus/build_manifest.py`; `python corpus/apollon_convert.py`; `python corpus/diff_report.py` | verificato (lanciati dall'agente) | 99 |
