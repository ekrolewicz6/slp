"""Compare streaming ASR pilot runs across model/sample conditions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir, pearson_safe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs/streaming_asr_model_comparison",
                        type=Path)
    parser.add_argument(
        "--run",
        action="append",
        nargs=3,
        metavar=("LABEL", "MODEL", "RESULTS_CSV"),
        required=True,
        help="Add one run as: label model path/to/asr_task_results.csv",
    )
    return parser.parse_args()


def summarize(label: str, model: str, path: Path) -> dict[str, float | int | str]:
    df = pd.read_csv(path)
    return {
        "label": label,
        "model": model,
        "rows": len(df),
        "sessions": df["transcript_id"].nunique(),
        "utterance_clips": int(df["n_utterance_clips_attempted"].sum()),
        "par_audio_min": df["total_par_audio_seconds"].sum() / 60,
        "mean_f1": df["concept_f1_vs_human"].mean(),
        "mean_recall": df["concept_recall_vs_human"].mean(),
        "mean_precision": df["concept_precision_vs_human"].mean(),
        "mean_asr_coverage": df["asr_concept_coverage_frac"].mean(),
        "mean_human_coverage": df["human_concept_coverage_frac"].mean(),
        "r_asr_coverage_wab": pearson_safe(df["asr_concept_coverage_frac"], df["wab_aq"]),
        "r_human_coverage_wab": pearson_safe(df["human_concept_coverage_frac"], df["wab_aq"]),
    }


def paired_delta(label_a: str, model_a: str, path_a: Path,
                 label_b: str, model_b: str, path_b: Path) -> pd.DataFrame:
    a = pd.read_csv(path_a).add_suffix("_a")
    b = pd.read_csv(path_b).add_suffix("_b")
    merged = a.merge(
        b,
        left_on=["transcript_id_a", "task_a"],
        right_on=["transcript_id_b", "task_b"],
        how="inner",
    )
    rows = []
    for metric in [
        "concept_f1_vs_human",
        "concept_recall_vs_human",
        "concept_precision_vs_human",
        "asr_concept_coverage_frac",
    ]:
        delta = merged[f"{metric}_b"] - merged[f"{metric}_a"]
        rows.append(
            {
                "comparison": f"{label_b}:{model_b} minus {label_a}:{model_a}",
                "metric": metric,
                "paired_rows": len(merged),
                "mean_a": merged[f"{metric}_a"].mean(),
                "mean_b": merged[f"{metric}_b"].mean(),
                "mean_delta": delta.mean(),
                "n_better": int((delta > 0).sum()),
                "n_worse": int((delta < 0).sum()),
                "n_same": int((delta == 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def md_table(frame: pd.DataFrame) -> str:
    data = frame.copy()
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
    run_specs = [(label, model, Path(path)) for label, model, path in args.run]

    summary = pd.DataFrame([summarize(label, model, path) for label, model, path in run_specs])
    summary.to_csv(out_dir / "run_summary.csv", index=False)

    deltas = []
    by_label: dict[str, list[tuple[str, Path]]] = {}
    for label, model, path in run_specs:
        by_label.setdefault(label, []).append((model, path))
    for label, runs in by_label.items():
        if len(runs) < 2:
            continue
        for idx in range(len(runs) - 1):
            model_a, path_a = runs[idx]
            model_b, path_b = runs[idx + 1]
            deltas.append(paired_delta(label, model_a, path_a, label, model_b, path_b))
    delta_df = pd.concat(deltas, ignore_index=True) if deltas else pd.DataFrame()
    delta_df.to_csv(out_dir / "paired_model_deltas.csv", index=False)

    lines = [
        "# Streaming ASR Model Comparison",
        "",
        "## Run Summary",
        "",
        md_table(summary.round(3)),
    ]
    if not delta_df.empty:
        lines.extend(["", "## Paired Deltas", "", md_table(delta_df.round(3))])
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The balanced sample tests whether ASR can preserve clinically meaningful "
            "prompt-conditioned content when participants actually produce content. The "
            "severe sample tests whether larger ASR alone rescues floor-level Broca speech. "
            "A large balanced improvement with no severe improvement would point to ASR "
            "model scale as the bottleneck; a small balanced improvement and no severe "
            "improvement points toward aphasia-specific ASR/alignment plus downstream "
            "clarification rather than generic model scaling alone.",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
