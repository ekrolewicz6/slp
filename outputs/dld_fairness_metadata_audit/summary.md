# DLD Fairness And Metadata Audit

- Task: DLD_SLI_vs_TD_age_le_84
- Feature set: full_language_age
- Participants: 756

## Metadata Coverage

| metadata_field | n_known | n_total | known_rate | n_levels | levels |
| --- | --- | --- | --- | --- | --- |
| corpus | 756 | 756 | 1.000 | 10 | Ambrose, Conti, ENNI, EisenbergGuo, EllisWeismer, Feldman, Gillam, Nicholas, Rescorla, Rondal |
| age_bin_12mo | 756 | 756 | 1.000 | 6 | 12-23, 24-35, 36-47, 48-59, 60-71, 72-83 |
| sex_token | 14 | 756 | 0.019 | 2 | F, M |
| task_proxy | 542 | 756 | 0.717 | 7 | conversation, elicited_context, interview, narrative, narrative_enni, narrative_gillam, parent_child |

## Reportable Subgroup Metrics

| group_col | group | n_participants | n_dld | positive_rate | balanced_accuracy | macro_f1 | positive_f1 | auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| corpus | EisenbergGuo | 32 | 15 | 0.469 | 0.453 | 0.423 | 0.261 | 0.529 |
| corpus | Feldman | 265 | 207 | 0.781 | 0.525 | 0.525 | 0.792 | 0.636 |
| corpus | ENNI | 187 | 37 | 0.198 | 0.730 | 0.769 | 0.610 | 0.856 |
| age_bin_12mo | 72-83 | 78 | 18 | 0.231 | 0.658 | 0.690 | 0.480 | 0.787 |
| age_bin_12mo | 36-47 | 192 | 69 | 0.359 | 0.736 | 0.735 | 0.662 | 0.858 |
| age_bin_12mo | 12-23 | 76 | 42 | 0.553 | 0.740 | 0.742 | 0.787 | 0.873 |
| age_bin_12mo | 24-35 | 202 | 87 | 0.431 | 0.824 | 0.827 | 0.798 | 0.937 |
| age_bin_12mo | 48-59 | 125 | 33 | 0.264 | 0.827 | 0.846 | 0.767 | 0.927 |
| age_bin_12mo | 60-71 | 83 | 21 | 0.253 | 0.857 | 0.868 | 0.800 | 0.932 |
| sex_token | unknown | 742 | 268 | 0.361 | 0.799 | 0.803 | 0.744 | 0.905 |
| task_proxy | parent_child | 248 | 189 | 0.762 | 0.564 | 0.563 | 0.790 | 0.687 |
| task_proxy | unknown | 214 | 24 | 0.112 | 0.703 | 0.714 | 0.489 | 0.868 |
| task_proxy | narrative | 28 | 18 | 0.643 | 0.717 | 0.721 | 0.811 | 0.783 |
| task_proxy | narrative_enni | 187 | 37 | 0.198 | 0.730 | 0.769 | 0.610 | 0.856 |

## Subgroup Metric Ranges

| group_col | n_reportable_groups | macro_f1_min | macro_f1_max | macro_f1_range | auc_min | auc_max | auc_range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| corpus | 3 | 0.423 | 0.769 | 0.345 | 0.529 | 0.856 | 0.327 |
| task_proxy | 4 | 0.563 | 0.769 | 0.205 | 0.687 | 0.868 | 0.181 |
| age_bin_12mo | 6 | 0.690 | 0.868 | 0.178 | 0.787 | 0.937 | 0.150 |

## Interpretation

- Corpus and age subgroup audits are feasible locally.
- Sex/gender coverage from path tokens is sparse and corpus-biased, so it is not a reliable fairness audit.
- Dialect, bilingual exposure, socioeconomic status, race/ethnicity, and intervention history are not available in the current feature table.
- Any clinically serious DLD screening claim needs a prospective or linked dataset with explicit demographic and language-exposure metadata.
