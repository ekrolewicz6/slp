# DLD Target Policy Simulation

- Participants: 270
- Top-k targets per participant per policy: 5

## Policy Summary

| policy | n_targets | n_participants | mean_deficit_z | mean_learning_utility | pct_too_easy | pct_too_hard | n_target_classes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_utility | 1270 | 270 | 1.258 | 1.026 | 0.085 | 0.011 | 11 |
| highest_deficit | 1270 | 270 | 1.620 | 0.887 | 0.083 | 0.141 | 11 |
| near_threshold | 1270 | 270 | 0.958 | 0.872 | 0.108 | 0.008 | 11 |
| generic_priority | 1270 | 270 | 1.269 | 0.784 | 0.192 | 0.088 | 11 |
| random_eligible | 1270 | 270 | 1.118 | 0.773 | 0.234 | 0.061 | 11 |
| easiest_deficit | 1270 | 270 | 0.696 | 0.595 | 0.432 | 0.008 | 11 |

## By Cluster

| cluster | policy | n_participants | mean_age | mean_deficit_z | mean_learning_utility | top_classes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | high_utility | 29 | 55.743 | 1.806 | 1.177 | utterance_length, grammar_function_words, predicate_structure, argument_structure |
| 0 | near_threshold | 29 | 55.743 | 1.358 | 0.995 | grammar_function_words, utterance_length, argument_structure, predicate_structure |
| 0 | easiest_deficit | 29 | 55.743 | 1.303 | 0.942 | grammar_function_words, utterance_length, argument_structure, predicate_structure |
| 0 | random_eligible | 29 | 55.743 | 2.188 | 0.791 | utterance_length, grammar_function_words, predicate_structure, argument_structure |
| 0 | generic_priority | 29 | 55.743 | 2.547 | 0.691 | utterance_length, argument_structure, predicate_structure, lexical_variety |
| 0 | highest_deficit | 29 | 55.743 | 3.234 | 0.455 | utterance_length, predicate_structure, argument_structure, lexical_variety |
| 1 | high_utility | 115 | 41.503 | 0.941 | 0.801 | grammar_function_words, lexical_variety, disfluency_repair, fluency_timing |
| 1 | highest_deficit | 115 | 41.503 | 1.131 | 0.774 | grammar_function_words, lexical_variety, disfluency_repair, fluency_timing |
| 1 | near_threshold | 115 | 41.503 | 0.823 | 0.739 | grammar_function_words, lexical_variety, elaboration, disfluency_repair |
| 1 | generic_priority | 115 | 41.503 | 1.016 | 0.690 | lexical_variety, grammar_function_words, utterance_length, disfluency_repair |
| 1 | random_eligible | 115 | 41.503 | 0.874 | 0.674 | grammar_function_words, lexical_variety, utterance_length, disfluency_repair |
| 1 | easiest_deficit | 115 | 41.503 | 0.643 | 0.548 | utterance_length, grammar_function_words, lexical_variety, disfluency_repair |
| 2 | high_utility | 126 | 35.689 | 1.383 | 1.169 | utterance_length, grammar_function_words, argument_structure, predicate_structure |
| 2 | highest_deficit | 126 | 35.689 | 1.634 | 1.076 | utterance_length, grammar_function_words, argument_structure, low_output |
| 2 | near_threshold | 126 | 35.689 | 0.972 | 0.949 | utterance_length, grammar_function_words, predicate_structure, argument_structure |
| 2 | generic_priority | 126 | 35.689 | 1.174 | 0.881 | utterance_length, argument_structure, predicate_structure, lexical_variety |
| 2 | random_eligible | 126 | 35.689 | 1.063 | 0.847 | utterance_length, grammar_function_words, predicate_structure, argument_structure |
| 2 | easiest_deficit | 126 | 35.689 | 0.597 | 0.551 | utterance_length, grammar_function_words, predicate_structure, syntactic_complexity |

## Target Class Distribution

| policy | target_class | n | pct |
| --- | --- | --- | --- |
| easiest_deficit | utterance_length | 319 | 0.251 |
| easiest_deficit | grammar_function_words | 205 | 0.161 |
| easiest_deficit | predicate_structure | 117 | 0.092 |
| easiest_deficit | lexical_variety | 111 | 0.087 |
| easiest_deficit | elaboration | 95 | 0.075 |
| easiest_deficit | fluency_timing | 95 | 0.075 |
| easiest_deficit | argument_structure | 94 | 0.074 |
| easiest_deficit | disfluency_repair | 74 | 0.058 |
| easiest_deficit | syntactic_complexity | 65 | 0.051 |
| easiest_deficit | utterance_variability | 53 | 0.042 |
| easiest_deficit | low_output | 42 | 0.033 |
| generic_priority | utterance_length | 290 | 0.228 |
| generic_priority | argument_structure | 202 | 0.159 |
| generic_priority | lexical_variety | 201 | 0.158 |
| generic_priority | grammar_function_words | 190 | 0.150 |
| generic_priority | predicate_structure | 182 | 0.143 |
| generic_priority | disfluency_repair | 58 | 0.046 |
| generic_priority | fluency_timing | 53 | 0.042 |
| generic_priority | elaboration | 42 | 0.033 |
| generic_priority | utterance_variability | 19 | 0.015 |
| generic_priority | syntactic_complexity | 18 | 0.014 |
| generic_priority | low_output | 15 | 0.012 |
| high_utility | utterance_length | 281 | 0.221 |
| high_utility | grammar_function_words | 245 | 0.193 |
| high_utility | lexical_variety | 121 | 0.095 |
| high_utility | argument_structure | 107 | 0.084 |
| high_utility | predicate_structure | 95 | 0.075 |
| high_utility | utterance_variability | 83 | 0.065 |
| high_utility | elaboration | 82 | 0.065 |
| high_utility | disfluency_repair | 67 | 0.053 |
| high_utility | fluency_timing | 63 | 0.050 |
| high_utility | low_output | 63 | 0.050 |
| high_utility | syntactic_complexity | 63 | 0.050 |
| highest_deficit | utterance_length | 260 | 0.205 |
| highest_deficit | grammar_function_words | 234 | 0.184 |
| highest_deficit | lexical_variety | 122 | 0.096 |
| highest_deficit | argument_structure | 108 | 0.085 |
| highest_deficit | predicate_structure | 101 | 0.080 |
| highest_deficit | low_output | 92 | 0.072 |
| highest_deficit | disfluency_repair | 80 | 0.063 |
| highest_deficit | elaboration | 73 | 0.057 |
| highest_deficit | utterance_variability | 72 | 0.057 |
| highest_deficit | fluency_timing | 68 | 0.054 |
| highest_deficit | syntactic_complexity | 60 | 0.047 |
| near_threshold | utterance_length | 310 | 0.244 |
| near_threshold | grammar_function_words | 234 | 0.184 |
| near_threshold | predicate_structure | 116 | 0.091 |
| near_threshold | lexical_variety | 105 | 0.083 |
| near_threshold | elaboration | 97 | 0.076 |
| near_threshold | argument_structure | 96 | 0.076 |
| near_threshold | utterance_variability | 71 | 0.056 |
| near_threshold | fluency_timing | 70 | 0.055 |
| near_threshold | disfluency_repair | 66 | 0.052 |
| near_threshold | syntactic_complexity | 64 | 0.050 |
| near_threshold | low_output | 41 | 0.032 |
| random_eligible | utterance_length | 297 | 0.234 |
| random_eligible | grammar_function_words | 209 | 0.165 |
| random_eligible | lexical_variety | 128 | 0.101 |
| random_eligible | predicate_structure | 121 | 0.095 |
| random_eligible | argument_structure | 86 | 0.068 |

## Interpretation

- This is a target-discovery simulation, not evidence of treatment efficacy.
- Near-threshold and high-utility policies prefer deficits that are measurable but not extreme.
- Highest-deficit policies often nominate severe low-output targets that may be clinically real but less immediately changeable.
- The next required experiment is to connect these nominated targets to longitudinal change or real intervention outcomes.
