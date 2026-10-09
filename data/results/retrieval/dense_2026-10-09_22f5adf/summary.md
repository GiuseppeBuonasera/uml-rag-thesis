# Retriever denso e ibrido — leave-one-out sul corpus (dense_2026-10-09_22f5adf)

Voce 107 di `docs/decisions.md`. SOLO retrieval, nessuna generazione; test set NON letto. 59 query, 58 candidati ciascuna (esclusa solo la query, come BM25). Generato da `retrieval/analyze_dense.py`.

Analisi eseguita sul commit `22f5adfbe6ce` (con modifiche non committate). GT del corpus: 59 diagrammi, sha256 del contenuto `b400d1dd7954e8a97c88ff604bc47f294e7eca2cb17d9cd7dd680542fd5db5fd` (JSON canonico dei `diagram_apollon_json`, indipendente dagli a capo); file `corpus/processed/corpus.jsonl` sha256 `01ef9a52fa255f07…`.

**Le misure servono SOLO a scegliere il modello denso.** J e Jt sono lessicali sui nomi del GT e favoriscono BM25 per costruzione: il confronto BM25 / denso / ibrido si decide con le generazioni sull'insieme di sviluppo (voce 107, precisazione 1).

## Pertinenza (media sulle 59 query della media dei primi k)

| Retriever | J@1 | J@2 | J@3 | Jt@1 | Jt@2 | Jt@3 | S@1 | S@2 | S@3 |
|---|---|---|---|---|---|---|---|---|---|
| casuale (20 seed: media ± sd) | 0.013 ± 0.004 | 0.014 ± 0.003 | 0.013 ± 0.002 | 0.018 ± 0.005 | 0.019 ± 0.003 | 0.018 ± 0.002 | 0.608 ± 0.024 | 0.605 ± 0.016 | 0.607 ± 0.013 |
| BM25 | 0.096 | 0.078 | 0.067 | 0.116 | 0.095 | 0.083 | 0.660 | 0.672 | 0.673 |
| **all-MiniLM-L6-v2** (scelto) | 0.087 | 0.066 | 0.054 | 0.105 | 0.083 | 0.070 | 0.647 | 0.662 | 0.646 |
| bge-small-en-v1.5 | 0.073 | 0.056 | 0.053 | 0.091 | 0.071 | 0.068 | 0.644 | 0.650 | 0.647 |
| gte-modernbert-base | 0.067 | 0.060 | 0.055 | 0.084 | 0.076 | 0.069 | 0.666 | 0.662 | 0.653 |
| Ibrido RRF (BM25 + all-MiniLM-L6-v2) | 0.093 | 0.072 | 0.063 | 0.113 | 0.091 | 0.081 | 0.661 | 0.656 | 0.662 |
| oracolo (massimo per misura) | 0.132 | 0.110 | 0.099 | 0.155 | 0.133 | 0.120 | 0.929 | 0.913 | 0.903 |

Ibrido RRF con gli altri densi (solo descrittivo):

| Retriever | J@1 | J@3 | Jt@1 | Jt@3 | S@1 | S@3 |
|---|---|---|---|---|---|---|
| Ibrido RRF (BM25 + bge-small-en-v1.5) | 0.088 | 0.064 | 0.108 | 0.084 | 0.665 | 0.659 |
| Ibrido RRF (BM25 + gte-modernbert-base) | 0.093 | 0.066 | 0.114 | 0.084 | 0.666 | 0.669 |

## Regola di scelta del modello denso (fissata prima dei calcoli)

Jt@3 massimo; modelli entro 0.01 dal migliore in parità, vince il più piccolo.

| Modello | parametri (M) | Jt@3 | distanza dal migliore |
|---|---|---|---|
| all-MiniLM-L6-v2 | 22.7 | 0.0697 | 0.0000 |
| gte-modernbert-base | 149 | 0.0685 | 0.0012 |
| bge-small-en-v1.5 | 33.4 | 0.0683 | 0.0014 |

- In parità: all-MiniLM-L6-v2, bge-small-en-v1.5, gte-modernbert-base. **Scelto: `sentence-transformers/all-MiniLM-L6-v2`** (revisione `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`).
- Bootstrap al 95% (1000 ricampionamenti delle query, seme 0; solo descrittivo, la regola non cambia):
  - Jt@3 all-MiniLM-L6-v2 − gte-modernbert-base: +0.0012 [-0.0044, +0.0066]
  - Jt@3 all-MiniLM-L6-v2 − BM25: -0.0137 [-0.0212, -0.0063]

## Sovrapposizione dei top-3 tra BM25 e ciascun denso

| Denso | media di \|∩\| / 3 | stesso top-1 | query con ∩ = 0 / 1 / 2 / 3 |
|---|---|---|---|
| all-MiniLM-L6-v2 | 0.407 | 46% (27/59) | 13 / 25 / 16 / 5 |
| bge-small-en-v1.5 | 0.435 | 46% (27/59) | 9 / 29 / 15 / 6 |
| gte-modernbert-base | 0.356 | 36% (21/59) | 16 / 25 / 16 / 2 |

## Hubness

| Retriever | distinti al rango 1 | distinti nei top-3 | mai nei top-3 | max al rango 1 | max nei top-3 |
|---|---|---|---|---|---|
| BM25 | 39 | 54 | 5 | 4 (Facepage) | 9 (University) |
| all-MiniLM-L6-v2 | 42 | 57 | 2 | 4 (TransportCompany) | 12 (TransportCompany) |
| bge-small-en-v1.5 | 42 | 52 | 7 | 3 (EatAtHome) | 10 (TruckLogistics) |
| gte-modernbert-base | 33 | 44 | 15 | 8 (TransportCompany) | 17 (TransportCompany) |
| Ibrido RRF (BM25 + all-MiniLM-L6-v2) | 40 | 55 | 4 | 3 (SmartHomeAutomationSystem) | 13 (EatAtHome) |

Atteso con distribuzione uniforme nei top-3: 3.0 per candidato.

## Le 3 query più divergenti tra BM25 e all-MiniLM-L6-v2

Ordinate per intersezione dei top-3 crescente, poi per id. Titoli = campo `name` del corpus; tra parentesi Jt con la query.

- **BankAccount** (BankAccount), ∩ = 0
  - BM25: Facepage (Facepage, Jt 0.07); PizzaDeliveryWithEntertainment (PizzaDeliveryWithEntertainment, Jt 0.07); HelpingHands (Helping Hands, Jt 0.00)
  - all-MiniLM-L6-v2: SellingGoods (SellingGoods, Jt 0.09); Hospital (Hospital, Jt 0.00); School (School, Jt 0.00)
  - Ibrido RRF (BM25 + all-MiniLM-L6-v2): Facepage (Facepage, Jt 0.07); SellingGoods (SellingGoods, Jt 0.09); GameArea (BoardGameArea, Jt 0.00)
- **Bookmaker** (Bookmaker), ∩ = 0
  - BM25: HomeForTheElderly (HomeForTheElderly, Jt 0.06); University (University, Jt 0.00); OilWells (Oil Wells, Jt 0.00)
  - all-MiniLM-L6-v2: CardGameApp (CardGameApp, Jt 0.00); TeamSportsScoutingSystem (Team Sports Scouting System, Jt 0.04); FitnessCompanyConan (FitnessCompanyConan, Jt 0.07)
  - Ibrido RRF (BM25 + all-MiniLM-L6-v2): FitnessCompanyConan (FitnessCompanyConan, Jt 0.07); CelO (CelO, Jt 0.05); CourseManagement (Course Management, Jt 0.00)
- **CelO** (CelO), ∩ = 0
  - BM25: ResearchCenter (Research Center, Jt 0.00); AlphaInsurance (AlphaInsurance, Jt 0.00); SellingGoods (SellingGoods, Jt 0.00)
  - all-MiniLM-L6-v2: PizzaDeliveryWithEntertainment (PizzaDeliveryWithEntertainment, Jt 0.00); FitnessCompanyConan (FitnessCompanyConan, Jt 0.05); Sightseeing (Sightseeing, Jt 0.05)
  - Ibrido RRF (BM25 + all-MiniLM-L6-v2): PizzaDeliveryWithEntertainment (PizzaDeliveryWithEntertainment, Jt 0.00); ResearchCenter (Research Center, Jt 0.00); TransportCompany (TransportCompany, Jt 0.04)

## Modelli, troncamenti, tempi (CPU)

| Modello | revisione | limite | testi troncati | mediana / max token | dim. | caricamento | embedding 59 testi |
|---|---|---|---|---|---|---|---|
| sentence-transformers/all-MiniLM-L6-v2 | `1110a243fdf4` | 256 | 37/59 | 289 / 814 | 384 | 8.49 s | 0.97 s (16.5 ms/testo) |
| BAAI/bge-small-en-v1.5 | `5c38ec7c405e` | 512 | 12/59 | 289 / 814 | 384 | 0.18 s | 2.72 s (46.1 ms/testo) |
| Alibaba-NLP/gte-modernbert-base | `e7f32e3c00f9` | 8192 | 0/59 | 297 / 798 | 768 | 0.42 s | 105.58 s (1789.5 ms/testo) |

Versioni: python 3.12.10, sentence-transformers 6.1.0, transformers 5.19.0, torch 2.10.0+cpu, tokenizers 0.23.3, huggingface_hub 1.33.0, numpy 2.2.6, torch_threads 8, HF_HUB_OFFLINE 1.

