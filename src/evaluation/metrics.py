"""Cross-fold metric aggregation for Phase 1."""

from __future__ import annotations

import numpy as np
from scipy.stats import pearsonr

from src.models.phase1_age.train import ModelResult


def fold_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    err = y_pred - y_true
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    if len(y_true) > 1 and np.std(y_true) > 0 and np.std(y_pred) > 0:
        r, _ = pearsonr(y_true, y_pred)
    else:
        r = float("nan")
    return {"mae_months": mae, "rmse_months": rmse, "pearson_r": float(r)}


def summarize(result: ModelResult) -> dict[str, float]:
    """Aggregate metrics over all CV folds (concat then compute)."""
    y_true = np.concatenate([f.y_true for f in result.folds])
    y_pred = np.concatenate([f.y_pred for f in result.folds])
    out = {"model": result.name, "n_test": int(len(y_true))}
    out.update(fold_metrics(y_true, y_pred))
    # also report per-fold MAE std to gauge stability
    per_fold_mae = [float(np.mean(np.abs(f.y_pred - f.y_true))) for f in result.folds]
    out["mae_std_across_folds"] = float(np.std(per_fold_mae))
    return out
