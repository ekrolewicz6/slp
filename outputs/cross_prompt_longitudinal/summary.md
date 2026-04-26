# Cross-Prompt Longitudinal Content State

- Sessions with WAB and >= 3 core tasks: 907
- Consecutive same-root pairs: 405
- Three-plus-session roots: 72

## Pair Change Correlations

| feature | n | r_delta_wab | r_abs_delta_wab |
| --- | --- | --- | --- |
| delta_content_mean_z | 405 | 0.177 | 0.227 |
| delta_core_content_mean_z | 405 | 0.178 | 0.236 |
| delta_coverage_mean | 405 | 0.211 | 0.260 |
| delta_tokens_mean | 405 | 0.053 | -0.039 |
| delta_meanutt_mean | 405 | 0.119 | 0.085 |
| stable_wab_lt5 | 378 | 0.461 | 0.061 |
| changed_wab_ge5 | 27 | 0.757 | 0.108 |
| changed_wab_ge10 | 13 | 1.000 | 0.143 |

## Early Content Change Predicting Later WAB Change

| target | n | mae | rmse | r |
| --- | --- | --- | --- | --- |
| later_delta_wab_aq | 72 | 2.618 | 5.423 | -0.009 |
