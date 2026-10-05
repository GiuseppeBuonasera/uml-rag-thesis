# Retrieval BM25 sul test set De Bari (testset_2026-10-04_stop2)

Configurazione congelata `config_bm25.yaml`: {'stopwords': True, 'stem': True, 'k1': 1.5, 'b': 0.75}. Commit `c161bab` (working tree modificato), test set `testset-v1` invariato: True. Jaccard con il ground truth SOLO descrittivo.

Fasce di score_norm del top-1 (cut-off congelati sul LOO): basso < 0.2893 <= medio < 0.3473 <= alto.

## Per esercizio

| # | Esercizio | top-1 (score_norm, J) | top-2 (score_norm, J) | top-3 (score_norm, J) | fascia | oracolo J@1 | ED | note |
|---|---|---|---|---|---|---|---|---|
| 1 | DB01_ProjectManagementSystem | ProjectManagement (0.347, 0.077) | ResearchCenter (0.328, 0.182) | eHome2020 (0.309, 0.000) | medio | 0.182 | 2.33 |  |
| 2 | DB02_HollywoodApproach | FilmSet (0.322, 0.000) | MilanLibrary (0.196, 0.043) | RealEstateAgency (0.183, 0.000) | medio | 0.083 | 1.33 |  |
| 3 | DB03_WordProcessor | Facepage (0.203, 0.067) | BuildingManagement (0.142, 0.000) | CardGameApp (0.120, 0.000) | basso | 0.083 | 4.67 | senza analogo (fascia bassa) |
| 4 | DB04_PatientRecordAndSchedulingSystem | TreatmentPlans (0.405, 0.111) | HospitalHouseMD (0.389, 0.200) | LabTracker (0.306, 0.167) | alto | 0.200 | 3.33 |  |
| 5 | DB05_MovieShop | Kinepolis (0.360, 0.048) | Menso (0.231, 0.000) | EatAtHome (0.180, 0.067) | alto | 0.111 | 2.33 |  |
| 6 | DB06_Flights | AirTravel (0.643, 0.235) | Boeing (0.163, 0.071) | DestroyBlockGame (0.091, 0.000) | alto | 0.235 | 3.67 | domain_overlap_static_example |
| 7 | DB07_BankSystem | BankAccount (0.306, 0.200) | SellingGoods (0.285, 0.077) | ClothingCompany (0.219, 0.083) | medio | 0.200 | 1.00 |  |
| 8 | DB08_VeterinaryClinic | EUScienceConnect (0.254, 0.071) | LabTracker (0.220, 0.100) | PizzaDeliveryWithEntertainment (0.189, 0.000) | basso | 0.154 | 2.00 | senza analogo (fascia bassa) |
| 9 | DB09_AutoRepair | RepairShops (0.319, 0.214) | Sober (0.269, 0.059) | TransportCompany (0.236, 0.050) | medio | 0.214 | 2.67 |  |
| 10 | DB10_Restaurant | Restaurant (0.400, 0.250) | EatAtHome (0.212, 0.167) | PizzaDeliveryWithEntertainment (0.199, 0.000) | alto | 0.250 | 2.67 |  |
| 11 | DB11_Deliveries | HelpingHands (0.319, 0.059) | SellingGoods (0.270, 0.077) | ProjectManagement (0.252, 0.000) | medio | 0.111 | 3.33 |  |
| 12 | DB12_Furniture | ClothingCompany (0.312, 0.071) | SellingGoods (0.242, 0.067) | TransportCompany (0.219, 0.053) | medio | 0.083 | 2.33 |  |
| 13 | DB13_Factory | ClothingCompany (0.316, 0.067) | SellingGoods (0.248, 0.062) | Musicmatic (0.184, 0.000) | medio | 0.105 | 1.67 |  |
| 14 | DB14_BicycleRental | TransportCompany (0.211, 0.000) | Sober (0.195, 0.000) | EUScienceConnect (0.194, 0.000) | basso | 0.062 | 2.67 | senza analogo (fascia bassa) |
| 15 | DB15_SaturnIntManagement | TruckLogistics (0.236, 0.000) | RealEstateAgency (0.229, 0.000) | Sober (0.221, 0.000) | basso | 0.050 | 4.33 | senza analogo (fascia bassa) |
| 16 | DB16_OOBank | BankAccount (0.470, 0.214) | Facepage (0.322, 0.053) | Gym (0.223, 0.048) | alto | 0.214 | 3.00 |  |
| 17 | DB17_PrepaidCellPhone | Boeing (0.203, 0.077) | AlphaInsurance (0.185, 0.059) | BankAccount (0.174, 0.000) | basso | 0.077 | 2.33 | senza analogo (fascia bassa) |
| 18 | DB18_LibrarySystem | MilanLibrary (0.492, 0.143) | Musicmatic (0.243, 0.071) | HotelBookingManagementSystem (0.213, 0.000) | alto | 0.143 | 1.67 |  |
| 19 | DB19_MyDoctor | LabTracker (0.424, 0.143) | TreatmentPlans (0.273, 0.150) | HospitalHouseMD (0.265, 0.154) | alto | 0.154 | 4.00 |  |
| 20 | DB20_OnlineShopping | ClothingCompany (0.305, 0.214) | SellingGoods (0.305, 0.200) | PizzaDeliveryWithEntertainment (0.257, 0.118) | medio | 0.250 | 4.67 |  |

## Riepiloghi (BM25, random su 20 seed, oracolo)

| Insieme | n | BM25 J@1 | BM25 J@3 | Random J@1 (sd) | Random J@3 (sd) | Oracolo J@1 | Oracolo J@3 | Spearman rho (p) |
|---|---|---|---|---|---|---|---|---|
| 20 esercizi | 20 | 0.113 | 0.077 | 0.015 (0.009) | 0.014 (0.005) | 0.148 | 0.105 | 0.49 (0.027) |
| 19 (senza es. 6) | 19 | 0.107 | 0.076 | 0.015 (0.010) | 0.015 (0.005) | 0.144 | 0.105 | 0.42 (0.076) |

## Distribuzioni: test set vs leave-one-out del corpus

| Distribuzione | n | media | min | q1 | mediana | q3 | max |
|---|---|---|---|---|---|---|---|
| score_norm top-1 LOO | 59 | 0.333 | 0.177 | 0.265 | 0.311 | 0.382 | 0.707 |
| score_norm top-1 test set | 20 | 0.342 | 0.203 | 0.292 | 0.319 | 0.401 | 0.643 |
| Jaccard top-1 LOO | 59 | 0.096 | 0.000 | 0.039 | 0.071 | 0.154 | 0.250 |
| Jaccard top-1 test set | 20 | 0.113 | 0.000 | 0.065 | 0.077 | 0.204 | 0.250 |

Fasce — LOO: basso 20, medio 19, alto 20; test set: basso 5, medio 8, alto 7.

## Hubness

Solo descrittivo (da `loo_2026-10-04_stop1/loo_top3.csv` e `testset_2026-10-04_stop2/testset_top3.csv`; tabella completa in `hubness.csv`). Nessuna modifica alla configurazione congelata.

- Candidati distinti al rank 1: LOO 39 su 59 (59 query); test set 17 su 59 (20 query).
- Candidati distinti nei top-3: LOO 54; test set 33.
- Candidati mai nei top-3: LOO 5; test set 26.
- Massimo al rank 1: LOO 4; test set 3. Massimo nei top-3: LOO 9 (atteso uniforme 3.0); test set 5 (atteso 1.0).

| Candidato | LOO rank 1 | LOO top-3 | test rank 1 | test top-3 |
|---|---|---|---|---|
| SellingGoods | 2 | 6 | 0 | 5 |
| PizzaDeliveryWithEntertainment | 1 | 8 | 0 | 3 |
| TransportCompany | 3 | 7 | 1 | 3 |
| University | 3 | 9 | 0 | 0 |
| Menso | 3 | 7 | 0 | 1 |
| HelpingHands | 1 | 7 | 1 | 1 |
| Musicmatic | 1 | 6 | 0 | 2 |
| ClothingCompany | 1 | 3 | 3 | 4 |
| MilanLibrary | 1 | 5 | 1 | 2 |
| Facepage | 4 | 4 | 1 | 2 |
| RepairShops | 2 | 5 | 1 | 1 |
| LabTracker | 0 | 3 | 1 | 3 |
| Sober | 1 | 3 | 0 | 3 |
| TreatmentPlans | 3 | 3 | 1 | 2 |
| Boeing | 1 | 3 | 1 | 2 |
| DestroyBlockGame | 2 | 4 | 0 | 1 |
| EatAtHome | 2 | 3 | 0 | 2 |
| TileOGame | 2 | 5 | 0 | 0 |
| AlphaInsurance | 1 | 4 | 0 | 1 |
| EUScienceConnect | 0 | 3 | 1 | 2 |
| HospitalHouseMD | 1 | 3 | 0 | 2 |
| Restaurant | 0 | 4 | 1 | 1 |
| BuildingManagement | 0 | 4 | 0 | 1 |
| CardGameApp | 0 | 4 | 0 | 1 |
