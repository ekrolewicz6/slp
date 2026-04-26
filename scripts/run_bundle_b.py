"""Bundle B: nonlinear autoencoder vs PCA vs raw GBM.

For d ∈ {3, 5, 8, 12, 20}, fit:
  - PCA(d)        — linear baseline (already known floor: ~10.15 MAE at d=20)
  - Autoencoder(d) — small MLP, early-stopped on held-out reconstruction

Then evaluate each by training a Phase-1-style GBM on z and reporting
child-grouped CV age-MAE. Compare against the raw 55-feature GBM (8.98).

If the AE recovers raw-GBM performance at modest d, that justifies replacing
PCA with AE in the real Phase 2 on aphasia.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.models.phase2_state.autoencoder import fit_autoencoder
from src.models.phase2_state.representation import (
    evaluate_age_from_state,
    fit_state,
)


META_COLS = {"transcript_id", "corpus", "child_id", "age_months", "n_chi_utterances"}
DIMS = [3, 5, 8, 12, 20]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path", default="data/features/phase1_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/bundle_b", type=Path)
    p.add_argument("--max-age-months", type=float, default=84.0)
    p.add_argument("--cv-folds", type=int, default=5)
    p.add_argument("--ae-epochs", type=int, default=400)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df = df.dropna(subset=["age_months", "child_id"]).copy()
    df = df[(df.age_months > 0) & (df.age_months <= args.max_age_months)]
    feature_cols = sorted(c for c in df.columns if c not in META_COLS)
    y = df["age_months"].to_numpy(dtype=float)
    groups = df["child_id"].to_numpy()
    print(f"loaded {len(df)} transcripts | {len(feature_cols)} features | "
          f"{df.child_id.nunique()} children")

    rows = []
    for d in DIMS:
        print(f"\n=== d = {d} ===")
        # PCA reference.
        pca_state = fit_state(df, feature_cols, d=d)
        Z_pca = pca_state.transform(df)
        m_pca = evaluate_age_from_state(Z_pca, y, groups, n_splits=args.cv_folds)
        print(f"  PCA   var={pca_state.variance_explained:.3f}  "
              f"MAE={m_pca['mae_months']:6.2f}  r={m_pca['pearson_r']:+.3f}")

        # Autoencoder.
        ae_state = fit_autoencoder(df, feature_cols, d=d, epochs=args.ae_epochs)
        Z_ae = ae_state.transform(df)
        m_ae = evaluate_age_from_state(Z_ae, y, groups, n_splits=args.cv_folds)
        print(f"  AE    val_recon_mse={ae_state.val_loss:.4f}  "
              f"MAE={m_ae['mae_months']:6.2f}  r={m_ae['pearson_r']:+.3f}  "
              f"(epochs={ae_state.n_epochs})")

        rows.append({
            "d": d,
            "pca_var_explained": pca_state.variance_explained,
            "pca_mae_months": m_pca["mae_months"],
            "pca_pearson_r": m_pca["pearson_r"],
            "ae_val_recon_mse": ae_state.val_loss,
            "ae_mae_months": m_ae["mae_months"],
            "ae_pearson_r": m_ae["pearson_r"],
            "ae_minus_pca_mae": m_ae["mae_months"] - m_pca["mae_months"],
        })

    out = pd.DataFrame(rows)
    out.to_csv(args.output_dir / "ae_vs_pca.csv", index=False)
    print("\nSummary (negative `ae_minus_pca_mae` = AE wins):")
    print(out.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))

    print(f"\nReference baselines:")
    print(f"  raw GBM(55 features) MAE  = 8.98 mo")
    print(f"  MLU-only Ridge MAE        = 12.00 mo")
    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
