"""Predict every WAB subtest from our features, not just AQ.

The english-results-data.xlsx spreadsheet has ~60 columns per patient.
We've been collapsing everything into AQ. Each subtest is a different
prognostic dimension that our features should hit differently:

  - Naming targets lexical access (Object Naming, BNT, VNT) —
    Anomic patients should fail; lexical-diversity features should help
  - Repetition targets phonological encoding — Conduction patients fail
  - Comprehension (Yes/No, AudWdRec, SeqComm, Sent.Comp.) — Wernicke
    patients fail; our production-derived features may NOT help
  - Fluency (WAB SpontSp Fluency) — exactly what we should predict

This script predicts each subtest separately with patient-grouped CV
and reports MAE / RMSE / Pearson r for each. Identifies where our
pipeline is strongest and where it needs new feature inputs.
"""

from __future__ import annotations

import argparse
import glob
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.stats import pearsonr


META = {"transcript_id", "section", "corpus", "participant_id",
        "patient_root", "session_letter", "age_years", "sex", "subtype",
        "wab_aq", "is_control", "session_date", "window_id", "window_index",
        "n_chi_utts_in_window"}


# Subtest columns to predict, with human labels and dimension tag
OUTCOMES = {
    "WAB AQ": ("WAB         AQ Note: for Baycrest and NEURAL corpora, "
                "WAB scores are from Bedside WAB", "summary"),
    "WAB Fluency": ("WAB SpontSp Fluency", "production"),
    "WAB InfoContent": ("WAB    SpontSp InfoContent", "content"),
    "WAB Repetition": ("WAB Repetition", "phonological"),
    "WAB Object Naming": ("WAB Object Naming", "lexical"),
    "WAB Word Fluency": ("WAB  WdFluency", "lexical"),
    "WAB Sent Completion": ("WAB SentComp", "production"),
    "WAB Resp Speech": ("WAB RespSp", "production"),
    "WAB Yes/No": ("WAB Yes/No Q", "comprehension"),
    "WAB AudWdRec": ("WAB       AudWdRec", "comprehension"),
    "WAB SeqComm": ("WAB        SeqComm", "comprehension"),
    "Sent Comp Total": ("Sent. Comp. - Full Total", "comprehension"),
    "VNT Total": ("VNT Total", "lexical-verb"),
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--results-xlsx",
                   default="data/raw/aphasiabank/metadata/english-results-data.xlsx",
                   type=Path)
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--embeddings-path",
                   default="data/features/aphasia_window_embeddings.parquet",
                   type=Path)
    p.add_argument("--acoustic-pattern", default="data/features/acoustic_g*.parquet")
    p.add_argument("--output-dir", default="outputs/multi_outcome", type=Path)
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


def cv_regress(X, y, groups, n_splits=5):
    n_g = len(set(groups))
    gkf = GroupKFold(n_splits=max(2, min(n_splits, n_g)))
    preds = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(X, y, groups):
        m = GradientBoostingRegressor(n_estimators=300, max_depth=3,
                                       learning_rate=0.05, subsample=0.9,
                                       random_state=0).fit(X[tr], y[tr])
        preds[te] = m.predict(X[te])
    err = preds - y
    return {"mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(err ** 2))),
            "r": float(pearsonr(y, preds)[0]) if np.std(preds) > 0 else float("nan")}


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load + prep results spreadsheet
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = pd.read_excel(args.results_xlsx, sheet_name="Time 1")
    res.columns = [c.replace("\n", " ").strip() for c in res.columns]
    # Coerce all numeric columns
    for label, (col, _) in OUTCOMES.items():
        if col in res.columns:
            res[col] = pd.to_numeric(res[col], errors="coerce")
    res = res.rename(columns={"Participant ID": "participant_id"})
    res["participant_id"] = res["participant_id"].astype(str).str.strip()

    print(f"loaded results: {len(res)} sessions; outcomes available:")
    for label, (col, dim) in OUTCOMES.items():
        if col in res.columns:
            n = res[col].notna().sum()
            print(f"  {label:25s} ({dim:14s}) n={n:>4}")

    # Load features
    feats = pd.read_parquet(args.features_path)
    feature_cols = sorted(c for c in feats.columns if c not in META)

    embs = pd.read_parquet(args.embeddings_path)
    df = feats.merge(embs, on="window_id", how="inner")
    emb_cols_full = sorted(c for c in embs.columns if c.startswith("emb"))
    Earr = StandardScaler().fit_transform(df[emb_cols_full].to_numpy(dtype=float))
    Er = PCA(n_components=64, random_state=0).fit_transform(Earr)
    for j in range(64):
        df[f"epca_{j:03d}"] = Er[:, j]
    emb_cols = [f"epca_{j:03d}" for j in range(64)]

    # Acoustic
    ac_paths = sorted(glob.glob(args.acoustic_pattern))
    if ac_paths:
        ac = pd.concat([pd.read_parquet(p) for p in ac_paths], ignore_index=True)
        ac_cols = sorted(c for c in ac.columns if c.startswith("ac_"))
        df = df.merge(ac[["window_id"] + ac_cols], on="window_id", how="left")
        # Replace NaN in acoustic with column means
        Xa = df[ac_cols].to_numpy(dtype=float)
        col_means = np.nanmean(Xa, axis=0)
        col_means = np.where(np.isnan(col_means), 0.0, col_means)
        inds = np.where(np.isnan(Xa))
        Xa = Xa.copy(); Xa[inds] = np.take(col_means, inds[1])
        df_ac = pd.DataFrame(Xa, columns=ac_cols, index=df.index)
        df = df.drop(columns=ac_cols).join(df_ac)
    else:
        ac_cols = []

    # Aggregate to patient-level
    pat = df.groupby("participant_id").agg(
        {**{c: "mean" for c in feature_cols + emb_cols + ac_cols},
         **{m: "first" for m in ["subtype", "corpus", "is_control"]}}
    ).reset_index()

    # Compute developmental-age-equivalent (CHILDES-trained age regressor)
    print("\n[dev-age] training age regressor on CHILDES, applying to AphasiaBank...")
    chi = pd.read_parquet("data/features/phase1_windowed_features.parquet")
    chi = chi.dropna(subset=["age_months"])
    chi = chi[(chi.age_months > 0) & (chi.age_months <= 84)]
    chi_meta = {"transcript_id", "corpus", "child_id", "age_months",
                "n_chi_utterances", "bundle", "window_id", "window_index",
                "n_chi_utts_in_window"}
    chi_feature_cols = sorted(c for c in chi.columns if c not in chi_meta)
    common = sorted(set(feature_cols) & set(chi_feature_cols))
    chi_X = chi[common].to_numpy(dtype=float)
    chi_y = chi["age_months"].to_numpy(dtype=float)
    chi_scaler = StandardScaler().fit(chi_X)
    age_model = GradientBoostingRegressor(n_estimators=400, max_depth=4,
                                           learning_rate=0.05,
                                           subsample=0.85,
                                           random_state=0).fit(
        chi_scaler.transform(chi_X), chi_y)
    pat_X_common = pat[common].to_numpy(dtype=float)
    pat["_dev_age"] = age_model.predict(chi_scaler.transform(pat_X_common))
    print(f"  dev-age range across patients: "
          f"{pat['_dev_age'].min():.1f} - {pat['_dev_age'].max():.1f} months")

    # Join with results (case-insensitive)
    pat["participant_id"] = pat["participant_id"].astype(str).str.strip()
    pat["__pid_lc"] = pat["participant_id"].str.lower()
    res["__pid_lc"] = res["participant_id"].str.lower()
    joined = pat.merge(res, on="__pid_lc", how="inner",
                        suffixes=("", "_res"))
    print(f"\njoined feature × results: {len(joined)} patients")

    # Run regression for each outcome
    rows = []
    for label, (col, dim) in OUTCOMES.items():
        if col not in joined.columns:
            continue
        sub = joined.dropna(subset=[col]).reset_index(drop=True)
        if len(sub) < 30:
            print(f"  {label}: only {len(sub)} patients with target — skip")
            continue
        y = sub[col].to_numpy(dtype=float)
        groups = sub["corpus"].to_numpy()
        # Add subtype as feature
        sub_arr = sub["subtype"].fillna("Unknown").to_numpy(dtype=object)
        Sub = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit_transform(
            sub_arr.reshape(-1, 1))

        Xfeat = sub[feature_cols].to_numpy(dtype=float)
        Xemb = sub[emb_cols].to_numpy(dtype=float)
        Xac = sub[ac_cols].to_numpy(dtype=float) if ac_cols else None

        # Compute dev-age-equivalent for each patient using CHILDES regressor
        # (single number from CHILDES-trained age model)
        # We'll do this once outside this loop — see below
        dev_age = sub["_dev_age"].to_numpy(dtype=float).reshape(-1, 1)

        # Setups
        setups = {
            "subtype_only": Sub,
            "features_only": Xfeat,
            "subtype+features": np.concatenate([Sub, Xfeat], axis=1),
            "subtype+features+emb": np.concatenate([Sub, Xfeat, Xemb], axis=1),
            "dev_age_only": dev_age,  # The "one-number sufficiency" test
            "subtype+dev_age": np.concatenate([Sub, dev_age], axis=1),
        }
        if Xac is not None:
            setups["subtype+features+emb+acoustic"] = np.concatenate(
                [Sub, Xfeat, Xemb, Xac], axis=1)

        best = None
        for setup_name, X in setups.items():
            r = cv_regress(X, y, groups, args.cv_folds)
            r.update({"outcome": label, "dimension": dim, "setup": setup_name,
                       "n": len(sub), "y_mean": float(y.mean()),
                       "y_std": float(y.std()), "y_max": float(y.max())})
            rows.append(r)
            if best is None or r["r"] > best["r"]:
                best = r
        # Print best for this outcome
        b = best
        rel_mae = b['mae'] / max(b['y_max'], 1)
        print(f"\n  {label:25s} ({dim:14s}, n={b['n']:>3}): "
              f"best={b['setup']:30s} MAE={b['mae']:5.2f} (rel={rel_mae:.2%})  r={b['r']:+.3f}")

    out = pd.DataFrame(rows)
    out.to_csv(args.output_dir / "multi_outcome_results.csv", index=False)
    print(f"\nDone. Saved {args.output_dir / 'multi_outcome_results.csv'}")

    # Summary table: one row per outcome with best setup
    print("\n=== Best setup per outcome ===")
    best_per = out.loc[out.groupby("outcome")["r"].idxmax()][
        ["outcome", "dimension", "setup", "n", "mae", "r"]]
    print(best_per.sort_values("r", ascending=False).to_string(index=False))


if __name__ == "__main__":
    main()
