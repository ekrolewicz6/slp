"""Cross-lifespan language-state comparison.

Compare TD child language, DLD/SLI, late talkers, adult controls, and aphasia
in a shared structural feature space. The goal is not to force one universal
axis; it is to test which populations are close, which are separable after
basic matching, and whether DLD looks like a developmental analog of aphasia or
a distinct developmental state.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.linalg import subspace_angles
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_dld_state_screening import clinical_label, participant_root  # noqa: E402


CHILDES_META = {
    "transcript_id",
    "corpus",
    "bundle",
    "child_id",
    "age_months",
    "window_id",
    "window_index",
    "n_chi_utts_in_window",
    "n_chi_utterances",
}

AB_META = {
    "transcript_id",
    "section",
    "corpus",
    "participant_id",
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

SURFACE_CORE = [
    "mlu_words",
    "mlu_morphemes",
    "ndw",
    "total_words",
    "verbs_per_utterance",
    "ttr",
    "function_word_ratio",
    "hapax_ratio",
    "log_total_tokens",
    "utt_len_mean",
    "utt_len_std",
    "utt_len_p10",
    "utt_len_p50",
    "utt_len_p90",
    "single_word_ratio",
    "repetition_per_utt",
    "retracing_per_utt",
    "pause_per_utt",
    "filler_per_utt",
    "n_utterances",
]

MAIN_SUBTYPES = ["Anomic", "Broca", "Conduction", "Wernicke"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--childes-features",
        default="data/features/phase1_windowed_features.parquet",
        type=Path,
    )
    parser.add_argument(
        "--aphasia-features",
        default="data/features/aphasiabank_windowed_features.parquet",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/dld_cross_lifespan_state", type=Path)
    parser.add_argument("--max-child-age", default=84.0, type=float)
    parser.add_argument("--feature-set", choices=["surface_core", "all_common"], default="surface_core")
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


def numeric_cols(df: pd.DataFrame, meta: set[str]) -> list[str]:
    return sorted(c for c in df.columns if c not in meta and pd.api.types.is_numeric_dtype(df[c]))


def aggregate_population(
    df: pd.DataFrame,
    entity_col: str,
    feature_cols: list[str],
    population: str,
    meta: dict[str, str] | None = None,
) -> pd.DataFrame:
    meta = meta or {}
    agg = {c: "mean" for c in feature_cols}
    for col in meta:
        if col in df.columns:
            agg[col] = "first"
    out = df.groupby(entity_col, as_index=False).agg(agg)
    out = out.rename(columns={entity_col: "entity_id"})
    out["population"] = population
    return out


def build_entities(childes: pd.DataFrame, ab: pd.DataFrame, feature_cols: list[str], max_child_age: float) -> pd.DataFrame:
    childes = childes.copy()
    childes["clinical_label"] = childes["transcript_id"].map(clinical_label)
    childes["participant_root"] = [
        participant_root(tid, lab) for tid, lab in zip(childes["transcript_id"], childes["clinical_label"])
    ]

    rows = []
    td = childes[
        childes["bundle"].isin(["Eng-NA", "Eng-UK"])
        & childes["age_months"].notna()
        & childes["age_months"].gt(0)
        & childes["age_months"].le(max_child_age)
    ].copy()
    rows.append(
        aggregate_population(
            td,
            "child_id",
            feature_cols,
            "TD_CHILDES",
            {"corpus": "first", "bundle": "first", "age_months": "mean"},
        )
    )

    clinical = childes[
        childes["bundle"].eq("Clinical-Eng")
        & childes["age_months"].notna()
        & childes["age_months"].gt(0)
        & childes["age_months"].le(max_child_age)
        & childes["clinical_label"].isin(["TD", "DLD_SLI", "LateTalker", "DS", "HL"])
    ].copy()
    for label, population in [
        ("TD", "TD_CLINICAL"),
        ("DLD_SLI", "DLD_SLI"),
        ("LateTalker", "LATE_TALKER"),
        ("DS", "DOWN_SYNDROME"),
        ("HL", "HEARING_LOSS"),
    ]:
        subset = clinical[clinical["clinical_label"].eq(label)].copy()
        if len(subset):
            rows.append(
                aggregate_population(
                    subset,
                    "participant_root",
                    feature_cols,
                    population,
                    {"corpus": "first", "age_months": "mean", "clinical_label": "first"},
                )
            )

    ab = ab.copy()
    controls = ab[ab["is_control"].eq(True)].copy()
    if len(controls):
        rows.append(
            aggregate_population(
                controls,
                "participant_id",
                feature_cols,
                "AB_CONTROL",
                {"corpus": "first", "age_years": "mean", "sex": "first", "subtype": "first"},
            )
        )

    pwa = ab[ab["is_control"].ne(True) & ab["subtype"].isin(MAIN_SUBTYPES)].copy()
    if len(pwa):
        rows.append(
            aggregate_population(
                pwa,
                "participant_id",
                feature_cols,
                "PWA_ALL",
                {"corpus": "first", "age_years": "mean", "sex": "first", "subtype": "first", "wab_aq": "mean"},
            )
        )
        for subtype in MAIN_SUBTYPES:
            subset = pwa[pwa["subtype"].eq(subtype)].copy()
            if len(subset):
                rows.append(
                    aggregate_population(
                        subset,
                        "participant_id",
                        feature_cols,
                        f"PWA_{subtype.upper()}",
                        {
                            "corpus": "first",
                            "age_years": "mean",
                            "sex": "first",
                            "subtype": "first",
                            "wab_aq": "mean",
                        },
                    )
                )

    return pd.concat(rows, ignore_index=True)


def scaled_matrix(entities: pd.DataFrame, feature_cols: list[str]) -> tuple[np.ndarray, Pipeline]:
    pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    X = pipe.fit_transform(entities[feature_cols])
    return X, pipe


def population_summary(entities: pd.DataFrame) -> pd.DataFrame:
    return (
        entities.groupby("population")
        .agg(
            n_entities=("entity_id", "nunique"),
            age_months_mean=("age_months", "mean"),
            age_years_mean=("age_years", "mean"),
            wab_aq_mean=("wab_aq", "mean"),
            mlu_mean=("mlu_words", "mean"),
            single_word_ratio_mean=("single_word_ratio", "mean"),
            utt_len_p90_mean=("utt_len_p90", "mean"),
        )
        .reset_index()
        .sort_values("population")
    )


def centroid_distances(entities: pd.DataFrame, X: np.ndarray) -> pd.DataFrame:
    work = entities[["population"]].copy()
    cols = [f"x{i}" for i in range(X.shape[1])]
    xdf = pd.concat([work, pd.DataFrame(X, columns=cols)], axis=1)
    cent = xdf.groupby("population")[cols].mean()
    rows = []
    for a, b in itertools.combinations(cent.index, 2):
        rows.append(
            {
                "population_a": a,
                "population_b": b,
                "centroid_distance": float(np.linalg.norm(cent.loc[a].to_numpy() - cent.loc[b].to_numpy())),
            }
        )
    return pd.DataFrame(rows).sort_values("centroid_distance")


def nearest_neighbor_distances(entities: pd.DataFrame, X: np.ndarray) -> pd.DataFrame:
    rows = []
    pops = sorted(entities["population"].unique())
    for a in pops:
        idx_a = np.flatnonzero(entities["population"].eq(a).to_numpy())
        if len(idx_a) < 2:
            continue
        nn = NearestNeighbors(n_neighbors=2).fit(X[idx_a])
        dist, _ = nn.kneighbors(X[idx_a])
        rows.append(
            {
                "from_population": a,
                "to_population": a,
                "n_from": int(len(idx_a)),
                "n_to": int(len(idx_a)),
                "median_nn_distance": float(np.median(dist[:, 1])),
                "mean_nn_distance": float(np.mean(dist[:, 1])),
            }
        )
        for b in pops:
            if a == b:
                continue
            idx_b = np.flatnonzero(entities["population"].eq(b).to_numpy())
            if len(idx_b) < 2:
                continue
            nn = NearestNeighbors(n_neighbors=1).fit(X[idx_b])
            dist, _ = nn.kneighbors(X[idx_a])
            rows.append(
                {
                    "from_population": a,
                    "to_population": b,
                    "n_from": int(len(idx_a)),
                    "n_to": int(len(idx_b)),
                    "median_nn_distance": float(np.median(dist[:, 0])),
                    "mean_nn_distance": float(np.mean(dist[:, 0])),
                }
            )
    return pd.DataFrame(rows).sort_values(["from_population", "median_nn_distance"])


def principal_angle_rows(entities: pd.DataFrame, X: np.ndarray, d: int = 5) -> pd.DataFrame:
    rows = []
    pops = sorted(entities["population"].unique())
    for a, b in itertools.combinations(pops, 2):
        ia = np.flatnonzero(entities["population"].eq(a).to_numpy())
        ib = np.flatnonzero(entities["population"].eq(b).to_numpy())
        if len(ia) < d + 2 or len(ib) < d + 2:
            continue
        da = min(d, len(ia) - 1, X.shape[1])
        db = min(d, len(ib) - 1, X.shape[1])
        dd = min(da, db)
        pca_a = PCA(n_components=dd, random_state=0).fit(X[ia])
        pca_b = PCA(n_components=dd, random_state=0).fit(X[ib])
        angles = np.degrees(subspace_angles(pca_a.components_.T, pca_b.components_.T))
        rows.append(
            {
                "population_a": a,
                "population_b": b,
                "d": int(dd),
                "mean_angle_deg": float(np.mean(angles)),
                "max_angle_deg": float(np.max(angles)),
                "min_angle_deg": float(np.min(angles)),
            }
        )
    return pd.DataFrame(rows).sort_values("mean_angle_deg")


def matched_low_output_classifier(entities: pd.DataFrame, X: np.ndarray, seed: int) -> pd.DataFrame:
    pairs = [
        ("DLD_SLI", "PWA_BROCA"),
        ("LATE_TALKER", "PWA_BROCA"),
        ("DLD_SLI", "TD_CHILDES"),
        ("PWA_BROCA", "AB_CONTROL"),
    ]
    rows = []
    for a, b in pairs:
        idx = np.flatnonzero(entities["population"].isin([a, b]).to_numpy())
        if len(idx) < 12:
            continue
        work = entities.iloc[idx].copy()
        mlu_min = max(work[work["population"].eq(a)]["mlu_words"].quantile(0.10), work[work["population"].eq(b)]["mlu_words"].quantile(0.10))
        mlu_max = min(work[work["population"].eq(a)]["mlu_words"].quantile(0.90), work[work["population"].eq(b)]["mlu_words"].quantile(0.90))
        matched_mask = work["mlu_words"].between(mlu_min, mlu_max)
        midx = idx[matched_mask.to_numpy()]
        if len(midx) < 12 or entities.iloc[midx]["population"].nunique() < 2:
            continue
        y = entities.iloc[midx]["population"].eq(b).astype(int).to_numpy()
        if min(np.bincount(y)) < 5:
            continue
        clf = Pipeline(
            [
                (
                    "model",
                    GradientBoostingClassifier(
                        n_estimators=200,
                        learning_rate=0.05,
                        max_depth=2,
                        subsample=0.9,
                        random_state=seed,
                    ),
                )
            ]
        )
        cv = StratifiedKFold(n_splits=min(5, int(min(np.bincount(y)))), shuffle=True, random_state=seed)
        pred = cross_val_predict(clf, X[midx], y, cv=cv)
        rows.append(
            {
                "population_a": a,
                "population_b": b,
                "n_entities": int(len(midx)),
                "n_a": int((y == 0).sum()),
                "n_b": int((y == 1).sum()),
                "mlu_min": float(mlu_min),
                "mlu_max": float(mlu_max),
                "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
                "positive_f1": float(f1_score(y, pred, zero_division=0)),
            }
        )
    return pd.DataFrame(rows).sort_values("macro_f1", ascending=False) if rows else pd.DataFrame()


def pca_plot(out_dir: Path, entities: pd.DataFrame, X: np.ndarray) -> pd.DataFrame:
    pca = PCA(n_components=2, random_state=0).fit(X)
    z = pca.transform(X)
    plot_df = entities[["entity_id", "population", "mlu_words", "wab_aq", "age_months", "age_years"]].copy()
    plot_df["pc1"] = z[:, 0]
    plot_df["pc2"] = z[:, 1]
    plot_df.to_csv(out_dir / "entity_pca_coordinates.csv", index=False)

    fig, ax = plt.subplots(figsize=(11, 8))
    order = [
        "TD_CHILDES",
        "TD_CLINICAL",
        "DLD_SLI",
        "LATE_TALKER",
        "AB_CONTROL",
        "PWA_BROCA",
        "PWA_ANOMIC",
        "PWA_CONDUCTION",
        "PWA_WERNICKE",
        "DOWN_SYNDROME",
        "HEARING_LOSS",
    ]
    for pop in order:
        sub = plot_df[plot_df["population"].eq(pop)]
        if sub.empty:
            continue
        ax.scatter(sub["pc1"], sub["pc2"], s=26, alpha=0.65, label=pop)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
    ax.set_title("Cross-lifespan language-state projection")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "cross_lifespan_pca.png", dpi=160)
    plt.close(fig)
    return pd.DataFrame(
        [
            {
                "pc1_variance": float(pca.explained_variance_ratio_[0]),
                "pc2_variance": float(pca.explained_variance_ratio_[1]),
                "pc12_variance": float(pca.explained_variance_ratio_[:2].sum()),
            }
        ]
    )


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    childes = pd.read_parquet(args.childes_features)
    ab = pd.read_parquet(args.aphasia_features)

    child_cols = set(numeric_cols(childes, CHILDES_META))
    ab_cols = set(numeric_cols(ab, AB_META))
    common = sorted(child_cols & ab_cols)
    if args.feature_set == "surface_core":
        feature_cols = [c for c in SURFACE_CORE if c in common]
    else:
        feature_cols = common

    entities = build_entities(childes, ab, feature_cols, args.max_child_age)
    entities.to_csv(out_dir / "cross_lifespan_entities.csv", index=False)

    X, _ = scaled_matrix(entities, feature_cols)
    pop = population_summary(entities)
    cent = centroid_distances(entities, X)
    nn = nearest_neighbor_distances(entities, X)
    angles = principal_angle_rows(entities, X)
    matched = matched_low_output_classifier(entities, X, args.seed)
    pca_info = pca_plot(out_dir, entities, X)

    pop.to_csv(out_dir / "population_summary.csv", index=False)
    cent.to_csv(out_dir / "centroid_distances.csv", index=False)
    nn.to_csv(out_dir / "nearest_neighbor_distances.csv", index=False)
    angles.to_csv(out_dir / "principal_angles.csv", index=False)
    matched.to_csv(out_dir / "matched_low_output_classifiers.csv", index=False)
    pca_info.to_csv(out_dir / "pca_variance.csv", index=False)

    focal_populations = ["TD_CHILDES", "TD_CLINICAL", "DLD_SLI", "LATE_TALKER", "AB_CONTROL", "PWA_BROCA"]
    focal_nn = nn[
        nn["from_population"].isin(["DLD_SLI", "LATE_TALKER", "PWA_BROCA"])
        & nn["to_population"].isin(focal_populations)
    ].copy()
    focal_cent = cent[
        cent["population_a"].isin(focal_populations)
        & cent["population_b"].isin(focal_populations)
    ].copy()
    focal_angles = angles[
        angles["population_a"].isin(focal_populations)
        & angles["population_b"].isin(focal_populations)
    ].copy()

    lines = [
        "# Cross-Lifespan Language-State Summary",
        "",
        f"- Feature set: {args.feature_set}",
        f"- Features: {len(feature_cols)}",
        f"- Entities: {len(entities)}",
        "",
        "## Population Summary",
        "",
        md_table(pop),
        "",
        "## PCA Variance",
        "",
        md_table(pca_info),
        "",
        "## Focal Nearest-Neighbor Distances",
        "",
        "Distances are in standardized feature space. Within-population rows are the internal nearest-neighbor baseline.",
        "",
        md_table(focal_nn, max_rows=80),
        "",
        "## Focal Centroid Distances",
        "",
        md_table(focal_cent.sort_values("centroid_distance"), max_rows=60),
        "",
        "## Focal Principal Angles",
        "",
        md_table(focal_angles.sort_values("mean_angle_deg"), max_rows=60),
        "",
        "## MLU-Matched Low-Output Separability",
        "",
        md_table(matched),
        "",
        "## Interpretation",
        "",
        "- If DLD is merely a child version of aphasia, DLD and Broca should be close after MLU matching.",
        "- If DLD is a developmental state and Broca is a damaged adult state, MLU-matched DLD-vs-Broca separability should remain high.",
        "- Nearest-neighbor and centroid distances are descriptive; corpus/task artifacts remain possible.",
        "- This script deliberately emphasizes surface-core features to reduce parser asymmetry between CHILDES and AphasiaBank.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    print((out_dir / "summary.md").resolve())


if __name__ == "__main__":
    main()
