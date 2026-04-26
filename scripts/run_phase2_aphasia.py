"""Phase 2 main run on AphasiaBank: WAB-AQ regression + subtype classification.

The headline hypothesis test of the project:
  - Does z (latent state) predict WAB-AQ better than the categorical
    aphasia-subtype label alone?
  - Does z preserve subtype-discrimination signal at low d?
  - What is the AQ-vs-subtype information ratio? (i.e. how much severity
    variance is left within each subtype?)

All evaluations use **participant-grouped 5-fold CV** so the same patient
never appears in both train and test (a session-level random split would
leak; same-patient repeats are very correlated).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr


META_COLS = {"transcript_id", "section", "corpus", "participant_id", "age_years",
             "sex", "subtype", "wab_aq", "is_control", "window_id", "window_index",
             "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/phase2_aphasia", type=Path)
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


# ---- WAB-AQ regression -----------------------------------------------------

def cv_regress(X, y, groups, model_factory, n_splits=5):
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(X, y, groups):
        m = model_factory()
        m.fit(X[tr], y[tr])
        preds[te] = m.predict(X[te])
    err = preds - y
    r = float(pearsonr(y, preds)[0]) if np.std(preds) > 0 else float("nan")
    return {"mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(err ** 2))),
            "r": r,
            "preds": preds}


def subtype_baseline(y, subtypes, groups, n_splits=5):
    """Predict mean AQ of held-out patient's subtype, using train-fold subtype-means."""
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(y.reshape(-1, 1), y, groups):
        subtype_mean = pd.Series(y[tr]).groupby(subtypes[tr]).mean()
        global_mean = float(y[tr].mean())
        for i in te:
            preds[i] = subtype_mean.get(subtypes[i], global_mean)
    err = preds - y
    return {"mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(err ** 2))),
            "r": float(pearsonr(y, preds)[0]) if np.std(preds) > 0 else float("nan")}


# ---- Subtype classification -------------------------------------------------

def cv_classify(X, y_str, groups, n_splits=5):
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.empty_like(y_str, dtype=object)
    for tr, te in gkf.split(X, y_str, groups):
        if len(set(y_str[tr])) < 2:
            preds[te] = y_str[tr][0]
            continue
        m = GradientBoostingClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05,
            subsample=0.9, random_state=0,
        ).fit(X[tr], y_str[tr])
        preds[te] = m.predict(X[te])
    return {
        "accuracy": float((preds == y_str).mean()),
        "macro_f1": float(f1_score(y_str, preds, average="macro", zero_division=0)),
        "per_class_f1": {
            c: float(f1_score(y_str == c, preds == c, zero_division=0))
            for c in sorted(set(y_str))
        },
    }


# ---- Main -------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[load] {args.features_path}")
    df = pd.read_parquet(args.features_path)
    feature_cols = sorted(c for c in df.columns if c not in META_COLS)
    print(f"  {len(df)} windows | {df['participant_id'].nunique()} participants "
          f"| {df['corpus'].nunique()} corpora | {len(feature_cols)} features")

    # ----- WAB-AQ regression -----
    print("\n========== WAB-AQ regression ==========")
    aq_df = df.dropna(subset=["wab_aq"]).copy().reset_index(drop=True)
    aq_df = aq_df[aq_df["wab_aq"].between(0, 100)].reset_index(drop=True)
    print(f"  {len(aq_df)} windows from {aq_df['participant_id'].nunique()} participants "
          f"with WAB-AQ ∈ [0, 100]")

    X = aq_df[feature_cols].to_numpy(dtype=float)
    y = aq_df["wab_aq"].to_numpy(dtype=float)
    groups = aq_df["participant_id"].to_numpy()

    print(f"  baseline 1: predict mean (no features) ...")
    mean_baseline_pred = np.full_like(y, y.mean())
    print(f"    MAE={np.mean(np.abs(mean_baseline_pred - y)):.2f}  "
          f"RMSE={np.sqrt(np.mean((mean_baseline_pred - y)**2)):.2f}")

    if aq_df["subtype"].notna().any():
        print(f"  baseline 2: predict mean AQ of held-out patient's subtype ...")
        sub_arr = aq_df["subtype"].fillna("unknown").to_numpy(dtype=object)
        sub_b = subtype_baseline(y, sub_arr, groups, n_splits=args.cv_folds)
        print(f"    MAE={sub_b['mae']:.2f}  RMSE={sub_b['rmse']:.2f}  r={sub_b['r']:+.3f}")

    print(f"  baseline 3: ridge on raw {len(feature_cols)} features ...")
    ridge = cv_regress(X, y, groups,
                       lambda: Pipeline([("sc", StandardScaler()),
                                         ("m", Ridge(alpha=1.0, random_state=0))]),
                       n_splits=args.cv_folds)
    print(f"    MAE={ridge['mae']:.2f}  RMSE={ridge['rmse']:.2f}  r={ridge['r']:+.3f}")

    print(f"  main: GBM on raw {len(feature_cols)} features ...")
    gbm = cv_regress(X, y, groups,
                     lambda: GradientBoostingRegressor(
                         n_estimators=400, max_depth=3, learning_rate=0.05,
                         subsample=0.9, random_state=0),
                     n_splits=args.cv_folds)
    print(f"    MAE={gbm['mae']:.2f}  RMSE={gbm['rmse']:.2f}  r={gbm['r']:+.3f}")

    # PCA z sweep
    print(f"  z-sweep: GBM on PCA z, d ∈ {{3, 5, 8, 12, 20}} ...")
    z_results = []
    Xs = StandardScaler().fit_transform(X)
    for d in [3, 5, 8, 12, 20]:
        pca = PCA(n_components=d, random_state=0).fit(Xs)
        Z = pca.transform(Xs)
        var = float(pca.explained_variance_ratio_.sum())
        m = cv_regress(Z, y, groups,
                       lambda: GradientBoostingRegressor(
                           n_estimators=400, max_depth=3, learning_rate=0.05,
                           subsample=0.9, random_state=0),
                       n_splits=args.cv_folds)
        z_results.append({"d": d, "var": var, "mae": m["mae"],
                          "rmse": m["rmse"], "r": m["r"]})
        print(f"    d={d:>2}  var={var:.3f}  MAE={m['mae']:.2f}  r={m['r']:+.3f}")

    pd.DataFrame(z_results).to_csv(args.output_dir / "wab_aq_z_sweep.csv", index=False)
    pd.DataFrame([
        {"setup": "predict_mean", "mae": float(np.mean(np.abs(mean_baseline_pred-y))),
         "rmse": float(np.sqrt(np.mean((mean_baseline_pred-y)**2))), "r": np.nan},
        {"setup": "subtype_mean_baseline", **(sub_b if 'sub_b' in dir() else {})},
        {"setup": "ridge_raw55", **{k: v for k, v in ridge.items() if k != "preds"}},
        {"setup": "gbm_raw55", **{k: v for k, v in gbm.items() if k != "preds"}},
    ]).to_csv(args.output_dir / "wab_aq_baselines.csv", index=False)

    # ----- Subtype classification -----
    print("\n========== Aphasia subtype classification ==========")
    # Drop classes with too few patients (need >=2 per class for classify CV).
    sub_df = df.dropna(subset=["subtype"]).copy().reset_index(drop=True)
    sub_df = sub_df[~sub_df["subtype"].isin({"control", "U", "unknown"})]
    counts_by_pat = (sub_df.drop_duplicates("participant_id")
                          .groupby("subtype")["participant_id"].count())
    keep = counts_by_pat[counts_by_pat >= 5].index.tolist()
    sub_df = sub_df[sub_df["subtype"].isin(keep)].reset_index(drop=True)
    print(f"  {len(sub_df)} windows from {sub_df['participant_id'].nunique()} patients "
          f"in subtypes: {sorted(keep)}")

    if len(sub_df) > 0 and len(keep) >= 2:
        Xc = sub_df[feature_cols].to_numpy(dtype=float)
        yc = sub_df["subtype"].to_numpy(dtype=object)
        groups_c = sub_df["participant_id"].to_numpy()

        raw = cv_classify(Xc, yc, groups_c, n_splits=args.cv_folds)
        print(f"  raw 55 features  acc={raw['accuracy']:.3f}  "
              f"macroF1={raw['macro_f1']:.3f}")

        Xcs = StandardScaler().fit_transform(Xc)
        for d in [5, 8, 12]:
            Z = PCA(n_components=d, random_state=0).fit_transform(Xcs)
            zres = cv_classify(Z, yc, groups_c, n_splits=args.cv_folds)
            print(f"  z={d}             acc={zres['accuracy']:.3f}  "
                  f"macroF1={zres['macro_f1']:.3f}")

        # Per-class breakdown for raw
        print("\n  per-class F1 (raw):")
        for c, f1 in sorted(raw["per_class_f1"].items()):
            n = int((yc == c).sum())
            print(f"    {c:14s}  n={n:>5}  F1={f1:.3f}")

        pd.DataFrame([{"setup": "raw_55", **{k: v for k, v in raw.items()
                                             if k != "per_class_f1"}}]).to_csv(
            args.output_dir / "subtype_classification.csv", index=False)
        pd.DataFrame([{"subtype": c, "f1": f1, "n": int((yc == c).sum())}
                      for c, f1 in raw["per_class_f1"].items()]).to_csv(
            args.output_dir / "subtype_per_class_f1.csv", index=False)

    # ----- 2D z projection -----
    print("\n========== 2D latent projection ==========")
    if len(aq_df) > 0:
        pca2 = PCA(n_components=2, random_state=0).fit(StandardScaler().fit_transform(X))
        Z2 = pca2.transform(StandardScaler().fit_transform(X))

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        sc = axes[0].scatter(Z2[:, 0], Z2[:, 1], c=y, cmap="RdYlGn", s=12, alpha=0.6)
        plt.colorbar(sc, ax=axes[0], label="WAB-AQ")
        axes[0].set_title(f"Aphasia z₁₂ coloured by WAB-AQ (n={len(y)} windows)")
        axes[0].set_xlabel("z₁"); axes[0].set_ylabel("z₂"); axes[0].grid(alpha=0.3)

        sub_arr = aq_df["subtype"].fillna("unknown").to_numpy(dtype=object)
        for sub in sorted(set(sub_arr)):
            mask = sub_arr == sub
            axes[1].scatter(Z2[mask, 0], Z2[mask, 1], s=10, alpha=0.5, label=f"{sub} ({mask.sum()})")
        axes[1].set_title("z₁₂ coloured by aphasia subtype")
        axes[1].set_xlabel("z₁"); axes[1].set_ylabel("z₂")
        axes[1].legend(loc="best", fontsize=7); axes[1].grid(alpha=0.3)

        fig.tight_layout()
        fig.savefig(args.output_dir / "aphasia_z2_projection.png", dpi=150)
        plt.close(fig)
        print(f"  saved 2D projection plot")

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
