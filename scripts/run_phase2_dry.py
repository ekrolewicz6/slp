"""Phase 2 dry run on CHILDES.

Reads `data/features/phase1_features.parquet`, fits PCA latent states z at
several dimensionalities, and asks:

  - How much age-prediction signal does z preserve vs the raw 55 features?
  - Where does the signal saturate (the d that "earns its complexity")?
  - Is the 2D projection developmentally meaningful (smooth age gradient)?
  - Do data-driven KMeans stages line up with developmental order?

Run after `run_phase1.py` has produced features:

    .venv/bin/python -m scripts.run_phase2_dry
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.models.phase2_state.representation import (
    cluster_stage_purity,
    evaluate_age_from_state,
    fit_state,
)
from src.viz.state_plots import dim_sweep, projection_2d, scree


META_COLS = {"transcript_id", "corpus", "child_id", "age_months",
             "n_chi_utterances", "bundle", "window_id", "window_index",
             "n_chi_utts_in_window"}
DIMS = [2, 3, 5, 8, 12, 20]
CLUSTER_KS = [3, 4, 5, 6]
RAW_GBM_BASELINE_MAE = 8.98  # from Phase 1 run on Eng-NA / 4191 transcripts
MLU_BASELINE_MAE = 12.00


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path", default="data/features/phase1_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/phase2_dry", type=Path)
    p.add_argument("--max-age-months", type=float, default=84.0)
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] Loading {args.features_path} ...")
    df = pd.read_parquet(args.features_path)
    df = df.dropna(subset=["age_months", "child_id"]).copy()
    df = df[(df["age_months"] > 0) & (df["age_months"] <= args.max_age_months)]
    print(f"  {len(df)} transcripts; {df['child_id'].nunique()} unique children; "
          f"{df['corpus'].nunique()} corpora.")

    feature_cols = sorted(c for c in df.columns if c not in META_COLS)
    print(f"  {len(feature_cols)} input features.")

    y = df["age_months"].to_numpy(dtype=float)
    groups = df["child_id"].to_numpy()

    # Fit a single full-d state model so we can read the variance spectrum.
    print("[2/4] Fitting full PCA spectrum ...")
    full_state = fit_state(df, feature_cols, d=min(len(feature_cols), 30))
    var_ratios = full_state.pca.explained_variance_ratio_
    scree(var_ratios, args.output_dir / "scree.png",
          f"PCA scree ({len(feature_cols)} input features)")

    # Sweep d.
    print(f"[3/4] Sweeping d ∈ {DIMS} (child-grouped {args.cv_folds}-fold CV) ...")
    sweep_rows = []
    states: dict[int, np.ndarray] = {}
    for d in DIMS:
        st = fit_state(df, feature_cols, d=d)
        Z = st.transform(df)
        m = evaluate_age_from_state(Z, y, groups, n_splits=args.cv_folds)
        sweep_rows.append({"d": d, "var_explained": st.variance_explained, **m})
        states[d] = Z
        print(f"  d={d:>2}  var={st.variance_explained:.3f}  "
              f"MAE={m['mae_months']:6.2f}  r={m['pearson_r']:+.3f}")

    sweep_df = pd.DataFrame(sweep_rows)
    sweep_df.to_csv(args.output_dir / "dim_sweep.csv", index=False)
    dim_sweep(sweep_df, RAW_GBM_BASELINE_MAE,
              args.output_dir / "dim_sweep.png",
              f"Age MAE from PCA z (vs raw GBM={RAW_GBM_BASELINE_MAE:.2f}, "
              f"MLU={MLU_BASELINE_MAE:.2f})")

    # 2D projection from the d=2 fit (faithful 2D, not a slice of d=20).
    Z2 = states[2]
    projection_2d(Z2, y, args.output_dir / "projection_2d.png",
                  "Latent state (PCA d=2) coloured by age")

    # Cluster stages on the d=8 representation (compromise between expressiveness
    # and clusterability — high-d KMeans is hostile).
    print(f"[4/4] Cluster-stage purity on d=8 representation ...")
    Z8 = states[8]
    purity_rows = []
    for k in CLUSTER_KS:
        p = cluster_stage_purity(Z8, y, k=k)
        purity_rows.append({"k": k, "silhouette": p["silhouette"],
                            "stage_age_spearman": p["stage_age_spearman"],
                            "cluster_mean_ages": p["cluster_mean_ages"],
                            "cluster_sizes": p["cluster_sizes"]})
        print(f"  k={k}  silhouette={p['silhouette']:+.3f}  "
              f"stage-age Spearman={p['stage_age_spearman']:+.3f}  "
              f"mean ages={[round(a, 1) for a in p['cluster_mean_ages']]}")
    pd.DataFrame(purity_rows).to_csv(args.output_dir / "cluster_purity.csv",
                                     index=False)

    print(f"Done. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
