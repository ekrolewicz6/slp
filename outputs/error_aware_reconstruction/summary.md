# Error-Aware Reconstruction Benchmark

- Segments: 7153
- WAB-labeled non-control segments: 4012
- Patient roots with WAB: 851
- Segments with any CHAT error tag: 3286
- Segments with positive oracle concept gain: 1065
- Mean oracle concept gain fraction: 0.017

## Error Rates By Subtype

| subtype | n_segments | n_patients | mean_wab_aq | mean_error_rate_100 | mean_unknown_intent_rate_100 | mean_oracle_gain_frac | pct_segments_with_gain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | 50 | 16 | 18.708 | 10.439 | 8.743 | 0.007 | 0.060 |
| Broca | 1161 | 280 | 51.904 | 9.233 | 2.775 | 0.043 | 0.356 |
| Wernicke | 274 | 60 | 49.830 | 6.834 | 3.998 | 0.023 | 0.234 |
| TransMotor | 108 | 23 | 72.345 | 5.471 | 1.315 | 0.025 | 0.194 |
| Conduction | 658 | 145 | 69.276 | 5.180 | 1.466 | 0.044 | 0.371 |
|  | 348 | 74 | 83.351 | 3.912 | 1.287 | 0.019 | 0.187 |
| White | 4 | 1 |  | 3.210 | 1.383 | 0.000 | 0.000 |
| Anomic | 1312 | 258 | 85.733 | 2.705 | 0.429 | 0.018 | 0.165 |
| TransSensory | 10 | 2 | 60.250 | 2.521 | 1.438 | 0.008 | 0.100 |
| NotAphasic | 612 | 115 | 96.539 | 0.812 | 0.050 | 0.004 | 0.049 |
| Isolation | 5 | 1 | 32.300 | 0.000 | 0.000 | 0.000 | 0.000 |

## Error Rates By Task

| task | n_segments | n_patients | mean_error_rate_100 | mean_paper_bottleneck_rate_100 | mean_oracle_gain_frac | pct_segments_with_gain |
| --- | --- | --- | --- | --- | --- | --- |
| Cookie | 1 | 1 | 6.000 | 6.000 | 0.100 | 1.000 |
| Cinderella | 1006 | 866 | 5.095 | 4.879 | 0.038 | 0.347 |
| Sandwich | 993 | 877 | 5.936 | 5.862 | 0.030 | 0.231 |
| Cat | 705 | 559 | 4.294 | 4.137 | 0.025 | 0.227 |
| Umbrella | 678 | 564 | 4.013 | 3.869 | 0.023 | 0.201 |
| Window | 1023 | 907 | 5.055 | 4.916 | 0.018 | 0.170 |
| Flood | 136 | 135 | 4.502 | 4.234 | 0.007 | 0.066 |

## Best WAB Models

| subset | setup | n | n_patients | mae | r | r_boot_lo | r_boot_hi |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_noncontrol_wab | target_augmented_content+error_profile+task | 4012 | 851 | 9.440 | 0.816 | 0.796 | 0.835 |
| all_noncontrol_wab | observed_content+error_profile+task | 4012 | 851 | 9.502 | 0.815 | 0.795 | 0.834 |
| all_noncontrol_wab | observed_content+task | 4012 | 851 | 10.387 | 0.782 | 0.758 | 0.803 |
| all_noncontrol_wab | target_augmented_content+task | 4012 | 851 | 10.720 | 0.771 | 0.747 | 0.790 |
| any_error_tag | target_augmented_content+error_profile+task | 2787 | 791 | 9.750 | 0.783 | 0.756 | 0.809 |
| any_error_tag | observed_content+error_profile+task | 2787 | 791 | 9.808 | 0.782 | 0.753 | 0.808 |
| any_error_tag | observed_content+task | 2787 | 791 | 10.583 | 0.748 | 0.715 | 0.777 |
| any_error_tag | target_augmented_content+task | 2787 | 791 | 10.688 | 0.745 | 0.715 | 0.771 |
| high_paper_bottleneck_error_rate_q75 | target_augmented_content+error_profile+task | 1006 | 403 | 9.817 | 0.756 | 0.715 | 0.790 |
| high_paper_bottleneck_error_rate_q75 | observed_content+error_profile+task | 1006 | 403 | 10.210 | 0.738 | 0.692 | 0.774 |
| high_paper_bottleneck_error_rate_q75 | target_augmented_content+task | 1006 | 403 | 10.207 | 0.732 | 0.684 | 0.771 |
| high_paper_bottleneck_error_rate_q75 | observed_content+task | 1006 | 403 | 10.980 | 0.687 | 0.632 | 0.732 |
| unknown_intent_error | target_augmented_content+error_profile+task | 1379 | 560 | 10.399 | 0.744 | 0.707 | 0.777 |
| unknown_intent_error | observed_content+error_profile+task | 1379 | 560 | 10.457 | 0.741 | 0.700 | 0.774 |
| unknown_intent_error | target_augmented_content+task | 1379 | 560 | 10.907 | 0.718 | 0.680 | 0.753 |
| unknown_intent_error | observed_content+task | 1379 | 560 | 11.136 | 0.709 | 0.665 | 0.745 |

## Signals Most Associated With Oracle Concept Gain

| signal | outcome | n | r |
| --- | --- | --- | --- |
| known_reconstructable_error_rate_100 | oracle_concept_gain_frac | 4542 | 0.575 |
| target_annotation_rate_100 | oracle_concept_gain_frac | 4542 | 0.540 |
| error_rate_100 | oracle_concept_gain_frac | 4542 | 0.471 |
| paper_bottleneck_error_rate_100 | oracle_concept_gain_frac | 4542 | 0.469 |
| error_phonological_rate_100 | oracle_concept_gain_frac | 4542 | 0.448 |
| error_neologism_rate_100 | oracle_concept_gain_frac | 4542 | 0.307 |
| error_semantic_rate_100 | oracle_concept_gain_frac | 4542 | 0.170 |
| unknown_intent_error_rate_100 | oracle_concept_gain_frac | 4542 | 0.098 |
| error_dysfluency_rate_100 | oracle_concept_gain_frac | 4542 | 0.063 |
| error_morphological_rate_100 | oracle_concept_gain_frac | 4542 | 0.041 |

## Interpretation

CHAT target annotations act as an oracle reconstruction layer. If target-augmented content substantially improves event-concept coverage or WAB prediction in high-error segments, LLM reconstruction is worth testing as an assistive layer. If it does not, stronger LLMs may still help communication, but they should not replace raw discourse measurement.
