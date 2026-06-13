# STRATEGY — where we are headed

> One-line thesis: **The field does not change on better measurement. It
> changes when a system can tell a clinician what to do for *this* patient,
> and prove it.** Everything we have today is descriptive. The next 100×
> is crossing from observation to a closed-loop interventional system that
> generates its own causal evidence at scale.

Last updated: 2026-04-26. Owner: Edan. Companion docs:
[RESEARCH_LOG.md](RESEARCH_LOG.md) (what we've proven), [SPEC.md](SPEC.md)
(original project spec).

---

## 0. The honest diagnosis

- **AphasiaBank is mined out.** Experiment #34 shows accuracy plateaus at
  n≈400 patients — we are *model-limited, not data-limited*. The next
  experiment on the same data is worth ~1.1×, not 100×.
- **The plateau is a representation ceiling, not a data ceiling.** We
  describe speech with 55 hand-crafted summary statistics plus an
  off-the-shelf MPNet that never saw disordered speech. That's why the
  fine-tune failed (#41). A speech-native learned representation should
  break the plateau. **This is buildable now** (Leap 1).
- **WAB-AQ is the wrong target.** It is slow and coarse; #23 shows it
  barely moves session-to-session, which is *why* trajectory prediction
  hit a noise floor. The thing that matters is real-world functional
  communication, not a test score.
- **We measure; we do not act.** No patient ever interacts with the
  system. There is no intervention, no continuous signal, no causal loop.
  That gap is the whole opportunity.

The strongest scientific seed we already have: **Broca aphasia occupies a
region of the language-state manifold that no neurotypical speaker —
child or adult — ever reaches** (#49). That reframes the work from "we
measure severity" toward "language ability is a geometry, and recovery is
a path through it." Hold that thought; it becomes the scientific spine
(§5).

---

## 1. The target system — the closed loop

Today's paradigm is **open-loop and episodic**: a clinician administers a
90-minute battery at intake and maybe discharge (two data points a year),
applies intuition-based therapy, and re-measures much later. Slow loop,
low resolution, expensive, inaccessible.

The field-changing paradigm is **closed-loop and continuous**:

```
   ┌────────────────────────────────────────────────────────────┐
   │                                                            │
   ▼                                                            │
[1] MEASURE            [2] REPRESENT          [3] INTERVENE      │
 ambient, daily   →    learned latent    →   micro-randomized    │
 (phone listens)       language state        therapy dose        │
                                                  │              │
                                                  ▼              │
                                            [4] LEARN CAUSE      │
                                            dose-response        │
                                            per phenotype  ──────┘
        (closed loop — runs daily, in the patient's real life)
```

We are in boxes 1–2 today (measurement + description). Boxes 3–4 —
intervention and causal learning — are the lever. Nothing substitutes for
them, because clinical practice changes on *what to do*, not on *what is*.

---

## 2. The five leaps

Each leap is rated by **impact**, **effort**, and **buildable-now?** —
whether it can be done on data/infra we already have.

### Leap 1 — Representation: kill the 55 hand-crafted features
- **What:** Replace summary-stat features + off-the-shelf MPNet with a
  speech-native self-supervised representation over raw audio (+transcript
  fused). Wav2Vec2 / HuBERT / Whisper-encoder embeddings, pooled per
  window.
- **Why:** The n≈400 plateau is representational. A learned latent space
  is the difference between "55 numbers" and "everything the signal
  carries."
- **Impact:** High (unlocks every downstream box). **Effort:** Weeks.
  **Buildable now:** ✅ — audio re-streams from TalkBank; labels exist.
- **Status in this repo:** ✅ shipped AND tested on real audio —
  [`src/features/foundation_rep.py`](src/features/foundation_rep.py),
  [`scripts/extract_foundation_embeddings.py`](scripts/extract_foundation_embeddings.py),
  [`scripts/benchmark_representations.py`](scripts/benchmark_representations.py),
  [`scripts/encoder_bakeoff.py`](scripts/encoder_bakeoff.py).
  **Verdict (#52, n=85, preliminary): task-dependent. HuBERT layer-9 beats
  hand-crafted on subtype (macro-F1 0.47 vs 0.35); hand-crafted text wins on
  severity (r 0.55 vs 0.41).** The ceiling breaks where acoustics matter.
  Next lever: a fine-tuned head / attentive pooling, and a full-corpus re-run.

### Leap 2 — Outcome: predict functional communication, not WAB-AQ
- **What:** Re-aim the whole system at real-world communicative success —
  "can she order coffee, answer the phone, argue with her son" — measured
  from naturalistic samples + patient/caregiver report (a lightweight
  daily EMA + a communicative-participation scale).
- **Why:** WAB-AQ is a proxy that barely moves (#23). Functional outcome
  is what matters to a human and what a payer/clinician acts on.
- **Impact:** High (makes it matter, not just measurable). **Effort:**
  Medium, but needs new data (no archived label exists). **Buildable
  now:** ⚠️ partial — instrument defined now, validated/collected in pilot.
- **Status in this repo:** ✅ instrument shipped —
  [`src/outcomes/functional_communication.py`](src/outcomes/functional_communication.py)
  + spec [`docs/pilot/outcome_instrument.md`](docs/pilot/outcome_instrument.md).
  Psychometric validation is a pilot deliverable.

### Leap 3 — Continuity: ambient, daily measurement
- **What:** A consented phone app that samples speech (with strict
  privacy controls) and produces a daily language-state estimate.
- **Why:** Two data points a year cannot support trajectory modeling, let
  alone control. 365 can. The $0 Whisper+parselmouth pipeline already
  makes this technically free.
- **Impact:** High (prerequisite for steering). **Effort:** Medium (app +
  on-device/edge inference + privacy). **Buildable now:** ⚠️ — the
  inference core exists; the app UI + consent flow do not.
- **Status in this repo:** ✅ measurement engine shipped AND now emits real
  estimates — [`src/app/daily_checkin.py`](src/app/daily_checkin.py): speech
  → on-device HuBERT embedding (waveform discarded) →
  [trained heads](src/models/heads/state_head.py) → real subtype posterior +
  WAB-AQ state estimate + functional score → closed-loop log row. Heads
  trained by [`scripts/train_state_heads.py`](scripts/train_state_heads.py)
  (#53). Demoed end-to-end on real audio (severity 66.3 vs true 72.8).
  Remaining: ASR→text link for severity-from-audio, larger SubtypeHead set,
  mobile UI + consent flow.

### Leap 4 — Intervention + causality: the lever
- **What:** The app *delivers* individualized practice and
  **micro-randomizes** dose / type / timing (micro-randomized trials +
  contextual bandit), using the continuous outcome to learn each
  patient's **dose-response surface**.
- **Why:** Produces *causal* evidence — the one thing observational
  AphasiaBank can never give. Directly solves the field's open wound:
  nobody knows the right therapy dose for whom.
- **Impact:** Field-defining. **Effort:** High (design + ethics + the
  learning system). **Buildable now:** ✅ the *machinery* is, in silico —
  [`src/closed_loop/`](src/closed_loop/) +
  [`scripts/simulate_closed_loop.py`](scripts/simulate_closed_loop.py)
  run the policy → trial → causal-recovery loop on simulated patients
  today. Real patients come in the pilot.

### Leap 5 — Scale + the scientific reframe
- **What:** Deploy multilingually at phone scale. Two payoffs: the N to
  power the causal learning, and a public-health intervention for the
  majority of stroke survivors worldwide who get little or no SLP.
- **Why / reframe:** **Language ability is a low-dimensional controllable
  dynamical system; therapy is a control input; we learn the controller.**
  Going from "we can read the state" to "we can steer the state, proven
  causally" is the sentence that rewrites the textbook.
- **Impact:** Field-defining + global. **Effort:** Very high (regulatory,
  multilingual, infra). **Buildable now:** ❌ — this is the destination.

---

## 3. What we are shipping in this repo *now* (the buildable slice)

| Component | Path | Runs today? | What it proves |
|---|---|---|---|
| Strategy north star | `STRATEGY.md` | — | Where we're headed |
| Foundation-model speech reps | `src/features/foundation_rep.py` | ✅ (with audio) | Leap 1 representation |
| Stream + extract learned reps | `scripts/extract_foundation_embeddings.py` | ✅ (cookie) | Leap 1 at scale |
| Representation benchmark | `scripts/benchmark_representations.py` | ✅ | Tests the n≈400 ceiling claim |
| Language-state estimator iface | `src/closed_loop/state.py` | ✅ | Box 2 interface |
| Adaptive policy (bandit) | `src/closed_loop/policy.py` | ✅ | Box 3 — micro-randomized dosing |
| Micro-randomized trial + log | `src/closed_loop/trial.py` | ✅ | Box 3/4 logging schema |
| Causal dose-response estimator | `src/closed_loop/causal.py` | ✅ | Box 4 — recovers cause from logs |
| In-silico patient dynamics | `src/closed_loop/simulator.py` | ✅ | Ground truth to validate against |
| End-to-end closed-loop demo | `scripts/simulate_closed_loop.py` | ✅ | The whole architecture, in silico |

The in-silico loop is the centerpiece of the buildable slice: it shows the
policy → trial → causal-recovery machinery working end-to-end, recovering
a *known* per-phenotype dose-response, **before a single patient is
enrolled.** It de-risks the pilot.

---

## 4. The 8-week pilot — the first real datapoint

Not a 200-patient trial. The smallest thing that produces evidence of a
kind that **does not currently exist anywhere**:

- **Cohort:** 5–8 consented chronic-aphasia patients (post-acute, stable
  enough for daily app use), recruited via one clinical partner.
- **Measure (Leap 1+3):** daily ~5-min speech sample → learned
  language-state estimate. Plus a weekly functional-communication EMA
  (Leap 2).
- **Intervene (Leap 4):** the app delivers one practice activity per day,
  **micro-randomizing one decision** (e.g., activity *type*: naming vs
  syntax vs conversation), logging context + arm + propensity + next-day
  state change.
- **Learn (Leap 4):** at 8 weeks, run `src/closed_loop/causal.py` on the
  real logs to estimate each patient's dose-response and per-phenotype
  optimal activity — the same estimator validated in silico.
- **Success = the estimator returns a stable, interpretable within-patient
  causal estimate against a continuous real-world signal.** Not a p-value
  on a group mean — a *personalized* dose-response. That single result is
  worth more to the field than the next fifty AphasiaBank notebooks.

Gating before patients: (a) Leap-1 benchmark beats hand-crafted features;
(b) in-silico loop recovers ground-truth dose-response within tolerance;
(c) IRB + consent + privacy review complete.

**Pilot is now specified.** Full draft protocol:
[`docs/pilot/PROTOCOL.md`](docs/pilot/PROTOCOL.md) (design, eligibility,
aphasia-friendly consent, privacy, analysis plan, regulatory). Sample size
grounded by a feasibility simulation
([`scripts/pilot_power.py`](scripts/pilot_power.py),
[`src/closed_loop/pilot_analysis.py`](src/closed_loop/pilot_analysis.py)):
at 8 patients × 8 weeks a within-patient micro-randomized trial recovers
the correct best activity at 67% point accuracy (vs 25% chance) and returns
a *confident* correct recommendation for ~38% of patients — **with partial
pooling toward the phenotype prior, which ~doubles the naive yield**. That
is adequate for a feasibility pilot (not for acting clinically — the
protocol forbids it) and sizes the successor trial.

---

## 5. The scientific spine (the part that rewrites the textbook)

The product vision (above) and the science reinforce each other.

- **Claim:** Language ability is a low-dimensional **controllable
  dynamical system**. State = position on the manifold. Development and
  recovery = trajectories. Therapy = a control input.
- **The Broca corollary (testable now-ish):** #49 shows Broca sits in a
  manifold region unreachable by typical development. So the deep
  question is: **is there a control path from the Broca region back to the
  healthy manifold, and is it different from the developmental path?** Our
  data already hint *yes* — which would mean therapy for Broca should
  **not** recapitulate child language acquisition, contradicting a
  Jakobson-era organizing principle of the field. Falsifiable. Memorable.
- **Why the closed loop is the proof engine:** you cannot demonstrate
  controllability by observation. You demonstrate it by *applying inputs
  and measuring the state response* — which is exactly boxes 3–4.

---

## 6. Risks & what we give up

- **Leaving the safety of public data.** The 100× is consented patients,
  IRB, recruitment, clinical partnerships — not notebooks. This is the
  real cost and why almost no one does it.
- **Regulatory:** the moment we make a clinical claim, this is FDA
  Software-as-a-Medical-Device territory. Plan for it; stage claims
  accordingly (wellness/decision-support first).
- **Measurement validity:** a daily learned state estimate must be shown
  reliable and meaningful vs. clinician-administered gold standards before
  anyone trusts it to drive dosing.
- **Privacy:** ambient speech capture is sensitive. On-device/edge
  inference, minimal retention, explicit consent are non-negotiable.
- **Engagement:** daily app use by aphasia patients is hard; the
  intervention must be genuinely usable, not a research burden.

---

## 7. Phases & milestones

- **Phase A — Representation (now → ~6 wks):** ship Leap 1; benchmark
  learned vs hand-crafted reps on existing labels; break or confirm the
  n≈400 plateau. *Done when:* learned reps beat hand-crafted on WAB-AQ
  and subtype with GroupKFold.
- **Phase B — In-silico loop (now, parallel):** validated closed-loop
  machinery + causal recovery. *Done when:* `simulate_closed_loop.py`
  recovers ground-truth per-phenotype optimal arm and the adaptive policy
  beats fixed/random on total recovery. *(Shipped in this repo.)*
- **Phase C — Outcome + app (parallel, longer):** define functional
  outcome instrument (Leap 2); build the daily-measurement app core
  (Leap 3); privacy + consent.
- **Phase D — Pilot (after A–C gate):** the 8-week study (§4).
- **Phase E — Scale + science (destination):** multilingual deployment;
  the controllability paper; the Broca control-path study.

---

## 8. How we'll know it worked

- **Near term (this repo):** learned reps beat hand-crafted features; the
  in-silico loop recovers known dose-response.
- **Mid term (pilot):** a real, stable, personalized dose-response from
  ≤8 patients against a continuous real-world signal.
- **Long term (field):** an SLP changes what they prescribe for a patient
  because the system told them to — and the patient does better than the
  population default would predict. That is the whole point.
