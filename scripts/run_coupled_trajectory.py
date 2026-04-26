"""Coupled multi-output trajectory model — fix for the D1 null result.

In #9 the per-dim trajectory + reweighting trick was a no-op because
each latent dim was modeled independently and was therefore scale-
invariant. The fix is a coupled model where dims share information
during fitting. Here we use a multi-output GBM (predict z_t2 vector
from z_t1 vector + Δt) with the gradient-boosted regression chain
trick: predict z₁_t2 first, then use that prediction as a feature for
predicting z₂_t2, and so on. This couples the dimensions during
training without requiring a special vector-valued kernel.

We also test the simplest alternative: a single GBM per output dim that
uses ALL prior z dims as features (rather than just z_d_t1 alone).
This was the natural per-dim-with-cross-talk baseline that should
have been done before the weighting trick.

Comparison vs:
  - no-change baseline (z_t2 = z_t1, per dim)
  - independent per-dim GBM (z_t2_d ~ z_t1_d + Δt)
  - all-dims-as-features per-dim GBM (z_t2_d ~ z_t1[1..d] + Δt)
  - chained GBM (z_t2_d ~ z_t1[1..d] + ẑ_t2[1..d-1] + Δt)
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler


META = {"transcript_id", "section", "corpus", "participant_id",
        "patient_root", "session_letter", "age_years", "sex", "subtype",
        "wab_aq", "is_control", "session_date", "window_id", "window_index",
        "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/coupled_trajectory",
                   type=Path)
    p.add_argument("--latent-d", type=int, default=8)
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


def aggregate_session(df, feature_cols):
    keep = ["patient_root", "session_letter", "session_date", "subtype",
            "wab_aq", "corpus", "participant_id"]
    return df.groupby("participant_id").agg(
        {**{f: "mean" for f in feature_cols},
         **{m: "first" for m in keep if m != "participant_id"}}
    ).reset_index()


def gbm():
    return GradientBoostingRegressor(
        n_estimators=300, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df["patient_root"] = df["participant_id"].str.replace(r"[a-zA-Z]$", "",
                                                          regex=True)
    df["session_letter"] = df["participant_id"].str.extract(r"([a-zA-Z])$")[0]
    feature_cols = sorted(c for c in df.columns if c not in META)

    sess = aggregate_session(df, feature_cols)
    Xs = StandardScaler().fit_transform(sess[feature_cols].to_numpy(dtype=float))
    Z = PCA(n_components=args.latent_d, random_state=0).fit_transform(Xs)
    for j in range(args.latent_d):
        sess[f"z{j+1}"] = Z[:, j]

    # Build (z_t1, z_t2) ordered pairs per patient
    pairs = []
    for pat, g in sess.groupby("patient_root"):
        g = g.sort_values("session_letter").reset_index(drop=True)
        if len(g) < 2:
            continue
        for i in range(len(g) - 1):
            r1, r2 = g.iloc[i], g.iloc[i + 1]
            d1, d2 = r1.get("session_date"), r2.get("session_date")
            try:
                dt = (datetime.fromisoformat(d2) -
                      datetime.fromisoformat(d1)).days
            except (TypeError, ValueError):
                dt = None
            row = {"patient_root": pat, "delta_t_days": dt}
            for j in range(args.latent_d):
                row[f"z{j+1}_t1"] = r1[f"z{j+1}"]
                row[f"z{j+1}_t2"] = r2[f"z{j+1}"]
            pairs.append(row)
    pdf = pd.DataFrame(pairs)
    pdf["delta_t_filled"] = pdf["delta_t_days"].fillna(
        pdf["delta_t_days"].median())
    print(f"trajectory pairs: {len(pdf)}")

    z_t1 = pdf[[f"z{j+1}_t1" for j in range(args.latent_d)]].to_numpy(dtype=float)
    z_t2 = pdf[[f"z{j+1}_t2" for j in range(args.latent_d)]].to_numpy(dtype=float)
    dt = pdf["delta_t_filled"].to_numpy(dtype=float).reshape(-1, 1)
    groups = pdf["patient_root"].to_numpy()

    n_g = len(set(groups))
    splits = max(2, min(args.cv_folds, n_g))
    gkf = GroupKFold(n_splits=splits)

    # Helper for CV per-dim MAE
    def cv_per_dim(predict_fn) -> np.ndarray:
        """predict_fn(X_train, y_train, X_test) → y_pred for one dim."""
        per_dim_mae = np.zeros(args.latent_d)
        for j in range(args.latent_d):
            preds = np.zeros(len(z_t2))
            for tr, te in gkf.split(z_t1, z_t2[:, j], groups):
                # X depends on the strategy — see the closures below
                yhat = predict_fn(j, tr, te)
                preds[te] = yhat
            per_dim_mae[j] = float(np.mean(np.abs(preds - z_t2[:, j])))
        return per_dim_mae

    # ----- Strategy 1: no-change -----
    no_change_mae = np.array([
        float(np.mean(np.abs(z_t1[:, j] - z_t2[:, j])))
        for j in range(args.latent_d)
    ])

    # ----- Strategy 2: independent per-dim (one feature: z_d_t1 + Δt) -----
    def indep(j, tr, te):
        X = np.concatenate([z_t1[:, [j]], dt], axis=1)
        m = gbm().fit(X[tr], z_t2[tr, j])
        return m.predict(X[te])
    indep_mae = cv_per_dim(indep)

    # ----- Strategy 3: all-dims-as-features per-dim -----
    def all_dims(j, tr, te):
        X = np.concatenate([z_t1, dt], axis=1)
        m = gbm().fit(X[tr], z_t2[tr, j])
        return m.predict(X[te])
    all_dims_mae = cv_per_dim(all_dims)

    # ----- Strategy 4: chained GBM (use earlier dims' predictions) -----
    def chained_predict() -> np.ndarray:
        per_dim_mae = np.zeros(args.latent_d)
        chain_preds_full = np.zeros_like(z_t2)
        for tr, te in gkf.split(z_t1, z_t2[:, 0], groups):
            for j in range(args.latent_d):
                base = np.concatenate([z_t1, dt,
                                        chain_preds_full[:, :j]], axis=1)
                m = gbm().fit(base[tr], z_t2[tr, j])
                chain_preds_full[te, j] = m.predict(base[te])
        for j in range(args.latent_d):
            per_dim_mae[j] = float(np.mean(np.abs(chain_preds_full[:, j]
                                                   - z_t2[:, j])))
        return per_dim_mae
    chained_mae = chained_predict()

    rows = []
    print(f"\n{'dim':>4} | {'no_change':>10} | {'indep':>9} | {'all_dims':>9} | {'chained':>9}")
    for j in range(args.latent_d):
        print(f"  z{j+1}  |   {no_change_mae[j]:.3f}    |  {indep_mae[j]:.3f}   |  "
              f"{all_dims_mae[j]:.3f}   |  {chained_mae[j]:.3f}")
        rows.append({
            "dim": f"z{j+1}",
            "no_change_mae": float(no_change_mae[j]),
            "indep_mae": float(indep_mae[j]),
            "all_dims_mae": float(all_dims_mae[j]),
            "chained_mae": float(chained_mae[j]),
            "best_strategy": ["no_change", "indep", "all_dims", "chained"][
                int(np.argmin([no_change_mae[j], indep_mae[j],
                                all_dims_mae[j], chained_mae[j]]))
            ],
        })

    out = pd.DataFrame(rows)
    out.to_csv(args.output_dir / "coupled_trajectory.csv", index=False)

    print(f"\nMean MAE across all dims:")
    print(f"  no_change:  {no_change_mae.mean():.3f}")
    print(f"  indep:      {indep_mae.mean():.3f}")
    print(f"  all_dims:   {all_dims_mae.mean():.3f}")
    print(f"  chained:    {chained_mae.mean():.3f}")

    # Strategy summary
    counts = out["best_strategy"].value_counts()
    print(f"\nBest-strategy frequency across {args.latent_d} dims:")
    for s in ["no_change", "indep", "all_dims", "chained"]:
        c = counts.get(s, 0)
        print(f"  {s:10s}: {c}/{args.latent_d}")

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
