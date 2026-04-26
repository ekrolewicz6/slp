"""Compare target-selection policies using item-level content predictions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions",
        default="outputs/treatment_target_sequencing/item_predictions.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/target_policy_simulation", type=Path)
    parser.add_argument("--top-k", default=5, type=int)
    parser.add_argument("--seed", default=0, type=int)
    return parser.parse_args()


def add_utilities(pred: pd.DataFrame) -> pd.DataFrame:
    out = pred.copy()
    out["p"] = out["pred_ability+item"]
    out["zone_045"] = 1 - (out["p"] - 0.45).abs()
    out["learning_utility"] = out["p"] * (1 - out["p"])
    out["too_easy"] = out["p"] >= 0.70
    out["too_hard"] = out["p"] <= 0.25
    pop = out.groupby("item_id")["hit"].mean().rename("item_hit_rate")
    out = out.merge(pop, on="item_id", how="left")
    return out


def select_policy(group: pd.DataFrame, policy: str, top_k: int, seed: int) -> pd.DataFrame:
    misses = group[group["hit"].eq(0)].copy()
    if misses.empty:
        return misses
    if policy == "near_threshold":
        sel = misses.sort_values(["zone_045", "learning_utility"], ascending=False)
    elif policy == "easy_missed":
        sel = misses.sort_values("p", ascending=False)
    elif policy == "hard_missed":
        sel = misses.sort_values("p", ascending=True)
    elif policy == "generic_popular":
        sel = misses.sort_values("item_hit_rate", ascending=False)
    elif policy == "high_utility":
        sel = misses.sort_values("learning_utility", ascending=False)
    elif policy == "random_missed":
        sel = misses.sample(frac=1, random_state=seed)
    else:
        raise ValueError(policy)
    return sel.head(top_k).assign(policy=policy)


def run_policies(pred: pd.DataFrame, top_k: int, seed: int) -> pd.DataFrame:
    policies = [
        "near_threshold",
        "high_utility",
        "easy_missed",
        "hard_missed",
        "generic_popular",
        "random_missed",
    ]
    rows = []
    for participant_id, group in pred.groupby("participant_id"):
        for i, policy in enumerate(policies):
            selected = select_policy(group, policy, top_k, seed + i)
            rows.append(selected)
    return pd.concat(rows, ignore_index=True)


def summarize(selected: pd.DataFrame) -> pd.DataFrame:
    return (
        selected.groupby("policy")
        .agg(
            n_targets=("item_id", "size"),
            n_participants=("participant_id", "nunique"),
            mean_pred_success=("p", "mean"),
            mean_zone_045=("zone_045", "mean"),
            mean_learning_utility=("learning_utility", "mean"),
            pct_too_easy=("too_easy", "mean"),
            pct_too_hard=("too_hard", "mean"),
            mean_item_popularity=("item_hit_rate", "mean"),
            task_diversity=("task", lambda s: s.nunique()),
        )
        .reset_index()
        .sort_values("mean_zone_045", ascending=False)
    )


def by_subtype(selected: pd.DataFrame) -> pd.DataFrame:
    return (
        selected.groupby(["subtype", "policy"], dropna=False)
        .agg(
            n_targets=("item_id", "size"),
            n_participants=("participant_id", "nunique"),
            mean_pred_success=("p", "mean"),
            mean_zone_045=("zone_045", "mean"),
            pct_too_easy=("too_easy", "mean"),
            pct_too_hard=("too_hard", "mean"),
        )
        .reset_index()
        .sort_values(["subtype", "mean_zone_045"], ascending=[True, False])
    )


def task_distribution(selected: pd.DataFrame) -> pd.DataFrame:
    counts = selected.groupby(["policy", "task"]).size().rename("n").reset_index()
    totals = counts.groupby("policy")["n"].transform("sum")
    counts["pct"] = counts["n"] / totals
    return counts.sort_values(["policy", "n"], ascending=[True, False])


def md_table(frame: pd.DataFrame, cols: list[str] | None = None, n: int | None = None) -> str:
    if frame.empty:
        return ""
    data = frame.copy()
    if cols:
        data = data[cols]
    if n:
        data = data.head(n)
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].astype(str)
    data = data.astype(str)
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(row.tolist()) + " |" for _, row in data.iterrows()]
    return "\n".join([header, sep] + body)


def write_summary(out_dir: Path, summary: pd.DataFrame, subtype: pd.DataFrame, tasks: pd.DataFrame, top_k: int) -> None:
    lines = [
        "# Target Policy Simulation",
        "",
        f"- Top-k targets per participant: {top_k}",
        "",
        "## Policy Summary",
        "",
        md_table(summary),
        "",
        "## Subtype Summary",
        "",
        md_table(
            subtype,
            ["subtype", "policy", "n_participants", "mean_pred_success", "mean_zone_045", "pct_too_easy", "pct_too_hard"],
            36,
        ),
        "",
        "## Task Distribution",
        "",
        md_table(tasks, ["policy", "task", "n", "pct"], 40),
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    pred = add_utilities(pd.read_csv(args.predictions))
    selected = run_policies(pred, args.top_k, args.seed)
    summary = summarize(selected)
    subtype = by_subtype(selected)
    tasks = task_distribution(selected)
    selected.to_csv(out_dir / "selected_targets_by_policy.csv", index=False)
    summary.to_csv(out_dir / "policy_summary.csv", index=False)
    subtype.to_csv(out_dir / "policy_by_subtype.csv", index=False)
    tasks.to_csv(out_dir / "policy_task_distribution.csv", index=False)
    write_summary(out_dir, summary, subtype, tasks, args.top_k)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
