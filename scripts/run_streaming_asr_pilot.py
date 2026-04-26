"""Run a storage-free streaming ASR pilot on AphasiaBank task speech.

This is the first real audio-recognition experiment in the project. It does
not require locally persisted AphasiaBank audio. For each selected session it:

1. resolves the TalkBank media URL from the local CHAT path;
2. parses PAR utterance time marks inside known prompt blocks;
3. streams short PAR-only clips via ffmpeg with the TalkBank cookie;
4. transcribes each clip with local Whisper;
5. scores task concept recovery against the human CHAT-derived concept hits.

Temporary WAV clips are deleted immediately after transcription.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extract_aphasia_acoustic import (  # noqa: E402
    cha_to_media_url,
    get_remote_size_mb,
    stream_extract_audio,
)
from scripts.run_cross_prompt_content import (  # noqa: E402
    CONCEPTS,
    chat_tokens,
    concept_hits,
    normalize_task,
)
from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


TIME_RE = re.compile(r"\x15(\d+)_(\d+)\x15")
DEFAULT_TASKS = ["Window", "Umbrella", "Cat", "Cinderella", "Sandwich"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments-path", default="outputs/cross_prompt_content/task_segments.csv",
                        type=Path)
    parser.add_argument("--output-dir", default="outputs/streaming_asr_pilot", type=Path)
    parser.add_argument("--model", default="tiny.en")
    parser.add_argument("--max-sessions", default=2, type=int)
    parser.add_argument("--max-mp4-mb", default=250, type=int)
    parser.add_argument("--min-mp4-mb", default=0.1, type=float,
                        help="Skip remote media whose probed size is missing or implausibly small.")
    parser.add_argument("--probe-limit", default=80, type=int)
    parser.add_argument("--tasks", default=",".join(DEFAULT_TASKS))
    parser.add_argument("--prefer-subtypes", default="Broca,Wernicke,Conduction,Anomic")
    parser.add_argument("--selection-mode", choices=["severe_first", "balanced_wab"],
                        default="severe_first")
    parser.add_argument("--transcript-ids", default="",
                        help="Comma-separated transcript IDs to force into the pilot.")
    parser.add_argument("--path-contains", default="",
                        help="Optional substring that selected CHAT file paths must contain.")
    parser.add_argument("--min-human-tokens", default=5, type=int)
    parser.add_argument("--min-clip-seconds", default=0.25, type=float)
    parser.add_argument("--clip-pad-seconds", default=0.08, type=float)
    parser.add_argument("--clip-source", choices=["utterance_http", "session_wav"],
                        default="utterance_http")
    parser.add_argument("--ffmpeg-timeout", default=90, type=int)
    parser.add_argument("--session-timeout", default=600, type=int)
    parser.add_argument("--asr-temperature", default=0.0, type=float)
    parser.add_argument("--include-asr-confidence", action="store_true",
                        help="Persist Whisper segment confidence diagnostics per task.")
    parser.add_argument("--save-clip-results", action="store_true",
                        help="Persist per-utterance clip ASR text and confidence diagnostics.")
    parser.add_argument("--whisper-progress", action="store_true",
                        help="Show Whisper frame progress bars.")
    parser.add_argument("--checkpoint-every", default=1, type=int,
                        help="Write partial CSV/summary outputs every N task rows; 0 disables.")
    parser.add_argument("--resume", action="store_true",
                        help="Resume by skipping transcript/task rows already in asr_task_results.csv.")
    parser.add_argument("--keep-audio", action="store_true")
    return parser.parse_args()


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def patient_root(participant_id: str) -> str:
    return re.sub(r"[A-Za-z]$", "", str(participant_id))


def parse_task_par_utterances(path: Path) -> dict[str, list[dict[str, object]]]:
    """Return PAR utterance text/time marks per normalized prompt task."""
    out: dict[str, list[dict[str, object]]] = {}
    current_task: str | None = None
    current_speaker: str | None = None
    last_record: dict[str, object] | None = None
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return out

    for raw in lines:
        if raw.startswith("@G:"):
            current_task = normalize_task(raw.split(":", 1)[1])
            current_speaker = None
            last_record = None
            continue

        if raw.startswith("*") and ":" in raw:
            speaker, payload = raw[1:].split(":", 1)
            current_speaker = speaker.strip()
            last_record = None
            if current_task and current_speaker == "PAR":
                for start_ms, end_ms in TIME_RE.findall(payload):
                    record = {
                        "start_s": int(start_ms) / 1000.0,
                        "end_s": int(end_ms) / 1000.0,
                        "chat_text": payload.strip(),
                    }
                    out.setdefault(current_task, []).append(record)
                    last_record = record
            continue

        if raw.startswith("\t") and current_task and current_speaker == "PAR":
            if last_record is not None:
                last_record["chat_text"] = f"{last_record['chat_text']} {raw.strip()}"
            for start_ms, end_ms in TIME_RE.findall(raw):
                record = {
                    "start_s": int(start_ms) / 1000.0,
                    "end_s": int(end_ms) / 1000.0,
                    "chat_text": raw.strip(),
                }
                out.setdefault(current_task, []).append(record)
                last_record = record
    return out


def stream_clip_to_wav(
    url: str,
    dest_wav: Path,
    cookie: str,
    start_s: float,
    end_s: float,
    timeout_s: int,
) -> tuple[bool, str]:
    duration = max(0.0, end_s - start_s)
    if duration <= 0:
        return False, "non_positive_duration"
    dest_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-headers",
        f"Cookie: talkbank={cookie}; connect.sid={cookie}\r\n",
        "-ss",
        f"{start_s:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        url,
        "-vn",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-y",
        str(dest_wav),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired:
        return False, "ffmpeg_timeout"
    except Exception as exc:
        return False, f"ffmpeg_{type(exc).__name__}"
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="ignore").strip().splitlines()
        return False, stderr[-1][:180] if stderr else f"ffmpeg_return_{result.returncode}"
    if not dest_wav.exists() or dest_wav.stat().st_size < 1024:
        return False, "empty_wav"
    return True, ""


def clip_local_wav(
    source_wav: Path,
    dest_wav: Path,
    start_s: float,
    end_s: float,
    timeout_s: int,
) -> tuple[bool, str]:
    duration = max(0.0, end_s - start_s)
    if duration <= 0:
        return False, "non_positive_duration"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start_s:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(source_wav),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-y",
        str(dest_wav),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired:
        return False, "ffmpeg_timeout"
    except Exception as exc:
        return False, f"ffmpeg_{type(exc).__name__}"
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="ignore").strip().splitlines()
        return False, stderr[-1][:180] if stderr else f"ffmpeg_return_{result.returncode}"
    if not dest_wav.exists() or dest_wav.stat().st_size < 1024:
        return False, "empty_wav"
    return True, ""


def select_sessions(
    segments: pd.DataFrame,
    tasks: list[str],
    prefer_subtypes: list[str],
    cookie: str,
    max_sessions: int,
    max_mp4_mb: int,
    min_mp4_mb: float,
    probe_limit: int,
    min_human_tokens: int,
    selection_mode: str,
    transcript_ids: list[str] | None = None,
    path_contains: str = "",
) -> pd.DataFrame:
    work = segments.copy()
    work = work[work["task"].isin(tasks)]
    work = work[work["wab_aq"].notna()]
    work = work[~work["is_control"].astype(bool)]
    work = work[work["observed_n_tokens"].fillna(0).astype(float) >= min_human_tokens]
    work["file_path"] = work["file_path"].astype(str)
    if path_contains:
        work = work[work["file_path"].str.contains(path_contains, regex=False)]
    work = work[work["file_path"].map(lambda p: Path(p).exists())]
    work["patient_root"] = work["participant_id"].map(patient_root)

    task_counts = work.groupby("transcript_id")["task"].nunique().rename("n_candidate_tasks")
    token_sums = work.groupby("transcript_id")["observed_n_tokens"].sum().rename("sum_human_tokens")
    sessions = (
        work.drop_duplicates("transcript_id")
        .merge(task_counts, on="transcript_id")
        .merge(token_sums, on="transcript_id")
    )
    subtype_rank = {name: idx for idx, name in enumerate(prefer_subtypes)}
    sessions["subtype_rank"] = sessions["subtype"].map(lambda x: subtype_rank.get(str(x), 999))
    sessions["media_url"] = sessions["file_path"].map(lambda p: cha_to_media_url(Path(p)))
    sessions = sessions[sessions["media_url"].notna()]
    if transcript_ids:
        forced = set(transcript_ids)
        sessions = sessions[sessions["transcript_id"].isin(forced)].copy()

    if selection_mode == "balanced_wab" and not transcript_ids:
        sessions = sessions.sort_values(
            ["n_candidate_tasks", "transcript_id"],
            ascending=[False, True],
        )
    else:
        sessions = sessions.sort_values(
            ["n_candidate_tasks", "subtype_rank", "wab_aq", "sum_human_tokens", "transcript_id"],
            ascending=[False, True, True, False, True],
        )

    streamable = []
    probed = 0
    for _, row in sessions.iterrows():
        if selection_mode == "severe_first" and max_sessions and len(streamable) >= max_sessions:
            break
        if probe_limit and probed >= probe_limit:
            break
        probed += 1
        size_mb = get_remote_size_mb(str(row["media_url"]), cookie)
        if (
            size_mb is None
            or (min_mp4_mb and size_mb < min_mp4_mb)
            or (max_mp4_mb and size_mb > max_mp4_mb)
        ):
            continue
        row = row.copy()
        row["remote_size_mb"] = size_mb
        row["probe_rank"] = probed
        streamable.append(row)

    streamable_df = pd.DataFrame(streamable)
    if streamable_df.empty or selection_mode == "severe_first" or transcript_ids:
        return streamable_df.head(max_sessions) if max_sessions else streamable_df

    streamable_df = streamable_df.sort_values("wab_aq").reset_index(drop=True)
    if max_sessions <= 0 or len(streamable_df) <= max_sessions:
        return streamable_df
    indices = np.linspace(0, len(streamable_df) - 1, num=max_sessions).round().astype(int)
    indices = sorted(set(int(i) for i in indices))
    # Fill any duplicate-rounded gaps with high-token candidates not already chosen.
    if len(indices) < max_sessions:
        remaining = (
            streamable_df.drop(index=indices)
            .sort_values(["n_candidate_tasks", "sum_human_tokens"], ascending=[False, False])
            .head(max_sessions - len(indices))
            .index.tolist()
        )
        indices.extend(remaining)
    return streamable_df.loc[indices].sort_values("wab_aq").reset_index(drop=True)


def score_task(
    row: pd.Series,
    asr_text: str,
    human_chat_text: str,
) -> dict[str, float | int | str]:
    task = str(row["task"])
    human_hits = {
        concept: int(row.get(f"observed_{task.lower()}_{concept}", 0) or 0)
        for concept in CONCEPTS[task]
    }
    asr_tokens = chat_tokens(asr_text, include_targets=False)
    chat_tokens_human = chat_tokens(human_chat_text, include_targets=False)
    asr_hits = concept_hits(asr_tokens, task)
    overlap = sum(1 for name in CONCEPTS[task] if human_hits[name] and asr_hits[name])
    false_pos = sum(1 for name in CONCEPTS[task] if (not human_hits[name]) and asr_hits[name])
    false_neg = sum(1 for name in CONCEPTS[task] if human_hits[name] and (not asr_hits[name]))
    asr_hit_sum = sum(asr_hits.values())
    human_hit_sum = sum(human_hits.values())
    precision = overlap / max(asr_hit_sum, 1)
    recall = overlap / max(human_hit_sum, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    token_intersection = len(set(asr_tokens) & set(chat_tokens_human))
    token_union = len(set(asr_tokens) | set(chat_tokens_human))
    return {
        "asr_text": asr_text,
        "asr_n_tokens": len(asr_tokens),
        "human_chat_n_tokens": len(chat_tokens_human),
        "human_concept_coverage": human_hit_sum,
        "human_concept_coverage_frac": human_hit_sum / max(len(CONCEPTS[task]), 1),
        "asr_concept_coverage": asr_hit_sum,
        "asr_concept_coverage_frac": asr_hit_sum / max(len(CONCEPTS[task]), 1),
        "concept_overlap": overlap,
        "concept_false_positive": false_pos,
        "concept_false_negative": false_neg,
        "concept_precision_vs_human": precision,
        "concept_recall_vs_human": recall,
        "concept_f1_vs_human": f1,
        "token_jaccard_vs_human": token_intersection / max(token_union, 1),
    }


def transcribe_clip(
    model: object,
    wav_path: Path,
    language: str,
    temperature: float,
    show_progress: bool,
) -> str:
    result = transcribe_clip_detailed(
        model,
        wav_path,
        language=language,
        temperature=temperature,
        show_progress=show_progress,
    )
    return str(result.get("text", "")).strip()


def transcribe_clip_detailed(
    model: object,
    wav_path: Path,
    language: str,
    temperature: float,
    show_progress: bool,
) -> dict[str, object]:
    kwargs = {
        "language": language,
        "temperature": temperature,
        "fp16": False,
        "condition_on_previous_text": False,
        "verbose": None if show_progress else False,
    }
    if show_progress:
        result = model.transcribe(str(wav_path), **kwargs)
    else:
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                result = model.transcribe(str(wav_path), **kwargs)
    return dict(result)


def summarize_whisper_result(result: dict[str, object]) -> dict[str, float | int]:
    segments = result.get("segments", [])
    if not isinstance(segments, list) or not segments:
        return {
            "whisper_segment_count": 0,
            "whisper_avg_logprob_mean": np.nan,
            "whisper_avg_logprob_min": np.nan,
            "whisper_no_speech_prob_mean": np.nan,
            "whisper_no_speech_prob_max": np.nan,
            "whisper_compression_ratio_mean": np.nan,
            "whisper_compression_ratio_max": np.nan,
        }
    frame = pd.DataFrame(segments)
    out: dict[str, float | int] = {"whisper_segment_count": int(len(frame))}
    for col, prefix in [
        ("avg_logprob", "whisper_avg_logprob"),
        ("no_speech_prob", "whisper_no_speech_prob"),
        ("compression_ratio", "whisper_compression_ratio"),
    ]:
        vals = pd.to_numeric(frame.get(col), errors="coerce")
        out[f"{prefix}_mean"] = float(vals.mean()) if vals.notna().any() else np.nan
        out[f"{prefix}_min"] = float(vals.min()) if vals.notna().any() else np.nan
        out[f"{prefix}_max"] = float(vals.max()) if vals.notna().any() else np.nan
    return out


def md_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    data = frame.copy()
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].astype(str)
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(row.tolist()) + " |" for _, row in data.iterrows()]
    return "\n".join([header, sep] + body)


def run_asr_for_task(
    model: object,
    audio_source: str | Path,
    cookie: str,
    utterances: list[dict[str, object]],
    temp_dir: Path,
    args: argparse.Namespace,
) -> tuple[str, str, dict[str, int | float], list[dict[str, object]]]:
    asr_parts = []
    chat_parts = []
    n_attempted = 0
    n_ok = 0
    n_failed = 0
    total_audio_s = 0.0
    failure_reasons: dict[str, int] = {}
    confidence_rows: list[dict[str, float | int]] = []
    clip_rows: list[dict[str, object]] = []
    for idx, utt in enumerate(utterances):
        start_s = max(0.0, float(utt["start_s"]) - args.clip_pad_seconds)
        end_s = float(utt["end_s"]) + args.clip_pad_seconds
        if end_s - start_s < args.min_clip_seconds:
            continue
        n_attempted += 1
        total_audio_s += end_s - start_s
        clip_row: dict[str, object] = {
            "utterance_idx": idx,
            "start_s": start_s,
            "end_s": end_s,
            "clip_seconds": end_s - start_s,
            "human_chat_text": str(utt.get("chat_text", "")),
            "asr_text": "",
            "clip_success": False,
            "failure_reason": "",
        }
        clip_path = temp_dir / f"utt_{idx:04d}.wav"
        if args.clip_source == "session_wav":
            ok, reason = clip_local_wav(
                Path(audio_source),
                clip_path,
                start_s,
                end_s,
                timeout_s=args.ffmpeg_timeout,
            )
        else:
            ok, reason = stream_clip_to_wav(
                str(audio_source),
                clip_path,
                cookie,
                start_s,
                end_s,
                timeout_s=args.ffmpeg_timeout,
            )
        if not ok:
            n_failed += 1
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
            clip_row["failure_reason"] = reason
            clip_rows.append(clip_row)
            continue
        transcribed_ok = False
        try:
            if args.include_asr_confidence:
                result = transcribe_clip_detailed(
                    model,
                    clip_path,
                    language="en",
                    temperature=args.asr_temperature,
                    show_progress=args.whisper_progress,
                )
                text = str(result.get("text", "")).strip()
                confidence = summarize_whisper_result(result)
                confidence_rows.append(confidence)
                clip_row.update(confidence)
            else:
                text = transcribe_clip(
                    model,
                    clip_path,
                    language="en",
                    temperature=args.asr_temperature,
                    show_progress=args.whisper_progress,
                )
            transcribed_ok = True
        except Exception as exc:
            n_failed += 1
            reason = f"whisper_{type(exc).__name__}"
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
            clip_row["failure_reason"] = reason
            text = ""
        finally:
            if not args.keep_audio:
                clip_path.unlink(missing_ok=True)
        clip_row["asr_text"] = text
        clip_row["clip_success"] = bool(transcribed_ok)
        clip_rows.append(clip_row)
        if transcribed_ok:
            if text:
                asr_parts.append(text)
            chat_parts.append(str(utt.get("chat_text", "")))
            n_ok += 1
    diagnostics = {
        "n_utterance_clips_attempted": n_attempted,
        "n_utterance_clips_transcribed": n_ok,
        "n_utterance_clips_failed": n_failed,
        "total_par_audio_seconds": total_audio_s,
        "failure_reasons": ";".join(f"{k}:{v}" for k, v in sorted(failure_reasons.items())),
    }
    if args.include_asr_confidence:
        conf = pd.DataFrame(confidence_rows)
        if conf.empty:
            diagnostics.update(
                {
                    "whisper_clip_segment_count_mean": np.nan,
                    "whisper_avg_logprob_mean": np.nan,
                    "whisper_avg_logprob_min": np.nan,
                    "whisper_no_speech_prob_mean": np.nan,
                    "whisper_no_speech_prob_max": np.nan,
                    "whisper_compression_ratio_mean": np.nan,
                    "whisper_compression_ratio_max": np.nan,
                }
            )
        else:
            diagnostics.update(
                {
                    "whisper_clip_segment_count_mean": conf["whisper_segment_count"].mean(),
                    "whisper_avg_logprob_mean": conf["whisper_avg_logprob_mean"].mean(),
                    "whisper_avg_logprob_min": conf["whisper_avg_logprob_min"].min(),
                    "whisper_no_speech_prob_mean": conf["whisper_no_speech_prob_mean"].mean(),
                    "whisper_no_speech_prob_max": conf["whisper_no_speech_prob_max"].max(),
                    "whisper_compression_ratio_mean": conf["whisper_compression_ratio_mean"].mean(),
                    "whisper_compression_ratio_max": conf["whisper_compression_ratio_max"].max(),
                }
            )
    return " ".join(asr_parts), " ".join(chat_parts), diagnostics, clip_rows


def write_summary(out_dir: Path, rows: pd.DataFrame, selected: pd.DataFrame, model_name: str) -> None:
    lines = ["# Streaming ASR Concept Pilot", ""]
    lines.append(f"- Whisper model: `{model_name}`")
    lines.append(f"- Sessions selected: {len(selected)}")
    lines.append(f"- Task rows attempted: {len(rows)}")
    if not rows.empty:
        lines.append(f"- Utterance clips attempted: {int(rows['n_utterance_clips_attempted'].sum())}")
        lines.append(f"- Utterance clips transcribed: {int(rows['n_utterance_clips_transcribed'].sum())}")
        lines.append(f"- PAR audio transcribed: {rows['total_par_audio_seconds'].sum() / 60:.2f} minutes")
        lines.append(
            "- Mean concept F1 vs human CHAT: "
            f"{rows['concept_f1_vs_human'].mean():.3f}"
        )
        lines.append(
            "- Mean concept recall vs human CHAT: "
            f"{rows['concept_recall_vs_human'].mean():.3f}"
        )
        lines.append(
            "- Mean concept precision vs human CHAT: "
            f"{rows['concept_precision_vs_human'].mean():.3f}"
        )
        lines.append(
            "- Correlation, ASR concept coverage vs WAB-AQ: "
            f"{pearson_safe(rows['asr_concept_coverage_frac'], rows['wab_aq']):.3f}"
        )
        lines.append(
            "- Correlation, human concept coverage vs WAB-AQ: "
            f"{pearson_safe(rows['human_concept_coverage_frac'], rows['wab_aq']):.3f}"
        )
        lines.extend(
            [
                "",
                "## By Task",
                "",
                rows.groupby("task")
                .agg(
                    n=("task", "size"),
                    mean_f1=("concept_f1_vs_human", "mean"),
                    mean_recall=("concept_recall_vs_human", "mean"),
                    mean_precision=("concept_precision_vs_human", "mean"),
                    mean_asr_coverage=("asr_concept_coverage_frac", "mean"),
                    mean_human_coverage=("human_concept_coverage_frac", "mean"),
                )
                .reset_index()
                .round(3)
                .pipe(md_table),
                "",
                "## Interpretation",
                "",
                "This is a feasibility pilot, not a publishable ASR benchmark. The key test is "
                "whether storage-free PAR-only streaming can recover enough prompt-conditioned "
                "concepts to support fully automated discourse-state measurement. Low concept "
                "F1 would mean the next highest-yield work is aphasia-tuned ASR or forced "
                "alignment, not larger downstream language models.",
            ]
        )
    else:
        lines.extend(["", "No task rows were transcribed."])
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(
    out_dir: Path,
    rows: list[dict[str, object]],
    selected: pd.DataFrame,
    model_name: str,
    clip_rows: list[dict[str, object]] | None = None,
) -> pd.DataFrame:
    results = pd.DataFrame(rows)
    results.to_csv(out_dir / "asr_task_results.csv", index=False)
    if clip_rows is not None:
        pd.DataFrame(clip_rows).to_csv(out_dir / "asr_clip_results.csv", index=False)
    write_summary(out_dir, results, selected, model_name)
    return results


def main() -> None:
    args = parse_args()
    load_dotenv()
    cookie = os.environ.get("APHASIABANK_COOKIE", "")
    if not cookie:
        raise SystemExit("APHASIABANK_COOKIE is required in .env or the environment.")

    out_dir = ensure_dir(args.output_dir)
    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]
    prefer_subtypes = [s.strip() for s in args.prefer_subtypes.split(",") if s.strip()]
    transcript_ids = [t.strip() for t in args.transcript_ids.split(",") if t.strip()]
    segments = pd.read_csv(args.segments_path)
    selected = select_sessions(
        segments,
        tasks=tasks,
        prefer_subtypes=prefer_subtypes,
        cookie=cookie,
        max_sessions=args.max_sessions,
        max_mp4_mb=args.max_mp4_mb,
        min_mp4_mb=args.min_mp4_mb,
        probe_limit=args.probe_limit,
        min_human_tokens=args.min_human_tokens,
        selection_mode=args.selection_mode,
        transcript_ids=transcript_ids,
        path_contains=args.path_contains,
    )
    selected.to_csv(out_dir / "selected_sessions.csv", index=False)
    if selected.empty:
        raise SystemExit("No streamable sessions matched the ASR pilot criteria.")

    import whisper  # noqa: PLC0415

    model = whisper.load_model(args.model)
    results_path = out_dir / "asr_task_results.csv"
    clip_results_path = out_dir / "asr_clip_results.csv"
    rows: list[dict[str, object]] = []
    clip_rows_all: list[dict[str, object]] = []
    completed_pairs: set[tuple[str, str]] = set()
    if args.resume and results_path.exists():
        previous = pd.read_csv(results_path)
        rows = previous.to_dict("records")
        if args.save_clip_results and clip_results_path.exists():
            clip_rows_all = pd.read_csv(clip_results_path).to_dict("records")
        completed_pairs = set(
            zip(
                previous["transcript_id"].astype(str),
                previous["task"].astype(str),
                strict=False,
            )
        )
        print(
            f"[ASR] Resuming with {len(completed_pairs)} completed transcript/task rows.",
            file=sys.stderr,
            flush=True,
        )

    print(
        f"[ASR] Selected {len(selected)} sessions; writing outputs to {out_dir.resolve()}",
        file=sys.stderr,
        flush=True,
    )
    run_started = time.monotonic()
    for session_idx, (_, session) in enumerate(selected.iterrows(), start=1):
        cha_path = Path(str(session["file_path"]))
        url = str(session["media_url"])
        task_utts = parse_task_par_utterances(cha_path)
        session_segments = segments[
            (segments["transcript_id"] == session["transcript_id"])
            & (segments["task"].isin(tasks))
        ].copy()
        print(
            "[ASR] "
            f"Session {session_idx}/{len(selected)} {session['transcript_id']} "
            f"subtype={session.get('subtype', '')} wab={float(session['wab_aq']):.1f} "
            f"tasks={len(session_segments)}",
            file=sys.stderr,
            flush=True,
        )
        with tempfile.TemporaryDirectory(prefix="streaming_asr_") as tmp:
            temp_dir = Path(tmp)
            audio_source: str | Path = url
            session_wav = temp_dir / "session.wav"
            if args.clip_source == "session_wav":
                ok = stream_extract_audio(url, session_wav, cookie, timeout_s=args.session_timeout)
                if not ok:
                    print(
                        f"[ASR] Skipping {session['transcript_id']}: session audio stream failed.",
                        file=sys.stderr,
                        flush=True,
                    )
                    continue
                audio_source = session_wav
            for _, seg_row in session_segments.iterrows():
                task = str(seg_row["task"])
                key = (str(seg_row["transcript_id"]), task)
                if key in completed_pairs:
                    continue
                utterances = task_utts.get(task, [])
                if not utterances:
                    print(
                        f"[ASR] {seg_row['transcript_id']} {task}: no PAR time-marked utterances.",
                        file=sys.stderr,
                        flush=True,
                    )
                    continue
                asr_text, human_chat_text, diag, clip_rows = run_asr_for_task(
                    model,
                    audio_source,
                    cookie,
                    utterances,
                    temp_dir,
                    args,
                )
                if args.save_clip_results:
                    for clip_row in clip_rows:
                        clip_rows_all.append(
                            {
                                "transcript_id": seg_row["transcript_id"],
                                "participant_id": seg_row["participant_id"],
                                "patient_root": patient_root(seg_row["participant_id"]),
                                "corpus": seg_row["corpus"],
                                "subtype": seg_row["subtype"],
                                "wab_aq": seg_row["wab_aq"],
                                "task": task,
                                **clip_row,
                            }
                        )
                scored = score_task(seg_row, asr_text, human_chat_text)
                rows.append(
                    {
                        "transcript_id": seg_row["transcript_id"],
                        "participant_id": seg_row["participant_id"],
                        "patient_root": patient_root(seg_row["participant_id"]),
                        "corpus": seg_row["corpus"],
                        "subtype": seg_row["subtype"],
                        "wab_aq": seg_row["wab_aq"],
                        "task": task,
                        "remote_size_mb": session["remote_size_mb"],
                        "media_url": url,
                        **diag,
                        **scored,
                    }
                )
                completed_pairs.add(key)
                print(
                    "[ASR] "
                    f"{seg_row['transcript_id']} {task}: "
                    f"F1={scored['concept_f1_vs_human']:.3f} "
                    f"R={scored['concept_recall_vs_human']:.3f} "
                    f"P={scored['concept_precision_vs_human']:.3f} "
                    f"clips={diag['n_utterance_clips_transcribed']}/"
                    f"{diag['n_utterance_clips_attempted']}",
                    file=sys.stderr,
                    flush=True,
                )
                if args.checkpoint_every and len(rows) % args.checkpoint_every == 0:
                    write_outputs(
                        out_dir,
                        rows,
                        selected,
                        args.model,
                        clip_rows_all if args.save_clip_results else None,
                    )

    results = write_outputs(
        out_dir,
        rows,
        selected,
        args.model,
        clip_rows_all if args.save_clip_results else None,
    )
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    elapsed_min = (time.monotonic() - run_started) / 60
    print(f"Done in {elapsed_min:.1f} min. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
