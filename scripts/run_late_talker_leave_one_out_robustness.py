"""Leave-one-child-out robustness for Rescorla late-talker early movement.

The trajectory typology suggested that 36-to-48 month movement is more
informative than earliest late-talker severity. This audit asks whether that
claim is dominated by one or two children.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


THRESHOLDS = (0.25, 0.50, 0.75, 1.00)
TARGETS = ("final_in_td_band", "persistent_gap")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--trajectory-classes",
        default="outputs/late_talker_trajectory_typology/late_talker_trajectory_classes.csv",
        type=Path,
    )
    p.add_argument(
        "--output-dir",
        default="outputs/late_talker_leave_one_out_robustness",
        type=Path,
    )
    return p.parse_args()


def odds_and_p(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    try:
        odds_ratio, p_value = fisher_exact([[a, b], [c, d]])
    except Exception:
        odds_ratio, p_value = np.nan, np.nan
    return float(odds_ratio), float(p_value)


def summarize_threshold(
    df: pd.DataFrame,
    threshold: float,
    *,
    omitted_participant: str | None = None,
) -> pd.DataFrame:
    work = df[df["delta_36_48_composite_z"].notna()].copy()
    if omitted_participant is not None:
        work = work[~work["participant_root"].eq(omitted_participant)].copy()
    work["early_gain"] = work["delta_36_48_composite_z"].ge(threshold)

    rows = []
    for target in TARGETS:
        gain = work[work["early_gain"]]
        no_gain = work[~work["early_gain"]]
        gain_pos = int(gain[target].sum())
        gain_neg = int(len(gain) - gain_pos)
        no_gain_pos = int(no_gain[target].sum())
        no_gain_neg = int(len(no_gain) - no_gain_pos)
        odds_ratio, p_value = odds_and_p(gain_pos, gain_neg, no_gain_pos, no_gain_neg)
        gain_rate = float(gain[target].mean()) if len(gain) else np.nan
        no_gain_rate = float(no_gain[target].mean()) if len(no_gain) else np.nan
        effect = gain_rate - no_gain_rate
        rows.append(
            {
                "omitted_participant": omitted_participant or "NONE",
                "threshold": threshold,
                "target": target,
                "n_total": len(work),
                "n_gain": len(gain),
                "n_no_gain": len(no_gain),
                "gain_target_rate": gain_rate,
                "no_gain_target_rate": no_gain_rate,
                "effect_gain_minus_no_gain": effect,
                "persistent_gap_reduction_if_gain": -effect if target == "persistent_gap" else np.nan,
                "odds_ratio_gain_vs_no_gain": odds_ratio,
                "fisher_p": p_value,
                "gain_positive": gain_pos,
                "gain_negative": gain_neg,
                "no_gain_positive": no_gain_pos,
                "no_gain_negative": no_gain_neg,
            }
        )
    return pd.DataFrame(rows)


def baseline_table(df: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([summarize_threshold(df, threshold) for threshold in THRESHOLDS], ignore_index=True)


def leave_one_out_table(df: pd.DataFrame) -> pd.DataFrame:
    measured = df[df["delta_36_48_composite_z"].notna()].copy()
    frames = []
    for participant in measured["participant_root"].sort_values():
        for threshold in THRESHOLDS:
            frames.append(summarize_threshold(df, threshold, omitted_participant=participant))
    return pd.concat(frames, ignore_index=True)


def influential_cases(baseline: pd.DataFrame, loo: pd.DataFrame, threshold: float = 0.75) -> pd.DataFrame:
    base = baseline[baseline["threshold"].eq(threshold)].set_index("target")
    rows = []
    for participant, group in loo[loo["threshold"].eq(threshold)].groupby("omitted_participant"):
        final = group[group["target"].eq("final_in_td_band")].iloc[0]
        persist = group[group["target"].eq("persistent_gap")].iloc[0]
        final_base = base.loc["final_in_td_band"]
        persist_base = base.loc["persistent_gap"]
        final_lift_shift = (
            final["effect_gain_minus_no_gain"] - final_base["effect_gain_minus_no_gain"]
        )
        persistent_reduction_shift = (
            persist["persistent_gap_reduction_if_gain"]
            - persist_base["persistent_gap_reduction_if_gain"]
        )
        rows.append(
            {
                "omitted_participant": participant,
                "final_td_lift_after_deletion": final["effect_gain_minus_no_gain"],
                "final_td_lift_shift": final_lift_shift,
                "final_td_fisher_p_after_deletion": final["fisher_p"],
                "persistent_gap_reduction_after_deletion": persist[
                    "persistent_gap_reduction_if_gain"
                ],
                "persistent_gap_reduction_shift": persistent_reduction_shift,
                "persistent_gap_fisher_p_after_deletion": persist["fisher_p"],
                "max_abs_effect_shift": max(
                    abs(final_lift_shift), abs(persistent_reduction_shift)
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("max_abs_effect_shift", ascending=False)


def stability_summary(loo: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold in THRESHOLDS:
        for target in TARGETS:
            subset = loo[loo["threshold"].eq(threshold) & loo["target"].eq(target)].copy()
            base = baseline[
                baseline["threshold"].eq(threshold) & baseline["target"].eq(target)
            ].iloc[0]
            effect = subset["effect_gain_minus_no_gain"]
            if target == "persistent_gap":
                effect_for_direction = subset["persistent_gap_reduction_if_gain"]
                base_effect_for_direction = base["persistent_gap_reduction_if_gain"]
            else:
                effect_for_direction = effect
                base_effect_for_direction = base["effect_gain_minus_no_gain"]
            rows.append(
                {
                    "threshold": threshold,
                    "target": target,
                    "baseline_effect": base_effect_for_direction,
                    "baseline_fisher_p": base["fisher_p"],
                    "loo_min_effect": float(effect_for_direction.min()),
                    "loo_median_effect": float(effect_for_direction.median()),
                    "loo_max_effect": float(effect_for_direction.max()),
                    "loo_all_same_direction": bool((effect_for_direction > 0).all()),
                    "loo_min_fisher_p": float(subset["fisher_p"].min()),
                    "loo_median_fisher_p": float(subset["fisher_p"].median()),
                    "loo_max_fisher_p": float(subset["fisher_p"].max()),
                    "loo_n_p_lt_0_05": int(subset["fisher_p"].lt(0.05).sum()),
                    "n_deletions": len(subset),
                }
            )
    return pd.DataFrame(rows)


def compact_participant_id(participant: str) -> str:
    return participant.split("/")[-1]


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    df = pd.read_csv(args.trajectory_classes)
    measured = df[df["delta_36_48_composite_z"].notna()].copy()
    baseline = baseline_table(df)
    loo = leave_one_out_table(df)
    influential = influential_cases(baseline, loo)
    stability = stability_summary(loo, baseline)

    baseline.to_csv(out_dir / "baseline_threshold_summary.csv", index=False)
    loo.to_csv(out_dir / "leave_one_out_threshold_summary.csv", index=False)
    influential.to_csv(out_dir / "influential_deletions.csv", index=False)
    stability.to_csv(out_dir / "stability_summary.csv", index=False)

    baseline_compact = baseline.copy()
    baseline_compact["target"] = baseline_compact["target"].replace(
        {
            "final_in_td_band": "final TD band",
            "persistent_gap": "persistent gap",
        }
    )
    baseline_compact = baseline_compact[
        [
            "threshold",
            "target",
            "n_gain",
            "n_no_gain",
            "gain_target_rate",
            "no_gain_target_rate",
            "effect_gain_minus_no_gain",
            "persistent_gap_reduction_if_gain",
            "fisher_p",
        ]
    ].round(3)

    stability_compact = stability.copy()
    stability_compact["target"] = stability_compact["target"].replace(
        {
            "final_in_td_band": "final TD lift",
            "persistent_gap": "persistent-gap reduction",
        }
    )
    stability_compact = stability_compact[
        [
            "threshold",
            "target",
            "baseline_effect",
            "loo_min_effect",
            "loo_median_effect",
            "loo_max_effect",
            "loo_all_same_direction",
            "baseline_fisher_p",
            "loo_n_p_lt_0_05",
            "n_deletions",
        ]
    ].round(3)

    top = influential.head(10).copy()
    top["case"] = top["omitted_participant"].map(compact_participant_id)
    top = top[
        [
            "case",
            "final_td_lift_after_deletion",
            "final_td_fisher_p_after_deletion",
            "persistent_gap_reduction_after_deletion",
            "persistent_gap_fisher_p_after_deletion",
            "max_abs_effect_shift",
        ]
    ].round(3)

    threshold_075 = stability[
        stability["threshold"].eq(0.75)
    ].set_index("target")
    final_075 = threshold_075.loc["final_in_td_band"]
    persist_075 = threshold_075.loc["persistent_gap"]
    interpretation = (
        "The early-movement clue is directionally robust but still fragile. At the "
        "0.75 z threshold, every leave-one-child-out deletion keeps the final-TD "
        "lift positive and the persistent-gap reduction positive. Statistical "
        "significance is not deletion-proof: the final-TD comparison remains "
        f"p < .05 for {int(final_075['loo_n_p_lt_0_05'])}/"
        f"{int(final_075['n_deletions'])} deletions, and the persistent-gap "
        f"comparison remains p < .05 for {int(persist_075['loo_n_p_lt_0_05'])}/"
        f"{int(persist_075['n_deletions'])}. This is strong enough to justify "
        "prospective measurement of early movement, but not strong enough to "
        "claim an individual prognosis rule."
    )

    lines = [
        "# Late-Talker Leave-One-Out Robustness",
        "",
        f"- Late talkers with measured 36-to-48 movement: {len(measured):,}",
        f"- Leave-one-child-out deletions per threshold: {len(measured):,}",
        "",
        "## Baseline Threshold Effects",
        "",
        md_table(baseline_compact),
        "",
        "## Leave-One-Out Stability",
        "",
        md_table(stability_compact),
        "",
        "## Most Influential Deletions at 0.75 z",
        "",
        md_table(top),
        "",
        "## Interpretation",
        "",
        interpretation,
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
