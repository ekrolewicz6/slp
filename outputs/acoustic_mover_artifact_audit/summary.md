# Acoustic-Only Stable-WAB Artifact Audit

- Acoustic-only stable-WAB examples audited: 11

## Label Summary

| audit_label | n |
| --- | --- |
| likely_voice_pitch_state_change | 6 |
| possible_recording_or_sample_artifact | 3 |
| quantity_or_transcription_shift | 2 |

## Audited Examples

| longitudinal_root | from_participant_id | to_participant_id | corpus | subtype | delta_wab_aq | delta_core_content_mean_z | no_token_acoustic_distance | voice_pitch_intensity_distance | reliable_families | audit_label | top_z_drivers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1012 | 1012-4 | 1012-5 | Fridriksson-2 | Broca | 0.000 | 0.734 | 2.602 | 2.700 | no_token_acoustic,voice_pitch_intensity | likely_voice_pitch_state_change | ac_jitter_local_std:+6.65z; ac_f0_std_mean:-3.87z; ac_f0_std_std:-3.81z; ac_f0_cv_mean:-3.79z; ac_f0_range_std:-3.68z; ac_f0_p90_std:-3.55z; ac_f0_p50_std:-3.34z; ac_f0_mean_std:-3.29z |
| 1014 | 1014-2 | 1014-3 | Fridriksson-2 | Anomic | 0.000 | 0.150 | 2.469 | 2.562 | no_token_acoustic,voice_pitch_intensity | likely_voice_pitch_state_change | ac_f0_p10_std:-6.05z; ac_f0_p50_std:-4.21z; ac_f0_p50_mean:-4.16z; ac_f0_mean_std:-4.13z; ac_jitter_local_mean:-3.97z; ac_f0_mean_mean:-3.92z; ac_f0_p90_mean:-3.83z; ac_f0_range_mean:-3.23z |
| 1012 | 1012-2 | 1012-3 | Fridriksson-2 | Broca | 0.000 | -0.095 | 2.178 | 2.260 | no_token_acoustic,voice_pitch_intensity | likely_voice_pitch_state_change | ac_f0_p50_std:-5.95z; ac_shimmer_local_std:-5.31z; ac_f0_p10_std:-4.68z; ac_f0_mean_std:-3.31z; ac_intensity_mean_std:-2.88z; ac_shimmer_local_mean:-1.86z; ac_f0_p50_mean:-1.68z; ac_n_utts_in_window:-1.68z |
| 1046 | 1046-2 | 1046-3 | Fridriksson-2 | Anomic | 0.000 | -0.462 | 1.548 | 1.560 | no_token_acoustic | likely_voice_pitch_state_change | ac_jitter_local_mean:+3.61z; ac_f0_p50_mean:+3.06z; ac_f0_mean_mean:+2.54z; ac_f0_p10_std:+2.31z; ac_f0_p90_mean:+1.98z; ac_jitter_local_std:+1.96z; ac_f0_range_mean:+1.80z; ac_voiced_fraction_std:-1.75z |
| 1012 | 1012-5 | 1012-6 | Fridriksson-2 | Broca | 0.000 | -0.517 | 1.545 | 1.603 | voice_pitch_intensity | likely_voice_pitch_state_change | ac_intensity_mean_std:+3.58z; ac_jitter_local_std:-3.27z; ac_f0_std_std:+2.52z; ac_f0_p90_std:+2.40z; ac_shimmer_local_std:+2.32z; ac_f0_cv_std:+2.30z; ac_f0_range_std:+2.30z; ac_jitter_local_mean:-1.95z |
| 1060 | 1060-2 | 1060-3 | Fridriksson-2 | Conduction | 0.000 | 0.338 | 1.529 | 1.587 | duration_intensity | likely_voice_pitch_state_change | ac_intensity_mean_std:-4.76z; ac_f0_mean_std:-2.39z; ac_f0_range_mean:-2.04z; ac_f0_p90_std:-2.03z; ac_f0_range_std:-2.01z; ac_f0_p50_std:-1.92z; ac_f0_p90_mean:-1.81z; ac_f0_std_std:-1.58z |
| 1108 | 1108-1 | 1108-2 | Fridriksson-2 | Broca | 0.000 | 0.723 | 1.463 | 1.517 | duration_intensity | possible_recording_or_sample_artifact | ac_intensity_std_mean:-5.79z; ac_intensity_mean_std:-3.09z; ac_intensity_std_std:-2.56z; ac_voiced_fraction_std:-1.59z; ac_intensity_mean_mean:+1.56z; ac_f0_mean_std:+1.09z; ac_f0_p50_std:+0.98z; ac_hnr_mean_mean:-0.91z |
| 1060 | 1060-1 | 1060-2 | Fridriksson-2 | Conduction | 0.000 | -0.167 | 1.131 | 1.172 | duration_intensity | possible_recording_or_sample_artifact | ac_intensity_mean_std:+4.96z; ac_hnr_mean_std:+1.33z; ac_hnr_mean_mean:+1.30z; ac_intensity_std_std:+1.15z; ac_f0_p10_std:+0.89z; ac_intensity_mean_mean:-0.88z; ac_f0_cv_std:-0.86z; ac_f0_p50_std:+0.85z |
| 1117 | 1117-5 | 1117-6 | Fridriksson-2 | Conduction | 0.000 | -0.583 | 0.902 | 0.933 | duration_intensity | possible_recording_or_sample_artifact | ac_intensity_std_std:-3.54z; ac_intensity_std_mean:-1.86z; ac_intensity_mean_std:-1.32z; ac_jitter_local_std:+0.83z; ac_f0_mean_std:-0.79z; ac_f0_p50_std:-0.74z; ac_f0_p10_mean:-0.71z; ac_f0_p50_mean:-0.63z |
| 1033 | 1033-4 | 1033-5 | Fridriksson-2 | Anomic | 0.000 | 0.177 | 0.510 | 0.517 | token_rate_count | quantity_or_transcription_shift | ac_n_utts_in_window:+2.32z; ac_n_voiced_utts:+2.17z; ac_f0_p10_std:+1.72z; ac_voiced_fraction_std:+1.00z; ac_f0_range_mean:-0.98z; ac_n_tokens_mean:-0.75z; ac_f0_std_mean:-0.61z; ac_f0_p90_mean:-0.59z |
| Kurland21 | Kurland21a | Kurland21b | Kurland | Anomic | 0.000 | -0.328 | 0.454 | 0.452 | token_rate_count | quantity_or_transcription_shift | ac_n_utts_in_window:-2.08z; ac_n_voiced_utts:-1.41z; ac_f0_mean_std:-0.99z; ac_f0_p50_std:-0.89z; ac_jitter_local_mean:-0.73z; ac_voiced_fraction_std:-0.70z; ac_f0_p10_std:-0.68z; ac_duration_s_std:+0.61z |

## Interpretation

This is a heuristic audit, not a clinical judgment. Cases labeled likely voice/pitch state change are the best candidates for manual audio review. Cases labeled possible recording/sample artifact should be treated as threats to the acoustic-state claim until reviewed.
