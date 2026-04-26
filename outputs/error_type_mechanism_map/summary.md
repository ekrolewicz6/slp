# Error-Type Mechanism Map

- Session rows: 1080
- Longitudinal roots: 570

## Error Signals vs Outcomes

| signal | n | r |
| --- | --- | --- |
| unknown_intent_error_rate_100 | 952 | -0.509 |
| paper_bottleneck_error_rate_100 | 952 | -0.424 |
| error_rate_100 | 952 | -0.420 |
| error_neologism_rate_100 | 952 | -0.396 |
| error_semantic_rate_100 | 952 | -0.384 |
| target_annotation_rate_100 | 952 | -0.336 |
| known_reconstructable_error_rate_100 | 952 | -0.198 |
| error_phonological_rate_100 | 952 | -0.188 |
| error_morphological_rate_100 | 952 | 0.072 |
| error_dysfluency_rate_100 | 952 | 0.074 |

## WAB Models

| setup | n | n_roots | mae | r |
| --- | --- | --- | --- | --- |
| content+error+verbosity | 952 | 511 | 7.859 | 0.887 |
| content+error | 952 | 511 | 7.899 | 0.884 |
| content_only | 952 | 511 | 8.222 | 0.875 |
| error_only | 952 | 511 | 12.882 | 0.644 |

## Subtype Models

| setup | n | n_roots | accuracy | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- | --- |
| content+error | 818 | 422 | 0.623 | 0.479 | 0.477 |
| content_only | 818 | 422 | 0.627 | 0.479 | 0.475 |
| error_only | 818 | 422 | 0.524 | 0.401 | 0.389 |

## Subtype Error Profiles

| subtype | n | mean_wab_aq | mean_error_rate_100 | mean_error_phonological_rate_100 | mean_error_semantic_rate_100 | mean_error_neologism_rate_100 | mean_unknown_intent_error_rate_100 | mean_oracle_concept_gain_frac |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Global | 16 | 18.450 | 9.932 | 0.900 | 4.650 | 4.382 | 8.300 | 0.004 |
| Broca | 305 | 50.777 | 9.716 | 4.236 | 2.531 | 2.822 | 2.859 | 0.044 |
| Wernicke | 64 | 47.962 | 7.499 | 0.872 | 4.264 | 2.250 | 4.507 | 0.022 |
| Conduction | 156 | 68.849 | 5.434 | 1.728 | 2.091 | 1.394 | 1.561 | 0.044 |
| TransMotor | 23 | 73.118 | 5.266 | 2.091 | 1.884 | 1.107 | 1.229 | 0.025 |
| nan | 97 | 82.100 | 3.841 | 1.347 | 1.660 | 0.712 | 1.442 | 0.018 |
| White | 1 |  | 3.210 | 1.064 | 0.967 | 0.862 | 1.383 | 0.000 |
| Anomic | 293 | 85.778 | 2.642 | 1.070 | 0.987 | 0.422 | 0.421 | 0.017 |
| TransSensory | 2 | 60.250 | 2.521 | 0.332 | 1.594 | 0.595 | 1.438 | 0.008 |
| NotAphasic | 122 | 96.584 | 0.820 | 0.411 | 0.311 | 0.054 | 0.051 | 0.004 |
| Isolation | 1 | 32.300 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Longitudinal Error Change Correlations

| delta_signal | n | r_delta_wab | r_delta_core_content | r_delta_coverage |
| --- | --- | --- | --- | --- |
| delta_oracle_concept_gain_frac | 405 | 0.040 | -0.229 | -0.229 |
| delta_known_reconstructable_error_rate_100 | 405 | -0.008 | -0.092 | -0.087 |
| delta_error_rate_100 | 405 | -0.114 | -0.090 | -0.086 |
| delta_target_annotation_rate_100 | 405 | -0.076 | -0.090 | -0.085 |
| delta_paper_bottleneck_error_rate_100 | 405 | -0.112 | -0.087 | -0.083 |
| delta_error_phonological_rate_100 | 405 | -0.046 | -0.074 | -0.070 |
| delta_error_semantic_rate_100 | 405 | -0.073 | -0.065 | -0.065 |
| delta_error_morphological_rate_100 | 405 | -0.038 | -0.046 | -0.056 |
| delta_unknown_intent_error_rate_100 | 405 | -0.131 | -0.022 | -0.021 |
| delta_error_neologism_rate_100 | 405 | -0.085 | -0.003 | -0.001 |
| delta_error_dysfluency_rate_100 | 405 | -0.005 | 0.015 | 0.012 |
| delta_observed_concept_density | 405 | 0.083 | 0.171 | 0.166 |
| delta_observed_concept_token_ratio | 405 | 0.085 | 0.264 | 0.264 |
| delta_observed_concept_coverage_frac | 405 | 0.212 | 0.988 | 0.998 |
