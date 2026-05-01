"""Pilot standard-acoustic subtype models on balanced eGeMAPS extraction."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import ensure_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--opensmile",
                   default="data/features/aphasia_opensmile_egemaps_balanced48.parquet",
                   type=Path)
    p.add_argument("--features",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--transcript-list",
                   default=None,
                   type=Path,
                   help="Optional manifest whose transcript_id/patient_root/subtype metadata are authoritative.")
    p.add_argument("--output-dir",
                   default="outputs/aphasia_standard_acoustic_replication",
                   type=Path)
    p.add_argument("--label", default="balanced48")
    p.add_argument("--repeats", type=int, default=20)
    p.add_argument("--splits", type=int, default=4)
    p.add_argument("--seed", type=int, default=13)
    return p.parse_args()


def patient_root(participant_id: object) -> str:
    s = str(participant_id)
    s = re.sub(r"-(?:\d+|LARC)$", "", s)
    s = re.sub(r"([A-Za-z]+\d+)[a-z]$", r"\1", s)
    return s


def load_manifest_table(opensmile_path: Path, manifest_path: Path) -> pd.DataFrame:
    os_df = pd.read_parquet(opensmile_path)
    manifest = pd.read_csv(manifest_path)
    required = {"transcript_id", "patient_root", "subtype", "wab_aq", "corpus", "participant_id"}
    missing = required.difference(manifest.columns)
    if missing:
        raise ValueError(f"Transcript manifest is missing required columns: {sorted(missing)}")

    label_cols = ["transcript_id", "patient_root", "subtype", "wab_aq", "corpus", "participant_id"]
    df = os_df.merge(
        manifest[label_cols].drop_duplicates("transcript_id"),
        on="transcript_id",
        how="inner",
        suffixes=("_opensmile", ""),
    )
    missing_transcripts = sorted(set(manifest["transcript_id"]) - set(df["transcript_id"]))
    if missing_transcripts:
        print(
            f"warning: {len(missing_transcripts)} manifest transcript(s) were not present in openSMILE output",
            file=sys.stderr,
        )
    if df.empty:
        raise ValueError("No openSMILE rows matched the transcript manifest")

    ambiguous = (
        df.dropna(subset=["subtype"])
        .drop_duplicates(["patient_root", "subtype"])
        .groupby("patient_root")["subtype"]
        .nunique()
    )
    ambiguous = ambiguous[ambiguous > 1]
    if not ambiguous.empty:
        raise ValueError(f"Manifest creates ambiguous patient roots: {ambiguous.index.tolist()}")

    os_cols = [c for c in df.columns if c.startswith("os_")]
    agg = {c: "mean" for c in os_cols}
    agg.update({
        "subtype": "first",
        "wab_aq": "first",
        "corpus": "first",
        "participant_id": "first",
        "transcript_id": "first",
        "window_id": "count",
    })
    root = df.groupby("patient_root", as_index=False).agg(agg).rename(
        columns={"window_id": "n_windows"}
    )
    keep = ["Anomic", "Broca", "Conduction", "Wernicke"]
    return root[root["subtype"].isin(keep)].copy()


def load_root_table(opensmile_path: Path, features_path: Path, transcript_list: Path | None) -> pd.DataFrame:
    if transcript_list is not None:
        return load_manifest_table(opensmile_path, transcript_list)

    os_df = pd.read_parquet(opensmile_path)
    feat = pd.read_parquet(features_path)
    meta = feat[
        ["window_id", "subtype", "wab_aq", "corpus", "participant_id"]
    ].drop_duplicates("window_id")
    df = os_df.merge(meta, on="window_id", how="left", suffixes=("", "_meta"))
    df["patient_root"] = df["participant_id"].map(patient_root)
    os_cols = [c for c in df.columns if c.startswith("os_")]
    agg = {c: "mean" for c in os_cols}
    agg.update({
        "subtype": "first",
        "wab_aq": "first",
        "corpus": "first",
        "participant_id": "first",
        "transcript_id": "first",
        "window_id": "count",
    })
    root = df.groupby("patient_root", as_index=False).agg(agg).rename(
        columns={"window_id": "n_windows"}
    )
    keep = ["Anomic", "Broca", "Conduction", "Wernicke"]
    root = root[root["subtype"].isin(keep)].copy()
    return root


def acoustic_pipeline(seed: int) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("pca", PCA(n_components=0.9, svd_solver="full", random_state=seed)),
        ("clf", LogisticRegression(
            C=0.5,
            class_weight="balanced",
            max_iter=2000,
            random_state=seed,
        )),
    ])


def simple_pipeline(seed: int) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=2000,
            random_state=seed,
        )),
    ])


def evaluate_cv(
    name: str,
    X: np.ndarray,
    y: np.ndarray,
    model,
    splits: int,
    repeats: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    pred_rows = []
    rskf = RepeatedStratifiedKFold(n_splits=splits, n_repeats=repeats, random_state=seed)
    for run_idx, (train_idx, test_idx) in enumerate(rskf.split(X, y), start=1):
        clf = clone(model)
        clf.fit(X[train_idx], y[train_idx])
        pred = clf.predict(X[test_idx])
        rows.append({
            "model": name,
            "run": run_idx,
            "balanced_accuracy": balanced_accuracy_score(y[test_idx], pred),
            "macro_f1": f1_score(y[test_idx], pred, average="macro"),
        })
        for i, p in zip(test_idx, pred):
            pred_rows.append({"model": name, "run": run_idx, "row_idx": int(i), "true": y[i], "pred": p})
    return pd.DataFrame(rows), pd.DataFrame(pred_rows)


def evaluate_leave_corpus_out(
    root: pd.DataFrame,
    model_configs: list[tuple[str, np.ndarray, object]],
) -> pd.DataFrame:
    rows = []
    y = root["subtype"].to_numpy()
    corpora = sorted(root["corpus"].dropna().unique())
    for corpus in corpora:
        test_mask = root["corpus"].to_numpy() == corpus
        train_mask = ~test_mask
        y_train = y[train_mask]
        y_test = y[test_mask]
        if len(y_test) < 4 or pd.Series(y_test).nunique() < 2 or pd.Series(y_train).nunique() < 2:
            continue
        for name, X, model in model_configs:
            clf = clone(model)
            clf.fit(X[train_mask], y_train)
            pred = clf.predict(X[test_mask])
            rows.append({
                "model": name,
                "held_out_corpus": corpus,
                "n_test": int(test_mask.sum()),
                "test_classes": ",".join(sorted(pd.Series(y_test).unique())),
                "balanced_accuracy": balanced_accuracy_score(y_test, pred),
                "macro_f1": f1_score(y_test, pred, average="macro"),
            })
    return pd.DataFrame(rows)


def evaluate_pairwise(root: pd.DataFrame, os_cols: list[str], seed: int) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(seed)
    pairs = [
        ("Wernicke", "Anomic"),
        ("Wernicke", "Conduction"),
        ("Conduction", "Anomic"),
        ("Broca", "Anomic"),
    ]
    for a, b in pairs:
        sub = root[root["subtype"].isin([a, b])].copy()
        if sub["subtype"].value_counts().min() < 4:
            continue
        X = sub[os_cols].to_numpy(dtype=float)
        X_wab = sub[["wab_aq"]].to_numpy(dtype=float)
        X_combined = sub[os_cols + ["wab_aq"]].to_numpy(dtype=float)
        X_random = rng.normal(size=(len(sub), len(os_cols)))
        y = sub["subtype"].to_numpy()
        cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=seed)
        for model_name, model_X, model in [
            ("wab_only", X_wab, simple_pipeline(seed)),
            ("egemaps_only", X, acoustic_pipeline(seed)),
            ("egemaps_plus_wab", X_combined, acoustic_pipeline(seed)),
            ("random_features", X_random, acoustic_pipeline(seed)),
        ]:
            pred = cross_val_predict(model, model_X, y, cv=cv)
            rows.append({
                "contrast": f"{a}_vs_{b}",
                "model": model_name,
                "n": len(sub),
                "balanced_accuracy": balanced_accuracy_score(y, pred),
                "macro_f1": f1_score(y, pred, average="macro"),
            })
    return pd.DataFrame(rows)


def opensmile_feature_families(os_cols: list[str]) -> dict[str, list[str]]:
    def contains(*needles: str) -> list[str]:
        lowered = [(c, c.lower()) for c in os_cols]
        return [c for c, low in lowered if any(n.lower() in low for n in needles)]

    families = {
        "pitch_f0": contains("F0semitone"),
        "loudness_intensity": contains("loudness", "equivalentSoundLevel"),
        "spectral_mfcc": contains("spectral", "mfcc", "alphaRatio", "hammarberg", "slope"),
        "voice_quality": contains("jitter", "shimmer", "HNR", "logRelF0"),
        "formants": contains("F1", "F2", "F3"),
        "timing_coverage": contains("PeaksPerSec", "VoicedSegments", "SegmentLength", "valid_time", "total_utt_audio", "window_span", "speech_coverage"),
    }
    return {name: cols for name, cols in families.items() if cols}


def evaluate_feature_families(
    root: pd.DataFrame,
    os_cols: list[str],
    splits: int,
    repeats: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    y = root["subtype"].to_numpy()
    for family, cols in opensmile_feature_families(os_cols).items():
        X = root[cols].to_numpy(dtype=float)
        scores, _ = evaluate_cv(
            family,
            X,
            y,
            acoustic_pipeline(seed),
            splits,
            repeats,
            seed,
        )
        lo_f1, hi_f1 = bootstrap_ci(scores["macro_f1"], rng)
        lo_ba, hi_ba = bootstrap_ci(scores["balanced_accuracy"], rng)
        rows.append({
            "feature_family": family,
            "n_features": len(cols),
            "mean_balanced_accuracy": scores["balanced_accuracy"].mean(),
            "ba_ci_low": lo_ba,
            "ba_ci_high": hi_ba,
            "mean_macro_f1": scores["macro_f1"].mean(),
            "f1_ci_low": lo_f1,
            "f1_ci_high": hi_f1,
        })
    return pd.DataFrame(rows).sort_values("mean_macro_f1", ascending=False)


def bootstrap_ci(values: pd.Series, rng: np.random.Generator, n_boot: int = 2000) -> tuple[float, float]:
    arr = values.to_numpy(dtype=float)
    if len(arr) == 0:
        return np.nan, np.nan
    boots = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_boot)]
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    out = [
        "| " + " | ".join(df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for row in df.itertuples(index=False):
        vals = []
        for value in row:
            if isinstance(value, float):
                vals.append(f"{value:.3f}")
            else:
                vals.append(str(value))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    rng = np.random.default_rng(args.seed)
    root = load_root_table(args.opensmile, args.features, args.transcript_list)
    os_cols = [c for c in root.columns if c.startswith("os_")]
    y = root["subtype"].to_numpy()
    X_os = root[os_cols].to_numpy(dtype=float)
    X_wab = root[["wab_aq"]].to_numpy(dtype=float)
    X_combined = root[os_cols + ["wab_aq"]].to_numpy(dtype=float)
    X_random = rng.normal(size=(len(root), len(os_cols)))

    evaluations = []
    predictions = []
    configs = [
        ("majority", X_os, DummyClassifier(strategy="most_frequent")),
        ("wab_only", X_wab, simple_pipeline(args.seed)),
        ("egemaps_only", X_os, acoustic_pipeline(args.seed)),
        ("egemaps_plus_wab", X_combined, acoustic_pipeline(args.seed)),
        ("random_features", X_random, acoustic_pipeline(args.seed)),
    ]
    for name, X, model in configs:
        scores, preds = evaluate_cv(name, X, y, model, args.splits, args.repeats, args.seed)
        evaluations.append(scores)
        predictions.append(preds)

    shuffled = y.copy()
    rng.shuffle(shuffled)
    scores, preds = evaluate_cv(
        "shuffled_labels",
        X_os,
        shuffled,
        acoustic_pipeline(args.seed),
        args.splits,
        args.repeats,
        args.seed,
    )
    evaluations.append(scores)
    predictions.append(preds)

    score_df = pd.concat(evaluations, ignore_index=True)
    pred_df = pd.concat(predictions, ignore_index=True)
    summary_rows = []
    for model, group in score_df.groupby("model"):
        lo_f1, hi_f1 = bootstrap_ci(group["macro_f1"], rng)
        lo_ba, hi_ba = bootstrap_ci(group["balanced_accuracy"], rng)
        summary_rows.append({
            "model": model,
            "mean_balanced_accuracy": group["balanced_accuracy"].mean(),
            "ba_ci_low": lo_ba,
            "ba_ci_high": hi_ba,
            "mean_macro_f1": group["macro_f1"].mean(),
            "f1_ci_low": lo_f1,
            "f1_ci_high": hi_f1,
        })
    summary = pd.DataFrame(summary_rows).sort_values("mean_macro_f1", ascending=False)
    pairwise = evaluate_pairwise(root, os_cols, args.seed)
    family_summary = evaluate_feature_families(root, os_cols, args.splits, args.repeats, args.seed)
    leave_corpus = evaluate_leave_corpus_out(
        root,
        [
            ("wab_only", X_wab, simple_pipeline(args.seed)),
            ("egemaps_only", X_os, acoustic_pipeline(args.seed)),
            ("egemaps_plus_wab", X_combined, acoustic_pipeline(args.seed)),
            ("random_features", X_random, acoustic_pipeline(args.seed)),
        ],
    )

    label = args.label
    root.to_csv(out_dir / f"{label}_root_table.csv", index=False)
    score_df.to_csv(out_dir / f"{label}_cv_scores.csv", index=False)
    pred_df.to_csv(out_dir / f"{label}_cv_predictions.csv", index=False)
    summary.to_csv(out_dir / f"{label}_model_summary.csv", index=False)
    pairwise.to_csv(out_dir / f"{label}_pairwise_summary.csv", index=False)
    family_summary.to_csv(out_dir / f"{label}_feature_family_summary.csv", index=False)
    leave_corpus.to_csv(out_dir / f"{label}_leave_corpus_out.csv", index=False)

    label_counts = root["subtype"].value_counts().rename_axis("subtype").reset_index(name="n_roots")
    corpus_counts = root.groupby(["corpus", "subtype"]).size().reset_index(name="n_roots")
    title_label = label[:1].upper() + label[1:]
    lines = [
        f"# {title_label} openSMILE/eGeMAPS Pilot",
        "",
        f"- Patient roots: {len(root):,}",
        f"- eGeMAPS feature columns: {len(os_cols):,}",
        f"- CV: repeated stratified {args.splits}-fold, repeats={args.repeats}",
        "- Preprocessing is inside each CV fold: median imputation, scaling, PCA, logistic regression.",
        f"- Metadata source: {'transcript manifest' if args.transcript_list else 'windowed feature metadata'}",
        "",
        "## Label Counts",
        "",
        md_table(label_counts),
        "",
        "## Model Summary",
        "",
        md_table(summary),
        "",
        "## Pairwise Acoustic Contrasts",
        "",
        md_table(pairwise),
        "",
        "## eGeMAPS Feature Families",
        "",
        md_table(family_summary),
        "",
        "## Leave-Corpus-Out Checks",
        "",
        md_table(leave_corpus),
        "",
        "## Corpus/Subtype Counts",
        "",
        md_table(corpus_counts),
        "",
        "## Interpretation",
        "",
        "This is a leakage-safe pilot, not a final replication. It uses one session per derived patient root, balanced subtype labels, standard eGeMAPS functionals, and fold-internal preprocessing. The next step is to expand this extraction across more patient roots and add corpus-held-out evaluation.",
        "",
    ]
    (out_dir / f"{label}_model_summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
