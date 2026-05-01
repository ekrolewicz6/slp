"""Create a human-review packet for the highest-value DLD conflict cases."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


REVIEW_PRIORITIES = (
    "highest_clinical_fairness_review",
    "highest_scientific_review",
)

CASE_COLUMNS = [
    "case_id",
    "participant_root",
    "corpus",
    "screen_label",
    "age_min",
    "age_max",
    "n_windows",
    "task_bucket",
    "task_proxy",
    "label_noise_flag",
    "conflict_archetype",
    "review_priority",
    "full_language_no_age",
    "full_language_age",
    "mlu_age",
    "corpus_age",
    "age_only",
    "norm_gap_mlu",
    "norm_gap_only",
]


GENERAL_REVIEW_QUESTIONS = [
    "Is the participant label a current clinical state, a history label, a screen label, or ambiguous?",
    "Is there bilingual, dialect, socioeconomic, hearing, attention, or task-context information that could explain the model conflict?",
    "Does the transcript appear representative of the child's ability, or is it too short, overly scaffolded, unusually quiet, or task constrained?",
    "Does the conflict suggest a missing construct that natural speech alone cannot resolve, such as sentence repetition, nonword repetition, comprehension, phonology, or literacy?",
    "If this were a real assessment, what next probe would an SLP choose before making a treatment or eligibility decision?",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--conflicts",
        default="outputs/dld_conflict_taxonomy/high_conflict_taxonomy.csv",
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/dld_conflict_review_packet", type=Path)
    p.add_argument("--max-cases", type=int, default=15)
    return p.parse_args()


def compact_id(root: str) -> str:
    parts = str(root).split("/")
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    return str(root)


def case_specific_questions(row: pd.Series) -> list[str]:
    questions = []
    if row["review_priority"] == "highest_clinical_fairness_review":
        questions.extend(
            [
                "Could this TD-labeled child be a missed-risk case, or is the model reacting to task/context rather than impairment?",
                "Would a structured language probe change the decision, especially sentence or nonword repetition?",
            ]
        )
    if row["review_priority"] == "highest_scientific_review":
        questions.extend(
            [
                "Why does language-only state look risky when corpus/age priors do not?",
                "Is this an atypical language profile, a label/context issue, or evidence that the model is finding a non-MLU signal?",
            ]
        )
    if row.get("task_bucket") == "natural_conversation":
        questions.append("Is adult scaffolding or conversational topic choice suppressing or inflating apparent ability?")
    if row.get("task_bucket") == "narrative_story":
        questions.append("Is narrative structure driving the conflict more than core language ability?")
    return questions


def select_cases(df: pd.DataFrame, max_cases: int) -> pd.DataFrame:
    work = df[df["review_priority"].isin(REVIEW_PRIORITIES)].copy()
    priority_rank = {name: i for i, name in enumerate(REVIEW_PRIORITIES)}
    work["priority_rank"] = work["review_priority"].map(priority_rank)
    work = work.sort_values(
        [
            "priority_rank",
            "full_language_no_age",
            "full_language_age",
            "corpus",
            "participant_root",
        ],
        ascending=[True, False, False, True, True],
    ).head(max_cases)
    work = work.reset_index(drop=True)
    work["case_id"] = [f"DLD-CONFLICT-{i:03d}" for i in range(1, len(work) + 1)]
    work["compact_participant_id"] = work["participant_root"].map(compact_id)
    work["case_specific_questions"] = work.apply(
        lambda row: " | ".join(case_specific_questions(row)), axis=1
    )
    return work


def write_review_packet(cases: pd.DataFrame, out_path: Path) -> None:
    lines = [
        "# DLD Conflict Review Packet",
        "",
        "This packet contains the highest-value DLD/TD conflict cases from the local CHILDES/DLD audit. It is for expert review and study design, not clinical decision-making.",
        "",
        "## General Review Questions",
        "",
    ]
    lines.extend([f"- {question}" for question in GENERAL_REVIEW_QUESTIONS])
    lines.extend(["", "## Cases", ""])

    for _, row in cases.iterrows():
        detail = pd.DataFrame(
            [
                {
                    "field": "participant",
                    "value": row["compact_participant_id"],
                },
                {
                    "field": "corpus / label",
                    "value": f"{row['corpus']} / {row['screen_label']}",
                },
                {
                    "field": "age range months",
                    "value": f"{row['age_min']:.1f}-{row['age_max']:.1f}",
                },
                {
                    "field": "task",
                    "value": f"{row['task_bucket']} ({row['task_proxy']})",
                },
                {
                    "field": "conflict",
                    "value": row["conflict_archetype"],
                },
                {
                    "field": "language-only risk",
                    "value": f"{row['full_language_no_age']:.3f}",
                },
                {
                    "field": "language+age risk",
                    "value": f"{row['full_language_age']:.3f}",
                },
                {
                    "field": "MLU+age risk",
                    "value": f"{row['mlu_age']:.3f}",
                },
                {
                    "field": "corpus+age risk",
                    "value": f"{row['corpus_age']:.3f}",
                },
            ]
        )
        lines.extend(
            [
                f"### {row['case_id']}: {row['compact_participant_id']}",
                "",
                md_table(detail),
                "",
                "**Review prompts**",
                "",
            ]
        )
        for question in case_specific_questions(row):
            lines.append(f"- {question}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    conflicts = pd.read_csv(args.conflicts)
    cases = select_cases(conflicts, args.max_cases)
    review_cases = cases[CASE_COLUMNS + ["compact_participant_id", "case_specific_questions"]].copy()

    review_cases.to_csv(out_dir / "review_cases.csv", index=False)
    write_review_packet(cases, out_dir / "review_packet.md")

    priority_summary = (
        cases.groupby("review_priority")
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )
    corpus_summary = (
        cases.groupby(["corpus", "review_priority"])
        .size()
        .reset_index(name="n")
        .sort_values(["n", "corpus"], ascending=[False, True])
    )
    task_summary = (
        cases.groupby("task_bucket")
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )
    compact_cases = review_cases[
        [
            "case_id",
            "compact_participant_id",
            "corpus",
            "screen_label",
            "age_min",
            "task_bucket",
            "conflict_archetype",
            "review_priority",
            "full_language_no_age",
            "corpus_age",
            "mlu_age",
        ]
    ].copy()
    compact_cases[["age_min", "full_language_no_age", "corpus_age", "mlu_age"]] = compact_cases[
        ["age_min", "full_language_no_age", "corpus_age", "mlu_age"]
    ].round(3)

    lines = [
        "# DLD Conflict Review Packet Summary",
        "",
        f"- Review cases packaged: {len(review_cases):,}",
        "- Selection rule: all `highest_clinical_fairness_review` cases plus the strongest `highest_scientific_review` cases.",
        f"- Packet: `{out_dir / 'review_packet.md'}`",
        "",
        "## Priority Mix",
        "",
        md_table(priority_summary),
        "",
        "## Corpus Mix",
        "",
        md_table(corpus_summary),
        "",
        "## Task Mix",
        "",
        md_table(task_summary),
        "",
        "## Case Index",
        "",
        md_table(compact_cases),
        "",
        "## Interpretation",
        "",
        "These 15 cases are the best current bridge from model result to field question. The clinical-fairness cases ask whether TD-labeled children can look language-risky after removing corpus/age shortcuts. The scientific cases ask whether language-only risk is capturing a non-MLU developmental signal or merely exposing label/task/context noise. The next step is expert review of the underlying transcripts and metadata, ideally paired with a structured sentence/nonword repetition probe in future data.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
