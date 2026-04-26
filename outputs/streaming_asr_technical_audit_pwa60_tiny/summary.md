# Streaming ASR Technical Audit

- Selected sessions: 60
- Sessions with any transcribed task: 52
- Session stream failures: 8
- Task rows below clip-success threshold 0.8: 5

## Metric Sensitivity

| sample | task_rows | sessions | clips_attempted | clips_transcribed | mean_clip_success_rate | mean_f1 | mean_recall | mean_precision | r_asr_coverage_wab | r_human_coverage_wab |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_transcribed_rows | 233.000 | 52.000 | 3809.000 | 3681.000 | 0.982 | 0.742 | 0.703 | 0.817 | 0.738 | 0.789 |
| clip_success_ge_0.8 | 228.000 | 51.000 | 3675.000 | 3675.000 | 1.000 | 0.755 | 0.717 | 0.830 | 0.732 | 0.787 |
| clip_success_lt_0.8 | 5.000 | 2.000 | 134.000 | 6.000 | 0.150 | 0.133 | 0.100 | 0.200 |  |  |

## Session Status By Corpus

| corpus | selected_sessions | streamed_sessions | failed_sessions | stream_success_rate |
| --- | --- | --- | --- | --- |
| UMD | 5 | 0 | 5 | 0.000 |
| Baycrest | 3 | 0 | 3 | 0.000 |
| Fridriksson-2 | 12 | 12 | 0 | 1.000 |
| Kurland | 10 | 10 | 0 | 1.000 |
| Richardson | 7 | 7 | 0 | 1.000 |
| Tucson | 5 | 5 | 0 | 1.000 |
| Adler | 4 | 4 | 0 | 1.000 |
| MSU | 3 | 3 | 0 | 1.000 |
| Williamson | 3 | 3 | 0 | 1.000 |
| BU | 1 | 1 | 0 | 1.000 |
| Fridriksson | 1 | 1 | 0 | 1.000 |
| NEURAL-2 | 1 | 1 | 0 | 1.000 |
| TAP | 1 | 1 | 0 | 1.000 |
| Thompson | 1 | 1 | 0 | 1.000 |
| UNH | 1 | 1 | 0 | 1.000 |
| Whiteside | 1 | 1 | 0 | 1.000 |
| Wozniak | 1 | 1 | 0 | 1.000 |

## Clip Failure Reasons

| failure_reason | count |
| --- | --- |
| empty_wav | 128 |

## Low Clip-Success Rows

| transcript_id | subtype | wab_aq | task | n_utterance_clips_attempted | n_utterance_clips_transcribed | clip_success_rate | failure_reasons | concept_f1_vs_human |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Protocol/Fridriksson-2/PWA/1012-3 | Broca | 40.600 | Cinderella | 44 | 0 | 0.000 | empty_wav:44 | 0.000 |
| Protocol/Fridriksson-2/PWA/1012-3 | Broca | 40.600 | Sandwich | 9 | 0 | 0.000 | empty_wav:9 | 0.000 |
| Protocol/Fridriksson-2/PWA/1012-5 | Broca | 40.600 | Window | 8 | 6 | 0.750 | empty_wav:2 | 0.667 |
| Protocol/Fridriksson-2/PWA/1012-5 | Broca | 40.600 | Cinderella | 62 | 0 | 0.000 | empty_wav:62 | 0.000 |
| Protocol/Fridriksson-2/PWA/1012-5 | Broca | 40.600 | Sandwich | 11 | 0 | 0.000 | empty_wav:11 | 0.000 |

## Interpretation

Technical media or slicing failures should not be interpreted as aphasic language-recognition failures. The thresholded sensitivity row estimates the ASR content result after excluding low-clip-success task rows, while failed sessions identify corpus/media sources that need extraction fixes.
