# Measurement Firewall Experiment

## Assessment Corruption If Reconstructed Text Is Scored

| item_universe | score_source | candidate_family | n | mean_wab | mean_raw_observed_concepts | mean_output_concepts | mean_measurement_delta | inflation_rate | deflation_rate | observed_loss_rate | overreach_rate | unknown_added_rate | negation_flip_rate | assessment_corruption_rate | known_target_token_recovery | firewall_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_reconstruction_safety_confidence_pwa12_tiny | asr_reconstruction_safety_confidence_pwa12_tiny | asr_par_text | 60 | 71.008 | 6.033 | 5.100 | -0.933 | 0.100 | 0.433 | 0.467 | 0.167 | 0.100 | 0.233 | 0.633 | 0.236 | do_not_score_as_patient_ability |
| asr_reconstruction_safety_confidence_pwa12_tiny | asr_reconstruction_safety_confidence_pwa12_tiny | human_oracle_targets | 60 | 71.008 | 6.033 | 6.300 | 0.267 | 0.217 | 0.000 | 0.000 | 0.000 | 0.050 | 0.000 | 0.217 | 0.532 | do_not_score_as_patient_ability |
| asr_reconstruction_safety_confidence_pwa12_tiny | asr_reconstruction_safety_confidence_pwa12_tiny | human_raw_chat | 60 | 71.008 | 6.033 | 6.033 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.247 | assessment_ok |
| asr_reconstruction_safety_pwa60_tiny_cleanclips | asr_reconstruction_safety_pwa60_tiny_cleanclips | asr_par_text | 228 | 66.122 | 4.939 | 4.250 | -0.689 | 0.075 | 0.474 | 0.544 | 0.158 | 0.057 | 0.346 | 0.711 | 0.200 | do_not_score_as_patient_ability |
| asr_reconstruction_safety_pwa60_tiny_cleanclips | asr_reconstruction_safety_pwa60_tiny_cleanclips | human_oracle_targets | 228 | 66.122 | 4.939 | 5.171 | 0.232 | 0.180 | 0.000 | 0.000 | 0.000 | 0.096 | 0.004 | 0.184 | 0.438 | do_not_score_as_patient_ability |
| asr_reconstruction_safety_pwa60_tiny_cleanclips | asr_reconstruction_safety_pwa60_tiny_cleanclips | human_raw_chat | 228 | 66.122 | 4.939 | 4.939 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.213 | assessment_ok |
| reconstruction_safety_400 | local_llm_reconstruction_compact | local_llm_reconstruction_compact | 25 | 66.617 | 5.600 | 5.520 | -0.080 | 0.320 | 0.240 | 0.440 | 0.400 | 0.240 | 0.480 | 0.760 | 0.212 | do_not_score_as_patient_ability |
| reconstruction_safety_400 | local_llm_reconstruction | local_llm_reconstruction | 25 | 66.617 | 5.600 | 6.360 | 0.760 | 0.360 | 0.000 | 0.040 | 0.280 | 0.160 | 0.360 | 0.520 | 0.266 | do_not_score_as_patient_ability |
| reconstruction_safety_400 | human_chat_benchmark | oracle_target_augmented | 400 | 69.318 | 5.835 | 6.585 | 0.750 | 0.412 | 0.000 | 0.000 | 0.000 | 0.200 | 0.015 | 0.415 | 0.732 | do_not_score_as_patient_ability |
| reconstruction_safety_400 | local_llm_reconstruction_conservative | local_llm_reconstruction_conservative | 25 | 66.617 | 5.600 | 5.760 | 0.160 | 0.120 | 0.000 | 0.000 | 0.080 | 0.000 | 0.120 | 0.200 | 0.332 | do_not_score_as_patient_ability |
| reconstruction_safety_400 | local_llm_reconstruction_full_conservative | local_llm_reconstruction_full_conservative | 400 | 69.318 | 5.835 | 5.798 | -0.038 | 0.060 | 0.075 | 0.098 | 0.072 | 0.010 | 0.120 | 0.188 | 0.347 | do_not_score_as_patient_ability |
| reconstruction_safety_400 | human_chat_benchmark | human_raw_chat | 400 | 69.318 | 5.835 | 5.835 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.341 | assessment_ok |

## Communication Gain vs Measurement Risk

| item_universe | candidate_family | n | mean_communication_gain_vs_raw | positive_communication_gain_rate | assessment_corruption_rate | unsafe_output_rate | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| reconstruction_safety_400 | oracle_target_augmented | 400 | 0.391 | 0.655 | 0.415 | 0.202 | support_maybe_measurement_no |
| asr_reconstruction_safety_confidence_pwa12_tiny | human_oracle_targets | 60 | 0.285 | 0.350 | 0.217 | 0.050 | support_maybe_measurement_no |
| asr_reconstruction_safety_pwa60_tiny_cleanclips | human_oracle_targets | 228 | 0.225 | 0.338 | 0.184 | 0.101 | support_maybe_measurement_no |
| reconstruction_safety_400 | local_llm_reconstruction_conservative | 25 | 0.040 | 0.040 | 0.200 | 0.160 | support_maybe_measurement_no |
| reconstruction_safety_400 | local_llm_reconstruction_full_conservative | 400 | 0.006 | 0.030 | 0.188 | 0.162 | support_maybe_measurement_no |
| asr_reconstruction_safety_confidence_pwa12_tiny | asr_par_text | 60 | -0.011 | 0.050 | 0.633 | 0.333 | no_support_gain_measurement_no |
| asr_reconstruction_safety_pwa60_tiny_cleanclips | asr_par_text | 228 | -0.013 | 0.053 | 0.711 | 0.430 | no_support_gain_measurement_no |
| reconstruction_safety_400 | local_llm_reconstruction | 25 | -0.026 | 0.080 | 0.520 | 0.440 | no_support_gain_measurement_no |
| reconstruction_safety_400 | local_llm_reconstruction_compact | 25 | -0.080 | 0.080 | 0.760 | 0.720 | no_support_gain_measurement_no |

## Clarification Burden

| source | table | policy_family | target_positive_item_recall | status | gate | k | offer_rate | useful_offer_precision | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | questions_per_100_items | useful_hits_per_100_items |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clarification_coverage_risk | target_recall | deployable | 0.500 | ok | content_gap_score>=5.000 | 5.000 | 0.420 | 0.530 | 0.550 | 0.435 | 0.525 | 1.888 | 5.091 | 42.000 | 22.250 |
| clarification_coverage_risk | target_recall | deployable | 0.700 | ok | content_gap_score>=3.000 | 5.000 | 0.645 | 0.523 | 0.767 | 0.453 | 0.675 | 1.911 | 5.609 | 64.500 | 33.750 |
| clarification_coverage_risk | target_recall | deployable | 0.800 | ok | content_gap_score>=3.000 | 5.000 | 0.645 | 0.523 | 0.767 | 0.453 | 0.675 | 1.911 | 5.609 | 64.500 | 33.750 |
| clarification_coverage_risk | target_recall | deployable | 0.900 | ok | content_gap_score>=2.000 | 5.000 | 0.780 | 0.481 | 0.830 | 0.500 | 0.800 | 2.080 | 6.265 | 78.000 | 37.500 |
| clarification_coverage_risk | target_recall | oracle_upper | 0.500 | ok | oracle_safe_known_gain | 5.000 | 0.212 | 0.988 | 0.390 | 0.000 | 0.000 | 1.012 | 3.632 | 21.250 | 21.000 |
| clarification_coverage_risk | target_recall | oracle_upper | 0.700 | ok | oracle_any_target_gain | 5.000 | 0.412 | 0.964 | 0.860 | 0.000 | 0.000 | 1.038 | 3.198 | 41.250 | 39.750 |
| clarification_coverage_risk | target_recall | oracle_upper | 0.800 | ok | oracle_any_target_gain | 5.000 | 0.412 | 0.964 | 0.860 | 0.000 | 0.000 | 1.038 | 3.198 | 41.250 | 39.750 |
| clarification_coverage_risk | target_recall | oracle_upper | 0.900 | ok | oracle_any_target_gain | 5.000 | 0.412 | 0.964 | 0.860 | 0.000 | 0.000 | 1.038 | 3.198 | 41.250 | 39.750 |
| clarification_coverage_risk | risk_frontier | strict |  | no_policy_met_constraint |  |  |  |  |  |  |  |  |  |  |  |
| clarification_coverage_risk | risk_frontier | moderate |  | no_policy_met_constraint |  |  |  |  |  |  |  |  |  |  |  |
| clarification_coverage_risk | risk_frontier | liberal |  | ok | content_gap_score>=11.000 | 5.000 | 0.098 | 0.462 | 0.087 | 0.436 | 0.188 | 2.167 | 7.500 | 9.750 | 4.500 |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | deployable | 0.500 | ok | content_gap_score>=6.000 | 5.000 | 0.400 | 0.292 | 0.500 | 0.667 | 0.467 | 3.429 | 15.000 | 40.000 | 11.667 |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | deployable | 0.700 | ok | missing_fraction_score>=0.250 | 5.000 | 0.867 | 0.192 | 0.750 | 0.769 | 0.933 | 5.200 | 21.667 | 86.667 | 16.667 |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | deployable | 0.800 | not_reached |  |  |  |  |  |  |  |  |  |  |  |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | deployable | 0.900 | not_reached |  |  |  |  |  |  |  |  |  |  |  |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | oracle_upper | 0.500 | ok | oracle_safe_known_gain | 5.000 | 0.167 | 0.800 | 0.562 | 0.000 | 0.000 | 1.250 | 5.556 | 16.667 | 13.333 |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | oracle_upper | 0.700 | ok | oracle_any_target_gain | 5.000 | 0.217 | 0.769 | 0.750 | 0.000 | 0.000 | 1.300 | 5.417 | 21.667 | 16.667 |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | oracle_upper | 0.800 | not_reached |  |  |  |  |  |  |  |  |  |  |  |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | oracle_upper | 0.900 | not_reached |  |  |  |  |  |  |  |  |  |  |  |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | risk_frontier | strict |  | no_policy_met_constraint |  |  |  |  |  |  |  |  |  |  |  |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | risk_frontier | moderate |  | no_policy_met_constraint |  |  |  |  |  |  |  |  |  |  |  |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | risk_frontier | liberal |  | ok | missing_fraction_score>=0.917 | 5.000 | 0.217 | 0.385 | 0.312 | 0.538 | 0.200 | 2.600 | 13.000 | 21.667 | 8.333 |

Deployable target-recall rows:

| source | table | policy_family | target_positive_item_recall | status | gate | k | offer_rate | useful_offer_precision | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | questions_per_100_items | useful_hits_per_100_items |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clarification_coverage_risk | target_recall | deployable | 0.500 | ok | content_gap_score>=5.000 | 5.000 | 0.420 | 0.530 | 0.550 | 0.435 | 0.525 | 1.888 | 5.091 | 42.000 | 22.250 |
| clarification_coverage_risk | target_recall | deployable | 0.700 | ok | content_gap_score>=3.000 | 5.000 | 0.645 | 0.523 | 0.767 | 0.453 | 0.675 | 1.911 | 5.609 | 64.500 | 33.750 |
| clarification_coverage_risk | target_recall | deployable | 0.800 | ok | content_gap_score>=3.000 | 5.000 | 0.645 | 0.523 | 0.767 | 0.453 | 0.675 | 1.911 | 5.609 | 64.500 | 33.750 |
| clarification_coverage_risk | target_recall | deployable | 0.900 | ok | content_gap_score>=2.000 | 5.000 | 0.780 | 0.481 | 0.830 | 0.500 | 0.800 | 2.080 | 6.265 | 78.000 | 37.500 |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | deployable | 0.500 | ok | content_gap_score>=6.000 | 5.000 | 0.400 | 0.292 | 0.500 | 0.667 | 0.467 | 3.429 | 15.000 | 40.000 | 11.667 |
| clarification_coverage_risk_asr_confidence_pwa12_tiny | target_recall | deployable | 0.700 | ok | missing_fraction_score>=0.250 | 5.000 | 0.867 | 0.192 | 0.750 | 0.769 | 0.933 | 5.200 | 21.667 | 86.667 | 16.667 |

## Synthesis

- Raw human CHAT text is the only safe assessment source in this comparison.
- Oracle or reconstructed support text can recover known targets, but the same operation changes the apparent content score. That is exactly why assessment and communication support must be separated.
- ASR-derived text is not a neutral replacement for raw transcripts: it can deflate observed content, lose concepts, or change safety labels.
- Clarification is not free. Current deployable policies recover meaningful targets only by asking many questions, and the ASR setting raises the burden further. Better uncertainty evidence is needed before a high-coverage clinical controller is acceptable.