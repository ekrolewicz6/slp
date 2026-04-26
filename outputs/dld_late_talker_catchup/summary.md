# DLD Late-Talker Catch-Up Summary

## Age Repair Audit

| rows_before_age_repair | missing_age_before | missing_age_after | transcripts | participant_roots |
| --- | --- | --- | --- | --- |
| 486 | 217 | 0 | 230 | 74 |

## Cross-Sectional TD-Residual State

Composite z is relative to same-age Rescorla TD children. Higher is more TD-like for the oriented feature set.

| age_repaired | clinical_label | n_participants | mean_composite_z | median_composite_z | mean_utterance_length_z | mean_lexical_predicate_z | mean_grammar_argument_z | mean_fluency_repair_z | mean_mlu | mean_single_word_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 36.000 | LateTalker | 31 | -1.568 | -1.506 | -2.631 | -1.726 | -1.529 | -0.568 | 1.916 | 0.573 |
| 36.000 | TD | 21 | -0.000 | 0.004 | -0.000 | 0.000 | -0.000 | 0.000 | 3.224 | 0.296 |
| 48.000 | LateTalker | 31 | -0.652 | -0.653 | -1.032 | -0.845 | -0.276 | -0.387 | 2.866 | 0.381 |
| 48.000 | TD | 14 | 0.000 | 0.153 | 0.000 | 0.000 | 0.000 | -0.000 | 3.520 | 0.290 |
| 49.000 | LateTalker | 3 |  |  |  |  |  |  | 3.043 | 0.345 |
| 49.000 | TD | 1 |  |  |  |  |  |  | 4.232 | 0.161 |
| 60.000 | LateTalker | 26 | -0.297 | -0.305 | -0.704 | -0.239 | -0.004 | -0.224 | 3.255 | 0.309 |
| 60.000 | TD | 19 | 0.000 | 0.150 | -0.000 | -0.000 | 0.000 | -0.000 | 3.641 | 0.259 |
| 61.000 | TD | 1 |  |  |  |  |  |  | 3.010 | 0.255 |
| 108.000 | LateTalker | 30 | -0.170 | -0.194 | -0.281 | -0.144 | 0.060 | -0.280 | 7.497 | 0.032 |
| 108.000 | TD | 25 | 0.000 | 0.078 | -0.000 | 0.000 | 0.000 | 0.000 | 7.727 | 0.031 |
| 156.000 | LateTalker | 21 | -0.560 | -0.542 | -0.783 | -0.930 |  | -0.302 | 4.468 | 0.392 |
| 156.000 | TD | 7 | 0.000 | -0.292 | 0.000 | 0.000 |  | -0.000 | 4.925 | 0.376 |

## Longitudinal Trajectories

| clinical_label | n_participants | median_n_ages | mean_first_z | mean_last_z | mean_delta_z | mean_slope_z_per_month | final_td_band_rate | persistent_gap_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LateTalker | 38 | 4.000 | -1.427 | -0.384 | 1.042 | 0.016 | 0.553 | 0.211 |
| TD | 21 | 3.000 | 0.057 | 0.054 | -0.003 | -0.002 | 0.857 | 0.000 |

## Early-To-Late Prediction

| feature_set | n_late_talkers | target | mae | corr | auc_for_final_td_band |
| --- | --- | --- | --- | --- | --- |
| early_mlu_only | 38 | last_composite_z | 0.524 | -0.309 | 0.342 |
| early_composite_only | 38 | last_composite_z | 0.528 | -0.368 | 0.328 |
| early_composite_only_gbm | 38 | last_composite_z | 0.576 | 0.092 | 0.454 |
| early_state_axes | 38 | last_composite_z | 0.594 | -0.246 | 0.311 |
| early_mlu_only_gbm | 38 | last_composite_z | 0.636 | 0.075 | 0.444 |
| early_state_axes_gbm | 38 | last_composite_z | 0.673 | -0.269 | 0.350 |

## Interpretation

- This is the local-data version of the highest-value DLD question: which late talkers catch up?
- Same-age TD residualization avoids using the external TD age model beyond its 84-month ceiling.
- The key outcome is whether early state axes predict final TD-band status better than early MLU alone.
- This remains corpus-specific until replicated outside Rescorla or linked to standardized literacy/school outcomes.
