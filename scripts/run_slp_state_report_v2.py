"""Generate a richer SLP-facing state report prototype.

V1 was useful but too centered on the two-axis content/risk model. V2 adds the
Brian-aligned dimensions: structural complexity, lexicon, fluency/timing,
acoustic coverage, data-quality flags, and explicit next-probe suggestions.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import drop_duplicate_windows, ensure_dir  # noqa: E402


STRUCTURAL_COLS = [
    "mlu_words",
    "mlu_morphemes",
    "utt_len_mean",
    "verbs_per_utterance",
    "pos_unique_tags",
    "unique_head_dep_pairs",
    "mean_dep_distance",
]

LEXICAL_COLS = [
    "ndw",
    "ttr",
    "hapax_ratio",
    "total_words",
    "pos_n_frac",
    "pos_v_frac",
]

FLUENCY_BURDEN_COLS = [
    "single_word_ratio",
    "repetition_per_utt",
    "retracing_per_utt",
    "pause_per_utt",
    "filler_per_utt",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--v1-reports",
                   default="outputs/slp_state_report_prototype/state_report_rows.csv",
                   type=Path)
    p.add_argument("--features",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--acoustic-pattern", default="data/features/acoustic_g*.parquet")
    p.add_argument("--quality-gates",
                   default="outputs/data_quality_gates/feature_table_gates.csv",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/slp_state_report_v2", type=Path)
    p.add_argument("--examples", default=24, type=int)
    return p.parse_args()


def percentile(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, method="average")


def mean_percentile(df: pd.DataFrame, cols: list[str], invert: bool = False) -> pd.Series:
    use = [c for c in cols if c in df.columns]
    if not use:
        return pd.Series(np.nan, index=df.index)
    ranks = pd.concat([percentile(df[c].astype(float)) for c in use], axis=1)
    score = ranks.mean(axis=1)
    return 1 - score if invert else score


def load_feature_state(path: Path) -> tuple[pd.DataFrame, dict]:
    features = pd.read_parquet(path)
    clean, audit = drop_duplicate_windows(features, "window_id")
    agg_cols = sorted(set(STRUCTURAL_COLS + LEXICAL_COLS + FLUENCY_BURDEN_COLS) & set(clean.columns))
    first_cols = [
        c for c in ["subtype", "corpus", "wab_aq", "sex", "age_years"]
        if c in clean.columns
    ]
    agg = {c: "mean" for c in agg_cols}
    agg.update({c: "first" for c in first_cols})
    agg["window_id"] = "count"
    pat = clean.groupby("participant_id", as_index=False).agg(agg)
    pat = pat.rename(columns={"window_id": "n_clean_windows"})
    pat["structural_complexity_pct"] = mean_percentile(pat, STRUCTURAL_COLS)
    pat["lexical_access_pct"] = mean_percentile(pat, LEXICAL_COLS)
    pat["fluency_disruption_pct"] = mean_percentile(pat, FLUENCY_BURDEN_COLS)
    return pat, audit


def load_acoustic_state(pattern: str) -> pd.DataFrame:
    paths = sorted(glob.glob(pattern))
    if not paths:
        return pd.DataFrame(columns=["participant_id"])
    ac = pd.concat([pd.read_parquet(p) for p in paths], ignore_index=True)
    if "participant_id" not in ac.columns:
        return pd.DataFrame(columns=["participant_id"])
    ac_cols = sorted(c for c in ac.columns if c.startswith("ac_") and pd.api.types.is_numeric_dtype(ac[c]))
    if not ac_cols:
        return pd.DataFrame(columns=["participant_id"])
    pat = ac.groupby("participant_id", as_index=False).agg(
        {**{c: "mean" for c in ac_cols}, "window_id": "count"}
    ).rename(columns={"window_id": "n_acoustic_windows"})

    values = pat[ac_cols].astype(float)
    med = values.median(axis=0)
    mad = (values - med).abs().median(axis=0).replace(0, np.nan)
    robust_z = ((values - med).abs() / (1.4826 * mad)).replace([np.inf, -np.inf], np.nan)
    pat["acoustic_atypicality_pct"] = percentile(robust_z.mean(axis=1))
    key_cols = ["participant_id", "n_acoustic_windows", "acoustic_atypicality_pct"]
    for col in [
        "ac_speech_rate_mean_mean",
        "ac_f0_cv_mean",
        "ac_hnr_mean_mean",
        "ac_shimmer_local_mean",
    ]:
        if col in pat.columns:
            key_cols.append(col)
    return pat[key_cols]


def level(value: float, high_bad: bool = False) -> str:
    if pd.isna(value):
        return "not available"
    if value < 0.25:
        return "low" if not high_bad else "lower burden"
    if value > 0.75:
        return "high" if not high_bad else "high burden"
    return "mid-range"


def fmt_pct(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:.2f}"


def next_probe(row: pd.Series) -> str:
    probes = []
    if pd.isna(row.get("acoustic_atypicality_pct")):
        probes.append("audio sample with usable time marks")
    if row.get("risk_percentile", 0) >= 0.75:
        probes.append("supported-choice clarification task")
    if row.get("content_percentile", 1) <= 0.25:
        probes.append("task-specific main-concept probe")
    if row.get("structural_complexity_pct", 1) <= 0.25:
        probes.append("sentence repetition")
    if row.get("lexical_access_pct", 1) <= 0.25:
        probes.append("naming or word-retrieval probe")
    if row.get("fluency_disruption_pct", 0) >= 0.75:
        probes.append("fluency/acoustic timing sample")
    if not probes:
        probes.append("repeat same task for longitudinal reliability")
    return "; ".join(dict.fromkeys(probes))


def quality_flags(row: pd.Series, duplicate_rows: int) -> str:
    flags = []
    if duplicate_rows:
        flags.append("global duplicated-window issue: strict runs drop ambiguous IDs")
    if row.get("n_clean_windows", 0) < 1:
        flags.append("no clean feature window")
    if pd.isna(row.get("acoustic_atypicality_pct")):
        flags.append("no acoustic feature coverage")
    if row.get("n_top_targets", 0) == 0:
        flags.append("no target candidates")
    if not flags:
        flags.append("no major local flag")
    return "; ".join(flags)


def report_card(row: pd.Series) -> str:
    targets = json.loads(row.get("top_event_targets", "[]") or "[]")
    target_text = "; ".join(
        f"{t['task']}:{t['concept']} (p={t['pred_success']}, zone={t['zone_score']})"
        for t in targets[:5]
    ) or "none available"
    acoustic = level(row.get("acoustic_atypicality_pct"), high_bad=True)
    movement = "yes" if row.get("stable_wab_mover_flag", False) else "no"
    return (
        f"## {row['participant_id']} | {row.get('subtype', 'Unknown')} | WAB-AQ {row.get('wab_aq', np.nan):.1f}\n\n"
        f"- Content carried: {level(row.get('content_percentile'))} ({fmt_pct(row.get('content_percentile'))})\n"
        f"- Unknown-intent risk: {level(row.get('risk_percentile'), high_bad=True)} ({fmt_pct(row.get('risk_percentile'))})\n"
        f"- Recoverable-error burden: {level(row.get('recoverable_percentile'), high_bad=True)} ({fmt_pct(row.get('recoverable_percentile'))})\n"
        f"- Structural complexity: {level(row.get('structural_complexity_pct'))} ({fmt_pct(row.get('structural_complexity_pct'))})\n"
        f"- Lexical access proxy: {level(row.get('lexical_access_pct'))} ({fmt_pct(row.get('lexical_access_pct'))})\n"
        f"- Fluency/timing disruption: {level(row.get('fluency_disruption_pct'), high_bad=True)} ({fmt_pct(row.get('fluency_disruption_pct'))})\n"
        f"- Acoustic/prosodic atypicality: {acoustic} ({fmt_pct(row.get('acoustic_atypicality_pct'))})\n"
        f"- Current decision hypothesis: {row.get('recommended_plan', 'clinical review')}\n"
        f"- Target candidates: {target_text}\n"
        f"- Stable-score discourse movement flag: {movement}\n"
        f"- Next probe to reduce uncertainty: {row.get('next_probe', '')}\n"
        f"- Quality/safety flags: {row.get('quality_flags', '')}\n"
    )


def md_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "_No rows._"
    show = df.head(max_rows).copy()
    out = ["| " + " | ".join(show.columns) + " |", "| " + " | ".join(["---"] * len(show.columns)) + " |"]
    for row in show.itertuples(index=False):
        vals = []
        for value in row:
            if isinstance(value, float):
                vals.append(f"{value:.3f}")
            else:
                vals.append(str(value))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    v1 = pd.read_csv(args.v1_reports)
    features, feature_audit = load_feature_state(args.features)
    acoustics = load_acoustic_state(args.acoustic_pattern)

    reports = v1.merge(features, on="participant_id", how="left", suffixes=("", "_features"))
    reports = reports.merge(acoustics, on="participant_id", how="left")
    duplicate_rows = int(feature_audit.get("duplicate_rows_dropped", 0))
    reports["quality_flags"] = reports.apply(lambda r: quality_flags(r, duplicate_rows), axis=1)
    reports["next_probe"] = reports.apply(next_probe, axis=1)

    dim_cols = [
        "content_percentile",
        "risk_percentile",
        "recoverable_percentile",
        "structural_complexity_pct",
        "lexical_access_pct",
        "fluency_disruption_pct",
        "acoustic_atypicality_pct",
    ]
    coverage = pd.DataFrame(
        [
            {
                "dimension": col,
                "coverage_n": int(reports[col].notna().sum()) if col in reports else 0,
                "coverage_rate": float(reports[col].notna().mean()) if col in reports else 0.0,
            }
            for col in dim_cols
        ]
    )
    plan_by_quality = reports.groupby("recommended_plan", dropna=False).agg(
        n=("participant_id", "size"),
        mean_content=("content_percentile", "mean"),
        mean_risk=("risk_percentile", "mean"),
        mean_complexity=("structural_complexity_pct", "mean"),
        mean_lexicon=("lexical_access_pct", "mean"),
        mean_fluency_disruption=("fluency_disruption_pct", "mean"),
        acoustic_coverage=("acoustic_atypicality_pct", lambda x: x.notna().mean()),
    ).reset_index().sort_values("n", ascending=False)

    examples = reports.sort_values(
        ["stable_wab_mover_flag", "risk_percentile", "content_percentile"],
        ascending=[False, False, True],
    ).head(args.examples)

    reports.to_csv(out_dir / "state_report_v2_rows.csv", index=False)
    coverage.to_csv(out_dir / "dimension_coverage.csv", index=False)
    plan_by_quality.to_csv(out_dir / "plan_dimension_summary.csv", index=False)
    (out_dir / "example_report_cards.md").write_text(
        "# Example SLP State Report V2 Cards\n\n"
        + "\n\n".join(report_card(row) for _, row in examples.iterrows())
        + "\n",
        encoding="utf-8",
    )
    summary = [
        "# SLP State Report V2",
        "",
        f"- Reports generated: {len(reports):,}",
        f"- Clean feature windows excluded because of duplicate `window_id`s: {duplicate_rows:,}",
        f"- Reports with acoustic coverage: {reports['acoustic_atypicality_pct'].notna().sum():,}",
        f"- Reports with stable-WAB movement flag: {reports['stable_wab_mover_flag'].sum():,}",
        "",
        "## Dimension Coverage",
        "",
        md_table(coverage),
        "",
        "## Plan By Dimension Summary",
        "",
        md_table(plan_by_quality.round(3)),
        "",
        "## Interpretation",
        "",
        "V2 reframes the report around SLP-readable state dimensions rather than a "
        "single score or subtype. It still remains an internal research artifact: "
        "decision labels are hypotheses, raw transcript/audio remain the measurement "
        "source of truth, and missing structured tasks or acoustic coverage are "
        "reported as uncertainty rather than hidden.",
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(summary), encoding="utf-8")
    print(out_dir / "summary.md")


if __name__ == "__main__":
    main()
