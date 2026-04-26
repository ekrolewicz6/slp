"""Probe whether 1-best ASR contains near-miss evidence for omitted concepts."""

from __future__ import annotations

import argparse
import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from scripts.run_cross_prompt_content import CONCEPTS, chat_tokens  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--concept-rows",
        default="outputs/asr_concept_evidence_pwa12_tiny/clip_concept_rows.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/asr_phonological_neighbor_probe_pwa12_tiny",
        type=Path,
    )
    parser.add_argument("--random-repeats", default=200, type=int)
    parser.add_argument("--seed", default=0, type=int)
    return parser.parse_args()


def alias_tokens(task: str, concept: str) -> list[str]:
    aliases = CONCEPTS.get(task, {}).get(concept, [])
    toks = []
    for alias in aliases:
        toks.extend(chat_tokens(str(alias).replace("_", " ")))
    return sorted(set(toks))


def token_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return float(SequenceMatcher(None, a, b).ratio())


def concept_similarity(asr_tokens: list[str], task: str, concept: str) -> float:
    aliases = alias_tokens(task, concept)
    if not aliases or not asr_tokens:
        return 0.0
    return max(token_similarity(tok, alias) for tok in asr_tokens for alias in aliases)


def build_probe_rows(rows: pd.DataFrame, random_repeats: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    probe_rows = []
    random_rows = []
    group_cols = ["transcript_id", "task", "utterance_idx"]
    for _, group in rows.groupby(group_cols, dropna=False):
        task = str(group["task"].iloc[0])
        if task not in CONCEPTS:
            continue
        asr_text = str(group["asr_text"].iloc[0] or "")
        asr_toks = chat_tokens(asr_text)
        missed = set(
            group[
                group["human_concept_present"].eq(1)
                & group["asr_concept_present"].eq(0)
            ]["concept"].astype(str)
        )
        if not missed:
            continue
        asr_present = set(group[group["asr_concept_present"].eq(1)]["concept"].astype(str))
        candidates = [concept for concept in CONCEPTS[task] if concept not in asr_present]
        scored = sorted(
            [
                {
                    "concept": concept,
                    "similarity": concept_similarity(asr_toks, task, concept),
                }
                for concept in candidates
            ],
            key=lambda x: (x["similarity"], x["concept"]),
            reverse=True,
        )
        ranked = [x["concept"] for x in scored]
        sims = {x["concept"]: x["similarity"] for x in scored}
        for k in [1, 3, 5]:
            topk = set(ranked[:k])
            probe_rows.append(
                {
                    "transcript_id": group["transcript_id"].iloc[0],
                    "task": task,
                    "utterance_idx": group["utterance_idx"].iloc[0],
                    "k": k,
                    "asr_token_count": len(asr_toks),
                    "missed_concepts": json.dumps(sorted(missed)),
                    "n_missed_concepts": len(missed),
                    "candidate_count": len(candidates),
                    "top_candidates": json.dumps(ranked[:k]),
                    "hit_any_missed": int(bool(topk & missed)),
                    "missed_concept_recall": len(topk & missed) / max(len(missed), 1),
                    "max_missed_similarity": max([sims.get(c, 0.0) for c in missed] or [0.0]),
                }
            )
        for repeat in range(random_repeats):
            shuffled = list(candidates)
            rng.shuffle(shuffled)
            for k in [1, 3, 5]:
                topk = set(shuffled[:k])
                random_rows.append(
                    {
                        "repeat": repeat,
                        "k": k,
                        "hit_any_missed": int(bool(topk & missed)),
                        "missed_concept_recall": len(topk & missed) / max(len(missed), 1),
                    }
                )
    return pd.DataFrame(probe_rows), pd.DataFrame(random_rows)


def summarize(probe: pd.DataFrame, random_probe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if probe.empty:
        return pd.DataFrame(), pd.DataFrame()
    summary = (
        probe.groupby("k")
        .agg(
            n_miss_clips=("utterance_idx", "size"),
            hit_any_missed=("hit_any_missed", "mean"),
            missed_concept_recall=("missed_concept_recall", "mean"),
            mean_candidate_count=("candidate_count", "mean"),
            mean_max_missed_similarity=("max_missed_similarity", "mean"),
            near_miss_ge_65=("max_missed_similarity", lambda x: (x >= 0.65).mean()),
            near_miss_ge_75=("max_missed_similarity", lambda x: (x >= 0.75).mean()),
            near_miss_ge_85=("max_missed_similarity", lambda x: (x >= 0.85).mean()),
        )
        .reset_index()
    )
    random_summary = (
        random_probe.groupby(["repeat", "k"])
        .agg(
            hit_any_missed=("hit_any_missed", "mean"),
            missed_concept_recall=("missed_concept_recall", "mean"),
        )
        .reset_index()
        .groupby("k")
        .agg(
            random_hit_any_mean=("hit_any_missed", "mean"),
            random_hit_any_p95=("hit_any_missed", lambda x: np.quantile(x, 0.95)),
            random_recall_mean=("missed_concept_recall", "mean"),
            random_recall_p95=("missed_concept_recall", lambda x: np.quantile(x, 0.95)),
        )
        .reset_index()
    )
    return summary, random_summary


def write_summary(
    out_dir: Path,
    probe: pd.DataFrame,
    summary: pd.DataFrame,
    random_summary: pd.DataFrame,
) -> None:
    merged = summary.merge(random_summary, on="k", how="left") if not summary.empty else summary
    examples = probe.sort_values("max_missed_similarity", ascending=False).head(20)
    lines = [
        "# ASR Phonological/String Neighbor Probe",
        "",
        f"- Missed-concept clip rows: {len(probe)}",
        "",
        "## Top-k Recovery Of Missed Concepts",
        "",
        md_table(merged.round(3)),
        "",
        "## Strongest Near-Miss Examples",
        "",
        md_table(
            examples[
                [
                    "transcript_id",
                    "task",
                    "utterance_idx",
                    "k",
                    "missed_concepts",
                    "top_candidates",
                    "max_missed_similarity",
                ]
            ].round(3)
        ),
        "",
        "## Interpretation",
        "",
        "This asks whether the 1-best ASR text preserves a string-level clue for "
        "concepts it failed to recognize exactly. If top-k recovery beats random "
        "and near-miss similarity is common, phonological-neighbor features may "
        "help a clarification gate. If it is close to random, we need actual "
        "ASR alternatives or audio-level forced alignment rather than mining the "
        "1-best transcript.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    rows = pd.read_csv(args.concept_rows)
    probe, random_probe = build_probe_rows(rows, args.random_repeats, args.seed)
    summary, random_summary = summarize(probe, random_probe)
    probe.to_csv(out_dir / "neighbor_probe_rows.csv", index=False)
    random_probe.to_csv(out_dir / "random_neighbor_probe_rows.csv", index=False)
    summary.to_csv(out_dir / "neighbor_summary.csv", index=False)
    random_summary.to_csv(out_dir / "random_neighbor_summary.csv", index=False)
    write_summary(out_dir, probe, summary, random_summary)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
