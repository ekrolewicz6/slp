"""Stream AphasiaBank media → foundation-model embedding per 100-utt window.

Leap 1 at corpus scale (STRATEGY.md §2). Mirrors
`extract_aphasia_acoustic.py` exactly — same streaming, same windowing,
same `window_id` schema — but replaces parselmouth summary statistics
with a self-supervised speech embedding (`src/features/foundation_rep.py`).
The output parquet (window_id → emb_000…emb_NNN) drops straight into
`benchmark_representations.py`.

Per session:
  1. Resolve media URL from the local .cha path.
  2. Stream the .mp4 via ffmpeg + cookie → temp 16 kHz mono WAV.
  3. Build the same 100-PAR-utterance windows we already use.
  4. For each window, concatenate its utterances' audio and embed.
  5. Write one row per window; delete the temp WAV.

Resumable: skips sessions already present in the output parquet.

Run:  .venv/bin/python -m scripts.extract_foundation_embeddings --limit 20
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq as pla
import soundfile as sf
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extract_aphasia_acoustic import (cha_to_media_url,
                                              get_remote_size_mb,
                                              stream_extract_audio)
from src.features.foundation_rep import EmbedderConfig, FoundationEmbedder
from src.features.windowed import window_utterances
from src.ingestion.talkbank_media import load_dotenv, request_headers

TARGET_SR = 16000


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-path",
                   default="data/features/aphasia_foundation_embeddings.parquet",
                   type=Path)
    p.add_argument("--audio-tmp", default="data/audio/fnd", type=Path)
    p.add_argument("--model-name", default="facebook/wav2vec2-base")
    p.add_argument("--layer", type=int, default=8)
    p.add_argument("--window-size", type=int, default=100)
    p.add_argument("--min-window-utts", type=int, default=50)
    p.add_argument("--max-mp4-mb", type=int, default=250)
    p.add_argument("--corpus-filter", default="")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--flush-every", type=int, default=200)
    return p.parse_args()


def session_window_embeddings(cha_path: Path, wav_path: Path,
                              embedder: FoundationEmbedder,
                              window_size: int, min_window_utts: int) -> list[dict]:
    """One pooled foundation embedding per window for a session."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        chat = pla.read_chat(str(cha_path), strict=False)
    windows = window_utterances(chat.utterances(), participant="PAR",
                                window_size=window_size,
                                min_window_utts=min_window_utts)
    if not windows:
        return []
    try:
        wav, sr = sf.read(str(wav_path))
    except Exception:
        return []
    if wav.ndim > 1:
        wav = wav.mean(axis=1)

    rows = []
    for w_idx, win in enumerate(windows):
        segs = []
        for u in win:
            tm = u.time_marks
            if tm is None or len(tm) != 2:
                continue
            a, b = int(tm[0] / 1000.0 * sr), int(tm[1] / 1000.0 * sr)
            if b - a < sr // 5:        # < 0.2 s
                continue
            segs.append(wav[max(0, a):min(len(wav), b)])
        if not segs:
            continue
        clip = np.concatenate(segs).astype(np.float32)
        vec = embedder.embed_segment(clip, sr)
        row = {f"emb_{i:04d}": float(v) for i, v in enumerate(vec)}
        row["window_index"] = w_idx
        rows.append(row)
    return rows


def main() -> None:
    args = parse_args()
    load_dotenv()
    headers, _, _ = request_headers(range_value=None)
    if "Cookie" not in headers:
        print("[!] Set APHASIABANK_COOKIE in .env", file=sys.stderr)
        sys.exit(1)

    feats = pd.read_parquet(args.features_path)
    by_session = feats.drop_duplicates("transcript_id")[
        ["transcript_id", "section", "corpus", "participant_id"]]
    if args.corpus_filter:
        keep = {c.strip() for c in args.corpus_filter.split(",")}
        by_session = by_session[by_session["corpus"].isin(keep)]

    idx = pd.read_parquet("data/features/aphasiabank_transcripts.parquet")
    path_lookup = idx.drop_duplicates("transcript_id").set_index(
        "transcript_id")["file_path"].to_dict()

    if args.output_path.exists():
        existing = pd.read_parquet(args.output_path)
        already = set(existing["transcript_id"].unique())
        print(f"resuming: {len(existing)} rows from {len(already)} sessions")
    else:
        existing, already = None, set()

    work = [r for r in by_session.itertuples(index=False)
            if r.transcript_id not in already]
    if args.limit:
        work = work[:args.limit]
    print(f"sessions to process: {len(work)}  model={args.model_name} layer={args.layer}")

    embedder = FoundationEmbedder(EmbedderConfig(
        model_name=args.model_name, layer=args.layer))
    args.audio_tmp.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for r in tqdm(work, desc="sessions"):
        tid = r.transcript_id
        cha_path = path_lookup.get(tid)
        if cha_path is None or not Path(cha_path).exists():
            continue
        url = cha_to_media_url(Path(cha_path))
        if url is None:
            continue
        if args.max_mp4_mb > 0:
            size_mb = get_remote_size_mb(url, headers)
            if size_mb is not None and size_mb > args.max_mp4_mb:
                tqdm.write(f"[skip] {tid}: {size_mb} MB > {args.max_mp4_mb}")
                continue
        wav_path = args.audio_tmp / f"{Path(cha_path).stem}.wav"
        if not stream_extract_audio(url, wav_path, headers):
            wav_path.unlink(missing_ok=True)
            continue
        try:
            srows = session_window_embeddings(
                Path(cha_path), wav_path, embedder,
                args.window_size, args.min_window_utts)
        except Exception as e:
            tqdm.write(f"[err] {tid}: {type(e).__name__}: {e}")
            srows = []
        for s in srows:
            s.update({"transcript_id": tid, "section": r.section,
                      "corpus": r.corpus, "participant_id": r.participant_id,
                      "window_id": f"{tid}#w{s['window_index']:02d}"})
            rows.append(s)
        wav_path.unlink(missing_ok=True)

        if len(rows) >= args.flush_every:
            part = pd.DataFrame(rows)
            if existing is not None:
                part = pd.concat([existing, part], ignore_index=True)
            part.to_parquet(args.output_path, index=False)
            existing, rows = part, []

    final = pd.DataFrame(rows)
    if existing is not None:
        final = pd.concat([existing, final], ignore_index=True)
    if len(final):
        final.to_parquet(args.output_path, index=False)
    print(f"done: {len(final)} window embeddings → {args.output_path}")


if __name__ == "__main__":
    main()
