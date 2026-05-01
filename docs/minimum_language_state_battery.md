# Minimum Language-State Battery

**Date:** 2026-04-30
**Status:** First operational draft after Brian MacWhinney call.

## Purpose

Define the smallest practical assessment battery that can support language-state modeling across aphasia, child language/DLD, and stuttering without pretending that natural conversation alone is enough.

Brian's guidance was clear: use both ecologically valid speech and tighter structured tasks. Natural speech shows how a person communicates in context. Structured tasks make specific capacities easier to measure.

## Design Principles

- Collect audio whenever possible, not transcript-only data.
- Pair natural speech with structured elicitation.
- Keep the battery short enough for real clinicians to use.
- Use task outputs that map to SLP-interpretable dimensions.
- Avoid names, dates of birth, and spoken identifiers.
- Preserve raw audio/transcript as the measurement source of truth.
- Treat ASR/LLM outputs as support, not assessment ground truth.

## Shared State Dimensions

| Dimension | What It Measures | Candidate Evidence |
| --- | --- | --- |
| Complexity | How much structure the speaker can produce | MLU, clause density, embedding, sentence repetition span |
| Accuracy | Whether forms are produced correctly | morphology, syntax errors, phonological errors, retracing, revisions |
| Lexicon | Word knowledge, retrieval, specificity | lexical diversity, nouns/verbs, word frequency, naming/retrieval proxies |
| Fluency/Acoustics | Timing, rhythm, voice, disfluency, motor/acoustic burden | pauses, speech rate, pitch, intensity, voice quality, disfluency counts |
| Content/Informativeness | Whether the expected ideas were communicated | main concepts, CIU-like scores, task-specific event concepts |
| Recoverability/Repairability | Whether the intended meaning is inferable and targetable | known target errors, unknown intent, near-threshold missed concepts |
| Task Sensitivity | Whether performance changes by elicitation condition | natural versus repetition versus narrative differences |
| Longitudinal Change | Whether state moves over time | within-person slopes, reliable change, stable-score movers |
| Context/Fairness | Whether interpretation depends on background or measurement context | age, language exposure, dialect, corpus/site, task, audio quality |

## Core Battery

| Task | Required? | Primary Purpose | Main State Dimensions | Key Risks |
| --- | --- | --- | --- | --- |
| Natural conversation/interview | Yes | Ecological communication sample | lexicon, fluency, content, repairability, pragmatics | hard to score, prompt variability, ASR errors |
| Picture description | Yes | Controlled but open discourse | content, lexicon, fluency, repairability | prompt-specific norms needed |
| Narrative/story retell | Yes where feasible | Discourse organization and event content | content, complexity, cohesion, narrative state | scoring rubrics vary by story |
| Sentence repetition | Yes | Tight probe of syntax, memory, and speech production | complexity, accuracy, fluency, ASR robustness | not fully ecological |
| Nonword repetition | Yes for child/stuttering tracks; optional for aphasia | Phonological memory/articulation probe | accuracy, phonology, acoustic quality | ASR may be unreliable |
| Comprehension task | Optional first pass, important later | Receptive language under controlled demands | comprehension, accuracy, task sensitivity | less functional than production tasks |
| Patient/caregiver/parent/teacher rating | Optional but high value | Functional and contextual anchor | participation, burden, real-world change | subjective and non-comparable |

## Adult Aphasia Variant

Minimum:

1. Picture description.
2. Narrative/story retell if tolerated.
3. Short open-ended conversation.
4. Sentence repetition or phrase repetition.
5. Optional naming/retrieval probe.
6. Optional comprehension probe.

Primary outputs:

- content conveyed,
- unknown-intent risk,
- known repairable errors,
- acoustic fluency,
- lexical retrieval profile,
- sentence repetition accuracy,
- change since prior sample,
- comparison to broad WAB/subtype only as context.

Special cautions:

- WAB-AQ and subtype are useful anchors but not clean ground truth.
- ASR/LLM reconstruction must not replace raw transcript/audio.
- Severe/floor cases need separation into low output, motor/acoustic failure, unknown intent, and known repairable targets.

## Child Language / DLD Variant

Minimum:

1. Natural speech sample with adult interlocutor.
2. Picture description or play-based elicitation.
3. Narrative/story retell for school-age children.
4. Sentence repetition.
5. Nonword repetition.
6. Optional comprehension task.
7. Parent/teacher context if available.

Primary outputs:

- age-referenced complexity,
- sentence repetition profile,
- nonword repetition/phonological burden,
- lexical diversity and specificity,
- narrative/content state,
- language difference versus disorder cautions,
- corpus/task artifact warnings,
- trajectory when longitudinal data exist.

Special cautions:

- DLD/SLI labels are noisy clinical anchors, not ground truth.
- Bilingualism, dialect, socioeconomic context, school fit, personality, and task conditions can affect apparent performance.
- A DLD screening claim is not credible without fairness and artifact audits.
- Current public data are stronger for discovery than diagnosis.

## Stuttering Recovery Variant

Minimum:

1. Natural speech sample.
2. Structured reading or repetition task where available.
3. Sentence repetition if available.
4. Repeated samples over time.
5. Recovery/persistence endpoint or later fluency status.

Primary outputs:

- disfluency type and frequency,
- acoustic timing and rhythm,
- speech rate and pause structure,
- lexical/syntactic load,
- task sensitivity,
- early-state predictors of recovery versus persistence.

Special cautions:

- Many young children show transient disfluency.
- Recovery labels must be defined carefully.
- Simple disfluency counts and age are required baselines.
- Stuttering is the near-term recovery sandbox, not a replacement for DLD work.

## Minimum Metadata

Required:

- pseudonym or participant code,
- age at sample,
- language(s) spoken or exposed where possible,
- task type,
- recording date or timepoint code,
- broad population label if available,
- consent/source status,
- audio availability,
- transcript availability.

Strongly preferred:

- sex/gender where appropriate and consented,
- dialect or region proxy,
- bilingual exposure details,
- education or grade,
- clinical diagnosis source,
- hearing status,
- motor speech status,
- intervention exposure,
- outcome timepoints.

Do not collect:

- name,
- date of birth,
- address,
- medical record number,
- spoken identifiers in the recording.

## Audio And Workflow Requirements

Minimum audio standard:

- one speaker sample per task where possible,
- quiet room,
- stable microphone distance,
- no spoken name at the start,
- task label recorded in metadata, not spoken into the file,
- store raw audio only when consent/licensing allows,
- otherwise stream or derive features and delete raw audio.

For sentence/nonword repetition:

- avoid recording the playback prompt over the participant voice where possible,
- use headphones or separate channels if feasible,
- store prompt item ID in metadata,
- score both exactness and error pattern.

## SLP-Facing Report Requirements

The report should not output one final "disordered/not disordered" label.

It should show:

- summary state by dimension,
- uncertainty,
- examples from the transcript,
- strengths,
- breakdowns,
- what changed since last sample,
- what not to infer,
- whether the sample quality is adequate,
- whether structured and natural tasks agree or diverge.

Initial report sections:

1. Sample quality.
2. Overall communication state.
3. Complexity.
4. Accuracy/error profile.
5. Lexicon.
6. Fluency/acoustics.
7. Content/informativeness.
8. Recoverability/repairability.
9. Task sensitivity.
10. Change over time.
11. Suggested next assessment questions, not treatment prescriptions.

## First Implementation Targets

1. Inventory existing corpora for these task types.
2. Run a structured-task plus natural-speech experiment where overlap exists.
3. Build openSMILE/eGeMAPS acoustic extraction.
4. Redesign the state report around this schema.
5. Use stuttering as the first recovery-prediction testbed if data support it.
