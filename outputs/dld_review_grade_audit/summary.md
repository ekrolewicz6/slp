# DLD Review-Grade Screening Audit

- Task: DLD_SLI_vs_TD_age_le_84
- Bootstrap resamples: 2000

## Participant-Level Bootstrap CIs

| feature_set | n_participants | n_positive | macro_f1 | macro_f1_lo | macro_f1_hi | auc | auc_lo | auc_hi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| corpus_age | 756 | 270 | 0.833 | 0.804 | 0.862 | 0.894 | 0.871 | 0.917 |
| full_language_age | 756 | 270 | 0.802 | 0.772 | 0.832 | 0.903 | 0.882 | 0.924 |
| full_language_no_age | 756 | 270 | 0.798 | 0.768 | 0.829 | 0.883 | 0.858 | 0.907 |
| mlu_age | 756 | 270 | 0.680 | 0.644 | 0.719 | 0.795 | 0.762 | 0.828 |
| norm_gap_mlu | 756 | 270 | 0.629 | 0.591 | 0.666 | 0.747 | 0.711 | 0.783 |
| age_only | 756 | 270 | 0.588 | 0.550 | 0.623 | 0.698 | 0.659 | 0.737 |
| norm_gap_only | 756 | 270 | 0.520 | 0.483 | 0.555 | 0.565 | 0.522 | 0.606 |

## Paired Model Differences

Positive delta means feature_set_a outperforms feature_set_b on the same participants.

| feature_set_a | feature_set_b | n_paired | delta_macro_f1 | delta_macro_f1_lo | delta_macro_f1_hi | delta_auc | delta_auc_lo | delta_auc_hi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_language_age | age_only | 756 | 0.215 | 0.168 | 0.263 | 0.205 | 0.162 | 0.247 |
| full_language_age | mlu_age | 756 | 0.122 | 0.079 | 0.163 | 0.109 | 0.077 | 0.141 |
| full_language_no_age | mlu_age | 756 | 0.118 | 0.075 | 0.162 | 0.088 | 0.054 | 0.122 |
| corpus_age | full_language_age | 756 | 0.031 | 0.003 | 0.060 | -0.009 | -0.031 | 0.011 |
| full_language_age | corpus_age | 756 | -0.031 | -0.061 | -0.003 | 0.009 | -0.012 | 0.029 |

## Corpus-Balanced Bootstrap

Each bootstrap samples equal positive and TD participant counts within corpora that contain both classes.

| feature_set | n_corpora_with_both_classes | balanced_sample_size_per_boot | macro_f1 | macro_f1_lo | macro_f1_hi | auc | auc_lo | auc_hi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| norm_gap_mlu | 4 | 236 | 0.612 | 0.553 | 0.669 | 0.703 | 0.641 | 0.760 |
| full_language_age | 4 | 236 | 0.599 | 0.547 | 0.651 | 0.669 | 0.615 | 0.721 |
| mlu_age | 4 | 236 | 0.571 | 0.512 | 0.631 | 0.658 | 0.598 | 0.722 |
| full_language_no_age | 4 | 236 | 0.567 | 0.521 | 0.619 | 0.602 | 0.547 | 0.659 |
| norm_gap_only | 4 | 236 | 0.567 | 0.524 | 0.612 | 0.658 | 0.602 | 0.714 |
| corpus_age | 4 | 236 | 0.529 | 0.503 | 0.553 | 0.543 | 0.509 | 0.578 |
| age_only | 4 | 236 | 0.428 | 0.373 | 0.484 | 0.484 | 0.414 | 0.555 |

## Negative Controls From First-Pass Run

| control | task | feature_set | n_windows | n_participants | window_balanced_accuracy | window_macro_f1 | window_auc | participant_balanced_accuracy | participant_macro_f1 | participant_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| participant_label_shuffle | DLD_SLI_vs_TD_age_le_84 | full_language_age | 1795 | 756 | 0.494 | 0.434 | 0.508 | 0.479 | 0.411 | 0.488 |
| random_features | DLD_SLI_vs_TD_age_le_84 | random_features | 1795 | 756 | 0.501 | 0.430 | 0.506 | 0.506 | 0.417 | 0.522 |

## Interpretation

- Full language state beats MLU+age and age-only with participant-level uncertainty.
- Corpus+age remains a serious artifact baseline; if it matches or beats full language, screening claims must be framed as corpus-bound.
- Corpus-balanced evaluation is the more honest estimate of transfer within the currently available Clinical-Eng data.
- The next publication-grade run should refit models inside each balanced bootstrap, not only resample held-out predictions.
