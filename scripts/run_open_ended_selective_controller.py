"""Open-ended rewrite/clarify/preserve controller benchmark.

This uses natural AphasiaBank interview utterances from the open-ended audit.
Labels are derived from CHAT target/error annotations, but deployable models
only see cleaned utterance text and optional neighboring context.
"""

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
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table, negation_count  # noqa: E402
from scripts.run_cross_prompt_content import chat_tokens  # noqa: E402
from src.analysis.review_grade import bootstrap_ci, ensure_dir  # noqa: E402


FILLERS = {"um", "uh", "hm", "hmm", "oh", "ah", "er", "erm"}
LABELS = ["clarify", "preserve", "rewrite"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--utterances-path",
        default="outputs/open_ended_reconstruction_audit/open_ended_utterances.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/open_ended_selective_controller",
        type=Path,
    )
    parser.add_argument("--folds", default=5, type=int)
    parser.add_argument("--seed", default=0, type=int)
    parser.add_argument("--min-tokens", default=1, type=int)
    parser.add_argument(
        "--balanced-preserve-n",
        default=3094,
        type=int,
        help="Number of preserve rows to keep in the balanced challenge set.",
    )
    parser.add_argument(
        "--natural-preserve-n",
        default=12000,
        type=int,
        help="Keep all rare rows plus this many preserve rows for natural-distribution CV.",
    )
    return parser.parse_args()


def action_label(row: pd.Series) -> str:
    if bool(row.get("needs_abstain_or_clarification", False)):
        return "clarify"
    if bool(row.get("safe_known_rewrite_candidate", False)):
        return "rewrite"
    return "preserve"


def add_context(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values(["transcript_id", "utterance_index"]).copy()
    out["prev_text"] = out.groupby("transcript_id")["observed_clean_text"].shift(1).fillna("")
    out["next_text"] = out.groupby("transcript_id")["observed_clean_text"].shift(-1).fillna("")
    out["context_text"] = (
        out["prev_text"].astype(str)
        + " [SEP] "
        + out["observed_clean_text"].astype(str)
        + " [SEP] "
        + out["next_text"].astype(str)
    )
    return out.sort_index()


def token_features(text: str) -> dict[str, float]:
    toks = chat_tokens(str(text), include_targets=False)
    n = len(toks)
    unique = len(set(toks))
    alpha_lens = [len(re.sub(r"[^a-z]", "", tok)) for tok in toks]
    repeated = sum(1 for a, b in zip(toks, toks[1:], strict=False) if a == b)
    filler = sum(1 for tok in toks if tok in FILLERS)
    return {
        "utt_tokens": float(n),
        "utt_type_token_ratio": unique / max(n, 1),
        "utt_mean_token_len": float(np.mean(alpha_lens)) if alpha_lens else 0.0,
        "utt_repetition_rate": repeated / max(n - 1, 1),
        "utt_filler_rate": filler / max(n, 1),
        "utt_negation_count": float(negation_count(text)),
        "utt_short_flag": float(n <= 2),
    }


def prepare(path: Path, min_tokens: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["action"] = df.apply(action_label, axis=1)
    df["observed_clean_text"] = df["observed_clean_text"].fillna("").astype(str)
    df = df[pd.to_numeric(df["observed_n_tokens"], errors="coerce").fillna(0) >= min_tokens].copy()
    df = add_context(df)
    feats = pd.DataFrame([token_features(x) for x in df["observed_clean_text"]], index=df.index)
    df = pd.concat([df, feats], axis=1)
    for col in [
        "known_reconstructable_error_count",
        "unknown_intent_error_count",
        "error_total",
        "paper_bottleneck_error_rate_100",
        "target_token_gain",
        "wab_aq",
    ]:
        df[col] = pd.to_numeric(df.get(col), errors="coerce")
    return df.reset_index(drop=True)


def balanced_challenge(df: pd.DataFrame, preserve_n: int, seed: int) -> pd.DataFrame:
    parts = []
    for action, group in df.groupby("action"):
        if action == "preserve" and len(group) > preserve_n:
            group = group.sample(n=preserve_n, random_state=seed)
        parts.append(group)
    return pd.concat(parts, ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)


def natural_screening_sample(df: pd.DataFrame, preserve_n: int, seed: int) -> pd.DataFrame:
    rare = df[df["action"].ne("preserve")]
    preserve = df[df["action"].eq("preserve")]
    if len(preserve) > preserve_n:
        preserve = preserve.sample(n=preserve_n, random_state=seed)
    return pd.concat([rare, preserve], ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)


def build_model(feature_set: str) -> Pipeline:
    numeric = [
        "utt_tokens",
        "utt_type_token_ratio",
        "utt_mean_token_len",
        "utt_repetition_rate",
        "utt_filler_rate",
        "utt_negation_count",
        "utt_short_flag",
    ]
    categorical: list[str] = []
    text_col = "observed_clean_text"

    if feature_set == "context_text":
        text_col = "context_text"
    if feature_set == "clinical_context":
        text_col = "context_text"
        numeric.append("wab_aq")
        categorical.extend(["subtype"])
    if feature_set == "privileged_error_oracle":
        numeric.extend(
            [
                "known_reconstructable_error_count",
                "unknown_intent_error_count",
                "error_total",
                "paper_bottleneck_error_rate_100",
                "target_token_gain",
            ]
        )

    transformers = [
        (
            "num",
            Pipeline(
                [
                    ("impute", SimpleImputer(strategy="median")),
                    ("scale", StandardScaler()),
                ]
            ),
            numeric,
        ),
        (
            "text",
            TfidfVectorizer(min_df=3, max_features=1500, ngram_range=(1, 2)),
            text_col,
        ),
    ]
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore"), categorical))

    return Pipeline(
        [
            ("features", ColumnTransformer(transformers)),
            (
                "clf",
                SGDClassifier(
                    loss="log_loss",
                    max_iter=1000,
                    tol=1e-3,
                    class_weight="balanced",
                    random_state=0,
                ),
            ),
        ]
    )


def grouped_predictions(df: pd.DataFrame, feature_set: str, folds: int) -> np.ndarray:
    y = df["action"].astype(str).to_numpy()
    groups = df["patient_root"].astype(str).to_numpy()
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
    return np.repeat(df["action"].mode().iloc[0], len(df))


def metric_row(df: pd.DataFrame, pred: np.ndarray, model: str, dataset: str) -> dict[str, float | str]:
    y = df["action"].astype(str).to_numpy()
    groups = df["patient_root"].astype(str).to_numpy()
    macro = f1_score(y, pred, labels=LABELS, average="macro", zero_division=0)
    weighted = f1_score(y, pred, labels=LABELS, average="weighted", zero_division=0)
    boot_mean, lo, hi = bootstrap_ci(
        y,
        pred,
        lambda yt, yp: f1_score(yt, yp, labels=LABELS, average="macro", zero_division=0),
        groups=groups,
        n_boot=200,
        seed=0,
    )
    out: dict[str, float | str] = {
        "dataset": dataset,
        "model": model,
        "n": len(df),
        "patients": int(df["patient_root"].nunique()),
        "macro_f1": macro,
        "macro_f1_boot_mean": boot_mean,
        "macro_f1_ci_low": lo,
        "macro_f1_ci_high": hi,
        "weighted_f1": weighted,
    }
    for label in LABELS:
        out[f"f1_{label}"] = f1_score(y == label, pred == label, zero_division=0)
        out[f"support_{label}"] = int((y == label).sum())
        out[f"pred_{label}"] = int((pred == label).sum())
    return out


def evaluate_dataset(df: pd.DataFrame, dataset: str, folds: int) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    predictions = {"majority": majority_predictions(df)}
    for feature_set in ["text_only", "context_text", "clinical_context", "privileged_error_oracle"]:
        print(f"[open-ended-controller] {dataset}: fitting {feature_set}", file=sys.stderr, flush=True)
        predictions[feature_set] = grouped_predictions(df, feature_set, folds)

    rows = [metric_row(df, pred, model, dataset) for model, pred in predictions.items()]
    pred_rows = []
    reports = {}
    y = df["action"].astype(str).to_numpy()
    for model, pred in predictions.items():
        report = classification_report(
            y,
            pred,
            labels=LABELS,
            output_dict=True,
            zero_division=0,
        )
        reports[f"{dataset}__{model}"] = pd.DataFrame(report).T.reset_index(names="label")
        for item_id, truth, guess in zip(df["utterance_id"], y, pred, strict=False):
            pred_rows.append(
                {
                    "dataset": dataset,
                    "model": model,
                    "utterance_id": item_id,
                    "true_action": truth,
                    "pred_action": guess,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(pred_rows), reports


def write_summary(out_dir: Path, df: pd.DataFrame, summary: pd.DataFrame) -> None:
    action_counts = df["action"].value_counts().to_dict()
    best = summary.sort_values(["dataset", "macro_f1"], ascending=[True, False])
    lines = [
        "# Open-Ended Selective Controller",
        "",
        f"- Utterances: {len(df)}",
        f"- Patients: {df['patient_root'].nunique()}",
        f"- Action labels: {json.dumps(action_counts, sort_keys=True)}",
        "",
        "## Model Results",
        "",
        md_table(best.round(3)),
        "",
        "## Interpretation",
        "",
        "This is the natural-conversation version of the rewrite/clarify/preserve "
        "problem. Labels come from CHAT error/target tags. Deployable text models "
        "do not see those tags; the privileged oracle does. If text/context models "
        "fail while the oracle succeeds, the open-ended control problem is real but "
        "requires better evidence than cleaned transcript text.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    full = prepare(args.utterances_path, args.min_tokens)
    natural = natural_screening_sample(full, args.natural_preserve_n, args.seed)
    balanced = balanced_challenge(full, args.balanced_preserve_n, args.seed)

    summaries = []
    pred_parts = []
    all_reports: dict[str, pd.DataFrame] = {}
    for name, dataset in [("natural_screening", natural), ("balanced_challenge", balanced)]:
        summary, preds, reports = evaluate_dataset(dataset, name, args.folds)
        summaries.append(summary)
        pred_parts.append(preds)
        all_reports.update(reports)

    summary_df = pd.concat(summaries, ignore_index=True)
    preds_df = pd.concat(pred_parts, ignore_index=True)
    full.to_csv(out_dir / "controller_utterances.csv", index=False)
    natural.to_csv(out_dir / "natural_screening_utterances.csv", index=False)
    balanced.to_csv(out_dir / "balanced_challenge_utterances.csv", index=False)
    summary_df.to_csv(out_dir / "model_summary.csv", index=False)
    preds_df.to_csv(out_dir / "predictions.csv", index=False)
    for name, report in all_reports.items():
        report.to_csv(out_dir / f"classification_report_{name}.csv", index=False)

    for dataset in ["natural_screening", "balanced_challenge"]:
        for model in ["context_text", "privileged_error_oracle"]:
            pred = preds_df[preds_df["dataset"].eq(dataset) & preds_df["model"].eq(model)]
            if pred.empty:
                continue
            cm = confusion_matrix(pred["true_action"], pred["pred_action"], labels=LABELS)
            pd.DataFrame(
                cm,
                index=[f"true_{x}" for x in LABELS],
                columns=[f"pred_{x}" for x in LABELS],
            ).reset_index(names="truth").to_csv(
                out_dir / f"confusion_{dataset}_{model}.csv",
                index=False,
            )

    write_summary(out_dir, full, summary_df)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
