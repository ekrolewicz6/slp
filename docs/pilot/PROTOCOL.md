# Pilot Protocol — Personalized Dose-Response in Post-Stroke Aphasia

**Working title:** A feasibility study of ambient daily language-state
measurement and within-patient micro-randomized therapy-activity dosing in
chronic aphasia.

**Version:** 0.1 (draft) · **Date:** 2026-04-26 · **Status:** pre-IRB draft

> ⚠️ **This is an engineering/scientific draft, not a finished regulatory
> document and not medical or legal advice.** It must be completed and
> reviewed with a clinical PI, an IRB/ethics board, and an institutional
> data-privacy officer before any human-subjects activity. Items in
> `{{double braces}}` are institution-specific placeholders. The study is
> designed as **minimal-risk measurement-and-feasibility research**: no
> clinical decisions are made from its outputs.

Companion: [STRATEGY.md](../../STRATEGY.md) (§4 is the source of this
pilot), [outcome_instrument.md](outcome_instrument.md) (the primary
outcome), [RESEARCH_LOG.md](../../RESEARCH_LOG.md) #50–#51.

---

## 1. Background & rationale

Aphasia therapy faces an unsolved dosing problem: *how much, what kind, for
whom* is decided by clinical intuition, not individualized evidence.
Outcome is measured rarely and coarsely (a clinician-administered battery
at intake/discharge), so the trajectory between visits — and each patient's
response to specific activities — is invisible.

This pilot tests whether two capabilities are feasible together: (a)
**ambient daily measurement** of a patient's language state from a short
self-recorded speech sample plus a brief self-report, and (b)
**within-patient micro-randomization** of the therapy activity delivered
each day, logged with known probability so the per-patient dose-response
can be estimated causally. It is the smallest study that produces evidence
of a kind that does not currently exist: a *personalized*, causally-grounded
estimate of which activity most improves an individual's communication,
against a continuous real-world signal.

It is explicitly **not** a treatment-efficacy trial. No participant's care
is directed by the system; their usual clinical care continues unchanged.

## 2. Objectives & endpoints

**Primary objective — feasibility.** Can chronic-aphasia participants
complete daily app-based measurement + a randomized daily activity over 8
weeks at acceptable adherence and burden?
- *Primary endpoints:* (1) adherence = proportion of days with a completed
  check-in (target ≥ 60% median); (2) retention = proportion completing 8
  weeks (target ≥ 70%); (3) burden = mean daily task time and a usability
  rating.

**Co-primary objective — measurement & estimation feasibility.** Can the
daily language-state estimate be produced and the per-patient dose-response
be estimated from the randomized log?
- *Endpoints:* (4) measurement yield = proportion of speech samples that
  produce a valid state estimate; (5) test–retest reliability of the daily
  estimate on stable days; (6) per-patient dose-response estimates with
  bootstrap CIs (partial-pooling estimator, §9) — reported descriptively.

**Secondary/exploratory.** Concurrent validity of the daily language-state
estimate vs a clinician-administered standard (WAB-AQ and/or the
communicative-participation instrument) at baseline and exit; association
between the learned state and the functional-communication outcome;
qualitative participant feedback.

> No hypothesis test of treatment effect is powered or claimed. The
> dose-response estimates are feasibility outputs to size a future trial.

## 3. Study design

Single-group, **8-week within-patient micro-randomized trial (a series of
n-of-1 designs)**. Each participant receives, once per day, one therapy
activity selected by **uniform random assignment** over the candidate
activity set (§6). Daily measurement (§7) is collected before/independently
of the activity. The uniform design is chosen over an adaptive bandit for
the pilot because it maximizes causal identifiability (bounded, known
propensities for every activity every day) — see RESEARCH_LOG #50 §3 and
the power analysis (§10). Adaptive allocation is deferred to a later study
once measurement validity is established.

## 4. Population

**Target N:** {{8}} participants (range 5–12; see §10).

**Inclusion:** adults ≥ {{18}}; chronic aphasia (≥ {{6 months}}
post-onset) following a single left-hemisphere stroke; sufficient
auditory/reading comprehension to engage with an aphasia-friendly app
(assessed by the clinical team); access to a compatible smartphone;
capacity to provide informed consent or available legally authorized
representative.

**Exclusion:** severe global aphasia precluding app use; significant
uncorrected hearing/vision impairment; degenerative neurological disease;
concurrent enrollment in a conflicting interventional trial; clinician
judgment that daily participation poses undue burden.

## 5. Recruitment & consent

Recruitment via {{clinical partner site}} outpatient SLP caseload.
**Aphasia-adapted informed consent is mandatory:** simplified,
aphasia-friendly consent materials (short sentences, supporting images,
key points highlighted), unhurried sessions, teach-back to confirm
understanding, and a formal capacity assessment by a clinician not
otherwise pressuring enrollment. Where capacity is in question, a legally
authorized representative consents and participant assent is sought.
Participants may withdraw at any time without affecting their care.

## 6. Intervention (the randomized activity set)

The candidate activities (the "arms") are evidence-based aphasia practice
tasks deliverable in-app, e.g.:
- **Naming** — confrontation/word-retrieval practice (lexical).
- **Syntax** — sentence construction/ordering practice (morphosyntactic).
- **Conversation** — scripted/structured conversational turns (pragmatic).
- **Script** — personally-relevant scripted-speech practice.

The final set, content, and difficulty calibration are defined with the
clinical PI. Each day, one activity is drawn uniformly at random and
delivered; the assignment, its probability (1/K), and timestamp are logged.
Activity dose (duration/intensity) is held constant in the pilot to isolate
*type*; dose becomes a second randomized factor in a later study.

> All activities are standard-of-care practice tasks; none is experimental.
> Randomization concerns *which* ordinary activity is suggested on a given
> day, not whether the participant receives therapy.

## 7. Measurements & schedule of assessments

| Assessment | Baseline | Daily | Weekly | Exit (wk 8) |
|---|:--:|:--:|:--:|:--:|
| Clinician language battery (WAB-AQ or equivalent) | ✓ | | | ✓ |
| Daily speech sample (~3–5 min, in-app) | | ✓ | | |
| Daily EMA (3 items, [outcome_instrument.md](outcome_instrument.md)) | | ✓ | | |
| Weekly communicative-participation composite | ✓ | | ✓ | ✓ |
| Randomized activity delivered + logged | | ✓ | | |
| Adherence / burden / usability | | (auto) | ✓ | ✓ |

The daily speech sample is processed **on-device** into a non-invertible
pooled embedding → calibrated language-state estimate; the raw waveform is
discarded (§8). The functional-communication outcome is computed from the
EMA + weekly items (Leap 2). The realized daily change in the
language-state (and/or functional) signal is the reward for the
dose-response analysis.

## 8. Data management & privacy

Privacy posture (non-negotiable, STRATEGY.md §6; implemented in
`src/app/daily_checkin.py`):
- **No raw audio leaves the device and none is retained.** Each sample is
  embedded locally; the waveform is discarded immediately after embedding.
- Only the pooled embedding (a non-invertible summary), the derived state
  estimate, the self-report scores, and activity/assignment metadata are
  stored — the minimum needed for the analysis.
- Data are de-identified with a study ID; the linkage key is held
  separately under {{institutional}} controls.
- Storage, encryption (in transit and at rest), access control, retention,
  and destruction follow {{institutional data-governance policy}} and
  applicable law ({{HIPAA / GDPR / local}}).
- Participants consent specifically to the embedding-and-discard pipeline
  and to which de-identified data are shared.

## 9. Statistical analysis plan

**Feasibility endpoints** (§2 primary): summarized descriptively
(proportions with exact CIs; medians/IQR for burden).

**Per-patient dose-response** (`src/closed_loop/pilot_analysis.py`): within
each participant, estimate each activity's state-adjusted effect (reward
per unit headroom) with a bootstrap 90% CI. Because daily assignment is
randomized with known probability, within-patient comparisons are causally
identified. **Estimation uses empirical-Bayes partial pooling:** each
participant's per-activity effect is shrunk toward the cohort/phenotype
mean for that activity, which materially improves small-sample precision
(§10). A participant's recommended activity is the top effect; it is
flagged "confidently separated" when its CI lower bound exceeds the
runner-up's estimate.

**Measurement validity** (secondary): test–retest reliability (ICC) of the
daily estimate on clinician-identified stable days; concurrent validity vs
the baseline/exit clinician battery (Pearson/Spearman).

**Analyses are descriptive and hypothesis-generating.** No confirmatory
treatment-effect test is performed.

## 10. Sample-size justification

Sizing is by *feasibility precision* and the personalized-estimation yield,
not a treatment-effect power calculation. The yield was simulated under
realistic measurement noise and per-patient effect heterogeneity
(`scripts/pilot_power.py`, 150 replicate pilots/cell; RESEARCH_LOG #51):

| N | Weeks | Point accuracy | % confident | Conf. precision | Yield |
|--:|--:|--:|--:|--:|--:|
| 8 | 8 | 67% (pooled) | 46% | 84% | 38% |
| 8 | 8 | 62% (naive) | 29% | 81% | 24% |
| 12 | 8 | 72% (pooled) | 49% | 88% | 43% |

Interpretation: at 8 participants × 8 weeks, the personalized estimator
identifies the correct best activity well above the 25%-chance baseline as
a point estimate (67%), and returns a *confident* correct recommendation
for ~38% of participants (partial pooling roughly doubles the naive yield).
This is adequate for a **feasibility** pilot whose goal is to demonstrate
the measurement+estimation loop and to size a properly-powered successor —
it is **not** sufficient to act clinically on individual recommendations,
which is why the protocol forbids doing so (§11). N = 8 is the proposed
target; 5–12 is acceptable given recruitment.

## 11. Risks & mitigation

The study is **minimal risk**. Identified risks:
- **Burden/fatigue** from daily tasks → short tasks (~few min), missed days
  permitted, no penalty, generous windows.
- **Privacy** of speech data → on-device embed-and-discard; no raw audio
  retained; de-identification; explicit consent (§8).
- **Frustration/distress** in a communication-impaired population →
  aphasia-friendly design, easy pause/withdraw, clinician check-ins.
- **Over-reliance on unvalidated estimates (key scientific risk)** → the
  pilot makes **no clinical recommendations**; estimates are not returned
  to participants or clinicians to direct care; usual care continues.
  Acting on the dose-response is explicitly out of scope until validated in
  a future trial.
- **Incidental findings** (e.g., apparent decline) → predefined clinician
  review path; refer to usual care if clinically indicated.

## 12. Safety monitoring & stopping rules

A clinician monitors adherence and participant well-being. Individual
stopping: withdrawal on request, clinician concern, or undue burden.
Study-level review at {{interim point}}; halt enrollment if adherence is
infeasible (e.g., median < {{30%}}) or any unanticipated privacy/safety
problem arises. Adverse events reported per {{IRB policy}}.

## 13. Regulatory considerations

- **IRB/ethics approval required** before any activity; this draft is an
  input to that submission.
- **Software-as-a-Medical-Device (SaMD):** as designed, the tool performs
  measurement and research data capture and makes **no diagnostic or
  treatment claim and no clinical recommendation**, situating this use as
  minimal-risk research / non-device wellness-and-feasibility. Any future
  product that returns clinical recommendations would require a separate
  regulatory pathway ({{FDA/CE}}) and is out of scope here. Confirm
  classification with {{regulatory counsel}}.
- Data-protection compliance per §8.

## 14. Roles, timeline, oversight

- **Clinical PI:** {{name}} — eligibility, consent oversight, safety.
- **Technical lead:** {{Edan}} — app, measurement engine, analysis.
- **Data/privacy officer:** {{name}}.
- **Timeline (indicative):** protocol finalization & IRB {{T0}}; app +
  measurement-validity gate {{T0+~6 wk, gated on STRATEGY Leap-1 benchmark}};
  recruitment {{T1}}; 8-week data collection; analysis & report.

## 15. Appendices

- **A. Outcome instrument:** [outcome_instrument.md](outcome_instrument.md).
- **B. Decision-log schema:** `src/closed_loop/trial.py` (`LOG_COLUMNS`);
  produced in-study by `src/app/daily_checkin.py`.
- **C. Analysis code:** `src/closed_loop/pilot_analysis.py`,
  `scripts/pilot_power.py`.
- **D. Consent materials (aphasia-friendly):** {{to be drafted with PI}}.
