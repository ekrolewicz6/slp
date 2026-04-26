"""Shared utilities for review-grade AphasiaBank / CHILDES experiments.

The older scripts in this repo were intentionally exploratory. These helpers
centralize the stricter choices we want for publication-facing runs:

* drop ambiguous duplicate window IDs before joins;
* use TD-only CHILDES for developmental comparisons;
* fit imputers, scalers, encoders, and PCA inside each CV fold;
* report patient-level / group-level metrics with bootstrap intervals.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
)
from sklearn.model_selection import GroupKFold, KFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


AB_META = {
    "transcript_id",
    "section",
    "corpus",
    "participant_id",
    "patient_root",
    "session_letter",
    "age_years",
    "sex",
    "subtype",
    "wab_aq",
    "is_control",
    "session_date",
    "window_id",
    "window_index",
    "n_chi_utts_in_window",
}

CHI_META = {
    "transcript_id",
    "corpus",
    "child_id",
    "age_months",
    "n_chi_utterances",
    "bundle",
    "window_id",
    "window_index",
    "n_chi_utts_in_window",
}

TD_BUNDLES = {"Eng-NA", "Eng-UK"}
MAIN_SUBTYPES = ["Anomic", "Broca", "Conduction", "Wernicke"]

ACOUSTIC_GROUPS = {
    "timing": [
        "ac_duration_s_mean",
        "ac_duration_s_std",
        "ac_n_tokens_mean",
        "ac_n_tokens_std",
        "ac_speech_rate_mean",
        "ac_speech_rate_std",
        "ac_n_utts_in_window",
    ],
    "pitch": [
        "ac_f0_mean_mean",
        "ac_f0_mean_std",
        "ac_f0_std_mean",
        "ac_f0_std_std",
        "ac_f0_p10_mean",
        "ac_f0_p10_std",
        "ac_f0_p50_mean",
        "ac_f0_p50_std",
        "ac_f0_p90_mean",
        "ac_f0_p90_std",
        "ac_f0_range_mean",
        "ac_f0_range_std",
        "ac_f0_cv_mean",
        "ac_f0_cv_std",
        "ac_voiced_fraction_mean",
        "ac_voiced_fraction_std",
        "ac_n_voiced_utts",
    ],
    "voice_quality": [
        "ac_jitter_local_mean",
        "ac_jitter_local_std",
        "ac_shimmer_local_mean",
        "ac_shimmer_local_std",
        "ac_hnr_mean_mean",
        "ac_hnr_mean_std",
    ],
    "intensity": [
        "ac_intensity_mean_mean",
        "ac_intensity_mean_std",
        "ac_intensity_std_mean",
        "ac_intensity_std_std",
    ],
}


class SafePCA(BaseEstimator, TransformerMixin):
    """PCA with n_components capped at fit time for small folds."""

    def __init__(self, n_components: int = 32, random_state: int = 0):
        self.n_components = n_components
        self.random_state = random_state

    def fit(self, X, y=None):  # noqa: ANN001
        max_components = max(1, min(X.shape[0] - 1, X.shape[1], self.n_components))
        self.model_ = PCA(n_components=max_components, random_state=self.random_state)
        self.model_.fit(X)
        self.n_components_ = max_components
        return self

    def transform(self, X):  # noqa: ANN001
        return self.model_.transform(X)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def numeric_feature_columns(df: pd.DataFrame, meta_cols: set[str]) -> list[str]:
    cols = []
    for col in df.columns:
        if col in meta_cols:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            cols.append(col)
    return sorted(cols)


def drop_duplicate_windows(df: pd.DataFrame, id_col: str = "window_id") -> tuple[pd.DataFrame, dict]:
    """Drop all rows whose window ID is ambiguous.

    Keeping "first" would silently attach embeddings/acoustics to the wrong
    transcript in collision cases, so the conservative review-grade choice is
    to remove all duplicated IDs.
    """

    before = len(df)
    unique_before = int(df[id_col].nunique(dropna=True))
    dup_mask = df[id_col].duplicated(keep=False)
    out = df.loc[~dup_mask].copy().reset_index(drop=True)
    audit = {
        "rows_before": int(before),
        "rows_after": int(len(out)),
        "unique_window_ids_before": unique_before,
        "duplicate_rows_dropped": int(dup_mask.sum()),
        "duplicate_window_ids": int(df.loc[dup_mask, id_col].nunique(dropna=True)),
    }
    if out[id_col].duplicated().any():
        raise AssertionError(f"{id_col} is still duplicated after cleaning")
    return out, audit


def load_ab_windowed(path: Path) -> tuple[pd.DataFrame, dict]:
    df = pd.read_parquet(path)
    df, audit = drop_duplicate_windows(df)
    return df, audit


def load_td_childes(path: Path, max_age_months: float = 84.0) -> tuple[pd.DataFrame, dict]:
    df = pd.read_parquet(path)
    before = len(df)
    if "bundle" in df.columns:
        df = df[df["bundle"].isin(TD_BUNDLES)].copy()
    df = df.dropna(subset=["age_months", "child_id"])
    df = df[(df["age_months"] > 0) & (df["age_months"] <= max_age_months)].copy()
    df, dup_audit = drop_duplicate_windows(df)
    audit = {
        "rows_before": int(before),
        "rows_after_td_filter": int(len(df)),
        "bundles": sorted(df["bundle"].dropna().unique().tolist()) if "bundle" in df else [],
        **{f"childes_{k}": v for k, v in dup_audit.items()},
    }
    return df.reset_index(drop=True), audit


def load_embeddings(path: Path) -> tuple[pd.DataFrame, list[str], dict]:
    df = pd.read_parquet(path)
    emb_cols = sorted(c for c in df.columns if c.startswith("emb"))
    before = len(df)
    if df["window_id"].duplicated().any():
        df = df.groupby("window_id", as_index=False)[emb_cols].mean()
    audit = {
        "embedding_rows_before": int(before),
        "embedding_rows_after": int(len(df)),
        "embedding_cols": int(len(emb_cols)),
    }
    return df, emb_cols, audit


def load_acoustics(pattern: str) -> tuple[pd.DataFrame, list[str], dict]:
    paths = sorted(Path().glob(pattern))
    if not paths:
        return pd.DataFrame({"window_id": []}), [], {"acoustic_files": 0}
    df = pd.concat([pd.read_parquet(p) for p in paths], ignore_index=True)
    ac_cols = sorted(c for c in df.columns if c.startswith("ac_"))
    before = len(df)
    agg = {c: "mean" for c in ac_cols}
    keep_meta = [c for c in ["transcript_id"] if c in df.columns]
    agg.update({c: "first" for c in keep_meta})
    df = df.groupby("window_id", as_index=False).agg(agg)
    audit = {
        "acoustic_files": int(len(paths)),
        "acoustic_rows_before": int(before),
        "acoustic_rows_after": int(len(df)),
        "acoustic_cols": int(len(ac_cols)),
    }
    return df, ac_cols, audit


def artifact_safe_features(
    chi: pd.DataFrame,
    ab: pd.DataFrame,
    common: Iterable[str],
    mode: str = "artifact_safe",
) -> list[str]:
    """Return cross-corpus comparable feature columns.

    `artifact_safe` removes features that are effectively absent in one corpus
    and common in the other. `no_rel` also removes dependency-relation columns.
    `surface_core` keeps a conservative subset that should be least sensitive
    to parser differences.
    """

    common = [c for c in common if c in chi.columns and c in ab.columns]
    asymmetric = []
    for col in common:
        ab_zero = (ab[col].fillna(0) == 0).mean()
        chi_zero = (chi[col].fillna(0) == 0).mean()
        if (ab_zero >= 0.99 and chi_zero <= 0.50) or (
            chi_zero >= 0.99 and ab_zero <= 0.50
        ):
            asymmetric.append(col)
    safe = [c for c in common if c not in asymmetric]
    if mode == "artifact_safe":
        return safe
    if mode == "no_rel":
        return [c for c in safe if not c.startswith("rel_")]
    if mode == "surface_core":
        preferred = {
            "function_word_ratio",
            "hapax_ratio",
            "log_total_tokens",
            "mlu_morphemes",
            "mlu_words",
            "n_utterances",
            "ndw",
            "pos_adj_frac",
            "pos_adv_frac",
            "pos_aux_frac",
            "pos_det_frac",
            "pos_n_frac",
            "pos_part_frac",
            "pos_prep_frac",
            "pos_pro_frac",
            "pos_unique_tags",
            "pos_v_frac",
            "single_word_ratio",
            "total_words",
            "ttr",
            "utt_len_mean",
            "utt_len_p10",
            "utt_len_p50",
            "utt_len_p90",
            "utt_len_std",
            "verbs_per_utterance",
        }
        return [c for c in safe if c in preferred]
    raise ValueError(f"Unknown safe feature mode: {mode}")


def aggregate_rows(
    df: pd.DataFrame,
    id_col: str,
    feature_cols: list[str],
    first_cols: list[str],
) -> pd.DataFrame:
    agg: dict[str, str] = {c: "mean" for c in feature_cols if c in df.columns}
    agg.update({c: "first" for c in first_cols if c in df.columns})
    return df.groupby(id_col, as_index=False).agg(agg)


def add_patient_root(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["patient_root"] = out["participant_id"].astype(str).str.replace(
        r"[A-Za-z]$", "", regex=True
    )
    out["session_letter"] = out["participant_id"].astype(str).str.extract(
        r"([A-Za-z])$"
    )[0]
    return out


def _numeric_pipe() -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )


def _embedding_pipe(emb_pca_d: int) -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("pca", SafePCA(n_components=emb_pca_d, random_state=0)),
        ]
    )


def build_preprocessor(
    columns_by_block: dict[str, list[str]],
    categorical_cols: list[str] | None = None,
    emb_pca_d: int = 32,
) -> ColumnTransformer:
    transformers = []
    for name, cols in columns_by_block.items():
        cols = list(cols)
        if not cols:
            continue
        pipe = _embedding_pipe(emb_pca_d) if name in {"embedding", "embeddings"} else _numeric_pipe()
        transformers.append((name, pipe, cols))
    if categorical_cols:
        transformers.append(
            (
                "categorical",
                OneHotEncoder(sparse_output=False, handle_unknown="ignore"),
                categorical_cols,
            )
        )
    return ColumnTransformer(transformers, remainder="drop", sparse_threshold=0.0)


def gbm_classifier(seed: int = 0) -> GradientBoostingClassifier:
    return GradientBoostingClassifier(
        n_estimators=80,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        random_state=seed,
    )


def gbm_regressor(seed: int = 0) -> GradientBoostingRegressor:
    return GradientBoostingRegressor(
        n_estimators=120,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        random_state=seed,
    )


def classifier_splits(
    y: np.ndarray,
    groups: np.ndarray | None,
    mode: str,
    n_splits: int,
    seed: int = 0,
):
    if mode == "group":
        if groups is None:
            raise ValueError("groups required for group CV")
        uniq = np.unique(groups)
        return GroupKFold(n_splits=max(2, min(n_splits, len(uniq)))).split(
            np.zeros(len(y)), y, groups
        )
    counts = Counter(y)
    min_class = min(counts.values())
    splits = max(2, min(n_splits, min_class))
    if len(counts) > 1 and min_class >= 2:
        return StratifiedKFold(
            n_splits=splits, shuffle=True, random_state=seed
        ).split(np.zeros(len(y)), y)
    return KFold(n_splits=max(2, min(n_splits, len(y))), shuffle=True, random_state=seed).split(
        np.zeros(len(y))
    )


def regression_splits(
    y: np.ndarray,
    groups: np.ndarray | None,
    mode: str,
    n_splits: int,
    seed: int = 0,
):
    if mode == "group":
        if groups is None:
            raise ValueError("groups required for group CV")
        uniq = np.unique(groups)
        return GroupKFold(n_splits=max(2, min(n_splits, len(uniq)))).split(
            np.zeros(len(y)), y, groups
        )
    return KFold(n_splits=max(2, min(n_splits, len(y))), shuffle=True, random_state=seed).split(
        np.zeros(len(y))
    )


def cross_val_predict_classifier(
    df: pd.DataFrame,
    y_col: str,
    columns_by_block: dict[str, list[str]],
    categorical_cols: list[str] | None = None,
    group_col: str | None = None,
    cv_mode: str = "stratified",
    n_splits: int = 5,
    emb_pca_d: int = 32,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    work = df.dropna(subset=[y_col]).reset_index(drop=True)
    y = work[y_col].astype(str).to_numpy()
    groups = work[group_col].astype(str).to_numpy() if group_col else None
    preds = np.empty_like(y, dtype=object)
    for tr, te in classifier_splits(y, groups, cv_mode, n_splits, seed):
        if len(np.unique(y[tr])) < 2:
            preds[te] = Counter(y[tr]).most_common(1)[0][0]
            continue
        prep = build_preprocessor(columns_by_block, categorical_cols, emb_pca_d)
        model = Pipeline([("prep", prep), ("model", clone(gbm_classifier(seed)))])
        model.fit(work.iloc[tr], y[tr])
        preds[te] = model.predict(work.iloc[te])
    return y, preds


def cross_val_predict_regressor(
    df: pd.DataFrame,
    y_col: str,
    columns_by_block: dict[str, list[str]],
    categorical_cols: list[str] | None = None,
    group_col: str | None = None,
    cv_mode: str = "kfold",
    n_splits: int = 5,
    emb_pca_d: int = 32,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    work = df.dropna(subset=[y_col]).reset_index(drop=True)
    y = work[y_col].astype(float).to_numpy()
    groups = work[group_col].astype(str).to_numpy() if group_col else None
    preds = np.zeros_like(y, dtype=float)
    for tr, te in regression_splits(y, groups, cv_mode, n_splits, seed):
        prep = build_preprocessor(columns_by_block, categorical_cols, emb_pca_d)
        model = Pipeline([("prep", prep), ("model", clone(gbm_regressor(seed)))])
        model.fit(work.iloc[tr], y[tr])
        preds[te] = model.predict(work.iloc[te])
    return y, preds


def classification_summary(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    labels = sorted(np.unique(y_true).tolist())
    out = {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }
    for label in labels:
        out[f"f1_{label}"] = float(f1_score(y_true == label, y_pred == label, zero_division=0))
        out[f"n_{label}"] = int((y_true == label).sum())
    return out


def regression_summary(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    r = pearson_safe(y_true, y_pred)
    return {
        "n": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "r": r,
    }


def pearson_safe(x: np.ndarray | pd.Series, y: np.ndarray | pd.Series) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3 or np.std(x[mask]) == 0 or np.std(y[mask]) == 0:
        return float("nan")
    return float(pearsonr(x[mask], y[mask])[0])


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    groups: np.ndarray | None = None,
    n_boot: int = 1000,
    seed: int = 0,
) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    vals = []
    if groups is None:
        n = len(y_true)
        for _ in range(n_boot):
            idx = rng.integers(0, n, size=n)
            try:
                vals.append(metric(y_true[idx], y_pred[idx]))
            except Exception:
                continue
    else:
        groups = np.asarray(groups)
        unique_groups = np.unique(groups)
        group_to_idx = {g: np.flatnonzero(groups == g) for g in unique_groups}
        for _ in range(n_boot):
            sampled = rng.choice(unique_groups, size=len(unique_groups), replace=True)
            idx = np.concatenate([group_to_idx[g] for g in sampled])
            try:
                vals.append(metric(y_true[idx], y_pred[idx]))
            except Exception:
                continue
    if not vals:
        return float("nan"), float("nan"), float("nan")
    arr = np.asarray(vals, dtype=float)
    return (
        float(np.nanmean(arr)),
        float(np.nanpercentile(arr, 2.5)),
        float(np.nanpercentile(arr, 97.5)),
    )


def binary_f1_metric(pos_label: str) -> Callable[[np.ndarray, np.ndarray], float]:
    def _metric(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(f1_score(y_true == pos_label, y_pred == pos_label, zero_division=0))

    return _metric


def macro_f1_metric(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


def balanced_downsample(
    df: pd.DataFrame,
    y_col: str,
    seed: int = 0,
    max_per_class: int | None = None,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    counts = df[y_col].value_counts()
    if len(counts) < 2:
        return df.copy()
    n = int(counts.min())
    if max_per_class is not None:
        n = min(n, max_per_class)
    parts = []
    for _, group in df.groupby(y_col):
        idx = group.index.to_numpy()
        chosen = rng.choice(idx, size=n, replace=False)
        parts.append(df.loc[chosen])
    return pd.concat(parts, ignore_index=True).sample(frac=1, random_state=seed).reset_index(
        drop=True
    )
