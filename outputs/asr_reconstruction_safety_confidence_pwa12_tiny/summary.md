# ASR Reconstruction Safety

- Items/task rows: 60
- Patients: 12
- Mean ASR F1 vs human concepts: 0.749
- Mean ASR recall vs human concepts: 0.721
- Mean ASR precision vs human concepts: 0.823

## Headline Safety Readout

- ASR observed-concept loss/item: 1.150 (human raw: 0.000)
- ASR concept overreach/item: 0.183 (human raw: 0.000)
- ASR unknown-intent added concepts/item: 0.133 (human raw: 0.000)
- ASR negation flip rate: 0.233 (human raw: 0.000)
- Mean ASR minus raw observed-loss delta: 1.150
- Mean ASR minus raw overreach delta: 0.183

## Overall Candidate Comparison

| candidate_family | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human | r_output_concepts_wab | r_overreach_wab | r_observed_loss_wab |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | 60 | 12 | 71.008 | 5.100 | 0.033 | 0.183 | 1.150 | 0.236 | 0.133 | 0.233 | 0.749 | 0.721 | 0.823 | 0.719 | -0.039 | -0.038 |
| human_oracle_targets | 60 | 12 | 71.008 | 6.300 | 0.217 | 0.000 | 0.000 | 0.532 | 0.083 | 0.000 | 0.749 | 0.721 | 0.823 | 0.778 |  |  |
| human_raw_chat | 60 | 12 | 71.008 | 6.033 | 0.000 | 0.000 | 0.000 | 0.247 | 0.000 | 0.000 | 0.749 | 0.721 | 0.823 | 0.784 |  |  |

## By Safety Bucket

| candidate_family | bucket | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | known_plus_unknown_risk | 14 | 6 | 65.607 | 5.286 | 0.071 | 0.429 | 0.571 | 0.392 | 0.500 | 0.286 | 0.804 | 0.800 | 0.847 |
| asr_par_text | known_target_safe_zone | 18 | 10 | 70.983 | 5.333 | 0.000 | 0.167 | 1.222 | 0.481 | 0.000 | 0.278 | 0.713 | 0.673 | 0.772 |
| asr_par_text | low_error_content | 22 | 9 | 80.014 | 5.591 | 0.045 | 0.045 | 1.273 | 0.000 | 0.000 | 0.227 | 0.806 | 0.777 | 0.892 |
| asr_par_text | other_error | 2 | 1 | 68.800 | 0.500 | 0.000 | 0.000 | 4.000 | 0.000 | 0.000 | 0.000 | 0.167 | 0.100 | 0.500 |
| asr_par_text | unknown_intent | 4 | 3 | 41.600 | 3.000 | 0.000 | 0.250 | 0.750 | 0.000 | 0.250 | 0.000 | 0.705 | 0.667 | 0.750 |
| human_oracle_targets | known_plus_unknown_risk | 14 | 6 | 65.607 | 5.714 | 0.214 | 0.000 | 0.000 | 0.929 | 0.357 | 0.000 | 0.804 | 0.800 | 0.847 |
| human_oracle_targets | known_target_safe_zone | 18 | 10 | 70.983 | 6.833 | 0.389 | 0.000 | 0.000 | 0.942 | 0.000 | 0.000 | 0.713 | 0.673 | 0.772 |
| human_oracle_targets | low_error_content | 22 | 9 | 80.014 | 6.864 | 0.091 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.806 | 0.777 | 0.892 |
| human_oracle_targets | other_error | 2 | 1 | 68.800 | 5.000 | 0.500 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.167 | 0.100 | 0.500 |
| human_oracle_targets | unknown_intent | 4 | 3 | 41.600 | 3.500 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.705 | 0.667 | 0.750 |
| human_raw_chat | known_plus_unknown_risk | 14 | 6 | 65.607 | 5.357 | 0.000 | 0.000 | 0.000 | 0.388 | 0.000 | 0.000 | 0.804 | 0.800 | 0.847 |
| human_raw_chat | known_target_safe_zone | 18 | 10 | 70.983 | 6.389 | 0.000 | 0.000 | 0.000 | 0.467 | 0.000 | 0.000 | 0.713 | 0.673 | 0.772 |
| human_raw_chat | low_error_content | 22 | 9 | 80.014 | 6.773 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.806 | 0.777 | 0.892 |
| human_raw_chat | other_error | 2 | 1 | 68.800 | 4.500 | 0.000 | 0.000 | 0.000 | 0.500 | 0.000 | 0.000 | 0.167 | 0.100 | 0.500 |
| human_raw_chat | unknown_intent | 4 | 3 | 41.600 | 3.500 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.705 | 0.667 | 0.750 |

## ASR Candidate By Subtype

| candidate_family | subtype | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | Anomic | 15 | 3 | 85.367 | 6.533 | 0.067 | 0.267 | 0.600 | 0.230 | 0.333 | 0.267 | 0.927 | 0.917 | 0.954 |
| asr_par_text | Broca | 15 | 3 | 43.700 | 1.200 | 0.000 | 0.067 | 2.533 | 0.200 | 0.000 | 0.200 | 0.360 | 0.303 | 0.533 |
| asr_par_text | Conduction | 10 | 2 | 69.200 | 5.900 | 0.100 | 0.200 | 0.800 | 0.253 | 0.100 | 0.400 | 0.831 | 0.820 | 0.872 |
| asr_par_text | NotAphasic | 15 | 3 | 96.467 | 7.933 | 0.000 | 0.133 | 0.667 | 0.267 | 0.000 | 0.200 | 0.941 | 0.919 | 0.980 |
| asr_par_text | Wernicke | 5 | 1 | 37.100 | 2.400 | 0.000 | 0.400 | 0.800 | 0.233 | 0.400 | 0.000 | 0.648 | 0.600 | 0.733 |

## ASR Candidate By Task

| candidate_family | task | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | Cat | 12 | 12 | 71.008 | 5.333 | 0.000 | 0.000 | 0.750 | 0.191 | 0.000 | 0.000 | 0.818 | 0.795 | 0.917 |
| asr_par_text | Cinderella | 12 | 12 | 71.008 | 5.583 | 0.000 | 0.417 | 1.750 | 0.379 | 0.333 | 0.500 | 0.635 | 0.603 | 0.705 |
| asr_par_text | Sandwich | 12 | 12 | 71.008 | 4.750 | 0.083 | 0.083 | 1.333 | 0.167 | 0.000 | 0.167 | 0.757 | 0.722 | 0.819 |
| asr_par_text | Umbrella | 12 | 12 | 71.008 | 4.917 | 0.083 | 0.250 | 0.750 | 0.192 | 0.250 | 0.500 | 0.833 | 0.830 | 0.851 |
| asr_par_text | Window | 12 | 12 | 71.008 | 4.917 | 0.000 | 0.167 | 1.167 | 0.250 | 0.083 | 0.000 | 0.704 | 0.656 | 0.824 |

## ASR Candidate By Severity

| candidate_family | severity_bin | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | mild_75_93_8 | 20 | 4 | 83.375 | 6.950 | 0.050 | 0.250 | 0.550 | 0.299 | 0.300 | 0.350 | 0.937 | 0.928 | 0.960 |
| asr_par_text | moderate_50_75 | 15 | 3 | 60.433 | 2.267 | 0.067 | 0.067 | 2.867 | 0.200 | 0.000 | 0.267 | 0.525 | 0.463 | 0.722 |
| asr_par_text | severe_lt50 | 10 | 2 | 23.950 | 1.400 | 0.000 | 0.300 | 0.500 | 0.117 | 0.200 | 0.000 | 0.424 | 0.400 | 0.467 |
| asr_par_text | very_mild_or_notaphasic_ge93_8 | 15 | 3 | 96.467 | 7.933 | 0.000 | 0.133 | 0.667 | 0.267 | 0.000 | 0.200 | 0.941 | 0.919 | 0.980 |

## Interpretation

This experiment treats ASR text as the substrate a downstream LLM or clinical controller would receive. The key distinction is whether ASR mainly loses observed human concepts, which is conservative but incomplete, or adds concepts/negation/unknown-intent content, which is unsafe for communication support. A safe product should use raw human/ASR speech for assessment, and only reconstruct when a controller can prove intent evidence is strong enough.
