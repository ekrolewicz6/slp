"""Generate an SLP-facing state report prototype from existing analyses."""

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
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--state",
        default="outputs/two_axis_state_typology/session_two_axis_state.csv",
        type=Path,
    )
    parser.add_argument(
        "--targets",
        default="outputs/treatment_target_sequencing/target_recommendations.csv",
        type=Path,
    )
    parser.add_argument(
        "--open-ended",
        default="outputs/open_ended_reconstruction_audit/open_ended_session_summary.csv",
        type=Path,
    )
    parser.add_argument(
        "--movers",
        default="outputs/stable_wab_movers/classified_pairs.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/slp_state_report_prototype", type=Path)
    parser.add_argument("--top-targets", default=5, type=int)
    return parser.parse_args()


def pct_rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, method="average")


def target_strings(targets: pd.DataFrame, top_n: int) -> pd.DataFrame:
    rows = []
    for pid, group in targets.groupby("participant_id"):
        top = group.sort_values("target_zone_score", ascending=False).head(top_n)
        rows.append(
            {
                "participant_id": pid,
                "top_event_targets": json.dumps(
                    [
                        {
                            "task": str(r["task"]),
                            "concept": str(r["concept"]),
                            "pred_success": round(float(r["pred_ability+item"]), 3),
                            "zone_score": round(float(r["target_zone_score"]), 3),
                        }
                        for _, r in top.iterrows()
                    ]
                ),
                "n_top_targets": len(top),
            }
        )
    return pd.DataFrame(rows)


def movement_flags(movers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pid_col, role in [("from_participant_id", "outgoing"), ("to_participant_id", "incoming")]:
        for pid, group in movers.groupby(pid_col):
            stable_moves = group[group["stable_wab_discourse_mover"].astype(bool)]
            if stable_moves.empty:
                continue
            strongest = stable_moves.sort_values("abs_delta_core_content_mean_z", ascending=False).iloc[0]
            rows.append(
                {
                    "participant_id": pid,
                    "movement_role": role,
                    "stable_wab_mover_flag": True,
                    "movement_type": strongest["mover_type"],
                    "movement_delta_content": strongest["delta_core_content_mean_z"],
                    "movement_delta_wab": strongest["delta_wab_aq"],
                    "movement_partner": strongest[
                        "to_participant_id" if role == "outgoing" else "from_participant_id"
                    ],
                }
            )
    if not rows:
        return pd.DataFrame(columns=["participant_id"])
    return pd.DataFrame(rows).sort_values("movement_delta_content").drop_duplicates("participant_id")


def plan_for(row: pd.Series) -> tuple[str, str, str]:
    priority = str(row.get("assistive_priority", "review"))
    targets = json.loads(row.get("top_event_targets", "[]") or "[]")
    target_text = ", ".join(f"{t['task']}:{t['concept']}" for t in targets[:5]) or "No high-confidence target list"
    risk_pct = float(row.get("risk_percentile", np.nan))
    recoverable_pct = float(row.get("recoverable_percentile", np.nan))
    open_clarify = float(row.get("abstain_or_clarify_utterance_frac", 0) or 0)

    if priority == "event-concept expansion":
        plan = "Event-concept expansion"
        rationale = f"Low content with lower unknown-intent risk; start with near-threshold concepts: {target_text}."
    elif priority == "known-target repair plus content expansion":
        plan = "Known-target repair plus content expansion"
        rationale = f"Recoverable-error burden is high; combine repair practice with near-threshold concepts: {target_text}."
    elif priority == "clarification/repair support":
        plan = "Clarification and repair support"
        rationale = "Content is relatively high but unknown-intent risk is elevated; prioritize repair/confirmation strategies over content drilling alone."
    elif priority == "high-support intent clarification":
        plan = "High-support intent clarification / AAC scaffolding"
        rationale = "Low content and high unknown-intent risk; avoid hidden correction and use explicit confirmation or supported choices."
    elif priority == "maintenance/generalization":
        plan = "Maintenance and generalization"
        rationale = f"Content is relatively high and unknown-intent risk is lower; use broader discourse generalization targets: {target_text}."
    else:
        plan = "Clinical review"
        rationale = f"Mixed profile; inspect discourse examples and consider targets: {target_text}."

    cautions = []
    if risk_pct >= 0.75 or open_clarify >= 0.05:
        cautions.append("Do not auto-rewrite; use clarify/confirm workflow.")
    if recoverable_pct >= 0.75 and risk_pct < 0.60:
        cautions.append("Known-target repair may be safer than open-ended reconstruction.")
    if bool(row.get("stable_wab_mover_flag", False)):
        cautions.append("Recent discourse movement despite stable WAB; inspect session pair.")
    caution_text = " ".join(cautions) if cautions else "No major automated-support caution from current features."
    return plan, rationale, caution_text


def build_reports(
    state: pd.DataFrame,
    targets: pd.DataFrame,
    open_ended: pd.DataFrame,
    movers: pd.DataFrame,
    top_n: int,
) -> pd.DataFrame:
    reports = state.copy()
    reports["content_percentile"] = pct_rank(reports["content_axis"])
    reports["risk_percentile"] = pct_rank(reports["risk_axis"])
    reports["recoverable_percentile"] = pct_rank(reports["recoverable_axis"])
    reports = reports.merge(target_strings(targets, top_n), on="participant_id", how="left")
    reports["top_event_targets"] = reports["top_event_targets"].fillna("[]")
    reports["n_top_targets"] = reports["n_top_targets"].fillna(0).astype(int)

    open_cols = [
        "participant_id",
        "n_open_ended_utterances",
        "safe_known_rewrite_utterance_frac",
        "abstain_or_clarify_utterance_frac",
        "unknown_intent_error_count_rate_100",
    ]
    reports = reports.merge(open_ended[open_cols], on="participant_id", how="left")
    for col in open_cols[1:]:
        reports[col] = pd.to_numeric(reports[col], errors="coerce").fillna(0)

    flags = movement_flags(movers)
    reports = reports.merge(flags, on="participant_id", how="left")
    reports["stable_wab_mover_flag"] = reports["stable_wab_mover_flag"].fillna(False).astype(bool)
    reports["movement_type"] = reports["movement_type"].fillna("")
    reports["movement_role"] = reports["movement_role"].fillna("")
    reports["movement_partner"] = reports["movement_partner"].fillna("")

    plans = reports.apply(plan_for, axis=1, result_type="expand")
    reports["recommended_plan"] = plans[0]
    reports["plan_rationale"] = plans[1]
    reports["automation_caution"] = plans[2]
    return reports


def same_wab_different_plan(reports: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "participant_id",
        "wab_aq",
        "subtype",
        "recommended_plan",
        "content_axis",
        "risk_axis",
        "recoverable_axis",
    ]
    a = reports[cols].reset_index(drop=True).reset_index(names="idx_a")
    b = reports[cols].reset_index(drop=True).reset_index(names="idx_b")
    pairs = a.merge(b, how="cross", suffixes=("_a", "_b"))
    pairs = pairs[pairs["idx_a"] < pairs["idx_b"]].copy()
    pairs = pairs[
        ((pairs["wab_aq_a"] - pairs["wab_aq_b"]).abs() <= 2)
        & (pairs["recommended_plan_a"] != pairs["recommended_plan_b"])
    ].copy()
    pairs["axis_contrast"] = (
        (pairs["content_axis_a"] - pairs["content_axis_b"]).abs()
        + (pairs["risk_axis_a"] - pairs["risk_axis_b"]).abs()
        + (pairs["recoverable_axis_a"] - pairs["recoverable_axis_b"]).abs()
    )
    return pairs.sort_values("axis_contrast", ascending=False).head(50)


def summarize(reports: pd.DataFrame, same_wab: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    plan_summary = (
        reports.groupby("recommended_plan")
        .agg(
            n=("participant_id", "size"),
            mean_wab=("wab_aq", "mean"),
            mean_content=("content_axis", "mean"),
            mean_unknown_risk=("risk_axis", "mean"),
            mean_recoverable=("recoverable_axis", "mean"),
            with_top_targets=("n_top_targets", lambda x: (x > 0).mean()),
            stable_wab_mover_rate=("stable_wab_mover_flag", "mean"),
        )
        .reset_index()
        .sort_values("mean_wab")
    )
    checks = pd.DataFrame(
        [
            {
                "check": "reports_total",
                "value": len(reports),
            },
            {
                "check": "reports_with_top_targets",
                "value": int((reports["n_top_targets"] > 0).sum()),
            },
            {
                "check": "high_risk_without_clarification_plan",
                "value": int(
                    (
                        (reports["risk_percentile"] >= 0.75)
                        & ~reports["recommended_plan"].str.contains("clarification|repair", case=False)
                    ).sum()
                ),
            },
            {
                "check": "same_wab_different_plan_pairs",
                "value": len(same_wab),
            },
        ]
    )
    return plan_summary, checks


def report_card(row: pd.Series) -> str:
    targets = json.loads(row.get("top_event_targets", "[]") or "[]")
    target_text = "; ".join(
        f"{t['task']}:{t['concept']} (p={t['pred_success']}, zone={t['zone_score']})"
        for t in targets
    ) or "None available"
    movement = (
        f"{row['movement_type']} vs {row['movement_partner']}"
        if bool(row.get("stable_wab_mover_flag", False))
        else "No stable-WAB movement flag"
    )
    return (
        f"## {row['participant_id']} | {row['subtype']} | WAB-AQ {row['wab_aq']:.1f}\n\n"
        f"- State: {row['state_quadrant']} / {row['assistive_priority']}\n"
        f"- Axes: content {row['content_percentile']:.2f} pct, unknown-risk {row['risk_percentile']:.2f} pct, "
        f"recoverable-error {row['recoverable_percentile']:.2f} pct\n"
        f"- Recommended plan: {row['recommended_plan']}\n"
        f"- Rationale: {row['plan_rationale']}\n"
        f"- Automation caution: {row['automation_caution']}\n"
        f"- Near-threshold targets: {target_text}\n"
        f"- Longitudinal flag: {movement}\n"
    )


def write_summary(
    out_dir: Path,
    reports: pd.DataFrame,
    plan_summary: pd.DataFrame,
    checks: pd.DataFrame,
    same_wab: pd.DataFrame,
) -> None:
    lines = [
        "# SLP State Report Prototype",
        "",
        f"- Reports generated: {len(reports)}",
        f"- Participants/sessions with top target recommendations: {(reports['n_top_targets'] > 0).sum()}",
        f"- Stable-WAB mover flags in reports: {reports['stable_wab_mover_flag'].sum()}",
        "",
        "## Plan Summary",
        "",
        md_table(plan_summary.round(3)),
        "",
        "## Internal Checks",
        "",
        md_table(checks),
        "",
        "## Same-WAB / Different-Plan Examples",
        "",
        md_table(
            same_wab[
                [
                    "participant_id_a",
                    "wab_aq_a",
                    "subtype_a",
                    "recommended_plan_a",
                    "participant_id_b",
                    "wab_aq_b",
                    "subtype_b",
                    "recommended_plan_b",
                    "axis_contrast",
                ]
            ].round(3).head(25)
        ),
        "",
        "## Interpretation",
        "",
        "This is not a validated clinical report. It is an internally auditable "
        "prototype that converts the current two-axis state model into care-planning "
        "hypotheses: content expansion, known-target repair, clarification/AAC "
        "support, or maintenance/generalization. The same-WAB/different-plan table "
        "is the key scientific value: it shows where discourse state may recommend "
        "different care despite similar standardized severity.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    state = pd.read_csv(args.state)
    targets = pd.read_csv(args.targets)
    open_ended = pd.read_csv(args.open_ended)
    movers = pd.read_csv(args.movers)
    reports = build_reports(state, targets, open_ended, movers, args.top_targets)
    same_wab = same_wab_different_plan(reports)
    plan_summary, checks = summarize(reports, same_wab)

    reports.to_csv(out_dir / "state_report_rows.csv", index=False)
    same_wab.to_csv(out_dir / "same_wab_different_plan_examples.csv", index=False)
    plan_summary.to_csv(out_dir / "plan_summary.csv", index=False)
    checks.to_csv(out_dir / "internal_checks.csv", index=False)
    examples = reports.sort_values(
        ["stable_wab_mover_flag", "risk_percentile", "content_percentile"],
        ascending=[False, False, True],
    ).head(20)
    (out_dir / "example_report_cards.md").write_text(
        "# Example State Report Cards\n\n"
        + "\n\n".join(report_card(row) for _, row in examples.iterrows())
        + "\n",
        encoding="utf-8",
    )
    write_summary(out_dir, reports, plan_summary, checks, same_wab)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
