# Late-Talker Bootstrap And Permutation Audit

- Bootstrap resamples per test: 10,000
- Permutations per test: 20,000
- Participants with measured 36-to-48 movement: 25

## Threshold Summary

| threshold | target | n_gain | n_no_gain | clinical_direction_effect | bootstrap_ci_lo | bootstrap_ci_hi | bootstrap_pr_effect_gt_0 | permutation_p_one_sided | permutation_p_two_sided | fisher_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.250 | final TD lift | 20 | 5 | 0.400 | -0.095 | 0.762 | 0.951 | 0.135 | 0.158 | 0.160 |
| 0.250 | persistent-gap reduction | 20 | 5 | 0.200 | -0.273 | 0.783 | 0.781 | 0.343 | 0.563 | 0.562 |
| 0.500 | final TD lift | 19 | 6 | 0.465 | 0.015 | 0.790 | 0.976 | 0.063 | 0.073 | 0.073 |
| 0.500 | persistent-gap reduction | 19 | 6 | 0.342 | -0.135 | 0.833 | 0.926 | 0.123 | 0.123 | 0.125 |
| 0.750 | final TD lift | 15 | 10 | 0.533 | 0.167 | 0.842 | 0.998 | 0.011 | 0.014 | 0.015 |
| 0.750 | persistent-gap reduction | 15 | 10 | 0.433 | 0.087 | 0.769 | 0.992 | 0.022 | 0.022 | 0.023 |
| 1.000 | final TD lift | 10 | 15 | 0.467 | 0.097 | 0.800 | 0.992 | 0.029 | 0.041 | 0.041 |
| 1.000 | persistent-gap reduction | 10 | 15 | 0.233 | -0.081 | 0.533 | 0.921 | 0.200 | 0.351 | 0.345 |

## Interpretation

The 0.75 z early-gain threshold remains the best local signal. Final TD-band lift is 0.533 with a bootstrap 95% CI [0.167, 0.842] and one-sided permutation p=0.0111. Persistent-gap reduction is 0.433 with bootstrap 95% CI [0.087, 0.769] and one-sided permutation p=0.0216. The CIs are wide because only 25 children have measured 36-to-48 movement, but both effects remain directionally positive under bootstrap resampling. This supports early movement as a prospective-study hypothesis, not an individual clinical rule.
