"""DLD narrative-state proxy analysis.

This is a proxy, not Main Concept Analysis. It uses structural transcript
features in narrative-like Clinical-Eng tasks to ask whether DLD/SLI narrative
samples show lower content/structure state than TD samples after age/task
constraints. True content-state scoring requires prompt-specific rubrics.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_dld_fairness_metadata_audit import parse_task_proxy  # noqa: E402
from scripts.run_dld_state_screening import clinical_label, participant_root  # noqa: E402


GOOD_FEATURES = [
    "mlu_words",
    "mlu_morphemes",
    "ndw",
    "verbs_per_utterance",
    "function_word_ratio",
    "utt_len_mean",
    "utt_len_p90",
    "pos_v_frac",
    "pos_det_frac",
    "pos_prep_frac",
    "rel_SUBJ_frac",
    "rel_OBJ_frac",
    "rel_MOD_frac",
    "mean_dep_distance",
]

BAD_FEATURES = ["single_word_ratio", "repetition_per_utt", "retracing_per_utt", "pause_per_utt"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--features-path",
        default="data/features/phase1_windowed_features.parquet",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/dld_narrative_proxy", type=Path)
    parser.add_argument("--seed", default=0, type=int)
    parser.add_argument("--max-age", default=156.0, type=float)
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


def repaired_age(transcript_id: str, age: float | None) -> float | None:
    if pd.notna(age):
        return float(age)
    parts = transcript_id.split("/")
    if len(parts) > 3 and parts[1] == "Rescorla" and parts[3].isdigit():
        return float(parts[3])
    return age if age is not None else None


def add_metadata(df: pd.DataFrame, max_age: float) -> pd.DataFrame:
    out = df[df["bundle"].eq("Clinical-Eng")].copy()
    out["clinical_label"] = out["transcript_id"].map(clinical_label)
    out["participant_root"] = [
        participant_root(tid, label) for tid, label in zip(out["transcript_id"], out["clinical_label"])
    ]
    out["age_repaired"] = [repaired_age(tid, age) for tid, age in zip(out["transcript_id"], out["age_months"])]
    out["task_proxy"] = [parse_task_proxy(tid, corpus) for tid, corpus in zip(out["transcript_id"], out["corpus"])]
    out = out[
        out["clinical_label"].isin(["TD", "DLD_SLI"])
        & out["age_repaired"].notna()
        & out["age_repaired"].gt(0)
        & out["age_repaired"].le(max_age)
    ].copy()
    narrative_tasks = {"narrative", "narrative_enni", "narrative_gillam", "frog_story"}
    out = out[out["task_proxy"].isin(narrative_tasks)].copy()
    return out.reset_index(drop=True)


def participant_task_table(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    return (
        df.groupby(["participant_root", "clinical_label", "corpus", "task_proxy"], as_index=False)
        .agg(
            age_mean=("age_repaired", "mean"),
            n_windows=("window_id", "count"),
            **{c: (c, "mean") for c in features},
        )
    )


def task_td_residuals(tab: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = tab.copy()
    oriented = {}
    for feature in features:
        oriented[feature] = -out[feature] if feature in BAD_FEATURES else out[feature]
    oriented = pd.DataFrame(oriented)
    for feature in features:
        out[f"{feature}_task_td_z"] = np.nan
    for (corpus, task), group in out.groupby(["corpus", "task_proxy"]):
        td_idx = group.index[group["clinical_label"].eq("TD")]
        if len(td_idx) < 5:
            continue
        for feature in features:
            vals = oriented.loc[td_idx, feature].replace([np.inf, -np.inf], np.nan).dropna()
            if len(vals) < 5:
                continue
            sd = float(vals.std(ddof=1))
            if not np.isfinite(sd) or sd <= 1e-9:
                continue
            mu = float(vals.mean())
            out.loc[group.index, f"{feature}_task_td_z"] = (oriented.loc[group.index, feature] - mu) / sd
    z_cols = [f"{c}_task_td_z" for c in features]
    out["narrative_proxy_z"] = out[z_cols].mean(axis=1, skipna=True)
    out["event_structure_proxy_z"] = out[
        [f"{c}_task_td_z" for c in ["verbs_per_utterance", "rel_SUBJ_frac", "rel_OBJ_frac", "rel_MOD_frac"] if f"{c}_task_td_z" in out]
    ].mean(axis=1, skipna=True)
    out["lexical_elaboration_proxy_z"] = out[
        [f"{c}_task_td_z" for c in ["ndw", "utt_len_p90", "mean_dep_distance"] if f"{c}_task_td_z" in out]
    ].mean(axis=1, skipna=True)
    out["repair_burden_proxy_z"] = out[
        [f"{c}_task_td_z" for c in ["single_word_ratio", "repetition_per_utt", "retracing_per_utt", "pause_per_utt"] if f"{c}_task_td_z" in out]
    ].mean(axis=1, skipna=True)
    return out


def summary_by_task(resid: pd.DataFrame) -> pd.DataFrame:
    return (
        resid.groupby(["corpus", "task_proxy", "clinical_label"])
        .agg(
            n_participants=("participant_root", "nunique"),
            mean_age=("age_mean", "mean"),
            mean_narrative_proxy_z=("narrative_proxy_z", "mean"),
            mean_event_structure_proxy_z=("event_structure_proxy_z", "mean"),
            mean_lexical_elaboration_proxy_z=("lexical_elaboration_proxy_z", "mean"),
            mean_repair_burden_proxy_z=("repair_burden_proxy_z", "mean"),
            mean_mlu=("mlu_words", "mean"),
            mean_ndw=("ndw", "mean"),
        )
        .reset_index()
        .sort_values(["corpus", "task_proxy", "clinical_label"])
    )


def narrative_classifier(resid: pd.DataFrame, seed: int) -> pd.DataFrame:
    feature_cols = [
        "narrative_proxy_z",
        "event_structure_proxy_z",
        "lexical_elaboration_proxy_z",
        "repair_burden_proxy_z",
        "age_mean",
        "mlu_words",
        "ndw",
    ]
    work = resid.dropna(subset=["narrative_proxy_z"]).copy()
    rows = []
    for name, group in [("all_narrative", work), *[(f"{c}_{t}", g) for (c, t), g in work.groupby(["corpus", "task_proxy"])]]:
        if group["clinical_label"].nunique() < 2:
            continue
        if group.groupby("clinical_label")["participant_root"].nunique().min() < 8:
            continue
        X = group[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(group[feature_cols].median(numeric_only=True))
        y = group["clinical_label"].eq("DLD_SLI").astype(int).to_numpy()
        groups = group["participant_root"].to_numpy()
        n_splits = min(5, len(np.unique(groups)))
        if n_splits < 2:
            continue
        cv = GroupKFold(n_splits=n_splits)
        clf = Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    GradientBoostingClassifier(
                        n_estimators=150,
                        max_depth=2,
                        learning_rate=0.05,
                        random_state=seed,
                    ),
                ),
            ]
        )
        pred = cross_val_predict(clf, X, y, groups=groups, cv=cv)
        try:
            proba = cross_val_predict(clf, X, y, groups=groups, cv=cv, method="predict_proba")[:, 1]
            auc = float(roc_auc_score(y, proba))
        except Exception:
            auc = float("nan")
        rows.append(
            {
                "analysis": name,
                "n_participants": int(group["participant_root"].nunique()),
                "n_dld": int(y.sum()),
                "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
                "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
                "positive_f1": float(f1_score(y, pred, zero_division=0)),
                "auc": auc,
            }
        )
    return pd.DataFrame(rows).sort_values("macro_f1", ascending=False) if rows else pd.DataFrame()


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    raw = pd.read_parquet(args.features_path)
    df = add_metadata(raw, args.max_age)
    features = [c for c in GOOD_FEATURES + BAD_FEATURES if c in df.columns]
    tab = participant_task_table(df, features)
    resid = task_td_residuals(tab, features)
    task_summary = summary_by_task(resid)
    clf = narrative_classifier(resid, args.seed)

    df.to_csv(out_dir / "narrative_windows.csv", index=False)
    resid.to_csv(out_dir / "narrative_participant_residuals.csv", index=False)
    task_summary.to_csv(out_dir / "narrative_proxy_by_task.csv", index=False)
    clf.to_csv(out_dir / "narrative_proxy_classifiers.csv", index=False)

    lines = [
        "# DLD Narrative Proxy Summary",
        "",
        f"- Narrative-like windows: {len(df)}",
        f"- Participant-task rows: {len(resid)}",
        "",
        "## Task-Level Proxy State",
        "",
        "Proxy z scores are oriented so higher means more TD-like within the same corpus/task reference.",
        "",
        md_table(task_summary),
        "",
        "## Narrative Proxy Classifiers",
        "",
        md_table(clf),
        "",
        "## Interpretation",
        "",
        "- This is not true content scoring. It is a structural narrative proxy.",
        "- ENNI and Feldman provide the main local narrative signal; Gillam has too few DLD rows in the current feature table.",
        "- The next real step is prompt-specific main-concept rubrics for child narratives, analogous to the AphasiaBank content-state work.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print((out_dir / "summary.md").resolve())


if __name__ == "__main__":
    main()
