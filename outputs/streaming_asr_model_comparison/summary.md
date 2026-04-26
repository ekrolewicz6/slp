# Streaming ASR Model Comparison

## Run Summary

| label | model | rows | sessions | utterance_clips | par_audio_min | mean_f1 | mean_recall | mean_precision | mean_asr_coverage | mean_human_coverage | r_asr_coverage_wab | r_human_coverage_wab |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| severe | tiny.en | 10 | 2 | 71 | 4.797 | 0.200 | 0.200 | 0.200 | 0.027 | 0.027 | -0.244 | -0.244 |
| severe | base.en | 10 | 2 | 71 | 4.797 | 0.200 | 0.200 | 0.200 | 0.027 | 0.027 | 0.163 | -0.244 |
| balanced4 | tiny.en | 20 | 4 | 200 | 14.202 | 0.833 | 0.770 | 0.938 | 0.406 | 0.518 | 0.828 | 0.931 |
| balanced4 | base.en | 20 | 4 | 200 | 14.202 | 0.855 | 0.794 | 0.950 | 0.416 | 0.518 | 0.849 | 0.931 |
| balanced12 | tiny.en | 60 | 12 | 739 | 54.587 | 0.783 | 0.732 | 0.873 | 0.362 | 0.436 | 0.722 | 0.764 |
| pwa30 | tiny.en | 150 | 30 | 2602 | 202.750 | 0.764 | 0.718 | 0.859 | 0.431 | 0.517 | 0.713 | 0.761 |
| pwa60 | tiny.en | 233 | 52 | 3809 | 255.574 | 0.742 | 0.703 | 0.817 | 0.346 | 0.404 | 0.738 | 0.789 |

## Paired Deltas

| comparison | metric | paired_rows | mean_a | mean_b | mean_delta | n_better | n_worse | n_same |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| severe:base.en minus severe:tiny.en | concept_f1_vs_human | 10 | 0.200 | 0.200 | 0.000 | 0 | 0 | 10 |
| severe:base.en minus severe:tiny.en | concept_recall_vs_human | 10 | 0.200 | 0.200 | 0.000 | 0 | 0 | 10 |
| severe:base.en minus severe:tiny.en | concept_precision_vs_human | 10 | 0.200 | 0.200 | 0.000 | 0 | 0 | 10 |
| severe:base.en minus severe:tiny.en | asr_concept_coverage_frac | 10 | 0.027 | 0.027 | 0.000 | 1 | 1 | 8 |
| balanced4:base.en minus balanced4:tiny.en | concept_f1_vs_human | 20 | 0.833 | 0.855 | 0.022 | 7 | 3 | 10 |
| balanced4:base.en minus balanced4:tiny.en | concept_recall_vs_human | 20 | 0.770 | 0.794 | 0.025 | 7 | 3 | 10 |
| balanced4:base.en minus balanced4:tiny.en | concept_precision_vs_human | 20 | 0.938 | 0.950 | 0.012 | 1 | 0 | 19 |
| balanced4:base.en minus balanced4:tiny.en | asr_concept_coverage_frac | 20 | 0.406 | 0.416 | 0.010 | 6 | 3 | 11 |

## Interpretation

The balanced sample tests whether ASR can preserve clinically meaningful prompt-conditioned content when participants actually produce content. The severe sample tests whether larger ASR alone rescues floor-level Broca speech. A large balanced improvement with no severe improvement would point to ASR model scale as the bottleneck; a small balanced improvement and no severe improvement points toward aphasia-specific ASR/alignment plus downstream clarification rather than generic model scaling alone.
