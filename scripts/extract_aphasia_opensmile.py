"""Stream AphasiaBank media and extract window-level openSMILE features.

This complements `scripts/extract_aphasia_acoustic.py`, which computes a
small custom Praat feature set. Here we use standard openSMILE eGeMAPS or
ComParE functionals so the acoustic claims can be replicated with a feature
set that other speech researchers recognize.

The script preserves the project's storage-light policy: media are streamed
to a temporary WAV, window-level features are saved, and the WAV is deleted
unless `--keep-audio` is set.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import audiofile
import numpy as np
import opensmile
import pandas as pd
import pylangacq as pla
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.windowed import window_utterances
from src.ingestion.talkbank_media import (
    ffmpeg_headers,
    load_dotenv,
    request_headers,
)


FEATURE_SETS = {
    "egemaps": opensmile.FeatureSet.eGeMAPSv02,
    "compare": opensmile.FeatureSet.ComParE_2016,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--features-path",
        default="data/features/aphasiabank_windowed_features.parquet",
        type=Path,
    )
    p.add_argument("--transcripts-path",
                   default="data/features/aphasiabank_transcripts.parquet",
                   type=Path)
    p.add_argument("--audio-tmp", default="data/audio/_opensmile_tmp", type=Path)
    p.add_argument(
        "--output-path",
        default="data/features/aphasia_opensmile_egemaps.parquet",
        type=Path,
    )
    p.add_argument(
        "--summary-path",
        default="outputs/opensmile_aphasia_smoke/summary.md",
        type=Path,
    )
    p.add_argument("--feature-set", choices=sorted(FEATURE_SETS), default="egemaps")
    p.add_argument("--window-size", type=int, default=100)
    p.add_argument("--min-window-utts", type=int, default=50)
    p.add_argument("--limit", type=int, default=0,
                   help="Process only this many sessions (0 = all).")
    p.add_argument("--corpus-filter", default="",
                   help="Comma-separated corpus names to restrict to.")
    p.add_argument("--transcript-list", default="", type=Path,
                   help="Optional CSV with transcript_id column to process.")
    p.add_argument("--keep-audio", action="store_true")
    p.add_argument("--flush-every", type=int, default=30)
    p.add_argument("--max-mp4-mb", type=int, default=400)
    return p.parse_args()


def cha_to_media_url(cha_abs_path: Path) -> str | None:
    parts = cha_abs_path.parts
    try:
        idx = parts.index("aphasiabank")
    except ValueError:
        return None
    rel = parts[idx + 1:]
    rel_url = "/".join(rel).replace(".cha", ".mp4")
    return f"https://media.talkbank.org/aphasia/English/{rel_url}"


def get_remote_size_mb(url: str, headers: dict[str, str]) -> int | None:
    import requests

    headers = {**headers, "Range": "bytes=0-1"}
    try:
        r = requests.head(url, headers=headers, timeout=15, allow_redirects=True)
        cr = r.headers.get("content-range", "")
        if "/" in cr:
            return int(cr.split("/")[-1]) // (1024 * 1024)
        cl = r.headers.get("content-length")
        if cl:
            return int(cl) // (1024 * 1024)
    except Exception:
        pass
    return None


def media_request_returns_html(url: str, headers: dict[str, str]) -> bool:
    import requests

    try:
        r = requests.get(
            url,
            headers={**headers, "Range": "bytes=0-10"},
            timeout=15,
            allow_redirects=True,
            stream=True,
        )
    except Exception:
        return False
    content_type = r.headers.get("content-type", "").lower()
    first = next(r.iter_content(chunk_size=32), b"")
    return "text/html" in content_type or first.lstrip().startswith(b"<html")


def stream_extract_audio(url: str, dest_wav: Path, headers: dict[str, str],
                         timeout_s: int = 300) -> bool:
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


def _slice_signal(signal: np.ndarray, sr: int, start_s: float,
                  end_s: float) -> np.ndarray | None:
    start = max(0, int(round(start_s * sr)))
    end = min(signal.shape[-1], int(round(end_s * sr)))
    if end <= start:
        return None
    return signal[..., start:end]


def _concat_participant_audio(signal: np.ndarray, sr: int,
                              utterances: list) -> tuple[np.ndarray | None, dict]:
    parts = []
    total_utt_s = 0.0
    valid_time_marks = 0
    first_start = None
    last_end = None

    for utt in utterances:
        tm = utt.time_marks
        if tm is None or len(tm) != 2:
            continue
        start_s = tm[0] / 1000.0
        end_s = tm[1] / 1000.0
        if end_s - start_s < 0.2:
            continue
        chunk = _slice_signal(signal, sr, start_s, end_s)
        if chunk is None or chunk.shape[-1] < int(0.2 * sr):
            continue
        parts.append(chunk)
        valid_time_marks += 1
        total_utt_s += end_s - start_s
        first_start = start_s if first_start is None else min(first_start, start_s)
        last_end = end_s if last_end is None else max(last_end, end_s)

    if not parts:
        return None, {
            "os_valid_time_mark_utts": 0,
            "os_total_utt_audio_s": 0.0,
            "os_window_span_s": 0.0,
            "os_speech_coverage": 0.0,
        }

    joined = np.concatenate(parts, axis=-1)
    span = (last_end - first_start) if first_start is not None and last_end else 0.0
    return joined, {
        "os_valid_time_mark_utts": float(valid_time_marks),
        "os_total_utt_audio_s": float(total_utt_s),
        "os_window_span_s": float(span),
        "os_speech_coverage": float(total_utt_s / span) if span > 0 else 0.0,
    }


def session_opensmile_windows(cha_path: Path, audio_path: Path, smile: opensmile.Smile,
                              window_size: int, min_window_utts: int) -> list[dict]:
    chat = pla.read_chat(str(cha_path), strict=False)
    windows = window_utterances(
        chat.utterances(),
        participant="PAR",
        window_size=window_size,
        min_window_utts=min_window_utts,
    )
    if not windows:
        return []

    signal, sr = audiofile.read(str(audio_path), always_2d=False)
    rows = []
    for w_idx, win in enumerate(windows):
        joined, timing = _concat_participant_audio(signal, sr, win)
        if joined is None or joined.shape[-1] < sr:
            continue
        feats = smile.process_signal(joined, sr)
        if feats.empty:
            continue
        row = {f"os_{k}": float(v) for k, v in feats.iloc[0].items()}
        row.update(timing)
        row["window_index"] = w_idx
        rows.append(row)
    return rows


def write_summary(path: Path, df: pd.DataFrame, args: argparse.Namespace,
                  skipped: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# AphasiaBank openSMILE Extraction",
        "",
        f"- Feature set: `{args.feature_set}`",
        f"- Output parquet: `{args.output_path}`",
        f"- Window rows: {len(df):,}",
        f"- Sessions: {df['transcript_id'].nunique() if len(df) else 0:,}",
        f"- Feature columns: {sum(1 for c in df.columns if c.startswith('os_')):,}",
        f"- Limit: {args.limit if args.limit else 'none'}",
        f"- Max MP4 MB: {args.max_mp4_mb}",
        "",
        "## Skips",
        "",
        "| reason | count |",
        "|---|---:|",
    ]
    for key, value in sorted(skipped.items()):
        lines.append(f"| {key} | {value} |")

    if len(df):
        by_corpus = df.groupby("corpus")["transcript_id"].nunique().sort_values(ascending=False)
        lines.extend(["", "## Sessions By Corpus", "", "| corpus | sessions |", "|---|---:|"])
        for corpus, count in by_corpus.items():
            lines.append(f"| {corpus} | {int(count)} |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "Window-level openSMILE features are computed from concatenated participant "
            "utterance audio inside each 100-utterance PAR window. This avoids examiner "
            "speech but does not preserve between-utterance pause durations, so timing "
            "features from transcript time marks remain separate.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


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
        ["transcript_id", "section", "corpus", "participant_id"]
    ]
    if args.transcript_list:
        wanted = pd.read_csv(args.transcript_list)["transcript_id"].astype(str)
        by_session = by_session[by_session["transcript_id"].isin(set(wanted))]
    if args.corpus_filter:
        keep = {c.strip() for c in args.corpus_filter.split(",") if c.strip()}
        by_session = by_session[by_session["corpus"].isin(keep)]

    idx = pd.read_parquet(args.transcripts_path)
    path_lookup = idx.drop_duplicates("transcript_id").set_index("transcript_id")[
        "file_path"
    ].to_dict()

    if args.output_path.exists():
        existing = pd.read_parquet(args.output_path)
        if "transcript_id" in existing.columns:
            already_done = set(existing["transcript_id"].unique())
        else:
            already_done = set()
    else:
        existing = None
        already_done = set()

    work = [r for r in by_session.itertuples(index=False)
            if r.transcript_id not in already_done]
    if args.limit:
        work = work[:args.limit]

    smile = opensmile.Smile(
        feature_set=FEATURE_SETS[args.feature_set],
        feature_level=opensmile.FeatureLevel.Functionals,
    )
    args.audio_tmp.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    skipped: dict[str, int] = {
        "missing_cha": 0,
        "missing_url": 0,
        "auth_or_html_response": 0,
        "too_large": 0,
        "ffmpeg_failure": 0,
        "no_window_features": 0,
        "exception": 0,
    }

    for r in tqdm(work, desc="sessions"):
        tid = r.transcript_id
        cha_path_s = path_lookup.get(tid)
        if cha_path_s is None or not Path(cha_path_s).exists():
            skipped["missing_cha"] += 1
            continue
        cha_path = Path(cha_path_s)
        url = cha_to_media_url(cha_path)
        if url is None:
            skipped["missing_url"] += 1
            continue
        if media_request_returns_html(url, headers):
            skipped["auth_or_html_response"] += 1
            continue
        if args.max_mp4_mb > 0:
            size_mb = get_remote_size_mb(url, headers)
            if size_mb is not None and size_mb > args.max_mp4_mb:
                skipped["too_large"] += 1
                continue

        wav_path = args.audio_tmp / f"{cha_path.stem}.wav"
        ok = stream_extract_audio(url, wav_path, headers)
        if not ok:
            skipped["ffmpeg_failure"] += 1
            wav_path.unlink(missing_ok=True)
            continue

        try:
            session_rows = session_opensmile_windows(
                cha_path,
                wav_path,
                smile,
                args.window_size,
                args.min_window_utts,
            )
        except Exception as e:
            tqdm.write(f"[err] {tid}: {type(e).__name__}: {e}")
            skipped["exception"] += 1
            session_rows = []

        if not session_rows:
            skipped["no_window_features"] += 1

        for srow in session_rows:
            srow["transcript_id"] = tid
            srow["section"] = r.section
            srow["corpus"] = r.corpus
            srow["participant_id"] = r.participant_id
            srow["window_id"] = f"{tid}#w{srow['window_index']:02d}"
            rows.append(srow)

        if not args.keep_audio:
            wav_path.unlink(missing_ok=True)

        if len(rows) >= args.flush_every:
            partial = pd.DataFrame(rows)
            if existing is not None:
                partial = pd.concat([existing, partial], ignore_index=True)
            args.output_path.parent.mkdir(parents=True, exist_ok=True)
            partial.to_parquet(args.output_path, index=False)
            existing = partial
            rows = []

    final = pd.DataFrame(rows)
    if existing is not None:
        final = pd.concat([existing, final], ignore_index=True)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    final.to_parquet(args.output_path, index=False)
    write_summary(args.summary_path, final, args, skipped)
    print(f"wrote {args.output_path} with {len(final)} window rows")
    print(f"wrote {args.summary_path}")


if __name__ == "__main__":
    main()
