# Balanced48 openSMILE/eGeMAPS Pilot

- Patient roots: 48
- eGeMAPS feature columns: 92
- CV: repeated stratified 4-fold, repeats=20
- Preprocessing is inside each CV fold: median imputation, scaling, PCA, logistic regression.
- Metadata source: windowed feature metadata

## Label Counts

| subtype | n_roots |
| --- | --- |
| Conduction | 12 |
| Broca | 12 |
| Anomic | 12 |
| Wernicke | 12 |

## Model Summary

| model | mean_balanced_accuracy | ba_ci_low | ba_ci_high | mean_macro_f1 | f1_ci_low | f1_ci_high |
| --- | --- | --- | --- | --- | --- | --- |
| wab_only | 0.554 | 0.529 | 0.579 | 0.533 | 0.508 | 0.559 |
| egemaps_plus_wab | 0.430 | 0.400 | 0.459 | 0.410 | 0.380 | 0.441 |
| egemaps_only | 0.384 | 0.354 | 0.415 | 0.363 | 0.332 | 0.391 |
| random_features | 0.317 | 0.285 | 0.347 | 0.299 | 0.268 | 0.329 |
| shuffled_labels | 0.299 | 0.278 | 0.320 | 0.284 | 0.263 | 0.304 |
| majority | 0.250 | 0.250 | 0.250 | 0.100 | 0.100 | 0.100 |

## Pairwise Acoustic Contrasts

| contrast | model | n | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- |
| Wernicke_vs_Anomic | wab_only | 24 | 0.917 | 0.916 |
| Wernicke_vs_Anomic | egemaps_only | 24 | 0.625 | 0.624 |
| Wernicke_vs_Anomic | egemaps_plus_wab | 24 | 0.708 | 0.708 |
| Wernicke_vs_Anomic | random_features | 24 | 0.333 | 0.329 |
| Wernicke_vs_Conduction | wab_only | 24 | 0.833 | 0.833 |
| Wernicke_vs_Conduction | egemaps_only | 24 | 0.792 | 0.791 |
| Wernicke_vs_Conduction | egemaps_plus_wab | 24 | 0.833 | 0.833 |
| Wernicke_vs_Conduction | random_features | 24 | 0.500 | 0.497 |
| Conduction_vs_Anomic | wab_only | 24 | 0.875 | 0.875 |
| Conduction_vs_Anomic | egemaps_only | 24 | 0.500 | 0.500 |
| Conduction_vs_Anomic | egemaps_plus_wab | 24 | 0.458 | 0.457 |
| Conduction_vs_Anomic | random_features | 24 | 0.458 | 0.450 |
| Broca_vs_Anomic | wab_only | 24 | 0.958 | 0.958 |
| Broca_vs_Anomic | egemaps_only | 24 | 0.667 | 0.667 |
| Broca_vs_Anomic | egemaps_plus_wab | 24 | 0.667 | 0.667 |
| Broca_vs_Anomic | random_features | 24 | 0.500 | 0.497 |

## eGeMAPS Feature Families

| feature_family | n_features | mean_balanced_accuracy | ba_ci_low | ba_ci_high | mean_macro_f1 | f1_ci_low | f1_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| timing_coverage | 10 | 0.445 | 0.416 | 0.474 | 0.419 | 0.389 | 0.447 |
| loudness_intensity | 12 | 0.361 | 0.334 | 0.386 | 0.334 | 0.308 | 0.360 |
| formants | 18 | 0.319 | 0.294 | 0.344 | 0.289 | 0.264 | 0.313 |
| spectral_mfcc | 41 | 0.307 | 0.280 | 0.335 | 0.278 | 0.251 | 0.306 |
| voice_quality | 16 | 0.287 | 0.263 | 0.311 | 0.265 | 0.242 | 0.288 |
| pitch_f0 | 10 | 0.290 | 0.267 | 0.316 | 0.256 | 0.234 | 0.281 |

## Leave-Corpus-Out Checks

| model | held_out_corpus | n_test | test_classes | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- | --- |
| wab_only | Fridriksson-2 | 16 | Anomic,Broca,Conduction,Wernicke | 0.662 | 0.637 |
| egemaps_only | Fridriksson-2 | 16 | Anomic,Broca,Conduction,Wernicke | 0.312 | 0.177 |
| egemaps_plus_wab | Fridriksson-2 | 16 | Anomic,Broca,Conduction,Wernicke | 0.362 | 0.271 |
| random_features | Fridriksson-2 | 16 | Anomic,Broca,Conduction,Wernicke | 0.275 | 0.263 |
| wab_only | Kurland | 5 | Anomic,Broca,Wernicke | 0.889 | 0.822 |
| egemaps_only | Kurland | 5 | Anomic,Broca,Wernicke | 0.444 | 0.300 |
| egemaps_plus_wab | Kurland | 5 | Anomic,Broca,Wernicke | 0.556 | 0.444 |
| random_features | Kurland | 5 | Anomic,Broca,Wernicke | 0.778 | 0.542 |
| wab_only | QAB | 13 | Anomic,Broca,Conduction | 0.595 | 0.444 |
| egemaps_only | QAB | 13 | Anomic,Broca,Conduction | 0.000 | 0.000 |
| egemaps_plus_wab | QAB | 13 | Anomic,Broca,Conduction | 0.083 | 0.083 |
| random_features | QAB | 13 | Anomic,Broca,Conduction | 0.500 | 0.286 |
| wab_only | Tucson | 8 | Anomic,Broca,Conduction,Wernicke | 0.417 | 0.458 |
| egemaps_only | Tucson | 8 | Anomic,Broca,Conduction,Wernicke | 0.333 | 0.243 |
| egemaps_plus_wab | Tucson | 8 | Anomic,Broca,Conduction,Wernicke | 0.333 | 0.225 |
| random_features | Tucson | 8 | Anomic,Broca,Conduction,Wernicke | 0.250 | 0.167 |

## Corpus/Subtype Counts

| corpus | subtype | n_roots |
| --- | --- | --- |
| Adler | Wernicke | 1 |
| Fridriksson-2 | Anomic | 5 |
| Fridriksson-2 | Broca | 5 |
| Fridriksson-2 | Conduction | 4 |
| Fridriksson-2 | Wernicke | 2 |
| Kurland | Anomic | 1 |
| Kurland | Broca | 1 |
| Kurland | Wernicke | 3 |
| QAB | Anomic | 4 |
| QAB | Broca | 2 |
| QAB | Conduction | 7 |
| Richardson | Wernicke | 1 |
| SCALE | Broca | 1 |
| SCALE | Wernicke | 1 |
| Tucson | Anomic | 2 |
| Tucson | Broca | 2 |
| Tucson | Conduction | 1 |
| Tucson | Wernicke | 3 |
| UNH | Broca | 1 |
| Williamson | Wernicke | 1 |

## Interpretation

This is a leakage-safe pilot, not a final replication. It uses one session per derived patient root, balanced subtype labels, standard eGeMAPS functionals, and fold-internal preprocessing. The next step is to expand this extraction across more patient roots and add corpus-held-out evaluation.
