# Data Quality Gates

- Required gate failures: 1
- Warnings: 3
- TalkBank media auth: PASS

## Feature Table Gates

| table | gate | status | detail | value |
| --- | --- | --- | --- | --- |
| aphasia_windowed | file_exists | PASS | data/features/aphasiabank_windowed_features.parquet | 1 |
| aphasia_windowed | row_count | PASS | rows | 4108 |
| aphasia_windowed | window_id_present | PASS | window_id | 1 |
| aphasia_windowed | window_id_missing | PASS | missing rows | 0 |
| aphasia_windowed | window_id_duplicate_rows | FAIL | 128 duplicated IDs | 303 |
| aphasia_windowed | transcript_id_present | PASS | transcript_id | 1 |
| aphasia_windowed | transcript_id_missing | PASS | missing rows | 0 |
| aphasia_windowed | transcript_id_repeated_windows | INFO | 943 duplicated IDs | 3368 |
| aphasia_windowed | participant_id_missing | PASS | participant_id | 0 |
| aphasia_windowed | participant_count | PASS | participant_id | 1609 |
| aphasia_windowed | numeric_feature_columns | PASS | numeric columns | 60 |
| aphasia_windowed | columns_over_50pct_missing | PASS | numeric columns | 0 |
| aphasia_windowed | all_zero_numeric_columns | WARN | pos_mod_frac, pos_conj_frac, pos_coord_frac, pos_neg_frac, pos_inf_frac, rel_SUBJ_frac, rel_MOD_frac, rel_COORD_frac, rel_PRED_frac, rel_JCT_frac | 18 |
| childes_windowed | file_exists | PASS | data/features/phase1_windowed_features.parquet | 1 |
| childes_windowed | row_count | PASS | rows | 23904 |
| childes_windowed | window_id_present | PASS | window_id | 1 |
| childes_windowed | window_id_missing | PASS | missing rows | 0 |
| childes_windowed | window_id_duplicate_rows | PASS | 0 duplicated IDs | 0 |
| childes_windowed | transcript_id_present | PASS | transcript_id | 1 |
| childes_windowed | transcript_id_missing | PASS | missing rows | 0 |
| childes_windowed | transcript_id_repeated_windows | INFO | 4626 duplicated IDs | 20514 |
| childes_windowed | participant_id_missing | PASS | child_id | 0 |
| childes_windowed | participant_count | PASS | child_id | 390 |
| childes_windowed | numeric_feature_columns | PASS | numeric columns | 58 |
| childes_windowed | columns_over_50pct_missing | PASS | numeric columns | 0 |
| childes_windowed | all_zero_numeric_columns | PASS |  | 0 |

## Split Leakage Gates

| table | splitter | fold | train_test_group_overlap | status | detail |
| --- | --- | --- | --- | --- | --- |
| aphasia_windowed | GroupKFold | 0 | 0 | PASS | participant_id |
| aphasia_windowed | GroupKFold | 1 | 0 | PASS | participant_id |
| aphasia_windowed | GroupKFold | 2 | 0 | PASS | participant_id |
| aphasia_windowed | GroupKFold | 3 | 0 | PASS | participant_id |
| aphasia_windowed | GroupKFold | 4 | 0 | PASS | participant_id |
| aphasia_windowed | naive_KFold_demonstration | -1 | 456 | WARN | expected leakage if row-wise KFold is used |
| childes_windowed | GroupKFold | 0 | 0 | PASS | child_id |
| childes_windowed | GroupKFold | 1 | 0 | PASS | child_id |
| childes_windowed | GroupKFold | 2 | 0 | PASS | child_id |
| childes_windowed | GroupKFold | 3 | 0 | PASS | child_id |
| childes_windowed | GroupKFold | 4 | 0 | PASS | child_id |
| childes_windowed | naive_KFold_demonstration | -1 | 237 | WARN | expected leakage if row-wise KFold is used |

## TalkBank Media Auth

| gate | status | detail |
| --- | --- | --- |
| talkbank_media_auth | PASS | source=env_cookie; status=206; content_type=video/mp4 |

## Time-Mark Summary By Corpus

| corpus | files | median_time_mark_fraction | transcripts_under_80pct | total_invalid_time_marks |
| --- | --- | --- | --- | --- |
| Duquesne | 55 | 0 | 55 | 0 |
| Control | 24 | 1 | 0 | 0 |
| BU | 22 | 0 | 22 | 0 |
| Pilot | 21 | 1 | 0 | 0 |
| Whiteside | 19 | 1 | 0 | 0 |
| SCALE | 14 | 1 | 0 | 0 |
| NRL | 9 | 1 | 0 | 0 |
| Kurland | 8 | 1 | 0 | 0 |
| Wozniak | 8 | 1 | 0 | 0 |
| Adler | 7 | 1 | 0 | 0 |
| Elman | 6 | 1 | 0 | 0 |
| Tucson | 4 | 1 | 0 | 0 |
| Williamson | 3 | 1 | 0 | 0 |

## Interpretation

A headline experiment is not review-grade until required ID gates pass, participant-level splits show zero train/test overlap, and audio-linked analyses either have adequate time marks or explicitly exclude sessions that do not.
