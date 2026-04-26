# Local LLM Reconstruction Pilot

- Items scored: 25
- Rewrite rate: 0.680
- Abstain rate: 0.200
- Candidates rate: 0.120
- Parse error rate: 0.000
- Mean latency seconds: 5.79

## Score Summary

| n_items | mean_concept_recovery_rate | mean_concept_overreach_count | mean_observed_concept_loss_count | mean_known_target_token_recovery_rate | unknown_intent_added_concept_rate | negation_flip_rate | r_wab_output_concept_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 25 | 0.265 | 0.560 | 1.200 | 0.212 | 0.600 | 0.480 | 0.663 |

## Action By Bucket

| bucket | n | rewrite_rate | abstain_rate | candidates_rate | parse_error_rate | mean_confidence | mean_concept_recovery | mean_overreach | mean_unknown_added | mean_negation_flip |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| high_error_no_gain_control | 5 | 0.400 | 0.400 | 0.200 | 0.000 | 0.460 | 0.000 | 0.000 | 0.000 | 0.600 |
| known_target_gain_safe | 5 | 0.800 | 0.000 | 0.200 | 0.000 | 0.800 | 0.370 | 0.600 | 0.000 | 0.600 |
| known_target_gain_with_unknown_risk | 5 | 0.800 | 0.200 | 0.000 | 0.000 | 0.700 | 0.553 | 0.800 | 2.200 | 0.600 |
| low_error_content_control | 5 | 1.000 | 0.000 | 0.000 | 0.000 | 0.890 | 0.400 | 0.800 | 0.000 | 0.400 |
| unknown_intent_no_gain | 5 | 0.400 | 0.400 | 0.200 | 0.000 | 0.460 | 0.000 | 0.600 | 0.600 | 0.200 |
