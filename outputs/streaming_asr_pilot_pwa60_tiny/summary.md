# Streaming ASR Concept Pilot

- Whisper model: `tiny.en`
- Sessions selected: 60
- Task rows attempted: 233
- Utterance clips attempted: 3809
- Utterance clips transcribed: 3681
- PAR audio transcribed: 255.57 minutes
- Mean concept F1 vs human CHAT: 0.742
- Mean concept recall vs human CHAT: 0.703
- Mean concept precision vs human CHAT: 0.817
- Correlation, ASR concept coverage vs WAB-AQ: 0.738
- Correlation, human concept coverage vs WAB-AQ: 0.789

## By Task

| task | n | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Cat | 40 | 0.812 | 0.768 | 0.884 | 0.429 | 0.500 |
| Cinderella | 51 | 0.658 | 0.619 | 0.743 | 0.271 | 0.337 |
| Sandwich | 50 | 0.753 | 0.699 | 0.851 | 0.300 | 0.373 |
| Umbrella | 40 | 0.813 | 0.794 | 0.855 | 0.490 | 0.520 |
| Window | 52 | 0.704 | 0.670 | 0.776 | 0.292 | 0.337 |

## Interpretation

This is a feasibility pilot, not a publishable ASR benchmark. The key test is whether storage-free PAR-only streaming can recover enough prompt-conditioned concepts to support fully automated discourse-state measurement. Low concept F1 would mean the next highest-yield work is aphasia-tuned ASR or forced alignment, not larger downstream language models.
