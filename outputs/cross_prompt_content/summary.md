# Cross-Prompt Content Summary

- Segments: 7153
- WAB-labeled non-control segments: 4012
- Patients/roots with WAB: 851

## Segment Counts

| task | n | n_wab | n_wab_noncontrol | n_patients | n_controls |
| --- | --- | --- | --- | --- | --- |
| Cat | 1201 | 640 | 582 | 1019 | 496 |
| Cinderella | 1494 | 954 | 899 | 1323 | 488 |
| Cookie | 1 | 0 | 0 | 1 | 0 |
| Flood | 273 | 133 | 133 | 272 | 137 |
| Sandwich | 1464 | 949 | 896 | 1323 | 471 |
| Umbrella | 1186 | 637 | 579 | 1035 | 508 |
| Window | 1534 | 981 | 923 | 1380 | 511 |

## Best Pooled Models

| setup | n | mae | r | r_boot_lo | r_boot_hi |
| --- | --- | --- | --- | --- | --- |
| subtype+observed+task | 3961 | 6.138 | 0.918 | 0.908 | 0.928 |
| subtype_only | 3961 | 7.916 | 0.857 | 0.838 | 0.876 |
| structure+observed+task | 4012 | 9.529 | 0.814 | 0.794 | 0.832 |
| observed_content+task | 4012 | 10.387 | 0.782 | 0.758 | 0.803 |
| observed_content_no_task | 4012 | 10.487 | 0.777 | 0.754 | 0.798 |
| target_augmented_content+task | 4012 | 10.720 | 0.771 | 0.747 | 0.790 |
| structure+task | 4012 | 12.557 | 0.658 | 0.620 | 0.693 |
| verbosity+task | 4012 | 13.210 | 0.620 | 0.580 | 0.660 |

## Best Task-Specific Models

| task | setup | n | mae | r | r_boot_lo | r_boot_hi |
| --- | --- | --- | --- | --- | --- | --- |
| Cat | structure+observed | 582 | 9.077 | 0.793 | 0.757 | 0.826 |
| Cat | observed_binary | 582 | 10.026 | 0.749 | 0.703 | 0.790 |
| Cat | observed_all | 582 | 10.024 | 0.747 | 0.705 | 0.788 |
| Cinderella | structure+observed | 899 | 8.259 | 0.868 | 0.851 | 0.885 |
| Cinderella | observed_all | 899 | 9.551 | 0.822 | 0.802 | 0.847 |
| Cinderella | target_augmented_all | 899 | 9.796 | 0.815 | 0.792 | 0.838 |
| Flood | structure+observed | 133 | 12.333 | 0.637 | 0.504 | 0.755 |
| Flood | target_augmented_all | 133 | 13.976 | 0.578 | 0.441 | 0.708 |
| Flood | observed_binary | 133 | 14.945 | 0.510 | 0.352 | 0.647 |
| Sandwich | structure+observed | 896 | 9.608 | 0.812 | 0.782 | 0.834 |
| Sandwich | observed_all | 896 | 10.173 | 0.794 | 0.762 | 0.820 |
| Sandwich | observed_binary | 896 | 10.225 | 0.788 | 0.753 | 0.814 |
| Umbrella | structure+observed | 579 | 9.344 | 0.806 | 0.769 | 0.838 |
| Umbrella | observed_binary | 579 | 9.404 | 0.788 | 0.745 | 0.830 |
| Umbrella | observed_all | 579 | 9.802 | 0.778 | 0.737 | 0.814 |
| Window | structure+observed | 923 | 9.296 | 0.836 | 0.813 | 0.859 |
| Window | observed_binary | 923 | 10.207 | 0.803 | 0.779 | 0.827 |
| Window | observed_all | 923 | 10.231 | 0.799 | 0.771 | 0.825 |

## Leave-Task-Out Transfer

| held_out_task | split | n_test | mae | r |
| --- | --- | --- | --- | --- |
| Cat | leave_task_out_participants_may_overlap | 582 | 8.886 | 0.803 |
| Cinderella | leave_task_out_participants_may_overlap | 899 | 13.388 | 0.801 |
| Flood | leave_task_out_participants_may_overlap | 133 | 14.266 | 0.571 |
| Sandwich | leave_task_out_participants_may_overlap | 896 | 10.484 | 0.796 |
| Umbrella | leave_task_out_participants_may_overlap | 579 | 10.339 | 0.758 |
| Window | leave_task_out_participants_may_overlap | 923 | 10.306 | 0.794 |
| Cat | leave_task_out_patient_disjoint | 582 | 10.088 | 0.787 |
| Cinderella | leave_task_out_patient_disjoint | 899 | 23.982 | 0.706 |
| Flood | leave_task_out_patient_disjoint | 133 | 14.579 | 0.560 |
| Sandwich | leave_task_out_patient_disjoint | 896 | 13.243 | 0.702 |
| Umbrella | leave_task_out_patient_disjoint | 579 | 12.824 | 0.725 |
