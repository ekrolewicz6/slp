"""Phase 1 end-to-end: download → parse → features → models → metrics → plots.

Usage:
    python -m scripts.run_phase1 --corpus Brown
    python -m scripts.run_phase1 --corpus Brown,Providence,MacWhinney
    python -m scripts.run_phase1 --corpus all      # every Eng-NA corpus

Outputs land under `outputs/phase1/`:
    features.parquet         — one row per transcript
    transcripts.parquet      — transcript metadata index
    metrics.csv              — model × corpus × CV metrics
    predicted_vs_actual_<model>.png
    residuals_by_corpus_<model>.png
    feature_importance_<model>.png
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from src.evaluation.metrics import summarize
from src.features.extractors import extract_features
from src.ingestion.childes import (
    build_transcript_index,
    download_eng_na_bundle,
    load_corpus,
)
from src.models.phase1_age.train import (
    KIDEVAL_FEATURES,
    MLU_FEATURES,
    train_and_evaluate,
)
from src.viz.plots import (
    feature_importance,
    predicted_vs_actual,
    residuals_by_corpus,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data/raw", type=Path)
    p.add_argument("--features-dir", default="data/features", type=Path)
    p.add_argument("--output-dir", default="outputs/phase1", type=Path)
    p.add_argument("--corpus", default="Brown",
                   help='Comma-separated corpus names, or "all".')
    p.add_argument("--min-utterances", type=int, default=20,
                   help="Drop transcripts with fewer than this many CHI utterances.")
    p.add_argument("--max-age-months", type=float, default=84.0,
                   help="Drop transcripts above this child age (default 7 years).")
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


def select_corpora(eng_na_root: Path, request: str) -> list[str]:
    if request == "all":
        return sorted([d.name for d in eng_na_root.iterdir()
                       if d.is_dir() and not d.name.startswith(".")])
    return [c.strip() for c in request.split(",") if c.strip()]


def build_feature_table(eng_na_root: Path, corpora: list[str],
                        min_utts: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (features_df, transcript_index_df)."""
    all_records = []
    all_features = []
    for corpus in tqdm(corpora, desc="corpora"):
        corpus_path = eng_na_root / corpus
        if not corpus_path.exists():
            print(f"  [skip] {corpus}: not found at {corpus_path}")
            continue
        try:
            chat = load_corpus(eng_na_root, corpus)
        except Exception as e:
            print(f"  [skip] {corpus}: load failed ({type(e).__name__}: {e})")
            continue
        records = build_transcript_index(chat, eng_na_root)
        utts_by_file = chat.utterances(by_file=True)
        for record, utts in zip(records, utts_by_file):
            feats = extract_features(utts, participant="CHI",
                                     min_utterances=min_utts)
            if feats is None:
                continue
            row = {
                "transcript_id": record.transcript_id,
                "corpus": record.corpus,
                "child_id": record.child_id,
                "age_months": record.age_months,
                "n_chi_utterances": record.n_chi_utterances,
                **feats,
            }
            all_features.append(row)
            all_records.append(record)
    feats_df = pd.DataFrame(all_features)
    idx_df = pd.DataFrame([r.__dict__ for r in all_records])
    return feats_df, idx_df


def main() -> None:
    args = parse_args()
    warnings.filterwarnings("ignore")

    print(f"[1/4] Ensuring Eng-NA bundle in {args.data_dir} ...")
    eng_na_root = download_eng_na_bundle(args.data_dir)

    corpora = select_corpora(eng_na_root, args.corpus)
    print(f"[2/4] Parsing + extracting features from {len(corpora)} corpus/corpora "
          f"(this can take a few minutes for large sets) ...")
    feats_df, idx_df = build_feature_table(eng_na_root, corpora, args.min_utterances)

    args.features_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    feats_df.to_parquet(args.features_dir / "phase1_features.parquet", index=False)
    idx_df.to_parquet(args.features_dir / "phase1_transcripts.parquet", index=False)

    n_with_age = int(feats_df["age_months"].notna().sum())
    print(f"  {len(feats_df)} transcripts extracted; {n_with_age} have a target age.")

    train_df = feats_df.dropna(subset=["age_months"]).copy()
    train_df = train_df[train_df["age_months"] <= args.max_age_months]
    train_df = train_df[train_df["age_months"] > 0]
    print(f"  {len(train_df)} transcripts used for training "
          f"(age ∈ (0, {args.max_age_months}] months).")

    if len(train_df) < 20 or train_df["child_id"].nunique() < 3:
        print("[!] Not enough labeled data for cross-validated training. "
              "Add more corpora and rerun.")
        return

    full_features = [c for c in train_df.columns
                     if c not in {"transcript_id", "corpus", "child_id",
                                  "age_months", "n_chi_utterances"}]

    specs = [
        ("mlu_only_ridge", MLU_FEATURES, "ridge"),
        ("kideval_ridge",  KIDEVAL_FEATURES, "ridge"),
        ("ridge_full",     full_features, "ridge"),
        ("gbm_full",       full_features, "gbm"),
    ]

    print(f"[3/4] Training {len(specs)} models with {args.cv_folds}-fold "
          f"GroupKFold over child_id ...")
    summaries = []
    results = {}
    for name, feats, kind in specs:
        result = train_and_evaluate(
            train_df,
            feature_cols=feats,
            target_col="age_months",
            group_col="child_id",
            n_splits=args.cv_folds,
            model_kind=kind,
        )
        result.name = name
        results[name] = result
        summary = summarize(result)
        summary["model"] = name
        summary["n_features"] = len(feats)
        summaries.append(summary)
        print(f"  - {name:20s}  MAE={summary['mae_months']:6.2f}  "
              f"RMSE={summary['rmse_months']:6.2f}  r={summary['pearson_r']:+.3f}")

    metrics_df = pd.DataFrame(summaries)
    metrics_df.to_csv(args.output_dir / "metrics.csv", index=False)

    print("[4/4] Writing plots ...")
    for name, result in results.items():
        title_suffix = f"({name}, {len(result.feature_names)} features)"
        predicted_vs_actual(result, args.output_dir / f"predicted_vs_actual_{name}.png",
                            f"Predicted vs actual age {title_suffix}")
        residuals_by_corpus(result, train_df,
                            args.output_dir / f"residuals_by_corpus_{name}.png",
                            f"Residuals by corpus {title_suffix}")
        feature_importance(result, args.output_dir / f"feature_importance_{name}.png",
                           f"Feature importance {title_suffix}")

    print(f"Done. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
