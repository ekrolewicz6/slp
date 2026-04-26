# ASR Safety Controller Pilot

- Items: 60
- Patients: 12
- Action labels: {"clarify": 18, "preserve": 24, "rewrite": 18}

## Model Summary

| model | n | macro_f1 | macro_f1_boot_mean | macro_f1_ci_low | macro_f1_ci_high | weighted_f1 | f1_clarify | support_clarify | pred_clarify | f1_preserve | support_preserve | pred_preserve | f1_rewrite | support_rewrite | pred_rewrite |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| privileged_error_oracle | 60 | 0.703 | 0.688 | 0.496 | 0.854 | 0.710 | 0.645 | 18 | 13 | 0.778 | 24 | 30 | 0.686 | 18 | 17 |
| clinical_upper | 60 | 0.448 | 0.433 | 0.291 | 0.586 | 0.466 | 0.258 | 18 | 13 | 0.630 | 24 | 30 | 0.457 | 18 | 17 |
| asr_operational_no_conf | 60 | 0.337 | 0.333 | 0.223 | 0.438 | 0.358 | 0.176 | 18 | 16 | 0.549 | 24 | 27 | 0.286 | 18 | 17 |
| asr_text_no_conf | 60 | 0.335 | 0.331 | 0.221 | 0.438 | 0.356 | 0.182 | 18 | 15 | 0.538 | 24 | 28 | 0.286 | 18 | 17 |
| asr_operational | 60 | 0.323 | 0.313 | 0.190 | 0.428 | 0.339 | 0.158 | 18 | 20 | 0.478 | 24 | 22 | 0.333 | 18 | 18 |
| asr_text | 60 | 0.315 | 0.303 | 0.180 | 0.417 | 0.333 | 0.111 | 18 | 18 | 0.500 | 24 | 24 | 0.333 | 18 | 18 |
| low_content_rule | 60 | 0.267 | 0.263 | 0.162 | 0.362 | 0.295 | 0.000 | 18 | 1 | 0.543 | 24 | 46 | 0.258 | 18 | 13 |
| majority | 60 | 0.190 | 0.189 | 0.126 | 0.246 | 0.229 | 0.000 | 18 | 0 | 0.571 | 24 | 60 | 0.000 | 18 | 0 |

## Best Deployable Model Report

| label | precision | recall | f1-score | support |
| --- | --- | --- | --- | --- |
| clarify | 0.111 | 0.111 | 0.111 | 18.000 |
| preserve | 0.500 | 0.500 | 0.500 | 24.000 |
| rewrite | 0.333 | 0.333 | 0.333 | 18.000 |
| accuracy | 0.333 | 0.333 | 0.333 | 0.333 |
| macro avg | 0.315 | 0.315 | 0.315 | 60.000 |
| weighted avg | 0.333 | 0.333 | 0.333 | 60.000 |

## Confusion Matrix, ASR Text Model

| truth | pred_clarify | pred_preserve | pred_rewrite |
| --- | --- | --- | --- |
| true_clarify | 2 | 7 | 9 |
| true_preserve | 9 | 12 | 3 |
| true_rewrite | 7 | 5 | 6 |

## Interpretation

This is the deployability test for reconstruction control. Labels use privileged CHAT error/target tags, but the ASR-only models receive only ASR text, task, and operational clip features. If ASR-only performance is weak, the system cannot safely decide rewrite/clarify/abstain from ASR alone and needs clinician confirmation, richer acoustic confidence, or personalized interaction.
