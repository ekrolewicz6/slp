"""Bundle E: prediction intervals for age estimates.

Runs on the windowed feature table (better-behaved than file-level) and
reports calibration of an 80% interval plus age-bin breakdown.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.models.phase1_age.intervals import evaluate_quantile_intervals


META_COLS = {"transcript_id", "corpus", "child_id", "age_months",
             "n_chi_utterances", "window_id", "window_index",
             "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/phase1_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/bundle_e", type=Path)
    p.add_argument("--max-age-months", type=float, default=84.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df = df.dropna(subset=["age_months", "child_id"]).copy()
    df = df[(df.age_months > 0) & (df.age_months <= args.max_age_months)]
    feature_cols = [c for c in df.columns if c not in META_COLS]
    print(f"loaded {len(df)} windowed rows | {len(feature_cols)} features")

    print("Fitting quantile GBMs at q={0.1, 0.5, 0.9} ...")
    res = evaluate_quantile_intervals(df, feature_cols)
    print(f"  observed coverage: {res['coverage_observed']:.3f}  "
          f"(target {res['coverage_target']:.2f})")
    print(f"  median-MAE       : {res['median_mae_months']:.2f} mo")
    print(f"  mean width       : {res['mean_interval_width_months']:.2f} mo")
    print(f"\nBy age bin (months):")
    by_bin_df = pd.DataFrame(res["by_age_bin"])
    print(by_bin_df.to_string(index=False, float_format=lambda v: f"{v:6.2f}"))

    by_bin_df.to_csv(args.output_dir / "by_age_bin.csv", index=False)
    with open(args.output_dir / "summary.json", "w") as f:
        json.dump({k: v for k, v in res.items() if k != "by_age_bin"}, f, indent=2)
    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
