"""DLD/Clinical-Eng language-state inventory and first-pass experiments.

This script starts the DLD track without pretending the local Clinical-Eng
metadata are cleaner than they are. Labels are recovered from CHILDES path
tokens, participant IDs are reconstructed from corpus-specific filenames, and
all screening metrics are reported with participant-held-out splits.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


META_COLS = {
    "transcript_id",
    "corpus",
    "bundle",
    "child_id",
    "age_months",
    "window_id",
    "window_index",
    "n_chi_utts_in_window",
    "clinical_label",
    "participant_root",
    "screen_label",
    "norm_pred_age",
    "norm_age_gap",
}

INTERPRETABLE_FEATURES = [
    "mlu_words",
    "mlu_morphemes",
    "ndw",
    "verbs_per_utterance",
    "ttr",
    "function_word_ratio",
    "hapax_ratio",
    "utt_len_mean",
    "utt_len_std",
    "utt_len_p50",
    "utt_len_p90",
    "single_word_ratio",
    "pos_n_frac",
    "pos_v_frac",
    "pos_pro_frac",
    "pos_det_frac",
    "pos_prep_frac",
    "rel_SUBJ_frac",
    "rel_OBJ_frac",
    "rel_MOD_frac",
    "mean_dep_distance",
    "repetition_per_utt",
    "retracing_per_utt",
    "pause_per_utt",
    "filler_per_utt",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--features-path",
        default="data/features/phase1_windowed_features.parquet",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/dld_state_screening", type=Path)
    parser.add_argument("--max-external-td-age", default=84.0, type=float)
    parser.add_argument("--seed", default=0, type=int)
    return parser.parse_args()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, obj: object) -> None:
    def convert(value):  # noqa: ANN001
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return float(value)
        if isinstance(value, np.ndarray):
            return value.tolist()
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=convert) + "\n")


def md_table(df: pd.DataFrame, max_rows: int | None = None, float_digits: int = 3) -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "_No rows._"
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(
                lambda x: "" if pd.isna(x) else f"{float(x):.{float_digits}f}"
            )
    cols = list(view.columns)
    rows = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(rows)


def numeric_feature_columns(df: pd.DataFrame) -> list[str]:
    return sorted(
        c
        for c in df.columns
        if c not in META_COLS and pd.api.types.is_numeric_dtype(df[c])
    )


def clinical_label(transcript_id: str) -> str | None:
    parts = transcript_id.split("/")
    if len(parts) < 4 or parts[0] != "Clinical-Eng":
        return None
    tokens = parts[2:-1]
    lower = [t.lower() for t in tokens]

    if any(t == "sli" or t == "li" or "sli" in t for t in lower):
        return "DLD_SLI"
    if any(t == "lt" or t.startswith("lt_") or t.startswith("lt-") for t in lower):
        return "LateTalker"
    if any(
        t == "td"
        or t.startswith("td_")
        or t.startswith("td-")
        or t == "0control"
        or t.endswith("control")
        or "control" in t
        for t in lower
    ):
        return "TD"
    if any(t == "hl" for t in lower):
        return "HL"
    if any(t == "ds" for t in lower):
        return "DS"
    if any(t in {"asd", "as"} for t in lower):
        return "ASD"
    if any("sib" in t for t in lower):
        return "FamilyRisk"
    return None


def _strip_known_age_suffix(base: str, suffixes: tuple[str, ...]) -> str:
    for suffix in sorted(suffixes, key=len, reverse=True):
        if base.endswith(suffix) and len(base) > len(suffix):
            return base[: -len(suffix)]
    return base


def participant_root(transcript_id: str, label: str | None) -> str:
    parts = transcript_id.split("/")
    corpus = parts[1] if len(parts) > 1 else "unknown"
    rel = parts[2:]
    base = rel[-1] if rel else transcript_id
    root = base

    if corpus == "Ambrose":
        root = base.split("_")[0]
    elif corpus == "Rescorla":
        root = _strip_known_age_suffix(base, ("156", "108", "60", "48", "36"))
    elif corpus == "Feldman":
        root = _strip_known_age_suffix(base, ("120", "108", "96", "84", "72", "60", "54", "48"))
    elif corpus == "Conti":
        if len(rel) >= 4 and rel[0] in {"Conti2", "Conti4"}:
            root = rel[-2]
        elif len(rel) >= 3 and rel[0] == "Conti3":
            root = rel[-1]
        else:
            root = re.sub(
                r"^(fatcon|motcon|fatsli|motsli|fatsib|motsib|slisib)",
                "",
                base,
                flags=re.IGNORECASE,
            )
    elif corpus == "Gillam":
        root = re.sub(r"-l$", "", base)
    else:
        root = base.split("_")[0]

    root = re.sub(r"\.[A-Za-z0-9]+$", "", root)
    root = root.strip().lower()
    return f"Clinical-Eng/{corpus}/{label or 'Unknown'}/{root}"


def add_clinical_metadata(df: pd.DataFrame) -> pd.DataFrame:
    out = df[df["bundle"].eq("Clinical-Eng")].copy()
    out["clinical_label"] = out["transcript_id"].map(clinical_label)
    out["participant_root"] = [
        participant_root(tid, lab) for tid, lab in zip(out["transcript_id"], out["clinical_label"])
    ]
    return out.reset_index(drop=True)


def classifier_pipeline(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            (
                "model",
                GradientBoostingClassifier(
                    n_estimators=250,
                    learning_rate=0.04,
                    max_depth=2,
                    subsample=0.9,
                    random_state=seed,
                ),
            ),
        ]
    )


def regressor_pipeline(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            (
                "model",
                GradientBoostingRegressor(
                    n_estimators=300,
                    learning_rate=0.04,
                    max_depth=2,
                    subsample=0.9,
                    random_state=seed,
                ),
            ),
        ]
    )


def grouped_binary_cv(
    df: pd.DataFrame,
    feature_cols: list[str],
    label_col: str,
    positive_label: str,
    group_col: str,
    seed: int,
) -> tuple[dict, pd.DataFrame]:
    work = df.dropna(subset=[label_col, group_col]).copy()
    work = work[work[label_col].isin(["TD", positive_label])].copy()
    work = work.dropna(subset=feature_cols, how="all").copy()
    y = (work[label_col].eq(positive_label)).astype(int).to_numpy()
    groups = work[group_col].astype(str).to_numpy()
    X = work[feature_cols]

    unique_groups = np.unique(groups)
    n_splits = min(5, len(unique_groups))
    if n_splits < 2 or len(np.unique(y)) < 2:
        raise ValueError(f"Not enough groups/classes for {label_col}={positive_label}")

    pred = np.zeros(len(work), dtype=int)
    proba = np.full(len(work), np.nan, dtype=float)
    fold_ids = np.zeros(len(work), dtype=int)
    gkf = GroupKFold(n_splits=n_splits)
    for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups), start=1):
        if len(np.unique(y[train_idx])) < 2:
            majority = int(np.bincount(y[train_idx]).argmax())
            pred[test_idx] = majority
            proba[test_idx] = float(majority)
        else:
            model = classifier_pipeline(seed + fold)
            model.fit(X.iloc[train_idx], y[train_idx])
            pred[test_idx] = model.predict(X.iloc[test_idx])
            if hasattr(model[-1], "predict_proba"):
                proba[test_idx] = model.predict_proba(X.iloc[test_idx])[:, 1]
            else:
                proba[test_idx] = pred[test_idx]
        fold_ids[test_idx] = fold

    auc = float("nan")
    if len(np.unique(y)) == 2 and np.isfinite(proba).all():
        auc = float(roc_auc_score(y, proba))

    pred_df = work[
        ["window_id", "transcript_id", "corpus", "participant_root", "age_months", label_col]
    ].copy()
    pred_df["y_true"] = y
    pred_df["y_pred"] = pred
    pred_df["y_proba"] = proba
    pred_df["fold"] = fold_ids

    participant = (
        pred_df.groupby("participant_root")
        .agg(
            y_true=("y_true", "max"),
            y_proba=("y_proba", "mean"),
            n_windows=("window_id", "count"),
            corpus=("corpus", "first"),
            age_min=("age_months", "min"),
            age_max=("age_months", "max"),
        )
        .reset_index()
    )
    participant["y_pred"] = (participant["y_proba"] >= 0.5).astype(int)

    metrics = {
        "n_windows": int(len(pred_df)),
        "n_participants": int(participant["participant_root"].nunique()),
        "n_positive_windows": int(y.sum()),
        "n_positive_participants": int(participant["y_true"].sum()),
        "window_accuracy": float(accuracy_score(y, pred)),
        "window_balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "window_macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        "window_positive_f1": float(f1_score(y, pred, zero_division=0)),
        "window_auc": auc,
        "participant_accuracy": float(accuracy_score(participant["y_true"], participant["y_pred"])),
        "participant_balanced_accuracy": float(
            balanced_accuracy_score(participant["y_true"], participant["y_pred"])
        ),
        "participant_macro_f1": float(
            f1_score(participant["y_true"], participant["y_pred"], average="macro", zero_division=0)
        ),
        "participant_positive_f1": float(
            f1_score(participant["y_true"], participant["y_pred"], zero_division=0)
        ),
        "participant_auc": float(roc_auc_score(participant["y_true"], participant["y_proba"]))
        if participant["y_true"].nunique() == 2
        else float("nan"),
    }
    return metrics, pred_df


def leave_corpus_out(
    df: pd.DataFrame,
    feature_cols: list[str],
    label_col: str,
    positive_label: str,
    seed: int,
    min_test_per_class: int = 10,
) -> pd.DataFrame:
    work = df[df[label_col].isin(["TD", positive_label])].copy()
    rows = []
    for corpus in sorted(work["corpus"].dropna().unique()):
        test = work[work["corpus"].eq(corpus)].copy()
        train = work[~work["corpus"].eq(corpus)].copy()
        if test[label_col].nunique() < 2 or train[label_col].nunique() < 2:
            continue
        test_counts = test[label_col].value_counts()
        if any(test_counts.get(c, 0) < min_test_per_class for c in ["TD", positive_label]):
            continue
        model = classifier_pipeline(seed)
        y_train = train[label_col].eq(positive_label).astype(int).to_numpy()
        y_test = test[label_col].eq(positive_label).astype(int).to_numpy()
        model.fit(train[feature_cols], y_train)
        pred = model.predict(test[feature_cols])
        proba = model.predict_proba(test[feature_cols])[:, 1]
        rows.append(
            {
                "heldout_corpus": corpus,
                "n_test_windows": int(len(test)),
                "n_test_participants": int(test["participant_root"].nunique()),
                "positive_rate": float(y_test.mean()),
                "accuracy": float(accuracy_score(y_test, pred)),
                "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
                "macro_f1": float(f1_score(y_test, pred, average="macro", zero_division=0)),
                "positive_f1": float(f1_score(y_test, pred, zero_division=0)),
                "auc": float(roc_auc_score(y_test, proba)),
            }
        )
    return pd.DataFrame(rows)


def external_td_age_model(
    full: pd.DataFrame,
    feature_cols: list[str],
    max_age: float,
    seed: int,
) -> tuple[Pipeline, dict, pd.DataFrame]:
    td = full[
        full["bundle"].isin(["Eng-NA", "Eng-UK"])
        & full["age_months"].notna()
        & full["age_months"].gt(0)
        & full["age_months"].le(max_age)
    ].copy()
    td = td.dropna(subset=feature_cols, how="all").copy()

    X = td[feature_cols]
    y = td["age_months"].astype(float).to_numpy()
    groups = td["child_id"].astype(str).to_numpy()
    n_splits = min(5, len(np.unique(groups)))
    pred = np.full(len(td), np.nan)
    gkf = GroupKFold(n_splits=n_splits)
    for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups), start=1):
        model = regressor_pipeline(seed + fold)
        model.fit(X.iloc[train_idx], y[train_idx])
        pred[test_idx] = model.predict(X.iloc[test_idx])

    metrics = {
        "n_td_windows": int(len(td)),
        "n_td_children": int(td["child_id"].nunique()),
        "age_min": float(td["age_months"].min()),
        "age_max": float(td["age_months"].max()),
        "grouped_cv_mae_months": float(mean_absolute_error(y, pred)),
        "grouped_cv_corr": float(np.corrcoef(y, pred)[0, 1]),
    }
    model = regressor_pipeline(seed)
    model.fit(X, y)
    td_pred = td[["window_id", "child_id", "corpus", "age_months"]].copy()
    td_pred["pred_age"] = pred
    return model, metrics, td_pred


def add_normative_gap(clin: pd.DataFrame, model: Pipeline, feature_cols: list[str], max_age: float) -> pd.DataFrame:
    out = clin.copy()
    valid = out["age_months"].notna() & out["age_months"].gt(0) & out["age_months"].le(max_age)
    out["norm_pred_age"] = np.nan
    out.loc[valid, "norm_pred_age"] = model.predict(out.loc[valid, feature_cols])
    out["norm_age_gap"] = out["norm_pred_age"] - out["age_months"]
    return out


def age_gap_summary(clin: pd.DataFrame) -> pd.DataFrame:
    work = clin[clin["norm_age_gap"].notna() & clin["clinical_label"].notna()].copy()
    rows = []
    for label, group in work.groupby("clinical_label"):
        rows.append(
            {
                "clinical_label": label,
                "n_windows": int(len(group)),
                "n_participants": int(group["participant_root"].nunique()),
                "age_mean": float(group["age_months"].mean()),
                "pred_age_mean": float(group["norm_pred_age"].mean()),
                "gap_mean": float(group["norm_age_gap"].mean()),
                "gap_median": float(group["norm_age_gap"].median()),
                "gap_q25": float(group["norm_age_gap"].quantile(0.25)),
                "gap_q75": float(group["norm_age_gap"].quantile(0.75)),
            }
        )
    return pd.DataFrame(rows).sort_values("gap_mean")


def trajectory_summary(clin: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = clin[
        clin["norm_age_gap"].notna()
        & clin["clinical_label"].isin(["TD", "DLD_SLI", "LateTalker"])
    ].copy()
    age_state = (
        work.groupby(["participant_root", "clinical_label", "corpus", "age_months"], as_index=False)
        .agg(norm_age_gap=("norm_age_gap", "mean"), n_windows=("window_id", "count"))
        .sort_values(["participant_root", "age_months"])
    )
    rows = []
    for pid, group in age_state.groupby("participant_root"):
        if group["age_months"].nunique() < 2:
            continue
        x = group["age_months"].to_numpy(dtype=float)
        y = group["norm_age_gap"].to_numpy(dtype=float)
        slope = float(np.polyfit(x, y, deg=1)[0])
        rows.append(
            {
                "participant_root": pid,
                "clinical_label": group["clinical_label"].iloc[0],
                "corpus": group["corpus"].iloc[0],
                "n_ages": int(group["age_months"].nunique()),
                "age_min": float(x.min()),
                "age_max": float(x.max()),
                "first_gap": float(y[np.argmin(x)]),
                "last_gap": float(y[np.argmax(x)]),
                "gap_slope_per_month": slope,
                "catching_up": bool(slope > 0),
            }
        )
    traj = pd.DataFrame(rows)
    if traj.empty:
        return traj, pd.DataFrame()
    summary = (
        traj.groupby("clinical_label")
        .agg(
            n_participants=("participant_root", "nunique"),
            median_n_ages=("n_ages", "median"),
            mean_first_gap=("first_gap", "mean"),
            mean_last_gap=("last_gap", "mean"),
            mean_slope_per_month=("gap_slope_per_month", "mean"),
            catchup_rate=("catching_up", "mean"),
        )
        .reset_index()
    )
    return traj, summary


def age_residual_matrix(
    reference_td: pd.DataFrame,
    target: pd.DataFrame,
    features: list[str],
) -> pd.DataFrame:
    features = [f for f in features if f in reference_td.columns and f in target.columns]
    ref = reference_td.dropna(subset=["age_months"]).copy()
    out = pd.DataFrame(index=target.index)
    x_ref = ref[["age_months"]].to_numpy(dtype=float)
    x_target = target[["age_months"]].to_numpy(dtype=float)
    for feature in features:
        y_ref = ref[feature].astype(float).to_numpy()
        ok = np.isfinite(y_ref) & np.isfinite(x_ref[:, 0])
        if ok.sum() < 20:
            continue
        pipe = Pipeline(
            [
                ("poly", PolynomialFeatures(degree=3, include_bias=False)),
                ("scale", StandardScaler()),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
        pipe.fit(x_ref[ok], y_ref[ok])
        ref_resid = y_ref[ok] - pipe.predict(x_ref[ok])
        scale = float(np.nanstd(ref_resid, ddof=1))
        if not np.isfinite(scale) or scale <= 1e-9:
            continue
        out[feature] = (target[feature].astype(float).to_numpy() - pipe.predict(x_target)) / scale
    return out


def dld_cluster_profiles(clin: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    labelled = clin[
        clin["clinical_label"].isin(["TD", "DLD_SLI"])
        & clin["age_months"].notna()
        & clin["age_months"].le(84)
    ].copy()
    td = labelled[labelled["clinical_label"].eq("TD")]
    dld = labelled[labelled["clinical_label"].eq("DLD_SLI")]
    resid = age_residual_matrix(td, dld, INTERPRETABLE_FEATURES)
    keep_cols = [c for c in resid.columns if resid[c].notna().mean() > 0.8]
    if len(keep_cols) < 3:
        return pd.DataFrame(), pd.DataFrame()

    dld_resid = pd.concat(
        [dld[["participant_root", "corpus", "age_months"]].reset_index(drop=True), resid[keep_cols].reset_index(drop=True)],
        axis=1,
    )
    part = (
        dld_resid.groupby("participant_root")
        .agg(
            corpus=("corpus", "first"),
            age_mean=("age_months", "mean"),
            n_windows=("age_months", "count"),
            **{c: (c, "mean") for c in keep_cols},
        )
        .reset_index()
    )
    matrix = part[keep_cols].replace([np.inf, -np.inf], np.nan)
    matrix = pd.DataFrame(SimpleImputer(strategy="median").fit_transform(matrix), columns=keep_cols)
    matrix = pd.DataFrame(StandardScaler().fit_transform(matrix), columns=keep_cols)
    k = min(3, len(part))
    if k < 2:
        return pd.DataFrame(), pd.DataFrame()
    km = KMeans(n_clusters=k, random_state=seed, n_init=20)
    part["cluster"] = km.fit_predict(matrix)

    profile_rows = []
    for cluster, group in part.groupby("cluster"):
        means = group[keep_cols].mean().sort_values()
        low = [f"{idx}:{val:.2f}" for idx, val in means.head(6).items()]
        high = [f"{idx}:{val:.2f}" for idx, val in means.tail(6).sort_values(ascending=False).items()]
        profile_rows.append(
            {
                "cluster": int(cluster),
                "n_participants": int(len(group)),
                "mean_age": float(group["age_mean"].mean()),
                "top_low_residual_features": "; ".join(low),
                "top_high_residual_features": "; ".join(high),
                "corpora": ", ".join(sorted(group["corpus"].dropna().unique())),
            }
        )
    return part, pd.DataFrame(profile_rows).sort_values("cluster")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    full = pd.read_parquet(args.features_path)
    clin = add_clinical_metadata(full)
    feature_cols = numeric_feature_columns(full)
    language_features = [c for c in feature_cols if c != "age_months"]

    inventory = {
        "clinical_windows": int(len(clin)),
        "clinical_transcripts": int(clin["transcript_id"].nunique()),
        "clinical_participant_roots": int(clin["participant_root"].nunique()),
        "clinical_corpora": int(clin["corpus"].nunique()),
        "label_counts_windows": dict(Counter(clin["clinical_label"].dropna())),
        "label_counts_participants": dict(
            clin.dropna(subset=["clinical_label"])
            .drop_duplicates("participant_root")["clinical_label"]
            .value_counts()
        ),
        "unlabelled_windows": int(clin["clinical_label"].isna().sum()),
    }
    write_json(out_dir / "inventory.json", inventory)

    corpus_label = (
        clin.dropna(subset=["clinical_label"])
        .groupby(["corpus", "clinical_label"])
        .agg(windows=("window_id", "count"), participants=("participant_root", "nunique"))
        .reset_index()
        .sort_values(["corpus", "clinical_label"])
    )
    corpus_label.to_csv(out_dir / "corpus_label_inventory.csv", index=False)

    age_model, age_metrics, td_age_cv = external_td_age_model(
        full, language_features, args.max_external_td_age, args.seed
    )
    td_age_cv.to_csv(out_dir / "external_td_age_cv_predictions.csv", index=False)
    clin = add_normative_gap(clin, age_model, language_features, args.max_external_td_age)
    clin.to_csv(out_dir / "clinical_with_normative_gap.csv", index=False)
    gap = age_gap_summary(clin)
    gap.to_csv(out_dir / "normative_age_gap_by_label.csv", index=False)

    labelled = clin[clin["clinical_label"].isin(["TD", "DLD_SLI", "LateTalker"])].copy()
    labelled["screen_label"] = labelled["clinical_label"]
    corpus_cols = []
    for corpus in sorted(labelled["corpus"].dropna().unique()):
        col = "corpus_" + re.sub(r"[^A-Za-z0-9]+", "_", corpus).strip("_")
        labelled[col] = labelled["corpus"].eq(corpus).astype(float)
        corpus_cols.append(col)
    labelled_age84 = labelled[labelled["age_months"].notna() & labelled["age_months"].le(84)].copy()

    feature_sets = {
        "age_only": ["age_months"],
        "corpus_age": ["age_months", *corpus_cols],
        "mlu_age": [
            c
            for c in ["age_months", "mlu_words", "mlu_morphemes", "utt_len_mean", "single_word_ratio"]
            if c in labelled.columns
        ],
        "full_language_no_age": language_features,
        "full_language_age": ["age_months", *language_features],
    }
    if "norm_age_gap" in labelled_age84.columns:
        feature_sets["norm_gap_only"] = ["norm_age_gap"]
        feature_sets["norm_gap_mlu"] = [
            c
            for c in ["norm_age_gap", "mlu_words", "mlu_morphemes", "utt_len_mean", "single_word_ratio"]
            if c in labelled_age84.columns
        ]

    screening_rows = []
    all_predictions = []
    tasks = [
        ("DLD_SLI_vs_TD", labelled, "DLD_SLI"),
        ("DLD_SLI_vs_TD_age_le_84", labelled_age84, "DLD_SLI"),
        ("LateTalker_vs_TD_age_le_84", labelled_age84, "LateTalker"),
    ]
    for task_name, task_df, positive in tasks:
        for fs_name, cols in feature_sets.items():
            if any(c not in task_df.columns for c in cols):
                continue
            if fs_name.startswith("norm_gap") and task_df["norm_age_gap"].notna().sum() < 50:
                continue
            task_work = task_df.dropna(subset=cols, how="all")
            try:
                metrics, preds = grouped_binary_cv(
                    task_work, cols, "screen_label", positive, "participant_root", args.seed
                )
            except ValueError:
                continue
            metrics.update({"task": task_name, "positive_label": positive, "feature_set": fs_name})
            screening_rows.append(metrics)
            preds["task"] = task_name
            preds["feature_set"] = fs_name
            all_predictions.append(preds)

    screening = pd.DataFrame(screening_rows)
    screening = screening[
        [
            "task",
            "positive_label",
            "feature_set",
            "n_windows",
            "n_participants",
            "n_positive_windows",
            "n_positive_participants",
            "window_balanced_accuracy",
            "window_macro_f1",
            "window_positive_f1",
            "window_auc",
            "participant_balanced_accuracy",
            "participant_macro_f1",
            "participant_positive_f1",
            "participant_auc",
        ]
    ].sort_values(["task", "participant_macro_f1"], ascending=[True, False])
    screening.to_csv(out_dir / "screening_metrics.csv", index=False)
    if all_predictions:
        pd.concat(all_predictions, ignore_index=True).to_csv(out_dir / "screening_predictions.csv", index=False)

    loco_rows = []
    for fs_name in ["mlu_age", "full_language_age", "norm_gap_mlu"]:
        cols = feature_sets.get(fs_name)
        if not cols:
            continue
        loco = leave_corpus_out(
            labelled_age84.dropna(subset=cols, how="all"),
            cols,
            "screen_label",
            "DLD_SLI",
            args.seed,
        )
        if not loco.empty:
            loco["feature_set"] = fs_name
            loco_rows.append(loco)
    loco_df = pd.concat(loco_rows, ignore_index=True) if loco_rows else pd.DataFrame()
    loco_df.to_csv(out_dir / "leave_corpus_out_dld_vs_td.csv", index=False)

    control_rows = []
    control_base = labelled_age84[
        labelled_age84["screen_label"].isin(["TD", "DLD_SLI"])
    ].copy()
    full_cols = feature_sets["full_language_age"]
    if not control_base.empty:
        rng = np.random.default_rng(args.seed)

        shuffled = control_base.copy()
        part_labels = shuffled.drop_duplicates("participant_root")[
            ["participant_root", "screen_label"]
        ].copy()
        shuffled_labels = rng.permutation(part_labels["screen_label"].to_numpy())
        shuffle_map = dict(zip(part_labels["participant_root"], shuffled_labels))
        shuffled["screen_label"] = shuffled["participant_root"].map(shuffle_map)
        metrics, _ = grouped_binary_cv(
            shuffled, full_cols, "screen_label", "DLD_SLI", "participant_root", args.seed
        )
        metrics.update(
            {
                "control": "participant_label_shuffle",
                "task": "DLD_SLI_vs_TD_age_le_84",
                "feature_set": "full_language_age",
            }
        )
        control_rows.append(metrics)

        random_df = control_base.copy()
        random_cols = []
        for j in range(25):
            col = f"random_feature_{j:02d}"
            random_df[col] = rng.normal(size=len(random_df))
            random_cols.append(col)
        metrics, _ = grouped_binary_cv(
            random_df, random_cols, "screen_label", "DLD_SLI", "participant_root", args.seed
        )
        metrics.update(
            {
                "control": "random_features",
                "task": "DLD_SLI_vs_TD_age_le_84",
                "feature_set": "random_features",
            }
        )
        control_rows.append(metrics)

    controls = pd.DataFrame(control_rows)
    if not controls.empty:
        controls = controls[
            [
                "control",
                "task",
                "feature_set",
                "n_windows",
                "n_participants",
                "window_balanced_accuracy",
                "window_macro_f1",
                "window_auc",
                "participant_balanced_accuracy",
                "participant_macro_f1",
                "participant_auc",
            ]
        ]
    controls.to_csv(out_dir / "negative_controls.csv", index=False)

    traj, traj_summary = trajectory_summary(clin)
    traj.to_csv(out_dir / "normative_gap_trajectories.csv", index=False)
    traj_summary.to_csv(out_dir / "trajectory_summary.csv", index=False)

    clusters, profiles = dld_cluster_profiles(clin, args.seed)
    clusters.to_csv(out_dir / "dld_age_residual_clusters.csv", index=False)
    profiles.to_csv(out_dir / "dld_cluster_profiles.csv", index=False)

    summary_lines = [
        "# DLD State Screening Summary",
        "",
        "## Inventory",
        "",
        f"- Clinical-Eng windows: {inventory['clinical_windows']}",
        f"- Reconstructed participant roots: {inventory['clinical_participant_roots']}",
        f"- Corpora: {inventory['clinical_corpora']}",
        f"- Window label counts: {inventory['label_counts_windows']}",
        f"- Participant label counts: {inventory['label_counts_participants']}",
        "",
        "## External TD Normative Age Model",
        "",
        md_table(pd.DataFrame([age_metrics])),
        "",
        "## Normative Language-Age Gap By Label",
        "",
        md_table(gap),
        "",
        "Negative gap means the external TD model thinks the speech looks younger than chronological age.",
        "",
        "## Participant-Held-Out Screening",
        "",
        md_table(screening),
        "",
        "## Leave-Corpus-Out DLD/SLI Versus TD",
        "",
        md_table(loco_df),
        "",
        "## Negative Controls",
        "",
        md_table(controls),
        "",
        "## Catch-Up Trajectories",
        "",
        md_table(traj_summary),
        "",
        "## DLD Age-Residual Clusters",
        "",
        md_table(profiles),
        "",
        "## Interpretation",
        "",
        "- Treat these as first-pass discovery results, not clinical screening claims.",
        "- The key comparison is whether full language state beats age-only and MLU+age under participant-held-out and corpus-held-out tests.",
        "- The language-age gap asks whether DLD looks like simple delay; the cluster profiles ask whether DLD contains separable residual mechanisms.",
        "- Older Clinical-Eng children exceed the external TD model's 84-month training ceiling, so age-gap and trajectory claims are currently restricted to ages <=84 months.",
    ]
    (out_dir / "summary.md").write_text("\n".join(summary_lines) + "\n")

    print((out_dir / "summary.md").resolve())


if __name__ == "__main__":
    main()
