"""Strict permutation tests for content-state incremental value.

The first shuffled-WAB control preserved subtype labels. Raw r stayed high
because subtype means remain predictable and content features encode subtype.
This script tests the sharper null:

1. How much does content improve over subtype-only on true labels?
2. How large is that improvement when WAB is shuffled within subtype?
3. Within each subtype, does content predict severity better than shuffled
   labels?
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_cross_prompt_robustness import feature_sets, load_model_df  # noqa: E402
from src.analysis.review_grade import (  # noqa: E402
    cross_val_predict_regressor,
    ensure_dir,
    regression_summary,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--state", default="outputs/cross_prompt_state/patient_content_state.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/cross_prompt_incremental_permutation", type=Path)
    p.add_argument("--n-permutations", default=200, type=int)
    p.add_argument("--cv-folds", default=5, type=int)
    p.add_argument("--seed", default=17, type=int)
    return p.parse_args()


def run_model(df: pd.DataFrame, y_col: str, setup: str, cv_folds: int) -> dict:
    blocks, cats = feature_sets(df)[setup]
    y, pred = cross_val_predict_regressor(
        df,
        y_col,
        blocks,
        categorical_cols=cats,
        group_col="patient_root",
        cv_mode="group",
        n_splits=cv_folds,
    )
    return regression_summary(y, pred)


def permute_within(df: pd.DataFrame, col: str, group_col: str, rng: np.random.Generator) -> np.ndarray:
    y = df[col].to_numpy().copy()
    for _, idx in df.groupby(group_col).groups.items():
        idx = np.asarray(list(idx), dtype=int)
        y[idx] = rng.permutation(y[idx])
    return y


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    rng = np.random.default_rng(args.seed)
    df = load_model_df(args.state)

    actual_base = run_model(df, "wab_aq", "subtype_only", args.cv_folds)
    actual_aug = run_model(df, "wab_aq", "subtype+content+verbosity", args.cv_folds)
    actual = {
        "condition": "actual",
        "baseline_setup": "subtype_only",
        "augmented_setup": "subtype+content+verbosity",
        "baseline_r": actual_base["r"],
        "augmented_r": actual_aug["r"],
        "delta_r": actual_aug["r"] - actual_base["r"],
        "baseline_mae": actual_base["mae"],
        "augmented_mae": actual_aug["mae"],
        "delta_mae_improvement": actual_base["mae"] - actual_aug["mae"],
    }

    rows = []
    for i in range(args.n_permutations):
        perm = df.copy()
        perm["wab_perm"] = permute_within(perm, "wab_aq", "subtype", rng)
        base = run_model(perm, "wab_perm", "subtype_only", args.cv_folds)
        aug = run_model(perm, "wab_perm", "subtype+content+verbosity", args.cv_folds)
        rows.append(
            {
                "iteration": i,
                "baseline_r": base["r"],
                "augmented_r": aug["r"],
                "delta_r": aug["r"] - base["r"],
                "baseline_mae": base["mae"],
                "augmented_mae": aug["mae"],
                "delta_mae_improvement": base["mae"] - aug["mae"],
            }
        )
    perm_df = pd.DataFrame(rows)
    perm_df.to_csv(out_dir / "incremental_permutations.csv", index=False)

    summary = pd.DataFrame(
        [
            actual,
            {
                "condition": "perm_mean",
                "baseline_setup": "subtype_only",
                "augmented_setup": "subtype+content+verbosity",
                "baseline_r": perm_df["baseline_r"].mean(),
                "augmented_r": perm_df["augmented_r"].mean(),
                "delta_r": perm_df["delta_r"].mean(),
                "baseline_mae": perm_df["baseline_mae"].mean(),
                "augmented_mae": perm_df["augmented_mae"].mean(),
                "delta_mae_improvement": perm_df["delta_mae_improvement"].mean(),
            },
            {
                "condition": "perm_p95",
                "baseline_setup": "subtype_only",
                "augmented_setup": "subtype+content+verbosity",
                "baseline_r": perm_df["baseline_r"].quantile(0.95),
                "augmented_r": perm_df["augmented_r"].quantile(0.95),
                "delta_r": perm_df["delta_r"].quantile(0.95),
                "baseline_mae": perm_df["baseline_mae"].quantile(0.05),
                "augmented_mae": perm_df["augmented_mae"].quantile(0.05),
                "delta_mae_improvement": perm_df["delta_mae_improvement"].quantile(0.95),
            },
            {
                "condition": "perm_max",
                "baseline_setup": "subtype_only",
                "augmented_setup": "subtype+content+verbosity",
                "baseline_r": perm_df["baseline_r"].max(),
                "augmented_r": perm_df["augmented_r"].max(),
                "delta_r": perm_df["delta_r"].max(),
                "baseline_mae": perm_df["baseline_mae"].min(),
                "augmented_mae": perm_df["augmented_mae"].min(),
                "delta_mae_improvement": perm_df["delta_mae_improvement"].max(),
            },
        ]
    )
    summary["actual_minus_value_delta_r"] = actual["delta_r"] - summary["delta_r"]
    summary["actual_minus_value_delta_mae"] = actual["delta_mae_improvement"] - summary["delta_mae_improvement"]
    summary.to_csv(out_dir / "incremental_summary.csv", index=False)

    subtype_rows = []
    subtype_perm_rows = []
    for subtype, group in df.groupby("subtype"):
        if len(group) < 50 or group["patient_root"].nunique() < 40:
            continue
        actual_sub = run_model(group.reset_index(drop=True), "wab_aq", "content+verbosity", args.cv_folds)
        subtype_rows.append({"subtype": subtype, "condition": "actual", **actual_sub})
        for i in range(args.n_permutations):
            perm = group.reset_index(drop=True).copy()
            perm["wab_perm"] = rng.permutation(perm["wab_aq"].to_numpy())
            res = run_model(perm, "wab_perm", "content+verbosity", args.cv_folds)
            subtype_perm_rows.append({"subtype": subtype, "iteration": i, **res})
    subtype_actual = pd.DataFrame(subtype_rows)
    subtype_perm = pd.DataFrame(subtype_perm_rows)
    subtype_actual.to_csv(out_dir / "within_subtype_actual.csv", index=False)
    subtype_perm.to_csv(out_dir / "within_subtype_permutations.csv", index=False)
    subtype_summary_rows = []
    for subtype, actual_row in subtype_actual.groupby("subtype").first().iterrows():
        perm_sub = subtype_perm[subtype_perm["subtype"].eq(subtype)]
        subtype_summary_rows.append(
            {
                "subtype": subtype,
                "actual_r": actual_row["r"],
                "perm_mean_r": perm_sub["r"].mean(),
                "perm_p95_r": perm_sub["r"].quantile(0.95),
                "perm_max_r": perm_sub["r"].max(),
                "actual_mae": actual_row["mae"],
                "perm_p05_mae": perm_sub["mae"].quantile(0.05),
                "beats_perm_p95": bool(actual_row["r"] > perm_sub["r"].quantile(0.95)),
            }
        )
    subtype_summary = pd.DataFrame(subtype_summary_rows)
    subtype_summary.to_csv(out_dir / "within_subtype_summary.csv", index=False)

    print(summary.to_string(index=False))
    print(subtype_summary.to_string(index=False))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
