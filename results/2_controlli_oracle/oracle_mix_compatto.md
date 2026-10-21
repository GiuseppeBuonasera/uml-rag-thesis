# Controllo "piu' esempi insieme" (oracle_mix) — SOLO ANALISI

JSON compatto, 54 esercizi di validazione, Gemma 4 26B A4B QAT, configurazione del 3b, blocco esempi libero. Regola registrata PRIMA della run (voce 164; compatto: voce 170), applicata da `experiments/analyze_oracle_mix.py`.

Analisi eseguita sul commit `4ae4fd693032` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Guadagno di completezza su zero_shot (media per esercizio)

| esempi nel prompt | guadagno |
|---|---|
| soluzione al 50 % da sola (oracle_partial) | +0.109 |
| 2 esempi bm25 + soluzione al 50 % (diluito) | +0.127 |
| soluzione al 50 % + meta' complementare (complemento) | +0.182 |
| esercizio intero (oracle_self, libero) | +0.264 |

## Esito (regola della voce 164)

- **Diluizione: nessuna diluizione** (diluito − 50 % = +0.018, Wilcoxon p 0.297, 54 esercizi; margine 0.03)
- **Somma: le due meta' si sommano in parte** (complemento − 50 % = +0.073, p 0.000; complemento − 100 % = -0.082, p 0.000)

Guadagno = completezza (elementi del riferimento ritrovati / elementi del riferimento) − media dello stesso esercizio con zero_shot nel 3b.
