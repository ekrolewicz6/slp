"""Phase 1 plots: predicted-vs-actual, residuals by corpus, feature importance."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.models.phase1_age.train import ModelResult


def predicted_vs_actual(result: ModelResult, out_path: Path, title: str) -> None:
    y_true = np.concatenate([f.y_true for f in result.folds])
    y_pred = np.concatenate([f.y_pred for f in result.folds])
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_true, y_pred, alpha=0.4, s=18)
    lo, hi = float(min(y_true.min(), y_pred.min())), float(max(y_true.max(), y_pred.max()))
    ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="y = x")
    ax.set_xlabel("Actual age (months)")
    ax.set_ylabel("Predicted age (months)")
    ax.set_title(title)
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def residuals_by_corpus(result: ModelResult, df: pd.DataFrame, out_path: Path,
                        title: str) -> None:
    y_true = np.concatenate([f.y_true for f in result.folds])
    y_pred = np.concatenate([f.y_pred for f in result.folds])
    test_children = sum([f.test_child_ids for f in result.folds], [])
    res = pd.DataFrame({
        "child_id": test_children,
        "residual": y_pred - y_true,
    })
    # Map child_id → corpus via df.
    lookup = df.drop_duplicates("child_id").set_index("child_id")["corpus"]
    res["corpus"] = res["child_id"].map(lookup).fillna("?")

    corpora = sorted(res["corpus"].unique())
    data = [res.loc[res["corpus"] == c, "residual"].to_numpy() for c in corpora]

    fig, ax = plt.subplots(figsize=(max(6, 0.4 * len(corpora) + 4), 5))
    ax.axhline(0, color="k", lw=0.8, alpha=0.5)
    ax.boxplot(data, tick_labels=corpora, showfliers=False)
    ax.set_ylabel("Residual (predicted − actual, months)")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def feature_importance(result: ModelResult, out_path: Path, title: str,
                       top_n: int = 20) -> None:
    if not result.feature_importances:
        return
    items = sorted(result.feature_importances.items(), key=lambda kv: kv[1],
                   reverse=True)[:top_n]
    names = [k for k, _ in items][::-1]
    vals = [v for _, v in items][::-1]
    fig, ax = plt.subplots(figsize=(7, max(4, 0.3 * len(names) + 1)))
    ax.barh(names, vals)
    ax.set_xlabel("Importance (mean across folds)")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
