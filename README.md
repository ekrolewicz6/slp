# Language State Modeling

Computational modeling of language ability as a continuous, measurable, predictable
state. Long-term goal is closed-loop adaptive dosing for SLPs; this repo is the
foundational layer (representation + trajectory). Full plan lives in [SPEC.md](SPEC.md).

Phase 1 (developmental age prediction from CHILDES transcripts) is implemented and
runnable end-to-end. Phases 2–5 are scoped in the spec.

## Setup

Requires Python 3.11 or 3.12.

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e .
```

## Phase 1: developmental age prediction

```bash
# Single corpus (smoke test, ~5s)
.venv/bin/python -m scripts.run_phase1 --corpus Brown

# Several corpora
.venv/bin/python -m scripts.run_phase1 --corpus Brown,MacWhinney,Providence

# All English-NA corpora (~1 min, ~4,200 transcripts)
.venv/bin/python -m scripts.run_phase1 --corpus all
```

The first run downloads the bundled `0-Eng-NA-MOR.zip` (~91 MB) into `data/raw/`.
Subsequent runs reuse the extracted bundle.

### What it does

1. **Ingest** — parse `.cha` files via `pylangacq` (`strict=False` to tolerate ~26
   mor/word misalignments in Brown).
2. **Extract features** per transcript, filtered to the target child (`CHI`):
   KidEval-style (MLU words/morphemes, NDW, verbs/utt), lexical (TTR, function-word
   ratio, hapax ratio), utterance shape (mean/std/percentiles of length), POS
   distribution over 16 categories, dependency relations + mean dep distance,
   disfluency markers (repetitions, retracings, pauses, fillers).
3. **Train** four models with **child-grouped** 5-fold CV (no child appears in both
   train and test): `mlu_only_ridge` (floor baseline), `kideval_ridge`, `ridge_full`,
   `gbm_full`.
4. **Evaluate + plot** — MAE/RMSE/Pearson per model; predicted-vs-actual,
   residuals-by-corpus, and feature-importance plots.

### Latest results (50 corpora, 4,191 transcripts, ages 0–84 mo)

| Model | Features | MAE (mo) | RMSE | Pearson r |
|---|---:|---:|---:|---:|
| `mlu_only_ridge` (baseline) | 1 | 12.00 | 14.67 | 0.540 |
| `kideval_ridge` | 5 | 12.09 | 14.77 | 0.536 |
| `ridge_full` | 55 | 12.10 | 15.46 | 0.537 |
| **`gbm_full`** | **55** | **8.98** | **11.60** | **0.747** |

GBM beats the MLU-only baseline by 25% on MAE; Pearson r jumps from 0.54 → 0.75.
`utt_len_std` (utterance-length variability) is the single highest-importance
feature, ahead of TTR, hapax ratio, retracing rate, and mlu_morphemes — all four of
the top features sit outside the classic MLU/KidEval set.

### Outputs

`outputs/phase1/`:
- `metrics.csv` — model × CV summary
- `predicted_vs_actual_<model>.png`
- `residuals_by_corpus_<model>.png`
- `feature_importance_<model>.png`

`data/features/`:
- `phase1_features.parquet` — one row per transcript, all 55 features + metadata
- `phase1_transcripts.parquet` — transcript-level index

## Repository layout

```
src/
  ingestion/childes.py        Eng-NA bundle download, .cha parsing
  features/extractors.py      Per-transcript feature dict
  models/phase1_age/train.py  GroupKFold training of Ridge / GBM
  evaluation/metrics.py       MAE / RMSE / Pearson aggregation
  viz/plots.py                Phase 1 plots
scripts/run_phase1.py         End-to-end CLI
data/raw/                     Downloaded corpora (gitignored)
data/features/                Cached features (gitignored)
outputs/phase1/               Metrics + plots (gitignored)
```

## Known limitations / next things

- **Bernstein corpus** fails to load (non-UTF-8 bytes in source). Skipped for now.
- **Ridge plateau** — adding the 50 extra features to Ridge does not beat MLU-only,
  while GBM exploits them readily. Suggests strong nonlinearity / feature
  redundancy. Worth re-examining with elastic net + stronger regularization, and
  with target transforms (e.g. log-age).
- **Corpus-specific bias** in GBM residuals (Evans, Gelman over-predict; Nelson
  under-predicts). A corpus-fixed-effect or domain-adaptation pass would help.
- The §Phase 1 spec called for utterance-window segmentation (100-utt windows). We
  currently aggregate features at the file level. Window-level features are a
  natural follow-up that should improve trajectory smoothness in Phase 3.

## Phase 2 dry run on CHILDES (architecture validation)

While AphasiaBank access is pending, the Phase 2 + Phase 3 architectures are
validated on the developmental data. Same code carries to aphasia later — only
the target swaps (age → WAB-AQ + subtype).

```bash
.venv/bin/python -m scripts.run_phase2_dry
```

Compresses the 55 features into a low-d latent state z via PCA and asks how
much age-prediction signal survives, then KMeans-clusters z and checks
whether data-driven "stages" line up with developmental order.

| Dim d | Variance explained | Age MAE (mo) | Pearson r |
|---:|---:|---:|---:|
| 2 | 0.43 | 11.96 | 0.53 |
| 5 | 0.61 | 10.87 | 0.62 |
| 8 | 0.69 | 10.66 | 0.64 |
| 12 | 0.78 | 10.42 | 0.65 |
| 20 | 0.89 | 10.15 | 0.66 |
| (raw 55, no PCA) | 1.00 | **8.98** | 0.75 |
| (MLU only baseline) | — | 12.00 | 0.54 |

**Cluster purity**: KMeans on z (d=8) into k ∈ {3, 4, 5, 6} produces
clusters whose mean ages are *perfectly monotonic* (Spearman ρ = 1.0 every
time). For k=4 the stages have mean ages 23 → 42 → 52 → 55 months — a
plausible early/early-mid/late-mid/late developmental ordering, found
without ever showing the model an age label.

**Two findings worth carrying into Phase 2 proper:**

- **Linear PCA leaves signal on the table.** Even at d=20 it does not reach
  raw-GBM performance (10.15 vs 8.98). The age-relevant structure is
  nonlinear → motivates autoencoder / VAE / contrastive embedding for the
  real Phase 2 on aphasia.
- **The latent space is geometrically smooth** in age (see
  `outputs/phase2_dry/projection_2d.png` — clean U-shape, age gradient
  along the manifold) with a small outlier branch worth investigating
  (likely school-age narrative tasks like Hicks/HSLLD storytelling).

## Phase 3 dry run on CHILDES (trajectory architecture)

```bash
.venv/bin/python -m scripts.run_phase3_dry
```

Filters to 59 truly-longitudinal children (≥5 sessions, ≥6 mo span, mean
inter-session gap ≥3 days — excludes cohort-style "child_ids" like HSLLD
HV1/HV2/HV3 and Gelman cohort labels). Holds out each child's final session
and predicts ẑ_T from the prior sessions using three trajectory models. The
"age MAE" column pushes predicted z back through a Phase-1 GBM age model
trained on the same z's, so trajectory error is reported in interpretable
months.

| Model | z-L2 MAE | median z-L2 | Age MAE from predicted z (mo) |
|---|---:|---:|---:|
| mean baseline | 3.27 | 2.47 | 9.94 |
| linear extrap | 3.03 | 2.48 | **7.70** |
| GP (RBF + noise) | **2.63** | **2.27** | 8.46 |
| (floor: age MAE from *actual* z) | — | — | 6.74 |

**59 children across 29 corpora; 2,756 sessions used.**

Three things from this:

1. **All trajectory models beat the mean baseline** — predicting where a
   child will be at their next session is genuinely possible from prior
   sessions in this latent space.
2. **GP wins in latent space, linear wins in age space.** The GP has more
   capacity and uses it on z dimensions that don't carry much age signal,
   paying when the downstream evaluator is age. This is real evidence that
   future trajectory models should be fit with weights tied to the outcome
   we care about, not equal weight on every latent dim.
3. **Linear is only 0.96 mo above the floor** — there's not much more juice
   to squeeze in age space without first improving the representation
   (which loops back to "build a real autoencoder for Phase 2").

## Pre-AphasiaBank deepening — what changed

Five focused experiments while the AphasiaBank application was pending.
Two produced clear wins, two produced informative null results, one is a
qualified upgrade. All are reproducible from the windowed feature table.

### Bundle A: latent-dim interpretability + corpus-out generalization

```bash
.venv/bin/python -m scripts.run_bundle_a
```

**Per-PCA-dim meaning (top loadings + outcome importance):**

| Dim | Variance | Pearson r vs age | Perm. importance | Loading interpretation |
|---:|---:|---:|---:|---|
| z₁ | 0.31 | +0.46 | 3.71 | **syntactic richness** — verbs/utt, POS variety, dep variety, SUBJ rel |
| z₂ | 0.12 | +0.39 | 1.69 | **utterance length** — MLU words/morphemes, p50/p90 length |
| z₃ | 0.09 | −0.24 | 1.27 | **session size** — n_utts, total_words, NDW (likely a methodology confound) |
| z₅ | 0.04 | −0.27 | 1.13 | **modification / nominal density** — MOD relations, nouns |
| z₈ | 0.03 | −0.02 | 0.45 | determiner-vs-modal axis (register?) |
| z₄, z₆, z₇ | 0.10 (combined) | ~0 | <0.3 | low-variance stylistic axes the model uses only via interactions |

z₁ and z₂ carry the bulk of the developmental signal and have clean
interpretations ("syntactic complexity" and "utterance length"). z₃ is
suspicious — its high importance is paired with negative correlation and
loadings that look like session-size proxies; some corpora may record
older children for shorter samples. **Worth flagging in any aphasia port:
a `session_size_artifact` axis is a real risk.**

**Leave-one-corpus-out (LOCO) generalization** — strictly harder than
child-grouped CV (every corpus has its own genre / transcription quirks):

| Setup | Corpus-mean MAE | Median | r̄ |
|---|---:|---:|---:|
| Raw 55 features (GBM) | 8.66 | 7.87 | 0.50 |
| PCA z=8 (GBM) | 9.19 | 7.57 | 0.43 |

Surprise: **PCA z=8 generalizes about as well as the full 55 features under
LOCO** (median MAE actually lower; mean slightly worse). The bottleneck
strips corpus-specific overfitting. Worst-generalizing held-outs are
school-age narrative protocols (Nelson MAE 22, Hicks 19, HSLLD 14) — we
should treat them as out-of-distribution for now.

### Bundle B: autoencoder vs PCA — null result

```bash
.venv/bin/python -m scripts.run_bundle_b
```

| d | PCA MAE | AE MAE | AE − PCA |
|---:|---:|---:|---:|
| 3 | 11.81 | 11.90 | +0.09 |
| 5 | 10.87 | 10.59 | −0.28 |
| 8 | 10.66 | 10.78 | +0.12 |
| 12 | 10.42 | 10.40 | −0.02 |
| 20 | 10.15 | 10.65 | +0.50 |

The earlier "linear PCA leaves signal on the table" framing was **partly
wrong**. AE doesn't beat PCA convincingly — they trade. The age-relevance
gap (10.15 vs raw GBM 8.98) is a *bottleneck width* problem, not a
*linearity* problem. The interaction signal the GBM uses on raw 55 features
just doesn't survive any low-d compression, linear or not. Implication for
Phase 2 on aphasia: don't expect dramatic point-prediction gains from AE
over PCA. AE buys you nonlinear interpretability and (potentially) better
transfer, not raw accuracy.

### Bundle C: 100-utterance windowing — biggest single win

```bash
.venv/bin/python -m scripts.run_phase1_windowed --corpus all
```

| Model | File-level MAE | Windowed MAE | Δ |
|---|---:|---:|---:|
| MLU only | 12.00 | 10.97 | −1.03 |
| KidEval | 12.09 | 8.90 | −3.19 |
| Ridge (55) | 12.10 | 8.39 | −3.71 |
| GBM (55) | **8.98** | **7.41** | **−1.57** |

**18% MAE reduction for the GBM, dramatic improvement for the linear
models.** With consistent window sizes the linear features become useful —
file-level aggregation was masking real linear signal under across-session
noise. Windowing also gives ~1.9× more rows (8,115 vs 4,191).

This **revises the framing from Bundle B**: when features are noisy
(file-level), PCA looks fine because there's not much signal to lose; with
clean windows there's more signal — but we haven't re-tested PCA on
windowed features yet. (Worth doing as a follow-up; might shrink the AE
null result.)

### Bundle D: trajectory upgrades — split outcome

```bash
.venv/bin/python -m scripts.run_bundle_d
```

**D1 (outcome-weighted trajectories) — null result.** Computed per-dim
importance weights (z₁=2.81, z₂=1.86, z₃=0.98, …, z₆=0.14) and applied them
as √-weighting before fitting per-dim trajectories. Result: **identical to
unweighted**. Reason: per-dim trajectory models are scale-invariant —
mean of a scaled vector divides out, linear extrapolation is linear in the
scaled axis, GP `normalize_y=True` undoes external scaling. The weighting
trick can't help when each dim is fit independently. A real fix would
require either a coupled multi-output model or a rotation into an
age-aligned basis — left as future work.

**D2 (single-snapshot prediction) — real signal.** For 12 held-out
children, predict ẑ_target from one prior session via a per-dim GBM:

| Method | z-L2 MAE | Age MAE (mo) |
|---|---:|---:|
| no-change baseline | 3.94 | 5.69 |
| population-drift baseline | 3.77 | 4.96 |
| **learned GBM per dim** | **3.45** | **4.73** |
| floor (perfect future-z) | — | 4.42 |

Learned model lands within 0.3 mo of the in-sample-z floor, beats both
baselines. **Predicting next-session z from one prior observation is
possible** — important for the aphasia case where 1–2 prior sessions is
typical.

### Bundle E: prediction intervals (calibration)

```bash
.venv/bin/python -m scripts.run_bundle_e
```

Quantile GBM at q ∈ {0.1, 0.5, 0.9} on the windowed table. Target 80%
interval coverage:

| Age bin (months) | n | Coverage | Mean width | Median MAE |
|---|---:|---:|---:|---:|
| 6 – 22 | 438 | 50% | 11.9 | 5.1 |
| 22 – 37 | 2,950 | 58% | 17.9 | 6.6 |
| 37 – 53 | 1,858 | **85%** | 22.5 | 6.5 |
| 53 – 68 | 1,935 | 73% | 23.7 | 8.6 |
| 68 – 84 | 302 | **8%** | 26.0 | 22.0 |

Calibrated only in the training bulk. **Tail bins are over-confident** —
the 68–84 mo bin is dominated by school-age narrative tasks the model
fundamentally fails at (median MAE 22 mo). Aphasia-port lesson: **always
report coverage-by-bin, never just overall coverage**.

## Where this leaves the headline numbers

After downloading all three openly-available English bundles (Eng-NA +
Eng-UK + Clinical-Eng) — 87 corpora, 14,530 raw transcripts, 23,904 windows
of which 19,762 are age-labelled across 328 children:

| Setup | MAE (mo) | Pearson r |
|---|---:|---:|
| MLU only (file-level baseline) | 12.00 | 0.54 |
| GBM 55-feature, file-level | 8.98 | 0.75 |
| GBM 55-feature, windowed (NA only) | 7.41 | 0.77 |
| **GBM 55-feature, windowed (full English union)** | **6.44** | **0.74** |
| Ridge 55-feature, windowed (union) | 7.33 | 0.66 |
| MLU-only ridge, windowed (union) | 8.02 | 0.60 |

**46% MAE reduction vs the standard MLU baseline** — windowing + adding
Eng-UK + Clinical-Eng each contribute. The MLU-only model also drops sharply
(12.00 → 8.02), so half the gain is fairer baseline conditions and half is
features+windowing.

## Multi-bundle results (after grabbing the rest of CHILDES)

```bash
# downloads Eng-NA, Eng-UK, Clinical-Eng (~250 MB total) on first run
.venv/bin/python -m scripts.run_phase1_windowed --bundles all
.venv/bin/python -m scripts.run_phase2_dry --features-path data/features/phase1_windowed_features.parquet
.venv/bin/python -m scripts.run_ood_na_uk
.venv/bin/python -m scripts.run_clinical_categories
```

### Phase 2 dry, refit on the union

| Dim d | Variance | Age MAE | r | vs raw GBM |
|---:|---:|---:|---:|---:|
| 2 | 0.43 | 7.64 | 0.64 | +1.20 |
| 3 | 0.48 | 7.34 | 0.67 | +0.90 |
| 5 | 0.56 | 7.03 | 0.70 | +0.59 |
| 8 | 0.66 | 6.84 | 0.71 | +0.40 |
| 12 | 0.75 | 6.76 | 0.72 | +0.32 |
| 20 | 0.88 | 6.69 | 0.72 | +0.25 |
| (raw 55, GBM) | — | 6.44 | 0.74 | — |

**Two big revisions** to the earlier dry-run framing:

- Even **d=2** beats the original file-level raw GBM (7.64 vs 8.98).
- The PCA-vs-raw gap at d=12 is now only 0.32 mo. This **further weakens
  the Bundle B "we need an autoencoder" finding** — the bottleneck barely
  costs anything once the data is windowed and bundled. AE on aphasia is
  worth trying for interpretability + transfer reasons, but the raw
  predictive-power motivation is much smaller than I claimed.
- Cluster purity still perfect (Spearman = 1.0 at every k tested). k=6
  stages: 26 → 33 → 41 → 50 → 55 → 64 mo — a clean developmental ordering.

### True OOD: train Eng-NA, predict Eng-UK (and reverse)

| Direction | Model | n_train | n_test | MAE | Pearson r | Bias |
|---|---|---:|---:|---:|---:|---:|
| NA → UK | ridge | 7,483 | 9,044 | 6.06 | 0.69 | +1.83 |
| **NA → UK** | **gbm** | 7,483 | 9,044 | **5.19** | **0.73** | +0.75 |
| UK → NA | ridge | 9,044 | 7,483 | 9.29 | 0.61 | −2.54 |
| UK → NA | gbm | 9,044 | 7,483 | 9.05 | 0.63 | −3.28 |

**Dramatic asymmetry — also a real finding.** NA → UK actually generalizes
*better* than within-distribution CV (5.19 vs 6.44 reference) because Eng-NA
is much more diverse (43 corpora, 196 children) than Eng-UK (11 corpora,
80 children) — diverse train + homogeneous test is an easy condition.
UK → NA is much harder (9.05 MAE, with a large negative bias: model
under-predicts NA ages). This is the textbook lesson on training-set
diversity, made visible. Importantly, **both directions still beat the MLU
baseline (12.00) — the developmental signal really is dialect-invariant**;
the model is learning age, not NA-vs-UK speech style.

Translation for AphasiaBank: **diversity of training corpora is more
load-bearing than total transcript count**. We should explicitly include all
AphasiaBank protocol sites (ACWT, Adler, APROCSA, etc.) when training, not
focus on a single high-volume site.

### Clinical-Eng diagnostic labels — first preview of the aphasia case

Extracted diagnosis from path tokens (TD, SLI, DS, HL, etc.). After
filtering classes with ≥200 windows: TD (1,579), SLI (619), DS (228) →
2,426 windows, 20 children, child-grouped 5-fold CV.

| Feature set | Accuracy | Macro F1 | TD F1 | SLI F1 | DS F1 |
|---|---:|---:|---:|---:|---:|
| Raw 55 features | 0.554 | 0.359 | 0.702 | 0.367 | 0.008 |
| PCA z=8 | 0.524 | 0.262 | 0.710 | 0.035 | 0.042 |

**Honest read**: this is a tiny clinical sample (20 children with extractable
labels) — child-grouped CV here is brutal and class imbalance dominates.
What we *can* say:

- **z preserves the TD-vs-clinical discrimination** (TD F1 0.71 vs raw 0.70).
- **z loses the SLI-vs-DS discrimination** at d=8 — these collapse into
  a single "non-TD" cluster. Either we need higher d, or these two
  populations genuinely sit close in our current feature space.
- **DS classification fails for both feature sets** — likely because the
  features can't distinguish DS speech from young TD speech without age
  context, and the DS children skew young.

**This is not a slam dunk preview, but it's not a refutation either.** The
question of whether categorical labels are lossy slices of a continuum gets
a partial yes (the binary TD-vs-clinical signal survives the bottleneck),
with a flag that fine-grained subtyping needs more data than we have here —
which is exactly the question to bring to AphasiaBank with WAB-AQ + subtype
labels and ~500 PWA participants.

## Datasets requiring user action (Phases 2+)

See [SPEC.md §15](SPEC.md). To unblock Phase 2/3/4 you need to:

- Apply for **AphasiaBank** membership at <https://aphasia.talkbank.org/>.
- Apply for **RELEASE** data access (individual-participant data, ~5,900 patients).
- Place credentials in `.env` (template in `.env.example`).
