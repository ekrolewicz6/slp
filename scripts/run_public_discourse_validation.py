"""Validate cross-prompt content state against public discourse outcomes.

Downloads from AphasiaBank's discourse resources give us external anchors:
Fergadiotis 2018 CIU/word counts and Cunningham & Haley 2020 WIM/MATTR/WAB
subtests. This script joins those published outcomes to our content-state
features and asks whether the event-content state predicts discourse
informativeness beyond verbosity.
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

from src.analysis.review_grade import (  # noqa: E402
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--state", default="outputs/cross_prompt_state/patient_content_state.csv", type=Path)
    p.add_argument("--discourse-dir", default="data/external/aphasiabank_discourse", type=Path)
    p.add_argument("--output-dir", default="outputs/public_discourse_validation", type=Path)
    p.add_argument("--cv-folds", default=5, type=int)
    return p.parse_args()


def norm_id(value: object) -> str:
    s = str(value).strip().lower()
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def load_state(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy()
    df["join_id"] = df["participant_id"].map(norm_id)
    df["subtype"] = df["subtype"].fillna("Unknown")
    return df


def load_fergadiotis(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = df.rename(columns=lambda c: str(c).strip())
    df["join_id"] = df["ID"].map(norm_id)
    rename = {
        "FSp#CIU": "ferg_free_ciu",
        "FSp#TNW": "ferg_free_tnw",
        "Cin#CIU": "ferg_cinderella_ciu",
        "Cin#TNW": "ferg_cinderella_tnw",
        "Um#CIU": "ferg_umbrella_ciu",
        "Um#TNW": "ferg_umbrella_tnw",
        "Free%": "ferg_free_ciu_pct",
        "Cin%": "ferg_cinderella_ciu_pct",
        "UMBR%": "ferg_umbrella_ciu_pct",
        "BNT": "ferg_bnt",
        "WAB": "ferg_wab_score",
        "WAB ": "ferg_wab_score",
        "VNT": "ferg_vnt",
    }
    df = df.rename(columns=rename)
    for col in [c for c in df.columns if c.startswith("ferg_")]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["source"] = "Fergadiotis2018"
    return df


def load_cunningham(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="CUNNINGHAM & HALEY 2020")
    df = df.rename(columns=lambda c: str(c).strip())
    df["join_id"] = df["PARTICIPANT"].map(norm_id)
    rename = {
        "WORD": "cunn_word_count",
        "WIM": "cunn_wim",
        "MATTR-5": "cunn_mattr5",
        "BNT": "cunn_bnt",
        "WABAQ": "cunn_wab_aq",
        "WABType": "cunn_wab_type",
        "WABInfo": "cunn_wab_info",
        "WABFluency": "cunn_wab_fluency",
        "SPONTScore": "cunn_spont_score",
        "WABAudRec": "cunn_wab_aud_rec",
        "WABSeqComm": "cunn_wab_seq_comm",
        "WABAV": "cunn_wab_av",
        "WABRep": "cunn_wab_rep",
        "WABObjectName": "cunn_wab_object_name",
        "WABWordFluency": "cunn_wab_word_fluency",
        "WABSentenceFluency": "cunn_wab_sentence_fluency",
        "WABResp": "cunn_wab_resp",
        "NAMINGAQ": "cunn_naming_aq",
        "VNT Total": "cunn_vnt_total",
        "Sent. Comp. - Full Total": "cunn_sent_comp_full_total",
    }
    df = df.rename(columns=rename)
    for col in [c for c in df.columns if c.startswith("cunn_") and c != "cunn_wab_type"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["source"] = "CunninghamHaley2020"
    return df


def join_public_outcomes(state: pd.DataFrame, discourse_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ferg = load_fergadiotis(discourse_dir / "fergadiotis_2018.xlsx")
    cunn = load_cunningham(discourse_dir / "cunningham_haley_2020.xlsm")
    ferg_join = state.merge(ferg, on="join_id", how="inner", suffixes=("", "_ferg"))
    cunn_join = state.merge(cunn, on="join_id", how="inner", suffixes=("", "_cunn"))
    public = pd.concat(
        [
            ferg_join.assign(public_source="Fergadiotis2018"),
            cunn_join.assign(public_source="CunninghamHaley2020"),
        ],
        ignore_index=True,
        sort=False,
    )
    return ferg_join, cunn_join, public


def available(cols: list[str], df: pd.DataFrame) -> list[str]:
    return [c for c in cols if c in df.columns and df[c].notna().any()]


def task_features_for_outcome(outcome: str, df: pd.DataFrame) -> list[str]:
    outcome_l = outcome.lower()
    if "cinderella" in outcome_l or "wim" in outcome_l or "mattr" in outcome_l:
        return available(["z_Cinderella", "coverage_Cinderella", "tokens_Cinderella", "meanutt_Cinderella"], df)
    if "umbrella" in outcome_l:
        return available(["z_Umbrella", "coverage_Umbrella", "tokens_Umbrella", "meanutt_Umbrella"], df)
    return available(["core_content_mean_z", "content_mean_z", "coverage_mean"], df)


def model_setups(outcome: str, df: pd.DataFrame) -> dict[str, tuple[dict[str, list[str]], list[str]]]:
    content_summary = available(
        [
            "core_content_mean_z",
            "content_mean_z",
            "coverage_mean",
            "content_min_z",
            "content_max_z",
            "content_sd_z",
        ],
        df,
    )
    core_vector = available([f"z_{t}" for t in ["Cat", "Cinderella", "Sandwich", "Umbrella", "Window"]], df)
    verbosity = available(["tokens_mean", "utts_mean", "meanutt_mean", "n_tasks"], df)
    task_content = [c for c in task_features_for_outcome(outcome, df) if not c.startswith("tokens_") and not c.startswith("meanutt_")]
    task_verb = [c for c in task_features_for_outcome(outcome, df) if c.startswith("tokens_") or c.startswith("meanutt_")]
    return {
        "task_content": ({"task_content": task_content}, []),
        "task_verbosity": ({"task_verbosity": task_verb}, []),
        "content_state": ({"content": content_summary + core_vector}, []),
        "verbosity_state": ({"verbosity": verbosity}, []),
        "content+verbosity": ({"content": content_summary + core_vector, "verbosity": verbosity}, []),
        "task_content+verbosity": ({"task_content": task_content, "task_verbosity": task_verb}, []),
        "subtype_only": ({}, ["subtype"]),
        "subtype+content": ({"content": content_summary + core_vector}, ["subtype"]),
    }


def run_models(df: pd.DataFrame, outcomes: dict[str, str], cv_folds: int) -> pd.DataFrame:
    rows = []
    for outcome, family in outcomes.items():
        if outcome not in df.columns:
            continue
        work = df.dropna(subset=[outcome, "patient_root"]).copy().reset_index(drop=True)
        work[outcome] = pd.to_numeric(work[outcome], errors="coerce")
        work = work.dropna(subset=[outcome]).reset_index(drop=True)
        if len(work) < 30:
            continue
        for setup, (blocks, cats) in model_setups(outcome, work).items():
            blocks = {k: v for k, v in blocks.items() if v}
            if not blocks and not cats:
                continue
            sub = work.dropna(subset=cats).reset_index(drop=True) if cats else work
            if len(sub) < 30 or sub["patient_root"].nunique() < 20:
                continue
            try:
                y, pred = cross_val_predict_regressor(
                    sub,
                    outcome,
                    blocks,
                    categorical_cols=cats,
                    group_col="patient_root",
                    cv_mode="group",
                    n_splits=cv_folds,
                )
                rows.append(
                    {
                        "outcome": outcome,
                        "family": family,
                        "setup": setup,
                        **regression_summary(y, pred),
                        "n_patients": int(sub["patient_root"].nunique()),
                    }
                )
            except Exception as exc:
                rows.append({"outcome": outcome, "family": family, "setup": setup, "error": type(exc).__name__})
    return pd.DataFrame(rows)


def run_correlations(df: pd.DataFrame, outcomes: dict[str, str]) -> pd.DataFrame:
    candidate_features = [
        "core_content_mean_z",
        "content_mean_z",
        "coverage_mean",
        "tokens_mean",
        "meanutt_mean",
        "z_Cinderella",
        "coverage_Cinderella",
        "tokens_Cinderella",
        "z_Umbrella",
        "coverage_Umbrella",
        "tokens_Umbrella",
    ]
    rows = []
    for outcome, family in outcomes.items():
        if outcome not in df.columns:
            continue
        for feat in candidate_features:
            if feat not in df.columns:
                continue
            sub = df[[outcome, feat]].copy()
            sub[outcome] = pd.to_numeric(sub[outcome], errors="coerce")
            sub[feat] = pd.to_numeric(sub[feat], errors="coerce")
            sub = sub.dropna()
            if len(sub) < 20:
                continue
            rows.append(
                {
                    "outcome": outcome,
                    "family": family,
                    "feature": feat,
                    "n": int(len(sub)),
                    "r": pearson_safe(sub[feat], sub[outcome]),
                }
            )
    return pd.DataFrame(rows)


def md_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    data = frame.copy()
    cols = list(data.columns)
    for col in cols:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else str(x))
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = ["| " + " | ".join(data.loc[i, cols].astype(str).tolist()) + " |" for i in data.index]
    return "\n".join([header, sep] + body)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    state = load_state(args.state)
    ferg, cunn, public = join_public_outcomes(state, args.discourse_dir)
    ferg.to_csv(out_dir / "fergadiotis_joined.csv", index=False)
    cunn.to_csv(out_dir / "cunningham_joined.csv", index=False)

    ferg_outcomes = {
        "ferg_free_ciu_pct": "CIU",
        "ferg_cinderella_ciu_pct": "CIU",
        "ferg_umbrella_ciu_pct": "CIU",
        "ferg_bnt": "lexical",
        "ferg_wab_score": "clinical",
        "ferg_vnt": "lexical",
    }
    cunn_outcomes = {
        "cunn_wim": "informativeness",
        "cunn_mattr5": "lexical_diversity",
        "cunn_word_count": "verbosity",
        "cunn_wab_aq": "clinical",
        "cunn_wab_info": "clinical_subtest",
        "cunn_wab_fluency": "clinical_subtest",
        "cunn_spont_score": "clinical_subtest",
        "cunn_wab_seq_comm": "clinical_subtest",
        "cunn_wab_rep": "clinical_subtest",
        "cunn_wab_object_name": "clinical_subtest",
        "cunn_naming_aq": "clinical_subtest",
        "cunn_vnt_total": "lexical",
        "cunn_sent_comp_full_total": "comprehension",
    }

    ferg_models = run_models(ferg, ferg_outcomes, args.cv_folds)
    cunn_models = run_models(cunn, cunn_outcomes, args.cv_folds)
    models = pd.concat([ferg_models, cunn_models], ignore_index=True, sort=False)
    models.to_csv(out_dir / "public_outcome_models.csv", index=False)

    corrs = pd.concat(
        [
            run_correlations(ferg, ferg_outcomes).assign(source="Fergadiotis2018"),
            run_correlations(cunn, cunn_outcomes).assign(source="CunninghamHaley2020"),
        ],
        ignore_index=True,
    )
    corrs.to_csv(out_dir / "public_outcome_correlations.csv", index=False)

    best = models.dropna(subset=["r"]).sort_values(["outcome", "r"], ascending=[True, False])
    best = best.groupby("outcome").head(3)
    lines = ["# Public Discourse Validation Summary\n"]
    lines.append(f"- Fergadiotis overlap: {len(ferg)} rows, {ferg['patient_root'].nunique()} patient roots")
    lines.append(f"- Cunningham/Haley overlap: {len(cunn)} rows, {cunn['patient_root'].nunique()} patient roots")
    lines.append("\n## Best Models Per Public Outcome\n")
    lines.append(md_table(best[["outcome", "family", "setup", "n", "mae", "r"]]))
    lines.append("\n## Direct Correlations With Content Features\n")
    view = corrs[corrs["feature"].isin(["core_content_mean_z", "z_Cinderella", "z_Umbrella", "tokens_mean", "tokens_Cinderella"])]
    view = view.sort_values(["outcome", "r"], ascending=[True, False]).groupby("outcome").head(5)
    lines.append(md_table(view[["source", "outcome", "family", "feature", "n", "r"]]))
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
