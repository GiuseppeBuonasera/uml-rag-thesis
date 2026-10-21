# Controllo "esempio parzialmente simile" (oracle_partial) — SOLO ANALISI

PlantUML, 54 esercizi di validazione, Gemma 4 26B A4B QAT, configurazione del 3b, blocco esempi libero. Esempio = la traccia vera dell'esercizio con la soluzione ridotta al 25 / 50 / 75 % delle classi; 100 % = oracle_self. Regola registrata PRIMA della run (voce 163), applicata da `experiments/analyze_oracle_partial.py`.

Analisi eseguita sul commit `4ae4fd693032` (con modifiche non committate). GT del corpus: 60 diagrammi, sha256 del contenuto `b700693f7f421c5dae9aa1e0608efa90ce668a377bedd37deffb211d45986991` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `87f56f95414607b9…`.

## Curva: somiglianza dell'esempio → guadagno di completezza su zero_shot

| esempio | somiglianza (Jt) | risposte | guadagno medio |
|---|---|---|---|
| 3b, miglior esempio con Jt 0.00-0.10 | 0.00-0.10 | 499 | +0.008 |
| 3b, miglior esempio con Jt 0.10-0.20 | 0.10-0.20 | 120 | +0.014 |
| 3b, miglior esempio con Jt 0.20-0.30 | 0.20-0.30 | 161 | +0.022 |
| 3b, miglior esempio con Jt 0.30-0.45 | 0.30-0.45 | 27 | +0.039 |
| soluzione al 25% delle classi | 0.34 | 54 | +0.036 |
| soluzione al 50% delle classi | 0.56 | 54 | +0.095 |
| soluzione al 75% delle classi | 0.77 | 54 | +0.173 |
| esercizio stesso (oracle_self) | 1.00 | 54 | +0.337 |

**Esito (regola della voce 163): soglia di utilita' al livello 50% (somiglianza media 0.56): sotto, l'esempio non porta un guadagno di almeno 0.05.**

Guadagno = completezza della risposta − media dello stesso esercizio con zero_shot nel 3b; completezza = elementi del riferimento ritrovati / elementi del riferimento (classi + attributi + relazioni + generalizzazioni, abbinamento rilassato). Le fasce del 3b sono descrittive (esempi reali, non controllati).
