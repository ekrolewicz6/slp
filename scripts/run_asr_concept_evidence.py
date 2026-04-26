"""Analyze concept-level ASR evidence from saved utterance clips."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from scripts.run_cross_prompt_content import CONCEPTS, chat_tokens, concept_hits  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


CONFIDENCE_FEATURES = [
    "low_logprob_score",
    "whisper_no_speech_prob_mean",
    "whisper_compression_ratio_mean",
    "short_clip_score",
    "asr_empty",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clip-results",
        default="outputs/streaming_asr_clip_evidence_pwa12_tiny/asr_clip_results.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/asr_concept_evidence_pwa12_tiny",
        type=Path,
    )
    return parser.parse_args()


def safe_auc(y: pd.Series, score: pd.Series) -> float:
    y = pd.Series(y).astype(int)
    score = pd.to_numeric(score, errors="coerce")
    mask = y.notna() & score.notna()
    y = y[mask]
    score = score[mask]
    if y.nunique() < 2 or len(y) < 10:
        return float("nan")
    return float(roc_auc_score(y, score))


def build_clip_concept_rows(clips: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, clip in clips.iterrows():
        task = str(clip["task"])
        if task not in CONCEPTS:
            continue
        human_hits = concept_hits(chat_tokens(str(clip.get("human_chat_text", ""))), task)
        asr_text = str(clip.get("asr_text", "") or "")
        asr_hits = concept_hits(chat_tokens(asr_text), task)
        asr_tokens = chat_tokens(asr_text)
        for concept in CONCEPTS[task]:
            human = int(bool(human_hits.get(concept, 0)))
            asr = int(bool(asr_hits.get(concept, 0)))
            rows.append(
                {
                    "transcript_id": clip.get("transcript_id", ""),
                    "participant_id": clip.get("participant_id", ""),
                    "patient_root": clip.get("patient_root", ""),
                    "corpus": clip.get("corpus", ""),
                    "subtype": clip.get("subtype", ""),
                    "wab_aq": clip.get("wab_aq", np.nan),
                    "task": task,
                    "utterance_idx": clip.get("utterance_idx", np.nan),
                    "concept": concept,
                    "human_concept_present": human,
                    "asr_concept_present": asr,
                    "concept_true_positive": int(human and asr),
                    "concept_false_negative": int(human and not asr),
                    "concept_false_positive": int(asr and not human),
                    "concept_true_negative": int(not human and not asr),
                    "clip_success": bool(clip.get("clip_success", False)),
                    "clip_seconds": clip.get("clip_seconds", np.nan),
                    "asr_token_count": len(asr_tokens),
                    "asr_empty": int(len(asr_tokens) == 0),
                    "human_chat_text": clip.get("human_chat_text", ""),
                    "asr_text": asr_text,
                    "whisper_segment_count": clip.get("whisper_segment_count", np.nan),
                    "whisper_avg_logprob_mean": clip.get("whisper_avg_logprob_mean", np.nan),
                    "whisper_avg_logprob_min": clip.get("whisper_avg_logprob_min", np.nan),
                    "whisper_no_speech_prob_mean": clip.get("whisper_no_speech_prob_mean", np.nan),
                    "whisper_no_speech_prob_max": clip.get("whisper_no_speech_prob_max", np.nan),
                    "whisper_compression_ratio_mean": clip.get(
                        "whisper_compression_ratio_mean", np.nan
                    ),
                    "whisper_compression_ratio_max": clip.get(
                        "whisper_compression_ratio_max", np.nan
                    ),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["whisper_avg_logprob_mean"] = pd.to_numeric(
        out["whisper_avg_logprob_mean"], errors="coerce"
    )
    out["low_logprob_score"] = -out["whisper_avg_logprob_mean"]
    out["whisper_no_speech_prob_mean"] = pd.to_numeric(
        out["whisper_no_speech_prob_mean"], errors="coerce"
    )
    out["whisper_compression_ratio_mean"] = pd.to_numeric(
        out["whisper_compression_ratio_mean"], errors="coerce"
    )
    out["clip_seconds"] = pd.to_numeric(out["clip_seconds"], errors="coerce")
    out["short_clip_score"] = -out["clip_seconds"]
    return out


def summarize_errors(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame()
    return (
        rows.groupby(["task"])
        .agg(
            concept_rows=("concept", "size"),
            human_positive=("human_concept_present", "sum"),
            asr_positive=("asr_concept_present", "sum"),
            false_negative=("concept_false_negative", "sum"),
            false_positive=("concept_false_positive", "sum"),
            concept_recall=("concept_true_positive", lambda x: np.nan),
        )
        .reset_index()
        .assign(
            concept_recall=lambda d: (
                (d["human_positive"] - d["false_negative"]) / d["human_positive"].clip(lower=1)
            ),
            concept_precision=lambda d: (
                (d["asr_positive"] - d["false_positive"]) / d["asr_positive"].clip(lower=1)
            ),
        )
    )


def summarize_confidence(rows: pd.DataFrame) -> pd.DataFrame:
    parts = []
    statuses = {
        "true_positive": rows["concept_true_positive"].astype(bool),
        "false_negative": rows["concept_false_negative"].astype(bool),
        "false_positive": rows["concept_false_positive"].astype(bool),
        "true_negative": rows["concept_true_negative"].astype(bool),
    }
    for label, mask in statuses.items():
        group = rows[mask]
        parts.append(
            {
                "status": label,
                "n": len(group),
                "mean_low_logprob_score": group["low_logprob_score"].mean(),
                "mean_no_speech_prob": group["whisper_no_speech_prob_mean"].mean(),
                "mean_compression_ratio": group["whisper_compression_ratio_mean"].mean(),
                "mean_clip_seconds": group["clip_seconds"].mean(),
                "asr_empty_rate": group["asr_empty"].mean(),
            }
        )
    return pd.DataFrame(parts)


def auc_summary(rows: pd.DataFrame) -> pd.DataFrame:
    positives = rows[rows["human_concept_present"].eq(1)].copy()
    negatives = rows[rows["human_concept_present"].eq(0)].copy()
    auc_rows = []
    for feature in CONFIDENCE_FEATURES:
        auc_rows.append(
            {
                "target": "missed_given_human_concept_present",
                "feature": feature,
                "auc": safe_auc(positives["concept_false_negative"], positives[feature]),
                "n": len(positives),
                "positives": int(positives["concept_false_negative"].sum()),
            }
        )
        auc_rows.append(
            {
                "target": "false_positive_given_human_concept_absent",
                "feature": feature,
                "auc": safe_auc(negatives["concept_false_positive"], negatives[feature]),
                "n": len(negatives),
                "positives": int(negatives["concept_false_positive"].sum()),
            }
        )
    return pd.DataFrame(auc_rows)


def threshold_curves(rows: pd.DataFrame) -> pd.DataFrame:
    positives = rows[rows["human_concept_present"].eq(1)].copy()
    curve_rows = []
    for feature in CONFIDENCE_FEATURES:
        score = pd.to_numeric(positives[feature], errors="coerce")
        values = score.dropna().quantile(np.linspace(0.5, 0.95, 10)).drop_duplicates()
        for threshold in values:
            flagged = score >= float(threshold)
            missed = positives["concept_false_negative"].astype(bool)
            curve_rows.append(
                {
                    "feature": feature,
                    "threshold": float(threshold),
                    "flag_rate": float(flagged.mean()),
                    "miss_capture_rate": float((flagged & missed).sum() / max(int(missed.sum()), 1)),
                    "hit_flag_rate": float(
                        (flagged & ~missed).sum() / max(int((~missed).sum()), 1)
                    ),
                    "flag_precision_for_miss": float((flagged & missed).sum() / max(int(flagged.sum()), 1)),
                }
            )
    return pd.DataFrame(curve_rows)


def write_summary(
    out_dir: Path,
    rows: pd.DataFrame,
    errors: pd.DataFrame,
    conf: pd.DataFrame,
    aucs: pd.DataFrame,
    curves: pd.DataFrame,
) -> None:
    best_auc = aucs.sort_values("auc", ascending=False).head(12)
    best_curves = curves.sort_values(
        ["miss_capture_rate", "flag_precision_for_miss", "flag_rate"],
        ascending=[False, False, True],
    ).head(12)
    lines = [
        "# ASR Concept-Level Evidence",
        "",
        f"- Clip-concept rows: {len(rows)}",
        f"- Human-positive concept rows: {int(rows['human_concept_present'].sum()) if len(rows) else 0}",
        f"- ASR-positive concept rows: {int(rows['asr_concept_present'].sum()) if len(rows) else 0}",
        f"- False negatives: {int(rows['concept_false_negative'].sum()) if len(rows) else 0}",
        f"- False positives: {int(rows['concept_false_positive'].sum()) if len(rows) else 0}",
        "",
        "## Error Summary By Task",
        "",
        md_table(errors.round(3)),
        "",
        "## Confidence By Concept Status",
        "",
        md_table(conf.round(3)),
        "",
        "## AUC: Does Confidence Predict Concept Errors?",
        "",
        md_table(best_auc.round(3)),
        "",
        "## Best Miss-Capture Thresholds",
        "",
        md_table(best_curves.round(3)),
        "",
        "## Interpretation",
        "",
        "This analysis is the concept-level version of the Whisper-confidence "
        "experiment. It tests whether utterance confidence can identify when a "
        "specific expected concept was omitted or hallucinated by ASR. Strong AUC "
        "or favorable miss-capture curves would justify concept-level uncertainty "
        "features in the clarification gate; weak curves mean we need richer "
        "evidence such as n-best hypotheses, forced alignment, or phonological "
        "neighbors.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    clips = pd.read_csv(args.clip_results)
    rows = build_clip_concept_rows(clips)
    errors = summarize_errors(rows)
    conf = summarize_confidence(rows)
    aucs = auc_summary(rows)
    curves = threshold_curves(rows)
    rows.to_csv(out_dir / "clip_concept_rows.csv", index=False)
    errors.to_csv(out_dir / "error_summary_by_task.csv", index=False)
    conf.to_csv(out_dir / "confidence_by_status.csv", index=False)
    aucs.to_csv(out_dir / "auc_summary.csv", index=False)
    curves.to_csv(out_dir / "threshold_curves.csv", index=False)
    write_summary(out_dir, rows, errors, conf, aucs, curves)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
