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
| 1 | Early movement is more meaningful than earliest late-talker severity. | Rescorla late talkers with strong 36-to-48 month gains show higher final TD-band rates and lower persistent-gap rates. | Small N, no treatment exposure, no external outcome/literacy endpoint. | Replicate in Manchester/Ellis Weismer/other longitudinal child datasets; add literacy/school outcomes. | Most promising child-language discovery. |
| 2 | Broad clinical scores hide different discourse states. | Same-WAB pairs and stable-WAB movers show large state differences despite similar WAB-AQ. | Needs clinician review and stronger task/corpus replication. | SLP review of report packets; corpus-held-out same-score examples. | Strong measurement claim. |
| 3 | DLD labels should be treated as noisy anchors, not ground truth. | 82 high-confidence label/corpus/state conflicts; only a subset are language-driven review cases. | Current public metadata cannot resolve whether conflicts are true label errors, task artifacts, context effects, or compensation. | Corpus-level review, demographic/dialect/bilingual metadata, structured-task replication. | Strong cautionary claim. |
| 4 | Natural speech and structured tasks are not interchangeable. | Within-task DLD signal is strong; cross-task transfer between narrative and natural speech is weak. | Current local data lack sentence repetition/nonword repetition overlap. | Acquire or collect paired natural speech plus sentence/nonword repetition. | Strong design claim. |
| 5 | ASR/LLM reconstruction should not be used as the measurement source of truth. | Multiple reconstruction and controller experiments show risk of cleanup, hallucinated content, and metric fragility. | Needs human-rated safety benchmark and modern-model replication. | Human adjudication of reconstruction safety; repeat with current models and ASR confidence. | Strong safety claim. |
| 6 | Acoustic state may be useful, but not as a standalone subtype classifier. | eGeMAPS beats random/shuffled controls but WAB severity outperforms eGeMAPS for 4-way subtype classification; custom features add modestly. | Audio results are sample-sensitive and recording artifacts are plausible. | Task-aligned audio review, all-corpus extraction, corpus-held-out tests, standard feature families. | Downgraded but still useful. |
| 7 | Acoustic-only stable-WAB movers are not yet evidence. | All 11 acoustic-only candidate pairs show medium/high recording-artifact risk in leading-clip technical screening. | Leading clips may include setup silence; task-aligned review is still needed. | Review exact utterance-aligned audio windows before making any clinical acoustic-change claim. | Falsification queue, not result. |

## Best Publishable Thread Right Now

The most defensible paper-like direction is not "AI predicts diagnosis." It is:

> A multidimensional language-state model reveals clinically meaningful disagreement between labels, scores, tasks, and trajectories in public SLP corpora.

A tighter version:

> In child language, early state movement predicts later late-talker status better than earliest severity alone; in aphasia, similar WAB scores hide different discourse-state profiles; in both cases, static labels and broad scores are insufficient measurement targets.

This would still be exploratory, but it is scientifically coherent and falsifiable.

## What Would Make This Much Stronger

1. External longitudinal child-language dataset with later functional outcomes.
2. Paired natural speech and sentence/nonword repetition.
3. SLP review of same-score/different-state report packets.
4. Task-aligned audio review for acoustic movers.
5. A prospective collection workflow that captures repeated samples, treatment exposure, and outcomes.

## What To Stop Overclaiming

- Do not claim that eGeMAPS or custom audio features classify aphasia subtype clinically.
- Do not claim DLD diagnosis from transcript features.
- Do not claim treatment-response prediction from current public data.
- Do not treat ASR/LLM-reconstructed text as patient-produced language.
- Do not treat WAB-AQ movement as the only meaningful recovery endpoint.

## Current Best Next Move

The next highest-learning step is to get one external bottleneck unstuck:

1. manually download the Dryad EMT-SF DLD treatment-response dataset;
2. get FluencyBank recovery/persistence access; or
3. get 1-3 SLPs to review the report packets.

Without one of those inputs, the remaining local work is mostly secondary robustness analysis rather than a new discovery path.
