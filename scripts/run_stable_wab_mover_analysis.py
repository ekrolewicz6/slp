"""Find stable-WAB patients whose discourse state changes reliably."""

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
from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pairs",
        default="outputs/cross_prompt_longitudinal/consecutive_pairs.csv",
        type=Path,
    )
    parser.add_argument(
        "--state",
        default="outputs/cross_prompt_longitudinal/longitudinal_content_state.csv",
        type=Path,
    )
    parser.add_argument(
        "--thresholds",
        default="outputs/reliable_change_thresholds/thresholds.csv",
        type=Path,
    )
    parser.add_argument(
        "--two-axis-state",
        default="outputs/two_axis_state_typology/session_two_axis_state.csv",
        type=Path,
    )
    parser.add_argument("--acoustic-pattern", default="data/features/acoustic_g*.parquet")
    parser.add_argument("--output-dir", default="outputs/stable_wab_movers", type=Path)
    parser.add_argument("--stable-wab", default=3.0, type=float)
    parser.add_argument("--wab-change", default=5.0, type=float)
    return parser.parse_args()


def threshold_map(thresholds: pd.DataFrame) -> dict[str, float]:
    return dict(zip(thresholds["metric"], thresholds["empirical_abs_q95"], strict=False))


def classify_pairs(pairs: pd.DataFrame, thresholds: dict[str, float], args: argparse.Namespace) -> pd.DataFrame:
    out = pairs.copy()
    out["stable_wab"] = out["abs_delta_wab_aq"] <= args.stable_wab
    out["wab_changed"] = out["abs_delta_wab_aq"] >= args.wab_change
    metrics = {
        "core_content": ("delta_core_content_mean_z", thresholds.get("core_content_mean_z", np.inf)),
        "content": ("delta_content_mean_z", thresholds.get("content_mean_z", np.inf)),
        "coverage": ("delta_coverage_mean", thresholds.get("coverage_mean", np.inf)),
        "tokens": ("delta_tokens_mean", thresholds.get("tokens_mean", np.inf)),
        "utterances": ("delta_utts_mean", thresholds.get("utts_mean", np.inf)),
        "mean_utt_len": ("delta_meanutt_mean", thresholds.get("meanutt_mean", np.inf)),
    }
    reliable_cols = []
    for name, (col, thr) in metrics.items():
        reliable = f"reliable_{name}_change"
        direction = f"{name}_change_direction"
        out[reliable] = out[col].abs() >= thr
        out[direction] = np.select(
            [out[reliable] & (out[col] > 0), out[reliable] & (out[col] < 0)],
            ["increase", "decrease"],
            default="stable",
        )
        reliable_cols.append(reliable)
    out["any_reliable_discourse_change"] = out[reliable_cols].any(axis=1)
    out["stable_wab_discourse_mover"] = out["stable_wab"] & out["any_reliable_discourse_change"]
    out["wab_mover_discourse_stable"] = out["wab_changed"] & ~out["any_reliable_discourse_change"]
    out["mover_type"] = np.select(
        [
            out["stable_wab"] & out["reliable_core_content_change"] & (out["delta_core_content_mean_z"] > 0),
            out["stable_wab"] & out["reliable_core_content_change"] & (out["delta_core_content_mean_z"] < 0),
            out["stable_wab"] & out["any_reliable_discourse_change"],
            out["wab_changed"] & out["any_reliable_discourse_change"],
            out["wab_changed"] & ~out["any_reliable_discourse_change"],
        ],
        [
            "stable_wab_content_improved",
            "stable_wab_content_declined",
            "stable_wab_other_discourse_mover",
            "wab_and_discourse_mover",
            "wab_mover_discourse_stable",
        ],
        default="stable_or_small_change",
    )
    return out


def add_pair_metadata(pairs: pd.DataFrame, state: pd.DataFrame, two_axis: pd.DataFrame) -> pd.DataFrame:
    state_cols = [
        "participant_id",
        "corpus",
        "subtype",
        "n_tasks",
        "core_n_tasks",
        "transcript_id",
    ]
    left = state[state_cols].drop_duplicates("participant_id")
    out = pairs.merge(
        left.add_prefix("from_meta_"),
        left_on="from_participant_id",
        right_on="from_meta_participant_id",
        how="left",
    )
    out = out.merge(
        left.add_prefix("to_meta_"),
        left_on="to_participant_id",
        right_on="to_meta_participant_id",
        how="left",
    )
    if not two_axis.empty:
        axis_cols = [
            "participant_id",
            "state_quadrant",
            "assistive_priority",
            "content_axis",
            "risk_axis",
            "recoverable_axis",
        ]
        axis = two_axis[axis_cols].drop_duplicates("participant_id")
        out = out.merge(
            axis.add_prefix("from_axis_"),
            left_on="from_participant_id",
            right_on="from_axis_participant_id",
            how="left",
        )
        out = out.merge(
            axis.add_prefix("to_axis_"),
            left_on="to_participant_id",
            right_on="to_axis_participant_id",
            how="left",
        )
    return out


def acoustic_families(ac_cols: list[str]) -> dict[str, list[str]]:
    no_token_count = [
        c for c in ac_cols
        if not any(token in c for token in ("n_tokens", "speech_rate", "n_utts", "n_voiced"))
    ]
    voice_pitch_intensity = [
        c for c in no_token_count
        if any(token in c for token in ("f0", "voiced_fraction", "jitter", "shimmer", "hnr", "intensity"))
    ]
    duration_intensity = [
        c for c in no_token_count
        if any(token in c for token in ("duration", "intensity"))
    ]
    token_rate_count = [
        c for c in ac_cols
        if any(token in c for token in ("n_tokens", "speech_rate", "n_utts", "n_voiced"))
    ]
    families = {
        "custom_no_token_count_acoustic": no_token_count,
        "voice_pitch_intensity": voice_pitch_intensity,
        "duration_intensity": duration_intensity,
        "token_rate_count": token_rate_count,
    }
    return {k: v for k, v in families.items() if v}


def load_acoustic_state(pattern: str) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    paths = sorted(glob.glob(pattern))
    if not paths:
        return pd.DataFrame(), {}
    raw = pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)
    ac_cols = [c for c in raw.columns if c.startswith("ac_")]
    if not ac_cols:
        return pd.DataFrame(), {}
    key_cols = ["corpus", "participant_id"]
    agg = raw.groupby(key_cols, as_index=False)[ac_cols].mean()
    means = agg[ac_cols].mean()
    stds = agg[ac_cols].std(ddof=0).replace(0, np.nan)
    z = (agg[ac_cols] - means) / stds
    z = z.replace([np.inf, -np.inf], np.nan)
    z.columns = [f"z_{c}" for c in ac_cols]
    state = pd.concat([agg[key_cols], z], axis=1)
    families = {
        family: [f"z_{c}" for c in cols]
        for family, cols in acoustic_families(ac_cols).items()
    }
    return state, families


def _row_distance(left: pd.DataFrame, right: pd.DataFrame) -> pd.Series:
    delta = right.to_numpy(dtype=float) - left.to_numpy(dtype=float)
    valid = ~np.isnan(delta)
    numerator = np.nansum(delta ** 2, axis=1)
    denom = valid.sum(axis=1)
    out = np.sqrt(numerator / np.maximum(denom, 1))
    out[denom == 0] = np.nan
    return pd.Series(out, index=left.index)


def add_acoustic_change(
    pairs: pd.DataFrame,
    acoustic_state: pd.DataFrame,
    families: dict[str, list[str]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if acoustic_state.empty or not families:
        return pairs, pd.DataFrame()

    out = pairs.merge(
        acoustic_state.add_prefix("from_ac_"),
        left_on=["from_meta_corpus", "from_meta_participant_id"],
        right_on=["from_ac_corpus", "from_ac_participant_id"],
        how="left",
    )
    out = out.merge(
        acoustic_state.add_prefix("to_ac_"),
        left_on=["to_meta_corpus", "to_meta_participant_id"],
        right_on=["to_ac_corpus", "to_ac_participant_id"],
        how="left",
    )
    out["has_acoustic_pair"] = out["from_ac_participant_id"].notna() & out["to_ac_participant_id"].notna()

    threshold_rows = []
    reliable_cols = []
    stable_mask = out["stable_wab"] & out["has_acoustic_pair"]
    for family, z_cols in families.items():
        left_cols = [f"from_ac_{c}" for c in z_cols]
        right_cols = [f"to_ac_{c}" for c in z_cols]
        distance_col = f"delta_{family}_distance"
        reliable_col = f"reliable_{family}_change"
        out[distance_col] = _row_distance(out[left_cols], out[right_cols])
        threshold = out.loc[stable_mask, distance_col].dropna().quantile(0.95)
        if pd.isna(threshold):
            threshold = np.inf
        out[reliable_col] = out["has_acoustic_pair"] & (out[distance_col] >= threshold)
        reliable_cols.append(reliable_col)
        threshold_rows.append({
            "family": family,
            "n_features": len(z_cols),
            "stable_wab_pairs_with_acoustics": int(stable_mask.sum()),
            "stable_wab_q95_distance": float(threshold),
            "all_pair_mean_distance": float(out[distance_col].mean()),
        })

    out["any_reliable_acoustic_change"] = out[reliable_cols].any(axis=1)
    out["stable_wab_acoustic_mover"] = (
        out["stable_wab"] & out["has_acoustic_pair"] & out["any_reliable_acoustic_change"]
    )
    out["stable_wab_acoustic_only_mover"] = (
        out["stable_wab_acoustic_mover"] & ~out["any_reliable_discourse_change"]
    )
    out["stable_wab_discourse_and_acoustic_mover"] = (
        out["stable_wab_acoustic_mover"] & out["any_reliable_discourse_change"]
    )
    return out, pd.DataFrame(threshold_rows)


def summarize(pairs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    stable_wab_n = int(pairs["stable_wab"].sum())
    overall_row = {
        "n_pairs": len(pairs),
        "stable_wab_pairs": stable_wab_n,
        "stable_wab_discourse_movers": int(pairs["stable_wab_discourse_mover"].sum()),
        "stable_wab_discourse_mover_rate": float(
            pairs["stable_wab_discourse_mover"].sum() / max(stable_wab_n, 1)
        ),
        "wab_changed_pairs": int(pairs["wab_changed"].sum()),
        "wab_mover_discourse_stable": int(pairs["wab_mover_discourse_stable"].sum()),
        "delta_content_vs_delta_wab_r": pearson_safe(
            pairs["delta_core_content_mean_z"], pairs["delta_wab_aq"]
        ),
        "abs_content_vs_abs_wab_r": pearson_safe(
            pairs["abs_delta_core_content_mean_z"], pairs["abs_delta_wab_aq"]
        ),
    }
    if "has_acoustic_pair" in pairs.columns:
        acoustic_stable = pairs["stable_wab"] & pairs["has_acoustic_pair"]
        acoustic_stable_n = int(acoustic_stable.sum())
        overall_row.update({
            "pairs_with_acoustics": int(pairs["has_acoustic_pair"].sum()),
            "stable_wab_pairs_with_acoustics": acoustic_stable_n,
            "stable_wab_acoustic_movers": int(pairs["stable_wab_acoustic_mover"].sum()),
            "stable_wab_acoustic_mover_rate": float(
                pairs["stable_wab_acoustic_mover"].sum() / max(acoustic_stable_n, 1)
            ),
            "stable_wab_acoustic_only_movers": int(pairs["stable_wab_acoustic_only_mover"].sum()),
            "stable_wab_discourse_and_acoustic_movers": int(
                pairs["stable_wab_discourse_and_acoustic_mover"].sum()
            ),
            "abs_acoustic_no_token_vs_abs_wab_r": pearson_safe(
                pairs.get("delta_custom_no_token_count_acoustic_distance", pd.Series(dtype=float)),
                pairs["abs_delta_wab_aq"],
            ),
            "abs_acoustic_no_token_vs_abs_content_r": pearson_safe(
                pairs.get("delta_custom_no_token_count_acoustic_distance", pd.Series(dtype=float)),
                pairs["abs_delta_core_content_mean_z"],
            ),
        })
    overall = pd.DataFrame([overall_row])
    by_type = (
        pairs.groupby("mover_type")
        .agg(
            n=("longitudinal_root", "size"),
            roots=("longitudinal_root", "nunique"),
            mean_abs_delta_wab=("abs_delta_wab_aq", "mean"),
            mean_delta_wab=("delta_wab_aq", "mean"),
            mean_abs_delta_content=("abs_delta_core_content_mean_z", "mean"),
            mean_delta_content=("delta_core_content_mean_z", "mean"),
            mean_abs_delta_coverage=("abs_delta_coverage_mean", "mean"),
            pct_broca=("from_meta_subtype", lambda s: float((s == "Broca").mean())),
            pct_anomic=("from_meta_subtype", lambda s: float((s == "Anomic").mean())),
            pct_conduction=("from_meta_subtype", lambda s: float((s == "Conduction").mean())),
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )
    by_subtype = (
        pairs.groupby("from_meta_subtype")
        .agg(
            n_pairs=("longitudinal_root", "size"),
            stable_wab_pairs=("stable_wab", "sum"),
            stable_wab_discourse_movers=("stable_wab_discourse_mover", "sum"),
            reliable_content_rate=("reliable_core_content_change", "mean"),
            mean_abs_delta_wab=("abs_delta_wab_aq", "mean"),
            mean_abs_delta_content=("abs_delta_core_content_mean_z", "mean"),
        )
        .reset_index()
    )
    by_subtype["stable_wab_mover_rate"] = (
        by_subtype["stable_wab_discourse_movers"] / by_subtype["stable_wab_pairs"].clip(lower=1)
    )
    return overall, by_type, by_subtype.sort_values("stable_wab_mover_rate", ascending=False)


def write_summary(
    out_dir: Path,
    pairs: pd.DataFrame,
    overall: pd.DataFrame,
    by_type: pd.DataFrame,
    by_subtype: pd.DataFrame,
    examples: pd.DataFrame,
    acoustic_thresholds: pd.DataFrame,
    acoustic_examples: pd.DataFrame,
) -> None:
    lines = [
        "# Stable-WAB Discourse Movers",
        "",
        "## Overall",
        "",
        md_table(overall.round(3)),
        "",
        "## Mover Types",
        "",
        md_table(by_type.round(3)),
        "",
        "## By Subtype",
        "",
        md_table(by_subtype.round(3)),
        "",
        "## Top Stable-WAB Mover Examples",
        "",
        md_table(
            examples[
                [
                    "longitudinal_root",
                    "from_participant_id",
                    "to_participant_id",
                    "from_meta_corpus",
                    "from_meta_subtype",
                    "from_wab_aq",
                    "to_wab_aq",
                    "delta_wab_aq",
                    "delta_core_content_mean_z",
                    "delta_coverage_mean",
                    "mover_type",
                    "from_axis_assistive_priority",
                    "to_axis_assistive_priority",
                ]
            ].round(3).head(30),
        ),
        "",
        "## Acoustic Reliable-Change Thresholds",
        "",
        md_table(acoustic_thresholds.round(3)) if not acoustic_thresholds.empty else "_No acoustic pairs available._",
        "",
        "## Top Stable-WAB Acoustic-Only Examples",
        "",
        md_table(
            acoustic_examples[
                [
                    "longitudinal_root",
                    "from_participant_id",
                    "to_participant_id",
                    "from_meta_corpus",
                    "from_meta_subtype",
                    "from_wab_aq",
                    "to_wab_aq",
                    "delta_wab_aq",
                    "delta_custom_no_token_count_acoustic_distance",
                    "reliable_custom_no_token_count_acoustic_change",
                    "delta_voice_pitch_intensity_distance",
                    "reliable_voice_pitch_intensity_change",
                    "delta_duration_intensity_distance",
                    "reliable_duration_intensity_change",
                    "delta_token_rate_count_distance",
                    "reliable_token_rate_count_change",
                    "delta_core_content_mean_z",
                    "mover_type",
                ]
            ].round(3).head(30),
        ) if not acoustic_examples.empty else "_No acoustic-only stable-WAB examples._",
        "",
        "## Interpretation",
        "",
        "These are cases where standardized WAB-AQ is stable but discourse state "
        "moves beyond the empirical 95% reliable-change threshold estimated from "
        "stable-WAB pairs. They are candidates for the clinical claim that discourse "
        "monitoring can detect meaningful movement that a broad aphasia score misses. "
        "The analysis does not prove functional improvement without external outcome "
        "ratings, but it identifies patient/session pairs that should be manually "
        "reviewed or targeted in future prospective work. Acoustic-only movers "
        "are especially useful falsification cases: if manual review finds no "
        "clinically visible speech-state change, the acoustic state should be "
        "downgraded; if it does, the broad WAB score is missing a measurable "
        "dimension of change.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    pairs = pd.read_csv(args.pairs)
    state = pd.read_csv(args.state)
    thresholds = threshold_map(pd.read_csv(args.thresholds))
    two_axis = pd.read_csv(args.two_axis_state) if args.two_axis_state.exists() else pd.DataFrame()
    classified = classify_pairs(pairs, thresholds, args)
    enriched = add_pair_metadata(classified, state, two_axis)
    acoustic_state, families = load_acoustic_state(args.acoustic_pattern)
    enriched, acoustic_thresholds = add_acoustic_change(enriched, acoustic_state, families)
    overall, by_type, by_subtype = summarize(enriched)
    examples = enriched[enriched["stable_wab_discourse_mover"]].copy()
    examples = examples.sort_values("abs_delta_core_content_mean_z", ascending=False).head(50)
    if "stable_wab_acoustic_only_mover" in enriched.columns:
        acoustic_examples = enriched[enriched["stable_wab_acoustic_only_mover"]].copy()
        acoustic_examples = acoustic_examples.sort_values(
            "delta_custom_no_token_count_acoustic_distance",
            ascending=False,
        ).head(50)
    else:
        acoustic_examples = pd.DataFrame()
    enriched.to_csv(out_dir / "classified_pairs.csv", index=False)
    overall.to_csv(out_dir / "overall_summary.csv", index=False)
    by_type.to_csv(out_dir / "mover_type_summary.csv", index=False)
    by_subtype.to_csv(out_dir / "subtype_summary.csv", index=False)
    acoustic_thresholds.to_csv(out_dir / "acoustic_thresholds.csv", index=False)
    examples.to_csv(out_dir / "stable_wab_mover_examples.csv", index=False)
    acoustic_examples.to_csv(out_dir / "stable_wab_acoustic_only_examples.csv", index=False)
    write_summary(out_dir, enriched, overall, by_type, by_subtype, examples, acoustic_thresholds, acoustic_examples)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
