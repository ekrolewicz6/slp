# DLD High-Conflict Taxonomy

- Participants audited: 756
- High-confidence conflicts: 82
- Conflict rate: 0.108

## Review Priority Summary

| review_priority | n |
| --- | --- |
| review_for_label_history_or_resolved_state | 31 |
| deconfounding_not_clinical_claim | 27 |
| highest_scientific_review | 12 |
| review_for_hidden_risk_or_context | 9 |
| highest_clinical_fairness_review | 3 |

## Conflict Archetypes

| conflict_archetype | review_priority | n | n_dld_labels | mean_age_min | mean_full_language_no_age | mean_corpus_age | mean_mlu_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| corpus_age_prior_without_language_state | deconfounding_not_clinical_claim | 27 | 20 | 40.916 | 0.358 | 0.806 | 0.493 |
| DLD_label_TD_state_broadly | review_for_label_history_or_resolved_state | 24 | 24 | 56.551 | 0.144 | 0.328 | 0.201 |
| TD_label_state_risk_plus_corpus_prior | review_for_hidden_risk_or_context | 9 | 0 | 36.481 | 0.838 | 0.789 | 0.465 |
| DLD_label_TD_state_but_MLU_risk | review_for_label_history_or_resolved_state | 7 | 7 | 43.319 | 0.104 | 0.524 | 0.678 |
| language_risk_without_corpus_not_MLU_only | highest_scientific_review | 7 | 6 | 31.895 | 0.848 | 0.347 | 0.359 |
| language_risk_without_corpus_with_MLU | highest_scientific_review | 5 | 4 | 44.887 | 0.829 | 0.270 | 0.593 |
| TD_label_state_risk_language_driven | highest_clinical_fairness_review | 3 | 0 | 36.133 | 0.869 | 0.393 | 0.527 |

## Highest Corpus-Level Conflict Rates

| corpus | total_participants | high_conflict_n | high_conflict_rate |
| --- | --- | --- | --- |
| EisenbergGuo | 32 | 11.000 | 0.344 |
| Conti | 17 | 3.000 | 0.176 |
| Feldman | 265 | 45.000 | 0.170 |
| Gillam | 14 | 2.000 | 0.143 |
| ENNI | 187 | 21.000 | 0.112 |
| Ambrose | 18 | 0.000 | 0.000 |
| EllisWeismer | 76 | 0.000 | 0.000 |
| Nicholas | 79 | 0.000 | 0.000 |
| Rescorla | 27 | 0.000 | 0.000 |
| Rondal | 41 | 0.000 | 0.000 |

## Conflict Counts By Corpus And Flag

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

## Conflict Rates By Age Band

| age_band | total_participants | high_conflict_n | high_conflict_rate |
| --- | --- | --- | --- |
| 48-60m | 117 | 17 | 0.145 |
| 72-96m | 77 | 10 | 0.130 |
| 36-48m | 165 | 21 | 0.127 |
| 60-72m | 76 | 8 | 0.105 |
| <36m | 321 | 26 | 0.081 |

## Conflict Rates By Task Context

| task_bucket | total_participants | high_conflict_n | high_conflict_rate |
| --- | --- | --- | --- |
| natural_conversation | 265 | 45.000 | 0.170 |
| narrative_story | 201 | 23.000 | 0.114 |
| unknown | 214 | 14.000 | 0.065 |
| elicited_context | 76 | 0.000 | 0.000 |

## Interpretation

The most scientifically valuable cases are not the easiest DLD-vs-TD classifications. They are the disagreements where language-state risk remains high after removing corpus/age priors, or where TD labels conflict with language-driven risk. Corpus-age-driven cases should be treated as deconfounding warnings, not clinical evidence. DLD-labeled but TD-like state cases may reflect resolved/compensated state, label-history effects, task insensitivity, or a language dimension not captured by the current feature set.
