"""Phase 3 on aphasia: predict ΔWAB-AQ between sessions from features at t1.

The headline question this answers:

    Does our continuous representation predict things that the categorical
    subtype label cannot?

Setup. Identify patients with ≥2 sessions (paired by patient_root, dropping
the trailing letter that orders Time 1 / Time 2 / ...). For each ordered
pair (t1, t2), build a row with:

    - features at t1 (mean over t1's windows)
    - WAB-AQ at t1                                (the "baseline severity")
    - subtype at t1
    - WAB-AQ at t2                                (the target)
    - Δt in days (from @Date headers)

Models compared, all under participant-grouped 5-fold CV (so a patient
never appears in both train and test):

    1. no_change             — predict aq_t2 = aq_t1
    2. baseline_aq_only      — GBM on (aq_t1, Δt)
    3. subtype_only          — GBM on one-hot subtype
    4. baseline_aq + subtype — GBM on (aq_t1, Δt, subtype)
    5. + features at t1      — GBM on (aq_t1, Δt, subtype, 55 features)
    6. + z=8 at t1           — GBM on (aq_t1, Δt, subtype, z₁..₈)

The interesting comparison is (4) vs (5): does adding features improve
prediction of the *next session's* AQ beyond what baseline AQ + subtype
already give us?

We also evaluate on the change-significant subset (|Δaq| ≥ 5 AQ points)
where there's actually room to improve over no-change.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.stats import pearsonr


META_COLS = {"transcript_id", "section", "corpus", "participant_id",
             "patient_root", "session_letter", "age_years",
             "sex", "subtype", "wab_aq", "is_control",
             "session_date", "window_id", "window_index",
             "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/phase3_aphasia", type=Path)
    p.add_argument("--cv-folds", type=int, default=5)
    return p.parse_args()


def aggregate_session(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """One row per session = mean features, with metadata."""
    keep = ["patient_root", "session_letter", "session_date", "subtype",
            "wab_aq", "corpus", "participant_id", "is_control"]
    agg = df.groupby("participant_id").agg(
        {**{f: "mean" for f in feature_cols},
         **{m: "first" for m in keep}}
    ).reset_index(drop=True)
    return agg


def build_pairs(sessions: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """For each patient, build (t1, t2) ordered pairs.

    Includes pairs (s1, s2), (s2, s3), … not just first→last, so a patient
    with 4 sessions contributes 3 pairs (with the same patient_root grouping
    so CV doesn't leak).
    """
    rows = []
    for pat, g in sessions.groupby("patient_root"):
        g = g.sort_values("session_letter").reset_index(drop=True)
        if len(g) < 2:
            continue
        for i in range(len(g) - 1):
            r1, r2 = g.iloc[i], g.iloc[i + 1]
            if pd.isna(r1["wab_aq"]) or pd.isna(r2["wab_aq"]):
                continue
            # Δt in days from session_date if available
            d1, d2 = r1.get("session_date"), r2.get("session_date")
            dt_days = None
            if isinstance(d1, str) and isinstance(d2, str):
                try:
                    dt_days = (datetime.fromisoformat(d2) -
                               datetime.fromisoformat(d1)).days
                except ValueError:
                    dt_days = None
            row = {
                "patient_root": pat,
                "corpus": r1["corpus"],
                "subtype_t1": r1["subtype"],
                "aq_t1": r1["wab_aq"],
                "aq_t2": r2["wab_aq"],
                "delta_aq": r2["wab_aq"] - r1["wab_aq"],
                "delta_t_days": dt_days,
                "session_letter_t1": r1["session_letter"],
                "session_letter_t2": r2["session_letter"],
            }
            for f in feature_cols:
                row[f"f1_{f}"] = r1[f]
            rows.append(row)
    return pd.DataFrame(rows)


def cv_predict(X, y, groups, n_splits, model_factory):
    n_groups = len(set(groups))
    splits = max(2, min(n_splits, n_groups))
    gkf = GroupKFold(n_splits=splits)
    preds = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(X, y, groups):
        m = model_factory()
        m.fit(X[tr], y[tr])
        preds[te] = m.predict(X[te])
    err = preds - y
    r = float(pearsonr(y, preds)[0]) if np.std(preds) > 0 else float("nan")
    return {"mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(err ** 2))),
            "r": r,
            "preds": preds}


def gbm_factory():
    return GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0,
    )


def onehot(values: np.ndarray, all_values: list[str]) -> np.ndarray:
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore",
                        categories=[all_values])
    return enc.fit_transform(values.reshape(-1, 1))


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[load] {args.features_path}")
    df = pd.read_parquet(args.features_path)
    df["patient_root"] = df["participant_id"].str.replace(r"[a-zA-Z]$", "",
                                                          regex=True)
    df["session_letter"] = df["participant_id"].str.extract(r"([a-zA-Z])$")[0]

    feature_cols = sorted(c for c in df.columns if c not in META_COLS)
    print(f"  {len(df)} windows | {len(feature_cols)} features")

    # ----- Aggregate windows → sessions -----
    sessions = aggregate_session(df, feature_cols)
    sessions = sessions.dropna(subset=["wab_aq"])
    print(f"  sessions with WAB-AQ: {len(sessions)} from "
          f"{sessions['patient_root'].nunique()} patients")

    # ----- Build trajectory pairs -----
    pairs = build_pairs(sessions, feature_cols)
    print(f"\n[pairs] {len(pairs)} (t1, t2) pairs from "
          f"{pairs['patient_root'].nunique()} patients")
    if not len(pairs):
        print("[!] No pairs found.")
        return
    print(f"  Δt (days): "
          f"mean={pairs['delta_t_days'].dropna().mean():.0f}  "
          f"median={pairs['delta_t_days'].dropna().median():.0f}  "
          f"non-null {pairs['delta_t_days'].notna().sum()}/{len(pairs)}")
    print(f"  Δaq: mean={pairs['delta_aq'].mean():+.2f}  "
          f"std={pairs['delta_aq'].std():.2f}  "
          f"|Δ|≥5: {(pairs['delta_aq'].abs()>=5).sum()}  "
          f"|Δ|≥10: {(pairs['delta_aq'].abs()>=10).sum()}")

    pairs.to_csv(args.output_dir / "pairs.csv", index=False)

    # ----- Modelling -----
    # Δt as a feature: fill missing with the median (no leak across folds for
    # this — the median is computed on the full data once).
    pairs["delta_t_days_filled"] = pairs["delta_t_days"].fillna(
        pairs["delta_t_days"].median())

    y = pairs["aq_t2"].to_numpy(dtype=float)
    groups = pairs["patient_root"].to_numpy()
    feat_t1 = pairs[[f"f1_{f}" for f in feature_cols]].to_numpy(dtype=float)
    aq_t1 = pairs["aq_t1"].to_numpy(dtype=float).reshape(-1, 1)
    dt = pairs["delta_t_days_filled"].to_numpy(dtype=float).reshape(-1, 1)

    sub_arr = pairs["subtype_t1"].fillna("Unknown").to_numpy(dtype=object)
    all_subs = sorted(set(sub_arr))
    sub_oh = onehot(sub_arr, all_subs)

    # Standardise + PCA z=8 on features (fit on full data — fine for our
    # comparative purposes, no information leak about the AQ target).
    Xs_scaled = StandardScaler().fit_transform(feat_t1)
    z8 = PCA(n_components=min(8, feat_t1.shape[1]),
             random_state=0).fit_transform(Xs_scaled)

    rows = []

    # 0. no_change baseline
    err = aq_t1.flatten() - y
    rows.append({"setup": "no_change_aq_t1",
                 "mae": float(np.mean(np.abs(err))),
                 "rmse": float(np.sqrt(np.mean(err ** 2))),
                 "r": float(pearsonr(y, aq_t1.flatten())[0])})
    print(f"\n[baseline] no_change           "
          f"MAE={rows[-1]['mae']:6.2f}  RMSE={rows[-1]['rmse']:6.2f}  "
          f"r={rows[-1]['r']:+.3f}")

    # 1. baseline_aq + Δt
    X_b = np.concatenate([aq_t1, dt], axis=1)
    r = cv_predict(X_b, y, groups, args.cv_folds, gbm_factory)
    rows.append({"setup": "aq_t1_plus_dt",
                 **{k: v for k, v in r.items() if k != "preds"}})
    print(f"[gbm    ] aq_t1 + Δt           "
          f"MAE={r['mae']:6.2f}  r={r['r']:+.3f}")

    # 2. subtype + aq_t1 + Δt
    X_bs = np.concatenate([aq_t1, dt, sub_oh], axis=1)
    r = cv_predict(X_bs, y, groups, args.cv_folds, gbm_factory)
    rows.append({"setup": "aq_t1_plus_dt_plus_subtype",
                 **{k: v for k, v in r.items() if k != "preds"}})
    print(f"[gbm    ] + subtype             "
          f"MAE={r['mae']:6.2f}  r={r['r']:+.3f}")

    # 3. + features (raw 55) at t1
    X_full = np.concatenate([aq_t1, dt, sub_oh, feat_t1], axis=1)
    r = cv_predict(X_full, y, groups, args.cv_folds, gbm_factory)
    feat_full = r
    rows.append({"setup": "aq_t1_plus_dt_plus_subtype_plus_features",
                 **{k: v for k, v in r.items() if k != "preds"}})
    print(f"[gbm    ] + features (raw 55)   "
          f"MAE={r['mae']:6.2f}  r={r['r']:+.3f}")

    # 4. + z=8 at t1
    X_z = np.concatenate([aq_t1, dt, sub_oh, z8], axis=1)
    r = cv_predict(X_z, y, groups, args.cv_folds, gbm_factory)
    rows.append({"setup": "aq_t1_plus_dt_plus_subtype_plus_z8",
                 **{k: v for k, v in r.items() if k != "preds"}})
    print(f"[gbm    ] + z=8                 "
          f"MAE={r['mae']:6.2f}  r={r['r']:+.3f}")

    # 5. features-only (no AQ baseline) — what can we say from speech alone?
    X_f_only = np.concatenate([dt, sub_oh, feat_t1], axis=1)
    r = cv_predict(X_f_only, y, groups, args.cv_folds, gbm_factory)
    rows.append({"setup": "features_plus_subtype_plus_dt_no_aq_t1",
                 **{k: v for k, v in r.items() if k != "preds"}})
    print(f"[gbm    ] features+sub+Δt (no aq_t1) "
          f"MAE={r['mae']:6.2f}  r={r['r']:+.3f}")

    pd.DataFrame(rows).to_csv(
        args.output_dir / "trajectory_metrics.csv", index=False)

    # ----- Direction-of-change task -----
    # The clinically actionable question isn't "predict the next AQ exactly"
    # (test-retest reliability is ~3-5 points; we're already inside noise).
    # It's "given the patient now, will they improve, stay the same, or decline?"
    # — much easier and far more useful.
    print("\n[direction] predict sign(Δaq) over the change-significant subset")
    for threshold in [0, 3, 5]:
        sub_p = pairs[pairs["delta_aq"].abs() >= threshold].reset_index(drop=True)
        if len(sub_p) < 20:
            print(f"  |Δaq|≥{threshold}: only {len(sub_p)} pairs — skip")
            continue
        n_pat = sub_p["patient_root"].nunique()
        sign_y = (sub_p["delta_aq"] > 0).astype(int).to_numpy()
        # baseline: predict majority class
        major = int(sign_y.mean() >= 0.5)
        major_acc = float((sign_y == major).mean())

        ft_b = sub_p[[f"f1_{f}" for f in feature_cols]].to_numpy(dtype=float)
        aq_b = sub_p["aq_t1"].to_numpy(dtype=float).reshape(-1, 1)
        dt_b = sub_p["delta_t_days_filled"].to_numpy(dtype=float).reshape(-1, 1)
        sub_arr_b = sub_p["subtype_t1"].fillna("Unknown").to_numpy(dtype=object)
        sub_b = onehot(sub_arr_b, sorted(set(sub_arr_b)))
        gb = sub_p["patient_root"].to_numpy()

        from sklearn.ensemble import GradientBoostingClassifier
        n_groups = len(set(gb))
        splits = max(2, min(args.cv_folds, n_groups))
        gkf = GroupKFold(n_splits=splits)
        preds = np.zeros_like(sign_y, dtype=int)
        X_full = np.concatenate([aq_b, dt_b, sub_b, ft_b], axis=1)
        for tr, te in gkf.split(X_full, sign_y, gb):
            if len(set(sign_y[tr])) < 2:
                preds[te] = sign_y[tr][0]
                continue
            clf = GradientBoostingClassifier(
                n_estimators=300, max_depth=3, learning_rate=0.05,
                subsample=0.9, random_state=0).fit(X_full[tr], sign_y[tr])
            preds[te] = clf.predict(X_full[te])
        print(f"  |Δaq|≥{threshold}: n={len(sub_p)} ({n_pat} pat), "
              f"improver-rate={sign_y.mean():.2f}, "
              f"majority_acc={major_acc:.3f}, "
              f"learned_acc={float((preds == sign_y).mean()):.3f}")

    # ----- z-space trajectory: predict z_t2 from z_t1 directly -----
    # Maybe AQ is too noisy/coarse; the latent dimensions might be more
    # sensitive to small clinical changes.
    print("\n[z-trajectory] predict z_t2 from z_t1 + Δt + features at t1")
    sessions_z = sessions.copy()
    Xs_all = StandardScaler().fit_transform(
        sessions_z[feature_cols].to_numpy(dtype=float))
    pca8 = PCA(n_components=8, random_state=0).fit(Xs_all)
    Z_all = pca8.transform(Xs_all)
    sessions_z = sessions_z.assign(**{f"z{i+1}": Z_all[:, i] for i in range(8)})

    z_pairs = []
    for pat, g in sessions_z.groupby("patient_root"):
        g = g.sort_values("session_letter").reset_index(drop=True)
        if len(g) < 2:
            continue
        for i in range(len(g) - 1):
            r1, r2 = g.iloc[i], g.iloc[i + 1]
            d1, d2 = r1.get("session_date"), r2.get("session_date")
            try:
                dtd = (datetime.fromisoformat(d2) - datetime.fromisoformat(d1)).days
            except (TypeError, ValueError):
                dtd = None
            row = {"patient_root": pat, "delta_t_days": dtd}
            for j in range(8):
                row[f"z{j+1}_t1"] = r1[f"z{j+1}"]
                row[f"z{j+1}_t2"] = r2[f"z{j+1}"]
            z_pairs.append(row)
    zdf = pd.DataFrame(z_pairs)
    if len(zdf) >= 20:
        zdf["delta_t_filled"] = zdf["delta_t_days"].fillna(zdf["delta_t_days"].median())
        gz = zdf["patient_root"].to_numpy()
        Xz_t1 = zdf[[f"z{j+1}_t1" for j in range(8)]].to_numpy(dtype=float)
        Xz_in = np.concatenate(
            [Xz_t1, zdf["delta_t_filled"].to_numpy(dtype=float).reshape(-1, 1)],
            axis=1)
        per_dim = []
        for j in range(8):
            yz = zdf[f"z{j+1}_t2"].to_numpy(dtype=float)
            no_change = float(np.mean(np.abs(Xz_t1[:, j] - yz)))
            r = cv_predict(Xz_in, yz, gz, args.cv_folds, gbm_factory)
            per_dim.append({"dim": f"z{j+1}",
                            "no_change_mae": no_change,
                            "learned_mae": r["mae"],
                            "r_pearson": r["r"],
                            "delta_mae": r["mae"] - no_change})
            print(f"  z{j+1}  no_change MAE={no_change:.3f}  "
                  f"learned MAE={r['mae']:.3f}  Δ={r['mae']-no_change:+.3f}")
        pd.DataFrame(per_dim).to_csv(
            args.output_dir / "z_trajectory_per_dim.csv", index=False)

    # ----- Visualization: per-patient trajectories -----
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: actual vs predicted aq_t2 from the full model.
    ax = axes[0]
    full_preds = feat_full["preds"]
    ax.scatter(y, full_preds, s=18, alpha=0.6)
    lo, hi = float(min(y.min(), full_preds.min())), float(max(y.max(), full_preds.max()))
    ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="y = x")
    ax.set_xlabel("True aq_t2"); ax.set_ylabel("Predicted aq_t2")
    ax.set_title(f"Full model (MAE={feat_full['mae']:.2f}, r={feat_full['r']:+.3f})")
    ax.legend(); ax.grid(alpha=0.3)

    # Right: per-patient trajectories — actual AQ over session-letter, top 16 patients.
    ax = axes[1]
    long_pats = sessions.groupby("patient_root").size()
    longest = long_pats[long_pats >= 2].sort_values(ascending=False).head(16).index
    cmap = plt.get_cmap("tab20")
    for i, pat in enumerate(longest):
        g = sessions[sessions.patient_root == pat].sort_values("session_letter")
        ax.plot(range(len(g)), g["wab_aq"].values, "o-",
                color=cmap(i % 20), alpha=0.7, lw=1, label=pat)
    ax.set_xlabel("Session index (chronological)")
    ax.set_ylabel("WAB-AQ")
    ax.set_title("Per-patient WAB-AQ trajectories (top 16 longitudinal)")
    ax.legend(loc="lower right", fontsize=7, ncol=2)
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(args.output_dir / "trajectory_summary.png", dpi=150)
    plt.close(fig)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
