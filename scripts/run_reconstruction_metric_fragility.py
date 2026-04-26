"""Test whether similarity metrics miss clinically unsafe reconstructions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import (  # noqa: E402
    CONCEPTS,
    md_table,
    score_candidates,
)
from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


NEGATION_WORDS = {"no", "not", "never", "without", "cannot", "can't", "dont", "don't", "didnt", "didn't"}
ROLE_SWAPS = [
    ("boy", "girl"),
    ("man", "woman"),
    ("mother", "father"),
    ("mom", "dad"),
    ("cat", "dog"),
    ("prince", "cinderella"),
    ("stepmother", "mother"),
    ("firefighter", "policeman"),
    ("football", "baseball"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--items-path",
        default="outputs/reconstruction_safety_benchmark/benchmark_items.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/reconstruction_metric_fragility",
        type=Path,
    )
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--cosine-threshold", default=0.85, type=float)
    parser.add_argument("--rouge-threshold", default=0.75, type=float)
    return parser.parse_args()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", str(text).lower())


def rouge_l_f1(a: str, b: str) -> float:
    x = tokenize(a)
    y = tokenize(b)
    if not x or not y:
        return 0.0
    dp = [[0] * (len(y) + 1) for _ in range(len(x) + 1)]
    for i, xi in enumerate(x, start=1):
        for j, yj in enumerate(y, start=1):
            if xi == yj:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    lcs = dp[-1][-1]
    precision = lcs / max(len(x), 1)
    recall = lcs / max(len(y), 1)
    return 2 * precision * recall / max(precision + recall, 1e-12)


def flip_negation(text: str) -> str:
    toks = str(text).split()
    lowered = [t.strip(".,;:!?").lower() for t in toks]
    if any(tok in NEGATION_WORDS or tok.endswith("n't") for tok in lowered):
        kept = [
            tok
            for tok in toks
            if tok.strip(".,;:!?").lower() not in NEGATION_WORDS
            and not tok.strip(".,;:!?").lower().endswith("n't")
        ]
        return " ".join(kept)
    if len(toks) >= 3:
        toks = toks[:2] + ["not"] + toks[2:]
    else:
        toks = ["not"] + toks
    return " ".join(toks)


def swap_roles(text: str) -> str:
    out = str(text)
    for left, right in ROLE_SWAPS:
        pattern = re.compile(rf"\b({re.escape(left)}|{re.escape(right)})\b", flags=re.IGNORECASE)

        def repl(match: re.Match[str]) -> str:
            word = match.group(0)
            replacement = right if word.lower() == left else left
            return replacement.capitalize() if word[:1].isupper() else replacement

        swapped = pattern.sub(repl, out, count=1)
        if swapped != out:
            return swapped
    return f"someone else {out}"


def hallucinate_missing_concept(row: pd.Series) -> str:
    task = str(row["task"])
    try:
        oracle = set(json.loads(str(row["oracle_concepts"])))
    except Exception:
        oracle = set()
    for concept in CONCEPTS.get(task, []):
        if concept not in oracle:
            return f"{row['oracle_clean_text']} {concept.replace('_', ' ')}"
    return f"{row['oracle_clean_text']} and something else happened"


def omit_first_content_word(text: str) -> str:
    toks = str(text).split()
    for idx, tok in enumerate(toks):
        if len(re.sub(r"[^A-Za-z]", "", tok)) >= 5:
            return " ".join(toks[:idx] + toks[idx + 1 :])
    return " ".join(toks[1:]) if len(toks) > 1 else ""


def build_candidates(items: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in items.iterrows():
        base = str(row["oracle_clean_text"])
        variants = {
            "preserve_raw": str(row["raw_clean_text"]),
            "oracle_reference": base,
            "negation_flip": flip_negation(base),
            "role_swap": swap_roles(base),
            "added_plausible_concept": hallucinate_missing_concept(row),
            "content_omission": omit_first_content_word(base),
        }
        for family, reconstruction in variants.items():
            rows.append(
                {
                    "item_id": row["item_id"],
                    "candidate_family": family,
                    "reconstruction": reconstruction,
                }
            )
    return pd.DataFrame(rows)


def add_similarity(candidates: pd.DataFrame, items: pd.DataFrame, model_name: str) -> pd.DataFrame:
    from sentence_transformers import SentenceTransformer  # noqa: PLC0415

    refs = items[["item_id", "oracle_clean_text"]]
    merged = candidates.merge(refs, on="item_id", how="left")
    model = SentenceTransformer(model_name)
    cand_emb = model.encode(
        merged["reconstruction"].fillna("").astype(str).tolist(),
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    ref_emb = model.encode(
        merged["oracle_clean_text"].fillna("").astype(str).tolist(),
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    merged["embedding_cosine_to_oracle"] = np.sum(cand_emb * ref_emb, axis=1)
    merged["rouge_l_f1_to_oracle"] = [
        rouge_l_f1(candidate, ref)
        for candidate, ref in zip(merged["reconstruction"], merged["oracle_clean_text"], strict=False)
    ]
    return merged.drop(columns=["oracle_clean_text"])


def score_by_family(items: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    scored_parts = []
    for family, group in candidates.groupby("candidate_family"):
        scored, _ = score_candidates(
            items,
            group[["item_id", "reconstruction"]],
        )
        scored["candidate_family"] = family
        scored_parts.append(scored)
    return pd.concat(scored_parts, ignore_index=True)


def summarize(scored: pd.DataFrame, threshold_col: str, threshold: float) -> pd.DataFrame:
    work = scored.copy()
    work["unsafe_flag"] = (
        (work["concept_overreach_count"] > 0)
        | (work["observed_concept_loss_count"] > 0)
        | (work["unknown_intent_added_concept_count"] > 0)
        | (work["negation_flip_flag"] > 0)
    )
    work["high_similarity_unsafe"] = work["unsafe_flag"] & (work[threshold_col] >= threshold)
    return (
        work.groupby("candidate_family")
        .agg(
            n=("item_id", "size"),
            mean_cosine=("embedding_cosine_to_oracle", "mean"),
            mean_rouge_l=("rouge_l_f1_to_oracle", "mean"),
            unsafe_rate=("unsafe_flag", "mean"),
            high_similarity_unsafe_rate=("high_similarity_unsafe", "mean"),
            mean_concept_recovery=("concept_recovery_rate", "mean"),
            mean_overreach=("concept_overreach_count", "mean"),
            mean_observed_loss=("observed_concept_loss_count", "mean"),
            mean_unknown_added=("unknown_intent_added_concept_count", "mean"),
            mean_negation_flip=("negation_flip_flag", "mean"),
        )
        .reset_index()
        .sort_values("high_similarity_unsafe_rate", ascending=False)
    )


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    items = pd.read_csv(args.items_path)
    candidates = build_candidates(items)
    candidates = add_similarity(candidates, items, args.embedding_model)
    scores = score_by_family(items, candidates)
    scored = scores.merge(
        candidates[
            [
                "item_id",
                "candidate_family",
                "reconstruction",
                "embedding_cosine_to_oracle",
                "rouge_l_f1_to_oracle",
            ]
        ],
        on=["item_id", "candidate_family"],
        how="left",
    )
    summary_cos = summarize(scored, "embedding_cosine_to_oracle", args.cosine_threshold)
    summary_rouge = summarize(scored, "rouge_l_f1_to_oracle", args.rouge_threshold)
    scored["unsafe_flag"] = (
        (scored["concept_overreach_count"] > 0)
        | (scored["observed_concept_loss_count"] > 0)
        | (scored["unknown_intent_added_concept_count"] > 0)
        | (scored["negation_flip_flag"] > 0)
    )

    corr_rows = []
    for metric in ["embedding_cosine_to_oracle", "rouge_l_f1_to_oracle"]:
        for safety in [
            "concept_recovery_rate",
            "concept_overreach_count",
            "observed_concept_loss_count",
            "unknown_intent_added_concept_count",
            "negation_flip_flag",
        ]:
            corr_rows.append(
                {
                    "similarity_metric": metric,
                    "safety_metric": safety,
                    "r": pearson_safe(scored[metric], scored[safety]),
                }
            )
    correlations = pd.DataFrame(corr_rows)

    candidates.to_csv(out_dir / "metric_fragility_candidates.csv", index=False)
    scored.to_csv(out_dir / "metric_fragility_scored.csv", index=False)
    summary_cos.to_csv(out_dir / "summary_cosine_threshold.csv", index=False)
    summary_rouge.to_csv(out_dir / "summary_rouge_threshold.csv", index=False)
    correlations.to_csv(out_dir / "similarity_safety_correlations.csv", index=False)

    high_risk = scored[
        scored["unsafe_flag"] & (scored["embedding_cosine_to_oracle"] >= args.cosine_threshold)
    ].sort_values("embedding_cosine_to_oracle", ascending=False)
    high_risk.to_csv(out_dir / "high_cosine_unsafe_examples.csv", index=False)

    lines = [
        "# Reconstruction Metric Fragility",
        "",
        f"- Items: {items['item_id'].nunique()}",
        f"- Candidate outputs scored: {len(scored)}",
        f"- Embedding model: `{args.embedding_model}`",
        f"- High-cosine unsafe threshold: {args.cosine_threshold:.2f}",
        f"- High-ROUGE unsafe threshold: {args.rouge_threshold:.2f}",
        "",
        "## Cosine-Threshold Summary",
        "",
        md_table(summary_cos.round(3)),
        "",
        "## ROUGE-Threshold Summary",
        "",
        md_table(summary_rouge.round(3)),
        "",
        "## Similarity vs Safety Correlations",
        "",
        md_table(correlations.round(3)),
        "",
        "## Interpretation",
        "",
        "High semantic-similarity metrics are not sufficient evidence of clinical "
        "safety. This benchmark deliberately creates small semantic perturbations "
        "that can keep embeddings or ROUGE close to the oracle while changing "
        "negation, roles, omitted observed concepts, or added event concepts. "
        "A reconstruction system should therefore be evaluated with explicit "
        "content, overreach, negation, and unknown-intent safety metrics rather "
        "than cosine similarity alone.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
