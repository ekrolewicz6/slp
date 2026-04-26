# Stable-WAB Discourse Movers

## Overall

| n_pairs | stable_wab_pairs | stable_wab_discourse_movers | stable_wab_discourse_mover_rate | wab_changed_pairs | wab_mover_discourse_stable | delta_content_vs_delta_wab_r | abs_content_vs_abs_wab_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 405 | 370 | 66 | 0.178 | 27 | 17 | 0.178 | 0.236 |

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

## Interpretation

These are cases where standardized WAB-AQ is stable but discourse state moves beyond the empirical 95% reliable-change threshold estimated from stable-WAB pairs. They are candidates for the clinical claim that discourse monitoring can detect meaningful movement that a broad aphasia score misses. The analysis does not prove functional improvement without external outcome ratings, but it identifies patient/session pairs that should be manually reviewed or targeted in future prospective work.
