"""Coverage-risk curves for top-k clarification policies.

Top-k candidate generation can recover many known target concepts when an
oracle says when to ask. This script asks the clinically harder question:
how much target recovery is available at fixed safety/burden limits?
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from scripts.run_cross_prompt_content import CONCEPTS  # noqa: E402
from scripts.run_topk_clarification_benchmark import build_reference_stats  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ranked-candidates",
        default="outputs/topk_clarification_benchmark/ranked_candidates.csv",
        type=Path,
    )
    parser.add_argument(
        "--reference-features",
        default="outputs/error_aware_reconstruction/segment_error_features.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/clarification_coverage_risk",
        type=Path,
    )
    parser.add_argument("--max-k", default=5, type=int)
    return parser.parse_args()


def enrich_scores(ranked: pd.DataFrame, ref: pd.DataFrame) -> pd.DataFrame:
    stats = build_reference_stats(ref)
    out = ranked.copy()
    median = []
    task_concepts = []
    for _, row in out.iterrows():
        task = str(row["task"])
        task_stats = stats.get(task, {})
        median.append(float(task_stats.get("median_control_concepts", 0.0)))
        task_concepts.append(len(CONCEPTS.get(task, {})))
    out["median_control_concepts"] = median
    out["n_task_concepts"] = task_concepts
    out["content_gap_score"] = out["median_control_concepts"] - out["input_concept_count"]
    out["low_content_score"] = -out["input_concept_count"]
    out["missing_fraction_score"] = out["candidate_count"] / out["n_task_concepts"].clip(lower=1)
    out["has_controller_prediction"] = out["controller_pred_action"].fillna("").ne("")
    return out


def score_policy(group: pd.DataFrame, offered: pd.Series, k: int, label: str) -> dict[str, float | int | str]:
    offered = offered.astype(bool) & (group["candidate_count"] > 0)
    positive = group["target_gain_n"] > 0
    hit = group[f"hit_at_{k}"].astype(bool)
    target_n = group["target_gain_n"].astype(float)
    concept_hits = group[f"target_recall_at_{k}"].astype(float) * target_n
    unknown_no_gain = (pd.to_numeric(group["unknown_intent_error_count"], errors="coerce").fillna(0) > 0) & ~positive
    low_error = group["bucket"].astype(str).eq("low_error_content_control")

    n_offered = int(offered.sum())
    useful_hits = int((offered & hit & positive).sum())
    recovered_targets = float(concept_hits[offered].sum())
    return {
        "gate": label,
        "k": k,
        "n_items": int(len(group)),
        "n_positive_items": int(positive.sum()),
        "n_offered": n_offered,
        "offer_rate": float(offered.mean()),
        "useful_offer_precision": float(useful_hits / max(n_offered, 1)),
        "positive_item_hit_recall": float(useful_hits / max(int(positive.sum()), 1)),
        "target_concept_recall": float(recovered_targets / max(float(target_n.sum()), 1.0)),
        "unnecessary_offer_rate": float((offered & ~positive).sum() / max(n_offered, 1)),
        "unknown_no_gain_item_offer_rate": float(
            (offered & unknown_no_gain).sum() / max(int(unknown_no_gain.sum()), 1)
        ),
        "low_error_control_item_offer_rate": float(
            (offered & low_error).sum() / max(int(low_error.sum()), 1)
        ),
        "turns_per_useful_hit": float(n_offered / max(useful_hits, 1)),
        "options_per_target_recovered": float((n_offered * k) / max(recovered_targets, 1.0)),
    }


def sweep_thresholds(ranked: pd.DataFrame, max_k: int) -> pd.DataFrame:
    rows = []
    score_cols = ["content_gap_score", "low_content_score", "missing_fraction_score"]
    for strategy, group in ranked.groupby("strategy"):
        group = group.reset_index(drop=True)
        for k in range(1, max_k + 1):
            static_gates = {
                "offer_all": pd.Series(True, index=group.index),
                "oracle_any_target_gain": group["target_gain_n"] > 0,
                "oracle_safe_known_gain": (group["target_gain_n"] > 0)
                & (pd.to_numeric(group["unknown_intent_error_count"], errors="coerce").fillna(0) == 0),
            }
            if bool(group["has_controller_prediction"].any()):
                static_gates["controller_not_preserve"] = group["controller_pred_action"].isin(
                    ["clarify", "rewrite"]
                )
                static_gates["controller_clarify_only"] = group["controller_pred_action"].eq("clarify")
            for label, offered in static_gates.items():
                row = score_policy(group, offered, k, label)
                row["strategy"] = strategy
                row["threshold"] = np.nan
                row["score"] = ""
                rows.append(row)

            for score_col in score_cols:
                values = sorted(pd.to_numeric(group[score_col], errors="coerce").dropna().unique(), reverse=True)
                for threshold in values:
                    offered = pd.to_numeric(group[score_col], errors="coerce") >= float(threshold)
                    row = score_policy(group, offered, k, f"{score_col}>={threshold:.3f}")
                    row["strategy"] = strategy
                    row["threshold"] = float(threshold)
                    row["score"] = score_col
                    rows.append(row)
    return pd.DataFrame(rows)


def build_frontier(curves: pd.DataFrame) -> pd.DataFrame:
    constraints = [
        {"constraint": "strict", "max_unnecessary": 0.25, "max_unknown_no_gain": 0.05},
        {"constraint": "moderate", "max_unnecessary": 0.40, "max_unknown_no_gain": 0.10},
        {"constraint": "liberal", "max_unnecessary": 0.60, "max_unknown_no_gain": 0.20},
    ]
    rows = []
    deployable = curves[~curves["gate"].astype(str).str.startswith("oracle_")].copy()
    for constraint in constraints:
        ok = deployable[
            (deployable["unnecessary_offer_rate"] <= constraint["max_unnecessary"])
            & (deployable["unknown_no_gain_item_offer_rate"] <= constraint["max_unknown_no_gain"])
        ].copy()
        if ok.empty:
            rows.append({**constraint, "status": "no_policy_met_constraint"})
            continue
        best = ok.sort_values(
            [
                "positive_item_hit_recall",
                "target_concept_recall",
                "useful_offer_precision",
                "offer_rate",
            ],
            ascending=[False, False, False, True],
        ).iloc[0].to_dict()
        best.update(constraint)
        best["status"] = "ok"
        rows.append(best)
    return pd.DataFrame(rows)


def build_recovery_burden(curves: pd.DataFrame) -> pd.DataFrame:
    rows = []
    targets = [0.50, 0.70, 0.80, 0.90]
    subsets = {
        "deployable": curves[~curves["gate"].astype(str).str.startswith("oracle_")],
        "oracle_upper": curves[curves["gate"].astype(str).str.startswith("oracle_")],
    }
    for subset_name, subset in subsets.items():
        for target in targets:
            ok = subset[subset["positive_item_hit_recall"] >= target].copy()
            if ok.empty:
                rows.append(
                    {
                        "policy_family": subset_name,
                        "target_positive_item_recall": target,
                        "status": "not_reached",
                    }
                )
                continue
            best = ok.sort_values(
                [
                    "n_offered",
                    "unnecessary_offer_rate",
                    "unknown_no_gain_item_offer_rate",
                    "useful_offer_precision",
                ],
                ascending=[True, True, True, False],
            ).iloc[0].to_dict()
            best["policy_family"] = subset_name
            best["target_positive_item_recall"] = target
            best["status"] = "ok"
            rows.append(best)
    return pd.DataFrame(rows)


def write_summary(
    out_dir: Path,
    curves: pd.DataFrame,
    frontier: pd.DataFrame,
    burden: pd.DataFrame,
) -> None:
    best_any = curves.sort_values(
        ["positive_item_hit_recall", "useful_offer_precision", "offer_rate"],
        ascending=[False, False, True],
    ).head(20)
    best_deployable = curves[
        ~curves["gate"].astype(str).str.startswith("oracle_")
    ].sort_values(
        ["positive_item_hit_recall", "useful_offer_precision", "offer_rate"],
        ascending=[False, False, True],
    ).head(20)
    lines = [
        "# Clarification Coverage-Risk Curves",
        "",
        f"- Policy rows: {len(curves)}",
        f"- Items: {int(curves['n_items'].max()) if len(curves) else 0}",
        "",
        "## Best Policies Overall",
        "",
        md_table(best_any.round(3)),
        "",
        "## Best Deployable Policies",
        "",
        md_table(best_deployable.round(3)),
        "",
        "## Deployable Frontier Under Risk Caps",
        "",
        md_table(frontier.round(3)),
        "",
        "## Question Burden To Reach Target Recovery",
        "",
        md_table(burden.round(3)),
        "",
        "## Interpretation",
        "",
        "The clinically relevant operating point is not the highest recall policy; "
        "it is the best recall available while keeping unnecessary clarification "
        "and unknown-intent offers below a tolerable burden. If no deployable "
        "policy survives strict caps, candidate generation is not the bottleneck; "
        "safe triggering and human confirmation are.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    ranked = pd.read_csv(args.ranked_candidates)
    ref = pd.read_csv(args.reference_features)
    enriched = enrich_scores(ranked, ref)
    curves = sweep_thresholds(enriched, args.max_k)
    frontier = build_frontier(curves)
    burden = build_recovery_burden(curves)
    enriched.to_csv(out_dir / "ranked_candidates_with_scores.csv", index=False)
    curves.to_csv(out_dir / "coverage_risk_curves.csv", index=False)
    frontier.to_csv(out_dir / "risk_frontier.csv", index=False)
    burden.to_csv(out_dir / "recovery_burden_targets.csv", index=False)
    write_summary(out_dir, curves, frontier, burden)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
