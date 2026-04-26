"""Within-corpus DLD deconfounding analyses.

The first DLD classifier was promising but corpus+age was a strong baseline.
This script asks whether DLD/SLI-vs-TD signal remains when each corpus is
treated as its own task/site, rather than letting the model exploit corpus
composition.
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

from scripts.run_dld_state_screening import (  # noqa: E402
    clinical_label,
    grouped_binary_cv,
    numeric_feature_columns,
    participant_root,
)


META_EXTRA = {"clinical_label", "participant_root", "screen_label"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--features-path",
        default="data/features/phase1_windowed_features.parquet",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/dld_corpus_deconfounding", type=Path)
    parser.add_argument("--seed", default=0, type=int)
    parser.add_argument("--max-age", default=84.0, type=float)
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


def add_metadata(df: pd.DataFrame, max_age: float) -> pd.DataFrame:
    out = df[df["bundle"].eq("Clinical-Eng")].copy()
    out["clinical_label"] = out["transcript_id"].map(clinical_label)
    out["participant_root"] = [
        participant_root(tid, label) for tid, label in zip(out["transcript_id"], out["clinical_label"])
    ]
    out["screen_label"] = out["clinical_label"]
    out = out[
        out["screen_label"].isin(["TD", "DLD_SLI"])
        & out["age_months"].notna()
        & out["age_months"].gt(0)
        & out["age_months"].le(max_age)
    ].copy()
    return out.reset_index(drop=True)


def participant_metrics(preds: pd.DataFrame) -> dict[str, float]:
    part = (
        preds.groupby("participant_root", as_index=False)
        .agg(
            y_true=("y_true", "max"),
            y_proba=("y_proba", "mean"),
            n_windows=("window_id", "count"),
        )
    )
    part["y_pred"] = (part["y_proba"] >= 0.5).astype(int)
    out = {
        "participant_balanced_accuracy": float(
            balanced_accuracy_score(part["y_true"], part["y_pred"])
        ),
        "participant_macro_f1": float(
            f1_score(part["y_true"], part["y_pred"], average="macro", zero_division=0)
        ),
        "participant_positive_f1": float(f1_score(part["y_true"], part["y_pred"], zero_division=0)),
        "participant_auc": float("nan"),
    }
    if part["y_true"].nunique() == 2:
        out["participant_auc"] = float(roc_auc_score(part["y_true"], part["y_proba"]))
    return out


def run_within_corpus(df: pd.DataFrame, feature_sets: dict[str, list[str]], seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    pred_rows = []
    for corpus, corpus_df in df.groupby("corpus"):
        if corpus_df["screen_label"].nunique() < 2:
            continue
        n_part = corpus_df.groupby("screen_label")["participant_root"].nunique().to_dict()
        if min(n_part.values()) < 8:
            continue
        for fs_name, cols in feature_sets.items():
            cols = [c for c in cols if c in corpus_df.columns]
            if not cols:
                continue
            try:
                metrics, preds = grouped_binary_cv(
                    corpus_df.dropna(subset=cols, how="all"),
                    cols,
                    "screen_label",
                    "DLD_SLI",
                    "participant_root",
                    seed,
                )
            except ValueError:
                continue
            pmetrics = participant_metrics(preds)
            rows.append(
                {
                    "corpus": corpus,
                    "feature_set": fs_name,
                    "n_windows": metrics["n_windows"],
                    "n_participants": metrics["n_participants"],
                    "n_dld_participants": metrics["n_positive_participants"],
                    "window_macro_f1": metrics["window_macro_f1"],
                    "window_auc": metrics["window_auc"],
                    **pmetrics,
                }
            )
            preds["corpus_model"] = corpus
            preds["feature_set"] = fs_name
            pred_rows.append(preds)
    return (
        pd.DataFrame(rows).sort_values(["corpus", "participant_macro_f1"], ascending=[True, False]),
        pd.concat(pred_rows, ignore_index=True) if pred_rows else pd.DataFrame(),
    )


def age_bin_balanced_subset(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["age_bin"] = (np.floor(work["age_months"] / 12.0) * 12).astype(int)
    keep = []
    for _, group in work.groupby(["corpus", "age_bin"]):
        roots = group.drop_duplicates("participant_root")
        counts = roots["screen_label"].value_counts()
        if counts.get("TD", 0) >= 3 and counts.get("DLD_SLI", 0) >= 3:
            keep.extend(group["participant_root"].unique().tolist())
    return work[work["participant_root"].isin(set(keep))].drop(columns=["age_bin"]).copy()


def pooled_prediction_summary(preds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fs, group in preds.groupby("feature_set"):
        part = (
            group.groupby("participant_root", as_index=False)
            .agg(
                y_true=("y_true", "max"),
                y_proba=("y_proba", "mean"),
                n_windows=("window_id", "count"),
                corpus=("corpus", "first"),
            )
        )
        part["y_pred"] = (part["y_proba"] >= 0.5).astype(int)
        rows.append(
            {
                "feature_set": fs,
                "n_participants": int(len(part)),
                "n_dld": int(part["y_true"].sum()),
                "participant_balanced_accuracy": float(
                    balanced_accuracy_score(part["y_true"], part["y_pred"])
                ),
                "participant_macro_f1": float(
                    f1_score(part["y_true"], part["y_pred"], average="macro", zero_division=0)
                ),
                "participant_auc": float(roc_auc_score(part["y_true"], part["y_proba"]))
                if part["y_true"].nunique() == 2
                else float("nan"),
            }
        )
    return pd.DataFrame(rows).sort_values("participant_macro_f1", ascending=False)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    raw = pd.read_parquet(args.features_path)
    df = add_metadata(raw, args.max_age)
    feature_cols = [c for c in numeric_feature_columns(df) if c not in META_EXTRA]
    feature_sets = {
        "age_only": ["age_months"],
        "mlu_age": [
            c
            for c in ["age_months", "mlu_words", "mlu_morphemes", "utt_len_mean", "single_word_ratio"]
            if c in df.columns
        ],
        "full_language_no_age": feature_cols,
        "full_language_age": ["age_months", *feature_cols],
    }

    inventory = (
        df.groupby(["corpus", "screen_label"])
        .agg(windows=("window_id", "count"), participants=("participant_root", "nunique"))
        .reset_index()
        .sort_values(["corpus", "screen_label"])
    )
    inventory.to_csv(out_dir / "corpus_label_inventory.csv", index=False)

    within, preds = run_within_corpus(df, feature_sets, args.seed)
    within.to_csv(out_dir / "within_corpus_metrics.csv", index=False)
    preds.to_csv(out_dir / "within_corpus_predictions.csv", index=False)
    pooled = pooled_prediction_summary(preds) if not preds.empty else pd.DataFrame()
    pooled.to_csv(out_dir / "within_corpus_pooled_predictions_summary.csv", index=False)

    matched_df = age_bin_balanced_subset(df)
    matched_within, matched_preds = run_within_corpus(matched_df, feature_sets, args.seed)
    matched_within.to_csv(out_dir / "age_bin_matched_within_corpus_metrics.csv", index=False)
    matched_preds.to_csv(out_dir / "age_bin_matched_within_corpus_predictions.csv", index=False)
    matched_pooled = pooled_prediction_summary(matched_preds) if not matched_preds.empty else pd.DataFrame()
    matched_pooled.to_csv(out_dir / "age_bin_matched_pooled_summary.csv", index=False)

    lines = [
        "# DLD Corpus Deconfounding Summary",
        "",
        "## Corpus/Label Inventory",
        "",
        md_table(inventory),
        "",
        "## Within-Corpus Metrics",
        "",
        "Each row trains and tests within one corpus using participant-held-out folds.",
        "",
        md_table(within),
        "",
        "## Pooled Within-Corpus Prediction Summary",
        "",
        md_table(pooled),
        "",
        "## Age-Bin Matched Within-Corpus Metrics",
        "",
        "Restricts to corpus x 12-month age bins containing both TD and DLD/SLI participants.",
        "",
        md_table(matched_within),
        "",
        "## Age-Bin Matched Pooled Summary",
        "",
        md_table(matched_pooled),
        "",
        "## Interpretation",
        "",
        "- If full language features remain useful within corpus, the signal is not only corpus membership.",
        "- If performance collapses after age-bin matching, apparent screening performance is mostly age/task/corpus composition.",
        "- Small corpora and path-derived labels still make this a discovery audit, not a clinical screening result.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print((out_dir / "summary.md").resolve())


if __name__ == "__main__":
    main()
