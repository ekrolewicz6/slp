# Dryad EMT-SF DLD Treatment Pilot

Dataset: Dryad DOI `10.5061/dryad.sj3tx96g9`, "Maximizing outcomes for preschoolers with developmental language disorders."

## Data Inventory

- Long-format rows: 704
- Unique shared participant IDs: 101
- Baseline randomized analysis participants: 98
- EMT-SF / control at baseline: 50 / 48

### Event Rows

| redcap_event_name | rows | participants | month |
| --- | --- | --- | --- |
| t30_arm_1 | 98 | 98 | 30 |
| t33_arm_1 | 101 | 101 | 33 |
| t36_arm_1 | 101 | 101 | 36 |
| t39_arm_1 | 101 | 101 | 39 |
| t42_arm_1 | 101 | 101 | 42 |
| t45_arm_1 | 101 | 101 | 45 |
| t49_arm_1 | 101 | 101 | 49 |

### Baseline Group Balance

| n | mean_age_m | mean_pls5_total | mean_lan_ndw | mean_lan_pps | group |
| --- | --- | --- | --- | --- | --- |
| 48 | 30.047 | 80.750 | 13.767 | 5.372 | Control |
| 50 | 29.893 | 80.480 | 14.000 | 5.091 | EMT-SF |

### Key Variable Missingness

| variable | nonmissing_n | missing_n | nonmissing_rate |
| --- | --- | --- | --- |
| t30_lan_c_ndw | 87 | 11 | 0.888 |
| t30_lan_30_c_pps | 87 | 11 | 0.888 |
| t36_ppvt5_ss | 88 | 10 | 0.898 |
| t36_evt3_ss | 88 | 10 | 0.898 |
| t42_spelt2_rs | 90 | 8 | 0.918 |
| t42_tegi_score | 90 | 8 | 0.918 |
| t49_ppvt5_ss | 83 | 15 | 0.847 |
| t49_evt3_ss | 84 | 14 | 0.857 |
| t49_spelt2_rs | 89 | 9 | 0.908 |
| t49_tegi_score | 87 | 11 | 0.888 |
| t49_celfp3_ss | 92 | 6 | 0.939 |
| t49_rbsna_total | 83 | 15 | 0.847 |

## Primary Treatment Contrasts

Transparent OLS models are used here rather than exact lavaan SEM replication. Vocabulary models adjust for baseline LAN NDW; grammar models adjust for baseline primed productive syntax.

| family | outcome | n | n_emt_sf | n_control | adjusted_tx_effect | adjusted_tx_ci_lo | adjusted_tx_ci_hi | adjusted_tx_p | adjusted_cohens_d_resid | model_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary_vocabulary | T36 vocabulary composite z | 88 | 44 | 44 | 0.281 | -0.017 | 0.580 | 0.064 | 0.400 | 0.363 |
| primary_vocabulary | T36 PPVT-5 SS | 88 | 44 | 44 | 4.449 | -0.098 | 8.996 | 0.055 | 0.415 | 0.142 |
| primary_vocabulary | T36 EVT-3 SS | 88 | 44 | 44 | 2.278 | -1.872 | 6.429 | 0.278 | 0.233 | 0.476 |
| primary_grammar | T42 grammar composite z | 90 | 44 | 46 | 0.421 | 0.089 | 0.752 | 0.013 | 0.533 | 0.215 |
| primary_grammar | T42 SPELT-P2 raw | 90 | 44 | 46 | 2.825 | 0.289 | 5.360 | 0.029 | 0.468 | 0.230 |
| primary_grammar | T42 SPELT-P2 SS | 90 | 44 | 46 | 6.194 | 0.902 | 11.486 | 0.022 | 0.492 | 0.233 |
| primary_grammar | T42 TEGI composite | 90 | 44 | 46 | 9.941 | 0.510 | 19.372 | 0.039 | 0.443 | 0.114 |

## Exploratory T49 Outcomes

| outcome | n | adjusted_tx_effect | adjusted_tx_ci_lo | adjusted_tx_ci_hi | adjusted_tx_p | adjusted_cohens_d_resid |
| --- | --- | --- | --- | --- | --- | --- |
| T49 vocabulary composite z | 86 | 0.400 | 0.048 | 0.752 | 0.026 | 0.489 |
| T49 grammar composite z | 89 | 0.495 | 0.154 | 0.836 | 0.005 | 0.614 |
| T49 CELF-P3 SS | 92 | 5.217 | -0.063 | 10.497 | 0.053 | 0.411 |
| T49 Renfrew Bus Story | 83 | 0.799 | -1.355 | 2.953 | 0.462 | 0.162 |

## Language-Sample Follow-Up Effects

| outcome | n | adjusted_tx_effect | adjusted_tx_ci_lo | adjusted_tx_ci_hi | adjusted_tx_p | adjusted_cohens_d_resid |
| --- | --- | --- | --- | --- | --- | --- |
| T33 lan_c_subjects_d | 86 | 1.390 | 0.107 | 2.672 | 0.034 | 0.465 |
| T39 lan_c_subjects_d | 92 | -2.094 | -4.353 | 0.165 | 0.069 | -0.384 |
| T33 lan_c_clause_utt | 86 | 0.054 | -0.004 | 0.112 | 0.069 | 0.399 |
| T36 lan_c_ndw | 88 | 3.938 | -0.544 | 8.420 | 0.084 | 0.372 |
| T33 lan_c_verbs_d | 86 | 1.101 | -0.195 | 2.397 | 0.095 | 0.364 |
| T36 lan_c_subjects_d | 88 | 1.435 | -0.336 | 3.206 | 0.111 | 0.344 |
| T42 lan_c_ndw | 90 | 4.431 | -1.647 | 10.509 | 0.151 | 0.306 |
| T33 lan_c_ndw | 86 | 2.150 | -1.379 | 5.679 | 0.229 | 0.261 |
| T45 lan_c_ndw | 90 | 3.815 | -2.677 | 10.307 | 0.246 | 0.247 |
| T36 lan_c_clause_utt | 88 | 0.046 | -0.036 | 0.128 | 0.264 | 0.240 |
| T36 lan_c_verbs_d | 88 | 1.006 | -0.871 | 2.883 | 0.290 | 0.227 |
| T39 lan_c_clause_utt | 92 | -0.038 | -0.151 | 0.074 | 0.501 | -0.141 |

## Baseline Moderator Screen

| outcome | moderator | n | interaction_coef | interaction_p | interaction_q_bh | interaction_p_maxT_family | main_tx_effect_at_mean_moderator |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T49 grammar composite z | CBCL internalizing | 89 | 0.461 | 0.007 | 0.520 | 0.070 | 0.504 |
| T42 grammar composite z | paternal speech/language/learning history | 85 | -0.421 | 0.014 | 0.550 | 0.180 | 0.473 |
| T42 grammar composite z | baseline FOCUS | 90 | 0.356 | 0.031 | 0.699 | 0.367 | 0.356 |
| T42 grammar composite z | child female | 90 | -0.328 | 0.049 | 0.699 | 0.509 | 0.424 |
| T42 grammar composite z | CBCL internalizing | 90 | 0.323 | 0.050 | 0.699 | 0.509 | 0.423 |
| T49 vocabulary composite z | child female | 86 | -0.338 | 0.056 | 0.699 | 0.315 | 0.398 |
| T49 grammar composite z | CBCL withdrawn | 89 | 0.322 | 0.089 | 0.699 | 0.609 | 0.578 |
| T42 grammar composite z | CBCL withdrawn | 90 | 0.295 | 0.109 | 0.699 | 0.808 | 0.504 |
| T49 grammar composite z | PLS-5 expressive communication | 89 | 0.278 | 0.112 | 0.699 | 0.733 | 0.490 |
| T49 grammar composite z | PLS-5 total language | 89 | 0.276 | 0.112 | 0.699 | 0.733 | 0.501 |
| T49 vocabulary composite z | PLS-5 expressive communication | 86 | 0.289 | 0.119 | 0.699 | 0.659 | 0.400 |
| T42 grammar composite z | maternal speech/language/learning history | 89 | -0.268 | 0.120 | 0.699 | 0.832 | 0.438 |

## Interpretation

This is the first local dataset that directly links a randomized DLD intervention to later outcomes. It is therefore more clinically relevant than the previous CHILDES-only DLD work. The treatment signal is strongest for grammar-related outcomes, especially the T42 grammar composite and SPELT-P2. The vocabulary signal at T36 is weaker in these transparent Python models.

The heterogeneous-response screen should be treated as exploratory. Robust moderator found after BH and max-T controls: `False`. The current shared dataset is too small to claim treatment matching, but it is exactly the kind of schema the project needs: baseline language sample variables, randomized treatment, repeated outcomes, and enough covariates to ask who benefits.

Main limitation: the dataset contains aggregate REDCap variables, not raw transcripts/audio. It can validate treatment-response questions, but it cannot yet connect our richer CLAN/TalkBank state representation directly to EMT-SF dose, target selection, or session-level change.
