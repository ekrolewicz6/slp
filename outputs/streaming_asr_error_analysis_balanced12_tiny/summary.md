# Streaming ASR Error Analysis

- Task rows: 60
- Concept decisions: 732
- Mean task F1: 0.783
- Mean task recall: 0.732
- Mean task precision: 0.873
- ASR coverage vs WAB r: 0.722

## Task Error Profile

| task | concepts | human_hits | asr_hits | false_negatives | false_positives | true_positives | recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cat | 144 | 64 | 53 | 12 | 1 | 52 | 0.812 | 0.981 |
| Cinderella | 180 | 69 | 58 | 13 | 2 | 56 | 0.812 | 0.966 |
| Sandwich | 144 | 73 | 59 | 16 | 2 | 57 | 0.781 | 0.966 |
| Umbrella | 120 | 58 | 53 | 8 | 3 | 50 | 0.862 | 0.943 |
| Window | 144 | 52 | 39 | 14 | 1 | 38 | 0.731 | 0.974 |

## Most Missed Concepts

| task | concept | human_hits | asr_hits | false_negatives | false_positives | true_positives | recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Window | kick | 10 | 6 | 4 | 0 | 6 | 0.600 | 1.000 |
| Cinderella | dress | 6 | 2 | 4 | 0 | 2 | 0.333 | 1.000 |
| Sandwich | peanut | 11 | 8 | 3 | 0 | 8 | 0.727 | 1.000 |
| Window | soccer_ball | 11 | 8 | 3 | 0 | 8 | 0.727 | 1.000 |
| Umbrella | rain | 10 | 7 | 3 | 0 | 7 | 0.700 | 1.000 |
| Cat | firefighters | 9 | 6 | 3 | 0 | 6 | 0.667 | 1.000 |
| Umbrella | refusal | 7 | 8 | 2 | 3 | 5 | 0.714 | 0.625 |
| Sandwich | butter | 11 | 9 | 2 | 0 | 9 | 0.818 | 1.000 |
| Sandwich | bread | 10 | 8 | 2 | 0 | 8 | 0.800 | 1.000 |
| Cat | dog | 9 | 7 | 2 | 0 | 7 | 0.778 | 1.000 |
| Cat | father | 6 | 4 | 2 | 0 | 4 | 0.667 | 1.000 |
| Cinderella | midnight | 5 | 3 | 2 | 0 | 3 | 0.600 | 1.000 |
| Sandwich | sandwich | 4 | 2 | 2 | 0 | 2 | 0.500 | 1.000 |
| Cat | chase | 3 | 1 | 2 | 0 | 1 | 0.333 | 1.000 |
| Sandwich | eat | 3 | 1 | 2 | 0 | 1 | 0.333 | 1.000 |
| Window | house | 2 | 0 | 2 | 0 | 0 | 0.000 | 0.000 |
| Sandwich | together | 6 | 6 | 1 | 1 | 5 | 0.833 | 0.833 |
| Sandwich | cut | 4 | 4 | 1 | 1 | 3 | 0.750 | 0.750 |
| Window | man | 4 | 4 | 1 | 1 | 3 | 0.750 | 0.750 |
| Cat | cat | 11 | 10 | 1 | 0 | 10 | 0.909 | 1.000 |
| Sandwich | jelly | 11 | 10 | 1 | 0 | 10 | 0.909 | 1.000 |
| Cinderella | ball | 8 | 7 | 1 | 0 | 7 | 0.875 | 1.000 |
| Window | window | 8 | 7 | 1 | 0 | 7 | 0.875 | 1.000 |
| Umbrella | umbrella | 7 | 6 | 1 | 0 | 6 | 0.857 | 1.000 |
| Cinderella | cinderella | 6 | 5 | 1 | 0 | 5 | 0.833 | 1.000 |

## Subtype Error Profile

| subtype | rows | human_hits | asr_hits | false_negatives | false_positives | true_positives | recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Anomic | 5 | 153 | 124 | 32 | 3 | 121 | 0.791 | 0.976 |
| Broca | 4 | 56 | 44 | 15 | 3 | 41 | 0.732 | 0.932 |
| NotAphasic | 1 | 45 | 43 | 3 | 1 | 42 | 0.933 | 0.977 |
| Wernicke | 1 | 14 | 12 | 4 | 2 | 10 | 0.714 | 0.833 |

## Interpretation

Most ASR content loss is false-negative loss rather than hallucinated false content. That makes ASR-derived discourse scores conservative: useful for tracking content state, but likely to under-score some concepts unless ASR normalization or forced alignment recovers aphasic productions.
