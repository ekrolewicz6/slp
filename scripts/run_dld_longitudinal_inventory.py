#!/usr/bin/env python3
"""Inventory local DLD/child-language longitudinal candidates."""

from __future__ import annotations

from pathlib import Path
import re
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_dld_state_screening import clinical_label, participant_root  # noqa: E402


FEATURES_PATH = Path("data/features/phase1_windowed_features.parquet")
OUT_DIR = Path("outputs/dld_longitudinal_inventory")


def md_table(df: pd.DataFrame, columns: list[str], max_rows: int | None = None) -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "_No rows._"
    view = df[columns].copy()
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(row[c]) else str(row[c]) for c in columns) + " |")
    return "\n".join(lines)


def repaired_age_months(transcript_id: str, age_months: float | None) -> float | None:
    if pd.notna(age_months):
        return float(age_months)
    parts = transcript_id.split("/")
    # Rescorla paths: Clinical-Eng/Rescorla/LT/156/name156
    if len(parts) >= 5 and parts[0] == "Clinical-Eng" and parts[1] == "Rescorla":
        if re.fullmatch(r"\d+", parts[3]):
            return float(parts[3])
        m = re.search(r"(36|48|60|108|156)$", parts[-1])
        if m:
            return float(m.group(1))
    # EllisWeismer paths often include tokens such as 30ec, 42pc, 54int, 66conv.
    for token in parts:
        m = re.match(r"^(30|42|54|66|78|90|108|120|156)", token)
        if m:
            return float(m.group(1))
    return None


def task_proxy(transcript_id: str) -> str:
    low = transcript_id.casefold()
    if any(tok in low for tok in ["conv", "conversation", "interview"]):
        return "conversation"
    if any(tok in low for tok in ["toyplay", "freeplay", "free play", "/play", "/pc", "parentchild"]):
        return "play_parent_child"
    if any(tok in low for tok in ["frog", "narrative", "story", "enni", "gillam"]):
        return "narrative"
    if "/ec" in low or low.endswith("ec"):
        return "examiner_child"
    if "int" in low:
        return "interview"
    if "read" in low:
        return "reading"
    return "unknown"


def load_clinical() -> pd.DataFrame:
    df = pd.read_parquet(FEATURES_PATH)
    clinical = df[df["bundle"].eq("Clinical-Eng")].copy()
    clinical["clinical_label"] = clinical["transcript_id"].map(clinical_label)
    clinical["participant_root"] = [
        participant_root(tid, lab)
        for tid, lab in zip(clinical["transcript_id"], clinical["clinical_label"])
    ]
    clinical["age_repaired"] = [
        repaired_age_months(tid, age)
        for tid, age in zip(clinical["transcript_id"], clinical["age_months"])
    ]
    clinical["task_proxy"] = clinical["transcript_id"].map(task_proxy)
    return clinical


def summarize(clinical: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    corpus_label = (
        clinical.groupby(["corpus", "clinical_label"], dropna=False)
        .agg(
            windows=("window_id", "nunique"),
            transcripts=("transcript_id", "nunique"),
            participants=("participant_root", "nunique"),
            ages=("age_repaired", "nunique"),
            min_age=("age_repaired", "min"),
            max_age=("age_repaired", "max"),
            task_types=("task_proxy", "nunique"),
        )
        .reset_index()
        .sort_values(["participants", "transcripts"], ascending=False)
    )

    participant = (
        clinical.groupby(["corpus", "clinical_label", "participant_root"], dropna=False)
        .agg(
            windows=("window_id", "nunique"),
            transcripts=("transcript_id", "nunique"),
            ages=("age_repaired", "nunique"),
            min_age=("age_repaired", "min"),
            max_age=("age_repaired", "max"),
            task_types=("task_proxy", lambda s: ",".join(sorted(set(map(str, s))))),
        )
        .reset_index()
    )
    participant["age_span_months"] = participant["max_age"] - participant["min_age"]
    participant["longitudinal_candidate"] = (participant["ages"] >= 2) | (
        participant["transcripts"] >= 2
    )

    long_by_corpus = (
        participant[participant["longitudinal_candidate"]]
        .groupby(["corpus", "clinical_label"], dropna=False)
        .agg(
            longitudinal_participants=("participant_root", "nunique"),
            median_ages=("ages", "median"),
            max_ages=("ages", "max"),
            median_age_span=("age_span_months", "median"),
            max_age_span=("age_span_months", "max"),
            task_type_sets=("task_types", lambda s: "; ".join(sorted(set(map(str, s)))[:8])),
        )
        .reset_index()
        .sort_values(["longitudinal_participants", "max_age_span"], ascending=False)
    )

    task_by_corpus = (
        clinical.groupby(["corpus", "task_proxy"], dropna=False)
        .agg(
            transcripts=("transcript_id", "nunique"),
            participants=("participant_root", "nunique"),
            labels=("clinical_label", "nunique"),
        )
        .reset_index()
        .sort_values(["transcripts", "participants"], ascending=False)
    )

    corpus_label.to_csv(OUT_DIR / "corpus_label_inventory.csv", index=False)
    participant.to_csv(OUT_DIR / "participant_longitudinal_inventory.csv", index=False)
    long_by_corpus.to_csv(OUT_DIR / "longitudinal_candidates_by_corpus.csv", index=False)
    task_by_corpus.to_csv(OUT_DIR / "task_proxy_by_corpus.csv", index=False)

    n_participants = clinical["participant_root"].nunique()
    n_long = int(participant["longitudinal_candidate"].sum())
    n_multi_age = int((participant["ages"] >= 2).sum())
    n_outcome_cols = len(
        [
            c
            for c in clinical.columns
            if any(tok in c.casefold() for tok in ["outcome", "literacy", "reading", "school"])
        ]
    )

    summary = f"""# DLD / Late-Talker Longitudinal Inventory

**Date:** 2026-04-30
**Script:** `scripts/run_dld_longitudinal_inventory.py`

## Scope

Loaded `data/features/phase1_windowed_features.parquet` and restricted to
Clinical-Eng windows. Participant roots use the same reconstruction logic as
the DLD screening and Rescorla catch-up scripts. Ages are repaired from paths
for Rescorla and common EllisWeismer age/task tokens where needed.

## Headline Counts

- Clinical-Eng windows: **{len(clinical):,}**
- transcripts: **{clinical['transcript_id'].nunique():,}**
- reconstructed participant roots: **{n_participants:,}**
- participants with repeated transcripts or repeated ages: **{n_long:,}**
- participants with at least two distinct ages: **{n_multi_age:,}**
- explicit outcome/literacy/school columns in this feature table: **{n_outcome_cols}**

## Best Local Longitudinal Candidates

{md_table(long_by_corpus, ['corpus', 'clinical_label', 'longitudinal_participants', 'median_ages', 'max_ages', 'median_age_span', 'max_age_span', 'task_type_sets'], max_rows=30)}

## Corpus/Label Inventory

{md_table(corpus_label, ['corpus', 'clinical_label', 'windows', 'transcripts', 'participants', 'ages', 'min_age', 'max_age', 'task_types'], max_rows=40)}

## Task Proxy Inventory

{md_table(task_by_corpus, ['corpus', 'task_proxy', 'transcripts', 'participants', 'labels'], max_rows=40)}

## Interpretation

The local Clinical-Eng data contain repeated samples, especially Rescorla and
EllisWeismer, but this feature table does not contain the outcome fields needed
for strong treatment-response or school/literacy prediction claims. Local DLD
work remains useful for mechanism, persistent-gap description, and data-needs
definition. It is not enough for the final clinical claim.

## Next Actions

1. Use Rescorla and EllisWeismer for local trajectory descriptions.
2. Keep Manchester Language Study and E-DLD access as the main outcome-linkage
   targets.
3. Do not claim DLD treatment-response prediction from local Clinical-Eng alone.
4. Pair this inventory with `outputs/structured_task_inventory/summary.md` to
   choose any natural-plus-structured child-language experiment.
"""
    (OUT_DIR / "summary.md").write_text(summary)


def main() -> None:
    clinical = load_clinical()
    summarize(clinical)
    print(f"Wrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()
