# AphasiaBank openSMILE Extraction

- Feature set: `egemaps`
- Output parquet: `data/features/aphasia_opensmile_egemaps_balanced84.parquet`
- Window rows: 110
- Sessions: 84
- Feature columns: 92
- Limit: none
- Max MP4 MB: 400

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
| Fridriksson-2 | 27 |
| Tucson | 14 |
| QAB | 14 |
| Kurland | 6 |
| SCALE | 5 |
| Richardson | 3 |
| NEURAL-2 | 2 |
| Kansas | 2 |
| NEURAL | 2 |
| Adler | 2 |
| Whiteside | 1 |
| UNH | 1 |
| ACWT | 1 |
| SouthAL | 1 |
| Elman | 1 |
| BU | 1 |
| Williamson | 1 |

## Notes

Window-level openSMILE features are computed from concatenated participant utterance audio inside each 100-utterance PAR window. This avoids examiner speech but does not preserve between-utterance pause durations, so timing features from transcript time marks remain separate.
