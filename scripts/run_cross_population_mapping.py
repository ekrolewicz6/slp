"""Cross-population mapping: place each PWA in the developmental z-space.

Procedure:
  1. Train a GBM age regressor on CHILDES (windowed features ± embeddings)
     so the model knows "what does a 24-month-old vs 60-month-old vs
     84-month-old sound like"
  2. Apply the model to AphasiaBank windows.
  3. Each PWA window gets a "developmental age equivalent" in months —
     the age at which their speech most resembles a typically-developing
     child.
  4. Aggregate to patient-level (mean across windows).
  5. Ask:
       - Does developmental-age-equivalent correlate with WAB-AQ?
       - Do different aphasia subtypes have different developmental
         age profiles?
       - Does it correlate within-subtype with severity?

This is the most novel scientific framing the project produces — no
existing literature compares PWA discourse to a developmental
age-equivalent in a unified embedding space.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr, ttest_ind


CHILDES_META = {"transcript_id", "corpus", "child_id", "age_months",
                "n_chi_utterances", "bundle", "window_id", "window_index",
                "n_chi_utts_in_window"}
AB_META = {"transcript_id", "section", "corpus", "participant_id",
           "patient_root", "session_letter", "age_years",
           "sex", "subtype", "wab_aq", "is_control",
           "session_date", "window_id", "window_index",
           "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--childes-features",
                   default="data/features/phase1_windowed_features.parquet",
                   type=Path)
    p.add_argument("--childes-emb",
                   default="data/features/childes_window_embeddings.parquet",
                   type=Path)
    p.add_argument("--aphasia-features",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--aphasia-emb",
                   default="data/features/aphasia_window_embeddings.parquet",
                   type=Path)
    p.add_argument("--output-dir",
                   default="outputs/cross_population", type=Path)
    p.add_argument("--max-childes-age", type=float, default=84.0)
    p.add_argument("--use-embeddings", action="store_true",
                   help="Concatenate MPNet embeddings to features.")
    p.add_argument("--emb-pca-d", type=int, default=64)
    return p.parse_args()


def load_feature_table(features_path, emb_path, meta_set, use_embeddings,
                       emb_pca_d):
    feats = pd.read_parquet(features_path)
    feature_cols = sorted(c for c in feats.columns if c not in meta_set)
    if not use_embeddings:
        return feats, feature_cols, []
    if not emb_path.exists():
        print(f"  [warn] embeddings not found at {emb_path}; using features only")
        return feats, feature_cols, []
    embs = pd.read_parquet(emb_path)
    df = feats.merge(embs, on="window_id", how="inner")
    emb_cols = sorted(c for c in embs.columns if c.startswith("emb"))
    return df, feature_cols, emb_cols


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # ----- CHILDES side -----
    print("[1/4] Loading CHILDES ...")
    chi, chi_feat_cols, chi_emb_cols = load_feature_table(
        args.childes_features, args.childes_emb, CHILDES_META,
        args.use_embeddings, args.emb_pca_d)
    chi = chi.dropna(subset=["age_months"])
    chi = chi[(chi.age_months > 0) & (chi.age_months <= args.max_childes_age)]
    print(f"  {len(chi)} CHILDES windows | {len(chi_feat_cols)} feats | "
          f"{len(chi_emb_cols)} emb dims")

    # ----- AphasiaBank side -----
    print("\n[2/4] Loading AphasiaBank ...")
    ab, ab_feat_cols, ab_emb_cols = load_feature_table(
        args.aphasia_features, args.aphasia_emb, AB_META,
        args.use_embeddings, args.emb_pca_d)
    print(f"  {len(ab)} AB windows | {len(ab_feat_cols)} feats | "
          f"{len(ab_emb_cols)} emb dims")

    # Use the intersection of structural features (should be identical;
    # the same extractor was used).
    common_feats = sorted(set(chi_feat_cols) & set(ab_feat_cols))
    print(f"  Common structural features: {len(common_feats)}")

    common_embs = []
    if args.use_embeddings and chi_emb_cols and ab_emb_cols:
        common_embs = sorted(set(chi_emb_cols) & set(ab_emb_cols))
        print(f"  Common embedding dims: {len(common_embs)}")

    use_cols = common_feats + common_embs

    # Build matrices.
    Xchi = chi[use_cols].to_numpy(dtype=float)
    ychi = chi["age_months"].to_numpy(dtype=float)
    Xab = ab[use_cols].to_numpy(dtype=float)

    # Joint scaler (fit on CHILDES, apply to both — controls must come
    # from somewhere).
    scaler = StandardScaler().fit(Xchi)
    Xchi_s = scaler.transform(Xchi)
    Xab_s = scaler.transform(Xab)

    # ----- Train developmental age regressor on CHILDES -----
    print("\n[3/4] Training developmental-age regressor on CHILDES ...")
    age_model = GradientBoostingRegressor(
        n_estimators=600, max_depth=4, learning_rate=0.05,
        subsample=0.85, random_state=0).fit(Xchi_s, ychi)
    in_sample_mae = float(np.mean(np.abs(age_model.predict(Xchi_s) - ychi)))
    print(f"  in-sample MAE: {in_sample_mae:.2f} months "
          f"({len(use_cols)} dims)")

    # ----- Apply to AphasiaBank -----
    print("\n[4/4] Applying to AphasiaBank ...")
    ab["dev_age_equiv_months"] = age_model.predict(Xab_s)
    print(f"  AB developmental-age-equivalent: "
          f"min {ab.dev_age_equiv_months.min():.1f} mo  "
          f"max {ab.dev_age_equiv_months.max():.1f} mo  "
          f"mean {ab.dev_age_equiv_months.mean():.1f} mo")

    # Aggregate to patient-level (one row per AB participant).
    pat = ab.groupby("participant_id").agg(
        dev_age_equiv_months=("dev_age_equiv_months", "mean"),
        wab_aq=("wab_aq", "first"),
        subtype=("subtype", "first"),
        corpus=("corpus", "first"),
        is_control=("is_control", "first"),
    ).reset_index()
    pat.to_csv(args.output_dir / "patient_dev_age_equiv.csv", index=False)

    # ----- Analyses -----
    have_aq = pat.dropna(subset=["wab_aq"])
    print(f"\n--- Patients with WAB-AQ: {len(have_aq)} ---")
    r, p = pearsonr(have_aq["wab_aq"], have_aq["dev_age_equiv_months"])
    print(f"  WAB-AQ ↔ dev-age-equiv: Pearson r = {r:+.3f} (p={p:.2e})")

    print("\n  Mean developmental-age-equivalent by subtype:")
    sub_stats = (have_aq.dropna(subset=["subtype"])
                        .groupby("subtype")
                        .agg(n=("participant_id", "count"),
                             dev_age_mean=("dev_age_equiv_months", "mean"),
                             dev_age_std=("dev_age_equiv_months", "std"),
                             aq_mean=("wab_aq", "mean"))
                        .sort_values("dev_age_mean")
                        .reset_index())
    print(sub_stats.to_string(index=False, float_format=lambda v: f"{v:6.2f}"))
    sub_stats.to_csv(args.output_dir / "subtype_dev_age.csv", index=False)

    # Within-subtype: does dev-age-equiv correlate with AQ?
    print("\n  Within-subtype: dev-age-equiv vs WAB-AQ correlation")
    for sub in sub_stats["subtype"]:
        rows = have_aq[have_aq["subtype"] == sub]
        if len(rows) < 8:
            continue
        r_, p_ = pearsonr(rows["dev_age_equiv_months"], rows["wab_aq"])
        print(f"    {sub:18s}  n={len(rows):>4}  r={r_:+.3f}  p={p_:.3f}")

    # ----- Visualization -----
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    ax = axes[0]
    ax.scatter(have_aq["dev_age_equiv_months"], have_aq["wab_aq"],
               s=20, alpha=0.5)
    ax.set_xlabel("Developmental age equivalent (months)")
    ax.set_ylabel("WAB-AQ")
    ax.set_title(f"Aphasia patients placed in developmental space\n"
                 f"(r={r:+.3f}, n={len(have_aq)})")
    ax.grid(alpha=0.3)
    # CHILDES upper bound line at 84 months
    ax.axvline(args.max_childes_age, color="r", ls="--", lw=1,
               label=f"CHILDES max age ({args.max_childes_age:.0f} mo)")
    ax.legend()

    ax = axes[1]
    sub_have = have_aq.dropna(subset=["subtype"])
    sub_have = sub_have[sub_have["subtype"].isin(
        ["Anomic", "Broca", "Conduction", "Wernicke", "Control",
         "NotAphasic"])]
    if len(sub_have):
        order = sub_have.groupby("subtype")["dev_age_equiv_months"].mean(
            ).sort_values().index.tolist()
        data_box = [sub_have[sub_have.subtype == s]["dev_age_equiv_months"]
                    for s in order]
        ax.boxplot(data_box, tick_labels=order, showfliers=False)
        ax.set_ylabel("Developmental age equivalent (months)")
        ax.set_title("Distribution by aphasia subtype")
        ax.grid(axis="y", alpha=0.3)
        ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    fig.savefig(args.output_dir / "dev_age_equiv.png", dpi=150)
    plt.close(fig)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
