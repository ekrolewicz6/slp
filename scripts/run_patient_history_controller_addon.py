"""Test whether prior patient/session history improves open-ended controller decisions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from scripts.run_cross_prompt_longitudinal import longitudinal_root, session_order_value  # noqa: E402
from scripts.run_open_ended_selective_controller import (  # noqa: E402
    LABELS,
    balanced_challenge,
    majority_predictions,
    metric_row,
    natural_screening_sample,
    prepare,
)
from src.analysis.review_grade import ensure_dir  # noqa: E402


BASE_NUMERIC = [
    "utt_tokens",
    "utt_type_token_ratio",
    "utt_mean_token_len",
    "utt_repetition_rate",
    "utt_filler_rate",
    "utt_negation_count",
    "utt_short_flag",
]

HISTORY_NUMERIC = [
    "has_history",
    "hist_n_open_ended_utterances",
    "hist_preserve_rate",
    "hist_rewrite_rate",
    "hist_clarify_rate",
    "hist_error_rate_100",
    "hist_known_reconstructable_rate_100",
    "hist_unknown_intent_rate_100",
    "hist_mean_tokens",
    "hist_mean_filler_rate",
    "hist_content_axis",
    "hist_risk_axis",
    "hist_recoverable_axis",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--utterances-path",
        default="outputs/open_ended_reconstruction_audit/open_ended_utterances.csv",
        type=Path,
    )
    parser.add_argument(
        "--state",
        default="outputs/two_axis_state_typology/session_two_axis_state.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/patient_history_controller", type=Path)
    parser.add_argument("--folds", default=5, type=int)
    parser.add_argument("--seed", default=0, type=int)
    parser.add_argument("--natural-preserve-n", default=12000, type=int)
    parser.add_argument("--balanced-preserve-n", default=3094, type=int)
    return parser.parse_args()


def add_history_features(df: pd.DataFrame, state: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["longitudinal_root"] = out["participant_id"].map(longitudinal_root)
    out["session_order"] = [
        session_order_value(pid, None) for pid in out["participant_id"].astype(str)
    ]

    action_wide = (
        out.pivot_table(
            index="participant_id",
            columns="action",
            values="utterance_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for label in LABELS:
        if label not in action_wide:
            action_wide[label] = 0
    action_wide["hist_n_open_ended_utterances"] = action_wide[LABELS].sum(axis=1)
    for label in LABELS:
        action_wide[f"hist_{label}_rate"] = action_wide[label] / action_wide[
            "hist_n_open_ended_utterances"
        ].clip(lower=1)

    session = (
        out.groupby("participant_id")
        .agg(
            longitudinal_root=("longitudinal_root", "first"),
            session_order=("session_order", "first"),
            hist_error_rate_100=("error_rate_100", "mean"),
            hist_known_reconstructable_rate_100=("known_reconstructable_error_rate_100", "mean"),
            hist_unknown_intent_rate_100=("unknown_intent_error_rate_100", "mean"),
            hist_mean_tokens=("utt_tokens", "mean"),
            hist_mean_filler_rate=("utt_filler_rate", "mean"),
        )
        .reset_index()
        .merge(
            action_wide[
                [
                    "participant_id",
                    "hist_n_open_ended_utterances",
                    "hist_preserve_rate",
                    "hist_rewrite_rate",
                    "hist_clarify_rate",
                ]
            ],
            on="participant_id",
            how="left",
        )
    )
    if not state.empty:
        state_cols = [
            "participant_id",
            "content_axis",
            "risk_axis",
            "recoverable_axis",
        ]
        session = session.merge(state[state_cols], on="participant_id", how="left")
        session = session.rename(
            columns={
                "content_axis": "hist_content_axis",
                "risk_axis": "hist_risk_axis",
                "recoverable_axis": "hist_recoverable_axis",
            }
        )
    else:
        session["hist_content_axis"] = np.nan
        session["hist_risk_axis"] = np.nan
        session["hist_recoverable_axis"] = np.nan

    session = session.sort_values(["longitudinal_root", "session_order", "participant_id"])
    hist_cols = [c for c in session.columns if c.startswith("hist_")]
    prev = session[["participant_id", "longitudinal_root"]].copy()
    shifted = session.groupby("longitudinal_root")[hist_cols].shift(1)
    shifted.columns = [f"prev_{c}" for c in shifted.columns]
    prev = pd.concat([prev, shifted], axis=1)
    prev["has_history"] = prev[f"prev_{hist_cols[0]}"].notna().astype(float) if hist_cols else 0.0
    prev = prev.rename(columns={f"prev_{c}": c for c in hist_cols})

    out = out.merge(prev.drop(columns=["longitudinal_root"]), on="participant_id", how="left")
    out["has_history"] = out["has_history"].fillna(0.0)
    for col in HISTORY_NUMERIC:
        if col not in out:
            out[col] = np.nan
    return out


def build_model(feature_set: str) -> Pipeline:
    numeric = list(BASE_NUMERIC)
    categorical: list[str] = []
    text_col = "context_text"
    if feature_set == "history_only":
        numeric = list(HISTORY_NUMERIC)
        text_col = "observed_clean_text"
    elif feature_set == "context_plus_history":
        numeric.extend(HISTORY_NUMERIC)
    elif feature_set == "context_plus_current_clinical":
        numeric.append("wab_aq")
        categorical.append("subtype")
    elif feature_set == "context_plus_history_current":
        numeric.extend(HISTORY_NUMERIC)
        numeric.append("wab_aq")
        categorical.append("subtype")
    elif feature_set == "context_text":
        pass
    else:
        raise ValueError(f"unknown feature set: {feature_set}")

    transformers = [
        (
            "num",
            Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]),
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
    groups = df["longitudinal_root"].astype(str).to_numpy()
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


def run_dataset(df: pd.DataFrame, dataset_name: str, folds: int, out_dir: Path) -> tuple[list[dict], pd.DataFrame]:
    feature_sets = [
        "majority",
        "context_text",
        "history_only",
        "context_plus_history",
        "context_plus_current_clinical",
        "context_plus_history_current",
    ]
    rows = []
    pred_parts = []
    for feature_set in feature_sets:
        if feature_set == "majority":
            pred = majority_predictions(df)
        else:
            pred = grouped_predictions(df, feature_set, folds)
        rows.append(metric_row(df, pred, feature_set, dataset_name))
        pred_parts.append(
            pd.DataFrame(
                {
                    "dataset": dataset_name,
                    "utterance_id": df["utterance_id"].to_numpy(),
                    "participant_id": df["participant_id"].to_numpy(),
                    "longitudinal_root": df["longitudinal_root"].to_numpy(),
                    "truth": df["action"].to_numpy(),
                    "model": feature_set,
                    "pred": pred,
                    "has_history": df["has_history"].to_numpy(),
                }
            )
        )
        report = classification_report(
            df["action"].astype(str),
            pred,
            labels=LABELS,
            output_dict=True,
            zero_division=0,
        )
        pd.DataFrame(report).transpose().to_csv(
            out_dir / f"classification_report_{dataset_name}__{feature_set}.csv"
        )
        pd.DataFrame(
            confusion_matrix(df["action"].astype(str), pred, labels=LABELS),
            index=LABELS,
            columns=LABELS,
        ).to_csv(out_dir / f"confusion_{dataset_name}__{feature_set}.csv")
    return rows, pd.concat(pred_parts, ignore_index=True)


def write_summary(out_dir: Path, summary: pd.DataFrame, datasets: dict[str, pd.DataFrame]) -> None:
    lines = [
        "# Patient-History Controller Add-On",
        "",
        "Dataset sizes:",
        "",
        md_table(
            pd.DataFrame(
                [
                    {
                        "dataset": name,
                        "n": len(df),
                        "patients": df["patient_root"].nunique(),
                        "longitudinal_roots": df["longitudinal_root"].nunique(),
                        "has_history_rate": df["has_history"].mean(),
                        "clarify": int((df["action"] == "clarify").sum()),
                        "rewrite": int((df["action"] == "rewrite").sum()),
                        "preserve": int((df["action"] == "preserve").sum()),
                    }
                    for name, df in datasets.items()
                ]
            ).round(3)
        ),
        "",
        "Model results:",
        "",
        md_table(summary.round(3)),
        "",
        "## Synthesis",
        "",
        "- Prior-session history is a plausible safety signal only if it improves clarify/rewrite decisions under root-held-out evaluation.",
        "- If history helps mostly on rows with previous sessions, it supports patient-specific controller calibration; if not, the bottleneck remains utterance-level intent evidence.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    state = pd.read_csv(args.state) if args.state.exists() else pd.DataFrame()
    df = prepare(args.utterances_path, min_tokens=1)
    df = add_history_features(df, state)

    natural = natural_screening_sample(df, args.natural_preserve_n, args.seed)
    balanced = balanced_challenge(df, args.balanced_preserve_n, args.seed)
    history_balanced = balanced_challenge(
        df[df["has_history"].eq(1.0)].copy(),
        min(args.balanced_preserve_n, int((df["has_history"].eq(1.0) & df["action"].eq("preserve")).sum())),
        args.seed,
    )
    datasets = {
        "natural_screening": natural,
        "balanced_challenge": balanced,
        "history_only_balanced": history_balanced,
    }
    all_rows = []
    pred_frames = []
    for name, data in datasets.items():
        rows, preds = run_dataset(data, name, args.folds, out_dir)
        all_rows.extend(rows)
        pred_frames.append(preds)

    summary = pd.DataFrame(all_rows).sort_values(["dataset", "macro_f1"], ascending=[True, False])
    predictions = pd.concat(pred_frames, ignore_index=True)
    df.to_csv(out_dir / "controller_utterances_with_history.csv", index=False)
    summary.to_csv(out_dir / "model_summary.csv", index=False)
    predictions.to_csv(out_dir / "predictions.csv", index=False)
    write_summary(out_dir, summary, datasets)
    print(f"Wrote patient-history controller add-on to {out_dir}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
