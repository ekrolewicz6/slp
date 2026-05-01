# Brian MacWhinney Meeting Notes

**Date:** 2026-04-29
**Participants:** Brian MacWhinney, Edan Krolewicz, Kristopher Weaver
**Context:** Follow-up call after sharing the pre-call research update in `docs/brian_research_update.md`.
**Caveat:** Notes are based on a computer-generated transcript and should be treated as a synthesis, not verbatim quotation.

## One-Sentence Takeaway

Brian broadly validated the direction, but sharpened the project: the highest-value work is not another classifier. It is building a reliable, easy-to-collect, multimodal language-state measurement layer that can eventually support longitudinal recovery and treatment-response questions.

## What Brian Confirmed

- The pre-call summary was accurate.
- The overall goal is sound, but execution is the hard part. The project needs concrete infrastructure, data-quality work, and careful task design.
- The field is ready for more data-driven assessment because many clinical tests are intuition-built, inconsistent, or not directly tied to treatment planning.
- Existing broad labels and scores are weak targets for AI if treated as ground truth.
- The clinically consequential question is longitudinal recovery and treatment response, but the data needed for that are sparse.

## Most Important Scientific Implications

### 1. Measurement Comes Before Treatment Optimization

Brian repeatedly returned to the same constraint: treatment-response prediction requires longitudinal data, and the available data are thin.

This means the near-term scientific target should be:

> Build a reliable language-state measurement layer first, then connect it to recovery and treatment once the right longitudinal data exist.

The project should not claim treatment optimization until it has:

- longitudinal recovery or treatment-linked data,
- transcript/audio samples across time,
- treatment type and dose,
- meaningful functional outcomes,
- clinician review of state reports.

### 2. DLD Is Important, But Weakly Labeled

Brian described DLD diagnosis as often impressionistic and vulnerable to confounds such as bilingualism, socioeconomic context, marginalization, personality/shyness, and school-environment mismatch.

Implication:

- DLD labels are useful for exploration but dangerous as hard ground truth.
- The project should distinguish language disorder from language difference and participation/context effects.
- DLD modeling must use fairness, corpus, age, bilingualism, dialect, task, and demographic audits before any clinical claim.

### 3. Stuttering May Be The Best Longitudinal Recovery Testbed

Brian noted that TalkBank has stronger longitudinal recovery data for children who stutter than for child language delay/DLD.

Implication:

- Add stuttering recovery as a high-priority track.
- Use it to test the general "early state predicts recovery" framework.
- Ask whether acoustic, disfluency, lexical, and interactional features predict spontaneous recovery versus persistent stuttering.

This may be the best available near-term dataset for a recovery-prediction result.

### 4. Natural Speech Is Necessary But Not Sufficient

Brian and Kristopher discussed whether normal conversation is enough for diagnosis or whether structured tasks are needed. Brian's answer was both.

Implication:

- Natural language samples capture ecological communication.
- Tight tasks capture interpretable capacities.
- The best assessment battery should combine natural speech with structured tasks.

Candidate structured tasks:

- sentence repetition,
- nonword repetition,
- comprehension tasks,
- narrative/story retell,
- picture description,
- conversation/open-ended discourse.

Sentence repetition is especially important because Brian said it can be automated and is a useful middle ground between unconstrained discourse and traditional tests.

### 5. Data Collection Is A Major Bottleneck

Brian agreed that clinicians often do not collect audio/language samples in routine practice, even when trained to value data collection.

His diagnosis:

- clinicians are overloaded,
- language-sample collection takes time,
- they may not know how to do it properly,
- unless it is extremely easy, it will not happen.

Implication:

> A recording front end may be as scientifically important as a model.

An app or lightweight recorder that feeds TalkBank/BA Web could produce more value than another offline experiment if it gets clinicians or families to collect usable data.

### 6. BA Web Is The Natural Infrastructure Target

Brian showed BA Web and described it as already supporting upload, transcription, acoustic analysis, and multiple analysis options.

Key points:

- BA Web is not widely used yet.
- Brian is willing to consider opening the web service.
- Opening the web service is different from opening the database.
- A recorder app should ideally connect to BA Web rather than duplicate TalkBank infrastructure.
- The app should collect age and pseudonymized identifiers, not names or dates of birth.
- The recording should avoid spoken names.

Implication:

> The product/infrastructure path should be "simple recorder -> BA Web analysis -> clinician/research output," not a parallel analysis silo.

### 7. EHR Data Is Not A Practical Near-Term Source

Brian and Kristopher both emphasized that EHR/hospital data access is extremely difficult because of HIPAA, data transfer agreements, and institutional review.

Implication:

- Do not make EHR extraction a near-term dependency.
- Favor prospective consent, schools, clinics, citizen-science workflows, or TalkBank-compatible upload pipelines.
- If collecting new data outside a university, investigate independent IRB.

### 8. Acoustic Features Need To Be Standardized

Brian pointed to standard acoustic feature sets:

- openSMILE,
- eGeMAPS,
- AVQI,
- FluCalc,
- standard vocal, fluency, motor-speech, and acoustic features.

He emphasized that these feature sets already provide the kitchen sink; the hard part is selecting what matters and ensuring the data quality is good enough.

Implication:

- Replace or supplement custom acoustic features with openSMILE/eGeMAPS.
- Run feature selection and stability analyses by disorder.
- Treat acoustic quality as both signal and possible measurement artifact.

### 9. Rich Output Beats One Score

Brian said clinicians need a rich output, not one score. He pointed to the second-language CAF framework:

- complexity,
- accuracy,
- lexicon,
- fluency.

He emphasized that acoustic fluency is especially important.

Implication:

The SLP-facing state report should be organized around multiple dimensions:

- complexity,
- accuracy/error profile,
- lexicon,
- fluency/acoustics,
- content/informativeness,
- recoverability/repairability,
- trajectory/change.

### 10. Keep Brian Updated, But Do Not Create Work For Him

Brian is open to receiving short research updates, bug reports, and remarkable findings, but he cannot take this on as an active project.

He mentioned that Franklin and Hojun have done substantial infrastructure work around Batchalign/BA Web/Batchalign 3 and that duplication should be avoided.

Implication:

- Send concise updates only when there is a real result or useful bug report.
- Share the GitHub repo.
- Avoid asking Brian/Franklin to do cleanup or ongoing supervision.
- If building infrastructure, align with BA Web and Batchalign 3 where possible.

## Revised Project Strategy

### Track A: Measurement Science

Goal: define reliable, multidimensional language-state measures across transcript, audio, and task.

Near-term work:

- harden aphasia state results,
- add openSMILE/eGeMAPS acoustic replication,
- add sentence repetition and nonword repetition tasks where data exist,
- map state dimensions to CAF plus content and repairability.

### Track B: Longitudinal Recovery

Goal: test whether early state predicts later change.

Near-term work:

- add stuttering recovery as a priority dataset,
- revisit Rescorla and Ellis Weismer for child language delay,
- keep aphasia stable-WAB mover and recovery analyses as adult validation.

### Track C: DLD And Child Language

Goal: use DLD as the highest population-impact domain, but treat labels cautiously.

Near-term work:

- avoid clinical screener claims,
- focus on developmental trajectories, fairness, and persistent-risk versus transient-delay,
- audit bilingual/dialect/SES/task confounds wherever metadata exists,
- use sentence repetition plus natural speech rather than natural speech alone.

### Track D: Data Collection Infrastructure

Goal: make speech/language sample collection easy enough to happen in practice.

Near-term work:

- design a mobile recorder/front end that uploads to BA Web,
- define minimal metadata and consent fields,
- build around pseudonyms and age, not identifiable names or birth dates,
- produce clinician and citizen-science workflows,
- investigate independent IRB or partner-lab options.

### Track E: Treatment-Response Inventory

Goal: identify whether treatment-response prediction is possible with existing data.

Near-term work:

- inventory aphasia treatment studies and Marian Brady-style meta-analyses,
- inventory child language/DLD intervention data,
- inventory stuttering recovery/intervention data,
- separate aggregate paper extraction from individual-level transcript-linked prediction.

## New Task Queue

### Brian-01: BA Web Recorder/App Feasibility Spec

Design a minimal recorder workflow:

- iOS/Android/web recorder,
- pseudonym plus age metadata,
- no names or dates of birth,
- recording protocol,
- upload to BA Web,
- result retrieval,
- SLP-facing interpretation,
- citizen-science mode,
- consent and IRB considerations.

### Brian-02: Sentence Repetition And Nonword Repetition Inventory

Find which TalkBank/CHILDES/clinical corpora include:

- sentence repetition,
- nonword repetition,
- comprehension tasks,
- structured elicitation tasks.

Then decide whether these can be paired with natural language samples.

### Brian-03: Stuttering Recovery Track

Inventory FluencyBank/stuttering longitudinal data and test:

- spontaneous recovery versus persistence,
- early disfluency/acoustic predictors,
- lexical/syntactic predictors,
- combined natural speech plus structured-task models.

### Brian-04: openSMILE/eGeMAPS Acoustic Replication

Replicate the acoustic aphasia findings using standard features:

- openSMILE,
- eGeMAPS,
- AVQI where relevant,
- FluCalc where relevant.

Compare against the current custom acoustic feature set.

### Brian-05: CAF Plus Content State Report

Redesign the SLP-facing state report around:

- complexity,
- accuracy,
- lexicon,
- fluency/acoustics,
- content/informativeness,
- recoverability/repairability,
- trajectory/change.

### Brian-06: DLD Label-Weakness Audit

Treat DLD/SLI labels as noisy targets and run:

- corpus/task artifact checks,
- bilingual/dialect/SES metadata audit,
- sensitivity to label definitions,
- models that separate language difference from language disorder where possible.

### Brian-07: Treatment-Response Evidence Inventory

Build a structured inventory of intervention evidence:

- child language/DLD,
- aphasia,
- apraxia/script therapy,
- stuttering,
- dementia if relevant.

Record whether each source has individual-level data, transcripts, audio, dose, goals, outcomes, and follow-up.

## Bottom Line

The project should keep the original vision, but the next phase should be more concrete:

> The field needs an easy way to collect speech/language samples, a richer measurement system than one score, and longitudinal evidence connecting state to recovery and treatment. The most immediate research value is validating the measurement layer and finding the best recovery datasets, especially stuttering and child language delay.
