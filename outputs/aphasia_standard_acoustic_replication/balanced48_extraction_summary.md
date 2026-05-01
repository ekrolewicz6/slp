# AphasiaBank openSMILE Extraction

- Feature set: `egemaps`
- Output parquet: `data/features/aphasia_opensmile_egemaps_balanced48.parquet`
- Window rows: 54
- Sessions: 48
- Feature columns: 92
- Limit: none
- Max MP4 MB: 250

## Skips

| reason | count |
|---|---:|
| auth_or_html_response | 0 |
| exception | 0 |
| ffmpeg_failure | 0 |
| missing_cha | 0 |
| missing_url | 0 |
| no_window_features | 0 |
| too_large | 0 |

## Sessions By Corpus

| corpus | sessions |
|---|---:|
| Fridriksson-2 | 16 |
| QAB | 13 |
| Tucson | 8 |
| Kurland | 5 |
| SCALE | 2 |
| Adler | 1 |
| Richardson | 1 |
| UNH | 1 |
| Williamson | 1 |

## Notes

Window-level openSMILE features are computed from concatenated participant utterance audio inside each 100-utterance PAR window. This avoids examiner speech but does not preserve between-utterance pause durations, so timing features from transcript time marks remain separate.
