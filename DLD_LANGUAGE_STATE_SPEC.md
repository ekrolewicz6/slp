# DLD And Cross-Lifespan Language State Spec

## Purpose

This spec adds a Developmental Language Disorder and child-language track to the language-state project.

The project should not become only an aphasia project. Aphasia gave us a strong test case because AphasiaBank has discourse samples, clinical scores, subtype labels, and repeated sessions. DLD is the natural next test because it asks whether the same state framework can help earlier in life, before language difficulties become entrenched in school, literacy, social participation, and long-term educational outcomes.

The cross-lifespan thesis is:

> Language ability can be represented as a measurable state across development, disorder, injury, and recovery, but the same surface score can hide different mechanisms.

DLD is high leverage because estimates in English-speaking countries are often around 7% of young children, and the disorder is widely under-identified. See the CATALISE terminology work and recent prevalence summaries:

- Bishop et al. / CATALISE terminology consensus: https://www.disturboprimariolinguaggio.it/wp-content/uploads/2020/02/Bishop2017terminology.pdf
- Raine Study DLD prevalence paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC9804624/

## Relationship To The Aphasia Track

Aphasia and DLD answer complementary scientific questions.

In aphasia, an adult language system is damaged. The key discovery was that broad labels and scores compress different communication states: content carried, unknown intent risk, repairability, acoustic/prosodic state, and longitudinal change.

In DLD, the language system is developing atypically. The central question is whether early speech samples reveal:

- which children are delayed but likely to catch up
- which children have persistent risk
- whether DLD is one broad delay axis or several distinct developmental profiles
- which treatment targets are most likely to improve functional communication
- whether the state variables generalize beyond aphasia

The DLD track should reuse the aphasia lesson: do not stop at classification. The goal is mechanism and target discovery.

## Current Data

Already local:

- `data/features/phase1_windowed_features.parquet`
  - Eng-NA and Eng-UK typically developing CHILDES windows
  - Clinical-Eng windows including TD, SLI/DLD-like, late talker, hearing loss, Down syndrome, and other groups
- `data/features/childes_window_embeddings.parquet`
  - semantic embeddings for CHILDES windows
- raw CHILDES bundles under `data/raw/`

Current limitations:

- Clinical-Eng labels are encoded in corpus paths, not a harmonized metadata table.
- Some corpora are longitudinal, but participant IDs need careful reconstruction from filenames.
- DLD labels are historically named SLI or LI in many corpora.
- Many corpora mix task type, age, site, and diagnostic group, so corpus-held-out tests are mandatory.
- Literacy, school, participation, and treatment outcomes are not yet consistently available locally.

## Main Scientific Questions

### Q1. Persistent Risk Versus Transient Delay

Can early language-state trajectories distinguish children who catch up from children whose language risk persists?

High-value endpoints:

- later language-state gap
- persistent SLI/DLD label where available
- narrative weakness at school age
- literacy or academic outcomes if obtainable

Initial experiments:

- Train a TD-only developmental age/state model.
- Apply it to late talkers and SLI/DLD corpora.
- Measure whether language-age gap closes, remains stable, or widens.
- Test whether early residual state predicts later residual state better than MLU alone.

### Q2. Natural Speech Screening

Can short transcript windows classify DLD/SLI risk better than age plus MLU, under participant-held-out and corpus-held-out splits?

Required controls:

- age-only baseline
- MLU plus age baseline
- full language-feature model without corpus/path features
- participant-level metrics, not only window-level metrics
- leave-corpus-out tests wherever both classes exist
- shuffled-label and random-feature controls before any strong claim

Target claim:

> Natural speech contains DLD risk signal beyond age and MLU, and the signal survives at least partial corpus transfer.

### Q3. Hidden DLD State Subtypes

Is DLD a single low-language axis, or are there separable profiles?

Candidate profiles:

- grammar/morphosyntax weakness
- low lexical diversity or retrieval weakness
- weak narrative/event content
- high disfluency or repair burden
- phonological/speech-sound burden where data supports it
- low output versus high-output/low-content profiles

Initial experiments:

- Residualize features against TD age norms.
- Cluster SLI/DLD children on residual state.
- Characterize clusters by feature deviations.
- Test whether clusters are stable across corpus, age, and task.

### Q4. Treatment Target Prioritization

Can the state model identify better therapy targets than generic age norms?

Without treatment-outcome data, this must remain a simulation:

- Identify near-threshold deficits rather than easiest or hardest skills.
- Compare target policies: weakest feature, nearest recoverable feature, age-salient feature, random feature, and clinician-generic proxy.
- Ask which policy should move the child farthest toward the TD manifold with the smallest hypothetical change.

The target policy should be framed as hypothesis generation, not treatment recommendation.

### Q5. Literacy And School Outcome Prediction

This is probably the highest-impact DLD question, but likely needs more data.

Can early speech state predict later reading, writing, narrative, academic, or participation outcomes better than broad diagnosis?

Needed data:

- longitudinal child language corpora with later literacy or school measures
- standardized test scores
- teacher/parent ratings
- reading and writing outcomes
- intervention history

If no public data is available, the project should produce a data-needs memo rather than overclaim.

### Q6. Fairness And Language Difference

A screening model that confuses dialect, bilingualism, socioeconomic context, or task style with disorder would be harmful.

Required audits:

- corpus/site effects
- dialect or region proxies
- age and sex where available
- bilingual or multilingual status where available
- task type effects
- recording/transcription source effects

Any DLD screening claim is not credible without this.

### Q7. Cross-Lifespan Universality

Do aphasia and DLD share state dimensions, or are they qualitatively different?

Experiments:

- Map DLD, TD, AphasiaBank controls, and PWA into a shared feature space.
- Compare subspace angles and nearest-neighbor distances.
- Test whether Broca-like low-output adult states differ from DLD low-output child states.
- Ask whether content, repairability, and acoustic state are lifespan-general or disorder-specific.

This is the route to the largest scientific claim.

## Experiment Queue

### DLD-00: Data Inventory And Label Audit

Build a Clinical-Eng inventory with reconstructed participant IDs, labels, ages, tasks, corpora, and longitudinal coverage.

Output:

- label counts
- corpus by label counts
- participant counts
- age coverage
- repeated-measure coverage
- known label ambiguities

### DLD-01: TD Normative State And Language-Age Gap

Train TD-only developmental models on Eng-NA/Eng-UK and apply them to Clinical-Eng.

Output:

- normative age model performance
- language-age gap by TD, SLI/DLD, late talker, and other groups
- whether SLI/DLD looks like delay alone or delay plus distinct residual pattern

### DLD-02: Natural-Speech DLD Screening Baselines

Classify TD versus SLI/DLD and TD versus late talker under participant-held-out CV.

Output:

- age-only, MLU+age, full-language, and language-age-gap baselines
- window-level and participant-level metrics
- confidence intervals
- corpus-held-out sensitivity

### DLD-03: Catch-Up Versus Persistent-Risk Trajectories

For children with repeated observations, model whether state gaps close or persist.

Output:

- per-child state slopes
- catch-up rate by label and corpus
- early-state predictors of later-state gap

### DLD-04: DLD State Subtypes

Cluster SLI/DLD participants on age-residualized language features.

Output:

- cluster profiles
- top residual feature deviations
- stability across corpus and age bins
- comparison with aphasia state axes

### DLD-05: Treatment-Target Policy Simulation

Simulate which feature or concept target would move a child most efficiently toward TD age norms.

Output:

- near-threshold versus weakest-target comparison
- target class frequencies by DLD subtype
- uncertainty-aware target rankings

### DLD-06: Literacy And School Outcome Data Search

Inventory public/requestable datasets with later literacy, school, or functional outcomes.

Output:

- dataset list
- access/licensing constraints
- required fields
- feasibility ranking

### DLD-07: Fairness And Artifact Audit

Test whether models are learning disorder risk or corpus/task/dialect artifacts.

Output:

- corpus prediction from features
- label prediction after corpus balancing
- leave-corpus-out performance
- failure examples and excluded claims

### DLD-08: Cross-Lifespan State Comparison

Compare TD, DLD, adult controls, and aphasia in one shared state space.

Output:

- subspace angles
- nearest-neighbor distances
- low-output DLD versus Broca separability
- shared versus disorder-specific state axes

## Success Criteria

A DLD result becomes publishable only if it survives:

- participant-level splitting
- corpus-held-out sensitivity where possible
- age-only and MLU+age baselines
- corpus/task artifact checks
- confidence intervals
- clear separation between screening, mechanism, and treatment claims

The strongest possible finding would be:

> Early natural speech contains stable, interpretable language-state dimensions that distinguish transient delay from persistent DLD risk and expose treatment-relevant profiles hidden by broad labels.

## What Would Make This Clinically Important

This track matters if it can help answer one of these:

- Which children need monitoring versus immediate intervention?
- Which children are likely to catch up?
- Which language targets are most likely to improve functional communication?
- Which children are being missed by broad screening tools?
- Which children are being over-flagged because the model confuses language difference with disorder?

Until those are validated, this remains a measurement and discovery program.

