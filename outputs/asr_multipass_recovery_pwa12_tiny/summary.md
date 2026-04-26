# ASR Multipass Recovery

- Missed-concept clips selected: 144
- ASR passes: 576

## Overall Union Recovery

| n_clips | n_missed_concepts | clips_any_union_recovery | mean_union_recovery_frac | concept_recovery_frac |
| --- | --- | --- | --- | --- |
| 144 | 168 | 0.153 | 0.135 | 0.131 |

## By Temperature

| temperature | n_passes | mean_recovery_frac | any_recovered |
| --- | --- | --- | --- |
| 0.000 | 144 | 0.000 | 0.000 |
| 0.200 | 144 | 0.035 | 0.042 |
| 0.400 | 144 | 0.056 | 0.062 |
| 0.600 | 144 | 0.076 | 0.090 |

## Recovered Examples

| transcript_id | task | utterance_idx | missed_concepts | union_recovered_concepts | union_recovery_frac |
| --- | --- | --- | --- | --- | --- |
| Protocol/Kurland/PWA/kurland10b | Cinderella | 16 | ball | ball | 1.000 |
| Protocol/Kurland/PWA/kurland10b | Cinderella | 32 | prince | prince | 1.000 |
| Protocol/Kurland/PWA/kurland16b | Cat | 5 | dog | dog | 1.000 |
| Protocol/Kurland/PWA/kurland24b | Sandwich | 2 | jelly;put_on | put_on | 0.500 |
| Protocol/Kurland/PWA/kurland24b | Umbrella | 8 | rain | rain | 1.000 |
| Protocol/Kurland/PWA/kurland24b | Window | 0 | kick;soccer_ball | kick | 0.500 |
| Protocol/Kurland/PWA/kurland25a | Cat | 5 | cat | cat | 1.000 |
| Protocol/Kurland/PWA/kurland25a | Window | 4 | house;kick | house | 0.500 |
| Protocol/MSU/PWA/MSU04b | Cinderella | 17 | fairy_godmother | fairy_godmother | 1.000 |
| Protocol/MSU/PWA/MSU04b | Umbrella | 22 | refusal | refusal | 1.000 |
| Protocol/NEURAL-2/PWA/284-2 | Cinderella | 24 | slipper | slipper | 1.000 |
| Protocol/NEURAL-2/PWA/284-2 | Cinderella | 28 | slipper | slipper | 1.000 |
| Protocol/NEURAL-2/PWA/284-2 | Sandwich | 3 | sandwich | sandwich | 1.000 |
| Protocol/NEURAL-2/PWA/284-2 | Window | 3 | soccer_ball | soccer_ball | 1.000 |
| Protocol/NEURAL-2/PWA/284-2 | Window | 4 | boy | boy | 1.000 |
| Protocol/NEURAL-2/PWA/305-2 | Umbrella | 7 | boy | boy | 1.000 |
| Protocol/NEURAL-2/PWA/305-2 | Umbrella | 8 | umbrella | umbrella | 1.000 |
| Protocol/Richardson/PWA/richardson09a | Cat | 2 | dog;tree | tree | 0.500 |
| Protocol/Richardson/PWA/richardson09a | Cat | 19 | climb | climb | 1.000 |
| Protocol/Richardson/PWA/richardson09a | Sandwich | 6 | together | together | 1.000 |

## Interpretation

This is an n-best proxy, not a true beam dump. It tests whether repeated Whisper passes at different temperatures recover concepts omitted by the original 1-best pass. Strong union recovery would justify a beam/n-best clarification system; weak recovery means missing concepts usually are not latent in cheap ASR alternatives.
