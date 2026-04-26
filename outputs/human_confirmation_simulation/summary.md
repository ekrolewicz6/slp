# Human Confirmation Simulation

Policy summary:

| policy | n_items | confirmations | confirmations_per_100_items | useful_confirmed_outputs | useful_outputs_per_100_items | confirmations_per_useful_output | unsafe_outputs_before_confirmation | unsafe_outputs_per_100_before | expected_residual_unsafe_per_100 | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| confirm_llm_rewrite_or_candidates_catch_0.90 | 400.000 | 112.000 | 28.000 | 12.000 | 3.000 | 9.333 | 65.000 | 16.250 | 1.625 |  |  |  |
| confirm_llm_rewrite_or_candidates_catch_0.95 | 400.000 | 112.000 | 28.000 | 12.000 | 3.000 | 9.333 | 65.000 | 16.250 | 0.813 |  |  |  |
| confirm_llm_rewrite_or_candidates_catch_0.99 | 400.000 | 112.000 | 28.000 | 12.000 | 3.000 | 9.333 | 65.000 | 16.250 | 0.163 |  |  |  |
| confirm_llm_rewrite_or_candidates_catch_1.00 | 400.000 | 112.000 | 28.000 | 12.000 | 3.000 | 9.333 | 65.000 | 16.250 | 0.000 |  |  |  |
| auto_llm_outputs_no_confirmation | 400.000 | 0.000 | 0.000 | 12.000 | 3.000 | 0.000 | 65.000 | 16.250 | 16.250 |  |  |  |
| clarification_clarification_coverage_risk_deployable_0.5 |  |  | 42.000 |  | 22.250 | 1.888 |  |  | 0.000 | 0.550 | 0.435 | 0.525 |
| clarification_clarification_coverage_risk_deployable_0.7 |  |  | 64.500 |  | 33.750 | 1.911 |  |  | 0.000 | 0.767 | 0.453 | 0.675 |
| clarification_clarification_coverage_risk_deployable_0.8 |  |  | 64.500 |  | 33.750 | 1.911 |  |  | 0.000 | 0.767 | 0.453 | 0.675 |
| clarification_clarification_coverage_risk_deployable_0.9 |  |  | 78.000 |  | 37.500 | 2.080 |  |  | 0.000 | 0.830 | 0.500 | 0.800 |
| clarification_clarification_coverage_risk_oracle_upper_0.5 |  |  | 21.250 |  | 21.000 | 1.012 |  |  | 0.000 | 0.390 | 0.000 | 0.000 |
| clarification_clarification_coverage_risk_oracle_upper_0.7 |  |  | 41.250 |  | 39.750 | 1.038 |  |  | 0.000 | 0.860 | 0.000 | 0.000 |
| clarification_clarification_coverage_risk_oracle_upper_0.8 |  |  | 41.250 |  | 39.750 | 1.038 |  |  | 0.000 | 0.860 | 0.000 | 0.000 |
| clarification_clarification_coverage_risk_oracle_upper_0.9 |  |  | 41.250 |  | 39.750 | 1.038 |  |  | 0.000 | 0.860 | 0.000 | 0.000 |
| clarification_clarification_coverage_risk_asr_confidence_pwa12_tiny_deployable_0.5 |  |  | 40.000 |  | 11.667 | 3.429 |  |  | 0.000 | 0.500 | 0.667 | 0.467 |
| clarification_clarification_coverage_risk_asr_confidence_pwa12_tiny_deployable_0.7 |  |  | 86.667 |  | 16.667 | 5.200 |  |  | 0.000 | 0.750 | 0.769 | 0.933 |
| clarification_clarification_coverage_risk_asr_confidence_pwa12_tiny_oracle_upper_0.5 |  |  | 16.667 |  | 13.333 | 1.250 |  |  | 0.000 | 0.562 | 0.000 | 0.000 |
| clarification_clarification_coverage_risk_asr_confidence_pwa12_tiny_oracle_upper_0.7 |  |  | 21.667 |  | 16.667 | 1.300 |  |  | 0.000 | 0.750 | 0.000 | 0.000 |

LLM confirmation burden by bucket:

| bucket | n_confirmations | useful_rate | unsafe_rate | mean_gain_vs_raw |
| --- | --- | --- | --- | --- |
| high_error_no_gain_control | 16 | 0.188 | 0.750 | -0.073 |
| known_target_gain_with_unknown_risk | 4 | 0.500 | 0.750 | 0.264 |
| known_target_gain_safe | 20 | 0.350 | 0.650 | 0.130 |
| low_error_content_control | 66 | 0.000 | 0.515 | 0.000 |
| unknown_intent_no_gain | 6 | 0.000 | 0.500 | 0.000 |

## Synthesis

- Perfect confirmation can make model-assisted rewriting safe, but the useful-output yield is low for the current conservative local model.
- Clarification policies are safer because they ask before rewriting, but high target recovery can require many questions, especially in ASR mode.
- The practical target is a controller that asks fewer, better questions by using uncertainty evidence rather than letting a rewriter act autonomously.