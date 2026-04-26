# ASR Prompt-Contamination Experiment

- Sessions: 12
- Task rows: 50
- Mean full task-window seconds: 104.0

## Summary

| rows | sessions | par_mean_f1 | full_mean_f1 | mean_delta_f1 | mean_delta_recall | mean_delta_precision | mean_delta_false_positive | mean_inv_chat_concepts | r_par_coverage_wab | r_full_coverage_wab |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | 12 | 0.756 | 0.761 | 0.005 | 0.076 | -0.068 | 0.400 | 0.980 | 0.775 | 0.800 |

## By Task

| task | n | mean_inv_concepts | par_f1 | full_f1 | delta_f1 | delta_recall | delta_precision | delta_false_positive | delta_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cat | 9 | 0.000 | 0.806 | 0.761 | -0.045 | 0.002 | -0.096 | 0.333 | 0.037 |
| Cinderella | 10 | 0.700 | 0.572 | 0.727 | 0.155 | 0.192 | 0.135 | 0.000 | 0.033 |
| Sandwich | 10 | 2.600 | 0.880 | 0.788 | -0.092 | 0.014 | -0.199 | 0.600 | 0.083 |
| Umbrella | 9 | 1.000 | 0.875 | 0.815 | -0.059 | 0.030 | -0.166 | 0.889 | 0.089 |
| Window | 12 | 0.583 | 0.680 | 0.726 | 0.046 | 0.119 | -0.032 | 0.250 | 0.062 |

## Interpretation

If full task-window ASR improves recall while also increasing false positives or investigator-chat concept counts, prompt contamination is a real risk. PAR-only utterance ASR is the safer measurement default; full-window ASR should be used only after separating speakers or proving that interviewer speech does not add task concepts.
