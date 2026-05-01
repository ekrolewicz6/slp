"""Create a local BA-Web-compatible recording package.

This is intentionally local-only: it copies/imports media, writes a manifest,
and runs validation. It does not upload, diagnose, or store anything outside the
chosen local output folder.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path


TASK_TYPES = {
    "conversation",
    "picture_description",
    "narrative",
    "sentence_repetition",
    "nonword_repetition",
    "reading",
    "comprehension",
    "rating",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--media-path", required=True, type=Path)
    p.add_argument("--participant-pseudonym", required=True)
    p.add_argument("--age-months", type=int, default=None)
    p.add_argument("--age-years", type=float, default=None)
    p.add_argument("--language", default="eng")
    p.add_argument("--population", required=True,
                   choices=["adult_aphasia", "child_language", "stuttering", "other"])
    p.add_argument("--task-id", required=True)
    p.add_argument("--task-type", required=True, choices=sorted(TASK_TYPES))
    p.add_argument("--task-script", type=Path, default=None)
    p.add_argument("--device", default="unknown")
    p.add_argument("--recorded-date", default=str(date.today()))
    p.add_argument("--output-root", default="data/recording_packages", type=Path)
    p.add_argument("--summary-path", default=None, type=Path)
    p.add_argument("--allow-research-sharing", action="store_true")
    p.add_argument("--allow-talkbank-deposit", action="store_true")
    p.add_argument("--spoken-phi-observed", action="store_true")
    return p.parse_args()


def media_duration_s(path: Path) -> float | None:
    if path.suffix.lower() == ".wav":
        import wave

        try:
            with wave.open(str(path), "rb") as wav:
                rate = wav.getframerate()
                return wav.getnframes() / rate if rate else None
        except Exception:
            return None
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", str(path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        return None
    return None


def wav_metadata(path: Path) -> dict:
    if path.suffix.lower() != ".wav":
        return {"media_format": path.suffix.lower().lstrip(".") or "unknown"}
    import wave

    with wave.open(str(path), "rb") as wav:
        rate = wav.getframerate()
        return {
            "media_format": "wav",
            "sample_rate_hz": rate,
            "channels": wav.getnchannels(),
            "duration_s": wav.getnframes() / rate if rate else None,
            "sample_width_bytes": wav.getsampwidth(),
        }


def package_id(args: argparse.Namespace) -> str:
    task = args.task_id.replace("/", "_").replace(" ", "_")
    pseudonym = args.participant_pseudonym.replace("/", "_").replace(" ", "_")
    return f"{pseudonym}_{args.recorded_date}_{task}"


def build_manifest(args: argparse.Namespace, media_rel: str, metadata: dict) -> dict:
    age_months = args.age_months
    if age_months is None and args.age_years is not None:
        age_months = int(round(args.age_years * 12))
    return {
        "schema_version": "0.1",
        "package_id": package_id(args),
        "participant": {
            "pseudonym": args.participant_pseudonym,
            "age_months": age_months,
            "language_primary": args.language,
            "languages_other": [],
            "sex_or_gender_optional": None,
            "population": args.population,
        },
        "task": {
            "task_id": args.task_id,
            "task_type": args.task_type,
            "prompt_language": args.language,
            "script_version": "0.1",
        },
        "recording": {
            "media_file": media_rel,
            "media_format": metadata.get("media_format", "unknown"),
            "sample_rate_hz": metadata.get("sample_rate_hz"),
            "channels": metadata.get("channels"),
            "duration_s": metadata.get("duration_s"),
            "device": args.device,
            "recorded_local_date": args.recorded_date,
        },
        "consent": {
            "consent_protocol": "local_mvp_no_upload",
            "allow_analysis": True,
            "allow_research_sharing": bool(args.allow_research_sharing),
            "allow_talkbank_deposit": bool(args.allow_talkbank_deposit),
        },
        "privacy": {
            "names_entered_in_app": False,
            "dob_entered_in_app": False,
            "phi_warning_acknowledged": True,
            "spoken_phi_review_required": True,
            "spoken_phi_observed_by_recorder": bool(args.spoken_phi_observed),
        },
        "analysis": {
            "intended_destination": "local_export",
            "asr_allowed_for_support": True,
            "asr_allowed_for_measurement": False,
        },
    }


def validate_package(pkg: Path, manifest: dict) -> dict:
    errors = []
    warnings = []
    participant = manifest.get("participant", {})
    task = manifest.get("task", {})
    recording = manifest.get("recording", {})
    privacy = manifest.get("privacy", {})
    consent = manifest.get("consent", {})

    if not participant.get("pseudonym"):
        errors.append("missing participant pseudonym")
    if participant.get("age_months") is None:
        errors.append("missing age_months")
    if not task.get("task_id"):
        errors.append("missing task_id")
    if task.get("task_type") not in TASK_TYPES:
        errors.append("invalid task_type")
    media_file = recording.get("media_file")
    media_path = pkg / media_file if media_file else None
    if not media_file or media_path is None or not media_path.exists():
        errors.append("missing media file")
    if recording.get("duration_s") is None:
        warnings.append("missing duration")
    elif recording["duration_s"] < 10:
        warnings.append("recording under 10 seconds")
    if privacy.get("spoken_phi_observed_by_recorder"):
        warnings.append("spoken PHI observed; requires review before sharing")
    if consent.get("allow_talkbank_deposit") and not consent.get("allow_research_sharing"):
        errors.append("TalkBank deposit requires research sharing consent")
    if task.get("task_type") not in {"sentence_repetition", "nonword_repetition"} and (
        participant.get("population") == "child_language"
    ):
        warnings.append("child/DLD package lacks tight repetition/nonword task")

    return {
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "warnings": warnings,
    }


def write_summary(path: Path, pkg: Path, validation: dict, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Local Recording Package Demo",
        "",
        f"- Package path: `{pkg}`",
        f"- Validation status: {validation['status']}",
        f"- Task: `{manifest['task']['task_id']}` / `{manifest['task']['task_type']}`",
        f"- Population: `{manifest['participant']['population']}`",
        f"- Duration: {manifest['recording'].get('duration_s')}",
        "",
        "## Errors",
        "",
    ]
    lines.extend(f"- {e}" for e in validation["errors"]) or lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {w}" for w in validation["warnings"]) or lines.append("- None")
    lines.extend([
        "",
        "## Notes",
        "",
        "The package is local-only and lives under `data/`, which is gitignored. "
        "This summary contains no raw media.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if not args.media_path.exists():
        raise FileNotFoundError(args.media_path)
    pkg = args.output_root / package_id(args)
    media_dir = pkg / "media"
    task_dir = pkg / "tasks"
    audit_dir = pkg / "audit"
    for d in [media_dir, task_dir, audit_dir]:
        d.mkdir(parents=True, exist_ok=True)

    media_dest = media_dir / args.media_path.name
    shutil.copy2(args.media_path, media_dest)
    if args.task_script and args.task_script.exists():
        shutil.copy2(args.task_script, task_dir / args.task_script.name)

    metadata = wav_metadata(media_dest)
    metadata["duration_s"] = metadata.get("duration_s") or media_duration_s(media_dest)
    manifest = build_manifest(args, f"media/{media_dest.name}", metadata)
    validation = validate_package(pkg, manifest)

    (pkg / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (audit_dir / "local_validation.json").write_text(
        json.dumps(validation, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.summary_path:
        write_summary(args.summary_path, pkg, validation, manifest)
    print(json.dumps({"package": str(pkg), **validation}, indent=2))


if __name__ == "__main__":
    main()
