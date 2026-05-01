# Partner Profile List

**Date:** 2026-04-30
**Goal:** identify the kinds of collaborators who can help turn retrospective
language-state research into prospective, clinically meaningful evidence.

## Partnership Thesis

We do not need a famous senior PI to start. We need collaborators with one of
three assets:

1. access to longitudinal speech/language samples;
2. willingness to pilot a low-burden recorder workflow;
3. expertise in a disorder area where state measurement could change decisions.

Brian's guidance suggests a practical target: an assistant professor, clinic,
or center that has real patients/children and enough research infrastructure to
handle consent and IRB, but not so much bureaucracy that a pilot becomes a
five-year negotiation.

## Highest-Priority Partner Profiles

| priority | partner type | why they matter | what we offer | first ask |
|---:|---|---|---|---|
| 1 | DLD treatment lab | closest to original vision: profile + treatment response | recorder package, state reports, modeling, public Dryad replication | review EMT-SF/DLD modeling plan and advise on measures |
| 2 | Stuttering recovery lab | strongest longitudinal recovery question Brian flagged | FluencyBank feature pipeline, recovery prediction, acoustic/disfluency modeling | help access/interpret Purdue/Ratner/UMD-CMU data |
| 3 | Aphasia discourse/treatment lab | validates adult state reports and same-score/different-state claim | content/recoverability/acoustic report prototypes | review whether report dimensions map to useful SLP decisions |
| 4 | SLP training clinic | fastest pilot for low-burden sample collection | local recorder/export workflow and feedback loop | test workflow on simulated/non-sensitive samples |
| 5 | Aphasia life participation center | functional communication and longitudinal monitoring | conversation/narrative state reports | co-design meaningful functional report outputs |
| 6 | School-based SLP group | highest population reach and workflow pressure | child-language recorder protocol and minimal state reports | observe what data collection burden is realistic |

## Concrete Research Targets To Know

These are not cold-email instructions yet; they are orientation targets.

### DLD / Child Language Treatment

- University of Delaware TELL Lab studies treatment efficacy and language
  learning, including how and when children acquire language and how research
  can improve interventions: https://sites.udel.edu/chs-tell/
- University of Illinois Applied Psycholinguistics Lab has a "Maximizing
  Outcomes for Preschoolers With DLD" clinical-trial line using Enhanced Milieu
  Teaching plus sentence-focused targets:
  https://apl.shs.illinois.edu/current-projects/maximizing-outcomes-for-preschoolers-with-dld-clinical-trial/
- UCL's Better Conversations with DLD work is relevant because it focuses on
  conversation-level intervention rather than only word/sentence targets:
  https://discovery.ucl.ac.uk/id/eprint/10212074/

Why this profile matters: if the Dryad EMT-SF dataset produces any moderation
signal, these are the kinds of researchers who can tell us whether it is
clinically plausible or just statistical overfitting.

### Stuttering Recovery

- Purdue Stuttering Project is the most important target because FluencyBank's
  Purdue corpus followed nearly 200 children over three years and explicitly
  links early measures to recovery/persistence:
  https://www.purdue.edu/stutteringproject/
- FluencyBank Purdue corpus documentation lists recovery/persistence-relevant
  publications and notes partial CHAT conversion:
  https://talkbank.org/fluency/access/Purdue.html
- FluencyBank Ratner corpus includes children enrolled within three months of
  stuttering onset and matched fluent peers:
  https://talkbank.org/fluency/access/Password/Ratner.html
- FluencyBank UMD-CMU includes annual samples over three years and matched
  fluent children:
  https://talkbank.org/fluency/access/UMD-CMU.html

Why this profile matters: recovery/persistence is a cleaner first scientific
target than treatment optimization because the outcome is longitudinal and
clinically meaningful without needing treatment-dose data.

### Aphasia Discourse / Treatment

- AphasiaBank remains the infrastructure anchor:
  https://talkbank.org/aphasia/
- Aphasia discourse treatment generalization work, such as multilevel discourse
  outcomes after Semantic Feature Analysis, is directly aligned with our
  content-state questions:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11427423/
- Multimodal aphasia discourse work is relevant if we later add gesture/video:
  https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2024.1419311/full

Why this profile matters: adult aphasia is still our best validation sandbox
because we already have strong retrospective analyses and report prototypes.

## Partner Fit Rubric

Score each potential partner 0-2:

| criterion | 0 | 1 | 2 |
|---|---|---|---|
| longitudinal data | none | some repeated measures | repeated speech samples plus outcomes |
| treatment detail | none | broad intervention labels | target/dose/session-level detail |
| data-sharing feasibility | no path | request/DUA possible | existing public or TalkBank-compatible path |
| SLP workflow access | no clinicians | occasional review | active clinic/school/center |
| research alignment | adjacent | related | directly about treatment/recovery/state measurement |
| implementation speed | slow/unclear | moderate | can pilot in weeks/months |

Prioritize partners scoring high on longitudinal data, workflow access, and
implementation speed.

## First Outreach Package

Before contacting anyone, prepare:

- one-page project charter;
- SLP state report V2 examples;
- recorder workflow spec;
- privacy/IRB posture;
- one specific ask;
- clear statement that this is not a diagnostic product.

## Recommended First Asks

### For DLD Labs

"We found a public EMT-SF DLD trial dataset with baseline language-sample
variables and follow-up vocabulary/grammar outcomes. Would you be willing to
review whether our planned baseline-state-by-treatment-response analysis asks a
clinically meaningful question?"

### For Stuttering Researchers

"Brian suggested stuttering recovery may be the strongest longitudinal testbed.
We can build a participant-clean feature and recovery-prediction pipeline for
FluencyBank. What recovery labels and feature families would you trust?"

### For Aphasia Clinicians / Discourse Researchers

"We have a prototype state report showing content, unknown-intent risk,
recoverable errors, acoustics, and stable-score discourse movement. Which parts
would change your next assessment or therapy probe, and which are misleading?"

### For SLP Clinics

"Can we observe or simulate whether a local recorder/export workflow would fit
inside a real session without increasing documentation burden?"

## Near-Term Target Order

1. Rebekah and 1-2 practicing SLPs for report/workflow review.
2. Brian/Franklin for BA Web API/package compatibility questions.
3. DLD treatment researcher for the Dryad EMT-SF analysis plan.
4. FluencyBank/stuttering researcher for recovery label interpretation.
5. Local SLP clinic or assistant professor for pilot feasibility.
