# docs/dati — materiale di riferimento (non corpus RAG)

Questa cartella contiene materiale raccolto/ricevuto che **non fa parte del corpus di
retrieval** (quello vive in `corpus/raw/models/`, vedi sotto). È tenuto qui come
riferimento per il prompt engineering, la valutazione e possibili estensioni future.

## Cosa NON c'è più qui

- `models/` (45 esercizi con descrizione + diagramma PlantUML di riferimento) è stato
  spostato in [`corpus/raw/models/`](../../corpus/raw/models/) — è il corpus primario
  per il retrieval. Vedi `corpus/processed/corpus.jsonl` per la versione indicizzata
  (generata da `corpus/build_manifest.py`).

## Cosa c'è qui

### `debari_baseline/`
Pacchetto dello studio precedente (replica/baseline in stile De Bari et al.): 15
esercizi in italiano (`Exercises.docx` / `Exercises.pdf`), le soluzioni generate da 4
LLM diversi (ChatGPT, DeepSeek, Gemini, Qwen) come screenshot in `Exercises/`, e
`Analysis.xlsx` con le valutazioni.

**Non è corpus few-shot.** È materiale di **benchmark/baseline di un altro studio**:
- almeno un esercizio (l'orologio digitale) è un diagramma a stati, non delle classi —
  fuori scope se il progetto resta sui class diagram.
- se in futuro si vogliono riusare questi 15 esercizi come *query di valutazione* per il
  nostro sistema RAG, vanno filtrati (solo class diagram) e va evitata la leakage: non
  devono comparire anche nel corpus di retrieval usato per generare i loro pochi-shot.

### `apollon_format_reference/`
Materiale che definisce il formato di output scelto (Apollon JSON, vedi
`docs/decisions.md`):
- `prompt.docx` (+ `prompt_template.txt`, estratto in testo semplice) — prompt template
  originale che istruisce l'LLM a produrre un diagramma delle classi in JSON
  compatibile con [Apollon](https://apollon.ase.in.tum.de).
- `diagram_example_1.json`, `diagram_example_2.json` — esempi di output Apollon validi
  (struttura `elements` / `relationships` / `assessments`), usati come riferimento per
  scrivere `corpus/apollon_convert.py` (vedi sotto) e per validare lo schema in
  `evaluation/metrics.py`.

### `external_exercise_pool/`
- `data.pdf` — raccolta di tracce di esercizi UML da una risorsa didattica pubblica
  (silvae86.github.io). **Solo tracce, senza diagrammi di riferimento**: non
  utilizzabile come corpus finché non viene accoppiato a una soluzione. Candidato per
  espandere il corpus in futuro, non usare prima di aver validato/creato le soluzioni.

## Nota di scope

Il target di generazione è **Apollon JSON**, non PlantUML (vedi
[`docs/decisions.md`](../decisions.md)). I 45 diagrammi di riferimento originali in
`corpus/raw/models/` sono in PlantUML; sono stati convertiti in Apollon JSON da
[`corpus/apollon_convert.py`](../../corpus/apollon_convert.py) (schema verificato
contro il pacchetto npm `@ls1intum/apollon`, non dedotto). Il risultato è in
`corpus/processed/corpus.jsonl` (campo `diagram_apollon_json`) e in
`corpus/processed/apollon/<id>.json`.

**È una conversione automatica con approssimazioni note**, non una nuova annotazione
manuale — ogni record ha un campo `apollon_conversion_warnings` che elenca i casi non
gestiti in modo esatto (soprattutto: il costrutto "classe associativa" di PlantUML,
`(A,B) .. C`, approssimato con due associazioni semplici di molteplicità `1`; 2 vincoli
XOR scartati perché non rappresentabili). Da rivedere manualmente prima di usare questi
diagrammi come few-shot "canonici" in valutazioni che contano sulla loro esattezza
semantica al 100%.
