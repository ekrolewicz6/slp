"""Run the review-grade, highest-learning experiment suite.

This script implements the plan captured after experiment #49:

1. strict replication / data audit for #48 and #49;
2. Broca "damaged adult state" falsification tests;
3. mechanistic multimodal subtype ablations;
4. fold-clean WAB subtest decomposition;
5. longitudinal state-change-before-WAB analysis;
6. Salem/Cinderella stimulus-conditioned informativeness proxies.

Outputs are written under `outputs/highest_learning/`.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import subspace_angles
from scipy.stats import pearsonr, ttest_ind
from sklearn.decomposition import NMF, PCA
from sklearn.metrics import f1_score
from sklearn.preprocessing import MinMaxScaler, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import (
    AB_META,
    ACOUSTIC_GROUPS,
    CHI_META,
    MAIN_SUBTYPES,
    aggregate_rows,
    add_patient_root,
    artifact_safe_features,
    balanced_downsample,
    binary_f1_metric,
    bootstrap_ci,
    classification_summary,
    cross_val_predict_classifier,
    cross_val_predict_regressor,
    ensure_dir,
    load_ab_windowed,
    load_acoustics,
    load_embeddings,
    load_td_childes,
    macro_f1_metric,
    numeric_feature_columns,
    pearson_safe,
    regression_summary,
    write_json,
)


OUTCOMES = {
    "WAB AQ": ("WAB         AQ Note: for Baycrest and NEURAL corpora, WAB scores are from Bedside WAB", "summary"),
    "WAB Fluency": ("WAB SpontSp Fluency", "production"),
    "WAB InfoContent": ("WAB    SpontSp InfoContent", "content"),
    "WAB Repetition": ("WAB Repetition", "phonological"),
    "WAB Object Naming": ("WAB Object Naming", "lexical"),
    "WAB Word Fluency": ("WAB  WdFluency", "lexical"),
    "WAB Sent Completion": ("WAB SentComp", "production"),
    "WAB Resp Speech": ("WAB RespSp", "production"),
    "WAB Yes/No": ("WAB Yes/No Q", "comprehension"),
    "WAB AudWdRec": ("WAB       AudWdRec", "comprehension"),
    "WAB SeqComm": ("WAB        SeqComm", "comprehension"),
    "Sent Comp Total": ("Sent. Comp. - Full Total", "comprehension"),
    "VNT Total": ("VNT Total", "lexical-verb"),
}

CINDERELLA_CONCEPTS = {
    "cinderella": ["cinderella"],
    "stepfamily": ["stepmother", "stepsister", "stepsisters", "sister", "sisters", "stepchildren"],
    "prince": ["prince"],
    "ball": ["ball", "dance", "party"],
    "invitation": ["invitation", "invite", "invited"],
    "chores": ["clean", "sweep", "scrub", "work", "poor"],
    "fairy_godmother": ["fairy", "godmother"],
    "magic": ["magic", "magical"],
    "dress": ["dress", "gown", "beautiful"],
    "carriage": ["carriage", "coach", "pumpkin"],
    "midnight": ["midnight", "twelve"],
    "slipper": ["slipper", "shoe", "glass"],
    "lost_slipper": ["lost", "left"],
    "fit": ["fit", "fits", "try"],
    "marriage": ["marry", "married", "wedding"],
    "castle": ["castle", "palace"],
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--aphasia-features", default="data/features/aphasiabank_windowed_features.parquet", type=Path)
    p.add_argument("--childes-features", default="data/features/phase1_windowed_features.parquet", type=Path)
    p.add_argument("--embeddings-path", default="data/features/aphasia_window_embeddings.parquet", type=Path)
    p.add_argument("--acoustic-pattern", default="data/features/acoustic_g*.parquet")
    p.add_argument("--results-xlsx", default="data/raw/aphasiabank/metadata/english-results-data.xlsx", type=Path)
    p.add_argument(
        "--salem-csv",
        default=(
            "data/raw/aphasiabank/extras/Salem/talkbank-preprocessed-cinderella-data/"
            "preprocessed-cinderella/aphasia-preprocessed/sessions-report.csv"
        ),
        type=Path,
    )
    p.add_argument(
        "--salem-yaml",
        default=(
            "data/raw/aphasiabank/extras/Salem/talkbank-preprocessed-cinderella-data/"
            "preprocessed-cinderella/aphasia-preprocessed/sessions.yaml"
        ),
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/highest_learning", type=Path)
    p.add_argument("--cv-folds", default=5, type=int)
    p.add_argument("--bootstrap", default=200, type=int)
    p.add_argument("--emb-pca-d", default=16, type=int)
    return p.parse_args()


def modality_table(
    ab: pd.DataFrame,
    feature_cols: list[str],
    embeddings: pd.DataFrame,
    emb_cols: list[str],
    acoustics: pd.DataFrame,
    ac_cols: list[str],
    require_embeddings: bool = True,
    require_acoustic: bool = True,
) -> pd.DataFrame:
    df = ab.copy()
    if require_embeddings:
        df = df.merge(embeddings[["window_id"] + emb_cols], on="window_id", how="inner")
    elif len(embeddings):
        df = df.merge(embeddings[["window_id"] + emb_cols], on="window_id", how="left")
    if require_acoustic:
        df = df.merge(acoustics[["window_id"] + ac_cols], on="window_id", how="inner")
    elif len(acoustics):
        df = df.merge(acoustics[["window_id"] + ac_cols], on="window_id", how="left")
    first_cols = ["wab_aq", "subtype", "corpus", "is_control", "session_date", "age_years", "sex"]
    cols = feature_cols + (emb_cols if require_embeddings or len(embeddings) else []) + ac_cols
    pat = aggregate_rows(df, "participant_id", cols, first_cols)
    pat["subtype_filled"] = pat["subtype"].fillna("Unknown")
    return pat


def run_data_audit(
    out_dir: Path,
    ab_audit: dict,
    chi_audit: dict,
    emb_audit: dict,
    ac_audit: dict,
    ab: pd.DataFrame,
    chi: pd.DataFrame,
) -> None:
    audit = {
        "aphasia": ab_audit,
        "childes_td_only": chi_audit,
        "embeddings": emb_audit,
        "acoustics": ac_audit,
        "aphasia_participants": int(ab["participant_id"].nunique()),
        "aphasia_windows_clean": int(len(ab)),
        "childes_children_td_only": int(chi["child_id"].nunique()),
        "childes_windows_td_only": int(len(chi)),
        "childes_bundles": sorted(chi["bundle"].dropna().unique().tolist()),
    }
    write_json(out_dir / "data_audit.json", audit)
    pd.DataFrame(
        [
            {"check": "aphasia_window_ids_unique", "passed": not ab["window_id"].duplicated().any()},
            {"check": "childes_window_ids_unique", "passed": not chi["window_id"].duplicated().any()},
            {"check": "childes_td_only", "passed": set(chi["bundle"].dropna().unique()) <= {"Eng-NA", "Eng-UK"}},
        ]
    ).to_csv(out_dir / "data_assertions.csv", index=False)


def run_principal_angles(
    out_dir: Path,
    chi: pd.DataFrame,
    ab: pd.DataFrame,
    feature_cols: list[str],
    d: int = 8,
) -> None:
    controls = ab[ab["is_control"] == True].copy()
    pwa = ab[(ab["is_control"] != True) & ab["subtype"].notna()].copy()
    pwa = pwa[~pwa["subtype"].isin({"Control", "NotAphasic", "Unknown", "U"})]
    populations = {
        "CHILDES_TD": chi,
        "AB_controls": controls,
        "AB_PWA": pwa,
        "AB_Broca": pwa[pwa["subtype"] == "Broca"],
        "AB_fluent": pwa[pwa["subtype"].isin(["Anomic", "Conduction", "Wernicke"])],
    }
    rows = []
    for a_name, a_df in populations.items():
        for b_name, b_df in populations.items():
            if a_name >= b_name or len(a_df) < d + 2 or len(b_df) < d + 2:
                continue
            X = pd.concat([a_df[feature_cols], b_df[feature_cols]], ignore_index=True)
            scaler = StandardScaler().fit(X.to_numpy(dtype=float))
            Xa = scaler.transform(a_df[feature_cols].to_numpy(dtype=float))
            Xb = scaler.transform(b_df[feature_cols].to_numpy(dtype=float))
            pca_a = PCA(n_components=d, random_state=0).fit(Xa)
            pca_b = PCA(n_components=d, random_state=0).fit(Xb)
            angles = subspace_angles(pca_a.components_.T, pca_b.components_.T)
            rows.append(
                {
                    "population_a": a_name,
                    "population_b": b_name,
                    "n_a": len(a_df),
                    "n_b": len(b_df),
                    "d": d,
                    "mean_angle_deg": float(np.degrees(angles).mean()),
                    "max_angle_deg": float(np.degrees(angles).max()),
                    "grassmann_distance": float(np.linalg.norm(np.sin(angles))),
                    **{f"angle_{i+1}_deg": float(np.degrees(v)) for i, v in enumerate(angles)},
                }
            )
    pd.DataFrame(rows).to_csv(out_dir / "principal_angles.csv", index=False)


def run_strict_acoustic_replication(
    out_dir: Path,
    pat: pd.DataFrame,
    feature_cols: list[str],
    emb_cols: list[str],
    ac_cols: list[str],
    cv_folds: int,
    n_boot: int,
    emb_pca_d: int,
) -> None:
    print("[strict acoustic] subtype classification")
    sub = pat.dropna(subset=["subtype"]).copy()
    sub = sub[~sub["subtype"].isin({"Unknown", "U"})]
    counts = sub["subtype"].value_counts()
    keep = counts[counts >= 10].index.tolist()
    sub = sub[sub["subtype"].isin(keep)].reset_index(drop=True)
    setups = {
        "structural": {"structural": feature_cols},
        "acoustic": {"acoustic": ac_cols},
        "structural+acoustic": {"structural": feature_cols, "acoustic": ac_cols},
        "structural+embedding+acoustic": {
            "structural": feature_cols,
            "embedding": emb_cols,
            "acoustic": ac_cols,
        },
    }
    rows = []
    per_class = []
    for cv_name, cv_mode, group_col in [
        ("patient_stratified", "stratified", None),
        ("corpus_held_out", "group", "corpus"),
    ]:
        for setup, blocks in setups.items():
            y, pred = cross_val_predict_classifier(
                sub,
                "subtype",
                blocks,
                group_col=group_col,
                cv_mode=cv_mode,
                n_splits=cv_folds,
                emb_pca_d=emb_pca_d,
            )
            summary = classification_summary(y, pred)
            ci_mean, ci_lo, ci_hi = bootstrap_ci(
                y,
                pred,
                macro_f1_metric,
                groups=sub[group_col].to_numpy() if group_col else None,
                n_boot=n_boot,
            )
            rows.append(
                {
                    "experiment": "strict_acoustic_subtype",
                    "cv": cv_name,
                    "setup": setup,
                    **summary,
                    "macro_f1_boot_mean": ci_mean,
                    "macro_f1_ci_low": ci_lo,
                    "macro_f1_ci_high": ci_hi,
                }
            )
            for label in sorted(np.unique(y)):
                m = binary_f1_metric(label)
                fmean, flo, fhi = bootstrap_ci(
                    y,
                    pred,
                    m,
                    groups=sub[group_col].to_numpy() if group_col else None,
                    n_boot=n_boot,
                )
                per_class.append(
                    {
                        "cv": cv_name,
                        "setup": setup,
                        "subtype": label,
                        "n": int((y == label).sum()),
                        "f1": float(f1_score(y == label, pred == label, zero_division=0)),
                        "f1_ci_low": flo,
                        "f1_ci_high": fhi,
                    }
                )
    pd.DataFrame(rows).to_csv(out_dir / "strict_acoustic_subtype.csv", index=False)
    pd.DataFrame(per_class).to_csv(out_dir / "strict_acoustic_per_class.csv", index=False)


def _entity_aggregate(
    df: pd.DataFrame,
    id_col: str,
    feature_cols: list[str],
    first_cols: list[str],
    label: str,
    source_kind: str,
) -> pd.DataFrame:
    out = aggregate_rows(df, id_col, feature_cols, first_cols)
    out = out.rename(columns={id_col: "entity_id"})
    out["label"] = label
    out["source_kind"] = source_kind
    if "corpus" in out.columns:
        out["source_corpus"] = out["source_kind"] + ":" + out["corpus"].astype(str)
    else:
        out["source_corpus"] = out["source_kind"]
    return out


def _binary_eval(
    df: pd.DataFrame,
    feature_cols: list[str],
    positive_label: str,
    cv_name: str,
    cv_mode: str,
    group_col: str | None,
    cv_folds: int,
    n_boot: int,
) -> dict:
    y, pred = cross_val_predict_classifier(
        df,
        "label",
        {"features": feature_cols},
        group_col=group_col,
        cv_mode=cv_mode,
        n_splits=cv_folds,
    )
    f1 = float(f1_score(y == positive_label, pred == positive_label, zero_division=0))
    fmean, flo, fhi = bootstrap_ci(
        y,
        pred,
        binary_f1_metric(positive_label),
        groups=df[group_col].to_numpy() if group_col else None,
        n_boot=n_boot,
    )
    return {
        "cv": cv_name,
        "n": int(len(y)),
        "n_positive": int((y == positive_label).sum()),
        "n_negative": int((y != positive_label).sum()),
        "f1": f1,
        "f1_boot_mean": fmean,
        "f1_ci_low": flo,
        "f1_ci_high": fhi,
        "accuracy": float((y == pred).mean()),
        "balanced_accuracy": float(
            classification_summary(y, pred)["balanced_accuracy"]
        ),
    }


def run_broca_falsification(
    out_dir: Path,
    chi: pd.DataFrame,
    ab: pd.DataFrame,
    common_raw: list[str],
    cv_folds: int,
    n_boot: int,
) -> None:
    print("[broca falsification] balanced MLU-matched classifiers")
    rows = []
    feature_sets = {
        mode: artifact_safe_features(chi, ab, common_raw, mode=mode)
        for mode in ["artifact_safe", "no_rel", "surface_core"]
    }
    write_json(
        out_dir / "broca_feature_sets.json",
        {name: cols for name, cols in feature_sets.items()},
    )
    ctrl = ab[ab["is_control"] == True].copy()
    for subtype in MAIN_SUBTYPES:
        pwa = ab[ab["subtype"] == subtype].copy()
        if len(pwa) < 30:
            continue
        lo, hi = pwa["mlu_words"].dropna().quantile([0.1, 0.9])
        child = chi[(chi["mlu_words"] >= lo) & (chi["mlu_words"] <= hi)].copy()
        ctl = ctrl[(ctrl["mlu_words"] >= lo) & (ctrl["mlu_words"] <= hi)].copy()
        if len(child) < 30 or len(ctl) < 20:
            continue
        for fs_name, fs_cols in feature_sets.items():
            pwa_tab = _entity_aggregate(
                pwa,
                "participant_id",
                fs_cols,
                ["corpus", "subtype", "mlu_words"],
                "pwa",
                "AB_PWA",
            )
            child_tab = _entity_aggregate(
                child,
                "child_id",
                fs_cols,
                ["corpus", "bundle", "age_months", "mlu_words"],
                "child",
                "CHILDES",
            )
            ctl_tab = _entity_aggregate(
                ctl,
                "participant_id",
                fs_cols,
                ["corpus", "subtype", "mlu_words"],
                "control",
                "AB_control",
            )
            pwa_eval_df = balanced_downsample(
                pd.concat([pwa_tab, child_tab], ignore_index=True), "label", seed=0
            )
            ctl_eval_df = balanced_downsample(
                pd.concat(
                    [ctl_tab, child_tab.assign(label="child")], ignore_index=True
                ),
                "label",
                seed=1,
            )
            for cv_name, cv_mode, group_col in [
                ("balanced_entity", "stratified", None),
                ("leave_corpus_out", "group", "source_corpus"),
            ]:
                pwa_res = _binary_eval(
                    pwa_eval_df,
                    fs_cols,
                    "pwa",
                    cv_name,
                    cv_mode,
                    group_col,
                    cv_folds,
                    n_boot,
                )
                ctl_res = _binary_eval(
                    ctl_eval_df,
                    fs_cols,
                    "control",
                    cv_name,
                    cv_mode,
                    group_col,
                    cv_folds,
                    n_boot,
                )
                rows.append(
                    {
                        "subtype": subtype,
                        "feature_set": fs_name,
                        "n_features": len(fs_cols),
                        "mlu_lo": float(lo),
                        "mlu_hi": float(hi),
                        "cv": cv_name,
                        "pwa_f1": pwa_res["f1"],
                        "pwa_f1_ci_low": pwa_res["f1_ci_low"],
                        "pwa_f1_ci_high": pwa_res["f1_ci_high"],
                        "control_f1": ctl_res["f1"],
                        "control_f1_ci_low": ctl_res["f1_ci_low"],
                        "control_f1_ci_high": ctl_res["f1_ci_high"],
                        "delta_f1": pwa_res["f1"] - ctl_res["f1"],
                        "delta_f1_conservative_low": pwa_res["f1_ci_low"] - ctl_res["f1_ci_high"],
                        "n_pwa_entities": int((pwa_eval_df["label"] == "pwa").sum()),
                        "n_child_entities": int((pwa_eval_df["label"] == "child").sum()),
                        "n_control_entities": int((ctl_eval_df["label"] == "control").sum()),
                    }
                )
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "broca_falsification.csv", index=False)

    neg_rows = []
    fs_cols = feature_sets["artifact_safe"]
    broca = ab[ab["subtype"] == "Broca"].copy()
    lo, hi = broca["mlu_words"].dropna().quantile([0.1, 0.9])
    child = chi[(chi["mlu_words"] >= lo) & (chi["mlu_words"] <= hi)].copy()
    broca_tab = _entity_aggregate(
        broca, "participant_id", fs_cols, ["corpus", "subtype", "mlu_words"], "pwa", "AB_PWA"
    )
    child_tab = _entity_aggregate(
        child, "child_id", fs_cols, ["corpus", "bundle", "age_months", "mlu_words"], "child", "CHILDES"
    )
    base = balanced_downsample(pd.concat([broca_tab, child_tab], ignore_index=True), "label", seed=2)
    shuffled = base.copy()
    rng = np.random.default_rng(0)
    shuffled["label"] = rng.permutation(shuffled["label"].to_numpy())
    neg_rows.append({"control": "shuffled_labels", **_binary_eval(shuffled, fs_cols, "pwa", "balanced_entity", "stratified", None, cv_folds, n_boot)})
    random_df = base[["entity_id", "label"]].copy()
    for j in range(16):
        random_df[f"rand_{j:02d}"] = rng.normal(size=len(random_df))
    neg_rows.append({"control": "random_features", **_binary_eval(random_df, [f"rand_{j:02d}" for j in range(16)], "pwa", "balanced_entity", "stratified", None, cv_folds, n_boot)})
    high_ctl = ctrl[ctrl["mlu_words"] > hi].copy()
    high_child = chi[chi["mlu_words"] > hi].copy()
    if len(high_ctl) >= 30 and len(high_child) >= 30:
        high_ctl_tab = _entity_aggregate(high_ctl, "participant_id", fs_cols, ["corpus", "mlu_words"], "control", "AB_control_high_mlu")
        high_child_tab = _entity_aggregate(high_child, "child_id", fs_cols, ["corpus", "bundle", "age_months", "mlu_words"], "child", "CHILDES_high_mlu")
        high_df = balanced_downsample(pd.concat([high_ctl_tab, high_child_tab], ignore_index=True), "label", seed=3)
        neg_rows.append({"control": "high_mlu_adult_control_vs_child", **_binary_eval(high_df, fs_cols, "control", "balanced_entity", "stratified", None, cv_folds, n_boot)})
    pd.DataFrame(neg_rows).to_csv(out_dir / "broca_negative_controls.csv", index=False)


def run_multimodal_mechanisms(
    out_dir: Path,
    pat: pd.DataFrame,
    feature_cols: list[str],
    emb_cols: list[str],
    ac_cols: list[str],
    cv_folds: int,
    n_boot: int,
    emb_pca_d: int,
) -> None:
    print("[mechanisms] pairwise subtype ablations")
    pairs = [
        ("Wernicke", "Anomic"),
        ("Wernicke", "Conduction"),
        ("Conduction", "Anomic"),
        ("Broca", "Control"),
    ]
    ac_groups = {
        group: [c for c in cols if c in ac_cols] for group, cols in ACOUSTIC_GROUPS.items()
    }
    setups = {
        "structural": {"structural": feature_cols},
        "embedding": {"embedding": emb_cols},
        "acoustic_all": {"acoustic": ac_cols},
        "acoustic_timing": {"acoustic": ac_groups["timing"]},
        "acoustic_pitch": {"acoustic": ac_groups["pitch"]},
        "acoustic_voice_quality": {"acoustic": ac_groups["voice_quality"]},
        "acoustic_intensity": {"acoustic": ac_groups["intensity"]},
        "structural+embedding+acoustic": {
            "structural": feature_cols,
            "embedding": emb_cols,
            "acoustic": ac_cols,
        },
    }
    rows = []
    for a, b in pairs:
        sub = pat[pat["subtype_filled"].isin([a, b])].copy()
        if len(sub) < 20 or sub["subtype_filled"].nunique() < 2:
            continue
        sub = balanced_downsample(sub, "subtype_filled", seed=4)
        for setup, blocks in setups.items():
            if not any(blocks.values()):
                continue
            for cv_name, cv_mode, group_col in [
                ("balanced_patient", "stratified", None),
                ("corpus_held_out", "group", "corpus"),
            ]:
                y, pred = cross_val_predict_classifier(
                    sub,
                    "subtype_filled",
                    blocks,
                    group_col=group_col,
                    cv_mode=cv_mode,
                    n_splits=cv_folds,
                    emb_pca_d=emb_pca_d,
                )
                ci_mean, ci_lo, ci_hi = bootstrap_ci(
                    y,
                    pred,
                    macro_f1_metric,
                    groups=sub[group_col].to_numpy() if group_col else None,
                    n_boot=n_boot,
                )
                rows.append(
                    {
                        "pair": f"{a}_vs_{b}",
                        "setup": setup,
                        "cv": cv_name,
                        **classification_summary(y, pred),
                        "macro_f1_ci_low": ci_lo,
                        "macro_f1_ci_high": ci_hi,
                    }
                )
    pd.DataFrame(rows).to_csv(out_dir / "multimodal_mechanisms.csv", index=False)


def _load_results(path: Path) -> pd.DataFrame:
    res = pd.read_excel(path, sheet_name="Time 1")
    res.columns = [c.replace("\n", " ").strip() for c in res.columns]
    res = res.rename(columns={"Participant ID": "participant_id"})
    res["participant_id"] = res["participant_id"].astype(str).str.strip()
    res["__pid_lc"] = res["participant_id"].str.lower()
    for _, (col, _) in OUTCOMES.items():
        if col in res.columns:
            res[col] = pd.to_numeric(res[col], errors="coerce")
    return res


def run_wab_subtests(
    out_dir: Path,
    pat: pd.DataFrame,
    feature_cols: list[str],
    emb_cols: list[str],
    ac_cols: list[str],
    results_xlsx: Path,
    cv_folds: int,
    emb_pca_d: int,
) -> None:
    print("[WAB subtests] fold-clean decomposition")
    res = _load_results(results_xlsx)
    work = pat.copy()
    work["__pid_lc"] = work["participant_id"].astype(str).str.lower()
    joined = work.merge(res, on="__pid_lc", how="inner", suffixes=("", "_res"))
    setups = {
        "structural_only": ({"structural": feature_cols}, []),
        "embedding_only": ({"embedding": emb_cols}, []),
        "acoustic_only": ({"acoustic": ac_cols}, []),
        "structural+embedding": ({"structural": feature_cols, "embedding": emb_cols}, []),
        "structural+acoustic": ({"structural": feature_cols, "acoustic": ac_cols}, []),
        "full_no_subtype": ({"structural": feature_cols, "embedding": emb_cols, "acoustic": ac_cols}, []),
        "subtype_only": ({}, ["subtype_filled"]),
        "subtype+structural": ({"structural": feature_cols}, ["subtype_filled"]),
        "subtype+full": (
            {"structural": feature_cols, "embedding": emb_cols, "acoustic": ac_cols},
            ["subtype_filled"],
        ),
    }
    rows = []
    for label, (col, dimension) in OUTCOMES.items():
        if col not in joined.columns:
            continue
        sub = joined.dropna(subset=[col]).reset_index(drop=True)
        if len(sub) < 50:
            continue
        sub = sub.rename(columns={col: "_target"})
        for setup, (blocks, cats) in setups.items():
            for cv_name, cv_mode, group_col in [
                ("patient_kfold", "kfold", None),
                ("corpus_held_out", "group", "corpus"),
            ]:
                y, pred = cross_val_predict_regressor(
                    sub,
                    "_target",
                    blocks,
                    categorical_cols=cats,
                    group_col=group_col,
                    cv_mode=cv_mode,
                    n_splits=cv_folds,
                    emb_pca_d=emb_pca_d,
                )
                rows.append(
                    {
                        "outcome": label,
                        "dimension": dimension,
                        "setup": setup,
                        "cv": cv_name,
                        **regression_summary(y, pred),
                    }
                )
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "wab_subtests_strict.csv", index=False)
    if not out.empty:
        best = out.loc[out.groupby(["outcome", "cv"])["r"].idxmax()].copy()
        best.to_csv(out_dir / "wab_subtests_best_by_outcome.csv", index=False)


def run_longitudinal_state_change(
    out_dir: Path,
    ab: pd.DataFrame,
    feature_cols: list[str],
    cv_folds: int,
) -> None:
    print("[longitudinal] state change before WAB change")
    session = aggregate_rows(
        ab,
        "participant_id",
        feature_cols,
        ["wab_aq", "subtype", "corpus", "session_date"],
    )
    session = add_patient_root(session)
    X = session[feature_cols].to_numpy(dtype=float)
    X_pos = MinMaxScaler().fit_transform(X)
    nmf = NMF(n_components=8, init="nndsvda", random_state=0, max_iter=2000)
    Z = nmf.fit_transform(X_pos)
    for j in range(Z.shape[1]):
        session[f"nmf{j+1}"] = Z[:, j]

    pairs = []
    for root, g in session.groupby("patient_root"):
        g = g.copy()
        if len(g) < 2:
            continue
        if g["session_date"].notna().any():
            g["_date"] = pd.to_datetime(g["session_date"], errors="coerce")
            g = g.sort_values(["_date", "session_letter", "participant_id"])
        else:
            g = g.sort_values(["session_letter", "participant_id"])
        for i in range(len(g) - 1):
            a, b = g.iloc[i], g.iloc[i + 1]
            za = a[[f"nmf{j+1}" for j in range(8)]].to_numpy(dtype=float)
            zb = b[[f"nmf{j+1}" for j in range(8)]].to_numpy(dtype=float)
            dt = np.nan
            if pd.notna(a.get("session_date")) and pd.notna(b.get("session_date")):
                dt = (pd.to_datetime(b["session_date"]) - pd.to_datetime(a["session_date"])).days
            if not np.isfinite(dt) or dt <= 0:
                dt = float(i + 1)
            row = {
                "patient_root": root,
                "from_session": a["participant_id"],
                "to_session": b["participant_id"],
                "corpus": a["corpus"],
                "subtype": a["subtype"],
                "dt_days": dt,
                "aq_t1": a["wab_aq"],
                "aq_t2": b["wab_aq"],
                "delta_aq": b["wab_aq"] - a["wab_aq"] if pd.notna(a["wab_aq"]) and pd.notna(b["wab_aq"]) else np.nan,
                "state_l2_change": float(np.linalg.norm(zb - za)),
            }
            for j in range(8):
                row[f"delta_nmf{j+1}"] = float(zb[j] - za[j])
                row[f"dzdt_nmf{j+1}"] = float((zb[j] - za[j]) / dt)
            pairs.append(row)
    pair_df = pd.DataFrame(pairs)
    pair_df.to_csv(out_dir / "longitudinal_state_pairs.csv", index=False)
    if pair_df.empty:
        return
    have_aq = pair_df.dropna(subset=["delta_aq"]).copy()
    stable = have_aq[have_aq["delta_aq"].abs() <= 5]
    changed = have_aq[have_aq["delta_aq"].abs() > 5]
    rows = []
    for group_name, group in [("stable_wab", stable), ("changed_wab", changed), ("all_with_aq", have_aq)]:
        if len(group) == 0:
            continue
        rows.append(
            {
                "group": group_name,
                "n_pairs": len(group),
                "mean_abs_delta_aq": float(group["delta_aq"].abs().mean()),
                "mean_state_l2_change": float(group["state_l2_change"].mean()),
                "r_state_change_abs_delta_aq": pearson_safe(
                    group["state_l2_change"], group["delta_aq"].abs()
                ),
            }
        )
    pd.DataFrame(rows).to_csv(out_dir / "longitudinal_stable_wab_summary.csv", index=False)

    first_pairs = pair_df.sort_values(["patient_root", "from_session"]).groupby("patient_root").head(1)
    final_rows = []
    for root, g in session.groupby("patient_root"):
        g = g.dropna(subset=["wab_aq"]).copy()
        if len(g) < 3:
            continue
        if g["session_date"].notna().any():
            g["_date"] = pd.to_datetime(g["session_date"], errors="coerce")
            g = g.sort_values(["_date", "session_letter", "participant_id"])
        else:
            g = g.sort_values(["session_letter", "participant_id"])
        fp = first_pairs[first_pairs["patient_root"] == root]
        if fp.empty:
            continue
        first, last = g.iloc[0], g.iloc[-1]
        row = {
            "patient_root": root,
            "corpus": first["corpus"],
            "subtype": first["subtype"],
            "baseline_aq": first["wab_aq"],
            "final_delta_aq": last["wab_aq"] - first["wab_aq"],
            "early_state_l2_change": fp.iloc[0]["state_l2_change"],
        }
        for j in range(8):
            row[f"early_dzdt_nmf{j+1}"] = fp.iloc[0][f"dzdt_nmf{j+1}"]
            row[f"baseline_nmf{j+1}"] = first[f"nmf{j+1}"]
        final_rows.append(row)
    final_df = pd.DataFrame(final_rows)
    final_df.to_csv(out_dir / "longitudinal_early_change_final_outcome.csv", index=False)
    if len(final_df) >= 20:
        cols = [c for c in final_df.columns if c.startswith("early_dzdt_") or c.startswith("baseline_nmf")]
        y, pred = cross_val_predict_regressor(
            final_df,
            "final_delta_aq",
            {"state": cols + ["baseline_aq"]},
            group_col=None,
            cv_mode="kfold",
            n_splits=min(cv_folds, len(final_df)),
        )
        pd.DataFrame([{**regression_summary(y, pred)}]).to_csv(
            out_dir / "longitudinal_final_delta_prediction.csv", index=False
        )


def _parse_salem_yaml(path: Path) -> pd.DataFrame:
    text = path.read_text(encoding="utf-8", errors="ignore")
    blocks = re.split(r"\n- !Session\n", text)
    rows = []
    for block in blocks:
        m = re.search(r"session_id:\s*([A-Za-z0-9_-]+)", block)
        if not m:
            continue
        sid = m.group(1)
        template_lines = []
        target_words = []
        in_template = False
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("template_texts:"):
                in_template = True
                continue
            if in_template and stripped.startswith("- "):
                template_lines.append(stripped[2:].strip("'\""))
                continue
            if in_template and not stripped.startswith("- "):
                in_template = False
            if "target_text:" in stripped:
                target_words.append(stripped.split("target_text:", 1)[1].strip().strip("'\""))
        text_joined = " ".join(template_lines)
        text_joined = re.sub(r"\{[^}]+\}", " ", text_joined.lower())
        target_joined = " ".join(target_words).lower()
        all_text = f"{text_joined} {target_joined}"
        tokens = re.findall(r"[a-z]+", all_text)
        token_set = set(tokens)
        concept_hits = {}
        for concept, terms in CINDERELLA_CONCEPTS.items():
            concept_hits[concept] = int(any(term in token_set for term in terms))
        rows.append(
            {
                "session_id": sid,
                "n_tokens_proxy": len(tokens),
                "concept_coverage": int(sum(concept_hits.values())),
                "concept_density": float(sum(concept_hits.values()) / max(len(tokens), 1)),
                "target_word_count": len(target_words),
                **{f"concept_{k}": v for k, v in concept_hits.items()},
            }
        )
    return pd.DataFrame(rows)


def run_ciu_proxy(
    out_dir: Path,
    ab: pd.DataFrame,
    feature_cols: list[str],
    salem_csv: Path,
    salem_yaml: Path,
    cv_folds: int,
) -> None:
    print("[CIU proxy] Salem/Cinderella concept coverage")
    if not salem_csv.exists() or not salem_yaml.exists():
        pd.DataFrame([{"status": "missing_salem_files"}]).to_csv(
            out_dir / "ciu_proxy_status.csv", index=False
        )
        return
    salem = pd.read_csv(salem_csv)
    salem.columns = [c.replace(" ", "_") for c in salem.columns]
    salem["wab_aq"] = pd.to_numeric(salem["wab_aq_index_(CHAT)"], errors="coerce")
    salem["n_targets"] = pd.to_numeric(salem["n_targets_(CHAT)"], errors="coerce")
    concept = _parse_salem_yaml(salem_yaml)
    salem = salem.merge(concept, on="session_id", how="left")
    salem.to_csv(out_dir / "ciu_proxy_session_features.csv", index=False)
    metric_cols = ["n_targets", "concept_coverage", "concept_density", "target_word_count"]
    corr_rows = []
    for col in metric_cols:
        sub = salem.dropna(subset=[col, "wab_aq"])
        corr_rows.append(
            {
                "metric": col,
                "n": len(sub),
                "r_with_wab_aq": pearson_safe(sub[col], sub["wab_aq"]),
            }
        )
    pd.DataFrame(corr_rows).to_csv(out_dir / "ciu_proxy_correlations.csv", index=False)

    rows = []
    salem_model = salem.dropna(subset=["wab_aq"]).copy()
    if len(salem_model) >= 50:
        y, pred = cross_val_predict_regressor(
            salem_model,
            "wab_aq",
            {"concept": metric_cols},
            cv_mode="kfold",
            n_splits=cv_folds,
        )
        rows.append(
            {
                "task": "salem_only_wab_aq_regression",
                "setup": "concept_only",
                "sample": "full_salem",
                **regression_summary(y, pred),
            }
        )
    salem_cls = salem.dropna(subset=["wab_type"]).copy()
    keep = salem_cls["wab_type"].value_counts()
    keep = keep[keep >= 10].index.tolist()
    salem_cls = salem_cls[salem_cls["wab_type"].isin(keep)].reset_index(drop=True)
    if len(salem_cls) >= 50 and salem_cls["wab_type"].nunique() >= 2:
        y, pred = cross_val_predict_classifier(
            salem_cls,
            "wab_type",
            {"concept": metric_cols},
            cv_mode="stratified",
            n_splits=cv_folds,
        )
        rows.append(
            {
                "task": "salem_only_subtype_classification",
                "setup": "concept_only",
                "sample": "full_salem",
                **classification_summary(y, pred),
            }
        )

    feats = ab.copy()
    feats["session_id"] = feats["participant_id"]
    joined = feats.merge(
        salem[["session_id", "wab_aq", "wab_type"] + metric_cols],
        on="session_id",
        how="inner",
        suffixes=("", "_salem"),
    )
    if joined.empty:
        pd.DataFrame(rows).to_csv(out_dir / "ciu_proxy_models.csv", index=False)
        return
    pat = aggregate_rows(
        joined,
        "session_id",
        feature_cols + metric_cols,
        ["subtype", "corpus", "wab_aq_salem", "wab_type"],
    )
    pat = pat.rename(columns={"wab_aq_salem": "salem_wab_aq"})
    setups = {
        "concept_only": {"concept": metric_cols},
        "structural_only": {"structural": feature_cols},
        "structural+concept": {"structural": feature_cols, "concept": metric_cols},
    }
    target = "salem_wab_aq" if "salem_wab_aq" in pat.columns else "wab_aq"
    if target in pat.columns and pat[target].notna().sum() >= 50:
        for setup, blocks in setups.items():
            y, pred = cross_val_predict_regressor(
                pat.dropna(subset=[target]),
                target,
                blocks,
                group_col="corpus",
                cv_mode="group",
                n_splits=cv_folds,
            )
            rows.append({"task": "wab_aq_regression", "setup": setup, **regression_summary(y, pred)})
    cls = pat.dropna(subset=["wab_type"]).copy()
    keep = cls["wab_type"].value_counts()
    keep = keep[keep >= 5].index.tolist()
    cls = cls[cls["wab_type"].isin(keep)].reset_index(drop=True)
    if len(cls) >= 40 and cls["wab_type"].nunique() >= 2:
        for setup, blocks in setups.items():
            y, pred = cross_val_predict_classifier(
                cls,
                "wab_type",
                blocks,
                group_col="corpus",
                cv_mode="group",
                n_splits=cv_folds,
            )
            rows.append({"task": "subtype_classification", "setup": setup, **classification_summary(y, pred)})
    if len(pat) < 50:
        rows.append(
            {
                "task": "structural_join_status",
                "setup": "not_run",
                "sample": "aphasiabank_salem_intersection",
                "n": int(len(pat)),
                "note": "Too few intersecting sessions for structural-vs-concept CV.",
            }
        )
    pd.DataFrame(rows).to_csv(out_dir / "ciu_proxy_models.csv", index=False)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)

    print("[load] strict datasets")
    ab, ab_audit = load_ab_windowed(args.aphasia_features)
    chi, chi_audit = load_td_childes(args.childes_features)
    embeddings, emb_cols, emb_audit = load_embeddings(args.embeddings_path)
    acoustics, ac_cols, ac_audit = load_acoustics(args.acoustic_pattern)

    feature_cols = numeric_feature_columns(ab, AB_META)
    chi_feature_cols = numeric_feature_columns(chi, CHI_META)
    common = sorted(set(feature_cols) & set(chi_feature_cols))
    safe_common = artifact_safe_features(chi, ab, common, mode="artifact_safe")

    run_data_audit(out_dir, ab_audit, chi_audit, emb_audit, ac_audit, ab, chi)
    run_principal_angles(out_dir, chi, ab, safe_common)

    pat_modal = modality_table(
        ab,
        feature_cols,
        embeddings,
        emb_cols,
        acoustics,
        ac_cols,
        require_embeddings=True,
        require_acoustic=True,
    )
    run_strict_acoustic_replication(
        out_dir,
        pat_modal,
        feature_cols,
        emb_cols,
        ac_cols,
        args.cv_folds,
        args.bootstrap,
        args.emb_pca_d,
    )
    run_broca_falsification(out_dir, chi, ab, common, args.cv_folds, args.bootstrap)
    run_multimodal_mechanisms(
        out_dir,
        pat_modal,
        feature_cols,
        emb_cols,
        ac_cols,
        args.cv_folds,
        args.bootstrap,
        args.emb_pca_d,
    )
    run_wab_subtests(
        out_dir,
        pat_modal,
        feature_cols,
        emb_cols,
        ac_cols,
        args.results_xlsx,
        args.cv_folds,
        args.emb_pca_d,
    )
    run_longitudinal_state_change(out_dir, ab, feature_cols, args.cv_folds)
    run_ciu_proxy(out_dir, ab, feature_cols, args.salem_csv, args.salem_yaml, args.cv_folds)

    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
