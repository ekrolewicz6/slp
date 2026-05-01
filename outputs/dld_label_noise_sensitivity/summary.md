# DLD Label-Noise Sensitivity

This audit treats DLD/SLI labels as noisy clinical anchors rather than clean ground truth.

## Symmetric Label-Noise Sensitivity

| feature_set | assumed_symmetric_label_noise | macro_f1 | macro_f1_lo | macro_f1_hi | auc | auc_lo | auc_hi |
| --- | --- | --- | --- | --- | --- | --- | --- |
| age_only | 0.000 | 0.588 | 0.588 | 0.588 | 0.698 | 0.698 | 0.698 |
| age_only | 0.050 | 0.572 | 0.557 | 0.587 | 0.675 | 0.655 | 0.693 |
| age_only | 0.100 | 0.558 | 0.536 | 0.579 | 0.654 | 0.630 | 0.677 |
| age_only | 0.150 | 0.544 | 0.518 | 0.570 | 0.633 | 0.600 | 0.665 |
| age_only | 0.200 | 0.530 | 0.503 | 0.556 | 0.613 | 0.578 | 0.645 |
| age_only | 0.300 | 0.502 | 0.470 | 0.533 | 0.575 | 0.536 | 0.611 |
| corpus_age | 0.000 | 0.833 | 0.833 | 0.833 | 0.894 | 0.894 | 0.894 |
| corpus_age | 0.050 | 0.798 | 0.782 | 0.813 | 0.849 | 0.830 | 0.867 |
| corpus_age | 0.100 | 0.762 | 0.741 | 0.784 | 0.806 | 0.778 | 0.831 |
| corpus_age | 0.150 | 0.729 | 0.704 | 0.754 | 0.766 | 0.736 | 0.796 |
| corpus_age | 0.200 | 0.693 | 0.664 | 0.721 | 0.724 | 0.690 | 0.759 |
| corpus_age | 0.300 | 0.626 | 0.594 | 0.659 | 0.648 | 0.610 | 0.683 |
| full_language_age | 0.000 | 0.802 | 0.802 | 0.802 | 0.903 | 0.903 | 0.903 |
| full_language_age | 0.050 | 0.769 | 0.752 | 0.786 | 0.857 | 0.836 | 0.878 |
| full_language_age | 0.100 | 0.736 | 0.716 | 0.758 | 0.814 | 0.786 | 0.838 |
| full_language_age | 0.150 | 0.704 | 0.678 | 0.730 | 0.770 | 0.739 | 0.801 |
| full_language_age | 0.200 | 0.672 | 0.643 | 0.700 | 0.729 | 0.694 | 0.762 |
| full_language_age | 0.300 | 0.609 | 0.580 | 0.641 | 0.651 | 0.614 | 0.691 |
| full_language_no_age | 0.000 | 0.798 | 0.798 | 0.798 | 0.883 | 0.883 | 0.883 |
| full_language_no_age | 0.050 | 0.766 | 0.750 | 0.782 | 0.839 | 0.817 | 0.859 |
| full_language_no_age | 0.100 | 0.734 | 0.712 | 0.755 | 0.798 | 0.772 | 0.823 |
| full_language_no_age | 0.150 | 0.702 | 0.675 | 0.727 | 0.757 | 0.725 | 0.787 |
| full_language_no_age | 0.200 | 0.670 | 0.644 | 0.699 | 0.719 | 0.686 | 0.752 |
| full_language_no_age | 0.300 | 0.607 | 0.575 | 0.639 | 0.642 | 0.605 | 0.680 |
| mlu_age | 0.000 | 0.680 | 0.680 | 0.680 | 0.795 | 0.795 | 0.795 |
| mlu_age | 0.050 | 0.655 | 0.639 | 0.671 | 0.761 | 0.740 | 0.780 |
| mlu_age | 0.100 | 0.631 | 0.609 | 0.653 | 0.728 | 0.702 | 0.755 |
| mlu_age | 0.150 | 0.607 | 0.580 | 0.631 | 0.698 | 0.667 | 0.728 |
| mlu_age | 0.200 | 0.583 | 0.555 | 0.611 | 0.668 | 0.633 | 0.701 |
| mlu_age | 0.300 | 0.537 | 0.504 | 0.568 | 0.610 | 0.569 | 0.649 |

## High-Confidence Label-Conflict Summary

| label_noise_flag | n | n_dld_labels | mean_full_language_no_age | mean_full_language_age | mean_corpus_age | mean_age_min |
| --- | --- | --- | --- | --- | --- | --- |
| no_high_conflict | 674 | 209 | 0.331 | 0.324 | 0.327 | 42.454 |
| DLD_label_but_state_TD_like | 31 | 31 | 0.135 | 0.154 | 0.372 | 53.563 |
| corpus_age_driven_risk | 27 | 20 | 0.358 | 0.410 | 0.806 | 40.916 |
| TD_label_but_state_risk | 12 | 0 | 0.846 | 0.843 | 0.690 | 36.394 |
| language_state_risk_without_corpus | 12 | 10 | 0.840 | 0.824 | 0.315 | 37.308 |

## High-Confidence Conflicts By Corpus

| corpus | label_noise_flag | n |
| --- | --- | --- |
| Conti | corpus_age_driven_risk | 3 |
| ENNI | DLD_label_but_state_TD_like | 14 |
| ENNI | language_state_risk_without_corpus | 6 |
| ENNI | TD_label_but_state_risk | 1 |
| EisenbergGuo | DLD_label_but_state_TD_like | 7 |
| EisenbergGuo | TD_label_but_state_risk | 2 |
| EisenbergGuo | corpus_age_driven_risk | 1 |
| EisenbergGuo | language_state_risk_without_corpus | 1 |
| Feldman | corpus_age_driven_risk | 23 |
| Feldman | TD_label_but_state_risk | 9 |
| Feldman | DLD_label_but_state_TD_like | 8 |
| Feldman | language_state_risk_without_corpus | 5 |
| Gillam | DLD_label_but_state_TD_like | 2 |

## Example Conflict Candidates

| participant_root | corpus | y_true | age_min | full_language_no_age | full_language_age | mlu_age | corpus_age | label_noise_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clinical-Eng/ENNI/DLD_SLI/474 | ENNI | 1 | 56.600 | 0.125 | 0.106 | 0.223 | 0.213 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/479 | ENNI | 1 | 57.267 | 0.229 | 0.217 | 0.241 | 0.190 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/480 | ENNI | 1 | 52.167 | 0.193 | 0.150 | 0.151 | 0.096 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/570 | ENNI | 1 | 69.700 | 0.139 | 0.242 | 0.046 | 0.141 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/572 | ENNI | 1 | 65.000 | 0.163 | 0.183 | 0.170 | 0.178 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/574 | ENNI | 1 | 60.867 | 0.113 | 0.135 | 0.132 | 0.201 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/575 | ENNI | 1 | 62.833 | 0.176 | 0.155 | 0.080 | 0.202 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/607 | ENNI | 1 | 73.500 | 0.051 | 0.058 | 0.078 | 0.092 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/609 | ENNI | 1 | 79.867 | 0.079 | 0.078 | 0.100 | 0.131 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/617 | ENNI | 1 | 78.833 | 0.084 | 0.154 | 0.085 | 0.154 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/667 | ENNI | 1 | 77.733 | 0.116 | 0.176 | 0.130 | 0.141 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/673 | ENNI | 1 | 83.267 | 0.234 | 0.185 | 0.103 | 0.147 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/678 | ENNI | 1 | 82.800 | 0.136 | 0.204 | 0.324 | 0.158 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/DLD_SLI/679 | ENNI | 1 | 80.800 | 0.156 | 0.196 | 0.096 | 0.131 | DLD_label_but_state_TD_like |
| Clinical-Eng/EisenbergGuo/DLD_SLI/019jc | EisenbergGuo | 1 | 41.000 | 0.119 | 0.119 | 0.569 | 0.427 | DLD_label_but_state_TD_like |
| Clinical-Eng/EisenbergGuo/DLD_SLI/035cb | EisenbergGuo | 1 | 45.000 | 0.084 | 0.083 | 0.126 | 0.503 | DLD_label_but_state_TD_like |
| Clinical-Eng/EisenbergGuo/DLD_SLI/064jg | EisenbergGuo | 1 | 37.000 | 0.101 | 0.129 | 0.463 | 0.581 | DLD_label_but_state_TD_like |
| Clinical-Eng/EisenbergGuo/DLD_SLI/073cb | EisenbergGuo | 1 | 41.000 | 0.129 | 0.115 | 0.262 | 0.419 | DLD_label_but_state_TD_like |
| Clinical-Eng/EisenbergGuo/DLD_SLI/083bb | EisenbergGuo | 1 | 38.000 | 0.087 | 0.107 | 0.309 | 0.526 | DLD_label_but_state_TD_like |
| Clinical-Eng/EisenbergGuo/DLD_SLI/084gd | EisenbergGuo | 1 | 45.000 | 0.125 | 0.187 | 0.222 | 0.338 | DLD_label_but_state_TD_like |
| Clinical-Eng/EisenbergGuo/DLD_SLI/109am | EisenbergGuo | 1 | 43.000 | 0.111 | 0.087 | 0.224 | 0.366 | DLD_label_but_state_TD_like |
| Clinical-Eng/Feldman/DLD_SLI/bra27 | Feldman | 1 | 27.000 | 0.201 | 0.127 | 0.200 | 0.796 | DLD_label_but_state_TD_like |
| Clinical-Eng/Feldman/DLD_SLI/ces42 | Feldman | 1 | 42.000 | 0.246 | 0.227 | 0.147 | 0.718 | DLD_label_but_state_TD_like |
| Clinical-Eng/Feldman/DLD_SLI/gig18 | Feldman | 1 | 18.000 | 0.154 | 0.139 | 0.581 | 0.712 | DLD_label_but_state_TD_like |
| Clinical-Eng/Feldman/DLD_SLI/hin33 | Feldman | 1 | 33.000 | 0.166 | 0.232 | 0.596 | 0.836 | DLD_label_but_state_TD_like |
| Clinical-Eng/Feldman/DLD_SLI/hin39 | Feldman | 1 | 39.000 | 0.160 | 0.204 | 0.434 | 0.738 | DLD_label_but_state_TD_like |
| Clinical-Eng/Feldman/DLD_SLI/mey30 | Feldman | 1 | 30.233 | 0.119 | 0.196 | 0.733 | 0.796 | DLD_label_but_state_TD_like |
| Clinical-Eng/Feldman/DLD_SLI/sno33 | Feldman | 1 | 32.000 | 0.106 | 0.248 | 0.904 | 0.801 | DLD_label_but_state_TD_like |
| Clinical-Eng/Feldman/DLD_SLI/sul18 | Feldman | 1 | 19.000 | 0.215 | 0.202 | 0.485 | 0.719 | DLD_label_but_state_TD_like |
| Clinical-Eng/Gillam/DLD_SLI/a-1-08 | Gillam | 1 | 75.000 | 0.042 | 0.086 | 0.696 | 0.046 | DLD_label_but_state_TD_like |
| Clinical-Eng/Gillam/DLD_SLI/a-2-61pre | Gillam | 1 | 74.000 | 0.025 | 0.045 | 0.667 | 0.050 | DLD_label_but_state_TD_like |
| Clinical-Eng/ENNI/TD/452 | ENNI | 0 | 48.400 | 0.923 | 0.918 | 0.690 | 0.139 | TD_label_but_state_risk |
| Clinical-Eng/EisenbergGuo/TD/058nr | EisenbergGuo | 0 | 36.000 | 0.832 | 0.771 | 0.388 | 0.821 | TD_label_but_state_risk |
| Clinical-Eng/EisenbergGuo/TD/072ag | EisenbergGuo | 0 | 39.000 | 0.818 | 0.836 | 0.301 | 0.421 | TD_label_but_state_risk |
| Clinical-Eng/Feldman/TD/dr2 | Feldman | 0 | 61.400 | 0.752 | 0.862 | 0.670 | 0.782 | TD_label_but_state_risk |
| Clinical-Eng/Feldman/TD/nchi0842 | Feldman | 0 | 42.000 | 0.854 | 0.827 | 0.196 | 0.718 | TD_label_but_state_risk |
| Clinical-Eng/Feldman/TD/nchi1336 | Feldman | 0 | 36.000 | 0.850 | 0.879 | 0.271 | 0.817 | TD_label_but_state_risk |
| Clinical-Eng/Feldman/TD/nchi1821 | Feldman | 0 | 24.000 | 0.912 | 0.878 | 0.296 | 0.813 | TD_label_but_state_risk |
| Clinical-Eng/Feldman/TD/nma239 | Feldman | 0 | 39.667 | 0.795 | 0.807 | 0.641 | 0.776 | TD_label_but_state_risk |
| Clinical-Eng/Feldman/TD/pdan33 | Feldman | 0 | 33.567 | 0.834 | 0.889 | 0.900 | 0.864 | TD_label_but_state_risk |

## Interpretation

The screening signal should be framed as a noisy-label measurement result, not a diagnostic classifier. High-confidence discordant cases are not automatically mislabeled; they are the participants where corpus/task context, diagnosis, and language-state evidence disagree enough to require corpus-level review.
