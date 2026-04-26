"""Test whether explicit paraphasia annotations (Salem dataset) improve
the Wernicke gap.

The Salem corpus is a CMU-curated subset of AphasiaBank Cinderella
narratives where every paraphasia (a target word the patient *meant*
to say but didn't) is human-annotated. We use this as a
"semantic-error rate" feature and test:

  1. Does the per-session paraphasia rate correlate with WAB-AQ
     (sanity check)?
  2. Within Wernicke patients specifically, does paraphasia rate
     predict severity that our other features miss?
  3. Does adding `paraphasia_rate` and `n_targets` to the
     subtype+features+embeddings model improve Wernicke F1?

Salem covers ~354 PWA sessions, of which we expect ~30-40 Wernicke.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.stats import pearsonr


META = {"transcript_id", "section", "corpus", "participant_id",
        "patient_root", "session_letter", "age_years", "sex", "subtype",
        "wab_aq", "is_control", "session_date", "window_id", "window_index",
        "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--salem-csv",
                   default="data/raw/aphasiabank/extras/Salem/"
                           "talkbank-preprocessed-cinderella-data/"
                           "preprocessed-cinderella/aphasia-preprocessed/"
                           "sessions-report.csv",
                   type=Path)
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--embeddings-path",
                   default="data/features/aphasia_window_embeddings.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/salem_paraphasia",
                   type=Path)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # ----- Load Salem session-level paraphasia counts -----
    salem = pd.read_csv(args.salem_csv)
    salem.columns = [c.replace(" ", "_") for c in salem.columns]
    print(f"Salem PWA sessions: {len(salem)}")
    salem["n_targets"] = pd.to_numeric(salem["n_targets_(CHAT)"],
                                        errors="coerce")
    salem["wab_aq"] = pd.to_numeric(salem["wab_aq_index_(CHAT)"],
                                     errors="coerce")
    print(salem[["session_id", "wab_type", "wab_aq", "n_targets"]].head().to_string(index=False))

    # paraphasia rate ≈ n_targets / utt_count_per_session;
    # we don't have per-session utterance counts for Salem cleanly,
    # so use n_targets directly as a count-based feature.
    print(f"\nn_targets distribution: mean {salem['n_targets'].mean():.1f}, "
          f"median {salem['n_targets'].median():.1f}, "
          f"max {salem['n_targets'].max()}")

    # ----- Sanity: paraphasia ↔ WAB-AQ correlation -----
    sub = salem.dropna(subset=["wab_aq", "n_targets"])
    r, p = pearsonr(sub["n_targets"], sub["wab_aq"])
    print(f"\n[sanity] n_targets ↔ WAB-AQ: r = {r:+.3f} (p={p:.2e}, n={len(sub)})")

    # By WAB type
    print(f"\n[sanity] paraphasia rate by subtype:")
    by_type = (salem.dropna(subset=["wab_aq", "n_targets"])
                    .groupby("wab_type")
                    .agg(n=("session_id", "count"),
                         n_targets_mean=("n_targets", "mean"),
                         n_targets_std=("n_targets", "std"),
                         aq_mean=("wab_aq", "mean")))
    print(by_type.to_string())
    by_type.to_csv(args.output_dir / "paraphasia_by_subtype.csv")

    # ----- Join to our AphasiaBank window features -----
    feats = pd.read_parquet(args.features_path)
    feats["session_id"] = feats["participant_id"]  # they match by convention
    print(f"\nfeatures: {len(feats)} windows; "
          f"intersect with Salem: ", end="")
    feat_with_salem = feats.merge(
        salem[["session_id", "n_targets"]], on="session_id", how="inner")
    print(f"{len(feat_with_salem)} windows from "
          f"{feat_with_salem['session_id'].nunique()} sessions")

    # Patient-level aggregation for subtype classification.
    feature_cols = sorted(c for c in feats.columns if c not in META)

    # Optional embeddings
    emb_cols = []
    if args.embeddings_path.exists():
        embs = pd.read_parquet(args.embeddings_path)
        feat_with_salem = feat_with_salem.merge(embs, on="window_id",
                                                  how="inner")
        all_emb = sorted(c for c in embs.columns if c.startswith("emb"))
        # PCA reduce 768→64
        E = StandardScaler().fit_transform(
            feat_with_salem[all_emb].to_numpy(dtype=float))
        Er = PCA(n_components=64, random_state=0).fit_transform(E)
        for j in range(64):
            feat_with_salem[f"epca_{j:03d}"] = Er[:, j]
        emb_cols = [f"epca_{j:03d}" for j in range(64)]
        print(f"  joined embeddings: {len(emb_cols)} reduced dims")

    pat = feat_with_salem.groupby("session_id").agg(
        {**{c: "mean" for c in feature_cols + emb_cols + ["n_targets"]},
         **{m: "first" for m in ["subtype", "wab_aq", "corpus"]}}
    ).reset_index()
    pat = pat.dropna(subset=["wab_aq", "subtype"])
    print(f"\npatient-level rows: {len(pat)}; "
          f"subtype counts: {pat['subtype'].value_counts().to_dict()}")

    # ----- Subtype classification: features+embeddings ± paraphasia -----
    keep = [s for s in pat["subtype"].value_counts().index
            if pat[pat["subtype"] == s]["session_id"].nunique() >= 5
            and s not in {"Unknown", "U"}]
    sub_pat = pat[pat["subtype"].isin(keep)].reset_index(drop=True)
    print(f"\nclassification rows: {len(sub_pat)}; classes: {sorted(keep)}")

    if len(sub_pat) >= 50:
        Xfeat = sub_pat[feature_cols].to_numpy(dtype=float)
        Xemb = sub_pat[emb_cols].to_numpy(dtype=float) if emb_cols else None
        Xpara = sub_pat[["n_targets"]].to_numpy(dtype=float)
        y = sub_pat["subtype"].to_numpy(dtype=object)
        groups = sub_pat["corpus"].to_numpy()

        def cv_classify(X):
            n_g = len(set(groups))
            splits = max(2, min(5, n_g))
            gkf = GroupKFold(n_splits=splits)
            preds = np.empty_like(y, dtype=object)
            for tr, te in gkf.split(X, y, groups):
                if len(set(y[tr])) < 2:
                    preds[te] = y[tr][0]; continue
                clf = GradientBoostingClassifier(
                    n_estimators=300, max_depth=3, learning_rate=0.05,
                    subsample=0.9, random_state=0).fit(X[tr], y[tr])
                preds[te] = clf.predict(X[te])
            return {
                "accuracy": float((preds == y).mean()),
                "macro_f1": float(f1_score(y, preds, average="macro",
                                            zero_division=0)),
                "per_class_f1": {c: float(f1_score(y == c, preds == c,
                                                    zero_division=0))
                                  for c in sorted(set(y))},
            }

        setups = {"features_only": Xfeat,
                  "features_plus_paraphasia":
                      np.concatenate([Xfeat, Xpara], axis=1)}
        if Xemb is not None:
            setups["features_plus_embeddings"] = np.concatenate(
                [Xfeat, Xemb], axis=1)
            setups["features_plus_embeddings_plus_paraphasia"] = np.concatenate(
                [Xfeat, Xemb, Xpara], axis=1)

        rows = []
        for name, X in setups.items():
            r = cv_classify(X)
            rows.append({"setup": name, **{k: v for k, v in r.items()
                                            if k != "per_class_f1"}})
            print(f"\n  {name}: acc={r['accuracy']:.3f}  "
                  f"macroF1={r['macro_f1']:.3f}")
            print("    per-class F1:")
            for c, f1 in sorted(r["per_class_f1"].items()):
                n = int((y == c).sum())
                print(f"      {c:18s} n={n:>3}  F1={f1:.3f}")

        pd.DataFrame(rows).to_csv(args.output_dir / "salem_classify.csv",
                                   index=False)
    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
