"""Bundle A: latent-dim interpretability + leave-one-corpus-out generalization."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.evaluation.generalization import aggregate_loco, leave_one_corpus_out
from src.models.phase2_state.interpretability import (
    loadings_table,
    outcome_relevance,
)
from src.models.phase2_state.representation import fit_state


META_COLS = {"transcript_id", "corpus", "child_id", "age_months",
             "n_chi_utterances", "bundle", "window_id", "window_index",
             "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path", default="data/features/phase1_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/bundle_a", type=Path)
    p.add_argument("--latent-d", type=int, default=8)
    p.add_argument("--max-age-months", type=float, default=84.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df = df.dropna(subset=["age_months", "child_id"]).copy()
    df = df[(df.age_months > 0) & (df.age_months <= args.max_age_months)]
    feature_cols = sorted(c for c in df.columns if c not in META_COLS)
    print(f"loaded {len(df)} transcripts, {len(feature_cols)} features, "
          f"{df.corpus.nunique()} corpora")

    # ------------------------------------------------------------------
    # A1: PCA loadings + per-dim outcome relevance.
    # ------------------------------------------------------------------
    print(f"\n[A1] PCA(d={args.latent_d}) loadings + outcome relevance")
    state = fit_state(df, feature_cols, d=args.latent_d)
    Z = state.transform(df)
    y = df["age_months"].to_numpy(dtype=float)
    groups = df["child_id"].to_numpy()

    loadings = loadings_table(state, top_k=5)
    loadings.to_csv(args.output_dir / "loadings.csv", index=False)
    print(loadings.to_string(index=False))

    relevance = outcome_relevance(Z, y, groups)
    relevance.to_csv(args.output_dir / "outcome_relevance.csv", index=False)
    print()
    print(relevance.to_string(index=False, float_format=lambda v: f"{v:+.4f}"))

    # ------------------------------------------------------------------
    # A2: leave-one-corpus-out, raw 55 features vs PCA z=8.
    # ------------------------------------------------------------------
    print(f"\n[A2] Leave-one-corpus-out (held-out corpus must have >=30 transcripts)")
    print("  raw 55 features ...")
    loco_raw = leave_one_corpus_out(df, feature_cols)
    loco_raw.to_csv(args.output_dir / "loco_raw_features.csv", index=False)
    raw_agg = aggregate_loco(loco_raw)

    print("  PCA z=8 ...")
    z_cols = [f"z{i+1}" for i in range(Z.shape[1])]
    z_df = pd.concat([
        df.reset_index(drop=True)[["corpus", "child_id", "age_months"]],
        pd.DataFrame(Z, columns=z_cols),
    ], axis=1)
    loco_z = leave_one_corpus_out(z_df, z_cols)
    loco_z.to_csv(args.output_dir / "loco_pca_z.csv", index=False)
    z_agg = aggregate_loco(loco_z)

    print(f"\n  raw  : MAE corpus-mean = {raw_agg['mae_corpus_mean']:6.2f} mo "
          f"(median {raw_agg['mae_corpus_median']:.2f}, std {raw_agg['mae_corpus_std']:.2f}, "
          f"r̄ = {raw_agg['pearson_r_mean']:+.3f})")
    print(f"  z=8  : MAE corpus-mean = {z_agg['mae_corpus_mean']:6.2f} mo "
          f"(median {z_agg['mae_corpus_median']:.2f}, std {z_agg['mae_corpus_std']:.2f}, "
          f"r̄ = {z_agg['pearson_r_mean']:+.3f})")
    print(f"  evaluated on {raw_agg['n_corpora_evaluated']} corpora")

    print("\n  Worst-generalizing corpora (raw):")
    print(loco_raw.tail(5).to_string(index=False, float_format=lambda v: f"{v:+.2f}"))
    print("\n  Best-generalizing corpora (raw):")
    print(loco_raw.head(5).to_string(index=False, float_format=lambda v: f"{v:+.2f}"))

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
