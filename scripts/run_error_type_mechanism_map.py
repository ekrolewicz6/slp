"""Map aphasia error types onto content, subtype, and change."""

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

from src.analysis.review_grade import (  # noqa: E402
    classification_summary,
    cross_val_predict_classifier,
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


ERROR_FEATURES = [
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
CONTENT_FEATURES = [
    "observed_concept_coverage_frac",
    "observed_concept_density",
    "observed_concept_token_ratio",
    "oracle_concept_gain_frac",
]
MAIN_SUBTYPES = ["Anomic", "Broca", "Conduction", "Wernicke"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--segments-path",
        default="outputs/error_aware_reconstruction/segment_error_features.csv",
        type=Path,
    )
    parser.add_argument(
        "--pairs-path",
        default="outputs/cross_prompt_longitudinal/consecutive_pairs.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/error_type_mechanism_map", type=Path)
    parser.add_argument("--cv-folds", default=5, type=int)
    return parser.parse_args()


def longitudinal_root(participant_id: str) -> str:
    value = str(participant_id)
    if re.search(r"-\d+$", value):
        return value.rsplit("-", 1)[0]
    return re.sub(r"[A-Za-z]$", "", value)


def aggregate_session(segments: pd.DataFrame) -> pd.DataFrame:
    work = segments[~segments["is_control"].astype(bool)].copy()
    agg = {
        "wab_aq": "first",
        "subtype": "first",
        "corpus": "first",
        "patient_root": "first",
        "age_years": "first",
        "sex": "first",
        "task": "nunique",
        "observed_n_tokens": "sum",
    }
    for col in ERROR_FEATURES + CONTENT_FEATURES:
        if col in work.columns:
            agg[col] = "mean"
    out = work.groupby("participant_id", as_index=False).agg(agg)
    out = out.rename(columns={"task": "n_tasks", "observed_n_tokens": "total_tokens"})
    out["longitudinal_root"] = out["participant_id"].map(longitudinal_root)
    return out


def correlations(session: pd.DataFrame) -> pd.DataFrame:
    outcomes = [
        "wab_aq",
        "observed_concept_coverage_frac",
        "oracle_concept_gain_frac",
    ]
    rows = []
    for signal in ERROR_FEATURES:
        for outcome in outcomes:
            if signal not in session.columns or outcome not in session.columns:
                continue
            work = session[[signal, outcome]].dropna()
            rows.append(
                {
                    "signal": signal,
                    "outcome": outcome,
                    "n": int(len(work)),
                    "r": pearson_safe(work[signal], work[outcome]),
                }
            )
    return pd.DataFrame(rows).sort_values(["outcome", "r"])


def wab_models(session: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    work = session.dropna(subset=["wab_aq", "longitudinal_root"]).reset_index(drop=True)
    setups = {
        "content_only": {"content": CONTENT_FEATURES},
        "error_only": {"error": ERROR_FEATURES},
        "content+error": {"content": CONTENT_FEATURES, "error": ERROR_FEATURES},
        "content+error+verbosity": {
            "content": CONTENT_FEATURES,
            "error": ERROR_FEATURES,
            "verbosity": ["total_tokens", "n_tasks"],
        },
    }
    rows = []
    for setup, blocks in setups.items():
        blocks = {k: [c for c in v if c in work.columns] for k, v in blocks.items()}
        y, pred = cross_val_predict_regressor(
            work,
            "wab_aq",
            blocks,
            group_col="longitudinal_root",
            cv_mode="group",
            n_splits=cv_folds,
        )
        rows.append({"setup": setup, **regression_summary(y, pred), "n_roots": work["longitudinal_root"].nunique()})
    return pd.DataFrame(rows).sort_values("r", ascending=False)


def subtype_models(session: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    work = session[session["subtype"].isin(MAIN_SUBTYPES)].copy().reset_index(drop=True)
    setups = {
        "content_only": {"content": CONTENT_FEATURES},
        "error_only": {"error": ERROR_FEATURES},
        "content+error": {"content": CONTENT_FEATURES, "error": ERROR_FEATURES},
    }
    rows = []
    for setup, blocks in setups.items():
        blocks = {k: [c for c in v if c in work.columns] for k, v in blocks.items()}
        y, pred = cross_val_predict_classifier(
            work,
            "subtype",
            blocks,
            group_col="longitudinal_root",
            cv_mode="group",
            n_splits=cv_folds,
        )
        rows.append({"setup": setup, **classification_summary(y, pred), "n_roots": work["longitudinal_root"].nunique()})
    return pd.DataFrame(rows).sort_values("macro_f1", ascending=False)


def subtype_error_table(session: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ERROR_FEATURES + CONTENT_FEATURES if c in session.columns]
    return (
        session.groupby("subtype", dropna=False)
        .agg(
            n=("participant_id", "size"),
            n_roots=("longitudinal_root", "nunique"),
            mean_wab_aq=("wab_aq", "mean"),
            **{f"mean_{c}": (c, "mean") for c in cols},
        )
        .reset_index()
        .sort_values("mean_error_rate_100", ascending=False)
    )


def longitudinal_error_change(session: pd.DataFrame, pairs_path: Path) -> pd.DataFrame:
    if not pairs_path.exists():
        return pd.DataFrame()
    pairs = pd.read_csv(pairs_path)
    keep = ["participant_id"] + [c for c in ERROR_FEATURES + CONTENT_FEATURES if c in session.columns]
    sess = session[keep].copy()
    from_s = sess.rename(columns={c: f"from_{c}" for c in keep if c != "participant_id"})
    to_s = sess.rename(columns={c: f"to_{c}" for c in keep if c != "participant_id"})
    out = pairs.merge(from_s, left_on="from_participant_id", right_on="participant_id", how="left")
    out = out.drop(columns=["participant_id"])
    out = out.merge(to_s, left_on="to_participant_id", right_on="participant_id", how="left")
    out = out.drop(columns=["participant_id"])
    for c in ERROR_FEATURES + CONTENT_FEATURES:
        if f"from_{c}" in out.columns and f"to_{c}" in out.columns:
            out[f"delta_{c}"] = out[f"to_{c}"] - out[f"from_{c}"]
    rows = []
    for c in ERROR_FEATURES + CONTENT_FEATURES:
        dc = f"delta_{c}"
        if dc not in out.columns:
            continue
        rows.append(
            {
                "delta_signal": dc,
                "n": int(out[[dc, "delta_wab_aq"]].dropna().shape[0]),
                "r_delta_wab": pearson_safe(out[dc], out["delta_wab_aq"]),
                "r_delta_core_content": pearson_safe(out[dc], out["delta_core_content_mean_z"]),
                "r_delta_coverage": pearson_safe(out[dc], out["delta_coverage_mean"]),
            }
        )
    return pd.DataFrame(rows).sort_values("r_delta_core_content")


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
    body = ["| " + " | ".join(str(x) for x in row.tolist()) + " |" for _, row in data.iterrows()]
    return "\n".join([header, sep] + body)


def write_summary(out_dir: Path, session: pd.DataFrame, corr: pd.DataFrame, wab: pd.DataFrame, subtype: pd.DataFrame, subtype_table: pd.DataFrame, longitudinal: pd.DataFrame) -> None:
    lines = [
        "# Error-Type Mechanism Map",
        "",
        f"- Session rows: {len(session)}",
        f"- Longitudinal roots: {session['longitudinal_root'].nunique()}",
        "",
        "## Error Signals vs Outcomes",
        "",
        md_table(corr[corr["outcome"].eq("wab_aq")], ["signal", "n", "r"], 12),
        "",
        "## WAB Models",
        "",
        md_table(wab, ["setup", "n", "n_roots", "mae", "r"]),
        "",
        "## Subtype Models",
        "",
        md_table(subtype, ["setup", "n", "n_roots", "accuracy", "balanced_accuracy", "macro_f1"]),
        "",
        "## Subtype Error Profiles",
        "",
        md_table(
            subtype_table,
            [
                "subtype",
                "n",
                "mean_wab_aq",
                "mean_error_rate_100",
                "mean_error_phonological_rate_100",
                "mean_error_semantic_rate_100",
                "mean_error_neologism_rate_100",
                "mean_unknown_intent_error_rate_100",
                "mean_oracle_concept_gain_frac",
            ],
            12,
        ),
        "",
        "## Longitudinal Error Change Correlations",
        "",
        md_table(longitudinal, ["delta_signal", "n", "r_delta_wab", "r_delta_core_content", "r_delta_coverage"], 15),
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    segments = pd.read_csv(args.segments_path)
    session = aggregate_session(segments)
    corr = correlations(session)
    wab = wab_models(session, args.cv_folds)
    subtype = subtype_models(session, args.cv_folds)
    subtype_table = subtype_error_table(session)
    longitudinal = longitudinal_error_change(session, args.pairs_path)

    session.to_csv(out_dir / "session_error_state.csv", index=False)
    corr.to_csv(out_dir / "error_outcome_correlations.csv", index=False)
    wab.to_csv(out_dir / "wab_models.csv", index=False)
    subtype.to_csv(out_dir / "subtype_models.csv", index=False)
    subtype_table.to_csv(out_dir / "subtype_error_profiles.csv", index=False)
    longitudinal.to_csv(out_dir / "longitudinal_error_change_correlations.csv", index=False)
    write_summary(out_dir, session, corr, wab, subtype, subtype_table, longitudinal)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
