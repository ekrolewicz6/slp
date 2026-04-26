"""NMF factorization of AphasiaBank features for clinical interpretability.

PCA produces orthogonal components that may not correspond to
recognizable clinical primitives (z₁ "syntactic richness" was lucky
to interpret, z₆/z₇ etc are abstract). Non-negative matrix
factorization (NMF) finds parts-based decompositions: each component
is a positive linear combination of features, often aligning more
naturally with what a clinician would call a primitive (e.g.
"productivity," "complexity," "fluency").

We compare PCA and NMF at d=8:
  1. WAB-AQ regression: which compresses better?
  2. Subtype classification: which preserves diagnostic signal?
  3. Loadings: which produces more clinically meaningful axes?
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import NMF, PCA
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler
from scipy.stats import pearsonr


META = {"transcript_id", "section", "corpus", "participant_id",
        "patient_root", "session_letter", "age_years", "sex", "subtype",
        "wab_aq", "is_control", "session_date", "window_id", "window_index",
        "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/nmf", type=Path)
    p.add_argument("--d", type=int, default=8)
    return p.parse_args()


def cv_regress(X, y, groups, factory, n_splits=5):
    n_g = len(set(groups))
    gkf = GroupKFold(n_splits=max(2, min(n_splits, n_g)))
    preds = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(X, y, groups):
        m = factory()
        m.fit(X[tr], y[tr])
        preds[te] = m.predict(X[te])
    err = preds - y
    return {"mae": float(np.mean(np.abs(err))),
            "r": float(pearsonr(y, preds)[0]) if np.std(preds) > 0
                 else float("nan")}


def cv_classify(X, y, groups, n_splits=5):
    n_g = len(set(groups))
    gkf = GroupKFold(n_splits=max(2, min(n_splits, n_g)))
    preds = np.empty_like(y, dtype=object)
    for tr, te in gkf.split(X, y, groups):
        if len(set(y[tr])) < 2:
            preds[te] = y[tr][0]; continue
        clf = GradientBoostingClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05,
            subsample=0.9, random_state=0).fit(X[tr], y[tr])
        preds[te] = clf.predict(X[te])
    return {"accuracy": float((preds == y).mean()),
            "macro_f1": float(f1_score(y, preds, average="macro",
                                        zero_division=0))}


def gbm_factory():
    return GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    feature_cols = sorted(c for c in df.columns if c not in META)
    X = df[feature_cols].to_numpy(dtype=float)
    print(f"loaded {len(df)} windows, {len(feature_cols)} features")

    # Aggregate to patient-level for AQ regression / subtype classification.
    pat = df.groupby("participant_id").agg(
        {**{c: "mean" for c in feature_cols},
         **{m: "first" for m in ["wab_aq", "subtype", "corpus"]}}
    ).reset_index()
    pat = pat.dropna(subset=["wab_aq"]).reset_index(drop=True)
    pat = pat[(pat.wab_aq >= 0) & (pat.wab_aq <= 100)].reset_index(drop=True)
    print(f"patient-level rows: {len(pat)}")

    Xp = pat[feature_cols].to_numpy(dtype=float)
    y_aq = pat["wab_aq"].to_numpy(dtype=float)
    groups = pat["corpus"].to_numpy()

    # PCA (z-scored).
    Xp_s = StandardScaler().fit_transform(Xp)
    pca = PCA(n_components=args.d, random_state=0).fit(Xp_s)
    Z_pca = pca.transform(Xp_s)
    print(f"\nPCA d={args.d}: variance explained = "
          f"{pca.explained_variance_ratio_.sum():.3f}")

    # NMF (min-max scaled to [0,1] for non-negativity).
    Xp_pos = MinMaxScaler().fit_transform(Xp)
    nmf = NMF(n_components=args.d, init="nndsvd", random_state=0,
              max_iter=2000, tol=1e-5).fit(Xp_pos)
    Z_nmf = nmf.transform(Xp_pos)
    print(f"NMF d={args.d}: reconstruction err = {nmf.reconstruction_err_:.3f}")

    # ----- AQ regression -----
    print(f"\n=== WAB-AQ regression on z=={args.d} ===")
    r_pca = cv_regress(Z_pca, y_aq, groups, gbm_factory)
    r_nmf = cv_regress(Z_nmf, y_aq, groups, gbm_factory)
    r_raw = cv_regress(Xp, y_aq, groups, gbm_factory)
    print(f"  PCA z=8     MAE={r_pca['mae']:.2f}  r={r_pca['r']:+.3f}")
    print(f"  NMF z=8     MAE={r_nmf['mae']:.2f}  r={r_nmf['r']:+.3f}")
    print(f"  raw 55      MAE={r_raw['mae']:.2f}  r={r_raw['r']:+.3f}  (reference)")

    # ----- Subtype classification -----
    print(f"\n=== Subtype classification on z=={args.d} ===")
    sub_df = pat.dropna(subset=["subtype"]).reset_index(drop=True)
    counts = sub_df.groupby("subtype")["participant_id"].count()
    keep = counts[counts >= 5].index.tolist()
    sub_df = sub_df[sub_df["subtype"].isin(keep)].reset_index(drop=True)
    print(f"  {len(sub_df)} patients in subtypes: {sorted(keep)}")

    Xs = sub_df[feature_cols].to_numpy(dtype=float)
    y_sub = sub_df["subtype"].to_numpy(dtype=object)
    g_sub = sub_df["corpus"].to_numpy()

    Xs_s = StandardScaler().fit_transform(Xs)
    Z_pca_s = PCA(n_components=args.d, random_state=0).fit_transform(Xs_s)
    Z_nmf_s = NMF(n_components=args.d, init="nndsvd", random_state=0,
                   max_iter=2000).fit_transform(MinMaxScaler().fit_transform(Xs))

    c_pca = cv_classify(Z_pca_s, y_sub, g_sub)
    c_nmf = cv_classify(Z_nmf_s, y_sub, g_sub)
    c_raw = cv_classify(Xs, y_sub, g_sub)
    print(f"  PCA z=8     acc={c_pca['accuracy']:.3f}  macroF1={c_pca['macro_f1']:.3f}")
    print(f"  NMF z=8     acc={c_nmf['accuracy']:.3f}  macroF1={c_nmf['macro_f1']:.3f}")
    print(f"  raw 55      acc={c_raw['accuracy']:.3f}  macroF1={c_raw['macro_f1']:.3f}")

    # ----- Loadings interpretability -----
    print(f"\n=== Top loadings per dim ===")
    print("\nPCA loadings (signed; top ±5 per dim):")
    for j in range(args.d):
        comp = pca.components_[j]
        top = np.argsort(comp)[::-1][:5]
        bot = np.argsort(comp)[:5]
        top_s = ", ".join(f"{feature_cols[i]} ({comp[i]:+.2f})" for i in top)
        bot_s = ", ".join(f"{feature_cols[i]} ({comp[i]:+.2f})" for i in bot)
        print(f"  PC{j+1}: +{top_s}")
        print(f"        −{bot_s}")

    print("\nNMF loadings (non-negative; top 6 per component):")
    for j in range(args.d):
        comp = nmf.components_[j]
        top = np.argsort(comp)[::-1][:6]
        top_s = ", ".join(f"{feature_cols[i]} ({comp[i]:.3f})" for i in top)
        print(f"  NMF{j+1}: {top_s}")

    rows = [
        {"setup": "PCA_aq_regression", **r_pca, "d": args.d},
        {"setup": "NMF_aq_regression", **r_nmf, "d": args.d},
        {"setup": "raw_aq_regression", **r_raw, "d": "raw"},
        {"setup": "PCA_subtype", **c_pca, "d": args.d},
        {"setup": "NMF_subtype", **c_nmf, "d": args.d},
        {"setup": "raw_subtype", **c_raw, "d": "raw"},
    ]
    pd.DataFrame(rows).to_csv(args.output_dir / "summary.csv", index=False)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
