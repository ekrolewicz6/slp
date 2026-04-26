# Streaming ASR Concept Pilot

- Whisper model: `tiny.en`
- Sessions selected: 12
- Task rows attempted: 60
- Utterance clips attempted: 861
- Utterance clips transcribed: 861
- PAR audio transcribed: 64.21 minutes
- Mean concept F1 vs human CHAT: 0.749
- Mean concept recall vs human CHAT: 0.721
- Mean concept precision vs human CHAT: 0.823
- Correlation, ASR concept coverage vs WAB-AQ: 0.722
- Correlation, human concept coverage vs WAB-AQ: 0.808

## By Task

| task | n | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Cat | 12 | 0.818 | 0.795 | 0.917 | 0.444 | 0.507 |
| Cinderella | 12 | 0.635 | 0.603 | 0.705 | 0.372 | 0.461 |
| Sandwich | 12 | 0.757 | 0.722 | 0.819 | 0.396 | 0.493 |
| Umbrella | 12 | 0.833 | 0.830 | 0.851 | 0.492 | 0.533 |
| Window | 12 | 0.704 | 0.656 | 0.824 | 0.410 | 0.493 |

## Interpretation

This is a feasibility pilot, not a publishable ASR benchmark. The key test is whether storage-free PAR-only streaming can recover enough prompt-conditioned concepts to support fully automated discourse-state measurement. Low concept F1 would mean the next highest-yield work is aphasia-tuned ASR or forced alignment, not larger downstream language models.
