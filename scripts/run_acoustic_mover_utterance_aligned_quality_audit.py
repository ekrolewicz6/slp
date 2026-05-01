"""Audit acoustic-only stable-WAB movers on PAR utterance-aligned audio spans."""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq as pla
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from scripts.extract_aphasia_acoustic import cha_to_media_url, get_remote_size_mb  # noqa: E402
from scripts.run_acoustic_mover_media_quality_audit import (  # noqa: E402
    audio_quality_metrics,
    resolve_transcript_path,
    to_float_audio,
)
from src.analysis.review_grade import ensure_dir  # noqa: E402
from src.ingestion.talkbank_media import ffmpeg_headers, load_dotenv, request_headers  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--audit",
        default="outputs/acoustic_mover_artifact_audit/acoustic_only_artifact_audit.csv",
        type=Path,
    )
    p.add_argument(
        "--classified-pairs",
        default="outputs/stable_wab_movers/classified_pairs.csv",
        type=Path,
    )
    p.add_argument(
        "--transcript-index",
        default="data/features/aphasiabank_transcripts.parquet",
        type=Path,
    )
    p.add_argument("--audio-tmp", default="data/audio/_utterance_quality_tmp", type=Path)
    p.add_argument("--output-dir", default="outputs/acoustic_mover_utterance_quality_audit", type=Path)
    p.add_argument("--max-mp4-mb", type=int, default=450)
    p.add_argument("--span-pad-seconds", type=float, default=2.0)
    p.add_argument("--max-span-seconds", type=float, default=900.0)
    p.add_argument("--ffmpeg-timeout", type=int, default=180)
    p.add_argument("--keep-audio", action="store_true")
    return p.parse_args()


def par_time_marks(cha_path: Path) -> list[tuple[float, float]]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        chat = pla.read_chat(str(cha_path), strict=False)
    marks: list[tuple[float, float]] = []
    for utt in chat.utterances():
        if getattr(utt, "participant", "") != "PAR":
            continue
        tm = getattr(utt, "time_marks", None)
        if tm is None or len(tm) != 2:
            continue
        start, end = tm[0] / 1000.0, tm[1] / 1000.0
        if end - start >= 0.15:
            marks.append((start, end))
    return marks


def stream_extract_span(
    url: str,
    dest_wav: Path,
    headers: dict[str, str],
    start_s: float,
    duration_s: float,
    timeout_s: int,
) -> bool:
    dest_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start_s:.3f}",
        "-headers",
        ffmpeg_headers(headers),
        "-i",
        url,
        "-t",
        f"{duration_s:.3f}",
        "-vn",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-y",
        str(dest_wav),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout_s)
        if result.returncode != 0:
            return False
        return dest_wav.exists() and dest_wav.stat().st_size > 1024
    except Exception:
        return False


def metrics_from_audio(audio: np.ndarray, sr: int) -> dict[str, float]:
    tmp = Path("__unused__")
    # Inline the same computation as audio_quality_metrics without writing a file.
    if len(audio) == 0:
        return {"quality_read_ok": 0.0, "duration_s": 0.0}
    abs_audio = np.abs(audio)
    rms = float(np.sqrt(np.mean(audio * audio)))
    peak = float(abs_audio.max())
    frame = max(1, int(sr * 0.020))
    n = len(audio) // frame
    if n > 0:
        framed = audio[: n * frame].reshape(n, frame)
        frame_rms = np.sqrt(np.mean(framed * framed, axis=1))
        frame_db = 20 * np.log10(np.maximum(frame_rms, 1e-9))
        p95 = float(np.percentile(frame_db, 95))
        p10 = float(np.percentile(frame_db, 10))
        silence_fraction = float(np.mean(frame_db < -45.0))
        active = frame_db[frame_db > -45.0]
    else:
        p95 = p10 = -90.0
        silence_fraction = 1.0
        active = np.array([], dtype=float)
    if len(active):
        active_rms_db = float(20 * math.log10(max(float(np.sqrt(np.mean(10 ** (active / 10)))), 1e-9)))
    else:
        active_rms_db = -90.0
    return {
        "quality_read_ok": 1.0,
        "sample_rate": float(sr),
        "duration_s": float(len(audio) / sr),
        "rms_dbfs": float(20 * math.log10(max(rms, 1e-9))),
        "active_rms_dbfs": active_rms_db,
        "peak_dbfs": float(20 * math.log10(max(peak, 1e-9))),
        "clipping_fraction": float(np.mean(abs_audio >= 0.99)),
        "near_zero_fraction": float(np.mean(abs_audio < 1e-4)),
        "silence_fraction": silence_fraction,
        "frame_p95_dbfs": p95,
        "frame_p10_dbfs": p10,
        "snr_proxy_db": p95 - p10,
        "dc_offset": float(np.mean(audio)),
    }


def par_audio_metrics(wav_path: Path, marks: list[tuple[float, float]], span_start_s: float) -> dict[str, float]:
    sr, samples = wavfile.read(wav_path)
    audio = to_float_audio(samples)
    chunks = []
    total_s = 0.0
    for start_s, end_s in marks:
        rel_start = max(0.0, start_s - span_start_s)
        rel_end = min(float(len(audio) / sr), end_s - span_start_s)
        if rel_end <= rel_start:
            continue
        lo = int(rel_start * sr)
        hi = int(rel_end * sr)
        if hi > lo:
            chunks.append(audio[lo:hi])
            total_s += (hi - lo) / sr
    if chunks:
        par_audio = np.concatenate(chunks)
    else:
        par_audio = np.array([], dtype=np.float32)
    metrics = metrics_from_audio(par_audio, sr)
    metrics["par_utterance_count"] = float(len(chunks))
    metrics["par_total_s"] = float(total_s)
    return metrics


def session_status_row(
    tid: str,
    cha_path_raw: str | None,
    headers: dict[str, str],
    args: argparse.Namespace,
) -> dict[str, float | str]:
    row: dict[str, float | str] = {"transcript_id": tid, "status": "missing_transcript_path"}
    if not cha_path_raw:
        return row
    cha_path = Path(cha_path_raw)
    marks = par_time_marks(cha_path)
    row["par_utterance_count"] = float(len(marks))
    if not marks:
        row["status"] = "missing_par_time_marks"
        return row
    first_s = min(s for s, _ in marks)
    last_s = max(e for _, e in marks)
    span_start = max(0.0, first_s - args.span_pad_seconds)
    span_end = last_s + args.span_pad_seconds
    row["transcript_span_s"] = span_end - span_start
    row["span_start_s"] = span_start
    if span_end - span_start > args.max_span_seconds:
        row["status"] = "span_too_long"
        return row

    url = cha_to_media_url(cha_path)
    if not url:
        row["status"] = "missing_media_url"
        return row
    size_mb = get_remote_size_mb(url, headers)
    row["remote_size_mb"] = float(size_mb) if size_mb is not None else np.nan
    if size_mb is not None and size_mb > args.max_mp4_mb:
        row["status"] = "skipped_oversize"
        return row

    wav_path = args.audio_tmp / f"{cha_path.stem}.wav"
    ok = stream_extract_span(url, wav_path, headers, span_start, span_end - span_start, args.ffmpeg_timeout)
    if not ok:
        row["status"] = "ffmpeg_failed"
        return row
    try:
        full = audio_quality_metrics(wav_path)
        par = par_audio_metrics(wav_path, marks, span_start)
        row.update({f"span_{k}": v for k, v in full.items()})
        row.update({f"par_{k}": v for k, v in par.items()})
        row["status"] = "ok"
    finally:
        if not args.keep_audio:
            wav_path.unlink(missing_ok=True)
    return row


def pair_flags(row: pd.Series) -> tuple[str, str, int]:
    flags: list[str] = []
    for side in ("from", "to"):
        if row.get(f"{side}_status") != "ok":
            flags.append(f"{side}_stream_not_ok")
        if row.get(f"{side}_par_duration_s", 0.0) < 5:
            flags.append(f"{side}_low_par_audio")
        if row.get(f"{side}_par_clipping_fraction", 0.0) > 0.005:
            flags.append(f"{side}_par_clipping")
        if row.get(f"{side}_par_snr_proxy_db", 0.0) < 12:
            flags.append(f"{side}_par_low_dynamic_range")
        if row.get(f"{side}_par_silence_fraction", 0.0) > 0.70:
            flags.append(f"{side}_par_mostly_silence")
    if abs(row.get("delta_par_rms_dbfs", 0.0)) > 10:
        flags.append("large_par_rms_shift")
    if abs(row.get("delta_par_silence_fraction", 0.0)) > 0.30:
        flags.append("large_par_silence_shift")
    if abs(row.get("delta_par_snr_proxy_db", 0.0)) > 15:
        flags.append("large_par_dynamic_range_shift")

    score = 0
    for flag in flags:
        if "stream_not_ok" in flag or "low_par_audio" in flag:
            score += 2
        elif flag.startswith("large_"):
            score += 2
        else:
            score += 1
    if score >= 4:
        risk = "high_utterance_artifact_risk"
    elif score >= 2:
        risk = "medium_utterance_artifact_risk"
    else:
        risk = "low_utterance_artifact_risk"
    return risk, ",".join(flags), score


def main() -> None:
    args = parse_args()
    load_dotenv()
    headers, _, _ = request_headers(range_value=None)
    if "Cookie" not in headers:
        raise SystemExit("Missing TALKBANK_COOKIE_HEADER or APHASIABANK_COOKIE in .env")

    out_dir = ensure_dir(args.output_dir)
    args.audio_tmp.mkdir(parents=True, exist_ok=True)
    audit = pd.read_csv(args.audit)
    classified = pd.read_csv(args.classified_pairs)
    idx = pd.read_parquet(args.transcript_index)
    path_lookup = idx.drop_duplicates("transcript_id").set_index("transcript_id")["file_path"].to_dict()

    keys = ["longitudinal_root", "from_participant_id", "to_participant_id"]
    rows = audit.merge(
        classified[keys + ["from_meta_transcript_id", "to_meta_transcript_id"]],
        on=keys,
        how="left",
    )
    tids = sorted(set(rows["from_meta_transcript_id"]).union(rows["to_meta_transcript_id"]))
    session_metrics: dict[str, dict[str, float | str]] = {}
    for i, tid in enumerate(tids, start=1):
        print(f"[{i}/{len(tids)}] utterance span {tid}", flush=True)
        cha_path_raw = resolve_transcript_path(str(tid), path_lookup)
        session_metrics[tid] = session_status_row(str(tid), cha_path_raw, headers, args)

    metric_cols = [
        "remote_size_mb",
        "transcript_span_s",
        "span_start_s",
        "par_utterance_count",
        "par_duration_s",
        "par_rms_dbfs",
        "par_active_rms_dbfs",
        "par_peak_dbfs",
        "par_clipping_fraction",
        "par_silence_fraction",
        "par_snr_proxy_db",
        "span_silence_fraction",
        "span_snr_proxy_db",
    ]
    pair_rows = []
    for _, row in rows.iterrows():
        from_m = session_metrics.get(row["from_meta_transcript_id"], {})
        to_m = session_metrics.get(row["to_meta_transcript_id"], {})
        out = row.to_dict()
        out["from_status"] = from_m.get("status", "missing")
        out["to_status"] = to_m.get("status", "missing")
        for col in metric_cols:
            out[f"from_{col}"] = from_m.get(col, np.nan)
            out[f"to_{col}"] = to_m.get(col, np.nan)
            try:
                out[f"delta_{col}"] = float(to_m.get(col, np.nan)) - float(from_m.get(col, np.nan))
            except Exception:
                out[f"delta_{col}"] = np.nan
        risk, flags, score = pair_flags(pd.Series(out))
        out["utterance_artifact_risk"] = risk
        out["utterance_artifact_flags"] = flags
        out["utterance_artifact_score"] = score
        pair_rows.append(out)

    session_df = pd.DataFrame(session_metrics.values())
    pair_df = pd.DataFrame(pair_rows)
    risk_summary = (
        pair_df.groupby(["audit_label", "utterance_artifact_risk"])
        .size()
        .reset_index(name="n")
        .sort_values(["audit_label", "utterance_artifact_risk"])
    )
    session_df.to_csv(out_dir / "session_utterance_quality_metrics.csv", index=False)
    pair_df.to_csv(out_dir / "pair_utterance_quality_audit.csv", index=False)
    risk_summary.to_csv(out_dir / "risk_summary.csv", index=False)

    compact_cols = [
        "longitudinal_root",
        "from_participant_id",
        "to_participant_id",
        "subtype",
        "audit_label",
        "utterance_artifact_risk",
        "utterance_artifact_flags",
        "delta_par_rms_dbfs",
        "delta_par_silence_fraction",
        "delta_par_snr_proxy_db",
        "from_par_duration_s",
        "to_par_duration_s",
        "from_status",
        "to_status",
    ]
    lines = [
        "# Acoustic Mover Utterance-Aligned Quality Audit",
        "",
        f"- Acoustic-only stable-WAB pairs audited: {len(pair_df):,}",
        f"- Sessions streamed: {len(session_df):,}",
        "",
        "## Risk Summary",
        "",
        md_table(risk_summary),
        "",
        "## Pair-Level Utterance-Aligned Audit",
        "",
        md_table(pair_df[compact_cols].round(3)),
        "",
        "## Interpretation",
        "",
        "This rerun uses transcript PAR time marks rather than the leading media clip. It is a stronger technical screen for the acoustic-only mover claim, but it still does not replace manual clinical audio review.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
