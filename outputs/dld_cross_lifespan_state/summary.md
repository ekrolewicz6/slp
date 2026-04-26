# Cross-Lifespan Language-State Summary

- Feature set: surface_core
- Features: 20
- Entities: 3154

## Population Summary

| population | n_entities | age_months_mean | age_years_mean | wab_aq_mean | mlu_mean | single_word_ratio_mean | utt_len_p90_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AB_CONTROL | 603 |  | 58.065 |  | 8.287 | 0.083 | 15.107 |
| DLD_SLI | 270 | 39.210 |  |  | 2.791 | 0.433 | 4.622 |
| DOWN_SYNDROME | 53 | 53.865 |  |  | 1.561 | 0.667 | 2.464 |
| HEARING_LOSS | 19 | 31.342 |  |  | 1.673 | 0.650 | 2.774 |
| LATE_TALKER | 91 | 35.275 |  |  | 2.886 | 0.411 | 5.297 |
| PWA_ALL | 677 |  | 61.241 | 68.727 | 5.308 | 0.157 | 9.451 |
| PWA_ANOMIC | 256 |  | 62.962 | 85.590 | 6.444 | 0.112 | 11.692 |
| PWA_BROCA | 215 |  | 57.169 | 52.303 | 3.427 | 0.268 | 5.925 |
| PWA_CONDUCTION | 157 |  | 63.061 | 69.589 | 5.929 | 0.099 | 10.472 |
| PWA_WERNICKE | 51 |  | 63.987 | 52.524 | 5.702 | 0.097 | 10.017 |
| TD_CHILDES | 276 | 34.819 |  |  | 3.044 | 0.401 | 5.486 |
| TD_CLINICAL | 486 | 44.654 |  |  | 4.195 | 0.260 | 6.868 |

## PCA Variance

| pc1_variance | pc2_variance | pc12_variance |
| --- | --- | --- |
| 0.545 | 0.140 | 0.685 |

## Focal Nearest-Neighbor Distances

Distances are in standardized feature space. Within-population rows are the internal nearest-neighbor baseline.

| from_population | to_population | n_from | n_to | median_nn_distance | mean_nn_distance |
| --- | --- | --- | --- | --- | --- |
| DLD_SLI | DLD_SLI | 270 | 270 | 1.206 | 1.532 |
| DLD_SLI | TD_CLINICAL | 270 | 486 | 1.292 | 1.637 |
| DLD_SLI | TD_CHILDES | 270 | 276 | 1.434 | 2.041 |
| DLD_SLI | PWA_BROCA | 270 | 215 | 1.731 | 2.608 |
| DLD_SLI | LATE_TALKER | 270 | 91 | 1.758 | 2.575 |
| DLD_SLI | AB_CONTROL | 270 | 603 | 4.334 | 4.669 |
| LATE_TALKER | TD_CLINICAL | 91 | 486 | 0.982 | 1.070 |
| LATE_TALKER | LATE_TALKER | 91 | 91 | 1.025 | 1.126 |
| LATE_TALKER | TD_CHILDES | 91 | 276 | 1.294 | 1.342 |
| LATE_TALKER | DLD_SLI | 91 | 270 | 1.415 | 1.678 |
| LATE_TALKER | PWA_BROCA | 91 | 215 | 1.925 | 2.342 |
| LATE_TALKER | AB_CONTROL | 91 | 603 | 4.642 | 4.754 |
| PWA_BROCA | PWA_BROCA | 215 | 215 | 1.015 | 1.055 |
| PWA_BROCA | TD_CLINICAL | 215 | 486 | 1.598 | 1.695 |
| PWA_BROCA | DLD_SLI | 215 | 270 | 1.670 | 1.831 |
| PWA_BROCA | TD_CHILDES | 215 | 276 | 1.727 | 1.878 |
| PWA_BROCA | LATE_TALKER | 215 | 91 | 2.089 | 2.404 |
| PWA_BROCA | AB_CONTROL | 215 | 603 | 3.672 | 3.702 |

## Focal Centroid Distances

| population_a | population_b | centroid_distance |
| --- | --- | --- |
| LATE_TALKER | TD_CHILDES | 1.221 |
| PWA_BROCA | TD_CHILDES | 1.502 |
| DLD_SLI | LATE_TALKER | 1.669 |
| DLD_SLI | TD_CHILDES | 1.679 |
| DLD_SLI | TD_CLINICAL | 2.148 |
| DLD_SLI | PWA_BROCA | 2.199 |
| LATE_TALKER | TD_CLINICAL | 2.213 |
| TD_CHILDES | TD_CLINICAL | 2.232 |
| LATE_TALKER | PWA_BROCA | 2.286 |
| PWA_BROCA | TD_CLINICAL | 2.498 |
| AB_CONTROL | PWA_BROCA | 5.763 |
| AB_CONTROL | TD_CLINICAL | 5.833 |
| AB_CONTROL | TD_CHILDES | 6.440 |
| AB_CONTROL | LATE_TALKER | 6.883 |
| AB_CONTROL | DLD_SLI | 6.952 |

## Focal Principal Angles

| population_a | population_b | d | mean_angle_deg | max_angle_deg | min_angle_deg |
| --- | --- | --- | --- | --- | --- |
| LATE_TALKER | TD_CHILDES | 5 | 26.523 | 70.342 | 3.728 |
| DLD_SLI | TD_CLINICAL | 5 | 29.775 | 89.035 | 2.910 |
| AB_CONTROL | PWA_BROCA | 5 | 31.444 | 83.865 | 4.965 |
| PWA_BROCA | TD_CHILDES | 5 | 32.368 | 86.099 | 3.756 |
| DLD_SLI | LATE_TALKER | 5 | 32.516 | 89.756 | 4.264 |
| LATE_TALKER | TD_CLINICAL | 5 | 33.325 | 83.052 | 2.486 |
| AB_CONTROL | TD_CHILDES | 5 | 35.428 | 88.535 | 10.350 |
| TD_CHILDES | TD_CLINICAL | 5 | 39.379 | 87.403 | 4.450 |
| DLD_SLI | TD_CHILDES | 5 | 40.744 | 87.200 | 4.334 |
| DLD_SLI | PWA_BROCA | 5 | 43.065 | 88.267 | 3.918 |
| LATE_TALKER | PWA_BROCA | 5 | 43.538 | 88.898 | 5.456 |
| AB_CONTROL | DLD_SLI | 5 | 47.113 | 88.267 | 8.829 |
| AB_CONTROL | LATE_TALKER | 5 | 49.271 | 89.763 | 14.963 |
| PWA_BROCA | TD_CLINICAL | 5 | 57.082 | 89.383 | 8.119 |
| AB_CONTROL | TD_CLINICAL | 5 | 58.210 | 88.371 | 15.299 |

## MLU-Matched Low-Output Separability

| population_a | population_b | n_entities | n_a | n_b | mlu_min | mlu_max | macro_f1 | positive_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LATE_TALKER | PWA_BROCA | 175 | 73 | 102 | 1.986 | 3.739 | 1.000 | 1.000 |
| PWA_BROCA | AB_CONTROL | 84 | 53 | 31 | 3.776 | 5.529 | 1.000 | 1.000 |
| DLD_SLI | PWA_BROCA | 316 | 160 | 156 | 1.723 | 4.923 | 0.987 | 0.987 |
| DLD_SLI | TD_CHILDES | 406 | 186 | 220 | 1.352 | 4.847 | 0.883 | 0.894 |

## Interpretation

- If DLD is merely a child version of aphasia, DLD and Broca should be close after MLU matching.
- If DLD is a developmental state and Broca is a damaged adult state, MLU-matched DLD-vs-Broca separability should remain high.
- Nearest-neighbor and centroid distances are descriptive; corpus/task artifacts remain possible.
- This script deliberately emphasizes surface-core features to reduce parser asymmetry between CHILDES and AphasiaBank.
