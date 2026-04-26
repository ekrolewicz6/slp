# Local LLM Reconstruction Pilot

- Items scored: 25
- Rewrite rate: 0.240
- Abstain rate: 0.720
- Candidates rate: 0.040
- Parse error rate: 0.000
- Mean latency seconds: 5.60

## Score Summary

| n_items | mean_concept_recovery_rate | mean_concept_overreach_count | mean_observed_concept_loss_count | mean_known_target_token_recovery_rate | unknown_intent_added_concept_rate | negation_flip_rate | r_wab_output_concept_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 25 | 0.080 | 0.080 | 0.000 | 0.332 | 0.000 | 0.120 | 0.638 |

## Action By Bucket

| bucket | n | rewrite_rate | abstain_rate | candidates_rate | parse_error_rate | mean_confidence | mean_concept_recovery | mean_overreach | mean_unknown_added | mean_negation_flip |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| high_error_no_gain_control | 5 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| known_target_gain_safe | 5 | 0.400 | 0.600 | 0.000 | 0.000 | 0.340 | 0.200 | 0.200 | 0.000 | 0.200 |
| known_target_gain_with_unknown_risk | 5 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| low_error_content_control | 5 | 0.800 | 0.200 | 0.000 | 0.000 | 0.720 | 0.200 | 0.200 | 0.000 | 0.400 |
| unknown_intent_no_gain | 5 | 0.000 | 0.800 | 0.200 | 0.000 | 0.060 | 0.000 | 0.000 | 0.000 | 0.000 |
