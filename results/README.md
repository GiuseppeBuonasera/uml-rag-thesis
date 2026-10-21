# Risultati raccolti

Cartella generata da `experiments/build_results.py` (copie: gli originali restano in `data/results/`).
**Riassunto delle valutazioni: [`README_valutazioni.md`](README_valutazioni.md)** (scritto a mano, non rigenerato).
Tutti i risultati sono ESPLORATIVI (voce 154): l'analisi statistica la fanno i relatori con il loro script (voce 158).
Modello: Gemma 4 26B A4B QAT (LM Studio), istruzioni v5, temperatura 0,3.

## classifica_run.xlsx — graduatoria di tutte le run
I 6 prompt del 3b e i controlli oracle sui 54 di validazione, per F1 medio, con la media sulla meta' piu' difficile e
su quella piu' facile degli esercizi (fogli "Per grandezza" e "Per Flesch-Kincaid").

In tutti gli Excel il primo foglio ordina per GRANDEZZA, la difficolta' dominante (Spearman con la completezza circa
−0,45 contro circa −0,2 di Flesch-Kincaid); il secondo per Flesch-Kincaid.

## 1_passo3b — il passo 3b (79 esercizi, 6 prompt x 2 formati x 3 ripetizioni = 2.874 risposte)
- `passo3b_completezza.xlsx`: completezza dello strumento dei relatori per esercizio e prompt (PlantUML e compatto);
  foglio "Per grandezza" e foglio "Per Flesch-Kincaid" (esercizi ordinati per difficolta'); Note.
- `evaluation_summary_relatori.xlsx`: il file prodotto dallo strumento dei relatori (2026-10-19).
- `passo3b_risultati.zip`: tutte le risposte in JSON e PlantUML (sviluppo e validazione), i GT in PlantUML, i testi.
- `difficolta.csv`: difficolta' degli esercizi (Flesch-Kincaid e grandezza).

## 2_controlli_oracle — controlli solo analisi (54 di validazione, 1 ripetizione)
- `controlli_f1.xlsx`: F1 per esercizio di tutti i controlli, stesso ordinamento (grandezza, Flesch-Kincaid).
- `oracle_self.md` (voce 162): l'esercizio stesso come esempio.
- `oracle_partial.md` (voce 163): solo una parte delle classi dell'esercizio stesso: quanto deve essere simile un esempio.
- `oracle_mix.md` (voci 164-165): esempio vicino + esempi lontani; due meta' complementari.
- `oracle_attr.md` (voci 167 e 169): esempi senza attributi.

## 3_sviluppo — analisi di sviluppo (piloti e dev set, fino alla voce 151)
Sommari delle prove usate per scegliere formato, istruzioni, k, retriever e modello.

Le decisioni e i numeri commentati sono in `docs/decisions.md`; lo stato in `docs/STATUS.md`.
