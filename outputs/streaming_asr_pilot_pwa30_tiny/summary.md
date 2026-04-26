# Streaming ASR Concept Pilot

- Whisper model: `tiny.en`
- Sessions selected: 30
- Task rows attempted: 150
- Utterance clips attempted: 2602
- Utterance clips transcribed: 2602
- PAR audio transcribed: 202.75 minutes
- Mean concept F1 vs human CHAT: 0.764
- Mean concept recall vs human CHAT: 0.718
- Mean concept precision vs human CHAT: 0.859
- Correlation, ASR concept coverage vs WAB-AQ: 0.713
- Correlation, human concept coverage vs WAB-AQ: 0.761

## By Task

| task | n | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Cat | 30 | 0.764 | 0.716 | 0.856 | 0.442 | 0.550 |
| Cinderella | 30 | 0.727 | 0.682 | 0.830 | 0.396 | 0.478 |
| Sandwich | 30 | 0.749 | 0.689 | 0.872 | 0.411 | 0.525 |
| Umbrella | 30 | 0.821 | 0.779 | 0.902 | 0.513 | 0.590 |
| Window | 30 | 0.760 | 0.724 | 0.834 | 0.392 | 0.444 |

## Interpretation

This is a feasibility pilot, not a publishable ASR benchmark. The key test is whether storage-free PAR-only streaming can recover enough prompt-conditioned concepts to support fully automated discourse-state measurement. Low concept F1 would mean the next highest-yield work is aphasia-tuned ASR or forced alignment, not larger downstream language models.
