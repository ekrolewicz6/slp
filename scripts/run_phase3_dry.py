"""Phase 3 dry run on CHILDES: per-child trajectory models in latent space.

Reuses the Phase 1 features + Phase 2 PCA state. For each truly longitudinal
child (≥5 sessions, ≥6 months span, mean inter-session gap ≥3 days), holds
out the final session and asks three trajectory models to predict ẑ_T from
the prior sessions.

Reports MAE in z (Euclidean) per model, plus — to make it interpretable —
the implied age error after pushing predicted z back through a Phase-1 GBM
age predictor trained on the same z's.

Run after `run_phase1.py` (for features) and `run_phase2_dry.py` is optional
(this script re-fits the state model itself).
"""

from __future__ import annotations

import argparse
import json
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
from src.models.phase3_trajectory.sequences import build_sequences, summarize_sequences
from src.viz.trajectory_plots import predicted_vs_actual_age, trajectories_in_z


META_COLS = {"transcript_id", "corpus", "child_id", "age_months",
             "n_chi_utterances", "bundle", "window_id", "window_index",
             "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path", default="data/features/phase1_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/phase3_dry", type=Path)
    p.add_argument("--latent-d", type=int, default=8)
    p.add_argument("--max-age-months", type=float, default=84.0)
    p.add_argument("--min-sessions", type=int, default=5)
    p.add_argument("--min-age-span", type=float, default=6.0)
    p.add_argument("--min-mean-gap-days", type=float, default=3.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/5] Loading features ...")
    df = pd.read_parquet(args.features_path)
    df = df.dropna(subset=["age_months", "child_id"]).copy()
    df = df[(df.age_months > 0) & (df.age_months <= args.max_age_months)]
    df = df.reset_index(drop=True)

    feature_cols = sorted(c for c in df.columns if c not in META_COLS)
    print(f"  {len(df)} transcripts | {len(feature_cols)} features | "
          f"{df.child_id.nunique()} children")

    print(f"[2/5] Fitting PCA(d={args.latent_d}) state model on full corpus ...")
    state = fit_state(df, feature_cols, d=args.latent_d)
    Z = state.transform(df)
    print(f"  variance explained: {state.variance_explained:.3f}")

    print(f"[3/5] Building per-child sequences (filters: "
          f"≥{args.min_sessions} sessions, ≥{args.min_age_span} mo span, "
          f"≥{args.min_mean_gap_days} days mean gap) ...")
    sequences = build_sequences(
        df, Z,
        min_sessions=args.min_sessions,
        min_age_span_months=args.min_age_span,
        min_mean_gap_days=args.min_mean_gap_days,
    )
    seq_df = summarize_sequences(sequences)
    seq_df.to_csv(args.output_dir / "sequences.csv", index=False)
    print(f"  kept {len(sequences)} children, {sum(len(s.times) for s in sequences)} "
          f"sessions; corpora: {sorted(set(s.corpus for s in sequences))}")

    if len(sequences) < 5:
        print("[!] Not enough longitudinal children to evaluate. Loosen filters.")
        return

    print(f"[4/5] Training Phase-1-style age predictor on z (for interpretability) ...")
    y = df["age_months"].to_numpy(dtype=float)
    age_model = GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0,
    ).fit(Z, y)
    in_sample_age_mae = float(np.mean(np.abs(age_model.predict(Z) - y)))
    print(f"  in-sample age MAE from z: {in_sample_age_mae:.2f} months "
          f"(reference; not an out-of-sample claim)")

    print(f"[5/5] Leave-last-out evaluation ...")
    models = [MeanBaseline(), LinearExtrapolation(), GPTrajectory()]
    summaries = []
    for m in models:
        s = evaluate_leave_last_out(m, sequences, age_predictor=age_model.predict)
        summaries.append({k: v for k, v in s.items() if k != "rows"})
        # Per-model rows to disk for downstream inspection.
        pd.DataFrame(s["rows"]).to_csv(
            args.output_dir / f"per_child_predictions_{m.name}.csv", index=False)
        print(f"  {m.name:7s}  z-L2 MAE={s['mean_z_l2_error']:6.3f}  "
              f"med={s['median_z_l2_error']:6.3f}  "
              f"age-MAE(pred z)={s.get('age_mae_from_predicted_z', float('nan')):5.2f}  "
              f"age-MAE(actual z)={s.get('age_mae_from_actual_z', float('nan')):5.2f}")

        if m.name == "gp":
            predicted_vs_actual_age(
                s["rows"],
                args.output_dir / "predicted_vs_actual_age_gp.png",
                "Held-out session: age inferred from GP-predicted z vs actual age",
            )

    pd.DataFrame(summaries).to_json(args.output_dir / "metrics.json",
                                    orient="records", indent=2)
    trajectories_in_z(
        sequences,
        args.output_dir / "trajectories_z1.png",
        f"z₁ trajectories for top-12 longitudinal children (PCA d={args.latent_d})",
    )
    print(f"Done. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
