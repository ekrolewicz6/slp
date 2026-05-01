"""Find matched WAB-AQ examples with different discourse state profiles."""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir  # noqa: E402


STATE_COLS = [
    "content_percentile",
    "risk_percentile",
    "recoverable_percentile",
    "structural_complexity_pct",
    "lexical_access_pct",
    "fluency_disruption_pct",
    "acoustic_atypicality_pct",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--reports",
                   default="outputs/slp_state_report_v2/state_report_v2_rows.csv",
                   type=Path)
    p.add_argument("--output-dir",
                   default="outputs/same_score_different_state_demo",
                   type=Path)
    p.add_argument("--max-wab-diff", type=float, default=2.0)
    p.add_argument("--examples", type=int, default=24)
    return p.parse_args()


def fmt(value: object, digits: int = 2) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if np.isnan(v):
        return "n/a"
    return f"{v:.{digits}f}"


def target_text(raw: object, top_n: int = 3) -> str:
    if not isinstance(raw, str) or not raw:
        return "none"
    try:
        targets = json.loads(raw)
    except json.JSONDecodeError:
        return "none"
    chunks = []
    for target in targets[:top_n]:
        chunks.append(
            f"{target.get('task')}:{target.get('concept')} "
            f"(p={target.get('pred_success')}, zone={target.get('zone_score')})"
        )
    return "; ".join(chunks) if chunks else "none"


def compute_pairs(df: pd.DataFrame, max_wab_diff: float) -> pd.DataFrame:
    rows = []
    use = df[df["wab_aq"].notna()].copy()
    for subtype, group in use.groupby("subtype", dropna=False):
        records = group.to_dict("records")
        for a, b in itertools.combinations(records, 2):
            if a["participant_id"] == b["participant_id"]:
                continue
            wab_diff = abs(float(a["wab_aq"]) - float(b["wab_aq"]))
            if wab_diff > max_wab_diff:
                continue
            values_a = np.array([
                float(a[c]) if pd.notna(a.get(c)) else np.nan
                for c in STATE_COLS
            ])
            values_b = np.array([
                float(b[c]) if pd.notna(b.get(c)) else np.nan
                for c in STATE_COLS
            ])
            mask = np.isfinite(values_a) & np.isfinite(values_b)
            if mask.sum() < 4:
                continue
            diffs = np.abs(values_a[mask] - values_b[mask])
            axis_max = float(diffs.max())
            axis_mean = float(diffs.mean())
            plan_diff = a.get("recommended_plan") != b.get("recommended_plan")
            next_probe_diff = a.get("next_probe") != b.get("next_probe")
            acoustic_contrast = abs(
                (float(a["acoustic_atypicality_pct"]) if pd.notna(a.get("acoustic_atypicality_pct")) else np.nan)
                - (float(b["acoustic_atypicality_pct"]) if pd.notna(b.get("acoustic_atypicality_pct")) else np.nan)
            )
            rows.append({
                "participant_a": a["participant_id"],
                "participant_b": b["participant_id"],
                "subtype": subtype,
                "corpus_a": a.get("corpus"),
                "corpus_b": b.get("corpus"),
                "wab_a": a["wab_aq"],
                "wab_b": b["wab_aq"],
                "wab_diff": wab_diff,
                "axis_max_diff": axis_max,
                "axis_mean_diff": axis_mean,
                "plan_diff": bool(plan_diff),
                "next_probe_diff": bool(next_probe_diff),
                "acoustic_contrast": acoustic_contrast,
                "content_diff": abs(a.get("content_percentile", np.nan) - b.get("content_percentile", np.nan)),
                "risk_diff": abs(a.get("risk_percentile", np.nan) - b.get("risk_percentile", np.nan)),
                "recoverable_diff": abs(a.get("recoverable_percentile", np.nan) - b.get("recoverable_percentile", np.nan)),
                "structure_diff": abs(a.get("structural_complexity_pct", np.nan) - b.get("structural_complexity_pct", np.nan)),
                "lexicon_diff": abs(a.get("lexical_access_pct", np.nan) - b.get("lexical_access_pct", np.nan)),
                "fluency_diff": abs(a.get("fluency_disruption_pct", np.nan) - b.get("fluency_disruption_pct", np.nan)),
                "plan_a": a.get("recommended_plan"),
                "plan_b": b.get("recommended_plan"),
                "next_probe_a": a.get("next_probe"),
                "next_probe_b": b.get("next_probe"),
            })
    return pd.DataFrame(rows)


def case_card(row: pd.Series, reports: pd.DataFrame) -> str:
    a = reports.loc[reports["participant_id"] == row["participant_a"]].iloc[0]
    b = reports.loc[reports["participant_id"] == row["participant_b"]].iloc[0]
    lines = [
        f"## {row['participant_a']} vs {row['participant_b']} | {row['subtype']} | WAB diff {fmt(row['wab_diff'])}",
        "",
        "| field | case A | case B |",
        "| --- | --- | --- |",
        f"| WAB-AQ | {fmt(a.get('wab_aq'), 1)} | {fmt(b.get('wab_aq'), 1)} |",
        f"| Corpus | {a.get('corpus')} | {b.get('corpus')} |",
        f"| Content carried pct | {fmt(a.get('content_percentile'))} | {fmt(b.get('content_percentile'))} |",
        f"| Unknown-intent risk pct | {fmt(a.get('risk_percentile'))} | {fmt(b.get('risk_percentile'))} |",
        f"| Recoverable-error burden pct | {fmt(a.get('recoverable_percentile'))} | {fmt(b.get('recoverable_percentile'))} |",
        f"| Structural complexity pct | {fmt(a.get('structural_complexity_pct'))} | {fmt(b.get('structural_complexity_pct'))} |",
        f"| Lexical access pct | {fmt(a.get('lexical_access_pct'))} | {fmt(b.get('lexical_access_pct'))} |",
        f"| Fluency disruption pct | {fmt(a.get('fluency_disruption_pct'))} | {fmt(b.get('fluency_disruption_pct'))} |",
        f"| Acoustic atypicality pct | {fmt(a.get('acoustic_atypicality_pct'))} | {fmt(b.get('acoustic_atypicality_pct'))} |",
        f"| Decision hypothesis | {a.get('recommended_plan')} | {b.get('recommended_plan')} |",
        f"| Next probe | {a.get('next_probe')} | {b.get('next_probe')} |",
        f"| Target candidates | {target_text(a.get('top_event_targets'))} | {target_text(b.get('top_event_targets'))} |",
        f"| Safety flags | {a.get('quality_flags')} | {b.get('quality_flags')} |",
        "",
        "**Interpretation:** Similar WAB-AQ does not imply the same discourse state. "
        "The useful clinical question is whether the differing axes would change "
        "what an SLP probes next.",
        "",
    ]
    return "\n".join(lines)


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No pairs._"
    out = [
        "| " + " | ".join(df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for row in df.itertuples(index=False):
        vals = []
        for value in row:
            if isinstance(value, float):
                vals.append(f"{value:.3f}")
            else:
                vals.append(str(value))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def write_summary(out_dir: Path, pairs: pd.DataFrame, selected: pd.DataFrame, reports: pd.DataFrame) -> None:
    subtype = (
        pairs.groupby("subtype", dropna=False)
        .agg(
            n_pairs=("participant_a", "size"),
            mean_wab_diff=("wab_diff", "mean"),
            mean_axis_max_diff=("axis_max_diff", "mean"),
            pct_plan_diff=("plan_diff", "mean"),
            pct_next_probe_diff=("next_probe_diff", "mean"),
        )
        .reset_index()
        .sort_values("n_pairs", ascending=False)
    )
    subtype.to_csv(out_dir / "summary_by_subtype.csv", index=False)

    lines = [
        "# Same-Score Different-State Demonstration",
        "",
        f"- Candidate same-subtype pairs within WAB-AQ diff threshold: {len(pairs):,}",
        f"- WAB-AQ diff threshold: {pairs['wab_diff'].max():.2f}" if len(pairs) else "- WAB-AQ diff threshold: n/a",
        f"- Selected review examples: {len(selected):,}",
        "",
        "## By Subtype",
        "",
        md_table(subtype),
        "",
        "## Selected Examples",
        "",
    ]
    for _, row in selected.iterrows():
        lines.append(case_card(row, reports))
    lines.extend([
        "## Interpretation",
        "",
        "This demo supports the measurement claim rather than a treatment claim. "
        "Broad WAB-AQ severity can match while content, unknown-intent risk, "
        "recoverability, structure, fluency, acoustics, and next-probe hypotheses "
        "differ. These examples should be reviewed by SLPs before being used as "
        "publication-facing case studies.",
        "",
    ])
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    reports = pd.read_csv(args.reports)
    pairs = compute_pairs(reports, args.max_wab_diff)
    if pairs.empty:
        pairs.to_csv(out_dir / "matched_pairs.csv", index=False)
        (out_dir / "summary.md").write_text("# Same-Score Different-State Demonstration\n\nNo pairs found.\n")
        return
    pairs = pairs.sort_values(
        ["plan_diff", "next_probe_diff", "axis_max_diff", "axis_mean_diff"],
        ascending=[False, False, False, False],
    )
    selected = (
        pairs.groupby("subtype", dropna=False)
        .head(max(2, args.examples // max(pairs["subtype"].nunique(), 1)))
        .head(args.examples)
        .copy()
    )
    pairs.to_csv(out_dir / "matched_pairs.csv", index=False)
    selected.to_csv(out_dir / "selected_examples.csv", index=False)
    write_summary(out_dir, pairs, selected, reports)


if __name__ == "__main__":
    main()
