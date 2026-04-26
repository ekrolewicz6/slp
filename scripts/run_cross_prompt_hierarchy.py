"""Concept hierarchy tests for cross-prompt content scoring.

Given the task-level concept features from run_cross_prompt_content.py, this
script asks whether each prompt's concepts behave like a severity-ordered
item ladder. A strong ladder is useful for SLP because it turns a discourse
sample into interpretable targets: which event concepts are preserved, and
which disappear until severity improves?
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--segments", default="outputs/cross_prompt_content/task_segments.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/cross_prompt_hierarchy", type=Path)
    p.add_argument("--min-n", default=80, type=int)
    p.add_argument("--random-orders", default=500, type=int)
    return p.parse_args()


def concept_cols(df: pd.DataFrame, task: str) -> list[str]:
    prefix = f"observed_{task.lower()}_"
    return sorted(c for c in df.columns if c.startswith(prefix))


def clean_concept(col: str, task: str) -> str:
    return re.sub(rf"^observed_{re.escape(task.lower())}_", "", col)


def logistic_threshold(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask].astype(float)
    y = y[mask].astype(int)
    if len(y) < 20 or len(np.unique(y)) < 2 or y.sum() < 5 or (len(y) - y.sum()) < 5:
        return float("nan"), float("nan")
    mu = float(np.mean(x))
    sd = float(np.std(x) or 1.0)
    xs = ((x - mu) / sd).reshape(-1, 1)
    model = LogisticRegression(solver="lbfgs")
    model.fit(xs, y)
    coef = float(model.coef_[0][0])
    intercept = float(model.intercept_[0])
    if coef <= 0:
        return float("nan"), coef
    threshold = mu + (-intercept / coef) * sd
    return float(threshold), coef


def guttman_reproducibility(frame: pd.DataFrame, cols: list[str]) -> float:
    if not cols:
        return float("nan")
    mat = frame[cols].fillna(0).astype(int).to_numpy()
    n, m = mat.shape
    if n == 0 or m == 0:
        return float("nan")
    errors = 0
    for row in mat:
        k = int(row.sum())
        ideal = np.zeros(m, dtype=int)
        ideal[:k] = 1
        errors += int(np.abs(row - ideal).sum())
    return float(1.0 - errors / (n * m))


def random_order_summary(frame: pd.DataFrame, cols: list[str], n_random: int, seed: int = 0) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    vals = []
    cols = list(cols)
    for _ in range(n_random):
        shuffled = list(rng.permutation(cols))
        vals.append(guttman_reproducibility(frame, shuffled))
    arr = np.asarray(vals, dtype=float)
    return {
        "random_mean": float(np.nanmean(arr)),
        "random_p95": float(np.nanpercentile(arr, 95)),
        "random_max": float(np.nanmax(arr)),
    }


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
    df = pd.read_csv(args.segments)
    pwa = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy()

    threshold_rows = []
    hierarchy_rows = []
    for task, group in pwa.groupby("task"):
        group = group.reset_index(drop=True)
        cols = concept_cols(group, task)
        if len(group) < args.min_n or len(cols) < 4:
            continue
        for col in cols:
            y = group[col].fillna(0).astype(int).to_numpy()
            x = group["wab_aq"].astype(float).to_numpy()
            threshold, coef = logistic_threshold(x, y)
            low = group[group["wab_aq"] < 60][col].mean()
            mid = group[(group["wab_aq"] >= 60) & (group["wab_aq"] < 80)][col].mean()
            high = group[group["wab_aq"] >= 80][col].mean()
            controls = df[(df["task"] == task) & (df["is_control"])]
            threshold_rows.append(
                {
                    "task": task,
                    "concept": clean_concept(col, task),
                    "n": int(len(group)),
                    "mention_rate_pwa": float(group[col].mean()),
                    "mention_rate_control": float(controls[col].mean()) if len(controls) else float("nan"),
                    "r_wab_aq": pearson_safe(group[col], group["wab_aq"]),
                    "threshold_aq_p50": threshold,
                    "logit_coef": coef,
                    "rate_aq_lt_60": float(low) if np.isfinite(low) else float("nan"),
                    "rate_aq_60_80": float(mid) if np.isfinite(mid) else float("nan"),
                    "rate_aq_ge_80": float(high) if np.isfinite(high) else float("nan"),
                }
            )

        task_thresholds = pd.DataFrame([r for r in threshold_rows if r["task"] == task])
        usable = task_thresholds.dropna(subset=["threshold_aq_p50"]).sort_values("threshold_aq_p50")
        order_cols = [f"observed_{task.lower()}_{c}" for c in usable["concept"].tolist()]
        if len(order_cols) < 4:
            order_cols = [
                f"observed_{task.lower()}_{c}"
                for c in task_thresholds.sort_values("mention_rate_pwa", ascending=False)["concept"].tolist()
            ]
        order_cols = [c for c in order_cols if c in group.columns]
        observed_rep = guttman_reproducibility(group, order_cols)
        rand = random_order_summary(group, order_cols, args.random_orders, seed=13)
        hierarchy_rows.append(
            {
                "task": task,
                "n": int(len(group)),
                "n_concepts": int(len(order_cols)),
                "observed_reproducibility": observed_rep,
                **rand,
                "beats_random_p95": bool(observed_rep > rand["random_p95"]),
                "ordered_concepts": ",".join(clean_concept(c, task) for c in order_cols),
            }
        )

    thresholds = pd.DataFrame(threshold_rows).sort_values(["task", "threshold_aq_p50", "mention_rate_pwa"])
    hierarchy = pd.DataFrame(hierarchy_rows).sort_values("observed_reproducibility", ascending=False)
    thresholds.to_csv(out_dir / "concept_thresholds.csv", index=False)
    hierarchy.to_csv(out_dir / "hierarchy_reproducibility.csv", index=False)

    lines = ["# Cross-Prompt Concept Hierarchy Summary\n"]
    lines.append("## Hierarchy Reproducibility\n")
    view = hierarchy[["task", "n", "n_concepts", "observed_reproducibility", "random_p95", "beats_random_p95"]]
    lines.append(md_table(view))
    lines.append("\n## Easiest And Hardest Concepts\n")
    extremes = []
    for task, group in thresholds.dropna(subset=["threshold_aq_p50"]).groupby("task"):
        low = group.sort_values("threshold_aq_p50").head(3)
        high = group.sort_values("threshold_aq_p50").tail(3)
        for label, part in [("easy", low), ("hard", high)]:
            for _, row in part.iterrows():
                extremes.append(
                    {
                        "task": task,
                        "band": label,
                        "concept": row["concept"],
                        "threshold_aq_p50": row["threshold_aq_p50"],
                        "control_rate": row["mention_rate_control"],
                    }
                )
    lines.append(md_table(pd.DataFrame(extremes)))
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
