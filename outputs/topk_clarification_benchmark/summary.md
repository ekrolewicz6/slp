# Top-k Clarification Benchmark

- Items: 400
- Input source: raw
- Strategies: context_cooccurrence, control_prior, hybrid, severity_near
- Positive target-gain items: 165

## Best Overall Policies

| strategy | policy | k | n_items | n_positive_items | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | low_error_control_offer_rate | unknown_no_gain_offer_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid | oracle_any_target_gain | 5 | 400 | 165 | 0.412 | 0.964 | 0.964 | 0.860 | 0.000 | 0.012 | 0.000 |
| hybrid | offer_all | 5 | 400 | 165 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.185 | 0.195 |
| context_cooccurrence | oracle_any_target_gain | 5 | 400 | 165 | 0.412 | 0.958 | 0.958 | 0.860 | 0.000 | 0.012 | 0.000 |
| context_cooccurrence | offer_all | 5 | 400 | 165 | 0.978 | 0.404 | 0.958 | 0.860 | 0.578 | 0.185 | 0.195 |
| control_prior | oracle_any_target_gain | 5 | 400 | 165 | 0.412 | 0.952 | 0.952 | 0.850 | 0.000 | 0.012 | 0.000 |
| hybrid | content_gap_gate | 5 | 400 | 165 | 0.890 | 0.441 | 0.952 | 0.853 | 0.542 | 0.128 | 0.180 |
| control_prior | offer_all | 5 | 400 | 165 | 0.978 | 0.402 | 0.952 | 0.850 | 0.578 | 0.185 | 0.195 |
| context_cooccurrence | oracle_any_target_gain | 4 | 400 | 165 | 0.412 | 0.945 | 0.945 | 0.797 | 0.000 | 0.012 | 0.000 |
| hybrid | oracle_any_target_gain | 4 | 400 | 165 | 0.412 | 0.945 | 0.945 | 0.787 | 0.000 | 0.012 | 0.000 |
| context_cooccurrence | content_gap_gate | 5 | 400 | 165 | 0.890 | 0.438 | 0.945 | 0.853 | 0.542 | 0.128 | 0.180 |
| context_cooccurrence | offer_all | 4 | 400 | 165 | 0.978 | 0.399 | 0.945 | 0.797 | 0.578 | 0.185 | 0.195 |
| hybrid | offer_all | 4 | 400 | 165 | 0.978 | 0.399 | 0.945 | 0.787 | 0.578 | 0.185 | 0.195 |
| control_prior | content_gap_gate | 5 | 400 | 165 | 0.890 | 0.435 | 0.939 | 0.843 | 0.542 | 0.128 | 0.180 |
| control_prior | oracle_any_target_gain | 4 | 400 | 165 | 0.412 | 0.933 | 0.933 | 0.773 | 0.000 | 0.012 | 0.000 |
| context_cooccurrence | content_gap_gate | 4 | 400 | 165 | 0.890 | 0.433 | 0.933 | 0.790 | 0.542 | 0.128 | 0.180 |
| hybrid | content_gap_gate | 4 | 400 | 165 | 0.890 | 0.433 | 0.933 | 0.780 | 0.542 | 0.128 | 0.180 |
| control_prior | offer_all | 4 | 400 | 165 | 0.978 | 0.394 | 0.933 | 0.773 | 0.578 | 0.185 | 0.195 |
| control_prior | content_gap_gate | 4 | 400 | 165 | 0.890 | 0.427 | 0.921 | 0.767 | 0.542 | 0.128 | 0.180 |
| context_cooccurrence | oracle_any_target_gain | 3 | 400 | 165 | 0.412 | 0.903 | 0.903 | 0.693 | 0.000 | 0.012 | 0.000 |
| control_prior | oracle_any_target_gain | 3 | 400 | 165 | 0.412 | 0.903 | 0.903 | 0.680 | 0.000 | 0.012 | 0.000 |

## k=3 Comparison

| strategy | policy | k | n_items | n_positive_items | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | low_error_control_offer_rate | unknown_no_gain_offer_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| context_cooccurrence | oracle_any_target_gain | 3 | 400 | 165 | 0.412 | 0.903 | 0.903 | 0.693 | 0.000 | 0.012 | 0.000 |
| control_prior | oracle_any_target_gain | 3 | 400 | 165 | 0.412 | 0.903 | 0.903 | 0.680 | 0.000 | 0.012 | 0.000 |
| context_cooccurrence | offer_all | 3 | 400 | 165 | 0.978 | 0.381 | 0.903 | 0.693 | 0.578 | 0.185 | 0.195 |
| control_prior | offer_all | 3 | 400 | 165 | 0.978 | 0.381 | 0.903 | 0.680 | 0.578 | 0.185 | 0.195 |
| hybrid | oracle_any_target_gain | 3 | 400 | 165 | 0.412 | 0.897 | 0.897 | 0.693 | 0.000 | 0.012 | 0.000 |
| hybrid | offer_all | 3 | 400 | 165 | 0.978 | 0.379 | 0.897 | 0.693 | 0.578 | 0.185 | 0.195 |
| context_cooccurrence | content_gap_gate | 3 | 400 | 165 | 0.890 | 0.413 | 0.891 | 0.687 | 0.542 | 0.128 | 0.180 |
| control_prior | content_gap_gate | 3 | 400 | 165 | 0.890 | 0.413 | 0.891 | 0.673 | 0.542 | 0.128 | 0.180 |
| hybrid | content_gap_gate | 3 | 400 | 165 | 0.890 | 0.410 | 0.885 | 0.687 | 0.542 | 0.128 | 0.180 |
| severity_near | oracle_any_target_gain | 3 | 400 | 165 | 0.412 | 0.697 | 0.697 | 0.487 | 0.000 | 0.012 | 0.000 |
| severity_near | offer_all | 3 | 400 | 165 | 0.978 | 0.294 | 0.697 | 0.487 | 0.578 | 0.185 | 0.195 |
| severity_near | content_gap_gate | 3 | 400 | 165 | 0.890 | 0.317 | 0.685 | 0.480 | 0.542 | 0.128 | 0.180 |
| context_cooccurrence | oracle_safe_known_gain | 3 | 400 | 165 | 0.212 | 0.929 | 0.479 | 0.323 | 0.000 | 0.012 | 0.000 |
| control_prior | oracle_safe_known_gain | 3 | 400 | 165 | 0.212 | 0.929 | 0.479 | 0.317 | 0.000 | 0.012 | 0.000 |
| hybrid | oracle_safe_known_gain | 3 | 400 | 165 | 0.212 | 0.929 | 0.479 | 0.327 | 0.000 | 0.012 | 0.000 |
| severity_near | oracle_safe_known_gain | 3 | 400 | 165 | 0.212 | 0.729 | 0.376 | 0.257 | 0.000 | 0.012 | 0.000 |
| context_cooccurrence | controller_not_preserve | 3 | 400 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| context_cooccurrence | controller_clarify_only | 3 | 400 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| control_prior | controller_not_preserve | 3 | 400 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| control_prior | controller_clarify_only | 3 | 400 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| hybrid | controller_not_preserve | 3 | 400 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| hybrid | controller_clarify_only | 3 | 400 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| severity_near | controller_not_preserve | 3 | 400 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| severity_near | controller_clarify_only | 3 | 400 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Deployable/Non-oracle Policies

| strategy | policy | k | n_items | n_positive_items | offer_rate | useful_offer_precision | positive_item_hit_recall | target_concept_recall | unnecessary_offer_rate | low_error_control_offer_rate | unknown_no_gain_offer_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid | offer_all | 5 | 400 | 165 | 0.978 | 0.407 | 0.964 | 0.860 | 0.578 | 0.185 | 0.195 |
| context_cooccurrence | offer_all | 5 | 400 | 165 | 0.978 | 0.404 | 0.958 | 0.860 | 0.578 | 0.185 | 0.195 |
| hybrid | content_gap_gate | 5 | 400 | 165 | 0.890 | 0.441 | 0.952 | 0.853 | 0.542 | 0.128 | 0.180 |
| control_prior | offer_all | 5 | 400 | 165 | 0.978 | 0.402 | 0.952 | 0.850 | 0.578 | 0.185 | 0.195 |
| context_cooccurrence | content_gap_gate | 5 | 400 | 165 | 0.890 | 0.438 | 0.945 | 0.853 | 0.542 | 0.128 | 0.180 |
| context_cooccurrence | offer_all | 4 | 400 | 165 | 0.978 | 0.399 | 0.945 | 0.797 | 0.578 | 0.185 | 0.195 |
| hybrid | offer_all | 4 | 400 | 165 | 0.978 | 0.399 | 0.945 | 0.787 | 0.578 | 0.185 | 0.195 |
| control_prior | content_gap_gate | 5 | 400 | 165 | 0.890 | 0.435 | 0.939 | 0.843 | 0.542 | 0.128 | 0.180 |
| context_cooccurrence | content_gap_gate | 4 | 400 | 165 | 0.890 | 0.433 | 0.933 | 0.790 | 0.542 | 0.128 | 0.180 |
| hybrid | content_gap_gate | 4 | 400 | 165 | 0.890 | 0.433 | 0.933 | 0.780 | 0.542 | 0.128 | 0.180 |
| control_prior | offer_all | 4 | 400 | 165 | 0.978 | 0.394 | 0.933 | 0.773 | 0.578 | 0.185 | 0.195 |
| control_prior | content_gap_gate | 4 | 400 | 165 | 0.890 | 0.427 | 0.921 | 0.767 | 0.542 | 0.128 | 0.180 |
| context_cooccurrence | offer_all | 3 | 400 | 165 | 0.978 | 0.381 | 0.903 | 0.693 | 0.578 | 0.185 | 0.195 |
| control_prior | offer_all | 3 | 400 | 165 | 0.978 | 0.381 | 0.903 | 0.680 | 0.578 | 0.185 | 0.195 |
| hybrid | offer_all | 3 | 400 | 165 | 0.978 | 0.379 | 0.897 | 0.693 | 0.578 | 0.185 | 0.195 |
| severity_near | offer_all | 5 | 400 | 165 | 0.978 | 0.379 | 0.897 | 0.737 | 0.578 | 0.185 | 0.195 |
| context_cooccurrence | content_gap_gate | 3 | 400 | 165 | 0.890 | 0.413 | 0.891 | 0.687 | 0.542 | 0.128 | 0.180 |
| control_prior | content_gap_gate | 3 | 400 | 165 | 0.890 | 0.413 | 0.891 | 0.673 | 0.542 | 0.128 | 0.180 |
| hybrid | content_gap_gate | 3 | 400 | 165 | 0.890 | 0.410 | 0.885 | 0.687 | 0.542 | 0.128 | 0.180 |
| severity_near | content_gap_gate | 5 | 400 | 165 | 0.890 | 0.410 | 0.885 | 0.730 | 0.542 | 0.128 | 0.180 |
| context_cooccurrence | offer_all | 2 | 400 | 165 | 0.978 | 0.350 | 0.830 | 0.570 | 0.578 | 0.185 | 0.195 |
| context_cooccurrence | content_gap_gate | 2 | 400 | 165 | 0.890 | 0.379 | 0.818 | 0.563 | 0.542 | 0.128 | 0.180 |
| severity_near | offer_all | 4 | 400 | 165 | 0.978 | 0.340 | 0.806 | 0.607 | 0.578 | 0.185 | 0.195 |
| severity_near | content_gap_gate | 4 | 400 | 165 | 0.890 | 0.368 | 0.794 | 0.600 | 0.542 | 0.128 | 0.180 |
| hybrid | offer_all | 2 | 400 | 165 | 0.978 | 0.332 | 0.788 | 0.543 | 0.578 | 0.185 | 0.195 |
| hybrid | content_gap_gate | 2 | 400 | 165 | 0.890 | 0.360 | 0.776 | 0.537 | 0.542 | 0.128 | 0.180 |
| control_prior | offer_all | 2 | 400 | 165 | 0.978 | 0.309 | 0.733 | 0.503 | 0.578 | 0.185 | 0.195 |
| control_prior | content_gap_gate | 2 | 400 | 165 | 0.890 | 0.334 | 0.721 | 0.497 | 0.542 | 0.128 | 0.180 |
| severity_near | offer_all | 3 | 400 | 165 | 0.978 | 0.294 | 0.697 | 0.487 | 0.578 | 0.185 | 0.195 |
| severity_near | content_gap_gate | 3 | 400 | 165 | 0.890 | 0.317 | 0.685 | 0.480 | 0.542 | 0.128 | 0.180 |
| context_cooccurrence | offer_all | 1 | 400 | 165 | 0.978 | 0.271 | 0.642 | 0.353 | 0.578 | 0.185 | 0.195 |
| context_cooccurrence | content_gap_gate | 1 | 400 | 165 | 0.890 | 0.292 | 0.630 | 0.347 | 0.542 | 0.128 | 0.180 |
| hybrid | offer_all | 1 | 400 | 165 | 0.978 | 0.256 | 0.606 | 0.333 | 0.578 | 0.185 | 0.195 |
| control_prior | offer_all | 1 | 400 | 165 | 0.978 | 0.253 | 0.600 | 0.330 | 0.578 | 0.185 | 0.195 |
| hybrid | content_gap_gate | 1 | 400 | 165 | 0.890 | 0.275 | 0.594 | 0.327 | 0.542 | 0.128 | 0.180 |
| control_prior | content_gap_gate | 1 | 400 | 165 | 0.890 | 0.272 | 0.588 | 0.323 | 0.542 | 0.128 | 0.180 |
| severity_near | offer_all | 2 | 400 | 165 | 0.978 | 0.223 | 0.527 | 0.330 | 0.578 | 0.185 | 0.195 |
| severity_near | content_gap_gate | 2 | 400 | 165 | 0.890 | 0.239 | 0.515 | 0.323 | 0.542 | 0.128 | 0.180 |
| severity_near | offer_all | 1 | 400 | 165 | 0.978 | 0.120 | 0.285 | 0.157 | 0.578 | 0.185 | 0.195 |
| severity_near | content_gap_gate | 1 | 400 | 165 | 0.890 | 0.129 | 0.279 | 0.153 | 0.542 | 0.128 | 0.180 |

## Interpretation

This is a clarification benchmark, not a rewriting benchmark. A high positive-item hit recall means the intended known target concept appears somewhere in a short candidate list. Useful-offer precision and the unknown/low-error offer rates quantify the clinical burden and safety cost. Oracle gates estimate the upper bound if we knew which rows had recoverable known targets; deployable gates show what current signals can do without CHAT target labels.
