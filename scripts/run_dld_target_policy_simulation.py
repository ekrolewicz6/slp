"""DLD residual-state target policy simulation.

This is not a treatment recommendation. It asks which measurable language
features a state model would nominate under different target-selection rules.
The input residuals are z-like deviations from age-matched TD norms produced
by scripts/run_dld_state_screening.py.
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


DESIRED_HIGH = {
    "mlu_words": "utterance_length",
    "mlu_morphemes": "utterance_length",
    "ndw": "lexical_variety",
    "verbs_per_utterance": "predicate_structure",
    "ttr": "lexical_variety",
    "function_word_ratio": "grammar_function_words",
    "utt_len_mean": "utterance_length",
    "utt_len_std": "utterance_variability",
    "utt_len_p50": "utterance_length",
    "utt_len_p90": "utterance_length",
    "pos_v_frac": "predicate_structure",
    "pos_det_frac": "grammar_function_words",
    "pos_prep_frac": "grammar_function_words",
    "rel_SUBJ_frac": "argument_structure",
    "rel_OBJ_frac": "argument_structure",
    "rel_MOD_frac": "elaboration",
    "mean_dep_distance": "syntactic_complexity",
}

DESIRED_LOW = {
    "single_word_ratio": "low_output",
    "repetition_per_utt": "disfluency_repair",
    "retracing_per_utt": "disfluency_repair",
    "pause_per_utt": "fluency_timing",
    "filler_per_utt": "fluency_timing",
}

AMBIGUOUS = {
    "hapax_ratio": "lexical_distribution",
    "pos_n_frac": "lexical_distribution",
    "pos_pro_frac": "reference_tracking",
}

GENERIC_PRIORITY = [
    "mlu_words",
    "verbs_per_utterance",
    "ndw",
    "function_word_ratio",
    "rel_SUBJ_frac",
    "rel_OBJ_frac",
    "utt_len_p90",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clusters",
        default="outputs/dld_state_screening/dld_age_residual_clusters.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/dld_target_policy_simulation", type=Path)
    parser.add_argument("--top-k", default=5, type=int)
    parser.add_argument("--seed", default=0, type=int)
    return parser.parse_args()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def md_table(df: pd.DataFrame, max_rows: int | None = None, float_digits: int = 3) -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "_No rows._"
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.{float_digits}f}")
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def target_candidates(row: pd.Series) -> pd.DataFrame:
    rows = []
    for feature, target_class in DESIRED_HIGH.items():
        if feature not in row or pd.isna(row[feature]):
            continue
        residual = float(row[feature])
        deficit = max(0.0, -residual)
        if deficit > 0:
            rows.append(
                {
                    "feature": feature,
                    "target_class": target_class,
                    "direction": "increase",
                    "residual_z": residual,
                    "deficit_z": deficit,
                }
            )
    for feature, target_class in DESIRED_LOW.items():
        if feature not in row or pd.isna(row[feature]):
            continue
        residual = float(row[feature])
        deficit = max(0.0, residual)
        if deficit > 0:
            rows.append(
                {
                    "feature": feature,
                    "target_class": target_class,
                    "direction": "decrease",
                    "residual_z": residual,
                    "deficit_z": deficit,
                }
            )
    # Ambiguous features are tracked but not eligible for target selection.
    for feature, target_class in AMBIGUOUS.items():
        if feature not in row or pd.isna(row[feature]):
            continue
        rows.append(
            {
                "feature": feature,
                "target_class": target_class,
                "direction": "review_only",
                "residual_z": float(row[feature]),
                "deficit_z": 0.0,
            }
        )
    cand = pd.DataFrame(rows)
    if cand.empty:
        return cand
    cand["near_threshold_score"] = 1 - (cand["deficit_z"] - 1.0).abs()
    cand["learning_utility"] = cand["deficit_z"] * np.exp(-0.5 * (cand["deficit_z"] - 1.0) ** 2)
    cand["too_easy"] = cand["deficit_z"] < 0.5
    cand["too_hard"] = cand["deficit_z"] > 2.5
    cand["eligible"] = cand["deficit_z"] >= 0.25
    return cand


def select_policy(candidates: pd.DataFrame, policy: str, top_k: int, seed: int) -> pd.DataFrame:
    eligible = candidates[candidates["eligible"]].copy()
    if eligible.empty:
        return eligible
    if policy == "near_threshold":
        selected = eligible.sort_values(["near_threshold_score", "learning_utility"], ascending=False)
    elif policy == "highest_deficit":
        selected = eligible.sort_values("deficit_z", ascending=False)
    elif policy == "easiest_deficit":
        selected = eligible.sort_values("deficit_z", ascending=True)
    elif policy == "high_utility":
        selected = eligible.sort_values("learning_utility", ascending=False)
    elif policy == "generic_priority":
        rank = {feature: idx for idx, feature in enumerate(GENERIC_PRIORITY)}
        selected = eligible.assign(generic_rank=eligible["feature"].map(rank).fillna(999))
        selected = selected.sort_values(["generic_rank", "deficit_z"], ascending=[True, False])
    elif policy == "random_eligible":
        selected = eligible.sample(frac=1.0, random_state=seed)
    else:
        raise ValueError(policy)
    return selected.head(top_k).assign(policy=policy)


def build_selected(clusters: pd.DataFrame, top_k: int, seed: int) -> pd.DataFrame:
    policies = [
        "near_threshold",
        "high_utility",
        "highest_deficit",
        "easiest_deficit",
        "generic_priority",
        "random_eligible",
    ]
    rows = []
    for i, (_, row) in enumerate(clusters.iterrows()):
        cand = target_candidates(row)
        if cand.empty:
            continue
        for policy in policies:
            selected = select_policy(cand, policy, top_k, seed + i)
            if selected.empty:
                continue
            selected = selected.assign(
                participant_root=row["participant_root"],
                corpus=row["corpus"],
                cluster=int(row["cluster"]),
                age_mean=float(row["age_mean"]),
            )
            rows.append(selected)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def summarize(selected: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    policy = (
        selected.groupby("policy")
        .agg(
            n_targets=("feature", "size"),
            n_participants=("participant_root", "nunique"),
            mean_deficit_z=("deficit_z", "mean"),
            mean_learning_utility=("learning_utility", "mean"),
            pct_too_easy=("too_easy", "mean"),
            pct_too_hard=("too_hard", "mean"),
            n_target_classes=("target_class", "nunique"),
        )
        .reset_index()
        .sort_values("mean_learning_utility", ascending=False)
    )
    by_cluster = (
        selected.groupby(["cluster", "policy"])
        .agg(
            n_participants=("participant_root", "nunique"),
            mean_age=("age_mean", "mean"),
            mean_deficit_z=("deficit_z", "mean"),
            mean_learning_utility=("learning_utility", "mean"),
            top_classes=("target_class", lambda s: ", ".join(s.value_counts().head(4).index.tolist())),
        )
        .reset_index()
        .sort_values(["cluster", "mean_learning_utility"], ascending=[True, False])
    )
    class_dist = (
        selected.groupby(["policy", "target_class"])
        .size()
        .rename("n")
        .reset_index()
        .sort_values(["policy", "n"], ascending=[True, False])
    )
    totals = class_dist.groupby("policy")["n"].transform("sum")
    class_dist["pct"] = class_dist["n"] / totals
    return policy, by_cluster, class_dist


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    clusters = pd.read_csv(args.clusters)
    selected = build_selected(clusters, args.top_k, args.seed)
    policy, by_cluster, class_dist = summarize(selected)

    selected.to_csv(out_dir / "selected_targets_by_policy.csv", index=False)
    policy.to_csv(out_dir / "policy_summary.csv", index=False)
    by_cluster.to_csv(out_dir / "policy_by_cluster.csv", index=False)
    class_dist.to_csv(out_dir / "target_class_distribution.csv", index=False)

    lines = [
        "# DLD Target Policy Simulation",
        "",
        f"- Participants: {clusters['participant_root'].nunique()}",
        f"- Top-k targets per participant per policy: {args.top_k}",
        "",
        "## Policy Summary",
        "",
        md_table(policy),
        "",
        "## By Cluster",
        "",
        md_table(by_cluster, max_rows=30),
        "",
        "## Target Class Distribution",
        "",
        md_table(class_dist, max_rows=60),
        "",
        "## Interpretation",
        "",
        "- This is a target-discovery simulation, not evidence of treatment efficacy.",
        "- Near-threshold and high-utility policies prefer deficits that are measurable but not extreme.",
        "- Highest-deficit policies often nominate severe low-output targets that may be clinically real but less immediately changeable.",
        "- The next required experiment is to connect these nominated targets to longitudinal change or real intervention outcomes.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print((out_dir / "summary.md").resolve())


if __name__ == "__main__":
    main()
