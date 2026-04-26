"""Pilot deployable ASR-only controller for rewrite/clarify/preserve decisions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table, negation_count  # noqa: E402
from scripts.run_cross_prompt_content import CONCEPTS, chat_tokens, concept_hits  # noqa: E402
from src.analysis.review_grade import bootstrap_ci, ensure_dir  # noqa: E402


FILLERS = {"um", "uh", "hm", "hmm", "oh", "ah", "er"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--items-path",
        default="outputs/asr_reconstruction_safety_pwa60_tiny_cleanclips/asr_safety_items.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/asr_safety_controller_pwa60_tiny_cleanclips",
        type=Path,
    )
    parser.add_argument("--folds", default=5, type=int)
    parser.add_argument("--seed", default=0, type=int)
    return parser.parse_args()


def action_label(bucket: str) -> str:
    if bucket in {"unknown_intent", "known_plus_unknown_risk"}:
        return "clarify"
    if bucket == "known_target_safe_zone":
        return "rewrite"
    return "preserve"


def token_features(text: str, task: str) -> dict[str, float]:
    toks = chat_tokens(str(text), include_targets=False)
    n = len(toks)
    unique = len(set(toks))
    hits = concept_hits(toks, task) if task in CONCEPTS else {}
    repeated = sum(1 for a, b in zip(toks, toks[1:], strict=False) if a == b)
    filler = sum(1 for tok in toks if tok in FILLERS)
    alpha_lens = [len(re.sub(r"[^a-z]", "", tok)) for tok in toks]
    return {
        "asr_token_count": float(n),
        "asr_type_token_ratio": unique / max(n, 1),
        "asr_mean_token_len": float(np.mean(alpha_lens)) if alpha_lens else 0.0,
        "asr_repeated_token_rate": repeated / max(n - 1, 1),
        "asr_filler_rate": filler / max(n, 1),
        "asr_negation_count": float(negation_count(text)),
        "asr_concept_count": float(sum(hits.values())),
        "asr_concept_frac": float(sum(hits.values()) / max(len(CONCEPTS.get(task, [])), 1)),
    }


def build_model(feature_set: str) -> Pipeline:
    numeric_base = [
        "asr_token_count",
        "asr_type_token_ratio",
        "asr_mean_token_len",
        "asr_repeated_token_rate",
        "asr_filler_rate",
        "asr_negation_count",
        "asr_concept_count",
        "asr_concept_frac",
        "clip_success_rate",
    ]
    operational_sets = {
        "asr_operational_no_conf",
        "asr_text_no_conf",
        "asr_operational",
        "asr_text",
        "clinical_upper",
    }
    confidence_sets = {"asr_operational", "asr_text", "clinical_upper"}
    if feature_set in operational_sets:
        numeric_base.extend(
            [
                "total_par_audio_seconds",
                "asr_speech_rate",
                "n_utterance_clips_attempted",
                "n_utterance_clips_transcribed",
            ]
        )
    if feature_set in confidence_sets:
        numeric_base.extend(
            [
                "whisper_clip_segment_count_mean",
                "whisper_avg_logprob_mean",
                "whisper_avg_logprob_min",
                "whisper_no_speech_prob_mean",
                "whisper_no_speech_prob_max",
                "whisper_compression_ratio_mean",
                "whisper_compression_ratio_max",
            ]
        )
    if feature_set == "clinical_upper":
        numeric_base.extend(["wab_aq"])
    if feature_set == "privileged_error_oracle":
        numeric_base.extend(
            [
                "known_reconstructable_error_count",
                "unknown_intent_error_count",
                "error_total",
                "oracle_concept_gain",
            ]
        )

    categorical = ["task"]
    if feature_set == "clinical_upper":
        categorical.append("subtype")

    transformers = [
        (
            "num",
            Pipeline(
                [
                    ("impute", SimpleImputer(strategy="median")),
                    ("scale", StandardScaler()),
                ]
            ),
            numeric_base,
        ),
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            categorical,
        ),
    ]
    if feature_set in {"asr_text_no_conf", "asr_text", "clinical_upper"}:
        transformers.append(
            (
                "text",
                TfidfVectorizer(min_df=2, max_features=500, ngram_range=(1, 2)),
                "asr_text",
            )
        )

    return Pipeline(
        [
            ("features", ColumnTransformer(transformers)),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=0,
                    solver="lbfgs",
                ),
            ),
        ]
    )


def grouped_predictions(df: pd.DataFrame, feature_set: str, folds: int) -> np.ndarray:
    groups = df["patient_root"].astype(str).to_numpy()
    y = df["action"].astype(str).to_numpy()
    pred = np.empty(len(df), dtype=object)
    splitter = GroupKFold(n_splits=min(folds, len(np.unique(groups))))
    for train_idx, test_idx in splitter.split(df, y, groups):
        if len(np.unique(y[train_idx])) < 2:
            pred[test_idx] = pd.Series(y[train_idx]).mode().iloc[0]
            continue
        model = build_model(feature_set)
        model.fit(df.iloc[train_idx], y[train_idx])
        pred[test_idx] = model.predict(df.iloc[test_idx])
    return pred


def majority_predictions(df: pd.DataFrame) -> np.ndarray:
    majority = df["action"].mode().iloc[0]
    return np.repeat(majority, len(df))


def low_content_rule(df: pd.DataFrame) -> np.ndarray:
    """Simple deployable rule: low ASR content -> clarify, high content -> preserve."""
    pred = []
    for _, row in df.iterrows():
        if row["asr_concept_count"] <= 1 and row["asr_token_count"] < 8:
            pred.append("clarify")
        elif row["asr_concept_count"] >= 2 and row["asr_token_count"] >= 8:
            pred.append("preserve")
        else:
            pred.append("rewrite")
    return np.asarray(pred, dtype=object)


def metric_rows(y: np.ndarray, pred: np.ndarray, label: str, groups: np.ndarray) -> dict[str, float | str]:
    labels = ["clarify", "preserve", "rewrite"]
    macro = f1_score(y, pred, average="macro", labels=labels, zero_division=0)
    weighted = f1_score(y, pred, average="weighted", labels=labels, zero_division=0)
    boot_mean, boot_lo, boot_hi = bootstrap_ci(
        y,
        pred,
        lambda yt, yp: f1_score(yt, yp, average="macro", labels=labels, zero_division=0),
        groups=groups,
        n_boot=1000,
        seed=0,
    )
    out: dict[str, float | str] = {
        "model": label,
        "n": len(y),
        "macro_f1": macro,
        "macro_f1_boot_mean": boot_mean,
        "macro_f1_ci_low": boot_lo,
        "macro_f1_ci_high": boot_hi,
        "weighted_f1": weighted,
    }
    for action in labels:
        out[f"f1_{action}"] = f1_score(y == action, pred == action, zero_division=0)
        out[f"support_{action}"] = int((y == action).sum())
        out[f"pred_{action}"] = int((pred == action).sum())
    return out


def write_summary(
    out_dir: Path,
    df: pd.DataFrame,
    summary: pd.DataFrame,
    reports: dict[str, pd.DataFrame],
    confusion: pd.DataFrame,
) -> None:
    lines = [
        "# ASR Safety Controller Pilot",
        "",
        f"- Items: {len(df)}",
        f"- Patients: {df['patient_root'].nunique()}",
        f"- Action labels: {json.dumps(df['action'].value_counts().to_dict(), sort_keys=True)}",
        "",
        "## Model Summary",
        "",
        md_table(summary.round(3)),
        "",
        "## Best Deployable Model Report",
        "",
        md_table(reports["asr_text"].round(3)),
        "",
        "## Confusion Matrix, ASR Text Model",
        "",
        md_table(confusion),
        "",
        "## Interpretation",
        "",
        "This is the deployability test for reconstruction control. Labels use "
        "privileged CHAT error/target tags, but the ASR-only models receive only "
        "ASR text, task, and operational clip features. If ASR-only performance is "
        "weak, the system cannot safely decide rewrite/clarify/abstain from ASR "
        "alone and needs clinician confirmation, richer acoustic confidence, or "
        "personalized interaction.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    df = pd.read_csv(args.items_path)
    df["action"] = df["bucket"].map(action_label)
    feature_rows = [
        token_features(text, task)
        for text, task in zip(df["asr_text"].fillna(""), df["task"], strict=False)
    ]
    df = pd.concat([df.reset_index(drop=True), pd.DataFrame(feature_rows)], axis=1)
    if "total_par_audio_seconds" not in df.columns:
        df["total_par_audio_seconds"] = 0.0
    df["total_par_audio_seconds"] = pd.to_numeric(df["total_par_audio_seconds"], errors="coerce")
    df["total_par_audio_seconds"] = df["total_par_audio_seconds"].fillna(0.0)
    df["asr_speech_rate"] = df["asr_token_count"] / df["total_par_audio_seconds"].clip(lower=1)
    for col in [
        "clip_success_rate",
        "total_par_audio_seconds",
        "n_utterance_clips_attempted",
        "n_utterance_clips_transcribed",
        "whisper_clip_segment_count_mean",
        "whisper_avg_logprob_mean",
        "whisper_avg_logprob_min",
        "whisper_no_speech_prob_mean",
        "whisper_no_speech_prob_max",
        "whisper_compression_ratio_mean",
        "whisper_compression_ratio_max",
        "known_reconstructable_error_count",
        "unknown_intent_error_count",
        "error_total",
        "oracle_concept_gain",
        "wab_aq",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = np.nan

    y = df["action"].astype(str).to_numpy()
    groups = df["patient_root"].astype(str).to_numpy()
    predictions = {
        "majority": majority_predictions(df),
        "low_content_rule": low_content_rule(df),
    }
    for feature_set in [
        "asr_operational_no_conf",
        "asr_text_no_conf",
        "asr_operational",
        "asr_text",
        "clinical_upper",
        "privileged_error_oracle",
    ]:
        predictions[feature_set] = grouped_predictions(df, feature_set, args.folds)

    summary = pd.DataFrame(
        [metric_rows(y, pred, label, groups) for label, pred in predictions.items()]
    ).sort_values("macro_f1", ascending=False)
    reports = {}
    pred_rows = []
    for label, pred in predictions.items():
        report = classification_report(
            y,
            pred,
            labels=["clarify", "preserve", "rewrite"],
            output_dict=True,
            zero_division=0,
        )
        reports[label] = pd.DataFrame(report).T.reset_index().rename(columns={"index": "label"})
        for item_id, truth, guess in zip(df["item_id"], y, pred, strict=False):
            pred_rows.append({"model": label, "item_id": item_id, "true_action": truth, "pred_action": guess})

    labels = ["clarify", "preserve", "rewrite"]
    confusion = pd.DataFrame(
        confusion_matrix(y, predictions["asr_text"], labels=labels),
        index=[f"true_{x}" for x in labels],
        columns=[f"pred_{x}" for x in labels],
    ).reset_index(names="truth")

    df.to_csv(out_dir / "controller_items.csv", index=False)
    summary.to_csv(out_dir / "model_summary.csv", index=False)
    pd.DataFrame(pred_rows).to_csv(out_dir / "predictions.csv", index=False)
    confusion.to_csv(out_dir / "confusion_asr_text.csv", index=False)
    for label, report in reports.items():
        report.to_csv(out_dir / f"classification_report_{label}.csv", index=False)
    write_summary(out_dir, df, summary, reports, confusion)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
