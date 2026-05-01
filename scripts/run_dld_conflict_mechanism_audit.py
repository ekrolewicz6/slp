"""Mechanism audit for the highest-value DLD/TD conflict cases.

This script does not publish raw transcript text. It uses the existing
participant-level prediction matrix plus child utterance features to ask what
kind of signal made each conflict case interesting.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


FEATURES = [
    "mlu_words",
    "mlu_morphemes",
    "ndw",
    "verbs_per_utterance",
    "function_word_ratio",
    "utt_len_mean",
    "utt_len_p50",
    "utt_len_p90",
    "single_word_ratio",
    "pos_v_frac",
    "pos_det_frac",
    "rel_SUBJ_frac",
    "rel_OBJ_frac",
    "rel_MOD_frac",
    "mean_dep_distance",
    "pause_per_utt",
    "repetition_per_utt",
    "retracing_per_utt",
    "filler_per_utt",
    "total_words",
    "n_utterances",
    "n_chi_utts_in_window",
]

AXES = {
    "output_complexity": [
        "mlu_words",
        "mlu_morphemes",
        "utt_len_mean",
        "utt_len_p50",
        "utt_len_p90",
        "ndw",
        "verbs_per_utterance",
    ],
    "syntax_argument_structure": [
        "rel_SUBJ_frac",
        "rel_OBJ_frac",
        "rel_MOD_frac",
        "mean_dep_distance",
        "function_word_ratio",
        "pos_det_frac",
    ],
    "lexical_predicate": ["ndw", "verbs_per_utterance", "pos_v_frac"],
    "fluency_repair": ["pause_per_utt", "repetition_per_utt", "retracing_per_utt", "filler_per_utt"],
}

INVERT_FOR_STRENGTH = {"single_word_ratio", "pause_per_utt", "repetition_per_utt", "retracing_per_utt", "filler_per_utt"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--review-cases",
        default="outputs/dld_conflict_review_packet/review_cases.csv",
        type=Path,
    )
    p.add_argument(
        "--clinical-features",
        default="outputs/dld_state_screening/clinical_with_normative_gap.csv",
        type=Path,
    )
    p.add_argument(
        "--predictions",
        default="outputs/dld_label_noise_sensitivity/participant_prediction_matrix.csv",
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/dld_conflict_mechanism_audit", type=Path)
    return p.parse_args()


def robust_scale(values: pd.Series) -> tuple[float, float]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return np.nan, np.nan
    median = float(clean.median())
    q25, q75 = np.percentile(clean, [25, 75])
    scale = float((q75 - q25) / 1.349)
    if not np.isfinite(scale) or scale < 1e-6:
        scale = float(clean.std(ddof=0))
    if not np.isfinite(scale) or scale < 1e-6:
        scale = 1.0
    return median, scale


def participant_feature_table(clinical: pd.DataFrame) -> pd.DataFrame:
    feature_cols = [c for c in FEATURES if c in clinical.columns]
    agg = {
        c: "mean"
        for c in feature_cols
    }
    agg.update(
        {
            "age_months": ["min", "max", "mean"],
            "window_id": "count",
            "transcript_id": pd.Series.nunique,
            "clinical_label": "first",
            "corpus": "first",
        }
    )
    out = clinical.groupby("participant_root").agg(agg)
    out.columns = [
        "_".join(c).rstrip("_") if isinstance(c, tuple) else c
        for c in out.columns.to_flat_index()
    ]
    out = out.rename(columns={f"{c}_mean": c for c in feature_cols})
    out = out.reset_index()
    out = out.rename(
        columns={
            "age_months_min": "age_min_feature",
            "age_months_max": "age_max_feature",
            "age_months_mean": "age_mean_feature",
            "window_id_count": "feature_windows",
            "transcript_id_nunique": "feature_transcripts",
            "clinical_label_first": "feature_clinical_label",
            "corpus_first": "feature_corpus",
        }
    )
    return out


def reference_pool(features: pd.DataFrame, case: pd.Series) -> tuple[pd.DataFrame, str]:
    td = features[features["feature_clinical_label"].eq("TD")].copy()
    age = float(case.get("age_min", np.nan))
    corpus = case.get("corpus")
    candidates = [
        (
            td[td["feature_corpus"].eq(corpus) & td["age_mean_feature"].sub(age).abs().le(6)],
            "same_corpus_td_age_pm6",
        ),
        (
            td[td["feature_corpus"].eq(corpus) & td["age_mean_feature"].sub(age).abs().le(12)],
            "same_corpus_td_age_pm12",
        ),
        (
            td[td["feature_corpus"].eq(corpus) & td["age_mean_feature"].sub(age).abs().le(24)],
            "same_corpus_td_age_pm24",
        ),
        (
            td[td["age_mean_feature"].sub(age).abs().le(12)],
            "all_corpus_td_age_pm12",
        ),
        (
            td[td["age_mean_feature"].sub(age).abs().le(24)],
            "all_corpus_td_age_pm24",
        ),
        (td, "all_td"),
    ]
    for pool, name in candidates:
        if len(pool) >= 8:
            return pool, name
    return td, "all_td_small"


def z_for_case(case_features: pd.Series, pool: pd.DataFrame, feature: str) -> float:
    col = feature
    if col not in pool.columns or col not in case_features.index:
        return np.nan
    median, scale = robust_scale(pool[col])
    value = pd.to_numeric(pd.Series([case_features[col]]), errors="coerce").iloc[0]
    if pd.isna(value) or pd.isna(median) or pd.isna(scale):
        return np.nan
    z = float((value - median) / scale)
    if feature in INVERT_FOR_STRENGTH:
        z = -z
    return z


def axis_score(zs: dict[str, float], axis: str) -> float:
    vals = [zs[f] for f in AXES[axis] if f in zs and np.isfinite(zs[f])]
    return float(np.mean(vals)) if vals else np.nan


def classify_case(row: pd.Series) -> str:
    lang_minus_mlu = row["language_minus_mlu"]
    lang_minus_corpus = row["language_minus_corpus"]
    output = row["output_complexity_z"]
    syntax = row["syntax_argument_structure_z"]
    lexical = row["lexical_predicate_z"]
    sample_low = bool(row["sample_quality_flag"] != "adequate_sample")
    td_labeled = row["screen_label"] == "TD"

    if sample_low and lang_minus_mlu >= 0.20:
        return "sample_constrained_language_risk"
    if td_labeled and lang_minus_corpus >= 0.35 and row["full_language_no_age"] >= 0.75:
        return "possible_hidden_td_language_risk"
    if row["mlu_age"] >= 0.65 and np.isfinite(output) and output <= -0.75:
        return "low_output_mlu_aligned"
    if lang_minus_mlu >= 0.25 and np.nanmin([syntax, lexical, output]) <= -0.50:
        return "non_mlu_language_state_signal"
    if lang_minus_corpus >= 0.35:
        return "language_risk_not_corpus_prior"
    return "mixed_or_borderline_state_conflict"


def top_feature_shifts(zs: dict[str, float], n: int = 5) -> str:
    items = [
        (feature, z)
        for feature, z in zs.items()
        if np.isfinite(z) and feature not in {"total_words", "n_utterances", "n_chi_utts_in_window"}
    ]
    items.sort(key=lambda x: abs(x[1]), reverse=True)
    return "; ".join(f"{feature}:{z:+.2f}" for feature, z in items[:n])


def sample_quality(case_features: pd.Series) -> str:
    utts = case_features.get("n_utterances", np.nan)
    words = case_features.get("total_words", np.nan)
    flags = []
    if pd.notna(utts) and utts < 40:
        flags.append("low_utterance_count")
    if pd.notna(words) and words < 100:
        flags.append("low_word_count")
    return ",".join(flags) if flags else "adequate_sample"


def coverage_flag(case_features: pd.Series) -> str:
    windows = case_features.get("feature_windows", np.nan)
    transcripts = case_features.get("feature_transcripts", np.nan)
    flags = []
    if pd.notna(windows) and windows <= 1:
        flags.append("single_window")
    if pd.notna(transcripts) and transcripts <= 1:
        flags.append("single_transcript")
    return ",".join(flags) if flags else "multi_window_or_longitudinal"


def run_audit(review_cases: pd.DataFrame, clinical: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    features = participant_feature_table(clinical)
    pred_cols = [
        "participant_root",
        "age_only",
        "corpus_age",
        "full_language_age",
        "full_language_no_age",
        "mlu_age",
        "norm_gap_mlu",
        "norm_gap_only",
    ]
    base = review_cases.merge(predictions[pred_cols], on="participant_root", how="left", suffixes=("", "_pred"))
    for col in pred_cols[1:]:
        pred_col = f"{col}_pred"
        if pred_col in base.columns:
            base[col] = base[col].fillna(base[pred_col])
            base = base.drop(columns=[pred_col])
    base = base.merge(features, on="participant_root", how="left")

    rows = []
    feature_cols = [c for c in FEATURES if c in clinical.columns]
    for _, case in base.iterrows():
        pool, pool_name = reference_pool(features, case)
        case_feature_row = case
        zs = {feature: z_for_case(case_feature_row, pool, feature) for feature in feature_cols}
        row = case.to_dict()
        row.update(
            {
                "reference_pool": pool_name,
                "reference_n": len(pool),
                "language_minus_mlu": float(case["full_language_no_age"] - case["mlu_age"]),
                "language_minus_corpus": float(case["full_language_no_age"] - case["corpus_age"]),
                "language_age_adjustment": float(case["full_language_age"] - case["full_language_no_age"]),
                "sample_quality_flag": sample_quality(case),
                "coverage_flag": coverage_flag(case),
                "top_feature_shifts_vs_td": top_feature_shifts(zs),
            }
        )
        for axis in AXES:
            row[f"{axis}_z"] = axis_score(zs, axis)
        row["mechanism_label"] = classify_case(pd.Series(row))
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    review_cases = pd.read_csv(args.review_cases)
    clinical = pd.read_csv(args.clinical_features)
    predictions = pd.read_csv(args.predictions)

    audit = run_audit(review_cases, clinical, predictions)
    mechanism_summary = (
        audit.groupby("mechanism_label")
        .agg(
            n=("participant_root", "count"),
            mean_language_minus_mlu=("language_minus_mlu", "mean"),
            mean_language_minus_corpus=("language_minus_corpus", "mean"),
            mean_output_complexity_z=("output_complexity_z", "mean"),
            mean_syntax_argument_z=("syntax_argument_structure_z", "mean"),
            mean_lexical_predicate_z=("lexical_predicate_z", "mean"),
            sample_flags=("sample_quality_flag", lambda s: "; ".join(sorted(set(s)))),
            coverage_flags=("coverage_flag", lambda s: "; ".join(sorted(set(s)))),
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )
    axis_summary = (
        audit.groupby("review_priority")
        .agg(
            n=("participant_root", "count"),
            mean_language_minus_mlu=("language_minus_mlu", "mean"),
            mean_language_minus_corpus=("language_minus_corpus", "mean"),
            mean_output_complexity_z=("output_complexity_z", "mean"),
            mean_syntax_argument_z=("syntax_argument_structure_z", "mean"),
            mean_lexical_predicate_z=("lexical_predicate_z", "mean"),
            mean_fluency_repair_z=("fluency_repair_z", "mean"),
        )
        .reset_index()
    )

    audit.to_csv(out_dir / "case_mechanism_audit.csv", index=False)
    mechanism_summary.to_csv(out_dir / "mechanism_summary.csv", index=False)
    axis_summary.to_csv(out_dir / "axis_summary.csv", index=False)

    compact_cases = audit[
        [
            "case_id",
            "compact_participant_id",
            "corpus",
            "screen_label",
            "age_min",
            "task_bucket",
            "review_priority",
            "mechanism_label",
            "sample_quality_flag",
            "coverage_flag",
            "language_minus_mlu",
            "language_minus_corpus",
            "output_complexity_z",
            "syntax_argument_structure_z",
            "lexical_predicate_z",
            "top_feature_shifts_vs_td",
        ]
    ].copy()
    round_cols = [
        "age_min",
        "language_minus_mlu",
        "language_minus_corpus",
        "output_complexity_z",
        "syntax_argument_structure_z",
        "lexical_predicate_z",
    ]
    compact_cases[round_cols] = compact_cases[round_cols].round(3)

    lines = [
        "# DLD Conflict Mechanism Audit",
        "",
        "This audit summarizes the 15 DLD/TD conflict review cases without publishing raw transcript text.",
        "",
        f"- Cases audited: {len(audit):,}",
        f"- Adequate-sample cases: {audit['sample_quality_flag'].eq('adequate_sample').sum():,}",
        f"- Single-window/single-transcript cases: {audit['coverage_flag'].str.contains('single_window').sum():,}",
        f"- Cases with language risk at least 0.25 above MLU risk: {audit['language_minus_mlu'].ge(0.25).sum():,}",
        f"- Cases with language risk at least 0.35 above corpus-age risk: {audit['language_minus_corpus'].ge(0.35).sum():,}",
        "",
        "## Mechanism Summary",
        "",
        md_table(mechanism_summary.round(3)),
        "",
        "## Axis Summary By Review Priority",
        "",
        md_table(axis_summary.round(3)),
        "",
        "## Case-Level Mechanism Index",
        "",
        md_table(compact_cases),
        "",
        "## Interpretation",
        "",
        "The highest-value DLD conflicts are mostly not simple MLU-only cases. Several cases have language-only risk far above MLU risk, suggesting that the model is responding to broader output, lexical-predicate, or syntactic/argument-structure patterns. However, some of the youngest natural-conversation cases are sample constrained, so they should be treated as review prompts rather than clinical findings. The next field-facing step is expert transcript review plus paired structured probes, especially sentence and nonword repetition.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
