# Streaming ASR Concept Pilot

- Whisper model: `tiny.en`
- Sessions selected: 12
- Task rows attempted: 60
- Utterance clips attempted: 739
- Utterance clips transcribed: 739
- PAR audio transcribed: 54.59 minutes
- Mean concept F1 vs human CHAT: 0.783
- Mean concept recall vs human CHAT: 0.732
- Mean concept precision vs human CHAT: 0.873
- Correlation, ASR concept coverage vs WAB-AQ: 0.722
- Correlation, human concept coverage vs WAB-AQ: 0.764

## By Task

| task | n | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Cat | 12 | 0.818 | 0.771 | 0.900 | 0.368 | 0.444 |
| Cinderella | 12 | 0.735 | 0.683 | 0.812 | 0.322 | 0.383 |
| Sandwich | 12 | 0.782 | 0.713 | 0.900 | 0.410 | 0.507 |
| Umbrella | 12 | 0.879 | 0.858 | 0.931 | 0.442 | 0.483 |
| Window | 12 | 0.703 | 0.635 | 0.823 | 0.271 | 0.361 |

## Interpretation

This is a feasibility pilot, not a publishable ASR benchmark. The key test is whether storage-free PAR-only streaming can recover enough prompt-conditioned concepts to support fully automated discourse-state measurement. Low concept F1 would mean the next highest-yield work is aphasia-tuned ASR or forced alignment, not larger downstream language models.
