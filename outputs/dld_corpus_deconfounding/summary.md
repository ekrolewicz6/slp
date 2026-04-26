# DLD Corpus Deconfounding Summary

## Corpus/Label Inventory

| corpus | screen_label | windows | participants |
| --- | --- | --- | --- |
| Ambrose | TD | 110 | 18 |
| Conti | DLD_SLI | 33 | 9 |
| Conti | TD | 30 | 8 |
| ENNI | DLD_SLI | 37 | 37 |
| ENNI | TD | 151 | 150 |
| EisenbergGuo | DLD_SLI | 20 | 15 |
| EisenbergGuo | TD | 17 | 17 |
| EllisWeismer | TD | 373 | 76 |
| Feldman | DLD_SLI | 470 | 207 |
| Feldman | TD | 130 | 58 |
| Gillam | DLD_SLI | 2 | 2 |
| Gillam | TD | 12 | 12 |
| Nicholas | TD | 211 | 79 |
| Rescorla | TD | 80 | 27 |
| Rondal | TD | 119 | 41 |

## Within-Corpus Metrics

Each row trains and tests within one corpus using participant-held-out folds.

| corpus | feature_set | n_windows | n_participants | n_dld_participants | window_macro_f1 | window_auc | participant_balanced_accuracy | participant_macro_f1 | participant_positive_f1 | participant_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Conti | full_language_age | 63 | 17 | 9 | 0.825 | 0.816 | 0.944 | 0.941 | 0.941 | 0.896 |
| Conti | age_only | 63 | 17 | 9 | 0.778 | 0.747 | 0.889 | 0.882 | 0.875 | 0.861 |
| Conti | mlu_age | 63 | 17 | 9 | 0.825 | 0.749 | 0.889 | 0.882 | 0.875 | 0.896 |
| Conti | full_language_no_age | 63 | 17 | 9 | 0.365 | 0.277 | 0.236 | 0.235 | 0.235 | 0.250 |
| ENNI | mlu_age | 188 | 187 | 37 | 0.724 | 0.762 | 0.707 | 0.724 | 0.545 | 0.761 |
| ENNI | full_language_age | 188 | 187 | 37 | 0.703 | 0.815 | 0.676 | 0.702 | 0.500 | 0.815 |
| ENNI | full_language_no_age | 188 | 187 | 37 | 0.688 | 0.795 | 0.663 | 0.688 | 0.475 | 0.795 |
| ENNI | age_only | 188 | 187 | 37 | 0.416 | 0.376 | 0.443 | 0.416 | 0.000 | 0.375 |
| EisenbergGuo | age_only | 37 | 32 | 15 | 0.644 | 0.557 | 0.661 | 0.656 | 0.667 | 0.557 |
| EisenbergGuo | full_language_age | 37 | 32 | 15 | 0.674 | 0.750 | 0.657 | 0.656 | 0.645 | 0.694 |
| EisenbergGuo | full_language_no_age | 37 | 32 | 15 | 0.644 | 0.747 | 0.627 | 0.625 | 0.625 | 0.686 |
| EisenbergGuo | mlu_age | 37 | 32 | 15 | 0.674 | 0.721 | 0.624 | 0.624 | 0.600 | 0.680 |
| Feldman | mlu_age | 600 | 265 | 207 | 0.561 | 0.635 | 0.536 | 0.526 | 0.866 | 0.625 |
| Feldman | full_language_age | 600 | 265 | 207 | 0.553 | 0.638 | 0.536 | 0.515 | 0.879 | 0.646 |
| Feldman | full_language_no_age | 600 | 265 | 207 | 0.544 | 0.592 | 0.511 | 0.479 | 0.868 | 0.610 |
| Feldman | age_only | 600 | 265 | 207 | 0.436 | 0.551 | 0.488 | 0.454 | 0.852 | 0.578 |

## Pooled Within-Corpus Prediction Summary

| feature_set | n_participants | n_dld | participant_balanced_accuracy | participant_macro_f1 | participant_auc |
| --- | --- | --- | --- | --- | --- |
| full_language_age | 501 | 268 | 0.798 | 0.800 | 0.844 |
| mlu_age | 501 | 268 | 0.785 | 0.787 | 0.828 |
| full_language_no_age | 501 | 268 | 0.760 | 0.762 | 0.811 |
| age_only | 501 | 268 | 0.726 | 0.727 | 0.766 |

## Age-Bin Matched Within-Corpus Metrics

Restricts to corpus x 12-month age bins containing both TD and DLD/SLI participants.

| corpus | feature_set | n_windows | n_participants | n_dld_participants | window_macro_f1 | window_auc | participant_balanced_accuracy | participant_macro_f1 | participant_positive_f1 | participant_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ENNI | mlu_age | 188 | 187 | 37 | 0.724 | 0.762 | 0.707 | 0.724 | 0.545 | 0.761 |
| ENNI | full_language_age | 188 | 187 | 37 | 0.703 | 0.815 | 0.676 | 0.702 | 0.500 | 0.815 |
| ENNI | full_language_no_age | 188 | 187 | 37 | 0.688 | 0.795 | 0.663 | 0.688 | 0.475 | 0.795 |
| ENNI | age_only | 188 | 187 | 37 | 0.416 | 0.376 | 0.443 | 0.416 | 0.000 | 0.375 |
| EisenbergGuo | age_only | 37 | 32 | 15 | 0.644 | 0.557 | 0.661 | 0.656 | 0.667 | 0.557 |
| EisenbergGuo | full_language_age | 37 | 32 | 15 | 0.674 | 0.750 | 0.657 | 0.656 | 0.645 | 0.694 |
| EisenbergGuo | full_language_no_age | 37 | 32 | 15 | 0.644 | 0.747 | 0.627 | 0.625 | 0.625 | 0.686 |
| EisenbergGuo | mlu_age | 37 | 32 | 15 | 0.674 | 0.721 | 0.624 | 0.624 | 0.600 | 0.680 |
| Feldman | mlu_age | 600 | 265 | 207 | 0.561 | 0.635 | 0.536 | 0.526 | 0.866 | 0.625 |
| Feldman | full_language_age | 600 | 265 | 207 | 0.553 | 0.638 | 0.536 | 0.515 | 0.879 | 0.646 |
| Feldman | full_language_no_age | 600 | 265 | 207 | 0.544 | 0.592 | 0.511 | 0.479 | 0.868 | 0.610 |
| Feldman | age_only | 600 | 265 | 207 | 0.436 | 0.551 | 0.488 | 0.454 | 0.852 | 0.578 |

## Age-Bin Matched Pooled Summary

| feature_set | n_participants | n_dld | participant_balanced_accuracy | participant_macro_f1 | participant_auc |
| --- | --- | --- | --- | --- | --- |
| full_language_age | 484 | 259 | 0.793 | 0.795 | 0.839 |
| mlu_age | 484 | 259 | 0.781 | 0.783 | 0.822 |
| full_language_no_age | 484 | 259 | 0.779 | 0.781 | 0.823 |
| age_only | 484 | 259 | 0.720 | 0.721 | 0.760 |

## Interpretation

- If full language features remain useful within corpus, the signal is not only corpus membership.
- If performance collapses after age-bin matching, apparent screening performance is mostly age/task/corpus composition.
- Small corpora and path-derived labels still make this a discovery audit, not a clinical screening result.
