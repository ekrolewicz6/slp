# Local LLM Reconstruction Pilot

- Items scored: 25
- Rewrite rate: 0.280
- Abstain rate: 0.160
- Candidates rate: 0.280
- Parse error rate: 0.280
- Mean latency seconds: 8.69

## Score Summary

| n_items | mean_concept_recovery_rate | mean_concept_overreach_count | mean_observed_concept_loss_count | mean_known_target_token_recovery_rate | unknown_intent_added_concept_rate | negation_flip_rate | r_wab_output_concept_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 25 | 0.177 | 0.480 | 0.040 | 0.266 | 0.400 | 0.360 | 0.577 |

## Action By Bucket

| bucket | n | rewrite_rate | abstain_rate | candidates_rate | parse_error_rate | mean_confidence | mean_concept_recovery | mean_overreach | mean_unknown_added | mean_negation_flip |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| high_error_no_gain_control | 5 | 0.000 | 0.200 | 0.400 | 0.400 | 0.240 | 0.000 | 0.000 | 0.000 | 0.400 |
| known_target_gain_safe | 5 | 0.400 | 0.000 | 0.200 | 0.400 | 0.460 | 0.320 | 0.600 | 0.000 | 0.400 |
| known_target_gain_with_unknown_risk | 5 | 0.000 | 0.000 | 0.600 | 0.400 | 0.360 | 0.167 | 1.200 | 1.600 | 0.600 |
| low_error_content_control | 5 | 1.000 | 0.000 | 0.000 | 0.000 | 0.920 | 0.400 | 0.000 | 0.000 | 0.400 |
| unknown_intent_no_gain | 5 | 0.000 | 0.600 | 0.200 | 0.200 | 0.120 | 0.000 | 0.600 | 0.600 | 0.000 |
