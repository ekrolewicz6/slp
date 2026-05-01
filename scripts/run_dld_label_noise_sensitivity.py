"""Audit how DLD screening conclusions change if clinical labels are noisy.

This uses existing participant-level held-out predictions. It does not refit
models; it asks how strongly the current conclusions depend on treating
DLD/SLI labels as clean ground truth.
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

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--participant-predictions",
        default="outputs/dld_review_grade_audit/participant_predictions.csv",
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/dld_label_noise_sensitivity", type=Path)
    p.add_argument("--bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=23)
    return p.parse_args()


def metrics(y_true: np.ndarray, y_proba: np.ndarray) -> dict[str, float]:
    y_pred = (y_proba >= 0.5).astype(int)
    out = {
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "positive_f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "auc": float("nan"),
    }
    if len(np.unique(y_true)) == 2:
        out["auc"] = float(roc_auc_score(y_true, y_proba))
    return out


def symmetric_noise_sensitivity(pred: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    noise_rates = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
    for feature_set, group in pred.groupby("feature_set"):
        group = group.reset_index(drop=True)
        y_true = group["y_true"].to_numpy(dtype=int)
        y_proba = group["y_proba"].to_numpy(dtype=float)
        for noise in noise_rates:
            boot = []
            for _ in range(n_boot):
                noisy = y_true.copy()
                if noise > 0:
                    flips = rng.random(len(noisy)) < noise
                    noisy[flips] = 1 - noisy[flips]
                vals = metrics(noisy, y_proba)
                boot.append(vals)
            row = {"feature_set": feature_set, "assumed_symmetric_label_noise": noise}
            for metric in ["balanced_accuracy", "macro_f1", "positive_f1", "auc"]:
                arr = np.array([b[metric] for b in boot], dtype=float)
                row[metric] = float(np.nanmean(arr))
                row[f"{metric}_lo"] = float(np.nanpercentile(arr, 2.5))
                row[f"{metric}_hi"] = float(np.nanpercentile(arr, 97.5))
            rows.append(row)
    return pd.DataFrame(rows)


def build_participant_matrix(pred: pd.DataFrame) -> pd.DataFrame:
    meta = pred.drop_duplicates("participant_root")[
        ["participant_root", "y_true", "corpus", "age_min", "age_max", "n_windows"]
    ]
    wide = pred.pivot_table(
        index="participant_root",
        columns="feature_set",
        values="y_proba",
        aggfunc="mean",
    ).reset_index()
    return meta.merge(wide, on="participant_root", how="left")


def label_noise_candidates(wide: pd.DataFrame) -> pd.DataFrame:
    out = wide.copy()
    for col in ["full_language_no_age", "full_language_age", "mlu_age", "corpus_age", "age_only"]:
        if col not in out.columns:
            out[col] = np.nan

    out["state_risk_consensus"] = (
        (out["full_language_no_age"] >= 0.75)
        & (out["full_language_age"] >= 0.75)
    )
    out["state_td_consensus"] = (
        (out["full_language_no_age"] <= 0.25)
        & (out["full_language_age"] <= 0.25)
    )
    out["td_label_state_risk"] = out["y_true"].eq(0) & out["state_risk_consensus"]
    out["dld_label_state_td_like"] = out["y_true"].eq(1) & out["state_td_consensus"]
    out["corpus_age_driven_risk"] = (
        (out["corpus_age"] >= 0.75)
        & (out["full_language_no_age"] < 0.50)
    )
    out["language_without_corpus_risk"] = (
        (out["full_language_no_age"] >= 0.75)
        & (out["corpus_age"] < 0.50)
    )
    out["label_noise_flag"] = np.select(
        [
            out["td_label_state_risk"],
            out["dld_label_state_td_like"],
            out["corpus_age_driven_risk"],
            out["language_without_corpus_risk"],
        ],
        [
            "TD_label_but_state_risk",
            "DLD_label_but_state_TD_like",
            "corpus_age_driven_risk",
            "language_state_risk_without_corpus",
        ],
        default="no_high_conflict",
    )
    return out.sort_values(["label_noise_flag", "corpus", "participant_root"])


def summarize_candidates(candidates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = (
        candidates.groupby("label_noise_flag")
        .agg(
            n=("participant_root", "count"),
            n_dld_labels=("y_true", "sum"),
            mean_full_language_no_age=("full_language_no_age", "mean"),
            mean_full_language_age=("full_language_age", "mean"),
            mean_corpus_age=("corpus_age", "mean"),
            mean_age_min=("age_min", "mean"),
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )
    by_corpus = (
        candidates[candidates["label_noise_flag"].ne("no_high_conflict")]
        .groupby(["corpus", "label_noise_flag"])
        .size()
        .reset_index(name="n")
        .sort_values(["corpus", "n"], ascending=[True, False])
    )
    return summary, by_corpus


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    pred = pd.read_csv(args.participant_predictions)
    noise = symmetric_noise_sensitivity(pred, args.bootstrap, args.seed)
    wide = build_participant_matrix(pred)
    candidates = label_noise_candidates(wide)
    candidate_summary, by_corpus = summarize_candidates(candidates)

    noise.to_csv(out_dir / "symmetric_noise_sensitivity.csv", index=False)
    wide.to_csv(out_dir / "participant_prediction_matrix.csv", index=False)
    candidates.to_csv(out_dir / "label_noise_candidates.csv", index=False)
    candidate_summary.to_csv(out_dir / "candidate_summary.csv", index=False)
    by_corpus.to_csv(out_dir / "candidate_by_corpus.csv", index=False)

    compact_noise = noise[
        noise["feature_set"].isin(["full_language_age", "full_language_no_age", "mlu_age", "corpus_age", "age_only"])
    ][
        [
            "feature_set",
            "assumed_symmetric_label_noise",
            "macro_f1",
            "macro_f1_lo",
            "macro_f1_hi",
            "auc",
            "auc_lo",
            "auc_hi",
        ]
    ]
    high_conflict = candidates[candidates["label_noise_flag"].ne("no_high_conflict")]
    lines = [
        "# DLD Label-Noise Sensitivity",
        "",
        "This audit treats DLD/SLI labels as noisy clinical anchors rather than clean ground truth.",
        "",
        "## Symmetric Label-Noise Sensitivity",
        "",
        md_table(compact_noise.round(3)),
        "",
        "## High-Confidence Label-Conflict Summary",
        "",
        md_table(candidate_summary.round(3)),
        "",
        "## High-Confidence Conflicts By Corpus",
        "",
        md_table(by_corpus),
        "",
        "## Example Conflict Candidates",
        "",
        md_table(
            high_conflict[
                [
                    "participant_root",
                    "corpus",
                    "y_true",
                    "age_min",
                    "full_language_no_age",
                    "full_language_age",
                    "mlu_age",
                    "corpus_age",
                    "label_noise_flag",
                ]
            ].round(3).head(40),
        ),
        "",
        "## Interpretation",
        "",
        "The screening signal should be framed as a noisy-label measurement result, not a diagnostic classifier. High-confidence discordant cases are not automatically mislabeled; they are the participants where corpus/task context, diagnosis, and language-state evidence disagree enough to require corpus-level review.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
