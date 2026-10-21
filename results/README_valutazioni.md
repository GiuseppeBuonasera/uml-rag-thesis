# Valutazioni dei risultati

Riassunto di quello che è emerso dalle valutazioni: il passo 3b (sezione 1) e i controlli oracle (sezione 2).

> **Natura dei risultati.** Tutte le analisi qui riportate sono **esplorative**: i risultati del 3b sono stati guardati
> prima che fosse scritto uno script di analisi registrato in anticipo (voce 154 di `docs/decisions.md`). L'analisi
> statistica ufficiale è quella dello script dei relatori (voce 158). Nessuna correzione per test multipli è applicata
> ai p-value di questa pagina.

---

## 1. Passo 3b

### 1.1 Cosa è stato generato

| | |
|---|---|
| Modello | Gemma 4 26B A4B QAT, locale (LM Studio); temperatura 0,3, top_p 0,95, top_k 64; ragionamento spento |
| Esercizi | **54 di validazione** (34 del corpus + 20 De Bari): analisi principale. **26 di sviluppo**: analisi secondaria (su di essi è stata tarata la configurazione) |
| Prompt | `zero_shot` (nessun esempio); `static k2` (2 esempi fissi: bank loans + AirTravel); `random k3` (3 esempi casuali); `bm25 k2`, `bm25 k3` (esempi recuperati con BM25); `hybrid k3` (BM25 + embedding, RRF) |
| Formati di uscita | PlantUML e JSON compatto, entrambi convertiti in Apollon v4 per la valutazione |
| Ripetizioni | 3 per esercizio, prompt e formato |
| Totale | **2.874 risposte** (1.938 sui 54 + 936 sui 26); 12 non valide (non leggibili dal post-processing) |

Gli esempi recuperati vengono da un pool di 79 esercizi (tutti gli altri) e sono congelati in
`data/retrieval_frozen/retrievals_3b.jsonl`: sono identici nelle 3 ripetizioni e nei due formati (tranne random, che
cambia a ogni ripetizione).

### 1.2 Metrica usata

**Completezza dello strumento dei relatori** (`evaluation_summary_relatori.xlsx`): elementi del diagramma di
riferimento ritrovati / elementi del diagramma di riferimento, in percentuale. È una **recall**: non penalizza gli
elementi in più. È riportata in totale e separata per classi, attributi e associazioni (generalizzazioni comprese).

- Media prima sulle ripetizioni valide di ogni esercizio, poi sugli esercizi (ogni esercizio pesa uguale).
- Le 12 risposte non valide sono **escluse** (lo strumento le aveva valutate come se fossero valide).
- Confronti tra prompt: **Wilcoxon appaiato** per esercizio. Legame con la difficoltà: **Spearman** con Flesch-Kincaid
  (leggibilità della traccia) e con la grandezza (classi + relazioni del diagramma di riferimento).

La nostra F1 (`evaluation/element_metrics.py`) porta alle stesse conclusioni: la correlazione con la completezza dei
relatori è 0,97-0,98. Le differenze principali: risposte non valide, abbinamento dei nomi più permissivo nello
strumento dei relatori, conteggio degli attributi.

### 1.3 Risultati sui 54 di validazione

Completezza media (%):

| Formato | Prompt | Totale | Classi | Attributi | Associazioni |
|---|---|---|---|---|---|
| PlantUML | zero_shot | 43,4 | 64,0 | 32,1 | 43,5 |
| PlantUML | static k2 | 43,4 | 63,0 | 32,5 | 43,7 |
| PlantUML | random k3 | **45,3** | 65,1 | 34,2 | 46,0 |
| PlantUML | bm25 k2 | 43,8 | 64,1 | 33,1 | 43,5 |
| PlantUML | bm25 k3 | 44,7 | 64,6 | 34,1 | 44,6 |
| PlantUML | hybrid k3 | 44,9 | 65,2 | 33,7 | 44,6 |
| Compatto | zero_shot | 38,2 | 57,2 | 28,7 | 35,8 |
| Compatto | static k2 | 41,5 | 62,0 | 29,0 | 42,0 |
| Compatto | random k3 | 41,5 | 62,2 | 29,6 | 40,8 |
| Compatto | bm25 k2 | 40,5 | 61,7 | 28,6 | 40,8 |
| Compatto | bm25 k3 | **41,9** | 63,2 | 30,3 | 43,2 |
| Compatto | hybrid k3 | 41,7 | 62,4 | 30,5 | 41,0 |

Confronti appaiati sulla completezza totale (d = differenza media in punti; "vince / perde" = esercizi in cui il primo
prompt fa meglio / peggio):

| Confronto | PlantUML: d | p | vince / perde | Compatto: d | p | vince / perde |
|---|---|---|---|---|---|---|
| bm25 k3 − random k3 | −0,57 | 0,48 | 18 / 23 | +0,42 | 0,65 | 24 / 22 |
| hybrid k3 − random k3 | −0,42 | 0,51 | 22 / 24 | +0,15 | 0,87 | 23 / 21 |
| bm25 k2 − static k2 | +0,46 | 0,95 | 17 / 24 | −1,04 | 0,15 | 14 / 28 |
| bm25 k3 − bm25 k2 | +0,88 | 0,07 | 25 / 14 | +1,46 | 0,09 | 23 / 13 |
| bm25 k3 − zero_shot | +1,34 | 0,21 | 22 / 18 | **+3,73** | **0,008** | 32 / 16 |
| random k3 − zero_shot | +1,91 | 0,12 | 23 / 19 | **+3,31** | **0,023** | 30 / 16 |
| static k2 − zero_shot | +0,01 | 0,91 | 22 / 22 | **+3,35** | **0,011** | 32 / 15 |
| hybrid k3 − zero_shot | +1,49 | 0,25 | 24 / 20 | **+3,46** | **0,003** | 34 / 15 |

Cosa dicono:

1. **Il retrieval non batte gli esempi casuali.** bm25 e hybrid contro random: differenze sotto il punto, in entrambe
   le direzioni, mai significative. Anche bm25 k2 contro gli esempi fissi (static k2) è nullo. **L'ipotesi centrale
   (esempi recuperati migliori di esempi statici o casuali) non è confermata.**
2. **Gli esempi aiutano solo nel compatto, e qualunque esempio va bene.** Nel compatto ogni prompt con esempi supera
   zero_shot di circa 3,3-3,7 punti (p < 0,05); in PlantUML il guadagno è 0-2 punti e non è significativo. Gli esempi
   servono soprattutto a mostrare il **formato** di uscita, non per il loro contenuto.
3. **PlantUML è meglio del compatto** con ogni prompt: da +1,9 (static k2, p 0,07) a +5,2 punti (zero_shot), con
   p ≤ 0,007 per tutti gli altri prompt.
4. **Tre esempi sono un po' meglio di due** (bm25 k3 contro k2: +0,9 / +1,5 punti, p 0,07 / 0,09), al limite.
5. **Le classi si ritrovano molto meglio degli attributi**: circa 62-65 % delle classi contro 29-34 % degli attributi.
   Le associazioni stanno nel mezzo (41-46 %).

### 1.4 Difficoltà degli esercizi (54 di validazione)

Correlazione di Spearman tra difficoltà e completezza totale, per prompt:

| Prompt | PlantUML: Flesch-Kincaid | PlantUML: grandezza | Compatto: Flesch-Kincaid | Compatto: grandezza |
|---|---|---|---|---|
| zero_shot | −0,19 | **−0,45** | −0,12 | −0,18 |
| static k2 | −0,23 | **−0,46** | −0,16 | **−0,46** |
| random k3 | −0,17 | **−0,44** | −0,16 | **−0,38** |
| bm25 k2 | −0,18 | **−0,43** | −0,16 | **−0,35** |
| bm25 k3 | −0,24 | **−0,45** | −0,20 | **−0,43** |
| hybrid k3 | −0,19 | **−0,45** | −0,23 | **−0,35** |

In grassetto p < 0,05 (per la grandezza quasi tutti p ≤ 0,01).

- **Conta la grandezza del diagramma, non la leggibilità del testo.** Più classi e relazioni ha l'esercizio, più la
  completezza scende (rho circa −0,45). Con Flesch-Kincaid le correlazioni sono deboli e mai significative.
- **Nessun prompt aiuta di più sugli esercizi difficili**: le correlazioni sono quasi uguali per tutti i prompt. Unica
  eccezione: zero_shot nel compatto non dipende dalla grandezza (−0,18), perché sbaglia spesso il formato anche sugli
  esercizi piccoli.
- Le due difficoltà sono indipendenti (rho −0,01). Combinate pesano molto: testo difficile e diagramma grande danno il
  26 % di completezza, contro il 62 % del caso facile.
- I dati per esercizio, ordinati per le due difficoltà, sono in `1_passo3b/passo3b_completezza.xlsx`.

### 1.5 I 26 esercizi di sviluppo (analisi secondaria)

Su questi esercizi è stata scelta la configurazione (istruzioni, modello, retriever), misurando bm25: bm25 e hybrid
sono quindi favoriti. Non vanno sommati ai 54.

- Completezza più alta (46-52 % contro 38-45 %): sono esercizi più piccoli (grandezza massima 26 contro 49), con
  testi un po' più difficili (Flesch-Kincaid 9,4 contro 8,4).
- **Stesse conclusioni dei 54**: in PlantUML nessun confronto significativo; nel compatto gli esempi battono zero_shot
  (bm25 k3 +5,1 punti, p 0,02; static k2 +5,5, p 0,01).
- Unico confronto diverso: **bm25 k3 batte random nel compatto** (+2,4 punti, p 0,04). È il vantaggio atteso sugli
  esercizi su cui è stata tarata la configurazione; sui 54 non si ripete (+0,4, p 0,65).
- Qui la grandezza non conta (rho circa 0), perché i 26 hanno diagrammi di grandezza simile; la leggibilità ha
  correlazioni negative (da −0,19 a −0,42), significative solo per random k3 e static k2 in PlantUML.

### 1.6 Altri riscontri (esplorativi, sui 54)

**Perché il retrieval non aiuta: gli esempi non sono abbastanza simili.**
- Somiglianza media dei nomi di classe tra esempio ed esercizio (Jaccard dei nomi, Jt): random 0,018, bm25 0,098,
  hybrid 0,090. Il miglior esempio di bm25 (0,154) è già vicino al migliore possibile nel pool (0,170).
- Solo 3 esercizi su 54 hanno un esempio con somiglianza ≥ 0,3; nel pool nessuna coppia arriva a 0,4.
- Il guadagno di bm25 su random non dipende dalla somiglianza dell'esempio (rho +0,05 / +0,08).
- I controlli oracle (prossima sezione) mostrano che un esempio serve davvero solo da una somiglianza di circa 0,4-0,56:
  il limite del 3b è il corpus, non il modello.

**Il modello prende i nomi dal testo, non dagli esempi.**
- Il 96 % dei nomi di classe generati compare nella traccia; le classi copiate da un esempio sono l'1,6-4,1 %.
- I nomi cambiano poco tra ripetizioni (Jaccard 0,86-0,88) e tra prompt (0,80); rispetto al riferimento il Jaccard è
  0,47-0,49.

**Cosa penalizza di più.**
- Circa il **70 % degli elementi mancanti** dipende da classi non abbinate: associazioni con un estremo non abbinato
  (29 %), attributi di classi non abbinate (20 %), classi mancanti (20 %). Tra classi abbinate manca solo il 4 % dei
  collegamenti.
- Le classi del riferimento il cui nome compare nel testo si ritrovano al 66 %, quelle senza al 6 %. Il riferimento ha
  5-6 volte più enum e classi "astratte" (non nominate nel testo) del modello.
- Il **26-39 % degli attributi del riferimento** non ha parole corrispondenti nel testo. Togliendoli dal calcolo la
  completezza sale di 3-6 punti, ma l'ordine tra i prompt non cambia.

**Scheletri** (risposte valide senza nessun attributo, quando il riferimento ne ha).
- PlantUML: 11 con zero_shot, 0-3 con gli esempi. Compatto: circa 20 con zero_shot e static, 36-45 con random, bm25
  e hybrid.
- Il fattore più forte è la presenza degli attributi nel testo: classi vuote 27-34 % quando il testo non li descrive,
  3-7 % quando li descrive. 8 esercizi fanno 119 dei 200 scheletri.
- Nel compatto gli esempi variabili raddoppiano gli scheletri. Il controllo "esempi senza attributi" (voce 169)
  conferma la causa: con esempi senza attributi gli scheletri del compatto passano dal 28 % al 91 %.

**Esempi singoli.** Con random, dove gli esempi sono assegnati a caso, nessun esempio funziona meglio o peggio degli
altri (test di permutazione, p 0,55); esempi più difficili o con più attributi non aiutano né peggiorano.

### 1.7 Cautele

- **Test multipli.** In questa pagina ci sono decine di test senza correzione. I risultati con p ≤ 0,001 (PlantUML
  meglio del compatto, correlazione con la grandezza) sono i più robusti; quelli tra 0,003 e 0,05 (per esempio esempi
  contro zero_shot nel compatto) potrebbero non reggere a una correzione come Holm, a seconda di quanti test si
  includono.
- **Potenza.** Con 54 esercizi la differenza minima rilevabile è circa 0,03 di F1 (stima dalla variabilità del dev
  set). Differenze più piccole tra bm25, hybrid e random non si possono escludere, ma sarebbero comunque piccole.
- **Riferimento.** Parte degli elementi del riferimento non si può ricavare dal testo (attributi non deducibili,
  astrazioni): il tetto reale della completezza è sotto il 100 %.
- **Un solo modello.** Tutto vale per Gemma 4 26B A4B QAT con questa configurazione.

### Fonti

- `1_passo3b/evaluation_summary_relatori.xlsx` (strumento dei relatori, 2026-10-19): tutte le tabelle di 1.3, 1.4 e 1.5.
- `docs/decisions.md`, voci 151 e 154-161: somiglianza degli esempi, vocabolario, penalità, scheletri, stabilità.
- `1_passo3b/passo3b_risultati.zip`: tutte le risposte, i diagrammi di riferimento e le tracce.

---

## 2. Controlli oracle

### 2.1 A cosa servono

Il 3b dice che il retrieval non batte gli esempi casuali, ma non dice **perché**. Le spiegazioni possibili sono due:

- (a) **limite del corpus**: nel pool non ci sono esempi abbastanza simili da essere utili;
- (b) **limite del modello**: il modello riscrive comunque tutto dal testo e usa gli esempi solo per il formato.

I controlli oracle separano le due spiegazioni dando al modello esempi **costruiti apposta**, a partire dalla soluzione
stessa dell'esercizio. Non sono configurazioni utilizzabili in un sistema reale (lì la soluzione non c'è): servono a
misurare cosa succederebbe con esempi molto più simili di quelli che il corpus offre.

### 2.2 Come sono stati fatti

| Controllo | Voce | Esempio dato al modello | Formati | Generazioni |
|---|---|---|---|---|
| **Esercizio stesso** | 162 | la traccia e la soluzione dell'esercizio stesso | PlantUML e compatto | 216 |
| **Parziale** | 163 | la traccia vera con la soluzione ridotta al 25, 50 o 75 % delle classi | solo PlantUML | 162 |
| **Misti** | 164-165 | metà soluzione + 2 esempi bm25 ("metà + 2 bm25"); le due metà complementari come due esempi ("due metà") | solo PlantUML | 108 |
| **Senza attributi** | 167, 169 | A: l'esercizio stesso senza attributi; B: gli esempi bm25 k3 del 3b senza attributi | PlantUML e compatto | 216 |

- Tutti sui **54 esercizi di validazione**, stessa configurazione del 3b (Gemma 4 26B A4B QAT, istruzioni v5),
  **1 ripetizione**; 702 generazioni, tutte valide.
- **Solo analisi**: i risultati non sono usati per nessuna scelta del sistema e non entrano nei dati dei relatori.
- **Regole fissate prima delle run**, con soglie e verdetti scritti e testati negli script di analisi
  (`experiments/analyze_oracle_*.py`). I controlli però sono stati pensati dopo aver visto il 3b.
- **Due versioni della frase che introduce gli esempi**: "standard", quella del 3b ("They describe other systems: do
  not copy their classes"), e "libera", senza il divieto, che altrimenti sarebbe falso quando l'esempio è l'esercizio
  stesso.

### 2.3 Metrica

**Completezza nostra**: elementi del riferimento ritrovati / elementi del riferimento, su classi, attributi, relazioni e
generalizzazioni, con l'abbinamento rilassato di `evaluation/element_metrics.py`. È la stessa idea della completezza dei
relatori, ma calcolata da noi: lo strumento dei relatori non ha valutato queste run.

Il **guadagno** è la completezza del controllo meno la completezza dello stesso esercizio con zero_shot nel 3b (media
delle 3 ripetizioni). I confronti appaiati sono con Wilcoxon. Le F1 per esercizio di tutti i controlli sono in
`2_controlli_oracle/controlli_f1.xlsx`.

### 2.4 Esercizio stesso come esempio (voce 162)

| Formato | Frase | Completezza | Precision | Copia quasi esatta | F1 classi | F1 attributi | F1 relazioni |
|---|---|---|---|---|---|---|---|
| PlantUML | libera | **0,760** | 0,791 | 13 % | 0,887 | 0,704 | 0,712 |
| PlantUML | standard | 0,746 | 0,771 | 17 % | 0,889 | 0,649 | 0,702 |
| PlantUML | 3b bm25 k3 (riferimento) | 0,434 | 0,482 | 0 % | 0,646 | 0,347 | 0,432 |
| Compatto | libera | **0,635** | 0,715 | 9 % | 0,824 | 0,509 | 0,646 |
| Compatto | standard | 0,639 | 0,696 | 6 % | 0,826 | 0,507 | 0,645 |
| Compatto | 3b bm25 k3 (riferimento) | 0,411 | 0,495 | 0 % | 0,629 | 0,294 | 0,440 |

"Copia quasi esatta" = completezza e precision entrambe ≥ 0,90.

- **Verdetto della regola: uso parziale, in entrambi i formati** (soglie: ≥ 0,80 "sa usare l'esempio", < 0,60 "non lo
  usa"). Con la soluzione davanti la completezza sale di circa 0,33 in PlantUML e 0,22 nel compatto, ma il modello
  la copia davvero solo nel 9-17 % dei casi: in genere la riscrive, perdendo parte degli attributi.
- **Il modello sa usare un esempio vicino**: la spiegazione (b) non basta. Il limite del 3b è in buona parte il corpus.
- **La frase "do not copy their classes" non frena la copia**: tra frase libera e standard la differenza è di
  ±0,015.
- **PlantUML sfrutta l'esempio meglio del compatto** (0,760 contro 0,635), soprattutto per gli attributi (F1 0,70
  contro 0,51).

### 2.5 Quanto deve essere simile un esempio (voci 163-165)

Guadagno di completezza su zero_shot in funzione della somiglianza dell'esempio, misurata come Jaccard dei nomi di
classe tra la soluzione dell'esempio e quella dell'esercizio (Jt). Solo PlantUML.

| Esempio | Somiglianza (Jt) | Risposte | Guadagno |
|---|---|---|---|
| 3b, miglior esempio con Jt 0,00-0,10 | 0,00-0,10 | 499 | +0,008 |
| 3b, miglior esempio con Jt 0,10-0,20 | 0,10-0,20 | 120 | +0,014 |
| 3b, miglior esempio con Jt 0,20-0,30 | 0,20-0,30 | 161 | +0,022 |
| 3b, miglior esempio con Jt 0,30-0,45 | 0,30-0,45 | 27 | +0,039 |
| soluzione al 25 % delle classi | 0,34 | 54 | +0,036 |
| soluzione al 50 % delle classi | 0,56 | 54 | **+0,095** |
| soluzione al 75 % delle classi | 0,77 | 54 | +0,173 |
| esercizio stesso | 1,00 | 54 | +0,337 |

- **Verdetto della regola: un esempio diventa utile (guadagno ≥ 0,05) al livello 50 %, cioè con somiglianza 0,56.**
  Interpolando, la soglia è intorno a Jt 0,4.
- **La curva è convessa**: il guadagno cresce poco finché l'esempio è lontano e molto quando si avvicina alla
  soluzione. Al 25 % il guadagno coincide con quello degli esempi reali del 3b di pari somiglianza: le due misure
  sono coerenti.
- **Il corpus sta tutto sotto la soglia.** Nel pool nessuna coppia di esercizi arriva a Jt 0,4 (solo 2 su 3.160
  superano 0,3); il vicino più simile dei 54 ha in media Jt 0,17, al massimo 0,33; due esercizi dello stesso dominio
  hanno in media 0,048. Per questo nel 3b il retrieval non poteva fare la differenza.

Più esempi insieme (voci 164-165):

| Esempi nel prompt | Guadagno |
|---|---|
| metà soluzione da sola | +0,095 |
| 2 esempi bm25 + metà soluzione | +0,118 |
| metà soluzione + metà complementare (due esempi) | +0,210 |
| soluzione intera in un esempio | +0,337 |

- **Esempi lontani accanto a uno vicino non fanno danno** (+0,024 rispetto alla metà da sola, p 0,07; verdetto
  "nessuna diluizione"). Quindi aggiungere esempi poco simili non è un rischio.
- **Due metà valgono meno di un esempio intero** (+0,210 contro +0,337, p < 0,001; verdetto "si sommano in parte"):
  con le stesse informazioni divise in due esempi il modello ottiene il 62 % del guadagno dell'esempio intero, e la
  seconda metà aggiunge circa la metà di quanto aggiungerebbe se fosse nello stesso esempio (+0,116 contro +0,242).
  Un esempio molto vicino vale più di più esempi parziali.

### 2.6 Esempi senza attributi (voci 167 e 169)

| Formato | Esempi | Scheletri | Recall attributi | F1 attributi | Completezza |
|---|---|---|---|---|---|
| PlantUML | A: esercizio stesso senza attributi | 21 % | 0,346 | 0,355 | 0,610 |
| PlantUML | esercizio stesso con attributi | 0 % | 0,696 | 0,704 | 0,760 |
| PlantUML | B: bm25 k3 senza attributi | **19 %** | 0,324 | 0,324 | 0,422 |
| PlantUML | bm25 k3 del 3b (con attributi) | 2 % | 0,346 | 0,347 | 0,434 |
| Compatto | A: esercizio stesso senza attributi | 49 % | 0,242 | 0,249 | 0,516 |
| Compatto | esercizio stesso con attributi | 15 % | 0,499 | 0,509 | 0,635 |
| Compatto | B: bm25 k3 senza attributi | **91 %** | **0,031** | 0,032 | 0,308 |
| Compatto | bm25 k3 del 3b (con attributi) | 28 % | 0,309 | 0,294 | 0,411 |

"Scheletro" = risposta valida senza nessun attributo, quando il riferimento ne ha.

- **B, verdetto della regola: gli esempi senza attributi causano gli scheletri, in entrambi i formati**
  (PlantUML +17 punti, p 0,003; compatto +62 punti, p < 0,001). È l'unica prova **causale** sugli scheletri: rispetto
  al 3b cambia solo la presenza degli attributi negli esempi.
- **Il compatto imita la forma degli esempi.** Con esempi senza attributi smette quasi del tutto di estrarli dal testo
  (recall da 0,31 a 0,03). PlantUML è molto più robusto: gli scheletri salgono, ma la recall degli attributi resta
  quasi uguale.
- **A: circa metà degli attributi ritrovati con l'esercizio stesso viene dal testo** (rapporto tra recall senza e con
  attributi: 0,50 in PlantUML, 0,48 nel compatto). In PlantUML la recall senza attributi (0,346) è identica a quella
  del 3b: quello che il modello ricava dal testo resta lo stesso, e l'altra metà era copiata dall'esempio.
- Classi e relazioni perfette restano utili anche senza attributi (completezza 0,61 contro 0,43 del 3b in PlantUML).

### 2.7 Cosa dicono i controlli, insieme

1. **Il modello sa sfruttare un esempio molto simile**, ma non lo copia: lo riscrive e usa soprattutto classi e
   relazioni.
2. **Un esempio serve solo sopra una somiglianza dei nomi di classe di circa 0,4-0,56.** Il corpus attuale non ha
   coppie di esercizi così simili: **il risultato negativo del 3b dipende dal corpus più che dal modello o dal metodo
   di retrieval.**
3. **Per una RAG di esempi efficace servirebbe un corpus con, per ogni esercizio, almeno un esempio molto vicino**
   (stesso dominio e struttura simile). Esempi lontani in più non danneggiano; un esempio completo vale più di più
   esempi parziali.
4. **Nel compatto la forma degli esempi conta molto**: esempi con poche classi dotate di attributi producono
   scheletri. Nel compatto andrebbero scelti esempi ricchi di attributi.

### 2.8 Cautele

- **Esempi artificiali.** Nei controlli parziali l'esempio ha la stessa traccia dell'esercizio e cambia solo la
  soluzione; un esempio reale simile al 50 % avrebbe anche una traccia diversa. La soglia misura la somiglianza della
  soluzione e potrebbe essere ottimistica.
- **Una sola ripetizione** per controllo: le medie sono su 54 risposte per colonna, non su 162 come nel 3b.
- **Parziale e misti solo in PlantUML.** La soglia di 0,4-0,56 vale per PlantUML; nel compatto, che reagisce di più
  alla forma degli esempi, potrebbe essere diversa.
- **Metrica nostra**, non quella dei relatori (con cui correla 0,97-0,98 sul 3b); i numeri non si sommano a quelli
  della sezione 1.
- **Disegnati dopo il 3b**: le regole erano fissate prima di ogni run, ma la scelta dei controlli nasce dai risultati
  del 3b.

### Fonti della sezione 2

- `2_controlli_oracle/oracle_self.md`, `oracle_partial.md`, `oracle_mix.md`, `oracle_attr.md`: i sommari prodotti dagli
  script di analisi.
- `2_controlli_oracle/controlli_f1.xlsx`: F1 per esercizio di tutti i controlli.
- `docs/decisions.md`, voci 162-169: disegno, regole e esiti.
