"""Phase 2 with semantic embeddings added to the structural feature set.

The headline test from #21 was that subtype + 55 structural features beat
subtype alone by ~0.5 MAE on WAB-AQ. The headline weakness from #22 was
that Wernicke (fluent but semantically impaired) classified at F1=0.18
because we don't measure semantics.

This script joins per-window MPNet embeddings (768-dim) to the existing
55-dim feature table and asks:

  - Does adding embeddings reduce the WAB-AQ regression MAE?
  - Does Wernicke F1 jump meaningfully?
  - Does within-subtype phenotyping become sharper for the fluent
    subtypes (Wernicke / Anomic / Conduction) that depend on semantic
    content?
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.stats import pearsonr, ttest_ind


META_COLS = {"transcript_id", "section", "corpus", "participant_id",
             "patient_root", "session_letter", "age_years",
             "sex", "subtype", "wab_aq", "is_control",
             "session_date", "window_id", "window_index",
             "n_chi_utts_in_window"}

MAJOR_SUBTYPES = ["Anomic", "Broca", "Conduction", "Wernicke"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--embeddings-path",
                   default="data/features/aphasia_window_embeddings.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/phase2_aphasia_embeddings",
                   type=Path)
    p.add_argument("--cv-folds", type=int, default=5)
    p.add_argument("--emb-pca-d", type=int, default=64,
                   help="Dimension to PCA-reduce 768-d embeddings to. "
                        "0 = use raw 768-d.")
    return p.parse_args()


def aggregate_to_patient(df, feature_cols, emb_cols):
    keep = ["participant_id", "corpus", "subtype", "wab_aq", "is_control"]
    return df.groupby("participant_id").agg(
        {**{f: "mean" for f in feature_cols + emb_cols},
         **{m: "first" for m in keep if m != "participant_id"}}
    ).reset_index()


def cv_regress(X, y, groups, n_splits, factory):
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(X, y, groups):
        m = factory()
        m.fit(X[tr], y[tr])
        preds[te] = m.predict(X[te])
    err = preds - y
    r = float(pearsonr(y, preds)[0]) if np.std(preds) > 0 else float("nan")
    return {"mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(err ** 2))),
            "r": r}


def cv_classify(X, y_str, groups, n_splits):
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.empty_like(y_str, dtype=object)
    for tr, te in gkf.split(X, y_str, groups):
        if len(set(y_str[tr])) < 2:
            preds[te] = y_str[tr][0]; continue
        clf = GradientBoostingClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05,
            subsample=0.9, random_state=0).fit(X[tr], y_str[tr])
        preds[te] = clf.predict(X[te])
    return {
        "accuracy": float((preds == y_str).mean()),
        "macro_f1": float(f1_score(y_str, preds, average="macro", zero_division=0)),
        "per_class_f1": {c: float(f1_score(y_str == c, preds == c, zero_division=0))
                         for c in sorted(set(y_str))},
    }


def gbm_factory():
    return GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    feats = pd.read_parquet(args.features_path)
    embs = pd.read_parquet(args.embeddings_path)
    print(f"features: {len(feats)} windows, {feats.shape[1]} cols")
    print(f"embeddings: {len(embs)} windows, {embs.shape[1]-1} dims")

    df = feats.merge(embs, on="window_id", how="inner")
    print(f"joined: {len(df)} windows")

    feature_cols = sorted(c for c in feats.columns if c not in META_COLS)
    emb_cols = sorted(c for c in embs.columns if c.startswith("emb"))
    print(f"  {len(feature_cols)} structural features, {len(emb_cols)} embedding dims")

    # PCA-reduce embeddings to a manageable dim before GBM.
    if args.emb_pca_d > 0 and args.emb_pca_d < len(emb_cols):
        emb_array = df[emb_cols].to_numpy(dtype=float)
        emb_scaled = StandardScaler().fit_transform(emb_array)
        emb_pca = PCA(n_components=args.emb_pca_d, random_state=0).fit(emb_scaled)
        emb_red = emb_pca.transform(emb_scaled)
        emb_cols_red = [f"epca_{i:03d}" for i in range(args.emb_pca_d)]
        for j, c in enumerate(emb_cols_red):
            df[c] = emb_red[:, j]
        emb_cols = emb_cols_red
        print(f"  embeddings reduced to {args.emb_pca_d}-d PCA "
              f"({emb_pca.explained_variance_ratio_.sum():.3f} var explained)")

    # ---- Aggregate to patient level for the AQ regression ----
    print("\n========== WAB-AQ regression (patient-level) ==========")
    pat = aggregate_to_patient(df, feature_cols, emb_cols)
    pat = pat.dropna(subset=["wab_aq"]).reset_index(drop=True)
    pat = pat[(pat["wab_aq"] >= 0) & (pat["wab_aq"] <= 100)].reset_index(drop=True)
    pat["sub_filled"] = pat["subtype"].fillna("Unknown")
    print(f"  {len(pat)} patients with WAB-AQ")

    y = pat["wab_aq"].to_numpy(dtype=float)
    groups = pat["corpus"].to_numpy()
    sub_arr = pat["sub_filled"].to_numpy(dtype=object)

    Xfeat = pat[feature_cols].to_numpy(dtype=float)
    Xemb = pat[emb_cols].to_numpy(dtype=float)

    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit(
        sub_arr.reshape(-1, 1))
    Sub = enc.transform(sub_arr.reshape(-1, 1))

    setups = {
        "subtype_only": Sub,
        "features_only_55": Xfeat,
        "embeddings_only": Xemb,
        "subtype_plus_features_55": np.concatenate([Sub, Xfeat], axis=1),
        "subtype_plus_embeddings": np.concatenate([Sub, Xemb], axis=1),
        "subtype_plus_features_plus_embeddings": np.concatenate(
            [Sub, Xfeat, Xemb], axis=1),
        "features_plus_embeddings_no_subtype": np.concatenate(
            [Xfeat, Xemb], axis=1),
    }

    rows_aq = []
    for name, X in setups.items():
        r = cv_regress(X, y, groups, args.cv_folds, gbm_factory)
        rows_aq.append({"setup": name, **r})
        print(f"  {name:42s}  MAE={r['mae']:6.2f}  RMSE={r['rmse']:6.2f}  r={r['r']:+.3f}")
    pd.DataFrame(rows_aq).to_csv(args.output_dir / "wab_aq.csv", index=False)

    # ---- Subtype classification (window-level, participant-grouped) ----
    print("\n========== Subtype classification ==========")
    sub_df = df.dropna(subset=["subtype"]).copy()
    sub_df = sub_df[~sub_df["subtype"].isin({"Unknown", "U"})]
    counts_by_pat = (sub_df.drop_duplicates("participant_id")
                            .groupby("subtype")["participant_id"].count())
    keep = counts_by_pat[counts_by_pat >= 5].index.tolist()
    sub_df = sub_df[sub_df["subtype"].isin(keep)].reset_index(drop=True)
    print(f"  {len(sub_df)} windows from "
          f"{sub_df['participant_id'].nunique()} patients in subtypes: "
          f"{sorted(keep)}")

    Xc_feat = sub_df[feature_cols].to_numpy(dtype=float)
    Xc_emb = sub_df[emb_cols].to_numpy(dtype=float)
    yc = sub_df["subtype"].to_numpy(dtype=object)
    gc = sub_df["participant_id"].to_numpy()

    setups_c = {
        "features_only_55": Xc_feat,
        "embeddings_only": Xc_emb,
        "features_plus_embeddings": np.concatenate([Xc_feat, Xc_emb], axis=1),
    }
    rows_c = []
    per_class_rows = []
    for name, X in setups_c.items():
        r = cv_classify(X, yc, gc, args.cv_folds)
        rows_c.append({"setup": name, "accuracy": r["accuracy"],
                       "macro_f1": r["macro_f1"]})
        for cls, f1 in r["per_class_f1"].items():
            per_class_rows.append({"setup": name, "subtype": cls, "f1": f1,
                                   "n": int((yc == cls).sum())})
        print(f"  {name:30s}  acc={r['accuracy']:.3f}  "
              f"macroF1={r['macro_f1']:.3f}")
    pd.DataFrame(rows_c).to_csv(args.output_dir / "subtype_classify.csv",
                                index=False)
    per_df = pd.DataFrame(per_class_rows)
    per_df.to_csv(args.output_dir / "subtype_per_class.csv", index=False)

    print("\n  Per-subtype F1 by setup:")
    pivot = per_df.pivot(index="subtype", columns="setup", values="f1")
    print(pivot.to_string(float_format=lambda v: f"{v:.3f}"))

    # ---- Within-subtype phenotyping with embeddings ----
    print("\n========== Within-subtype phenotyping (with embeddings) ==========")
    pat["sub_filled"] = pat["subtype"].fillna("Unknown")
    Xall = StandardScaler().fit_transform(
        np.concatenate([Xfeat, Xemb], axis=1))
    pca = PCA(n_components=8, random_state=0).fit(Xall)
    Z = pca.transform(Xall)
    print(f"  joint feature+emb space PCA(d=8) variance: "
          f"{pca.explained_variance_ratio_.sum():.3f}")
    for j in range(8):
        pat[f"jz{j+1}"] = Z[:, j]

    pheno_rows = []
    for subtype in MAJOR_SUBTYPES:
        sub = pat[pat["sub_filled"] == subtype]
        if len(sub) < 30:
            continue
        Zs = sub[[f"jz{j+1}" for j in range(8)]].to_numpy()
        km = KMeans(n_clusters=2, n_init=10, random_state=0).fit(Zs)
        sub = sub.assign(cluster=km.labels_)
        a = sub[sub.cluster == 0]["wab_aq"].dropna()
        b = sub[sub.cluster == 1]["wab_aq"].dropna()
        if len(a) >= 5 and len(b) >= 5:
            t, p = ttest_ind(a, b, equal_var=False)
        else:
            t, p = float("nan"), float("nan")
        pheno_rows.append({"subtype": subtype, "n": int(len(sub)),
                           "n_c0": int(len(a)), "n_c1": int(len(b)),
                           "mean_aq_c0": float(a.mean()) if len(a) else None,
                           "mean_aq_c1": float(b.mean()) if len(b) else None,
                           "t_stat": float(t), "p": float(p)})
        print(f"  {subtype:11s} n={len(sub):>3}  "
              f"c0_AQ={a.mean():.1f} (n={len(a)})  "
              f"c1_AQ={b.mean():.1f} (n={len(b)})  "
              f"t={t:+.2f}  p={p:.3f}")
    pd.DataFrame(pheno_rows).to_csv(
        args.output_dir / "phenotyping.csv", index=False)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
