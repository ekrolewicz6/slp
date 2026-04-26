# ASR Reconstruction Safety

- Items/task rows: 233
- Patients: 52
- Mean ASR F1 vs human concepts: 0.742
- Mean ASR recall vs human concepts: 0.703
- Mean ASR precision vs human concepts: 0.817

## Headline Safety Readout

- ASR observed-concept loss/item: 0.906 (human raw: 0.000)
- ASR concept overreach/item: 0.167 (human raw: 0.000)
- ASR unknown-intent added concepts/item: 0.064 (human raw: 0.000)
- ASR negation flip rate: 0.352 (human raw: 0.000)
- Mean ASR minus raw observed-loss delta: 0.906
- Mean ASR minus raw overreach delta: 0.167

## Overall Candidate Comparison

| candidate_family | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human | r_output_concepts_wab | r_overreach_wab | r_observed_loss_wab |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | 233 | 52 | 65.575 | 4.167 | 0.013 | 0.167 | 0.906 | 0.196 | 0.064 | 0.352 | 0.742 | 0.703 | 0.817 | 0.746 | -0.076 | 0.144 |
| human_oracle_targets | 233 | 52 | 65.575 | 5.142 | 0.193 | 0.000 | 0.000 | 0.446 | 0.116 | 0.009 | 0.742 | 0.703 | 0.817 | 0.767 |  |  |
| human_raw_chat | 233 | 52 | 65.575 | 4.893 | 0.000 | 0.000 | 0.000 | 0.214 | 0.000 | 0.000 | 0.742 | 0.703 | 0.817 | 0.788 |  |  |

## By Safety Bucket

| candidate_family | bucket | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | known_plus_unknown_risk | 49 | 24 | 55.637 | 3.694 | 0.000 | 0.265 | 0.796 | 0.414 | 0.265 | 0.388 | 0.802 | 0.771 | 0.899 |
| asr_par_text | known_target_safe_zone | 58 | 34 | 69.017 | 4.655 | 0.052 | 0.138 | 1.155 | 0.420 | 0.000 | 0.500 | 0.733 | 0.692 | 0.803 |
| asr_par_text | low_content_no_error | 7 | 5 | 38.600 | 0.143 | 0.000 | 0.143 | 0.000 | 0.000 | 0.000 | 0.143 | 0.000 | 0.000 | 0.000 |
| asr_par_text | low_error_content | 95 | 34 | 77.296 | 5.021 | 0.000 | 0.158 | 0.947 | 0.000 | 0.000 | 0.284 | 0.804 | 0.762 | 0.881 |
| asr_par_text | other_error | 1 | 1 | 73.400 | 4.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| asr_par_text | unknown_intent | 23 | 13 | 37.522 | 1.652 | 0.000 | 0.087 | 0.652 | 0.043 | 0.087 | 0.261 | 0.588 | 0.546 | 0.652 |
| human_oracle_targets | known_plus_unknown_risk | 49 | 24 | 55.637 | 4.776 | 0.449 | 0.000 | 0.000 | 0.988 | 0.551 | 0.020 | 0.802 | 0.771 | 0.899 |
| human_oracle_targets | known_target_safe_zone | 58 | 34 | 69.017 | 6.155 | 0.397 | 0.000 | 0.000 | 0.940 | 0.000 | 0.017 | 0.733 | 0.692 | 0.803 |
| human_oracle_targets | low_content_no_error | 7 | 5 | 38.600 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| human_oracle_targets | low_error_content | 95 | 34 | 77.296 | 5.811 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.804 | 0.762 | 0.881 |
| human_oracle_targets | other_error | 1 | 1 | 73.400 | 4.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| human_oracle_targets | unknown_intent | 23 | 13 | 37.522 | 2.217 | 0.000 | 0.000 | 0.000 | 0.043 | 0.000 | 0.000 | 0.588 | 0.546 | 0.652 |
| human_raw_chat | known_plus_unknown_risk | 49 | 24 | 55.637 | 4.224 | 0.000 | 0.000 | 0.000 | 0.447 | 0.000 | 0.000 | 0.802 | 0.771 | 0.899 |
| human_raw_chat | known_target_safe_zone | 58 | 34 | 69.017 | 5.621 | 0.000 | 0.000 | 0.000 | 0.465 | 0.000 | 0.000 | 0.733 | 0.692 | 0.803 |
| human_raw_chat | low_content_no_error | 7 | 5 | 38.600 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| human_raw_chat | low_error_content | 95 | 34 | 77.296 | 5.811 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.804 | 0.762 | 0.881 |
| human_raw_chat | other_error | 1 | 1 | 73.400 | 4.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| human_raw_chat | unknown_intent | 23 | 13 | 37.522 | 2.217 | 0.000 | 0.000 | 0.000 | 0.043 | 0.000 | 0.000 | 0.588 | 0.546 | 0.652 |

## ASR Candidate By Subtype

| candidate_family | subtype | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | Anomic | 60 | 12 | 85.350 | 5.667 | 0.000 | 0.150 | 1.250 | 0.148 | 0.017 | 0.433 | 0.878 | 0.820 | 0.976 |
| asr_par_text | Broca | 87 | 22 | 46.609 | 1.885 | 0.034 | 0.172 | 0.782 | 0.183 | 0.057 | 0.356 | 0.552 | 0.528 | 0.619 |
| asr_par_text | Conduction | 15 | 3 | 75.433 | 5.867 | 0.000 | 0.133 | 0.867 | 0.474 | 0.133 | 0.467 | 0.898 | 0.857 | 0.984 |
| asr_par_text | NotAphasic | 40 | 8 | 96.625 | 7.675 | 0.000 | 0.100 | 0.850 | 0.178 | 0.000 | 0.250 | 0.938 | 0.901 | 0.989 |
| asr_par_text | Wernicke | 31 | 7 | 35.690 | 2.323 | 0.000 | 0.290 | 0.677 | 0.211 | 0.226 | 0.258 | 0.679 | 0.639 | 0.760 |

## ASR Candidate By Task

| candidate_family | task | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | Cat | 40 | 40 | 69.892 | 5.150 | 0.000 | 0.075 | 0.925 | 0.141 | 0.000 | 0.300 | 0.812 | 0.768 | 0.884 |
| asr_par_text | Cinderella | 51 | 51 | 63.386 | 4.059 | 0.039 | 0.294 | 1.333 | 0.416 | 0.078 | 0.647 | 0.658 | 0.619 | 0.743 |
| asr_par_text | Sandwich | 50 | 50 | 64.048 | 3.600 | 0.020 | 0.040 | 0.940 | 0.117 | 0.020 | 0.200 | 0.753 | 0.699 | 0.851 |
| asr_par_text | Umbrella | 40 | 40 | 69.892 | 4.900 | 0.000 | 0.300 | 0.600 | 0.174 | 0.150 | 0.425 | 0.813 | 0.794 | 0.855 |
| asr_par_text | Window | 52 | 52 | 62.546 | 3.500 | 0.000 | 0.135 | 0.673 | 0.115 | 0.077 | 0.192 | 0.704 | 0.670 | 0.776 |

## ASR Candidate By Severity

| candidate_family | severity_bin | n | patients | mean_wab | output_concepts | concept_recovery | concept_overreach | observed_loss | known_target_token_recovery | unknown_intent_added | negation_flip | asr_f1_vs_human | asr_recall_vs_human | asr_precision_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asr_par_text | mild_75_93_8 | 70 | 14 | 84.079 | 5.871 | 0.000 | 0.157 | 1.200 | 0.211 | 0.043 | 0.457 | 0.884 | 0.829 | 0.976 |
| asr_par_text | moderate_50_75 | 45 | 9 | 60.911 | 2.956 | 0.044 | 0.111 | 0.800 | 0.195 | 0.000 | 0.333 | 0.765 | 0.723 | 0.852 |
| asr_par_text | severe_lt50 | 78 | 21 | 35.736 | 1.538 | 0.013 | 0.244 | 0.731 | 0.192 | 0.154 | 0.321 | 0.499 | 0.478 | 0.565 |
| asr_par_text | very_mild_or_notaphasic_ge93_8 | 40 | 8 | 96.625 | 7.675 | 0.000 | 0.100 | 0.850 | 0.178 | 0.000 | 0.250 | 0.938 | 0.901 | 0.989 |

## Interpretation

This experiment treats ASR text as the substrate a downstream LLM or clinical controller would receive. The key distinction is whether ASR mainly loses observed human concepts, which is conservative but incomplete, or adds concepts/negation/unknown-intent content, which is unsafe for communication support. A safe product should use raw human/ASR speech for assessment, and only reconstruct when a controller can prove intent evidence is strong enough.
