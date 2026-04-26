"""Minimal/adaptive prompt assessment for content-state measurement.

If content state is clinically useful, SLPs need to know how much elicitation
is necessary. This script evaluates all subsets of the five core AphasiaBank
protocol prompts and asks:

* how well each subset recovers the full five-prompt content state;
* how well each subset predicts WAB-AQ under patient-grouped CV;
* which prompt order gives the best adaptive short assessment.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import (  # noqa: E402
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


CORE_TASKS = ["Cat", "Cinderella", "Sandwich", "Umbrella", "Window"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--state", default="outputs/cross_prompt_state/patient_content_state.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/minimal_adaptive_assessment", type=Path)
    p.add_argument("--cv-folds", default=5, type=int)
    return p.parse_args()


def load_complete_state(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy()
    required = [f"z_{t}" for t in CORE_TASKS]
    df = df.dropna(subset=required + ["patient_root", "wab_aq"]).reset_index(drop=True)
    df["full_core_content_mean_z"] = df[required].mean(axis=1)
    return df


def subset_features(df: pd.DataFrame, tasks: tuple[str, ...]) -> tuple[pd.DataFrame, list[str], list[str]]:
    out = df.copy()
    z_cols = [f"z_{t}" for t in tasks]
    coverage_cols = [f"coverage_{t}" for t in tasks]
    token_cols = [f"tokens_{t}" for t in tasks]
    meanutt_cols = [f"meanutt_{t}" for t in tasks]
    out["subset_mean_z"] = out[z_cols].mean(axis=1)
    out["subset_min_z"] = out[z_cols].min(axis=1)
    out["subset_max_z"] = out[z_cols].max(axis=1)
    out["subset_sd_z"] = out[z_cols].std(axis=1).fillna(0.0)
    out["subset_coverage_mean"] = out[coverage_cols].mean(axis=1)
    out["subset_tokens_mean"] = out[token_cols].mean(axis=1)
    out["subset_meanutt_mean"] = out[meanutt_cols].mean(axis=1)
    content_cols = ["subset_mean_z", "subset_min_z", "subset_max_z", "subset_sd_z", "subset_coverage_mean"] + z_cols
    verbosity_cols = ["subset_tokens_mean", "subset_meanutt_mean"]
    return out, content_cols, verbosity_cols


def evaluate_subsets(df: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    rows = []
    for k in range(1, len(CORE_TASKS) + 1):
        for tasks in itertools.combinations(CORE_TASKS, k):
            work, content_cols, verbosity_cols = subset_features(df, tasks)
            state_r = pearson_safe(work["subset_mean_z"], work["full_core_content_mean_z"])
            raw_wab_r = pearson_safe(work["subset_mean_z"], work["wab_aq"])
            setups = {
                "content_only": {"content": content_cols},
                "content+verbosity": {"content": content_cols, "verbosity": verbosity_cols},
                "verbosity_only": {"verbosity": verbosity_cols},
            }
            for setup, blocks in setups.items():
                y, pred = cross_val_predict_regressor(
                    work,
                    "wab_aq",
                    blocks,
                    group_col="patient_root",
                    cv_mode="group",
                    n_splits=cv_folds,
                )
                rows.append(
                    {
                        "tasks": "+".join(tasks),
                        "n_tasks": k,
                        "setup": setup,
                        "state_r": state_r,
                        "raw_subset_wab_r": raw_wab_r,
                        **regression_summary(y, pred),
                    }
                )
    return pd.DataFrame(rows).sort_values(["n_tasks", "setup", "r"], ascending=[True, True, False])


def greedy_order(subsets: pd.DataFrame, setup: str = "content_only") -> pd.DataFrame:
    selected: list[str] = []
    rows = []
    remaining = set(CORE_TASKS)
    for step in range(1, len(CORE_TASKS) + 1):
        candidates = []
        for task in sorted(remaining):
            tasks = tuple(sorted(selected + [task]))
            label = "+".join(tasks)
            row = subsets[(subsets["tasks"].eq(label)) & (subsets["setup"].eq(setup))]
            if len(row):
                candidates.append(row.iloc[0].to_dict() | {"added_task": task})
        if not candidates:
            break
        best = sorted(candidates, key=lambda r: (r["r"], r["state_r"]), reverse=True)[0]
        selected.append(best["added_task"])
        remaining.remove(best["added_task"])
        best["step"] = step
        best["selected_order"] = " -> ".join(selected)
        rows.append(best)
    return pd.DataFrame(rows)


def md_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    data = frame.copy()
    cols = list(data.columns)
    for col in cols:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else str(x))
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = ["| " + " | ".join(data.loc[i, cols].astype(str).tolist()) + " |" for i in data.index]
    return "\n".join([header, sep] + body)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    df = load_complete_state(args.state)
    subsets = evaluate_subsets(df, args.cv_folds)
    subsets.to_csv(out_dir / "subset_results.csv", index=False)

    best_by_k = (
        subsets[subsets["setup"].eq("content_only")]
        .sort_values(["n_tasks", "r", "state_r"], ascending=[True, False, False])
        .groupby("n_tasks")
        .head(5)
        .reset_index(drop=True)
    )
    best_by_k.to_csv(out_dir / "best_content_subsets_by_k.csv", index=False)

    greedy = greedy_order(subsets, setup="content_only")
    greedy.to_csv(out_dir / "greedy_prompt_order.csv", index=False)

    lines = ["# Minimal / Adaptive Assessment Summary\n"]
    lines.append(f"- Complete five-core-task sessions: {len(df)}")
    lines.append("\n## Best Content-Only Subsets By Number Of Prompts\n")
    lines.append(md_table(best_by_k[["n_tasks", "tasks", "state_r", "raw_subset_wab_r", "mae", "r"]]))
    lines.append("\n## Greedy Prompt Order For WAB Prediction\n")
    lines.append(md_table(greedy[["step", "added_task", "selected_order", "state_r", "mae", "r"]]))
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
