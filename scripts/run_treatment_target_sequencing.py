"""Treatment-target sequencing from item-level content state.

This experiment turns the content-state measurement into a care-planning
question: can we predict which specific event concepts a patient will mention
or miss from their broader content ability, and can we identify plausible
"next targets" among missed concepts?

This is not a treatment efficacy test because we do not have therapy response
labels. It is a target-selection validity test.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir  # noqa: E402


CORE_TASKS = ["Cat", "Cinderella", "Sandwich", "Umbrella", "Window"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--segments", default="outputs/cross_prompt_content/task_segments.csv", type=Path)
    p.add_argument("--state", default="outputs/cross_prompt_state/patient_content_state.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/treatment_target_sequencing", type=Path)
    p.add_argument("--cv-folds", default=5, type=int)
    return p.parse_args()


def concept_columns(task: str, df: pd.DataFrame) -> list[str]:
    return sorted(c for c in df.columns if c.startswith(f"observed_{task.lower()}_"))


def concept_name(col: str, task: str) -> str:
    return re.sub(rf"^observed_{re.escape(task.lower())}_", "", col)


def build_item_matrix(segments: pd.DataFrame, state: pd.DataFrame) -> pd.DataFrame:
    seg = segments[
        segments["wab_aq"].notna()
        & ~segments["is_control"].astype(bool)
        & segments["task"].isin(CORE_TASKS)
    ].copy()
    state_cols = ["participant_id", "patient_root", "subtype", "wab_aq", "core_content_mean_z"]
    z_cols = [f"z_{t}" for t in CORE_TASKS]
    state = state[state_cols + z_cols].copy()
    seg = seg.merge(state, on=["participant_id", "patient_root"], how="left", suffixes=("", "_state"))
    rows = []
    for row in seg.itertuples(index=False):
        task = row.task
        cols = concept_columns(task, seg)
        other_z = [
            getattr(row, f"z_{t}")
            for t in CORE_TASKS
            if t != task and hasattr(row, f"z_{t}") and pd.notna(getattr(row, f"z_{t}"))
        ]
        if len(other_z) < 2:
            continue
        ability_excluding_task = float(np.mean(other_z))
        for col in cols:
            hit = getattr(row, col)
            if pd.isna(hit):
                continue
            rows.append(
                {
                    "participant_id": row.participant_id,
                    "patient_root": row.patient_root,
                    "subtype": row.subtype,
                    "task": task,
                    "item_id": f"{task}:{concept_name(col, task)}",
                    "concept": concept_name(col, task),
                    "hit": int(hit),
                    "wab_aq": row.wab_aq,
                    "ability_excluding_task": ability_excluding_task,
                    "core_content_mean_z": row.core_content_mean_z,
                    "task_content_z": getattr(row, f"z_{task}") if hasattr(row, f"z_{task}") else np.nan,
                }
            )
    return pd.DataFrame(rows)


def make_model(numeric: list[str], categorical: list[str]) -> Pipeline:
    transformers = []
    if numeric:
        transformers.append(
            (
                "num",
                Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]),
                numeric,
            )
        )
    if categorical:
        transformers.append(
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical,
            )
        )
    prep = ColumnTransformer(transformers, remainder="drop", sparse_threshold=0.0)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", solver="lbfgs")
    return Pipeline([("prep", prep), ("model", clf)])


def cv_predict(df: pd.DataFrame, numeric: list[str], categorical: list[str], cv_folds: int) -> np.ndarray:
    groups = df["patient_root"].astype(str).to_numpy()
    y = df["hit"].astype(int).to_numpy()
    preds = np.zeros(len(df), dtype=float)
    splitter = GroupKFold(n_splits=min(cv_folds, len(np.unique(groups))))
    for train, test in splitter.split(df, y, groups):
        model = make_model(numeric, categorical)
        model.fit(df.iloc[train], y[train])
        preds[test] = model.predict_proba(df.iloc[test])[:, 1]
    return preds


def metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, float | int]:
    clipped = np.clip(pred, 1e-6, 1 - 1e-6)
    return {
        "n": int(len(y)),
        "positive_rate": float(np.mean(y)),
        "auc": float(roc_auc_score(y, pred)) if len(np.unique(y)) == 2 else float("nan"),
        "average_precision": float(average_precision_score(y, pred)),
        "brier": float(brier_score_loss(y, clipped)),
        "log_loss": float(log_loss(y, clipped)),
        "accuracy_at_0.5": float(accuracy_score(y, pred >= 0.5)),
    }


def run_models(items: pd.DataFrame, cv_folds: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    setups = {
        "item_popularity": ([], ["item_id"]),
        "ability_only": (["ability_excluding_task"], []),
        "ability+task": (["ability_excluding_task"], ["task"]),
        "ability+item": (["ability_excluding_task"], ["item_id"]),
        "ability+item+subtype": (["ability_excluding_task"], ["item_id", "subtype"]),
        "wab+item": (["wab_aq"], ["item_id"]),
    }
    rows = []
    pred_df = items.copy()
    for setup, (numeric, categorical) in setups.items():
        pred = cv_predict(items, numeric, categorical, cv_folds)
        pred_df[f"pred_{setup}"] = pred
        rows.append({"setup": setup, **metrics(items["hit"].to_numpy(), pred)})
    return pd.DataFrame(rows).sort_values("auc", ascending=False), pred_df


def item_difficulty(pred_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for item, group in pred_df.groupby("item_id"):
        rows.append(
            {
                "item_id": item,
                "task": group["task"].iloc[0],
                "concept": group["concept"].iloc[0],
                "n": int(len(group)),
                "hit_rate": float(group["hit"].mean()),
                "mean_pred": float(group["pred_ability+item"].mean()),
                "mean_ability_hit": float(group.loc[group["hit"].eq(1), "ability_excluding_task"].mean()),
                "mean_ability_miss": float(group.loc[group["hit"].eq(0), "ability_excluding_task"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["hit_rate", "task"])


def recommendations(pred_df: pd.DataFrame) -> pd.DataFrame:
    misses = pred_df[pred_df["hit"].eq(0)].copy()
    # "Reachable" means the model thinks the item is not trivially impossible
    # but not already too easy. These are hypotheses for therapy targeting.
    misses["target_zone_score"] = 1.0 - (misses["pred_ability+item"] - 0.45).abs()
    recs = (
        misses[(misses["pred_ability+item"] >= 0.25) & (misses["pred_ability+item"] <= 0.70)]
        .sort_values(["participant_id", "target_zone_score"], ascending=[True, False])
        .groupby("participant_id")
        .head(10)
        .reset_index(drop=True)
    )
    return recs[
        [
            "participant_id",
            "patient_root",
            "subtype",
            "wab_aq",
            "task",
            "concept",
            "item_id",
            "ability_excluding_task",
            "pred_ability+item",
            "target_zone_score",
        ]
    ]


def calibration(pred_df: pd.DataFrame) -> pd.DataFrame:
    out = pred_df.copy()
    out["bin"] = pd.cut(out["pred_ability+item"], bins=np.linspace(0, 1, 11), include_lowest=True)
    return out.groupby("bin", observed=True).agg(
        n=("hit", "size"),
        mean_pred=("pred_ability+item", "mean"),
        observed_hit_rate=("hit", "mean"),
    ).reset_index()


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
    segments = pd.read_csv(args.segments)
    state = pd.read_csv(args.state)
    items = build_item_matrix(segments, state)
    items.to_csv(out_dir / "item_observations.csv", index=False)

    model_results, pred_df = run_models(items, args.cv_folds)
    model_results.to_csv(out_dir / "item_prediction_models.csv", index=False)
    pred_df.to_csv(out_dir / "item_predictions.csv", index=False)

    diff = item_difficulty(pred_df)
    diff.to_csv(out_dir / "item_difficulty.csv", index=False)

    recs = recommendations(pred_df)
    recs.to_csv(out_dir / "target_recommendations.csv", index=False)

    calib = calibration(pred_df)
    calib.to_csv(out_dir / "calibration.csv", index=False)

    lines = ["# Treatment Target Sequencing Summary\n"]
    lines.append(f"- Item observations: {len(items)}")
    lines.append(f"- Participants: {items['participant_id'].nunique()}")
    lines.append(f"- Items/concepts: {items['item_id'].nunique()}")
    lines.append("\n## Item-Hit Prediction Models\n")
    lines.append(md_table(model_results))
    lines.append("\n## Hardest And Easiest Items\n")
    view = pd.concat([diff.head(10), diff.tail(10)], ignore_index=True)
    lines.append(md_table(view[["item_id", "n", "hit_rate", "mean_pred", "mean_ability_hit", "mean_ability_miss"]]))
    lines.append("\n## Calibration For Ability + Item Model\n")
    lines.append(md_table(calib))
    lines.append("\n## Example Reachable Target Recommendations\n")
    lines.append(md_table(recs.head(20)[["participant_id", "subtype", "wab_aq", "task", "concept", "pred_ability+item"]]))
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
