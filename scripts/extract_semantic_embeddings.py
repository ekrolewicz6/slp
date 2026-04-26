"""Compute semantic embeddings for every windowed AphasiaBank + CHILDES sample.

Strategy:
  1. For each .cha file we already extracted features from, re-load it via
     pylangacq to get the participant's utterances.
  2. Embed each utterance with `all-mpnet-base-v2` (768-dim) using MPS.
  3. For each 100-utt window we previously extracted features for,
     average the per-utterance embeddings → one 768-d vector per window.
  4. Save as a separate parquet aligned by `window_id` so it can be
     joined to the existing feature tables.

Why mean-pool: simple, fast, robust. Variance / attention-pool can come
later. Mean of utterance embeddings approximates the "centroid" of the
patient's productive language for that window in semantic space.
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq as pla
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from src.features.windowed import window_utterances


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--target", choices=["aphasia", "childes"], required=True)
    p.add_argument("--features-path", type=Path)
    p.add_argument("--output-path", type=Path)
    p.add_argument("--participant", default=None,
                   help="PAR for aphasia, CHI for CHILDES (auto if omitted)")
    p.add_argument("--model", default="sentence-transformers/all-mpnet-base-v2")
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--window-size", type=int, default=100)
    p.add_argument("--min-window-utts", type=int, default=50)
    return p.parse_args()


def utt_to_text(u) -> str:
    """Reconstruct the surface form of an utterance from its tokens."""
    out = []
    for t in u.tokens:
        word = (t.word or "").strip()
        if not word or word in {".", "?", "!", ",", ";", ":"}:
            continue
        out.append(word)
    return " ".join(out)


def main() -> None:
    args = parse_args()
    if args.features_path is None:
        args.features_path = Path(
            "data/features/aphasiabank_windowed_features.parquet"
            if args.target == "aphasia"
            else "data/features/phase1_windowed_features.parquet"
        )
    if args.output_path is None:
        args.output_path = Path(
            f"data/features/{args.target}_window_embeddings.parquet")
    if args.participant is None:
        args.participant = "PAR" if args.target == "aphasia" else "CHI"

    print(f"loading {args.features_path}")
    df = pd.read_parquet(args.features_path)
    file_paths = df.drop_duplicates("transcript_id")
    if args.target == "aphasia":
        file_paths = file_paths[["transcript_id", "section", "corpus",
                                  "participant_id", "window_id"]]
    print(f"  {len(df)} windows from {df['transcript_id'].nunique()} files")

    # Map transcript_id → file_path (we kept it in the AphasiaBank parquet
    # via the index file; for CHILDES we infer from data/raw/Eng-NA etc).
    if args.target == "aphasia":
        idx = pd.read_parquet(
            "data/features/aphasiabank_transcripts.parquet")
        path_lookup = idx.drop_duplicates("transcript_id").set_index(
            "transcript_id")["file_path"].to_dict()
    else:
        # CHILDES windowed parquet has transcript_id like "Brown/Adam/020304".
        # Reconstruct path under data/raw/<bundle>/<transcript_id>.cha
        # The bundle column was added in the windowed extraction.
        path_lookup = {}
        for _, r in df.drop_duplicates("transcript_id").iterrows():
            bundle = r["bundle"]
            tid = r["transcript_id"].split("/", 1)[1] if "/" in r["transcript_id"] else r["transcript_id"]
            path_lookup[r["transcript_id"]] = (
                Path("data/raw") / bundle / f"{tid}.cha"
            )

    print(f"loading model {args.model} on MPS")
    model = SentenceTransformer(args.model, device="mps")

    # For each file: load utts, segment into windows, embed each utt,
    # mean-pool per window.
    rows = []
    n_skipped = 0
    grouped = df.groupby("transcript_id")
    for tid, gdf in tqdm(grouped, desc="files"):
        path = path_lookup.get(tid)
        if path is None or not Path(path).exists():
            n_skipped += 1
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                chat = pla.read_chat(str(path), strict=False)
            utts = chat.utterances()
        except Exception:
            n_skipped += 1
            continue

        windows = window_utterances(
            utts, participant=args.participant,
            window_size=args.window_size, min_window_utts=args.min_window_utts,
        )
        if not windows:
            continue

        # Embed all utterances in this file at once for throughput.
        all_texts: list[str] = []
        bounds: list[tuple[int, int]] = []
        cursor = 0
        for w in windows:
            texts = [utt_to_text(u) for u in w]
            texts = [t for t in texts if t]
            bounds.append((cursor, cursor + len(texts)))
            all_texts.extend(texts)
            cursor += len(texts)
        if not all_texts:
            continue
        embs = model.encode(all_texts, batch_size=args.batch_size,
                            convert_to_numpy=True,
                            show_progress_bar=False)

        for w_idx, (lo, hi) in enumerate(bounds):
            if hi <= lo:
                continue
            mean_emb = embs[lo:hi].mean(axis=0)
            window_id = f"{tid}#w{w_idx:02d}"
            row = {"window_id": window_id}
            for j in range(mean_emb.shape[0]):
                row[f"emb{j:03d}"] = float(mean_emb[j])
            rows.append(row)

    print(f"\n{n_skipped} files skipped (path missing or load failed)")
    out = pd.DataFrame(rows)
    print(f"computed embeddings for {len(out)} windows; "
          f"emb dim={out.shape[1]-1}")
    out.to_parquet(args.output_path, index=False)
    print(f"wrote {args.output_path.resolve()}")


if __name__ == "__main__":
    main()
