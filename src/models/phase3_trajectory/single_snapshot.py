"""Single-snapshot trajectory prediction: ẑ_target from one prior session.

Phase 3 dry run used 5+ prior sessions to predict the next, but the realistic
clinical case for SLPs has 1–2 prior measurements. This module trains a
population-level model that maps (z_prior, t_prior, t_target) → ẑ_target,
using all (early, late) pairs from training children.

Two baselines we evaluate against:
  - "no change": predict z_target = z_prior. The model must beat this.
  - "population mean drift": predict z_target = z_prior + Δ̄(Δt), where
    Δ̄(Δt) is the mean per-dim change over Δt months across the training set.

The learned predictor is one GBM per latent dimension on features
[z_prior_1..z_prior_d, t_prior, Δt].
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

from src.models.phase3_trajectory.sequences import ChildSequence


@dataclass
class SnapshotPair:
    z_prior: np.ndarray
    t_prior: float
    z_target: np.ndarray
    t_target: float
    child_id: str
    corpus: str

    @property
    def delta_t(self) -> float:
        return self.t_target - self.t_prior


def build_pairs(sequences: list[ChildSequence],
                max_pairs_per_child: int = 50) -> list[SnapshotPair]:
    """Sample (i, j) pairs with i < j from each child's sequence.

    Capped per child so a 240-session child doesn't dominate the dataset.
    """
    pairs: list[SnapshotPair] = []
    for seq in sequences:
        n = len(seq.times)
        if n < 2:
            continue
        # All ordered pairs i<j; subsample if needed.
        all_pairs = [(i, j) for i in range(n - 1) for j in range(i + 1, n)]
        if len(all_pairs) > max_pairs_per_child:
            rng = np.random.default_rng(42)
            idx = rng.choice(len(all_pairs), size=max_pairs_per_child, replace=False)
            all_pairs = [all_pairs[k] for k in idx]
        for i, j in all_pairs:
            pairs.append(SnapshotPair(
                z_prior=seq.Z[i], t_prior=float(seq.times[i]),
                z_target=seq.Z[j], t_target=float(seq.times[j]),
                child_id=seq.child_id, corpus=seq.corpus,
            ))
    return pairs


def _featurize(pairs: list[SnapshotPair]) -> tuple[np.ndarray, np.ndarray]:
    d = pairs[0].z_prior.shape[0]
    X = np.zeros((len(pairs), d + 2), dtype=float)
    Y = np.zeros((len(pairs), d), dtype=float)
    for k, p in enumerate(pairs):
        X[k, :d] = p.z_prior
        X[k, d] = p.t_prior
        X[k, d + 1] = p.delta_t
        Y[k] = p.z_target
    return X, Y


def fit_snapshot_predictor(train_pairs: list[SnapshotPair]):
    """One GBM per latent dim. Returns a predict(X) function (vectorised)."""
    X, Y = _featurize(train_pairs)
    d = Y.shape[1]
    models = [
        GradientBoostingRegressor(
            n_estimators=300, max_depth=3, learning_rate=0.05,
            subsample=0.9, random_state=0,
        ).fit(X, Y[:, j]) for j in range(d)
    ]

    def predict(X_query: np.ndarray) -> np.ndarray:
        preds = np.column_stack([m.predict(X_query) for m in models])
        return preds

    return predict


def population_mean_drift(train_pairs: list[SnapshotPair],
                          dt_bin_months: float = 3.0):
    """Estimate mean per-dim Δz as a step function of Δt over training pairs."""
    d = train_pairs[0].z_prior.shape[0]
    by_bin: dict[int, list[np.ndarray]] = {}
    for p in train_pairs:
        b = int(p.delta_t // dt_bin_months)
        by_bin.setdefault(b, []).append(p.z_target - p.z_prior)
    bin_mean = {b: np.mean(v, axis=0) for b, v in by_bin.items()}
    fallback = np.mean(np.vstack(list(bin_mean.values())), axis=0)

    def predict_drift(z_prior: np.ndarray, dt: float) -> np.ndarray:
        b = int(dt // dt_bin_months)
        return z_prior + bin_mean.get(b, fallback)

    return predict_drift


def evaluate_snapshot(
    sequences: list[ChildSequence],
    *,
    n_test_children: int = 12,
    age_predictor=None,
    random_state: int = 0,
) -> dict:
    """Train on N-k children's pairs, evaluate on held-out k children's pairs.

    Reports per-pair z-L2 MAE for: learned model, no-change baseline,
    population-mean-drift baseline. If `age_predictor` is supplied, also
    converts each prediction to age-space MAE.
    """
    rng = np.random.default_rng(random_state)
    by_child = {s.child_id: s for s in sequences}
    child_ids = sorted(by_child.keys())
    if len(child_ids) <= n_test_children:
        raise ValueError("Need more children than n_test_children for split.")
    test_ids = set(rng.choice(child_ids, size=n_test_children, replace=False))
    train_seqs = [by_child[c] for c in child_ids if c not in test_ids]
    test_seqs = [by_child[c] for c in child_ids if c in test_ids]

    train_pairs = build_pairs(train_seqs)
    test_pairs = build_pairs(test_seqs, max_pairs_per_child=20)
    if not train_pairs or not test_pairs:
        return {"error": "insufficient pairs"}

    predictor = fit_snapshot_predictor(train_pairs)
    drift_predictor = population_mean_drift(train_pairs)

    X_test, Y_test = _featurize(test_pairs)
    pred_learned = predictor(X_test)
    pred_nochange = X_test[:, :Y_test.shape[1]]
    pred_drift = np.array([
        drift_predictor(p.z_prior, p.delta_t) for p in test_pairs
    ])

    def z_l2_mae(pred):
        return float(np.mean(np.sqrt(np.sum((pred - Y_test) ** 2, axis=1))))

    out = {
        "n_train_pairs": len(train_pairs),
        "n_test_pairs": len(test_pairs),
        "n_test_children": len(test_seqs),
        "z_l2_mae_no_change": z_l2_mae(pred_nochange),
        "z_l2_mae_pop_drift": z_l2_mae(pred_drift),
        "z_l2_mae_learned": z_l2_mae(pred_learned),
    }

    if age_predictor is not None:
        actual_age = np.array([p.t_target for p in test_pairs])
        ages_actual_z = age_predictor(Y_test)
        ages_no_change = age_predictor(pred_nochange)
        ages_drift = age_predictor(pred_drift)
        ages_learned = age_predictor(pred_learned)
        out.update({
            "age_mae_floor_actual_z": float(np.mean(np.abs(ages_actual_z - actual_age))),
            "age_mae_no_change": float(np.mean(np.abs(ages_no_change - actual_age))),
            "age_mae_pop_drift": float(np.mean(np.abs(ages_drift - actual_age))),
            "age_mae_learned": float(np.mean(np.abs(ages_learned - actual_age))),
        })
    return out
