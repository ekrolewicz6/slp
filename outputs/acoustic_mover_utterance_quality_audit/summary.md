# Acoustic Mover Utterance-Aligned Quality Audit

- Acoustic-only stable-WAB pairs audited: 11
- Sessions streamed: 20

## Risk Summary

| audit_label | utterance_artifact_risk | n |
| --- | --- | --- |
| likely_voice_pitch_state_change | high_utterance_artifact_risk | 2 |
| likely_voice_pitch_state_change | low_utterance_artifact_risk | 1 |
| likely_voice_pitch_state_change | medium_utterance_artifact_risk | 3 |
| possible_recording_or_sample_artifact | medium_utterance_artifact_risk | 3 |
| quantity_or_transcription_shift | high_utterance_artifact_risk | 2 |

## Pair-Level Utterance-Aligned Audit

| longitudinal_root | from_participant_id | to_participant_id | subtype | audit_label | utterance_artifact_risk | utterance_artifact_flags | delta_par_rms_dbfs | delta_par_silence_fraction | delta_par_snr_proxy_db | from_par_duration_s | to_par_duration_s | from_status | to_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1012 | 1012-4 | 1012-5 | Broca | likely_voice_pitch_state_change | high_utterance_artifact_risk | from_par_mostly_silence,to_par_mostly_silence,large_par_rms_shift | 12.311 | -0.239 | -3.403 | 41.432 | 16.712 | ok | ok |
| 1014 | 1014-2 | 1014-3 | Anomic | likely_voice_pitch_state_change | high_utterance_artifact_risk | from_par_mostly_silence,large_par_rms_shift,large_par_silence_shift | 14.729 | -0.306 | 9.818 | 258.366 | 321.170 | ok | ok |
| 1012 | 1012-2 | 1012-3 | Broca | likely_voice_pitch_state_change | medium_utterance_artifact_risk | from_par_mostly_silence,to_par_mostly_silence | -2.219 | -0.008 | 1.001 | 128.404 | 23.377 | ok | ok |
| 1046 | 1046-2 | 1046-3 | Anomic | likely_voice_pitch_state_change | medium_utterance_artifact_risk | from_par_mostly_silence,to_par_mostly_silence | -1.356 | -0.020 | -4.828 | 513.376 | 475.481 | ok | ok |
| 1012 | 1012-5 | 1012-6 | Broca | likely_voice_pitch_state_change | low_utterance_artifact_risk | from_par_mostly_silence | 5.444 | -0.065 | 4.779 | 16.712 | 37.461 | ok | ok |
| 1060 | 1060-2 | 1060-3 | Conduction | likely_voice_pitch_state_change | medium_utterance_artifact_risk | from_par_mostly_silence,to_par_mostly_silence | 5.616 | -0.086 | 1.615 | 358.538 | 256.556 | ok | ok |
| 1108 | 1108-1 | 1108-2 | Broca | possible_recording_or_sample_artifact | medium_utterance_artifact_risk | large_par_dynamic_range_shift | -0.857 | -0.059 | -93.224 | 214.861 | 264.143 | ok | ok |
| 1060 | 1060-1 | 1060-2 | Conduction | possible_recording_or_sample_artifact | medium_utterance_artifact_risk | from_par_mostly_silence,to_par_mostly_silence | 1.563 | -0.025 | 13.959 | 275.298 | 358.538 | ok | ok |
| 1117 | 1117-5 | 1117-6 | Conduction | possible_recording_or_sample_artifact | medium_utterance_artifact_risk | large_par_dynamic_range_shift | 0.880 | -0.002 | -17.241 | 371.477 | 386.973 | ok | ok |
| 1033 | 1033-4 | 1033-5 | Anomic | quantity_or_transcription_shift | high_utterance_artifact_risk | from_par_mostly_silence,large_par_rms_shift,large_par_silence_shift | 10.469 | -0.366 | -1.730 | 291.096 | 379.525 | ok | ok |
| Kurland21 | Kurland21a | Kurland21b | Anomic | quantity_or_transcription_shift | high_utterance_artifact_risk | from_stream_not_ok,to_par_low_dynamic_range,to_par_mostly_silence |  |  |  |  | 247.459 | span_too_long | ok |

## Interpretation

This rerun uses transcript PAR time marks rather than the leading media clip. It is a stronger technical screen for the acoustic-only mover claim, but it still does not replace manual clinical audio review.
