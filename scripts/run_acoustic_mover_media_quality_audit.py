"""Stream acoustic-only stable-WAB movers and audit recording-level quality.

This does not judge clinical change. It asks whether the acoustic-only mover
signal is technically plausible or likely explained by recording artifacts.
Temporary WAV files are deleted after each session unless --keep-audio is set.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from scripts.extract_aphasia_acoustic import (  # noqa: E402
    cha_to_media_url,
    get_remote_size_mb,
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
    p.add_argument("--audio-tmp", default="data/audio/_media_quality_tmp", type=Path)
    p.add_argument("--output-dir", default="outputs/acoustic_mover_media_quality_audit", type=Path)
    p.add_argument("--max-mp4-mb", type=int, default=450)
    p.add_argument(
        "--clip-seconds",
        type=int,
        default=180,
        help="Extract only the first N seconds for a bounded technical-quality audit.",
    )
    p.add_argument("--ffmpeg-timeout", type=int, default=120)
    p.add_argument("--keep-audio", action="store_true")
    return p.parse_args()


def stream_extract_audio_clip(
    url: str,
    dest_wav: Path,
    headers: dict[str, str],
    clip_seconds: int,
    timeout_s: int,
) -> bool:
    dest_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-headers",
        ffmpeg_headers(headers),
        "-i",
        url,
        "-t",
        str(clip_seconds),
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


def to_float_audio(samples: np.ndarray) -> np.ndarray:
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if np.issubdtype(samples.dtype, np.integer):
        max_abs = float(np.iinfo(samples.dtype).max)
        return samples.astype(np.float32) / max_abs
    return samples.astype(np.float32)


def frame_rms_db(audio: np.ndarray, sr: int, frame_ms: float = 20.0) -> np.ndarray:
    frame = max(1, int(sr * frame_ms / 1000.0))
    n = len(audio) // frame
    if n <= 0:
        return np.array([], dtype=float)
    framed = audio[: n * frame].reshape(n, frame)
    rms = np.sqrt(np.mean(framed * framed, axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-9))


def audio_quality_metrics(wav_path: Path) -> dict[str, float]:
    sr, samples = wavfile.read(wav_path)
    audio = to_float_audio(samples)
    if len(audio) == 0:
        return {"sample_rate": float(sr), "duration_s": 0.0, "quality_read_ok": 0.0}

    abs_audio = np.abs(audio)
    rms = float(np.sqrt(np.mean(audio * audio)))
    peak = float(abs_audio.max())
    frame_db = frame_rms_db(audio, sr)
    active = frame_db[frame_db > -45.0] if len(frame_db) else np.array([], dtype=float)

    if len(frame_db):
        p95 = float(np.percentile(frame_db, 95))
        p10 = float(np.percentile(frame_db, 10))
        silence_fraction = float(np.mean(frame_db < -45.0))
    else:
        p95 = p10 = -90.0
        silence_fraction = 1.0

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


def artifact_flags(row: pd.Series) -> tuple[str, str, int]:
    flags: list[str] = []
    for side in ("from", "to"):
        if row.get(f"{side}_status", "missing") != "ok":
            flags.append(f"{side}_stream_not_ok")
        if row.get(f"{side}_quality_read_ok", 0.0) < 1:
            flags.append(f"{side}_read_failed")
        if row.get(f"{side}_duration_s", 0.0) < 30:
            flags.append(f"{side}_short_audio")
        if row.get(f"{side}_clipping_fraction", 0.0) > 0.005:
            flags.append(f"{side}_clipping")
        if row.get(f"{side}_snr_proxy_db", 0.0) < 12:
            flags.append(f"{side}_low_dynamic_range")
        if row.get(f"{side}_silence_fraction", 0.0) > 0.70:
            flags.append(f"{side}_mostly_silence")

    if abs(row.get("delta_rms_dbfs", 0.0)) > 10:
        flags.append("large_rms_shift")
    if abs(row.get("delta_active_rms_dbfs", 0.0)) > 10:
        flags.append("large_active_rms_shift")
    if abs(row.get("delta_silence_fraction", 0.0)) > 0.30:
        flags.append("large_silence_shift")
    if abs(row.get("delta_snr_proxy_db", 0.0)) > 15:
        flags.append("large_dynamic_range_shift")

    score = 0
    for flag in flags:
        if flag.endswith(("read_failed", "short_audio", "clipping", "mostly_silence")):
            score += 2
        elif flag.startswith("large_"):
            score += 2
        else:
            score += 1

    if score >= 4:
        risk = "high_recording_artifact_risk"
    elif score >= 2:
        risk = "medium_recording_artifact_risk"
    else:
        risk = "low_recording_artifact_risk"
    return risk, ",".join(flags), score


def resolve_transcript_path(transcript_id: str, lookup: dict[str, str]) -> str | None:
    """Resolve longitudinal IDs that may include speaker-role path segments."""

    if transcript_id in lookup:
        return lookup[transcript_id]
    parts = transcript_id.split("/")
    candidates = []
    if len(parts) >= 4 and parts[-2] in {"PWA", "Control"}:
        candidates.append("/".join(parts[:-2] + [parts[-1]]))
    if len(parts) >= 3:
        stem = parts[-1].lower()
        candidates.append("/".join(parts[:-1] + [stem]))
    if len(parts) >= 4 and parts[-2] in {"PWA", "Control"}:
        stem = parts[-1].lower()
        candidates.append("/".join(parts[:-2] + [stem]))
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


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
    transcript_cols = keys + ["from_meta_transcript_id", "to_meta_transcript_id"]
    rows = audit.merge(classified[transcript_cols], on=keys, how="left")

    session_cache_path = out_dir / "session_quality_metrics.csv"
    session_metrics: dict[str, dict[str, float | str]] = {}
    if session_cache_path.exists():
        cached = pd.read_csv(session_cache_path)
        for record in cached.to_dict("records"):
            if record.get("status") == "ok" and not pd.isna(record.get("duration_s", np.nan)):
                session_metrics[str(record["transcript_id"])] = record

    tids = sorted(set(rows["from_meta_transcript_id"]).union(rows["to_meta_transcript_id"]))
    for i, tid in enumerate(tids, start=1):
        if str(tid) in session_metrics:
            print(f"[{i}/{len(tids)}] cached {tid}", flush=True)
            continue
        print(f"[{i}/{len(tids)}] streaming {tid}", flush=True)
        cha_path_raw = resolve_transcript_path(str(tid), path_lookup)
        metrics: dict[str, float | str] = {"transcript_id": tid, "status": "missing_transcript_path"}
        if cha_path_raw:
            cha_path = Path(cha_path_raw)
            url = cha_to_media_url(cha_path)
            metrics["media_url_available"] = float(bool(url))
            if url:
                size_mb = get_remote_size_mb(url, headers)
                metrics["remote_size_mb"] = float(size_mb) if size_mb is not None else np.nan
                if size_mb is not None and size_mb > args.max_mp4_mb:
                    metrics["status"] = "skipped_oversize"
                else:
                    wav_path = args.audio_tmp / f"{cha_path.stem}.wav"
                    ok = stream_extract_audio_clip(
                        url,
                        wav_path,
                        headers,
                        clip_seconds=args.clip_seconds,
                        timeout_s=args.ffmpeg_timeout,
                    )
                    if ok:
                        try:
                            metrics.update(audio_quality_metrics(wav_path))
                            metrics["status"] = "ok"
                        except Exception as exc:  # pragma: no cover - defensive audit
                            metrics["status"] = f"quality_error:{type(exc).__name__}"
                    else:
                        metrics["status"] = "ffmpeg_failed"
                    if not args.keep_audio:
                        wav_path.unlink(missing_ok=True)
        session_metrics[tid] = metrics
        pd.DataFrame(session_metrics.values()).to_csv(session_cache_path, index=False)

    session_df = pd.DataFrame(session_metrics.values())
    pair_rows = []
    metric_cols = [
        "remote_size_mb",
        "quality_read_ok",
        "duration_s",
        "rms_dbfs",
        "active_rms_dbfs",
        "peak_dbfs",
        "clipping_fraction",
        "near_zero_fraction",
        "silence_fraction",
        "frame_p95_dbfs",
        "frame_p10_dbfs",
        "snr_proxy_db",
        "dc_offset",
    ]
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
        risk, flags, score = artifact_flags(pd.Series(out))
        out["recording_artifact_risk"] = risk
        out["recording_artifact_flags"] = flags
        out["recording_artifact_score"] = score
        pair_rows.append(out)

    pair_df = pd.DataFrame(pair_rows)
    risk_summary = (
        pair_df.groupby(["audit_label", "recording_artifact_risk"])
        .size()
        .reset_index(name="n")
        .sort_values(["audit_label", "recording_artifact_risk"])
    )
    compact_cols = [
        "longitudinal_root",
        "from_participant_id",
        "to_participant_id",
        "corpus",
        "subtype",
        "audit_label",
        "recording_artifact_risk",
        "recording_artifact_flags",
        "delta_rms_dbfs",
        "delta_active_rms_dbfs",
        "delta_silence_fraction",
        "delta_snr_proxy_db",
        "from_status",
        "to_status",
    ]

    session_df.to_csv(session_cache_path, index=False)
    pair_df.to_csv(out_dir / "pair_quality_audit.csv", index=False)
    risk_summary.to_csv(out_dir / "risk_summary.csv", index=False)

    lines = [
        "# Acoustic Mover Media-Quality Audit",
        "",
        f"- Acoustic-only stable-WAB pairs audited: {len(pair_df):,}",
        f"- Sessions streamed: {len(session_df):,}",
        "",
        "## Risk Summary",
        "",
        md_table(risk_summary),
        "",
        "## Pair-Level Technical Audit",
        "",
        md_table(pair_df[compact_cols].round(3)),
        "",
        "## Interpretation",
        "",
        f"This audit only tests recording-level technical plausibility from the first {args.clip_seconds} seconds of each media file. Low recording-artifact risk would not prove clinical acoustic change, and high risk does not prove artifact because the analyzed clip can include setup silence before the relevant utterances. But high risk weakens an acoustic-only mover claim until task-aligned audio is reviewed manually.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
