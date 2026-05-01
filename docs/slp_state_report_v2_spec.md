# SLP State Report V2 Spec

**Date:** 2026-04-30
**Status:** internal research prototype, not a clinical report

## Purpose

The report should help an SLP answer:

1. What kind of communication state is this person in?
2. What evidence supports that interpretation?
3. What changed since the last sample, if anything?
4. What should not be inferred from this sample?
5. What would be useful to probe next?

It should not claim diagnosis, prognosis, or treatment recommendation without
clinical validation.

## Required Sections

### 1. Snapshot

- Pseudonym or participant code.
- Age band if available, never date of birth.
- Population/domain.
- Task type and sample length.
- Broad score/subtype only as context, not as the headline.
- Data-quality flags: short sample, duplicate ID, missing time marks, ASR-only,
  low audio quality, missing structured task.

### 2. State Dimensions

Each dimension should show:

- relative level;
- uncertainty or coverage;
- main supporting features;
- what the dimension does and does not mean.

Dimensions:

| dimension | clinical meaning | candidate evidence |
|---|---|---|
| Content carried | Did expected ideas make it into the sample? | main concepts, CIU proxy, task concepts |
| Unknown intent risk | How often is intended meaning not recoverable? | unknown-intent errors, clarification/abstain rate |
| Recoverable errors | Are missed targets known enough to repair? | near-threshold concepts, known-target errors |
| Structural complexity | How elaborated is the produced language? | MLU, utterance length, dependency diversity, verbs/utterance |
| Lexical access | How much and what kind of vocabulary appears? | NDW, TTR, noun/verb balance, word specificity |
| Fluency/timing | How effortful or disrupted is output timing? | pauses, retracing, repetition, speech rate |
| Acoustic/prosodic state | Are voice/prosody/timing signals atypical? | eGeMAPS/openSMILE, custom pitch/voice/timing |
| Longitudinal movement | Is discourse changing over time? | reliable state deltas, stable-score movers |
| Task sensitivity | Does performance depend on prompt type? | picture/narrative/conversation/structured-task contrast |

### 3. Decision Hypotheses

Decision hypotheses must be framed as hypotheses, not instructions.

Examples:

- High unknown-intent risk: use supported choices and explicit confirmation.
- High recoverable-error burden: probe known-target repair before open-ended
  rewriting.
- Low content with low unknown-risk: consider event-concept expansion.
- Stable broad score with moving discourse state: inspect session pair and
  confirm with repeat sample.
- High acoustic atypicality: do not rely on transcript-only scoring.

### 4. Target Candidates

Targets are only candidates.

Show:

- target concept or task;
- why it is near-threshold;
- confidence/coverage;
- whether it came from raw transcript/audio or AI-reconstructed text.

Never score reconstructed text as independent patient ability.

### 5. Safety Notes

Required notes:

- This is not a validated diagnostic report.
- Raw audio/transcript is the assessment source of truth.
- ASR/LLM reconstruction is communication support, not measurement evidence.
- Missing sentence-repetition/nonword-repetition data limits DLD-style
  interpretation.
- Missing audio/time marks limits acoustic interpretation.
- Broad scores may not move even when discourse state moves.

## V2 Acceptance Criteria

- Every reported dimension maps to `docs/state_feature_schema.md`.
- Every row carries data-quality flags.
- Same-score/different-state examples remain visible.
- The report can be generated for adult aphasia now and adapted to child/DLD and
  stuttering later.
- The report makes clear what additional sample/task would reduce uncertainty.
