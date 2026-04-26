"""Cinderella concept hierarchy / narrative content staging.

If observed concept coverage is a strong severity signal, the next question is
whether the individual story concepts form a reproducible severity-ordered
hierarchy. A hierarchy would be more scientifically interesting than a raw
count: it would imply that aphasia degrades discourse content in an ordered
way, not just by reducing total output.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--joined", default="outputs/salem_cinderella_deep/salem_deep_joined.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/salem_concept_hierarchy", type=Path)
    p.add_argument("--bootstrap", default=500, type=int)
    return p.parse_args()


def concept_cols(df: pd.DataFrame) -> list[str]:
    return sorted(
        c for c in df.columns
        if c.startswith("observed_concept_")
        and c not in {"observed_concept_coverage", "observed_concept_density"}
    )


def fit_concept_thresholds(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for col in cols:
        y = df[col].astype(int).to_numpy()
        if y.sum() < 5 or y.sum() > len(y) - 5:
            continue
        x = df[["wab_aq"]].to_numpy(dtype=float)
        model = LogisticRegression(solver="lbfgs").fit(x, y)
        intercept = float(model.intercept_[0])
        slope = float(model.coef_[0, 0])
        threshold = float(-intercept / slope) if abs(slope) > 1e-9 else float("nan")
        prob = model.predict_proba(x)[:, 1]
        auc = float(roc_auc_score(y, prob))
        rows.append(
            {
                "concept": col.replace("observed_concept_", ""),
                "n": int(len(y)),
                "mention_rate": float(y.mean()),
                "slope_per_aq": slope,
                "threshold_aq_p50": threshold,
                "auc": auc,
                "r_with_wab_aq": pearson_safe(y, df["wab_aq"]),
            }
        )
    return pd.DataFrame(rows).sort_values("threshold_aq_p50")


def hierarchy_errors(X: np.ndarray, order: np.ndarray) -> tuple[int, float]:
    """Guttman-style errors after ordering concepts easiest -> hardest.

    For a participant with k observed concepts, the ideal hierarchical pattern
    has the k easiest concepts present and the rest absent. Errors are Hamming
    deviations from that ideal.
    """

    Xo = X[:, order]
    errors = 0
    for row in Xo:
        k = int(row.sum())
        ideal = np.zeros_like(row)
        if k:
            ideal[:k] = 1
        errors += int(np.abs(row - ideal).sum())
    cr = 1.0 - errors / Xo.size
    return errors, float(cr)


def bootstrap_thresholds(df: pd.DataFrame, cols: list[str], n_boot: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    participants = df["participant_id"].astype(str).unique()
    rows = []
    for b in range(n_boot):
        sampled = rng.choice(participants, size=len(participants), replace=True)
        boot = pd.concat([df[df["participant_id"].astype(str) == p] for p in sampled], ignore_index=True)
        tab = fit_concept_thresholds(boot, cols)
        tab["boot"] = b
        rows.append(tab)
    all_boot = pd.concat(rows, ignore_index=True)
    return (
        all_boot.groupby("concept")
        .agg(
            threshold_ci_low=("threshold_aq_p50", lambda s: float(np.nanpercentile(s, 2.5))),
            threshold_ci_high=("threshold_aq_p50", lambda s: float(np.nanpercentile(s, 97.5))),
            auc_ci_low=("auc", lambda s: float(np.nanpercentile(s, 2.5))),
            auc_ci_high=("auc", lambda s: float(np.nanpercentile(s, 97.5))),
        )
        .reset_index()
    )


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    df = pd.read_csv(args.joined)
    df = df[df["extract_error"].fillna("") == ""].copy()
    df = df.dropna(subset=["wab_aq", "participant_id"]).reset_index(drop=True)
    cols = concept_cols(df)

    thresholds = fit_concept_thresholds(df, cols)
    cis = bootstrap_thresholds(df, cols, args.bootstrap, seed=0)
    thresholds = thresholds.merge(cis, on="concept", how="left")
    thresholds.to_csv(out_dir / "concept_thresholds.csv", index=False)

    ordered = thresholds["concept"].tolist()
    ordered_cols = [f"observed_concept_{c}" for c in ordered]
    X = df[ordered_cols].astype(int).to_numpy()
    order = np.arange(len(ordered_cols))
    errors, cr = hierarchy_errors(X, order)

    rng = np.random.default_rng(0)
    random_cr = []
    for _ in range(1000):
        perm = rng.permutation(len(ordered_cols))
        _, cr_perm = hierarchy_errors(X, perm)
        random_cr.append(cr_perm)
    random_cr = np.asarray(random_cr)
    summary = {
        "n_sessions": int(len(df)),
        "n_concepts": int(len(ordered_cols)),
        "hierarchy_errors": int(errors),
        "coefficient_reproducibility": float(cr),
        "random_cr_mean": float(random_cr.mean()),
        "random_cr_p95": float(np.percentile(random_cr, 95)),
        "beats_random_p95": bool(cr > np.percentile(random_cr, 95)),
        "coverage_r_wab": pearson_safe(df[ordered_cols].sum(axis=1), df["wab_aq"]),
    }
    pd.DataFrame([summary]).to_csv(out_dir / "hierarchy_summary.csv", index=False)

    subtype_rows = []
    for subtype, group in df.groupby("wab_type"):
        if len(group) < 20:
            continue
        Xs = group[ordered_cols].astype(int).to_numpy()
        e, c = hierarchy_errors(Xs, order)
        subtype_rows.append(
            {
                "wab_type": subtype,
                "n": len(group),
                "coefficient_reproducibility": c,
                "coverage_r_wab": pearson_safe(group[ordered_cols].sum(axis=1), group["wab_aq"]),
            }
        )
    pd.DataFrame(subtype_rows).sort_values("coefficient_reproducibility", ascending=False).to_csv(
        out_dir / "hierarchy_by_subtype.csv",
        index=False,
    )

    print(thresholds.to_string(index=False))
    print(pd.DataFrame([summary]).to_string(index=False))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
