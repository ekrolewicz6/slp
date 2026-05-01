# Ordered Task List After Brian MacWhinney Call

**Date:** 2026-04-30
**Source context:** `docs/brian_meeting_2026-04-29.md` and local-only transcript in `docs/private/`.

## Executive Decision

Do not jump straight to treatment optimization, a DLD diagnostic classifier, or a full mobile app.

Brian's guidance implies this order:

```text
define what to measure
-> inventory which data/tasks exist
-> standardize feature extraction
-> run the best longitudinal recovery experiments
-> validate rich SLP-facing reports
-> then build the recorder/BA Web collection workflow
-> then pursue prospective data and treatment-response modeling
```

The immediate goal is a credible measurement and recovery-prediction program, not a clinical product claim.

## Operating Rules

- **Measurement before treatment.** No treatment recommendation claims until there are treatment type, dose, goals, repeated samples, and outcomes.
- **Rich profile before one score.** Output should describe complexity, accuracy, lexicon, fluency/acoustics, content, repairability, and change.
- **Natural speech plus tight tasks.** Conversation is ecologically valid but not enough; sentence repetition and nonword repetition are priority structured tasks.
- **DLD labels are weak targets.** Treat DLD/SLI labels as noisy anchors, not clean ground truth.
- **Use standard acoustic features.** Replicate custom acoustic work with openSMILE/eGeMAPS, AVQI, and FluCalc where appropriate.
- **Do not duplicate TalkBank infrastructure.** If building collection tools, align with BA Web/Batchalign rather than creating a parallel silo.
- **No EHR dependency.** EHR/hospital data access is too slow and institution-specific for the near-term plan.
- **Keep Brian's burden low.** Send concise updates only when there is a result, bug report, or specific low-effort infrastructure question.

## Phase 0: Lock The Strategy

**Goal:** Make sure the project has one coherent operating plan.

- [x] **0.1 Create a one-page project charter.**
  - State the mission: language-state measurement for SLP.
  - State the long-term goal: treatment-response prediction.
  - State the near-term goal: reliable multidimensional state measurement and recovery prediction.
  - State non-claims: not diagnostic, not treatment recommender, not replacing SLPs.
  - Deliverable: `docs/project_charter.md`.
  - Done when: a new collaborator can read one page and understand the project.

- [x] **0.2 Define the first three publishable claims we are trying to test.**
  - Claim A: broad scores/labels hide separable state dimensions.
  - Claim B: early state can predict recovery better than simple baselines in at least one longitudinal disorder dataset.
  - Claim C: a rich SLP-facing state report is more clinically useful than a one-score classifier.
  - Deliverable: short section in `docs/project_charter.md`.
  - Done when: every experiment can be mapped to one of these claims or cut.

- [x] **0.3 Create a live project board from this document.**
  - Columns: Backlog, Doing, Blocked, Done, Rejected.
  - Keep task IDs from this plan.
  - Deliverable: GitHub Projects, Linear, Notion, or a local `TASKS.md`.
  - Done when: you have a single place to track work without scanning the full research log.

## Phase 1: Define The Measurement Battery

**Goal:** Decide what an ideal sample should include before building models or an app.

- [x] **1.1 Specify the minimum SLP language-state battery.**
  - Natural conversation or interview.
  - Picture description.
  - Narrative/story retell.
  - Sentence repetition.
  - Nonword repetition.
  - Optional comprehension task.
  - Optional patient/caregiver or parent/teacher rating.
  - Deliverable: `docs/minimum_language_state_battery.md`.
  - Done when: every task has a purpose and expected output dimension.

- [x] **1.2 Define adult aphasia versus child-language variants.**
  - Adult aphasia: picture description, narrative, conversation, repetition, naming/retrieval if available, acoustic fluency.
  - Child language/DLD: natural speech, sentence repetition, nonword repetition, narrative, comprehension, parent/teacher context.
  - Stuttering: natural speech, structured reading/repetition if available, disfluency profile, acoustic timing.
  - Deliverable: task-by-population table.
  - Done when: the battery is not one-size-fits-all but still uses shared dimensions.

- [x] **1.3 Define the state dimensions.**
  - Complexity.
  - Accuracy/error profile.
  - Lexicon.
  - Fluency/acoustics.
  - Content/informativeness.
  - Recoverability/repairability.
  - Longitudinal change.
  - Context/fairness metadata.
  - Deliverable: state-dimension schema.
  - Done when: every model feature maps to an interpretable state dimension or is marked exploratory.

- [x] **1.4 Define the SLP-facing output before modeling.**
  - One-page summary.
  - Example transcript excerpts.
  - Strengths.
  - Breakdown types.
  - Uncertainty.
  - Change since prior sample.
  - "Do not infer" safety notes.
  - Deliverable: revised state-report wireframe.
  - Done when: Rebekah or another SLP can say whether the report would be useful.

## Phase 2: Inventory The Data We Can Actually Use

**Goal:** Find the highest-value existing data before building new infrastructure.

- [x] **2.1 Structured-task inventory across local TalkBank/CHILDES data.**
  - Search for sentence repetition, nonword repetition, comprehension, narrative, picture description, reading, and conversation.
  - Record whether audio exists.
  - Record whether participants also have natural speech.
  - Deliverable: `outputs/structured_task_inventory/summary.md`.
  - Done when: we know which corpora support natural-plus-tight-task modeling.

- [x] **2.2 Stuttering recovery data inventory.**
  - Inventory FluencyBank or other stuttering corpora available locally or requestable.
  - Identify longitudinal participants.
  - Identify recovery/persistence labels or inferable endpoints.
  - Record audio availability and task types.
  - Deliverable: `outputs/stuttering_recovery_inventory/summary.md`.
  - Done when: we know whether stuttering can support the first recovery-prediction paper.

- [x] **2.3 DLD/late-talker longitudinal inventory.**
  - Revisit Rescorla and Ellis Weismer.
  - Track Manchester Language Study access.
  - Track E-DLD and other requestable datasets.
  - Identify outcome variables: language, literacy, school, participation, intervention exposure.
  - Deliverable: updated `outputs/dld_data_needs/summary.md`.
  - Done when: we know which DLD questions are answerable now versus prospective only.

- [x] **2.4 Treatment-response evidence inventory.**
  - Child language/DLD intervention studies.
  - Aphasia treatment and recovery studies.
  - Apraxia/script therapy.
  - Stuttering treatment/recovery.
  - Dementia where relevant.
  - For each source: individual data, transcript, audio, dose, goals, outcome, follow-up, access.
  - Deliverable: `outputs/treatment_response_inventory/summary.md`.
  - Done when: we can say honestly whether treatment-response modeling is possible from existing data.
  - Result: inventory complete. The 2026 Dryad EMT-SF DLD randomized-trial
    dataset is the first public treatment-response pilot, but CLI download is
    blocked by Dryad/AWS WAF and needs manual browser download. RELEASE is
    scientifically important but not locally modelable without IPD access.

- [x] **2.5 Infrastructure inventory: BA Web, Batchalign, CLAN, KidEval.**
  - Identify what inputs BA Web accepts.
  - Identify what outputs BA Web returns.
  - Identify whether there is an API or only web upload.
  - Identify where Batchalign 3 is going so we do not duplicate it.
  - Deliverable: `docs/ba_web_integration_notes.md`.
  - Done when: we have a concise question list for Brian/Franklin, not a vague ask.
  - Result: initial inventory complete; API/auth/upload details remain a specific
    question list for Brian/Franklin.

## Phase 3: Standardize Feature Extraction

**Goal:** Make the measurement layer defensible and comparable to existing work.

- [x] **3.1 Build a standard acoustic extraction path.**
  - Add openSMILE/eGeMAPS extraction.
  - Add AVQI if voice/motor-speech analysis is feasible.
  - Add FluCalc or fluency/disfluency features where available.
  - Preserve current custom acoustic features for comparison.
  - Deliverable: standard acoustic feature tables and script.
  - Done when: the aphasia acoustic results can be rerun with standard features.
  - Result: openSMILE/eGeMAPS local and streaming scripts exist. The local WAV
    smoke test succeeds; the AphasiaBank streaming smoke currently fails because
    the media request returns the TalkBank/SLA auth modal instead of MP4 bytes.
    Full replication is now task 4.7 after auth is refreshed.

- [x] **3.2 Build a shared CAF-plus-content feature map.**
  - Complexity: MLU, clauses, syntax proxies.
  - Accuracy: error tags, morphology, retracing, revisions where available.
  - Lexicon: diversity, specificity, word classes, retrieval proxies.
  - Fluency: pauses, timing, disfluencies, acoustic duration/rhythm.
  - Content: expected concepts, CIU/main-concept proxies.
  - Repairability: known target versus unknown intent.
  - Deliverable: `docs/state_feature_schema.md`.
  - Done when: every report dimension has computable candidate features.

- [x] **3.3 Add data-quality gates.**
  - Audio duration and quality.
  - Missing/invalid time marks.
  - ASR confidence where available.
  - Transcript length and speaker-role checks.
  - Duplicate participant/window checks.
  - Corpus/task leakage checks.
  - Deliverable: reusable audit script.
  - Done when: every headline model can fail fast on bad data.
  - Result: `scripts/run_data_quality_gates.py` and
    `outputs/data_quality_gates/summary.md` now audit duplicate IDs,
    participant leakage, missingness/all-zero artifacts, time marks, and media
    auth.

## Phase 4: Run The Highest-Value Existing-Data Experiments

**Goal:** Use current data to find a real scientific result before building an app.

### Priority 1: Stuttering Recovery

- [ ] **4.1 First-pass stuttering recovery model.**
  - Predict recovery/persistence from early samples.
  - Baselines: age, sex if available, simple disfluency count, sample duration.
  - Full model: acoustic, disfluency, lexical, syntactic, task features.
  - Deliverable: `outputs/stuttering_recovery_baseline/summary.md`.
  - Done when: we know whether early state predicts recovery better than simple baselines.

- [ ] **4.2 Stuttering feature ablation.**
  - Acoustic only.
  - Disfluency only.
  - Lexical/syntactic only.
  - Natural speech only.
  - Structured task only if available.
  - Combined model.
  - Deliverable: ablation table with patient-level CIs.
  - Done when: we know which signals actually carry recovery information.

- [ ] **4.3 Stuttering robustness audit.**
  - Participant-level splits.
  - Corpus/site held out if possible.
  - Shuffled-label controls.
  - Random-feature controls.
  - Bootstrap CIs.
  - Deliverable: review-grade summary.
  - Done when: result is either strong enough to share with Brian or clearly falsified.

### Priority 2: DLD Label-Weakness And Persistent Risk

- [x] **4.4 DLD label-noise sensitivity.**
  - Compare label definitions: SLI, LI, DLD-like, late talker.
  - Test corpus/task artifact strength.
  - Test age/MLU baselines.
  - Deliverable: `outputs/dld_label_weakness_audit/summary.md`.
  - Done when: we can state what current DLD labels can and cannot support.
  - Result: `scripts/run_dld_label_noise_sensitivity.py` and
    `outputs/dld_label_noise_sensitivity/summary.md` treat DLD/SLI labels as
    noisy anchors. Full-language models remain informative under simulated
    10-20% label noise, but 82 high-confidence label/corpus/state conflicts
    show why this should be framed as measurement disagreement, not diagnosis.

- [x] **4.5 DLD structured-task plus natural-speech experiment.**
  - Use corpora with both natural and tight tasks if found.
  - Compare natural-only, structured-only, and combined models.
  - Deliverable: `outputs/dld_structured_plus_natural/summary.md`.
  - Done when: we know whether Brian's "both" claim improves measurement.
  - Result: `scripts/run_dld_task_context_comparison.py` and
    `outputs/dld_task_context_comparison/summary.md` show strong within-context
    DLD signal but weak narrative/natural-speech transfer. This supports a
    prospective battery that pairs natural speech with structured tasks.

- [x] **4.6 Late-talker and DLD persistent-risk rerun.**
  - Use better longitudinal labels if found.
  - Predict later language/literacy/school outcome if available.
  - Baselines: age, MLU, early broad score.
  - Deliverable: updated longitudinal summary.
  - Done when: either early state predicts persistence, or we document why current data cannot answer it.
  - Result: `scripts/run_dld_late_talker_persistence_sensitivity.py` and
    `outputs/dld_late_talker_persistence_sensitivity/summary.md` show that
    earliest state alone is weak, but 36-to-48-month movement predicts later
    TD-band and persistent-gap status better in Rescorla.

### Priority 3: Aphasia Validation Sandbox

- [x] **4.7 openSMILE/eGeMAPS aphasia replication.**
  - Replicate current acoustic subtype gains with standard features.
  - Compare custom features versus standard features.
  - Ablate timing, pitch, voice quality, intensity.
  - Deliverable: `outputs/aphasia_standard_acoustic_replication/summary.md`.
  - Done when: the acoustic finding either survives standardization or is downgraded.
  - Result: TalkBank media auth works, balanced 48-root and 84-root eGeMAPS
    pilots are complete, and the custom-vs-standard audit is complete on 83
    common roots. eGeMAPS beats random/shuffled controls but WAB-only is
    stronger in 4-way subtype classification. Timing/coverage is the strongest
    eGeMAPS feature family. Custom Praat-style features add a modest increment
    over WAB on the balanced common 80-root subset, but the earlier larger
    custom-feature advantage was sample-sensitive. This downgrades the acoustic
    subtype-classifier claim and redirects the acoustic work toward mechanism
    and state-report validation.

- [x] **4.8 Same-score different-state demonstration.**
  - Select matched WAB-AQ pairs with different content, recoverability, and acoustic profiles.
  - Generate report examples.
  - Deliverable: curated examples for clinician review.
  - Done when: examples make the "one score is not enough" claim obvious.
  - Result: `scripts/run_same_score_different_state_demo.py` and
    `outputs/same_score_different_state_demo/summary.md` identify 11,398
    same-subtype pairs within WAB-AQ diff <= 2.0 with substantial state-plan
    contrasts.

- [x] **4.9 Stable-score mover replication.**
  - Reconfirm discourse-state movement under stable WAB.
  - Add standard acoustic features if possible.
  - Deliverable: updated stable-mover summary.
  - Done when: we know whether this is robust enough to pitch as a measurement paper.
  - Result: `scripts/run_stable_wab_mover_analysis.py` and
    `outputs/stable_wab_movers/summary.md` find 66 stable-WAB discourse movers,
    17 stable-WAB acoustic movers among 110 stable pairs with acoustic coverage,
    and 11 acoustic-only falsification candidates.

- [x] **4.10 Acoustic-only mover artifact audit.**
  - Audit the stable-WAB acoustic-only mover set for likely signal versus
    recording/session artifacts.
  - Deliverable: `outputs/acoustic_mover_artifact_audit/summary.md`.
  - Done when: acoustic-only cases are separated into manual-review candidates
    versus likely artifact/quantity shifts.
  - Result: `scripts/run_acoustic_mover_artifact_audit.py` labels 6 cases as
    likely voice/pitch state changes, 3 as possible recording/sample artifacts,
    and 2 as quantity/transcription shifts.

## Phase 5: Build The Clinician-Facing Report

**Goal:** Convert state modeling into something an SLP can judge.

- [x] **5.1 Redesign the state report around CAF plus content.**
  - Complexity.
  - Accuracy.
  - Lexicon.
  - Fluency/acoustics.
  - Content/informativeness.
  - Recoverability/repairability.
  - Trajectory/change.
  - Deliverable: `outputs/slp_state_report_v2/example_report_cards.md`.
  - Done when: the report is readable without knowing the model internals.
  - Result: `docs/slp_state_report_v2_spec.md`,
    `scripts/run_slp_state_report_v2.py`, and
    `outputs/slp_state_report_v2/summary.md` now add structural, lexical,
    fluency, acoustic, longitudinal, quality, and next-probe fields.

- [x] **5.2 Create three report sets.**
  - Adult aphasia examples.
  - Child DLD/late-talker examples.
  - Stuttering recovery examples if data support it.
  - Deliverable: de-identified report packet.
  - Done when: each report includes uncertainty and "do not infer" warnings.
  - Result: `scripts/create_slp_report_packets.py` writes
    `outputs/slp_report_packets/`. Adult aphasia cards use real V2 report rows;
    child/DLD cards separate late-talker trajectory examples from residual-state
    target/probe examples; stuttering is currently a wireframe/data-source
    packet because local recovery data are unavailable.

- [ ] **5.3 Run informal SLP review.**
  - Start with Rebekah and 1-3 trusted SLPs.
  - Ask: understandable, useful, misleading, missing, would it change next assessment?
  - Deliverable: `outputs/slp_report_review/summary.md`.
  - Done when: we know whether the report is clinically meaningful or just computationally interesting.

## Phase 6: Design The Recorder And BA Web Path

**Goal:** Make future data collection realistic without duplicating TalkBank.

- [x] **6.1 BA Web recorder workflow spec.**
  - User types: clinician, researcher, family/citizen-science participant.
  - Metadata: pseudonym, age, language(s), task, consent, optional sex/gender where appropriate.
  - Explicit exclusions: no names, no DOB, no spoken names.
  - Output: upload package compatible with BA Web.
  - Deliverable: `docs/ba_web_recorder_workflow_spec.md`.
  - Done when: it can be sent to Brian as a low-effort concrete proposal.
  - Result: local-first package workflow, manifest schema, validation gates,
    and Brian/Franklin API questions are now documented.

- [x] **6.2 Recording protocol scripts.**
  - Adult aphasia protocol.
  - Child language/DLD protocol.
  - Stuttering protocol.
  - Include instructions for headphones/speaker separation for repetition tasks.
  - Deliverable: `docs/recording_protocols.md`.
  - Done when: a nontechnical clinician could run the protocol.
  - Result: adult aphasia, child/DLD, and stuttering recording scripts are now
    drafted with universal setup, task prompts, metadata, stop rules, and the
    ASR/LLM scoring boundary.

- [x] **6.3 Privacy and consent packet.**
  - Consent language draft.
  - Data handling diagram.
  - Pseudonymization rules.
  - Audio retention/deletion choices.
  - Independent IRB versus partner-lab options.
  - Deliverable: `docs/privacy_irb_plan.md`.
  - Done when: we know the path to prospective data without pretending HIPAA/EHR will be easy.
  - Result: local-first privacy posture, consent tiers, spoken-PHI handling,
    IRB paths, repository rules, and pre-collection checklist are drafted.

- [x] **6.4 Build a local-only recorder prototype.**
  - Record audio.
  - Capture metadata.
  - Export package.
  - Do not upload anywhere by default.
  - Deliverable: minimal app or web prototype.
  - Done when: the workflow can be tested without handling real patient data.
  - Result: `scripts/create_recording_package.py` creates and validates local
    package folders. Demo output: `outputs/recorder_package_demo/summary.md`.

- [ ] **6.5 Add BA Web integration only after workflow review.**
  - Manual upload first.
  - API/web-service integration later if Brian/Franklin confirm path.
  - Deliverable: integration plan or prototype.
  - Done when: it uses TalkBank infrastructure rather than bypassing it.

## Phase 7: Prospective Study And Partnership Path

**Goal:** Prepare for the data that would actually answer treatment questions.

- [x] **7.1 Identify partner profiles.**
  - Local assistant professor.
  - SLP clinic.
  - school-based SLP group.
  - aphasia life participation center.
  - stuttering clinic.
  - Deliverable: target collaborator list.
  - Done when: each target has a clear reason to care.
  - Result: `docs/partner_profile_list.md` prioritizes DLD treatment labs,
    stuttering recovery labs, aphasia discourse/treatment labs, clinics, aphasia
    life participation centers, and school-based SLP groups.

- [x] **7.2 Independent IRB feasibility.**
  - Cost.
  - Timeline.
  - Minimal-risk protocol requirements.
  - Consent and data retention.
  - Deliverable: `docs/independent_irb_options.md`.
  - Done when: we know whether university affiliation is required for the next data step.
  - Result: `docs/independent_irb_options.md` concludes that independent IRB
    review is feasible but should not be the default first move. The project
    should first use existing data, SLP review, simulated recorder workflows,
    and partner conversations, then choose independent IRB only for a concrete
    prospective protocol.

- [x] **7.3 Prospective pilot design.**
  - Population: choose one first, probably stuttering recovery or child language risk.
  - Timepoints.
  - Battery.
  - Outcome measures.
  - Intervention exposure.
  - Clinician burden.
  - Deliverable: prospective pilot protocol.
  - Done when: this could become an IRB submission.
  - Result: `docs/prospective_pilot_design.md` defines the ordered pilot path:
    SLP report usability, non-sensitive recorder feasibility, then a
    partner-based longitudinal pilot in child/DLD, stuttering, or adult aphasia
    depending on which data access path becomes real first.

- [x] **7.4 Funding path memo.**
  - NIH fit by institute and mechanism.
  - SBIR feasibility.
  - Foundation options.
  - Why a research partner is needed.
  - Deliverable: `docs/funding_path_memo.md`.
  - Done when: the funding route is concrete enough to discuss with a potential academic partner.
  - Result: `docs/funding_path_memo.md` separates the science route from the
    product route. The recommended path is partner-led NIDCD/NICHD-style
    measurement and recovery science first, then SBIR/STTR product translation
    only after the recorder/report workflow has user evidence and deployment
    shape.

## Phase 8: Communication With Brian And Franklin

**Goal:** Preserve the relationship and avoid creating work for them.

- [x] **8.1 Send one concise post-call thank-you and GitHub link.**
  - Include the public repo link.
  - Mention that the transcript is private/local only.
  - Mention that we are prioritizing measurement, stuttering recovery, structured tasks, and BA Web alignment.
  - Ask no open-ended labor-intensive questions.
  - Done when: Brian has context but no burden.
  - Result: draft update is in `docs/brian_research_update.md`; send after the
    GitHub push is complete.

- [ ] **8.2 Only send future updates at decision points.**
  - Strong stuttering recovery result.
  - BA Web recorder spec ready for review.
  - Bug report or data issue.
  - Clinician report prototype ready.
  - Done when: every email has a concrete artifact and one clear ask.

- [ ] **8.3 Prepare a Franklin-specific technical note only if needed.**
  - Inputs/outputs.
  - No philosophical framing.
  - Where we can integrate with BA Web/Batchalign.
  - Done when: there is a technical reason to involve him.

## Deprioritize For Now

- [ ] Do not build a direct DLD diagnostic classifier as the main product.
- [ ] Do not build a full cloud app before the battery, report, privacy path, and BA Web workflow are specified.
- [ ] Do not rely on EHR data.
- [ ] Do not treat WAB-AQ, aphasia subtype, or DLD label as clean ground truth.
- [ ] Do not use LLM reconstruction as the assessment source of truth.
- [ ] Do not ask Brian or Franklin for broad project management help.
- [ ] Do not chase new model architectures before the measurement/data questions are settled.

## First-Week Queue Status

The initial first-week queue is complete except for items blocked by external
data/access/review. Project charter, minimum battery, structured-task
inventory, stuttering inventory, openSMILE/eGeMAPS setup, BA Web recorder
workflow, and the Brian follow-up draft now exist. The next runnable work
requires one of: manual Dryad download, FluencyBank access, BA Web API details,
or SLP review.

## First Decision Gate

After the structured-task and stuttering inventories, decide:

- If stuttering has usable longitudinal recovery labels, make it the first recovery-prediction paper.
- If stuttering data are not usable, prioritize aphasia stable-score mover plus standard acoustic replication as the first measurement paper.
- If structured child-language tasks exist with enough overlap, run the natural-plus-tight-task DLD experiment.
- If none of the existing data can answer recovery, pivot to the recorder/prospective-data path sooner.

## North Star

The project should become the system that makes this loop scientifically credible:

```text
easy sample collection
-> reliable transcript/audio/task state
-> rich SLP-interpretable report
-> longitudinal recovery prediction
-> treatment-response learning
```

Everything that does not strengthen one part of that loop should be delayed or cut.
