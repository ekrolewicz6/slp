# Treatment Target Sequencing Summary

- Item observations: 47114
- Participants: 907
- Items/concepts: 61

## Item-Hit Prediction Models

| setup | n | positive_rate | auc | average_precision | brier | log_loss | accuracy_at_0.5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ability+item+subtype | 47114 | 0.473 | 0.856 | 0.841 | 0.155 | 0.473 | 0.775 |
| ability+item | 47114 | 0.473 | 0.855 | 0.838 | 0.155 | 0.475 | 0.774 |
| wab+item | 47114 | 0.473 | 0.845 | 0.830 | 0.161 | 0.489 | 0.766 |
| item_popularity | 47114 | 0.473 | 0.756 | 0.707 | 0.200 | 0.584 | 0.690 |
| ability+task | 47114 | 0.473 | 0.737 | 0.688 | 0.207 | 0.599 | 0.674 |
| ability_only | 47114 | 0.473 | 0.727 | 0.668 | 0.210 | 0.607 | 0.667 |

## Hardest And Easiest Items

| item_id | n | hit_rate | mean_pred | mean_ability_hit | mean_ability_miss |
| --- | --- | --- | --- | --- | --- |
| Sandwich:plate | 877 | 0.059 | 0.071 | -0.597 | -2.362 |
| Window:run_away | 906 | 0.065 | 0.076 | -1.638 | -2.402 |
| Cinderella:magic | 870 | 0.078 | 0.089 | -0.652 | -2.091 |
| Window:angry | 906 | 0.106 | 0.119 | -1.752 | -2.423 |
| Window:inside | 906 | 0.141 | 0.157 | -1.098 | -2.558 |
| Sandwich:cut | 877 | 0.169 | 0.185 | -1.113 | -2.489 |
| Sandwich:spread | 877 | 0.174 | 0.191 | -1.001 | -2.522 |
| Window:chair | 906 | 0.177 | 0.193 | -1.097 | -2.621 |
| Umbrella:lesson | 578 | 0.202 | 0.222 | -1.381 | -2.143 |
| Sandwich:knife | 877 | 0.210 | 0.228 | -1.106 | -2.563 |
| Sandwich:jelly | 877 | 0.726 | 0.739 | -1.718 | -3.687 |
| Sandwich:peanut | 877 | 0.726 | 0.739 | -1.685 | -3.776 |
| Cat:father | 574 | 0.733 | 0.747 | -1.614 | -3.352 |
| Umbrella:refusal | 578 | 0.749 | 0.765 | -1.777 | -2.621 |
| Cat:dog | 574 | 0.753 | 0.765 | -1.686 | -3.266 |
| Sandwich:bread | 877 | 0.772 | 0.782 | -1.763 | -3.930 |
| Sandwich:butter | 877 | 0.805 | 0.814 | -1.857 | -3.907 |
| Umbrella:rain | 578 | 0.813 | 0.822 | -1.587 | -3.740 |
| Window:soccer_ball | 906 | 0.837 | 0.843 | -1.910 | -4.615 |
| Cat:cat | 574 | 0.862 | 0.864 | -1.715 | -4.348 |

## Calibration For Ability + Item Model

| bin | n | mean_pred | observed_hit_rate |
| --- | --- | --- | --- |
| (-0.001, 0.1] | 6694 | 0.048 | 0.057 |
| (0.1, 0.2] | 4899 | 0.149 | 0.133 |
| (0.2, 0.3] | 4299 | 0.249 | 0.225 |
| (0.3, 0.4] | 3938 | 0.350 | 0.310 |
| (0.4, 0.5] | 3892 | 0.450 | 0.399 |
| (0.5, 0.6] | 3971 | 0.550 | 0.517 |
| (0.6, 0.7] | 4205 | 0.652 | 0.620 |
| (0.7, 0.8] | 4748 | 0.753 | 0.745 |
| (0.8, 0.9] | 5690 | 0.852 | 0.850 |
| (0.9, 1.0] | 4778 | 0.938 | 0.940 |

## Example Reachable Target Recommendations

| participant_id | subtype | wab_aq | task | concept | pred_ability+item |
| --- | --- | --- | --- | --- | --- |
| 100-1 | Anomic | 79.700 | Umbrella | lesson | 0.451 |
| 100-1 | Anomic | 79.700 | Cat | call | 0.366 |
| 100-1 | Anomic | 79.700 | Cat | rescue | 0.564 |
| 100-1 | Anomic | 79.700 | Window | break | 0.608 |
| 100-1 | Anomic | 79.700 | Sandwich | spread | 0.283 |
| 100-1 | Anomic | 79.700 | Window | chair | 0.261 |
| 100-1 | Anomic | 79.700 | Cinderella | fairy_godmother | 0.658 |
| 100-1 | Anomic | 79.700 | Cinderella | loss | 0.665 |
| 100-1 | Anomic | 79.700 | Cinderella | marriage | 0.682 |
| 100-1 | Anomic | 79.700 | Umbrella | take | 0.686 |
| 100-2 | Anomic | 79.700 | Cat | rescue | 0.477 |
| 100-2 | Anomic | 79.700 | Sandwich | sandwich | 0.400 |
| 100-2 | Anomic | 79.700 | Window | break | 0.518 |
| 100-2 | Anomic | 79.700 | Cinderella | chores | 0.359 |
| 100-2 | Anomic | 79.700 | Cinderella | fit | 0.550 |
| 100-2 | Anomic | 79.700 | Cat | stuck | 0.333 |
| 100-2 | Anomic | 79.700 | Cinderella | carriage | 0.299 |
| 100-2 | Anomic | 79.700 | Cat | call | 0.272 |
| 100-2 | Anomic | 79.700 | Sandwich | knife | 0.270 |
| 100-2 | Anomic | 79.700 | Umbrella | wet | 0.650 |
