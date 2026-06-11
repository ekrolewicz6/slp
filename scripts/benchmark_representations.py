"""Does a learned speech representation beat the 55 hand-crafted features?

The decisive test of Leap 1 (STRATEGY.md §2). Experiment #34 showed the
hand-crafted pipeline plateaus at n≈400 — model-limited, not data-limited.
If that ceiling is *representational*, a self-supervised speech embedding
should carry signal the summary statistics discard and push past it.

Runs the SAME patient-grouped protocol on both representations:
  - WAB-AQ regression       (GBM, GroupKFold by corpus, MAE + Pearson r)
  - Subtype classification  (GBM, GroupKFold by corpus, accuracy + macro-F1)

Setups compared:
  - handcrafted   : the existing 55 windowed features (always available)
  - foundation    : PCA-reduced wav2vec2/HuBERT window embeddings
  - fusion        : handcrafted + foundation

The foundation setups run only if
`data/features/aphasia_foundation_embeddings.parquet` exists (produced by
`extract_foundation_embeddings.py`). Until then the script reports the
hand-crafted baseline so the comparison harness is ready the moment the
embeddings land.

Run:  .venv/bin/python -m scripts.benchmark_representations
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import (GradientBoostingClassifier,
                              GradientBoostingRegressor)
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
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
    p.add_argument("--embeddings-path",
                   default="data/features/aphasia_foundation_embeddings.parquet",
                   type=Path)
    p.add_argument("--pca-dim", type=int, default=64)
    p.add_argument("--output-dir", default="outputs/representation_benchmark", type=Path)
    return p.parse_args()


def reg_cv(X, y, groups):
    gkf = GroupKFold(n_splits=max(2, min(5, len(set(groups)))))
    pred = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(X, y, groups):
        m = GradientBoostingRegressor(n_estimators=300, max_depth=3,
                                      learning_rate=0.05, subsample=0.9,
                                      random_state=0).fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    r = pearsonr(y, pred)[0] if np.std(pred) > 0 else float("nan")
    return {"mae": float(np.mean(np.abs(pred - y))), "r": float(r)}


def clf_cv(X, y, groups):
    gkf = GroupKFold(n_splits=max(2, min(5, len(set(groups)))))
    pred = np.empty(len(y), dtype=object)
    for tr, te in gkf.split(X, y, groups):
        m = GradientBoostingClassifier(n_estimators=300, max_depth=3,
                                       learning_rate=0.05, subsample=0.9,
                                       random_state=0).fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    return {"acc": float((pred == y).mean()),
            "macro_f1": float(f1_score(y, pred, average="macro"))}


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    feats = pd.read_parquet(args.features_path)
    feat_cols = sorted(c for c in feats.columns if c not in META)

    have_emb = args.embeddings_path.exists()
    if have_emb:
        emb = pd.read_parquet(args.embeddings_path)
        emb_cols = sorted(c for c in emb.columns if c.startswith("emb_"))
        df = feats.merge(emb[["window_id"] + emb_cols], on="window_id", how="inner")
        print(f"foundation embeddings: {len(emb)} windows · {len(emb_cols)}-d · "
              f"merged to {len(df)} windows with hand-crafted features")
    else:
        df = feats
        emb_cols = []
        print(f"[note] {args.embeddings_path} not found — running hand-crafted "
              f"baseline only. Run extract_foundation_embeddings.py to populate "
              f"the learned-representation setups.")

    # patient-level aggregation
    agg = {**{c: "mean" for c in feat_cols + emb_cols},
           **{m: "first" for m in ["subtype", "corpus", "wab_aq"]}}
    pat = df.groupby("participant_id").agg(agg).reset_index()

    setups = {"handcrafted": feat_cols}
    if emb_cols:
        # reduce learned embeddings to PCA-dim to match scale of handcrafted
        E = StandardScaler().fit_transform(pat[emb_cols].to_numpy(float))
        k = min(args.pca_dim, E.shape[1], max(2, len(pat) - 1))
        Ep = PCA(n_components=k, random_state=0).fit_transform(E)
        for j in range(k):
            pat[f"fnd_{j:03d}"] = Ep[:, j]
        fnd_cols = [f"fnd_{j:03d}" for j in range(k)]
        setups["foundation"] = fnd_cols
        setups["fusion"] = feat_cols + fnd_cols

    rows = []

    # --- WAB-AQ regression ---
    reg = pat.dropna(subset=["wab_aq"]).reset_index(drop=True)
    print(f"\nWAB-AQ regression: n={len(reg)} patients")
    if len(reg) >= 30:
        groups = reg["corpus"].to_numpy()
        for name, cols in setups.items():
            X = StandardScaler().fit_transform(reg[cols].to_numpy(float))
            r = reg_cv(X, reg["wab_aq"].to_numpy(float), groups)
            rows.append({"task": "wab_aq", "setup": name, "n": len(reg), **r})
            print(f"    {name:12s}  MAE={r['mae']:5.2f}  r={r['r']:+.3f}")

    # --- subtype classification ---
    clf = pat.dropna(subset=["subtype"])
    keep = clf["subtype"].value_counts()
    keep = keep[keep >= 8].index
    clf = clf[clf["subtype"].isin(keep)].reset_index(drop=True)
    print(f"\nSubtype classification: n={len(clf)} patients · "
          f"{clf['subtype'].nunique()} classes")
    if len(clf) >= 30:
        groups = clf["corpus"].to_numpy()
        for name, cols in setups.items():
            X = StandardScaler().fit_transform(clf[cols].to_numpy(float))
            r = clf_cv(X, clf["subtype"].to_numpy(), groups)
            rows.append({"task": "subtype", "setup": name, "n": len(clf), **r})
            print(f"    {name:12s}  acc={r['acc']:.3f}  macro-F1={r['macro_f1']:.3f}")

    out = pd.DataFrame(rows)
    out.to_csv(args.output_dir / "representation_benchmark.csv", index=False)
    print(f"\nsaved {args.output_dir / 'representation_benchmark.csv'}")
    if not have_emb:
        print("\nThis is the BASELINE. The Leap-1 claim is confirmed iff "
              "'foundation' or 'fusion' beats 'handcrafted' here once embeddings "
              "are extracted.")


if __name__ == "__main__":
    main()
