# Main Concept Rubric Experiment

- Rubric slots extracted: 229
- Rubric concepts extracted: 83
- Scored segments: 6879

## Extracted Rubrics

| task | n_concepts | n_slots | mean_terms_per_slot |
| --- | --- | --- | --- |
| Cat | 12 | 34 | 7.382 |
| Cinderella | 34 | 93 | 5.290 |
| Sandwich | 10 | 27 | 6.667 |
| Umbrella | 19 | 53 | 4.925 |
| Window | 8 | 22 | 5.773 |

## Segment Scores By Task

| task | n | mean_heuristic | mean_mca_complete | mean_mca_partial | r_heuristic_mca_partial |
| --- | --- | --- | --- | --- | --- |
| Cat | 1201 | 0.685 | 0.437 | 0.713 | 0.894 |
| Cinderella | 1494 | 0.562 | 0.398 | 0.642 | 0.924 |
| Sandwich | 1464 | 0.534 | 0.518 | 0.718 | 0.886 |
| Umbrella | 1186 | 0.694 | 0.261 | 0.566 | 0.901 |
| Window | 1534 | 0.491 | 0.348 | 0.609 | 0.892 |

## Raw Correlations With WAB-AQ

| feature | r_wab_aq |
| --- | --- |
| heuristic_observed_content | 0.742 |
| mca_complete_frac | 0.649 |
| mca_partial_frac | 0.736 |
| mca_slot_hit_frac | 0.734 |

## Patient-Grouped WAB Models

| setup | n | n_patients | mae | r | r_boot_lo | r_boot_hi |
| --- | --- | --- | --- | --- | --- | --- |
| mca_partial+error+task | 3879 | 851 | 9.873 | 0.799 | 0.777 | 0.818 |
| heuristic+mca_partial+task | 3879 | 851 | 10.329 | 0.786 | 0.763 | 0.808 |
| heuristic_content+task | 3879 | 851 | 10.591 | 0.776 | 0.752 | 0.798 |
| mca_partial+task | 3879 | 851 | 10.831 | 0.762 | 0.736 | 0.785 |
| mca_augmented_partial+task | 3879 | 851 | 11.103 | 0.752 | 0.727 | 0.775 |
| mca_complete+task | 3879 | 851 | 11.262 | 0.742 | 0.717 | 0.765 |

