# Reconstruction Safety Benchmark

- Items: 400
- Buckets: 5
- Mean known-target errors/item: 13.27
- Mean unknown-intent errors/item: 4.10

## Bucket Counts

| bucket | n | mean_wab_aq | mean_known_target_errors | mean_unknown_intent_errors | mean_oracle_gain |
| --- | --- | --- | --- | --- | --- |
| high_error_no_gain_control | 80 | 63.739 | 5.912 | 0.000 | 0.000 |
| known_target_gain_safe | 80 | 71.187 | 9.762 | 0.000 | 1.500 |
| known_target_gain_with_unknown_risk | 80 | 62.908 | 37.800 | 12.775 | 2.188 |
| low_error_content_control | 80 | 90.370 | 0.000 | 0.000 | 0.062 |
| unknown_intent_no_gain | 80 | 59.442 | 12.863 | 7.725 | 0.000 |

## Baseline Candidate Scores

| candidate | n_items | mean_concept_recovery_rate | mean_concept_overreach_count | mean_observed_concept_loss_count | mean_known_target_token_recovery_rate | unknown_intent_added_concept_rate | negation_flip_rate | r_wab_output_concept_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| preserve_raw | 400 | 0.000 | 0.000 | 0.000 | 0.341 | 0.000 | 0.000 | 0.691 |
| oracle_target_augmented | 400 | 0.412 | 0.000 | 0.000 | 0.732 | 0.500 | 0.015 | 0.651 |

## Use

To score model outputs, create a CSV with columns `item_id,reconstruction` and run this script with `--candidate-path path/to/outputs.csv`. Primary safety metrics are concept recovery, concept overreach, unknown-intent added concepts, observed-concept loss, and negation flips.
