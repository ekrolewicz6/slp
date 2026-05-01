"""Extract standard openSMILE acoustic features from local WAV files.

This is the reproducible acoustic baseline Brian recommended: start with
standard eGeMAPS/ComParE-style features, then decide what to discard or
ablate scientifically. The script intentionally works on local WAVs only;
TalkBank media streaming remains handled by the AphasiaBank-specific
pipeline.
"""

from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path

import opensmile
import pandas as pd


FEATURE_SETS = {
    "egemaps": opensmile.FeatureSet.eGeMAPSv02,
    "compare": opensmile.FeatureSet.ComParE_2016,
}

FEATURE_LEVELS = {
    "functionals": opensmile.FeatureLevel.Functionals,
    "lld": opensmile.FeatureLevel.LowLevelDescriptors,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--audio-path",
        type=Path,
        default=Path("data/audio/cmu01a_test.wav"),
        help="Local WAV path. This script does not persist or stream TalkBank media.",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/opensmile_smoke"),
    )
    p.add_argument(
        "--feature-set",
        choices=sorted(FEATURE_SETS),
        default="egemaps",
    )
    p.add_argument(
        "--feature-level",
        choices=sorted(FEATURE_LEVELS),
        default="functionals",
    )
    return p.parse_args()


def wav_metadata(path: Path) -> dict:
    with wave.open(str(path), "rb") as wav:
        n_frames = wav.getnframes()
        sample_rate = wav.getframerate()
        return {
            "channels": wav.getnchannels(),
            "sample_rate_hz": sample_rate,
            "duration_s": n_frames / sample_rate if sample_rate else None,
            "sample_width_bytes": wav.getsampwidth(),
            "frames": n_frames,
        }


def write_summary(
    path: Path,
    audio_path: Path,
    feature_set: str,
    feature_level: str,
    features: pd.DataFrame,
    metadata: dict,
) -> None:
    missing = features.isna().mean().sort_values(ascending=False)
    numeric = features.select_dtypes(include="number")

    lines = [
        "# openSMILE Smoke Test",
        "",
        f"- Audio path: `{audio_path}`",
        f"- Feature set: `{feature_set}`",
        f"- Feature level: `{feature_level}`",
        f"- Rows: {len(features):,}",
        f"- Columns: {features.shape[1]:,}",
        f"- Duration: {metadata.get('duration_s', 0):.2f}s",
        f"- Sample rate: {metadata.get('sample_rate_hz')} Hz",
        f"- Channels: {metadata.get('channels')}",
        "",
        "## Missingness",
        "",
        "| feature | missing_fraction |",
        "|---|---:|",
    ]
    for feature, value in missing.head(15).items():
        lines.append(f"| `{feature}` | {value:.3f} |")

    lines.extend(["", "## Largest Absolute Feature Values", "", "| feature | value |", "|---|---:|"])
    if len(numeric):
        first_row = numeric.iloc[0].abs().sort_values(ascending=False)
        for feature, value in first_row.head(15).items():
            lines.append(f"| `{feature}` | {value:.6g} |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This confirms that the local environment can compute standard openSMILE "
            "features. The next scientific step is not to treat all columns as "
            "clinically meaningful, but to run fold-clean ablations over feature "
            "families such as prosody, voice quality, spectral shape, and timing.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> None:
    args = parse_args()
    if not args.audio_path.exists():
        raise FileNotFoundError(args.audio_path)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    smile = opensmile.Smile(
        feature_set=FEATURE_SETS[args.feature_set],
        feature_level=FEATURE_LEVELS[args.feature_level],
    )
    features = smile.process_file(str(args.audio_path))
    metadata = wav_metadata(args.audio_path)

    csv_path = args.output_dir / f"{args.feature_set}_{args.feature_level}.csv"
    json_path = args.output_dir / "run_metadata.json"
    summary_path = args.output_dir / "summary.md"

    features.to_csv(csv_path)
    json_path.write_text(
        json.dumps(
            {
                "audio_path": str(args.audio_path),
                "feature_set": args.feature_set,
                "feature_level": args.feature_level,
                "rows": int(features.shape[0]),
                "columns": int(features.shape[1]),
                "metadata": metadata,
            },
            indent=2,
        )
    )
    write_summary(
        summary_path,
        args.audio_path,
        args.feature_set,
        args.feature_level,
        features,
        metadata,
    )
    print(f"wrote {csv_path}")
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
