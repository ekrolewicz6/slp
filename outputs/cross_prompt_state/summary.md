# Cross-Prompt Content State Reliability

- Session-level rows: 1570
- WAB-labeled non-control sessions with >=3 core tasks: 907

## Patient-Level WAB Models

| setup | n | mae | r | r_boot_lo | r_boot_hi | n_patients |
| --- | --- | --- | --- | --- | --- | --- |
| subtype+content | 894 | 5.429 | 0.941 | 0.931 | 0.949 | 801 |
| content+verbosity | 907 | 7.418 | 0.890 | 0.872 | 0.907 | 814 |
| coverage_vector | 907 | 8.395 | 0.864 | 0.844 | 0.882 | 814 |
| content_summary | 907 | 8.466 | 0.863 | 0.843 | 0.882 | 814 |
| all_task_vector_z | 907 | 8.411 | 0.863 | 0.844 | 0.881 | 814 |
| core_task_vector_z | 907 | 8.483 | 0.860 | 0.841 | 0.879 | 814 |
| subtype_only | 894 | 8.066 | 0.857 | 0.839 | 0.874 | 801 |
| verbosity_summary | 907 | 12.056 | 0.698 | 0.658 | 0.740 | 814 |

## Split-Half Reliability

| split | n | r_between_halves | r_left_wab_aq | r_right_wab_aq |
| --- | --- | --- | --- | --- |
| picture_vs_story_procedure | 517 | 0.818 | 0.771 | 0.790 |
| narrative_vs_procedure | 517 | 0.721 | 0.798 | 0.694 |
| short_sequences_vs_cinderella | 539 | 0.781 | 0.782 | 0.736 |
| cronbach_alpha_core_tasks | 517 | 0.909 | 0.813 |  |

## Strongest Pairwise Task Correlations

| task_a | task_b | n | r |
| --- | --- | --- | --- |
| Umbrella | Window | 668 | 0.782 |
| Cat | Umbrella | 663 | 0.751 |
| Cat | Window | 662 | 0.744 |
| Cat | Cinderella | 635 | 0.740 |
| Cinderella | Window | 949 | 0.727 |
| Cinderella | Umbrella | 610 | 0.722 |
| Cinderella | Sandwich | 923 | 0.702 |
| Cat | Sandwich | 635 | 0.693 |
| Sandwich | Window | 966 | 0.691 |
| Sandwich | Umbrella | 635 | 0.663 |

## Weakest Pairwise Task Correlations

| task_a | task_b | n | r |
| --- | --- | --- | --- |
| Flood | Window | 135 | 0.514 |
| Flood | Umbrella | 135 | 0.439 |
| Flood | Sandwich | 132 | 0.410 |
| Cinderella | Flood | 120 | 0.393 |
| Cat | Cookie | 0 |  |
| Cinderella | Cookie | 1 |  |
| Cookie | Flood | 0 |  |
| Cookie | Sandwich | 1 |  |
| Cookie | Umbrella | 0 |  |
| Cookie | Window | 0 |  |
