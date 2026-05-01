"""Compare custom Praat-style acoustics with standard openSMILE/eGeMAPS.

The comparison is intentionally restricted to roots present in both feature
sets, then repeated on a balanced subset so subtype frequency does not explain
the result.
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_opensmile_balanced48_model import (  # noqa: E402
    acoustic_pipeline,
    bootstrap_ci,
    evaluate_cv,
    md_table,
    simple_pipeline,
)
from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--manifest",
        default="outputs/aphasia_standard_acoustic_replication/balanced84_patient_root_transcript_list.csv",
        type=Path,
    )
    p.add_argument(
        "--egemaps",
        default="data/features/aphasia_opensmile_egemaps_balanced84.parquet",
        type=Path,
    )
    p.add_argument("--custom-pattern", default="data/features/acoustic_g*.parquet")
    p.add_argument(
        "--output-dir",
        default="outputs/aphasia_standard_acoustic_replication",
        type=Path,
    )
    p.add_argument("--repeats", type=int, default=20)
    p.add_argument("--splits", type=int, default=4)
    p.add_argument("--seed", type=int, default=17)
    return p.parse_args()


def load_custom_features(pattern: str) -> pd.DataFrame:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No custom acoustic feature files matched {pattern!r}")
    return pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)


def aggregate_roots(feature_df: pd.DataFrame, manifest: pd.DataFrame, prefix: str) -> pd.DataFrame:
    label_cols = ["transcript_id", "patient_root", "subtype", "wab_aq", "corpus", "participant_id"]
    df = feature_df.merge(
        manifest[label_cols].drop_duplicates("transcript_id"),
        on="transcript_id",
        how="inner",
        suffixes=("_feature", ""),
    )
    feature_cols = [c for c in df.columns if c.startswith(prefix)]
    if not feature_cols:
        raise ValueError(f"No columns starting with {prefix!r}")
    agg = {c: "mean" for c in feature_cols}
    agg.update({
        "subtype": "first",
        "wab_aq": "first",
        "corpus": "first",
        "participant_id": "first",
        "transcript_id": "first",
        "window_id": "count",
    })
    return df.groupby("patient_root", as_index=False).agg(agg).rename(
        columns={"window_id": f"n_{prefix.rstrip('_')}_windows"}
    )


def make_combined_table(egemaps: pd.DataFrame, custom: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    os_cols = [c for c in egemaps.columns if c.startswith("os_")]
    ac_cols = [c for c in custom.columns if c.startswith("ac_")]
    meta_cols = ["patient_root", "subtype", "wab_aq", "corpus", "participant_id", "transcript_id"]
    merged = egemaps[meta_cols + os_cols].merge(
        custom[["patient_root"] + ac_cols],
        on="patient_root",
        how="inner",
    )
    return merged, os_cols, ac_cols


def balanced_subset(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    min_n = int(df["subtype"].value_counts().min())
    parts = []
    for subtype, group in df.groupby("subtype", sort=True):
        parts.append(group.sample(n=min_n, random_state=seed))
    return pd.concat(parts, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)


def summarize_scores(score_df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for model, group in score_df.groupby("model"):
        lo_f1, hi_f1 = bootstrap_ci(group["macro_f1"], rng)
        lo_ba, hi_ba = bootstrap_ci(group["balanced_accuracy"], rng)
        rows.append({
            "model": model,
            "mean_balanced_accuracy": group["balanced_accuracy"].mean(),
            "ba_ci_low": lo_ba,
            "ba_ci_high": hi_ba,
            "mean_macro_f1": group["macro_f1"].mean(),
            "f1_ci_low": lo_f1,
            "f1_ci_high": hi_f1,
        })
    return pd.DataFrame(rows).sort_values("mean_macro_f1", ascending=False)


def evaluate_feature_sets(
    df: pd.DataFrame,
    os_cols: list[str],
    ac_cols: list[str],
    subset_label: str,
    splits: int,
    repeats: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    y = df["subtype"].to_numpy()
    X_os = df[os_cols].to_numpy(dtype=float)
    X_ac = df[ac_cols].to_numpy(dtype=float)
    X_wab = df[["wab_aq"]].to_numpy(dtype=float)
    X_both = df[os_cols + ac_cols].to_numpy(dtype=float)
    X_os_wab = df[os_cols + ["wab_aq"]].to_numpy(dtype=float)
    X_ac_wab = df[ac_cols + ["wab_aq"]].to_numpy(dtype=float)
    X_all = df[os_cols + ac_cols + ["wab_aq"]].to_numpy(dtype=float)
    X_random = rng.normal(size=(len(df), X_both.shape[1]))
    transcript_derived_tokens = ("n_tokens", "speech_rate", "n_utts", "n_voiced")
    custom_no_token_count_cols = [
        c for c in ac_cols if not any(token in c for token in transcript_derived_tokens)
    ]
    custom_token_rate_count_cols = [
        c for c in ac_cols if any(token in c for token in transcript_derived_tokens)
    ]
    custom_voice_pitch_intensity_cols = [
        c for c in custom_no_token_count_cols
        if any(token in c for token in ("f0", "voiced_fraction", "jitter", "shimmer", "hnr", "intensity"))
    ]

    configs = [
        ("majority", X_wab, DummyClassifier(strategy="most_frequent")),
        ("wab_only", X_wab, simple_pipeline(seed)),
        ("egemaps_only", X_os, acoustic_pipeline(seed)),
        ("custom_only", X_ac, acoustic_pipeline(seed)),
        ("egemaps_plus_wab", X_os_wab, acoustic_pipeline(seed)),
        ("custom_plus_wab", X_ac_wab, acoustic_pipeline(seed)),
        ("egemaps_plus_custom", X_both, acoustic_pipeline(seed)),
        ("all_acoustic_plus_wab", X_all, acoustic_pipeline(seed)),
        ("random_features", X_random, acoustic_pipeline(seed)),
    ]
    if custom_no_token_count_cols:
        configs.append((
            "custom_no_token_counts",
            df[custom_no_token_count_cols].to_numpy(dtype=float),
            acoustic_pipeline(seed),
        ))
    if custom_voice_pitch_intensity_cols:
        configs.append((
            "custom_voice_pitch_intensity",
            df[custom_voice_pitch_intensity_cols].to_numpy(dtype=float),
            acoustic_pipeline(seed),
        ))
    if custom_token_rate_count_cols:
        configs.append((
            "custom_token_rate_count",
            df[custom_token_rate_count_cols].to_numpy(dtype=float),
            acoustic_pipeline(seed),
        ))
    scores = []
    preds = []
    for name, X, model in configs:
        score_df, pred_df = evaluate_cv(name, X, y, model, splits, repeats, seed)
        scores.append(score_df)
        preds.append(pred_df)

    shuffled = y.copy()
    rng.shuffle(shuffled)
    score_df, pred_df = evaluate_cv(
        "shuffled_labels",
        X_both,
        shuffled,
        acoustic_pipeline(seed),
        splits,
        repeats,
        seed,
    )
    scores.append(score_df)
    preds.append(pred_df)

    score_df = pd.concat(scores, ignore_index=True)
    pred_df = pd.concat(preds, ignore_index=True)
    score_df["subset"] = subset_label
    pred_df["subset"] = subset_label
    return score_df, pred_df


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    manifest = pd.read_csv(args.manifest)
    egemaps_root = aggregate_roots(pd.read_parquet(args.egemaps), manifest, "os_")
    custom_root = aggregate_roots(load_custom_features(args.custom_pattern), manifest, "ac_")
    common, os_cols, ac_cols = make_combined_table(egemaps_root, custom_root)
    balanced = balanced_subset(common, args.seed)

    all_scores = []
    all_preds = []
    subset_tables = {
        f"common{len(common)}": common,
        f"balanced_common{len(balanced)}": balanced,
    }
    for subset_label, table in subset_tables.items():
        scores, preds = evaluate_feature_sets(
            table,
            os_cols,
            ac_cols,
            subset_label,
            args.splits,
            args.repeats,
            args.seed,
        )
        all_scores.append(scores)
        all_preds.append(preds)
        table.to_csv(out_dir / f"feature_set_{subset_label}_root_table.csv", index=False)

    scores = pd.concat(all_scores, ignore_index=True)
    preds = pd.concat(all_preds, ignore_index=True)
    summaries = []
    for subset_label, group in scores.groupby("subset"):
        summary = summarize_scores(group, args.seed)
        summary.insert(0, "subset", subset_label)
        summaries.append(summary)
    summary = pd.concat(summaries, ignore_index=True)

    coverage = pd.DataFrame([
        {
            "feature_set": "egemaps",
            "roots": len(egemaps_root),
            "subtype_counts": dict(egemaps_root["subtype"].value_counts().sort_index()),
        },
        {
            "feature_set": "custom",
            "roots": len(custom_root),
            "subtype_counts": dict(custom_root["subtype"].value_counts().sort_index()),
        },
        {
            "feature_set": "common",
            "roots": len(common),
            "subtype_counts": dict(common["subtype"].value_counts().sort_index()),
        },
        {
            "feature_set": "balanced_common",
            "roots": len(balanced),
            "subtype_counts": dict(balanced["subtype"].value_counts().sort_index()),
        },
    ])

    scores.to_csv(out_dir / "feature_set_cv_scores.csv", index=False)
    preds.to_csv(out_dir / "feature_set_cv_predictions.csv", index=False)
    summary.to_csv(out_dir / "feature_set_model_summary.csv", index=False)
    coverage.to_csv(out_dir / "feature_set_coverage.csv", index=False)

    lines = [
        "# Custom vs Standard Acoustic Feature Comparison",
        "",
        f"- eGeMAPS roots from balanced84 manifest: {len(egemaps_root):,}",
        f"- Custom acoustic roots on the same manifest: {len(custom_root):,}",
        f"- Common roots: {len(common):,}",
        f"- Balanced common roots: {len(balanced):,}",
        f"- eGeMAPS features: {len(os_cols):,}",
        f"- Custom acoustic features: {len(ac_cols):,}",
        f"- CV: repeated stratified {args.splits}-fold, repeats={args.repeats}",
        "",
        "## Coverage",
        "",
        md_table(coverage),
        "",
        "## Model Summary",
        "",
        md_table(summary),
        "",
        "## Interpretation",
        "",
        "This comparison uses only patient roots present in both acoustic feature sets. The balanced subset is the cleaner headline check because the custom extraction is missing one Wernicke root from the eGeMAPS balanced84 manifest.",
        "",
    ]
    (out_dir / "feature_set_comparison_summary.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
