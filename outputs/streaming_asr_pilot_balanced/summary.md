# Streaming ASR Concept Pilot

- Whisper model: `tiny.en`
- Sessions selected: 4
- Task rows attempted: 20
- Utterance clips attempted: 200
- Utterance clips transcribed: 200
- PAR audio transcribed: 14.20 minutes
- Mean concept F1 vs human CHAT: 0.833
- Mean concept recall vs human CHAT: 0.770
- Mean concept precision vs human CHAT: 0.938
- Correlation, ASR concept coverage vs WAB-AQ: 0.828
- Correlation, human concept coverage vs WAB-AQ: 0.931

## By Task

| task | n | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Cat | 4 | 0.813 | 0.712 | 1.000 | 0.375 | 0.604 |
| Cinderella | 4 | 0.794 | 0.708 | 0.938 | 0.300 | 0.417 |
| Sandwich | 4 | 0.700 | 0.659 | 0.750 | 0.438 | 0.500 |
| Umbrella | 4 | 0.969 | 0.944 | 1.000 | 0.500 | 0.550 |
| Window | 4 | 0.889 | 0.825 | 1.000 | 0.417 | 0.521 |

## Interpretation

This is a feasibility pilot, not a publishable ASR benchmark. The key test is whether storage-free PAR-only streaming can recover enough prompt-conditioned concepts to support fully automated discourse-state measurement. Low concept F1 would mean the next highest-yield work is aphasia-tuned ASR or forced alignment, not larger downstream language models.
