# Pilota sulla temperatura — `pilot_temperature_gemma4-12b-qat`

> **Rigenerato il 2026-10-09 dopo la correzione del GT di eHome2020 (voce 99; rigenerazione: voce 105).** Cambia solo la colonna esplorativa "esempi: token" di ApartmentBuilding (4.382 -> 4.379; eHome2020 e' tra i suoi esempi e la dimensione si ricalcola dal corpus attuale: i prompt effettivamente inviati nel 2026-10-06 contenevano il GT precedente). Esito della regola della voce 75 invariato.

**Esperimento PRELIMINARE** sul corpus (split `corpus`, selezione leave-one-out), mai sul test set: da dichiarare come tale in tesi. Regola di decisione registrata PRIMA della run (docs/decisions.md, voce 75) e applicata cosi' com'e'. Generato da `experiments/analyze_pilot.py` dalle risposte grezze (`raw/`).

Modello `google/gemma-4-12b-qat` (QAT (q4_0)), contesto 32768, enable_thinking False; bm25 k=2; top_p 0.95, top_k 64, max_tokens 12288; 36 risposte (6 esercizi × 2 temperature × 3 ripetizioni). Ragionamento nelle risposte: no.

## Validita'

Risposte (su 18 per temperatura) che superano ciascun livello (cumulativo).

| temperatura | L0 estratto | L1 JSON | L2 schema | L3 integrita' | L4 stile | troncate (length) |
|---|---|---|---|---|---|---|
| 0 | 8 | 6 | 6 | 5 | 5 | 6 |
| 0.3 | 14 | 13 | 12 | 8 | 8 | 3 |

Esiti di fallimento (`failure`) per temperatura:

- 0: incomplete_json 4, integrity 1, invalid_json 2, nessuno (L4) 5, truncated 6
- 0.3: incomplete_json 1, integrity 4, invalid_json 1, nessuno (L4) 8, schema 1, truncated 3

Per esercizio (livello raggiunto da ciascuna ripetizione, r0 / r1 / r2; −1 = nessun JSON estratto):

| esercizio | t = 0 | t = 0.3 |
|---|---|---|
| Louvre | -1 (length) / -1 / -1 | 4 / 0 / 4 |
| Sober | 0 / -1 / -1 | 1 / -1 (length) / -1 (length) |
| StudentAppointment | 4 / 2 / 4 | -1 / 4 / 4 |
| CardGameApp | 0 / -1 (length) / -1 (length) | 2 / -1 (length) / 2 |
| ApartmentBuilding | 4 / 4 / 4 | 4 / 4 / 4 |
| FilmSet | -1 (length) / -1 (length) / -1 (length) | 2 / 4 / 2 |

Risposte troncate (finish_reason = length): nodi e relazioni scritti prima del tetto (conteggio testuale delle chiavi `"type": "class"` e `"sourceHandle"`), contro il ground truth:

| chiamata | caratteri | nodi | relazioni | GT nodi | GT relazioni |
|---|---|---|---|---|---|
| CardGameApp__bm25__k2__t0__r1 | 25909 | 11 | 63 | 13 | 13 |
| CardGameApp__bm25__k2__t0__r2 | 25909 | 11 | 63 | 13 | 13 |
| CardGameApp__bm25__k2__t0.3__r1 | 25347 | 14 | 59 | 13 | 13 |
| FilmSet__bm25__k2__t0__r0 | 26359 | 12 | 49 | 12 | 13 |
| FilmSet__bm25__k2__t0__r1 | 25149 | 12 | 45 | 12 | 13 |
| FilmSet__bm25__k2__t0__r2 | 25149 | 12 | 45 | 12 | 13 |
| Louvre__bm25__k2__t0__r0 | 24501 | 12 | 55 | 7 | 7 |
| Sober__bm25__k2__t0.3__r1 | 23753 | 9 | 54 | 9 | 10 |
| Sober__bm25__k2__t0.3__r2 | 30285 | 10 | 80 | 9 | 10 |

Diagnostici (non metriche; non si combinano con L0-L4): risposte con almeno un diagnostico, tra quelle che superano L1.

| temperatura | formato della risposta | layout |
|---|---|---|
| 0 | nessuno | nessuno |
| 0.3 | nessuno | out_of_canvas 1, overlapping_nodes 1 |

## Variabilita' tra ripetizioni

Jaccard medio dei nomi di classe tra le coppie di ripetizioni (solo coppie in cui entrambe superano L1; tra parentesi le coppie usate su 3) e coppie identiche byte per byte (testo grezzo, su 3).

| esercizio | t = 0: Jaccard tra ripetizioni | t = 0: identiche | t = 0.3: Jaccard tra ripetizioni | t = 0.3: identiche |
|---|---|---|---|---|
| Louvre | — (0) | 1/3 (r1=r2) | 0.636 (1) | 0/3 |
| Sober | — (0) | 1/3 (r1=r2) | — (0) | 0/3 |
| StudentAppointment | 1.000 (3) | 0/3 | 1.000 (1) | 0/3 |
| CardGameApp | — (0) | 1/3 (r1=r2) | 0.714 (1) | 0/3 |
| ApartmentBuilding | 1.000 (3) | 1/3 (r1=r2) | 1.000 (3) | 0/3 |
| FilmSet | — (0) | 1/3 (r1=r2) | 1.000 (3) | 0/3 |

A temperature 0 la coppia identica e' r1 = r2 in 5 esercizi su 6; r0 differisce sempre. Le tre ripetizioni sono consecutive (seed 42, 43, 44, che a temperature 0 non dovrebbero contare). Ipotesi NON verificata: r0 e' la prima valutazione del prompt, r1 e r2 riusano la cache del prompt di LM Studio (percorso numerico diverso).

## Qualita' approssimata: Jaccard dei nomi di classe con il ground truth

Solo risposte che superano L1; media per esercizio (tra parentesi le risposte usate su 3).

| esercizio | t = 0 | t = 0.3 |
|---|---|---|
| Louvre | — (0) | 0.390 (2) |
| Sober | — (0) | 0.133 (1) |
| StudentAppointment | 0.571 (3) | 0.571 (2) |
| CardGameApp | — (0) | 0.429 (2) |
| ApartmentBuilding | 1.000 (3) | 1.000 (3) |
| FilmSet | — (0) | 0.714 (3) |

## Tempi e token di output

| temperatura | latenza s (min / mediana / max) | token di completamento (min / mediana / max) | totale token di completamento |
|---|---|---|---|
| 0 | 36.7 / 81.8 / 289.6 | 1397 / 3621 / 12288 | 109881 |
| 0.3 | 44.7 / 93.1 / 280.2 | 2036 / 4237 / 12288 | 92023 |

Durata complessiva delle generazioni: 76.0 minuti.

## Regola di decisione (voce 75), applicata cosi' com'e'

| temperatura | V = risposte che superano L0-L3 | J = Jaccard medio con il GT (risposte L1) | risposte L1 | troncate |
|---|---|---|---|---|
| 0 | 5/18 | 0.786 | 6 | 6 |
| 0.3 | 8/18 | 0.620 | 13 | 3 |

**Esito: STOP: nessuna decisione (controllo preliminare)**
- temperature 0: 6 risposte troncate su 18 (soglia: piu' di 1)
- temperature 0.3: 3 risposte troncate su 18 (soglia: piu' di 1)

## ESPLORATIVO — non usato per decidere

### Relazioni rispetto al ground truth (risposte che superano L1)

Accoppiamento 1:1 per coppia di classi non ordinata (nomi normalizzati, case-insensitive), prima le relazioni dello stesso tipo. Verso: solo per relazioni dello stesso tipo orientato (in Apollon per composizione e aggregazione la sorgente e' la parte). Molteplicita': confrontate per estremo di classe (esclusi generalizzazione e realizzazione), normalizzate: senza spazi, 'n' -> '*', '0..*' = '*'.

| temperatura | relazioni risposta | relazioni GT | stessa coppia | stesso tipo | stesso verso (tipi orientati) | comp./aggr.: stesso verso | stesse molteplicita' |
|---|---|---|---|---|---|---|---|
| 0 | 23 | 27 | 15 | 9 | 3/6 | 3/6 | 5/15 |
| 0.3 | 105 | 110 | 32 | 19 | 10/13 | 5/6 | 10/25 |

Tipo diverso con la stessa coppia, t = 0 (GT -> risposta): ClassBidirectional -> ClassAggregation 3, ClassBidirectional -> ClassUnidirectional 2, ClassBidirectional -> ClassComposition 1

Tipo diverso con la stessa coppia, t = 0.3 (GT -> risposta): ClassBidirectional -> ClassUnidirectional 6, ClassUnidirectional -> ClassComposition 4, ClassBidirectional -> ClassAggregation 3

Per esercizio (somma sulle risposte L1): stessa coppia / relazioni GT × risposte L1; stesso tipo; stesso verso; stesse molteplicita'.

| esercizio | t | stessa coppia | relazioni GT (× risposte) | stesso tipo | stesso verso | stesse molt. |
|---|---|---|---|---|---|---|
| Louvre | 0 | — | — | — | — | — |
| Louvre | 0.3 | 4 | 14 | 0 | 0/0 | 0/4 |
| Sober | 0 | — | — | — | — | — |
| Sober | 0.3 | 0 | 10 | 0 | 0/0 | 0/0 |
| StudentAppointment | 0 | 6 | 18 | 3 | 0/0 | 0/6 |
| StudentAppointment | 0.3 | 2 | 12 | 1 | 0/0 | 0/2 |
| CardGameApp | 0 | — | — | — | — | — |
| CardGameApp | 0.3 | 4 | 26 | 0 | 0/0 | 0/4 |
| ApartmentBuilding | 0 | 9 | 9 | 6 | 3/6 | 5/9 |
| ApartmentBuilding | 0.3 | 9 | 9 | 7 | 5/6 | 8/9 |
| FilmSet | 0 | — | — | — | — | — |
| FilmSet | 0.3 | 13 | 39 | 11 | 5/7 | 2/6 |

### Calibrazione dei token di prompt

Rapporto token reali (server, tokenizer di Gemma 4) / stima cl100k_base su 36 chiamate: min 1.195, mediana 1.222, max 1.239. Le ripetizioni dello stesso prompt hanno lo stesso rapporto (6 prompt distinti). Uso: ricalcolo delle tabelle della domanda 8 per il Passo 3b (`experiments/context_budget.py`).

### Risposte troncate (cicli di relazioni): legate al prompt o agli esempi recuperati?

Conteggi testuali (valgono anche per le risposte non decodificabili): relazioni = coppie `"source"`/`"target"` scritte; coppie distinte = coppie (sorgente, destinazione) diverse; classi dagli esempi = nomi di classe della risposta presenti negli esempi recuperati e assenti dal GT. Token degli esempi e del GT: stima cl100k_base del JSON compatto; prompt: token reali dal server.

| chiamata | t | troncata | prompt reale | esempi: token / relazioni | GT: token / relazioni | completamento | relazioni scritte | coppie distinte | classi dagli esempi |
|---|---|---|---|---|---|---|---|---|---|
| ApartmentBuilding__bm25__k2__t0__r0 | 0 | no | 8233 | 4379 / 14 | 841 / 3 | 1397 | 3 | 3 | — |
| ApartmentBuilding__bm25__k2__t0__r1 | 0 | no | 8233 | 4379 / 14 | 841 / 3 | 2144 | 3 | 3 | — |
| ApartmentBuilding__bm25__k2__t0__r2 | 0 | no | 8233 | 4379 / 14 | 841 / 3 | 2144 | 3 | 3 | — |
| ApartmentBuilding__bm25__k2__t0.3__r0 | 0.3 | no | 8233 | 4379 / 14 | 841 / 3 | 2037 | 3 | 3 | — |
| ApartmentBuilding__bm25__k2__t0.3__r1 | 0.3 | no | 8233 | 4379 / 14 | 841 / 3 | 2036 | 3 | 3 | — |
| ApartmentBuilding__bm25__k2__t0.3__r2 | 0.3 | no | 8233 | 4379 / 14 | 841 / 3 | 2149 | 3 | 3 | — |
| CardGameApp__bm25__k2__t0__r0 | 0 | no | 14672 | 9177 / 38 | 3450 / 13 | 4914 | 12 | 11 | — |
| CardGameApp__bm25__k2__t0__r1 | 0 | SI | 14672 | 9177 / 38 | 3450 / 13 | 12288 | 63 | 6 | — |
| CardGameApp__bm25__k2__t0__r2 | 0 | SI | 14672 | 9177 / 38 | 3450 / 13 | 12288 | 63 | 6 | — |
| CardGameApp__bm25__k2__t0.3__r0 | 0.3 | no | 14672 | 9177 / 38 | 3450 / 13 | 4197 | 10 | 9 | — |
| CardGameApp__bm25__k2__t0.3__r1 | 0.3 | SI | 14672 | 9177 / 38 | 3450 / 13 | 12288 | 59 | 21 | — |
| CardGameApp__bm25__k2__t0.3__r2 | 0.3 | no | 14672 | 9177 / 38 | 3450 / 13 | 5106 | 14 | 14 | — |
| FilmSet__bm25__k2__t0__r0 | 0 | SI | 14067 | 8663 / 36 | 3401 / 13 | 12288 | 49 | 12 | — |
| FilmSet__bm25__k2__t0__r1 | 0 | SI | 14067 | 8663 / 36 | 3401 / 13 | 12288 | 45 | 11 | — |
| FilmSet__bm25__k2__t0__r2 | 0 | SI | 14067 | 8663 / 36 | 3401 / 13 | 12288 | 45 | 11 | — |
| FilmSet__bm25__k2__t0.3__r0 | 0.3 | no | 14067 | 8663 / 36 | 3401 / 13 | 5049 | 13 | 12 | — |
| FilmSet__bm25__k2__t0.3__r1 | 0.3 | no | 14067 | 8663 / 36 | 3401 / 13 | 5641 | 16 | 14 | — |
| FilmSet__bm25__k2__t0.3__r2 | 0.3 | no | 14067 | 8663 / 36 | 3401 / 13 | 5165 | 14 | 13 | — |
| Louvre__bm25__k2__t0__r0 | 0 | SI | 13870 | 8414 / 36 | 1724 / 7 | 12288 | 55 | 3 | — |
| Louvre__bm25__k2__t0__r1 | 0 | no | 13870 | 8414 / 36 | 1724 / 7 | 3858 | 10 | 10 | — |
| Louvre__bm25__k2__t0__r2 | 0 | no | 13870 | 8414 / 36 | 1724 / 7 | 3858 | 10 | 10 | — |
| Louvre__bm25__k2__t0.3__r0 | 0.3 | no | 13870 | 8414 / 36 | 1724 / 7 | 4495 | 8 | 7 | — |
| Louvre__bm25__k2__t0.3__r1 | 0.3 | no | 13870 | 8414 / 36 | 1724 / 7 | 2803 | 7 | 6 | — |
| Louvre__bm25__k2__t0.3__r2 | 0.3 | no | 13870 | 8414 / 36 | 1724 / 7 | 4277 | 16 | 15 | — |
| Sober__bm25__k2__t0__r0 | 0 | no | 10150 | 5543 / 22 | 3479 / 10 | 2836 | 9 | 9 | vehicle |
| Sober__bm25__k2__t0__r1 | 0 | no | 10150 | 5543 / 22 | 3479 / 10 | 3384 | 12 | 12 | vehicle |
| Sober__bm25__k2__t0__r2 | 0 | no | 10150 | 5543 / 22 | 3479 / 10 | 3384 | 12 | 12 | vehicle |
| Sober__bm25__k2__t0.3__r0 | 0.3 | no | 10150 | 5543 / 22 | 3479 / 10 | 3052 | 8 | 8 | — |
| Sober__bm25__k2__t0.3__r1 | 0.3 | SI | 10150 | 5543 / 22 | 3479 / 10 | 12288 | 54 | 13 | vehicle |
| Sober__bm25__k2__t0.3__r2 | 0.3 | SI | 10150 | 5543 / 22 | 3479 / 10 | 12288 | 80 | 10 | vehicle |
| StudentAppointment__bm25__k2__t0__r0 | 0 | no | 8046 | 4447 / 17 | 1308 / 6 | 2695 | 5 | 5 | — |
| StudentAppointment__bm25__k2__t0__r1 | 0 | no | 8046 | 4447 / 17 | 1308 / 6 | 2650 | 5 | 5 | — |
| StudentAppointment__bm25__k2__t0__r2 | 0 | no | 8046 | 4447 / 17 | 1308 / 6 | 2889 | 6 | 6 | — |
| StudentAppointment__bm25__k2__t0.3__r0 | 0.3 | no | 8046 | 4447 / 17 | 1308 / 6 | 2131 | 7 | 6 | — |
| StudentAppointment__bm25__k2__t0.3__r1 | 0.3 | no | 8046 | 4447 / 17 | 1308 / 6 | 3642 | 7 | 5 | — |
| StudentAppointment__bm25__k2__t0.3__r2 | 0.3 | no | 8046 | 4447 / 17 | 1308 / 6 | 3379 | 6 | 6 | — |

Mediane, troncate contro non troncate:

| gruppo | n | prompt reale | token degli esempi | relazioni degli esempi | token del GT | relazioni del GT | relazioni scritte | coppie distinte / relazioni scritte |
|---|---|---|---|---|---|---|---|---|
| troncate | 9 | 14067 | 8663 | 36 | 3450 | 13 | 55 | 0.24 |
| non troncate | 27 | 10150 | 5543 | 22 | 1724 | 7 | 8 | 1.00 |

Per esercizio (prompt ed esempi sono gli stessi per le 6 risposte dell'esercizio: cambiano solo temperatura e ripetizione), in ordine di prompt reale:

| esercizio | prompt reale | esempi recuperati | esempi: token / relazioni | GT: token / relazioni | troncate t = 0 | troncate t = 0.3 |
|---|---|---|---|---|---|---|
| CardGameApp | 14672 | TileOGame, TeamSportsScoutingSystem | 9177 / 38 | 3450 / 13 | 2/3 | 1/3 |
| FilmSet | 14067 | TransportCompany, MilanLibrary | 8663 / 36 | 3401 / 13 | 3/3 | 0/3 |
| Louvre | 13870 | MilanLibrary, HelpingHands | 8414 / 36 | 1724 / 7 | 1/3 | 0/3 |
| Sober | 10150 | HelpingHands, TruckLogistics | 5543 / 22 | 3479 / 10 | 0/3 | 2/3 |
| ApartmentBuilding | 8233 | eHome2020, RealEstateAgency | 4379 / 14 | 841 / 3 | 0/3 | 0/3 |
| StudentAppointment | 8046 | UniversityExams, University | 4447 / 17 | 1308 / 6 | 0/3 | 0/3 |

**Sintesi (esplorativa)**:
- le troncature compaiono solo negli esercizi con il prompt più lungo: 4 esercizi con almeno una troncata (prompt reale >= 10150), 2 senza (prompt <= 8233). Gli stessi esercizi hanno anche gli esempi recuperati più grandi (token e relazioni): il prompt è fatto quasi tutto dagli esempi, quindi **lunghezza del prompt e dimensione degli esempi non si possono separare** con questi dati;
- la dimensione del GT non spiega da sola i cicli: Louvre ha il GT tra i più piccoli e un prompt lungo, e tronca; StudentAppointment e ApartmentBuilding hanno GT e prompt piccoli e non troncano mai;
- nelle troncate le relazioni ripetono le stesse coppie (coppie distinte / relazioni scritte in mediana 0.24): è un ciclo sulle relazioni, non un diagramma più grande;
- classi copiate dagli esempi (presenti negli esempi, assenti dal GT): in 2 risposte troncate su 9 e in 3 non troncate su 27;
- a parità di prompt (stesso esercizio) la troncatura dipende anche dal campionamento (temperatura, ripetizione): non è determinata solo dal prompt;
- limiti: 6 configurazioni di prompt distinte, nessun test statistico; servirebbe un esperimento che vari la lunghezza del prompt a parità di esempi (o il contrario) per separare i due fattori.

### Id nello schema non valido del template v4 (solo descrittivo)

Il template v4 usa come esempio l'id "a1b2c3d4-e5f6-4890-81h2-i3j4k5l6m7n8" (non un UUID valido); L3 non richiede il formato UUID (voce 64). Classificazione per risposta (36):

- frammento del template v4 (-4890-81h2-): 31
- altro formato: 3
- non classificabile (JSON non decodificabile): 1
- forma UUID con caratteri non esadecimali: 1
- con il frammento del template, t = 0: 17/18
- con il frammento del template, t = 0.3: 14/18
