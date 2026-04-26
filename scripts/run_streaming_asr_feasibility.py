"""Audit streaming-audio feasibility for real ASR experiments.

The project intentionally does not persist AphasiaBank audio. This script
documents the actual state:

* what acoustic features survived from streamed media;
* which transcript IDs map to TalkBank media URLs;
* whether credentials and ffmpeg are available;
* a small remote-size probe for candidate sessions;
* whether local ASR backends are installed.

It never writes audio to disk.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extract_aphasia_acoustic import cha_to_media_url, get_remote_size_mb  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs/streaming_asr_feasibility", type=Path)
    parser.add_argument("--probe-limit", default=40, type=int)
    parser.add_argument("--max-candidate-mb", default=250, type=int)
    return parser.parse_args()


def load_dotenv(path: Path = Path(".env")) -> dict[str, str]:
    vals = {}
    if not path.exists():
        return vals
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip()
        os.environ.setdefault(k.strip(), v.strip())
    return vals


def acoustic_manifest() -> tuple[pd.DataFrame, pd.DataFrame]:
    paths = sorted(Path("data/features").glob("acoustic_g*.parquet"))
    rows = []
    frames = []
    for path in paths:
        df = pd.read_parquet(path)
        frames.append(df.assign(source_file=path.name))
        rows.append(
            {
                "source_file": path.name,
                "rows": len(df),
                "sessions": int(df["transcript_id"].nunique()),
                "windows": int(df["window_id"].nunique()),
                "size_kb": round(path.stat().st_size / 1024, 1),
            }
        )
    all_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return all_df, pd.DataFrame(rows)


def build_stream_manifest(acoustic: pd.DataFrame) -> pd.DataFrame:
    idx = pd.read_parquet("data/features/aphasiabank_transcripts.parquet")
    idx = idx.drop_duplicates("transcript_id")
    cols = ["transcript_id", "file_path", "section", "corpus", "participant_id"]
    idx = idx[[c for c in cols if c in idx.columns]].copy()
    covered = acoustic.groupby("transcript_id").agg(
        acoustic_windows=("window_id", "nunique"),
        acoustic_rows=("window_id", "size"),
    )
    manifest = idx.merge(covered, on="transcript_id", how="left")
    manifest["has_acoustic_features"] = manifest["acoustic_windows"].notna()
    manifest["acoustic_windows"] = manifest["acoustic_windows"].fillna(0).astype(int)
    manifest["acoustic_rows"] = manifest["acoustic_rows"].fillna(0).astype(int)
    manifest["media_url"] = manifest["file_path"].map(lambda p: cha_to_media_url(Path(p)) if pd.notna(p) else None)
    manifest["cha_exists"] = manifest["file_path"].map(lambda p: Path(p).exists() if pd.notna(p) else False)
    return manifest


def asr_backend_status() -> pd.DataFrame:
    modules = ["whisper", "faster_whisper", "mlx_whisper", "torch", "torchaudio", "openai"]
    commands = ["ffmpeg", "whisper"]
    rows = []
    for module in modules:
        rows.append(
            {
                "kind": "python_module",
                "name": module,
                "available": bool(importlib.util.find_spec(module)),
                "path": "",
            }
        )
    for command in commands:
        path = shutil.which(command)
        rows.append({"kind": "command", "name": command, "available": path is not None, "path": path or ""})
    return pd.DataFrame(rows)


def probe_remote_sizes(manifest: pd.DataFrame, cookie: str, limit: int, max_candidate_mb: int) -> pd.DataFrame:
    if not cookie:
        return pd.DataFrame()
    work = manifest[
        manifest["media_url"].notna() & manifest["cha_exists"] & manifest["has_acoustic_features"]
    ].copy()
    # Prefer sessions that already produced acoustics and have fewer windows,
    # because they are likely tractable for ASR pilots.
    work = work.sort_values(["acoustic_windows", "transcript_id"], ascending=[True, True]).head(limit)
    rows = []
    for _, row in work.iterrows():
        size_mb = get_remote_size_mb(str(row["media_url"]), cookie)
        rows.append(
            {
                "transcript_id": row["transcript_id"],
                "corpus": row.get("corpus", ""),
                "participant_id": row.get("participant_id", ""),
                "acoustic_windows": int(row["acoustic_windows"]),
                "remote_size_mb": size_mb,
                "candidate_under_limit": bool(size_mb is not None and size_mb <= max_candidate_mb),
                "media_url": row["media_url"],
            }
        )
    return pd.DataFrame(rows)


def md_table(frame: pd.DataFrame, n: int | None = None) -> str:
    if frame.empty:
        return ""
    data = frame.copy()
    if n:
        data = data.head(n)
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.2f}")
        else:
            data[col] = data[col].astype(str)
    data = data.astype(str)
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(row.tolist()) + " |" for _, row in data.iterrows()]
    return "\n".join([header, sep] + body)


def write_summary(
    out_dir: Path,
    acoustic_summary: pd.DataFrame,
    manifest: pd.DataFrame,
    backend: pd.DataFrame,
    probes: pd.DataFrame,
    cookie_present: bool,
) -> None:
    lines = [
        "# Streaming ASR Feasibility",
        "",
        f"- TalkBank cookie present: {cookie_present}",
        f"- Transcript sessions indexed: {manifest['transcript_id'].nunique()}",
        f"- Sessions with acoustic features from streamed media: {manifest['has_acoustic_features'].sum()}",
        f"- Acoustic windows persisted: {manifest['acoustic_windows'].sum()}",
        f"- Local audio/video files intentionally persisted: 1 demo WAV plus scratch dirs",
        "",
        "## Acoustic Feature Files",
        "",
        md_table(acoustic_summary),
        "",
        "## ASR Backend Status",
        "",
        md_table(backend),
        "",
        "## Remote Size Probe",
        "",
        md_table(probes[["transcript_id", "corpus", "participant_id", "acoustic_windows", "remote_size_mb", "candidate_under_limit"]], 40)
        if not probes.empty
        else "No remote probes run because cookie was unavailable.",
        "",
        "## Interpretation",
        "",
        "The real-ASR branch is feasible as a streaming experiment, not a local-file experiment. "
        "The next blocker is choosing/installing an ASR backend or using an external API; the "
        "media access pattern itself is already implemented by `scripts/extract_aphasia_acoustic.py`.",
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    dotenv = load_dotenv()
    cookie = os.environ.get("APHASIABANK_COOKIE", "")
    cookie_present = bool(cookie or dotenv.get("APHASIABANK_COOKIE"))

    acoustic, acoustic_summary = acoustic_manifest()
    manifest = build_stream_manifest(acoustic)
    backend = asr_backend_status()
    probes = probe_remote_sizes(manifest, cookie, args.probe_limit, args.max_candidate_mb)

    acoustic_summary.to_csv(out_dir / "acoustic_feature_summary.csv", index=False)
    manifest.to_csv(out_dir / "streaming_media_manifest.csv", index=False)
    backend.to_csv(out_dir / "asr_backend_status.csv", index=False)
    probes.to_csv(out_dir / "remote_size_probe.csv", index=False)
    write_summary(out_dir, acoustic_summary, manifest, backend, probes, cookie_present)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
