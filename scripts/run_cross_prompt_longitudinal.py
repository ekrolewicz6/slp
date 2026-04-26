"""Longitudinal change tests for cross-prompt content state.

This probes the clinical monitoring question: does the interpretable content
state move with, or ahead of, WAB-AQ changes across repeated sessions?
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_cross_prompt_state_reliability import (  # noqa: E402
    aggregate_session_task,
    build_session_state,
)
from src.analysis.review_grade import ensure_dir, pearson_safe, regression_summary  # noqa: E402
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--segments", default="outputs/cross_prompt_content/task_segments.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/cross_prompt_longitudinal", type=Path)
    p.add_argument("--min-core-tasks", default=3, type=int)
    return p.parse_args()


def longitudinal_root(participant_id: str) -> str:
    pid = str(participant_id)
    pid = re.sub(r"[A-Za-z]$", "", pid)
    pid = re.sub(r"-\d+$", "", pid)
    return pid


def session_order_value(participant_id: str, session_date: object) -> float:
    if isinstance(session_date, str) and session_date:
        dt = pd.to_datetime(session_date, errors="coerce")
        if pd.notna(dt):
            return float(dt.value)
    pid = str(participant_id)
    m = re.search(r"([A-Za-z])$", pid)
    if m:
        return float(ord(m.group(1).lower()) - ord("a") + 1)
    m = re.search(r"-(\d+)$", pid)
    if m:
        return float(m.group(1))
    return 0.0


def add_session_metadata(state: pd.DataFrame, segments: pd.DataFrame) -> pd.DataFrame:
    meta = segments.groupby("participant_id", as_index=False).agg(
        session_date=("session_date", "first"),
        transcript_id=("transcript_id", "first"),
    )
    out = state.merge(meta, on="participant_id", how="left")
    out["longitudinal_root"] = out["participant_id"].map(longitudinal_root)
    out["session_order"] = [
        session_order_value(pid, date)
        for pid, date in out[["participant_id", "session_date"]].itertuples(index=False)
    ]
    return out


def consecutive_pairs(state: pd.DataFrame) -> pd.DataFrame:
    rows = []
    features = [
        "content_mean_z",
        "core_content_mean_z",
        "coverage_mean",
        "tokens_mean",
        "utts_mean",
        "meanutt_mean",
    ]
    for root, group in state.groupby("longitudinal_root"):
        group = group.sort_values(["session_order", "participant_id"]).reset_index(drop=True)
        if len(group) < 2:
            continue
        for i in range(len(group) - 1):
            a = group.iloc[i]
            b = group.iloc[i + 1]
            row = {
                "longitudinal_root": root,
                "from_participant_id": a["participant_id"],
                "to_participant_id": b["participant_id"],
                "from_wab_aq": a["wab_aq"],
                "to_wab_aq": b["wab_aq"],
                "delta_wab_aq": b["wab_aq"] - a["wab_aq"],
                "abs_delta_wab_aq": abs(b["wab_aq"] - a["wab_aq"]),
                "from_core_n_tasks": a["core_n_tasks"],
                "to_core_n_tasks": b["core_n_tasks"],
            }
            for feat in features:
                row[f"from_{feat}"] = a.get(feat, np.nan)
                row[f"to_{feat}"] = b.get(feat, np.nan)
                row[f"delta_{feat}"] = b.get(feat, np.nan) - a.get(feat, np.nan)
                row[f"abs_delta_{feat}"] = abs(row[f"delta_{feat}"])
            rows.append(row)
    return pd.DataFrame(rows)


def early_to_late_rows(state: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for root, group in state.groupby("longitudinal_root"):
        group = group.sort_values(["session_order", "participant_id"]).reset_index(drop=True)
        if len(group) < 3:
            continue
        first, second, last = group.iloc[0], group.iloc[1], group.iloc[-1]
        rows.append(
            {
                "longitudinal_root": root,
                "n_sessions": int(len(group)),
                "early_delta_content_mean_z": second["content_mean_z"] - first["content_mean_z"],
                "early_delta_core_content_mean_z": second["core_content_mean_z"] - first["core_content_mean_z"],
                "early_delta_coverage_mean": second["coverage_mean"] - first["coverage_mean"],
                "early_delta_tokens_mean": second["tokens_mean"] - first["tokens_mean"],
                "later_delta_wab_aq": last["wab_aq"] - second["wab_aq"],
                "total_delta_wab_aq": last["wab_aq"] - first["wab_aq"],
                "from_participant_id": first["participant_id"],
                "mid_participant_id": second["participant_id"],
                "last_participant_id": last["participant_id"],
            }
        )
    return pd.DataFrame(rows)


def pair_summaries(pairs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feat in [
        "delta_content_mean_z",
        "delta_core_content_mean_z",
        "delta_coverage_mean",
        "delta_tokens_mean",
        "delta_meanutt_mean",
    ]:
        rows.append(
            {
                "feature": feat,
                "n": int(pairs[[feat, "delta_wab_aq"]].dropna().shape[0]),
                "r_delta_wab": pearson_safe(pairs[feat], pairs["delta_wab_aq"]),
                "r_abs_delta_wab": pearson_safe(pairs[f"abs_{feat}"], pairs["abs_delta_wab_aq"])
                if f"abs_{feat}" in pairs.columns else float("nan"),
            }
        )
    for label, mask in [
        ("stable_wab_lt5", pairs["abs_delta_wab_aq"] < 5),
        ("changed_wab_ge5", pairs["abs_delta_wab_aq"] >= 5),
        ("changed_wab_ge10", pairs["abs_delta_wab_aq"] >= 10),
    ]:
        sub = pairs[mask]
        rows.append(
            {
                "feature": label,
                "n": int(len(sub)),
                "r_delta_wab": float(sub["abs_delta_content_mean_z"].mean()) if len(sub) else float("nan"),
                "r_abs_delta_wab": float(sub["abs_delta_coverage_mean"].mean()) if len(sub) else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def early_prediction(early: pd.DataFrame) -> pd.DataFrame:
    if len(early) < 12:
        return pd.DataFrame()
    features = [
        "early_delta_content_mean_z",
        "early_delta_core_content_mean_z",
        "early_delta_coverage_mean",
        "early_delta_tokens_mean",
    ]
    y = early["later_delta_wab_aq"].astype(float).to_numpy()
    preds = np.zeros_like(y)
    groups = early["longitudinal_root"].astype(str).to_numpy()
    logo = LeaveOneGroupOut()
    model = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "model",
                GradientBoostingRegressor(
                    n_estimators=80,
                    max_depth=2,
                    learning_rate=0.05,
                    subsample=0.9,
                    random_state=0,
                ),
            ),
        ]
    )
    for train, test in logo.split(early[features], y, groups):
        if len(train) < 8:
            preds[test] = np.mean(y[train]) if len(train) else 0.0
            continue
        model.fit(early.iloc[train][features], y[train])
        preds[test] = model.predict(early.iloc[test][features])
    return pd.DataFrame([{"target": "later_delta_wab_aq", **regression_summary(y, preds)}])


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
    segments = pd.read_csv(args.segments)
    segments = segments[segments["wab_aq"].notna() & ~segments["is_control"].astype(bool)].copy()
    session_task = aggregate_session_task(segments)
    state = build_session_state(session_task)
    state = add_session_metadata(state, segments)
    state = state[state["core_n_tasks"] >= args.min_core_tasks].copy()
    state.to_csv(out_dir / "longitudinal_content_state.csv", index=False)

    pairs = consecutive_pairs(state)
    pairs.to_csv(out_dir / "consecutive_pairs.csv", index=False)
    summaries = pair_summaries(pairs) if not pairs.empty else pd.DataFrame()
    summaries.to_csv(out_dir / "pair_summaries.csv", index=False)

    early = early_to_late_rows(state)
    early.to_csv(out_dir / "early_to_late_rows.csv", index=False)
    pred = early_prediction(early)
    pred.to_csv(out_dir / "early_prediction.csv", index=False)

    lines = ["# Cross-Prompt Longitudinal Content State\n"]
    lines.append(f"- Sessions with WAB and >= {args.min_core_tasks} core tasks: {len(state)}")
    lines.append(f"- Consecutive same-root pairs: {len(pairs)}")
    lines.append(f"- Three-plus-session roots: {len(early)}")
    lines.append("\n## Pair Change Correlations\n")
    lines.append(md_table(summaries))
    if not pred.empty:
        lines.append("\n## Early Content Change Predicting Later WAB Change\n")
        lines.append(md_table(pred))
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
