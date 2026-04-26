"""Benchmark top-k clarification candidates for reconstruction safety.

The safety-controller experiments show that automatic rewriting is too risky
from ASR text alone. A safer product can ask targeted clarification questions
instead: "Did you mean X, Y, or Z?" This script tests whether simple prompt
and context priors can put the intended known target concept into a short list
without over-offering suggestions on low-error or unknown-intent items.
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

from scripts.build_reconstruction_safety_benchmark import (  # noqa: E402
    concept_set_from_text,
    md_table,
)
from scripts.run_cross_prompt_content import CONCEPTS  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--items-path",
        default="outputs/reconstruction_safety_benchmark/benchmark_items.csv",
        type=Path,
    )
    parser.add_argument(
        "--reference-features",
        default="outputs/error_aware_reconstruction/segment_error_features.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/topk_clarification_benchmark", type=Path)
    parser.add_argument("--max-k", default=5, type=int)
    parser.add_argument("--input-source", choices=["raw", "asr"], default="raw")
    parser.add_argument("--predictions-path", type=Path, default=None)
    parser.add_argument("--prediction-model", default="asr_text")
    return parser.parse_args()


def json_set(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return set()
    if isinstance(parsed, list):
        return {str(x) for x in parsed}
    return set()


def concept_col(task: str, concept: str) -> str:
    return f"observed_{task.lower()}_{concept}"


def build_reference_stats(ref: pd.DataFrame) -> dict:
    stats: dict[str, dict] = {}
    for task, concepts in CONCEPTS.items():
        task_ref = ref[ref["task"].eq(task)].copy()
        if task_ref.empty:
            continue
        control_ref = task_ref[task_ref.get("is_control", False).astype(bool)]
        prior_ref = control_ref if len(control_ref) >= 20 else task_ref
        priors = {}
        present_wab_mean = {}
        for concept in concepts:
            col = concept_col(task, concept)
            if col not in task_ref.columns:
                priors[concept] = 0.0
                present_wab_mean[concept] = np.nan
                continue
            priors[concept] = float(pd.to_numeric(prior_ref[col], errors="coerce").fillna(0).mean())
            with_wab = task_ref[
                (pd.to_numeric(task_ref[col], errors="coerce").fillna(0) > 0)
                & task_ref["wab_aq"].notna()
                & ~task_ref.get("is_control", False).astype(bool)
            ]
            present_wab_mean[concept] = float(with_wab["wab_aq"].mean()) if len(with_wab) else np.nan

        conditional = {obs: {} for obs in concepts}
        for obs in concepts:
            obs_col = concept_col(task, obs)
            if obs_col not in task_ref.columns:
                continue
            obs_vec = pd.to_numeric(task_ref[obs_col], errors="coerce").fillna(0) > 0
            n_obs = int(obs_vec.sum())
            for cand in concepts:
                cand_col = concept_col(task, cand)
                if cand_col not in task_ref.columns:
                    conditional[obs][cand] = priors.get(cand, 0.0)
                    continue
                cand_vec = pd.to_numeric(task_ref[cand_col], errors="coerce").fillna(0) > 0
                n_both = int((obs_vec & cand_vec).sum())
                conditional[obs][cand] = float((n_both + 0.5) / (n_obs + 1.0))

        median_control = float(prior_ref["observed_concept_coverage"].median())
        stats[task] = {
            "priors": priors,
            "conditional": conditional,
            "present_wab_mean": present_wab_mean,
            "median_control_concepts": median_control,
        }
    return stats


def input_concepts(row: pd.Series, input_source: str) -> set[str]:
    task = str(row["task"])
    if input_source == "asr" and "asr_text" in row and pd.notna(row.get("asr_text")):
        return concept_set_from_text(str(row.get("asr_text", "")), task, include_targets=False)
    return json_set(row.get("observed_concepts"))


def rank_candidates(
    task: str,
    observed: set[str],
    wab_aq: float,
    strategy: str,
    stats: dict,
) -> list[str]:
    if task not in CONCEPTS:
        return []
    task_stats = stats.get(task, {})
    priors = task_stats.get("priors", {})
    conditional = task_stats.get("conditional", {})
    present_wab_mean = task_stats.get("present_wab_mean", {})
    candidates = [concept for concept in CONCEPTS[task] if concept not in observed]

    def prior_score(concept: str) -> float:
        return float(priors.get(concept, 0.0))

    def conditional_score(concept: str) -> float:
        if not observed:
            return prior_score(concept)
        vals = [conditional.get(obs, {}).get(concept, prior_score(concept)) for obs in observed]
        return float(np.mean(vals)) if vals else prior_score(concept)

    def severity_score(concept: str) -> float:
        mean_wab = present_wab_mean.get(concept, np.nan)
        if not np.isfinite(wab_aq) or not np.isfinite(mean_wab):
            return prior_score(concept)
        return -abs(float(wab_aq) - float(mean_wab))

    if strategy == "control_prior":
        key = lambda c: (prior_score(c), c)
    elif strategy == "context_cooccurrence":
        key = lambda c: (conditional_score(c), prior_score(c), c)
    elif strategy == "severity_near":
        key = lambda c: (severity_score(c), prior_score(c), c)
    elif strategy == "hybrid":
        key = lambda c: (
            0.55 * conditional_score(c)
            + 0.35 * prior_score(c)
            + 0.10 * max(severity_score(c), -100) / 100,
            c,
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    return sorted(candidates, key=key, reverse=True)


def add_controller_predictions(
    items: pd.DataFrame,
    predictions_path: Path | None,
    prediction_model: str,
) -> pd.DataFrame:
    out = items.copy()
    out["controller_pred_action"] = ""
    if predictions_path is None or not predictions_path.exists():
        return out
    preds = pd.read_csv(predictions_path)
    preds = preds[preds["model"].eq(prediction_model)]
    if preds.empty:
        return out
    pred_map = preds.set_index("item_id")["pred_action"].to_dict()
    out["controller_pred_action"] = out["item_id"].map(pred_map).fillna("")
    return out


def policy_gates(row: pd.Series, task_stats: dict) -> dict[str, bool]:
    target_gain = set(row["target_gain_concepts"])
    unknown_count = float(row.get("unknown_intent_error_count", 0) or 0)
    input_count = int(row["input_concept_count"])
    median_control = float(task_stats.get("median_control_concepts", 0))
    pred = str(row.get("controller_pred_action", ""))
    return {
        "offer_all": True,
        "content_gap_gate": input_count < median_control,
        "oracle_any_target_gain": bool(target_gain),
        "oracle_safe_known_gain": bool(target_gain) and unknown_count == 0,
        "controller_not_preserve": pred in {"clarify", "rewrite"},
        "controller_clarify_only": pred == "clarify",
    }


def evaluate(items: pd.DataFrame, stats: dict, max_k: int, input_source: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    strategies = ["control_prior", "context_cooccurrence", "severity_near", "hybrid"]
    item_rows = []
    for _, row in items.iterrows():
        task = str(row["task"])
        observed_human = json_set(row.get("observed_concepts"))
        oracle = json_set(row.get("oracle_concepts"))
        target_gain = sorted(oracle - observed_human)
        observed_input = input_concepts(row, input_source)
        base = row.to_dict()
        base["target_gain_concepts"] = target_gain
        base["input_concepts"] = sorted(observed_input)
        base["input_concept_count"] = len(observed_input)
        wab = pd.to_numeric(row.get("wab_aq", np.nan), errors="coerce")
        for strategy in strategies:
            ranking = rank_candidates(task, observed_input, float(wab), strategy, stats)
            top = ranking[:max_k]
            hits = set(top) & set(target_gain)
            out = {
                "item_id": row["item_id"],
                "strategy": strategy,
                "task": task,
                "bucket": row.get("bucket", ""),
                "patient_root": row.get("patient_root", ""),
                "wab_aq": row.get("wab_aq", np.nan),
                "unknown_intent_error_count": row.get("unknown_intent_error_count", 0),
                "target_gain_n": len(target_gain),
                "target_gain_concepts": json.dumps(target_gain),
                "input_concept_count": len(observed_input),
                "candidate_count": len(ranking),
                "top_candidates": json.dumps(top),
                "controller_pred_action": row.get("controller_pred_action", ""),
            }
            for k in range(1, max_k + 1):
                topk = set(ranking[:k])
                out[f"hit_at_{k}"] = int(bool(topk & set(target_gain)))
                out[f"target_recall_at_{k}"] = (
                    len(topk & set(target_gain)) / len(target_gain) if target_gain else 0.0
                )
            item_rows.append(out)

    ranked = pd.DataFrame(item_rows)
    policy_rows = []
    item_meta = items.set_index("item_id")
    for strategy, group in ranked.groupby("strategy"):
        for k in range(1, max_k + 1):
            for policy in [
                "offer_all",
                "content_gap_gate",
                "oracle_any_target_gain",
                "oracle_safe_known_gain",
                "controller_not_preserve",
                "controller_clarify_only",
            ]:
                offered = []
                useful = []
                concept_hits = []
                target_totals = []
                low_error_offers = []
                unknown_no_gain_offers = []
                for _, r in group.iterrows():
                    meta = item_meta.loc[r["item_id"]].copy()
                    meta["target_gain_concepts"] = json.loads(r["target_gain_concepts"])
                    meta["input_concept_count"] = r["input_concept_count"]
                    meta["controller_pred_action"] = r.get("controller_pred_action", "")
                    gates = policy_gates(meta, stats.get(str(meta["task"]), {}))
                    offer = bool(gates[policy]) and int(r["candidate_count"]) > 0
                    target_n = int(r["target_gain_n"])
                    target_totals.append(target_n)
                    hit_n = float(r[f"target_recall_at_{k}"]) * target_n
                    offered.append(offer)
                    useful.append(offer and bool(r[f"hit_at_{k}"]))
                    concept_hits.append(hit_n if offer else 0.0)
                    low_error_offers.append(
                        offer and str(r.get("bucket", "")) == "low_error_content_control"
                    )
                    unknown_no_gain_offers.append(
                        offer
                        and float(r.get("unknown_intent_error_count", 0) or 0) > 0
                        and target_n == 0
                    )
                offered_arr = np.asarray(offered, dtype=bool)
                useful_arr = np.asarray(useful, dtype=bool)
                positive = group["target_gain_n"].to_numpy() > 0
                n_offered = int(offered_arr.sum())
                n_positive = int(positive.sum())
                total_targets = int(np.sum(target_totals))
                policy_rows.append(
                    {
                        "strategy": strategy,
                        "policy": policy,
                        "k": k,
                        "n_items": len(group),
                        "n_positive_items": n_positive,
                        "offer_rate": float(offered_arr.mean()),
                        "useful_offer_precision": float(useful_arr.sum() / max(n_offered, 1)),
                        "positive_item_hit_recall": float(
                            (useful_arr & positive).sum() / max(n_positive, 1)
                        ),
                        "target_concept_recall": float(np.sum(concept_hits) / max(total_targets, 1)),
                        "unnecessary_offer_rate": float((offered_arr & ~positive).sum() / max(n_offered, 1)),
                        "low_error_control_offer_rate": float(np.mean(low_error_offers)),
                        "unknown_no_gain_offer_rate": float(np.mean(unknown_no_gain_offers)),
                    }
                )
    summary = pd.DataFrame(policy_rows)
    return ranked, summary


def write_summary(out_dir: Path, ranked: pd.DataFrame, summary: pd.DataFrame, input_source: str) -> None:
    best = summary.sort_values(
        ["positive_item_hit_recall", "useful_offer_precision", "offer_rate"],
        ascending=[False, False, True],
    ).head(20)
    deployable = summary[
        summary["policy"].isin(["offer_all", "content_gap_gate", "controller_not_preserve", "controller_clarify_only"])
    ].sort_values(["positive_item_hit_recall", "useful_offer_precision"], ascending=False)
    k3 = summary[summary["k"].eq(3)].sort_values(
        ["positive_item_hit_recall", "useful_offer_precision"], ascending=False
    )
    lines = [
        "# Top-k Clarification Benchmark",
        "",
        f"- Items: {ranked['item_id'].nunique()}",
        f"- Input source: {input_source}",
        f"- Strategies: {', '.join(sorted(ranked['strategy'].unique()))}",
        f"- Positive target-gain items: {int((ranked.drop_duplicates('item_id')['target_gain_n'] > 0).sum())}",
        "",
        "## Best Overall Policies",
        "",
        md_table(best.round(3).head(20)),
        "",
        "## k=3 Comparison",
        "",
        md_table(k3.round(3).head(40)),
        "",
        "## Deployable/Non-oracle Policies",
        "",
        md_table(deployable.head(40).round(3)),
        "",
        "## Interpretation",
        "",
        "This is a clarification benchmark, not a rewriting benchmark. A high "
        "positive-item hit recall means the intended known target concept appears "
        "somewhere in a short candidate list. Useful-offer precision and the "
        "unknown/low-error offer rates quantify the clinical burden and safety "
        "cost. Oracle gates estimate the upper bound if we knew which rows had "
        "recoverable known targets; deployable gates show what current signals can "
        "do without CHAT target labels.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    items = pd.read_csv(args.items_path)
    ref = pd.read_csv(args.reference_features)
    items = add_controller_predictions(items, args.predictions_path, args.prediction_model)
    stats = build_reference_stats(ref)
    ranked, summary = evaluate(items, stats, args.max_k, args.input_source)
    ranked.to_csv(out_dir / "ranked_candidates.csv", index=False)
    summary.to_csv(out_dir / "policy_summary.csv", index=False)
    write_summary(out_dir, ranked, summary, args.input_source)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
