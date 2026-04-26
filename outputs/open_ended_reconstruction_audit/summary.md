# Open-Ended Reconstruction Audit

- Open-ended PAR utterances: 66321
- Sessions: 679
- Patients/roots: 533
- Corpora: 28
- Utterances with any CHAT error tag: 4335
- Safe known-target rewrite candidates: 3094
- Utterances needing abstain/clarification: 1010

## Policy Buckets

| policy_bucket | utterances | frac_utterances |
| --- | --- | --- |
| safe_known_rewrite_candidate | 3094 | 0.047 |
| needs_abstain_or_clarification | 1010 | 0.015 |
| any_error_tag | 4335 | 0.065 |

## WAB Correlations

| signal | n | r_wab_aq |
| --- | --- | --- |
| unknown_intent_error_count_rate_100 | 578 | -0.360 |
| abstain_or_clarify_utterance_frac | 578 | -0.357 |
| target_token_gain_rate_100 | 578 | -0.327 |
| error_total_rate_100 | 578 | -0.309 |
| known_reconstructable_error_count_rate_100 | 578 | -0.190 |
| safe_known_rewrite_utterance_frac | 578 | -0.038 |
| n_open_ended_utterances | 578 | 0.268 |
| observed_tokens | 578 | 0.318 |

## By Subtype

| subtype | sessions | mean_wab | mean_open_ended_utts | error_rate_100 | known_rewrite_rate_100 | unknown_intent_rate_100 | safe_rewrite_utterance_frac | abstain_or_clarify_frac |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Global | 4 | 22.200 | 50.750 | 7.050 | 4.604 | 2.447 | 0.069 | 0.085 |
| Broca | 138 | 51.237 | 52.812 | 3.838 | 2.535 | 1.249 | 0.064 | 0.026 |
| Wernicke | 38 | 53.321 | 85.895 | 2.078 | 0.997 | 0.942 | 0.048 | 0.055 |
| Conduction | 94 | 70.132 | 108.638 | 2.406 | 1.470 | 0.783 | 0.067 | 0.038 |
| TransSensory | 2 | 60.250 | 77.000 | 2.067 | 1.440 | 0.626 | 0.068 | 0.035 |
| TransMotor | 17 | 71.212 | 74.000 | 3.513 | 3.116 | 0.283 | 0.104 | 0.015 |
| Anomic | 206 | 85.468 | 90.010 | 1.569 | 1.252 | 0.217 | 0.057 | 0.012 |
| NotAphasic | 115 | 96.436 | 192.017 | 0.543 | 0.489 | 0.018 | 0.036 | 0.001 |
| Isolation | 1 | 32.300 | 18.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## By Corpus

| corpus | sessions | mean_wab | mean_open_ended_utts | unknown_intent_rate_100 | safe_rewrite_utterance_frac |
| --- | --- | --- | --- | --- | --- |
| NEURAL-2 | 130 | 84.123 | 191.600 | 0.278 | 0.055 |
| Kurland | 108 | 71.900 | 49.370 | 0.334 | 0.035 |
| SCALE | 55 | 69.407 | 70.073 | 0.579 | 0.052 |
| NEURAL | 48 |  | 102.958 | 0.468 | 0.058 |
| UNH | 35 | 67.712 | 66.514 | 1.175 | 0.056 |
| Williamson | 26 | 75.200 | 74.154 | 0.523 | 0.097 |
| Adler | 25 | 69.672 | 93.360 | 1.589 | 0.070 |
| Kansas | 23 | 62.157 | 50.870 | 0.459 | 0.057 |
| Tucson | 23 | 68.405 | 63.391 | 0.779 | 0.055 |
| Richardson | 21 | 76.052 | 107.143 | 0.002 | 0.004 |
| Whiteside | 20 | 73.810 | 82.750 | 0.609 | 0.061 |
| TAP | 19 | 63.658 | 59.789 | 1.044 | 0.080 |
| Elman | 17 | 71.665 | 77.588 | 0.651 | 0.027 |
| UMD | 16 | 76.050 | 72.438 | 0.921 | 0.040 |
| Fridriksson | 16 | 72.988 | 107.750 | 1.284 | 0.124 |
| Thompson | 16 | 84.169 | 92.438 | 0.147 | 0.077 |
| MSU | 15 | 75.800 | 103.867 | 0.814 | 0.088 |
| ACWT | 11 | 69.355 | 62.273 | 0.330 | 0.096 |
| Baycrest | 11 | 77.060 | 51.182 | 0.342 | 0.024 |
| BU | 11 | 71.010 | 126.000 | 0.493 | 0.042 |
| Wozniak | 7 | 81.700 | 104.714 | 0.049 | 0.039 |
| Wright | 7 | 69.886 | 73.857 | 1.080 | 0.044 |
| TCU | 6 | 76.917 | 157.000 | 0.186 | 0.052 |
| CMU | 5 | 73.950 | 59.600 | 0.000 | 0.191 |
| Kempler | 3 | 64.600 | 42.667 | 0.617 | 0.062 |
| TCU-bi | 2 | 71.400 | 171.000 | 0.090 | 0.014 |
| Garrett | 2 | 72.950 | 67.500 | 1.621 | 0.168 |
| STAR | 1 | 75.100 | 58.000 | 1.695 | 0.172 |

## Interpretation

This reproduces the open-ended interview setting used by recent GenAI aphasia reconstruction work, but separates utterances into safe known-target rewrite candidates versus unknown-intent cases that should trigger abstention or clarification. A useful assistant should not treat all CHAT error tags as equally reconstructable.
