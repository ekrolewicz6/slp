"""Taxonomize high-confidence DLD label/corpus/state disagreements."""

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
    p = argparse.ArgumentParser()
    p.add_argument(
        "--candidates",
        default="outputs/dld_label_noise_sensitivity/label_noise_candidates.csv",
        type=Path,
    )
    p.add_argument(
        "--task-inventory",
        default="outputs/dld_task_context_comparison/task_context_inventory.csv",
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/dld_conflict_taxonomy", type=Path)
    return p.parse_args()


def age_band(age_months: float) -> str:
    if pd.isna(age_months):
        return "unknown"
    if age_months < 36:
        return "<36m"
    if age_months < 48:
        return "36-48m"
    if age_months < 60:
        return "48-60m"
    if age_months < 72:
        return "60-72m"
    if age_months < 96:
        return "72-96m"
    return ">=96m"


def screen_label_from_root(root: str) -> str:
    parts = str(root).split("/")
    if len(parts) >= 3:
        return parts[2]
    return "unknown"


def dominant_task_table(task_inventory: pd.DataFrame) -> pd.DataFrame:
    task = task_inventory.copy()
    task["rank"] = task.groupby(["corpus", "screen_label"])["participants"].rank(
        method="first", ascending=False
    )
    return (
        task[task["rank"].eq(1)][["corpus", "screen_label", "task_bucket", "task_proxy"]]
        .drop_duplicates(["corpus", "screen_label"])
    )


def archetype(row: pd.Series) -> str:
    flag = row["label_noise_flag"]
    mlu = row.get("mlu_age", np.nan)
    corpus_age = row.get("corpus_age", np.nan)
    lang_no_age = row.get("full_language_no_age", np.nan)
    if flag == "DLD_label_but_state_TD_like":
        if mlu >= 0.50:
            return "DLD_label_TD_state_but_MLU_risk"
        return "DLD_label_TD_state_broadly"
    if flag == "TD_label_but_state_risk":
        if corpus_age >= 0.70:
            return "TD_label_state_risk_plus_corpus_prior"
        return "TD_label_state_risk_language_driven"
    if flag == "corpus_age_driven_risk":
        return "corpus_age_prior_without_language_state"
    if flag == "language_state_risk_without_corpus":
        if mlu < 0.50:
            return "language_risk_without_corpus_not_MLU_only"
        return "language_risk_without_corpus_with_MLU"
    if lang_no_age >= 0.75:
        return "unflagged_language_high"
    return "no_high_conflict"


def review_priority(row: pd.Series) -> str:
    flag = row["label_noise_flag"]
    arch = row["conflict_archetype"]
    if flag == "language_state_risk_without_corpus":
        return "highest_scientific_review"
    if arch == "TD_label_state_risk_language_driven":
        return "highest_clinical_fairness_review"
    if flag == "TD_label_but_state_risk":
        return "review_for_hidden_risk_or_context"
    if flag == "corpus_age_driven_risk":
        return "deconfounding_not_clinical_claim"
    if flag == "DLD_label_but_state_TD_like":
        return "review_for_label_history_or_resolved_state"
    return "none"


def rate_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    total = df.groupby(cols).size().reset_index(name="total_participants")
    conflicts = (
        df[df["label_noise_flag"].ne("no_high_conflict")]
        .groupby(cols)
        .size()
        .reset_index(name="high_conflict_n")
    )
    out = total.merge(conflicts, on=cols, how="left").fillna({"high_conflict_n": 0})
    out["high_conflict_rate"] = out["high_conflict_n"] / out["total_participants"]
    return out.sort_values(["high_conflict_rate", "high_conflict_n"], ascending=False)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    candidates = pd.read_csv(args.candidates)
    task_inventory = pd.read_csv(args.task_inventory)

    task = dominant_task_table(task_inventory)
    df = candidates.copy()
    df["screen_label"] = df["participant_root"].map(screen_label_from_root)
    df["age_band"] = df["age_min"].map(age_band)
    df = df.merge(task, on=["corpus", "screen_label"], how="left")
    df["task_bucket"] = df["task_bucket"].fillna("unknown_or_mixed")
    df["task_proxy"] = df["task_proxy"].fillna("unknown")
    df["conflict_archetype"] = df.apply(archetype, axis=1)
    df["review_priority"] = df.apply(review_priority, axis=1)

    conflicts = df[df["label_noise_flag"].ne("no_high_conflict")].copy()
    archetype_summary = (
        conflicts.groupby(["conflict_archetype", "review_priority"])
        .agg(
            n=("participant_root", "count"),
            n_dld_labels=("y_true", "sum"),
            mean_age_min=("age_min", "mean"),
            mean_full_language_no_age=("full_language_no_age", "mean"),
            mean_corpus_age=("corpus_age", "mean"),
            mean_mlu_age=("mlu_age", "mean"),
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )
    corpus_rates = rate_table(df, ["corpus"])
    corpus_flag = (
        conflicts.groupby(["corpus", "label_noise_flag"])
        .size()
        .reset_index(name="n")
        .sort_values(["corpus", "n"], ascending=[True, False])
    )
    age_rates = rate_table(df, ["age_band"])
    task_rates = rate_table(df, ["task_bucket"])
    priority_summary = (
        conflicts.groupby("review_priority")
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )

    df.to_csv(out_dir / "participant_conflict_taxonomy.csv", index=False)
    conflicts.to_csv(out_dir / "high_conflict_taxonomy.csv", index=False)
    archetype_summary.to_csv(out_dir / "archetype_summary.csv", index=False)
    corpus_rates.to_csv(out_dir / "corpus_conflict_rates.csv", index=False)
    corpus_flag.to_csv(out_dir / "corpus_flag_counts.csv", index=False)
    age_rates.to_csv(out_dir / "age_band_conflict_rates.csv", index=False)
    task_rates.to_csv(out_dir / "task_bucket_conflict_rates.csv", index=False)
    priority_summary.to_csv(out_dir / "review_priority_summary.csv", index=False)

    top_corpus_rates = corpus_rates[corpus_rates["total_participants"] >= 10].head(12)
    lines = [
        "# DLD High-Conflict Taxonomy",
        "",
        f"- Participants audited: {len(df):,}",
        f"- High-confidence conflicts: {len(conflicts):,}",
        f"- Conflict rate: {len(conflicts) / len(df):.3f}",
        "",
        "## Review Priority Summary",
        "",
        md_table(priority_summary),
        "",
        "## Conflict Archetypes",
        "",
        md_table(archetype_summary.round(3)),
        "",
        "## Highest Corpus-Level Conflict Rates",
        "",
        md_table(top_corpus_rates.round(3)),
        "",
        "## Conflict Counts By Corpus And Flag",
        "",
        md_table(corpus_flag),
        "",
        "## Conflict Rates By Age Band",
        "",
        md_table(age_rates.round(3)),
        "",
        "## Conflict Rates By Task Context",
        "",
        md_table(task_rates.round(3)),
        "",
        "## Interpretation",
        "",
        "The most scientifically valuable cases are not the easiest DLD-vs-TD classifications. They are the disagreements where language-state risk remains high after removing corpus/age priors, or where TD labels conflict with language-driven risk. Corpus-age-driven cases should be treated as deconfounding warnings, not clinical evidence. DLD-labeled but TD-like state cases may reflect resolved/compensated state, label-history effects, task insensitivity, or a language dimension not captured by the current feature set.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
