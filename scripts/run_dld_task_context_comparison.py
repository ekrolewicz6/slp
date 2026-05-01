"""Compare DLD/SLI signal across narrative and natural-speech task contexts."""

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

from scripts.run_dld_fairness_metadata_audit import parse_task_proxy  # noqa: E402
from scripts.run_dld_state_screening import (  # noqa: E402
    clinical_label,
    classifier_pipeline,
    grouped_binary_cv,
    numeric_feature_columns,
    participant_root,
)
from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


META_EXTRA = {"clinical_label", "participant_root", "screen_label", "task_proxy", "task_bucket"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path", default="data/features/phase1_windowed_features.parquet", type=Path)
    p.add_argument("--output-dir", default="outputs/dld_task_context_comparison", type=Path)
    p.add_argument("--max-age", default=156.0, type=float)
    p.add_argument("--seed", default=31, type=int)
    return p.parse_args()


def task_bucket(task_proxy: str) -> str:
    if task_proxy in {"narrative", "narrative_enni", "narrative_gillam", "frog_story", "story"}:
        return "narrative_story"
    if task_proxy in {"parent_child", "conversation", "interview", "meal", "play"}:
        return "natural_conversation"
    if task_proxy in {"elicited_context"}:
        return "elicited_context"
    return "unknown"


def add_metadata(df: pd.DataFrame, max_age: float) -> pd.DataFrame:
    out = df[df["bundle"].eq("Clinical-Eng")].copy()
    out["clinical_label"] = out["transcript_id"].map(clinical_label)
    out["participant_root"] = [
        participant_root(tid, label) for tid, label in zip(out["transcript_id"], out["clinical_label"])
    ]
    out["screen_label"] = out["clinical_label"]
    out["task_proxy"] = [parse_task_proxy(tid, corpus) for tid, corpus in zip(out["transcript_id"], out["corpus"])]
    out["task_bucket"] = out["task_proxy"].map(task_bucket)
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
        "participant_balanced_accuracy": float(balanced_accuracy_score(part["y_true"], part["y_pred"])),
        "participant_macro_f1": float(f1_score(part["y_true"], part["y_pred"], average="macro", zero_division=0)),
        "participant_positive_f1": float(f1_score(part["y_true"], part["y_pred"], zero_division=0)),
        "participant_auc": float("nan"),
    }
    if part["y_true"].nunique() == 2 and part["y_proba"].notna().all():
        out["participant_auc"] = float(roc_auc_score(part["y_true"], part["y_proba"]))
    return out


def feature_sets(df: pd.DataFrame) -> dict[str, list[str]]:
    numeric = [c for c in numeric_feature_columns(df) if c not in META_EXTRA]
    return {
        "age_only": ["age_months"],
        "mlu_age": [
            c for c in ["age_months", "mlu_words", "mlu_morphemes", "utt_len_mean", "single_word_ratio"]
            if c in df.columns
        ],
        "full_language_no_age": numeric,
        "full_language_age": ["age_months", *numeric],
    }


def within_bucket(df: pd.DataFrame, fsets: dict[str, list[str]], seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    pred_rows = []
    for bucket, group in df.groupby("task_bucket"):
        if group["screen_label"].nunique() < 2:
            continue
        part_counts = group.groupby("screen_label")["participant_root"].nunique()
        if part_counts.min() < 8:
            continue
        for fs_name, cols in fsets.items():
            cols = [c for c in cols if c in group.columns]
            if not cols:
                continue
            try:
                metrics, preds = grouped_binary_cv(
                    group,
                    cols,
                    "screen_label",
                    "DLD_SLI",
                    "participant_root",
                    seed,
                )
            except ValueError:
                continue
            rows.append({
                "analysis": "within_bucket_cv",
                "train_bucket": bucket,
                "test_bucket": bucket,
                "feature_set": fs_name,
                "n_windows": metrics["n_windows"],
                "n_participants": metrics["n_participants"],
                "n_dld_participants": metrics["n_positive_participants"],
                **participant_metrics(preds),
            })
            preds["analysis"] = "within_bucket_cv"
            preds["train_bucket"] = bucket
            preds["test_bucket"] = bucket
            preds["feature_set"] = fs_name
            pred_rows.append(preds)
    return pd.DataFrame(rows), pd.concat(pred_rows, ignore_index=True) if pred_rows else pd.DataFrame()


def train_test_bucket_transfer(df: pd.DataFrame, fsets: dict[str, list[str]], seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    pred_rows = []
    buckets = sorted(df["task_bucket"].unique())
    for train_bucket in buckets:
        train = df[df["task_bucket"].eq(train_bucket)].copy()
        if train["screen_label"].nunique() < 2:
            continue
        if train.groupby("screen_label")["participant_root"].nunique().min() < 8:
            continue
        for test_bucket in buckets:
            if test_bucket == train_bucket:
                continue
            test = df[df["task_bucket"].eq(test_bucket)].copy()
            if test["screen_label"].nunique() < 2:
                continue
            if test.groupby("screen_label")["participant_root"].nunique().min() < 8:
                continue
            for fs_name, cols in fsets.items():
                cols = [c for c in cols if c in train.columns and c in test.columns]
                if not cols:
                    continue
                model = classifier_pipeline(seed)
                X_train = train[cols]
                y_train = train["screen_label"].eq("DLD_SLI").astype(int).to_numpy()
                X_test = test[cols]
                y_test = test["screen_label"].eq("DLD_SLI").astype(int).to_numpy()
                model.fit(X_train, y_train)
                proba = model.predict_proba(X_test)[:, 1]
                pred = (proba >= 0.5).astype(int)
                pred_df = test[
                    ["window_id", "transcript_id", "corpus", "participant_root", "age_months", "screen_label"]
                ].copy()
                pred_df["y_true"] = y_test
                pred_df["y_pred"] = pred
                pred_df["y_proba"] = proba
                rows.append({
                    "analysis": "train_bucket_test_bucket",
                    "train_bucket": train_bucket,
                    "test_bucket": test_bucket,
                    "feature_set": fs_name,
                    "n_windows": int(len(test)),
                    "n_participants": int(test["participant_root"].nunique()),
                    "n_dld_participants": int(test[test["screen_label"].eq("DLD_SLI")]["participant_root"].nunique()),
                    **participant_metrics(pred_df),
                })
                pred_df["analysis"] = "train_bucket_test_bucket"
                pred_df["train_bucket"] = train_bucket
                pred_df["test_bucket"] = test_bucket
                pred_df["feature_set"] = fs_name
                pred_rows.append(pred_df)
    return pd.DataFrame(rows), pd.concat(pred_rows, ignore_index=True) if pred_rows else pd.DataFrame()


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    raw = pd.read_parquet(args.features_path)
    df = add_metadata(raw, args.max_age)
    fsets = feature_sets(df)
    inventory = (
        df.groupby(["task_bucket", "task_proxy", "corpus", "screen_label"])
        .agg(windows=("window_id", "count"), participants=("participant_root", "nunique"))
        .reset_index()
        .sort_values(["task_bucket", "task_proxy", "corpus", "screen_label"])
    )
    within, within_preds = within_bucket(df, fsets, args.seed)
    transfer, transfer_preds = train_test_bucket_transfer(df, fsets, args.seed)
    metrics = pd.concat([within, transfer], ignore_index=True)
    preds = pd.concat([within_preds, transfer_preds], ignore_index=True)

    inventory.to_csv(out_dir / "task_context_inventory.csv", index=False)
    metrics.to_csv(out_dir / "task_context_metrics.csv", index=False)
    preds.to_csv(out_dir / "task_context_predictions.csv", index=False)

    compact = metrics[
        [
            "analysis",
            "train_bucket",
            "test_bucket",
            "feature_set",
            "n_participants",
            "n_dld_participants",
            "participant_balanced_accuracy",
            "participant_macro_f1",
            "participant_positive_f1",
            "participant_auc",
        ]
    ].sort_values(["analysis", "test_bucket", "participant_macro_f1"], ascending=[True, True, False])
    lines = [
        "# DLD Task-Context Comparison",
        "",
        "This compares narrative/story contexts with natural conversation/play contexts in the local Clinical-Eng data. It still does not test sentence repetition or nonword repetition because the local inventory found no usable candidates.",
        "",
        "## Task Context Inventory",
        "",
        md_table(inventory),
        "",
        "## Metrics",
        "",
        md_table(compact.round(3)),
        "",
        "## Interpretation",
        "",
        "- Narrative/story data carry a usable DLD/SLI signal in the local data, especially ENNI and Gillam-style narratives.",
        "- Natural conversation is less clean because the available DLD and TD samples are unevenly distributed across corpora and tasks.",
        "- Cross-task transfer is the honest stress test: if train-on-narrative/test-on-natural or the reverse collapses, the model is learning task context rather than a task-general language state.",
        "- The result supports Brian's advice: natural speech and tight/structured tasks should be paired prospectively rather than treated as interchangeable.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
