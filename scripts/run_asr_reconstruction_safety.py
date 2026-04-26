"""Score ASR transcripts as inputs to reconstruction/safety controllers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import (  # noqa: E402
    ERROR_RE,
    clean_transcript_text,
    concept_set_from_text,
    extract_target_records,
    negation_count,
    score_candidates,
)
from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asr-results",
        default="outputs/streaming_asr_pilot_pwa60_tiny/asr_task_results.csv",
        type=Path,
    )
    parser.add_argument(
        "--error-segments",
        default="outputs/error_aware_reconstruction/segment_error_features.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/asr_reconstruction_safety_pwa60_tiny",
        type=Path,
    )
    parser.add_argument("--min-clip-success", default=0.0, type=float)
    return parser.parse_args()


def bucket_for(row: pd.Series) -> str:
    if float(row.get("unknown_intent_error_count", 0) or 0) > 0:
        if float(row.get("known_reconstructable_error_count", 0) or 0) > 0:
            return "known_plus_unknown_risk"
        return "unknown_intent"
    if float(row.get("known_reconstructable_error_count", 0) or 0) > 0:
        return "known_target_safe_zone"
    if float(row.get("error_total", 0) or 0) > 0:
        return "other_error"
    if float(row.get("observed_concept_coverage", 0) or 0) > 0:
        return "low_error_content"
    return "low_content_no_error"


def severity_bin(wab: float) -> str:
    if not np.isfinite(wab):
        return "unknown"
    if wab < 50:
        return "severe_lt50"
    if wab < 75:
        return "moderate_50_75"
    if wab < 93.8:
        return "mild_75_93_8"
    return "very_mild_or_notaphasic_ge93_8"


def md_table(frame: pd.DataFrame, max_rows: int = 60) -> str:
    if frame.empty:
        return ""
    data = frame.head(max_rows).copy()
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else str(x))
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(row.tolist()) + " |" for _, row in data.iterrows()]
    return "\n".join([header, sep] + body)


def build_items(merged: pd.DataFrame) -> pd.DataFrame:
    confidence_cols = [
        "whisper_clip_segment_count_mean",
        "whisper_avg_logprob_mean",
        "whisper_avg_logprob_min",
        "whisper_no_speech_prob_mean",
        "whisper_no_speech_prob_max",
        "whisper_compression_ratio_mean",
        "whisper_compression_ratio_max",
        "total_par_audio_seconds",
        "n_utterance_clips_attempted",
        "n_utterance_clips_transcribed",
    ]
    rows = []
    for idx, row in merged.reset_index(drop=True).iterrows():
        raw_text = str(row.get("raw_task_text", "") or "")
        task = str(row["task"])
        observed = concept_set_from_text(raw_text, task, include_targets=False)
        oracle = concept_set_from_text(raw_text, task, include_targets=True)
        target_records = extract_target_records(raw_text)
        known_targets = sorted(
            {
                rec["target"].lower()
                for rec in target_records
                if rec["target_status"] == "known"
            }
        )
        unknown_codes = sorted(
            rec["error_code"] for rec in target_records if rec["target_status"] == "unknown"
        )
        rows.append(
            {
                "item_id": f"asr_{idx + 1:04d}",
                "bucket": bucket_for(row),
                "task": task,
                "subtype": row.get("subtype", ""),
                "wab_aq": row.get("wab_aq", np.nan),
                "severity_bin": severity_bin(float(row.get("wab_aq", np.nan))),
                "participant_id": row.get("participant_id", ""),
                "patient_root": row.get("patient_root", ""),
                "corpus": row.get("corpus", ""),
                "file_path": row.get("file_path", ""),
                "transcript_id": row.get("transcript_id", ""),
                "raw_transcript": raw_text,
                "raw_clean_text": clean_transcript_text(raw_text, include_targets=False),
                "oracle_clean_text": clean_transcript_text(raw_text, include_targets=True),
                "asr_text": str(row.get("asr_text", "") or ""),
                "observed_concepts": json.dumps(sorted(observed)),
                "oracle_concepts": json.dumps(sorted(oracle)),
                "known_targets": json.dumps(known_targets),
                "unknown_target_error_codes": json.dumps(unknown_codes),
                "all_error_codes": json.dumps(sorted(ERROR_RE.findall(raw_text))),
                "observed_concept_count": len(observed),
                "oracle_concept_count": len(oracle),
                "oracle_concept_gain": int(len(oracle - observed)),
                "error_total": row.get("error_total", 0),
                "paper_bottleneck_error_rate_100": row.get("paper_bottleneck_error_rate_100", 0),
                "known_reconstructable_error_count": row.get("known_reconstructable_error_count", 0),
                "unknown_intent_error_count": row.get("unknown_intent_error_count", 0),
                "raw_negation_count": negation_count(raw_text),
                "clip_success_rate": row.get("clip_success_rate", np.nan),
                "asr_concept_f1_vs_human": row.get("concept_f1_vs_human", np.nan),
                "asr_concept_recall_vs_human": row.get("concept_recall_vs_human", np.nan),
                "asr_concept_precision_vs_human": row.get("concept_precision_vs_human", np.nan),
                "asr_human_false_positive": row.get("concept_false_positive", np.nan),
                "asr_human_false_negative": row.get("concept_false_negative", np.nan),
                **{col: row.get(col, np.nan) for col in confidence_cols},
            }
        )
    return pd.DataFrame(rows)


def candidate_frame(items: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family, col in {
        "human_raw_chat": "raw_clean_text",
        "human_oracle_targets": "oracle_clean_text",
        "asr_par_text": "asr_text",
    }.items():
        rows.append(
            items[["item_id", col]]
            .rename(columns={col: "reconstruction"})
            .assign(candidate_family=family)
        )
    return pd.concat(rows, ignore_index=True)


def score_all_candidates(items: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    parts = []
    meta_cols = [
        "item_id",
        "transcript_id",
        "bucket",
        "severity_bin",
        "task",
        "subtype",
        "corpus",
        "patient_root",
        "clip_success_rate",
        "asr_concept_f1_vs_human",
        "asr_concept_recall_vs_human",
        "asr_concept_precision_vs_human",
        "asr_human_false_positive",
        "asr_human_false_negative",
    ]
    meta = items[meta_cols].copy()
    for family, group in candidates.groupby("candidate_family"):
        scored, _ = score_candidates(items, group[["item_id", "reconstruction"]])
        scored["candidate_family"] = family
        scored = scored.drop(columns=[c for c in ["bucket", "task", "subtype"] if c in scored.columns])
        scored = scored.merge(meta, on="item_id", how="left")
        parts.append(scored)
    return pd.concat(parts, ignore_index=True)


def summarize(scored: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    return (
        scored.groupby(group_cols)
        .agg(
            n=("item_id", "size"),
            patients=("patient_root", "nunique"),
            mean_wab=("wab_aq", "mean"),
            output_concepts=("output_concept_count", "mean"),
            concept_recovery=("concept_recovery_rate", "mean"),
            concept_overreach=("concept_overreach_count", "mean"),
            observed_loss=("observed_concept_loss_count", "mean"),
            known_target_token_recovery=("known_target_token_recovery_rate", "mean"),
            unknown_intent_added=("unknown_intent_added_concept_count", "mean"),
            negation_flip=("negation_flip_flag", "mean"),
            asr_f1_vs_human=("asr_concept_f1_vs_human", "mean"),
            asr_recall_vs_human=("asr_concept_recall_vs_human", "mean"),
            asr_precision_vs_human=("asr_concept_precision_vs_human", "mean"),
        )
        .reset_index()
    )


def overall_summary(scored: pd.DataFrame) -> pd.DataFrame:
    summary = summarize(scored, ["candidate_family"])
    corr_rows = []
    for family, group in scored.groupby("candidate_family"):
        corr_rows.append(
            {
                "candidate_family": family,
                "r_output_concepts_wab": pearson_safe(group["output_concept_count"], group["wab_aq"]),
                "r_overreach_wab": pearson_safe(group["concept_overreach_count"], group["wab_aq"]),
                "r_observed_loss_wab": pearson_safe(group["observed_concept_loss_count"], group["wab_aq"]),
            }
        )
    return summary.merge(pd.DataFrame(corr_rows), on="candidate_family", how="left")


def compare_asr_to_raw(scored: pd.DataFrame) -> pd.DataFrame:
    wide = scored.pivot_table(
        index="item_id",
        columns="candidate_family",
        values=[
            "output_concept_count",
            "concept_overreach_count",
            "observed_concept_loss_count",
            "unknown_intent_added_concept_count",
            "negation_flip_flag",
        ],
        aggfunc="first",
    )
    wide.columns = [f"{metric}__{family}" for metric, family in wide.columns]
    out = wide.reset_index()
    for metric in [
        "output_concept_count",
        "concept_overreach_count",
        "observed_concept_loss_count",
        "unknown_intent_added_concept_count",
        "negation_flip_flag",
    ]:
        out[f"delta_{metric}_asr_minus_raw"] = (
            out[f"{metric}__asr_par_text"] - out[f"{metric}__human_raw_chat"]
        )
    return out


def write_summary(
    out_dir: Path,
    items: pd.DataFrame,
    overall: pd.DataFrame,
    by_bucket: pd.DataFrame,
    by_subtype: pd.DataFrame,
    by_task: pd.DataFrame,
    by_severity: pd.DataFrame,
    deltas: pd.DataFrame,
) -> None:
    asr = overall[overall["candidate_family"].eq("asr_par_text")].iloc[0]
    raw = overall[overall["candidate_family"].eq("human_raw_chat")].iloc[0]
    delta_means = deltas.filter(like="delta_").mean(numeric_only=True).to_dict()
    lines = [
        "# ASR Reconstruction Safety",
        "",
        f"- Items/task rows: {len(items)}",
        f"- Patients: {items['patient_root'].nunique()}",
        f"- Mean ASR F1 vs human concepts: {items['asr_concept_f1_vs_human'].mean():.3f}",
        f"- Mean ASR recall vs human concepts: {items['asr_concept_recall_vs_human'].mean():.3f}",
        f"- Mean ASR precision vs human concepts: {items['asr_concept_precision_vs_human'].mean():.3f}",
        "",
        "## Headline Safety Readout",
        "",
        f"- ASR observed-concept loss/item: {asr['observed_loss']:.3f} "
        f"(human raw: {raw['observed_loss']:.3f})",
        f"- ASR concept overreach/item: {asr['concept_overreach']:.3f} "
        f"(human raw: {raw['concept_overreach']:.3f})",
        f"- ASR unknown-intent added concepts/item: {asr['unknown_intent_added']:.3f} "
        f"(human raw: {raw['unknown_intent_added']:.3f})",
        f"- ASR negation flip rate: {asr['negation_flip']:.3f} "
        f"(human raw: {raw['negation_flip']:.3f})",
        f"- Mean ASR minus raw observed-loss delta: "
        f"{delta_means.get('delta_observed_concept_loss_count_asr_minus_raw', float('nan')):.3f}",
        f"- Mean ASR minus raw overreach delta: "
        f"{delta_means.get('delta_concept_overreach_count_asr_minus_raw', float('nan')):.3f}",
        "",
        "## Overall Candidate Comparison",
        "",
        md_table(overall.round(3)),
        "",
        "## By Safety Bucket",
        "",
        md_table(by_bucket.round(3), 80),
        "",
        "## ASR Candidate By Subtype",
        "",
        md_table(by_subtype[by_subtype["candidate_family"].eq("asr_par_text")].round(3), 40),
        "",
        "## ASR Candidate By Task",
        "",
        md_table(by_task[by_task["candidate_family"].eq("asr_par_text")].round(3), 40),
        "",
        "## ASR Candidate By Severity",
        "",
        md_table(by_severity[by_severity["candidate_family"].eq("asr_par_text")].round(3), 40),
        "",
        "## Interpretation",
        "",
        "This experiment treats ASR text as the substrate a downstream LLM or "
        "clinical controller would receive. The key distinction is whether ASR "
        "mainly loses observed human concepts, which is conservative but "
        "incomplete, or adds concepts/negation/unknown-intent content, which is "
        "unsafe for communication support. A safe product should use raw human/ASR "
        "speech for assessment, and only reconstruct when a controller can prove "
        "intent evidence is strong enough.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    asr = pd.read_csv(args.asr_results)
    errors = pd.read_csv(args.error_segments)
    asr["clip_success_rate"] = (
        pd.to_numeric(asr["n_utterance_clips_transcribed"], errors="coerce")
        / pd.to_numeric(asr["n_utterance_clips_attempted"], errors="coerce").clip(lower=1)
    )
    if args.min_clip_success > 0:
        asr = asr[asr["clip_success_rate"] >= args.min_clip_success].copy()
    merge_cols = ["transcript_id", "task"]
    merged = asr.merge(
        errors,
        on=merge_cols,
        how="inner",
        suffixes=("", "_segment"),
    )
    if merged.empty:
        raise SystemExit("No ASR rows matched error-aware segment rows.")
    for col in ["subtype", "wab_aq", "participant_id", "patient_root", "corpus", "file_path"]:
        seg_col = f"{col}_segment"
        if seg_col in merged.columns:
            merged[col] = merged[col].where(merged[col].notna(), merged[seg_col])
    items = build_items(merged)
    candidates = candidate_frame(items)
    scored = score_all_candidates(items, candidates)
    overall = overall_summary(scored)
    by_bucket = summarize(scored, ["candidate_family", "bucket"])
    by_subtype = summarize(scored, ["candidate_family", "subtype"])
    by_task = summarize(scored, ["candidate_family", "task"])
    by_severity = summarize(scored, ["candidate_family", "severity_bin"])
    deltas = compare_asr_to_raw(scored)

    items.to_csv(out_dir / "asr_safety_items.csv", index=False)
    candidates.to_csv(out_dir / "asr_safety_candidates.csv", index=False)
    scored.to_csv(out_dir / "asr_safety_scores.csv", index=False)
    overall.to_csv(out_dir / "overall_candidate_summary.csv", index=False)
    by_bucket.to_csv(out_dir / "by_bucket.csv", index=False)
    by_subtype.to_csv(out_dir / "by_subtype.csv", index=False)
    by_task.to_csv(out_dir / "by_task.csv", index=False)
    by_severity.to_csv(out_dir / "by_severity.csv", index=False)
    deltas.to_csv(out_dir / "asr_minus_raw_deltas.csv", index=False)
    write_summary(out_dir, items, overall, by_bucket, by_subtype, by_task, by_severity, deltas)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
