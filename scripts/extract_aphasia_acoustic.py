"""Stream AphasiaBank media → extract acoustic features per 100-utt window.

For each session in our existing windowed feature table:
  1. Resolve media URL from the local .cha path.
  2. Stream the .mp4 via ffmpeg with cookie auth, write a temp 16kHz mono WAV.
  3. Load with parselmouth.
  4. Use pylangacq time_marks to slice each PAR utterance.
  5. Compute per-utterance acoustic features.
  6. Aggregate into per-window means/stds matching our existing window_id schema.
  7. Save acoustic feature parquet, delete temp WAV.

Skips sessions where the media is missing, the .cha has no time marks,
or ffmpeg returns errors.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import parselmouth
import pylangacq as pla
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.features.acoustic import (
    aggregate_window_features,
    utterance_features,
)
from src.features.windowed import window_utterances
from src.ingestion.talkbank_media import ffmpeg_headers, load_dotenv, request_headers


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--audio-tmp", default="data/audio/_tmp", type=Path)
    p.add_argument("--output-path",
                   default="data/features/aphasia_acoustic_features.parquet",
                   type=Path)
    p.add_argument("--window-size", type=int, default=100)
    p.add_argument("--min-window-utts", type=int, default=50)
    p.add_argument("--limit", type=int, default=0,
                   help="Process only this many sessions (0 = all).")
    p.add_argument("--corpus-filter", default="",
                   help="Comma-separated corpus names to restrict to.")
    p.add_argument("--keep-audio", action="store_true",
                   help="Don't delete temp WAV after extraction.")
    p.add_argument("--flush-every", type=int, default=30,
                   help="Flush partial parquet to disk every N rows.")
    p.add_argument("--max-mp4-mb", type=int, default=400,
                   help="Skip files larger than this many MB (saves time).")
    return p.parse_args()


def cha_to_media_url(cha_abs_path: Path) -> str | None:
    """Translate a .cha file path under data/raw/aphasiabank/... into the
    corresponding media URL on media.talkbank.org."""
    parts = cha_abs_path.parts
    try:
        idx = parts.index("aphasiabank")
    except ValueError:
        return None
    rel = parts[idx + 1:]  # e.g. ('Protocol', 'CMU', 'PWA', 'cmu03a.cha')
    rel_url = "/".join(rel).replace(".cha", ".mp4")
    return f"https://media.talkbank.org/aphasia/English/{rel_url}"


def get_remote_size_mb(url: str, headers: dict[str, str]) -> int | None:
    """Probe HTTP Content-Range to get total file size in MB."""
    import requests
    headers = {**headers, "Range": "bytes=0-1"}
    try:
        r = requests.head(url, headers=headers, timeout=15,
                          allow_redirects=True)
        cr = r.headers.get("content-range", "")
        if "/" in cr:
            total = int(cr.split("/")[-1])
            return total // (1024 * 1024)
        cl = r.headers.get("content-length")
        if cl:
            return int(cl) // (1024 * 1024)
    except Exception:
        pass
    return None


def stream_extract_audio(url: str, dest_wav: Path,
                         headers: dict[str, str], timeout_s: int = 300) -> bool:
    """Run ffmpeg with HTTP-direct read + cookies → write 16kHz mono WAV.
    Returns True on success."""
    dest_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-headers", ffmpeg_headers(headers),
        "-i", url,
        "-vn", "-ar", "16000", "-ac", "1",
        "-y", str(dest_wav),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout_s)
        if r.returncode != 0:
            return False
        return dest_wav.exists() and dest_wav.stat().st_size > 1024
    except Exception:
        return False


def session_acoustic_windows(cha_path: Path, audio_path: Path,
                              window_size: int, min_window_utts: int) -> list[dict]:
    """For one session, return one acoustic-feature dict per window."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        chat = pla.read_chat(str(cha_path), strict=False)
    utts = chat.utterances()

    windows = window_utterances(utts, participant="PAR",
                                 window_size=window_size,
                                 min_window_utts=min_window_utts)
    if not windows:
        return []

    try:
        sound = parselmouth.Sound(str(audio_path))
    except Exception:
        return []

    rows = []
    for w_idx, win in enumerate(windows):
        per_utt = []
        for u in win:
            tm = u.time_marks
            if tm is None or len(tm) != 2:
                continue
            start_s, end_s = tm[0] / 1000.0, tm[1] / 1000.0
            if end_s - start_s < 0.2:
                continue
            try:
                sub = sound.extract_part(from_time=start_s, to_time=end_s,
                                          preserve_times=False)
            except Exception:
                continue
            n_tok = sum(1 for t in u.tokens if (t.word or "").strip()
                        and t.word not in {".", "?", "!", ",", ";", ":"})
            try:
                feats = utterance_features(sub, n_tokens=n_tok)
            except Exception:
                continue
            per_utt.append(feats)

        if not per_utt:
            continue
        agg = aggregate_window_features(per_utt)
        agg["window_index"] = w_idx
        rows.append(agg)
    return rows


def main() -> None:
    args = parse_args()
    load_dotenv()
    headers, _, _ = request_headers(range_value=None)
    if "Cookie" not in headers:
        print("[!] Set TALKBANK_COOKIE_HEADER or APHASIABANK_COOKIE in .env",
              file=sys.stderr)
        sys.exit(1)

    feats = pd.read_parquet(args.features_path)
    by_session = feats.drop_duplicates("transcript_id")[
        ["transcript_id", "section", "corpus", "participant_id"]]
    print(f"sessions in features parquet: {len(by_session)}")

    if args.corpus_filter:
        keep = {c.strip() for c in args.corpus_filter.split(",")}
        by_session = by_session[by_session["corpus"].isin(keep)]
        print(f"  filtered to corpora {sorted(keep)}: {len(by_session)} sessions")

    idx = pd.read_parquet(
        "data/features/aphasiabank_transcripts.parquet")
    path_lookup = idx.drop_duplicates("transcript_id").set_index(
        "transcript_id")["file_path"].to_dict()

    rows: list[dict] = []
    if args.output_path.exists():
        existing = pd.read_parquet(args.output_path)
        already_done = set(existing["transcript_id"].unique())
        print(f"  loaded {len(existing)} existing rows from "
              f"{len(already_done)} sessions; will skip those")
    else:
        existing = None
        already_done = set()

    work = [r for r in by_session.itertuples(index=False)
            if r.transcript_id not in already_done]
    if args.limit:
        work = work[:args.limit]
    print(f"  processing {len(work)} new sessions")

    args.audio_tmp.mkdir(parents=True, exist_ok=True)

    for r in tqdm(work, desc="sessions"):
        tid = r.transcript_id
        cha_path = path_lookup.get(tid)
        if cha_path is None or not Path(cha_path).exists():
            continue
        url = cha_to_media_url(Path(cha_path))
        if url is None:
            continue

        # Skip files larger than the threshold to keep moving
        if args.max_mp4_mb > 0:
            size_mb = get_remote_size_mb(url, headers)
            if size_mb is not None and size_mb > args.max_mp4_mb:
                tqdm.write(f"[skip] {tid}: too big ({size_mb} MB > "
                           f"{args.max_mp4_mb} MB)")
                continue

        wav_path = args.audio_tmp / f"{Path(cha_path).stem}.wav"
        ok = stream_extract_audio(url, wav_path, headers)
        if not ok:
            tqdm.write(f"[skip] {tid}: ffmpeg failure")
            wav_path.unlink(missing_ok=True)
            continue

        try:
            session_rows = session_acoustic_windows(
                Path(cha_path), wav_path,
                args.window_size, args.min_window_utts)
        except Exception as e:
            tqdm.write(f"[err]  {tid}: {type(e).__name__}: {e}")
            session_rows = []

        for srow in session_rows:
            srow["transcript_id"] = tid
            srow["section"] = r.section
            srow["corpus"] = r.corpus
            srow["participant_id"] = r.participant_id
            srow["window_id"] = f"{tid}#w{srow['window_index']:02d}"
            rows.append(srow)

        if not args.keep_audio:
            wav_path.unlink(missing_ok=True)

        # Periodic flush to disk so we don't lose work on interrupt.
        if len(rows) >= args.flush_every:
            partial = pd.DataFrame(rows)
            if existing is not None:
                partial = pd.concat([existing, partial], ignore_index=True)
            partial.to_parquet(args.output_path, index=False)
            existing = partial
            rows = []

    final = pd.DataFrame(rows)
    if existing is not None:
        final = pd.concat([existing, final], ignore_index=True)
    final.to_parquet(args.output_path, index=False)
    print(f"\nwrote {args.output_path} with "
          f"{len(final)} window rows from "
          f"{final['transcript_id'].nunique()} sessions")


if __name__ == "__main__":
    main()
