"""Estimate confirmation burden for making reconstruction clinically safe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--llm-outputs",
        default="outputs/local_llm_reconstruction_full_conservative/local_llm_outputs.csv",
        type=Path,
    )
    parser.add_argument(
        "--llm-scores",
        default="outputs/local_llm_reconstruction_full_conservative/local_llm_scores.csv",
        type=Path,
    )
    parser.add_argument(
        "--raw-scores",
        default="outputs/reconstruction_safety_benchmark/scores_preserve_raw.csv",
        type=Path,
    )
    parser.add_argument(
        "--burden",
        default="outputs/measurement_firewall/clarification_burden_synthesis.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/human_confirmation_simulation", type=Path)
    return parser.parse_args()


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def prepare_llm(outputs: pd.DataFrame, scores: pd.DataFrame, raw_scores: pd.DataFrame) -> pd.DataFrame:
    raw = raw_scores[["item_id", "known_target_token_recovery_rate"]].rename(
        columns={"known_target_token_recovery_rate": "raw_known_target_token_recovery"}
    )
    scored = scores.merge(
        outputs[["item_id", "action", "confidence", "bucket"]],
        on=["item_id", "bucket"],
        how="left",
    ).merge(raw, on="item_id", how="left")
    scored["action"] = scored["action"].fillna("missing")
    scored["requires_confirmation"] = scored["action"].isin(["rewrite", "candidates"])
    scored["unsafe_flag"] = (
        (pd.to_numeric(scored["concept_overreach_count"], errors="coerce").fillna(0) > 0)
        | (pd.to_numeric(scored["unknown_intent_added_concept_count"], errors="coerce").fillna(0) > 0)
        | (pd.to_numeric(scored["negation_flip_flag"], errors="coerce").fillna(0) > 0)
    )
    scored["communication_gain_vs_raw"] = pd.to_numeric(
        scored["known_target_token_recovery_rate"], errors="coerce"
    ).fillna(0) - pd.to_numeric(scored["raw_known_target_token_recovery"], errors="coerce").fillna(0)
    scored["useful_gain_flag"] = scored["communication_gain_vs_raw"] > 0.05
    return scored


def llm_policy_rows(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(scored)
    action = scored[scored["requires_confirmation"]].copy()
    for catch_rate in [0.90, 0.95, 0.99, 1.00]:
        useful = int(action["useful_gain_flag"].sum())
        unsafe = int(action["unsafe_flag"].sum())
        rows.append(
            {
                "policy": f"confirm_llm_rewrite_or_candidates_catch_{catch_rate:.2f}",
                "n_items": n,
                "confirmations": len(action),
                "confirmations_per_100_items": 100 * len(action) / max(n, 1),
                "useful_confirmed_outputs": useful,
                "useful_outputs_per_100_items": 100 * useful / max(n, 1),
                "confirmations_per_useful_output": len(action) / max(useful, 1),
                "unsafe_outputs_before_confirmation": unsafe,
                "unsafe_outputs_per_100_before": 100 * unsafe / max(n, 1),
                "expected_residual_unsafe_per_100": 100 * unsafe * (1 - catch_rate) / max(n, 1),
            }
        )
    auto = scored.copy()
    rows.append(
        {
            "policy": "auto_llm_outputs_no_confirmation",
            "n_items": n,
            "confirmations": 0,
            "confirmations_per_100_items": 0.0,
            "useful_confirmed_outputs": int(auto["useful_gain_flag"].sum()),
            "useful_outputs_per_100_items": 100 * auto["useful_gain_flag"].sum() / max(n, 1),
            "confirmations_per_useful_output": 0.0,
            "unsafe_outputs_before_confirmation": int(auto["unsafe_flag"].sum()),
            "unsafe_outputs_per_100_before": 100 * auto["unsafe_flag"].sum() / max(n, 1),
            "expected_residual_unsafe_per_100": 100 * auto["unsafe_flag"].sum() / max(n, 1),
        }
    )
    return pd.DataFrame(rows)


def clarification_policy_rows(burden: pd.DataFrame) -> pd.DataFrame:
    if burden.empty:
        return pd.DataFrame()
    rows = []
    ok = burden[(burden["table"].eq("target_recall")) & (burden["status"].eq("ok"))].copy()
    for row in ok.itertuples(index=False):
        rows.append(
            {
                "policy": f"clarification_{getattr(row, 'source')}_{getattr(row, 'policy_family')}_{getattr(row, 'target_positive_item_recall')}",
                "n_items": np.nan,
                "confirmations": np.nan,
                "confirmations_per_100_items": getattr(row, "questions_per_100_items", np.nan),
                "useful_confirmed_outputs": np.nan,
                "useful_outputs_per_100_items": getattr(row, "useful_hits_per_100_items", np.nan),
                "confirmations_per_useful_output": getattr(row, "turns_per_useful_hit", np.nan),
                "unsafe_outputs_before_confirmation": np.nan,
                "unsafe_outputs_per_100_before": np.nan,
                "expected_residual_unsafe_per_100": 0.0,
                "target_concept_recall": getattr(row, "target_concept_recall", np.nan),
                "unnecessary_offer_rate": getattr(row, "unnecessary_offer_rate", np.nan),
                "unknown_no_gain_item_offer_rate": getattr(row, "unknown_no_gain_item_offer_rate", np.nan),
            }
        )
    return pd.DataFrame(rows)


def by_bucket(scored: pd.DataFrame) -> pd.DataFrame:
    action = scored[scored["requires_confirmation"]].copy()
    return (
        action.groupby("bucket")
        .agg(
            n_confirmations=("item_id", "size"),
            useful_rate=("useful_gain_flag", "mean"),
            unsafe_rate=("unsafe_flag", "mean"),
            mean_gain_vs_raw=("communication_gain_vs_raw", "mean"),
        )
        .reset_index()
        .sort_values("unsafe_rate", ascending=False)
    )


def write_summary(out_dir: Path, policies: pd.DataFrame, bucket_summary: pd.DataFrame) -> None:
    lines = [
        "# Human Confirmation Simulation",
        "",
        "Policy summary:",
        "",
        md_table(policies.round(3)),
        "",
        "LLM confirmation burden by bucket:",
        "",
        md_table(bucket_summary.round(3)),
        "",
        "## Synthesis",
        "",
        "- Perfect confirmation can make model-assisted rewriting safe, but the useful-output yield is low for the current conservative local model.",
        "- Clarification policies are safer because they ask before rewriting, but high target recovery can require many questions, especially in ASR mode.",
        "- The practical target is a controller that asks fewer, better questions by using uncertainty evidence rather than letting a rewriter act autonomously.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    outputs = read(args.llm_outputs)
    scores = read(args.llm_scores)
    raw_scores = read(args.raw_scores)
    burden = read(args.burden)
    scored = prepare_llm(outputs, scores, raw_scores)
    llm_policies = llm_policy_rows(scored)
    clarification_policies = clarification_policy_rows(burden)
    policies = pd.concat([llm_policies, clarification_policies], ignore_index=True)
    bucket_summary = by_bucket(scored)
    scored.to_csv(out_dir / "llm_confirmation_items.csv", index=False)
    policies.to_csv(out_dir / "confirmation_policy_summary.csv", index=False)
    bucket_summary.to_csv(out_dir / "llm_confirmation_by_bucket.csv", index=False)
    write_summary(out_dir, policies, bucket_summary)
    print(f"Wrote human confirmation simulation to {out_dir}")
    print(policies.head(30).to_string(index=False))


if __name__ == "__main__":
    main()
