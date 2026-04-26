"""Build per-child longitudinal sequences in latent space.

Some CHILDES `child_id` values are actually multi-child cohorts (HSLLD HV1,
Gelman cohort labels, Morisset Seattle/Topeka, NewmanRatner numeric IDs) —
their "sessions" cluster at single ages. We filter those out by requiring
the per-child age series to have a meaningful spread *and* a non-trivial
mean inter-session gap.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ChildSequence:
    child_id: str
    corpus: str
    times: np.ndarray  # ages in months, sorted ascending
    Z: np.ndarray      # latent state, one row per time, same order as times


def build_sequences(
    df: pd.DataFrame,
    Z: np.ndarray,
    *,
    min_sessions: int = 5,
    min_age_span_months: float = 6.0,
    min_mean_gap_days: float = 3.0,
) -> list[ChildSequence]:
    """Return one ChildSequence per child that passes the longitudinal filter.

    `df` must align row-for-row with `Z`. Required columns: `child_id`,
    `corpus`, `age_months`.
    """
    if len(df) != len(Z):
        raise ValueError("df and Z must align")

    work = df.reset_index(drop=True).copy()
    work["__row"] = np.arange(len(work))

    sequences: list[ChildSequence] = []
    for (corpus, child), grp in work.groupby(["corpus", "child_id"], sort=False):
        if len(grp) < min_sessions:
            continue
        ordered = grp.sort_values("age_months")
        ages = ordered["age_months"].to_numpy(dtype=float)
        rows = ordered["__row"].to_numpy(dtype=int)

        span = float(ages.max() - ages.min())
        if span < min_age_span_months:
            continue
        # Inter-session gaps in days. Reject cohort-style groupings where many
        # rows share the same nominal age.
        gaps_days = np.diff(ages) * 30.4375
        if gaps_days.size == 0 or float(np.mean(gaps_days)) < min_mean_gap_days:
            continue

        sequences.append(ChildSequence(
            child_id=str(child),
            corpus=str(corpus),
            times=ages,
            Z=Z[rows],
        ))
    return sequences


def summarize_sequences(sequences: list[ChildSequence]) -> pd.DataFrame:
    return pd.DataFrame([{
        "corpus": s.corpus,
        "child_id": s.child_id,
        "n_sessions": len(s.times),
        "age_min": float(s.times.min()),
        "age_max": float(s.times.max()),
        "age_span": float(s.times.max() - s.times.min()),
    } for s in sequences])
