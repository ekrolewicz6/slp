# Late-Talker Leave-One-Out Robustness

- Late talkers with measured 36-to-48 movement: 25
- Leave-one-child-out deletions per threshold: 25

## Baseline Threshold Effects

| threshold | target | n_gain | n_no_gain | gain_target_rate | no_gain_target_rate | effect_gain_minus_no_gain | persistent_gap_reduction_if_gain | fisher_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.250 | final TD band | 20 | 5 | 0.600 | 0.200 | 0.400 |  | 0.160 |
| 0.250 | persistent gap | 20 | 5 | 0.200 | 0.400 | -0.200 | 0.200 | 0.562 |
| 0.500 | final TD band | 19 | 6 | 0.632 | 0.167 | 0.465 |  | 0.073 |
| 0.500 | persistent gap | 19 | 6 | 0.158 | 0.500 | -0.342 | 0.342 | 0.125 |
| 0.750 | final TD band | 15 | 10 | 0.733 | 0.200 | 0.533 |  | 0.015 |
| 0.750 | persistent gap | 15 | 10 | 0.067 | 0.500 | -0.433 | 0.433 | 0.023 |
| 1.000 | final TD band | 10 | 15 | 0.800 | 0.333 | 0.467 |  | 0.041 |
| 1.000 | persistent gap | 10 | 15 | 0.100 | 0.333 | -0.233 | 0.233 | 0.345 |

## Leave-One-Out Stability

| threshold | target | baseline_effect | loo_min_effect | loo_median_effect | loo_max_effect | loo_all_same_direction | baseline_fisher_p | loo_n_p_lt_0_05 | n_deletions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.250 | final TD lift | 0.400 | 0.350 | 0.379 | 0.600 | True | 0.160 | 0 | 25 |
| 0.250 | persistent-gap reduction | 0.200 | 0.050 | 0.189 | 0.300 | True | 0.562 | 0 | 25 |
| 0.500 | final TD lift | 0.465 | 0.432 | 0.444 | 0.632 | True | 0.073 | 1 | 25 |
| 0.500 | persistent-gap reduction | 0.342 | 0.242 | 0.333 | 0.442 | True | 0.125 | 0 | 25 |
| 0.750 | final TD lift | 0.533 | 0.511 | 0.514 | 0.622 | True | 0.015 | 25 | 25 |
| 0.750 | persistent-gap reduction | 0.433 | 0.378 | 0.429 | 0.500 | True | 0.023 | 11 | 25 |
| 1.000 | final TD lift | 0.467 | 0.443 | 0.444 | 0.556 | True | 0.041 | 17 | 25 |
| 1.000 | persistent-gap reduction | 0.233 | 0.186 | 0.222 | 0.333 | True | 0.345 | 0 | 25 |

## Most Influential Deletions at 0.75 z

| case | final_td_lift_after_deletion | final_td_fisher_p_after_deletion | persistent_gap_reduction_after_deletion | persistent_gap_fisher_p_after_deletion | max_abs_effect_shift |
| --- | --- | --- | --- | --- | --- |
| mcb | 0.622 | 0.009 | 0.489 | 0.015 | 0.089 |
| mel | 0.622 | 0.009 | 0.489 | 0.015 | 0.089 |
| pat | 0.586 | 0.011 | 0.500 | 0.006 | 0.067 |
| kin | 0.511 | 0.033 | 0.489 | 0.015 | 0.056 |
| spi | 0.511 | 0.033 | 0.378 | 0.047 | 0.056 |
| son | 0.511 | 0.033 | 0.378 | 0.047 | 0.056 |
| phi | 0.511 | 0.033 | 0.378 | 0.047 | 0.056 |
| peq | 0.511 | 0.033 | 0.378 | 0.047 | 0.056 |
| ban | 0.511 | 0.033 | 0.489 | 0.015 | 0.056 |
| sul | 0.511 | 0.033 | 0.489 | 0.015 | 0.056 |

## Interpretation

The early-movement clue is directionally robust but still fragile. At the 0.75 z threshold, every leave-one-child-out deletion keeps the final-TD lift positive and the persistent-gap reduction positive. Statistical significance is not deletion-proof: the final-TD comparison remains p < .05 for 25/25 deletions, and the persistent-gap comparison remains p < .05 for 11/25. This is strong enough to justify prospective measurement of early movement, but not strong enough to claim an individual prognosis rule.
