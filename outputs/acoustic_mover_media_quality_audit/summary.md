# Acoustic Mover Media-Quality Audit

- Acoustic-only stable-WAB pairs audited: 11
- Sessions streamed: 20

## Risk Summary

| audit_label | recording_artifact_risk | n |
| --- | --- | --- |
| likely_voice_pitch_state_change | high_recording_artifact_risk | 4 |
| likely_voice_pitch_state_change | medium_recording_artifact_risk | 2 |
| possible_recording_or_sample_artifact | high_recording_artifact_risk | 1 |
| possible_recording_or_sample_artifact | medium_recording_artifact_risk | 2 |
| quantity_or_transcription_shift | high_recording_artifact_risk | 2 |

## Pair-Level Technical Audit

| longitudinal_root | from_participant_id | to_participant_id | corpus | subtype | audit_label | recording_artifact_risk | recording_artifact_flags | delta_rms_dbfs | delta_active_rms_dbfs | delta_silence_fraction | delta_snr_proxy_db | from_status | to_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1012 | 1012-4 | 1012-5 | Fridriksson-2 | Broca | likely_voice_pitch_state_change | high_recording_artifact_risk | from_mostly_silence,to_mostly_silence,large_rms_shift | 14.248 | 5.632 | -0.221 | -0.832 | ok | ok |
| 1014 | 1014-2 | 1014-3 | Fridriksson-2 | Anomic | likely_voice_pitch_state_change | high_recording_artifact_risk | from_mostly_silence,to_mostly_silence,large_rms_shift | 14.306 | 6.204 | -0.268 | 9.085 | ok | ok |
| 1012 | 1012-2 | 1012-3 | Fridriksson-2 | Broca | likely_voice_pitch_state_change | high_recording_artifact_risk | from_mostly_silence,to_mostly_silence | -1.111 | -5.030 | -0.006 | 1.047 | ok | ok |
| 1046 | 1046-2 | 1046-3 | Fridriksson-2 | Anomic | likely_voice_pitch_state_change | medium_recording_artifact_risk | from_mostly_silence | -1.103 | -1.766 | -0.039 | -5.800 | ok | ok |
| 1012 | 1012-5 | 1012-6 | Fridriksson-2 | Broca | likely_voice_pitch_state_change | medium_recording_artifact_risk | from_mostly_silence | 8.729 | 6.131 | -0.207 | 6.084 | ok | ok |
| 1060 | 1060-2 | 1060-3 | Fridriksson-2 | Conduction | likely_voice_pitch_state_change | high_recording_artifact_risk | from_mostly_silence,to_mostly_silence | -1.812 | -1.748 | 0.015 | -3.461 | ok | ok |
| 1108 | 1108-1 | 1108-2 | Fridriksson-2 | Broca | possible_recording_or_sample_artifact | medium_recording_artifact_risk | large_dynamic_range_shift | 0.316 | -0.139 | -0.045 | -90.497 | ok | ok |
| 1060 | 1060-1 | 1060-2 | Fridriksson-2 | Conduction | possible_recording_or_sample_artifact | high_recording_artifact_risk | from_mostly_silence,to_mostly_silence | -0.783 | -0.467 | 0.014 | 5.901 | ok | ok |
| 1117 | 1117-5 | 1117-6 | Fridriksson-2 | Conduction | possible_recording_or_sample_artifact | medium_recording_artifact_risk | large_dynamic_range_shift | -1.640 | -0.748 | 0.091 | -97.346 | ok | ok |
| 1033 | 1033-4 | 1033-5 | Fridriksson-2 | Anomic | quantity_or_transcription_shift | high_recording_artifact_risk | from_mostly_silence,large_rms_shift,large_silence_shift | 11.083 | 7.799 | -0.358 | 1.047 | ok | ok |
| Kurland21 | Kurland21a | Kurland21b | Kurland | Anomic | quantity_or_transcription_shift | high_recording_artifact_risk | from_mostly_silence,to_mostly_silence | -2.936 | -2.655 | 0.012 | 2.196 | ok | ok |

## Interpretation

This audit only tests recording-level technical plausibility from the first 180 seconds of each media file. Low recording-artifact risk would not prove clinical acoustic change, and high risk does not prove artifact because the analyzed clip can include setup silence before the relevant utterances. But high risk weakens an acoustic-only mover claim until task-aligned audio is reviewed manually.
