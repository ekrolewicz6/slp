"""Quantile-regression prediction intervals for age estimates.

Replaces a single point prediction with [q0.1, q0.5, q0.9] from three
gradient-boosting quantile regressors. The interval [q0.1, q0.9] is
calibrated to ~80% coverage in expectation; we report empirical coverage
on held-out folds plus the mean interval width.

Used at output time to deliver "predicted developmental age = X months,
80% interval [Y, Z]" instead of a bare scalar.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold


def evaluate_quantile_intervals(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "age_months",
    group_col: str = "child_id",
    n_splits: int = 5,
    quantiles: tuple[float, float, float] = (0.1, 0.5, 0.9),
) -> dict:
    """Child-grouped CV. Returns coverage, mean width, and per-bin breakdown."""
    work = df.dropna(subset=feature_cols + [target_col, group_col]).reset_index(drop=True)
    X = work[feature_cols].to_numpy(dtype=float)
    y = work[target_col].to_numpy(dtype=float)
    groups = work[group_col].to_numpy()

    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)

    pred_lo = np.zeros_like(y)
    pred_md = np.zeros_like(y)
    pred_hi = np.zeros_like(y)
    for train_idx, test_idx in gkf.split(X, y, groups):
        Xt, yt = X[train_idx], y[train_idx]
        Xv = X[test_idx]
        models = {q: GradientBoostingRegressor(
            loss="quantile", alpha=q, n_estimators=400, max_depth=3,
            learning_rate=0.05, subsample=0.9, random_state=0,
        ).fit(Xt, yt) for q in quantiles}
        pred_lo[test_idx] = models[quantiles[0]].predict(Xv)
        pred_md[test_idx] = models[quantiles[1]].predict(Xv)
        pred_hi[test_idx] = models[quantiles[2]].predict(Xv)

    in_band = (y >= pred_lo) & (y <= pred_hi)
    width = pred_hi - pred_lo
    median_mae = float(np.mean(np.abs(pred_md - y)))
    coverage_target = quantiles[2] - quantiles[0]

    # Per-age-bin breakdown so we can see if intervals widen as kids get older.
    bins = np.linspace(y.min(), y.max(), 6)
    bin_idx = np.digitize(y, bins[1:-1])
    by_bin = []
    for b in range(len(bins) - 1):
        m = bin_idx == b
        if m.sum() < 5:
            continue
        by_bin.append({
            "bin_age_lo": float(bins[b]),
            "bin_age_hi": float(bins[b + 1]),
            "n": int(m.sum()),
            "coverage": float(in_band[m].mean()),
            "mean_width": float(width[m].mean()),
            "median_mae": float(np.mean(np.abs(pred_md[m] - y[m]))),
        })
    return {
        "n": int(len(y)),
        "coverage_target": coverage_target,
        "coverage_observed": float(in_band.mean()),
        "median_mae_months": median_mae,
        "mean_interval_width_months": float(width.mean()),
        "by_age_bin": by_bin,
    }
