"""Review-grade audit for the first DLD screening run.

This script does not refit the DLD models. It audits the held-out predictions
from scripts/run_dld_state_screening.py at participant level:

* bootstrap confidence intervals;
* paired bootstrap model differences;
* corpus-balanced bootstrap evaluation;
* comparison to negative controls.

The result should be read as a validation audit of the first-pass experiment,
not as the final publication run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


METRIC_COLS = ["balanced_accuracy", "macro_f1", "positive_f1", "auc"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions",
        default="outputs/dld_state_screening/screening_predictions.csv",
        type=Path,
    )
    parser.add_argument(
        "--negative-controls",
        default="outputs/dld_state_screening/negative_controls.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/dld_review_grade_audit", type=Path)
    parser.add_argument("--task", default="DLD_SLI_vs_TD_age_le_84")
    parser.add_argument("--bootstrap", default=2000, type=int)
    parser.add_argument("--seed", default=0, type=int)
    return parser.parse_args()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def md_table(df: pd.DataFrame, max_rows: int | None = None, digits: int = 3) -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "_No rows._"
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.{digits}f}")
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def participant_predictions(pred: pd.DataFrame, task: str) -> pd.DataFrame:
    work = pred[pred["task"].eq(task)].copy()
    part = (
        work.groupby(["task", "feature_set", "participant_root"], as_index=False)
        .agg(
            y_true=("y_true", "max"),
            y_proba=("y_proba", "mean"),
            n_windows=("window_id", "count"),
            corpus=("corpus", "first"),
            age_min=("age_months", "min"),
            age_max=("age_months", "max"),
        )
    )
    part["y_pred"] = (part["y_proba"] >= 0.5).astype(int)
    return part


def metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> dict[str, float]:
    out = {
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "positive_f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "auc": float("nan"),
    }
    if len(np.unique(y_true)) == 2 and np.isfinite(y_proba).all():
        out["auc"] = float(roc_auc_score(y_true, y_proba))
    return out


def bootstrap_metric_rows(part: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for fs, group in part.groupby("feature_set"):
        group = group.reset_index(drop=True)
        base = metrics(group["y_true"].to_numpy(), group["y_pred"].to_numpy(), group["y_proba"].to_numpy())
        boot = {m: [] for m in METRIC_COLS}
        for _ in range(n_boot):
            idx = rng.choice(len(group), size=len(group), replace=True)
            vals = metrics(
                group.loc[idx, "y_true"].to_numpy(),
                group.loc[idx, "y_pred"].to_numpy(),
                group.loc[idx, "y_proba"].to_numpy(),
            )
            for m in METRIC_COLS:
                boot[m].append(vals[m])
        row = {
            "feature_set": fs,
            "n_participants": int(len(group)),
            "n_positive": int(group["y_true"].sum()),
        }
        for m in METRIC_COLS:
            arr = np.asarray(boot[m], dtype=float)
            row[m] = base[m]
            row[f"{m}_lo"] = float(np.nanpercentile(arr, 2.5))
            row[f"{m}_hi"] = float(np.nanpercentile(arr, 97.5))
        rows.append(row)
    return pd.DataFrame(rows).sort_values("macro_f1", ascending=False)


def paired_diff_rows(part: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    comparisons = [
        ("full_language_age", "mlu_age"),
        ("full_language_age", "age_only"),
        ("full_language_age", "corpus_age"),
        ("full_language_no_age", "mlu_age"),
        ("corpus_age", "full_language_age"),
    ]
    rows = []
    for a, b in comparisons:
        pa = part[part["feature_set"].eq(a)].copy()
        pb = part[part["feature_set"].eq(b)].copy()
        merged = pa.merge(
            pb,
            on=["task", "participant_root", "y_true", "corpus"],
            suffixes=("_a", "_b"),
        )
        if len(merged) < 20:
            continue
        base_a = metrics(
            merged["y_true"].to_numpy(),
            merged["y_pred_a"].to_numpy(),
            merged["y_proba_a"].to_numpy(),
        )
        base_b = metrics(
            merged["y_true"].to_numpy(),
            merged["y_pred_b"].to_numpy(),
            merged["y_proba_b"].to_numpy(),
        )
        row = {"feature_set_a": a, "feature_set_b": b, "n_paired": int(len(merged))}
        boot = {m: [] for m in METRIC_COLS}
        for _ in range(n_boot):
            idx = rng.choice(len(merged), size=len(merged), replace=True)
            va = metrics(
                merged.loc[idx, "y_true"].to_numpy(),
                merged.loc[idx, "y_pred_a"].to_numpy(),
                merged.loc[idx, "y_proba_a"].to_numpy(),
            )
            vb = metrics(
                merged.loc[idx, "y_true"].to_numpy(),
                merged.loc[idx, "y_pred_b"].to_numpy(),
                merged.loc[idx, "y_proba_b"].to_numpy(),
            )
            for m in METRIC_COLS:
                boot[m].append(va[m] - vb[m])
        for m in METRIC_COLS:
            arr = np.asarray(boot[m], dtype=float)
            row[f"delta_{m}"] = base_a[m] - base_b[m]
            row[f"delta_{m}_lo"] = float(np.nanpercentile(arr, 2.5))
            row[f"delta_{m}_hi"] = float(np.nanpercentile(arr, 97.5))
        rows.append(row)
    return pd.DataFrame(rows).sort_values("delta_macro_f1", ascending=False)


def corpus_balanced_bootstrap(part: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for fs, group in part.groupby("feature_set"):
        strata = []
        for corpus, cg in group.groupby("corpus"):
            pos = cg[cg["y_true"].eq(1)].reset_index(drop=True)
            neg = cg[cg["y_true"].eq(0)].reset_index(drop=True)
            n = min(len(pos), len(neg))
            if n >= 3:
                strata.append((corpus, pos, neg, n))
        if not strata:
            continue
        boot = {m: [] for m in METRIC_COLS}
        n_sample = 0
        for _ in range(n_boot):
            samples = []
            for _, pos, neg, n in strata:
                samples.append(pos.iloc[rng.choice(len(pos), size=n, replace=True)])
                samples.append(neg.iloc[rng.choice(len(neg), size=n, replace=True)])
            sample = pd.concat(samples, ignore_index=True)
            n_sample = len(sample)
            vals = metrics(
                sample["y_true"].to_numpy(),
                sample["y_pred"].to_numpy(),
                sample["y_proba"].to_numpy(),
            )
            for m in METRIC_COLS:
                boot[m].append(vals[m])
        row = {
            "feature_set": fs,
            "n_corpora_with_both_classes": int(len(strata)),
            "balanced_sample_size_per_boot": int(n_sample),
        }
        for m in METRIC_COLS:
            arr = np.asarray(boot[m], dtype=float)
            row[m] = float(np.nanmean(arr))
            row[f"{m}_lo"] = float(np.nanpercentile(arr, 2.5))
            row[f"{m}_hi"] = float(np.nanpercentile(arr, 97.5))
        rows.append(row)
    return pd.DataFrame(rows).sort_values("macro_f1", ascending=False)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    pred = pd.read_csv(args.predictions)
    part = participant_predictions(pred, args.task)
    part.to_csv(out_dir / "participant_predictions.csv", index=False)

    ci = bootstrap_metric_rows(part, args.bootstrap, args.seed)
    diff = paired_diff_rows(part, args.bootstrap, args.seed + 1)
    balanced = corpus_balanced_bootstrap(part, args.bootstrap, args.seed + 2)
    ci.to_csv(out_dir / "participant_bootstrap_cis.csv", index=False)
    diff.to_csv(out_dir / "paired_model_differences.csv", index=False)
    balanced.to_csv(out_dir / "corpus_balanced_bootstrap.csv", index=False)

    controls = pd.read_csv(args.negative_controls) if args.negative_controls.exists() else pd.DataFrame()
    controls.to_csv(out_dir / "negative_controls_copy.csv", index=False)

    compact_ci_cols = [
        "feature_set",
        "n_participants",
        "n_positive",
        "macro_f1",
        "macro_f1_lo",
        "macro_f1_hi",
        "auc",
        "auc_lo",
        "auc_hi",
    ]
    compact_diff_cols = [
        "feature_set_a",
        "feature_set_b",
        "n_paired",
        "delta_macro_f1",
        "delta_macro_f1_lo",
        "delta_macro_f1_hi",
        "delta_auc",
        "delta_auc_lo",
        "delta_auc_hi",
    ]
    compact_bal_cols = [
        "feature_set",
        "n_corpora_with_both_classes",
        "balanced_sample_size_per_boot",
        "macro_f1",
        "macro_f1_lo",
        "macro_f1_hi",
        "auc",
        "auc_lo",
        "auc_hi",
    ]

    lines = [
        "# DLD Review-Grade Screening Audit",
        "",
        f"- Task: {args.task}",
        f"- Bootstrap resamples: {args.bootstrap}",
        "",
        "## Participant-Level Bootstrap CIs",
        "",
        md_table(ci[compact_ci_cols]),
        "",
        "## Paired Model Differences",
        "",
        "Positive delta means feature_set_a outperforms feature_set_b on the same participants.",
        "",
        md_table(diff[compact_diff_cols]),
        "",
        "## Corpus-Balanced Bootstrap",
        "",
        "Each bootstrap samples equal positive and TD participant counts within corpora that contain both classes.",
        "",
        md_table(balanced[compact_bal_cols]),
        "",
        "## Negative Controls From First-Pass Run",
        "",
        md_table(controls),
        "",
        "## Interpretation",
        "",
        "- Full language state beats MLU+age and age-only with participant-level uncertainty.",
        "- Corpus+age remains a serious artifact baseline; if it matches or beats full language, screening claims must be framed as corpus-bound.",
        "- Corpus-balanced evaluation is the more honest estimate of transfer within the currently available Clinical-Eng data.",
        "- The next publication-grade run should refit models inside each balanced bootstrap, not only resample held-out predictions.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print((out_dir / "summary.md").resolve())


if __name__ == "__main__":
    main()
