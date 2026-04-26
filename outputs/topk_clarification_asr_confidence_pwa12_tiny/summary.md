# Top-k Clarification Benchmark

- Items: 60
- Input source: asr
- Strategies: context_cooccurrence, control_prior, hybrid, severity_near
- Positive target-gain items: 13

## Best Overall Policies

| strategy | policy | k | n_items | n_positive_items | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | low_error_control_offer_rate | unknown_no_gain_offer_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| context_cooccurrence | oracle_any_target_gain | 5 | 60 | 13 | 0.217 | 0.769 | 0.769 | 0.750 | 0.000 | 0.000 | 0.000 |
| control_prior | oracle_any_target_gain | 5 | 60 | 13 | 0.217 | 0.769 | 0.769 | 0.750 | 0.000 | 0.000 | 0.000 |
| hybrid | oracle_any_target_gain | 5 | 60 | 13 | 0.217 | 0.769 | 0.769 | 0.750 | 0.000 | 0.000 | 0.000 |
| context_cooccurrence | offer_all | 5 | 60 | 13 | 1.000 | 0.167 | 0.769 | 0.750 | 0.783 | 0.000 | 0.250 |
| control_prior | offer_all | 5 | 60 | 13 | 1.000 | 0.167 | 0.769 | 0.750 | 0.783 | 0.000 | 0.250 |
| hybrid | offer_all | 5 | 60 | 13 | 1.000 | 0.167 | 0.769 | 0.750 | 0.783 | 0.000 | 0.250 |
| context_cooccurrence | oracle_any_target_gain | 2 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.562 | 0.000 | 0.000 | 0.000 |
| context_cooccurrence | oracle_any_target_gain | 3 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.562 | 0.000 | 0.000 | 0.000 |
| context_cooccurrence | oracle_any_target_gain | 4 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.625 | 0.000 | 0.000 | 0.000 |
| control_prior | oracle_any_target_gain | 2 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.562 | 0.000 | 0.000 | 0.000 |
| control_prior | oracle_any_target_gain | 3 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.562 | 0.000 | 0.000 | 0.000 |
| control_prior | oracle_any_target_gain | 4 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.625 | 0.000 | 0.000 | 0.000 |
| hybrid | oracle_any_target_gain | 2 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.562 | 0.000 | 0.000 | 0.000 |
| hybrid | oracle_any_target_gain | 3 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.562 | 0.000 | 0.000 | 0.000 |
| hybrid | oracle_any_target_gain | 4 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.625 | 0.000 | 0.000 | 0.000 |
| context_cooccurrence | content_gap_gate | 5 | 60 | 13 | 0.883 | 0.170 | 0.692 | 0.688 | 0.774 | 0.000 | 0.233 |
| control_prior | content_gap_gate | 5 | 60 | 13 | 0.883 | 0.170 | 0.692 | 0.688 | 0.774 | 0.000 | 0.233 |
| hybrid | content_gap_gate | 5 | 60 | 13 | 0.883 | 0.170 | 0.692 | 0.688 | 0.774 | 0.000 | 0.233 |
| context_cooccurrence | offer_all | 2 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| context_cooccurrence | offer_all | 3 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |

## k=3 Comparison

| strategy | policy | k | n_items | n_positive_items | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | low_error_control_offer_rate | unknown_no_gain_offer_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| context_cooccurrence | oracle_any_target_gain | 3 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.562 | 0.000 | 0.000 | 0.000 |
| control_prior | oracle_any_target_gain | 3 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.562 | 0.000 | 0.000 | 0.000 |
| hybrid | oracle_any_target_gain | 3 | 60 | 13 | 0.217 | 0.692 | 0.692 | 0.562 | 0.000 | 0.000 | 0.000 |
| context_cooccurrence | offer_all | 3 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| control_prior | offer_all | 3 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| hybrid | offer_all | 3 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| context_cooccurrence | content_gap_gate | 3 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.500 | 0.774 | 0.000 | 0.233 |
| control_prior | content_gap_gate | 3 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.500 | 0.774 | 0.000 | 0.233 |
| hybrid | content_gap_gate | 3 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.500 | 0.774 | 0.000 | 0.233 |
| context_cooccurrence | oracle_safe_known_gain | 3 | 60 | 13 | 0.167 | 0.700 | 0.538 | 0.438 | 0.000 | 0.000 | 0.000 |
| control_prior | oracle_safe_known_gain | 3 | 60 | 13 | 0.167 | 0.700 | 0.538 | 0.438 | 0.000 | 0.000 | 0.000 |
| hybrid | oracle_safe_known_gain | 3 | 60 | 13 | 0.167 | 0.700 | 0.538 | 0.438 | 0.000 | 0.000 | 0.000 |
| severity_near | oracle_any_target_gain | 3 | 60 | 13 | 0.217 | 0.538 | 0.538 | 0.562 | 0.000 | 0.000 | 0.000 |
| context_cooccurrence | controller_not_preserve | 3 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.438 | 0.697 | 0.000 | 0.150 |
| control_prior | controller_not_preserve | 3 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.438 | 0.697 | 0.000 | 0.150 |
| hybrid | controller_not_preserve | 3 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.438 | 0.697 | 0.000 | 0.150 |
| severity_near | offer_all | 3 | 60 | 13 | 1.000 | 0.117 | 0.538 | 0.562 | 0.783 | 0.000 | 0.250 |
| severity_near | controller_not_preserve | 3 | 60 | 13 | 0.550 | 0.182 | 0.462 | 0.500 | 0.697 | 0.000 | 0.150 |
| severity_near | content_gap_gate | 3 | 60 | 13 | 0.883 | 0.113 | 0.462 | 0.500 | 0.774 | 0.000 | 0.233 |
| severity_near | oracle_safe_known_gain | 3 | 60 | 13 | 0.167 | 0.500 | 0.385 | 0.375 | 0.000 | 0.000 | 0.000 |
| context_cooccurrence | controller_clarify_only | 3 | 60 | 13 | 0.267 | 0.312 | 0.385 | 0.312 | 0.625 | 0.000 | 0.033 |
| control_prior | controller_clarify_only | 3 | 60 | 13 | 0.267 | 0.312 | 0.385 | 0.312 | 0.625 | 0.000 | 0.033 |
| hybrid | controller_clarify_only | 3 | 60 | 13 | 0.267 | 0.312 | 0.385 | 0.312 | 0.625 | 0.000 | 0.033 |
| severity_near | controller_clarify_only | 3 | 60 | 13 | 0.267 | 0.250 | 0.308 | 0.375 | 0.625 | 0.000 | 0.033 |

## Deployable/Non-oracle Policies

| strategy | policy | k | n_items | n_positive_items | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | low_error_control_offer_rate | unknown_no_gain_offer_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| context_cooccurrence | offer_all | 5 | 60 | 13 | 1.000 | 0.167 | 0.769 | 0.750 | 0.783 | 0.000 | 0.250 |
| control_prior | offer_all | 5 | 60 | 13 | 1.000 | 0.167 | 0.769 | 0.750 | 0.783 | 0.000 | 0.250 |
| hybrid | offer_all | 5 | 60 | 13 | 1.000 | 0.167 | 0.769 | 0.750 | 0.783 | 0.000 | 0.250 |
| context_cooccurrence | content_gap_gate | 5 | 60 | 13 | 0.883 | 0.170 | 0.692 | 0.688 | 0.774 | 0.000 | 0.233 |
| control_prior | content_gap_gate | 5 | 60 | 13 | 0.883 | 0.170 | 0.692 | 0.688 | 0.774 | 0.000 | 0.233 |
| hybrid | content_gap_gate | 5 | 60 | 13 | 0.883 | 0.170 | 0.692 | 0.688 | 0.774 | 0.000 | 0.233 |
| context_cooccurrence | offer_all | 2 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| context_cooccurrence | offer_all | 3 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| context_cooccurrence | offer_all | 4 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.625 | 0.783 | 0.000 | 0.250 |
| control_prior | offer_all | 2 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| control_prior | offer_all | 3 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| control_prior | offer_all | 4 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.625 | 0.783 | 0.000 | 0.250 |
| hybrid | offer_all | 2 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| hybrid | offer_all | 3 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.562 | 0.783 | 0.000 | 0.250 |
| hybrid | offer_all | 4 | 60 | 13 | 1.000 | 0.150 | 0.692 | 0.625 | 0.783 | 0.000 | 0.250 |
| context_cooccurrence | controller_not_preserve | 5 | 60 | 13 | 0.550 | 0.242 | 0.615 | 0.625 | 0.697 | 0.000 | 0.150 |
| control_prior | controller_not_preserve | 5 | 60 | 13 | 0.550 | 0.242 | 0.615 | 0.625 | 0.697 | 0.000 | 0.150 |
| hybrid | controller_not_preserve | 5 | 60 | 13 | 0.550 | 0.242 | 0.615 | 0.625 | 0.697 | 0.000 | 0.150 |
| context_cooccurrence | content_gap_gate | 2 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.500 | 0.774 | 0.000 | 0.233 |
| context_cooccurrence | content_gap_gate | 3 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.500 | 0.774 | 0.000 | 0.233 |
| context_cooccurrence | content_gap_gate | 4 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.562 | 0.774 | 0.000 | 0.233 |
| control_prior | content_gap_gate | 2 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.500 | 0.774 | 0.000 | 0.233 |
| control_prior | content_gap_gate | 3 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.500 | 0.774 | 0.000 | 0.233 |
| control_prior | content_gap_gate | 4 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.562 | 0.774 | 0.000 | 0.233 |
| hybrid | content_gap_gate | 2 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.500 | 0.774 | 0.000 | 0.233 |
| hybrid | content_gap_gate | 3 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.500 | 0.774 | 0.000 | 0.233 |
| hybrid | content_gap_gate | 4 | 60 | 13 | 0.883 | 0.151 | 0.615 | 0.562 | 0.774 | 0.000 | 0.233 |
| severity_near | offer_all | 4 | 60 | 13 | 1.000 | 0.133 | 0.615 | 0.625 | 0.783 | 0.000 | 0.250 |
| severity_near | offer_all | 5 | 60 | 13 | 1.000 | 0.133 | 0.615 | 0.625 | 0.783 | 0.000 | 0.250 |
| context_cooccurrence | controller_not_preserve | 2 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.438 | 0.697 | 0.000 | 0.150 |
| context_cooccurrence | controller_not_preserve | 3 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.438 | 0.697 | 0.000 | 0.150 |
| context_cooccurrence | controller_not_preserve | 4 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.500 | 0.697 | 0.000 | 0.150 |
| control_prior | controller_not_preserve | 2 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.438 | 0.697 | 0.000 | 0.150 |
| control_prior | controller_not_preserve | 3 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.438 | 0.697 | 0.000 | 0.150 |
| control_prior | controller_not_preserve | 4 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.500 | 0.697 | 0.000 | 0.150 |
| hybrid | controller_not_preserve | 2 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.438 | 0.697 | 0.000 | 0.150 |
| hybrid | controller_not_preserve | 3 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.438 | 0.697 | 0.000 | 0.150 |
| hybrid | controller_not_preserve | 4 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.500 | 0.697 | 0.000 | 0.150 |
| severity_near | controller_not_preserve | 4 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.562 | 0.697 | 0.000 | 0.150 |
| severity_near | controller_not_preserve | 5 | 60 | 13 | 0.550 | 0.212 | 0.538 | 0.562 | 0.697 | 0.000 | 0.150 |

## Interpretation

This is a clarification benchmark, not a rewriting benchmark. A high positive-item hit recall means the intended known target concept appears somewhere in a short candidate list. Useful-offer precision and the unknown/low-error offer rates quantify the clinical burden and safety cost. Oracle gates estimate the upper bound if we knew which rows had recoverable known targets; deployable gates show what current signals can do without CHAT target labels.
