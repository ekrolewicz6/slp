# Reliable Change Thresholds

- Consecutive session pairs: 405
- Stable-WAB pairs for thresholding: 370
- Core content empirical 95% reliable-change threshold: 1.162 z
- Core content stable SD of delta: 0.600
- Specificity among stable-WAB pairs: 0.949
- Sensitivity among WAB movers >=5 AQ: 0.259
- Sensitivity among WAB movers >=10 AQ: 0.385
- Delta content vs delta WAB r: 0.178

## Thresholds

| metric | n_stable_pairs | stable_sd_delta | empirical_abs_q90 | empirical_abs_q95 | rci95_parametric |
| --- | --- | --- | --- | --- | --- |
| core_content_mean_z | 370 | 0.600 | 0.953 | 1.162 | 1.175 |
| content_mean_z | 370 | 0.598 | 0.955 | 1.162 | 1.173 |
| coverage_mean | 370 | 0.080 | 0.126 | 0.155 | 0.156 |
| tokens_mean | 370 | 46.996 | 72.936 | 105.167 | 92.112 |
| utts_mean | 370 | 6.392 | 10.629 | 14.340 | 12.527 |
| meanutt_mean | 370 | 1.198 | 1.958 | 2.312 | 2.348 |

## Classification Against WAB Change

| metric | threshold | stable_specificity | changed_sensitivity | large_changed_sensitivity | content_change_rate_all | speech_only_mover_rate | wab_changed_content_stable_rate | delta_r_wab |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| core_content_mean_z | 1.162 | 0.949 | 0.259 | 0.385 | 0.067 | 0.047 | 0.049 | 0.178 |
| content_mean_z | 1.162 | 0.949 | 0.259 | 0.385 | 0.067 | 0.047 | 0.049 | 0.177 |
| coverage_mean | 0.155 | 0.949 | 0.296 | 0.462 | 0.072 | 0.047 | 0.047 | 0.211 |
| tokens_mean | 105.167 | 0.949 | 0.000 | 0.000 | 0.047 | 0.047 | 0.067 | 0.053 |
| utts_mean | 14.340 | 0.949 | 0.037 | 0.077 | 0.049 | 0.047 | 0.064 | 0.022 |
| meanutt_mean | 2.312 | 0.949 | 0.074 | 0.154 | 0.054 | 0.047 | 0.062 | 0.119 |

## Subgroups

| group_col | group | n_pairs | mean_abs_delta_wab | mean_abs_delta_core_content | reliable_core_change_rate | delta_r_wab |
| --- | --- | --- | --- | --- | --- | --- |
| corpus | UNH | 19 | 6.711 | 0.654 | 0.158 | 0.433 |
| corpus | SCALE | 18 | 7.817 | 0.592 | 0.111 | 0.200 |
| subtype | Broca | 142 | 1.122 | 0.481 | 0.085 | 0.205 |
| subtype | Wernicke | 26 | 1.500 | 0.415 | 0.077 | 0.230 |
| subtype | Anomic | 119 | 0.581 | 0.527 | 0.076 | 0.188 |
| corpus | Kurland | 34 | 0.053 | 0.533 | 0.059 | -0.194 |
| corpus | Fridriksson-2 | 246 | 0.000 | 0.444 | 0.049 |  |
| subtype | Conduction | 64 | 0.998 | 0.512 | 0.047 | -0.008 |
| corpus | NEURAL-2 | 66 | 0.000 | 0.427 | 0.030 |  |
| subtype | NotAphasic | 35 | 0.240 | 0.426 | 0.029 | 0.286 |
