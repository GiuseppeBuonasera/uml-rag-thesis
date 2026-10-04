# Provenienza — `corpus/raw/models_original/`

## Dataset

**Golden UML Modelset** (v1, pubblicato il 2025-08-28): un insieme curato dalla comunità di
diagrammi delle classi UML (PlantUML) con descrizione testuale.

- Autori: Charlotte Verbruggen (TU Wien), Lukas Netz (RWTH Aachen University),
  Philipp-Lorenz Glaser (TU Wien), Marion Scholz (TU Wien), Christian Huemer (TU Wien),
  Marco Calamo (Sapienza Università di Roma), Bernhard Rumpe (RWTH Aachen University),
  Monique Snoeck (KU Leuven), Dominik Bork (TU Wien).
- Zenodo: <https://zenodo.org/records/16985872>. DOI: **10.5281/zenodo.16985873**, letto
  dalla pagina del record il 2026-10-01. Non è stato verificato se sia il DOI della v1 o il
  DOI "concept" che vale per tutte le versioni: controllarlo prima di citarlo nella tesi.
- Articolo associato: C. Verbruggen et al., "Toward a Community-Curated Golden Dataset of UML
  Models", MODELS 2025 Educators Symposium
  (<https://www.se-rwth.de/publications/Toward-a-Community-Curated-Golden-Dataset-of-UML-Models.pdf>).
- Sito del dataset: <https://golden-uml-modelset.vercel.app/>.

## Licenza

**Creative Commons Attribution 4.0 International (CC BY 4.0)**:
<https://creativecommons.org/licenses/by/4.0/legalcode> (sintesi:
<https://creativecommons.org/licenses/by/4.0/>).

**L'attribuzione è obbligatoria**. Ogni uso, tesi compresa, deve citare il dataset (autori,
titolo, DOI), indicare la licenza e dichiarare le modifiche fatte (sezione successiva).

## Modifiche

**I file originali non sono modificati.** Le 45 cartelle (`description.md`, `metadata.txt`,
`plantuml.txt`, `plantuml.png`, `plantuml.svg`, `extramaterial/`) restano come scaricate, e
nessuno script scrive in questa cartella. Correzioni e trasformazioni sono applicate a valle,
in `corpus/processed/corpus.jsonl` e `corpus/processed/apollon/`:

- correzioni dei diagrammi in `corpus/corrections/<id>.yaml`, tracciate nel campo
  `corrections_applied` di `corpus.jsonl`;
- esclusioni di paragrafi dalle descrizioni in `corpus/description_exclusions/<id>.yaml`
  (campo `description_exclusions_applied`);
- conversione da PlantUML ad Apollon JSON v4 con `corpus/apollon_convert.py`; i limiti
  della conversione sono in `corpus/apollon_limitations.md`.

La cronologia delle scelte è in `docs/decisions.md`.

## Fonti originali dei singoli modelli

Ogni `metadata.txt` riporta la fonte originale (`source`, `citation`, `contact`) e va
conservato. Riepilogo del 2026-10-01:

| `source` | modelli |
|---|---|
| KU Leuven, LIRIS — https://merode.econ.kuleuven.be/cases/index.asp | 12 |
| McGill University (citazione: Chen et al., MODELS 2023, doi:10.1109/MODELS58315.2023.00037) | 10 |
| TU Wien, Business Informatics Group | 10 |
| RWTH (incl. SWTExamWS1213, SWTExamWS1415) | 7 |
| KU Leuven, LIRIS — Handbook Principles of Database Management (Lemahieu et al., 2018) | 6 |
