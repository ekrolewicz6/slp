# Current Discovery Scorecard

**Date:** 2026-05-01

This scorecard ranks the project's current claims by scientific value, evidence quality, clinical relevance, and what would be needed to make each claim publishable.

## Short Answer

The project is no longer best described as "can AI diagnose aphasia or DLD?" That framing is too small and, in places, wrong.

The strongest current direction is:

> Language-state change and state disagreement are more informative than static labels, one-time severity scores, or one-dimensional surface measures.

The most promising discovery thread is now cross-lifespan and longitudinal:

```text
same broad score/label
-> different communication state
-> different trajectory or review priority
-> different next assessment/treatment hypothesis
```

## Ranked Claims

| rank | claim | current evidence | main weakness | next required test | status |
| ---: | --- | --- | --- | --- | --- |
| 1 | Early movement is more meaningful than earliest static severity. | Rescorla late talkers with strong 36-to-48 month gains show higher final TD-band rates and lower persistent-gap rates; Dryad EMT-SF data from Grauzer, Roberts, and Jones (2026) show early language-sample movement predicts later T42/T49 outcomes beyond baseline state and treatment group. | Dryad has aggregate variables rather than raw transcripts/audio; treatment assignment only weakly moves aggregate early state. | Replicate in raw transcript datasets with treatment dose/targets and later literacy/school outcomes. | Strongest child-language discovery. |
| 2 | Broad clinical scores hide different discourse states. | Same-WAB pairs and stable-WAB movers show large state differences despite similar WAB-AQ. | Needs clinician review and stronger task/corpus replication. | SLP review of report packets; corpus-held-out same-score examples. | Strong measurement claim. |
| 3 | DLD labels should be treated as noisy anchors, not ground truth. | 82 high-confidence label/corpus/state conflicts; 15 highest-value cases split into sample-constrained, possible hidden TD risk, non-MLU language-state, language-not-corpus-prior, and low-output/MLU-aligned mechanisms. | Current public metadata cannot resolve whether conflicts are true label errors, task artifacts, context effects, or compensation. | Corpus-level review, demographic/dialect/bilingual metadata, structured-task replication. | Strong cautionary claim. |
| 4 | Natural speech and structured tasks are not interchangeable. | Within-task DLD signal is strong; cross-task transfer between narrative and natural speech is weak. | Current local data lack sentence repetition/nonword repetition overlap. | Acquire or collect paired natural speech plus sentence/nonword repetition. | Strong design claim. |
| 5 | ASR/LLM reconstruction should not be used as the measurement source of truth. | Multiple reconstruction and controller experiments show risk of cleanup, hallucinated content, and metric fragility. | Needs human-rated safety benchmark and modern-model replication. | Human adjudication of reconstruction safety; repeat with current models and ASR confidence. | Strong safety claim. |
| 6 | Acoustic state may be useful, but not as a standalone subtype classifier. | eGeMAPS beats random/shuffled controls but WAB severity outperforms eGeMAPS for 4-way subtype classification; custom features add modestly. | Audio results are sample-sensitive and recording artifacts are plausible. | Task-aligned audio review, all-corpus extraction, corpus-held-out tests, standard feature families. | Downgraded but still useful. |
| 7 | Acoustic-only stable-WAB movers are not yet evidence. | Leading-clip screening flagged all 11 candidate pairs; utterance-aligned PAR spans still flag most pairs as medium/high technical risk, with only one low-risk voice/pitch candidate. | Automated technical screens do not replace clinical audio review. | Manually review the low-risk candidate and any borderline utterance-aligned pairs before making a clinical acoustic-change claim. | Falsification queue, not result. |

## Best Publishable Thread Right Now

The most defensible paper-like direction is not "AI predicts diagnosis." It is:

> A multidimensional language-state model reveals clinically meaningful disagreement between labels, scores, tasks, and trajectories in public SLP corpora.

A tighter version:

> In child language, early state movement predicts later status and treatment-linked outcomes better than earliest severity alone; in aphasia, similar WAB scores hide different discourse-state profiles; in both cases, static labels and broad scores are insufficient measurement targets.

This would still be exploratory, but it is scientifically coherent and falsifiable.

## What Would Make This Much Stronger

1. Raw transcript/audio treatment-response data with intervention dose, targets, and session timing.
2. External longitudinal child-language dataset with later literacy/school outcomes.
3. Paired natural speech and sentence/nonword repetition.
4. SLP review of same-score/different-state report packets and the 15-case DLD conflict packet.
5. Manual clinical audio review for the one low-risk acoustic-only mover candidate.

## What To Stop Overclaiming

- Do not claim that eGeMAPS or custom audio features classify aphasia subtype clinically.
- Do not claim DLD diagnosis from transcript features.
- Do not claim individualized treatment-response prediction from current public data.
- Do not treat ASR/LLM-reconstructed text as patient-produced language.
- Do not treat WAB-AQ movement as the only meaningful recovery endpoint.

## Current Best Next Move

The Dryad EMT-SF dataset is now local and analyzed. The next highest-learning step is to get one remaining bottleneck unstuck:

1. get raw transcript/audio or session-level dose/target metadata for an EMT-SF-style treatment dataset;
2. get FluencyBank recovery/persistence access; or
3. get 1-3 SLPs to review the report packets.

Without one of those inputs, the remaining local work is mostly secondary robustness analysis rather than a new discovery path. The best local-only Dryad result is early movement predicting later outcomes, but it cannot yet identify treatment targets or dosing rules.
