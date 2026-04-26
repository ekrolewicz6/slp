# Target Policy Simulation

- Top-k targets per participant: 5

## Policy Summary

| policy | n_targets | n_participants | mean_pred_success | mean_zone_045 | mean_learning_utility | pct_too_easy | pct_too_hard | mean_item_popularity | task_diversity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| near_threshold | 4533 | 907 | 0.440 | 0.939 | 0.240 | 0.003 | 0.009 | 0.438 | 5 |
| high_utility | 4533 | 907 | 0.481 | 0.928 | 0.242 | 0.006 | 0.006 | 0.466 | 5 |
| generic_popular | 4533 | 907 | 0.663 | 0.763 | 0.194 | 0.466 | 0.009 | 0.619 | 5 |
| easy_missed | 4533 | 907 | 0.668 | 0.762 | 0.194 | 0.473 | 0.005 | 0.615 | 5 |
| random_missed | 4533 | 907 | 0.345 | 0.758 | 0.160 | 0.123 | 0.444 | 0.335 | 5 |
| hard_missed | 4533 | 907 | 0.114 | 0.658 | 0.086 | 0.003 | 0.878 | 0.101 | 5 |

## Subtype Summary

| subtype | policy | n_participants | mean_pred_success | mean_zone_045 | pct_too_easy | pct_too_hard |
| --- | --- | --- | --- | --- | --- | --- |
| Anomic | near_threshold | 270 | 0.446 | 0.939 | 0.004 | 0.009 |
| Anomic | high_utility | 270 | 0.493 | 0.928 | 0.009 | 0.004 |
| Anomic | random_missed | 270 | 0.412 | 0.788 | 0.159 | 0.305 |
| Anomic | generic_popular | 270 | 0.721 | 0.724 | 0.598 | 0.003 |
| Anomic | easy_missed | 270 | 0.725 | 0.721 | 0.609 | 0.003 |
| Anomic | hard_missed | 270 | 0.152 | 0.697 | 0.003 | 0.833 |
| Broca | near_threshold | 270 | 0.428 | 0.940 | 0.001 | 0.016 |
| Broca | high_utility | 270 | 0.459 | 0.931 | 0.003 | 0.014 |
| Broca | easy_missed | 270 | 0.560 | 0.844 | 0.213 | 0.013 |
| Broca | generic_popular | 270 | 0.552 | 0.842 | 0.210 | 0.024 |
| Broca | random_missed | 270 | 0.229 | 0.720 | 0.053 | 0.657 |
| Broca | hard_missed | 270 | 0.044 | 0.593 | 0.001 | 0.978 |
| Conduction | near_threshold | 141 | 0.444 | 0.941 | 0.001 | 0.003 |
| Conduction | high_utility | 141 | 0.494 | 0.929 | 0.003 | 0.001 |
| Conduction | random_missed | 141 | 0.355 | 0.757 | 0.136 | 0.443 |
| Conduction | generic_popular | 141 | 0.713 | 0.731 | 0.586 | 0.000 |
| Conduction | easy_missed | 141 | 0.717 | 0.728 | 0.593 | 0.000 |
| Conduction | hard_missed | 141 | 0.095 | 0.644 | 0.001 | 0.945 |
| Global | near_threshold | 14 | 0.393 | 0.914 | 0.000 | 0.014 |
| Global | high_utility | 14 | 0.409 | 0.911 | 0.000 | 0.014 |
| Global | easy_missed | 14 | 0.425 | 0.898 | 0.043 | 0.014 |
| Global | generic_popular | 14 | 0.421 | 0.894 | 0.043 | 0.057 |
| Global | random_missed | 14 | 0.113 | 0.658 | 0.000 | 0.843 |
| Global | hard_missed | 14 | 0.009 | 0.559 | 0.000 | 1.000 |
| Isolation | easy_missed | 1 | 0.381 | 0.913 | 0.000 | 0.000 |
| Isolation | high_utility | 1 | 0.381 | 0.913 | 0.000 | 0.000 |
| Isolation | near_threshold | 1 | 0.381 | 0.913 | 0.000 | 0.000 |
| Isolation | generic_popular | 1 | 0.368 | 0.900 | 0.000 | 0.000 |
| Isolation | random_missed | 1 | 0.117 | 0.667 | 0.000 | 1.000 |
| Isolation | hard_missed | 1 | 0.006 | 0.556 | 0.000 | 1.000 |
| NotAphasic | near_threshold | 111 | 0.457 | 0.931 | 0.009 | 0.004 |
| NotAphasic | high_utility | 111 | 0.499 | 0.922 | 0.013 | 0.000 |
| NotAphasic | random_missed | 111 | 0.502 | 0.800 | 0.224 | 0.163 |
| NotAphasic | hard_missed | 111 | 0.251 | 0.772 | 0.009 | 0.613 |
| NotAphasic | generic_popular | 111 | 0.775 | 0.673 | 0.729 | 0.000 |
| NotAphasic | easy_missed | 111 | 0.778 | 0.671 | 0.736 | 0.000 |

## Task Distribution

| policy | task | n | pct |
| --- | --- | --- | --- |
| easy_missed | Sandwich | 1144 | 0.252 |
| easy_missed | Cinderella | 993 | 0.219 |
| easy_missed | Window | 940 | 0.207 |
| easy_missed | Cat | 757 | 0.167 |
| easy_missed | Umbrella | 699 | 0.154 |
| generic_popular | Sandwich | 1197 | 0.264 |
| generic_popular | Cinderella | 933 | 0.206 |
| generic_popular | Window | 906 | 0.200 |
| generic_popular | Cat | 830 | 0.183 |
| generic_popular | Umbrella | 667 | 0.147 |
| hard_missed | Window | 2406 | 0.531 |
| hard_missed | Sandwich | 1227 | 0.271 |
| hard_missed | Cinderella | 831 | 0.183 |
| hard_missed | Umbrella | 50 | 0.011 |
| hard_missed | Cat | 19 | 0.004 |
| high_utility | Cinderella | 1463 | 0.323 |
| high_utility | Sandwich | 1066 | 0.235 |
| high_utility | Window | 860 | 0.190 |
| high_utility | Cat | 598 | 0.132 |
| high_utility | Umbrella | 546 | 0.120 |
| near_threshold | Cinderella | 1425 | 0.314 |
| near_threshold | Sandwich | 1116 | 0.246 |
| near_threshold | Window | 920 | 0.203 |
| near_threshold | Cat | 566 | 0.125 |
| near_threshold | Umbrella | 506 | 0.112 |
| random_missed | Cinderella | 1462 | 0.323 |
| random_missed | Sandwich | 1300 | 0.287 |
| random_missed | Window | 1135 | 0.250 |
| random_missed | Cat | 434 | 0.096 |
| random_missed | Umbrella | 202 | 0.045 |
