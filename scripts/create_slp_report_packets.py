"""Create review packets for SLP-facing state reports.

The packets are intentionally conservative:

* adult aphasia uses the current V2 state-report rows;
* child language uses retrospective DLD/late-talker state outputs;
* stuttering is a wireframe/data-access packet because local recovery data are
  not available in this checkout.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adult-reports",
                        default="outputs/slp_state_report_v2/state_report_v2_rows.csv",
                        type=Path)
    parser.add_argument("--dld-trajectories",
                        default="outputs/dld_late_talker_catchup/rescorla_trajectories.csv",
                        type=Path)
    parser.add_argument("--dld-age-features",
                        default="outputs/dld_late_talker_catchup/rescorla_participant_age_features.csv",
                        type=Path)
    parser.add_argument("--dld-targets",
                        default="outputs/dld_target_policy_simulation/selected_targets_by_policy.csv",
                        type=Path)
    parser.add_argument("--stuttering-inventory",
                        default="outputs/stuttering_recovery_inventory/external_fluencybank_candidates.csv",
                        type=Path)
    parser.add_argument("--output-dir", default="outputs/slp_report_packets", type=Path)
    parser.add_argument("--adult-per-plan", default=2, type=int)
    parser.add_argument("--child-examples", default=8, type=int)
    return parser.parse_args()


def safe_float(value: object) -> float | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(v):
        return None
    return v


def fmt(value: object, digits: int = 2) -> str:
    v = safe_float(value)
    if v is None:
        return "n/a"
    return f"{v:.{digits}f}"


def level(value: object, high_bad: bool = False) -> str:
    v = safe_float(value)
    if v is None:
        return "not available"
    if v < 0.25:
        return "low" if not high_bad else "lower burden"
    if v > 0.75:
        return "high" if not high_bad else "high burden"
    return "mid-range"


def deidentify(values: list[str], prefix: str) -> dict[str, str]:
    return {value: f"{prefix}_{i:03d}" for i, value in enumerate(values, start=1)}


def parse_targets(raw: object, top_n: int = 4) -> str:
    if not isinstance(raw, str) or not raw.strip():
        return "none available"
    try:
        targets = json.loads(raw)
    except json.JSONDecodeError:
        return "none available"
    if not targets:
        return "none available"
    chunks = []
    for target in targets[:top_n]:
        task = target.get("task", "task")
        concept = target.get("concept", "concept")
        pred = target.get("pred_success", "n/a")
        zone = target.get("zone_score", "n/a")
        chunks.append(f"{task}:{concept} (p={pred}, zone={zone})")
    return "; ".join(chunks)


def adult_packet(adult: pd.DataFrame, per_plan: int) -> tuple[str, pd.DataFrame]:
    adult = adult.copy()
    adult["selection_score"] = (
        adult["risk_percentile"].fillna(0)
        + adult["recoverable_percentile"].fillna(0)
        + adult["stable_wab_mover_flag"].fillna(False).astype(int) * 0.25
        + adult["acoustic_atypicality_pct"].fillna(0) * 0.25
    )
    selected = (
        adult.sort_values(["recommended_plan", "selection_score"], ascending=[True, False])
        .groupby("recommended_plan", dropna=False)
        .head(per_plan)
        .copy()
    )
    selected = selected.sort_values(["recommended_plan", "selection_score"], ascending=[True, False])
    id_map = deidentify(selected["participant_id"].astype(str).tolist(), "adult_case")
    selected["review_id"] = selected["participant_id"].astype(str).map(id_map)

    lines = [
        "# Adult Aphasia State Report Packet",
        "",
        "**Purpose:** SLP review of whether multidimensional discourse/audio state is more useful than a single WAB-AQ score or subtype label.",
        "",
        "**Use constraints:** These are research examples, not clinical reports. Raw transcript/audio remains the measurement source of truth; ASR or LLM reconstruction must not be scored as patient ability.",
        "",
        "## Example Cards",
        "",
    ]
    for _, row in selected.iterrows():
        movement = "yes" if bool(row.get("stable_wab_mover_flag", False)) else "no"
        lines.extend([
            f"### {row['review_id']} | {row.get('subtype', 'Unknown')} | WAB-AQ {fmt(row.get('wab_aq'), 1)}",
            "",
            f"- Content carried: {level(row.get('content_percentile'))} ({fmt(row.get('content_percentile'))})",
            f"- Unknown-intent risk: {level(row.get('risk_percentile'), high_bad=True)} ({fmt(row.get('risk_percentile'))})",
            f"- Recoverable-error burden: {level(row.get('recoverable_percentile'), high_bad=True)} ({fmt(row.get('recoverable_percentile'))})",
            f"- Structural complexity: {level(row.get('structural_complexity_pct'))} ({fmt(row.get('structural_complexity_pct'))})",
            f"- Lexical access proxy: {level(row.get('lexical_access_pct'))} ({fmt(row.get('lexical_access_pct'))})",
            f"- Fluency/timing disruption: {level(row.get('fluency_disruption_pct'), high_bad=True)} ({fmt(row.get('fluency_disruption_pct'))})",
            f"- Acoustic/prosodic atypicality: {level(row.get('acoustic_atypicality_pct'), high_bad=True)} ({fmt(row.get('acoustic_atypicality_pct'))})",
            f"- Current decision hypothesis: {row.get('recommended_plan', 'clinical review')}",
            f"- Why this hypothesis: {row.get('plan_rationale', 'n/a')}",
            f"- Target candidates: {parse_targets(row.get('top_event_targets'))}",
            f"- Stable-score discourse movement flag: {movement}",
            f"- Next probe to reduce uncertainty: {row.get('next_probe', 'n/a')}",
            f"- Quality/safety flags: {row.get('quality_flags', 'n/a')}",
            "",
        ])

    lines.extend([
        "## Questions For SLP Review",
        "",
        "1. Can you tell what the main communication risk is from this card?",
        "2. Is the recommended next probe clinically plausible?",
        "3. Which field is confusing, missing, or too model-y?",
        "4. Would this change how you monitor the patient over time?",
        "5. What would you need before trusting this with a real patient?",
        "",
    ])
    return "\n".join(lines), selected


def classify_child(row: pd.Series) -> str:
    if bool(row.get("final_in_td_band", False)):
        return "caught up / near TD-band by final sample"
    if bool(row.get("persistent_gap", False)):
        return "persistent-risk profile"
    delta = safe_float(row.get("delta_composite_z")) or 0.0
    if delta >= 0.75:
        return "improving but not clearly normalized"
    if delta <= -0.25:
        return "declining or widening gap"
    return "uncertain / needs follow-up"


def target_text(targets: pd.DataFrame, participant_root: str, policy: str = "high_utility") -> str:
    if targets.empty:
        return "none available"
    rows = targets[
        (targets["participant_root"].astype(str) == participant_root)
        & (targets["policy"].astype(str) == policy)
    ].head(5)
    if rows.empty:
        rows = targets[targets["participant_root"].astype(str) == participant_root].head(5)
    if rows.empty:
        return "none available"
    return "; ".join(
        f"{r.target_class} via {r.feature} (deficit z={fmt(r.deficit_z)}, utility={fmt(r.learning_utility)})"
        for r in rows.itertuples(index=False)
    )


def child_packet(
    trajectories: pd.DataFrame,
    age_features: pd.DataFrame,
    targets: pd.DataFrame,
    n_examples: int,
) -> tuple[str, pd.DataFrame, pd.DataFrame]:
    traj = trajectories.copy()
    traj["trajectory_class"] = traj.apply(classify_child, axis=1)
    pools = []
    for label in [
        "caught up / near TD-band by final sample",
        "persistent-risk profile",
        "improving but not clearly normalized",
        "declining or widening gap",
        "uncertain / needs follow-up",
    ]:
        subset = traj[traj["trajectory_class"] == label].copy()
        if subset.empty:
            continue
        subset["abs_first_gap"] = subset["first_composite_z"].abs()
        pools.append(subset.sort_values("abs_first_gap", ascending=False).head(2))
    selected = pd.concat(pools, ignore_index=True).head(n_examples) if pools else traj.head(n_examples)
    selected = selected.copy()
    id_map = deidentify(selected["participant_root"].astype(str).tolist(), "child_case")
    selected["review_id"] = selected["participant_root"].astype(str).map(id_map)

    age_first = (
        age_features.sort_values("age_repaired")
        .groupby("participant_root", as_index=False)
        .first()
    )
    age_last = (
        age_features.sort_values("age_repaired")
        .groupby("participant_root", as_index=False)
        .last()
    )
    selected = selected.merge(
        age_first[["participant_root", "single_word_ratio", "pause_per_utt", "repetition_per_utt"]],
        on="participant_root",
        how="left",
        suffixes=("", "_first"),
    )
    selected = selected.merge(
        age_last[["participant_root", "single_word_ratio", "pause_per_utt", "repetition_per_utt"]],
        on="participant_root",
        how="left",
        suffixes=("_first", "_last"),
    )

    lines = [
        "# Child Language / DLD State Report Packet",
        "",
        "**Purpose:** SLP review of whether child language-state summaries are useful for tracking risk and choosing next probes.",
        "",
        "**Use constraints:** These are retrospective research examples. DLD/late-talker labels are noisy anchors, not ground truth. The packet does not claim diagnosis or treatment efficacy.",
        "",
        "## Example Cards",
        "",
    ]
    for _, row in selected.iterrows():
        root = str(row["participant_root"])
        lines.extend([
            f"### {row['review_id']} | {row.get('clinical_label', 'unknown')} | ages {fmt(row.get('age_first'), 0)}-{fmt(row.get('age_last'), 0)} months",
            "",
            f"- Trajectory class: {row.get('trajectory_class')}",
            f"- First state z: {fmt(row.get('first_composite_z'))}",
            f"- Final state z: {fmt(row.get('last_composite_z'))}",
            f"- Change in state z: {fmt(row.get('delta_composite_z'))}",
            f"- First MLU words: {fmt(row.get('first_mlu'))}",
            f"- Final MLU words: {fmt(row.get('last_mlu'))}",
            f"- Single-word ratio: {fmt(row.get('single_word_ratio_first'))} -> {fmt(row.get('single_word_ratio_last'))}",
            f"- Pause rate per utterance: {fmt(row.get('pause_per_utt_first'))} -> {fmt(row.get('pause_per_utt_last'))}",
            f"- Repetition rate per utterance: {fmt(row.get('repetition_per_utt_first'))} -> {fmt(row.get('repetition_per_utt_last'))}",
            "- Candidate target/probe areas: not case-linked in current outputs; see separate DLD target/probe cards below.",
            "- Next probe to reduce uncertainty: sentence repetition plus nonword repetition, then narrative/content task.",
            "- Quality/safety flags: no treatment-response claim; needs standardized outcome and intervention exposure.",
            "",
        ])

    target_profiles = pd.DataFrame()
    if not targets.empty:
        high = targets[targets["policy"].astype(str) == "high_utility"].copy()
        if not high.empty:
            participant_rank = (
                high.groupby(["participant_root", "corpus", "cluster"], as_index=False)
                .agg(
                    mean_deficit_z=("deficit_z", "mean"),
                    mean_learning_utility=("learning_utility", "mean"),
                    age_mean=("age_mean", "first"),
                )
                .sort_values(["cluster", "mean_learning_utility"], ascending=[True, False])
                .groupby("cluster", dropna=False)
                .head(2)
                .head(6)
            )
            target_profiles = participant_rank.copy()
            target_profiles["review_id"] = [
                f"dld_target_case_{i:03d}" for i in range(1, len(target_profiles) + 1)
            ]
            lines.extend([
                "## DLD Target/Probe Profile Cards",
                "",
                "These examples come from the separate DLD residual-state target simulation, not the Rescorla late-talker trajectory table above.",
                "",
            ])
            for row in target_profiles.itertuples(index=False):
                root = str(row.participant_root)
                lines.extend([
                    f"### {row.review_id} | {row.corpus} | cluster {row.cluster} | mean age {fmt(row.age_mean, 0)} months",
                    "",
                    f"- Mean target deficit z: {fmt(row.mean_deficit_z)}",
                    f"- Mean learning-utility proxy: {fmt(row.mean_learning_utility)}",
                    f"- Candidate target/probe areas: {target_text(targets, root)}",
                    "- Next probe to reduce uncertainty: pair natural language sample with sentence repetition and nonword repetition.",
                    "- Quality/safety flags: target policy is unvalidated; needs treatment-response outcome data.",
                    "",
                ])

    lines.extend([
        "## Questions For SLP Review",
        "",
        "1. Does this format make late-talker catch-up versus persistent risk easier to discuss?",
        "2. Are the candidate target/probe areas clinically meaningful or too abstract?",
        "3. What parent/teacher or school participation fields are missing?",
        "4. Would sentence repetition or nonword repetition change how you interpret this child?",
        "5. What would you need before using this for progress monitoring?",
        "",
    ])
    return "\n".join(lines), selected, target_profiles


def stuttering_packet(candidates: pd.DataFrame) -> str:
    lines = [
        "# Stuttering Recovery Report Packet",
        "",
        "**Status:** wireframe only. The local checkout does not contain the child longitudinal FluencyBank recovery data needed to generate real stuttering report cards.",
        "",
        "## Why This Packet Is A Wireframe",
        "",
        "Brian identified stuttering recovery as a high-value longitudinal question: many children recover, but the important clinical question is who will persist and who needs more intensive support. The local inventory found only a small number of fluency-related files and no usable recovery/persistence dataset.",
        "",
        "## Candidate Data Sources To Acquire",
        "",
    ]
    if not candidates.empty:
        lines.extend(["| corpus | url | why it matters |", "| --- | --- | --- |"])
        for row in candidates.itertuples(index=False):
            lines.append(f"| {row.corpus} | {row.url} | {row.why_it_matters} |")
    else:
        lines.append("_No candidate table found._")

    lines.extend([
        "",
        "## Intended Stuttering Report Fields",
        "",
        "- Baseline severity and age.",
        "- Disfluency profile: repetitions, prolongations, blocks, interjections, revisions.",
        "- Acoustic/timing profile: speech rate, pause burden, rhythm, voice quality where relevant.",
        "- Linguistic load: utterance length, lexical/syntactic complexity, narrative demand.",
        "- Task contrast: conversation versus story/reading/repetition if available.",
        "- Parent/clinician severity rating.",
        "- Recovery/persistence status at follow-up.",
        "- Treatment exposure and dose.",
        "- Next probe to reduce uncertainty.",
        "",
        "## First Scientific Question",
        "",
        "Can early acoustic, disfluency, linguistic, and task-state features predict recovery/persistence beyond age, sex, baseline severity, and simple disfluency counts?",
        "",
        "## Review Questions For Fluency Specialists",
        "",
        "1. Which disfluency classes must be separated for recovery prediction?",
        "2. Which acoustic timing features are trusted versus noisy?",
        "3. What follow-up interval defines recovery or persistence?",
        "4. What parent or participation measure should be captured?",
        "5. What treatment exposure data are minimally necessary?",
        "",
    ])
    return "\n".join(lines)


def write_summary(
    out_dir: Path,
    adult_selected: pd.DataFrame,
    child_selected: pd.DataFrame,
    child_target_profiles: pd.DataFrame,
    stutter_candidates: pd.DataFrame,
) -> None:
    lines = [
        "# SLP Report Packet Summary",
        "",
        f"- Adult aphasia example cards: {len(adult_selected)}",
        f"- Child/DLD trajectory cards: {len(child_selected)}",
        f"- Child/DLD target-profile cards: {len(child_target_profiles)}",
        f"- Stuttering data-source candidates: {len(stutter_candidates)}",
        "",
        "## Outputs",
        "",
        "- `adult_aphasia_packet.md`",
        "- `child_language_dld_packet.md`",
        "- `stuttering_recovery_packet.md`",
        "- `review_packet_index.md`",
        "- `review_form_template.csv`",
        "",
        "## Interpretation",
        "",
        "The adult packet is the most evidence-backed because it uses the current AphasiaBank state-report rows. The child packet separates late-talker trajectory examples from DLD target/probe profile examples because those outputs do not overlap at the case level. The stuttering packet is a wireframe because usable longitudinal recovery data are not local yet.",
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_index(out_dir: Path) -> None:
    lines = [
        "# SLP Report Review Packet Index",
        "",
        "Use these packets for informal SLP review before collecting new patient data.",
        "",
        "## Packets",
        "",
        "1. `adult_aphasia_packet.md`: real retrospective adult aphasia examples from current state-report outputs.",
        "2. `child_language_dld_packet.md`: retrospective child/DLD and late-talker trajectory examples.",
        "3. `stuttering_recovery_packet.md`: wireframe plus data-source list; not populated with real recovery cases yet.",
        "4. `review_form_template.csv`: row template for collecting reviewer feedback.",
        "",
        "## Universal Review Questions",
        "",
        "1. What is the main communication problem implied by the report?",
        "2. What would you assess next?",
        "3. What field is confusing or unsafe?",
        "4. What patient/family/clinician context is missing?",
        "5. Would this report change monitoring, goal selection, or documentation?",
        "",
        "## Safety Boundary",
        "",
        "These packets are research artifacts. They do not diagnose, recommend treatment, or score reconstructed AI output as patient ability.",
        "",
    ]
    (out_dir / "review_packet_index.md").write_text("\n".join(lines), encoding="utf-8")


def write_review_template(out_dir: Path) -> None:
    header = (
        "reviewer_id,role,packet,case_id,main_problem_free_text,next_probe_free_text,"
        "understandability_1_5,usefulness_1_5,actionability_1_5,"
        "misinterpretation_risk_1_5,workflow_fit_1_5,most_useful_field,"
        "confusing_or_unsafe_field,missing_context,would_change_monitoring_y_n,notes\n"
    )
    (out_dir / "review_form_template.csv").write_text(header, encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)

    adult = pd.read_csv(args.adult_reports)
    trajectories = pd.read_csv(args.dld_trajectories)
    age_features = pd.read_csv(args.dld_age_features)
    targets = pd.read_csv(args.dld_targets) if args.dld_targets.exists() else pd.DataFrame()
    candidates = pd.read_csv(args.stuttering_inventory) if args.stuttering_inventory.exists() else pd.DataFrame()

    adult_md, adult_selected = adult_packet(adult, args.adult_per_plan)
    child_md, child_selected, child_target_profiles = child_packet(
        trajectories, age_features, targets, args.child_examples
    )
    stuttering_md = stuttering_packet(candidates)

    (out_dir / "adult_aphasia_packet.md").write_text(adult_md, encoding="utf-8")
    (out_dir / "child_language_dld_packet.md").write_text(child_md, encoding="utf-8")
    (out_dir / "stuttering_recovery_packet.md").write_text(stuttering_md, encoding="utf-8")
    adult_selected.to_csv(out_dir / "adult_selected_cases.csv", index=False)
    child_selected.to_csv(out_dir / "child_selected_cases.csv", index=False)
    child_target_profiles.to_csv(out_dir / "child_target_profile_cases.csv", index=False)
    write_index(out_dir)
    write_review_template(out_dir)
    write_summary(out_dir, adult_selected, child_selected, child_target_profiles, candidates)


if __name__ == "__main__":
    main()
