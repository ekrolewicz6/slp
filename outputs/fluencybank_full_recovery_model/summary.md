# Full FluencyBank Transcript Recovery Model

**Question:** after full FluencyBank transcript access, does early within-child transcript movement predict recovered versus persistent stuttering better than earliest-session state?

## Data Audit

- Local FluencyBank `.cha` files scanned: 1,999
- Parsed feature rows with at least the target-utterance threshold: 1,922
- Recovery-labelled CWS participants with usable features: 253
- Labelled participants with at least two usable sessions: 152

### Corpus Inventory

| corpus | cha_files | parsed_feature_rows | parse_success_rate | participants_with_features | labelled_recovery_participants | persistent_participants | recovered_participants | median_sessions_per_featured_participant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IISRP | 752 | 739 | 0.983 | 122 | 87 | 19 | 68 | 7.000 |
| Purdue | 359 | 359 | 1.000 | 215 | 84 | 42 | 42 | 1.000 |
| UMD-CMU | 143 | 140 | 0.979 | 29 | 0 | 0 | 0 | 6.000 |
| Ulm | 140 | 140 | 1.000 | 140 | 0 | 0 | 0 | 1.000 |
| Voices-AWS | 102 | 89 | 0.873 | 89 | 0 | 0 | 0 | 1.000 |
| Tellis | 95 | 64 | 0.674 | 13 | 0 | 0 | 0 | 5.000 |
| Wagovich | 90 | 90 | 1.000 | 9 | 0 | 0 | 0 | 10.000 |
| IISRP-new | 89 | 87 | 0.978 | 87 | 82 | 15 | 67 | 1.000 |
| Ratner | 60 | 59 | 0.983 | 49 | 0 | 0 | 0 | 1.000 |
| Sawyer | 51 | 51 | 1.000 | 51 | 0 | 0 | 0 | 1.000 |
| Voices-CWS | 48 | 36 | 0.750 | 36 | 0 | 0 | 0 | 1.000 |
| Hakim | 32 | 32 | 1.000 | 16 | 0 | 0 | 0 | 2.000 |
| Maxfield | 17 | 17 | 1.000 | 17 | 0 | 0 | 0 | 1.000 |
| Brejon | 8 | 8 | 1.000 | 8 | 0 | 0 | 0 | 1.000 |
| Voices-AWC | 7 | 7 | 1.000 | 7 | 0 | 0 | 0 | 1.000 |
| VanZaalen | 5 | 3 | 0.600 | 3 | 0 | 0 | 0 | 1.000 |
| Examples | 1 | 1 | 1.000 | 1 | 0 | 0 | 0 | 1.000 |

### Recovery Endpoint Inventory

| corpus | recovery_label | participants |
| --- | --- | --- |
| IISRP | persistent | 19 |
| IISRP | recovered | 68 |
| IISRP-new | persistent | 15 |
| IISRP-new | recovered | 67 |
| Purdue | persistent | 42 |
| Purdue | recovered | 42 |

### Parse Status

| corpus | parse_status | files |
| --- | --- | --- |
| Brejon | parsed | 8 |
| Examples | parsed | 1 |
| Hakim | parsed | 32 |
| IISRP | parsed | 739 |
| IISRP | too_few_target_utterances | 13 |
| IISRP-new | failed | 2 |
| IISRP-new | parsed | 87 |
| Maxfield | parsed | 17 |
| Purdue | parsed | 359 |
| Ratner | failed | 1 |
| Ratner | parsed | 59 |
| Sawyer | parsed | 51 |
| Tellis | parsed | 64 |
| Tellis | too_few_target_utterances | 31 |
| UMD-CMU | failed | 1 |
| UMD-CMU | parsed | 140 |
| UMD-CMU | too_few_target_utterances | 2 |
| Ulm | parsed | 140 |
| VanZaalen | parsed | 3 |
| VanZaalen | too_few_target_utterances | 2 |
| Voices-AWC | parsed | 7 |
| Voices-AWS | failed | 4 |
| Voices-AWS | parsed | 89 |
| Voices-AWS | too_few_target_utterances | 9 |
| Voices-CWS | failed | 2 |
| Voices-CWS | parsed | 36 |
| Voices-CWS | too_few_target_utterances | 10 |
| Wagovich | parsed | 90 |

## Earliest-Session Model

| feature_set | n | n_features | persistent_rate | auc | balanced_accuracy | macro_f1 | persistent_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| majority_baseline | 253 | 0 | 0.300 |  | 0.500 | 0.412 | 0.000 |
| demographics | 253 | 2 | 0.300 | 0.521 | 0.497 | 0.487 | 0.353 |
| first_disfluency | 253 | 12 | 0.300 | 0.629 | 0.637 | 0.623 | 0.506 |
| first_language | 253 | 15 | 0.300 | 0.717 | 0.688 | 0.660 | 0.570 |
| first_all_transcript | 253 | 62 | 0.300 | 0.666 | 0.612 | 0.600 | 0.474 |

## Early-Movement Model

Movement rows restrict to labelled participants with at least two usable sessions. `movement_only` uses first-to-second-session deltas plus within-child slopes; `first_plus_movement` adds those movement features to earliest-session state.

| feature_set | n | n_features | persistent_rate | auc | balanced_accuracy | macro_f1 | persistent_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| majority_baseline | 152 | 0 | 0.316 |  | 0.500 | 0.406 | 0.000 |
| demographics | 152 | 2 | 0.316 | 0.496 | 0.529 | 0.515 | 0.407 |
| first_disfluency | 152 | 12 | 0.316 | 0.631 | 0.606 | 0.602 | 0.471 |
| first_language | 152 | 15 | 0.316 | 0.673 | 0.641 | 0.614 | 0.533 |
| first_all_transcript | 152 | 62 | 0.316 | 0.604 | 0.562 | 0.555 | 0.426 |
| movement_only | 152 | 124 | 0.316 | 0.421 | 0.460 | 0.459 | 0.299 |
| first_plus_movement | 152 | 186 | 0.316 | 0.594 | 0.589 | 0.589 | 0.438 |

## Bootstrap Confidence Intervals

| feature_set | auc_ci_low | auc_ci_high | balanced_accuracy_ci_low | balanced_accuracy_ci_high | bootstraps |
| --- | --- | --- | --- | --- | --- |
| majority_baseline | 0.500 | 0.500 | 0.500 | 0.500 | 1000 |
| demographics | 0.401 | 0.600 | 0.449 | 0.621 | 1000 |
| first_disfluency | 0.531 | 0.728 | 0.528 | 0.689 | 1000 |
| first_language | 0.579 | 0.755 | 0.553 | 0.719 | 1000 |
| first_all_transcript | 0.510 | 0.699 | 0.482 | 0.646 | 1000 |
| movement_only | 0.324 | 0.526 | 0.380 | 0.545 | 1000 |
| first_plus_movement | 0.486 | 0.689 | 0.504 | 0.671 | 1000 |
| delta_first_plus_movement_minus_first_all | -0.118 | 0.083 | -0.067 | 0.120 | 1000 |

## Shuffled-Label Checks

| feature_set | observed_auc | perm_mean_auc | perm_p_auc_ge_observed | permutations |
| --- | --- | --- | --- | --- |
| first_all_transcript | 0.604 | 0.493 | 0.050 | 200 |
| movement_only | 0.421 | 0.501 | 0.900 | 200 |
| first_plus_movement | 0.594 | 0.495 | 0.085 | 200 |

## Leave-Corpus-Out Checks

| held_out_corpus | feature_set | n | n_features | persistent_rate | auc | balanced_accuracy | macro_f1 | persistent_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IISRP | first_all_transcript | 87 | 62 | 0.218 | 0.637 | 0.493 | 0.435 | 0.000 |
| IISRP | first_plus_movement | 87 | 186 | 0.218 | 0.336 | 0.464 | 0.458 | 0.121 |
| Purdue | first_all_transcript | 65 | 62 | 0.446 | 0.525 | 0.521 | 0.420 | 0.125 |
| Purdue | first_plus_movement | 65 | 186 | 0.446 | 0.408 | 0.465 | 0.439 | 0.267 |

## Interpretation

The best movement-subset model is `first_language` with AUC 0.673, balanced accuracy 0.641, and macro-F1 0.614.

Adding early movement to earliest transcript state changes AUC by -0.010 and balanced accuracy by +0.027 on the movement-eligible participant subset.

This is the first full-access transcript-level test of the stuttering recovery thesis. It treats IISRP/IISRP-new directory labels (`CWS-rec`, `CWS-per`) and Purdue `Rec/Per` workbook labels as recovery endpoints; other corpora contribute to the inventory but not the recovery endpoint unless they expose a comparable label.

A positive early-movement delta would support the cross-disorder state-movement hypothesis. A weak or negative delta would mean the stuttering recovery track needs richer predictors, official severity trajectories, acoustics, or treatment/context metadata before it can carry the main scientific claim.

Row-level transcript and participant features are stored in gitignored `data/parsed/fluencybank/`; aggregate outputs are in this directory.
