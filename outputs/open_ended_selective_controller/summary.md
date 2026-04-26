# Open-Ended Selective Controller

- Utterances: 66321
- Patients: 533
- Action labels: {"clarify": 1010, "preserve": 62217, "rewrite": 3094}

## Model Results

| dataset | model | n | patients | macro_f1 | macro_f1_boot_mean | macro_f1_ci_low | macro_f1_ci_high | weighted_f1 | f1_clarify | support_clarify | pred_clarify | f1_preserve | support_preserve | pred_preserve | f1_rewrite | support_rewrite | pred_rewrite |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced_challenge | privileged_error_oracle | 7198 | 517 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 0.999 | 1010 | 1008 | 1.000 | 3094 | 3094 | 1.000 | 3094 | 3096 |
| balanced_challenge | clinical_context | 7198 | 517 | 0.521 | 0.520 | 0.501 | 0.543 | 0.575 | 0.335 | 1010 | 1153 | 0.656 | 3094 | 3238 | 0.573 | 3094 | 2807 |
| balanced_challenge | context_text | 7198 | 517 | 0.478 | 0.477 | 0.463 | 0.491 | 0.553 | 0.221 | 1010 | 1011 | 0.634 | 3094 | 3262 | 0.580 | 3094 | 2925 |
| balanced_challenge | text_only | 7198 | 517 | 0.469 | 0.469 | 0.455 | 0.485 | 0.548 | 0.197 | 1010 | 922 | 0.639 | 3094 | 3353 | 0.572 | 3094 | 2923 |
| balanced_challenge | majority | 7198 | 517 | 0.200 | 0.200 | 0.189 | 0.214 | 0.258 | 0.000 | 1010 | 0 | 0.601 | 3094 | 7198 | 0.000 | 3094 | 0 |
| natural_screening | privileged_error_oracle | 16104 | 533 | 0.999 | 0.999 | 0.998 | 1.000 | 1.000 | 0.998 | 1010 | 1005 | 1.000 | 12000 | 12000 | 0.999 | 3094 | 3099 |
| natural_screening | clinical_context | 16104 | 533 | 0.511 | 0.510 | 0.491 | 0.531 | 0.726 | 0.274 | 1010 | 1659 | 0.845 | 12000 | 11982 | 0.413 | 3094 | 2463 |
| natural_screening | text_only | 16104 | 533 | 0.480 | 0.480 | 0.468 | 0.492 | 0.731 | 0.156 | 1010 | 963 | 0.857 | 12000 | 12817 | 0.428 | 3094 | 2324 |
| natural_screening | context_text | 16104 | 533 | 0.475 | 0.475 | 0.462 | 0.489 | 0.726 | 0.152 | 1010 | 964 | 0.854 | 12000 | 12736 | 0.419 | 3094 | 2404 |
| natural_screening | majority | 16104 | 533 | 0.285 | 0.285 | 0.278 | 0.291 | 0.636 | 0.000 | 1010 | 0 | 0.854 | 12000 | 16104 | 0.000 | 3094 | 0 |

## Interpretation

This is the natural-conversation version of the rewrite/clarify/preserve problem. Labels come from CHAT error/target tags. Deployable text models do not see those tags; the privileged oracle does. If text/context models fail while the oracle succeeds, the open-ended control problem is real but requires better evidence than cleaned transcript text.
