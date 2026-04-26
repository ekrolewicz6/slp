# No-Clinician Discovery Suite

## Longitudinal Change Subtypes

| change_subtype | n_pairs | n_roots | stable_wab_rate | mean_delta_wab | mean_delta_content | mean_delta_coverage | mean_delta_risk | mean_delta_recoverable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stable_or_unclassified | 216 | 129 | 0.981 | 0.062 | 0.064 | 0.010 | 0.010 | 0.055 |
| mixed_multiaxis_change | 38 | 33 | 1.000 | 0.179 | -0.039 | -0.008 | 0.022 | -2.720 |
| semantic_content_decline | 21 | 21 | 0.857 | -1.762 | -1.320 | -0.174 | -0.064 | 0.043 |
| semantic_content_gain | 21 | 20 | 0.810 | 1.233 | 1.254 | 0.173 | -0.360 | -0.719 |
| more_words_without_content_gain | 20 | 19 | 1.000 | 0.000 | 0.154 | 0.019 | -0.340 | -0.184 |
| intent_risk_worsening | 17 | 13 | 0.882 | -2.282 | 0.000 | 0.000 | 9.543 | -0.825 |
| longer_utterances_without_content_gain | 17 | 16 | 1.000 | 0.000 | 0.325 | 0.042 | 0.891 | 0.113 |
| intent_safety_gain_without_content_gain | 16 | 13 | 0.938 | -0.325 | -0.042 | -0.006 | -6.683 | 3.437 |
| wab_only_change | 12 | 10 | 0.000 | 2.450 | 0.034 | 0.011 | -0.096 | -0.153 |
| known_repair_opportunity_increase | 11 | 10 | 0.727 | 1.809 | -0.454 | -0.059 | -0.948 | 10.512 |
| concept_efficiency_gain | 7 | 6 | 0.571 | 1.714 | 0.846 | 0.136 | -0.037 | 0.550 |
| more_utterances_without_content_gain | 6 | 6 | 1.000 | 0.000 | 0.191 | 0.026 | -2.755 | -1.745 |
| content_gain_with_more_output | 3 | 3 | 0.000 | 10.700 | 1.777 | 0.227 | -1.142 | -0.184 |

Top subtype/change cells:

| from_meta_subtype | change_subtype | n_pairs |
| --- | --- | --- |
| Anomic | stable_or_unclassified | 77 |
| Anomic | mixed_multiaxis_change | 11 |
| Anomic | semantic_content_decline | 7 |
| Anomic | semantic_content_gain | 7 |
| Anomic | more_words_without_content_gain | 5 |
| Anomic | longer_utterances_without_content_gain | 4 |
| Anomic | wab_only_change | 4 |
| Anomic | concept_efficiency_gain | 3 |
| Anomic | known_repair_opportunity_increase | 1 |
| Broca | stable_or_unclassified | 61 |
| Broca | mixed_multiaxis_change | 17 |
| Broca | intent_safety_gain_without_content_gain | 10 |
| Broca | intent_risk_worsening | 9 |
| Broca | semantic_content_decline | 8 |
| Broca | semantic_content_gain | 8 |
| Broca | known_repair_opportunity_increase | 6 |
| Broca | wab_only_change | 6 |
| Broca | longer_utterances_without_content_gain | 5 |
| Broca | more_utterances_without_content_gain | 5 |
| Broca | more_words_without_content_gain | 3 |
| Broca | concept_efficiency_gain | 2 |
| Broca | content_gain_with_more_output | 2 |
| Conduction | stable_or_unclassified | 31 |
| Conduction | mixed_multiaxis_change | 7 |
| Conduction | more_words_without_content_gain | 5 |
| Conduction | known_repair_opportunity_increase | 3 |
| Conduction | longer_utterances_without_content_gain | 3 |
| Conduction | semantic_content_decline | 3 |
| Conduction | semantic_content_gain | 3 |
| Conduction | concept_efficiency_gain | 2 |

## Patient-Specific Concept Reliability

- Repeated root-item observations: 10,161
- Variable/changing root-items: 2,642

By task:

| task | n_root_items | variable_rate | gained_rate | lost_rate | mean_flip_rate |
| --- | --- | --- | --- | --- | --- |
| Window | 2256 | 0.277 | 0.112 | 0.093 | 0.200 |
| Cinderella | 2775 | 0.271 | 0.117 | 0.083 | 0.196 |
| Sandwich | 2172 | 0.254 | 0.096 | 0.088 | 0.174 |
| Cat | 1608 | 0.251 | 0.118 | 0.113 | 0.230 |
| Umbrella | 1350 | 0.228 | 0.118 | 0.091 | 0.209 |

Most change-sensitive concepts:

| task | concept | item_id | n_roots | mean_hit_rate | stable_present_rate | stable_absent_rate | gained_rate | lost_rate | variable_rate | mean_flip_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sandwich | sandwich | Sandwich:sandwich | 181 | 0.326 | 0.138 | 0.442 | 0.166 | 0.155 | 0.420 | 0.307 |
| Umbrella | wet | Umbrella:wet | 135 | 0.545 | 0.341 | 0.252 | 0.170 | 0.215 | 0.407 | 0.365 |
| Window | break | Window:break | 188 | 0.423 | 0.234 | 0.362 | 0.202 | 0.128 | 0.404 | 0.288 |
| Window | look | Window:look | 188 | 0.554 | 0.340 | 0.261 | 0.165 | 0.149 | 0.399 | 0.286 |
| Cinderella | chores | Cinderella:chores | 185 | 0.391 | 0.232 | 0.411 | 0.124 | 0.157 | 0.357 | 0.275 |
| Sandwich | together | Sandwich:together | 181 | 0.635 | 0.453 | 0.193 | 0.149 | 0.105 | 0.354 | 0.261 |
| Window | boy | Window:boy | 188 | 0.652 | 0.473 | 0.176 | 0.117 | 0.128 | 0.351 | 0.242 |
| Cat | climb | Cat:climb | 134 | 0.671 | 0.500 | 0.157 | 0.142 | 0.179 | 0.343 | 0.301 |
| Cinderella | loss | Cinderella:loss | 185 | 0.428 | 0.254 | 0.411 | 0.135 | 0.086 | 0.335 | 0.251 |
| Window | man | Window:man | 188 | 0.602 | 0.441 | 0.234 | 0.181 | 0.085 | 0.324 | 0.238 |
| Cinderella | marriage | Cinderella:marriage | 185 | 0.472 | 0.303 | 0.373 | 0.146 | 0.086 | 0.324 | 0.236 |
| Cat | chase | Cat:chase | 134 | 0.569 | 0.403 | 0.276 | 0.172 | 0.119 | 0.321 | 0.297 |
| Sandwich | eat | Sandwich:eat | 181 | 0.264 | 0.127 | 0.552 | 0.122 | 0.110 | 0.320 | 0.229 |
| Sandwich | put_on | Sandwich:put_on | 181 | 0.686 | 0.536 | 0.149 | 0.133 | 0.099 | 0.315 | 0.222 |
| Window | house | Window:house | 188 | 0.296 | 0.160 | 0.527 | 0.144 | 0.112 | 0.314 | 0.233 |
| Cinderella | dress | Cinderella:dress | 185 | 0.559 | 0.389 | 0.297 | 0.146 | 0.070 | 0.314 | 0.226 |
| Cat | stuck | Cat:stuck | 134 | 0.305 | 0.149 | 0.537 | 0.149 | 0.149 | 0.313 | 0.302 |
| Umbrella | take | Umbrella:take | 135 | 0.417 | 0.267 | 0.422 | 0.193 | 0.067 | 0.311 | 0.290 |
| Window | chair | Window:chair | 188 | 0.200 | 0.074 | 0.617 | 0.106 | 0.128 | 0.309 | 0.224 |
| Cinderella | ball | Cinderella:ball | 185 | 0.666 | 0.519 | 0.189 | 0.119 | 0.108 | 0.292 | 0.202 |
| Cinderella | midnight | Cinderella:midnight | 185 | 0.565 | 0.411 | 0.297 | 0.124 | 0.114 | 0.292 | 0.201 |
| Cat | firefighters | Cat:firefighters | 134 | 0.642 | 0.500 | 0.216 | 0.134 | 0.112 | 0.284 | 0.269 |
| Cinderella | castle | Cinderella:castle | 185 | 0.263 | 0.130 | 0.589 | 0.114 | 0.097 | 0.281 | 0.210 |
| Cinderella | fit | Cinderella:fit | 185 | 0.560 | 0.416 | 0.303 | 0.108 | 0.081 | 0.281 | 0.199 |
| Window | kick | Window:kick | 188 | 0.690 | 0.548 | 0.176 | 0.096 | 0.085 | 0.277 | 0.204 |

Therapy-target reliability overlay:

| target_reliability_bucket | n_targets | mean_zone_score | mean_pred_success | n_patients |
| --- | --- | --- | --- | --- |
| stable_absent | 3080 | 0.906 | 0.425 | 577 |
| not_repeated_or_unobserved | 2909 | 0.911 | 0.437 | 322 |
| variable_other | 776 | 0.900 | 0.455 | 301 |
| gained | 685 | 0.901 | 0.469 | 292 |
| lost | 601 | 0.906 | 0.466 | 287 |

## Boundary Analyses

Severe/Broca floor mechanisms:

| floor_mechanism | n | mean_wab | mean_content | mean_risk | mean_recoverable | pct_broca | mean_open_clarify_frac |
| --- | --- | --- | --- | --- | --- | --- | --- |
| low_output_or_motor_floor | 151 | 37.787 | 0.099 | 4.982 | 5.807 | 0.755 | 0.013 |
| unknown_intent_floor | 51 | 46.967 | 0.184 | 6.059 | 6.078 | 0.706 | 0.028 |
| mixed_floor | 24 | 43.579 | 0.195 | 0.951 | 1.413 | 0.542 | 0.023 |
| known_repairable_error_floor | 15 | 48.353 | 0.219 | 0.739 | 10.242 | 0.933 | 0.005 |
| low_content_low_error_floor | 12 | 49.633 | 0.202 | 0.067 | 0.525 | 0.750 | 0.005 |

Wernicke vs non-Wernicke overall:

| is_wernicke | n | mean_wab | mean_content | mean_risk | mean_recoverable | mean_unknown_intent_rate | mean_open_clarify_frac |
| --- | --- | --- | --- | --- | --- | --- | --- |
| False | 892 | 71.086 | 0.457 | 1.540 | 3.583 | 1.540 | 0.011 |
| True | 64 | 47.962 | 0.324 | 4.507 | 2.134 | 4.507 | 0.032 |

Wernicke vs same-WAB-bin non-Wernicke contrasts:

| wab_bin | metric | n_wernicke | n_non_wernicke | mean_wernicke | mean_non_wernicke | wernicke_minus_other | cohens_d |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mild | content_axis | 1 | 338 | 0.607 | 0.585 | 0.022 |  |
| moderate | content_axis | 26 | 298 | 0.513 | 0.378 | 0.135 | 0.843 |
| severe | content_axis | 37 | 141 | 0.183 | 0.108 | 0.075 | 0.671 |
| mild | recoverable_axis | 1 | 338 | 1.026 | 2.241 | -1.216 |  |
| moderate | recoverable_axis | 26 | 298 | 3.085 | 6.116 | -3.030 | -0.459 |
| severe | recoverable_axis | 37 | 141 | 1.495 | 3.899 | -2.404 | -0.433 |
| mild | risk_axis | 1 | 338 | 0.000 | 0.430 | -0.430 |  |
| moderate | risk_axis | 26 | 298 | 1.605 | 2.075 | -0.470 | -0.171 |
| severe | risk_axis | 37 | 141 | 6.668 | 4.289 | 2.379 | 0.391 |
| mild | unknown_intent_error_rate_100 | 1 | 338 | 0.000 | 0.430 | -0.430 |  |
| moderate | unknown_intent_error_rate_100 | 26 | 298 | 1.605 | 2.075 | -0.470 | -0.171 |
| severe | unknown_intent_error_rate_100 | 37 | 141 | 6.668 | 4.289 | 2.379 | 0.391 |

High-WAB state abnormalities:

| subtype | n | abnormal_rate | content_abnormal_rate | risk_abnormal_rate | recoverable_abnormal_rate | mean_content | mean_risk | mean_recoverable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NotAphasic | 114 | 0.000 | 0.000 | 0.000 | 0.000 | 0.712 | 0.051 | 0.667 |
|  | 6 | 0.000 | 0.000 | 0.000 | 0.000 | 0.708 | 0.082 | 0.251 |

High-WAB content vs control-norm proxy:

| subtype | n | below_control_5th_proxy_rate | mean_control_norm_content_z |
| --- | --- | --- | --- |
|  | 6 | 0.500 | -0.990 |
| NotAphasic | 112 | 0.214 | -0.704 |

## Synthesis

- The no-clinician data can already separate several clinically different change mechanisms: semantic content movement, output-quantity movement, intent-risk movement, and repair-opportunity movement.
- Concept targets are not all equivalent. Some are stable absences, while others are variable or gained/lost across repeated sessions; the latter are better candidates for change-sensitive targets and monitoring.
- WAB-AQ and subtype compress distinct states. Severe/Broca floor cases split into low-output, unknown-intent, repairable-error, and low-content/low-error profiles. Wernicke profiles show risk/recoverability patterns that are not captured by severity alone. High-WAB cases can still carry abnormal discourse-state signatures.