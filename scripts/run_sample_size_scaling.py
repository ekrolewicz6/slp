"""Sample-size scaling curves for the Phase 2 WAB-AQ regression.

Sub-sample patients at n ∈ {50, 100, 200, 400, 800} (capped by available
data). Re-run the headline regression. Plot accuracy vs n. Two purposes:

  1. Show whether we're data-limited or model-limited.
  2. Quantify how much extra signal RELEASE-scale data (~5,900 patients)
     would buy us — concrete evidence in the application.

Repeats each n with k=5 random sub-sample seeds for noise estimates.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler


META = {"transcript_id", "section", "corpus", "participant_id",
        "patient_root", "session_letter", "age_years", "sex", "subtype",
        "wab_aq", "is_control", "session_date", "window_id",
        "window_index", "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--embeddings-path",
                   default="data/features/aphasia_window_embeddings.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/sample_size_scaling",
                   type=Path)
    p.add_argument("--cv-folds", type=int, default=5)
    p.add_argument("--n-seeds", type=int, default=5)
    p.add_argument("--use-embeddings", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    feats = pd.read_parquet(args.features_path)
    feature_cols = sorted(c for c in feats.columns if c not in META)

    if args.use_embeddings and args.embeddings_path.exists():
        embs = pd.read_parquet(args.embeddings_path)
        df = feats.merge(embs, on="window_id", how="inner")
        emb_cols_full = sorted(c for c in embs.columns if c.startswith("emb"))
        # Reduce to 64-d PCA for efficiency
        em_arr = StandardScaler().fit_transform(
            df[emb_cols_full].to_numpy(dtype=float))
        em_red = PCA(n_components=64, random_state=0).fit_transform(em_arr)
        for j in range(64):
            df[f"epca_{j:03d}"] = em_red[:, j]
        emb_cols = [f"epca_{j:03d}" for j in range(64)]
    else:
        df = feats
        emb_cols = []

    pat = df.dropna(subset=["wab_aq"]).copy()
    pat = pat.groupby("participant_id").agg(
        {**{c: "mean" for c in feature_cols + emb_cols},
         **{m: "first" for m in
            ["corpus", "subtype", "wab_aq", "is_control"]}}
    ).reset_index()
    pat = pat[pat["wab_aq"].between(0, 100)].reset_index(drop=True)
    pat["sub_filled"] = pat["subtype"].fillna("Unknown")
    print(f"baseline: {len(pat)} patients with WAB-AQ "
          f"({pat['corpus'].nunique()} corpora)")

    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit(
        pat["sub_filled"].to_numpy(dtype=object).reshape(-1, 1))
    Sub_full = enc.transform(pat["sub_filled"].to_numpy(dtype=object).reshape(-1, 1))
    X_full = pat[feature_cols + emb_cols].to_numpy(dtype=float)
    y_full = pat["wab_aq"].to_numpy(dtype=float)
    g_full = pat["corpus"].to_numpy()

    sample_sizes = [50, 100, 200, 400, 800]
    sample_sizes = [n for n in sample_sizes if n <= len(pat)]
    if sample_sizes[-1] != len(pat):
        sample_sizes.append(len(pat))

    rows = []
    for n in sample_sizes:
        for seed in range(args.n_seeds):
            rng = np.random.default_rng(seed * 1000 + n)
            idx = rng.choice(len(pat), size=n, replace=False)
            X = np.concatenate([Sub_full[idx], X_full[idx]], axis=1)
            y = y_full[idx]
            g = g_full[idx]
            ng = len(set(g))
            splits = max(2, min(args.cv_folds, ng))
            gkf = GroupKFold(n_splits=splits)
            preds = np.zeros_like(y, dtype=float)
            for tr, te in gkf.split(X, y, g):
                m = GradientBoostingRegressor(
                    n_estimators=400, max_depth=3, learning_rate=0.05,
                    subsample=0.9, random_state=0).fit(X[tr], y[tr])
                preds[te] = m.predict(X[te])
            mae = float(np.mean(np.abs(preds - y)))
            rows.append({"n": n, "seed": seed, "mae": mae,
                         "n_corpora": ng})
        sub = [r for r in rows if r["n"] == n]
        print(f"  n={n:>4}  MAE={np.mean([r['mae'] for r in sub]):6.2f}  "
              f"std±{np.std([r['mae'] for r in sub]):.2f}  "
              f"({args.n_seeds} seeds)")

    out = pd.DataFrame(rows)
    out.to_csv(args.output_dir / "scaling_curve.csv", index=False)

    # Plot
    fig, ax = plt.subplots(figsize=(7, 5))
    means = out.groupby("n")["mae"].mean()
    sds = out.groupby("n")["mae"].std()
    ax.errorbar(means.index, means.values, yerr=sds.values, fmt="o-",
                capsize=4)
    ax.set_xlabel("Number of patients (n)")
    ax.set_ylabel("WAB-AQ MAE (subtype + features + embeddings)")
    ax.set_title(f"Phase 2 scaling — error vs sample size "
                 f"({'+ embeddings' if args.use_embeddings else 'features only'})")
    ax.set_xscale("log")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(args.output_dir / "scaling_curve.png", dpi=150)
    plt.close(fig)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
