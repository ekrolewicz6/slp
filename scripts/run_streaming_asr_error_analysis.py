"""Analyze concept-level errors from streaming ASR pilot outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_cross_prompt_content import CONCEPTS, chat_tokens, concept_hits  # noqa: E402
from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asr-results", default="outputs/streaming_asr_pilot_balanced12_tiny/asr_task_results.csv",
                        type=Path)
    parser.add_argument("--segments-path", default="outputs/cross_prompt_content/task_segments.csv",
                        type=Path)
    parser.add_argument("--output-dir", default="outputs/streaming_asr_error_analysis",
                        type=Path)
    return parser.parse_args()


def md_table(frame: pd.DataFrame, max_rows: int = 30) -> str:
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


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    asr = pd.read_csv(args.asr_results)
    segments = pd.read_csv(args.segments_path)
    key_cols = ["transcript_id", "task"]
    source = asr.merge(
        segments,
        on=key_cols,
        how="left",
        suffixes=("", "_segment"),
    )

    rows = []
    for _, row in source.iterrows():
        task = str(row["task"])
        if task not in CONCEPTS:
            continue
        asr_hits = concept_hits(chat_tokens(str(row.get("asr_text", ""))), task)
        for concept in CONCEPTS[task]:
            human = int(row.get(f"observed_{task.lower()}_{concept}", 0) or 0)
            pred = int(asr_hits.get(concept, 0))
            rows.append(
                {
                    "transcript_id": row["transcript_id"],
                    "participant_id": row["participant_id"],
                    "subtype": row.get("subtype", ""),
                    "wab_aq": row.get("wab_aq", pd.NA),
                    "task": task,
                    "concept": concept,
                    "human_hit": human,
                    "asr_hit": pred,
                    "false_negative": int(human == 1 and pred == 0),
                    "false_positive": int(human == 0 and pred == 1),
                    "true_positive": int(human == 1 and pred == 1),
                    "true_negative": int(human == 0 and pred == 0),
                    "asr_n_tokens": row.get("asr_n_tokens", pd.NA),
                    "human_chat_n_tokens": row.get("human_chat_n_tokens", pd.NA),
                }
            )
    concept_rows = pd.DataFrame(rows)
    concept_rows.to_csv(out_dir / "concept_level_errors.csv", index=False)

    by_task = (
        concept_rows.groupby("task")
        .agg(
            concepts=("concept", "size"),
            human_hits=("human_hit", "sum"),
            asr_hits=("asr_hit", "sum"),
            false_negatives=("false_negative", "sum"),
            false_positives=("false_positive", "sum"),
            true_positives=("true_positive", "sum"),
        )
        .reset_index()
    )
    by_task["recall"] = by_task["true_positives"] / by_task["human_hits"].clip(lower=1)
    by_task["precision"] = by_task["true_positives"] / by_task["asr_hits"].clip(lower=1)
    by_task.to_csv(out_dir / "by_task_errors.csv", index=False)

    by_concept = (
        concept_rows.groupby(["task", "concept"])
        .agg(
            human_hits=("human_hit", "sum"),
            asr_hits=("asr_hit", "sum"),
            false_negatives=("false_negative", "sum"),
            false_positives=("false_positive", "sum"),
            true_positives=("true_positive", "sum"),
        )
        .reset_index()
    )
    by_concept["recall"] = by_concept["true_positives"] / by_concept["human_hits"].clip(lower=1)
    by_concept["precision"] = by_concept["true_positives"] / by_concept["asr_hits"].clip(lower=1)
    by_concept = by_concept.sort_values(
        ["false_negatives", "false_positives", "human_hits"],
        ascending=[False, False, False],
    )
    by_concept.to_csv(out_dir / "by_concept_errors.csv", index=False)

    by_subtype = (
        concept_rows.dropna(subset=["subtype"])
        .groupby("subtype")
        .agg(
            rows=("transcript_id", "nunique"),
            human_hits=("human_hit", "sum"),
            asr_hits=("asr_hit", "sum"),
            false_negatives=("false_negative", "sum"),
            false_positives=("false_positive", "sum"),
            true_positives=("true_positive", "sum"),
        )
        .reset_index()
    )
    by_subtype["recall"] = by_subtype["true_positives"] / by_subtype["human_hits"].clip(lower=1)
    by_subtype["precision"] = by_subtype["true_positives"] / by_subtype["asr_hits"].clip(lower=1)
    by_subtype.to_csv(out_dir / "by_subtype_errors.csv", index=False)

    task_rows = asr.copy()
    lines = [
        "# Streaming ASR Error Analysis",
        "",
        f"- Task rows: {len(task_rows)}",
        f"- Concept decisions: {len(concept_rows)}",
        f"- Mean task F1: {task_rows['concept_f1_vs_human'].mean():.3f}",
        f"- Mean task recall: {task_rows['concept_recall_vs_human'].mean():.3f}",
        f"- Mean task precision: {task_rows['concept_precision_vs_human'].mean():.3f}",
        f"- ASR coverage vs WAB r: {pearson_safe(task_rows['asr_concept_coverage_frac'], task_rows['wab_aq']):.3f}",
        "",
        "## Task Error Profile",
        "",
        md_table(by_task.round(3)),
        "",
        "## Most Missed Concepts",
        "",
        md_table(by_concept[by_concept["false_negatives"] > 0].round(3), 25),
        "",
        "## Subtype Error Profile",
        "",
        md_table(by_subtype.round(3)),
        "",
        "## Interpretation",
        "",
        "Most ASR content loss is false-negative loss rather than hallucinated false "
        "content. That makes ASR-derived discourse scores conservative: useful for "
        "tracking content state, but likely to under-score some concepts unless ASR "
        "normalization or forced alignment recovers aphasic productions.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
