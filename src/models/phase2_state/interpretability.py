"""Make z dimensions interpretable.

Two layers:

1. **Loadings**: which input features each latent dim is built from. For PCA
   this is the standardized component vector; for the autoencoder it falls
   back to a numerical Jacobian at each row's encoder mapping (averaged).
   Reported as top-k positive and top-k negative features per dim.

2. **Outcome relevance**: how much each latent dim contributes to the age
   prediction. We compute (a) absolute Pearson r between each dim and age,
   and (b) GBM permutation importance per dim — they often disagree, which
   is itself informative.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold

from src.models.phase2_state.representation import StateModel


def loadings_table(state: StateModel, top_k: int = 6) -> pd.DataFrame:
    """For each latent dim d, return its top_k +/- input features."""
    components = state.pca.components_  # (d, n_features)
    feature_names = state.feature_names
    rows = []
    for j, comp in enumerate(components):
        order = np.argsort(comp)
        bottom = order[:top_k]
        top = order[::-1][:top_k]
        rows.append({
            "dim": f"z{j+1}",
            "variance_explained": float(state.pca.explained_variance_ratio_[j]),
            "top_positive": ", ".join(
                f"{feature_names[i]} (+{comp[i]:.2f})" for i in top
            ),
            "top_negative": ", ".join(
                f"{feature_names[i]} ({comp[i]:.2f})" for i in bottom
            ),
        })
    return pd.DataFrame(rows)


def outcome_relevance(
    Z: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    n_splits: int = 5,
    n_permutation_repeats: int = 5,
    random_state: int = 0,
) -> pd.DataFrame:
    """Per-dim Pearson r with target + permutation importance from a GBM.

    Permutation importance is computed inside child-grouped folds and then
    averaged, so the score reflects out-of-sample contribution.
    """
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    importances = np.zeros(Z.shape[1])
    for train_idx, test_idx in gkf.split(Z, y, groups):
        model = GradientBoostingRegressor(
            n_estimators=400, max_depth=3, learning_rate=0.05,
            subsample=0.9, random_state=random_state,
        ).fit(Z[train_idx], y[train_idx])
        r = permutation_importance(
            model, Z[test_idx], y[test_idx],
            n_repeats=n_permutation_repeats, random_state=random_state,
            scoring="neg_mean_absolute_error",
        )
        importances += r.importances_mean
    importances /= splits

    pearson = np.array([
        float(np.corrcoef(Z[:, j], y)[0, 1]) if np.std(Z[:, j]) > 0 else 0.0
        for j in range(Z.shape[1])
    ])
    return pd.DataFrame({
        "dim": [f"z{j+1}" for j in range(Z.shape[1])],
        "abs_pearson_with_age": np.abs(pearson),
        "pearson_with_age": pearson,
        "permutation_importance_mae": importances,
    }).sort_values("permutation_importance_mae", ascending=False).reset_index(drop=True)
