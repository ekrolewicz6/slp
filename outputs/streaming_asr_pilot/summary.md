# Streaming ASR Concept Pilot

- Whisper model: `tiny.en`
- Sessions selected: 2
- Task rows attempted: 10
- Utterance clips attempted: 71
- Utterance clips transcribed: 71
- PAR audio transcribed: 4.80 minutes
- Mean concept F1 vs human CHAT: 0.200
- Mean concept recall vs human CHAT: 0.200
- Mean concept precision vs human CHAT: 0.200
- Correlation, ASR concept coverage vs WAB-AQ: -0.244
- Correlation, human concept coverage vs WAB-AQ: -0.244

## By Task

| task | n | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Cat | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Cinderella | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Sandwich | 2 | 0.000 | 0.000 | 0.000 | 0.042 | 0.000 |
| Umbrella | 2 | 0.500 | 0.500 | 0.500 | 0.050 | 0.050 |
| Window | 2 | 0.500 | 0.500 | 0.500 | 0.042 | 0.083 |

## Interpretation

This is a feasibility pilot, not a publishable ASR benchmark. The key test is whether storage-free PAR-only streaming can recover enough prompt-conditioned concepts to support fully automated discourse-state measurement. Low concept F1 would mean the next highest-yield work is aphasia-tuned ASR or forced alignment, not larger downstream language models.
