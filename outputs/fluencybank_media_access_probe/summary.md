# FluencyBank Media Access Probe

**Question:** can the current TalkBank credential stream FluencyBank media for acoustic recovery modeling?

- Corpora probed: 17
- Sample files probed: 49
- Corpora with at least one accessible media sample: 12

## Corpus Summary

| corpus | samples_probed | accessible_samples | statuses | median_remote_size_mb |
| --- | --- | --- | --- | --- |
| Brejon | 3 | 3 | accessible | 21.504 |
| Examples | 1 | 1 | accessible | 16.695 |
| Hakim | 3 | 3 | accessible | 9.093 |
| IISRP | 3 | 0 | blocked_or_missing | 0.000 |
| IISRP-new | 3 | 0 | blocked_or_missing | 0.000 |
| Maxfield | 3 | 3 | accessible | 1596.434 |
| Purdue | 3 | 0 | blocked_or_missing | 0.000 |
| Ratner | 3 | 3 | accessible | 349.766 |
| Sawyer | 3 | 3 | accessible | 17.552 |
| Tellis | 3 | 3 | accessible | 5.604 |
| UMD-CMU | 3 | 3 | accessible | 201.455 |
| Ulm | 3 | 0 | blocked_or_missing | 0.000 |
| VanZaalen | 3 | 3 | accessible | 8.025 |
| Voices-AWC | 3 | 3 | accessible | 890.536 |
| Voices-AWS | 3 | 3 | accessible | 140.977 |
| Voices-CWS | 3 | 3 | accessible | 50.781 |
| Wagovich | 3 | 0 | blocked_or_missing | 0.000 |

## Interpretation

This probe uses HTTP range requests only; it does not download media. A corpus with accessible samples is technically streamable for future openSMILE/eGeMAPS extraction, but a full acoustic study still needs duration/quality checks and task alignment.

Purdue is transcript-only according to its TalkBank access page, so recovery modeling for Purdue remains transcript-only. IISRP transcript access is open under the current credential, but the sampled IISRP media URLs are still blocked or unavailable from this environment. Ratner and UMD-CMU show accessible MP4 samples; those are candidates for future acoustic feasibility work.
