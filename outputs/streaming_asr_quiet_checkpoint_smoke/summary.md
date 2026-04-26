# Streaming ASR Concept Pilot

- Whisper model: `tiny.en`
- Sessions selected: 1
- Task rows attempted: 5
- Utterance clips attempted: 30
- Utterance clips transcribed: 30
- PAR audio transcribed: 1.96 minutes
- Mean concept F1 vs human CHAT: 0.800
- Mean concept recall vs human CHAT: 0.800
- Mean concept precision vs human CHAT: 0.800
- Correlation, ASR concept coverage vs WAB-AQ: nan
- Correlation, human concept coverage vs WAB-AQ: nan

## By Task

| task | n | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Cat | 1 | 1.000 | 1.000 | 1.000 | 0.083 | 0.083 |
| Cinderella | 1 | 1.000 | 1.000 | 1.000 | 0.067 | 0.067 |
| Sandwich | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Umbrella | 1 | 1.000 | 1.000 | 1.000 | 0.100 | 0.100 |
| Window | 1 | 1.000 | 1.000 | 1.000 | 0.250 | 0.250 |

## Interpretation

This is a feasibility pilot, not a publishable ASR benchmark. The key test is whether storage-free PAR-only streaming can recover enough prompt-conditioned concepts to support fully automated discourse-state measurement. Low concept F1 would mean the next highest-yield work is aphasia-tuned ASR or forced alignment, not larger downstream language models.
