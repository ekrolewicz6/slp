"""DLD fairness and metadata-coverage audit.

Local Clinical-Eng metadata are uneven. This script reports what subgroup
auditing is possible now and evaluates the DLD/SLI-vs-TD screening predictions
by available corpus, age-bin, task proxy, and path-encoded sex tokens.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions",
        default="outputs/dld_state_screening/screening_predictions.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/dld_fairness_metadata_audit", type=Path)
    parser.add_argument("--task", default="DLD_SLI_vs_TD_age_le_84")
    parser.add_argument("--feature-set", default="full_language_age")
    return parser.parse_args()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def md_table(df: pd.DataFrame, max_rows: int | None = None, digits: int = 3) -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "_No rows._"
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.{digits}f}")
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def parse_sex_token(transcript_id: str) -> str:
    parts = transcript_id.split("/")
    for token in parts[2:-1]:
        m = re.fullmatch(r"\d{1,2}([mf])", token.lower())
        if m:
            return "F" if m.group(1) == "f" else "M"
    return "unknown"


def parse_task_proxy(transcript_id: str, corpus: str) -> str:
    tid = transcript_id.lower()
    if corpus == "ENNI":
        return "narrative_enni"
    if corpus == "Gillam":
        return "narrative_gillam"
    if "narrative" in tid:
        return "narrative"
    if "frog" in tid:
        return "frog_story"
    if "spontaneous" in tid:
        return "spontaneous"
    if "parentchild" in tid:
        return "parent_child"
    if "/meal/" in tid:
        return "meal"
    if "/play/" in tid:
        return "play"
    if "/story/" in tid:
        return "story"
    if re.search(r"/\d+(ec|pc|int|conv)/", tid):
        token = re.search(r"/\d+(ec|pc|int|conv)/", tid).group(1)
        return {"ec": "elicited_context", "pc": "parent_child", "int": "interview", "conv": "conversation"}[token]
    return "unknown"


def participant_predictions(pred: pd.DataFrame, task: str, feature_set: str) -> pd.DataFrame:
    work = pred[pred["task"].eq(task) & pred["feature_set"].eq(feature_set)].copy()
    work["sex_token"] = work["transcript_id"].map(parse_sex_token)
    work["task_proxy"] = [parse_task_proxy(tid, corpus) for tid, corpus in zip(work["transcript_id"], work["corpus"])]
    part = (
        work.groupby("participant_root", as_index=False)
        .agg(
            y_true=("y_true", "max"),
            y_proba=("y_proba", "mean"),
            n_windows=("window_id", "count"),
            corpus=("corpus", "first"),
            age_mean=("age_months", "mean"),
            sex_token=("sex_token", lambda s: s.value_counts().index[0] if len(s) else "unknown"),
            task_proxy=("task_proxy", lambda s: s.value_counts().index[0] if len(s) else "unknown"),
        )
    )
    part["y_pred"] = (part["y_proba"] >= 0.5).astype(int)
    part["age_bin_12mo"] = (np.floor(part["age_mean"] / 12.0) * 12).astype(int).astype(str) + "-" + (
        np.floor(part["age_mean"] / 12.0) * 12 + 11
    ).astype(int).astype(str)
    return part


def subgroup_metrics(part: pd.DataFrame, group_col: str, min_n: int = 20) -> pd.DataFrame:
    rows = []
    for value, group in part.groupby(group_col, dropna=False):
        if len(group) < min_n or group["y_true"].nunique() < 2:
            continue
        row = {
            "group_col": group_col,
            "group": value,
            "n_participants": int(len(group)),
            "n_dld": int(group["y_true"].sum()),
            "positive_rate": float(group["y_true"].mean()),
            "balanced_accuracy": float(balanced_accuracy_score(group["y_true"], group["y_pred"])),
            "macro_f1": float(f1_score(group["y_true"], group["y_pred"], average="macro", zero_division=0)),
            "positive_f1": float(f1_score(group["y_true"], group["y_pred"], zero_division=0)),
            "auc": float(roc_auc_score(group["y_true"], group["y_proba"])),
        }
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["group_col", "macro_f1"]) if rows else pd.DataFrame()


def coverage_rows(part: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in ["corpus", "age_bin_12mo", "sex_token", "task_proxy"]:
        known = part[col].notna() & ~part[col].eq("unknown")
        rows.append(
            {
                "metadata_field": col,
                "n_known": int(known.sum()),
                "n_total": int(len(part)),
                "known_rate": float(known.mean()),
                "n_levels": int(part.loc[known, col].nunique()),
                "levels": ", ".join(map(str, sorted(part.loc[known, col].unique())[:20])),
            }
        )
    return pd.DataFrame(rows)


def gap_rows(subgroups: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, group in subgroups.groupby("group_col"):
        if len(group) < 2:
            continue
        rows.append(
            {
                "group_col": col,
                "n_reportable_groups": int(len(group)),
                "macro_f1_min": float(group["macro_f1"].min()),
                "macro_f1_max": float(group["macro_f1"].max()),
                "macro_f1_range": float(group["macro_f1"].max() - group["macro_f1"].min()),
                "auc_min": float(group["auc"].min()),
                "auc_max": float(group["auc"].max()),
                "auc_range": float(group["auc"].max() - group["auc"].min()),
            }
        )
    return pd.DataFrame(rows).sort_values("macro_f1_range", ascending=False) if rows else pd.DataFrame()


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    pred = pd.read_csv(args.predictions)
    part = participant_predictions(pred, args.task, args.feature_set)
    coverage = coverage_rows(part)
    subgroups = pd.concat(
        [
            subgroup_metrics(part, "corpus"),
            subgroup_metrics(part, "age_bin_12mo"),
            subgroup_metrics(part, "sex_token"),
            subgroup_metrics(part, "task_proxy"),
        ],
        ignore_index=True,
    )
    gaps = gap_rows(subgroups)

    part.to_csv(out_dir / "participant_predictions_with_metadata.csv", index=False)
    coverage.to_csv(out_dir / "metadata_coverage.csv", index=False)
    subgroups.to_csv(out_dir / "subgroup_metrics.csv", index=False)
    gaps.to_csv(out_dir / "subgroup_metric_ranges.csv", index=False)

    lines = [
        "# DLD Fairness And Metadata Audit",
        "",
        f"- Task: {args.task}",
        f"- Feature set: {args.feature_set}",
        f"- Participants: {len(part)}",
        "",
        "## Metadata Coverage",
        "",
        md_table(coverage),
        "",
        "## Reportable Subgroup Metrics",
        "",
        md_table(subgroups),
        "",
        "## Subgroup Metric Ranges",
        "",
        md_table(gaps),
        "",
        "## Interpretation",
        "",
        "- Corpus and age subgroup audits are feasible locally.",
        "- Sex/gender coverage from path tokens is sparse and corpus-biased, so it is not a reliable fairness audit.",
        "- Dialect, bilingual exposure, socioeconomic status, race/ethnicity, and intervention history are not available in the current feature table.",
        "- Any clinically serious DLD screening claim needs a prospective or linked dataset with explicit demographic and language-exposure metadata.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print((out_dir / "summary.md").resolve())


if __name__ == "__main__":
    main()
