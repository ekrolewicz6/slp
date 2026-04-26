# Streaming ASR Patient-Level Bootstrap Analysis

- Source: `outputs/streaming_asr_pilot_pwa30_tiny/asr_task_results.csv`
- Patients: 29
- Task rows: 150
- Utterance clips transcribed: 2602
- PAR audio transcribed: 202.75 min

## Patient-Level Bootstrap CIs

| metric | point | boot_mean | ci_low | ci_high |
| --- | --- | --- | --- | --- |
| mean_f1 | 0.764 | 0.764 | 0.656 | 0.857 |
| mean_recall | 0.718 | 0.719 | 0.610 | 0.814 |
| mean_precision | 0.856 | 0.856 | 0.754 | 0.940 |
| mean_asr_coverage | 0.434 | 0.434 | 0.344 | 0.518 |
| mean_human_coverage | 0.519 | 0.519 | 0.436 | 0.598 |
| coverage_gap_asr_minus_human | -0.085 | -0.085 | -0.123 | -0.059 |
| r_asr_coverage_wab | 0.810 | 0.806 | 0.621 | 0.925 |
| r_human_coverage_wab | 0.877 | 0.872 | 0.757 | 0.945 |
| mean_false_positive | 0.155 | 0.155 | 0.097 | 0.221 |
| mean_false_negative | 1.200 | 1.199 | 0.855 | 1.676 |

## By Task

| task | n_patients | n_task_rows | mean_wab | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cat | 29 | 30 | 72.350 | 0.764 | 0.716 | 0.856 | 0.442 | 0.550 |
| Cinderella | 29 | 30 | 72.350 | 0.727 | 0.682 | 0.830 | 0.396 | 0.478 |
| Sandwich | 29 | 30 | 72.350 | 0.749 | 0.689 | 0.872 | 0.411 | 0.525 |
| Umbrella | 29 | 30 | 72.350 | 0.821 | 0.779 | 0.902 | 0.513 | 0.590 |
| Window | 29 | 30 | 72.350 | 0.760 | 0.724 | 0.834 | 0.392 | 0.444 |

## By Subtype

| subtype | n_patients | n_task_rows | mean_wab | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Anomic | 10 | 55 | 83.636 | 0.822 | 0.768 | 0.945 | 0.478 | 0.600 |
| Broca | 6 | 30 | 42.983 | 0.522 | 0.462 | 0.658 | 0.141 | 0.220 |
| NotAphasic | 6 | 30 | 96.417 | 0.965 | 0.942 | 0.992 | 0.689 | 0.724 |
| Conduction | 3 | 15 | 67.967 | 0.838 | 0.792 | 0.913 | 0.472 | 0.554 |
| Wernicke | 2 | 10 | 49.850 | 0.823 | 0.782 | 0.904 | 0.393 | 0.432 |
| Isolation | 1 | 5 | 32.300 | 0.000 | 0.000 | 0.000 | 0.000 | 0.100 |
| TransMotor | 1 | 5 | 78.200 | 0.803 | 0.721 | 0.921 | 0.477 | 0.630 |

## By Corpus

| corpus | n_patients | n_task_rows | mean_wab | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kurland | 13 | 70 | 66.871 | 0.764 | 0.718 | 0.852 | 0.427 | 0.497 |
| NEURAL-2 | 5 | 25 | 91.240 | 0.796 | 0.748 | 0.927 | 0.553 | 0.703 |
| BU | 3 | 15 | 60.800 | 0.721 | 0.647 | 0.867 | 0.347 | 0.462 |
| MSU | 3 | 15 | 84.200 | 0.927 | 0.899 | 0.983 | 0.491 | 0.527 |
| Richardson | 2 | 10 | 46.650 | 0.348 | 0.340 | 0.383 | 0.148 | 0.232 |
| ACWT | 1 | 5 | 96.000 | 0.945 | 0.897 | 1.000 | 0.580 | 0.643 |
| Adler | 1 | 5 | 65.500 | 0.922 | 0.865 | 1.000 | 0.447 | 0.507 |
| CMU | 1 | 5 | 88.300 | 0.742 | 0.662 | 0.883 | 0.337 | 0.467 |

## Leave-One-Corpus-Out Sensitivity

| n_patients | n_task_rows | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage | mean_coverage_gap_asr_minus_human | r_asr_coverage_wab | r_human_coverage_wab | mean_false_positive | mean_false_negative | excluded_corpus |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 28.000 | 145.000 | 0.758 | 0.712 | 0.851 | 0.428 | 0.514 | -0.086 | 0.808 | 0.878 | 0.161 | 1.214 | ACWT |
| 28.000 | 145.000 | 0.758 | 0.713 | 0.851 | 0.433 | 0.519 | -0.086 | 0.812 | 0.878 | 0.161 | 1.214 | Adler |
| 26.000 | 135.000 | 0.769 | 0.727 | 0.855 | 0.444 | 0.525 | -0.082 | 0.784 | 0.864 | 0.165 | 1.177 | BU |
| 28.000 | 145.000 | 0.765 | 0.720 | 0.855 | 0.437 | 0.521 | -0.084 | 0.830 | 0.891 | 0.146 | 1.171 | CMU |
| 16.000 | 80.000 | 0.765 | 0.718 | 0.865 | 0.434 | 0.535 | -0.101 | 0.829 | 0.902 | 0.125 | 1.375 | Kurland |
| 26.000 | 135.000 | 0.745 | 0.698 | 0.841 | 0.427 | 0.518 | -0.091 | 0.809 | 0.894 | 0.165 | 1.277 | MSU |
| 24.000 | 125.000 | 0.757 | 0.712 | 0.841 | 0.409 | 0.481 | -0.072 | 0.846 | 0.859 | 0.154 | 1.025 | NEURAL-2 |
| 27.000 | 140.000 | 0.795 | 0.746 | 0.891 | 0.455 | 0.540 | -0.086 | 0.782 | 0.859 | 0.152 | 1.200 | Richardson |

## Interpretation

This analysis treats participants as the uncertainty unit. The headline ASR content-state metrics should be read from the patient-level rows, not only from task rows, because repeated prompt tasks from the same speaker are not independent evidence.
