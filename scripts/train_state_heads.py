"""Train the calibrated state heads from real data and persist them.

Closes the `state=None/pending` gap in the measurement engine. Per the
Leap-1 verdict (#52):
  - SeverityHead : 55 text features → WAB-AQ, on all labeled patients.
  - SubtypeHead  : HuBERT layer-9 embedding → subtype, on the bake-off set.

Reports patient-grouped, corpus-OOD CV for each, then fits on all data and
saves to data/models/ (gitignored — models stay local like the parquets).

Run:  .venv/bin/python -m scripts.train_state_heads
"""

from __future__ import annotations

import argparse
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

from src.models.heads import SeverityHead, SubtypeHead

META = {"transcript_id", "section", "corpus", "participant_id", "patient_root",
        "session_letter", "age_years", "sex", "subtype", "wab_aq", "is_control",
        "session_date", "window_id", "window_index", "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--bakeoff-path",
                   default="data/features/aphasia_bakeoff_embeddings.parquet",
                   type=Path)
    p.add_argument("--model-dir", default="data/models", type=Path)
    p.add_argument("--pca-dim", type=int, default=48)
    return p.parse_args()


def train_severity(feats: pd.DataFrame, model_dir: Path) -> None:
    feat_cols = sorted(c for c in feats.columns if c not in META)
    pat = feats.groupby("participant_id").agg(
        {**{c: "mean" for c in feat_cols},
         **{m: "first" for m in ["corpus", "wab_aq"]}}).reset_index()
    pat = pat.dropna(subset=["wab_aq"]).reset_index(drop=True)
    X = pat[feat_cols].to_numpy(float)
    y = pat["wab_aq"].to_numpy(float)
    g = pat["corpus"].to_numpy()

    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    gkf = GroupKFold(n_splits=min(5, len(set(g))))
    pred = np.zeros_like(y)
    for tr, te in gkf.split(Xs, y, g):
        pred[te] = GradientBoostingRegressor(
            n_estimators=400, max_depth=3, learning_rate=0.05, subsample=0.9,
            random_state=0).fit(Xs[tr], y[tr]).predict(Xs[te])
    mae = float(np.mean(np.abs(pred - y)))
    r = float(pearsonr(y, pred)[0])
    print(f"[severity] n={len(pat)}  corpus-OOD CV: MAE={mae:.2f}  r={r:+.3f}")

    final = GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05, subsample=0.9,
        random_state=0).fit(Xs, y)
    head = SeverityHead(model=final, scaler=scaler, feature_names=feat_cols,
                        cv_mae=mae, cv_r=r)
    head.save(model_dir / "severity_head.joblib")
    print(f"[severity] saved → {model_dir / 'severity_head.joblib'}")


def train_subtype(feats: pd.DataFrame, bake: pd.DataFrame, model_dir: Path,
                  pca_dim: int) -> None:
    hub = sorted(c for c in bake.columns if c.startswith("hub9_"))
    sub_label = feats.drop_duplicates("participant_id").set_index(
        "participant_id")["subtype"]
    pat = bake.groupby("participant_id").agg(
        {**{c: "mean" for c in hub}, "corpus": "first"}).reset_index()
    pat["subtype"] = pat["participant_id"].map(sub_label)
    pat = pat.dropna(subset=["subtype"])
    keep = pat["subtype"].value_counts()
    pat = pat[pat["subtype"].isin(keep[keep >= 6].index)].reset_index(drop=True)

    X = pat[hub].to_numpy(float)
    y = pat["subtype"].to_numpy()
    g = pat["corpus"].to_numpy()
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    k = min(pca_dim, Xs.shape[1], max(2, len(pat) - 1))
    pca = PCA(n_components=k, random_state=0).fit(Xs)
    Z = pca.transform(Xs)

    gkf = GroupKFold(n_splits=max(2, min(5, len(set(g)))))
    pred = np.empty(len(y), dtype=object)
    for tr, te in gkf.split(Z, y, g):
        pred[te] = GradientBoostingClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.9,
            random_state=0).fit(Z[tr], y[tr]).predict(Z[te])
    mf1 = float(f1_score(y, pred, average="macro"))
    print(f"[subtype]  n={len(pat)}  classes={sorted(set(y))}")
    print(f"[subtype]  corpus-OOD CV: macro-F1={mf1:.3f}")

    final = GradientBoostingClassifier(
        n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.9,
        random_state=0).fit(Z, y)
    head = SubtypeHead(model=final, scaler=scaler, pca=pca,
                       classes=list(final.classes_),
                       encoder_name="facebook/hubert-base-ls960", layer=9,
                       cv_macro_f1=mf1)
    head.save(model_dir / "subtype_head.joblib")
    print(f"[subtype]  saved → {model_dir / 'subtype_head.joblib'}")


def main() -> None:
    args = parse_args()
    args.model_dir.mkdir(parents=True, exist_ok=True)
    feats = pd.read_parquet(args.features_path)
    print("Training calibrated state heads (Leap-1 recipe: text→severity, "
          "HuBERT→subtype)\n")
    train_severity(feats, args.model_dir)
    print()
    if args.bakeoff_path.exists():
        bake = pd.read_parquet(args.bakeoff_path)
        train_subtype(feats, bake, args.model_dir, args.pca_dim)
    else:
        print(f"[subtype]  {args.bakeoff_path} not found — skip "
              f"(run encoder_bakeoff.py first)")
    print("\nDone. The daily-checkin engine can now load these heads and emit "
          "real estimates instead of state_pending=None.")


if __name__ == "__main__":
    main()
