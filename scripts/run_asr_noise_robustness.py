"""ASR/noise robustness simulation for content-state scoring.

A clinic-facing discourse biomarker must survive imperfect transcripts. This
script simulates token deletion/substitution noise and measures how well noisy
content state preserves the original content state and WAB-AQ signal.
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

from scripts.run_cross_prompt_content import (  # noqa: E402
    CONCEPTS,
    chat_tokens,
    concept_hits,
    parse_task_utterances,
)
from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


CORE_TASKS = ["Cat", "Cinderella", "Sandwich", "Umbrella", "Window"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--segments", default="outputs/cross_prompt_content/task_segments.csv", type=Path)
    p.add_argument("--state", default="outputs/cross_prompt_state/patient_content_state.csv", type=Path)
    p.add_argument("--norms", default="outputs/cross_prompt_content/control_norms.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/asr_noise_robustness", type=Path)
    p.add_argument("--replicates", default=50, type=int)
    p.add_argument("--seed", default=23, type=int)
    return p.parse_args()


def segment_tokens(df: pd.DataFrame) -> dict[tuple[str, str], list[str]]:
    cache: dict[str, dict[str, list[str]]] = {}
    out: dict[tuple[str, str], list[str]] = {}
    for path, task in df[["file_path", "task"]].drop_duplicates().itertuples(index=False):
        if path not in cache:
            segments = parse_task_utterances(Path(path))
            cache[path] = {
                t: chat_tokens(" ".join(utts), include_targets=False)
                for t, utts in segments.items()
            }
        out[(path, task)] = cache.get(path, {}).get(task, [])
    return out


def corrupt_tokens(tokens: list[str], delete_p: float, substitute_p: float, rng: np.random.Generator) -> list[str]:
    out = []
    for tok in tokens:
        if rng.random() < delete_p:
            continue
        if rng.random() < substitute_p:
            out.append("asrerror")
        else:
            out.append(tok)
    return out


def score_noisy_segments(
    base: pd.DataFrame,
    token_map: dict[tuple[str, str], list[str]],
    norms: pd.DataFrame,
    delete_p: float,
    substitute_p: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    norm_lookup = {
        (row.task, row.prefix): (row.mean_coverage_frac, row.sd_coverage_frac)
        for row in norms.itertuples(index=False)
    }
    rows = []
    for row in base.itertuples(index=False):
        tokens = token_map.get((row.file_path, row.task), [])
        noisy = corrupt_tokens(tokens, delete_p, substitute_p, rng)
        hits = concept_hits(noisy, row.task)
        coverage_frac = sum(hits.values()) / len(CONCEPTS[row.task])
        mean, sd = norm_lookup.get((row.task, "observed"), (0.0, 1.0))
        sd = sd or 1.0
        rows.append(
            {
                "participant_id": row.participant_id,
                "patient_root": row.patient_root,
                "task": row.task,
                "wab_aq": row.wab_aq,
                "original_control_z": row.observed_control_z,
                "noisy_coverage_frac": coverage_frac,
                "noisy_control_z": (coverage_frac - mean) / sd,
                "n_tokens_original": len(tokens),
                "n_tokens_noisy": len(noisy),
            }
        )
    return pd.DataFrame(rows)


def aggregate_state(scored: pd.DataFrame) -> pd.DataFrame:
    pivot = scored.pivot_table(index="participant_id", columns="task", values="noisy_control_z", aggfunc="mean")
    orig = scored.pivot_table(index="participant_id", columns="task", values="original_control_z", aggfunc="mean")
    meta = scored.groupby("participant_id", as_index=False).agg(
        patient_root=("patient_root", "first"),
        wab_aq=("wab_aq", "mean"),
    ).set_index("participant_id")
    state = meta.copy()
    for task in CORE_TASKS:
        state[f"noisy_z_{task}"] = pivot[task] if task in pivot else np.nan
        state[f"original_z_{task}"] = orig[task] if task in orig else np.nan
    noisy_cols = [f"noisy_z_{t}" for t in CORE_TASKS]
    orig_cols = [f"original_z_{t}" for t in CORE_TASKS]
    state["noisy_core_content_mean_z"] = state[noisy_cols].mean(axis=1)
    state["original_core_content_mean_z"] = state[orig_cols].mean(axis=1)
    state["n_tasks"] = state[noisy_cols].notna().sum(axis=1)
    return state.reset_index()


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    rng = np.random.default_rng(args.seed)
    segments = pd.read_csv(args.segments)
    base = segments[
        segments["wab_aq"].notna()
        & ~segments["is_control"].astype(bool)
        & segments["task"].isin(CORE_TASKS)
    ].copy()
    norms = pd.read_csv(args.norms)
    token_map = segment_tokens(base)

    levels = [
        (0.00, 0.00),
        (0.05, 0.00),
        (0.10, 0.00),
        (0.20, 0.00),
        (0.30, 0.00),
        (0.40, 0.00),
        (0.50, 0.00),
        (0.10, 0.05),
        (0.20, 0.10),
        (0.30, 0.15),
    ]
    rows = []
    state_rows = []
    for delete_p, substitute_p in levels:
        reps = 1 if delete_p == 0 and substitute_p == 0 else args.replicates
        for rep in range(reps):
            scored = score_noisy_segments(base, token_map, norms, delete_p, substitute_p, rng)
            state = aggregate_state(scored)
            state["delete_p"] = delete_p
            state["substitute_p"] = substitute_p
            state["replicate"] = rep
            state_rows.append(state)
            eval_df = state[state["n_tasks"] >= 3].dropna(subset=["wab_aq", "noisy_core_content_mean_z", "original_core_content_mean_z"])
            rows.append(
                {
                    "delete_p": delete_p,
                    "substitute_p": substitute_p,
                    "replicate": rep,
                    "n": int(len(eval_df)),
                    "mean_token_retention": float(scored["n_tokens_noisy"].sum() / max(scored["n_tokens_original"].sum(), 1)),
                    "r_noisy_vs_original_state": pearson_safe(
                        eval_df["noisy_core_content_mean_z"],
                        eval_df["original_core_content_mean_z"],
                    ),
                    "r_noisy_state_wab": pearson_safe(eval_df["noisy_core_content_mean_z"], eval_df["wab_aq"]),
                    "r_original_state_wab": pearson_safe(eval_df["original_core_content_mean_z"], eval_df["wab_aq"]),
                    "mean_abs_state_error": float(
                        np.mean(np.abs(eval_df["noisy_core_content_mean_z"] - eval_df["original_core_content_mean_z"]))
                    ),
                }
            )
    results = pd.DataFrame(rows)
    results.to_csv(out_dir / "noise_replicate_results.csv", index=False)
    pd.concat(state_rows, ignore_index=True).to_csv(out_dir / "noisy_state_replicates.csv", index=False)
    summary = results.groupby(["delete_p", "substitute_p"], as_index=False).agg(
        n=("n", "mean"),
        mean_token_retention=("mean_token_retention", "mean"),
        r_noisy_vs_original_state_mean=("r_noisy_vs_original_state", "mean"),
        r_noisy_vs_original_state_p05=("r_noisy_vs_original_state", lambda s: float(s.quantile(0.05))),
        r_noisy_state_wab_mean=("r_noisy_state_wab", "mean"),
        r_noisy_state_wab_p05=("r_noisy_state_wab", lambda s: float(s.quantile(0.05))),
        mean_abs_state_error=("mean_abs_state_error", "mean"),
    )
    summary.to_csv(out_dir / "noise_summary.csv", index=False)
    print(summary.to_string(index=False))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
