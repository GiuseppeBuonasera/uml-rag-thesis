# Note di trascrizione — De Bari 1: Project Management System

Fonte immagine: `corpus/raw/debari_test/_images/db01.png` (1383x736). Ingrandimento 1.8x della zona
x 390-990 / y 400-690 (Project, Manager, Team, etichette con triangoli).

## Elementi esclusi (non di modello)
- Titolo della figura "Figure 2-15. Class diagram" (cornice/titolo).

## Ambiguità e interpretazioni
1. **Nomi con spazi → PascalCase** (convenzione approvata il 2026-10-02): classe "Work Product" →
   `WorkProduct`; attributi "Percent Complete" → `PercentComplete`, "Start Date" → `StartDate`,
   "End Date" → `EndDate`, "Phone Number" → `PhoneNumber`; operazioni "Initiate Project" →
   `InitiateProject()`, "Terminate Project" → `TerminateProject()`.
2. **Operazioni senza parentesi** (regola approvata il 2026-10-03, stessa lettura dell'xlsx): nel terzo
   comparto (WorkProduct, Requirement, System, Manager) i nomi sono scritti senza "()". Sono operazioni
   per posizione nel riquadro, quindi trascritte come `Nome()` senza parametri né tipo di ritorno (mai
   inventati). Team e
   Project hanno solo due comparti: le voci sono attributi.
3. **Nessuna molteplicità e nessun ruolo** su nessuna relazione: gli estremi sono stati controllati tutti
   e non riportano testo.
4. **Etichette con triangolo del verso di lettura**: Input ◄, Output ►, Manage ►, Execute ◄ (Lead
   senza triangolo). Riga PlantUML scritta nel verso di lettura (Project → Requirement/System,
   Manager → Project, Team → Project). Il verso viene comunque scartato dalla conversione
   (`apollon_limitations.md` §3). Classificazione approvata il 2026-10-03: tutte associazioni. Input e
   Output, pur essendo anche sostantivi, sono nomi di associazione perché hanno il triangolo pieno del
   verso di lettura, che i nomi di ruolo non hanno.
5. Attributi senza tipo nell'immagine: trascritti senza tipo (warning "senza tipo dichiarato").

## Analysis.xlsx ("Part 2 - 1")
Nessuna discrepanza: classi, membri, relazioni e conteggi (6 / 17 / 7) coincidono.
