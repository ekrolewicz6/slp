"""Train on Eng-NA, predict Eng-UK (and reverse). True out-of-distribution test.

Stronger generalization check than leave-one-corpus-out: we train on a whole
dialect/protocol distribution and predict another. If a model's MAE survives
this split, it's actually learning developmental signal — not corpus-specific
artifacts of NA conventions.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


META_COLS = {"transcript_id", "corpus", "child_id", "age_months",
             "n_chi_utterances", "window_id", "window_index",
             "n_chi_utts_in_window", "bundle"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/phase1_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/ood_na_uk", type=Path)
    p.add_argument("--max-age-months", type=float, default=84.0)
    return p.parse_args()


def evaluate(model, X_train, y_train, X_test, y_test) -> dict:
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    err = pred - y_test
    return {
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "bias": float(np.mean(err)),
        "r": float(np.corrcoef(y_test, pred)[0, 1])
             if np.std(pred) > 0 and np.std(y_test) > 0 else float("nan"),
        "n_test": int(len(y_test)),
        "n_train": int(len(y_train)),
    }


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df = df.dropna(subset=["age_months"]).copy()
    df = df[(df.age_months > 0) & (df.age_months <= args.max_age_months)]
    feature_cols = sorted(c for c in df.columns if c not in META_COLS)

    na = df[df.bundle == "Eng-NA"].copy()
    uk = df[df.bundle == "Eng-UK"].copy()
    print(f"NA: {len(na)} windows ({na.child_id.nunique()} children, "
          f"{na.corpus.nunique()} corpora)")
    print(f"UK: {len(uk)} windows ({uk.child_id.nunique()} children, "
          f"{uk.corpus.nunique()} corpora)")

    if len(na) == 0 or len(uk) == 0:
        print("[!] One of the bundles is empty in the feature table. Aborting.")
        return

    Xna = na[feature_cols].to_numpy(dtype=float)
    yna = na["age_months"].to_numpy(dtype=float)
    Xuk = uk[feature_cols].to_numpy(dtype=float)
    yuk = uk["age_months"].to_numpy(dtype=float)

    models = {
        "ridge": Pipeline([("scale", StandardScaler()),
                           ("model", Ridge(alpha=1.0, random_state=0))]),
        "gbm": GradientBoostingRegressor(
            n_estimators=400, max_depth=3, learning_rate=0.05,
            subsample=0.9, random_state=0,
        ),
    }

    rows = []
    for name, proto in models.items():
        m_na = evaluate(clone(proto), Xna, yna, Xuk, yuk)
        m_uk = evaluate(clone(proto), Xuk, yuk, Xna, yna)
        rows.append({"model": name, "direction": "NA→UK", **m_na})
        rows.append({"model": name, "direction": "UK→NA", **m_uk})

    out = pd.DataFrame(rows)
    out.to_csv(args.output_dir / "metrics.csv", index=False)
    print()
    print(out.to_string(index=False, float_format=lambda v: f"{v:+.2f}"))

    print(f"\nReference: child-grouped within-distribution windowed GBM = 7.41 MAE")
    print(f"Done. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
