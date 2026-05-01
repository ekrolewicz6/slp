# Project Charter: Language-State Modeling For SLP

**Date:** 2026-04-30
**Status:** Active operating charter after the 2026-04-29 Brian MacWhinney call.

## Mission

Build a clinically grounded measurement framework for speech-language pathology that represents speech and language ability as a multidimensional, changing state rather than as a single score, broad diagnosis, or static deficit list.

The project exists to make this loop scientifically credible:

```text
speech/language sample
-> reliable transcript/audio/task state
-> rich SLP-interpretable report
-> longitudinal recovery prediction
-> treatment-response learning
-> better next sample or treatment target
```

## Long-Term Goal

Predict how a person's communication state is likely to change under different supports or treatment conditions, with honest uncertainty.

In the ideal version, an SLP can collect a short, high-quality sample, receive a clear state profile, compare that profile to relevant trajectories, and make better decisions about what to assess, monitor, or target next.

## Near-Term Goal

Do not claim treatment optimization yet.

The near-term goal is to validate the measurement layer:

- define a minimum language-state battery,
- map transcript/audio/task features to interpretable clinical dimensions,
- identify which existing datasets can answer recovery questions,
- test whether early state predicts later change in at least one longitudinal disorder dataset,
- produce SLP-facing reports that clinicians find useful and not misleading.

## Core Hypothesis

Broad clinical scores and labels hide separable state dimensions.

Two people can look similar under a single score but differ in:

- content/informativeness,
- recoverability and repairability,
- complexity,
- accuracy/error profile,
- lexicon,
- fluency and acoustics,
- task sensitivity,
- longitudinal change.

Those differences should matter for assessment, monitoring, and eventually treatment planning.

## First Three Publishable Claims To Test

### Claim A: Same Score, Different State

Broad scores and labels compress clinically meaningful state differences.

Initial evidence:

- aphasia patients with similar WAB-AQ can differ in discourse content, unknown-intent risk, repairability, and acoustic state,
- Broca aphasia can be low-output without being child-like,
- DLD/SLI, late talking, and Broca aphasia can overlap on MLU but remain structurally distinct.

Required next evidence:

- review-grade replication,
- patient-level confidence intervals,
- standard acoustic feature replication,
- SLP-facing examples.

### Claim B: Early State Predicts Recovery

Early speech/language state should predict later recovery or persistence better than simple baselines in at least one longitudinal disorder dataset.

Primary near-term target:

- stuttering recovery, because Brian indicated TalkBank has stronger longitudinal recovery data for stuttering than for child language delay/DLD.

Secondary targets:

- late talker catch-up,
- DLD persistent risk,
- aphasia stable-score movers and recovery trajectories.

Required next evidence:

- longitudinal participant IDs,
- early sample features,
- later recovery/persistence endpoints,
- simple baselines,
- robust splits and bootstrap confidence intervals.

### Claim C: Rich State Reports Beat One-Score Classifiers

SLPs need an interpretable profile, not only a probability of disorder.

The report should organize evidence around:

- complexity,
- accuracy,
- lexicon,
- fluency/acoustics,
- content/informativeness,
- recoverability/repairability,
- change over time,
- uncertainty and "do not infer" cautions.

Required next evidence:

- v2 state report prototype,
- informal SLP review,
- examples where a one-score summary would hide clinically relevant differences.

## Active Tracks

### Track 1: Aphasia Validation Sandbox

AphasiaBank currently gives the strongest combination of discourse tasks, clinical labels, WAB scores, repeated sessions, and streamable audio.

Use aphasia to validate:

- same-score different-state examples,
- standard acoustic replication,
- content/informativeness state,
- stable-score but moving-discourse cases,
- measurement firewall for ASR/LLM reconstruction.

### Track 2: Child Language And DLD

DLD and child language are likely the largest population-impact domain, but DLD labels are weak clinical anchors.

Use this track to study:

- persistent risk versus transient delay,
- language difference versus disorder,
- age and MLU baselines,
- corpus/task artifacts,
- structured tasks plus natural speech,
- fairness and missing metadata.

Do not present current DLD models as clinical screeners.

### Track 3: Stuttering Recovery

Stuttering may be the best near-term longitudinal recovery testbed.

Use this track to ask:

- can early speech state predict recovery versus persistence?
- do acoustic, disfluency, lexical, syntactic, and task features add beyond simple fluency counts?
- can the same recovery framework later transfer to DLD and aphasia?

### Track 4: Collection Infrastructure

Data collection is itself a bottleneck.

Build toward:

- simple recorder/front end,
- pseudonym plus age metadata,
- no names or dates of birth,
- no spoken names in recordings,
- BA Web or TalkBank-compatible upload,
- clinician-readable outputs.

Do not duplicate BA Web/Batchalign unless integration is impossible.

## Non-Claims

This project is not currently:

- a diagnostic tool,
- a treatment recommender,
- a replacement for an SLP,
- a validated DLD screener,
- a validated aphasia subtype classifier,
- a clinical ASR system,
- evidence that LLM reconstruction should be used for assessment.

Raw transcript/audio remains the assessment source of truth. ASR/LLM reconstruction is a support layer unless clinically validated.

## Decision Rules

- If a task does not support measurement, recovery prediction, report validity, or data collection, delay it.
- If a result depends on weak labels, report it as discovery, not clinical validation.
- If corpus/task artifacts explain a result, do not bury that weakness.
- If a model cannot beat age, MLU, simple disfluency counts, or broad scores, it is not yet scientifically interesting.
- If an output is not interpretable to an SLP, it is not ready for clinical-facing work.
- If a workflow is too hard for a busy clinician, it will not produce useful prospective data.

## Next 30 Days

1. Finish the minimum language-state battery.
2. Inventory structured tasks in local TalkBank/CHILDES data.
3. Inventory stuttering longitudinal recovery data.
4. Scope openSMILE/eGeMAPS replication.
5. Build the CAF-plus-content feature schema.
6. Redesign the SLP state report around interpretable dimensions.
7. Draft the BA Web recorder workflow spec, but do not build the full app yet.
