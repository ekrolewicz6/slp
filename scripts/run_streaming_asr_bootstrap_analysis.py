"""Patient-level uncertainty analysis for streaming ASR concept outputs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asr-results",
        default="outputs/streaming_asr_pilot_pwa30_tiny/asr_task_results.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/streaming_asr_bootstrap_pwa30_tiny",
        type=Path,
    )
    parser.add_argument("--n-boot", default=5000, type=int)
    parser.add_argument("--seed", default=0, type=int)
    return parser.parse_args()


def patient_root(participant_id: str) -> str:
    return re.sub(r"[A-Za-z]$", "", str(participant_id))


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


def first_mode(values: pd.Series) -> object:
    clean = values.dropna()
    if clean.empty:
        return pd.NA
    modes = clean.mode()
    return modes.iloc[0] if not modes.empty else clean.iloc[0]


def load_patient_summary(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = pd.read_csv(path)
    if rows.empty:
        raise SystemExit(f"No ASR task rows found in {path}")
    if "patient_root" not in rows.columns:
        rows["patient_root"] = rows["participant_id"].map(patient_root)
    numeric_cols = [
        "wab_aq",
        "concept_f1_vs_human",
        "concept_recall_vs_human",
        "concept_precision_vs_human",
        "asr_concept_coverage_frac",
        "human_concept_coverage_frac",
        "concept_false_positive",
        "concept_false_negative",
        "n_utterance_clips_attempted",
        "n_utterance_clips_transcribed",
        "total_par_audio_seconds",
    ]
    for col in numeric_cols:
        if col in rows.columns:
            rows[col] = pd.to_numeric(rows[col], errors="coerce")

    patient = (
        rows.groupby("patient_root")
        .agg(
            n_task_rows=("task", "size"),
            n_transcripts=("transcript_id", "nunique"),
            transcript_id=("transcript_id", first_mode),
            participant_id=("participant_id", first_mode),
            corpus=("corpus", first_mode),
            subtype=("subtype", first_mode),
            wab_aq=("wab_aq", "mean"),
            mean_f1=("concept_f1_vs_human", "mean"),
            mean_recall=("concept_recall_vs_human", "mean"),
            mean_precision=("concept_precision_vs_human", "mean"),
            mean_asr_coverage=("asr_concept_coverage_frac", "mean"),
            mean_human_coverage=("human_concept_coverage_frac", "mean"),
            mean_false_positive=("concept_false_positive", "mean"),
            mean_false_negative=("concept_false_negative", "mean"),
            clips_attempted=("n_utterance_clips_attempted", "sum"),
            clips_transcribed=("n_utterance_clips_transcribed", "sum"),
            par_audio_seconds=("total_par_audio_seconds", "sum"),
        )
        .reset_index()
    )
    return rows, patient


def summarize(patient: pd.DataFrame) -> dict[str, float]:
    return {
        "n_patients": float(patient["patient_root"].nunique()),
        "n_task_rows": float(patient["n_task_rows"].sum()),
        "mean_f1": float(patient["mean_f1"].mean()),
        "mean_recall": float(patient["mean_recall"].mean()),
        "mean_precision": float(patient["mean_precision"].mean()),
        "mean_asr_coverage": float(patient["mean_asr_coverage"].mean()),
        "mean_human_coverage": float(patient["mean_human_coverage"].mean()),
        "mean_coverage_gap_asr_minus_human": float(
            (patient["mean_asr_coverage"] - patient["mean_human_coverage"]).mean()
        ),
        "r_asr_coverage_wab": pearson_safe(patient["mean_asr_coverage"], patient["wab_aq"]),
        "r_human_coverage_wab": pearson_safe(patient["mean_human_coverage"], patient["wab_aq"]),
        "mean_false_positive": float(patient["mean_false_positive"].mean()),
        "mean_false_negative": float(patient["mean_false_negative"].mean()),
    }


def bootstrap_metrics(
    patient: pd.DataFrame,
    metric_fns: dict[str, Callable[[pd.DataFrame], float]],
    n_boot: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    point = {name: fn(patient) for name, fn in metric_fns.items()}
    vals = {name: [] for name in metric_fns}
    n = len(patient)
    for _ in range(n_boot):
        sample = patient.iloc[rng.integers(0, n, size=n)]
        for name, fn in metric_fns.items():
            try:
                vals[name].append(fn(sample))
            except Exception:
                vals[name].append(np.nan)
    rows = []
    for name, arr in vals.items():
        x = np.asarray(arr, dtype=float)
        rows.append(
            {
                "metric": name,
                "point": point[name],
                "boot_mean": float(np.nanmean(x)),
                "ci_low": float(np.nanpercentile(x, 2.5)),
                "ci_high": float(np.nanpercentile(x, 97.5)),
            }
        )
    return pd.DataFrame(rows)


def subgroup_summary(rows: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if group_col not in rows.columns:
        return pd.DataFrame()
    out = (
        rows.groupby(group_col)
        .agg(
            n_patients=("patient_root", "nunique"),
            n_task_rows=("task", "size"),
            mean_wab=("wab_aq", "mean"),
            mean_f1=("concept_f1_vs_human", "mean"),
            mean_recall=("concept_recall_vs_human", "mean"),
            mean_precision=("concept_precision_vs_human", "mean"),
            mean_asr_coverage=("asr_concept_coverage_frac", "mean"),
            mean_human_coverage=("human_concept_coverage_frac", "mean"),
        )
        .reset_index()
    )
    return out.sort_values(["n_patients", "n_task_rows"], ascending=[False, False])


def leave_corpus_out(patient: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corpus in sorted(patient["corpus"].dropna().unique()):
        sub = patient[patient["corpus"] != corpus].copy()
        if len(sub) < 3:
            continue
        metrics = summarize(sub)
        metrics["excluded_corpus"] = corpus
        rows.append(metrics)
    return pd.DataFrame(rows)


def write_summary(
    out_dir: Path,
    asr_path: Path,
    patient: pd.DataFrame,
    ci: pd.DataFrame,
    by_task: pd.DataFrame,
    by_subtype: pd.DataFrame,
    by_corpus: pd.DataFrame,
    lco: pd.DataFrame,
) -> None:
    lines = [
        "# Streaming ASR Patient-Level Bootstrap Analysis",
        "",
        f"- Source: `{asr_path}`",
        f"- Patients: {patient['patient_root'].nunique()}",
        f"- Task rows: {int(patient['n_task_rows'].sum())}",
        f"- Utterance clips transcribed: {int(patient['clips_transcribed'].sum())}",
        f"- PAR audio transcribed: {patient['par_audio_seconds'].sum() / 60:.2f} min",
        "",
        "## Patient-Level Bootstrap CIs",
        "",
        md_table(ci.round(3)),
        "",
        "## By Task",
        "",
        md_table(by_task.round(3)),
        "",
        "## By Subtype",
        "",
        md_table(by_subtype.round(3)),
        "",
        "## By Corpus",
        "",
        md_table(by_corpus.round(3), 80),
        "",
        "## Leave-One-Corpus-Out Sensitivity",
        "",
        md_table(lco.round(3), 80),
        "",
        "## Interpretation",
        "",
        "This analysis treats participants as the uncertainty unit. The headline "
        "ASR content-state metrics should be read from the patient-level rows, "
        "not only from task rows, because repeated prompt tasks from the same "
        "speaker are not independent evidence.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    rows, patient = load_patient_summary(args.asr_results)

    metrics = {
        "mean_f1": lambda x: float(x["mean_f1"].mean()),
        "mean_recall": lambda x: float(x["mean_recall"].mean()),
        "mean_precision": lambda x: float(x["mean_precision"].mean()),
        "mean_asr_coverage": lambda x: float(x["mean_asr_coverage"].mean()),
        "mean_human_coverage": lambda x: float(x["mean_human_coverage"].mean()),
        "coverage_gap_asr_minus_human": lambda x: float(
            (x["mean_asr_coverage"] - x["mean_human_coverage"]).mean()
        ),
        "r_asr_coverage_wab": lambda x: pearson_safe(x["mean_asr_coverage"], x["wab_aq"]),
        "r_human_coverage_wab": lambda x: pearson_safe(x["mean_human_coverage"], x["wab_aq"]),
        "mean_false_positive": lambda x: float(x["mean_false_positive"].mean()),
        "mean_false_negative": lambda x: float(x["mean_false_negative"].mean()),
    }
    ci = bootstrap_metrics(patient, metrics, n_boot=args.n_boot, seed=args.seed)
    by_task = subgroup_summary(rows, "task")
    by_subtype = subgroup_summary(rows, "subtype")
    by_corpus = subgroup_summary(rows, "corpus")
    lco = leave_corpus_out(patient)

    rows.to_csv(out_dir / "task_rows.csv", index=False)
    patient.to_csv(out_dir / "patient_summary.csv", index=False)
    ci.to_csv(out_dir / "patient_bootstrap_ci.csv", index=False)
    by_task.to_csv(out_dir / "by_task.csv", index=False)
    by_subtype.to_csv(out_dir / "by_subtype.csv", index=False)
    by_corpus.to_csv(out_dir / "by_corpus.csv", index=False)
    lco.to_csv(out_dir / "leave_one_corpus_out.csv", index=False)
    write_summary(out_dir, args.asr_results, patient, ci, by_task, by_subtype, by_corpus, lco)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
