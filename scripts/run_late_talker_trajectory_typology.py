"""Create a trajectory typology for Rescorla late talkers.

The earlier analysis showed that earliest state is weak, while 36-to-48 month
movement is more predictive. This script turns that into interpretable
trajectory classes and checks sensitivity to the early-gain threshold.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--model-table",
        default="outputs/dld_late_talker_persistence_sensitivity/late_talker_model_table.csv",
        type=Path,
    )
    p.add_argument(
        "--trajectories",
        default="outputs/dld_late_talker_catchup/rescorla_trajectories.csv",
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/late_talker_trajectory_typology", type=Path)
    p.add_argument("--strong-gain-threshold", type=float, default=0.75)
    return p.parse_args()


def trajectory_class(row: pd.Series, threshold: float) -> str:
    delta = row.get("delta_36_48_composite_z", np.nan)
    if pd.isna(delta):
        return "missing_36_48_movement"
    strong_gain = delta >= threshold
    persistent = bool(row.get("persistent_gap", False))
    recovered = bool(row.get("final_in_td_band", False))
    if persistent and strong_gain:
        return "early_gain_but_persistent_gap"
    if persistent:
        return "low_early_gain_persistent_gap"
    if recovered and strong_gain:
        return "early_gain_recovered"
    if recovered:
        return "late_or_low_early_gain_recovered"
    if strong_gain:
        return "early_gain_partial_recovery"
    return "low_early_gain_partial_or_unresolved"


def sensitivity_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold in [0.25, 0.50, 0.75, 1.00]:
        subset = df[df["delta_36_48_composite_z"].notna()].copy()
        subset["early_gain"] = subset["delta_36_48_composite_z"] >= threshold
        for target in ["final_in_td_band", "persistent_gap"]:
            target_bool = subset[target].astype(bool)
            gain_bool = subset["early_gain"].astype(bool)
            true_pos = int((gain_bool & target_bool).sum())
            true_neg = int((gain_bool & ~target_bool).sum())
            false_pos = int((~gain_bool & target_bool).sum())
            false_neg = int((~gain_bool & ~target_bool).sum())
            table = [[true_pos, true_neg], [false_pos, false_neg]]
            try:
                odds_ratio, p_value = fisher_exact(table)
            except Exception:
                odds_ratio, p_value = np.nan, np.nan
            for early_gain, group in subset.groupby("early_gain"):
                rows.append(
                    {
                        "threshold": threshold,
                        "target": target,
                        "early_gain": bool(early_gain),
                        "n": len(group),
                        "target_rate": float(group[target].mean()),
                        "odds_ratio_gain_vs_no_gain": float(odds_ratio),
                        "fisher_p": float(p_value),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    model = pd.read_csv(args.model_table)
    traj = pd.read_csv(args.trajectories)
    df = model.merge(
        traj[["participant_root", "n_ages", "delta_composite_z", "slope_z_per_month", "last_mlu"]],
        on="participant_root",
        how="left",
    )
    df["trajectory_class"] = df.apply(trajectory_class, axis=1, threshold=args.strong_gain_threshold)
    df["early_gain_bin"] = pd.cut(
        df["delta_36_48_composite_z"],
        bins=[-np.inf, 0.0, 0.25, 0.50, 0.75, 1.00, np.inf],
        labels=["decline", "0-0.25z", "0.25-0.50z", "0.50-0.75z", "0.75-1.00z", ">=1.00z"],
    ).astype(str)
    df.loc[df["delta_36_48_composite_z"].isna(), "early_gain_bin"] = "missing"

    class_summary = (
        df.groupby("trajectory_class")
        .agg(
            n=("participant_root", "count"),
            final_td_rate=("final_in_td_band", "mean"),
            persistent_gap_rate=("persistent_gap", "mean"),
            mean_first_composite_z=("first_composite_z", "mean"),
            mean_delta_36_48_z=("delta_36_48_composite_z", "mean"),
            mean_last_composite_z=("last_composite_z", "mean"),
            mean_age_last=("age_last", "mean"),
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )
    gain_bin_summary = (
        df.groupby("early_gain_bin", dropna=False)
        .agg(
            n=("participant_root", "count"),
            final_td_rate=("final_in_td_band", "mean"),
            persistent_gap_rate=("persistent_gap", "mean"),
            mean_last_composite_z=("last_composite_z", "mean"),
        )
        .reset_index()
    )
    sensitivity = sensitivity_rows(df)
    long_horizon = df[df["age_last"] >= 108].copy()
    long_horizon_summary = (
        long_horizon.groupby("trajectory_class")
        .agg(
            n=("participant_root", "count"),
            final_td_rate=("final_in_td_band", "mean"),
            persistent_gap_rate=("persistent_gap", "mean"),
            mean_last_composite_z=("last_composite_z", "mean"),
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )

    df.to_csv(out_dir / "late_talker_trajectory_classes.csv", index=False)
    class_summary.to_csv(out_dir / "trajectory_class_summary.csv", index=False)
    gain_bin_summary.to_csv(out_dir / "early_gain_bin_summary.csv", index=False)
    sensitivity.to_csv(out_dir / "early_gain_threshold_sensitivity.csv", index=False)
    long_horizon_summary.to_csv(out_dir / "long_horizon_class_summary.csv", index=False)

    compact_sensitivity = sensitivity[
        sensitivity["target"].isin(["final_in_td_band", "persistent_gap"])
    ].copy()
    compact_sensitivity["target_rate"] = compact_sensitivity["target_rate"].round(3)
    compact_sensitivity["odds_ratio_gain_vs_no_gain"] = compact_sensitivity[
        "odds_ratio_gain_vs_no_gain"
    ].round(3)
    compact_sensitivity["fisher_p"] = compact_sensitivity["fisher_p"].round(3)

    lines = [
        "# Late-Talker Trajectory Typology",
        "",
        f"- Late talkers typed: {len(df):,}",
        f"- Strong early-gain threshold: >= {args.strong_gain_threshold:.2f} z from 36 to 48 months",
        f"- Participants with measured 36-to-48 movement: {df['delta_36_48_composite_z'].notna().sum():,}",
        "",
        "## Trajectory Classes",
        "",
        md_table(class_summary.round(3)),
        "",
        "## Long-Horizon Subset (final age >= 108 months)",
        "",
        md_table(long_horizon_summary.round(3)),
        "",
        "## Early-Gain Bins",
        "",
        md_table(gain_bin_summary.round(3)),
        "",
        "## Threshold Sensitivity",
        "",
        md_table(compact_sensitivity),
        "",
        "## Interpretation",
        "",
        "The useful construct is not earliest late-talker severity. It is early movement. A strong 36-to-48 month gain is associated with higher final TD-band rates and lower persistent-gap rates, especially at stricter thresholds. The sample is small and not treatment-linked, so this should be framed as a trajectory-phenotyping result and a prospective-study design clue, not as a clinical prognosis model.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
