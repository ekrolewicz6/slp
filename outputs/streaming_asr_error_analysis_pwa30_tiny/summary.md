# Streaming ASR Error Analysis

- Task rows: 150
- Concept decisions: 1830
- Mean task F1: 0.764
- Mean task recall: 0.718
- Mean task precision: 0.859
- ASR coverage vs WAB r: 0.713

## Task Error Profile

| task | concepts | human_hits | asr_hits | false_negatives | false_positives | true_positives | recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cat | 360 | 198 | 159 | 40 | 1 | 158 | 0.798 | 0.994 |
| Cinderella | 450 | 215 | 178 | 43 | 6 | 172 | 0.800 | 0.966 |
| Sandwich | 360 | 189 | 148 | 47 | 6 | 142 | 0.751 | 0.959 |
| Umbrella | 300 | 177 | 154 | 28 | 5 | 149 | 0.842 | 0.968 |
| Window | 360 | 160 | 141 | 25 | 6 | 135 | 0.844 | 0.957 |

## Most Missed Concepts

| task | concept | human_hits | asr_hits | false_negatives | false_positives | true_positives | recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cinderella | midnight | 19 | 8 | 11 | 0 | 8 | 0.421 | 1.000 |
| Sandwich | eat | 14 | 4 | 10 | 0 | 4 | 0.286 | 1.000 |
| Sandwich | jelly | 26 | 17 | 9 | 0 | 17 | 0.654 | 1.000 |
| Cat | chase | 17 | 10 | 7 | 0 | 10 | 0.588 | 1.000 |
| Sandwich | butter | 27 | 21 | 6 | 0 | 21 | 0.778 | 1.000 |
| Window | soccer_ball | 26 | 20 | 6 | 0 | 20 | 0.769 | 1.000 |
| Umbrella | rain | 24 | 18 | 6 | 0 | 18 | 0.750 | 1.000 |
| Cat | dog | 21 | 15 | 6 | 0 | 15 | 0.714 | 1.000 |
| Sandwich | peanut | 24 | 20 | 5 | 1 | 19 | 0.792 | 0.950 |
| Umbrella | umbrella | 20 | 15 | 5 | 0 | 15 | 0.750 | 1.000 |
| Cat | ladder | 16 | 11 | 5 | 0 | 11 | 0.688 | 1.000 |
| Sandwich | sandwich | 10 | 5 | 5 | 0 | 5 | 0.500 | 1.000 |
| Window | man | 17 | 14 | 4 | 1 | 13 | 0.765 | 0.929 |
| Cat | father | 20 | 16 | 4 | 0 | 16 | 0.800 | 1.000 |
| Cat | firefighters | 19 | 15 | 4 | 0 | 15 | 0.789 | 1.000 |
| Cinderella | prince | 19 | 15 | 4 | 0 | 15 | 0.789 | 1.000 |
| Cinderella | slipper | 18 | 14 | 4 | 0 | 14 | 0.778 | 1.000 |
| Umbrella | outside | 17 | 13 | 4 | 0 | 13 | 0.765 | 1.000 |
| Cinderella | stepfamily | 16 | 12 | 4 | 0 | 12 | 0.750 | 1.000 |
| Umbrella | wet | 16 | 12 | 4 | 0 | 12 | 0.750 | 1.000 |
| Cinderella | fairy_godmother | 14 | 10 | 4 | 0 | 10 | 0.714 | 1.000 |
| Window | break | 11 | 7 | 4 | 0 | 7 | 0.636 | 1.000 |
| Cinderella | cinderella | 18 | 16 | 3 | 1 | 15 | 0.833 | 0.938 |
| Cinderella | dress | 18 | 16 | 3 | 1 | 15 | 0.833 | 0.938 |
| Cinderella | loss | 16 | 14 | 3 | 1 | 13 | 0.812 | 0.929 |

## Subtype Error Profile

| subtype | rows | human_hits | asr_hits | false_negatives | false_positives | true_positives | recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Anomic | 11 | 400 | 318 | 91 | 9 | 309 | 0.772 | 0.972 |
| Broca | 6 | 78 | 50 | 31 | 3 | 47 | 0.603 | 0.940 |
| Conduction | 3 | 100 | 85 | 18 | 3 | 82 | 0.820 | 0.965 |
| Isolation | 1 | 6 | 0 | 6 | 0 | 0 | 0.000 | 0.000 |
| NotAphasic | 6 | 265 | 252 | 15 | 2 | 250 | 0.943 | 0.992 |
| TransMotor | 1 | 39 | 29 | 12 | 2 | 27 | 0.692 | 0.931 |
| Wernicke | 2 | 51 | 46 | 10 | 5 | 41 | 0.804 | 0.891 |

## Interpretation

Most ASR content loss is false-negative loss rather than hallucinated false content. That makes ASR-derived discourse scores conservative: useful for tracking content state, but likely to under-score some concepts unless ASR normalization or forced alignment recovers aphasic productions.
