# FluencyBank Purdue Recovery Pilot

**Question:** Can earliest available Purdue transcript state predict later recovered versus persistent stuttering labels?

## Data

- Source: FluencyBank English Purdue Corpus, Smith, Weber, Hampton Wray, Walsh, and Usler; DOI `10.21415/P2JB-CA45`.
- Purdue CHAT files parsed: 240
- Unmatched or failed CHAT files: 119
- Strict Rec/Per children with an earliest transcript: 84
- Persistent rate in modeled set: 0.500

### Demographic Label Inventory

| label | n |
| --- | --- |
| Rec | 51 |
| Per | 50 |
| No Data | 8 |
| Y1 only | 5 |
| NEI | 1 |
| Y1 only/Per? | 1 |

## First-Pass Recovery Classification

Endpoint is strict `Per` versus `Rec` from the distributed Purdue demographics workbook. Ambiguous labels such as `No Data`, `NEI`, and `Y1 only` are excluded.

| feature_set | n | n_features | persistent_rate | balanced_accuracy | macro_f1 | persistent_f1 | auc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| majority_baseline | 84 | 0 | 0.500 | 0.476 | 0.471 | 0.421 | 0.476 |
| age_sex_ses | 84 | 4 | 0.500 | 0.524 | 0.517 | 0.574 | 0.567 |
| simple_disfluency | 84 | 7 | 0.500 | 0.595 | 0.592 | 0.553 | 0.597 |
| language_structure | 84 | 10 | 0.500 | 0.524 | 0.524 | 0.524 | 0.570 |
| baseline_tests | 84 | 8 | 0.500 | 0.583 | 0.580 | 0.615 | 0.586 |
| all_transcript | 84 | 17 | 0.500 | 0.571 | 0.569 | 0.538 | 0.590 |
| all_available | 84 | 29 | 0.500 | 0.524 | 0.524 | 0.512 | 0.568 |

## Shuffled-Label AUC Check

| feature_set | observed_auc | perm_mean_auc | perm_p_auc_ge_observed | permutations |
| --- | --- | --- | --- | --- |
| simple_disfluency | 0.597 | 0.493 | 0.124 | 200 |
| all_transcript | 0.590 | 0.491 | 0.144 | 200 |
| all_available | 0.568 | 0.497 | 0.159 | 200 |

## Label Group Feature Means

| rec_per | n | mlu_words_mean | ndw_mean | ttr_mean | repetition_per_utt_mean | retracing_per_utt_mean | filler_per_utt_mean | stutter_arrow_spans_per_utt_mean | repeated_sound_runs_per_utt_mean | spelt3_mean | bbtop_ci_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Per | 42 | 4.206 | 281.690 | 0.309 | 0.255 | 0.074 | 0.096 | 0.122 | 0.038 | 95.810 | 90.345 |
| Rec | 42 | 4.354 | 305.810 | 0.305 | 0.208 | 0.082 | 0.088 | 0.094 | 0.029 | 98.310 | 95.357 |

## Interpretation

The best first-pass feature set is `simple_disfluency` with AUC 0.597, balanced accuracy 0.595, and macro-F1 0.592.

This is a real unblock for the stuttering track: Purdue gives us an accessible longitudinal Rec/Per endpoint. However, this is still a pilot. The model uses one earliest transcript per child, no acoustic features yet, no official severity trajectory modeling, and no external corpus-held-out validation. IISRP, Wagovich, Ratner, and Maxfield remain password-gated and are still needed for replication.

Next experiment: add longitudinal change features from later Purdue transcripts and test whether early transcript state predicts final persistence beyond baseline demographics and standardized tests.
