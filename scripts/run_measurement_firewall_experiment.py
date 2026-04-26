"""Test the measurement firewall: assessment text vs support text.

The clinical safety rule is simple: never score a patient's language ability
from text that has been reconstructed, corrected, or ASR-transformed unless
the measurement target is explicitly "system output quality."

This script quantifies why. It compares raw human CHAT scoring, oracle target
augmentation, local reconstruction pilots, and ASR-derived text as if each were
used for assessment, then summarizes clarification burden from the existing
controller simulations.
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

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark-items",
        default="outputs/reconstruction_safety_benchmark/benchmark_items.csv",
        type=Path,
    )
    parser.add_argument(
        "--raw-scores",
        default="outputs/reconstruction_safety_benchmark/scores_preserve_raw.csv",
        type=Path,
    )
    parser.add_argument(
        "--oracle-scores",
        default="outputs/reconstruction_safety_benchmark/scores_oracle_target_augmented.csv",
        type=Path,
    )
    parser.add_argument(
        "--local-score-dirs",
        nargs="*",
        default=[
            "outputs/local_llm_reconstruction",
            "outputs/local_llm_reconstruction_compact",
            "outputs/local_llm_reconstruction_conservative",
            "outputs/local_llm_reconstruction_full_conservative",
        ],
    )
    parser.add_argument(
        "--asr-score-dirs",
        nargs="*",
        default=[
            "outputs/asr_reconstruction_safety_confidence_pwa12_tiny",
            "outputs/asr_reconstruction_safety_pwa60_tiny_cleanclips",
        ],
    )
    parser.add_argument(
        "--clarification-dirs",
        nargs="*",
        default=[
            "outputs/clarification_coverage_risk",
            "outputs/clarification_coverage_risk_asr_confidence_pwa12_tiny",
        ],
    )
    parser.add_argument("--output-dir", default="outputs/measurement_firewall", type=Path)
    return parser.parse_args()


def safe_read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_benchmark_scores(args: argparse.Namespace) -> pd.DataFrame:
    items = safe_read(args.benchmark_items)
    if items.empty:
        return pd.DataFrame()
    meta = items[
        [
            "item_id",
            "bucket",
            "task",
            "subtype",
            "wab_aq",
            "observed_concept_count",
            "oracle_concept_count",
            "oracle_concept_gain",
        ]
    ].copy()

    parts = []
    for path, source, family in [
        (args.raw_scores, "human_chat_benchmark", "human_raw_chat"),
        (args.oracle_scores, "human_chat_benchmark", "oracle_target_augmented"),
    ]:
        df = safe_read(path)
        if df.empty:
            continue
        df = df.copy()
        df["score_source"] = source
        df["candidate_family"] = family
        parts.append(df)

    for score_dir in args.local_score_dirs:
        path = Path(score_dir) / "local_llm_scores.csv"
        df = safe_read(path)
        if df.empty:
            continue
        df = df.copy()
        df["score_source"] = Path(score_dir).name
        df["candidate_family"] = Path(score_dir).name
        parts.append(df)

    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    out = out.drop(columns=[c for c in ["bucket", "task", "subtype", "wab_aq"] if c in out.columns])
    out = out.merge(meta, on="item_id", how="left")
    out["item_universe"] = "reconstruction_safety_400"
    return out


def load_asr_scores(asr_dirs: list[str]) -> pd.DataFrame:
    parts = []
    for score_dir in asr_dirs:
        base = Path(score_dir)
        scores = safe_read(base / "asr_safety_scores.csv")
        items = safe_read(base / "asr_safety_items.csv")
        if scores.empty:
            continue
        scores = scores.copy()
        scores["score_source"] = base.name
        if not items.empty and "observed_concept_count" in items:
            meta_cols = [
                "item_id",
                "observed_concept_count",
                "oracle_concept_count",
                "oracle_concept_gain",
            ]
            scores = scores.merge(items[meta_cols], on="item_id", how="left", suffixes=("", "_item"))
        scores["item_universe"] = base.name
        parts.append(scores)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def add_firewall_metrics(scores: pd.DataFrame) -> pd.DataFrame:
    if scores.empty:
        return scores
    out = scores.copy()
    for col in [
        "output_concept_count",
        "observed_concept_count",
        "oracle_concept_count",
        "concept_overreach_count",
        "observed_concept_loss_count",
        "unknown_intent_added_concept_count",
        "negation_flip_flag",
        "known_target_token_recovery_rate",
    ]:
        out[col] = pd.to_numeric(out.get(col), errors="coerce").fillna(0)
    out["measurement_delta_vs_raw"] = out["output_concept_count"] - out["observed_concept_count"]
    out["measurement_inflation_flag"] = out["measurement_delta_vs_raw"] > 0
    out["measurement_deflation_flag"] = out["measurement_delta_vs_raw"] < 0
    out["unsafe_output_flag"] = (
        (out["concept_overreach_count"] > 0)
        | (out["unknown_intent_added_concept_count"] > 0)
        | (out["negation_flip_flag"] > 0)
    )
    out["assessment_corruption_flag"] = (
        out["measurement_inflation_flag"]
        | out["measurement_deflation_flag"]
        | (out["observed_concept_loss_count"] > 0)
        | out["unsafe_output_flag"]
    )
    out["assessment_policy"] = np.where(
        out["candidate_family"].isin(["human_raw_chat", "human_raw_chat"]),
        "allowed_for_assessment",
        "communication_support_only",
    )
    return out


def summarize_firewall(scored: pd.DataFrame) -> pd.DataFrame:
    if scored.empty:
        return pd.DataFrame()
    summary = (
        scored.groupby(["item_universe", "score_source", "candidate_family"], dropna=False)
        .agg(
            n=("item_id", "size"),
            mean_wab=("wab_aq", "mean"),
            mean_raw_observed_concepts=("observed_concept_count", "mean"),
            mean_output_concepts=("output_concept_count", "mean"),
            mean_measurement_delta=("measurement_delta_vs_raw", "mean"),
            inflation_rate=("measurement_inflation_flag", "mean"),
            deflation_rate=("measurement_deflation_flag", "mean"),
            observed_loss_rate=("observed_concept_loss_count", lambda s: float((s > 0).mean())),
            overreach_rate=("concept_overreach_count", lambda s: float((s > 0).mean())),
            unknown_added_rate=("unknown_intent_added_concept_count", lambda s: float((s > 0).mean())),
            negation_flip_rate=("negation_flip_flag", lambda s: float((s > 0).mean())),
            assessment_corruption_rate=("assessment_corruption_flag", "mean"),
            known_target_token_recovery=("known_target_token_recovery_rate", "mean"),
        )
        .reset_index()
        .sort_values(["item_universe", "assessment_corruption_rate"], ascending=[True, False])
    )
    summary["firewall_decision"] = np.where(
        summary["candidate_family"].eq("human_raw_chat"),
        "assessment_ok",
        "do_not_score_as_patient_ability",
    )
    return summary


def summarize_by_bucket(scored: pd.DataFrame) -> pd.DataFrame:
    if scored.empty or "bucket" not in scored:
        return pd.DataFrame()
    return (
        scored.groupby(["item_universe", "candidate_family", "bucket"], dropna=False)
        .agg(
            n=("item_id", "size"),
            mean_measurement_delta=("measurement_delta_vs_raw", "mean"),
            inflation_rate=("measurement_inflation_flag", "mean"),
            deflation_rate=("measurement_deflation_flag", "mean"),
            assessment_corruption_rate=("assessment_corruption_flag", "mean"),
            known_target_token_recovery=("known_target_token_recovery_rate", "mean"),
        )
        .reset_index()
        .sort_values(["item_universe", "candidate_family", "assessment_corruption_rate"], ascending=[True, True, False])
    )


def communication_gain_vs_measurement_risk(scored: pd.DataFrame) -> pd.DataFrame:
    if scored.empty:
        return pd.DataFrame()
    rows = []
    for (universe, family), group in scored.groupby(["item_universe", "candidate_family"]):
        if family == "human_raw_chat":
            continue
        raw = scored[
            (scored["item_universe"] == universe)
            & (scored["candidate_family"].isin(["human_raw_chat", "human_raw_chat"]))
        ][["item_id", "known_target_token_recovery_rate"]].rename(
            columns={"known_target_token_recovery_rate": "raw_known_target_token_recovery"}
        )
        merged = group.merge(raw, on="item_id", how="left")
        merged["communication_gain_vs_raw"] = (
            merged["known_target_token_recovery_rate"] - merged["raw_known_target_token_recovery"].fillna(0)
        )
        rows.append(
            {
                "item_universe": universe,
                "candidate_family": family,
                "n": len(merged),
                "mean_communication_gain_vs_raw": float(merged["communication_gain_vs_raw"].mean()),
                "positive_communication_gain_rate": float((merged["communication_gain_vs_raw"] > 0).mean()),
                "assessment_corruption_rate": float(merged["assessment_corruption_flag"].mean()),
                "unsafe_output_rate": float(merged["unsafe_output_flag"].mean()),
                "interpretation": "support_maybe_measurement_no"
                if merged["communication_gain_vs_raw"].mean() > 0
                else "no_support_gain_measurement_no",
            }
        )
    return pd.DataFrame(rows).sort_values(["mean_communication_gain_vs_raw", "assessment_corruption_rate"], ascending=[False, True])


def clarification_burden(clarification_dirs: list[str]) -> pd.DataFrame:
    rows = []
    for directory in clarification_dirs:
        base = Path(directory)
        targets = safe_read(base / "recovery_burden_targets.csv")
        frontier = safe_read(base / "risk_frontier.csv")
        if not targets.empty:
            for row in targets.itertuples(index=False):
                rows.append(
                    {
                        "source": base.name,
                        "table": "target_recall",
                        "policy_family": getattr(row, "policy_family", ""),
                        "target_positive_item_recall": getattr(row, "target_positive_item_recall", np.nan),
                        "status": getattr(row, "status", ""),
                        "gate": getattr(row, "gate", ""),
                        "k": getattr(row, "k", np.nan),
                        "offer_rate": getattr(row, "offer_rate", np.nan),
                        "useful_offer_precision": getattr(row, "useful_offer_precision", np.nan),
                        "target_concept_recall": getattr(row, "target_concept_recall", np.nan),
                        "unnecessary_offer_rate": getattr(row, "unnecessary_offer_rate", np.nan),
                        "unknown_no_gain_item_offer_rate": getattr(row, "unknown_no_gain_item_offer_rate", np.nan),
                        "turns_per_useful_hit": getattr(row, "turns_per_useful_hit", np.nan),
                        "options_per_target_recovered": getattr(row, "options_per_target_recovered", np.nan),
                    }
                )
        if not frontier.empty:
            for row in frontier.itertuples(index=False):
                rows.append(
                    {
                        "source": base.name,
                        "table": "risk_frontier",
                        "policy_family": getattr(row, "constraint", ""),
                        "target_positive_item_recall": np.nan,
                        "status": getattr(row, "status", ""),
                        "gate": getattr(row, "gate", ""),
                        "k": getattr(row, "k", np.nan),
                        "offer_rate": getattr(row, "offer_rate", np.nan),
                        "useful_offer_precision": getattr(row, "useful_offer_precision", np.nan),
                        "target_concept_recall": getattr(row, "target_concept_recall", np.nan),
                        "unnecessary_offer_rate": getattr(row, "unnecessary_offer_rate", np.nan),
                        "unknown_no_gain_item_offer_rate": getattr(row, "unknown_no_gain_item_offer_rate", np.nan),
                        "turns_per_useful_hit": getattr(row, "turns_per_useful_hit", np.nan),
                        "options_per_target_recovered": getattr(row, "options_per_target_recovered", np.nan),
                    }
                )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["questions_per_100_items"] = pd.to_numeric(out["offer_rate"], errors="coerce") * 100
    out["useful_hits_per_100_items"] = out["questions_per_100_items"] * pd.to_numeric(
        out["useful_offer_precision"], errors="coerce"
    )
    return out


def write_summary(
    out_dir: Path,
    firewall_summary: pd.DataFrame,
    gain_risk: pd.DataFrame,
    burden: pd.DataFrame,
) -> None:
    deployable = burden[
        (burden["table"] == "target_recall")
        & (burden["policy_family"] == "deployable")
        & (burden["status"] == "ok")
    ].copy()
    lines = [
        "# Measurement Firewall Experiment",
        "",
        "## Assessment Corruption If Reconstructed Text Is Scored",
        "",
        md_table(firewall_summary.head(80).round(3)),
        "",
        "## Communication Gain vs Measurement Risk",
        "",
        md_table(gain_risk.head(80).round(3)),
        "",
        "## Clarification Burden",
        "",
        md_table(burden.head(80).round(3)),
        "",
        "Deployable target-recall rows:",
        "",
        md_table(deployable.head(80).round(3)),
        "",
        "## Synthesis",
        "",
        "- Raw human CHAT text is the only safe assessment source in this comparison.",
        "- Oracle or reconstructed support text can recover known targets, but the same operation changes the apparent content score. That is exactly why assessment and communication support must be separated.",
        "- ASR-derived text is not a neutral replacement for raw transcripts: it can deflate observed content, lose concepts, or change safety labels.",
        "- Clarification is not free. Current deployable policies recover meaningful targets only by asking many questions, and the ASR setting raises the burden further. Better uncertainty evidence is needed before a high-coverage clinical controller is acceptable.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)

    benchmark_scores = load_benchmark_scores(args)
    asr_scores = load_asr_scores(args.asr_score_dirs)
    scored = add_firewall_metrics(pd.concat([benchmark_scores, asr_scores], ignore_index=True))
    firewall_summary = summarize_firewall(scored)
    bucket_summary = summarize_by_bucket(scored)
    gain_risk = communication_gain_vs_measurement_risk(scored)
    burden = clarification_burden(args.clarification_dirs)

    scored.to_csv(out_dir / "firewall_scored_items.csv", index=False)
    firewall_summary.to_csv(out_dir / "firewall_summary.csv", index=False)
    bucket_summary.to_csv(out_dir / "firewall_by_bucket.csv", index=False)
    gain_risk.to_csv(out_dir / "communication_gain_vs_measurement_risk.csv", index=False)
    burden.to_csv(out_dir / "clarification_burden_synthesis.csv", index=False)
    write_summary(out_dir, firewall_summary, gain_risk, burden)

    print(f"Wrote measurement firewall experiment to {out_dir}")
    print(firewall_summary.to_string(index=False))
    if not burden.empty:
        print(burden.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
