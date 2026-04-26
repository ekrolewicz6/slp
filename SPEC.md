# MASTER SPEC

**Project:** Computational Language State & Recovery Modeling (SLP / Aphasia Focus)

## 0. Mission

Build a system that models human language ability as a continuous, measurable, and predictable state, using only existing transcript and clinical datasets.

The long-term goal is to:

Discover whether language development and recovery follow predictable trajectories that can be modeled, forecasted, and eventually optimized.

### Long-term vision (informs design priorities)

The end-state is **closed-loop, adaptive SLP dosing** — turning therapy planning into a measurable control system:

```
state → intervention → response → update → next intervention
```

The system should not output "do therapy X." It should output a **decision surface**: distributions, tradeoffs, and uncertainty across intervention regimes, leaving the clinician in control but informed.

To get there, build in this order — each layer is independently valuable and unlocks the next:

1. **Better scoring** — a continuous representation of language ability that beats MLU/KidEval
2. **Trajectory** — where the patient is going, not just where they are
3. **Delta thinking** — velocity, acceleration, plateaus (rate of change > absolute score)
4. **Decision surfaces** — comparative response distributions across interventions
5. **Adaptive dosing** — closed-loop updates after each session

### Realistic outcome targets

- **Baseline success (~70% likely with good execution):** beat MLU/KidEval/clinical baselines, show aphasia categories are lossy, produce cleaner trajectory predictions, publishable system.
- **High-impact (~20%):** new standard latent-state representation; convincing demonstration that recovery trajectories are predictable in that space.
- **Stretch (<5%):** partially generalizable recovery model showing therapy meaningfully shifts trajectories for identifiable subgroups. Limited by causal-signal-vs-observational-noise issues in existing data (inconsistent therapy protocols, missing covariates, selection bias, noisy outcomes).

The biggest risk is **not failure** — it's building something technically impressive that doesn't change how anyone thinks. Optimize for interpretability, clear baseline-beating, and connection to clinical questions.

## 1. Core Hypothesis

Language ability is not best described by:

- discrete diagnoses (e.g., Broca vs Wernicke)
- isolated metrics (MLU, WAB, etc.)

Instead:

Language ability is a latent state in a continuous space, and individuals move through this space over time according to predictable dynamics.

## 2. End-State Vision

System learns:

- Language State (z) at time t
- → Predicts future Language State at time t + Δ
- → Under different conditions (natural recovery, therapy, etc.)

Eventually:

```
E[future z | current z, intervention A]
vs
E[future z | current z, intervention B]
```

## 3. System Architecture (High-Level)

```
Raw Data (CHILDES, AphasiaBank, RELEASE)
    ↓
Parsing & Feature Extraction (CLAN + custom)
    ↓
Language State Representation Model (z)
    ↓
Trajectory Model (z_t → z_t+Δ)
    ↓
Outcome Prediction / Recovery Modeling
    ↓
Counterfactual Simulation (later phase)
```

## 4. Phased Execution Plan

### PHASE 1: Developmental Representation (CHILDES)

#### Goal

Learn mapping:

```
transcript → developmental language state (z)
```

#### Data

- CHILDES (English corpora)
- CLAN outputs (MOR, POST, MEGRASP, KIDEVAL)

#### Tasks

**1. Data ingestion**

Parse `.cha` files:

- child_id
- age (months)
- corpus
- participants
- utterances

**2. Utterance segmentation**

- Segment into 100-child-utterance windows
- Normalize shorter samples

**3. Feature extraction**

Extract:

*A. KidEval metrics*
- MLU (words, morphemes)
- NDW
- tokens
- verbs per utterance

*B. Sagae-style syntactic features*
- POS tags
- dependency relations
- head-dependent pairs
- head-relation-dependent triples

*C. Additional features (extend beyond paper)*
- utterance length distribution
- type-token ratio
- function word ratio
- error markers (if available)

**4. Model: Predict age**

Train models:

- Ridge / ElasticNet
- Random Forest
- Gradient Boosting

Target:

```
age_months
```

**5. Evaluation**

Metrics:

- MAE (months)
- RMSE
- Pearson correlation

Baselines:

- MLU-only
- KidEval-only

**6. Output**

For each transcript:

- predicted developmental age
- confidence interval
- feature importance

#### Success criteria

- Beats MLU baseline
- Generalizes across children
- Produces smooth trajectories

---

### PHASE 2: Language-State Representation (AphasiaBank)

#### Goal

Learn:

```
transcript → latent language state z
```

#### Data

- AphasiaBank transcripts
- EVAL / C-QPA outputs
- clinical scores (WAB, AQ, etc.)

#### Tasks

**1. Feature extraction**

Combine:

- syntactic features (from Phase 1)
- lexical features
- discourse features
- fluency markers
- error types

**2. Representation learning**

Train:

- PCA (baseline)
- Autoencoder
- Variational Autoencoder
- Contrastive embedding model

Goal:

```
z ∈ R^d (d ≈ 5–20)
```

**3. Evaluate representation**

Predict:

- WAB / AQ scores
- aphasia severity
- aphasia subtype

**4. Replace categories**

Test:

- clustering vs classical labels
- overlap between subtypes
- predictive power of z vs labels

#### Success criteria

- z predicts outcomes better than subtype labels
- stable across corpora
- interpretable dimensions

---

### PHASE 3: Trajectory Modeling

#### Goal

Learn:

```
z_t → z_(t+Δ)
```

#### Data

- AphasiaBank longitudinal samples
- RELEASE dataset (if available)

#### Tasks

**1. Build sequences**

For each patient:

```
[z_1, z_2, z_3, ..., z_T]
```

**2. Train models**

- Linear dynamical system
- RNN / LSTM
- Neural ODE
- Gaussian Process regression

**3. Predict future state**

```
z_(t+Δ)
```

**4. Evaluate**

Metrics:

- MAE in latent space
- error in clinical score prediction
- trajectory smoothness

#### Success criteria

- Predict future better than baseline
- stable across datasets

---

### PHASE 4: Recovery Modeling (with RELEASE)

#### Goal

Understand:

```
what drives recovery
```

#### Tasks

**1. Merge datasets**

Combine:

- latent state z
- time since stroke
- therapy variables
- demographics

**2. Model:**

```
z_(t+Δ) = f(z_t, therapy, covariates)
```

**3. Identify effects**

- therapy dose effect
- therapy type effect
- interaction with baseline state

#### Success criteria

- consistent effects across datasets
- interpretable mechanisms

---

### PHASE 5: Counterfactual Modeling (Final Stage)

#### Goal

Estimate:

```
E[z_future | z_current, intervention A]
vs
E[z_future | z_current, intervention B]
```

#### Methods

- causal inference (propensity matching)
- doubly robust estimators
- structural causal models

#### Output

For each patient:

- predicted trajectories under different treatments
- uncertainty
- confidence

#### Success criteria

- matches known clinical findings
- replicates across datasets

## 5. Data Requirements

### 5.1 Datasets

#### CHILDES (Child Language Data Exchange System) — **automated**

- **Access:** Open. Programmatically downloadable from `https://childes.talkbank.org/`.
- **Format:** `.cha` files (CHAT transcript format).
- **Volume:** ~50,000+ transcripts across many corpora (English: Brown, Providence, Manchester, Thomas, MacWhinney, etc.).
- **Acquisition:** scripted via HTTP fetch of corpus zips, or via the `pylangacq` library which can download corpora directly.
- **Use:** Phase 1 (developmental modeling, age prediction).

#### AphasiaBank — **requires human access request**

- **Access:** Restricted. Requires institutional membership + signed data-use agreement at `https://aphasia.talkbank.org/`.
- **What's included:** transcripts of aphasic and control speech, discourse tasks (Cinderella narrative, picture descriptions, procedural discourse), demographic + clinical metadata (WAB-AQ, aphasia subtype, time post-onset).
- **Acquisition:** **MANUAL — user must apply for membership and download.** Once credentials are obtained, downloads can be scripted.
- **Use:** Phase 2 (latent state representation), Phase 3 (trajectory).

#### RELEASE (REhabilitation and recovery of peopLE with Aphasia after StrokE) — **requires human access request**

- **Access:** Restricted. Individual-participant-data meta-analysis hosted via University of Glasgow / data-sharing agreement.
- **What's included:** ~5,900 individuals across 174 datasets; therapy dose (hours, frequency, intensity), therapy type, baseline + outcome scores, demographics, time since stroke.
- **Acquisition:** **MANUAL — user must apply via the RELEASE collaboration. Application typically requires a research protocol.**
- **Use:** Phase 4 (recovery modeling), Phase 5 (counterfactual).

#### TalkBank (broader) — **automated**

- Other relevant TalkBank corpora: FluencyBank (stuttering), DementiaBank, RHDBank (right-hemisphere damage). Treat as optional secondary validation sets.

#### Public norm/reference data — **automated**

- CDI (MacArthur-Bates Communicative Development Inventory) norms — for developmental sanity checks.
- WAB-AQ score distributions from published literature — for severity calibration.

### 5.2 What requires human intervention (flagged explicitly)

| Step | Who does it | Notes |
|---|---|---|
| AphasiaBank membership application | **User** | One-time. Required before Phase 2. |
| RELEASE data-sharing application | **User** | One-time. Required before Phase 4. May take weeks/months. |
| CLAN binary install | **User** (one-time) | macOS/Linux/Windows installer from TalkBank; agent can verify install but cannot bypass GUI installer on macOS. |
| Credential storage for restricted datasets | **User** | Place credentials in `.env` (gitignored); agent reads from there. |
| Ethics / IRB review | **User** | If results will be published or deployed clinically. |

Everything else (download, parsing, feature extraction, modeling, evaluation, visualization) must be fully scripted.

### 5.3 Patient-level input specification

When the eventual system runs on a new patient, define the input layers:

**Tier 1 — Minimum viable input (required):**
- 1 language sample, 5–10 min OR ~50–100 utterances (picture description, conversation, or narrative retell).
- Age.
- Diagnosis if known; time-since-onset for aphasia.

**Tier 2 — High-value input (unlocks trajectory modeling):**
- 2–5 longitudinal samples (e.g., baseline, +2–4 weeks, +2–3 months).
- Therapy exposure: hours/week, broad type, setting (school/clinic/home) — coarse labels are fine.
- Basic covariates (severity if known).

**Tier 3 — Ideal input (unlocks dosing-level modeling):**
- Structured therapy data (targets, frequency, duration, changes over time).
- Environmental input (caregiver interaction, language exposure).
- Standardized scores (WAB/AQ) for validation.

Design ingestion to **degrade gracefully** as tiers drop — never require Tier 3 to produce Tier 1 outputs.

### 5.4 Output specification by stage

The model's outputs must be tied to data maturity. Do not promise Stage 4 outputs from Stage 1 data.

| Stage | Inputs available | Outputs | Latency | Realistic accuracy |
|---|---|---|---|---|
| 1 | 1 transcript + age | Language state z, predicted developmental/recovery age, CI, feature deviations | Seconds | Moderate–strong for state; weak for intervention effects |
| 2 | Multiple transcripts | Trajectory estimate, plateau detection, comparison to similar patients | Real-time per session | Good for stagnation/atypical progression |
| 3 | Trajectories + cohort | Relative response patterns across intervention classes (NOT prescriptions) | Real-time | Moderate, non-causal |
| 4 | Therapy metadata + longitudinal | Expected outcomes under different dosing, response curves with uncertainty | Real-time inference | Initially noisy but directional |
| 5 | High-quality longitudinal + interventional | Adaptive dosing recommendations with uncertainty | Real-time + closed-loop updates | Requires data we don't yet have at scale |

Phases 1–3 of the build correspond roughly to stages 1–3 of output capability; Phase 4–5 of the build target stages 4–5.

## 6. Data Structures

### Transcript table

- transcript_id
- child_or_patient_id
- age_months
- corpus
- num_utterances

### Feature table

- transcript_id
- feature_name
- value

### Latent state table

- transcript_id
- z_1 ... z_d

### Trajectory table

- patient_id
- time
- z_state

## 7. Evaluation Philosophy

### Must show:

- Improvement over baselines
- Generalization across datasets
- Stability across time
- Interpretability

### Must avoid:

- overfitting
- dataset-specific hacks
- black-box outputs with no explanation

## 8. Outputs

**1. Model comparison reports**
- MLU vs KidEval vs syntax vs combined

**2. Trajectory visualizations**
- actual vs predicted
- recovery curves

**3. State-space visualization**
- 2D/3D projection of z
- clustering

**4. Feature importance reports**
- what drives predictions

## 9. Non-goals

Do NOT:

- build a product UI first
- claim clinical use
- jump to therapy recommendations early
- rely only on LLMs
- output prescriptions ("do therapy X"). Always output **decision surfaces** — distributions, tradeoffs, uncertainty
- present black-box scores without feature attributions
- collect more input per patient when the actual constraint is more patients with consistent measurement over time

## 10. Engineering Constraints

- Python only
- Modular pipeline (each phase = importable package, runnable end-to-end with one command)
- Reproducible runs (seed control, pinned deps, deterministic feature extraction; track config + data hash per run)
- Handle missing data (graceful degradation across input tiers — see §5.3)
- Scalable to thousands of transcripts
- Cache parsed transcripts and extracted features (re-parsing `.cha` files is expensive)
- Clear separation of data layer (raw → parsed → features) from modeling layer
- Every model output paired with feature attribution / uncertainty
- All restricted-data credentials read from `.env` (gitignored), never hardcoded

## 10a. Tooling & Dependencies

### Required external tools

- **CLAN** (TalkBank's analysis suite) — provides `kideval`, `mor`, `post`, `megrasp`, `eval`. Install from `https://dali.talkbank.org/clan/`. Agent should detect install path and fall back to Python re-implementations where possible.
- **Python 3.11+**

### Core Python libraries

- **`pylangacq`** — pure-Python CHAT (`.cha`) parser. Primary parser; preferred over shelling out to CLAN for portability.
- **`pandas`, `numpy`, `scipy`** — data wrangling.
- **`scikit-learn`** — Ridge, ElasticNet, Random Forest, Gradient Boosting, PCA, clustering, evaluation.
- **`xgboost` / `lightgbm`** — stronger GBM baselines.
- **`pytorch`** — autoencoders, VAEs, RNNs/LSTMs, contrastive embedding (Phase 2–3).
- **`torchdiffeq`** — Neural ODEs (Phase 3).
- **`gpytorch`** — Gaussian Process trajectory models (Phase 3).
- **`statsmodels` / `linearmodels`** — linear dynamical systems, mixed-effects, panel models (Phase 3–4).
- **`econml` / `dowhy`** — causal inference, doubly robust estimators (Phase 5).
- **`shap`** — feature attribution.
- **`matplotlib`, `seaborn`, `plotly`** — visualizations including 2D/3D state-space projections.
- **`umap-learn`** — non-linear projection of latent space.
- **`spacy` or `stanza`** — backup POS/dependency parsing if MOR/POST output is missing or insufficient.
- **`hydra-core` or `pydantic-settings`** — config management.
- **`mlflow` or `wandb`** — experiment tracking.
- **`pytest`** — testing (especially for parsing edge cases and feature determinism).

### Repo layout (recommended)

```
language-state-modeling/
  SPEC.md
  README.md
  pyproject.toml
  .env.example
  data/
    raw/           # downloaded corpora (gitignored)
    parsed/        # parsed transcript cache
    features/      # extracted features
  src/
    ingestion/     # download + parse CHILDES, AphasiaBank, RELEASE
    features/      # KidEval, Sagae syntactic, lexical, discourse, fluency
    models/
      phase1_age/
      phase2_state/
      phase3_trajectory/
      phase4_recovery/
      phase5_counterfactual/
    evaluation/
    viz/
  configs/         # per-experiment configs
  notebooks/       # exploratory only; not part of pipeline
  tests/
  scripts/         # one-shot CLI entry points per phase
```

## 11. Deliverables

**Phase 1**
- Age prediction model
- CHILDES pipeline

**Phase 2**
- Latent state model
- Aphasia representation

**Phase 3**
- Trajectory model

**Phase 4**
- Recovery model

**Phase 5**
- Counterfactual model

## 12. Final Success Definition

The system succeeds if it demonstrates:

Language ability is a predictable, continuous state that evolves over time and can be modeled better than existing clinical tools.

## 13. Simplest version of the goal

If the agent forgets everything:

Build a model that takes transcripts and predicts where someone is in language development or recovery — and how they will change over time.

## 14. First concrete milestone (start here)

Before touching aphasia data, ship Phase 1 end-to-end on CHILDES:

1. Download a single English corpus (e.g., Brown) via `pylangacq`.
2. Parse all `.cha` files, extract child utterances, compute MLU + KidEval-style features.
3. Train Ridge + Gradient Boosting to predict `age_months`.
4. Report MAE/RMSE/Pearson vs an MLU-only baseline.
5. Plot predicted vs actual age, residuals by corpus, and feature importance.

This validates the toolchain (CLAN/pylangacq, feature pipeline, modeling) before scaling to the full CHILDES + restricted datasets.

## 15. Action items requiring user (human) intervention

Track these separately — the agent cannot complete them:

- [ ] Apply for AphasiaBank membership (`https://aphasia.talkbank.org/`) — needed before Phase 2.
- [ ] Apply for RELEASE data access — needed before Phase 4. Allow weeks-to-months lead time; start early.
- [ ] Install CLAN locally and confirm install path.
- [ ] Place credentials for restricted datasets in `.env`.
- [ ] If pursuing publication or any clinical-facing claim, secure IRB / ethics review.
- [ ] If pursuing the long-term vision (closed-loop dosing), arrange clinical partners for prospective longitudinal data collection — existing observational data alone will not get past Stage 3 outputs.
