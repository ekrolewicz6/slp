# Patient-History Controller Add-On

Dataset sizes:

| dataset | n | patients | longitudinal_roots | has_history_rate | clarify | rewrite | preserve |
| --- | --- | --- | --- | --- | --- | --- | --- |
| natural_screening | 16104 | 533 | 447 | 0.323 | 1010 | 3094 | 12000 |
| balanced_challenge | 7198 | 517 | 432 | 0.324 | 1010 | 3094 | 3094 |
| history_only_balanced | 4362 | 156 | 156 | 1.000 | 321 | 947 | 3094 |

Model results:

| dataset | model | n | patients | macro_f1 | macro_f1_boot_mean | macro_f1_ci_low | macro_f1_ci_high | weighted_f1 | f1_clarify | support_clarify | pred_clarify | f1_preserve | support_preserve | pred_preserve | f1_rewrite | support_rewrite | pred_rewrite |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced_challenge | context_plus_history_current | 7198 | 517 | 0.534 | 0.533 | 0.512 | 0.561 | 0.587 | 0.352 | 1010 | 1212 | 0.673 | 3094 | 3177 | 0.577 | 3094 | 2809 |
| balanced_challenge | context_plus_current_clinical | 7198 | 517 | 0.520 | 0.519 | 0.502 | 0.539 | 0.576 | 0.327 | 1010 | 1076 | 0.662 | 3094 | 3275 | 0.570 | 3094 | 2847 |
| balanced_challenge | context_plus_history | 7198 | 517 | 0.512 | 0.509 | 0.480 | 0.541 | 0.576 | 0.293 | 1010 | 985 | 0.651 | 3094 | 3164 | 0.594 | 3094 | 3049 |
| balanced_challenge | context_text | 7198 | 517 | 0.475 | 0.475 | 0.460 | 0.491 | 0.553 | 0.207 | 1010 | 849 | 0.633 | 3094 | 3296 | 0.587 | 3094 | 3053 |
| balanced_challenge | history_only | 7198 | 517 | 0.467 | 0.464 | 0.437 | 0.499 | 0.525 | 0.267 | 1010 | 1152 | 0.592 | 3094 | 3166 | 0.541 | 3094 | 2880 |
| balanced_challenge | majority | 7198 | 517 | 0.200 | 0.200 | 0.189 | 0.214 | 0.258 | 0.000 | 1010 | 0 | 0.601 | 3094 | 7198 | 0.000 | 3094 | 0 |
| history_only_balanced | context_plus_history_current | 4362 | 156 | 0.574 | 0.565 | 0.505 | 0.616 | 0.730 | 0.399 | 321 | 561 | 0.840 | 3094 | 3004 | 0.484 | 947 | 797 |
| history_only_balanced | context_plus_history | 4362 | 156 | 0.534 | 0.530 | 0.490 | 0.573 | 0.722 | 0.306 | 321 | 379 | 0.849 | 3094 | 3208 | 0.448 | 947 | 775 |
| history_only_balanced | history_only | 4362 | 156 | 0.495 | 0.493 | 0.463 | 0.528 | 0.706 | 0.208 | 321 | 399 | 0.840 | 3094 | 3171 | 0.437 | 947 | 792 |
| history_only_balanced | context_plus_current_clinical | 4362 | 156 | 0.477 | 0.474 | 0.445 | 0.504 | 0.683 | 0.224 | 321 | 321 | 0.823 | 3094 | 3259 | 0.383 | 947 | 782 |
| history_only_balanced | context_text | 4362 | 156 | 0.431 | 0.429 | 0.406 | 0.452 | 0.667 | 0.108 | 321 | 269 | 0.817 | 3094 | 3411 | 0.366 | 947 | 682 |
| history_only_balanced | majority | 4362 | 156 | 0.277 | 0.276 | 0.261 | 0.291 | 0.589 | 0.000 | 321 | 0 | 0.830 | 3094 | 4362 | 0.000 | 947 | 0 |
| natural_screening | context_plus_history_current | 16104 | 533 | 0.524 | 0.522 | 0.500 | 0.549 | 0.735 | 0.292 | 1010 | 1515 | 0.850 | 12000 | 12010 | 0.429 | 3094 | 2579 |
| natural_screening | context_plus_current_clinical | 16104 | 533 | 0.502 | 0.502 | 0.485 | 0.518 | 0.727 | 0.238 | 1010 | 1320 | 0.847 | 12000 | 12182 | 0.422 | 3094 | 2602 |
| natural_screening | context_plus_history | 16104 | 533 | 0.497 | 0.495 | 0.474 | 0.516 | 0.733 | 0.198 | 1010 | 942 | 0.854 | 12000 | 12605 | 0.438 | 3094 | 2557 |
| natural_screening | context_text | 16104 | 533 | 0.475 | 0.475 | 0.460 | 0.488 | 0.724 | 0.151 | 1010 | 1110 | 0.849 | 12000 | 12544 | 0.426 | 3094 | 2450 |
| natural_screening | history_only | 16104 | 533 | 0.441 | 0.439 | 0.421 | 0.457 | 0.697 | 0.130 | 1010 | 1151 | 0.832 | 12000 | 12805 | 0.361 | 3094 | 2148 |
| natural_screening | majority | 16104 | 533 | 0.285 | 0.285 | 0.278 | 0.291 | 0.636 | 0.000 | 1010 | 0 | 0.854 | 12000 | 16104 | 0.000 | 3094 | 0 |

## Synthesis

- Prior-session history is a plausible safety signal only if it improves clarify/rewrite decisions under root-held-out evaluation.
- If history helps mostly on rows with previous sessions, it supports patient-specific controller calibration; if not, the bottleneck remains utterance-level intent evidence.