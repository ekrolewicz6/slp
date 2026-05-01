# AphasiaBank openSMILE Extraction

- Feature set: `egemaps`
- Output parquet: `data/features/aphasia_opensmile_egemaps_smoke.parquet`
- Window rows: 5
- Sessions: 2
- Feature columns: 92
- Limit: 3
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
| too_large | 1 |

## Sessions By Corpus

| corpus | sessions |
|---|---:|
| NEURAL-2 | 2 |

## Notes

Window-level openSMILE features are computed from concatenated participant utterance audio inside each 100-utterance PAR window. This avoids examiner speech but does not preserve between-utterance pause durations, so timing features from transcript time marks remain separate.
