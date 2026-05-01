# Late-Talker Persistence Sensitivity

- Late talkers with longitudinal trajectories: 38
- Late talkers with final age >= 108 months: 32
- Final TD-band rate: 0.553
- Persistent-gap rate: 0.211

## Prediction Metrics

| cohort | target | feature_set | n | positive_rate | balanced_accuracy | macro_f1 | positive_f1 | auc | mae | corr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_longitudinal | final_in_td_band | first_mlu_only | 38 | 0.553 | 0.534 | 0.526 | 0.638 | 0.471 |  |  |
| all_longitudinal | final_in_td_band | first_composite_only | 38 | 0.553 | 0.427 | 0.415 | 0.553 | 0.398 |  |  |
| all_longitudinal | final_in_td_band | first_axes | 38 | 0.553 | 0.356 | 0.352 | 0.455 | 0.294 |  |  |
| all_longitudinal | final_in_td_band | first_plus_36_48_change | 38 | 0.553 | 0.710 | 0.709 | 0.732 | 0.742 |  |  |
| all_longitudinal | persistent_gap | first_mlu_only | 38 | 0.211 | 0.608 | 0.504 | 0.400 | 0.492 |  |  |
| all_longitudinal | persistent_gap | first_composite_only | 38 | 0.211 | 0.217 | 0.255 | 0.000 | 0.262 |  |  |
| all_longitudinal | persistent_gap | first_axes | 38 | 0.211 | 0.346 | 0.360 | 0.091 | 0.425 |  |  |
| all_longitudinal | persistent_gap | first_plus_36_48_change | 38 | 0.211 | 0.708 | 0.635 | 0.500 | 0.708 |  |  |
| all_longitudinal | last_composite_z | first_mlu_only | 38 |  |  |  |  |  | 0.538 | -0.284 |
| all_longitudinal | last_composite_z | first_composite_only | 38 |  |  |  |  |  | 0.541 | -0.388 |
| all_longitudinal | last_composite_z | first_axes | 38 |  |  |  |  |  | 0.658 | -0.245 |
| all_longitudinal | last_composite_z | first_plus_36_48_change | 38 |  |  |  |  |  | 0.537 | 0.291 |
| final_age_ge_108 | final_in_td_band | first_mlu_only | 32 | 0.562 | 0.401 | 0.401 | 0.457 | 0.480 |  |  |
| final_age_ge_108 | final_in_td_band | first_composite_only | 32 | 0.562 | 0.437 | 0.435 | 0.471 | 0.425 |  |  |
| final_age_ge_108 | final_in_td_band | first_axes | 32 | 0.562 | 0.393 | 0.391 | 0.486 | 0.456 |  |  |
| final_age_ge_108 | final_in_td_band | first_plus_36_48_change | 32 | 0.562 | 0.710 | 0.712 | 0.757 | 0.750 |  |  |
| final_age_ge_108 | persistent_gap | first_mlu_only | 32 | 0.188 | 0.442 | 0.376 | 0.240 | 0.429 |  |  |
| final_age_ge_108 | persistent_gap | first_composite_only | 32 | 0.188 | 0.353 | 0.364 | 0.105 | 0.442 |  |  |
| final_age_ge_108 | persistent_gap | first_axes | 32 | 0.188 | 0.532 | 0.521 | 0.267 | 0.526 |  |  |
| final_age_ge_108 | persistent_gap | first_plus_36_48_change | 32 | 0.188 | 0.756 | 0.726 | 0.571 | 0.782 |  |  |
| final_age_ge_108 | last_composite_z | first_mlu_only | 32 |  |  |  |  |  | 0.517 | -0.479 |
| final_age_ge_108 | last_composite_z | first_composite_only | 32 |  |  |  |  |  | 0.519 | -0.426 |
| final_age_ge_108 | last_composite_z | first_axes | 32 |  |  |  |  |  | 0.534 | -0.083 |
| final_age_ge_108 | last_composite_z | first_plus_36_48_change | 32 |  |  |  |  |  | 0.423 | 0.495 |

## Early State Bins

| first_state_bin | n | mean_first_z | mean_last_z | final_td_band_rate | persistent_gap_rate | mean_delta_36_48_z |
| --- | --- | --- | --- | --- | --- | --- |
| very_low | 12 | -2.473 | -0.322 | 0.583 | 0.167 | 1.642 |
| low | 14 | -1.406 | -0.409 | 0.571 | 0.286 | 0.847 |
| near_td | 5 | -0.734 | -0.698 | 0.400 | 0.200 | 0.537 |
| td_like | 7 | -0.170 | -0.219 | 0.571 | 0.143 | 0.067 |

## Interpretation

In the local Rescorla data, earliest transcript state alone is useful descriptively but weak as an individual-level predictor of final catch-up. The more interesting signal is early change: adding 36-to-48-month movement improves prediction even when final observations are restricted to 108+ months. This still falls short of treatment-response science, because it lacks treatment exposure, standardized outcome anchors, and external replication.
