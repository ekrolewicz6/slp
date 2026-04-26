# DLD Narrative Proxy Summary

- Narrative-like windows: 664
- Participant-task rows: 521

## Task-Level Proxy State

Proxy z scores are oriented so higher means more TD-like within the same corpus/task reference.

| corpus | task_proxy | clinical_label | n_participants | mean_age | mean_narrative_proxy_z | mean_event_structure_proxy_z | mean_lexical_elaboration_proxy_z | mean_repair_burden_proxy_z | mean_mlu | mean_ndw |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ENNI | narrative_enni | DLD_SLI | 76 | 84.977 | -0.513 | 0.039 | -0.848 | -0.600 | 5.940 | 132.559 |
| ENNI | narrative_enni | TD | 297 | 84.340 | -0.000 | -0.000 | 0.000 | 0.000 | 7.333 | 159.912 |
| Feldman | narrative | DLD_SLI | 18 | 63.998 | -0.409 | -0.191 | -0.999 | 0.272 | 4.221 | 154.483 |
| Feldman | narrative | TD | 10 | 60.349 | -0.000 | -0.000 | 0.000 | -0.000 | 5.082 | 170.345 |
| Gillam | narrative_gillam | DLD_SLI | 19 | 103.474 | -0.674 | -0.169 | -1.115 | -0.965 | 6.561 | 168.842 |
| Gillam | narrative_gillam | TD | 101 | 108.149 | 0.000 | 0.000 | 0.000 | 0.000 | 8.151 | 206.297 |

## Narrative Proxy Classifiers

| analysis | n_participants | n_dld | balanced_accuracy | macro_f1 | positive_f1 | auc |
| --- | --- | --- | --- | --- | --- | --- |
| all_narrative | 521 | 113 | 0.735 | 0.764 | 0.614 | 0.863 |
| ENNI_narrative_enni | 373 | 76 | 0.698 | 0.715 | 0.533 | 0.845 |
| Gillam_narrative_gillam | 120 | 19 | 0.661 | 0.664 | 0.432 | 0.715 |
| Feldman_narrative | 28 | 18 | 0.489 | 0.475 | 0.700 | 0.622 |

## Interpretation

- This is not true content scoring. It is a structural narrative proxy.
- ENNI and Feldman provide the main local narrative signal; Gillam has too few DLD rows in the current feature table.
- The next real step is prompt-specific main-concept rubrics for child narratives, analogous to the AphasiaBank content-state work.
