"""Phase 2 refined run: the actual headline test.

The first run produced a counter-intuitive result: predict-subtype-mean
got MAE 6.85 on WAB-AQ, while feature-based GBM got 23.40 MAE. That
*looks* like categorical labels destroy the features — but it's
partially circular, because WAB subtype is *defined from* WAB subtest
scores, which in turn determine WAB-AQ. The real hypothesis test is:

    Conditional on the subtype label, can our features predict the
    residual AQ variation that subtype alone can't?

If yes → continuous z is informationally additive over the diagnostic
category. If no → the categorical label is a complete summary and z
adds nothing.

We also fix two issues with the first run:
  - aggregate windows to patient-level (one prediction per participant);
  - separately analyse PWA-only (subtype != Control / NotAphasic).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.stats import pearsonr


META_COLS = {"transcript_id", "section", "corpus", "participant_id", "age_years",
             "sex", "subtype", "wab_aq", "is_control", "window_id", "window_index",
             "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/phase2_aphasia_refined", type=Path)
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


def aggregate_to_patient(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """One row per patient: mean of feature values across their windows."""
    keep_meta = ["participant_id", "corpus", "subtype", "wab_aq", "is_control"]
    agg = df.groupby("participant_id").agg(
        {**{f: "mean" for f in feature_cols},
         **{m: "first" for m in keep_meta if m != "participant_id"}}
    ).reset_index()
    return agg


def cv_regress(X, y, groups, n_splits, model_factory):
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(X, y, groups):
        m = model_factory()
        m.fit(X[tr], y[tr])
        preds[te] = m.predict(X[te])
    err = preds - y
    return {
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "r": float(pearsonr(y, preds)[0]) if np.std(preds) > 0 else float("nan"),
        "preds": preds,
    }


def subtype_mean_baseline(y, subtypes, groups, n_splits):
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(y.reshape(-1, 1), y, groups):
        means = pd.Series(y[tr]).groupby(subtypes[tr]).mean()
        global_mean = float(y[tr].mean())
        for i in te:
            preds[i] = means.get(subtypes[i], global_mean)
    err = preds - y
    return {
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "r": float(pearsonr(y, preds)[0]) if np.std(preds) > 0 else float("nan"),
        "preds": preds,
    }


def featurize_with_subtype(X_feat, subtypes):
    """Concatenate one-hot subtype + raw features. Used for the additive test."""
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    S = enc.fit_transform(subtypes.reshape(-1, 1))
    return np.concatenate([S, X_feat], axis=1)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    feature_cols = sorted(c for c in df.columns if c not in META_COLS)
    print(f"loaded {len(df)} windows, {len(feature_cols)} features")

    # ------------------------------------------------------------------
    # Patient-level aggregation
    # ------------------------------------------------------------------
    pat = aggregate_to_patient(df, feature_cols)
    pat = pat.dropna(subset=["wab_aq"]).reset_index(drop=True)
    pat = pat[(pat.wab_aq >= 0) & (pat.wab_aq <= 100)].reset_index(drop=True)
    pat["subtype_filled"] = pat["subtype"].fillna("Unknown")
    print(f"patient-level: {len(pat)} patients with WAB-AQ")

    groups = pat["corpus"].to_numpy()  # corpus-grouped CV avoids site-leakage
    y = pat["wab_aq"].to_numpy(dtype=float)
    X = pat[feature_cols].to_numpy(dtype=float)
    sub_arr = pat["subtype_filled"].to_numpy(dtype=object)

    rows = []

    # 1. Baselines.
    print("\n--- baselines (patient-level, corpus-grouped CV) ---")
    mp = float(y.mean())
    bl = {"setup": "predict_mean", "mae": float(np.mean(np.abs(y - mp))),
          "rmse": float(np.sqrt(np.mean((y - mp) ** 2))), "r": float("nan")}
    rows.append(bl)
    print(f"  predict_mean             MAE={bl['mae']:6.2f}  RMSE={bl['rmse']:6.2f}")

    # 2. Subtype-mean baseline.
    sub_b = subtype_mean_baseline(y, sub_arr, groups, args.cv_folds)
    rows.append({"setup": "subtype_mean_only",
                 **{k: v for k, v in sub_b.items() if k != "preds"}})
    print(f"  subtype_mean_only        MAE={sub_b['mae']:6.2f}  "
          f"RMSE={sub_b['rmse']:6.2f}  r={sub_b['r']:+.3f}")

    # 3. Features only (raw, GBM).
    feat_b = cv_regress(X, y, groups, args.cv_folds,
                        lambda: GradientBoostingRegressor(
                            n_estimators=400, max_depth=3, learning_rate=0.05,
                            subsample=0.9, random_state=0))
    rows.append({"setup": "features_only_gbm",
                 **{k: v for k, v in feat_b.items() if k != "preds"}})
    print(f"  features_only_gbm        MAE={feat_b['mae']:6.2f}  "
          f"RMSE={feat_b['rmse']:6.2f}  r={feat_b['r']:+.3f}")

    # 4. Subtype + features. The headline test: does z add signal on top?
    Xs_subtype_feats = featurize_with_subtype(X, sub_arr)
    add_b = cv_regress(Xs_subtype_feats, y, groups, args.cv_folds,
                       lambda: GradientBoostingRegressor(
                           n_estimators=400, max_depth=3, learning_rate=0.05,
                           subsample=0.9, random_state=0))
    rows.append({"setup": "subtype_plus_features_gbm",
                 **{k: v for k, v in add_b.items() if k != "preds"}})
    print(f"  subtype_plus_features    MAE={add_b['mae']:6.2f}  "
          f"RMSE={add_b['rmse']:6.2f}  r={add_b['r']:+.3f}")
    print(f"    Δ from subtype_only    {sub_b['mae'] - add_b['mae']:+.2f} mae  "
          f"({sub_b['r']:+.3f} → {add_b['r']:+.3f} r)")

    # 5. PCA z + subtype.
    Xs_scaled = StandardScaler().fit_transform(X)
    Z8 = PCA(n_components=8, random_state=0).fit_transform(Xs_scaled)
    z_only = cv_regress(Z8, y, groups, args.cv_folds,
                        lambda: GradientBoostingRegressor(
                            n_estimators=400, max_depth=3, learning_rate=0.05,
                            subsample=0.9, random_state=0))
    rows.append({"setup": "z8_only_gbm",
                 **{k: v for k, v in z_only.items() if k != "preds"}})
    print(f"  z8_only_gbm              MAE={z_only['mae']:6.2f}  "
          f"r={z_only['r']:+.3f}")

    add_z = cv_regress(featurize_with_subtype(Z8, sub_arr), y, groups,
                       args.cv_folds,
                       lambda: GradientBoostingRegressor(
                           n_estimators=400, max_depth=3, learning_rate=0.05,
                           subsample=0.9, random_state=0))
    rows.append({"setup": "subtype_plus_z8_gbm",
                 **{k: v for k, v in add_z.items() if k != "preds"}})
    print(f"  subtype_plus_z8_gbm      MAE={add_z['mae']:6.2f}  r={add_z['r']:+.3f}")

    # 6. PWA-only restriction: drop Control + NotAphasic.
    print("\n--- PWA-only (drop Control + NotAphasic) ---")
    pwa = pat[~pat["subtype_filled"].isin({"Control", "NotAphasic", "Unknown"})].reset_index(drop=True)
    print(f"  {len(pwa)} PWA patients in subtypes: "
          f"{sorted(set(pwa['subtype_filled']))}")
    if len(pwa) > 30:
        Xp = pwa[feature_cols].to_numpy(dtype=float)
        yp = pwa["wab_aq"].to_numpy(dtype=float)
        gp = pwa["corpus"].to_numpy()
        sp = pwa["subtype_filled"].to_numpy(dtype=object)

        for label, model_fn, X_in in [
            ("predict_mean_pwa", None, None),
            ("subtype_mean_pwa", subtype_mean_baseline, None),
            ("features_only_gbm_pwa",
             lambda: GradientBoostingRegressor(
                 n_estimators=400, max_depth=3, learning_rate=0.05,
                 subsample=0.9, random_state=0), Xp),
            ("subtype_plus_features_pwa",
             lambda: GradientBoostingRegressor(
                 n_estimators=400, max_depth=3, learning_rate=0.05,
                 subsample=0.9, random_state=0),
             featurize_with_subtype(Xp, sp)),
        ]:
            if label == "predict_mean_pwa":
                m = float(yp.mean())
                r = {"mae": float(np.mean(np.abs(yp - m))),
                     "rmse": float(np.sqrt(np.mean((yp - m)**2))), "r": float("nan")}
            elif label == "subtype_mean_pwa":
                r = subtype_mean_baseline(yp, sp, gp, args.cv_folds)
                r = {k: v for k, v in r.items() if k != "preds"}
            else:
                r = cv_regress(X_in, yp, gp, args.cv_folds, model_fn)
                r = {k: v for k, v in r.items() if k != "preds"}
            rows.append({"setup": label, **r})
            print(f"  {label:30s}  MAE={r['mae']:6.2f}  r={r.get('r', 0):+.3f}")

    pd.DataFrame(rows).to_csv(args.output_dir / "patient_level_metrics.csv",
                              index=False)

    # ------------------------------------------------------------------
    # Per-patient prediction scatter for the additive setup.
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    ax = axes[0]
    ax.scatter(y, sub_b["preds"], s=18, alpha=0.5, label="subtype-only baseline")
    ax.plot([0, 100], [0, 100], "k--", lw=1)
    ax.set_xlabel("True WAB-AQ"); ax.set_ylabel("Predicted")
    ax.set_title(f"Subtype-mean baseline (MAE={sub_b['mae']:.2f}, r={sub_b['r']:+.3f})")
    ax.grid(alpha=0.3); ax.set_xlim(0, 105); ax.set_ylim(0, 105)

    ax = axes[1]
    ax.scatter(y, feat_b["preds"], s=18, alpha=0.5, c="C3",
               label="GBM on features only")
    ax.scatter(y, add_b["preds"], s=18, alpha=0.5, c="C2",
               label="GBM on subtype + features")
    ax.plot([0, 100], [0, 100], "k--", lw=1)
    ax.set_xlabel("True WAB-AQ"); ax.set_ylabel("Predicted")
    ax.set_title(f"Features-only (MAE={feat_b['mae']:.2f}, r={feat_b['r']:+.3f}) vs "
                 f"subtype+features (MAE={add_b['mae']:.2f}, r={add_b['r']:+.3f})")
    ax.legend(); ax.grid(alpha=0.3); ax.set_xlim(0, 105); ax.set_ylim(0, 105)

    fig.tight_layout()
    fig.savefig(args.output_dir / "subtype_vs_features_pred.png", dpi=150)
    plt.close(fig)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
