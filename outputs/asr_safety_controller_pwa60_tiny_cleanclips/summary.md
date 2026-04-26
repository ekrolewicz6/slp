# ASR Safety Controller Pilot

- Items: 228
- Patients: 51
- Action labels: {"clarify": 72, "preserve": 102, "rewrite": 54}

## Model Summary

| model | n | macro_f1 | macro_f1_boot_mean | macro_f1_ci_low | macro_f1_ci_high | weighted_f1 | f1_clarify | support_clarify | pred_clarify | f1_preserve | support_preserve | pred_preserve | f1_rewrite | support_rewrite | pred_rewrite |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| privileged_error_oracle | 228 | 0.919 | 0.918 | 0.874 | 0.955 | 0.925 | 0.910 | 72 | 62 | 0.948 | 102 | 111 | 0.899 | 54 | 55 |
| clinical_upper | 228 | 0.601 | 0.596 | 0.509 | 0.685 | 0.616 | 0.653 | 72 | 72 | 0.653 | 102 | 97 | 0.496 | 54 | 59 |
| asr_text | 228 | 0.553 | 0.549 | 0.474 | 0.621 | 0.570 | 0.536 | 72 | 66 | 0.641 | 102 | 104 | 0.482 | 54 | 58 |
| asr_operational | 228 | 0.497 | 0.493 | 0.413 | 0.572 | 0.515 | 0.496 | 72 | 65 | 0.581 | 102 | 101 | 0.414 | 54 | 62 |
| low_content_rule | 228 | 0.263 | 0.261 | 0.209 | 0.319 | 0.312 | 0.050 | 72 | 8 | 0.578 | 102 | 175 | 0.162 | 54 | 45 |
| majority | 228 | 0.206 | 0.206 | 0.170 | 0.235 | 0.277 | 0.000 | 72 | 0 | 0.618 | 102 | 228 | 0.000 | 54 | 0 |

## Best Deployable Model Report

| label | precision | recall | f1-score | support |
| --- | --- | --- | --- | --- |
| clarify | 0.561 | 0.514 | 0.536 | 72.000 |
| preserve | 0.635 | 0.647 | 0.641 | 102.000 |
| rewrite | 0.466 | 0.500 | 0.482 | 54.000 |
| accuracy | 0.570 | 0.570 | 0.570 | 0.570 |
| macro avg | 0.554 | 0.554 | 0.553 | 228.000 |
| weighted avg | 0.571 | 0.570 | 0.570 | 228.000 |

## Confusion Matrix, ASR Text Model

| truth | pred_clarify | pred_preserve | pred_rewrite |
| --- | --- | --- | --- |
| true_clarify | 37 | 22 | 13 |
| true_preserve | 18 | 66 | 18 |
| true_rewrite | 11 | 16 | 27 |

## Interpretation

This is the deployability test for reconstruction control. Labels use privileged CHAT error/target tags, but the ASR-only models receive only ASR text, task, and operational clip features. If ASR-only performance is weak, the system cannot safely decide rewrite/clarify/abstain from ASR alone and needs clinician confirmation, richer acoustic confidence, or personalized interaction.
