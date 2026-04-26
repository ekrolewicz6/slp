"""Estimate reliable-change thresholds for prompt-conditioned content state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pairs-path",
        default="outputs/cross_prompt_longitudinal/consecutive_pairs.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/reliable_change_thresholds", type=Path)
    parser.add_argument("--stable-wab-delta", default=3.0, type=float)
    parser.add_argument("--changed-wab-delta", default=5.0, type=float)
    parser.add_argument("--large-wab-delta", default=10.0, type=float)
    parser.add_argument("--seed", default=0, type=int)
    return parser.parse_args()


METRICS = {
    "core_content_mean_z": "delta_core_content_mean_z",
    "content_mean_z": "delta_content_mean_z",
    "coverage_mean": "delta_coverage_mean",
    "tokens_mean": "delta_tokens_mean",
    "utts_mean": "delta_utts_mean",
    "meanutt_mean": "delta_meanutt_mean",
}


def bootstrap_ci(values: np.ndarray, fn, n_boot: int = 1000, seed: int = 0) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return float("nan"), float("nan"), float("nan")
    stats = []
    for _ in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        stats.append(fn(sample))
    arr = np.asarray(stats, dtype=float)
    return float(np.nanmean(arr)), float(np.nanpercentile(arr, 2.5)), float(np.nanpercentile(arr, 97.5))


def threshold_rows(pairs: pd.DataFrame, stable_delta: float, seed: int) -> pd.DataFrame:
    stable = pairs[pairs["abs_delta_wab_aq"] <= stable_delta].copy()
    rows = []
    for metric, delta_col in METRICS.items():
        vals = stable[delta_col].dropna().astype(float).to_numpy()
        abs_vals = np.abs(vals)
        sd = float(np.std(vals, ddof=1)) if len(vals) > 1 else float("nan")
        sem = sd / np.sqrt(2) if np.isfinite(sd) else float("nan")
        rci95 = 1.96 * sd if np.isfinite(sd) else float("nan")
        q90, q90_lo, q90_hi = bootstrap_ci(abs_vals, lambda x: np.quantile(x, 0.90), seed=seed)
        q95, q95_lo, q95_hi = bootstrap_ci(abs_vals, lambda x: np.quantile(x, 0.95), seed=seed + 1)
        rows.append(
            {
                "metric": metric,
                "delta_col": delta_col,
                "n_stable_pairs": int(len(vals)),
                "stable_mean_delta": float(np.mean(vals)) if len(vals) else float("nan"),
                "stable_sd_delta": sd,
                "sem": sem,
                "rci95_parametric": rci95,
                "empirical_abs_q90": q90,
                "empirical_abs_q90_lo": q90_lo,
                "empirical_abs_q90_hi": q90_hi,
                "empirical_abs_q95": q95,
                "empirical_abs_q95_lo": q95_lo,
                "empirical_abs_q95_hi": q95_hi,
            }
        )
    return pd.DataFrame(rows)


def classification_rows(
    pairs: pd.DataFrame,
    thresholds: pd.DataFrame,
    stable_delta: float,
    changed_delta: float,
    large_delta: float,
) -> pd.DataFrame:
    rows = []
    for _, thr in thresholds.iterrows():
        metric = thr["metric"]
        delta_col = thr["delta_col"]
        for threshold_name in ["empirical_abs_q90", "empirical_abs_q95", "rci95_parametric"]:
            threshold = float(thr[threshold_name])
            if not np.isfinite(threshold):
                continue
            work = pairs[pairs[delta_col].notna()].copy()
            work["content_reliable_change"] = work[delta_col].abs() > threshold
            work["content_reliable_improve"] = work[delta_col] > threshold
            work["content_reliable_decline"] = work[delta_col] < -threshold
            stable = work["abs_delta_wab_aq"] <= stable_delta
            changed = work["abs_delta_wab_aq"] >= changed_delta
            large = work["abs_delta_wab_aq"] >= large_delta
            wab_improve = work["delta_wab_aq"] >= changed_delta
            wab_decline = work["delta_wab_aq"] <= -changed_delta
            rows.append(
                {
                    "metric": metric,
                    "threshold_name": threshold_name,
                    "threshold": threshold,
                    "n_pairs": int(len(work)),
                    "stable_wab_delta": stable_delta,
                    "changed_wab_delta": changed_delta,
                    "large_wab_delta": large_delta,
                    "stable_specificity": float((~work.loc[stable, "content_reliable_change"]).mean())
                    if stable.any()
                    else float("nan"),
                    "changed_sensitivity": float(work.loc[changed, "content_reliable_change"].mean())
                    if changed.any()
                    else float("nan"),
                    "large_changed_sensitivity": float(work.loc[large, "content_reliable_change"].mean())
                    if large.any()
                    else float("nan"),
                    "content_change_rate_all": float(work["content_reliable_change"].mean()),
                    "speech_only_mover_rate": float((stable & work["content_reliable_change"]).mean()),
                    "wab_changed_content_stable_rate": float((changed & ~work["content_reliable_change"]).mean()),
                    "directional_wab_improve_sensitivity": float(
                        work.loc[wab_improve, "content_reliable_improve"].mean()
                    )
                    if wab_improve.any()
                    else float("nan"),
                    "directional_wab_decline_sensitivity": float(
                        work.loc[wab_decline, "content_reliable_decline"].mean()
                    )
                    if wab_decline.any()
                    else float("nan"),
                    "delta_r_wab": pearson_safe(work[delta_col], work["delta_wab_aq"]),
                }
            )
    return pd.DataFrame(rows)


def mover_examples(pairs: pd.DataFrame, thresholds: pd.DataFrame) -> pd.DataFrame:
    core_thr = thresholds[
        thresholds["metric"].eq("core_content_mean_z")
    ]["empirical_abs_q95"].iloc[0]
    work = pairs.copy()
    work["reliable_core_change"] = work["delta_core_content_mean_z"].abs() > core_thr
    work["mover_type"] = np.select(
        [
            (work["abs_delta_wab_aq"] <= 3) & work["reliable_core_change"],
            (work["abs_delta_wab_aq"] >= 5) & ~work["reliable_core_change"],
            (work["delta_wab_aq"] >= 5) & (work["delta_core_content_mean_z"] > core_thr),
            (work["delta_wab_aq"] <= -5) & (work["delta_core_content_mean_z"] < -core_thr),
        ],
        [
            "speech_only_mover_stable_wab",
            "wab_mover_content_stable",
            "aligned_improvement",
            "aligned_decline",
        ],
        default="other",
    )
    cols = [
        "mover_type",
        "longitudinal_root",
        "from_participant_id",
        "to_participant_id",
        "from_wab_aq",
        "to_wab_aq",
        "delta_wab_aq",
        "delta_core_content_mean_z",
        "delta_coverage_mean",
        "delta_tokens_mean",
        "from_core_n_tasks",
        "to_core_n_tasks",
    ]
    return (
        work[work["mover_type"].ne("other")]
        .assign(abs_core_delta=lambda d: d["delta_core_content_mean_z"].abs())
        .sort_values(["mover_type", "abs_core_delta"], ascending=[True, False])
        [cols]
        .head(200)
    )


def subgroup_rows(pairs: pd.DataFrame, thresholds: pd.DataFrame) -> pd.DataFrame:
    core_thr = float(
        thresholds[thresholds["metric"].eq("core_content_mean_z")]["empirical_abs_q95"].iloc[0]
    )
    work = pairs.copy()
    work["reliable_core_change"] = work["delta_core_content_mean_z"].abs() > core_thr
    # Recover corpus/subtype from participant ids by joining first-session state if available.
    state_path = Path("outputs/cross_prompt_longitudinal/longitudinal_content_state.csv")
    if state_path.exists():
        state = pd.read_csv(state_path)[["participant_id", "corpus", "subtype"]]
        work = work.merge(
            state.rename(columns={"participant_id": "from_participant_id"}),
            on="from_participant_id",
            how="left",
        )
    rows = []
    for col in ["corpus", "subtype"]:
        if col not in work.columns:
            continue
        for value, group in work.groupby(col, dropna=False):
            if len(group) < 10:
                continue
            rows.append(
                {
                    "group_col": col,
                    "group": value,
                    "n_pairs": int(len(group)),
                    "mean_abs_delta_wab": float(group["abs_delta_wab_aq"].mean()),
                    "mean_abs_delta_core_content": float(
                        group["delta_core_content_mean_z"].abs().mean()
                    ),
                    "reliable_core_change_rate": float(group["reliable_core_change"].mean()),
                    "delta_r_wab": pearson_safe(
                        group["delta_core_content_mean_z"], group["delta_wab_aq"]
                    ),
                }
            )
    return pd.DataFrame(rows)


def md_table(frame: pd.DataFrame, cols: list[str] | None = None, n: int | None = None) -> str:
    if frame.empty:
        return ""
    data = frame.copy()
    if cols:
        data = data[cols]
    if n:
        data = data.head(n)
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].astype(str)
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(data.loc[i].astype(str).tolist()) + " |" for i in data.index]
    return "\n".join([header, sep] + body)


def write_summary(
    out_dir: Path,
    pairs: pd.DataFrame,
    thresholds: pd.DataFrame,
    classification: pd.DataFrame,
    subgroups: pd.DataFrame,
) -> None:
    core = thresholds[thresholds["metric"].eq("core_content_mean_z")].iloc[0]
    best = classification[
        classification["metric"].eq("core_content_mean_z")
        & classification["threshold_name"].eq("empirical_abs_q95")
    ].iloc[0]
    lines = [
        "# Reliable Change Thresholds",
        "",
        f"- Consecutive session pairs: {len(pairs)}",
        f"- Stable-WAB pairs for thresholding: {(pairs['abs_delta_wab_aq'] <= 3).sum()}",
        f"- Core content empirical 95% reliable-change threshold: {core['empirical_abs_q95']:.3f} z",
        f"- Core content stable SD of delta: {core['stable_sd_delta']:.3f}",
        f"- Specificity among stable-WAB pairs: {best['stable_specificity']:.3f}",
        f"- Sensitivity among WAB movers >=5 AQ: {best['changed_sensitivity']:.3f}",
        f"- Sensitivity among WAB movers >=10 AQ: {best['large_changed_sensitivity']:.3f}",
        f"- Delta content vs delta WAB r: {best['delta_r_wab']:.3f}",
        "",
        "## Thresholds",
        "",
        md_table(
            thresholds,
            [
                "metric",
                "n_stable_pairs",
                "stable_sd_delta",
                "empirical_abs_q90",
                "empirical_abs_q95",
                "rci95_parametric",
            ],
        ),
        "",
        "## Classification Against WAB Change",
        "",
        md_table(
            classification[
                classification["threshold_name"].isin(["empirical_abs_q95"])
            ],
            [
                "metric",
                "threshold",
                "stable_specificity",
                "changed_sensitivity",
                "large_changed_sensitivity",
                "content_change_rate_all",
                "speech_only_mover_rate",
                "wab_changed_content_stable_rate",
                "delta_r_wab",
            ],
        ),
        "",
        "## Subgroups",
        "",
        md_table(
            subgroups.sort_values("reliable_core_change_rate", ascending=False),
            [
                "group_col",
                "group",
                "n_pairs",
                "mean_abs_delta_wab",
                "mean_abs_delta_core_content",
                "reliable_core_change_rate",
                "delta_r_wab",
            ],
            20,
        ),
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    pairs = pd.read_csv(args.pairs_path)
    pairs = pairs.dropna(subset=["delta_wab_aq", "delta_core_content_mean_z"]).copy()
    thresholds = threshold_rows(pairs, args.stable_wab_delta, args.seed)
    classification = classification_rows(
        pairs,
        thresholds,
        args.stable_wab_delta,
        args.changed_wab_delta,
        args.large_wab_delta,
    )
    examples = mover_examples(pairs, thresholds)
    subgroups = subgroup_rows(pairs, thresholds)

    thresholds.to_csv(out_dir / "thresholds.csv", index=False)
    classification.to_csv(out_dir / "threshold_classification.csv", index=False)
    examples.to_csv(out_dir / "mover_examples.csv", index=False)
    subgroups.to_csv(out_dir / "subgroup_reliable_change.csv", index=False)
    write_summary(out_dir, pairs, thresholds, classification, subgroups)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
