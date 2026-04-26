# Cross-Prompt Concept Hierarchy Summary

## Hierarchy Reproducibility

| task | n | n_concepts | observed_reproducibility | random_p95 | beats_random_p95 |
| --- | --- | --- | --- | --- | --- |
| Window | 923 | 12 | 0.830 | 0.723 | True |
| Sandwich | 896 | 12 | 0.828 | 0.705 | True |
| Umbrella | 579 | 10 | 0.807 | 0.725 | True |
| Cinderella | 899 | 15 | 0.795 | 0.734 | True |
| Cat | 582 | 12 | 0.792 | 0.718 | True |
| Flood | 133 | 8 | 0.744 | 0.741 | True |

## Easiest And Hardest Concepts

| task | band | concept | threshold_aq_p50 | control_rate |
| --- | --- | --- | --- | --- |
| Cat | easy | cat | 42.606 | 0.988 |
| Cat | easy | dog | 46.613 | 0.891 |
| Cat | easy | father | 51.169 | 0.877 |
| Cat | hard | rescue | 91.146 | 0.718 |
| Cat | hard | stuck | 100.308 | 0.583 |
| Cat | hard | call | 102.393 | 0.702 |
| Cinderella | easy | slipper | 62.053 | 0.984 |
| Cinderella | easy | ball | 62.146 | 0.975 |
| Cinderella | easy | cinderella | 64.939 | 0.971 |
| Cinderella | hard | chores | 90.879 | 0.625 |
| Cinderella | hard | castle | 102.468 | 0.547 |
| Cinderella | hard | magic | 142.832 | 0.361 |
| Flood | easy | girl | 58.897 | 0.547 |
| Flood | easy | water | 59.185 | 0.934 |
| Flood | easy | rescue | 75.359 | 0.876 |
| Flood | hard | storm | 191.417 | 0.212 |
| Flood | hard | man | 269.859 | 0.343 |
| Flood | hard | boy | 273.115 | 0.080 |
| Sandwich | easy | butter | 43.978 | 1.000 |
| Sandwich | easy | bread | 44.955 | 0.998 |
| Sandwich | easy | jelly | 51.410 | 0.979 |
| Sandwich | hard | cut | 110.790 | 0.450 |
| Sandwich | hard | plate | 132.822 | 0.289 |
| Sandwich | hard | eat | 159.936 | 0.270 |
| Umbrella | easy | refusal | 20.941 | 0.815 |
| Umbrella | easy | rain | 45.215 | 0.974 |
| Umbrella | easy | mother | 57.425 | 0.970 |
| Umbrella | hard | wet | 75.143 | 0.797 |
| Umbrella | hard | take | 86.142 | 0.799 |
| Umbrella | hard | lesson | 182.375 | 0.419 |
| Window | easy | soccer_ball | 42.446 | 0.994 |
| Window | easy | window | 56.242 | 0.988 |
| Window | easy | kick | 59.280 | 0.945 |
| Window | hard | inside | 127.214 | 0.335 |
| Window | hard | angry | 175.314 | 0.188 |
| Window | hard | run_away | 306.153 | 0.159 |
