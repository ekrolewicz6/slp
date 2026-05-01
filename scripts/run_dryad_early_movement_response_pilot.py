"""Dryad EMT-SF early-movement response pilot.

This tests the project's current strongest child-language hypothesis in a
randomized treatment dataset: early state movement may be more informative
than static baseline severity.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from scripts.run_dryad_emt_sf_treatment_pilot import (  # noqa: E402
    LANGUAGE_SAMPLE_MEASURES,
    make_wide,
    ols,
    prepare_analysis_table,
    read_long,
    z_composite,
    zscore,
)
from src.analysis.review_grade import ensure_dir  # noqa: E402


FOLLOWUP_EVENTS = ["t33", "t36", "t39"]
OUTCOMES = {
    "t42_grammar_composite_z": "T42 grammar composite",
    "t49_grammar_composite_z": "T49 grammar composite",
    "t49_vocab_composite_z": "T49 vocabulary composite",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--data-dir",
        default="data/external/dryad_emt_sf_dld",
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/dryad_early_movement_response", type=Path)
    return p.parse_args()


def add_state_and_movement(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    baseline_cols = [f"t30_{measure}" for measure in LANGUAGE_SAMPLE_MEASURES if f"t30_{measure}" in out.columns]
    out["baseline_language_sample_state_z"] = z_composite(out, baseline_cols)

    for event in FOLLOWUP_EVENTS:
        delta_cols = []
        for measure in ["lan_c_ndw", "lan_c_verbs_d", "lan_c_subjects_d", "lan_c_clause_utt"]:
            base = f"t30_{measure}"
            follow = f"{event}_{measure}"
            if base not in out.columns or follow not in out.columns:
                continue
            delta_col = f"delta_{event}_{measure}"
            out[delta_col] = out[follow] - out[base]
            delta_cols.append(delta_col)
        out[f"movement_{event}_language_sample_z"] = z_composite(out, delta_cols)
    return out


def fit_model(df: pd.DataFrame, y_col: str, cols: list[str]) -> dict[str, object]:
    work = df[["tx", y_col] + cols].copy()
    for col in cols:
        work[col] = pd.to_numeric(work[col], errors="coerce")
        if work[col].notna().any():
            work[col] = work[col].fillna(work[col].mean(skipna=True))
            work[col] = zscore(work[col])
    work = work.dropna(subset=["tx", y_col])
    X_cols = [np.ones(len(work)), work["tx"].to_numpy(dtype=float)]
    names = ["intercept", "tx"]
    for col in cols:
        X_cols.append(work[col].to_numpy(dtype=float))
        names.append(col)
    fit = ols(work[y_col].to_numpy(dtype=float), np.column_stack(X_cols))
    return {"fit": fit, "names": names, "n": int(fit["n"])}


def coef_row(
    model: dict[str, object],
    term: str,
    label: str,
    outcome_label: str,
    movement_label: str,
    model_name: str,
) -> dict[str, float | str]:
    names = model["names"]
    fit = model["fit"]
    idx = names.index(term)
    return {
        "outcome": outcome_label,
        "movement_window": movement_label,
        "model": model_name,
        "term": label,
        "n": int(fit["n"]),
        "coef": float(fit["beta"][idx]),
        "se": float(fit["se"][idx]),
        "p": float(fit["p"][idx]),
        "ci_lo": float(fit["beta"][idx] - stats.t.ppf(0.975, fit["df"]) * fit["se"][idx]),
        "ci_hi": float(fit["beta"][idx] + stats.t.ppf(0.975, fit["df"]) * fit["se"][idx]),
        "model_r2": float(fit["r2"]),
    }


def treatment_effect_on_movement(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event in FOLLOWUP_EVENTS:
        movement_col = f"movement_{event}_language_sample_z"
        model = fit_model(df, movement_col, ["baseline_language_sample_state_z"])
        rows.append(
            coef_row(
                model,
                "tx",
                "EMT-SF treatment",
                "early language-sample movement",
                event.upper(),
                "movement ~ tx + baseline_state",
            )
        )
    return pd.DataFrame(rows)


def movement_predicts_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event in FOLLOWUP_EVENTS:
        movement_col = f"movement_{event}_language_sample_z"
        for outcome_col, outcome_label in OUTCOMES.items():
            if outcome_col not in df.columns:
                continue
            base_model = fit_model(df, outcome_col, ["baseline_language_sample_state_z"])
            move_model = fit_model(df, outcome_col, ["baseline_language_sample_state_z", movement_col])
            tx_base = coef_row(
                base_model,
                "tx",
                "EMT-SF treatment",
                outcome_label,
                event.upper(),
                "baseline+tx",
            )
            tx_move = coef_row(
                move_model,
                "tx",
                "EMT-SF treatment",
                outcome_label,
                event.upper(),
                "baseline+tx+movement",
            )
            movement = coef_row(
                move_model,
                movement_col,
                "early movement",
                outcome_label,
                event.upper(),
                "baseline+tx+movement",
            )
            movement["r2_gain_vs_baseline_tx"] = movement["model_r2"] - tx_base["model_r2"]
            movement["tx_coef_before_movement"] = tx_base["coef"]
            movement["tx_coef_after_movement"] = tx_move["coef"]
            movement["tx_coef_change_after_movement"] = tx_move["coef"] - tx_base["coef"]
            rows.append(movement)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    long = read_long(args.data_dir)
    df = add_state_and_movement(prepare_analysis_table(make_wide(long)))

    movement_tx = treatment_effect_on_movement(df)
    prediction = movement_predicts_outcomes(df)

    movement_tx.to_csv(out_dir / "movement_treatment_effects.csv", index=False)
    prediction.to_csv(out_dir / "movement_outcome_prediction.csv", index=False)

    movement_view = movement_tx[
        ["movement_window", "n", "coef", "ci_lo", "ci_hi", "p", "model_r2"]
    ].round(3)
    prediction_view = prediction.sort_values("p").head(12)[
        [
            "outcome",
            "movement_window",
            "n",
            "coef",
            "ci_lo",
            "ci_hi",
            "p",
            "r2_gain_vs_baseline_tx",
            "tx_coef_before_movement",
            "tx_coef_after_movement",
        ]
    ].round(3)

    best = prediction.sort_values("p").iloc[0]
    lines = [
        "# Dryad Early-Movement Response Pilot",
        "",
        "This experiment asks whether early language-sample movement predicts later vocabulary/grammar outcomes in the randomized EMT-SF DLD dataset.",
        "",
        "Dataset citation: Grauzer, Jeffrey; Roberts, Megan; Jones, Maranda (2026), *Maximizing outcomes for preschoolers with developmental language disorders* [Dataset], Dryad, https://doi.org/10.5061/dryad.sj3tx96g9. Trial registry context: ClinicalTrials.gov `NCT03782493` lists Megan Y. Roberts, Pamela Hadley, and Ann Kaiser as principal investigators.",
        "",
        "## Does Treatment Move The Early Language-Sample State?",
        "",
        md_table(movement_view),
        "",
        "## Does Early Movement Predict Later Outcomes?",
        "",
        md_table(prediction_view),
        "",
        "## Interpretation",
        "",
        f"The strongest movement predictor is `{best['movement_window']}` movement for `{best['outcome']}`: coefficient {best['coef']:.3f}, p={best['p']:.3f}, with R2 gain {best['r2_gain_vs_baseline_tx']:.3f} beyond baseline state and treatment group.",
        "",
        "The important scientific result is mixed. Early language-sample movement is sometimes predictive of later grammar/vocabulary outcomes, but treatment assignment does not strongly move the aggregate early language-sample state in these simple models. That means this dataset supports the early-movement measurement thesis more than it supports a treatment-mediation claim.",
        "",
        "For the broader project, this is still valuable: it is the first randomized DLD dataset here where repeated state movement can be related to later standardized outcomes. The next-generation dataset should keep this structure but add raw transcripts/audio, session dose, treatment targets, and repeated clinician goals.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
