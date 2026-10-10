# Retrieval BM25 sul test set De Bari (testset_2026-10-10_loo)

Configurazione congelata `config_bm25.yaml`: {'stopwords': True, 'stem': True, 'k1': 1.5, 'b': 0.75}. Commit `366ed7a` (working tree modificato), test set `testset-v1` invariato: True. Jaccard con il ground truth SOLO descrittivo.

Protocollo: leave-one-out (voce 112): candidati = 59 del corpus + gli altri 19 esercizi De Bari (78), indice BM25 rifittato per ogni esercizio; vicini dal test set nei top-3: 17/60, al rango 1: 5/20.

Fasce di score_norm del top-1 (cut-off congelati sul LOO): basso < 0.2893 <= medio < 0.3473 <= alto.

## Per esercizio

| # | Esercizio | top-1 (score_norm, J) | top-2 (score_norm, J) | top-3 (score_norm, J) | fascia | oracolo J@1 | ED | note |
|---|---|---|---|---|---|---|---|---|
| 1 | DB01_ProjectManagementSystem | ProjectManagement (0.361, 0.077) | ResearchCenter (0.356, 0.182) | eHome2020 (0.317, 0.000) | alto | 0.182 | 2.33 |  |
| 2 | DB02_HollywoodApproach | FilmSet (0.331, 0.000) | MilanLibrary (0.202, 0.043) | RealEstateAgency (0.186, 0.000) | medio | 0.083 | 1.33 |  |
| 3 | DB03_WordProcessor | Facepage (0.207, 0.067) | BuildingManagement (0.126, 0.000) | CardGameApp (0.109, 0.000) | basso | 0.083 | 4.67 | senza analogo (fascia bassa) |
| 4 | DB04_PatientRecordAndSchedulingSystem | TreatmentPlans (0.377, 0.111) | HospitalHouseMD (0.361, 0.200) | DB19_MyDoctor (0.285, 0.250) | alto | 0.250 | 3.33 |  |
| 5 | DB05_MovieShop | Kinepolis (0.319, 0.048) | DB20_OnlineShopping (0.243, 0.050) | Menso (0.202, 0.000) | medio | 0.111 | 2.33 |  |
| 6 | DB06_Flights | AirTravel (0.645, 0.235) | Boeing (0.164, 0.071) | DestroyBlockGame (0.092, 0.000) | alto | 0.235 | 3.67 | domain_overlap_static_example |
| 7 | DB07_BankSystem | DB16_OOBank (0.312, 0.133) | BankAccount (0.306, 0.200) | DB10_Restaurant (0.261, 0.000) | medio | 0.200 | 1.00 |  |
| 8 | DB08_VeterinaryClinic | DB10_Restaurant (0.302, 0.067) | DB09_AutoRepair (0.232, 0.143) | EUScienceConnect (0.229, 0.071) | medio | 0.154 | 2.00 |  |
| 9 | DB09_AutoRepair | RepairShops (0.309, 0.214) | Sober (0.263, 0.059) | TransportCompany (0.230, 0.050) | medio | 0.214 | 2.67 |  |
| 10 | DB10_Restaurant | Restaurant (0.396, 0.250) | DB08_VeterinaryClinic (0.243, 0.067) | EatAtHome (0.214, 0.167) | alto | 0.250 | 2.67 |  |
| 11 | DB11_Deliveries | HelpingHands (0.314, 0.059) | SellingGoods (0.274, 0.077) | EatAtHome (0.256, 0.100) | medio | 0.133 | 3.33 |  |
| 12 | DB12_Furniture | DB13_Factory (0.451, 0.000) | ClothingCompany (0.285, 0.071) | DB10_Restaurant (0.232, 0.000) | alto | 0.083 | 2.33 |  |
| 13 | DB13_Factory | DB12_Furniture (0.358, 0.000) | ClothingCompany (0.269, 0.067) | SellingGoods (0.220, 0.062) | alto | 0.125 | 1.67 |  |
| 14 | DB14_BicycleRental | DB13_Factory (0.273, 0.077) | DB09_AutoRepair (0.222, 0.000) | DB10_Restaurant (0.209, 0.077) | basso | 0.083 | 2.67 | senza analogo (fascia bassa) |
| 15 | DB15_SaturnIntManagement | TruckLogistics (0.236, 0.000) | RealEstateAgency (0.227, 0.000) | DB09_AutoRepair (0.222, 0.000) | basso | 0.056 | 4.33 | senza analogo (fascia bassa) |
| 16 | DB16_OOBank | BankAccount (0.435, 0.214) | Facepage (0.298, 0.053) | DB07_BankSystem (0.278, 0.133) | alto | 0.214 | 3.00 |  |
| 17 | DB17_PrepaidCellPhone | Boeing (0.211, 0.077) | AlphaInsurance (0.193, 0.059) | BankAccount (0.169, 0.000) | basso | 0.083 | 2.33 | senza analogo (fascia bassa) |
| 18 | DB18_LibrarySystem | MilanLibrary (0.464, 0.143) | DB19_MyDoctor (0.256, 0.071) | Musicmatic (0.215, 0.071) | alto | 0.143 | 1.67 |  |
| 19 | DB19_MyDoctor | LabTracker (0.412, 0.143) | DB04_PatientRecordAndSchedulingSystem (0.351, 0.250) | TreatmentPlans (0.273, 0.150) | alto | 0.250 | 4.00 |  |
| 20 | DB20_OnlineShopping | ClothingCompany (0.292, 0.214) | SellingGoods (0.289, 0.200) | BuildingManagement (0.244, 0.000) | medio | 0.250 | 4.67 |  |

## Riepiloghi (BM25, random su 20 seed, oracolo)

| Insieme | n | BM25 J@1 | BM25 J@3 | Random J@1 (sd) | Random J@3 (sd) | Oracolo J@1 | Oracolo J@3 | Spearman rho (p) |
|---|---|---|---|---|---|---|---|---|
| 20 esercizi | 20 | 0.106 | 0.085 | 0.015 (0.008) | 0.015 (0.004) | 0.159 | 0.121 | 0.31 (0.185) |
| 19 (senza es. 6) | 19 | 0.100 | 0.085 | 0.016 (0.008) | 0.016 (0.004) | 0.155 | 0.122 | 0.20 (0.407) |

## Distribuzioni: test set vs leave-one-out del corpus

| Distribuzione | n | media | min | q1 | mediana | q3 | max |
|---|---|---|---|---|---|---|---|
| score_norm top-1 LOO | 59 | 0.333 | 0.177 | 0.265 | 0.311 | 0.382 | 0.707 |
| score_norm top-1 test set | 20 | 0.350 | 0.207 | 0.300 | 0.325 | 0.400 | 0.645 |
| Jaccard top-1 LOO | 59 | 0.096 | 0.000 | 0.039 | 0.071 | 0.154 | 0.250 |
| Jaccard top-1 test set | 20 | 0.106 | 0.000 | 0.056 | 0.077 | 0.161 | 0.250 |

Fasce — LOO: basso 20, medio 19, alto 20; test set: basso 4, medio 7, alto 9.
