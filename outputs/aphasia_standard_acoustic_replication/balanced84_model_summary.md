# Balanced84 openSMILE/eGeMAPS Pilot

- Patient roots: 84
- eGeMAPS feature columns: 92
- CV: repeated stratified 4-fold, repeats=20
- Preprocessing is inside each CV fold: median imputation, scaling, PCA, logistic regression.
- Metadata source: transcript manifest

## Label Counts

| subtype | n_roots |
| --- | --- |
| Conduction | 21 |
| Broca | 21 |
| Anomic | 21 |
| Wernicke | 21 |

## Model Summary

| model | mean_balanced_accuracy | ba_ci_low | ba_ci_high | mean_macro_f1 | f1_ci_low | f1_ci_high |
| --- | --- | --- | --- | --- | --- | --- |
| wab_only | 0.549 | 0.528 | 0.570 | 0.526 | 0.504 | 0.547 |
| egemaps_plus_wab | 0.457 | 0.434 | 0.481 | 0.440 | 0.417 | 0.463 |
| egemaps_only | 0.407 | 0.386 | 0.427 | 0.391 | 0.371 | 0.411 |
| random_features | 0.268 | 0.248 | 0.288 | 0.255 | 0.234 | 0.276 |
| shuffled_labels | 0.218 | 0.198 | 0.238 | 0.207 | 0.189 | 0.225 |
| majority | 0.250 | 0.250 | 0.250 | 0.096 | 0.096 | 0.096 |

## Pairwise Acoustic Contrasts

| contrast | model | n | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- |
| Wernicke_vs_Anomic | wab_only | 42 | 0.976 | 0.976 |
| Wernicke_vs_Anomic | egemaps_only | 42 | 0.643 | 0.643 |
| Wernicke_vs_Anomic | egemaps_plus_wab | 42 | 0.667 | 0.666 |
| Wernicke_vs_Anomic | random_features | 42 | 0.524 | 0.524 |
| Wernicke_vs_Conduction | wab_only | 42 | 0.738 | 0.738 |
| Wernicke_vs_Conduction | egemaps_only | 42 | 0.690 | 0.689 |
| Wernicke_vs_Conduction | egemaps_plus_wab | 42 | 0.714 | 0.712 |
| Wernicke_vs_Conduction | random_features | 42 | 0.238 | 0.238 |
| Conduction_vs_Anomic | wab_only | 42 | 0.881 | 0.880 |
| Conduction_vs_Anomic | egemaps_only | 42 | 0.571 | 0.568 |
| Conduction_vs_Anomic | egemaps_plus_wab | 42 | 0.667 | 0.664 |
| Conduction_vs_Anomic | random_features | 42 | 0.429 | 0.427 |
| Broca_vs_Anomic | wab_only | 42 | 0.929 | 0.928 |
| Broca_vs_Anomic | egemaps_only | 42 | 0.619 | 0.618 |
| Broca_vs_Anomic | egemaps_plus_wab | 42 | 0.714 | 0.712 |
| Broca_vs_Anomic | random_features | 42 | 0.548 | 0.547 |

## eGeMAPS Feature Families

| feature_family | n_features | mean_balanced_accuracy | ba_ci_low | ba_ci_high | mean_macro_f1 | f1_ci_low | f1_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| timing_coverage | 10 | 0.463 | 0.443 | 0.483 | 0.449 | 0.429 | 0.469 |
| loudness_intensity | 12 | 0.390 | 0.369 | 0.410 | 0.364 | 0.346 | 0.385 |
| voice_quality | 16 | 0.373 | 0.351 | 0.395 | 0.355 | 0.334 | 0.378 |
| formants | 18 | 0.344 | 0.326 | 0.361 | 0.327 | 0.309 | 0.346 |
| spectral_mfcc | 41 | 0.305 | 0.284 | 0.326 | 0.286 | 0.265 | 0.308 |
| pitch_f0 | 10 | 0.322 | 0.301 | 0.342 | 0.281 | 0.263 | 0.302 |

## Leave-Corpus-Out Checks

| model | held_out_corpus | n_test | test_classes | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- | --- |
| wab_only | Fridriksson-2 | 27 | Anomic,Broca,Conduction,Wernicke | 0.576 | 0.565 |
| egemaps_only | Fridriksson-2 | 27 | Anomic,Broca,Conduction,Wernicke | 0.312 | 0.216 |
| egemaps_plus_wab | Fridriksson-2 | 27 | Anomic,Broca,Conduction,Wernicke | 0.312 | 0.215 |
| random_features | Fridriksson-2 | 27 | Anomic,Broca,Conduction,Wernicke | 0.240 | 0.280 |
| wab_only | Kurland | 6 | Anomic,Broca,Wernicke | 0.611 | 0.600 |
| egemaps_only | Kurland | 6 | Anomic,Broca,Wernicke | 0.444 | 0.357 |
| egemaps_plus_wab | Kurland | 6 | Anomic,Broca,Wernicke | 0.444 | 0.357 |
| random_features | Kurland | 6 | Anomic,Broca,Wernicke | 0.778 | 0.575 |
| wab_only | QAB | 14 | Anomic,Broca,Conduction | 0.651 | 0.444 |
| egemaps_only | QAB | 14 | Anomic,Broca,Conduction | 0.381 | 0.198 |
| egemaps_plus_wab | QAB | 14 | Anomic,Broca,Conduction | 0.381 | 0.241 |
| random_features | QAB | 14 | Anomic,Broca,Conduction | 0.083 | 0.071 |
| wab_only | SCALE | 5 | Broca,Wernicke | 0.125 | 0.083 |
| egemaps_only | SCALE | 5 | Broca,Wernicke | 1.000 | 1.000 |
| egemaps_plus_wab | SCALE | 5 | Broca,Wernicke | 0.375 | 0.250 |
| random_features | SCALE | 5 | Broca,Wernicke | 0.750 | 0.417 |
| wab_only | Tucson | 14 | Anomic,Broca,Conduction,Wernicke | 0.417 | 0.397 |
| egemaps_only | Tucson | 14 | Anomic,Broca,Conduction,Wernicke | 0.312 | 0.215 |
| egemaps_plus_wab | Tucson | 14 | Anomic,Broca,Conduction,Wernicke | 0.312 | 0.215 |
| random_features | Tucson | 14 | Anomic,Broca,Conduction,Wernicke | 0.417 | 0.433 |

## Corpus/Subtype Counts

| corpus | subtype | n_roots |
| --- | --- | --- |
| ACWT | Wernicke | 1 |
| Adler | Wernicke | 2 |
| BU | Anomic | 1 |
| Elman | Wernicke | 1 |
| Fridriksson-2 | Anomic | 8 |
| Fridriksson-2 | Broca | 9 |
| Fridriksson-2 | Conduction | 8 |
| Fridriksson-2 | Wernicke | 2 |
| Kansas | Wernicke | 2 |
| Kurland | Anomic | 1 |
| Kurland | Broca | 2 |
| Kurland | Wernicke | 3 |
| NEURAL | Anomic | 1 |
| NEURAL | Conduction | 1 |
| NEURAL-2 | Anomic | 1 |
| NEURAL-2 | Broca | 1 |
| QAB | Anomic | 4 |
| QAB | Broca | 3 |
| QAB | Conduction | 7 |
| Richardson | Anomic | 1 |
| Richardson | Conduction | 1 |
| Richardson | Wernicke | 1 |
| SCALE | Broca | 1 |
| SCALE | Wernicke | 4 |
| SouthAL | Broca | 1 |
| Tucson | Anomic | 4 |
| Tucson | Broca | 3 |
| Tucson | Conduction | 4 |
| Tucson | Wernicke | 3 |
| UNH | Broca | 1 |
| Whiteside | Wernicke | 1 |
| Williamson | Wernicke | 1 |

## Interpretation

This is a leakage-safe pilot, not a final replication. It uses one session per derived patient root, balanced subtype labels, standard eGeMAPS functionals, and fold-internal preprocessing. The next step is to expand this extraction across more patient roots and add corpus-held-out evaluation.
