# Streaming ASR Patient-Level Bootstrap Analysis

- Source: `outputs/streaming_asr_pilot_pwa60_tiny/asr_task_results.csv`
- Patients: 52
- Task rows: 233
- Utterance clips transcribed: 3681
- PAR audio transcribed: 255.57 min

## Patient-Level Bootstrap CIs

| metric | point | boot_mean | ci_low | ci_high |
| --- | --- | --- | --- | --- |
| mean_f1 | 0.716 | 0.716 | 0.640 | 0.788 |
| mean_recall | 0.680 | 0.680 | 0.604 | 0.751 |
| mean_precision | 0.792 | 0.792 | 0.712 | 0.868 |
| mean_asr_coverage | 0.321 | 0.322 | 0.264 | 0.383 |
| mean_human_coverage | 0.378 | 0.378 | 0.316 | 0.443 |
| coverage_gap_asr_minus_human | -0.057 | -0.057 | -0.074 | -0.042 |
| r_asr_coverage_wab | 0.881 | 0.881 | 0.823 | 0.923 |
| r_human_coverage_wab | 0.902 | 0.902 | 0.856 | 0.938 |
| mean_false_positive | 0.188 | 0.189 | 0.138 | 0.245 |
| mean_false_negative | 0.909 | 0.906 | 0.725 | 1.113 |

## By Task

| task | n_patients | n_task_rows | mean_wab | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Window | 52 | 52 | 62.546 | 0.704 | 0.670 | 0.776 | 0.292 | 0.337 |
| Cinderella | 51 | 51 | 63.386 | 0.658 | 0.619 | 0.743 | 0.271 | 0.337 |
| Sandwich | 50 | 50 | 64.048 | 0.753 | 0.699 | 0.851 | 0.300 | 0.373 |
| Cat | 40 | 40 | 69.892 | 0.812 | 0.768 | 0.884 | 0.429 | 0.500 |
| Umbrella | 40 | 40 | 69.892 | 0.813 | 0.794 | 0.855 | 0.490 | 0.520 |

## By Subtype

| subtype | n_patients | n_task_rows | mean_wab | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Broca | 22 | 87 | 46.609 | 0.552 | 0.528 | 0.619 | 0.156 | 0.202 |
| Anomic | 12 | 60 | 85.350 | 0.878 | 0.820 | 0.976 | 0.472 | 0.562 |
| NotAphasic | 8 | 40 | 96.625 | 0.938 | 0.901 | 0.989 | 0.633 | 0.692 |
| Wernicke | 7 | 31 | 35.690 | 0.679 | 0.639 | 0.760 | 0.197 | 0.224 |
| Conduction | 3 | 15 | 75.433 | 0.898 | 0.857 | 0.984 | 0.492 | 0.547 |

## By Corpus

| corpus | n_patients | n_task_rows | mean_wab | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fridriksson-2 | 12 | 36 | 38.058 | 0.531 | 0.516 | 0.616 | 0.114 | 0.169 |
| Kurland | 10 | 49 | 61.647 | 0.769 | 0.709 | 0.865 | 0.370 | 0.442 |
| Richardson | 7 | 34 | 75.950 | 0.686 | 0.643 | 0.763 | 0.396 | 0.470 |
| Tucson | 5 | 25 | 78.220 | 0.941 | 0.914 | 0.994 | 0.481 | 0.513 |
| Adler | 4 | 19 | 56.200 | 0.755 | 0.740 | 0.779 | 0.271 | 0.304 |
| MSU | 3 | 15 | 69.000 | 0.831 | 0.820 | 0.874 | 0.368 | 0.387 |
| Williamson | 3 | 15 | 67.333 | 0.592 | 0.515 | 0.717 | 0.276 | 0.357 |
| BU | 1 | 5 | 90.600 | 0.768 | 0.680 | 0.950 | 0.460 | 0.653 |
| Fridriksson | 1 | 5 | 57.500 | 0.920 | 0.875 | 1.000 | 0.273 | 0.307 |
| NEURAL-2 | 1 | 5 | 100.000 | 0.956 | 0.935 | 0.980 | 0.710 | 0.740 |
| TAP | 1 | 5 | 91.200 | 0.948 | 0.911 | 1.000 | 0.480 | 0.510 |
| Thompson | 1 | 5 | 88.900 | 0.931 | 0.911 | 0.960 | 0.650 | 0.663 |
| UNH | 1 | 5 | 50.800 | 0.333 | 0.300 | 0.400 | 0.073 | 0.153 |
| Whiteside | 1 | 5 | 84.000 | 0.978 | 0.960 | 1.000 | 0.517 | 0.533 |
| Wozniak | 1 | 5 | 84.500 | 0.855 | 0.773 | 0.975 | 0.477 | 0.577 |

## Leave-One-Corpus-Out Sensitivity

| n_patients | n_task_rows | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage | mean_coverage_gap_asr_minus_human | r_asr_coverage_wab | r_human_coverage_wab | mean_false_positive | mean_false_negative | excluded_corpus |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 48.000 | 214.000 | 0.715 | 0.677 | 0.795 | 0.327 | 0.386 | -0.059 | 0.873 | 0.896 | 0.200 | 0.950 | Adler |
| 51.000 | 228.000 | 0.715 | 0.680 | 0.789 | 0.319 | 0.373 | -0.054 | 0.881 | 0.900 | 0.188 | 0.875 | BU |
| 51.000 | 228.000 | 0.712 | 0.676 | 0.788 | 0.322 | 0.380 | -0.058 | 0.881 | 0.902 | 0.192 | 0.919 | Fridriksson |
| 40.000 | 197.000 | 0.771 | 0.729 | 0.844 | 0.384 | 0.441 | -0.058 | 0.851 | 0.886 | 0.161 | 0.881 | Fridriksson-2 |
| 42.000 | 184.000 | 0.706 | 0.676 | 0.777 | 0.311 | 0.365 | -0.054 | 0.907 | 0.924 | 0.179 | 0.865 | Kurland |
| 49.000 | 218.000 | 0.709 | 0.671 | 0.787 | 0.319 | 0.378 | -0.059 | 0.896 | 0.916 | 0.183 | 0.932 | MSU |
| 51.000 | 228.000 | 0.711 | 0.675 | 0.788 | 0.314 | 0.371 | -0.058 | 0.875 | 0.898 | 0.188 | 0.915 | NEURAL-2 |
| 45.000 | 199.000 | 0.723 | 0.688 | 0.798 | 0.311 | 0.366 | -0.055 | 0.870 | 0.892 | 0.186 | 0.879 | Richardson |
| 51.000 | 228.000 | 0.711 | 0.675 | 0.788 | 0.318 | 0.376 | -0.058 | 0.880 | 0.904 | 0.192 | 0.919 | TAP |
| 51.000 | 228.000 | 0.712 | 0.675 | 0.788 | 0.315 | 0.373 | -0.058 | 0.879 | 0.900 | 0.184 | 0.915 | Thompson |
| 47.000 | 208.000 | 0.692 | 0.655 | 0.770 | 0.304 | 0.364 | -0.060 | 0.883 | 0.904 | 0.204 | 0.954 | Tucson |
| 51.000 | 228.000 | 0.723 | 0.687 | 0.799 | 0.326 | 0.383 | -0.057 | 0.883 | 0.904 | 0.192 | 0.907 | UNH |
| 51.000 | 228.000 | 0.711 | 0.674 | 0.788 | 0.318 | 0.375 | -0.058 | 0.879 | 0.901 | 0.192 | 0.923 | Whiteside |
| 49.000 | 218.000 | 0.723 | 0.690 | 0.796 | 0.324 | 0.380 | -0.056 | 0.882 | 0.899 | 0.187 | 0.887 | Williamson |
| 51.000 | 228.000 | 0.713 | 0.678 | 0.788 | 0.318 | 0.375 | -0.056 | 0.879 | 0.901 | 0.188 | 0.899 | Wozniak |

## Interpretation

This analysis treats participants as the uncertainty unit. The headline ASR content-state metrics should be read from the patient-level rows, not only from task rows, because repeated prompt tasks from the same speaker are not independent evidence.
