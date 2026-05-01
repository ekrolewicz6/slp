# DLD Conflict Mechanism Audit

This audit summarizes the 15 DLD/TD conflict review cases without publishing raw transcript text.

- Cases audited: 15
- Adequate-sample cases: 9
- Single-window/single-transcript cases: 14
- Cases with language risk at least 0.25 above MLU risk: 11
- Cases with language risk at least 0.35 above corpus-age risk: 13

## Mechanism Summary

| mechanism_label | n | mean_language_minus_mlu | mean_language_minus_corpus | mean_output_complexity_z | mean_syntax_argument_z | mean_lexical_predicate_z | sample_flags | coverage_flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sample_constrained_language_risk | 6 | 0.421 | 0.366 | -0.421 | -0.336 | -0.482 | low_word_count | single_transcript; single_window,single_transcript |
| possible_hidden_td_language_risk | 4 | 0.405 | 0.553 | -0.962 | -0.627 | -0.664 | adequate_sample | single_window,single_transcript |
| language_risk_not_corpus_prior | 2 | 0.201 | 0.652 | -2.686 | -1.024 | -1.234 | adequate_sample | single_window,single_transcript |
| non_mlu_language_state_signal | 2 | 0.500 | 0.679 | -2.083 | -0.812 | -1.693 | adequate_sample | single_window,single_transcript |
| low_output_mlu_aligned | 1 | 0.078 | 0.658 | -2.614 | -1.428 | -1.792 | adequate_sample | single_window,single_transcript |

## Axis Summary By Review Priority

| review_priority | n | mean_language_minus_mlu | mean_language_minus_corpus | mean_output_complexity_z | mean_syntax_argument_z | mean_lexical_predicate_z | mean_fluency_repair_z |
| --- | --- | --- | --- | --- | --- | --- | --- |
| highest_clinical_fairness_review | 3 | 0.341 | 0.476 | -0.924 | -0.716 | -1.015 | -0.183 |
| highest_scientific_review | 12 | 0.384 | 0.525 | -1.313 | -0.623 | -0.846 | -0.153 |

## Case-Level Mechanism Index

| case_id | compact_participant_id | corpus | screen_label | age_min | task_bucket | review_priority | mechanism_label | sample_quality_flag | coverage_flag | language_minus_mlu | language_minus_corpus | output_complexity_z | syntax_argument_structure_z | lexical_predicate_z | top_feature_shifts_vs_td |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DLD-CONFLICT-001 | TD/452 | ENNI | TD | 48.400 | narrative_story | highest_clinical_fairness_review | possible_hidden_td_language_risk | adequate_sample | single_window,single_transcript | 0.233 | 0.784 | -2.288 | -1.386 | -2.995 | rel_SUBJ_frac:-8.73; pos_det_frac:+7.52; verbs_per_utterance:-3.56; rel_OBJ_frac:-3.42; ndw:-3.27 |
| DLD-CONFLICT-002 | TD/pgas21 | Feldman | TD | 21.000 | natural_conversation | highest_clinical_fairness_review | sample_constrained_language_risk | low_word_count | single_window,single_transcript | 0.275 | 0.247 | -0.349 | -0.294 | -0.374 | mean_dep_distance:-0.93; ndw:-0.86; repetition_per_utt:+0.70; rel_MOD_frac:-0.62; rel_OBJ_frac:+0.59 |
| DLD-CONFLICT-003 | TD/072ag | EisenbergGuo | TD | 39.000 | unknown | highest_clinical_fairness_review | possible_hidden_td_language_risk | adequate_sample | single_window,single_transcript | 0.517 | 0.397 | -0.134 | -0.469 | 0.323 | pause_per_utt:-3.92; single_word_ratio:-2.56; function_word_ratio:-1.74; pos_v_frac:+1.15; rel_SUBJ_frac:-0.90 |
| DLD-CONFLICT-004 | DLD_SLI/gla15 | Feldman | DLD_SLI | 14.933 | natural_conversation | highest_scientific_review | sample_constrained_language_risk | low_word_count | single_window,single_transcript | 0.379 | 0.436 | -0.553 | -0.469 | -0.492 | pause_per_utt:-5.79; mlu_morphemes:-1.54; single_word_ratio:-1.01; mean_dep_distance:-0.92; verbs_per_utterance:-0.89 |
| DLD-CONFLICT-005 | DLD_SLI/bea15 | Feldman | DLD_SLI | 14.500 | natural_conversation | highest_scientific_review | sample_constrained_language_risk | low_word_count | single_window,single_transcript | 0.538 | 0.422 | -0.754 | -0.709 | -0.840 | repetition_per_utt:-2.07; single_word_ratio:-1.51; mlu_words:-1.20; utt_len_mean:-1.20; mlu_morphemes:-1.20 |
| DLD-CONFLICT-006 | DLD_SLI/pop15 | Feldman | DLD_SLI | 15.000 | natural_conversation | highest_scientific_review | sample_constrained_language_risk | low_word_count | single_transcript | 0.525 | 0.414 | -0.207 | -0.448 | -0.263 | function_word_ratio:-1.43; retracing_per_utt:-1.15; pause_per_utt:-1.03; pos_v_frac:-0.78; repetition_per_utt:-0.77 |
| DLD-CONFLICT-007 | DLD_SLI/fei15 | Feldman | DLD_SLI | 15.233 | natural_conversation | highest_scientific_review | sample_constrained_language_risk | low_word_count | single_window,single_transcript | 0.502 | 0.385 | -0.097 | -0.113 | -0.288 | rel_MOD_frac:+2.17; pos_det_frac:-1.07; function_word_ratio:-0.92; mean_dep_distance:-0.86; pause_per_utt:-0.70 |
| DLD-CONFLICT-008 | DLD_SLI/477 | ENNI | DLD_SLI | 56.100 | narrative_story | highest_scientific_review | language_risk_not_corpus_prior | adequate_sample | single_window,single_transcript | 0.218 | 0.735 | -1.973 | -0.388 | -2.034 | single_word_ratio:-3.16; mlu_morphemes:-2.36; mlu_words:-2.34; utt_len_mean:-2.34; verbs_per_utterance:-2.19 |
| DLD-CONFLICT-009 | DLD_SLI/476 | ENNI | DLD_SLI | 57.233 | narrative_story | highest_scientific_review | non_mlu_language_state_signal | adequate_sample | single_window,single_transcript | 0.627 | 0.657 | -1.366 | 0.473 | -1.108 | single_word_ratio:-20.02; repetition_per_utt:-4.41; rel_SUBJ_frac:-3.48; rel_OBJ_frac:+3.26; function_word_ratio:+2.19 |
| DLD-CONFLICT-010 | DLD_SLI/444 | ENNI | DLD_SLI | 50.133 | narrative_story | highest_scientific_review | non_mlu_language_state_signal | adequate_sample | single_window,single_transcript | 0.374 | 0.701 | -2.800 | -2.097 | -2.279 | single_word_ratio:-11.87; rel_SUBJ_frac:-6.89; utt_len_p50:-5.40; rel_OBJ_frac:-4.25; mean_dep_distance:-3.25 |
| DLD-CONFLICT-011 | TD/077eg | EisenbergGuo | TD | 39.000 | unknown | highest_scientific_review | possible_hidden_td_language_risk | adequate_sample | single_window,single_transcript | 0.321 | 0.395 | -1.539 | -0.130 | -0.602 | rel_SUBJ_frac:+7.06; pos_det_frac:-3.62; mean_dep_distance:-3.20; utt_len_p90:-2.02; ndw:-2.01 |
| DLD-CONFLICT-012 | DLD_SLI/427 | ENNI | DLD_SLI | 55.533 | narrative_story | highest_scientific_review | low_output_mlu_aligned | adequate_sample | single_window,single_transcript | 0.078 | 0.658 | -2.614 | -1.428 | -1.792 | rel_SUBJ_frac:-5.45; mlu_words:-3.42; utt_len_mean:-3.42; rel_OBJ_frac:+3.26; mean_dep_distance:-3.22 |
| DLD-CONFLICT-013 | DLD_SLI/gig21 | Feldman | DLD_SLI | 21.000 | natural_conversation | highest_scientific_review | sample_constrained_language_risk | low_word_count | single_window,single_transcript | 0.310 | 0.294 | -0.567 | 0.015 | -0.633 | repetition_per_utt:-2.69; mean_dep_distance:+1.40; ndw:-1.03; rel_SUBJ_frac:-0.80; pos_det_frac:-0.74 |
| DLD-CONFLICT-014 | TD/447 | ENNI | TD | 50.167 | narrative_story | highest_scientific_review | possible_hidden_td_language_risk | adequate_sample | single_window,single_transcript | 0.548 | 0.635 | 0.115 | -0.524 | 0.617 | rel_OBJ_frac:-2.06; pos_v_frac:+1.08; verbs_per_utterance:+1.00; filler_per_utt:+0.93; function_word_ratio:-0.89 |
| DLD-CONFLICT-015 | DLD_SLI/413 | ENNI | DLD_SLI | 58.867 | narrative_story | highest_scientific_review | language_risk_not_corpus_prior | adequate_sample | single_window,single_transcript | 0.183 | 0.569 | -3.399 | -1.660 | -0.434 | single_word_ratio:-13.43; rel_SUBJ_frac:-5.37; mlu_morphemes:-4.93; utt_len_p50:-4.05; utt_len_p90:-4.05 |

## Interpretation

The highest-value DLD conflicts are mostly not simple MLU-only cases. Several cases have language-only risk far above MLU risk, suggesting that the model is responding to broader output, lexical-predicate, or syntactic/argument-structure patterns. However, some of the youngest natural-conversation cases are sample constrained, so they should be treated as review prompts rather than clinical findings. The next field-facing step is expert transcript review plus paired structured probes, especially sentence and nonword repetition.
