# Streaming ASR Concept Pilot

- Whisper model: `tiny.en`
- Sessions selected: 1
- Task rows attempted: 2
- Utterance clips attempted: 10
- Utterance clips transcribed: 10
- PAR audio transcribed: 0.64 minutes
- Mean concept F1 vs human CHAT: 1.000
- Mean concept recall vs human CHAT: 1.000
- Mean concept precision vs human CHAT: 1.000
- Correlation, ASR concept coverage vs WAB-AQ: nan
- Correlation, human concept coverage vs WAB-AQ: nan

## By Task

| task | n | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Umbrella | 1 | 1.000 | 1.000 | 1.000 | 0.100 | 0.100 |
| Window | 1 | 1.000 | 1.000 | 1.000 | 0.250 | 0.250 |

## Interpretation

This is a feasibility pilot, not a publishable ASR benchmark. The key test is whether storage-free PAR-only streaming can recover enough prompt-conditioned concepts to support fully automated discourse-state measurement. Low concept F1 would mean the next highest-yield work is aphasia-tuned ASR or forced alignment, not larger downstream language models.
