# Streaming ASR Concept Pilot

- Whisper model: `base.en`
- Sessions selected: 4
- Task rows attempted: 20
- Utterance clips attempted: 200
- Utterance clips transcribed: 200
- PAR audio transcribed: 14.20 minutes
- Mean concept F1 vs human CHAT: 0.855
- Mean concept recall vs human CHAT: 0.794
- Mean concept precision vs human CHAT: 0.950
- Correlation, ASR concept coverage vs WAB-AQ: 0.849
- Correlation, human concept coverage vs WAB-AQ: 0.931

## By Task

| task | n | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Cat | 4 | 0.857 | 0.788 | 1.000 | 0.438 | 0.604 |
| Cinderella | 4 | 0.889 | 0.812 | 1.000 | 0.333 | 0.417 |
| Sandwich | 4 | 0.636 | 0.557 | 0.750 | 0.375 | 0.500 |
| Umbrella | 4 | 0.950 | 0.909 | 1.000 | 0.475 | 0.550 |
| Window | 4 | 0.942 | 0.906 | 1.000 | 0.458 | 0.521 |

## Interpretation

This is a feasibility pilot, not a publishable ASR benchmark. The key test is whether storage-free PAR-only streaming can recover enough prompt-conditioned concepts to support fully automated discourse-state measurement. Low concept F1 would mean the next highest-yield work is aphasia-tuned ASR or forced alignment, not larger downstream language models.
