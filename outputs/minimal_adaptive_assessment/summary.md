# Minimal / Adaptive Assessment Summary

- Complete five-core-task sessions: 517

## Best Content-Only Subsets By Number Of Prompts

| n_tasks | tasks | state_r | raw_subset_wab_r | mae | r |
| --- | --- | --- | --- | --- | --- |
| 1 | Cinderella | 0.870 | 0.736 | 9.375 | 0.753 |
| 1 | Cat | 0.891 | 0.737 | 9.718 | 0.728 |
| 1 | Sandwich | 0.802 | 0.694 | 10.044 | 0.702 |
| 1 | Umbrella | 0.897 | 0.685 | 10.505 | 0.681 |
| 1 | Window | 0.859 | 0.675 | 10.323 | 0.681 |
| 2 | Cinderella+Sandwich | 0.925 | 0.790 | 8.901 | 0.779 |
| 2 | Cat+Cinderella | 0.948 | 0.793 | 8.779 | 0.777 |
| 2 | Cat+Sandwich | 0.932 | 0.786 | 8.879 | 0.772 |
| 2 | Cinderella+Window | 0.944 | 0.774 | 9.225 | 0.765 |
| 2 | Cat+Window | 0.945 | 0.764 | 9.401 | 0.747 |
| 3 | Cat+Cinderella+Sandwich | 0.966 | 0.815 | 8.409 | 0.804 |
| 3 | Cat+Cinderella+Window | 0.974 | 0.801 | 8.479 | 0.800 |
| 3 | Cinderella+Sandwich+Window | 0.968 | 0.805 | 8.489 | 0.794 |
| 3 | Cat+Sandwich+Window | 0.967 | 0.797 | 8.486 | 0.792 |
| 3 | Cinderella+Sandwich+Umbrella | 0.977 | 0.798 | 8.648 | 0.790 |
| 4 | Cat+Cinderella+Sandwich+Window | 0.985 | 0.819 | 8.019 | 0.814 |
| 4 | Cat+Cinderella+Sandwich+Umbrella | 0.993 | 0.813 | 8.270 | 0.805 |
| 4 | Cinderella+Sandwich+Umbrella+Window | 0.990 | 0.802 | 8.240 | 0.800 |
| 4 | Cat+Cinderella+Umbrella+Window | 0.992 | 0.798 | 8.377 | 0.798 |
| 4 | Cat+Sandwich+Umbrella+Window | 0.989 | 0.795 | 8.338 | 0.796 |
| 5 | Cat+Cinderella+Sandwich+Umbrella+Window | 1.000 | 0.813 | 8.026 | 0.818 |

## Greedy Prompt Order For WAB Prediction

| step | added_task | selected_order | state_r | mae | r |
| --- | --- | --- | --- | --- | --- |
| 1 | Cinderella | Cinderella | 0.870 | 9.375 | 0.753 |
| 2 | Sandwich | Cinderella -> Sandwich | 0.925 | 8.901 | 0.779 |
| 3 | Cat | Cinderella -> Sandwich -> Cat | 0.966 | 8.409 | 0.804 |
| 4 | Window | Cinderella -> Sandwich -> Cat -> Window | 0.985 | 8.019 | 0.814 |
| 5 | Umbrella | Cinderella -> Sandwich -> Cat -> Window -> Umbrella | 1.000 | 8.026 | 0.818 |
