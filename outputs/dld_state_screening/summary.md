# DLD State Screening Summary

## Inventory

- Clinical-Eng windows: 4067
- Reconstructed participant roots: 1562
- Corpora: 17
- Window label counts: {'HL': 78, 'TD': 1603, 'FamilyRisk': 10, 'DLD_SLI': 636, 'LateTalker': 635, 'DS': 228}
- Participant label counts: {'TD': 779, 'DLD_SLI': 329, 'DS': 101, 'LateTalker': 93, 'HL': 19, 'FamilyRisk': 6}

## External TD Normative Age Model

| n_td_windows | n_td_children | age_min | age_max | grouped_cv_mae_months | grouped_cv_corr |
| --- | --- | --- | --- | --- | --- |
| 16527 | 276 | 6.000 | 84.000 | 5.813 | 0.765 |

## Normative Language-Age Gap By Label

| clinical_label | n_windows | n_participants | age_mean | pred_age_mean | gap_mean | gap_median | gap_q25 | gap_q75 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DS | 111 | 53 | 54.367 | 27.358 | -27.009 | -26.034 | -31.761 | -17.244 |
| DLD_SLI | 562 | 270 | 43.123 | 35.549 | -7.574 | -5.074 | -15.348 | 2.259 |
| LateTalker | 432 | 91 | 45.095 | 37.938 | -7.157 | -6.928 | -11.253 | -2.579 |
| HL | 78 | 19 | 32.270 | 27.475 | -4.795 | -3.706 | -9.974 | 0.256 |
| FamilyRisk | 10 | 6 | 31.717 | 27.639 | -4.078 | -3.264 | -6.639 | -1.942 |
| TD | 1233 | 486 | 41.762 | 40.513 | -1.248 | -0.244 | -5.460 | 4.255 |

Negative gap means the external TD model thinks the speech looks younger than chronological age.

## Participant-Held-Out Screening

| task | positive_label | feature_set | n_windows | n_participants | n_positive_windows | n_positive_participants | window_balanced_accuracy | window_macro_f1 | window_positive_f1 | window_auc | participant_balanced_accuracy | participant_macro_f1 | participant_positive_f1 | participant_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DLD_SLI_vs_TD | DLD_SLI | corpus_age | 2239 | 1108 | 636 | 329 | 0.861 | 0.856 | 0.796 | 0.922 | 0.794 | 0.804 | 0.718 | 0.861 |
| DLD_SLI_vs_TD | DLD_SLI | full_language_age | 2239 | 1108 | 636 | 329 | 0.810 | 0.813 | 0.731 | 0.917 | 0.780 | 0.792 | 0.698 | 0.900 |
| DLD_SLI_vs_TD | DLD_SLI | full_language_no_age | 2239 | 1108 | 636 | 329 | 0.801 | 0.804 | 0.718 | 0.889 | 0.772 | 0.786 | 0.688 | 0.870 |
| DLD_SLI_vs_TD | DLD_SLI | mlu_age | 2239 | 1108 | 636 | 329 | 0.675 | 0.695 | 0.524 | 0.809 | 0.661 | 0.679 | 0.501 | 0.810 |
| DLD_SLI_vs_TD | DLD_SLI | norm_gap_mlu | 2239 | 1108 | 636 | 329 | 0.628 | 0.641 | 0.430 | 0.743 | 0.603 | 0.606 | 0.371 | 0.764 |
| DLD_SLI_vs_TD | DLD_SLI | age_only | 2150 | 1071 | 636 | 329 | 0.578 | 0.572 | 0.312 | 0.747 | 0.589 | 0.585 | 0.342 | 0.700 |
| DLD_SLI_vs_TD | DLD_SLI | norm_gap_only | 1795 | 756 | 562 | 270 | 0.580 | 0.571 | 0.323 | 0.632 | 0.548 | 0.520 | 0.265 | 0.565 |
| DLD_SLI_vs_TD_age_le_84 | DLD_SLI | corpus_age | 1795 | 756 | 562 | 270 | 0.890 | 0.875 | 0.834 | 0.935 | 0.837 | 0.833 | 0.788 | 0.894 |
| DLD_SLI_vs_TD_age_le_84 | DLD_SLI | full_language_age | 1795 | 756 | 562 | 270 | 0.826 | 0.826 | 0.762 | 0.921 | 0.798 | 0.802 | 0.741 | 0.903 |
| DLD_SLI_vs_TD_age_le_84 | DLD_SLI | full_language_no_age | 1795 | 756 | 562 | 270 | 0.812 | 0.813 | 0.742 | 0.897 | 0.795 | 0.798 | 0.737 | 0.883 |
| DLD_SLI_vs_TD_age_le_84 | DLD_SLI | mlu_age | 1795 | 756 | 562 | 270 | 0.682 | 0.699 | 0.546 | 0.794 | 0.671 | 0.680 | 0.538 | 0.795 |
| DLD_SLI_vs_TD_age_le_84 | DLD_SLI | norm_gap_mlu | 1795 | 756 | 562 | 270 | 0.651 | 0.663 | 0.486 | 0.729 | 0.630 | 0.629 | 0.445 | 0.747 |
| DLD_SLI_vs_TD_age_le_84 | DLD_SLI | age_only | 1795 | 756 | 562 | 270 | 0.607 | 0.611 | 0.404 | 0.750 | 0.591 | 0.588 | 0.401 | 0.698 |
| DLD_SLI_vs_TD_age_le_84 | DLD_SLI | norm_gap_only | 1795 | 756 | 562 | 270 | 0.580 | 0.571 | 0.323 | 0.632 | 0.548 | 0.520 | 0.265 | 0.565 |
| LateTalker_vs_TD_age_le_84 | LateTalker | full_language_age | 1665 | 577 | 432 | 91 | 0.732 | 0.755 | 0.618 | 0.895 | 0.760 | 0.803 | 0.658 | 0.960 |
| LateTalker_vs_TD_age_le_84 | LateTalker | mlu_age | 1665 | 577 | 432 | 91 | 0.709 | 0.731 | 0.579 | 0.880 | 0.732 | 0.768 | 0.596 | 0.943 |
| LateTalker_vs_TD_age_le_84 | LateTalker | corpus_age | 1665 | 577 | 432 | 91 | 0.647 | 0.659 | 0.470 | 0.840 | 0.669 | 0.691 | 0.465 | 0.915 |
| LateTalker_vs_TD_age_le_84 | LateTalker | norm_gap_mlu | 1665 | 577 | 432 | 91 | 0.653 | 0.669 | 0.480 | 0.816 | 0.662 | 0.688 | 0.456 | 0.897 |
| LateTalker_vs_TD_age_le_84 | LateTalker | full_language_no_age | 1665 | 577 | 432 | 91 | 0.579 | 0.584 | 0.331 | 0.788 | 0.547 | 0.551 | 0.191 | 0.887 |
| LateTalker_vs_TD_age_le_84 | LateTalker | age_only | 1665 | 577 | 432 | 91 | 0.550 | 0.535 | 0.218 | 0.797 | 0.529 | 0.521 | 0.131 | 0.889 |
| LateTalker_vs_TD_age_le_84 | LateTalker | norm_gap_only | 1665 | 577 | 432 | 91 | 0.552 | 0.549 | 0.270 | 0.730 | 0.506 | 0.500 | 0.118 | 0.748 |

## Leave-Corpus-Out DLD/SLI Versus TD

| heldout_corpus | n_test_windows | n_test_participants | positive_rate | accuracy | balanced_accuracy | macro_f1 | positive_f1 | auc | feature_set |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Conti | 63 | 17 | 0.524 | 0.746 | 0.744 | 0.744 | 0.765 | 0.789 | mlu_age |
| ENNI | 188 | 187 | 0.197 | 0.830 | 0.598 | 0.618 | 0.333 | 0.789 | mlu_age |
| EisenbergGuo | 37 | 32 | 0.541 | 0.514 | 0.546 | 0.445 | 0.250 | 0.582 | mlu_age |
| Feldman | 600 | 265 | 0.783 | 0.273 | 0.531 | 0.256 | 0.142 | 0.484 | mlu_age |
| Conti | 63 | 17 | 0.524 | 0.683 | 0.685 | 0.682 | 0.677 | 0.733 | full_language_age |
| ENNI | 188 | 187 | 0.197 | 0.803 | 0.684 | 0.686 | 0.493 | 0.734 | full_language_age |
| EisenbergGuo | 37 | 32 | 0.541 | 0.514 | 0.537 | 0.483 | 0.357 | 0.538 | full_language_age |
| Feldman | 600 | 265 | 0.783 | 0.240 | 0.504 | 0.215 | 0.073 | 0.528 | full_language_age |
| Conti | 63 | 17 | 0.524 | 0.794 | 0.786 | 0.786 | 0.827 | 0.951 | norm_gap_mlu |
| ENNI | 188 | 187 | 0.197 | 0.809 | 0.677 | 0.684 | 0.486 | 0.819 | norm_gap_mlu |
| EisenbergGuo | 37 | 32 | 0.541 | 0.514 | 0.524 | 0.510 | 0.471 | 0.635 | norm_gap_mlu |
| Feldman | 600 | 265 | 0.783 | 0.295 | 0.542 | 0.283 | 0.191 | 0.619 | norm_gap_mlu |

## Negative Controls

| control | task | feature_set | n_windows | n_participants | window_balanced_accuracy | window_macro_f1 | window_auc | participant_balanced_accuracy | participant_macro_f1 | participant_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| participant_label_shuffle | DLD_SLI_vs_TD_age_le_84 | full_language_age | 1795 | 756 | 0.494 | 0.434 | 0.508 | 0.479 | 0.411 | 0.488 |
| random_features | DLD_SLI_vs_TD_age_le_84 | random_features | 1795 | 756 | 0.501 | 0.430 | 0.506 | 0.506 | 0.417 | 0.522 |

## Catch-Up Trajectories

| clinical_label | n_participants | median_n_ages | mean_first_gap | mean_last_gap | mean_slope_per_month | catchup_rate |
| --- | --- | --- | --- | --- | --- | --- |
| DLD_SLI | 22 | 4.000 | -14.608 | -28.700 | -9.566 | 0.045 |
| LateTalker | 76 | 3.000 | -4.923 | -11.775 | -0.237 | 0.171 |
| TD | 98 | 3.000 | 1.748 | -7.509 | -1.654 | 0.153 |

## DLD Age-Residual Clusters

| cluster | n_participants | mean_age | top_low_residual_features | top_high_residual_features | corpora |
| --- | --- | --- | --- | --- | --- |
| 0 | 29 | 55.743 | utt_len_p90:-2.89; mlu_words:-2.78; utt_len_mean:-2.78; mlu_morphemes:-2.72; ndw:-2.69; verbs_per_utterance:-2.59 | single_word_ratio:2.29; pos_n_frac:1.04; ttr:0.81; hapax_ratio:0.64; rel_MOD_frac:0.35; repetition_per_utt:-0.41 | Conti, ENNI, Feldman |
| 1 | 115 | 40.358 | single_word_ratio:-0.61; ttr:-0.39; pos_n_frac:-0.35; filler_per_utt:-0.31; pos_prep_frac:-0.26; rel_MOD_frac:-0.18 | pause_per_utt:0.79; rel_OBJ_frac:0.72; repetition_per_utt:0.66; rel_SUBJ_frac:0.44; pos_v_frac:0.38; utt_len_p50:0.36 | ENNI, EisenbergGuo, Feldman |
| 2 | 126 | 35.663 | utt_len_p90:-0.96; rel_SUBJ_frac:-0.89; function_word_ratio:-0.87; utt_len_mean:-0.86; mlu_words:-0.86; utt_len_std:-0.84 | hapax_ratio:1.32; single_word_ratio:1.24; ttr:1.18; pause_per_utt:0.12; pos_n_frac:0.07; repetition_per_utt:0.03 | ENNI, EisenbergGuo, Feldman, Gillam |

## Interpretation

- Treat these as first-pass discovery results, not clinical screening claims.
- The key comparison is whether full language state beats age-only and MLU+age under participant-held-out and corpus-held-out tests.
- The language-age gap asks whether DLD looks like simple delay; the cluster profiles ask whether DLD contains separable residual mechanisms.
- Older Clinical-Eng children exceed the external TD model's 84-month training ceiling, so age-gap and trajectory claims are currently restricted to ages <=84 months.
