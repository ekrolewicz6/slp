"""Build a two-axis aphasia discourse state typology.

Axes:
1. event-content / informativeness;
2. unknown-intent error risk.

This is a practical bridge from measurement to care planning: patients with
low content but low unknown-intent risk may need concept expansion, while
patients with high content but high unknown-intent risk may need repair,
clarification, or AAC support rather than simple content targets.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import (  # noqa: E402
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--session-path",
        default="outputs/error_type_mechanism_map/session_error_state.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/two_axis_state_typology", type=Path)
    parser.add_argument("--cv-folds", default=5, type=int)
    return parser.parse_args()


def zscore(s: pd.Series) -> pd.Series:
    sd = s.std(ddof=0)
    if not np.isfinite(sd) or sd == 0:
        return s * 0
    return (s - s.mean()) / sd


def assign_typology(session: pd.DataFrame) -> pd.DataFrame:
    out = session.copy()
    out = out[out["wab_aq"].notna()].copy()
    out["content_axis"] = out["observed_concept_coverage_frac"]
    out["risk_axis"] = out["unknown_intent_error_rate_100"]
    out["recoverable_axis"] = out["known_reconstructable_error_rate_100"]
    out["content_axis_z"] = zscore(out["content_axis"])
    out["risk_axis_z"] = zscore(out["risk_axis"])
    out["recoverable_axis_z"] = zscore(out["recoverable_axis"])

    content_cut = float(out["content_axis"].median())
    risk_cut = float(out["risk_axis"].median())
    recoverable_cut = float(out["recoverable_axis"].median())

    high_content = out["content_axis"] >= content_cut
    high_risk = out["risk_axis"] > risk_cut
    high_recoverable = out["recoverable_axis"] > recoverable_cut

    out["state_quadrant"] = np.select(
        [
            high_content & ~high_risk,
            high_content & high_risk,
            ~high_content & ~high_risk,
            ~high_content & high_risk,
        ],
        [
            "high_content_low_unknown_risk",
            "high_content_high_unknown_risk",
            "low_content_low_unknown_risk",
            "low_content_high_unknown_risk",
        ],
        default="unclassified",
    )
    out["assistive_priority"] = np.select(
        [
            ~high_content & ~high_risk & high_recoverable,
            ~high_content & ~high_risk & ~high_recoverable,
            high_content & high_risk,
            ~high_content & high_risk,
            high_content & ~high_risk,
        ],
        [
            "known-target repair plus content expansion",
            "event-concept expansion",
            "clarification/repair support",
            "high-support intent clarification",
            "maintenance/generalization",
        ],
        default="review",
    )
    return out


def quadrant_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("state_quadrant")
        .agg(
            n=("participant_id", "size"),
            n_roots=("longitudinal_root", "nunique"),
            mean_wab_aq=("wab_aq", "mean"),
            mean_content=("content_axis", "mean"),
            mean_unknown_risk=("risk_axis", "mean"),
            mean_recoverable=("recoverable_axis", "mean"),
            mean_oracle_gain=("oracle_concept_gain_frac", "mean"),
            pct_broca=("subtype", lambda s: float((s == "Broca").mean())),
            pct_wernicke=("subtype", lambda s: float((s == "Wernicke").mean())),
            pct_anomic=("subtype", lambda s: float((s == "Anomic").mean())),
            pct_conduction=("subtype", lambda s: float((s == "Conduction").mean())),
        )
        .reset_index()
        .sort_values("mean_wab_aq")
    )


def priority_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("assistive_priority")
        .agg(
            n=("participant_id", "size"),
            mean_wab_aq=("wab_aq", "mean"),
            mean_content=("content_axis", "mean"),
            mean_unknown_risk=("risk_axis", "mean"),
            mean_recoverable=("recoverable_axis", "mean"),
            mean_oracle_gain=("oracle_concept_gain_frac", "mean"),
        )
        .reset_index()
        .sort_values("mean_wab_aq")
    )


def models(df: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    work = df.dropna(subset=["longitudinal_root", "wab_aq"]).reset_index(drop=True)
    setups = {
        "content_axis": ({"content": ["content_axis"]}, None),
        "content+risk_axes": ({"axes": ["content_axis", "risk_axis"]}, None),
        "content+risk+recoverable_axes": (
            {"axes": ["content_axis", "risk_axis", "recoverable_axis"]},
            None,
        ),
        "quadrant_only": ({}, ["state_quadrant"]),
        "priority_only": ({}, ["assistive_priority"]),
        "axes+quadrant": (
            {"axes": ["content_axis", "risk_axis", "recoverable_axis"]},
            ["state_quadrant"],
        ),
    }
    rows = []
    for setup, (blocks, cats) in setups.items():
        y, pred = cross_val_predict_regressor(
            work,
            "wab_aq",
            blocks,
            categorical_cols=cats,
            group_col="longitudinal_root",
            cv_mode="group",
            n_splits=cv_folds,
        )
        rows.append({"setup": setup, **regression_summary(y, pred), "n_roots": work["longitudinal_root"].nunique()})
    return pd.DataFrame(rows).sort_values("r", ascending=False)


def examples(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "state_quadrant",
        "assistive_priority",
        "participant_id",
        "corpus",
        "subtype",
        "wab_aq",
        "content_axis",
        "risk_axis",
        "recoverable_axis",
        "oracle_concept_gain_frac",
        "total_tokens",
        "n_tasks",
    ]
    parts = []
    for _, group in df.groupby("state_quadrant"):
        g = group.copy()
        g["extremeness"] = g["content_axis_z"].abs() + g["risk_axis_z"].abs()
        parts.append(g.sort_values("extremeness", ascending=False).head(10)[cols])
    return pd.concat(parts, ignore_index=True)


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
    data = data.astype(str)
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(row.tolist()) + " |" for _, row in data.iterrows()]
    return "\n".join([header, sep] + body)


def write_summary(out_dir: Path, df: pd.DataFrame, qs: pd.DataFrame, ps: pd.DataFrame, model_rows: pd.DataFrame) -> None:
    axis_corr = pd.DataFrame(
        [
            {"axis": "content", "r_wab_aq": pearson_safe(df["content_axis"], df["wab_aq"])},
            {"axis": "unknown_intent_risk", "r_wab_aq": pearson_safe(df["risk_axis"], df["wab_aq"])},
            {"axis": "known_recoverable", "r_wab_aq": pearson_safe(df["recoverable_axis"], df["wab_aq"])},
            {"axis": "content_vs_unknown_risk", "r_wab_aq": pearson_safe(df["content_axis"], df["risk_axis"])},
        ]
    )
    lines = [
        "# Two-Axis State Typology",
        "",
        f"- Sessions: {len(df)}",
        f"- Longitudinal roots: {df['longitudinal_root'].nunique()}",
        "",
        "## Axis Correlations",
        "",
        md_table(axis_corr),
        "",
        "## Quadrants",
        "",
        md_table(qs),
        "",
        "## Assistive Priorities",
        "",
        md_table(ps),
        "",
        "## WAB Models",
        "",
        md_table(model_rows, ["setup", "n", "n_roots", "mae", "r"]),
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    session = pd.read_csv(args.session_path)
    typed = assign_typology(session)
    qs = quadrant_summary(typed)
    ps = priority_summary(typed)
    model_rows = models(typed, args.cv_folds)
    ex = examples(typed)

    typed.to_csv(out_dir / "session_two_axis_state.csv", index=False)
    qs.to_csv(out_dir / "quadrant_summary.csv", index=False)
    ps.to_csv(out_dir / "assistive_priority_summary.csv", index=False)
    model_rows.to_csv(out_dir / "wab_models.csv", index=False)
    ex.to_csv(out_dir / "state_examples.csv", index=False)
    write_summary(out_dir, typed, qs, ps, model_rows)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
