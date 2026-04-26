# Local LLM Reconstruction Pilot

- Items scored: 400
- Rewrite rate: 0.265
- Abstain rate: 0.710
- Candidates rate: 0.015
- Parse error rate: 0.010
- Mean latency seconds: 5.41

## Score Summary

| n_items | mean_concept_recovery_rate | mean_concept_overreach_count | mean_observed_concept_loss_count | mean_known_target_token_recovery_rate | unknown_intent_added_concept_rate | negation_flip_rate | r_wab_output_concept_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 400 | 0.025 | 0.085 | 0.155 | 0.347 | 0.025 | 0.120 | 0.680 |

## Action By Bucket

| bucket | n | rewrite_rate | abstain_rate | candidates_rate | parse_error_rate | mean_confidence | mean_concept_recovery | mean_overreach | mean_unknown_added | mean_negation_flip |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| high_error_no_gain_control | 80 | 0.188 | 0.800 | 0.013 | 0.000 | 0.158 | 0.000 | 0.062 | 0.000 | 0.113 |
| known_target_gain_safe | 80 | 0.212 | 0.713 | 0.037 | 0.037 | 0.188 | 0.069 | 0.100 | 0.000 | 0.087 |
| known_target_gain_with_unknown_risk | 80 | 0.037 | 0.950 | 0.013 | 0.000 | 0.037 | 0.019 | 0.050 | 0.075 | 0.025 |
| low_error_content_control | 80 | 0.825 | 0.175 | 0.000 | 0.000 | 0.729 | 0.037 | 0.188 | 0.000 | 0.350 |
| unknown_intent_no_gain | 80 | 0.062 | 0.912 | 0.013 | 0.013 | 0.056 | 0.000 | 0.025 | 0.025 | 0.025 |
