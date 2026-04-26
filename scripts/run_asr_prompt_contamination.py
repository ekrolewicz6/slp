"""Compare PAR-only ASR with full task-window ASR for prompt contamination."""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extract_aphasia_acoustic import cha_to_media_url, stream_extract_audio  # noqa: E402
from scripts.run_cross_prompt_content import CONCEPTS, chat_tokens, concept_hits, normalize_task  # noqa: E402
from scripts.run_streaming_asr_pilot import (  # noqa: E402
    clip_local_wav,
    load_dotenv,
    patient_root,
    score_task,
    transcribe_clip,
)
from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


TIME_RE = re.compile(r"\x15(\d+)_(\d+)\x15")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--par-results",
        default="outputs/streaming_asr_pilot_pwa60_tiny/asr_task_results.csv",
        type=Path,
    )
    parser.add_argument(
        "--selected-sessions",
        default="outputs/streaming_asr_pilot_pwa60_tiny/selected_sessions.csv",
        type=Path,
    )
    parser.add_argument(
        "--segments-path",
        default="outputs/cross_prompt_content/task_segments.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/asr_prompt_contamination_pwa12_tiny",
        type=Path,
    )
    parser.add_argument("--model", default="tiny.en")
    parser.add_argument("--max-sessions", default=12, type=int)
    parser.add_argument("--max-task-seconds", default=360.0, type=float)
    parser.add_argument("--clip-pad-seconds", default=0.25, type=float)
    parser.add_argument("--ffmpeg-timeout", default=120, type=int)
    parser.add_argument("--session-timeout", default=600, type=int)
    parser.add_argument("--asr-temperature", default=0.0, type=float)
    return parser.parse_args()


def md_table(frame: pd.DataFrame, max_rows: int = 40) -> str:
    if frame.empty:
        return ""
    data = frame.head(max_rows).copy()
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].astype(str)
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(row.tolist()) + " |" for _, row in data.iterrows()]
    return "\n".join([header, sep] + body)


def parse_task_speaker_utterances(path: Path) -> dict[str, list[dict[str, object]]]:
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
            if current_task and current_speaker in {"PAR", "INV"}:
                for start_ms, end_ms in TIME_RE.findall(payload):
                    record = {
                        "speaker": current_speaker,
                        "start_s": int(start_ms) / 1000.0,
                        "end_s": int(end_ms) / 1000.0,
                        "chat_text": payload.strip(),
                    }
                    out.setdefault(current_task, []).append(record)
                    last_record = record
            continue
        if raw.startswith("\t") and current_task and current_speaker in {"PAR", "INV"}:
            if last_record is not None:
                last_record["chat_text"] = f"{last_record['chat_text']} {raw.strip()}"
            for start_ms, end_ms in TIME_RE.findall(raw):
                record = {
                    "speaker": current_speaker,
                    "start_s": int(start_ms) / 1000.0,
                    "end_s": int(end_ms) / 1000.0,
                    "chat_text": raw.strip(),
                }
                out.setdefault(current_task, []).append(record)
                last_record = record
    return out


def concept_count(text: str, task: str) -> int:
    if task not in CONCEPTS:
        return 0
    hits = concept_hits(chat_tokens(text, include_targets=False), task)
    return int(sum(hits.values()))


def select_balanced_sessions(
    par: pd.DataFrame,
    selected: pd.DataFrame,
    max_sessions: int,
) -> pd.DataFrame:
    ok_ids = set(par["transcript_id"].astype(str))
    sessions = selected[selected["transcript_id"].astype(str).isin(ok_ids)].copy()
    sessions["wab_aq"] = pd.to_numeric(sessions["wab_aq"], errors="coerce")
    sessions = sessions.dropna(subset=["wab_aq"]).sort_values("wab_aq").reset_index(drop=True)
    if max_sessions <= 0 or len(sessions) <= max_sessions:
        return sessions
    indices = np.linspace(0, len(sessions) - 1, num=max_sessions).round().astype(int)
    return sessions.loc[sorted(set(int(i) for i in indices))].reset_index(drop=True)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    load_dotenv()
    cookie = os.environ.get("APHASIABANK_COOKIE", "")
    if not cookie:
        raise SystemExit("APHASIABANK_COOKIE is required in .env or the environment.")

    par = pd.read_csv(args.par_results)
    selected = pd.read_csv(args.selected_sessions)
    segments = pd.read_csv(args.segments_path)
    chosen = select_balanced_sessions(par, selected, args.max_sessions)
    chosen.to_csv(out_dir / "selected_sessions.csv", index=False)

    import whisper  # noqa: PLC0415

    model = whisper.load_model(args.model)
    rows = []
    for session_idx, (_, session) in enumerate(chosen.iterrows(), start=1):
        cha_path = Path(str(session["file_path"]))
        url = str(session.get("media_url") or cha_to_media_url(cha_path))
        task_utts = parse_task_speaker_utterances(cha_path)
        session_segments = segments[
            segments["transcript_id"].astype(str).eq(str(session["transcript_id"]))
        ].copy()
        print(
            f"[contam] session {session_idx}/{len(chosen)} {session['transcript_id']} "
            f"wab={float(session['wab_aq']):.1f}",
            file=sys.stderr,
            flush=True,
        )
        with tempfile.TemporaryDirectory(prefix="asr_contam_") as tmp:
            temp_dir = Path(tmp)
            session_wav = temp_dir / "session.wav"
            if not stream_extract_audio(url, session_wav, cookie, timeout_s=args.session_timeout):
                continue
            for _, seg_row in session_segments.iterrows():
                task = str(seg_row["task"])
                if task not in CONCEPTS or task not in task_utts:
                    continue
                records = task_utts[task]
                starts = [float(r["start_s"]) for r in records]
                ends = [float(r["end_s"]) for r in records]
                start_s = max(0.0, min(starts) - args.clip_pad_seconds)
                end_s = max(ends) + args.clip_pad_seconds
                duration = end_s - start_s
                if duration <= 0 or duration > args.max_task_seconds:
                    continue
                clip_path = temp_dir / f"{task}.wav"
                ok, reason = clip_local_wav(
                    session_wav,
                    clip_path,
                    start_s,
                    end_s,
                    timeout_s=args.ffmpeg_timeout,
                )
                if not ok:
                    continue
                try:
                    full_text = transcribe_clip(
                        model,
                        clip_path,
                        language="en",
                        temperature=args.asr_temperature,
                        show_progress=False,
                    )
                finally:
                    clip_path.unlink(missing_ok=True)
                par_chat = " ".join(str(r["chat_text"]) for r in records if r["speaker"] == "PAR")
                inv_chat = " ".join(str(r["chat_text"]) for r in records if r["speaker"] == "INV")
                full_scored = score_task(seg_row, full_text, par_chat)
                par_row = par[
                    par["transcript_id"].astype(str).eq(str(session["transcript_id"]))
                    & par["task"].astype(str).eq(task)
                ]
                if par_row.empty:
                    continue
                par_row = par_row.iloc[0]
                rows.append(
                    {
                        "transcript_id": session["transcript_id"],
                        "participant_id": seg_row["participant_id"],
                        "patient_root": patient_root(seg_row["participant_id"]),
                        "corpus": seg_row["corpus"],
                        "subtype": seg_row["subtype"],
                        "wab_aq": seg_row["wab_aq"],
                        "task": task,
                        "full_window_seconds": duration,
                        "inv_chat_concept_count": concept_count(inv_chat, task),
                        "par_only_f1": par_row["concept_f1_vs_human"],
                        "par_only_recall": par_row["concept_recall_vs_human"],
                        "par_only_precision": par_row["concept_precision_vs_human"],
                        "par_only_coverage": par_row["asr_concept_coverage_frac"],
                        "par_only_false_positive": par_row["concept_false_positive"],
                        "full_window_f1": full_scored["concept_f1_vs_human"],
                        "full_window_recall": full_scored["concept_recall_vs_human"],
                        "full_window_precision": full_scored["concept_precision_vs_human"],
                        "full_window_coverage": full_scored["asr_concept_coverage_frac"],
                        "full_window_false_positive": full_scored["concept_false_positive"],
                        "human_coverage": full_scored["human_concept_coverage_frac"],
                        "delta_f1_full_minus_par": full_scored["concept_f1_vs_human"]
                        - par_row["concept_f1_vs_human"],
                        "delta_recall_full_minus_par": full_scored["concept_recall_vs_human"]
                        - par_row["concept_recall_vs_human"],
                        "delta_precision_full_minus_par": full_scored["concept_precision_vs_human"]
                        - par_row["concept_precision_vs_human"],
                        "delta_false_positive_full_minus_par": full_scored["concept_false_positive"]
                        - par_row["concept_false_positive"],
                        "delta_coverage_full_minus_par": full_scored["asr_concept_coverage_frac"]
                        - par_row["asr_concept_coverage_frac"],
                        "full_window_asr_text": full_text,
                    }
                )
                print(
                    f"[contam] {session['transcript_id']} {task}: "
                    f"dF1={rows[-1]['delta_f1_full_minus_par']:.3f} "
                    f"dFP={rows[-1]['delta_false_positive_full_minus_par']}",
                    file=sys.stderr,
                    flush=True,
                )

    result = pd.DataFrame(rows)
    result.to_csv(out_dir / "prompt_contamination_rows.csv", index=False)
    if result.empty:
        raise SystemExit("No prompt-contamination rows completed.")

    by_task = (
        result.groupby("task")
        .agg(
            n=("task", "size"),
            mean_inv_concepts=("inv_chat_concept_count", "mean"),
            par_f1=("par_only_f1", "mean"),
            full_f1=("full_window_f1", "mean"),
            delta_f1=("delta_f1_full_minus_par", "mean"),
            delta_recall=("delta_recall_full_minus_par", "mean"),
            delta_precision=("delta_precision_full_minus_par", "mean"),
            delta_false_positive=("delta_false_positive_full_minus_par", "mean"),
            delta_coverage=("delta_coverage_full_minus_par", "mean"),
        )
        .reset_index()
    )
    by_task.to_csv(out_dir / "by_task.csv", index=False)
    summary = pd.DataFrame(
        [
            {
                "rows": len(result),
                "sessions": result["transcript_id"].nunique(),
                "par_mean_f1": result["par_only_f1"].mean(),
                "full_mean_f1": result["full_window_f1"].mean(),
                "mean_delta_f1": result["delta_f1_full_minus_par"].mean(),
                "mean_delta_recall": result["delta_recall_full_minus_par"].mean(),
                "mean_delta_precision": result["delta_precision_full_minus_par"].mean(),
                "mean_delta_false_positive": result["delta_false_positive_full_minus_par"].mean(),
                "mean_inv_chat_concepts": result["inv_chat_concept_count"].mean(),
                "r_par_coverage_wab": pearson_safe(result["par_only_coverage"], result["wab_aq"]),
                "r_full_coverage_wab": pearson_safe(result["full_window_coverage"], result["wab_aq"]),
            }
        ]
    )
    summary.to_csv(out_dir / "summary_metrics.csv", index=False)

    lines = [
        "# ASR Prompt-Contamination Experiment",
        "",
        f"- Sessions: {result['transcript_id'].nunique()}",
        f"- Task rows: {len(result)}",
        f"- Mean full task-window seconds: {result['full_window_seconds'].mean():.1f}",
        "",
        "## Summary",
        "",
        md_table(summary.round(3)),
        "",
        "## By Task",
        "",
        md_table(by_task.round(3)),
        "",
        "## Interpretation",
        "",
        "If full task-window ASR improves recall while also increasing false "
        "positives or investigator-chat concept counts, prompt contamination is "
        "a real risk. PAR-only utterance ASR is the safer measurement default; "
        "full-window ASR should be used only after separating speakers or proving "
        "that interviewer speech does not add task concepts.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
