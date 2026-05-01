# Prospective Pilot Design

**Date:** 2026-04-30
**Status:** protocol design, not an IRB submission

## Bottom Line

The first prospective work should not try to prove treatment optimization.
That claim needs treatment type, dose, goals, repeated samples, and outcomes.

The highest-learning sequence is:

```text
SLP usability pilot with mock/de-identified reports
-> local recorder feasibility with non-sensitive samples
-> partner-based longitudinal pilot in one population
-> treatment-response pilot only after measurement and workflow survive
```

The first patient-facing pilot should be chosen by data access, not ambition.
If we can access FluencyBank recovery data or a stuttering clinic, stuttering
recovery is the cleanest first longitudinal science case. If we can access a
school or child-language clinic, DLD/late-talker state tracking is the highest
population-impact path and closest to the original vision. If aphasia access is
easiest, adult aphasia is the best measurement-validation sandbox but should
avoid treatment claims at first.

## Why A Prospective Pilot Is Needed

The retrospective work has shown that language samples can expose separable
state dimensions: content carried, unknown-intent risk, recoverability, acoustic
state, structural complexity, lexical access, fluency, and longitudinal movement.

It has not shown that these dimensions change SLP decisions or improve outcomes.
That requires a prospective workflow where samples, state reports, decisions,
and outcomes are all captured in the same system.

## Pilot 0: SLP Report Usability, No Patient Collection

**Purpose:** Determine whether the state report is understandable, trustworthy,
and decision-relevant before collecting patient data.

**Participants:** 5-15 practicing SLPs, beginning with trusted reviewers.

**Materials:**

- adult aphasia report examples from existing AphasiaBank analyses;
- child/DLD report examples from CHILDES/DLD retrospective analyses;
- stuttering report wireframes if recovery data are not yet available;
- short explanation of what the report may and may not claim.

**Tasks for reviewers:**

1. Read 3-6 reports.
2. Identify what they think is the main communication problem.
3. Choose the next assessment probe they would run.
4. Mark confusing, misleading, or missing fields.
5. Say whether the report would change their next clinical action.

**Primary outcomes:**

- comprehension of each report field;
- perceived usefulness;
- perceived risk of misinterpretation;
- changes to next-assessment decisions;
- missing information needed for trust.

**Decision rule:** Do not collect patient data until SLPs can interpret the
report without model-internal explanation and can identify at least one concrete
way it could guide assessment or monitoring.

## Pilot 1: Local Recorder Feasibility, Non-Sensitive Samples

**Purpose:** Test whether the collection workflow is easy enough to run before
using it with clinical participants.

**Participants:** project members, healthy adult volunteers, or simulated users.

**Battery:**

- consent and setup screen;
- pseudonym and age only, no DOB or names;
- natural conversation prompt;
- picture description or narrative retell;
- sentence repetition;
- nonword repetition;
- optional comprehension item;
- local validation and export package.

**Primary outcomes:**

- completion time;
- failed recordings;
- missing metadata;
- audio quality flags;
- package validation failures;
- user confusion points;
- whether the exported package is BA-Web-compatible.

**Decision rule:** Move to patient-facing collection only when a nontechnical
user can complete the workflow without raw media entering Git, cloud storage, or
unreviewed sharing.

## Pilot 2: Child Language / DLD State Tracking

**Why this matters:** This is closest to the original vision and likely the
largest population-impact target. DLD diagnosis is noisy, and SLPs need better
ways to understand which children are likely to catch up, persist, or respond
to specific intervention profiles.

**Best setting:** school-based SLP group, university child-language clinic, or
DLD treatment lab.

**Population:**

- ages 3-7;
- children referred for language concerns, late talkers, or DLD/LI labels;
- optional typically developing comparison group;
- record language exposure and bilingual context where possible.

**Timepoints:**

- baseline;
- 6-8 weeks;
- 12-16 weeks;
- 6 months;
- 12 months if feasible.

**Minimum battery:**

- natural parent/clinician-child interaction;
- narrative or story retell;
- picture description;
- sentence repetition;
- nonword repetition;
- brief comprehension probe;
- parent or teacher functional-language rating;
- current treatment goals and weekly dose if the child receives services.

**Outcomes to capture:**

- later language score if available;
- goal attainment or progress-monitoring score;
- narrative/content state change;
- school participation or teacher rating;
- intervention type, frequency, duration, and targets;
- whether the child was discharged, escalated, or changed goals.

**Primary scientific question:**

Can early multidimensional language state predict persistent risk or early
response better than age, MLU, broad test score, and diagnosis label?

**Key model comparison:**

```text
age + MLU + label
vs.
age + MLU + structured tasks
vs.
age + MLU + natural speech
vs.
full state model + intervention exposure
```

**Decision rule:** A useful result is not just high classification accuracy.
The target is calibrated risk or response prediction with interpretable state
dimensions that explain why two similar children need different next probes or
monitoring plans.

## Pilot 3: Stuttering Recovery Prediction

**Why this matters:** Brian emphasized that many young children who stutter
recover, but the clinically important question is who will persist and who needs
more intensive support. This may be the cleanest recovery-prediction test if
longitudinal FluencyBank data or a fluency clinic partner is available.

**Best setting:** fluency clinic or FluencyBank-connected research group.

**Population:**

- preschool or early school-age children who stutter;
- early in course when recovery/persistence is unknown.

**Timepoints:**

- baseline;
- 3 months;
- 6 months;
- 12 months;
- 24 months if feasible.

**Minimum battery:**

- natural speech;
- structured story or picture task;
- reading or repetition when age-appropriate;
- parent severity rating;
- clinician fluency severity rating;
- treatment exposure and dose.

**Outcomes to capture:**

- recovered versus persistent status;
- severity trajectory;
- treatment escalation;
- participation/avoidance rating if available.

**Primary scientific question:**

Can early acoustic, disfluency, linguistic, and task-state features predict
recovery/persistence beyond age, sex, baseline severity, and simple disfluency
counts?

## Pilot 4: Adult Aphasia State Monitoring

**Why this matters:** AphasiaBank is the strongest current validation sandbox,
and adult aphasia reports can quickly test whether broad WAB scores hide
clinically meaningful state differences. This is the fastest path to a
measurement paper, but not the first treatment-optimization paper.

**Best setting:** aphasia center, life participation group, university clinic,
or adult outpatient SLP partner.

**Population:**

- adults with chronic or subacute aphasia;
- include subtype and WAB/subtest scores when available, but do not require
  subtype to define the state.

**Timepoints:**

- baseline;
- every 4-6 weeks for 3-6 months;
- optional post-therapy or post-program sample.

**Minimum battery:**

- conversation/interview;
- picture description;
- narrative retell;
- repetition if feasible;
- naming/retrieval probe if partner already collects one;
- WAB subtests or short clinical anchors when available.

**Outcomes to capture:**

- WAB subtests or AQ if already administered;
- goal attainment;
- SLP-rated communication change;
- content-state movement;
- stable-score mover status;
- treatment exposure and dose if available.

**Primary scientific question:**

Do discourse/audio state variables detect clinically meaningful movement before
or beyond WAB-AQ, and do SLPs judge the resulting reports as useful?

## Recommended Order Right Now

1. **Run Pilot 0 with de-identified or synthetic reports.** This is the fastest
   way to learn whether the report has clinical value and what is missing.
2. **Finish recorder feasibility with non-sensitive samples.** This validates
   the workflow before consent and IRB work.
3. **Use existing data to choose the first patient-facing population.** The
   first choice should be whichever of FluencyBank, DLD treatment data, or adult
   aphasia partner access becomes real first.
4. **Do not start treatment-response claims until intervention exposure is
   captured.** Treatment optimization is the north star, but premature claims
   would weaken the project.

## Minimum Data Dictionary For Any Prospective Pilot

Every prospective sample should include:

- pseudonymous participant ID;
- age in months or years, not DOB;
- language exposure;
- task ID and prompt version;
- recording date relative to enrollment, not necessarily calendar date in
  shared data;
- population label and source;
- current clinical label, if known;
- raw audio retention consent flag;
- TalkBank deposit consent flag;
- transcript status: human, ASR, checked ASR, or unavailable;
- quality flags;
- current treatment type;
- current treatment target;
- session frequency and dose;
- current functional goal;
- outcome measures and dates;
- withdrawal/deletion status.

## Analysis Plan

For each prospective pilot:

1. Run data-quality gates before modeling.
2. Compute state dimensions from raw transcript/audio, not reconstructed text.
3. Fit baselines first: age, broad score, label, MLU, sample length.
4. Add natural speech features.
5. Add structured-task features.
6. Add acoustic/openSMILE features where audio quality is sufficient.
7. Add treatment exposure only when it is measured with enough detail.
8. Report participant-level splits, bootstrap confidence intervals, and
   negative controls.
9. Report what the model cannot infer.

## What Would Make This Field-Changing

The meaningful result is not "AI diagnoses DLD" or "AI scores aphasia."

The meaningful result would be:

```text
For the same broad score or diagnosis, the state report separates patients into
different mechanisms of difficulty, predicts different trajectories, and changes
what an SLP would assess or monitor next.
```

That is the bridge from measurement to treatment optimization.
