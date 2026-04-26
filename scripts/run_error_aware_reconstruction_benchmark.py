"""Error-aware reconstruction benchmark inspired by Adikari et al. 2025.

The Scientific Reports paper tests GPT-style sentence reconstruction for
open-ended aphasic conversation. Before adding another LLM dependency, this
script uses the supervision already present in CHAT transcripts:

* CLAN error tags such as [* p:n], [* s:r], [* n:uk], [* m:0ed].
* Target annotations such as [: umbrella] or [: x@n].

For each prompt-conditioned discourse segment, we measure whether target
annotations "rescue" event-concept coverage, which error types create the
largest content loss, and whether oracle-corrected content changes WAB-AQ
prediction under patient-grouped CV.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_cross_prompt_content import (  # noqa: E402
    add_control_norms,
    build_segments,
    parse_task_utterances,
)
from src.analysis.review_grade import (  # noqa: E402
    bootstrap_ci,
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


ERROR_RE = re.compile(r"\[\*\s*([a-z])(?::([^\]]+))?\]", flags=re.IGNORECASE)
TARGET_RE = re.compile(r"\[:\s*([^\]]+)\]")

CATEGORY_NAMES = {
    "p": "phonological",
    "s": "semantic",
    "n": "neologism",
    "m": "morphological",
    "d": "dysfluency",
}

SUBTYPE_COLUMNS = [
    "p_w",
    "p_n",
    "p_m",
    "p_unspecified",
    "s_r",
    "s_ur",
    "s_uk",
    "s_per",
    "s_unspecified",
    "n_k",
    "n_uk",
    "n_unspecified",
    "m_all",
    "d_sw",
    "d_other",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data/raw/aphasiabank/Protocol", type=Path)
    parser.add_argument(
        "--segments-path",
        default="outputs/cross_prompt_content/task_segments.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/error_aware_reconstruction", type=Path)
    parser.add_argument("--cv-folds", default=5, type=int)
    parser.add_argument("--min-tokens", default=5, type=int)
    return parser.parse_args()


def normalize_error_code(letter: str, detail: str | None) -> str:
    letter = letter.lower()
    detail = (detail or "").lower().strip()
    primary = detail.split()[0].split(":")[0].split("-")[0] if detail else ""

    if letter == "m":
        return "m_all"
    if letter == "d":
        return "d_sw" if primary == "sw" else "d_other"
    if letter in {"p", "s", "n"}:
        return f"{letter}_{primary or 'unspecified'}"
    return f"{letter}_other"


def extract_error_features(text: str, observed_tokens: float) -> dict[str, float]:
    counts = {f"error_{name}": 0.0 for name in CATEGORY_NAMES.values()}
    subtype_counts = {f"error_{name}": 0.0 for name in SUBTYPE_COLUMNS}

    for letter, detail in ERROR_RE.findall(text):
        letter = letter.lower()
        category = CATEGORY_NAMES.get(letter)
        if category:
            counts[f"error_{category}"] += 1.0
        code = normalize_error_code(letter, detail)
        col = f"error_{code}"
        if col in subtype_counts:
            subtype_counts[col] += 1.0

    targets = [t.strip().lower() for t in TARGET_RE.findall(text)]
    unknown_targets = sum(1 for t in targets if t in {"x@n", "xx@n"} or t.startswith("x@"))
    total_errors = float(sum(counts.values()))
    denom = max(float(observed_tokens), 1.0)

    features: dict[str, float] = {
        "error_total": total_errors,
        "target_annotation_count": float(len(targets)),
        "known_target_annotation_count": float(len(targets) - unknown_targets),
        "unknown_target_annotation_count": float(unknown_targets),
        "error_rate_100": 100.0 * total_errors / denom,
        "target_annotation_rate_100": 100.0 * len(targets) / denom,
        "known_target_rate_100": 100.0 * (len(targets) - unknown_targets) / denom,
        "unknown_target_rate_100": 100.0 * unknown_targets / denom,
    }
    features.update(counts)
    features.update(subtype_counts)

    for col in list(counts) + list(subtype_counts):
        features[f"{col}_rate_100"] = 100.0 * features[col] / denom

    features["paper_bottleneck_error_count"] = (
        features["error_phonological"]
        + features["error_semantic"]
        + features["error_neologism"]
    )
    features["paper_bottleneck_error_rate_100"] = (
        100.0 * features["paper_bottleneck_error_count"] / denom
    )
    features["known_reconstructable_error_count"] = (
        features["error_p_w"]
        + features["error_p_n"]
        + features["error_p_m"]
        + features["error_s_r"]
        + features["error_s_ur"]
        + features["error_n_k"]
    )
    features["unknown_intent_error_count"] = features["error_s_uk"] + features["error_n_uk"]
    features["known_reconstructable_error_rate_100"] = (
        100.0 * features["known_reconstructable_error_count"] / denom
    )
    features["unknown_intent_error_rate_100"] = (
        100.0 * features["unknown_intent_error_count"] / denom
    )
    return features


def load_segments(args: argparse.Namespace) -> pd.DataFrame:
    if args.segments_path.exists():
        return pd.read_csv(args.segments_path)
    segments = build_segments(args.root, min_tokens=args.min_tokens)
    segments, _ = add_control_norms(segments)
    return segments


def attach_raw_text(segments: pd.DataFrame) -> pd.DataFrame:
    cache: dict[str, dict[str, list[str]]] = {}
    raw_texts = []
    utterance_counts = []

    for _, row in segments.iterrows():
        path = str(row["file_path"])
        if path not in cache:
            cache[path] = parse_task_utterances(Path(path))
        utts = cache[path].get(str(row["task"]), [])
        raw_texts.append("\n".join(utts))
        utterance_counts.append(len(utts))

    out = segments.copy()
    out["raw_task_text"] = raw_texts
    out["raw_task_utterances"] = utterance_counts
    return out


def build_error_segments(args: argparse.Namespace) -> pd.DataFrame:
    segments = attach_raw_text(load_segments(args))
    feature_rows = [
        extract_error_features(text, tokens)
        for text, tokens in zip(segments["raw_task_text"], segments["observed_n_tokens"])
    ]
    errors = pd.DataFrame(feature_rows)
    out = pd.concat([segments.reset_index(drop=True), errors], axis=1)
    out["oracle_concept_gain"] = (
        out["target_augmented_concept_coverage"] - out["observed_concept_coverage"]
    )
    out["oracle_concept_gain_frac"] = (
        out["target_augmented_concept_coverage_frac"]
        - out["observed_concept_coverage_frac"]
    )
    out["oracle_token_gain"] = out["target_augmented_n_tokens"] - out["observed_n_tokens"]
    out["has_any_error_tag"] = out["error_total"] > 0
    out["has_paper_bottleneck_error"] = out["paper_bottleneck_error_count"] > 0
    out["has_unknown_intent_error"] = out["unknown_intent_error_count"] > 0
    return out


def grouped_metric_row(
    work: pd.DataFrame,
    setup: str,
    y: np.ndarray,
    pred: np.ndarray,
    subset: str,
) -> dict[str, float | int | str]:
    groups = work["patient_root"].astype(str).to_numpy()
    r_mean, r_lo, r_hi = bootstrap_ci(y, pred, pearson_safe, groups=groups, n_boot=500, seed=0)
    return {
        "subset": subset,
        "setup": setup,
        **regression_summary(y, pred),
        "r_boot_mean": r_mean,
        "r_boot_lo": r_lo,
        "r_boot_hi": r_hi,
        "n_patients": int(work["patient_root"].nunique()),
    }


def run_wab_models(df: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    observed = [
        "observed_concept_coverage",
        "observed_concept_coverage_frac",
        "observed_concept_density",
        "observed_concept_token_ratio",
        "observed_control_z",
        "observed_control_gap",
        "observed_control_pct",
    ]
    target = [
        "target_augmented_concept_coverage",
        "target_augmented_concept_coverage_frac",
        "target_augmented_concept_density",
        "target_augmented_concept_token_ratio",
        "target_augmented_control_z",
        "target_augmented_control_gap",
        "target_augmented_control_pct",
    ]
    error_profile = [
        "error_rate_100",
        "error_phonological_rate_100",
        "error_semantic_rate_100",
        "error_neologism_rate_100",
        "error_morphological_rate_100",
        "error_dysfluency_rate_100",
        "known_reconstructable_error_rate_100",
        "unknown_intent_error_rate_100",
        "target_annotation_rate_100",
    ]
    verbosity = ["observed_n_tokens", "n_utterances", "mean_utt_tokens"]

    setups = {
        "task_only": ({}, ["task"]),
        "observed_content+task": ({"content": observed}, ["task"]),
        "observed_content+error_profile+task": (
            {"content": observed, "error_profile": error_profile},
            ["task"],
        ),
        "target_augmented_content+task": ({"content": target}, ["task"]),
        "target_augmented_content+error_profile+task": (
            {"content": target, "error_profile": error_profile},
            ["task"],
        ),
        "verbosity+task": ({"verbosity": verbosity}, ["task"]),
        "error_profile+task": ({"error_profile": error_profile}, ["task"]),
    }

    base = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy()
    q75 = float(base["paper_bottleneck_error_rate_100"].quantile(0.75))
    subsets = {
        "all_noncontrol_wab": base,
        "any_error_tag": base[base["error_total"] > 0],
        "high_paper_bottleneck_error_rate_q75": base[
            base["paper_bottleneck_error_rate_100"] >= q75
        ],
        "unknown_intent_error": base[base["unknown_intent_error_count"] > 0],
    }

    rows = []
    for subset_name, sub in subsets.items():
        sub = sub.dropna(subset=["patient_root"]).reset_index(drop=True)
        if len(sub) < 80 or sub["patient_root"].nunique() < 20:
            continue
        for setup, (blocks, cats) in setups.items():
            keep_blocks = {
                name: [col for col in cols if col in sub.columns]
                for name, cols in blocks.items()
            }
            keep_blocks = {name: cols for name, cols in keep_blocks.items() if cols}
            if not keep_blocks and not cats:
                continue
            y, pred = cross_val_predict_regressor(
                sub,
                "wab_aq",
                keep_blocks,
                categorical_cols=cats,
                group_col="patient_root",
                cv_mode="group",
                n_splits=cv_folds,
            )
            rows.append(grouped_metric_row(sub, setup, y, pred, subset_name))
    return pd.DataFrame(rows)


def summarize_errors(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pwa = df[~df["is_control"].astype(bool)].copy()
    subtype = (
        pwa.groupby("subtype", dropna=False)
        .agg(
            n_segments=("subtype", "size"),
            n_patients=("patient_root", "nunique"),
            mean_wab_aq=("wab_aq", "mean"),
            mean_error_rate_100=("error_rate_100", "mean"),
            mean_paper_bottleneck_rate_100=("paper_bottleneck_error_rate_100", "mean"),
            mean_unknown_intent_rate_100=("unknown_intent_error_rate_100", "mean"),
            mean_oracle_gain_frac=("oracle_concept_gain_frac", "mean"),
            pct_segments_with_gain=("oracle_concept_gain", lambda s: float((s > 0).mean())),
        )
        .reset_index()
        .sort_values("mean_error_rate_100", ascending=False)
    )
    task = (
        pwa.groupby("task")
        .agg(
            n_segments=("task", "size"),
            n_patients=("patient_root", "nunique"),
            mean_error_rate_100=("error_rate_100", "mean"),
            mean_paper_bottleneck_rate_100=("paper_bottleneck_error_rate_100", "mean"),
            mean_oracle_gain_frac=("oracle_concept_gain_frac", "mean"),
            pct_segments_with_gain=("oracle_concept_gain", lambda s: float((s > 0).mean())),
        )
        .reset_index()
        .sort_values("mean_oracle_gain_frac", ascending=False)
    )

    rows = []
    signal_cols = [
        "error_rate_100",
        "error_phonological_rate_100",
        "error_semantic_rate_100",
        "error_neologism_rate_100",
        "error_morphological_rate_100",
        "error_dysfluency_rate_100",
        "known_reconstructable_error_rate_100",
        "unknown_intent_error_rate_100",
        "paper_bottleneck_error_rate_100",
        "target_annotation_rate_100",
    ]
    outcomes = [
        "observed_concept_coverage_frac",
        "oracle_concept_gain_frac",
        "target_augmented_concept_coverage_frac",
        "wab_aq",
    ]
    for signal in signal_cols:
        for outcome in outcomes:
            work = pwa[[signal, outcome]].dropna()
            rows.append(
                {
                    "signal": signal,
                    "outcome": outcome,
                    "n": int(len(work)),
                    "r": pearson_safe(work[signal], work[outcome]),
                }
            )
    correlations = pd.DataFrame(rows).sort_values(["outcome", "r"], ascending=[True, False])
    return subtype, task, correlations


def high_risk_examples(df: pd.DataFrame, n: int = 80) -> pd.DataFrame:
    cols = [
        "transcript_id",
        "corpus",
        "participant_id",
        "patient_root",
        "task",
        "subtype",
        "wab_aq",
        "observed_n_tokens",
        "error_total",
        "paper_bottleneck_error_rate_100",
        "unknown_intent_error_count",
        "oracle_concept_gain",
        "oracle_concept_gain_frac",
        "observed_concept_coverage_frac",
        "target_augmented_concept_coverage_frac",
        "raw_task_text",
        "file_path",
    ]
    work = df[df["error_total"] > 0].copy()
    work["risk_score"] = (
        work["unknown_intent_error_count"] * 4.0
        + work["paper_bottleneck_error_rate_100"]
        + work["oracle_concept_gain"].clip(lower=0) * 2.0
    )
    return work.sort_values("risk_score", ascending=False)[cols + ["risk_score"]].head(n)


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
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else str(x))
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(data.loc[i].astype(str).tolist()) + " |" for i in data.index]
    return "\n".join([header, sep] + body)


def write_summary(
    out_dir: Path,
    df: pd.DataFrame,
    subtype: pd.DataFrame,
    task: pd.DataFrame,
    correlations: pd.DataFrame,
    models: pd.DataFrame,
) -> None:
    pwa = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)]
    lines = [
        "# Error-Aware Reconstruction Benchmark",
        "",
        f"- Segments: {len(df)}",
        f"- WAB-labeled non-control segments: {len(pwa)}",
        f"- Patient roots with WAB: {pwa['patient_root'].nunique()}",
        f"- Segments with any CHAT error tag: {int((df['error_total'] > 0).sum())}",
        f"- Segments with positive oracle concept gain: {int((df['oracle_concept_gain'] > 0).sum())}",
        f"- Mean oracle concept gain fraction: {df['oracle_concept_gain_frac'].mean():.3f}",
        "",
        "## Error Rates By Subtype",
        "",
        md_table(
            subtype,
            [
                "subtype",
                "n_segments",
                "n_patients",
                "mean_wab_aq",
                "mean_error_rate_100",
                "mean_unknown_intent_rate_100",
                "mean_oracle_gain_frac",
                "pct_segments_with_gain",
            ],
            12,
        ),
        "",
        "## Error Rates By Task",
        "",
        md_table(task, n=12),
        "",
        "## Best WAB Models",
        "",
    ]
    if not models.empty:
        best = models.sort_values(["subset", "r"], ascending=[True, False]).groupby("subset").head(4)
        lines.append(
            md_table(
                best,
                ["subset", "setup", "n", "n_patients", "mae", "r", "r_boot_lo", "r_boot_hi"],
            )
        )
    else:
        lines.append("No WAB models were run.")

    lines.extend(
        [
            "",
            "## Signals Most Associated With Oracle Concept Gain",
            "",
            md_table(
                correlations[correlations["outcome"].eq("oracle_concept_gain_frac")],
                ["signal", "outcome", "n", "r"],
                10,
            ),
            "",
            "## Interpretation",
            "",
            "CHAT target annotations act as an oracle reconstruction layer. If target-augmented content "
            "substantially improves event-concept coverage or WAB prediction in high-error segments, "
            "LLM reconstruction is worth testing as an assistive layer. If it does not, stronger LLMs may "
            "still help communication, but they should not replace raw discourse measurement.",
            "",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)

    df = build_error_segments(args)
    df.to_csv(out_dir / "segment_error_features.csv", index=False)

    subtype, task, correlations = summarize_errors(df)
    subtype.to_csv(out_dir / "subtype_error_rates.csv", index=False)
    task.to_csv(out_dir / "task_error_rates.csv", index=False)
    correlations.to_csv(out_dir / "error_signal_correlations.csv", index=False)

    models = run_wab_models(df, args.cv_folds)
    if not models.empty:
        models.sort_values(["subset", "r"], ascending=[True, False]).to_csv(
            out_dir / "wab_model_results.csv",
            index=False,
        )
    else:
        pd.DataFrame().to_csv(out_dir / "wab_model_results.csv", index=False)

    high_risk_examples(df).to_csv(out_dir / "high_risk_reconstruction_examples.csv", index=False)
    write_summary(out_dir, df, subtype, task, correlations, models)

    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
