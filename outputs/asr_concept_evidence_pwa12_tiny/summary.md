# ASR Concept-Level Evidence

- Clip-concept rows: 11127
- Human-positive concept rows: 656
- ASR-positive concept rows: 512
- False negatives: 168
- False positives: 24

## Error Summary By Task

| task | concept_rows | human_positive | asr_positive | false_negative | false_positive | concept_recall | concept_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Cat | 1752 | 124 | 102 | 24 | 2 | 0.806 | 0.980 |
| Cinderella | 5505 | 183 | 128 | 62 | 7 | 0.661 | 0.945 |
| Sandwich | 1056 | 112 | 93 | 22 | 3 | 0.804 | 0.968 |
| Umbrella | 1530 | 124 | 102 | 31 | 9 | 0.750 | 0.912 |
| Window | 1284 | 113 | 87 | 29 | 3 | 0.743 | 0.966 |

## Confidence By Concept Status

| status | n | mean_low_logprob_score | mean_no_speech_prob | mean_compression_ratio | mean_clip_seconds | asr_empty_rate |
| --- | --- | --- | --- | --- | --- | --- |
| true_positive | 488 | 0.555 | 0.061 | 0.948 | 6.451 | 0.000 |
| false_negative | 168 | 0.811 | 0.150 | 1.062 | 5.539 | 0.006 |
| false_positive | 24 | 0.742 | 0.110 | 0.911 | 5.816 | 0.000 |
| true_negative | 10447 | 0.709 | 0.140 | 0.899 | 4.507 | 0.001 |

## AUC: Does Confidence Predict Concept Errors?

| target | feature | auc | n | positives |
| --- | --- | --- | --- | --- |
| missed_given_human_concept_present | low_logprob_score | 0.772 | 656 | 168 |
| missed_given_human_concept_present | whisper_no_speech_prob_mean | 0.710 | 656 | 168 |
| false_positive_given_human_concept_absent | whisper_compression_ratio_mean | 0.612 | 10471 | 24 |
| missed_given_human_concept_present | short_clip_score | 0.593 | 656 | 168 |
| false_positive_given_human_concept_absent | low_logprob_score | 0.548 | 10471 | 24 |
| missed_given_human_concept_present | asr_empty | 0.503 | 656 | 168 |
| false_positive_given_human_concept_absent | asr_empty | 0.499 | 10471 | 24 |
| false_positive_given_human_concept_absent | whisper_no_speech_prob_mean | 0.480 | 10471 | 24 |
| false_positive_given_human_concept_absent | short_clip_score | 0.416 | 10471 | 24 |
| missed_given_human_concept_present | whisper_compression_ratio_mean | 0.363 | 656 | 168 |

## Best Miss-Capture Thresholds

| feature | threshold | flag_rate | miss_capture_rate | hit_flag_rate | flag_precision_for_miss |
| --- | --- | --- | --- | --- | --- |
| asr_empty | 0.000 | 1.000 | 1.000 | 1.000 | 0.256 |
| low_logprob_score | 0.572 | 0.497 | 0.768 | 0.404 | 0.396 |
| low_logprob_score | 0.596 | 0.447 | 0.732 | 0.348 | 0.420 |
| whisper_no_speech_prob_mean | 0.033 | 0.498 | 0.708 | 0.426 | 0.364 |
| low_logprob_score | 0.639 | 0.398 | 0.685 | 0.299 | 0.441 |
| whisper_no_speech_prob_mean | 0.043 | 0.448 | 0.667 | 0.373 | 0.381 |
| low_logprob_score | 0.670 | 0.348 | 0.649 | 0.244 | 0.478 |
| whisper_no_speech_prob_mean | 0.056 | 0.399 | 0.613 | 0.326 | 0.393 |
| low_logprob_score | 0.708 | 0.299 | 0.583 | 0.201 | 0.500 |
| short_clip_score | -4.666 | 0.502 | 0.571 | 0.477 | 0.292 |
| whisper_no_speech_prob_mean | 0.071 | 0.348 | 0.542 | 0.281 | 0.399 |
| short_clip_score | -4.202 | 0.453 | 0.542 | 0.422 | 0.306 |

## Interpretation

This analysis is the concept-level version of the Whisper-confidence experiment. It tests whether utterance confidence can identify when a specific expected concept was omitted or hallucinated by ASR. Strong AUC or favorable miss-capture curves would justify concept-level uncertainty features in the clarification gate; weak curves mean we need richer evidence such as n-best hypotheses, forced alignment, or phonological neighbors.
