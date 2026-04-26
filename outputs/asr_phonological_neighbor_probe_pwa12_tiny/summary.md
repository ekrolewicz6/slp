# ASR Phonological/String Neighbor Probe

- Missed-concept clip rows: 432

## Top-k Recovery Of Missed Concepts

| k | n_miss_clips | hit_any_missed | missed_concept_recall | mean_candidate_count | mean_max_missed_similarity | near_miss_ge_65 | near_miss_ge_75 | near_miss_ge_85 | random_hit_any_mean | random_hit_any_p95 | random_recall_mean | random_recall_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 144 | 0.257 | 0.247 | 12.188 | 0.555 | 0.382 | 0.188 | 0.062 | 0.097 | 0.132 | 0.083 | 0.118 |
| 3 | 144 | 0.493 | 0.449 | 12.188 | 0.555 | 0.382 | 0.188 | 0.062 | 0.284 | 0.333 | 0.250 | 0.300 |
| 5 | 144 | 0.632 | 0.580 | 12.188 | 0.555 | 0.382 | 0.188 | 0.062 | 0.466 | 0.521 | 0.423 | 0.480 |

## Strongest Near-Miss Examples

| transcript_id | task | utterance_idx | k | missed_concepts | top_candidates | max_missed_similarity |
| --- | --- | --- | --- | --- | --- | --- |
| Protocol/MSU/PWA/MSU04b | Umbrella | 16 | 1 | ["rain"] | ["rain"] | 0.889 |
| Protocol/Kurland/PWA/kurland24b | Umbrella | 1 | 5 | ["rain"] | ["rain", "take", "refusal", "lesson", "return_home"] | 0.889 |
| Protocol/Kurland/PWA/kurland24b | Umbrella | 1 | 3 | ["rain"] | ["rain", "take", "refusal"] | 0.889 |
| Protocol/Kurland/PWA/kurland24b | Umbrella | 1 | 1 | ["rain"] | ["rain"] | 0.889 |
| Protocol/MSU/PWA/MSU04b | Umbrella | 16 | 5 | ["rain"] | ["rain", "boy", "refusal", "outside", "mother"] | 0.889 |
| Protocol/MSU/PWA/MSU04b | Umbrella | 16 | 3 | ["rain"] | ["rain", "boy", "refusal"] | 0.889 |
| Protocol/NEURAL-2/PWA/305-2 | Umbrella | 8 | 5 | ["umbrella"] | ["umbrella", "mother", "wet", "return_home", "lesson"] | 0.875 |
| Protocol/NEURAL-2/PWA/305-2 | Umbrella | 8 | 3 | ["umbrella"] | ["umbrella", "mother", "wet"] | 0.875 |
| Protocol/NEURAL-2/PWA/305-2 | Umbrella | 8 | 1 | ["umbrella"] | ["umbrella"] | 0.875 |
| Protocol/Richardson/PWA/richardson14a | Window | 3 | 5 | ["soccer_ball"] | ["soccer_ball", "run_away", "man", "boy", "angry"] | 0.857 |
| Protocol/NEURAL-2/PWA/305-2 | Cinderella | 21 | 1 | ["slipper"] | ["slipper"] | 0.857 |
| Protocol/Richardson/PWA/richardson09a | Window | 19 | 1 | ["run_away"] | ["run_away"] | 0.857 |
| Protocol/NEURAL-2/PWA/305-2 | Cinderella | 21 | 5 | ["slipper"] | ["slipper", "chores", "stepfamily", "midnight", "fairy_godmother"] | 0.857 |
| Protocol/NEURAL-2/PWA/305-2 | Cinderella | 21 | 3 | ["slipper"] | ["slipper", "chores", "stepfamily"] | 0.857 |
| Protocol/NEURAL-2/PWA/305-2 | Cinderella | 19 | 3 | ["slipper"] | ["slipper", "loss", "chores"] | 0.857 |
| Protocol/NEURAL-2/PWA/305-2 | Cinderella | 19 | 5 | ["slipper"] | ["slipper", "loss", "chores", "dress", "midnight"] | 0.857 |
| Protocol/Richardson/PWA/richardson09a | Window | 19 | 5 | ["run_away"] | ["run_away", "boy", "look", "house", "window"] | 0.857 |
| Protocol/NEURAL-2/PWA/305-2 | Cinderella | 19 | 1 | ["slipper"] | ["slipper"] | 0.857 |
| Protocol/Kurland/PWA/kurland24b | Window | 0 | 5 | ["kick", "soccer_ball"] | ["soccer_ball", "run_away", "man", "angry", "look"] | 0.857 |
| Protocol/Kurland/PWA/kurland24b | Window | 0 | 3 | ["kick", "soccer_ball"] | ["soccer_ball", "run_away", "man"] | 0.857 |

## Interpretation

This asks whether the 1-best ASR text preserves a string-level clue for concepts it failed to recognize exactly. If top-k recovery beats random and near-miss similarity is common, phonological-neighbor features may help a clarification gate. If it is close to random, we need actual ASR alternatives or audio-level forced alignment rather than mining the 1-best transcript.
