"""Phase 2 dry run on CHILDES.

Goal: validate the representation-learning architecture on developmental data
before AphasiaBank arrives. We collapse the 55-feature transcript vectors into
a low-dimensional latent state z and ask three questions:

1. **Does z carry the signal?** Train a GBM age predictor on z (instead of raw
   X) and compare MAE to (a) MLU-only baseline, (b) GBM on raw X (8.98 mo).
   A good z preserves most predictive power at d ≤ 10 dimensions.

2. **Is z geometrically meaningful?** Project to 2D, color by age, look for
   monotonic developmental progression rather than corpus-driven clusters.

3. **Does z replace categorical thinking?** KMeans into k stages, then check
   whether mean age per cluster is monotonic and whether children pass through
   stages in order over time. (The Phase 2 spec calls this "Test: clustering
   vs classical labels". Here we don't have categorical labels, so we test
   that data-driven stages line up with developmental order.)

Phase-2-on-aphasia will swap (age) → (WAB-AQ + subtype) but the architecture
is identical.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import silhouette_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr, spearmanr


@dataclass
class StateModel:
    """A fitted (scaler → PCA) pipeline producing latent state z."""
    d: int
    scaler: StandardScaler
    pca: PCA
    feature_names: list[str]

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        X = df[self.feature_names].to_numpy(dtype=float)
        return self.pca.transform(self.scaler.transform(X))

    @property
    def variance_explained(self) -> float:
        return float(self.pca.explained_variance_ratio_.sum())


def fit_state(df: pd.DataFrame, feature_cols: list[str], d: int) -> StateModel:
    X = df[feature_cols].to_numpy(dtype=float)
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    pca = PCA(n_components=d, random_state=0).fit(Xs)
    return StateModel(d=d, scaler=scaler, pca=pca, feature_names=list(feature_cols))


def evaluate_age_from_state(
    Z: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    n_splits: int = 5,
) -> dict[str, float]:
    """Child-grouped CV: GBM age prediction from z."""
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.zeros_like(y, dtype=float)
    for train_idx, test_idx in gkf.split(Z, y, groups):
        model = GradientBoostingRegressor(
            n_estimators=400, max_depth=3, learning_rate=0.05,
            subsample=0.9, random_state=0,
        )
        model.fit(Z[train_idx], y[train_idx])
        preds[test_idx] = model.predict(Z[test_idx])
    err = preds - y
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    r = float(pearsonr(y, preds)[0]) if np.std(preds) > 0 else float("nan")
    return {"mae_months": mae, "rmse_months": rmse, "pearson_r": r}


def cluster_stage_purity(
    Z: np.ndarray,
    y: np.ndarray,
    k: int = 4,
) -> dict[str, float]:
    """KMeans into k stages; check whether mean-age-per-cluster is monotonic.

    Returns mean-age-rank Spearman correlation with cluster index (after
    relabeling clusters by ascending mean age). A perfect developmental
    ordering gives Spearman = 1.0.
    """
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(Z)
    labels = km.labels_
    # Relabel clusters by mean age ascending.
    means = pd.Series(y).groupby(labels).mean().sort_values()
    relabel = {old: new for new, old in enumerate(means.index)}
    new_labels = np.array([relabel[l] for l in labels])
    sil = float(silhouette_score(Z, new_labels)) if k > 1 else float("nan")

    cluster_mean_ages = [
        float(np.mean(y[new_labels == c])) for c in range(k)
    ]
    cluster_n = [int((new_labels == c).sum()) for c in range(k)]
    spearman_rho = float(spearmanr(np.arange(k), cluster_mean_ages)[0])
    return {
        "k": k,
        "silhouette": sil,
        "stage_age_spearman": spearman_rho,
        "cluster_mean_ages": cluster_mean_ages,
        "cluster_sizes": cluster_n,
    }
