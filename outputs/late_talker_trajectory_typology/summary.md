# Late-Talker Trajectory Typology

- Late talkers typed: 38
- Strong early-gain threshold: >= 0.75 z from 36 to 48 months
- Participants with measured 36-to-48 movement: 25

## Trajectory Classes

| trajectory_class | n | final_td_rate | persistent_gap_rate | mean_first_composite_z | mean_delta_36_48_z | mean_last_composite_z | mean_age_last |
| --- | --- | --- | --- | --- | --- | --- | --- |
| missing_36_48_movement | 13 | 0.615 | 0.154 | -1.306 |  | -0.375 | 144.923 |
| early_gain_recovered | 11 | 1.000 | 0.000 | -1.756 | 1.508 | 0.141 | 115.636 |
| low_early_gain_persistent_gap | 5 | 0.000 | 1.000 | -1.045 | 0.262 | -1.370 | 134.400 |
| early_gain_partial_recovery | 3 | 0.000 | 0.000 | -2.095 | 0.999 | -0.643 | 140.000 |
| low_early_gain_partial_or_unresolved | 3 | 0.000 | 0.000 | -1.271 | 0.329 | -0.590 | 104.000 |
| late_or_low_early_gain_recovered | 2 | 1.000 | 0.000 | -0.385 | 0.106 | 0.190 | 84.000 |
| early_gain_but_persistent_gap | 1 | 0.000 | 1.000 | -1.830 | 1.084 | -1.121 | 60.000 |

## Long-Horizon Subset (final age >= 108 months)

| trajectory_class | n | final_td_rate | persistent_gap_rate | mean_last_composite_z |
| --- | --- | --- | --- | --- |
| missing_36_48_movement | 13 | 0.615 | 0.154 | -0.375 |
| early_gain_recovered | 9 | 1.000 | 0.000 | 0.054 |
| low_early_gain_persistent_gap | 4 | 0.000 | 1.000 | -1.420 |
| early_gain_partial_recovery | 3 | 0.000 | 0.000 | -0.643 |
| low_early_gain_partial_or_unresolved | 2 | 0.000 | 0.000 | -0.611 |
| late_or_low_early_gain_recovered | 1 | 1.000 | 0.000 | 0.401 |

## Early-Gain Bins

| early_gain_bin | n | final_td_rate | persistent_gap_rate | mean_last_composite_z |
| --- | --- | --- | --- | --- |
| 0-0.25z | 2 | 0.000 | 0.000 | -0.577 |
| 0.25-0.50z | 1 | 0.000 | 1.000 | -1.171 |
| 0.50-0.75z | 4 | 0.250 | 0.500 | -0.666 |
| 0.75-1.00z | 5 | 0.600 | 0.000 | -0.302 |
| >=1.00z | 10 | 0.800 | 0.100 | 0.001 |
| decline | 3 | 0.333 | 0.667 | -1.085 |
| missing | 13 | 0.615 | 0.154 | -0.375 |

## Threshold Sensitivity

| threshold | target | early_gain | n | target_rate | odds_ratio_gain_vs_no_gain | fisher_p |
| --- | --- | --- | --- | --- | --- | --- |
| 0.250 | final_in_td_band | False | 5 | 0.200 | 6.000 | 0.160 |
| 0.250 | final_in_td_band | True | 20 | 0.600 | 6.000 | 0.160 |
| 0.250 | persistent_gap | False | 5 | 0.400 | 0.375 | 0.562 |
| 0.250 | persistent_gap | True | 20 | 0.200 | 0.375 | 0.562 |
| 0.500 | final_in_td_band | False | 6 | 0.167 | 8.571 | 0.073 |
| 0.500 | final_in_td_band | True | 19 | 0.632 | 8.571 | 0.073 |
| 0.500 | persistent_gap | False | 6 | 0.500 | 0.188 | 0.125 |
| 0.500 | persistent_gap | True | 19 | 0.158 | 0.188 | 0.125 |
| 0.750 | final_in_td_band | False | 10 | 0.200 | 11.000 | 0.015 |
| 0.750 | final_in_td_band | True | 15 | 0.733 | 11.000 | 0.015 |
| 0.750 | persistent_gap | False | 10 | 0.500 | 0.071 | 0.023 |
| 0.750 | persistent_gap | True | 15 | 0.067 | 0.071 | 0.023 |
| 1.000 | final_in_td_band | False | 15 | 0.333 | 8.000 | 0.041 |
| 1.000 | final_in_td_band | True | 10 | 0.800 | 8.000 | 0.041 |
| 1.000 | persistent_gap | False | 15 | 0.333 | 0.222 | 0.345 |
| 1.000 | persistent_gap | True | 10 | 0.100 | 0.222 | 0.345 |

## Interpretation

The useful construct is not earliest late-talker severity. It is early movement. A strong 36-to-48 month gain is associated with higher final TD-band rates and lower persistent-gap rates, especially at stricter thresholds. The sample is small and not treatment-linked, so this should be framed as a trajectory-phenotyping result and a prospective-study design clue, not as a clinical prognosis model.
