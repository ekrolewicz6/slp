"""Windowed feature extraction over all AphasiaBank corpora.

Mirrors `run_phase1_windowed.py` but for the PAR participant in each
session, with WAB-AQ + subtype + demographics joined inline from the
`@ID` headers.

Output:
    data/features/aphasiabank_windowed_features.parquet  — one row per window
    data/features/aphasiabank_transcripts.parquet        — one row per session
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import pandas as pd
from tqdm import tqdm

import pylangacq as pla

from src.features.windowed import extract_windowed_features
from src.ingestion.aphasiabank import index_aphasiabank


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data/raw/aphasiabank", type=Path)
    p.add_argument("--features-dir", default="data/features", type=Path)
    p.add_argument("--window-size", type=int, default=100)
    p.add_argument("--min-window-utts", type=int, default=50)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.features_dir.mkdir(parents=True, exist_ok=True)
    warnings.filterwarnings("ignore")

    print(f"[1/3] Indexing AphasiaBank under {args.data_dir} ...")
    records = index_aphasiabank(args.data_dir)
    idx_df = pd.DataFrame([r.__dict__ for r in records])
    print(f"  {len(idx_df)} PAR records across "
          f"{idx_df['section'].nunique()} sections, "
          f"{idx_df['corpus'].nunique()} corpora.")
    if "wab_aq" in idx_df.columns:
        print(f"  WAB-AQ inline coverage: "
              f"{int(idx_df['wab_aq'].notna().sum())}/{len(idx_df)} sessions "
              f"({idx_df['wab_aq'].notna().mean():.1%})")
        print(f"  Subtype inline coverage: "
              f"{int(idx_df['subtype'].notna().sum())}/{len(idx_df)} sessions "
              f"({idx_df['subtype'].notna().mean():.1%})")

    idx_df.to_parquet(args.features_dir / "aphasiabank_transcripts.parquet",
                      index=False)

    print(f"\n[2/3] Extracting features in {args.window_size}-utt windows "
          f"(min {args.min_window_utts}) ...")
    rows = []
    by_file = idx_df.drop_duplicates("file_path")[["file_path", "transcript_id",
                                                    "section", "corpus",
                                                    "participant_id", "age_years",
                                                    "sex", "subtype", "wab_aq",
                                                    "is_control", "session_date"]]
    for fpath, group in tqdm(by_file.groupby("file_path"), desc=".cha files"):
        meta = group.iloc[0].to_dict()
        try:
            chat = pla.read_chat(fpath, strict=False)
            utts = chat.utterances()
        except Exception as e:
            continue
        window_rows = extract_windowed_features(
            utts, participant="PAR",
            window_size=args.window_size, min_window_utts=args.min_window_utts,
        )
        for w in window_rows:
            rows.append({
                "transcript_id": meta["transcript_id"],
                "section": meta["section"],
                "corpus": meta["corpus"],
                "participant_id": meta["participant_id"],
                "age_years": meta["age_years"],
                "sex": meta["sex"],
                "subtype": meta["subtype"],
                "wab_aq": meta["wab_aq"],
                "is_control": meta["is_control"],
                "session_date": meta["session_date"],
                "window_id": f"{meta['transcript_id']}#w{w['window_index']:02d}",
                **w,
            })

    feat_df = pd.DataFrame(rows)
    print(f"  {len(feat_df)} windows from {feat_df['transcript_id'].nunique()} sessions "
          f"across {feat_df['participant_id'].nunique()} participants, "
          f"{feat_df['corpus'].nunique()} corpora.")

    feat_df.to_parquet(args.features_dir / "aphasiabank_windowed_features.parquet",
                       index=False)

    print("\n[3/3] Sanity summary ...")
    if "wab_aq" in feat_df.columns:
        n_with_aq = feat_df["wab_aq"].notna().sum()
        n_with_subtype = feat_df["subtype"].notna().sum()
        print(f"  Windows with WAB-AQ:  {n_with_aq:>6} ({n_with_aq/len(feat_df):.1%})")
        print(f"  Windows with subtype: {n_with_subtype:>6} ({n_with_subtype/len(feat_df):.1%})")
        print(f"  WAB-AQ distribution: min {feat_df['wab_aq'].min():.1f} "
              f"max {feat_df['wab_aq'].max():.1f} "
              f"mean {feat_df['wab_aq'].mean():.1f}")
        print(f"\n  Subtype distribution:")
        for sub, n in feat_df["subtype"].value_counts(dropna=False).head(15).items():
            print(f"    {str(sub):20s} {n:>5}")
    print(f"\nDone. Outputs in {args.features_dir.resolve()}")


if __name__ == "__main__":
    main()
