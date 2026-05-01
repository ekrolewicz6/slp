# State Feature Schema: CAF Plus Content

**Date:** 2026-04-30
**Status:** First computable schema for the post-Brian measurement layer.

## Purpose

Map model features to SLP-interpretable state dimensions. This schema is the bridge between raw transcripts/audio and the eventual SLP-facing state report.

The report should not say only "aphasic," "DLD-like," "persistent stutterer," or "low score." It should describe the dimensions that produced the risk or impairment signal.

## Top-Level Dimensions

| State Dimension | Plain Meaning | Primary Data Source | Report Use |
| --- | --- | --- | --- |
| Complexity | How much linguistic structure the person can produce | transcript, sentence repetition | syntactic/utterance-level profile |
| Accuracy | How often produced forms match expected forms | transcript, error tags, repetition tasks | error profile and target hypotheses |
| Lexicon | Word knowledge, specificity, and retrieval | transcript, naming/retrieval tasks | lexical strength/weakness profile |
| Fluency/Acoustics | Timing, rhythm, pausing, voice, disfluency, motor burden | audio, transcript disfluency markers | fluency and speech-production profile |
| Content/Informativeness | Whether the expected ideas were communicated | task rubrics, main concepts, CIU-like scores | functional communication profile |
| Recoverability/Repairability | Whether missing/incorrect content has an inferable target | transcript, task rubric, error labels | clarify versus target versus abstain decisions |
| Task Sensitivity | Whether state changes across elicitation conditions | repeated tasks in same session | natural-plus-tight-task interpretation |
| Longitudinal Change | Whether state moves over time | repeated samples | monitoring and recovery prediction |
| Context/Fairness | Whether interpretation depends on language, dialect, site, task, or audio quality | metadata, corpus, audio audit | safety and bias warnings |

## Feature Families

### 1. Complexity

Candidate transcript features:

- `mlu_words`
- `mlu_morphemes`
- `utt_len_mean`
- `utt_len_p50`
- `utt_len_p90`
- `verbs_per_utterance`
- clause or dependency depth proxies
- `mean_dep_distance`
- `max_dep_distance`
- `unique_head_dep_pairs`
- `unique_head_rel_dep_triples`

Structured-task features:

- sentence repetition exact span
- sentence repetition partial-credit score
- sentence length at failure
- syntactic construction at failure

Required baselines:

- age
- MLU
- transcript length
- task type

Interpretation:

Low complexity can reflect developmental stage, aphasia, low output, task demand, motor burden, or insufficient sample length. It should never be interpreted alone.

### 2. Accuracy

Candidate transcript features:

- morphology error tags where available
- phonological error tags where available
- semantic/paraphasia tags where available
- `retracing_per_utt`
- `repetition_per_utt`
- `filler_per_utt`
- `pause_per_utt`
- repair/revision markers
- mismatch between intended and produced task concepts

Structured-task features:

- sentence repetition exactness
- nonword repetition phoneme or syllable accuracy
- comprehension item accuracy
- error type by item complexity

Interpretation:

Accuracy should be separated from informativeness. A speaker can be inaccurate but still communicatively informative, or grammatically accurate but low-content.

### 3. Lexicon

Candidate transcript features:

- `ndw`
- `ttr`
- `hapax_ratio`
- noun/verb/adjective/adverb fractions
- content-word ratio
- function-word ratio
- word frequency and concreteness if added
- lexical specificity
- naming/retrieval task performance where available

Structured-task features:

- naming accuracy
- word retrieval latency if audio/time marks support it
- semantic category fluency if available

Interpretation:

Lexical weakness can mean small vocabulary, retrieval difficulty, semantic degradation, task unfamiliarity, bilingual exposure, or transcript length artifact. The report should show uncertainty when these cannot be separated.

### 4. Fluency And Acoustics

Candidate transcript features:

- `pause_per_utt`
- `filler_per_utt`
- `repetition_per_utt`
- `retracing_per_utt`
- utterance count and sample duration where available
- disfluency type counts in stuttering corpora

Candidate acoustic features:

- duration
- speech rate
- pause duration and distribution
- f0 mean/range/variability
- intensity mean/variability
- jitter
- shimmer
- harmonic-to-noise ratio
- voiced fraction
- openSMILE/eGeMAPS features
- AVQI where voice/motor-speech analysis is appropriate
- FluCalc or fluency-specific measures where available

Required controls:

- recording quality
- microphone/source
- clip duration
- speaker diarization quality
- child versus adult ASR reliability

Interpretation:

Acoustic features may be clinically meaningful signal or recording artifact. The report must include sample-quality warnings.

### 5. Content And Informativeness

Candidate features:

- expected concept coverage
- main concept complete/accurate score
- main concept partial score
- CIU-like ratio where labels exist
- task-specific event concept hits
- content efficiency: concepts per word or per utterance
- concept hierarchy/difficulty position
- missing high-value concepts

Task sources:

- AphasiaBank protocol tasks
- Cinderella/Salem
- ENNI/Gillam/Frog-style child narratives where rubrics can be built
- picture description tasks with known expected concepts

Interpretation:

Content is closer to functional communication than syntax alone. It is also task-dependent, so comparison must be task-matched.

### 6. Recoverability And Repairability

Candidate features:

- known target error rate
- unknown-intent rate
- near-threshold missed concepts
- concept appears in ASR/LLM alternatives but not 1-best
- clarification burden estimate
- unsafe reconstruction risk
- semantic overreach risk

Policy outputs:

- preserve raw
- ask clarification
- offer candidate options
- abstain
- never score reconstructed text as patient-produced assessment evidence

Interpretation:

Repairability is not the same as severity. A severe-looking sample with known targets may be more targetable than a fluent but unknown-intent sample.

### 7. Task Sensitivity

Candidate features:

- natural speech versus picture description delta
- narrative versus conversation delta
- sentence repetition versus spontaneous complexity delta
- nonword repetition versus lexical speech delta
- reading versus conversation disfluency delta
- task-specific content stability

Interpretation:

Task sensitivity is clinically important because tight tasks are interpretable but less ecological, while natural speech is ecological but noisy. Disagreement between tasks is a finding, not just nuisance.

### 8. Longitudinal Change

Candidate features:

- within-person state slopes
- reliable-change thresholds
- stable-score movers
- early-to-late prediction
- recovery versus persistence status
- change in content, complexity, fluency, or repairability separately

Required controls:

- same or comparable task across time
- sample length
- audio quality
- time between sessions
- intervention exposure where available

Interpretation:

The key question is whether state moves before broad scores move, and whether early state predicts later recovery or persistence.

### 9. Context And Fairness

Candidate metadata:

- age
- language exposure
- bilingual/multilingual status
- dialect/region proxy
- sex/gender where appropriate and consented
- education/grade
- SES proxy where ethically available
- hearing status
- motor speech status
- corpus/site
- task
- recording quality

Required audits:

- corpus prediction from features
- label prediction after corpus balancing
- age and MLU baselines
- task-held-out tests
- dialect/bilingualism sensitivity where metadata exists
- shuffled-label and random-feature controls

Interpretation:

A model that confuses language difference, task style, or recording source with disorder is clinically unsafe.

## State Report Mapping

| Report Section | Primary Feature Families | Required Caveats |
| --- | --- | --- |
| Sample quality | fluency/acoustics, context | poor audio, short sample, missing task labels |
| Overall state | all dimensions | not a diagnosis |
| Complexity | complexity, task sensitivity | age/task/sample-length dependent |
| Accuracy | accuracy, structured tasks | labels may be sparse |
| Lexicon | lexicon, content | transcript length and bilingual exposure matter |
| Fluency/acoustics | acoustic, disfluency | recording quality can dominate |
| Content/informativeness | content | task-specific rubrics needed |
| Recoverability | repairability, content | do not infer unknown intent |
| Change over time | longitudinal | requires comparable tasks |
| Next assessment questions | weak or divergent dimensions | not treatment prescription |

## Minimum Modeling Requirements

Every publishable model should report:

- participant-level split,
- corpus/task sensitivity,
- simple baselines,
- confidence intervals,
- shuffled-label or random-feature negative control,
- missing metadata caveats,
- feature-family ablations,
- sample-quality exclusions.

## Immediate Implementation

1. Build feature-family column lists for existing child and aphasia feature tables.
2. Add openSMILE/eGeMAPS features to the acoustic family.
3. Create a state-report v2 generator using this schema.
4. For each experiment, report which dimensions are supported by local data and which are missing.
