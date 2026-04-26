"""Random-vocabulary placebo for cross-prompt content scoring.

The true prompt concept sets should beat arbitrary task words sampled from the
same CHAT transcripts. This is a negative control against the explanation that
the content score is just "any words produced" or generic lexical richness.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_cross_prompt_content import (  # noqa: E402
    CONCEPTS,
    FUNCTION_WORDS,
    chat_tokens,
    parse_task_utterances,
    stem,
)
from src.analysis.review_grade import (  # noqa: E402
    cross_val_predict_regressor,
    ensure_dir,
    regression_summary,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--segments", default="outputs/cross_prompt_content/task_segments.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/cross_prompt_placebo", type=Path)
    p.add_argument("--n-placebo", default=100, type=int)
    p.add_argument("--cv-folds", default=5, type=int)
    p.add_argument("--seed", default=0, type=int)
    return p.parse_args()


def token_sets(df: pd.DataFrame) -> dict[tuple[str, str], set[str]]:
    cache: dict[str, dict[str, list[str]]] = {}
    out: dict[tuple[str, str], set[str]] = {}
    for path, task in df[["file_path", "task"]].drop_duplicates().itertuples(index=False):
        if path not in cache:
            segments = parse_task_utterances(Path(path))
            cache[path] = {
                t: chat_tokens(" ".join(utts), include_targets=False)
                for t, utts in segments.items()
            }
        toks = cache.get(path, {}).get(task, [])
        out[(path, task)] = {stem(t) for t in toks if t not in FUNCTION_WORDS and len(t) > 2}
    return out


def task_vocab(df: pd.DataFrame, sets: dict[tuple[str, str], set[str]]) -> dict[str, list[str]]:
    vocabs = {}
    for task, group in df.groupby("task"):
        doc_counts: Counter[str] = Counter()
        for path, t in group[["file_path", "task"]].drop_duplicates().itertuples(index=False):
            doc_counts.update(sets.get((path, t), set()))
        n_docs = max(1, group[["file_path", "task"]].drop_duplicates().shape[0])
        true_terms = {stem(term) for terms in CONCEPTS.get(task, {}).values() for term in terms}
        vocab = [
            word
            for word, count in doc_counts.items()
            if count >= 10 and count / n_docs <= 0.90 and word not in true_terms
        ]
        vocabs[task] = sorted(vocab)
    return vocabs


def add_placebo_features(
    df: pd.DataFrame,
    sets: dict[tuple[str, str], set[str]],
    sampled: dict[str, list[str]],
) -> pd.DataFrame:
    out = df.copy()
    coverage = []
    density = []
    for row in out.itertuples(index=False):
        words = sampled.get(row.task, [])
        token_set = sets.get((row.file_path, row.task), set())
        hits = len(set(words) & token_set)
        n_words = max(1, len(words))
        coverage.append(hits / n_words)
        density.append(hits / max(float(row.observed_n_tokens), 1.0))
    out["placebo_coverage_frac"] = coverage
    out["placebo_density"] = density
    return out


def score_model(df: pd.DataFrame, features: list[str], cv_folds: int) -> dict:
    y, pred = cross_val_predict_regressor(
        df,
        "wab_aq",
        {"content": features},
        categorical_cols=["task"],
        group_col="patient_root",
        cv_mode="group",
        n_splits=cv_folds,
    )
    return regression_summary(y, pred)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    rng = np.random.default_rng(args.seed)

    df = pd.read_csv(args.segments)
    df = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy().reset_index(drop=True)
    df = df[df["task"].isin(CONCEPTS)].copy().reset_index(drop=True)
    sets = token_sets(df)
    vocabs = task_vocab(df, sets)

    true_features = [
        "observed_concept_coverage_frac",
        "observed_concept_density",
        "observed_concept_token_ratio",
    ]
    true = score_model(df, true_features, args.cv_folds)

    rows = []
    for i in range(args.n_placebo):
        sampled = {}
        for task in sorted(df["task"].unique()):
            n_concepts = len(CONCEPTS[task])
            vocab = vocabs.get(task, [])
            if len(vocab) < n_concepts:
                sampled[task] = vocab
            else:
                sampled[task] = rng.choice(vocab, size=n_concepts, replace=False).tolist()
        placebo_df = add_placebo_features(df, sets, sampled)
        result = score_model(placebo_df, ["placebo_coverage_frac", "placebo_density"], args.cv_folds)
        rows.append(
            {
                "iteration": i,
                **result,
                "sampled_words": ";".join(f"{task}:{','.join(words)}" for task, words in sampled.items()),
            }
        )

    placebo = pd.DataFrame(rows)
    placebo.to_csv(out_dir / "placebo_scores.csv", index=False)
    summary = pd.DataFrame(
        [
            {"model": "true_prompt_concepts", **true},
            {
                "model": "random_vocab_mean",
                "n": int(placebo["n"].iloc[0]) if len(placebo) else 0,
                "mae": float(placebo["mae"].mean()),
                "rmse": float(placebo["rmse"].mean()),
                "r": float(placebo["r"].mean()),
            },
            {
                "model": "random_vocab_p95",
                "n": int(placebo["n"].iloc[0]) if len(placebo) else 0,
                "mae": float(placebo["mae"].quantile(0.05)),
                "rmse": float(placebo["rmse"].quantile(0.05)),
                "r": float(placebo["r"].quantile(0.95)),
            },
            {
                "model": "random_vocab_max",
                "n": int(placebo["n"].iloc[0]) if len(placebo) else 0,
                "mae": float(placebo["mae"].min()),
                "rmse": float(placebo["rmse"].min()),
                "r": float(placebo["r"].max()),
            },
        ]
    )
    summary["true_minus_value"] = np.nan
    true_r = float(true["r"])
    summary.loc[summary["model"].ne("true_prompt_concepts"), "true_minus_value"] = (
        true_r - summary.loc[summary["model"].ne("true_prompt_concepts"), "r"]
    )
    summary.to_csv(out_dir / "placebo_summary.csv", index=False)

    print(summary.to_string(index=False))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
