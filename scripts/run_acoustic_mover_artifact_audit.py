"""Audit stable-WAB acoustic-only movers for likely artifacts vs speech-state change."""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--classified-pairs", default="outputs/stable_wab_movers/classified_pairs.csv", type=Path)
    p.add_argument(
        "--acoustic-only",
        default="outputs/stable_wab_movers/stable_wab_acoustic_only_examples.csv",
        type=Path,
    )
    p.add_argument("--acoustic-pattern", default="data/features/acoustic_g*.parquet")
    p.add_argument("--output-dir", default="outputs/acoustic_mover_artifact_audit", type=Path)
    return p.parse_args()


def load_raw_acoustic(pattern: str) -> pd.DataFrame:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No acoustic files matched {pattern!r}")
    raw = pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)
    ac_cols = [c for c in raw.columns if c.startswith("ac_")]
    agg = raw.groupby(["corpus", "participant_id"], as_index=False).agg(
        {**{c: "mean" for c in ac_cols}, "window_id": "count"}
    )
    return agg.rename(columns={"window_id": "ac_n_windows"})


def feature_kind(name: str) -> str:
    low = name.lower()
    if any(token in low for token in ("jitter", "shimmer", "hnr", "voiced_fraction")):
        return "voice_quality"
    if "f0" in low:
        return "pitch"
    if "intensity" in low:
        return "intensity"
    if "duration" in low:
        return "duration"
    if any(token in low for token in ("speech_rate", "n_tokens", "n_utts", "n_voiced")):
        return "quantity_rate"
    return "other"


def top_z_drivers(row: pd.Series, limit: int = 8) -> tuple[str, dict[str, int]]:
    drivers = []
    counts: dict[str, int] = {}
    for col in row.index:
        if not col.startswith("from_ac_z_ac_"):
            continue
        base = col.replace("from_ac_z_", "")
        to_col = f"to_ac_z_{base}"
        if to_col not in row.index:
            continue
        before = row[col]
        after = row[to_col]
        if pd.isna(before) or pd.isna(after):
            continue
        delta = float(after - before)
        kind = feature_kind(base)
        drivers.append((abs(delta), base, delta, kind))
    drivers.sort(reverse=True)
    for _, _, _, kind in drivers[:limit]:
        counts[kind] = counts.get(kind, 0) + 1
    driver_text = "; ".join(
        f"{name}:{delta:+.2f}z" for _, name, delta, _ in drivers[:limit]
    )
    return driver_text, counts


def classify_row(row: pd.Series, kind_counts: dict[str, int]) -> tuple[str, str]:
    flags = []
    if row.get("reliable_custom_no_token_count_acoustic_change", False):
        flags.append("no_token_acoustic")
    if row.get("reliable_voice_pitch_intensity_change", False):
        flags.append("voice_pitch_intensity")
    if row.get("reliable_duration_intensity_change", False):
        flags.append("duration_intensity")
    if row.get("reliable_token_rate_count_change", False):
        flags.append("token_rate_count")

    artifact_points = 0
    if abs(row.get("delta_ac_intensity_mean_mean", 0.0)) >= 8:
        artifact_points += 1
    if abs(row.get("delta_ac_intensity_std_mean", 0.0)) >= 4:
        artifact_points += 1
    if min(row.get("from_ac_voiced_fraction_mean", np.inf), row.get("to_ac_voiced_fraction_mean", np.inf)) < 0.20:
        artifact_points += 1
    if min(row.get("from_ac_n_voiced_utts", np.inf), row.get("to_ac_n_voiced_utts", np.inf)) < 10:
        artifact_points += 1
    if kind_counts.get("quantity_rate", 0) >= 3:
        artifact_points += 1

    if "token_rate_count" in flags and len(flags) == 1:
        label = "quantity_or_transcription_shift"
    elif artifact_points >= 2:
        label = "possible_recording_or_sample_artifact"
    elif kind_counts.get("voice_quality", 0) + kind_counts.get("pitch", 0) >= 3:
        label = "likely_voice_pitch_state_change"
    elif "duration_intensity" in flags:
        label = "duration_intensity_change_candidate"
    else:
        label = "mixed_acoustic_change"
    return label, ",".join(flags)


def build_audit(classified: pd.DataFrame, examples: pd.DataFrame, acoustic: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["longitudinal_root", "from_participant_id", "to_participant_id"]
    z_cols = [c for c in classified.columns if c.startswith("from_ac_z_ac_") or c.startswith("to_ac_z_ac_")]
    keep = key_cols + [
        "from_meta_corpus",
        "from_meta_subtype",
        "from_wab_aq",
        "to_wab_aq",
        "delta_wab_aq",
        "delta_core_content_mean_z",
        "delta_custom_no_token_count_acoustic_distance",
        "delta_voice_pitch_intensity_distance",
        "delta_duration_intensity_distance",
        "delta_token_rate_count_distance",
        "reliable_custom_no_token_count_acoustic_change",
        "reliable_voice_pitch_intensity_change",
        "reliable_duration_intensity_change",
        "reliable_token_rate_count_change",
    ] + z_cols
    rows = examples[key_cols].merge(classified[keep], on=key_cols, how="left")
    rows = rows.merge(
        acoustic.add_prefix("from_raw_"),
        left_on=["from_meta_corpus", "from_participant_id"],
        right_on=["from_raw_corpus", "from_raw_participant_id"],
        how="left",
    )
    rows = rows.merge(
        acoustic.add_prefix("to_raw_"),
        left_on=["from_meta_corpus", "to_participant_id"],
        right_on=["to_raw_corpus", "to_raw_participant_id"],
        how="left",
    )
    raw_cols = [c for c in acoustic.columns if c.startswith("ac_")]
    for col in raw_cols:
        from_col = f"from_raw_{col}"
        to_col = f"to_raw_{col}"
        if from_col in rows.columns and to_col in rows.columns:
            rows[f"delta_{col}"] = rows[to_col] - rows[from_col]

    audit_rows = []
    for _, row in rows.iterrows():
        driver_text, kind_counts = top_z_drivers(row)
        label, flags = classify_row(row, kind_counts)
        audit_rows.append({
            "longitudinal_root": row["longitudinal_root"],
            "from_participant_id": row["from_participant_id"],
            "to_participant_id": row["to_participant_id"],
            "corpus": row["from_meta_corpus"],
            "subtype": row["from_meta_subtype"],
            "from_wab_aq": row["from_wab_aq"],
            "to_wab_aq": row["to_wab_aq"],
            "delta_wab_aq": row["delta_wab_aq"],
            "delta_core_content_mean_z": row["delta_core_content_mean_z"],
            "no_token_acoustic_distance": row["delta_custom_no_token_count_acoustic_distance"],
            "voice_pitch_intensity_distance": row["delta_voice_pitch_intensity_distance"],
            "duration_intensity_distance": row["delta_duration_intensity_distance"],
            "token_rate_count_distance": row["delta_token_rate_count_distance"],
            "reliable_families": flags,
            "audit_label": label,
            "top_z_drivers": driver_text,
            "delta_duration_s_mean": row.get("delta_ac_duration_s_mean", np.nan),
            "delta_f0_mean": row.get("delta_ac_f0_mean_mean", np.nan),
            "delta_voiced_fraction": row.get("delta_ac_voiced_fraction_mean", np.nan),
            "delta_hnr_mean": row.get("delta_ac_hnr_mean_mean", np.nan),
            "delta_intensity_mean": row.get("delta_ac_intensity_mean_mean", np.nan),
            "from_n_voiced_utts": row.get("from_raw_ac_n_voiced_utts", np.nan),
            "to_n_voiced_utts": row.get("to_raw_ac_n_voiced_utts", np.nan),
        })
    return pd.DataFrame(audit_rows)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    classified = pd.read_csv(args.classified_pairs)
    examples = pd.read_csv(args.acoustic_only)
    acoustic = load_raw_acoustic(args.acoustic_pattern)
    audit = build_audit(classified, examples, acoustic)
    label_summary = audit.groupby("audit_label").size().reset_index(name="n").sort_values("n", ascending=False)
    audit.to_csv(out_dir / "acoustic_only_artifact_audit.csv", index=False)
    label_summary.to_csv(out_dir / "audit_label_summary.csv", index=False)

    lines = [
        "# Acoustic-Only Stable-WAB Artifact Audit",
        "",
        f"- Acoustic-only stable-WAB examples audited: {len(audit):,}",
        "",
        "## Label Summary",
        "",
        md_table(label_summary),
        "",
        "## Audited Examples",
        "",
        md_table(
            audit[
                [
                    "longitudinal_root",
                    "from_participant_id",
                    "to_participant_id",
                    "corpus",
                    "subtype",
                    "delta_wab_aq",
                    "delta_core_content_mean_z",
                    "no_token_acoustic_distance",
                    "voice_pitch_intensity_distance",
                    "reliable_families",
                    "audit_label",
                    "top_z_drivers",
                ]
            ].round(3)
        ),
        "",
        "## Interpretation",
        "",
        "This is a heuristic audit, not a clinical judgment. Cases labeled likely voice/pitch state change are the best candidates for manual audio review. Cases labeled possible recording/sample artifact should be treated as threats to the acoustic-state claim until reviewed.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
