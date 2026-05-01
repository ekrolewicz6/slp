# Funding Path Memo

**Date:** 2026-04-30
**Status:** planning memo, not grant advice

## Bottom Line

There are two different funding stories:

1. **Scientific discovery:** build the evidence that language-state measurement
   predicts recovery, persistent risk, or treatment response.
2. **Product translation:** build a recorder/reporting system that clinicians,
   families, or researchers can use.

The project should not lead with a product grant yet. The strongest near-term
path is:

```text
existing-data results + SLP report usability
-> academic or clinical research partner
-> R21/R01-style measurement/recovery grant or partner-led pilot
-> SBIR/STTR only when the recorder/report product has a clear user and market
```

## Best NIH Fit

### NIDCD: primary fit

NIDCD is the best institute for the adult aphasia, stuttering, voice/speech,
and language-disorder parts of the work. Its Voice, Speech, and Language
Program explicitly covers diagnostic and intervention strategies for people with
communication impairments, including children with developmental language
disorder and adults with aphasia:
https://www.nidcd.nih.gov/research/extramural/voice-speech-language-program

NIDCD also frames its mission around hearing, balance, taste, smell, voice,
speech, and language, and supports basic, clinical, translational, and training
work:
https://www.nidcd.nih.gov/funding

Best-fitting NIDCD framing:

- multidimensional language-state measurement;
- stuttering recovery prediction;
- aphasia discourse-state monitoring;
- acoustic plus transcript biomarkers;
- clinically interpretable digital assessment;
- early translational work that can later inform treatment optimization.

### NICHD: child/DLD developmental fit

NICHD is relevant for the developmental child-language side, especially if the
question is language development, multilingualism, school-age outcomes, or
developmental risk rather than a specific communication-disorder treatment. Its
Child Development and Behavior Branch lists language development and
multilingualism in scope:
https://www.nichd.nih.gov/about/org/der/branches/cdbb

Best-fitting NICHD framing:

- developmental trajectories;
- late-talker catch-up versus persistence;
- child language risk and school outcomes;
- multilingual or demographic context;
- measurement infrastructure for developmental language research.

### NIA, NIMH, and others: later, not first

NIA could become relevant for dementia or primary progressive aphasia. NIMH
could become relevant for autism, psychosis, or mental-health-linked language
signals. These are not the first path unless we pivot the scientific question.

## Grant Mechanism Strategy

### First academic mechanism: R21 or pilot-style partner grant

An R21-like exploratory grant fits if the project is framed as a high-risk,
high-reward measurement and recovery-prediction study. NIH parent announcements
currently include R21 and other investigator-initiated mechanisms:
https://grants.nih.gov/funding/nih-guide-for-grants-and-contracts/parent-announcements

A strong R21 concept would be:

```text
Multidimensional speech-language state measurement for predicting recovery and
persistent risk across aphasia, DLD/late talking, or stuttering.
```

The application should be partner-led by an academic or clinical PI. Our role
would be technical collaborator, consultant, software lead, or subaward.

### R01: later, after pilot evidence

An R01 makes sense only after we have:

- review-grade retrospective results;
- SLP usability evidence;
- a feasible collection workflow;
- preliminary longitudinal signal;
- partner access to participants and outcomes.

The R01 should probably test one population deeply, not all SLP at once.

### SBIR/STTR: product route, not discovery-first route

NIH SBIR/STTR can fund small businesses, and NIH describes the programs as a
major non-dilutive source for early-stage small-business R&D. NIH SEED pages
state that the SBIR/STTR programs were reauthorized on April 13, 2026:
https://seed.nih.gov/small-business-funding/small-business-program-basics/understanding-sbir-sttr

Eligibility and structure matter. NIH SEED eligibility guidance is here:
https://seed.nih.gov/small-business-funding/small-business-program-basics/eligibility-criteria

SBIR/STTR is attractive only if we form a for-profit company or appropriate
small-business entity and can describe:

- a concrete technology innovation;
- customer/user need;
- commercialization path;
- feasibility milestones;
- research partner or clinical validation plan.

STTR is especially relevant if the product is co-developed with a university or
clinical lab. SBIR may be relevant if the company owns and executes most of the
R&D. Either way, this path is premature until the recorder/report product and
first user workflow are clearer.

## Non-NIH Paths

### ASHFoundation

The American Speech-Language-Hearing Foundation supports research in
communication sciences and disorders. Its New Century Scholars Research Grant
has offered grants up to $25,000:
https://www.ashfoundation.org/Apply/New-Century-Scholars-Research-Grant/

This is not enough for the full project, but it could support:

- SLP report usability study;
- small prospective pilot;
- de-identified report review;
- early-career collaborator involvement.

### PCORI

PCORI funds patient-centered comparative clinical effectiveness research:
https://www.pcori.org/funding-opportunities

PCORI is not the first step. It becomes relevant only when we are comparing
actual clinical strategies, such as different monitoring or treatment-selection
workflows, with patient-centered outcomes.

### Foundations and philanthropy

Foundation or philanthropic support may be useful for:

- open-source recorder/report tooling;
- data infrastructure;
- clinician usability;
- citizen-science sample collection;
- work that is too early or too infrastructure-heavy for NIH.

This path is flexible but usually needs a clear public-benefit story and
credible governance around privacy, data sharing, and clinical claims.

## Recommended Funding Sequence

### Stage 1: no external funding required

Complete these with current resources:

- openSMILE/eGeMAPS aphasia replication after TalkBank media auth works;
- Dryad EMT-SF treatment-response pilot after manual dataset download;
- SLP report usability review with de-identified examples;
- non-sensitive recorder feasibility;
- Brian/Franklin-compatible BA Web workflow notes.

Goal: create proof that the project is scientifically disciplined, not just
ambitious.

### Stage 2: small partner-supported pilot

Find one partner who can provide one of:

- child/DLD longitudinal samples and outcomes;
- stuttering recovery data;
- aphasia discourse samples plus clinical anchors;
- SLP workflow review access.

Funding target:

- ASHFoundation-style small grant;
- internal university pilot funds;
- departmental seed grant;
- small philanthropic gift.

Goal: get enough prospective and usability evidence for a serious NIH proposal.

### Stage 3: NIH exploratory grant

Best first NIH posture:

```text
R21-style measurement and recovery-prediction study, partner PI, project as
technical/software/data-science collaborator.
```

Pick one scientific lane:

- **Stuttering recovery:** strongest recovery-prediction framing if data access
  is real.
- **DLD/late-talker persistence:** highest population impact and closest to the
  original vision.
- **Aphasia state monitoring:** strongest current retrospective evidence and
  fastest measurement-validation paper.

### Stage 4: SBIR/STTR product translation

Only after the state report and recorder workflow are validated enough to define
a product:

- Phase I: feasibility of local recorder plus BA-Web-compatible reporting;
- Phase II: larger validation and deployment;
- STTR if university/lab partnership is central;
- SBIR if company-led development is central.

## What We Need Before Talking To Funders

The project needs a crisp one-page pitch for each path:

- **Science pitch:** broad clinical scores hide state mechanisms; state
  measurement predicts recovery/persistence/change better than labels.
- **Clinical pitch:** SLPs need a usable report that tells them what to probe
  next, not another uninterpretable score.
- **Data pitch:** current retrospective data are enough to justify a pilot, but
  treatment optimization needs prospective intervention exposure and outcomes.
- **Infrastructure pitch:** recorder and BA-Web-compatible packaging reduce the
  field's data-collection bottleneck.

## Near-Term Recommendation

Do not form an SBIR company or write an NIH application immediately.

Instead, use the next results to earn the right to ask for funding:

1. finish the strict acoustic replication;
2. run the public DLD treatment-response pilot if/when Dryad files are
   available;
3. create adult/child/stuttering report packets;
4. collect SLP usability feedback;
5. identify one partner-lab path;
6. then choose R21/R01 versus SBIR/STTR based on whether the next milestone is
   scientific discovery or product deployment.
