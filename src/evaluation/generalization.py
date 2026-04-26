"""Leave-one-corpus-out generalization.

The Phase 1 / Phase 2 child-grouped K-fold tests held out *children*, but
every corpus appeared in both train and test. That doesn't catch the case
where a corpus has its own genre / recording / transcription idiosyncrasies
that the model has memorized.

This module trains on N-1 corpora and predicts the held-out corpus, repeated
for every corpus large enough to evaluate. The aggregate is corpus-weighted,
not transcript-weighted, so a single huge corpus can't dominate the metric.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor


def leave_one_corpus_out(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "age_months",
    corpus_col: str = "corpus",
    min_test_transcripts: int = 30,
    model_factory=lambda: GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0,
    ),
) -> pd.DataFrame:
    """Returns one row per held-out corpus with MAE and Pearson r."""
    work = df.dropna(subset=feature_cols + [target_col, corpus_col]).copy()
    rows = []
    for corpus in sorted(work[corpus_col].unique()):
        is_test = work[corpus_col] == corpus
        if is_test.sum() < min_test_transcripts:
            continue
        X_train = work.loc[~is_test, feature_cols].to_numpy(dtype=float)
        y_train = work.loc[~is_test, target_col].to_numpy(dtype=float)
        X_test = work.loc[is_test, feature_cols].to_numpy(dtype=float)
        y_test = work.loc[is_test, target_col].to_numpy(dtype=float)
        model = model_factory()
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        err = pred - y_test
        rows.append({
            "held_out_corpus": corpus,
            "n_test": int(is_test.sum()),
            "n_train": int((~is_test).sum()),
            "mae_months": float(np.mean(np.abs(err))),
            "rmse_months": float(np.sqrt(np.mean(err ** 2))),
            "mean_bias_months": float(np.mean(err)),
            "pearson_r": float(np.corrcoef(y_test, pred)[0, 1])
                          if np.std(pred) > 0 and np.std(y_test) > 0 else float("nan"),
        })
    out = pd.DataFrame(rows).sort_values("mae_months").reset_index(drop=True)
    return out


def aggregate_loco(loco_df: pd.DataFrame) -> dict:
    """Equal-weight average across held-out corpora (not transcript-weighted)."""
    return {
        "n_corpora_evaluated": int(len(loco_df)),
        "mae_corpus_mean": float(loco_df["mae_months"].mean()),
        "mae_corpus_median": float(loco_df["mae_months"].median()),
        "mae_corpus_std": float(loco_df["mae_months"].std()),
        "pearson_r_mean": float(loco_df["pearson_r"].mean()),
    }
