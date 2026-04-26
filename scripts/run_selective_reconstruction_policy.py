"""Selective reconstruction policy simulation.

Experiment #59 showed that oracle target augmentation helps mainly in
high-error, known-target segments. This script asks what a clinical control
policy should do before we spend compute on LLM rewrites:

* preserve raw speech;
* rewrite known-target errors;
* rewrite all errors;
* abstain around unknown-intent errors;
* estimate the oracle upper bound.

The policies still use CHAT target annotations when they choose "rewrite", so
this is a simulation, not a deployable assistant. The point is to quantify the
scientific/clinical value of selective reconstruction versus blanket cleaning.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import (  # noqa: E402
    bootstrap_ci,
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--features-path",
        default="outputs/error_aware_reconstruction/segment_error_features.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/selective_reconstruction_policy", type=Path)
    parser.add_argument("--cv-folds", default=5, type=int)
    return parser.parse_args()


def policy_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "preserve_raw": pd.Series(False, index=df.index),
        "rewrite_all": pd.Series(True, index=df.index),
        "rewrite_any_error": df["error_total"] > 0,
        "rewrite_known_target": df["known_reconstructable_error_count"] > 0,
        "rewrite_known_no_unknown": (df["known_reconstructable_error_count"] > 0)
        & (df["unknown_intent_error_count"] == 0),
        "rewrite_phonological_known": (
            (df["error_p_w"] + df["error_p_n"] + df["error_p_m"]) > 0
        )
        & (df["unknown_intent_error_count"] == 0),
        "abstain_unknown_rewrite_known": (df["known_reconstructable_error_count"] > 0)
        & (df["unknown_intent_error_count"] == 0),
        "oracle_gain_only": df["oracle_concept_gain"] > 0,
        "oracle_safe_gain_only": (df["oracle_concept_gain"] > 0)
        & (df["unknown_intent_error_count"] == 0),
    }


def add_policy_features(df: pd.DataFrame, policy: str, mask: pd.Series) -> pd.DataFrame:
    out = df.copy()
    m = mask.astype(bool).to_numpy()
    out["policy"] = policy
    out["policy_rewrite"] = m
    out["policy_concept_coverage"] = np.where(
        m, out["target_augmented_concept_coverage"], out["observed_concept_coverage"]
    )
    out["policy_concept_coverage_frac"] = np.where(
        m, out["target_augmented_concept_coverage_frac"], out["observed_concept_coverage_frac"]
    )
    out["policy_n_tokens"] = np.where(
        m, out["target_augmented_n_tokens"], out["observed_n_tokens"]
    )
    out["policy_concept_density"] = out["policy_concept_coverage"] / out["policy_n_tokens"].clip(
        lower=1
    )
    out["policy_concept_token_ratio"] = np.where(
        m, out["target_augmented_concept_token_ratio"], out["observed_concept_token_ratio"]
    )
    out["policy_gain_frac"] = out["policy_concept_coverage_frac"] - out[
        "observed_concept_coverage_frac"
    ]

    for task, group in out.groupby("task"):
        controls = group[group["is_control"].astype(bool)]
        vals = controls["policy_concept_coverage_frac"].dropna()
        if len(vals) < 5:
            vals = group["policy_concept_coverage_frac"].dropna()
        mean = float(vals.mean()) if len(vals) else 0.0
        sd = float(vals.std(ddof=0)) if len(vals) else 1.0
        if not np.isfinite(sd) or sd <= 0:
            sd = 1.0
        idx = group.index
        out.loc[idx, "policy_control_gap"] = out.loc[idx, "policy_concept_coverage_frac"] - mean
        out.loc[idx, "policy_control_z"] = out.loc[idx, "policy_control_gap"] / sd
        out.loc[idx, "policy_control_pct"] = out.loc[idx, "policy_concept_coverage_frac"] / max(
            mean, 1e-6
        )
    return out


def summarize_policy(df: pd.DataFrame, policy_df: pd.DataFrame) -> dict[str, float | int | str]:
    rewrite = policy_df["policy_rewrite"].astype(bool)
    gain_possible = df["oracle_concept_gain_frac"].clip(lower=0)
    gain_captured = policy_df["policy_gain_frac"].clip(lower=0)
    total_possible = float(gain_possible.sum())
    rewritten = policy_df[rewrite]
    positive_gain = df["oracle_concept_gain"] > 0

    return {
        "policy": str(policy_df["policy"].iloc[0]),
        "n_segments": int(len(policy_df)),
        "n_rewritten": int(rewrite.sum()),
        "rewrite_rate": float(rewrite.mean()),
        "mean_policy_gain_frac": float(policy_df["policy_gain_frac"].mean()),
        "total_gain_captured_frac": float(gain_captured.sum() / total_possible)
        if total_possible > 0
        else 0.0,
        "positive_gain_recall": float((rewrite & positive_gain).sum() / max(int(positive_gain.sum()), 1)),
        "unnecessary_rewrite_rate": float((rewrite & ~positive_gain).sum() / max(int(rewrite.sum()), 1)),
        "rewritten_unknown_intent_rate": float(
            rewritten["has_unknown_intent_error"].mean() if len(rewritten) else 0.0
        ),
        "rewritten_mean_unknown_intent_error_rate_100": float(
            rewritten["unknown_intent_error_rate_100"].mean() if len(rewritten) else 0.0
        ),
    }


def metric_row(work: pd.DataFrame, setup: str, y: np.ndarray, pred: np.ndarray, subset: str) -> dict:
    groups = work["patient_root"].astype(str).to_numpy()
    r_mean, r_lo, r_hi = bootstrap_ci(y, pred, pearson_safe, groups=groups, n_boot=500, seed=0)
    return {
        "subset": subset,
        "setup": setup,
        **regression_summary(y, pred),
        "r_boot_mean": r_mean,
        "r_boot_lo": r_lo,
        "r_boot_hi": r_hi,
        "n_patients": int(work["patient_root"].nunique()),
    }


def run_policy_wab_models(policy_frames: list[pd.DataFrame], cv_folds: int) -> pd.DataFrame:
    feature_cols = [
        "policy_concept_coverage",
        "policy_concept_coverage_frac",
        "policy_concept_density",
        "policy_concept_token_ratio",
        "policy_control_z",
        "policy_control_gap",
        "policy_control_pct",
    ]
    error_cols = [
        "error_rate_100",
        "known_reconstructable_error_rate_100",
        "unknown_intent_error_rate_100",
        "paper_bottleneck_error_rate_100",
    ]
    rows = []
    for frame in policy_frames:
        policy = str(frame["policy"].iloc[0])
        base = frame[frame["wab_aq"].notna() & ~frame["is_control"].astype(bool)].copy()
        q75 = float(base["paper_bottleneck_error_rate_100"].quantile(0.75))
        subsets = {
            "all_noncontrol_wab": base,
            "high_bottleneck_error_q75": base[base["paper_bottleneck_error_rate_100"] >= q75],
            "unknown_intent_error": base[base["unknown_intent_error_count"] > 0],
        }
        for subset, work in subsets.items():
            work = work.dropna(subset=["patient_root"]).reset_index(drop=True)
            if len(work) < 80 or work["patient_root"].nunique() < 20:
                continue
            setups = {
                f"{policy}:policy_content+task": ({"content": feature_cols}, ["task"]),
                f"{policy}:policy_content+error_profile+task": (
                    {"content": feature_cols, "error_profile": error_cols},
                    ["task"],
                ),
            }
            for setup, (blocks, cats) in setups.items():
                y, pred = cross_val_predict_regressor(
                    work,
                    "wab_aq",
                    blocks,
                    categorical_cols=cats,
                    group_col="patient_root",
                    cv_mode="group",
                    n_splits=cv_folds,
                )
                rows.append(metric_row(work, setup, y, pred, subset))
    return pd.DataFrame(rows)


def md_table(frame: pd.DataFrame, cols: list[str] | None = None, n: int | None = None) -> str:
    if frame.empty:
        return ""
    data = frame.copy()
    if cols:
        data = data[cols]
    if n:
        data = data.head(n)
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else str(x))
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(data.loc[i].astype(str).tolist()) + " |" for i in data.index]
    return "\n".join([header, sep] + body)


def write_summary(out_dir: Path, summaries: pd.DataFrame, models: pd.DataFrame) -> None:
    lines = [
        "# Selective Reconstruction Policy",
        "",
        "## Policy Tradeoffs",
        "",
        md_table(
            summaries.sort_values(
                ["total_gain_captured_frac", "rewritten_unknown_intent_rate"],
                ascending=[False, True],
            ),
            [
                "policy",
                "rewrite_rate",
                "mean_policy_gain_frac",
                "total_gain_captured_frac",
                "positive_gain_recall",
                "unnecessary_rewrite_rate",
                "rewritten_unknown_intent_rate",
            ],
        ),
        "",
        "## Best Clinical-Signal Models",
        "",
    ]
    if not models.empty:
        view = models.sort_values(["subset", "r"], ascending=[True, False]).groupby("subset").head(8)
        lines.append(md_table(view, ["subset", "setup", "n", "n_patients", "mae", "r"]))
    else:
        lines.append("No models were run.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The safest deployable policy is not necessarily the policy with the highest oracle gain. "
            "A clinically useful assistant should maximize known-target content recovery while minimizing "
            "rewrites in unknown-intent segments, where the chance of plausible hallucination is highest.",
            "",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    df = pd.read_csv(args.features_path)

    frames = []
    summaries = []
    for policy, mask in policy_masks(df).items():
        frame = add_policy_features(df, policy, mask)
        frames.append(frame)
        summaries.append(summarize_policy(df, frame))

    summaries_df = pd.DataFrame(summaries)
    summaries_df.to_csv(out_dir / "policy_tradeoffs.csv", index=False)

    models = run_policy_wab_models(frames, args.cv_folds)
    models.to_csv(out_dir / "policy_wab_model_results.csv", index=False)
    write_summary(out_dir, summaries_df, models)

    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
