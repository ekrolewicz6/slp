# Selective Reconstruction Policy

## Policy Tradeoffs

| policy | rewrite_rate | mean_policy_gain_frac | total_gain_captured_frac | positive_gain_recall | unnecessary_rewrite_rate | rewritten_unknown_intent_rate |
| --- | --- | --- | --- | --- | --- | --- |
| rewrite_all | 1.000 | 0.017 | 1.000 | 1.000 | 0.851 | 0.214 |
| oracle_gain_only | 0.149 | 0.017 | 1.000 | 1.000 | 0.000 | 0.546 |
| rewrite_any_error | 0.459 | 0.017 | 0.992 | 0.989 | 0.680 | 0.465 |
| rewrite_known_target | 0.390 | 0.017 | 0.984 | 0.978 | 0.626 | 0.417 |
| oracle_safe_gain_only | 0.068 | 0.007 | 0.410 | 0.454 | 0.000 | 0.000 |
| rewrite_known_no_unknown | 0.227 | 0.007 | 0.395 | 0.435 | 0.715 | 0.000 |
| abstain_unknown_rewrite_known | 0.227 | 0.007 | 0.395 | 0.435 | 0.715 | 0.000 |
| rewrite_phonological_known | 0.151 | 0.005 | 0.297 | 0.315 | 0.689 | 0.000 |
| preserve_raw | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Best Clinical-Signal Models

| subset | setup | n | n_patients | mae | r |
| --- | --- | --- | --- | --- | --- |
| all_noncontrol_wab | rewrite_any_error:policy_content+error_profile+task | 4012 | 851 | 9.406 | 0.817 |
| all_noncontrol_wab | rewrite_known_target:policy_content+error_profile+task | 4012 | 851 | 9.405 | 0.817 |
| all_noncontrol_wab | rewrite_all:policy_content+error_profile+task | 4012 | 851 | 9.416 | 0.817 |
| all_noncontrol_wab | oracle_gain_only:policy_content+error_profile+task | 4012 | 851 | 9.420 | 0.817 |
| all_noncontrol_wab | rewrite_phonological_known:policy_content+error_profile+task | 4012 | 851 | 9.476 | 0.816 |
| all_noncontrol_wab | rewrite_known_no_unknown:policy_content+error_profile+task | 4012 | 851 | 9.489 | 0.815 |
| all_noncontrol_wab | abstain_unknown_rewrite_known:policy_content+error_profile+task | 4012 | 851 | 9.489 | 0.815 |
| all_noncontrol_wab | oracle_safe_gain_only:policy_content+error_profile+task | 4012 | 851 | 9.495 | 0.814 |
| high_bottleneck_error_q75 | rewrite_known_target:policy_content+error_profile+task | 1006 | 403 | 9.745 | 0.759 |
| high_bottleneck_error_q75 | oracle_gain_only:policy_content+error_profile+task | 1006 | 403 | 9.795 | 0.758 |
| high_bottleneck_error_q75 | rewrite_all:policy_content+error_profile+task | 1006 | 403 | 9.818 | 0.757 |
| high_bottleneck_error_q75 | rewrite_any_error:policy_content+error_profile+task | 1006 | 403 | 9.818 | 0.757 |
| high_bottleneck_error_q75 | oracle_gain_only:policy_content+task | 1006 | 403 | 10.121 | 0.741 |
| high_bottleneck_error_q75 | rewrite_known_no_unknown:policy_content+error_profile+task | 1006 | 403 | 10.106 | 0.738 |
| high_bottleneck_error_q75 | abstain_unknown_rewrite_known:policy_content+error_profile+task | 1006 | 403 | 10.106 | 0.738 |
| high_bottleneck_error_q75 | rewrite_known_target:policy_content+task | 1006 | 403 | 10.144 | 0.738 |
| unknown_intent_error | oracle_gain_only:policy_content+error_profile+task | 1379 | 560 | 10.343 | 0.750 |
| unknown_intent_error | rewrite_all:policy_content+error_profile+task | 1379 | 560 | 10.329 | 0.747 |
| unknown_intent_error | rewrite_any_error:policy_content+error_profile+task | 1379 | 560 | 10.329 | 0.747 |
| unknown_intent_error | rewrite_known_target:policy_content+error_profile+task | 1379 | 560 | 10.357 | 0.747 |
| unknown_intent_error | preserve_raw:policy_content+error_profile+task | 1379 | 560 | 10.447 | 0.742 |
| unknown_intent_error | rewrite_known_no_unknown:policy_content+error_profile+task | 1379 | 560 | 10.447 | 0.742 |
| unknown_intent_error | rewrite_phonological_known:policy_content+error_profile+task | 1379 | 560 | 10.447 | 0.742 |
| unknown_intent_error | abstain_unknown_rewrite_known:policy_content+error_profile+task | 1379 | 560 | 10.447 | 0.742 |

## Interpretation

The safest deployable policy is not necessarily the policy with the highest oracle gain. A clinically useful assistant should maximize known-target content recovery while minimizing rewrites in unknown-intent segments, where the chance of plausible hallucination is highest.
