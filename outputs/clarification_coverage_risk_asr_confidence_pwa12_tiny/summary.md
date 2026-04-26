# Clarification Coverage-Risk Curves

- Policy rows: 1060
- Items: 60

## Best Policies Overall

| gate | k | n_items | n_positive_items | n_offered | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | low_error_control_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | strategy | threshold | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oracle_any_target_gain | 5 | 60 | 13 | 13 | 0.217 | 0.769 | 0.769 | 0.750 | 0.000 | 0.000 | 0.000 | 1.300 | 5.417 | context_cooccurrence |  |  |
| oracle_any_target_gain | 5 | 60 | 13 | 13 | 0.217 | 0.769 | 0.769 | 0.750 | 0.000 | 0.000 | 0.000 | 1.300 | 5.417 | control_prior |  |  |
| oracle_any_target_gain | 5 | 60 | 13 | 13 | 0.217 | 0.769 | 0.769 | 0.750 | 0.000 | 0.000 | 0.000 | 1.300 | 5.417 | hybrid |  |  |
| missing_fraction_score>=0.250 | 5 | 60 | 13 | 52 | 0.867 | 0.192 | 0.769 | 0.750 | 0.769 | 0.933 | 0.000 | 5.200 | 21.667 | context_cooccurrence | 0.250 | missing_fraction_score |
| missing_fraction_score>=0.250 | 5 | 60 | 13 | 52 | 0.867 | 0.192 | 0.769 | 0.750 | 0.769 | 0.933 | 0.000 | 5.200 | 21.667 | control_prior | 0.250 | missing_fraction_score |
| missing_fraction_score>=0.250 | 5 | 60 | 13 | 52 | 0.867 | 0.192 | 0.769 | 0.750 | 0.769 | 0.933 | 0.000 | 5.200 | 21.667 | hybrid | 0.250 | missing_fraction_score |
| low_content_score>=-9.000 | 5 | 60 | 13 | 55 | 0.917 | 0.182 | 0.769 | 0.750 | 0.764 | 0.933 | 0.000 | 5.500 | 22.917 | context_cooccurrence | -9.000 | low_content_score |
| low_content_score>=-9.000 | 5 | 60 | 13 | 55 | 0.917 | 0.182 | 0.769 | 0.750 | 0.764 | 0.933 | 0.000 | 5.500 | 22.917 | control_prior | -9.000 | low_content_score |
| low_content_score>=-9.000 | 5 | 60 | 13 | 55 | 0.917 | 0.182 | 0.769 | 0.750 | 0.764 | 0.933 | 0.000 | 5.500 | 22.917 | hybrid | -9.000 | low_content_score |
| missing_fraction_score>=0.200 | 5 | 60 | 13 | 56 | 0.933 | 0.179 | 0.769 | 0.750 | 0.768 | 0.933 | 0.000 | 5.600 | 23.333 | context_cooccurrence | 0.200 | missing_fraction_score |
| missing_fraction_score>=0.200 | 5 | 60 | 13 | 56 | 0.933 | 0.179 | 0.769 | 0.750 | 0.768 | 0.933 | 0.000 | 5.600 | 23.333 | control_prior | 0.200 | missing_fraction_score |
| missing_fraction_score>=0.200 | 5 | 60 | 13 | 56 | 0.933 | 0.179 | 0.769 | 0.750 | 0.768 | 0.933 | 0.000 | 5.600 | 23.333 | hybrid | 0.200 | missing_fraction_score |
| content_gap_score>=-1.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | context_cooccurrence | -1.000 | content_gap_score |
| low_content_score>=-10.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | context_cooccurrence | -10.000 | low_content_score |
| missing_fraction_score>=0.167 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | context_cooccurrence | 0.167 | missing_fraction_score |
| content_gap_score>=-1.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | control_prior | -1.000 | content_gap_score |
| low_content_score>=-10.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | control_prior | -10.000 | low_content_score |
| missing_fraction_score>=0.167 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | control_prior | 0.167 | missing_fraction_score |
| content_gap_score>=-1.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | hybrid | -1.000 | content_gap_score |
| low_content_score>=-10.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | hybrid | -10.000 | low_content_score |

## Best Deployable Policies

| gate | k | n_items | n_positive_items | n_offered | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | low_error_control_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | strategy | threshold | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| missing_fraction_score>=0.250 | 5 | 60 | 13 | 52 | 0.867 | 0.192 | 0.769 | 0.750 | 0.769 | 0.933 | 0.000 | 5.200 | 21.667 | context_cooccurrence | 0.250 | missing_fraction_score |
| missing_fraction_score>=0.250 | 5 | 60 | 13 | 52 | 0.867 | 0.192 | 0.769 | 0.750 | 0.769 | 0.933 | 0.000 | 5.200 | 21.667 | control_prior | 0.250 | missing_fraction_score |
| missing_fraction_score>=0.250 | 5 | 60 | 13 | 52 | 0.867 | 0.192 | 0.769 | 0.750 | 0.769 | 0.933 | 0.000 | 5.200 | 21.667 | hybrid | 0.250 | missing_fraction_score |
| low_content_score>=-9.000 | 5 | 60 | 13 | 55 | 0.917 | 0.182 | 0.769 | 0.750 | 0.764 | 0.933 | 0.000 | 5.500 | 22.917 | context_cooccurrence | -9.000 | low_content_score |
| low_content_score>=-9.000 | 5 | 60 | 13 | 55 | 0.917 | 0.182 | 0.769 | 0.750 | 0.764 | 0.933 | 0.000 | 5.500 | 22.917 | control_prior | -9.000 | low_content_score |
| low_content_score>=-9.000 | 5 | 60 | 13 | 55 | 0.917 | 0.182 | 0.769 | 0.750 | 0.764 | 0.933 | 0.000 | 5.500 | 22.917 | hybrid | -9.000 | low_content_score |
| missing_fraction_score>=0.200 | 5 | 60 | 13 | 56 | 0.933 | 0.179 | 0.769 | 0.750 | 0.768 | 0.933 | 0.000 | 5.600 | 23.333 | context_cooccurrence | 0.200 | missing_fraction_score |
| missing_fraction_score>=0.200 | 5 | 60 | 13 | 56 | 0.933 | 0.179 | 0.769 | 0.750 | 0.768 | 0.933 | 0.000 | 5.600 | 23.333 | control_prior | 0.200 | missing_fraction_score |
| missing_fraction_score>=0.200 | 5 | 60 | 13 | 56 | 0.933 | 0.179 | 0.769 | 0.750 | 0.768 | 0.933 | 0.000 | 5.600 | 23.333 | hybrid | 0.200 | missing_fraction_score |
| content_gap_score>=-1.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | context_cooccurrence | -1.000 | content_gap_score |
| low_content_score>=-10.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | context_cooccurrence | -10.000 | low_content_score |
| missing_fraction_score>=0.167 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | context_cooccurrence | 0.167 | missing_fraction_score |
| content_gap_score>=-1.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | control_prior | -1.000 | content_gap_score |
| low_content_score>=-10.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | control_prior | -10.000 | low_content_score |
| missing_fraction_score>=0.167 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | control_prior | 0.167 | missing_fraction_score |
| content_gap_score>=-1.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | hybrid | -1.000 | content_gap_score |
| low_content_score>=-10.000 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | hybrid | -10.000 | low_content_score |
| missing_fraction_score>=0.167 | 5 | 60 | 13 | 59 | 0.983 | 0.169 | 0.769 | 0.750 | 0.780 | 1.000 | 0.000 | 5.900 | 24.583 | hybrid | 0.167 | missing_fraction_score |
| offer_all | 5 | 60 | 13 | 60 | 1.000 | 0.167 | 0.769 | 0.750 | 0.783 | 1.000 | 0.000 | 6.000 | 25.000 | context_cooccurrence |  |  |
| content_gap_score>=-2.000 | 5 | 60 | 13 | 60 | 1.000 | 0.167 | 0.769 | 0.750 | 0.783 | 1.000 | 0.000 | 6.000 | 25.000 | context_cooccurrence | -2.000 | content_gap_score |

## Deployable Frontier Under Risk Caps

| constraint | max_unnecessary | max_unknown_no_gain | status | gate | k | n_items | n_positive_items | n_offered | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | low_error_control_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | strategy | threshold | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 0.250 | 0.050 | no_policy_met_constraint |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| moderate | 0.400 | 0.100 | no_policy_met_constraint |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| liberal | 0.600 | 0.200 | ok | missing_fraction_score>=0.917 | 5.000 | 60.000 | 13.000 | 13.000 | 0.217 | 0.385 | 0.385 | 0.312 | 0.538 | 0.200 | 0.000 | 2.600 | 13.000 | context_cooccurrence | 0.917 | missing_fraction_score |

## Question Burden To Reach Target Recovery

| gate | k | n_items | n_positive_items | n_offered | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | unknown_no_gain_item_offer_rate | low_error_control_item_offer_rate | turns_per_useful_hit | options_per_target_recovered | strategy | threshold | score | policy_family | target_positive_item_recall | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| content_gap_score>=6.000 | 5.000 | 60.000 | 13.000 | 24.000 | 0.400 | 0.292 | 0.538 | 0.500 | 0.667 | 0.467 | 0.000 | 3.429 | 15.000 | context_cooccurrence | 6.000 | content_gap_score | deployable | 0.500 | ok |
| missing_fraction_score>=0.250 | 5.000 | 60.000 | 13.000 | 52.000 | 0.867 | 0.192 | 0.769 | 0.750 | 0.769 | 0.933 | 0.000 | 5.200 | 21.667 | context_cooccurrence | 0.250 | missing_fraction_score | deployable | 0.700 | ok |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | deployable | 0.800 | not_reached |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | deployable | 0.900 | not_reached |
| oracle_safe_known_gain | 5.000 | 60.000 | 13.000 | 10.000 | 0.167 | 0.800 | 0.615 | 0.562 | 0.000 | 0.000 | 0.000 | 1.250 | 5.556 | context_cooccurrence |  |  | oracle_upper | 0.500 | ok |
| oracle_any_target_gain | 5.000 | 60.000 | 13.000 | 13.000 | 0.217 | 0.769 | 0.769 | 0.750 | 0.000 | 0.000 | 0.000 | 1.300 | 5.417 | context_cooccurrence |  |  | oracle_upper | 0.700 | ok |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | oracle_upper | 0.800 | not_reached |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | oracle_upper | 0.900 | not_reached |

## Interpretation

The clinically relevant operating point is not the highest recall policy; it is the best recall available while keeping unnecessary clarification and unknown-intent offers below a tolerable burden. If no deployable policy survives strict caps, candidate generation is not the bottleneck; safe triggering and human confirmation are.
