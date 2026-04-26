# ASR Reconstruction Safety

- Items/task rows: 228
- Patients: 51
- Mean ASR F1 vs human concepts: 0.755
- Mean ASR recall vs human concepts: 0.717
- Mean ASR precision vs human concepts: 0.830

## Headline Safety Readout

- ASR observed-concept loss/item: 0.873 (human raw: 0.000)
- ASR concept overreach/item: 0.171 (human raw: 0.000)
- ASR unknown-intent added concepts/item: 0.066 (human raw: 0.000)
- ASR negation flip rate: 0.346 (human raw: 0.000)
- Mean ASR minus raw observed-loss delta: 0.873
- Mean ASR minus raw overreach delta: 0.171

## Overall Candidate Comparison

| candidate_family | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human | r_output_concepts_wab | r_overreach_wab | r_observed_loss_wab |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | 228 | 51 | 66.122 | 4.250 | 0.013 | 0.171 | 0.873 | 0.200 | 0.066 | 0.346 | 0.755 | 0.717 | 0.830 | 0.740 | -0.087 | 0.180 |
| human_oracle_targets | 228 | 51 | 66.122 | 5.171 | 0.180 | 0.000 | 0.000 | 0.438 | 0.118 | 0.004 | 0.755 | 0.717 | 0.830 | 0.769 |  |  |
| human_raw_chat | 228 | 51 | 66.122 | 4.939 | 0.000 | 0.000 | 0.000 | 0.213 | 0.000 | 0.000 | 0.755 | 0.717 | 0.830 | 0.787 |  |  |

## By Safety Bucket

| candidate_family | bucket | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | known_plus_unknown_risk | 49 | 24 | 55.637 | 3.694 | 0.000 | 0.265 | 0.796 | 0.414 | 0.265 | 0.388 | 0.802 | 0.771 | 0.899 |
| asr_par_text | known_target_safe_zone | 54 | 32 | 71.122 | 5.000 | 0.056 | 0.148 | 1.056 | 0.451 | 0.000 | 0.481 | 0.788 | 0.743 | 0.862 |
| asr_par_text | low_content_no_error | 7 | 5 | 38.600 | 0.143 | 0.000 | 0.143 | 0.000 | 0.000 | 0.000 | 0.143 | 0.000 | 0.000 | 0.000 |
| asr_par_text | low_error_content | 94 | 33 | 77.686 | 5.053 | 0.000 | 0.160 | 0.936 | 0.000 | 0.000 | 0.287 | 0.806 | 0.765 | 0.880 |
| asr_par_text | other_error | 1 | 1 | 73.400 | 4.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| asr_par_text | unknown_intent | 23 | 13 | 37.522 | 1.652 | 0.000 | 0.087 | 0.652 | 0.043 | 0.087 | 0.261 | 0.588 | 0.546 | 0.652 |
| human_oracle_targets | known_plus_unknown_risk | 49 | 24 | 55.637 | 4.776 | 0.449 | 0.000 | 0.000 | 0.988 | 0.551 | 0.020 | 0.802 | 0.771 | 0.899 |
| human_oracle_targets | known_target_safe_zone | 54 | 32 | 71.122 | 6.333 | 0.352 | 0.000 | 0.000 | 0.935 | 0.000 | 0.000 | 0.788 | 0.743 | 0.862 |
| human_oracle_targets | low_content_no_error | 7 | 5 | 38.600 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| human_oracle_targets | low_error_content | 94 | 33 | 77.686 | 5.830 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.806 | 0.765 | 0.880 |
| human_oracle_targets | other_error | 1 | 1 | 73.400 | 4.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| human_oracle_targets | unknown_intent | 23 | 13 | 37.522 | 2.217 | 0.000 | 0.000 | 0.000 | 0.043 | 0.000 | 0.000 | 0.588 | 0.546 | 0.652 |
| human_raw_chat | known_plus_unknown_risk | 49 | 24 | 55.637 | 4.224 | 0.000 | 0.000 | 0.000 | 0.447 | 0.000 | 0.000 | 0.802 | 0.771 | 0.899 |
| human_raw_chat | known_target_safe_zone | 54 | 32 | 71.122 | 5.852 | 0.000 | 0.000 | 0.000 | 0.474 | 0.000 | 0.000 | 0.788 | 0.743 | 0.862 |
| human_raw_chat | low_content_no_error | 7 | 5 | 38.600 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| human_raw_chat | low_error_content | 94 | 33 | 77.686 | 5.830 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.806 | 0.765 | 0.880 |
| human_raw_chat | other_error | 1 | 1 | 73.400 | 4.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| human_raw_chat | unknown_intent | 23 | 13 | 37.522 | 2.217 | 0.000 | 0.000 | 0.000 | 0.043 | 0.000 | 0.000 | 0.588 | 0.546 | 0.652 |

## ASR Candidate By Subtype

| candidate_family | subtype | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | Anomic | 60 | 12 | 85.350 | 5.667 | 0.000 | 0.150 | 1.250 | 0.148 | 0.017 | 0.433 | 0.878 | 0.820 | 0.976 |
| asr_par_text | Broca | 82 | 21 | 46.976 | 1.976 | 0.037 | 0.183 | 0.683 | 0.195 | 0.061 | 0.341 | 0.578 | 0.554 | 0.644 |
| asr_par_text | Conduction | 15 | 3 | 75.433 | 5.867 | 0.000 | 0.133 | 0.867 | 0.474 | 0.133 | 0.467 | 0.898 | 0.857 | 0.984 |
| asr_par_text | NotAphasic | 40 | 8 | 96.625 | 7.675 | 0.000 | 0.100 | 0.850 | 0.178 | 0.000 | 0.250 | 0.938 | 0.901 | 0.989 |
| asr_par_text | Wernicke | 31 | 7 | 35.690 | 2.323 | 0.000 | 0.290 | 0.677 | 0.211 | 0.226 | 0.258 | 0.679 | 0.639 | 0.760 |

## ASR Candidate By Task

| candidate_family | task | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | Cat | 40 | 40 | 69.892 | 5.150 | 0.000 | 0.075 | 0.925 | 0.141 | 0.000 | 0.300 | 0.812 | 0.768 | 0.884 |
| asr_par_text | Cinderella | 49 | 49 | 64.316 | 4.224 | 0.041 | 0.306 | 1.306 | 0.433 | 0.082 | 0.633 | 0.684 | 0.644 | 0.773 |
| asr_par_text | Sandwich | 48 | 48 | 65.025 | 3.750 | 0.021 | 0.042 | 0.854 | 0.122 | 0.021 | 0.188 | 0.785 | 0.729 | 0.886 |
| asr_par_text | Umbrella | 40 | 40 | 69.892 | 4.900 | 0.000 | 0.300 | 0.600 | 0.174 | 0.150 | 0.425 | 0.813 | 0.794 | 0.855 |
| asr_par_text | Window | 51 | 51 | 62.976 | 3.529 | 0.000 | 0.137 | 0.647 | 0.118 | 0.078 | 0.196 | 0.705 | 0.674 | 0.771 |

## ASR Candidate By Severity

| candidate_family | severity_bin | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | mild_75_93_8 | 70 | 14 | 84.079 | 5.871 | 0.000 | 0.157 | 1.200 | 0.211 | 0.043 | 0.457 | 0.884 | 0.829 | 0.976 |
| asr_par_text | moderate_50_75 | 45 | 9 | 60.911 | 2.956 | 0.044 | 0.111 | 0.800 | 0.195 | 0.000 | 0.333 | 0.765 | 0.723 | 0.852 |
| asr_par_text | severe_lt50 | 73 | 20 | 35.403 | 1.616 | 0.014 | 0.260 | 0.616 | 0.205 | 0.164 | 0.301 | 0.524 | 0.504 | 0.590 |
| asr_par_text | very_mild_or_notaphasic_ge93_8 | 40 | 8 | 96.625 | 7.675 | 0.000 | 0.100 | 0.850 | 0.178 | 0.000 | 0.250 | 0.938 | 0.901 | 0.989 |

## Interpretation

This experiment treats ASR text as the substrate a downstream LLM or clinical controller would receive. The key distinction is whether ASR mainly loses observed human concepts, which is conservative but incomplete, or adds concepts/negation/unknown-intent content, which is unsafe for communication support. A safe product should use raw human/ASR speech for assessment, and only reconstruct when a controller can prove intent evidence is strong enough.
