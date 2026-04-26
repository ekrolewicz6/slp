"""Within-subtype phenotyping + early trajectory-class prediction.

Two follow-up analyses on the AphasiaBank features:

  A. **Within-subtype phenotyping.** For each major aphasia subtype
     (Anomic, Broca, Conduction, Wernicke), project patients into z and
     KMeans-split into 2 sub-clusters. Compare the sub-clusters on
     baseline severity, trajectory direction, and demographics. Tests
     the strongest version of the project hypothesis: *if two patients
     share the same diagnostic label but z separates them, the
     categorical label is hiding clinically meaningful heterogeneity.*

  B. **Trajectory-class prediction.** Define each longitudinal patient
     as Improver (ΔAQ ≥ +5), Stable (|ΔAQ| < 5), or Decliner
     (ΔAQ ≤ −5). Train a classifier to predict the class from
     **session-1 features alone** with patient-grouped CV. Compare to:
     (a) majority-class baseline, (b) subtype + baseline-AQ baseline.

If the within-subtype splits separate patients on outcome and the
trajectory classifier beats the majority baseline, we have the
clearest aphasia-data evidence yet that z resolves what subtype hides.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score, confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.stats import ttest_ind, fisher_exact

META_COLS = {"transcript_id", "section", "corpus", "participant_id",
             "patient_root", "session_letter", "age_years",
             "sex", "subtype", "wab_aq", "is_control",
             "session_date", "window_id", "window_index",
             "n_chi_utts_in_window"}

MAJOR_SUBTYPES = ["Anomic", "Broca", "Conduction", "Wernicke"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/phase4_phenotyping", type=Path)
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


def aggregate_session(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    keep = ["patient_root", "session_letter", "session_date", "subtype",
            "wab_aq", "corpus", "section", "participant_id", "is_control",
            "age_years", "sex"]
    return df.groupby("participant_id").agg(
        {**{f: "mean" for f in feature_cols},
         **{m: "first" for m in keep}}
    ).reset_index(drop=True)


def aggregate_patient_first_session(sessions: pd.DataFrame,
                                     feature_cols: list[str]) -> pd.DataFrame:
    """For each patient, keep the FIRST session as the baseline row."""
    return (sessions.sort_values(["patient_root", "session_letter"])
                    .drop_duplicates("patient_root", keep="first")
                    .reset_index(drop=True))


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df["patient_root"] = df["participant_id"].str.replace(r"[a-zA-Z]$", "",
                                                          regex=True)
    df["session_letter"] = df["participant_id"].str.extract(r"([a-zA-Z])$")[0]
    feature_cols = sorted(c for c in df.columns if c not in META_COLS)

    sessions = aggregate_session(df, feature_cols)
    print(f"Sessions: {len(sessions)} | patients: {sessions['patient_root'].nunique()}")

    # Use the FIRST session per patient as their baseline row.
    baseline = aggregate_patient_first_session(sessions, feature_cols)
    print(f"Baseline rows (one per patient): {len(baseline)}")

    # Compute trajectory class for longitudinal-with-AQ subset.
    multi = sessions.dropna(subset=["wab_aq"]).groupby("patient_root").filter(
        lambda g: len(g) >= 2 and g["wab_aq"].notna().sum() >= 2)
    arc = []
    for pat, g in multi.groupby("patient_root"):
        g = g.sort_values("session_letter").dropna(subset=["wab_aq"])
        if len(g) < 2:
            continue
        delta = g["wab_aq"].iloc[-1] - g["wab_aq"].iloc[0]
        if delta >= 5:
            cls = "Improver"
        elif delta <= -5:
            cls = "Decliner"
        else:
            cls = "Stable"
        arc.append({"patient_root": pat, "delta_aq": delta,
                    "trajectory_class": cls,
                    "aq_t1": g["wab_aq"].iloc[0]})
    arc_df = pd.DataFrame(arc)
    print(f"\nLongitudinal patients with AQ at ≥2 timepoints: {len(arc_df)}")
    print(f"  Trajectory class distribution:")
    print(arc_df["trajectory_class"].value_counts().to_string())

    baseline = baseline.merge(arc_df[["patient_root", "delta_aq",
                                       "trajectory_class", "aq_t1"]],
                              on="patient_root", how="left")
    # Use baseline session's AQ when arc-based AQ-t1 is missing.
    baseline["aq_t1"] = baseline["aq_t1"].fillna(baseline["wab_aq"])

    # ----- Phenotyping: KMeans within each major subtype -----
    print("\n=== A. Within-subtype phenotyping ===")
    Xall = StandardScaler().fit_transform(
        baseline[feature_cols].to_numpy(dtype=float))
    pca = PCA(n_components=8, random_state=0).fit(Xall)
    Z = pca.transform(Xall)
    for j in range(8):
        baseline[f"z{j+1}"] = Z[:, j]

    pheno_rows = []
    for subtype in MAJOR_SUBTYPES:
        sub = baseline[baseline["subtype"] == subtype].copy()
        if len(sub) < 30:
            print(f"  {subtype}: n={len(sub)} too small, skip")
            continue
        Zsub = sub[[f"z{j+1}" for j in range(8)]].to_numpy()
        km = KMeans(n_clusters=2, n_init=10, random_state=0).fit(Zsub)
        sub["sub_cluster"] = km.labels_

        # Differences in baseline AQ between sub-clusters
        c0_aq = sub[sub.sub_cluster == 0]["aq_t1"].dropna()
        c1_aq = sub[sub.sub_cluster == 1]["aq_t1"].dropna()
        if len(c0_aq) >= 5 and len(c1_aq) >= 5:
            t, p = ttest_ind(c0_aq, c1_aq, equal_var=False)
        else:
            t, p = float("nan"), float("nan")

        # Trajectory split: if within-subtype longitudinal subset is large enough
        long_sub = sub.dropna(subset=["trajectory_class"])
        traj_table = pd.crosstab(long_sub["sub_cluster"],
                                  long_sub["trajectory_class"])

        pheno_rows.append({
            "subtype": subtype,
            "n_patients": int(len(sub)),
            "n_cluster0": int((sub.sub_cluster == 0).sum()),
            "n_cluster1": int((sub.sub_cluster == 1).sum()),
            "mean_aq_cluster0": float(c0_aq.mean()) if len(c0_aq) else float("nan"),
            "mean_aq_cluster1": float(c1_aq.mean()) if len(c1_aq) else float("nan"),
            "t_stat_aq": float(t),
            "p_aq": float(p),
            "n_with_traj": int(len(long_sub)),
            "trajectory_table": traj_table.to_dict() if len(long_sub) else {},
        })
        print(f"  {subtype}  n={len(sub)}  "
              f"AQ: c0={c0_aq.mean():.1f} (n={len(c0_aq)}) vs "
              f"c1={c1_aq.mean():.1f} (n={len(c1_aq)})  "
              f"t={t:+.2f}  p={p:.3f}")
        if len(long_sub):
            print(f"    longitudinal n={len(long_sub)}, trajectory by cluster:")
            print("   " + traj_table.to_string().replace("\n", "\n    "))

    pd.DataFrame(pheno_rows).to_csv(
        args.output_dir / "subtype_phenotyping.csv", index=False)

    # ----- Trajectory-class prediction from session-1 features -----
    print("\n=== B. Trajectory-class prediction from session-1 features ===")
    traj = baseline.dropna(subset=["trajectory_class"]).copy()
    print(f"  n patients with trajectory class: {len(traj)}")
    print(f"  class counts: "
          f"{traj['trajectory_class'].value_counts().to_dict()}")

    if len(traj) < 30:
        print("  not enough data for grouped CV")
        return

    Xt = traj[feature_cols].to_numpy(dtype=float)
    yt = traj["trajectory_class"].to_numpy(dtype=object)
    groups = traj["patient_root"].to_numpy()

    sub_arr = traj["subtype"].fillna("Unknown").to_numpy(dtype=object)
    aq_t1 = traj["aq_t1"].fillna(traj["aq_t1"].median()).to_numpy(dtype=float).reshape(-1, 1)

    # Majority baseline.
    counts = pd.Series(yt).value_counts()
    major = counts.idxmax()
    major_acc = float((yt == major).mean())
    print(f"\n  Majority class = {major}; baseline accuracy = {major_acc:.3f}")

    n_groups = len(set(groups))
    splits = max(2, min(args.cv_folds, n_groups))
    gkf = GroupKFold(n_splits=splits)

    def cv_classify(X):
        preds = np.empty_like(yt, dtype=object)
        for tr, te in gkf.split(X, yt, groups):
            if len(set(yt[tr])) < 2:
                preds[te] = yt[tr][0]
                continue
            clf = GradientBoostingClassifier(
                n_estimators=300, max_depth=3, learning_rate=0.05,
                subsample=0.9, random_state=0).fit(X[tr], yt[tr])
            preds[te] = clf.predict(X[te])
        return preds, float((preds == yt).mean()), float(
            f1_score(yt, preds, average="macro", zero_division=0))

    # Setups
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    sub_oh = enc.fit_transform(sub_arr.reshape(-1, 1))
    setups = {
        "subtype_only": sub_oh,
        "aq_t1_only": aq_t1,
        "subtype_plus_aq_t1": np.concatenate([sub_oh, aq_t1], axis=1),
        "features_only": Xt,
        "features_plus_subtype": np.concatenate([Xt, sub_oh], axis=1),
        "features_plus_aq_t1": np.concatenate([Xt, aq_t1], axis=1),
        "features_plus_subtype_plus_aq_t1": np.concatenate([Xt, sub_oh, aq_t1], axis=1),
    }

    rows_b = []
    print()
    for name, X in setups.items():
        preds, acc, mf1 = cv_classify(X)
        print(f"  {name:38s}  acc={acc:.3f}  macroF1={mf1:.3f}")
        rows_b.append({"setup": name, "accuracy": acc, "macro_f1": mf1})
    pd.DataFrame(rows_b).to_csv(
        args.output_dir / "trajectory_class_prediction.csv", index=False)

    # Confusion matrix on the best setup (features_plus_subtype_plus_aq_t1)
    best_X = setups["features_plus_subtype_plus_aq_t1"]
    best_preds, best_acc, best_mf1 = cv_classify(best_X)
    classes = sorted(set(yt) | set(best_preds))
    cm = confusion_matrix(yt, best_preds, labels=classes)
    print(f"\n  Confusion matrix (rows=true, cols=pred), best setup:")
    print(f"  classes: {classes}")
    for i, row in enumerate(cm):
        print(f"    {classes[i]:10s}  " + "  ".join(f"{v:>4d}" for v in row))

    # ----- Visualizations -----
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, subtype in zip(axes.flatten(), MAJOR_SUBTYPES):
        sub = baseline[baseline["subtype"] == subtype]
        if len(sub) < 30:
            ax.set_title(f"{subtype} (n={len(sub)}, too small)"); continue
        Zs = sub[["z1", "z2"]].to_numpy()
        # color by baseline AQ
        sc = ax.scatter(Zs[:, 0], Zs[:, 1], c=sub["aq_t1"], cmap="RdYlGn",
                        vmin=0, vmax=100, s=30, alpha=0.7)
        # overlay trajectory class
        for cls, marker, color in [
            ("Improver", "^", "blue"), ("Decliner", "v", "red"),
        ]:
            m = sub[sub["trajectory_class"] == cls]
            if len(m):
                ax.scatter(m["z1"], m["z2"], marker=marker, s=120,
                           facecolors="none", edgecolors=color, linewidths=2,
                           label=f"{cls} (n={len(m)})")
        ax.set_title(f"{subtype} (n={len(sub)})")
        ax.set_xlabel("z1"); ax.set_ylabel("z2")
        ax.legend(loc="best", fontsize=8)
        ax.grid(alpha=0.3)
        plt.colorbar(sc, ax=ax, label="baseline AQ")
    fig.tight_layout()
    fig.savefig(args.output_dir / "subtype_phenotyping_z12.png", dpi=150)
    plt.close(fig)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
