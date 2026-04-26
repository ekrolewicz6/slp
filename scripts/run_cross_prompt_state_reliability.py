"""Patient/session-level reliability of prompt-normalized content state.

The cross-prompt model shows that prompt-specific content predicts WAB-AQ.
This script asks a harder measurement question: do different prompts measure
the same patient-level discourse content state?

Outputs:
* pairwise correlations of content z-scores across prompts;
* split-half reliability across prompt families;
* patient/session-level WAB-AQ prediction from compact content summaries.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import (  # noqa: E402
    bootstrap_ci,
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


CORE_TASKS = ["Cat", "Cinderella", "Sandwich", "Umbrella", "Window"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--segments", default="outputs/cross_prompt_content/task_segments.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/cross_prompt_state", type=Path)
    p.add_argument("--cv-folds", default=5, type=int)
    return p.parse_args()


def mode_or_first(series: pd.Series) -> object:
    vals = series.dropna()
    if vals.empty:
        return np.nan
    mode = vals.mode()
    return mode.iloc[0] if len(mode) else vals.iloc[0]


def aggregate_session_task(df: pd.DataFrame) -> pd.DataFrame:
    agg = {
        "patient_root": "first",
        "corpus": "first",
        "subtype": mode_or_first,
        "wab_aq": "mean",
        "age_years": "mean",
        "sex": mode_or_first,
        "is_control": "max",
        "observed_control_z": "mean",
        "observed_control_gap": "mean",
        "observed_control_pct": "mean",
        "observed_concept_coverage_frac": "mean",
        "observed_concept_density": "mean",
        "observed_n_tokens": "mean",
        "n_utterances": "mean",
        "mean_utt_tokens": "mean",
    }
    cols = {k: v for k, v in agg.items() if k in df.columns}
    return df.groupby(["participant_id", "task"], as_index=False).agg(cols)


def build_session_state(session_task: pd.DataFrame) -> pd.DataFrame:
    meta = session_task.groupby("participant_id", as_index=False).agg(
        {
            "patient_root": "first",
            "corpus": "first",
            "subtype": mode_or_first,
            "wab_aq": "mean",
            "age_years": "mean",
            "sex": mode_or_first,
            "is_control": "max",
        }
    )
    z = session_task.pivot(index="participant_id", columns="task", values="observed_control_z")
    cov = session_task.pivot(index="participant_id", columns="task", values="observed_concept_coverage_frac")
    tokens = session_task.pivot(index="participant_id", columns="task", values="observed_n_tokens")
    utts = session_task.pivot(index="participant_id", columns="task", values="n_utterances")
    mutt = session_task.pivot(index="participant_id", columns="task", values="mean_utt_tokens")

    state = meta.set_index("participant_id")
    for task in z.columns:
        state[f"z_{task}"] = z[task]
        state[f"coverage_{task}"] = cov[task]
        state[f"tokens_{task}"] = tokens[task]
        state[f"utts_{task}"] = utts[task]
        state[f"meanutt_{task}"] = mutt[task]

    z_cols = [f"z_{t}" for t in z.columns]
    cov_cols = [f"coverage_{t}" for t in cov.columns]
    token_cols = [f"tokens_{t}" for t in tokens.columns]
    utt_cols = [f"utts_{t}" for t in utts.columns]
    mutt_cols = [f"meanutt_{t}" for t in mutt.columns]

    state["content_mean_z"] = state[z_cols].mean(axis=1)
    state["content_min_z"] = state[z_cols].min(axis=1)
    state["content_max_z"] = state[z_cols].max(axis=1)
    state["content_sd_z"] = state[z_cols].std(axis=1)
    state["coverage_mean"] = state[cov_cols].mean(axis=1)
    state["tokens_mean"] = state[token_cols].mean(axis=1)
    state["utts_mean"] = state[utt_cols].mean(axis=1)
    state["meanutt_mean"] = state[mutt_cols].mean(axis=1)
    state["n_tasks"] = state[z_cols].notna().sum(axis=1)

    core_z = [f"z_{t}" for t in CORE_TASKS if f"z_{t}" in state.columns]
    state["core_content_mean_z"] = state[core_z].mean(axis=1)
    state["core_n_tasks"] = state[core_z].notna().sum(axis=1)
    return state.reset_index()


def pairwise_task_correlations(state: pd.DataFrame) -> pd.DataFrame:
    tasks = sorted(c.removeprefix("z_") for c in state.columns if c.startswith("z_"))
    rows = []
    for i, a in enumerate(tasks):
        for b in tasks[i + 1:]:
            cols = [f"z_{a}", f"z_{b}"]
            sub = state[cols].dropna()
            rows.append(
                {
                    "task_a": a,
                    "task_b": b,
                    "n": int(len(sub)),
                    "r": pearson_safe(sub[cols[0]], sub[cols[1]]) if len(sub) >= 3 else float("nan"),
                }
            )
    return pd.DataFrame(rows).sort_values("r", ascending=False)


def cronbach_alpha(frame: pd.DataFrame, cols: list[str]) -> float:
    mat = frame[cols].dropna().astype(float)
    if mat.shape[0] < 10 or mat.shape[1] < 2:
        return float("nan")
    item_vars = mat.var(axis=0, ddof=1).sum()
    total_var = mat.sum(axis=1).var(ddof=1)
    k = mat.shape[1]
    if total_var == 0:
        return float("nan")
    return float(k / (k - 1) * (1 - item_vars / total_var))


def split_half_reliability(state: pd.DataFrame) -> pd.DataFrame:
    rows = []
    splits = {
        "picture_vs_story_procedure": (
            ["z_Cat", "z_Umbrella", "z_Window"],
            ["z_Cinderella", "z_Sandwich"],
        ),
        "narrative_vs_procedure": (
            ["z_Cat", "z_Umbrella", "z_Window", "z_Cinderella"],
            ["z_Sandwich"],
        ),
        "short_sequences_vs_cinderella": (
            ["z_Cat", "z_Umbrella", "z_Window"],
            ["z_Cinderella"],
        ),
    }
    for name, (left_cols, right_cols) in splits.items():
        left_cols = [c for c in left_cols if c in state.columns]
        right_cols = [c for c in right_cols if c in state.columns]
        if not left_cols or not right_cols:
            continue
        sub = state[left_cols + right_cols + ["wab_aq"]].dropna()
        if len(sub) < 20:
            continue
        left = sub[left_cols].mean(axis=1)
        right = sub[right_cols].mean(axis=1)
        rows.append(
            {
                "split": name,
                "n": int(len(sub)),
                "r_between_halves": pearson_safe(left, right),
                "r_left_wab_aq": pearson_safe(left, sub["wab_aq"]),
                "r_right_wab_aq": pearson_safe(right, sub["wab_aq"]),
            }
        )
    core_cols = [f"z_{t}" for t in CORE_TASKS if f"z_{t}" in state.columns]
    complete = state.dropna(subset=core_cols)
    rows.append(
        {
            "split": "cronbach_alpha_core_tasks",
            "n": int(len(complete)),
            "r_between_halves": cronbach_alpha(state, core_cols),
            "r_left_wab_aq": pearson_safe(complete[core_cols].mean(axis=1), complete["wab_aq"]) if len(complete) else float("nan"),
            "r_right_wab_aq": float("nan"),
        }
    )
    return pd.DataFrame(rows)


def model_rows(state: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    work = state.dropna(subset=["wab_aq", "patient_root"]).copy()
    work = work[~work["is_control"].astype(bool)].copy()
    work = work[work["core_n_tasks"] >= 3].reset_index(drop=True)
    z_cols = [c for c in work.columns if c.startswith("z_") and work[c].notna().any()]
    core_z_cols = [f"z_{t}" for t in CORE_TASKS if f"z_{t}" in work.columns]
    coverage_cols = [c for c in work.columns if c.startswith("coverage_") and work[c].notna().any()]
    verbosity = ["tokens_mean", "utts_mean", "meanutt_mean", "n_tasks"]
    summaries = ["content_mean_z", "content_min_z", "content_max_z", "content_sd_z", "coverage_mean", "core_content_mean_z", "core_n_tasks"]
    setups = {
        "verbosity_summary": ({"verbosity": verbosity}, None),
        "content_summary": ({"content": summaries}, None),
        "core_task_vector_z": ({"content": core_z_cols}, None),
        "all_task_vector_z": ({"content": z_cols}, None),
        "coverage_vector": ({"content": coverage_cols}, None),
        "content+verbosity": ({"content": summaries + core_z_cols, "verbosity": verbosity}, None),
        "subtype_only": ({}, ["subtype"]),
        "subtype+content": ({"content": summaries + core_z_cols}, ["subtype"]),
    }
    rows = []
    for setup, (blocks, cats) in setups.items():
        sub = work.copy()
        if cats:
            sub = sub.dropna(subset=cats).reset_index(drop=True)
        blocks = {k: [c for c in v if c in sub.columns] for k, v in blocks.items()}
        blocks = {k: v for k, v in blocks.items() if v}
        if not blocks and not cats:
            continue
        y, pred = cross_val_predict_regressor(
            sub,
            "wab_aq",
            blocks,
            categorical_cols=cats,
            group_col="patient_root",
            cv_mode="group",
            n_splits=cv_folds,
        )
        r_mean, r_lo, r_hi = bootstrap_ci(
            y,
            pred,
            pearson_safe,
            groups=sub["patient_root"].astype(str).to_numpy(),
            n_boot=500,
            seed=0,
        )
        rows.append(
            {
                "setup": setup,
                **regression_summary(y, pred),
                "r_boot_mean": r_mean,
                "r_boot_lo": r_lo,
                "r_boot_hi": r_hi,
                "n_sessions": int(len(sub)),
                "n_patients": int(sub["patient_root"].nunique()),
            }
        )
    return pd.DataFrame(rows).sort_values("r", ascending=False)


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
    session_task = aggregate_session_task(df)
    state = build_session_state(session_task)

    session_task.to_csv(out_dir / "session_task_content.csv", index=False)
    state.to_csv(out_dir / "patient_content_state.csv", index=False)

    noncontrol_state = state[~state["is_control"].astype(bool)].copy()
    pairwise = pairwise_task_correlations(noncontrol_state)
    pairwise.to_csv(out_dir / "pairwise_task_correlations.csv", index=False)

    split_half = split_half_reliability(
        state[state["wab_aq"].notna() & ~state["is_control"].astype(bool)].copy()
    )
    split_half.to_csv(out_dir / "split_half_reliability.csv", index=False)

    models = model_rows(state, cv_folds=args.cv_folds)
    models.to_csv(out_dir / "patient_state_models.csv", index=False)

    lines = ["# Cross-Prompt Content State Reliability\n"]
    lines.append(f"- Session-level rows: {len(state)}")
    pwa_wab = state[state["wab_aq"].notna() & ~state["is_control"].astype(bool)]
    lines.append(f"- WAB-labeled non-control sessions with >=3 core tasks: {int((pwa_wab['core_n_tasks'] >= 3).sum())}")
    lines.append("\n## Patient-Level WAB Models\n")
    lines.append(md_table(models[["setup", "n", "mae", "r", "r_boot_lo", "r_boot_hi", "n_patients"]]))
    lines.append("\n## Split-Half Reliability\n")
    lines.append(md_table(split_half))
    lines.append("\n## Strongest Pairwise Task Correlations\n")
    lines.append(md_table(pairwise.head(10)))
    lines.append("\n## Weakest Pairwise Task Correlations\n")
    lines.append(md_table(pairwise.tail(10)))
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
