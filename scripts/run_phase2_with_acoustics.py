"""Phase 2 with structural + semantic + acoustic features stacked.

Fires whatever acoustic data has been extracted (whether the full
1683 sessions or a partial subset). Asks:

  1. Does adding acoustics reduce WAB-AQ MAE further (best so far 9.69)?
  2. Does Wernicke F1 finally move from its 0.18-0.20 floor?
  3. Within-subtype phenotyping — does Conduction (the previously-null
     subtype) split with prosody features?

If only a subset of patients has acoustic features, we run on that
subset only — that's a different sample than #21/#29 but the
direction of effect (does adding acoustics help?) is what we care about.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.stats import pearsonr, ttest_ind


META = {"transcript_id", "section", "corpus", "participant_id",
        "patient_root", "session_letter", "age_years", "sex", "subtype",
        "wab_aq", "is_control", "session_date", "window_id", "window_index",
        "n_chi_utts_in_window"}

MAJOR = ["Anomic", "Broca", "Conduction", "Wernicke"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--embeddings-path",
                   default="data/features/aphasia_window_embeddings.parquet",
                   type=Path)
    p.add_argument("--acoustic-pattern", default="data/features/acoustic_g*.parquet",
                   help="Glob pattern for acoustic-feature parquets to merge.")
    p.add_argument("--output-dir",
                   default="outputs/phase2_aphasia_acoustic", type=Path)
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


def cv_regress(X, y, groups, n_splits, factory):
    n_g = len(set(groups))
    splits = max(2, min(n_splits, n_g))
    gkf = GroupKFold(n_splits=splits)
    preds = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(X, y, groups):
        m = factory()
        m.fit(X[tr], y[tr])
        preds[te] = m.predict(X[te])
    err = preds - y
    return {"mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(err ** 2))),
            "r": float(pearsonr(y, preds)[0]) if np.std(preds) > 0
                 else float("nan")}


def cv_classify(X, y_str, groups, n_splits):
    n_g = len(set(groups))
    splits = max(2, min(n_splits, n_g))
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
        "macro_f1": float(f1_score(y_str, preds, average="macro",
                                    zero_division=0)),
        "per_class_f1": {c: float(f1_score(y_str == c, preds == c,
                                            zero_division=0))
                          for c in sorted(set(y_str))},
    }


def gbm():
    return GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    feats = pd.read_parquet(args.features_path)
    feature_cols = sorted(c for c in feats.columns if c not in META)

    # Load all available acoustic parquets
    ac_paths = sorted(Path().glob(args.acoustic_pattern))
    if not ac_paths:
        print(f"[!] No acoustic parquets found at {args.acoustic_pattern}",
              flush=True)
        return
    ac = pd.concat([pd.read_parquet(p) for p in ac_paths], ignore_index=True)
    ac_cols = sorted(c for c in ac.columns if c.startswith("ac_"))
    print(f"loaded acoustic features: {len(ac)} window rows from "
          f"{ac['transcript_id'].nunique()} sessions, {len(ac_cols)} cols")

    df = feats.merge(ac[["window_id"] + ac_cols], on="window_id", how="inner")
    print(f"joined feats+acoustic: {len(df)} windows, "
          f"{df['transcript_id'].nunique()} sessions")

    # Optional embeddings join
    has_emb = args.embeddings_path.exists()
    emb_cols = []
    if has_emb:
        embs = pd.read_parquet(args.embeddings_path)
        df = df.merge(embs, on="window_id", how="inner")
        all_emb = sorted(c for c in embs.columns if c.startswith("emb"))
        # Reduce 768->64 for efficiency
        E = StandardScaler().fit_transform(df[all_emb].to_numpy(dtype=float))
        Er = PCA(n_components=min(64, len(all_emb)),
                  random_state=0).fit_transform(E)
        for j in range(Er.shape[1]):
            df[f"epca_{j:03d}"] = Er[:, j]
        emb_cols = [f"epca_{j:03d}" for j in range(Er.shape[1])]
        print(f"  joined embeddings (PCA-reduced to {len(emb_cols)})")

    # Patient-level
    pat = df.groupby("participant_id").agg(
        {**{c: "mean" for c in feature_cols + ac_cols + emb_cols},
         **{m: "first" for m in ["wab_aq", "subtype", "corpus", "is_control"]}}
    ).reset_index()
    pat = pat.dropna(subset=["wab_aq"])
    pat = pat[pat.wab_aq.between(0, 100)].reset_index(drop=True)
    pat["sub_filled"] = pat["subtype"].fillna("Unknown")
    print(f"  patient-level: {len(pat)} patients with WAB-AQ")

    Xfeat = pat[feature_cols].to_numpy(dtype=float)
    Xac = np.array(pat[ac_cols].to_numpy(dtype=float), copy=True)
    if Xac.size:
        col_means = np.nanmean(Xac, axis=0)
        col_means = np.where(np.isnan(col_means), 0.0, col_means)
        inds = np.where(np.isnan(Xac))
        Xac[inds] = np.take(col_means, inds[1])

    Xemb = pat[emb_cols].to_numpy(dtype=float) if emb_cols else None
    y = pat["wab_aq"].to_numpy(dtype=float)
    groups = pat["corpus"].to_numpy()
    sub_arr = pat["sub_filled"].to_numpy(dtype=object)
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit(
        sub_arr.reshape(-1, 1))
    Sub = enc.transform(sub_arr.reshape(-1, 1))

    # ----- WAB-AQ regression -----
    print(f"\n========== WAB-AQ regression (n={len(pat)}) ==========")
    setups = {
        "subtype_only": Sub,
        "features_only": Xfeat,
        "acoustic_only": Xac,
        "subtype_plus_features": np.concatenate([Sub, Xfeat], axis=1),
        "subtype_plus_features_plus_acoustic":
            np.concatenate([Sub, Xfeat, Xac], axis=1),
    }
    if Xemb is not None:
        setups["subtype_plus_features_plus_embeddings"] = np.concatenate(
            [Sub, Xfeat, Xemb], axis=1)
        setups["subtype_plus_features_plus_emb_plus_acoustic"] = np.concatenate(
            [Sub, Xfeat, Xemb, Xac], axis=1)

    rows = []
    for name, X in setups.items():
        r = cv_regress(X, y, groups, args.cv_folds, gbm)
        rows.append({"setup": name, **r})
        print(f"  {name:50s}  MAE={r['mae']:.2f}  r={r['r']:+.3f}")
    pd.DataFrame(rows).to_csv(args.output_dir / "wab_aq.csv", index=False)

    # ----- Subtype classification -----
    print(f"\n========== Subtype classification ==========")
    sub_df = df.dropna(subset=["subtype"]).copy()
    sub_df = sub_df[~sub_df["subtype"].isin({"Unknown", "U"})]
    counts_pat = (sub_df.drop_duplicates("participant_id")
                          .groupby("subtype")["participant_id"].count())
    keep = counts_pat[counts_pat >= 5].index.tolist()
    sub_df = sub_df[sub_df["subtype"].isin(keep)].reset_index(drop=True)

    Xc_feat = sub_df[feature_cols].to_numpy(dtype=float)
    Xc_ac = np.array(sub_df[ac_cols].to_numpy(dtype=float), copy=True)
    if Xc_ac.size:
        col_means = np.nanmean(Xc_ac, axis=0)
        col_means = np.where(np.isnan(col_means), 0.0, col_means)
        inds = np.where(np.isnan(Xc_ac))
        Xc_ac[inds] = np.take(col_means, inds[1])
    Xc_emb = sub_df[emb_cols].to_numpy(dtype=float) if emb_cols else None
    yc = sub_df["subtype"].to_numpy(dtype=object)
    gc = sub_df["participant_id"].to_numpy()
    print(f"  {len(sub_df)} windows from "
          f"{sub_df['participant_id'].nunique()} patients in subtypes: "
          f"{sorted(keep)}")

    setups_c = {
        "features_only": Xc_feat,
        "acoustic_only": Xc_ac,
        "features_plus_acoustic":
            np.concatenate([Xc_feat, Xc_ac], axis=1),
    }
    if Xc_emb is not None:
        setups_c["features_plus_embeddings_plus_acoustic"] = np.concatenate(
            [Xc_feat, Xc_emb, Xc_ac], axis=1)

    rows_c = []
    per_class_rows = []
    for name, X in setups_c.items():
        r = cv_classify(X, yc, gc, args.cv_folds)
        rows_c.append({"setup": name, "accuracy": r["accuracy"],
                       "macro_f1": r["macro_f1"]})
        print(f"\n  {name}: acc={r['accuracy']:.3f}  macroF1={r['macro_f1']:.3f}")
        for c, f1 in r["per_class_f1"].items():
            per_class_rows.append({"setup": name, "subtype": c, "f1": f1,
                                   "n": int((yc == c).sum())})
            print(f"    {c:18s} F1={f1:.3f}")
    pd.DataFrame(rows_c).to_csv(args.output_dir / "subtype_classify.csv",
                                index=False)
    pd.DataFrame(per_class_rows).to_csv(
        args.output_dir / "subtype_per_class.csv", index=False)

    # ----- Within-subtype phenotyping with acoustics -----
    print(f"\n========== Within-subtype phenotyping (joint feat+ac+emb space) ==========")
    Xall = pat[feature_cols + ac_cols + emb_cols].to_numpy(dtype=float)
    inds = np.where(np.isnan(Xall))
    Xall[inds] = np.take(np.nanmean(Xall, axis=0), inds[1])
    Xall_s = StandardScaler().fit_transform(Xall)
    pca = PCA(n_components=8, random_state=0).fit(Xall_s)
    Z = pca.transform(Xall_s)
    for j in range(8):
        pat[f"jz{j+1}"] = Z[:, j]
    print(f"  joint space PCA(d=8) variance: "
          f"{pca.explained_variance_ratio_.sum():.3f}")

    pheno_rows = []
    for subtype in MAJOR:
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
                           "mean_aq_c0": float(a.mean()) if len(a) else None,
                           "mean_aq_c1": float(b.mean()) if len(b) else None,
                           "t_stat": float(t), "p": float(p)})
        print(f"  {subtype:11s} n={len(sub):>3}  "
              f"AQ c0={a.mean():.1f} ({len(a)})  c1={b.mean():.1f} ({len(b)})  "
              f"t={t:+.2f} p={p:.3f}")
    pd.DataFrame(pheno_rows).to_csv(
        args.output_dir / "phenotyping.csv", index=False)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
