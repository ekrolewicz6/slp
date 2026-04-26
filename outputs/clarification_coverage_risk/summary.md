# Clarification Coverage-Risk Curves

- Policy rows: 1300
- Items: 400

## Best Policies Overall

| gate | k | n_items | n_positive_items | n_offered | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | low_error_control_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | strategy | threshold | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oracle_any_target_gain | 5 | 400 | 165 | 165 | 0.412 | 0.964 | 0.964 | 0.860 | 0.000 | 0.000 | 0.062 | 1.038 | 3.198 | hybrid |  |  |
| missing_fraction_score>=0.167 | 5 | 400 | 165 | 372 | 0.930 | 0.427 | 0.964 | 0.860 | 0.556 | 0.912 | 0.788 | 2.340 | 7.209 | hybrid | 0.167 | missing_fraction_score |
| missing_fraction_score>=0.133 | 5 | 400 | 165 | 376 | 0.940 | 0.423 | 0.964 | 0.860 | 0.561 | 0.938 | 0.788 | 2.365 | 7.287 | hybrid | 0.133 | missing_fraction_score |
| content_gap_score>=0.000 | 5 | 400 | 165 | 379 | 0.948 | 0.420 | 0.964 | 0.860 | 0.565 | 0.938 | 0.825 | 2.384 | 7.345 | hybrid | 0.000 | content_gap_score |
| missing_fraction_score>=0.100 | 5 | 400 | 165 | 381 | 0.952 | 0.417 | 0.964 | 0.860 | 0.567 | 0.938 | 0.838 | 2.396 | 7.384 | hybrid | 0.100 | missing_fraction_score |
| low_content_score>=-12.000 | 5 | 400 | 165 | 383 | 0.958 | 0.415 | 0.964 | 0.860 | 0.569 | 0.912 | 0.912 | 2.409 | 7.422 | hybrid | -12.000 | low_content_score |
| low_content_score>=-13.000 | 5 | 400 | 165 | 387 | 0.968 | 0.411 | 0.964 | 0.860 | 0.574 | 0.938 | 0.912 | 2.434 | 7.500 | hybrid | -13.000 | low_content_score |
| missing_fraction_score>=0.083 | 5 | 400 | 165 | 387 | 0.968 | 0.411 | 0.964 | 0.860 | 0.574 | 0.938 | 0.912 | 2.434 | 7.500 | hybrid | 0.083 | missing_fraction_score |
| content_gap_score>=-1.000 | 5 | 400 | 165 | 389 | 0.972 | 0.409 | 0.964 | 0.860 | 0.576 | 0.975 | 0.900 | 2.447 | 7.539 | hybrid | -1.000 | content_gap_score |
| content_gap_score>=-2.000 | 5 | 400 | 165 | 390 | 0.975 | 0.408 | 0.964 | 0.860 | 0.577 | 0.975 | 0.912 | 2.453 | 7.558 | hybrid | -2.000 | content_gap_score |
| offer_all | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid |  |  |
| content_gap_score>=-3.000 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | -3.000 | content_gap_score |
| low_content_score>=-14.000 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | -14.000 | low_content_score |
| low_content_score>=-15.000 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | -15.000 | low_content_score |
| missing_fraction_score>=0.067 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | 0.067 | missing_fraction_score |
| missing_fraction_score>=0.000 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | 0.000 | missing_fraction_score |
| oracle_any_target_gain | 5 | 400 | 165 | 165 | 0.412 | 0.958 | 0.958 | 0.860 | 0.000 | 0.000 | 0.062 | 1.044 | 3.198 | context_cooccurrence |  |  |
| missing_fraction_score>=0.200 | 5 | 400 | 165 | 364 | 0.910 | 0.434 | 0.958 | 0.857 | 0.549 | 0.912 | 0.700 | 2.304 | 7.082 | hybrid | 0.200 | missing_fraction_score |
| missing_fraction_score>=0.167 | 5 | 400 | 165 | 372 | 0.930 | 0.425 | 0.958 | 0.860 | 0.556 | 0.912 | 0.788 | 2.354 | 7.209 | context_cooccurrence | 0.167 | missing_fraction_score |
| missing_fraction_score>=0.133 | 5 | 400 | 165 | 376 | 0.940 | 0.420 | 0.958 | 0.860 | 0.561 | 0.938 | 0.788 | 2.380 | 7.287 | context_cooccurrence | 0.133 | missing_fraction_score |

## Best Deployable Policies

| gate | k | n_items | n_positive_items | n_offered | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | low_error_control_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | strategy | threshold | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| missing_fraction_score>=0.167 | 5 | 400 | 165 | 372 | 0.930 | 0.427 | 0.964 | 0.860 | 0.556 | 0.912 | 0.788 | 2.340 | 7.209 | hybrid | 0.167 | missing_fraction_score |
| missing_fraction_score>=0.133 | 5 | 400 | 165 | 376 | 0.940 | 0.423 | 0.964 | 0.860 | 0.561 | 0.938 | 0.788 | 2.365 | 7.287 | hybrid | 0.133 | missing_fraction_score |
| content_gap_score>=0.000 | 5 | 400 | 165 | 379 | 0.948 | 0.420 | 0.964 | 0.860 | 0.565 | 0.938 | 0.825 | 2.384 | 7.345 | hybrid | 0.000 | content_gap_score |
| missing_fraction_score>=0.100 | 5 | 400 | 165 | 381 | 0.952 | 0.417 | 0.964 | 0.860 | 0.567 | 0.938 | 0.838 | 2.396 | 7.384 | hybrid | 0.100 | missing_fraction_score |
| low_content_score>=-12.000 | 5 | 400 | 165 | 383 | 0.958 | 0.415 | 0.964 | 0.860 | 0.569 | 0.912 | 0.912 | 2.409 | 7.422 | hybrid | -12.000 | low_content_score |
| low_content_score>=-13.000 | 5 | 400 | 165 | 387 | 0.968 | 0.411 | 0.964 | 0.860 | 0.574 | 0.938 | 0.912 | 2.434 | 7.500 | hybrid | -13.000 | low_content_score |
| missing_fraction_score>=0.083 | 5 | 400 | 165 | 387 | 0.968 | 0.411 | 0.964 | 0.860 | 0.574 | 0.938 | 0.912 | 2.434 | 7.500 | hybrid | 0.083 | missing_fraction_score |
| content_gap_score>=-1.000 | 5 | 400 | 165 | 389 | 0.972 | 0.409 | 0.964 | 0.860 | 0.576 | 0.975 | 0.900 | 2.447 | 7.539 | hybrid | -1.000 | content_gap_score |
| content_gap_score>=-2.000 | 5 | 400 | 165 | 390 | 0.975 | 0.408 | 0.964 | 0.860 | 0.577 | 0.975 | 0.912 | 2.453 | 7.558 | hybrid | -2.000 | content_gap_score |
| offer_all | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid |  |  |
| content_gap_score>=-3.000 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | -3.000 | content_gap_score |
| low_content_score>=-14.000 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | -14.000 | low_content_score |
| low_content_score>=-15.000 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | -15.000 | low_content_score |
| missing_fraction_score>=0.067 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | 0.067 | missing_fraction_score |
| missing_fraction_score>=0.000 | 5 | 400 | 165 | 391 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.975 | 0.925 | 2.459 | 7.578 | hybrid | 0.000 | missing_fraction_score |
| missing_fraction_score>=0.200 | 5 | 400 | 165 | 364 | 0.910 | 0.434 | 0.958 | 0.857 | 0.549 | 0.912 | 0.700 | 2.304 | 7.082 | hybrid | 0.200 | missing_fraction_score |
| missing_fraction_score>=0.167 | 5 | 400 | 165 | 372 | 0.930 | 0.425 | 0.958 | 0.860 | 0.556 | 0.912 | 0.788 | 2.354 | 7.209 | context_cooccurrence | 0.167 | missing_fraction_score |
| missing_fraction_score>=0.133 | 5 | 400 | 165 | 376 | 0.940 | 0.420 | 0.958 | 0.860 | 0.561 | 0.938 | 0.788 | 2.380 | 7.287 | context_cooccurrence | 0.133 | missing_fraction_score |
| content_gap_score>=0.000 | 5 | 400 | 165 | 379 | 0.948 | 0.417 | 0.958 | 0.860 | 0.565 | 0.938 | 0.825 | 2.399 | 7.345 | context_cooccurrence | 0.000 | content_gap_score |
| missing_fraction_score>=0.100 | 5 | 400 | 165 | 381 | 0.952 | 0.415 | 0.958 | 0.860 | 0.567 | 0.938 | 0.838 | 2.411 | 7.384 | context_cooccurrence | 0.100 | missing_fraction_score |

## Deployable Frontier Under Risk Caps

| constraint | max_unnecessary | max_unknown_no_gain | status | gate | k | n_items | n_positive_items | n_offered | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | low_error_control_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | strategy | threshold | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 0.250 | 0.050 | no_policy_met_constraint |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| moderate | 0.400 | 0.100 | no_policy_met_constraint |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| liberal | 0.600 | 0.200 | ok | content_gap_score>=11.000 | 5.000 | 400.000 | 165.000 | 39.000 | 0.098 | 0.462 | 0.109 | 0.087 | 0.436 | 0.188 | 0.000 | 2.167 | 7.500 | hybrid | 11.000 | content_gap_score |

## Question Burden To Reach Target Recovery

| gate | k | n_items | n_positive_items | n_offered | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | low_error_control_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | strategy | threshold | score | policy_family | target_positive_item_recall | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| content_gap_score>=5.000 | 5 | 400 | 165 | 168 | 0.420 | 0.530 | 0.539 | 0.550 | 0.435 | 0.525 | 0.000 | 1.888 | 5.091 | hybrid | 5.000 | content_gap_score | deployable | 0.500 | ok |
| content_gap_score>=3.000 | 5 | 400 | 165 | 258 | 0.645 | 0.523 | 0.818 | 0.767 | 0.453 | 0.675 | 0.162 | 1.911 | 5.609 | hybrid | 3.000 | content_gap_score | deployable | 0.700 | ok |
| content_gap_score>=3.000 | 5 | 400 | 165 | 258 | 0.645 | 0.523 | 0.818 | 0.767 | 0.453 | 0.675 | 0.162 | 1.911 | 5.609 | hybrid | 3.000 | content_gap_score | deployable | 0.800 | ok |
| content_gap_score>=2.000 | 5 | 400 | 165 | 312 | 0.780 | 0.481 | 0.909 | 0.830 | 0.500 | 0.800 | 0.388 | 2.080 | 6.265 | hybrid | 2.000 | content_gap_score | deployable | 0.900 | ok |
| oracle_safe_known_gain | 5 | 400 | 165 | 85 | 0.212 | 0.988 | 0.509 | 0.390 | 0.000 | 0.000 | 0.062 | 1.012 | 3.632 | hybrid |  |  | oracle_upper | 0.500 | ok |
| oracle_any_target_gain | 5 | 400 | 165 | 165 | 0.412 | 0.964 | 0.964 | 0.860 | 0.000 | 0.000 | 0.062 | 1.038 | 3.198 | hybrid |  |  | oracle_upper | 0.700 | ok |
| oracle_any_target_gain | 5 | 400 | 165 | 165 | 0.412 | 0.964 | 0.964 | 0.860 | 0.000 | 0.000 | 0.062 | 1.038 | 3.198 | hybrid |  |  | oracle_upper | 0.800 | ok |
| oracle_any_target_gain | 5 | 400 | 165 | 165 | 0.412 | 0.964 | 0.964 | 0.860 | 0.000 | 0.000 | 0.062 | 1.038 | 3.198 | hybrid |  |  | oracle_upper | 0.900 | ok |

## Interpretation

The clinically relevant operating point is not the highest recall policy; it is the best recall available while keeping unnecessary clarification and unknown-intent offers below a tolerable burden. If no deployable policy survives strict caps, candidate generation is not the bottleneck; safe triggering and human confirmation are.
