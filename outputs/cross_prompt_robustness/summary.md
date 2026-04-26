# Cross-Prompt Robustness Summary

## Main CV Setups

| cv | setup | n | mae | r | r_boot_lo | r_boot_hi |
| --- | --- | --- | --- | --- | --- | --- |
| corpus_grouped | subtype+content+verbosity | 907 | 6.095 | 0.928 | 0.905 | 0.940 |
| corpus_grouped | content+verbosity | 907 | 7.987 | 0.878 | 0.834 | 0.893 |
| corpus_grouped | subtype_only | 907 | 8.420 | 0.841 | 0.798 | 0.872 |
| corpus_grouped | verbosity | 907 | 13.071 | 0.631 | 0.550 | 0.674 |
| participant_grouped | subtype+content+verbosity | 907 | 5.500 | 0.938 | 0.928 | 0.948 |
| participant_grouped | content+verbosity | 907 | 7.417 | 0.890 | 0.872 | 0.908 |
| participant_grouped | subtype_only | 907 | 8.203 | 0.852 | 0.834 | 0.869 |
| participant_grouped | verbosity | 907 | 12.056 | 0.698 | 0.658 | 0.740 |

## Leave-One-Corpus-Out: Content + Verbosity

| held_corpus | n_test | test_mean_wab | mae | r |
| --- | --- | --- | --- | --- |
| NEURAL-2 | 128 | 84.227 | 6.941 | 0.883 |
| Fridriksson-2 | 328 | 63.262 | 8.288 | 0.880 |
| Kurland | 62 | 71.963 | 9.505 | 0.824 |
| SCALE | 54 | 69.006 | 8.970 | 0.755 |

## Within-Subtype Models

| subtype | setup | n | mae | r |
| --- | --- | --- | --- | --- |
| Anomic | content+verbosity | 270 | 4.176 | 0.489 |
| Anomic | verbosity | 270 | 4.770 | 0.260 |
| Broca | content+verbosity | 270 | 6.432 | 0.822 |
| Broca | verbosity | 270 | 10.609 | 0.460 |
| Conduction | content+verbosity | 141 | 5.035 | 0.796 |
| Conduction | verbosity | 141 | 8.209 | 0.293 |
| NotAphasic | content+verbosity | 111 | 1.486 | 0.278 |
| NotAphasic | verbosity | 111 | 1.561 | 0.208 |
| Wernicke | content+verbosity | 63 | 5.596 | 0.863 |
| Wernicke | verbosity | 63 | 11.568 | 0.460 |

## Core-Task Ablation

| drop_task | n | mae | r |
| --- | --- | --- | --- |
| none | 907 | 8.483 | 0.860 |
| Cat | 907 | 8.580 | 0.856 |
| Umbrella | 907 | 8.612 | 0.856 |
| Window | 907 | 8.665 | 0.855 |
| Cinderella | 907 | 8.717 | 0.849 |
| Sandwich | 907 | 9.372 | 0.832 |

## Shuffled-WAB Negative Control Within Subtype

| setup | n_permutations | mean_r | p95_r | max_r | mean_mae |
| --- | --- | --- | --- | --- | --- |
| content+verbosity | 100 | 0.646 | 0.667 | 0.684 | 12.618 |
| subtype+content+verbosity | 100 | 0.834 | 0.841 | 0.848 | 8.649 |
