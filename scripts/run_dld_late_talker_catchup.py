"""Late-talker catch-up analysis using Clinical-Eng/Rescorla.

The Rescorla corpus is the most direct local test of the DLD question:
which late talkers catch up, and which remain behind? This script repairs
path-encoded ages, builds age-matched TD residuals inside the Rescorla corpus,
and summarizes longitudinal change.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, roc_auc_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_dld_state_screening import clinical_label, participant_root  # noqa: E402


GOOD_FEATURES = [
    "mlu_words",
    "mlu_morphemes",
    "ndw",
    "verbs_per_utterance",
    "function_word_ratio",
    "utt_len_mean",
    "utt_len_p50",
    "utt_len_p90",
    "pos_v_frac",
    "pos_det_frac",
    "rel_SUBJ_frac",
    "rel_OBJ_frac",
    "mean_dep_distance",
]

BAD_FEATURES = [
    "single_word_ratio",
    "pause_per_utt",
    "repetition_per_utt",
    "retracing_per_utt",
    "filler_per_utt",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--features-path",
        default="data/features/phase1_windowed_features.parquet",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/dld_late_talker_catchup", type=Path)
    parser.add_argument("--seed", default=0, type=int)
    return parser.parse_args()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def md_table(df: pd.DataFrame, max_rows: int | None = None, digits: int = 3) -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "_No rows._"
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.{digits}f}")
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def repaired_age(transcript_id: str, current_age: float | None) -> float | None:
    if pd.notna(current_age):
        return float(current_age)
    parts = transcript_id.split("/")
    # Clinical-Eng/Rescorla/LT/156/name156
    if len(parts) >= 5 and parts[0] == "Clinical-Eng" and parts[1] == "Rescorla":
        if re.fullmatch(r"\d+", parts[3]):
            return float(parts[3])
        m = re.search(r"(36|48|60|108|156)$", parts[-1])
        if m:
            return float(m.group(1))
    return current_age if current_age is not None else None


def add_metadata(df: pd.DataFrame) -> pd.DataFrame:
    out = df[df["transcript_id"].str.startswith("Clinical-Eng/Rescorla/")].copy()
    out["clinical_label"] = out["transcript_id"].map(clinical_label)
    out = out[out["clinical_label"].isin(["TD", "LateTalker"])].copy()
    out["age_repaired"] = [
        repaired_age(tid, age) for tid, age in zip(out["transcript_id"], out["age_months"])
    ]
    out["participant_root"] = [
        participant_root(tid, label) for tid, label in zip(out["transcript_id"], out["clinical_label"])
    ]
    return out.reset_index(drop=True)


def aggregate_participant_age(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    return (
        df.groupby(["participant_root", "clinical_label", "age_repaired"], as_index=False)
        .agg(
            n_windows=("window_id", "count"),
            n_transcripts=("transcript_id", "nunique"),
            **{c: (c, "mean") for c in feature_cols},
        )
        .sort_values(["participant_root", "age_repaired"])
    )


def residualize_against_td(part_age: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    out = part_age.copy()
    oriented = {}
    for col in feature_cols:
        if col in BAD_FEATURES:
            oriented[col] = -out[col].astype(float)
        else:
            oriented[col] = out[col].astype(float)
    oriented_df = pd.DataFrame(oriented)

    for col in feature_cols:
        out[f"{col}_td_z"] = np.nan
    for age, group in out.groupby("age_repaired"):
        td_idx = group.index[group["clinical_label"].eq("TD")]
        if len(td_idx) < 5:
            continue
        for col in feature_cols:
            td_vals = oriented_df.loc[td_idx, col].replace([np.inf, -np.inf], np.nan).dropna()
            if len(td_vals) < 5:
                continue
            sd = float(td_vals.std(ddof=1))
            if not np.isfinite(sd) or sd <= 1e-9:
                continue
            mu = float(td_vals.mean())
            idx = group.index
            out.loc[idx, f"{col}_td_z"] = (oriented_df.loc[idx, col] - mu) / sd

    z_cols = [f"{c}_td_z" for c in feature_cols if f"{c}_td_z" in out.columns]
    out["rescorla_composite_z"] = out[z_cols].mean(axis=1, skipna=True)
    out["utterance_length_z"] = out[[f"{c}_td_z" for c in ["mlu_words", "mlu_morphemes", "utt_len_mean", "utt_len_p90"] if f"{c}_td_z" in out]].mean(axis=1)
    out["lexical_predicate_z"] = out[[f"{c}_td_z" for c in ["ndw", "verbs_per_utterance", "pos_v_frac"] if f"{c}_td_z" in out]].mean(axis=1)
    out["grammar_argument_z"] = out[[f"{c}_td_z" for c in ["function_word_ratio", "pos_det_frac", "rel_SUBJ_frac", "rel_OBJ_frac"] if f"{c}_td_z" in out]].mean(axis=1)
    out["fluency_repair_z"] = out[[f"{c}_td_z" for c in ["single_word_ratio", "pause_per_utt", "repetition_per_utt", "retracing_per_utt"] if f"{c}_td_z" in out]].mean(axis=1)
    return out


def cross_section_summary(resid: pd.DataFrame) -> pd.DataFrame:
    return (
        resid.groupby(["age_repaired", "clinical_label"])
        .agg(
            n_participants=("participant_root", "nunique"),
            mean_composite_z=("rescorla_composite_z", "mean"),
            median_composite_z=("rescorla_composite_z", "median"),
            mean_utterance_length_z=("utterance_length_z", "mean"),
            mean_lexical_predicate_z=("lexical_predicate_z", "mean"),
            mean_grammar_argument_z=("grammar_argument_z", "mean"),
            mean_fluency_repair_z=("fluency_repair_z", "mean"),
            mean_mlu=("mlu_words", "mean"),
            mean_single_word_ratio=("single_word_ratio", "mean"),
        )
        .reset_index()
        .sort_values(["age_repaired", "clinical_label"])
    )


def trajectory_rows(resid: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pid, group in resid.sort_values("age_repaired").groupby("participant_root"):
        if group["age_repaired"].nunique() < 2:
            continue
        x = group["age_repaired"].to_numpy(dtype=float)
        y = group["rescorla_composite_z"].to_numpy(dtype=float)
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() < 2:
            continue
        slope = float(np.polyfit(x[ok], y[ok], 1)[0])
        first = group.iloc[np.argmin(x)]
        last = group.iloc[np.argmax(x)]
        rows.append(
            {
                "participant_root": pid,
                "clinical_label": group["clinical_label"].iloc[0],
                "n_ages": int(group["age_repaired"].nunique()),
                "age_first": float(first["age_repaired"]),
                "age_last": float(last["age_repaired"]),
                "first_composite_z": float(first["rescorla_composite_z"]),
                "last_composite_z": float(last["rescorla_composite_z"]),
                "delta_composite_z": float(last["rescorla_composite_z"] - first["rescorla_composite_z"]),
                "slope_z_per_month": slope,
                "final_in_td_band": bool(last["rescorla_composite_z"] >= -0.5),
                "persistent_gap": bool(last["rescorla_composite_z"] <= -1.0),
                "first_mlu": float(first["mlu_words"]),
                "last_mlu": float(last["mlu_words"]),
            }
        )
    return pd.DataFrame(rows)


def trajectory_summary(traj: pd.DataFrame) -> pd.DataFrame:
    if traj.empty:
        return traj
    return (
        traj.groupby("clinical_label")
        .agg(
            n_participants=("participant_root", "nunique"),
            median_n_ages=("n_ages", "median"),
            mean_first_z=("first_composite_z", "mean"),
            mean_last_z=("last_composite_z", "mean"),
            mean_delta_z=("delta_composite_z", "mean"),
            mean_slope_z_per_month=("slope_z_per_month", "mean"),
            final_td_band_rate=("final_in_td_band", "mean"),
            persistent_gap_rate=("persistent_gap", "mean"),
        )
        .reset_index()
    )


def early_to_late_prediction(traj: pd.DataFrame, resid: pd.DataFrame, seed: int) -> pd.DataFrame:
    lt = traj[traj["clinical_label"].eq("LateTalker")].copy()
    if len(lt) < 20:
        return pd.DataFrame()
    earliest = (
        resid[resid["participant_root"].isin(lt["participant_root"])]
        .sort_values("age_repaired")
        .groupby("participant_root", as_index=False)
        .first()
    )
    target = lt[["participant_root", "last_composite_z", "final_in_td_band"]]
    data = earliest.merge(target, on="participant_root", how="inner")
    feature_sets = {
        "early_mlu_only": ["mlu_words"],
        "early_composite_only": ["rescorla_composite_z"],
        "early_state_axes": [
            "rescorla_composite_z",
            "utterance_length_z",
            "lexical_predicate_z",
            "grammar_argument_z",
            "fluency_repair_z",
            "mlu_words",
            "single_word_ratio",
        ],
    }
    rows = []
    y = data["last_composite_z"].to_numpy(dtype=float)
    y_bin = data["final_in_td_band"].astype(int).to_numpy()
    n_splits = min(5, len(data))
    if n_splits < 3:
        return pd.DataFrame()
    cv = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for name, cols in feature_sets.items():
        cols = [c for c in cols if c in data.columns]
        if not cols:
            continue
        X = data[cols].replace([np.inf, -np.inf], np.nan).fillna(data[cols].median(numeric_only=True))
        model = Pipeline(
            [
                ("scale", StandardScaler()),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
        pred = cross_val_predict(model, X, y, cv=cv)
        auc = float("nan")
        if len(np.unique(y_bin)) == 2:
            try:
                auc = float(roc_auc_score(y_bin, pred))
            except ValueError:
                auc = float("nan")
        rows.append(
            {
                "feature_set": name,
                "n_late_talkers": int(len(data)),
                "target": "last_composite_z",
                "mae": float(mean_absolute_error(y, pred)),
                "corr": float(np.corrcoef(y, pred)[0, 1]) if len(data) > 2 else float("nan"),
                "auc_for_final_td_band": auc,
            }
        )

        gbm = GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.05, random_state=seed)
        pred_gbm = cross_val_predict(gbm, X, y, cv=cv)
        auc_gbm = float("nan")
        if len(np.unique(y_bin)) == 2:
            try:
                auc_gbm = float(roc_auc_score(y_bin, pred_gbm))
            except ValueError:
                auc_gbm = float("nan")
        rows.append(
            {
                "feature_set": f"{name}_gbm",
                "n_late_talkers": int(len(data)),
                "target": "last_composite_z",
                "mae": float(mean_absolute_error(y, pred_gbm)),
                "corr": float(np.corrcoef(y, pred_gbm)[0, 1]) if len(data) > 2 else float("nan"),
                "auc_for_final_td_band": auc_gbm,
            }
        )
    return pd.DataFrame(rows).sort_values("mae")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    df = pd.read_parquet(args.features_path)
    res = add_metadata(df)
    features = [c for c in GOOD_FEATURES + BAD_FEATURES if c in res.columns]

    audit = pd.DataFrame(
        [
            {
                "rows_before_age_repair": int(len(res)),
                "missing_age_before": int(res["age_months"].isna().sum()),
                "missing_age_after": int(pd.isna(res["age_repaired"]).sum()),
                "transcripts": int(res["transcript_id"].nunique()),
                "participant_roots": int(res["participant_root"].nunique()),
            }
        ]
    )
    res.to_csv(out_dir / "rescorla_windows_age_repaired.csv", index=False)
    audit.to_csv(out_dir / "age_repair_audit.csv", index=False)

    part_age = aggregate_participant_age(res.dropna(subset=["age_repaired"]), features)
    resid = residualize_against_td(part_age, features)
    cross = cross_section_summary(resid)
    traj = trajectory_rows(resid)
    traj_sum = trajectory_summary(traj)
    pred = early_to_late_prediction(traj, resid, args.seed)

    part_age.to_csv(out_dir / "rescorla_participant_age_features.csv", index=False)
    resid.to_csv(out_dir / "rescorla_td_residual_state.csv", index=False)
    cross.to_csv(out_dir / "rescorla_cross_section_summary.csv", index=False)
    traj.to_csv(out_dir / "rescorla_trajectories.csv", index=False)
    traj_sum.to_csv(out_dir / "rescorla_trajectory_summary.csv", index=False)
    pred.to_csv(out_dir / "early_to_late_prediction.csv", index=False)

    lines = [
        "# DLD Late-Talker Catch-Up Summary",
        "",
        "## Age Repair Audit",
        "",
        md_table(audit),
        "",
        "## Cross-Sectional TD-Residual State",
        "",
        "Composite z is relative to same-age Rescorla TD children. Higher is more TD-like for the oriented feature set.",
        "",
        md_table(cross),
        "",
        "## Longitudinal Trajectories",
        "",
        md_table(traj_sum),
        "",
        "## Early-To-Late Prediction",
        "",
        md_table(pred),
        "",
        "## Interpretation",
        "",
        "- This is the local-data version of the highest-value DLD question: which late talkers catch up?",
        "- Same-age TD residualization avoids using the external TD age model beyond its 84-month ceiling.",
        "- The key outcome is whether early state axes predict final TD-band status better than early MLU alone.",
        "- This remains corpus-specific until replicated outside Rescorla or linked to standardized literacy/school outcomes.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print((out_dir / "summary.md").resolve())


if __name__ == "__main__":
    main()
