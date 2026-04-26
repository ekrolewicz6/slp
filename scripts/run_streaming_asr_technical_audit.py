"""Audit stream/session and clip-level technical failures in ASR runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asr-results",
        default="outputs/streaming_asr_pilot_pwa60_tiny/asr_task_results.csv",
        type=Path,
    )
    parser.add_argument(
        "--selected-sessions",
        default="outputs/streaming_asr_pilot_pwa60_tiny/selected_sessions.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/streaming_asr_technical_audit_pwa60_tiny",
        type=Path,
    )
    parser.add_argument("--clip-success-threshold", default=0.8, type=float)
    return parser.parse_args()


def md_table(frame: pd.DataFrame, max_rows: int = 40) -> str:
    if frame.empty:
        return ""
    data = frame.head(max_rows).copy()
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].astype(str)
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(row.tolist()) + " |" for _, row in data.iterrows()]
    return "\n".join([header, sep] + body)


def summarize_metrics(rows: pd.DataFrame, label: str) -> dict[str, float | str]:
    return {
        "sample": label,
        "task_rows": float(len(rows)),
        "sessions": float(rows["transcript_id"].nunique()) if not rows.empty else 0.0,
        "clips_attempted": float(rows["n_utterance_clips_attempted"].sum()) if not rows.empty else 0.0,
        "clips_transcribed": float(rows["n_utterance_clips_transcribed"].sum()) if not rows.empty else 0.0,
        "mean_clip_success_rate": float(rows["clip_success_rate"].mean()) if not rows.empty else float("nan"),
        "mean_f1": float(rows["concept_f1_vs_human"].mean()) if not rows.empty else float("nan"),
        "mean_recall": float(rows["concept_recall_vs_human"].mean()) if not rows.empty else float("nan"),
        "mean_precision": float(rows["concept_precision_vs_human"].mean()) if not rows.empty else float("nan"),
        "r_asr_coverage_wab": pearson_safe(rows["asr_concept_coverage_frac"], rows["wab_aq"])
        if len(rows) >= 3
        else float("nan"),
        "r_human_coverage_wab": pearson_safe(rows["human_concept_coverage_frac"], rows["wab_aq"])
        if len(rows) >= 3
        else float("nan"),
    }


def parse_failure_reasons(rows: pd.DataFrame) -> pd.DataFrame:
    counts: dict[str, int] = {}
    for raw in rows.get("failure_reasons", pd.Series(dtype=str)).fillna("").astype(str):
        for item in raw.split(";"):
            if not item or ":" not in item:
                continue
            reason, count = item.rsplit(":", 1)
            try:
                counts[reason] = counts.get(reason, 0) + int(count)
            except ValueError:
                counts[item] = counts.get(item, 0) + 1
    return (
        pd.DataFrame([{"failure_reason": k, "count": v} for k, v in counts.items()])
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
        if counts
        else pd.DataFrame(columns=["failure_reason", "count"])
    )


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    asr = pd.read_csv(args.asr_results)
    selected = pd.read_csv(args.selected_sessions).copy()

    for col in [
        "n_utterance_clips_attempted",
        "n_utterance_clips_transcribed",
        "concept_f1_vs_human",
        "concept_recall_vs_human",
        "concept_precision_vs_human",
        "asr_concept_coverage_frac",
        "human_concept_coverage_frac",
        "wab_aq",
    ]:
        if col in asr.columns:
            asr[col] = pd.to_numeric(asr[col], errors="coerce")

    asr["clip_success_rate"] = (
        asr["n_utterance_clips_transcribed"] / asr["n_utterance_clips_attempted"].clip(lower=1)
    )
    transcribed_ids = set(asr["transcript_id"].astype(str))
    selected["streamed_any_task"] = selected["transcript_id"].astype(str).isin(transcribed_ids)
    failed_sessions = selected[~selected["streamed_any_task"]].copy()
    low_clip = asr[asr["clip_success_rate"] < args.clip_success_threshold].copy()
    ok_clip = asr[asr["clip_success_rate"] >= args.clip_success_threshold].copy()

    status_by_corpus = (
        selected.groupby("corpus")
        .agg(
            selected_sessions=("transcript_id", "nunique"),
            streamed_sessions=("streamed_any_task", "sum"),
        )
        .reset_index()
    )
    status_by_corpus["failed_sessions"] = (
        status_by_corpus["selected_sessions"] - status_by_corpus["streamed_sessions"]
    )
    status_by_corpus["stream_success_rate"] = (
        status_by_corpus["streamed_sessions"] / status_by_corpus["selected_sessions"].clip(lower=1)
    )
    status_by_corpus = status_by_corpus.sort_values(
        ["failed_sessions", "selected_sessions"],
        ascending=[False, False],
    )

    sensitivity = pd.DataFrame(
        [
            summarize_metrics(asr, "all_transcribed_rows"),
            summarize_metrics(ok_clip, f"clip_success_ge_{args.clip_success_threshold:g}"),
            summarize_metrics(low_clip, f"clip_success_lt_{args.clip_success_threshold:g}"),
        ]
    )
    reasons = parse_failure_reasons(asr)

    failed_sessions.to_csv(out_dir / "failed_sessions.csv", index=False)
    low_clip.to_csv(out_dir / "low_clip_success_rows.csv", index=False)
    status_by_corpus.to_csv(out_dir / "session_status_by_corpus.csv", index=False)
    sensitivity.to_csv(out_dir / "metric_sensitivity.csv", index=False)
    reasons.to_csv(out_dir / "clip_failure_reasons.csv", index=False)

    lines = [
        "# Streaming ASR Technical Audit",
        "",
        f"- Selected sessions: {selected['transcript_id'].nunique()}",
        f"- Sessions with any transcribed task: {len(transcribed_ids)}",
        f"- Session stream failures: {len(failed_sessions)}",
        f"- Task rows below clip-success threshold {args.clip_success_threshold:g}: {len(low_clip)}",
        "",
        "## Metric Sensitivity",
        "",
        md_table(sensitivity.round(3)),
        "",
        "## Session Status By Corpus",
        "",
        md_table(status_by_corpus.round(3), 80),
        "",
        "## Clip Failure Reasons",
        "",
        md_table(reasons, 40),
        "",
        "## Low Clip-Success Rows",
        "",
        md_table(
            low_clip[
                [
                    "transcript_id",
                    "subtype",
                    "wab_aq",
                    "task",
                    "n_utterance_clips_attempted",
                    "n_utterance_clips_transcribed",
                    "clip_success_rate",
                    "failure_reasons",
                    "concept_f1_vs_human",
                ]
            ].round(3),
            40,
        ),
        "",
        "## Interpretation",
        "",
        "Technical media or slicing failures should not be interpreted as aphasic "
        "language-recognition failures. The thresholded sensitivity row estimates "
        "the ASR content result after excluding low-clip-success task rows, while "
        "failed sessions identify corpus/media sources that need extraction fixes.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
