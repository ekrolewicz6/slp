"""Sensitivity checks for late-talker catch-up and persistent-gap prediction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import balanced_accuracy_score, f1_score, mean_absolute_error, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--residual-state",
        default="outputs/dld_late_talker_catchup/rescorla_td_residual_state.csv",
        type=Path,
    )
    p.add_argument(
        "--trajectories",
        default="outputs/dld_late_talker_catchup/rescorla_trajectories.csv",
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/dld_late_talker_persistence_sensitivity", type=Path)
    p.add_argument("--seed", default=41, type=int)
    return p.parse_args()


def build_model_table(resid: pd.DataFrame, traj: pd.DataFrame) -> pd.DataFrame:
    lt = resid[resid["clinical_label"].eq("LateTalker")].copy()
    rows = []
    for pid, group in lt.sort_values("age_repaired").groupby("participant_root"):
        t = traj[traj["participant_root"].eq(pid)]
        if t.empty:
            continue
        first = group.iloc[0]
        row = {
            "participant_root": pid,
            "age_first": first["age_repaired"],
            "first_composite_z": first["rescorla_composite_z"],
            "first_mlu": first["mlu_words"],
            "first_utterance_length_z": first["utterance_length_z"],
            "first_lexical_predicate_z": first["lexical_predicate_z"],
            "first_grammar_argument_z": first["grammar_argument_z"],
            "first_fluency_repair_z": first["fluency_repair_z"],
            "last_composite_z": t["last_composite_z"].iloc[0],
            "final_in_td_band": int(t["final_in_td_band"].iloc[0]),
            "persistent_gap": int(t["persistent_gap"].iloc[0]),
            "age_last": t["age_last"].iloc[0],
        }
        by_age = group.set_index("age_repaired")
        if 36.0 in by_age.index and 48.0 in by_age.index:
            row["delta_36_48_composite_z"] = (
                by_age.loc[48.0, "rescorla_composite_z"] - by_age.loc[36.0, "rescorla_composite_z"]
            )
            row["delta_36_48_mlu"] = by_age.loc[48.0, "mlu_words"] - by_age.loc[36.0, "mlu_words"]
        else:
            row["delta_36_48_composite_z"] = np.nan
            row["delta_36_48_mlu"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def clf_pipeline(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    C=0.5,
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=seed,
                ),
            ),
        ]
    )


def reg_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )


def evaluate(table: pd.DataFrame, seed: int) -> pd.DataFrame:
    feature_sets = {
        "first_mlu_only": ["first_mlu"],
        "first_composite_only": ["first_composite_z"],
        "first_axes": [
            "first_composite_z",
            "first_utterance_length_z",
            "first_lexical_predicate_z",
            "first_grammar_argument_z",
            "first_fluency_repair_z",
            "first_mlu",
        ],
        "first_plus_36_48_change": [
            "first_composite_z",
            "first_utterance_length_z",
            "first_lexical_predicate_z",
            "first_grammar_argument_z",
            "first_fluency_repair_z",
            "first_mlu",
            "delta_36_48_composite_z",
            "delta_36_48_mlu",
        ],
    }
    rows = []
    for target in ["final_in_td_band", "persistent_gap"]:
        y = table[target].to_numpy(dtype=int)
        if len(np.unique(y)) < 2 or min(np.bincount(y)) < 4:
            continue
        cv = StratifiedKFold(n_splits=min(5, min(np.bincount(y))), shuffle=True, random_state=seed)
        for name, cols in feature_sets.items():
            X = table[cols]
            proba = cross_val_predict(clf_pipeline(seed), X, y, cv=cv, method="predict_proba")[:, 1]
            pred = (proba >= 0.5).astype(int)
            rows.append({
                "target": target,
                "feature_set": name,
                "n": len(table),
                "positive_rate": float(y.mean()),
                "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
                "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
                "positive_f1": float(f1_score(y, pred, zero_division=0)),
                "auc": float(roc_auc_score(y, proba)),
            })
    y_cont = table["last_composite_z"].to_numpy(dtype=float)
    cv_reg = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=seed,
    )
    bins = pd.qcut(y_cont, q=min(5, len(np.unique(y_cont))), labels=False, duplicates="drop")
    for name, cols in feature_sets.items():
        pred = cross_val_predict(reg_pipeline(), table[cols], y_cont, cv=cv_reg.split(table[cols], bins))
        rows.append({
            "target": "last_composite_z",
            "feature_set": name,
            "n": len(table),
            "positive_rate": np.nan,
            "balanced_accuracy": np.nan,
            "macro_f1": np.nan,
            "positive_f1": np.nan,
            "auc": np.nan,
            "mae": float(mean_absolute_error(y_cont, pred)),
            "corr": pearson_safe(y_cont, pred),
        })
    return pd.DataFrame(rows)


def descriptive_bins(table: pd.DataFrame) -> pd.DataFrame:
    work = table.copy()
    work["first_state_bin"] = pd.cut(
        work["first_composite_z"],
        bins=[-np.inf, -2.0, -1.0, -0.5, np.inf],
        labels=["very_low", "low", "near_td", "td_like"],
    )
    return (
        work.groupby("first_state_bin", observed=True)
        .agg(
            n=("participant_root", "count"),
            mean_first_z=("first_composite_z", "mean"),
            mean_last_z=("last_composite_z", "mean"),
            final_td_band_rate=("final_in_td_band", "mean"),
            persistent_gap_rate=("persistent_gap", "mean"),
            mean_delta_36_48_z=("delta_36_48_composite_z", "mean"),
        )
        .reset_index()
    )


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    resid = pd.read_csv(args.residual_state)
    traj = pd.read_csv(args.trajectories)
    table = build_model_table(resid, traj)
    metrics_all = evaluate(table, args.seed)
    metrics_all.insert(0, "cohort", "all_longitudinal")
    long_horizon = table[table["age_last"].ge(108)].copy()
    metrics_long = evaluate(long_horizon, args.seed) if len(long_horizon) >= 12 else pd.DataFrame()
    if not metrics_long.empty:
        metrics_long.insert(0, "cohort", "final_age_ge_108")
    metrics = pd.concat([metrics_all, metrics_long], ignore_index=True)
    bins = descriptive_bins(table)
    table.to_csv(out_dir / "late_talker_model_table.csv", index=False)
    metrics.to_csv(out_dir / "persistence_prediction_metrics.csv", index=False)
    bins.to_csv(out_dir / "early_state_bin_outcomes.csv", index=False)

    lines = [
        "# Late-Talker Persistence Sensitivity",
        "",
        f"- Late talkers with longitudinal trajectories: {len(table):,}",
        f"- Late talkers with final age >= 108 months: {len(long_horizon):,}",
        f"- Final TD-band rate: {table['final_in_td_band'].mean():.3f}",
        f"- Persistent-gap rate: {table['persistent_gap'].mean():.3f}",
        "",
        "## Prediction Metrics",
        "",
        md_table(metrics.round(3)),
        "",
        "## Early State Bins",
        "",
        md_table(bins.round(3)),
        "",
        "## Interpretation",
        "",
        "In the local Rescorla data, earliest transcript state alone is useful descriptively but weak as an individual-level predictor of final catch-up. The more interesting signal is early change: adding 36-to-48-month movement improves prediction even when final observations are restricted to 108+ months. This still falls short of treatment-response science, because it lacks treatment exposure, standardized outcome anchors, and external replication.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
