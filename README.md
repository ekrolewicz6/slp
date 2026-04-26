# Language State Modeling

This project studies whether human language ability can be modeled as a measurable, changing state rather than as a single clinical score or broad diagnosis.

The original vision was a closed-loop system for speech-language pathology:

```text
speech sample -> language state -> predicted change -> treatment target -> new speech sample
```

The current work has moved from a developmental proof of concept into aphasia, where the practical question is sharper: can transcripts, discourse tasks, and audio reveal clinically meaningful differences that standard aphasia scores compress or miss?

This repository is research software. It is not a diagnostic tool, treatment recommender, or replacement for a speech-language pathologist.

## Current Thesis

Aphasia is not well described by one score or one subtype label. The data support a richer state model with at least these separable dimensions:

- how much expected content a speaker communicates
- how often the listener can infer the intended meaning
- whether missed content is known and repairable versus unknown
- how speech timing, pitch, voice quality, and other acoustic signals differ by subtype
- whether a patient is changing in discourse even when a broad clinical score is stable

The strongest current claim is not "AI can score aphasia." It is:

> A patient's speech contains multiple measurable state variables, and those variables expose different clinical problems that broad scores and labels often collapse together.

## Plain-English Summary

Many aphasia assessments produce a broad score that says roughly how impaired someone is. That is useful, but it can hide the reason the person is struggling.

Two people can have similar scores but very different communication problems. One may say very little. Another may say many words but miss the main point. Another may produce understandable pieces that need targeted clarification. Another may mainly show acoustic or fluency changes. A useful treatment system should not treat these as the same state.

This project is building the measurement layer for that idea. It asks whether existing public language datasets can show:

- what information survived in a speech sample
- what information was expected but missing
- which errors are stable versus changing over time
- which changes are visible before standard clinical scores move
- where AI systems are useful, and where they are unsafe because they silently alter the evidence

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

### 5. Audio changes the subtype picture

Text alone has trouble with some fluent aphasia distinctions, especially Wernicke-like profiles. Acoustic features improved subtype separation substantially in the latest acoustic experiments.

This suggests that some aphasia states are not only lexical or syntactic. Timing, rhythm, pitch variability, intensity, and voice quality may carry clinically relevant information that transcripts miss.

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
| Is DLD screening mostly corpus/task artifact? | `outputs/dld_corpus_deconfounding/summary.md` |
| Do child narrative tasks show a DLD state signal? | `outputs/dld_narrative_proxy/summary.md` |
| What fairness audits are possible with current child metadata? | `outputs/dld_fairness_metadata_audit/summary.md` |
| What DLD targets would residual-state policies nominate? | `outputs/dld_target_policy_simulation/summary.md` |
| What outcome data are needed for clinically meaningful DLD work? | `outputs/dld_data_needs/summary.md` |
| How should Manchester Language Study data be integrated? | `outputs/dld_manchester_access_plan/summary.md` |
| How could the state model generalize across SLP disorders? | `outputs/dld_cross_disorder_generalization_plan/summary.md` |
| What prospective DLD study would test the clinical claim? | `outputs/dld_prospective_study_blueprint/summary.md` |

The full experiment history is in `RESEARCH_LOG.md`. The original project specification is in `SPEC.md`.

## Current Research Direction

The project should now be understood as a language-state measurement project for SLP, with three near-term scientific goals:

1. Harden the state model.
   - Replicate headline results under stricter patient-level splits, corpus-held-out tests, duplicate checks, and fold-clean preprocessing.
   - Confirm that acoustic subtype gains and Broca-versus-child separability survive conservative controls.

2. Turn discourse state into clinically meaningful constructs.
   - Separate content carried, unknown intent risk, known repair opportunities, acoustic/prosodic state, and longitudinal change.
   - Test whether these state dimensions explain different treatment-relevant problems hidden under the same WAB score.

3. Build safe AI support around the measurement firewall.
   - Use raw transcript/audio for assessment.
   - Use ASR and generative models only for communication assistance, clarification, target discovery, and clinician-facing summaries unless clinically validated.

The project now also has a DLD and cross-lifespan extension in `DLD_LANGUAGE_STATE_SPEC.md`. That track asks whether the same state framework can explain developmental language disorder, late-talker catch-up, hidden DLD profiles, and early speech-state predictors of literacy or school outcomes.

## What Is Not Solved Yet

The project has not yet shown that its state variables improve patient outcomes. It also has not validated the state reports with practicing SLPs.

The largest remaining gaps are:

- prospective clinical validation
- therapy-response data with enough detail to test dosing policies
- external replication outside AphasiaBank-style tasks
- robust ASR uncertainty handling for impaired speech
- clinician review of whether the proposed state reports match useful decision-making

For adaptive treatment optimization, datasets with intervention type, dose, timing, patient goals, and repeated outcome measures are still needed.

## Data

The project uses public or access-controlled language datasets, including:

- CHILDES for developmental language modeling
- AphasiaBank transcripts and metadata for aphasia discourse and WAB-linked analyses
- AphasiaBank media streamed from TalkBank for acoustic feature extraction when credentials are available
- task-specific prompts such as Cinderella and related discourse tasks for content-state modeling

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
.venv/bin/python scripts/run_dld_corpus_deconfounding.py
.venv/bin/python scripts/run_dld_narrative_proxy.py
.venv/bin/python scripts/run_dld_fairness_metadata_audit.py
.venv/bin/python scripts/run_dld_target_policy_simulation.py
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

> Better SLP measurement may come from modeling what information a person communicates, what remains ambiguous, what is repairable, how the acoustic signal behaves, and how those variables change over time.

That is the layer needed before closed-loop adaptive therapy can be scientifically credible.
