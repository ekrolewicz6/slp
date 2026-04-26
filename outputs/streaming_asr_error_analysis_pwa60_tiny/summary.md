# Streaming ASR Error Analysis

- Task rows: 233
- Concept decisions: 2869
- Mean task F1: 0.742
- Mean task recall: 0.703
- Mean task precision: 0.817
- ASR coverage vs WAB r: 0.738

## Task Error Profile

| task | concepts | human_hits | asr_hits | false_negatives | false_positives | true_positives | recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cat | 480 | 240 | 206 | 37 | 3 | 203 | 0.846 | 0.985 |
| Cinderella | 765 | 258 | 207 | 68 | 17 | 190 | 0.736 | 0.918 |
| Sandwich | 600 | 224 | 180 | 47 | 3 | 177 | 0.790 | 0.983 |
| Umbrella | 400 | 208 | 196 | 24 | 12 | 184 | 0.885 | 0.939 |
| Window | 624 | 210 | 182 | 35 | 7 | 175 | 0.833 | 0.962 |

## Most Missed Concepts

| task | concept | human_hits | asr_hits | false_negatives | false_positives | true_positives | recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sandwich | bread | 33 | 19 | 14 | 0 | 19 | 0.576 | 1.000 |
| Cinderella | midnight | 22 | 8 | 14 | 0 | 8 | 0.364 | 1.000 |
| Cinderella | dress | 18 | 9 | 10 | 1 | 8 | 0.444 | 0.889 |
| Cat | firefighters | 25 | 16 | 9 | 0 | 16 | 0.640 | 1.000 |
| Cinderella | slipper | 28 | 22 | 8 | 2 | 20 | 0.714 | 0.909 |
| Window | soccer_ball | 36 | 28 | 8 | 0 | 28 | 0.778 | 1.000 |
| Cat | chase | 20 | 13 | 7 | 0 | 13 | 0.650 | 1.000 |
| Sandwich | peanut | 32 | 26 | 6 | 0 | 26 | 0.812 | 1.000 |
| Cinderella | ball | 31 | 25 | 6 | 0 | 25 | 0.806 | 1.000 |
| Cinderella | prince | 20 | 14 | 6 | 0 | 14 | 0.700 | 1.000 |
| Window | kick | 30 | 26 | 5 | 1 | 25 | 0.833 | 0.962 |
| Sandwich | butter | 34 | 29 | 5 | 0 | 29 | 0.853 | 1.000 |
| Umbrella | rain | 34 | 29 | 5 | 0 | 29 | 0.853 | 1.000 |
| Cat | dog | 30 | 25 | 5 | 0 | 25 | 0.833 | 1.000 |
| Window | boy | 26 | 21 | 5 | 0 | 21 | 0.808 | 1.000 |
| Cinderella | cinderella | 24 | 19 | 5 | 0 | 19 | 0.792 | 1.000 |
| Umbrella | refusal | 25 | 27 | 4 | 6 | 21 | 0.840 | 0.778 |
| Cinderella | marriage | 17 | 14 | 4 | 1 | 13 | 0.765 | 0.929 |
| Sandwich | jelly | 29 | 25 | 4 | 0 | 25 | 0.862 | 1.000 |
| Window | man | 24 | 20 | 4 | 0 | 20 | 0.833 | 1.000 |
| Umbrella | wet | 21 | 17 | 4 | 0 | 17 | 0.810 | 1.000 |
| Cat | ladder | 18 | 14 | 4 | 0 | 14 | 0.778 | 1.000 |
| Cinderella | stepfamily | 15 | 11 | 4 | 0 | 11 | 0.733 | 1.000 |
| Cinderella | carriage | 13 | 9 | 4 | 0 | 9 | 0.692 | 1.000 |
| Window | break | 13 | 9 | 4 | 0 | 9 | 0.692 | 1.000 |

## Subtype Error Profile

| subtype | rows | human_hits | asr_hits | false_negatives | false_positives | true_positives | recall | precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Anomic | 12 | 406 | 340 | 75 | 9 | 331 | 0.815 | 0.974 |
| Broca | 22 | 214 | 164 | 68 | 18 | 146 | 0.682 | 0.890 |
| Conduction | 3 | 99 | 88 | 13 | 2 | 86 | 0.869 | 0.977 |
| NotAphasic | 8 | 337 | 307 | 34 | 4 | 303 | 0.899 | 0.987 |
| Wernicke | 7 | 84 | 72 | 21 | 9 | 63 | 0.750 | 0.875 |

## Interpretation

Most ASR content loss is false-negative loss rather than hallucinated false content. That makes ASR-derived discourse scores conservative: useful for tracking content state, but likely to under-score some concepts unless ASR normalization or forced alignment recovers aphasic productions.
