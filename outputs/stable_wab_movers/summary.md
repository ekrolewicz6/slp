# Stable-WAB Discourse Movers

## Overall

| n_pairs | stable_wab_pairs | stable_wab_discourse_movers | stable_wab_discourse_mover_rate | wab_changed_pairs | wab_mover_discourse_stable | delta_content_vs_delta_wab_r | abs_content_vs_abs_wab_r | pairs_with_acoustics | stable_wab_pairs_with_acoustics | stable_wab_acoustic_movers | stable_wab_acoustic_mover_rate | stable_wab_acoustic_only_movers | stable_wab_discourse_and_acoustic_movers | abs_acoustic_no_token_vs_abs_wab_r | abs_acoustic_no_token_vs_abs_content_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 405 | 370 | 66 | 0.178 | 27 | 17 | 0.178 | 0.236 | 112 | 110 | 17 | 0.155 | 11 | 6 | -0.056 | -0.097 |

## Mover Types

| mover_type | n | roots | mean_abs_delta_wab | mean_delta_wab | mean_abs_delta_content | mean_delta_content | mean_abs_delta_coverage | pct_broca | pct_anomic | pct_conduction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stable_or_small_change | 312 | 157 | 0.157 | 0.062 | 0.405 | 0.064 | 0.053 | 0.343 | 0.308 | 0.144 |
| stable_wab_other_discourse_mover | 47 | 35 | 0.102 | 0.102 | 0.401 | 0.055 | 0.054 | 0.298 | 0.213 | 0.234 |
| wab_mover_discourse_stable | 17 | 13 | 8.765 | 0.000 | 0.401 | 0.167 | 0.055 | 0.471 | 0.235 | 0.294 |
| stable_wab_content_improved | 10 | 10 | 0.280 | -0.280 | 1.392 | 1.392 | 0.184 | 0.400 | 0.500 | 0.000 |
| wab_and_discourse_mover | 10 | 10 | 17.170 | 3.710 | 1.418 | 0.293 | 0.200 | 0.500 | 0.100 | 0.100 |
| stable_wab_content_declined | 9 | 9 | 0.000 | 0.000 | 1.738 | -1.738 | 0.235 | 0.444 | 0.333 | 0.222 |

## By Subtype

| from_meta_subtype | n_pairs | stable_wab_pairs | stable_wab_discourse_movers | reliable_content_rate | mean_abs_delta_wab | mean_abs_delta_content | stable_wab_mover_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | 8 | 8 | 2 | 0.000 | 0.000 | 0.172 | 0.250 |
| Conduction | 64 | 56 | 13 | 0.047 | 0.998 | 0.512 | 0.232 |
| TransMotor | 9 | 9 | 2 | 0.000 | 0.056 | 0.416 | 0.222 |
| NotAphasic | 35 | 33 | 6 | 0.029 | 0.240 | 0.426 | 0.182 |
| Broca | 142 | 128 | 22 | 0.085 | 1.122 | 0.481 | 0.172 |
| Anomic | 119 | 111 | 18 | 0.076 | 0.581 | 0.527 | 0.162 |
| Wernicke | 26 | 24 | 3 | 0.077 | 1.500 | 0.415 | 0.125 |
| TransSensory | 1 | 0 | 0 | 0.000 | 37.000 | 1.069 | 0.000 |

## Top Stable-WAB Mover Examples

| longitudinal_root | from_participant_id | to_participant_id | from_meta_corpus | from_meta_subtype | from_wab_aq | to_wab_aq | delta_wab_aq | delta_core_content_mean_z | delta_coverage_mean | mover_type | from_axis_assistive_priority | to_axis_assistive_priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1030 | 1030-6 | 1030-1 | Fridriksson-2 | Broca | 73.900 | 73.900 | 0.000 | -2.461 | -0.344 | stable_wab_content_declined | clarification/repair support | high-support intent clarification |
| 1033 | 1033-5 | 1033-6 | Fridriksson-2 | Anomic | 80.300 | 80.300 | 0.000 | -2.347 | -0.317 | stable_wab_content_declined | clarification/repair support | high-support intent clarification |
| 1072 | 1072-4 | 1072-1 | Fridriksson-2 | Broca | 67.000 | 67.000 | 0.000 | -2.020 | -0.278 | stable_wab_content_declined | maintenance/generalization | known-target repair plus content expansion |
| 1080 | 1080-6 | 1080-1 | Fridriksson-2 | Broca | 71.400 | 71.400 | 0.000 | -1.853 | -0.261 | stable_wab_content_declined | clarification/repair support | event-concept expansion |
| 1030 | 1030-1 | 1030-2 | Fridriksson-2 | Broca | 73.900 | 73.900 | 0.000 | 1.719 | 0.233 | stable_wab_content_improved | high-support intent clarification | high-support intent clarification |
| 1114 | 1114-3 | 1114-4 | Fridriksson-2 | Conduction | 51.900 | 51.900 | 0.000 | -1.680 | -0.222 | stable_wab_content_declined | high-support intent clarification | high-support intent clarification |
| Kurland25 | Kurland25b | Kurland25c | Kurland | Anomic | 81.400 | 81.400 | 0.000 | -1.605 | -0.207 | stable_wab_content_declined | clarification/repair support | high-support intent clarification |
| MSU07 | MSU07a | MSU07b | MSU | Broca | 61.400 | 61.400 | 0.000 | 1.551 | 0.190 | stable_wab_content_improved | event-concept expansion | known-target repair plus content expansion |
| 1059 | 1059-1 | 1059-2 | Fridriksson-2 | Anomic | 91.300 | 91.300 | 0.000 | 1.548 | 0.211 | stable_wab_content_improved | event-concept expansion | maintenance/generalization |
| 99 | 99-1 | 99-2 | NEURAL-2 | NotAphasic | 96.200 | 96.200 | 0.000 | 1.535 | 0.197 | stable_wab_content_improved | maintenance/generalization | maintenance/generalization |
| 1033 | 1033-3 | 1033-4 | Fridriksson-2 | Anomic | 80.300 | 80.300 | 0.000 | 1.436 | 0.200 | stable_wab_content_improved | high-support intent clarification | clarification/repair support |
| 1080 | 1080-3 | 1080-4 | Fridriksson-2 | Broca | 71.400 | 71.400 | 0.000 | 1.342 | 0.183 | stable_wab_content_improved | high-support intent clarification | high-support intent clarification |
| 1026 | 1026-3 | 1026-4 | Fridriksson-2 | Anomic | 88.800 | 88.800 | 0.000 | -1.296 | -0.178 | stable_wab_content_declined | maintenance/generalization | maintenance/generalization |
| Kurland21 | Kurland21b | Kurland21c | Kurland | Anomic | 81.800 | 81.800 | 0.000 | 1.225 | 0.153 | stable_wab_content_improved | event-concept expansion | clarification/repair support |
| 1040 | 1040-4 | 1040-5 | Fridriksson-2 | Broca | 65.500 | 65.500 | 0.000 | 1.202 | 0.161 | stable_wab_content_improved | maintenance/generalization | maintenance/generalization |
| 1016 | 1016-4 | 1016-5 | Fridriksson-2 | Broca | 36.300 | 36.300 | 0.000 | -1.191 | -0.161 | stable_wab_content_declined | high-support intent clarification | high-support intent clarification |
| MSU03 | MSU03a | MSU03b | MSU | Conduction | 72.400 | 72.400 | 0.000 | -1.188 | -0.150 | stable_wab_content_declined | clarification/repair support | known-target repair plus content expansion |
| SCALE06 | SCALE06c | SCALE06d | SCALE | Anomic | 86.100 | 83.300 | -2.800 | 1.188 | 0.157 | stable_wab_content_improved | known-target repair plus content expansion | maintenance/generalization |
| 101 | 101-1 | 101-2 | NEURAL-2 | Anomic | 91.500 | 91.500 | 0.000 | 1.176 | 0.157 | stable_wab_content_improved | maintenance/generalization | maintenance/generalization |
| 1117 | 1117-4 | 1117-5 | Fridriksson-2 | Conduction | 72.900 | 72.900 | 0.000 | 1.156 | 0.156 | stable_wab_other_discourse_mover | high-support intent clarification | clarification/repair support |
| 65 | 65-1 | 65-2 | NEURAL-2 | NotAphasic | 99.400 | 99.400 | 0.000 | -1.150 | -0.150 | stable_wab_other_discourse_mover | maintenance/generalization | maintenance/generalization |
| 1072 | 1072-1 | 1072-3 | Fridriksson-2 | Broca | 67.000 | 67.000 | 0.000 | 1.146 | 0.156 | stable_wab_other_discourse_mover | known-target repair plus content expansion | known-target repair plus content expansion |
| 1104 | 1104-1 | 1104-2 | Fridriksson-2 | Anomic | 82.200 | 82.200 | 0.000 | 0.919 | 0.128 | stable_wab_other_discourse_mover | maintenance/generalization | maintenance/generalization |
| SCALE14 | SCALE14a | SCALE14c | SCALE | Anomic | 67.600 | 70.000 | 2.400 | 0.905 | 0.077 | stable_wab_other_discourse_mover | high-support intent clarification | high-support intent clarification |
| 1010 | 1010-3 | 1010-4 | Fridriksson-2 | Broca | 28.600 | 28.600 | 0.000 | 0.855 | 0.111 | stable_wab_other_discourse_mover | high-support intent clarification | high-support intent clarification |
| 1015 | 1015-6 | 1015-1 | Fridriksson-2 | Broca | 52.900 | 52.900 | 0.000 | -0.789 | -0.106 | stable_wab_other_discourse_mover | clarification/repair support | high-support intent clarification |
| 1087 | 1087-5 | 1087-6 | Fridriksson-2 | TransMotor | 78.200 | 78.200 | 0.000 | -0.752 | -0.111 | stable_wab_other_discourse_mover | maintenance/generalization | event-concept expansion |
| 1089 | 1089-2 | 1089-3 | Fridriksson-2 | Wernicke | 69.200 | 69.200 | 0.000 | 0.734 | 0.100 | stable_wab_other_discourse_mover | clarification/repair support | clarification/repair support |
| 1046 | 1046-5 | 1046-1 | Fridriksson-2 | Anomic | 82.300 | 82.300 | 0.000 | -0.676 | -0.106 | stable_wab_other_discourse_mover | maintenance/generalization | event-concept expansion |
| 1114 | 1114-5 | 1114-6 | Fridriksson-2 | Conduction | 51.900 | 51.900 | 0.000 | 0.659 | 0.083 | stable_wab_other_discourse_mover | high-support intent clarification | high-support intent clarification |

## Acoustic Reliable-Change Thresholds

| family | n_features | stable_wab_pairs_with_acoustics | stable_wab_q95_distance | all_pair_mean_distance |
| --- | --- | --- | --- | --- |
| custom_no_token_count_acoustic | 28 | 110 | 1.547 | 0.702 |
| voice_pitch_intensity | 26 | 110 | 1.596 | 0.716 |
| duration_intensity | 6 | 110 | 1.678 | 0.418 |
| token_rate_count | 6 | 110 | 0.992 | 0.437 |

## Top Stable-WAB Acoustic-Only Examples

| longitudinal_root | from_participant_id | to_participant_id | from_meta_corpus | from_meta_subtype | from_wab_aq | to_wab_aq | delta_wab_aq | delta_custom_no_token_count_acoustic_distance | reliable_custom_no_token_count_acoustic_change | delta_voice_pitch_intensity_distance | reliable_voice_pitch_intensity_change | delta_duration_intensity_distance | reliable_duration_intensity_change | delta_token_rate_count_distance | reliable_token_rate_count_change | delta_core_content_mean_z | mover_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1012 | 1012-4 | 1012-5 | Fridriksson-2 | Broca | 40.600 | 40.600 | 0.000 | 2.602 | True | 2.700 | True | 1.130 | False | 0.294 | False | 0.734 | stable_or_small_change |
| 1014 | 1014-2 | 1014-3 | Fridriksson-2 | Anomic | 85.800 | 85.800 | 0.000 | 2.469 | True | 2.562 | True | 0.282 | False | 0.377 | False | 0.150 | stable_or_small_change |
| 1012 | 1012-2 | 1012-3 | Fridriksson-2 | Broca | 40.600 | 40.600 | 0.000 | 2.178 | True | 2.260 | True | 1.363 | False | 0.789 | False | -0.095 | stable_or_small_change |
| 1046 | 1046-2 | 1046-3 | Fridriksson-2 | Anomic | 82.300 | 82.300 | 0.000 | 1.548 | True | 1.560 | False | 0.875 | False | 0.646 | False | -0.462 | stable_or_small_change |
| 1012 | 1012-5 | 1012-6 | Fridriksson-2 | Broca | 40.600 | 40.600 | 0.000 | 1.545 | False | 1.603 | True | 1.575 | False | 0.308 | False | -0.517 | stable_or_small_change |
| 1060 | 1060-2 | 1060-3 | Fridriksson-2 | Conduction | 63.100 | 63.100 | 0.000 | 1.529 | False | 1.587 | False | 2.032 | True | 0.759 | False | 0.338 | stable_or_small_change |
| 1108 | 1108-1 | 1108-2 | Fridriksson-2 | Broca | 54.900 | 54.900 | 0.000 | 1.463 | False | 1.517 | False | 2.949 | True | 0.250 | False | 0.723 | stable_or_small_change |
| 1060 | 1060-1 | 1060-2 | Fridriksson-2 | Conduction | 63.100 | 63.100 | 0.000 | 1.131 | False | 1.172 | False | 2.123 | True | 0.423 | False | -0.167 | stable_or_small_change |
| 1117 | 1117-5 | 1117-6 | Fridriksson-2 | Conduction | 72.900 | 72.900 | 0.000 | 0.902 | False | 0.933 | False | 1.734 | True | 0.241 | False | -0.583 | stable_or_small_change |
| 1033 | 1033-4 | 1033-5 | Fridriksson-2 | Anomic | 80.300 | 80.300 | 0.000 | 0.510 | False | 0.517 | False | 0.289 | False | 1.337 | True | 0.177 | stable_or_small_change |
| Kurland21 | Kurland21a | Kurland21b | Kurland | Anomic | 81.800 | 81.800 | 0.000 | 0.454 | False | 0.452 | False | 0.283 | False | 1.039 | True | -0.328 | stable_or_small_change |

## Interpretation

These are cases where standardized WAB-AQ is stable but discourse state moves beyond the empirical 95% reliable-change threshold estimated from stable-WAB pairs. They are candidates for the clinical claim that discourse monitoring can detect meaningful movement that a broad aphasia score misses. The analysis does not prove functional improvement without external outcome ratings, but it identifies patient/session pairs that should be manually reviewed or targeted in future prospective work. Acoustic-only movers are especially useful falsification cases: if manual review finds no clinically visible speech-state change, the acoustic state should be downgraded; if it does, the broad WAB score is missing a measurable dimension of change.
