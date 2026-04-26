"""Bundle D: outcome-weighted trajectories + single-snapshot prediction."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from src.models.phase2_state.representation import fit_state
from src.models.phase3_trajectory.evaluation import evaluate_leave_last_out
from src.models.phase3_trajectory.models import (
    GPTrajectory,
    LinearExtrapolation,
    MeanBaseline,
)
from src.models.phase3_trajectory.sequences import build_sequences
from src.models.phase3_trajectory.single_snapshot import evaluate_snapshot
from src.models.phase3_trajectory.weighted import (
    OutcomeWeightedWrapper,
    outcome_weights_from_gbm,
)


META_COLS = {"transcript_id", "corpus", "child_id", "age_months", "n_chi_utterances"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path", default="data/features/phase1_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/bundle_d", type=Path)
    p.add_argument("--latent-d", type=int, default=8)
    p.add_argument("--max-age-months", type=float, default=84.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df = df.dropna(subset=["age_months", "child_id"]).copy()
    df = df[(df.age_months > 0) & (df.age_months <= args.max_age_months)]
    df = df.reset_index(drop=True)
    feature_cols = sorted(c for c in df.columns if c not in META_COLS)

    state = fit_state(df, feature_cols, d=args.latent_d)
    Z = state.transform(df)
    y = df["age_months"].to_numpy(dtype=float)
    sequences = build_sequences(df, Z)

    # Build a Phase-1-style age predictor on z (for interpretable age MAE).
    age_model = GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0,
    ).fit(Z, y)

    print(f"loaded {len(df)} transcripts, {len(sequences)} longitudinal children")

    # ------------------------------------------------------------------
    # D1: outcome-weighted vs baseline trajectory models.
    # ------------------------------------------------------------------
    print(f"\n[D1] Outcome-weighted trajectory models")
    weights = outcome_weights_from_gbm(Z, y)
    print(f"  per-dim age weights (mean=1.0): "
          f"{np.array2string(weights, precision=2, suppress_small=True)}")

    base_models = [MeanBaseline(), LinearExtrapolation(), GPTrajectory()]
    rows = []
    for base in base_models:
        s_unw = evaluate_leave_last_out(base, sequences,
                                        age_predictor=age_model.predict)
        s_wgt = evaluate_leave_last_out(
            OutcomeWeightedWrapper(base, weights), sequences,
            age_predictor=age_model.predict,
        )
        rows.append({
            "model": base.name,
            "z_l2_unweighted": s_unw["mean_z_l2_error"],
            "z_l2_weighted":   s_wgt["mean_z_l2_error"],
            "age_mae_unweighted": s_unw["age_mae_from_predicted_z"],
            "age_mae_weighted":   s_wgt["age_mae_from_predicted_z"],
        })
        print(f"  {base.name:7s}  z-L2 {s_unw['mean_z_l2_error']:.3f} "
              f"→ {s_wgt['mean_z_l2_error']:.3f}   "
              f"age-MAE {s_unw['age_mae_from_predicted_z']:.2f} "
              f"→ {s_wgt['age_mae_from_predicted_z']:.2f}")

    pd.DataFrame(rows).to_csv(args.output_dir / "weighted_vs_unweighted.csv",
                              index=False)
    print(f"  floor (age MAE from actual z): "
          f"{rows[0]['age_mae_unweighted'] - 0:.2f} ... "
          f"(see Phase 3 dry run for 6.74 reference)")

    # ------------------------------------------------------------------
    # D2: single-snapshot prediction.
    # ------------------------------------------------------------------
    print(f"\n[D2] Single-snapshot: predict ẑ from one prior session")
    snap = evaluate_snapshot(sequences, n_test_children=12,
                             age_predictor=age_model.predict)
    print(f"  pairs: {snap['n_train_pairs']} train, {snap['n_test_pairs']} test "
          f"({snap['n_test_children']} held-out children)")
    print(f"  z-L2 MAE   no-change={snap['z_l2_mae_no_change']:.3f}  "
          f"pop-drift={snap['z_l2_mae_pop_drift']:.3f}  "
          f"learned={snap['z_l2_mae_learned']:.3f}")
    print(f"  age MAE    no-change={snap['age_mae_no_change']:.2f}  "
          f"pop-drift={snap['age_mae_pop_drift']:.2f}  "
          f"learned={snap['age_mae_learned']:.2f}  "
          f"(floor={snap['age_mae_floor_actual_z']:.2f})")
    pd.DataFrame([snap]).to_csv(args.output_dir / "single_snapshot.csv", index=False)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
