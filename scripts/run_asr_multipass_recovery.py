"""Re-stream missed-concept clips and test ASR alternative recovery."""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import concept_set_from_text, md_table  # noqa: E402
from scripts.extract_aphasia_acoustic import stream_extract_audio  # noqa: E402
from scripts.run_streaming_asr_pilot import (  # noqa: E402
    clip_local_wav,
    summarize_whisper_result,
    transcribe_clip_detailed,
)
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clip-results",
        default="outputs/streaming_asr_clip_evidence_pwa12_tiny/asr_clip_results.csv",
        type=Path,
    )
    parser.add_argument(
        "--concept-rows",
        default="outputs/asr_concept_evidence_pwa12_tiny/clip_concept_rows.csv",
        type=Path,
    )
    parser.add_argument(
        "--selected-sessions",
        default="outputs/streaming_asr_clip_evidence_pwa12_tiny/selected_sessions.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/asr_multipass_recovery_pwa12_tiny",
        type=Path,
    )
    parser.add_argument("--model", default="tiny.en")
    parser.add_argument("--temperatures", default="0.0,0.2,0.4,0.6")
    parser.add_argument("--max-clips", default=0, type=int)
    parser.add_argument("--clip-pad-seconds", default=0.08, type=float)
    parser.add_argument("--ffmpeg-timeout", default=90, type=int)
    parser.add_argument("--session-timeout", default=600, type=int)
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


def missed_clip_frame(clips: pd.DataFrame, concepts: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["transcript_id", "task", "utterance_idx"]
    missed = (
        concepts[concepts["concept_false_negative"].eq(1)]
        .groupby(key_cols)
        .agg(missed_concepts=("concept", lambda x: sorted(set(map(str, x)))))
        .reset_index()
    )
    out = missed.merge(clips, on=key_cols, how="left", suffixes=("", "_clip"))
    session_cols = ["transcript_id", "media_url", "file_path", "remote_size_mb"]
    out = out.merge(selected[session_cols].drop_duplicates("transcript_id"), on="transcript_id", how="left")
    out["n_missed_concepts"] = out["missed_concepts"].map(len)
    return out.sort_values(["transcript_id", "task", "utterance_idx"]).reset_index(drop=True)


def transcribe_quiet(model: object, wav_path: Path, temperature: float) -> dict[str, object]:
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            return transcribe_clip_detailed(
                model,
                wav_path,
                language="en",
                temperature=temperature,
                show_progress=False,
            )


def score_recovery(text: str, task: str, missed_concepts: list[str]) -> tuple[list[str], float]:
    recovered = sorted(concept_set_from_text(text, task, include_targets=False) & set(missed_concepts))
    return recovered, len(recovered) / max(len(missed_concepts), 1)


def run_multipass(
    clips: pd.DataFrame,
    temperatures: list[float],
    model_name: str,
    cookie: str,
    args: argparse.Namespace,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    import whisper  # noqa: PLC0415

    model = whisper.load_model(model_name)
    pass_rows = []
    recovery_rows = []
    with tempfile.TemporaryDirectory(prefix="asr_multipass_") as tmp:
        tmp_dir = Path(tmp)
        for session_idx, (transcript_id, group) in enumerate(clips.groupby("transcript_id"), start=1):
            media_url = str(group["media_url"].iloc[0])
            session_wav = tmp_dir / f"session_{session_idx:03d}.wav"
            print(
                f"[multipass] {session_idx}/{clips['transcript_id'].nunique()} {transcript_id} "
                f"clips={len(group)}",
                file=sys.stderr,
                flush=True,
            )
            ok = stream_extract_audio(media_url, session_wav, cookie, timeout_s=args.session_timeout)
            if not ok:
                for _, clip in group.iterrows():
                    recovery_rows.append(
                        {
                            "transcript_id": transcript_id,
                            "task": clip["task"],
                            "utterance_idx": clip["utterance_idx"],
                            "missed_concepts": ";".join(clip["missed_concepts"]),
                            "n_missed_concepts": clip["n_missed_concepts"],
                            "union_recovered_concepts": "",
                            "union_recovery_frac": 0.0,
                            "failure_reason": "session_audio_stream_failed",
                        }
                    )
                continue
            for _, clip in group.iterrows():
                clip_path = tmp_dir / f"clip_{session_idx:03d}_{int(clip['utterance_idx']):04d}.wav"
                ok, reason = clip_local_wav(
                    session_wav,
                    clip_path,
                    float(clip["start_s"]),
                    float(clip["end_s"]),
                    timeout_s=args.ffmpeg_timeout,
                )
                if not ok:
                    recovery_rows.append(
                        {
                            "transcript_id": transcript_id,
                            "task": clip["task"],
                            "utterance_idx": clip["utterance_idx"],
                            "missed_concepts": ";".join(clip["missed_concepts"]),
                            "n_missed_concepts": clip["n_missed_concepts"],
                            "union_recovered_concepts": "",
                            "union_recovery_frac": 0.0,
                            "failure_reason": reason,
                        }
                    )
                    continue
                union_texts = []
                union_recovered: set[str] = set()
                for temp in temperatures:
                    result = transcribe_quiet(model, clip_path, temperature=temp)
                    text = str(result.get("text", "") or "").strip()
                    confidence = summarize_whisper_result(result)
                    recovered, recovery_frac = score_recovery(text, str(clip["task"]), clip["missed_concepts"])
                    union_texts.append(text)
                    union_recovered.update(recovered)
                    pass_rows.append(
                        {
                            "transcript_id": transcript_id,
                            "task": clip["task"],
                            "utterance_idx": clip["utterance_idx"],
                            "temperature": temp,
                            "missed_concepts": ";".join(clip["missed_concepts"]),
                            "n_missed_concepts": clip["n_missed_concepts"],
                            "asr_text": text,
                            "recovered_concepts": ";".join(recovered),
                            "recovery_frac": recovery_frac,
                            **confidence,
                        }
                    )
                recovery_rows.append(
                    {
                        "transcript_id": transcript_id,
                        "task": clip["task"],
                        "utterance_idx": clip["utterance_idx"],
                        "missed_concepts": ";".join(clip["missed_concepts"]),
                        "n_missed_concepts": clip["n_missed_concepts"],
                        "union_text": " || ".join(union_texts),
                        "union_recovered_concepts": ";".join(sorted(union_recovered)),
                        "union_recovery_frac": len(union_recovered) / max(int(clip["n_missed_concepts"]), 1),
                        "failure_reason": "",
                    }
                )
                clip_path.unlink(missing_ok=True)
    return pd.DataFrame(pass_rows), pd.DataFrame(recovery_rows)


def summarize(pass_rows: pd.DataFrame, recovery: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    by_temp = (
        pass_rows.groupby("temperature")
        .agg(
            n_passes=("temperature", "size"),
            mean_recovery_frac=("recovery_frac", "mean"),
            any_recovered=("recovered_concepts", lambda x: (x.astype(str).str.len() > 0).mean()),
        )
        .reset_index()
    )
    overall = pd.DataFrame(
        [
            {
                "n_clips": len(recovery),
                "n_missed_concepts": int(recovery["n_missed_concepts"].sum()),
                "clips_any_union_recovery": float(
                    recovery["union_recovered_concepts"].astype(str).str.len().gt(0).mean()
                ),
                "mean_union_recovery_frac": float(recovery["union_recovery_frac"].mean()),
                "concept_recovery_frac": float(
                    sum(
                        len([x for x in str(v).split(";") if x])
                        for v in recovery["union_recovered_concepts"]
                    )
                    / max(int(recovery["n_missed_concepts"].sum()), 1)
                ),
            }
        ]
    )
    return by_temp, overall


def write_summary(
    out_dir: Path,
    clips: pd.DataFrame,
    pass_rows: pd.DataFrame,
    recovery: pd.DataFrame,
    by_temp: pd.DataFrame,
    overall: pd.DataFrame,
) -> None:
    examples = recovery[recovery["union_recovered_concepts"].astype(str).str.len().gt(0)].head(20)
    lines = [
        "# ASR Multipass Recovery",
        "",
        f"- Missed-concept clips selected: {len(clips)}",
        f"- ASR passes: {len(pass_rows)}",
        "",
        "## Overall Union Recovery",
        "",
        md_table(overall.round(3)),
        "",
        "## By Temperature",
        "",
        md_table(by_temp.round(3)),
        "",
        "## Recovered Examples",
        "",
        md_table(
            examples[
                [
                    "transcript_id",
                    "task",
                    "utterance_idx",
                    "missed_concepts",
                    "union_recovered_concepts",
                    "union_recovery_frac",
                ]
            ].round(3)
        ),
        "",
        "## Interpretation",
        "",
        "This is an n-best proxy, not a true beam dump. It tests whether repeated "
        "Whisper passes at different temperatures recover concepts omitted by the "
        "original 1-best pass. Strong union recovery would justify a beam/n-best "
        "clarification system; weak recovery means missing concepts usually are "
        "not latent in cheap ASR alternatives.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    load_dotenv()
    cookie = os.environ.get("APHASIABANK_COOKIE", "")
    if not cookie:
        raise SystemExit("APHASIABANK_COOKIE is required in .env or the environment.")
    out_dir = ensure_dir(args.output_dir)
    clips = pd.read_csv(args.clip_results)
    concepts = pd.read_csv(args.concept_rows)
    selected = pd.read_csv(args.selected_sessions)
    missed = missed_clip_frame(clips, concepts, selected)
    if args.max_clips > 0:
        missed = missed.head(args.max_clips).copy()
    temperatures = [float(x.strip()) for x in args.temperatures.split(",") if x.strip()]
    missed.to_csv(out_dir / "selected_missed_clips.csv", index=False)
    pass_rows, recovery = run_multipass(missed, temperatures, args.model, cookie, args)
    by_temp, overall = summarize(pass_rows, recovery)
    pass_rows.to_csv(out_dir / "multipass_clip_passes.csv", index=False)
    recovery.to_csv(out_dir / "multipass_recovery.csv", index=False)
    by_temp.to_csv(out_dir / "recovery_by_temperature.csv", index=False)
    overall.to_csv(out_dir / "overall_recovery.csv", index=False)
    write_summary(out_dir, missed, pass_rows, recovery, by_temp, overall)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
