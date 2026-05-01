# Aphasia Standard Acoustic Replication Summary

## What Ran

- Verified TalkBank media streaming with the `.env` `TALKBANK_COOKIE_HEADER`.
- Extracted standard openSMILE/eGeMAPS features for a balanced **84-root** AphasiaBank subtype sample: 21 Anomic, 21 Broca, 21 Conduction, 21 Wernicke.
- Re-ran fold-clean subtype models with patient-root rows, repeated stratified CV, fold-internal imputation/scaling/PCA, random-feature controls, shuffled-label controls, feature-family ablations, and leave-corpus-out checks.
- Compared standard eGeMAPS against the project's custom Praat-style acoustic features on the common roots.

## Main Result

The broad claim "standard acoustic features classify aphasia subtype well" is not supported yet.

On the 84-root eGeMAPS sample:

| model | balanced accuracy | macro F1 |
|---|---:|---:|
| WAB-only | 0.549 | 0.526 |
| eGeMAPS + WAB | 0.457 | 0.440 |
| eGeMAPS only | 0.407 | 0.391 |
| random features | 0.268 | 0.255 |
| shuffled labels | 0.218 | 0.207 |
| majority | 0.250 | 0.096 |

eGeMAPS beats random/shuffled controls, but WAB severity remains stronger for 4-way subtype separation.

## Mechanistic Signal

The best eGeMAPS family was `timing_coverage`:

| eGeMAPS family | balanced accuracy | macro F1 |
|---|---:|---:|
| timing_coverage | 0.463 | 0.449 |
| loudness_intensity | 0.390 | 0.364 |
| voice_quality | 0.373 | 0.355 |
| formants | 0.344 | 0.327 |
| spectral_mfcc | 0.305 | 0.286 |
| pitch_f0 | 0.322 | 0.281 |

Pairwise, eGeMAPS is most informative for Wernicke-vs-Conduction, but still does not beat WAB-only on the tested contrasts.

## Custom vs Standard Features

After backfilling 8 of the 9 missing custom-acoustic balanced84 sessions, the common-root comparison has **83** roots; the balanced common subset has **80** roots.

On the balanced common 80-root subset:

| model | balanced accuracy | macro F1 |
|---|---:|---:|
| custom + WAB | 0.563 | 0.546 |
| WAB-only | 0.542 | 0.520 |
| custom voice/pitch/intensity | 0.496 | 0.484 |
| custom only | 0.484 | 0.466 |
| custom no token/count features | 0.472 | 0.459 |
| eGeMAPS + WAB | 0.436 | 0.418 |
| eGeMAPS only | 0.393 | 0.378 |

The custom feature advantage is now modest, not dramatic. The earlier stronger 48-root result was sample-sensitive. The most defensible interpretation is that acoustic/timing features add some information, but not enough to replace clinical severity or support a broad subtype-classification claim.

## Current Scientific Takeaway

This strengthens the project's measurement argument rather than a subtype-classifier argument:

- broad aphasia subtype labels are probably too coarse and partly severity-coded;
- standard eGeMAPS alone is not the right headline;
- custom timing/voice features may capture useful state information;
- the next publishable path is to predict clinically meaningful state dimensions and same-score differences, not to claim subtype diagnosis from acoustics.

## Remaining Gaps

- One selected Wernicke root, `Protocol/SCALE/scale06d`, failed custom ffmpeg extraction.
- The all-corpus extraction is technically feasible but still multi-hour.
- Corpus-held-out checks remain unstable because many corpora have small and skewed subtype coverage.
- The result needs a patient-level bootstrap and external or held-corpus replication before any publication claim.
