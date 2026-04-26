"""Robustness battery for the cross-prompt content-state result.

The content-state claim is strong enough that the next risk is false
confidence from corpus composition, subtype confounds, or a brittle prompt
lexicon. This script runs heavier but bounded checks:

* participant-grouped and corpus-grouped CV;
* leave-one-corpus-out transfer for large corpora;
* within-subtype severity prediction;
* core-task leave-one-out ablations;
* shuffled-WAB negative controls within subtype.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import (  # noqa: E402
    bootstrap_ci,
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


CORE_TASKS = ["Cat", "Cinderella", "Sandwich", "Umbrella", "Window"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--state", default="outputs/cross_prompt_state/patient_content_state.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/cross_prompt_robustness", type=Path)
    p.add_argument("--cv-folds", default=5, type=int)
    p.add_argument("--n-permutations", default=100, type=int)
    p.add_argument("--min-corpus-n", default=50, type=int)
    p.add_argument("--seed", default=0, type=int)
    return p.parse_args()


def load_model_df(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy()
    df = df[df["core_n_tasks"] >= 3].reset_index(drop=True)
    df["subtype"] = df["subtype"].fillna("Unknown")
    df["sex"] = df["sex"].fillna("Unknown")
    return df


def feature_sets(df: pd.DataFrame) -> dict[str, tuple[dict[str, list[str]], list[str]]]:
    core_z = [f"z_{t}" for t in CORE_TASKS if f"z_{t}" in df.columns and df[f"z_{t}"].notna().any()]
    all_z = [c for c in df.columns if c.startswith("z_") and df[c].notna().any()]
    coverage = [c for c in df.columns if c.startswith("coverage_") and df[c].notna().any()]
    content_summary = [
        c for c in [
            "content_mean_z",
            "core_content_mean_z",
            "content_min_z",
            "content_max_z",
            "content_sd_z",
            "coverage_mean",
            "core_n_tasks",
        ]
        if c in df.columns
    ]
    verbosity = [c for c in ["tokens_mean", "utts_mean", "meanutt_mean", "n_tasks"] if c in df.columns]
    demographics = [c for c in ["age_years"] if c in df.columns]
    return {
        "content_summary": ({"content": content_summary}, []),
        "core_task_vector": ({"content": core_z}, []),
        "all_task_vector": ({"content": all_z}, []),
        "coverage_vector": ({"content": coverage}, []),
        "verbosity": ({"verbosity": verbosity}, []),
        "content+verbosity": ({"content": content_summary + core_z, "verbosity": verbosity}, []),
        "subtype_only": ({}, ["subtype"]),
        "subtype+verbosity": ({"verbosity": verbosity}, ["subtype"]),
        "subtype+content": ({"content": content_summary + core_z}, ["subtype"]),
        "subtype+content+verbosity": (
            {"content": content_summary + core_z, "verbosity": verbosity},
            ["subtype"],
        ),
        "demo+subtype": ({"demographics": demographics}, ["subtype", "sex"]),
        "demo+subtype+content": (
            {"demographics": demographics, "content": content_summary + core_z},
            ["subtype", "sex"],
        ),
    }


def model_cv_rows(df: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    rows = []
    setups = feature_sets(df)
    for cv_name, group_col in [("participant_grouped", "patient_root"), ("corpus_grouped", "corpus")]:
        for setup, (blocks, cats) in setups.items():
            blocks = {k: [c for c in v if c in df.columns] for k, v in blocks.items()}
            blocks = {k: v for k, v in blocks.items() if v}
            if not blocks and not cats:
                continue
            sub = df.dropna(subset=cats).reset_index(drop=True) if cats else df.copy()
            try:
                y, pred = cross_val_predict_regressor(
                    sub,
                    "wab_aq",
                    blocks,
                    categorical_cols=cats,
                    group_col=group_col,
                    cv_mode="group",
                    n_splits=cv_folds,
                )
                mean, lo, hi = bootstrap_ci(
                    y,
                    pred,
                    pearson_safe,
                    groups=sub[group_col].astype(str).to_numpy(),
                    n_boot=500,
                    seed=0,
                )
                rows.append(
                    {
                        "cv": cv_name,
                        "setup": setup,
                        **regression_summary(y, pred),
                        "r_boot_mean": mean,
                        "r_boot_lo": lo,
                        "r_boot_hi": hi,
                        "n_patients": int(sub["patient_root"].nunique()),
                        "n_corpora": int(sub["corpus"].nunique()),
                    }
                )
            except Exception as exc:
                rows.append({"cv": cv_name, "setup": setup, "error": type(exc).__name__})
    return pd.DataFrame(rows)


def sklearn_model(numeric_cols: list[str], categorical_cols: list[str]) -> Pipeline:
    transformers = []
    if numeric_cols:
        transformers.append(
            (
                "num",
                Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]),
                numeric_cols,
            )
        )
    if categorical_cols:
        transformers.append(
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_cols,
            )
        )
    prep = ColumnTransformer(transformers, remainder="drop", sparse_threshold=0.0)
    model = GradientBoostingRegressor(
        n_estimators=120,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        random_state=0,
    )
    return Pipeline([("prep", prep), ("model", model)])


def summarize_pred(y: np.ndarray, pred: np.ndarray) -> dict[str, float | int]:
    return {
        "n": int(len(y)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(mean_squared_error(y, pred) ** 0.5),
        "r": pearson_safe(y, pred),
    }


def leave_one_corpus_rows(df: pd.DataFrame, min_corpus_n: int) -> pd.DataFrame:
    setups = feature_sets(df)
    selected = {
        "content+verbosity": setups["content+verbosity"],
        "subtype_only": setups["subtype_only"],
        "subtype+content+verbosity": setups["subtype+content+verbosity"],
    }
    rows = []
    counts = df["corpus"].value_counts()
    for held_corpus in counts[counts >= min_corpus_n].index:
        train = df[df["corpus"] != held_corpus].copy()
        test = df[df["corpus"] == held_corpus].copy()
        for setup, (blocks, cats) in selected.items():
            num_cols = [c for cols in blocks.values() for c in cols if c in df.columns]
            if not num_cols and not cats:
                continue
            sub_train = train.dropna(subset=cats).reset_index(drop=True) if cats else train
            sub_test = test.dropna(subset=cats).reset_index(drop=True) if cats else test
            if len(sub_train) < 50 or len(sub_test) < 10:
                continue
            model = sklearn_model(num_cols, cats)
            model.fit(sub_train, sub_train["wab_aq"].astype(float))
            pred = model.predict(sub_test)
            y = sub_test["wab_aq"].astype(float).to_numpy()
            rows.append(
                {
                    "held_corpus": held_corpus,
                    "setup": setup,
                    "n_train": int(len(sub_train)),
                    "n_test": int(len(sub_test)),
                    "test_mean_wab": float(np.mean(y)),
                    **summarize_pred(y, pred),
                }
            )
    return pd.DataFrame(rows)


def within_subtype_rows(df: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    setups = feature_sets(df)
    selected = {
        "content_summary": setups["content_summary"],
        "content+verbosity": setups["content+verbosity"],
        "verbosity": setups["verbosity"],
        "core_task_vector": setups["core_task_vector"],
    }
    rows = []
    for subtype, group in df.groupby("subtype"):
        if len(group) < 50 or group["patient_root"].nunique() < 40:
            continue
        for setup, (blocks, cats) in selected.items():
            try:
                y, pred = cross_val_predict_regressor(
                    group.reset_index(drop=True),
                    "wab_aq",
                    blocks,
                    categorical_cols=cats,
                    group_col="patient_root",
                    cv_mode="group",
                    n_splits=cv_folds,
                )
                rows.append(
                    {
                        "subtype": subtype,
                        "setup": setup,
                        **regression_summary(y, pred),
                        "n_patients": int(group["patient_root"].nunique()),
                    }
                )
            except Exception as exc:
                rows.append({"subtype": subtype, "setup": setup, "error": type(exc).__name__})
    return pd.DataFrame(rows)


def task_ablation_rows(df: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    rows = []
    base_cols = [f"z_{t}" for t in CORE_TASKS if f"z_{t}" in df.columns]
    for drop_task in ["none"] + CORE_TASKS:
        cols = [c for c in base_cols if drop_task == "none" or c != f"z_{drop_task}"]
        if len(cols) < 2:
            continue
        y, pred = cross_val_predict_regressor(
            df,
            "wab_aq",
            {"content": cols},
            group_col="patient_root",
            cv_mode="group",
            n_splits=cv_folds,
        )
        rows.append({"drop_task": drop_task, "features": ",".join(cols), **regression_summary(y, pred)})
    return pd.DataFrame(rows)


def permutation_rows(df: pd.DataFrame, n_permutations: int, cv_folds: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    setups = feature_sets(df)
    selected = {
        "content+verbosity": setups["content+verbosity"],
        "subtype+content+verbosity": setups["subtype+content+verbosity"],
    }
    rows = []
    group_to_idx = {k: v.index.to_numpy() for k, v in df.groupby("subtype")}
    for i in range(n_permutations):
        perm = df.copy()
        perm_y = perm["wab_aq"].to_numpy().copy()
        for idx in group_to_idx.values():
            perm_y[idx] = rng.permutation(perm_y[idx])
        perm["wab_perm"] = perm_y
        for setup, (blocks, cats) in selected.items():
            y, pred = cross_val_predict_regressor(
                perm,
                "wab_perm",
                blocks,
                categorical_cols=cats,
                group_col="patient_root",
                cv_mode="group",
                n_splits=cv_folds,
                seed=i,
            )
            rows.append({"iteration": i, "setup": setup, **regression_summary(y, pred)})
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


def write_summary(
    out_dir: Path,
    cv: pd.DataFrame,
    corpus: pd.DataFrame,
    within: pd.DataFrame,
    ablation: pd.DataFrame,
    perm: pd.DataFrame,
) -> None:
    lines = ["# Cross-Prompt Robustness Summary\n"]
    lines.append("## Main CV Setups\n")
    view = cv[cv["setup"].isin(["content+verbosity", "subtype_only", "subtype+content+verbosity", "verbosity"])]
    lines.append(md_table(view[["cv", "setup", "n", "mae", "r", "r_boot_lo", "r_boot_hi"]].sort_values(["cv", "r"], ascending=[True, False])))
    if not corpus.empty:
        lines.append("\n## Leave-One-Corpus-Out: Content + Verbosity\n")
        view = corpus[corpus["setup"].eq("content+verbosity")].sort_values("r", ascending=False)
        lines.append(md_table(view[["held_corpus", "n_test", "test_mean_wab", "mae", "r"]]))
    if not within.empty:
        lines.append("\n## Within-Subtype Models\n")
        view = within[within["setup"].isin(["content+verbosity", "verbosity"])].sort_values(["subtype", "r"], ascending=[True, False])
        lines.append(md_table(view[["subtype", "setup", "n", "mae", "r"]]))
    if not ablation.empty:
        lines.append("\n## Core-Task Ablation\n")
        lines.append(md_table(ablation[["drop_task", "n", "mae", "r"]].sort_values("r", ascending=False)))
    if not perm.empty:
        lines.append("\n## Shuffled-WAB Negative Control Within Subtype\n")
        summary = perm.groupby("setup", as_index=False).agg(
            n_permutations=("iteration", "nunique"),
            mean_r=("r", "mean"),
            p95_r=("r", lambda s: float(s.quantile(0.95))),
            max_r=("r", "max"),
            mean_mae=("mae", "mean"),
        )
        lines.append(md_table(summary))
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    df = load_model_df(args.state)
    df.to_csv(out_dir / "model_state.csv", index=False)

    cv = model_cv_rows(df, args.cv_folds)
    cv.to_csv(out_dir / "main_cv_results.csv", index=False)

    corpus = leave_one_corpus_rows(df, args.min_corpus_n)
    corpus.to_csv(out_dir / "leave_one_corpus_results.csv", index=False)

    within = within_subtype_rows(df, args.cv_folds)
    within.to_csv(out_dir / "within_subtype_results.csv", index=False)

    ablation = task_ablation_rows(df, args.cv_folds)
    ablation.to_csv(out_dir / "task_ablation_results.csv", index=False)

    perm = permutation_rows(df, args.n_permutations, args.cv_folds, args.seed)
    perm.to_csv(out_dir / "permutation_results.csv", index=False)

    write_summary(out_dir, cv, corpus, within, ablation, perm)
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
