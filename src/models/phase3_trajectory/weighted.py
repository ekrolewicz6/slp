"""Outcome-weighted trajectory fitting.

Phase 3 dry run found: GP wins on z-L2 MAE but loses on age-MAE because it
spends capacity on z dimensions that don't carry age signal. Fix: scale each
latent dim by its outcome relevance before fitting per-dim trajectories.
After scaling, equal-weight MSE in z-space approximates outcome-weighted
loss in age-space.

Use:
    weights = outcome_weights_from_gbm(Z, y)
    wrapped = OutcomeWeightedWrapper(GPTrajectory(), weights)
    wrapped.predict(history_t, history_Z, t_query)  # → ẑ in original scale

This is a thin transform; the underlying trajectory model is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import permutation_importance

from src.models.phase3_trajectory.models import TrajectoryModel


def outcome_weights_from_gbm(
    Z: np.ndarray,
    y: np.ndarray,
    *,
    n_repeats: int = 5,
    floor: float = 0.05,
    random_state: int = 0,
) -> np.ndarray:
    """Per-dim weights ∝ permutation importance for predicting y from z.

    A floor keeps low-importance dims from collapsing to zero (which would
    make the inverse-scaled prediction ill-defined and prevent any z-space
    movement on those dims). Returns weights normalised to mean 1.0.
    """
    model = GradientBoostingRegressor(
        n_estimators=300, max_depth=3, learning_rate=0.05,
        random_state=random_state,
    ).fit(Z, y)
    pi = permutation_importance(
        model, Z, y, n_repeats=n_repeats, random_state=random_state,
        scoring="neg_mean_absolute_error",
    )
    raw = np.maximum(pi.importances_mean, 0.0)
    raw = np.maximum(raw, raw.max() * floor)  # apply floor relative to top
    return raw / raw.mean()


@dataclass
class OutcomeWeightedWrapper(TrajectoryModel):
    """Wrap an existing trajectory model with outcome-weighted dim scaling."""
    base: TrajectoryModel
    weights: np.ndarray  # shape (d,), positive

    @property
    def name(self) -> str:
        return f"{self.base.name}_w"

    def predict(self, history_t: np.ndarray, history_Z: np.ndarray,
                t_query: float) -> np.ndarray:
        scale = np.sqrt(self.weights)
        Z_scaled = history_Z * scale
        z_pred_scaled = self.base.predict(history_t, Z_scaled, t_query)
        return z_pred_scaled / scale
