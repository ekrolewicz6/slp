# Language State Modeling

This project studies whether human language ability can be modeled as a measurable, changing state rather than as a single clinical score or broad diagnosis.

The original vision was a closed-loop system for speech-language pathology:

```text
speech sample -> language state -> predicted change -> treatment target -> new speech sample
```

The current work has three connected tracks: child language and DLD as the highest-impact long-term clinical target, aphasia as the strongest current validation sandbox, and stuttering/recovery as a promising longitudinal testbed. Across all three, the practical question is the same: can transcripts, structured tasks, and audio reveal clinically meaningful state differences that broad scores and labels compress or miss?

This repository is research software. It is not a diagnostic tool, treatment recommender, or replacement for a speech-language pathologist.

## Current Thesis

Language difficulty is not well described by one score, one subtype label, or one surface measure like MLU. The data support a richer state model with at least these separable dimensions:

- how much expected content a speaker communicates
- how often the listener can infer the intended meaning
- whether missed content is known and repairable versus unknown
- how speech timing, pitch, voice quality, and other acoustic signals differ by subtype
- whether a patient is changing in discourse even when a broad clinical score is stable
- whether a child or adult is low-output for developmental, acquired, acoustic/motor, lexical, syntactic, task, or contextual reasons

The strongest current claim is not "AI can score aphasia." It is:

> Speech and language samples contain multiple measurable state variables, and those variables expose different clinical problems that broad scores and labels often collapse together.

After the 2026-04-29 discussion with Brian MacWhinney, the project direction is more concrete: measurement must come before treatment optimization; natural speech should be paired with tight tasks such as sentence repetition and nonword repetition; acoustic features should be standardized around tools such as openSMILE/eGeMAPS where possible; and data collection itself may be a central scientific bottleneck.

## Plain-English Summary

Many aphasia assessments produce a broad score that says roughly how impaired someone is. That is useful, but it can hide the reason the person is struggling.

Two people can have similar scores but very different communication problems. One may say very little. Another may say many words but miss the main point. Another may produce understandable pieces that need targeted clarification. Another may mainly show acoustic or fluency changes. A useful treatment system should not treat these as the same state.

This project is building the measurement layer for that idea. It asks whether existing public language datasets and future easy-to-collect samples can show:

- what information survived in a speech sample
- what information was expected but missing
- which errors are stable versus changing over time
- which changes are visible before standard clinical scores move
- where AI systems are useful, and where they are unsafe because they silently alter the evidence

The long-term goal remains treatment-response prediction. The near-term requirement is more basic: define reliable state measures, collect better longitudinal samples, and validate that the resulting reports mean something to SLPs.

## What We Have Learned

### 1. The original state-space idea survived, but changed shape

Early experiments on child language showed that transcript features can recover developmental structure. That validated the basic representation idea: language samples contain enough signal to place a speaker in a meaningful state space.

In aphasia, the result became more nuanced. Broad clinical subtype labels, such as Broca, Wernicke, Anomic, and Conduction, are not useless. They are strong signals. The better conclusion is that continuous language-state features add information to subtype labels rather than replacing them.

### 2. WAB-AQ is too coarse for many discovery questions

The Western Aphasia Battery Aphasia Quotient, or WAB-AQ, is a broad clinical severity score. It is useful, but it is often stable from session to session. Several experiments found that predicting the next WAB-AQ is not the best way to study short-term change.

More interesting changes appear inside discourse state variables: content, concept efficiency, known repair opportunities, unknown intent risk, and acoustic features.

### 3. Broca aphasia is low-output, but not simply "child-like"

An early result suggested Broca speech resembled early child language because both can have low mean utterance length. Later, stricter comparisons changed the interpretation.

The better current claim is:

> Broca aphasia can be low-MLU, but it is not just a reversion to child language. It appears more like a damaged adult language state with distinct structure.

That matters because it pushes against an oversimplified analogy and creates a more falsifiable scientific question.

### 4. Event content is one of the strongest interpretable signals

Across picture and story prompts, expected event content is highly informative. Instead of only measuring syntax or word count, the model asks whether the speaker communicated the concepts that the task made relevant.

The cross-prompt content experiments showed that observed content plus task information predicts aphasia severity well, and subtype plus content performs better still. This supports a practical direction for SLP: measure whether communication carries the intended ideas, not only whether it is grammatically rich.

### 5. Audio is useful, but not as a simple subtype classifier

The stricter openSMILE/eGeMAPS replication changed the acoustic story. Standard eGeMAPS features beat random and shuffled controls, but WAB severity still outperformed eGeMAPS for broad 4-way subtype classification.

The more defensible acoustic claim is narrower: timing, coverage, voice, pitch, and intensity features may add state information, especially when combined with clinical severity or discourse features. Audio should be treated as part of a mechanistic state report, not as a standalone aphasia-subtype diagnostic.

### 6. "Severe" or "floor" performance is not one thing

Low scores can come from different mechanisms:

- very low output
- high unknown-intent risk
- known but repairable target errors
- low content despite relatively low measured error
- mixed patterns

These distinctions matter because they imply different support strategies. A person who gives known but incorrect targets may need different help than a person whose intended message cannot be inferred at all.

### 7. Standard scores can miss real discourse movement

Longitudinal experiments found patients whose WAB-AQ stayed stable while discourse state moved. The reverse also appeared: some WAB changes were not mirrored by the measured discourse variables.

This does not prove clinical utility yet, but it suggests that discourse monitoring may detect changes that broad batteries miss.

### 8. AI reconstruction is not safe as measurement

ASR and generative reconstruction can make impaired speech look cleaner than it was, or introduce content the patient did not actually produce. That makes them dangerous if used as evidence of patient ability.

The current rule is a measurement firewall:

```text
raw human transcript or audio -> assessment
ASR / LLM reconstruction -> communication support only
```

AI may help a patient communicate, but reconstructed text should not be scored as if the patient independently produced it.

### 9. Clarification is safer than autonomous rewriting

Experiments with conservative local LLM reconstruction showed that fully automatic rewriting has limited utility and meaningful risk. Asking targeted clarification questions is safer, but can create a high burden.

Adding patient history improves controller decisions, especially deciding when to clarify, but it does not solve the problem by itself.

## Key Research Outputs

| Question | Main Output |
| --- | --- |
| Can expected task content predict severity? | `outputs/cross_prompt_content/summary.md` |
| Do content and intent-risk axes define useful states? | `outputs/two_axis_state_typology/summary.md` |
| What can we discover without clinician labels beyond the existing datasets? | `outputs/no_clinician_discovery/summary.md` |
| Can discourse move while WAB stays stable? | `outputs/stable_wab_movers/summary.md` |
| Is ASR or LLM reconstruction safe for assessment? | `outputs/measurement_firewall/summary.md` |
| Does patient history improve rewrite/clarify/abstain decisions? | `outputs/patient_history_controller/summary.md` |
| How useful is conservative local LLM reconstruction? | `outputs/local_llm_reconstruction_full_conservative/summary.md` |
| Would human confirmation make reconstruction safer? | `outputs/human_confirmation_simulation/summary.md` |
| What would an SLP-facing state report look like? | `outputs/slp_state_report_prototype/summary.md` |
| Can the state framework generalize to DLD/child language risk? | `outputs/dld_state_screening/summary.md` |
| Are DLD, late talking, and Broca aphasia the same low-output state? | `outputs/dld_cross_lifespan_state/summary.md` |
| Does the DLD screening signal survive uncertainty and corpus balancing? | `outputs/dld_review_grade_audit/summary.md` |
| Do late talkers catch up, and can early state predict that? | `outputs/dld_late_talker_catchup/summary.md` |
| Does early movement predict late-talker persistence better than earliest state? | `outputs/dld_late_talker_persistence_sensitivity/summary.md` |
| Is DLD screening mostly corpus/task artifact? | `outputs/dld_corpus_deconfounding/summary.md` |
| How sensitive are DLD results to noisy labels? | `outputs/dld_label_noise_sensitivity/summary.md` |
| Do child narrative tasks show a DLD state signal? | `outputs/dld_narrative_proxy/summary.md` |
| Does DLD signal transfer across narrative and natural-speech contexts? | `outputs/dld_task_context_comparison/summary.md` |
| What fairness audits are possible with current child metadata? | `outputs/dld_fairness_metadata_audit/summary.md` |
| What DLD targets would residual-state policies nominate? | `outputs/dld_target_policy_simulation/summary.md` |
| What outcome data are needed for clinically meaningful DLD work? | `outputs/dld_data_needs/summary.md` |
| How should Manchester Language Study data be integrated? | `outputs/dld_manchester_access_plan/summary.md` |
| What does the Dryad EMT-SF randomized DLD dataset show? | `outputs/dryad_emt_sf_treatment_pilot/summary.md` |
| Does early language-sample movement predict later treatment outcomes? | `outputs/dryad_early_movement_response/summary.md` |
| How could the state model generalize across SLP disorders? | `outputs/dld_cross_disorder_generalization_plan/summary.md` |
| What prospective DLD study would test the clinical claim? | `outputs/dld_prospective_study_blueprint/summary.md` |
| What did Brian MacWhinney's post-call guidance change? | `docs/brian_meeting_2026-04-29.md` |
| What should we do next, in order? | `docs/post_brian_ordered_task_list.md` |
| What is the current operating charter? | `docs/project_charter.md` |
| What is the minimum measurement battery? | `docs/minimum_language_state_battery.md` |
| Which local corpora contain structured tasks? | `outputs/structured_task_inventory/summary.md` |
| Can we run stuttering recovery locally now? | `outputs/stuttering_recovery_inventory/summary.md` |
| Which DLD/late-talker longitudinal data are local? | `outputs/dld_longitudinal_inventory/summary.md` |
| How do features map to SLP-readable state dimensions? | `docs/state_feature_schema.md` |
| Can the local environment compute standard openSMILE features? | `outputs/opensmile_smoke/summary.md` |
| Can AphasiaBank media be streamed for standard acoustic extraction? | `outputs/opensmile_aphasia_smoke/summary.md` |
| Do standard eGeMAPS features carry subtype signal under strict balanced-root tests? | `outputs/aphasia_standard_acoustic_replication/balanced84_model_summary.md` |
| Do custom Praat-style acoustic features outperform standard eGeMAPS on the same roots? | `outputs/aphasia_standard_acoustic_replication/feature_set_comparison_summary.md` |
| What is the current standard-acoustic replication takeaway? | `outputs/aphasia_standard_acoustic_replication/summary.md` |
| Can the same WAB score hide different state profiles? | `outputs/same_score_different_state_demo/summary.md` |
| Do stable-WAB patients show discourse or acoustic movement? | `outputs/stable_wab_movers/summary.md` |
| Are acoustic-only stable-WAB movers plausible signal or artifact? | `outputs/acoustic_mover_artifact_audit/summary.md` |
| Do acoustic-only movers survive a media-quality screen? | `outputs/acoustic_mover_media_quality_audit/summary.md` |
| Do acoustic-only movers survive utterance-aligned media review? | `outputs/acoustic_mover_utterance_quality_audit/summary.md` |
| What kinds of DLD label/state conflicts are most scientifically useful? | `outputs/dld_conflict_taxonomy/summary.md` |
| Which DLD/TD conflict cases should experts review first? | `outputs/dld_conflict_review_packet/summary.md` |
| What mechanisms explain the highest-value DLD/TD conflict cases? | `outputs/dld_conflict_mechanism_audit/summary.md` |
| Can late-talker trajectories be typed by early movement? | `outputs/late_talker_trajectory_typology/summary.md` |
| Does the late-talker early-movement result survive leave-one-child-out deletion? | `outputs/late_talker_leave_one_out_robustness/summary.md` |
| What are the bootstrap CIs and permutation nulls for late-talker early movement? | `outputs/late_talker_bootstrap_permutation/summary.md` |
| Which discoveries are strongest right now? | `docs/current_discovery_scorecard.md` |
| How should a recorder connect to TalkBank infrastructure? | `docs/ba_web_integration_notes.md` |
| Which treatment-response datasets can we actually model? | `outputs/treatment_response_inventory/summary.md` |
| What data-quality gates must future experiments pass? | `outputs/data_quality_gates/summary.md` |
| What should the SLP-facing state report contain? | `docs/slp_state_report_v2_spec.md` |
| What does the richer SLP report prototype produce? | `outputs/slp_state_report_v2/summary.md` |
| What packets can SLPs review now? | `outputs/slp_report_packets/summary.md` |
| What should a BA-Web-compatible recorder export? | `docs/ba_web_recorder_workflow_spec.md` |
| What task scripts should the recorder use? | `docs/recording_protocols.md` |
| What privacy/IRB posture should future collection use? | `docs/privacy_irb_plan.md` |
| Can we create a local recording package now? | `outputs/recorder_package_demo/summary.md` |
| What partner profiles should we pursue first? | `docs/partner_profile_list.md` |
| Is independent IRB feasible without university affiliation? | `docs/independent_irb_options.md` |
| What prospective pilot should we run first? | `docs/prospective_pilot_design.md` |
| What funding path fits this project? | `docs/funding_path_memo.md` |

The full experiment history is in `RESEARCH_LOG.md`. The original project specification is in `SPEC.md`.

## Current Checkpoint

As of 2026-05-01, the current local-data batch is complete. The project can now stream TalkBank media with the local cookie, run standard openSMILE/eGeMAPS extraction, compare standard and custom acoustic features, audit stable-WAB discourse/acoustic movers, and run the latest DLD label-noise, task-context, late-talker persistence, expert-review-packet, conflict-mechanism, and Dryad EMT-SF treatment-response checks.

The main conclusion from this batch is cautious but useful: the strongest publishable direction is multidimensional state measurement, not a standalone classifier. The late-talker results now make the best current child-language discovery thread more specific: early movement appears more meaningful than earliest severity. At the 0.75 z movement threshold, the final TD-band lift is 0.533 with bootstrap 95% CI [0.167, 0.842] and one-sided permutation p=0.011; persistent-gap reduction is 0.433 with bootstrap 95% CI [0.087, 0.769] and p=0.022. The acoustic-only mover result moved in the opposite direction: utterance-aligned media review still flags most candidate pairs as medium/high technical risk, leaving only one low-risk voice/pitch candidate for manual clinical audio review.

The DLD work now has a concrete expert-review path rather than only aggregate classifier metrics. The current packet contains 15 high-value DLD/TD conflict cases: 3 TD-labeled children whose language state looks risky without corpus shortcuts, and 12 cases where language-only risk remains high even when corpus/age priors do not. Mechanism audit splits those cases into sample-constrained, possible hidden TD risk, non-MLU language-state, language-not-corpus-prior, and low-output/MLU-aligned profiles. These cases define what an SLP or child-language researcher should inspect next.

The Dryad EMT-SF dataset changes the project materially because it is the first local dataset with randomized DLD intervention assignment and repeated outcomes. Transparent Python models show clearer grammar effects than short-term vocabulary effects, no robust baseline moderator after correction, and a strong early-movement signal: early language-sample movement predicts later T42/T49 grammar and vocabulary outcomes beyond baseline state and treatment group. Treatment assignment only weakly moves the aggregate early state, so this supports the measurement thesis more than a simple treatment-mediation story.

The next high-value work is blocked on fewer external inputs than before: FluencyBank recovery access, BA Web integration details, SLP review of the report packets, and access to raw transcript/audio or session-level EMT-SF dose/target data.

## Current Research Direction

The project should now be understood as a language-state measurement project for SLP, with five near-term scientific goals:

1. Harden the state model.
   - Replicate headline results under stricter patient-level splits, corpus-held-out tests, duplicate checks, and fold-clean preprocessing.
   - Confirm that acoustic subtype gains and Broca-versus-child separability survive conservative controls.

2. Turn discourse state into clinically meaningful constructs.
   - Separate content carried, unknown intent risk, known repair opportunities, acoustic/prosodic state, and longitudinal change.
   - Test whether these state dimensions explain different treatment-relevant problems hidden under the same WAB score.

3. Pair natural language samples with tighter tasks.
   - Inventory and model sentence repetition, nonword repetition, comprehension, narrative, picture description, and open conversation where data permit.
   - Treat natural speech as ecologically important but not sufficient by itself.

4. Build the data-collection path.
   - Explore a simple recorder/front end that can feed BA Web or TalkBank-compatible analysis rather than duplicating existing infrastructure.
   - Use pseudonyms and age, avoid names and dates of birth, and design around consent, IRB, and clinician workload from the start.

5. Build safe AI support around the measurement firewall.
   - Use raw transcript/audio for assessment.
   - Use ASR and generative models only for communication assistance, clarification, target discovery, and clinician-facing summaries unless clinically validated.

The project now also has a DLD and cross-lifespan extension in `DLD_LANGUAGE_STATE_SPEC.md`. That track asks whether the same state framework can explain developmental language disorder, late-talker catch-up, hidden DLD profiles, and early speech-state predictors of literacy or school outcomes. After Brian's feedback, DLD labels should be treated as noisy targets, not clean ground truth. Stuttering recovery should also be added as a high-priority longitudinal testbed because the available recovery data may be stronger than the current child language delay data.

## What Is Not Solved Yet

The project has not yet shown that its state variables improve patient outcomes. It also has not validated the state reports with practicing SLPs.

The largest remaining gaps are:

- prospective clinical validation
- therapy-response data with enough detail to test dosing policies
- external replication outside AphasiaBank-style tasks
- robust ASR uncertainty handling for impaired speech
- clinician review of whether the proposed state reports match useful decision-making
- easy recording/upload workflows that clinicians or families will actually use
- structured-task data paired with natural speech
- full all-corpus acoustic extraction beyond the current balanced84/common-root pilots
- first SLP usability review of the state report
- a partner-based prospective pilot with consented longitudinal samples and treatment exposure
- raw transcript/audio, treatment target, dose, and session-level metadata for the EMT-SF-style treatment-response question

For adaptive treatment optimization, datasets with intervention type, dose, timing, patient goals, and repeated outcome measures are still needed.

## Data

The project uses public or access-controlled language datasets, including:

- CHILDES for developmental language modeling
- AphasiaBank transcripts and metadata for aphasia discourse and WAB-linked analyses
- AphasiaBank media streamed from TalkBank for acoustic feature extraction when credentials are available
- task-specific prompts such as Cinderella and related discourse tasks for content-state modeling
- Dryad EMT-SF DLD randomized intervention data stored locally under gitignored `data/external/dryad_emt_sf_dld/`

Audio is not persisted by default. The acoustic pipeline streams media, extracts features, and deletes temporary WAV files.

## Reproducing Key Analyses

The exact command set changes as experiments are added, but the main current analyses are organized as scripts under `scripts/` and write summaries under `outputs/`.

Representative commands:

```bash
.venv/bin/python scripts/run_cross_prompt_content.py
.venv/bin/python scripts/run_two_axis_state_typology.py
.venv/bin/python scripts/run_stable_wab_mover_analysis.py
.venv/bin/python scripts/run_no_clinician_discovery_suite.py
.venv/bin/python scripts/run_measurement_firewall_experiment.py
.venv/bin/python scripts/run_patient_history_controller_addon.py
.venv/bin/python scripts/run_human_confirmation_simulation.py
.venv/bin/python scripts/run_dld_state_screening.py
.venv/bin/python scripts/run_dld_cross_lifespan_state.py
.venv/bin/python scripts/run_dld_review_grade_audit.py
.venv/bin/python scripts/run_dld_late_talker_catchup.py
.venv/bin/python scripts/run_late_talker_leave_one_out_robustness.py
.venv/bin/python scripts/run_late_talker_bootstrap_permutation_audit.py
.venv/bin/python scripts/run_dld_corpus_deconfounding.py
.venv/bin/python scripts/create_dld_conflict_review_packet.py
.venv/bin/python scripts/run_dld_conflict_mechanism_audit.py
.venv/bin/python scripts/run_dld_narrative_proxy.py
.venv/bin/python scripts/run_dld_fairness_metadata_audit.py
.venv/bin/python scripts/run_dld_target_policy_simulation.py
.venv/bin/python scripts/run_dryad_emt_sf_treatment_pilot.py
.venv/bin/python scripts/run_dryad_early_movement_response_pilot.py
```

Some experiments require AphasiaBank access, a TalkBank cookie, or a local LLM runtime.

## Repository Layout

```text
data/                 Local data and extracted features
outputs/              Experiment outputs and summaries
scripts/              Analysis and experiment scripts
tests/                Regression and data-integrity tests
RESEARCH_LOG.md       Chronological experiment record
SPEC.md               Original research specification
README.md             Current project overview
```

## Bottom Line

The project began as a search for a general language-state trajectory. It has become a more specific and more clinically grounded hypothesis:

> Better SLP measurement may come from modeling what information a person communicates, what remains ambiguous, what is repairable, how the acoustic signal behaves, how the person performs on tight elicitation tasks, and how those variables change over time.

That is the layer needed before closed-loop adaptive therapy can be scientifically credible.
