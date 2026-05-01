# DLD Task-Context Comparison

This compares narrative/story contexts with natural conversation/play contexts in the local Clinical-Eng data. It still does not test sentence repetition or nonword repetition because the local inventory found no usable candidates.

## Task Context Inventory

| task_bucket | task_proxy | corpus | screen_label | windows | participants |
| --- | --- | --- | --- | --- | --- |
| elicited_context | elicited_context | EllisWeismer | TD | 169 | 70 |
| narrative_story | narrative | Feldman | DLD_SLI | 121 | 18 |
| narrative_story | narrative | Feldman | TD | 42 | 10 |
| narrative_story | narrative_enni | ENNI | DLD_SLI | 79 | 76 |
| narrative_story | narrative_enni | ENNI | TD | 300 | 297 |
| narrative_story | narrative_gillam | Gillam | DLD_SLI | 19 | 19 |
| narrative_story | narrative_gillam | Gillam | TD | 103 | 101 |
| natural_conversation | conversation | EllisWeismer | TD | 44 | 37 |
| natural_conversation | interview | EllisWeismer | TD | 47 | 36 |
| natural_conversation | parent_child | EllisWeismer | TD | 113 | 66 |
| natural_conversation | parent_child | Feldman | DLD_SLI | 359 | 193 |
| natural_conversation | parent_child | Feldman | TD | 91 | 48 |
| unknown | unknown | Ambrose | TD | 110 | 18 |
| unknown | unknown | Conti | DLD_SLI | 35 | 9 |
| unknown | unknown | Conti | TD | 30 | 8 |
| unknown | unknown | EisenbergGuo | DLD_SLI | 20 | 15 |
| unknown | unknown | EisenbergGuo | TD | 17 | 17 |
| unknown | unknown | Nicholas | TD | 211 | 79 |
| unknown | unknown | Rescorla | TD | 107 | 36 |
| unknown | unknown | Rondal | TD | 119 | 41 |

## Metrics

| analysis | train_bucket | test_bucket | feature_set | n_participants | n_dld_participants | participant_balanced_accuracy | participant_macro_f1 | participant_positive_f1 | participant_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train_bucket_test_bucket | natural_conversation | narrative_story | full_language_age | 521 | 113 | 0.578 | 0.587 | 0.300 | 0.701 |
| train_bucket_test_bucket | natural_conversation | narrative_story | full_language_no_age | 521 | 113 | 0.575 | 0.582 | 0.288 | 0.699 |
| train_bucket_test_bucket | unknown | narrative_story | full_language_age | 521 | 113 | 0.533 | 0.514 | 0.152 | 0.654 |
| train_bucket_test_bucket | natural_conversation | narrative_story | mlu_age | 521 | 113 | 0.516 | 0.479 | 0.081 | 0.595 |
| train_bucket_test_bucket | unknown | narrative_story | full_language_no_age | 521 | 113 | 0.516 | 0.479 | 0.081 | 0.555 |
| train_bucket_test_bucket | natural_conversation | narrative_story | age_only | 521 | 113 | 0.498 | 0.461 | 0.060 | 0.552 |
| train_bucket_test_bucket | unknown | narrative_story | mlu_age | 521 | 113 | 0.509 | 0.458 | 0.035 | 0.586 |
| train_bucket_test_bucket | unknown | narrative_story | age_only | 521 | 113 | 0.482 | 0.436 | 0.290 | 0.496 |
| train_bucket_test_bucket | narrative_story | natural_conversation | full_language_age | 312 | 193 | 0.578 | 0.548 | 0.780 | 0.667 |
| train_bucket_test_bucket | unknown | natural_conversation | full_language_no_age | 312 | 193 | 0.620 | 0.514 | 0.413 | 0.738 |
| train_bucket_test_bucket | narrative_story | natural_conversation | full_language_no_age | 312 | 193 | 0.504 | 0.391 | 0.766 | 0.626 |
| train_bucket_test_bucket | narrative_story | natural_conversation | mlu_age | 312 | 193 | 0.490 | 0.311 | 0.086 | 0.482 |
| train_bucket_test_bucket | unknown | natural_conversation | mlu_age | 312 | 193 | 0.516 | 0.310 | 0.060 | 0.448 |
| train_bucket_test_bucket | narrative_story | natural_conversation | age_only | 312 | 193 | 0.511 | 0.308 | 0.060 | 0.344 |
| train_bucket_test_bucket | unknown | natural_conversation | age_only | 312 | 193 | 0.503 | 0.305 | 0.059 | 0.349 |
| train_bucket_test_bucket | unknown | natural_conversation | full_language_age | 312 | 193 | 0.510 | 0.299 | 0.041 | 0.499 |
| train_bucket_test_bucket | natural_conversation | unknown | full_language_age | 223 | 24 | 0.743 | 0.651 | 0.421 | 0.828 |
| train_bucket_test_bucket | narrative_story | unknown | mlu_age | 223 | 24 | 0.599 | 0.580 | 0.271 | 0.454 |
| train_bucket_test_bucket | natural_conversation | unknown | full_language_no_age | 223 | 24 | 0.655 | 0.578 | 0.313 | 0.780 |
| train_bucket_test_bucket | narrative_story | unknown | age_only | 223 | 24 | 0.460 | 0.451 | 0.000 | 0.553 |
| train_bucket_test_bucket | natural_conversation | unknown | mlu_age | 223 | 24 | 0.561 | 0.303 | 0.215 | 0.571 |
| train_bucket_test_bucket | natural_conversation | unknown | age_only | 223 | 24 | 0.439 | 0.250 | 0.162 | 0.503 |
| train_bucket_test_bucket | narrative_story | unknown | full_language_age | 223 | 24 | 0.373 | 0.174 | 0.140 | 0.510 |
| train_bucket_test_bucket | narrative_story | unknown | full_language_no_age | 223 | 24 | 0.512 | 0.160 | 0.197 | 0.458 |
| within_bucket_cv | narrative_story | narrative_story | full_language_age | 521 | 113 | 0.719 | 0.747 | 0.585 | 0.885 |
| within_bucket_cv | narrative_story | narrative_story | mlu_age | 521 | 113 | 0.714 | 0.738 | 0.573 | 0.865 |
| within_bucket_cv | narrative_story | narrative_story | full_language_no_age | 521 | 113 | 0.679 | 0.703 | 0.511 | 0.855 |
| within_bucket_cv | narrative_story | narrative_story | age_only | 521 | 113 | 0.535 | 0.530 | 0.203 | 0.534 |
| within_bucket_cv | natural_conversation | natural_conversation | full_language_age | 312 | 193 | 0.767 | 0.778 | 0.850 | 0.814 |
| within_bucket_cv | natural_conversation | natural_conversation | full_language_no_age | 312 | 193 | 0.762 | 0.771 | 0.845 | 0.793 |
| within_bucket_cv | natural_conversation | natural_conversation | mlu_age | 312 | 193 | 0.763 | 0.769 | 0.836 | 0.825 |
| within_bucket_cv | natural_conversation | natural_conversation | age_only | 312 | 193 | 0.749 | 0.752 | 0.817 | 0.827 |
| within_bucket_cv | unknown | unknown | full_language_age | 223 | 24 | 0.742 | 0.789 | 0.615 | 0.930 |
| within_bucket_cv | unknown | unknown | mlu_age | 223 | 24 | 0.740 | 0.780 | 0.600 | 0.954 |
| within_bucket_cv | unknown | unknown | age_only | 223 | 24 | 0.688 | 0.711 | 0.476 | 0.943 |
| within_bucket_cv | unknown | unknown | full_language_no_age | 223 | 24 | 0.550 | 0.562 | 0.188 | 0.839 |

## Interpretation

- Narrative/story data carry a usable DLD/SLI signal in the local data, especially ENNI and Gillam-style narratives.
- Natural conversation is less clean because the available DLD and TD samples are unevenly distributed across corpora and tasks.
- Cross-task transfer is the honest stress test: if train-on-narrative/test-on-natural or the reverse collapses, the model is learning task context rather than a task-general language state.
- The result supports Brian's advice: natural speech and tight/structured tasks should be paired prospectively rather than treated as interchangeable.
