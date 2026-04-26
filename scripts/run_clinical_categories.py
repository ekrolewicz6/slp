"""Categorical-vs-z dry run on Clinical-Eng diagnostic labels.

The §Phase 2 spec hypothesis is that categorical clinical labels are lossy
slices of an underlying continuous state. We can test this *now*, before
AphasiaBank arrives, on Clinical-Eng — which has explicit diagnostic groups
(TD, HL, DS, SLI/LI, etc.) coded into the corpus directory structure.

Three questions:

  1. **Can we predict diagnosis from the latent state z at all?** If z carries
     no clinical signal, the architecture is a non-starter for aphasia.
  2. **Does z compress beat raw 55-feature classification?** Same logic as
     Phase 2 dry run on age — if the bottleneck preserves clinical signal,
     it argues z captures the right primitives.
  3. **Does the latent space cluster by diagnosis?** If so, "categories" are
     organic; if z bleeds across them, that's evidence for the continuum
     hypothesis.

Diagnosis labels are extracted from the relative path: the first subdirectory
under the corpus name often encodes the group (e.g. `Ambrose/HL/...`,
`EllisWeismer/TD/...`, `Hooshyar/DS/...`). Corpora without a recognizable
group label are dropped from this evaluation.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

META_COLS = {"transcript_id", "corpus", "child_id", "age_months",
             "n_chi_utterances", "bundle", "window_id", "window_index",
             "n_chi_utts_in_window", "diagnosis"}

# Subdir tokens that look like diagnostic labels (extend as needed).
KNOWN_LABELS = {
    "TD", "HL", "DS", "SLI", "LI", "ASD", "AS", "ADHD",
    "Chronic", "Acute", "TBI", "PPA", "FXS",
}


def extract_diagnosis(transcript_id: str) -> str | None:
    """Look at the path under the corpus root; return the first subdir if it
    matches a known diagnostic-label token. transcript_id format from our
    pipeline: `<bundle>/<corpus>/<sub1>/.../<file>`.
    """
    parts = transcript_id.split("/")
    if len(parts) < 3:
        return None
    # parts[0] = bundle, parts[1] = corpus, parts[2:] = subpath
    for token in parts[2:-1]:
        if token in KNOWN_LABELS:
            return token
    return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/phase1_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/clinical_categories", type=Path)
    p.add_argument("--latent-d", type=int, default=8)
    return p.parse_args()


def cv_classify(X: np.ndarray, y_str: np.ndarray, groups: np.ndarray,
                n_splits: int = 5) -> dict:
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.empty_like(y_str, dtype=object)
    for train_idx, test_idx in gkf.split(X, y_str, groups):
        # Refit per fold; weak class imbalance handling via stratifying within group
        # is not necessary because GBC handles class weights internally if needed.
        if len(set(y_str[train_idx])) < 2:
            preds[test_idx] = y_str[train_idx][0]
            continue
        model = GradientBoostingClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05,
            subsample=0.9, random_state=0,
        ).fit(X[train_idx], y_str[train_idx])
        preds[test_idx] = model.predict(X[test_idx])
    return {
        "accuracy": float((preds == y_str).mean()),
        "macro_f1": float(f1_score(y_str, preds, average="macro", zero_division=0)),
        "per_class_f1": {
            c: float(f1_score(y_str == c, preds == c, zero_division=0))
            for c in sorted(set(y_str))
        },
    }


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df = df[df["bundle"] == "Clinical-Eng"].copy().reset_index(drop=True)
    df["diagnosis"] = df["transcript_id"].apply(extract_diagnosis)
    labelled = df.dropna(subset=["diagnosis"]).copy().reset_index(drop=True)
    print(f"Clinical-Eng total windows: {len(df)}")
    print(f"Labelled (extractable diagnosis token): {len(labelled)}  "
          f"({labelled['child_id'].nunique()} children, "
          f"{labelled['corpus'].nunique()} corpora)")
    print(f"Diagnosis distribution: {Counter(labelled['diagnosis'])}")

    # Drop tiny classes (<200 windows) — cross-fold becomes meaningless.
    counts = labelled["diagnosis"].value_counts()
    keep = counts[counts >= 200].index.tolist()
    labelled = labelled[labelled["diagnosis"].isin(keep)].reset_index(drop=True)
    print(f"After dropping classes <200 windows: {len(labelled)} rows; "
          f"classes: {sorted(keep)}")

    feature_cols = sorted(c for c in labelled.columns if c not in META_COLS)
    X_raw = labelled[feature_cols].to_numpy(dtype=float)
    y = labelled["diagnosis"].to_numpy(dtype=object)
    groups = labelled["child_id"].to_numpy()

    # Reuse the same z used elsewhere (PCA d=8) but fit on Clinical-Eng only,
    # to avoid Eng-NA/UK age signal swamping the clinical signal.
    scaler = StandardScaler().fit(X_raw)
    Xs = scaler.transform(X_raw)
    pca = PCA(n_components=args.latent_d, random_state=0).fit(Xs)
    Z = pca.transform(Xs)
    print(f"PCA(d={args.latent_d}) variance explained: "
          f"{pca.explained_variance_ratio_.sum():.3f}")

    print("\n[1] Diagnosis classification, child-grouped 5-fold CV:")
    raw_metrics = cv_classify(X_raw, y, groups)
    z_metrics = cv_classify(Z, y, groups)
    print(f"  raw 55 features  acc={raw_metrics['accuracy']:.3f}  "
          f"macroF1={raw_metrics['macro_f1']:.3f}")
    print(f"  z=8 (PCA)       acc={z_metrics['accuracy']:.3f}  "
          f"macroF1={z_metrics['macro_f1']:.3f}")

    print("\n  per-class F1 (raw):")
    for c, f1 in sorted(raw_metrics["per_class_f1"].items()):
        print(f"    {c:6s} {f1:.3f}")
    print("\n  per-class F1 (z=8):")
    for c, f1 in sorted(z_metrics["per_class_f1"].items()):
        print(f"    {c:6s} {f1:.3f}")

    pd.DataFrame([
        {"feature_set": "raw_55", **{k: v for k, v in raw_metrics.items() if k != "per_class_f1"}},
        {"feature_set": "pca_z8", **{k: v for k, v in z_metrics.items() if k != "per_class_f1"}},
    ]).to_csv(args.output_dir / "diagnosis_classification.csv", index=False)

    # Where does each diagnosis sit in z? Compute centroid + spread.
    centroids = []
    for diag in sorted(set(y)):
        mask = y == diag
        centroids.append({
            "diagnosis": diag,
            "n_windows": int(mask.sum()),
            **{f"z{j+1}_mean": float(Z[mask, j].mean()) for j in range(args.latent_d)},
            **{f"z{j+1}_std": float(Z[mask, j].std()) for j in range(args.latent_d)},
        })
    pd.DataFrame(centroids).to_csv(args.output_dir / "z_centroids.csv", index=False)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
