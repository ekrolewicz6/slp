"""Re-run Phase 1 with 100-utterance windowing instead of file-level aggregation.

Each transcript yields one row per non-overlapping 100-CHI-utt window with
≥50 utterances. All feature extractors apply unchanged.

Open question this answers: does fine-grained temporal resolution help age
prediction (more rows + less per-row noise variance) or hurt it (within-
session variation diluting the developmental signal)?
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from src.evaluation.metrics import summarize
from src.features.windowed import extract_windowed_features
from src.ingestion.childes import (
    build_transcript_index,
    download_eng_na_bundle,
    download_english_bundles,
    load_corpus,
)
from src.models.phase1_age.train import (
    KIDEVAL_FEATURES,
    MLU_FEATURES,
    train_and_evaluate,
)


META_COLS = {"transcript_id", "corpus", "child_id", "age_months",
             "n_chi_utterances", "window_id", "window_index",
             "n_chi_utts_in_window", "bundle"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data/raw", type=Path)
    p.add_argument("--features-dir", default="data/features", type=Path)
    p.add_argument("--output-dir", default="outputs/phase1_windowed", type=Path)
    p.add_argument("--bundles", default="all",
                   help="Comma-separated bundle names (Eng-NA,Eng-UK,Clinical-Eng) or 'all'.")
    p.add_argument("--corpus", default="all",
                   help="Comma-separated corpus names within selected bundles, or 'all'.")
    p.add_argument("--window-size", type=int, default=100)
    p.add_argument("--min-window-utts", type=int, default=50)
    p.add_argument("--max-age-months", type=float, default=84.0)
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


def select_corpora_in(root: Path, request: str) -> list[str]:
    if request == "all":
        return sorted([d.name for d in root.iterdir()
                       if d.is_dir() and not d.name.startswith(".")])
    return [c.strip() for c in request.split(",") if c.strip()]


def build_window_table(bundle_roots: dict[str, Path], corpus_request: str,
                       window_size: int, min_window_utts: int) -> pd.DataFrame:
    rows = []
    for bundle_name, root in bundle_roots.items():
        corpora = select_corpora_in(root, corpus_request)
        for corpus in tqdm(corpora, desc=f"{bundle_name} corpora"):
            corpus_path = root / corpus
            if not corpus_path.exists():
                continue
            try:
                chat = load_corpus(root, corpus)
            except Exception as e:
                print(f"  [skip] {bundle_name}/{corpus}: {type(e).__name__}: {e}")
                continue
            records = build_transcript_index(chat, root)
            utts_by_file = chat.utterances(by_file=True)
            for record, utts in zip(records, utts_by_file):
                window_rows = extract_windowed_features(
                    utts, participant="CHI",
                    window_size=window_size, min_window_utts=min_window_utts,
                )
                for w in window_rows:
                    rows.append({
                        "transcript_id": f"{bundle_name}/{record.transcript_id}",
                        "corpus": record.corpus,
                        "bundle": bundle_name,
                        "child_id": f"{bundle_name}/{record.corpus}/{record.child_id}",
                        "age_months": record.age_months,
                        "window_id": f"{bundle_name}/{record.transcript_id}#w{w['window_index']:02d}",
                        **w,
                    })
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    warnings.filterwarnings("ignore")
    args.features_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("[1/4] Locating bundles ...")
    all_roots = download_english_bundles(args.data_dir)
    if args.bundles == "all":
        bundle_roots = all_roots
    else:
        keep = {b.strip() for b in args.bundles.split(",")}
        bundle_roots = {k: v for k, v in all_roots.items() if k in keep}
    print(f"  using bundles: {list(bundle_roots.keys())}")

    print(f"[2/4] Re-extracting features in {args.window_size}-utt windows "
          f"(min {args.min_window_utts}) ...")
    df = build_window_table(bundle_roots, args.corpus, args.window_size,
                            args.min_window_utts)
    print(f"  {len(df)} windows from {df['transcript_id'].nunique()} transcripts "
          f"({df['child_id'].nunique()} children, {df['corpus'].nunique()} corpora, "
          f"{df['bundle'].nunique()} bundles)")
    df.to_parquet(args.features_dir / "phase1_windowed_features.parquet",
                  index=False)

    train_df = df.dropna(subset=["age_months"]).copy()
    train_df = train_df[(train_df.age_months > 0)
                        & (train_df.age_months <= args.max_age_months)]

    feature_cols = [c for c in train_df.columns if c not in META_COLS]
    print(f"  {len(train_df)} windowed rows used for training, "
          f"{len(feature_cols)} features.")

    specs = [
        ("mlu_only_ridge", MLU_FEATURES, "ridge"),
        ("kideval_ridge",  KIDEVAL_FEATURES, "ridge"),
        ("ridge_full",     feature_cols, "ridge"),
        ("gbm_full",       feature_cols, "gbm"),
    ]

    print(f"[3/4] Training {len(specs)} models with child-grouped {args.cv_folds}-fold CV ...")
    summaries = []
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
        s = summarize(result)
        s["model"] = name
        s["n_features"] = len(feats)
        summaries.append(s)
        print(f"  - {name:20s}  MAE={s['mae_months']:6.2f}  "
              f"RMSE={s['rmse_months']:6.2f}  r={s['pearson_r']:+.3f}")

    metrics_df = pd.DataFrame(summaries)
    metrics_df.to_csv(args.output_dir / "metrics.csv", index=False)
    print("\n[4/4] Comparison vs file-level (Phase 1):")
    print(f"  file-level GBM(55) MAE      = 8.98")
    print(f"  windowed   GBM(55) MAE      = {metrics_df.loc[metrics_df.model=='gbm_full','mae_months'].iloc[0]:.2f}")
    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
