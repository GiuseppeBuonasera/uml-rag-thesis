# Insieme di sviluppo — validità del JSON compatto (varianti contro `dev_v5base` C-G, k = 3)

Esperimento di SVILUPPO (20 esercizi di sviluppo, pool unico), mai esercizi di valutazione. Gemma 4 12B QAT, istruzioni v4 del compatto. Regola registrata PRIMA della run (voce 119), applicata da `experiments/analyze_compact.py`. Le varianti con lo schema restano subordinate alla domanda 14 per i relatori.

Analisi eseguita sul commit `2b74319a3f11` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Regola (voce 119), applicata così com'è

Ammissibile se dM_primaria >= -0,03 e [(dVc >= +4 e dR >= -0,03) oppure (dR >= +0,03 e dVc >= -2)]; esclusa con 2 o più troncamenti; tra le ammissibili vince l'R più alto, entro 0,01 la più semplice (indent < schema < both).

- **indent**: AMMISSIBILE (dVc +5, dR +0.054, dM_primaria +0.058; guadagno di validità sì, di contenuto sì)
- **schema**: AMMISSIBILE (dVc +7, dR +0.040, dM_primaria +0.045; guadagno di validità sì, di contenuto sì)
- **both**: AMMISSIBILE (dVc +7, dR +0.074, dM_primaria +0.076; guadagno di validità sì, di contenuto sì)

**Esito: variante both (in parità: both).** Subordinata alla domanda 14 (generazione vincolata).

## Metriche

| run | V | Vc | J | R | M primaria | troncate | motivi di invalidità | completamento med | latenza med (s) |
|---|---|---|---|---|---|---|---|---|---|
| baseline (dev_v5base C-G) | 35/40 | 33/40 | 0.452 | 0.210 | 0.156 | 0 | {'incomplete_json': 2, 'invalid_json': 3} | 542 | 39.7 |
| indent (dev_cindent) | 40/40 | 38/40 | 0.539 | 0.264 | 0.214 | 0 | — | 778 | 20.4 |
| schema (dev_cschema) | 40/40 | 40/40 | 0.543 | 0.250 | 0.202 | 0 | — | 736 | 22.2 |
| both (dev_cboth) | 40/40 | 40/40 | 0.528 | 0.284 | 0.233 | 0 | — | 794 | 25.3 |
| riferimento: PlantUML v5 (dev_v5 P-G) | 40/40 | 38/40 | 0.540 | 0.361 | 0.317 | 0 | — | 218 | 8.0 |
