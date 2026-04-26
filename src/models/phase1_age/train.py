"""Phase 1: train age-prediction models from per-transcript features.

Three models:
  - `mlu_only`     — Ridge regression on MLU (words) alone. Floor baseline.
  - `kideval_only` — Ridge on classic KidEval features (MLU/NDW/verbs/tokens).
  - `ridge_full`   — Ridge on the full feature set.
  - `gbm_full`     — Gradient boosting on the full feature set.

Held-out evaluation is **child-grouped** (`GroupKFold` over `child_id`) so the
same child cannot appear in both train and test folds — what we actually want
to know is generalization to a new child, not memorization of one child's
trajectory.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MLU_FEATURES = ["mlu_words"]
KIDEVAL_FEATURES = ["mlu_words", "mlu_morphemes", "ndw", "total_words",
                    "verbs_per_utterance"]


@dataclass
class FoldResult:
    fold: int
    y_true: np.ndarray
    y_pred: np.ndarray
    test_child_ids: list[str]


@dataclass
class ModelResult:
    name: str
    feature_names: list[str]
    folds: list[FoldResult]
    feature_importances: dict[str, float] | None  # mean across folds for tree models
    fitted_full: object  # model trained on all data, for inspection / reuse


def _make_models(feature_count: int) -> dict[str, object]:
    return {
        "ridge": Pipeline([
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=1.0, random_state=0)),
        ]),
        "gbm": GradientBoostingRegressor(
            n_estimators=400,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            random_state=0,
        ),
    }


def train_and_evaluate(
    df: pd.DataFrame,
    *,
    feature_cols: list[str],
    target_col: str = "age_months",
    group_col: str = "child_id",
    n_splits: int = 5,
    model_kind: str = "ridge",
) -> ModelResult:
    """Train + cross-validate a single model spec.

    `df` must have columns `feature_cols + [target_col, group_col]`.
    """
    # Drop rows missing any feature or the target.
    work = df.dropna(subset=feature_cols + [target_col, group_col]).reset_index(drop=True)

    X = work[feature_cols].to_numpy(dtype=float)
    y = work[target_col].to_numpy(dtype=float)
    groups = work[group_col].to_numpy()

    # GroupKFold with k > n_groups would error; clamp.
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)

    folds: list[FoldResult] = []
    fold_importances: list[np.ndarray] = []
    for i, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        model = _make_models(len(feature_cols))[model_kind]
        model.fit(X[train_idx], y[train_idx])
        y_pred = model.predict(X[test_idx])
        folds.append(FoldResult(
            fold=i,
            y_true=y[test_idx],
            y_pred=y_pred,
            test_child_ids=list(groups[test_idx]),
        ))
        if hasattr(model, "feature_importances_"):
            fold_importances.append(model.feature_importances_)
        elif hasattr(model, "named_steps") and hasattr(model.named_steps.get("model"), "coef_"):
            # Use absolute standardized coefficients as a rough importance proxy.
            fold_importances.append(np.abs(model.named_steps["model"].coef_))

    # Refit on full data for downstream inspection.
    full_model = _make_models(len(feature_cols))[model_kind]
    full_model.fit(X, y)

    importances = None
    if fold_importances:
        mean = np.mean(np.vstack(fold_importances), axis=0)
        importances = {name: float(val) for name, val in zip(feature_cols, mean)}

    return ModelResult(
        name=f"{model_kind}::{len(feature_cols)}feat",
        feature_names=feature_cols,
        folds=folds,
        feature_importances=importances,
        fitted_full=full_model,
    )
