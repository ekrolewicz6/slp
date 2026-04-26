"""Placebo test for Cinderella concept specificity.

Observed Cinderella concept coverage predicts WAB-AQ. This script asks whether
that is truly stimulus-conditioned content, or whether any matched set of
common transcript words would work equally well.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_salem_cinderella_deep import CINDERELLA_CONCEPTS, _tokenize  # noqa: E402
from src.analysis.review_grade import (  # noqa: E402
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--salem-root",
        default=(
            "data/raw/aphasiabank/extras/Salem/talkbank-preprocessed-cinderella-data/"
            "preprocessed-cinderella"
        ),
        type=Path,
    )
    p.add_argument("--joined", default="outputs/salem_cinderella_deep/salem_deep_joined.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/salem_story_specificity", type=Path)
    p.add_argument("--n-placebo", default=200, type=int)
    p.add_argument("--cv-folds", default=5, type=int)
    return p.parse_args()


def observed_tokens_by_session(yaml_path: Path) -> dict[str, list[str]]:
    text = yaml_path.read_text(encoding="utf-8", errors="ignore")
    blocks = re.split(r"\n- !Session\n", text)
    out = {}
    for block in blocks:
        m = re.search(r"session_id:\s*([A-Za-z0-9_-]+)", block)
        if not m:
            continue
        sid = m.group(1)
        template_lines = []
        in_template = False
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("template_texts:"):
                in_template = True
                continue
            if in_template and stripped.startswith("- "):
                template_lines.append(stripped[2:].strip("'\""))
                continue
            if in_template and not stripped.startswith("- "):
                in_template = False
        observed_text = re.sub(r"\{[^}]+\}", " ", " ".join(template_lines))
        out[sid] = _tokenize(observed_text)
    return out


def lexicon_features(tokens_by_session: dict[str, list[str]], lexicon: dict[str, list[str]], prefix: str) -> pd.DataFrame:
    rows = []
    for sid, toks in tokens_by_session.items():
        token_set = set(toks)
        hits = {
            name: int(any(term in token_set for term in terms))
            for name, terms in lexicon.items()
        }
        total = int(sum(hits.values()))
        rows.append(
            {
                "session_id": sid,
                f"{prefix}_coverage": float(total),
                f"{prefix}_density": float(total / max(len(toks), 1)),
                f"{prefix}_n_tokens": float(len(toks)),
                **{f"{prefix}_{k}": float(v) for k, v in hits.items()},
            }
        )
    return pd.DataFrame(rows)


def score_features(df: pd.DataFrame, cols: list[str], cv_folds: int) -> dict:
    sub = df.dropna(subset=["wab_aq", "participant_id"]).reset_index(drop=True)
    y, pred = cross_val_predict_regressor(
        sub,
        "wab_aq",
        {"features": cols},
        group_col="participant_id",
        cv_mode="group",
        n_splits=cv_folds,
    )
    return regression_summary(y, pred)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    yaml_path = args.salem_root / "aphasia-preprocessed" / "sessions.yaml"
    joined = pd.read_csv(args.joined)
    joined = joined[joined["extract_error"].fillna("") == ""].copy()
    tokens_by_session = observed_tokens_by_session(yaml_path)

    true_feat = lexicon_features(tokens_by_session, CINDERELLA_CONCEPTS, "true")
    base = joined[["session_id", "participant_id", "wab_aq"]].merge(true_feat, on="session_id", how="inner")
    true_cols = [c for c in base.columns if c.startswith("true_")]
    true_score = score_features(base, true_cols, args.cv_folds)
    true_corr = pearson_safe(base["true_coverage"], base["wab_aq"])

    concept_terms = {t for terms in CINDERELLA_CONCEPTS.values() for t in terms}
    session_counts: dict[str, int] = {}
    for toks in tokens_by_session.values():
        for tok in set(toks):
            if tok not in concept_terms and len(tok) > 1:
                session_counts[tok] = session_counts.get(tok, 0) + 1
    vocab = [tok for tok, n in session_counts.items() if n >= 5]
    sizes = [len(v) for v in CINDERELLA_CONCEPTS.values()]
    rng = np.random.default_rng(0)
    rows = []
    for i in range(args.n_placebo):
        lexicon = {}
        for j, size in enumerate(sizes):
            chosen = rng.choice(vocab, size=min(size, len(vocab)), replace=False)
            lexicon[f"placebo_{j:02d}"] = list(chosen)
        feat = lexicon_features(tokens_by_session, lexicon, "placebo")
        df = joined[["session_id", "participant_id", "wab_aq"]].merge(feat, on="session_id", how="inner")
        cols = [c for c in df.columns if c.startswith("placebo_")]
        score = score_features(df, cols, args.cv_folds)
        rows.append(
            {
                "iteration": i,
                "coverage_r": pearson_safe(df["placebo_coverage"], df["wab_aq"]),
                **score,
            }
        )
    placebo = pd.DataFrame(rows)
    placebo.to_csv(out_dir / "placebo_lexicon_scores.csv", index=False)
    summary = {
        "true_r_cv": true_score["r"],
        "true_mae": true_score["mae"],
        "true_coverage_r": true_corr,
        "placebo_r_mean": float(placebo["r"].mean()),
        "placebo_r_p95": float(placebo["r"].quantile(0.95)),
        "placebo_r_max": float(placebo["r"].max()),
        "placebo_coverage_r_mean": float(placebo["coverage_r"].mean()),
        "placebo_coverage_r_p95": float(placebo["coverage_r"].quantile(0.95)),
        "true_beats_placebo_p95": bool(true_score["r"] > placebo["r"].quantile(0.95)),
        "n_placebo": int(args.n_placebo),
        "vocab_size": int(len(vocab)),
    }
    pd.DataFrame([summary]).to_csv(out_dir / "story_specificity_summary.csv", index=False)
    print(pd.DataFrame([summary]).to_string(index=False))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
