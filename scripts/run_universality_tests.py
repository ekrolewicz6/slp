"""Universality of the language-ability manifold across CHILDES and AphasiaBank.

Tests whether aphasia and child language development share the same
underlying dimensional structure. If true, this is a fundamental finding
about the structure of language ability.

Three tests:

  T1. **Same axes** — Procrustes-aligned PCA. Fit PCA d=8 on CHILDES
      and AphasiaBank separately, align via orthogonal Procrustes,
      measure residual disparity. Small disparity = same axes.

  T2. **Same direction of change** — for each longitudinal PWA who
      improves, compute their feature change vector. For CHILDES,
      compute the population-level "older minus younger" feature
      direction. Compute cosine similarity between PWA improvement
      direction and developmental direction. If positive on average,
      aphasia recovery tracks developmental progression on the same
      axes.

  T3. **Same manifold** — fit a single joint PCA on combined CHILDES +
      AphasiaBank data. For each PWA, compute distance to nearest
      CHILDES neighbor. Compare to within-CHILDES nearest-neighbor
      distances. If PWA distances are comparable to CHILDES distances,
      PWAs are *on* the developmental manifold; if much larger, PWAs
      sit *beside* it.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import procrustes
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.preprocessing import StandardScaler


CHI_META = {"transcript_id", "corpus", "child_id", "age_months",
            "n_chi_utterances", "bundle", "window_id", "window_index",
            "n_chi_utts_in_window"}
AB_META = {"transcript_id", "section", "corpus", "participant_id",
           "patient_root", "session_letter", "age_years", "sex", "subtype",
           "wab_aq", "is_control", "session_date", "window_id",
           "window_index", "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--childes-features",
                   default="data/features/phase1_windowed_features.parquet",
                   type=Path)
    p.add_argument("--aphasia-features",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/universality", type=Path)
    p.add_argument("--latent-d", type=int, default=8)
    p.add_argument("--max-childes-age", type=float, default=84.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading CHILDES + AphasiaBank features...")
    chi = pd.read_parquet(args.childes_features)
    chi = chi.dropna(subset=["age_months"])
    chi = chi[(chi.age_months > 0) & (chi.age_months <= args.max_childes_age)]
    ab = pd.read_parquet(args.aphasia_features)

    chi_cols = sorted(c for c in chi.columns if c not in CHI_META)
    ab_cols = sorted(c for c in ab.columns if c not in AB_META)
    common = sorted(set(chi_cols) & set(ab_cols))
    print(f"  CHILDES: {len(chi)} windows | AphasiaBank: {len(ab)} windows | "
          f"common features: {len(common)}")

    Xchi = chi[common].to_numpy(dtype=float)
    Xab = ab[common].to_numpy(dtype=float)

    # Scale on combined data so units match
    scaler = StandardScaler().fit(np.vstack([Xchi, Xab]))
    Xchi_s = scaler.transform(Xchi)
    Xab_s = scaler.transform(Xab)

    d = args.latent_d

    # ============================================================
    # T1. Procrustes-aligned PCA: same axes?
    # ============================================================
    print(f"\n=== T1. Procrustes PCA invariance (d={d}) ===")
    pca_chi = PCA(n_components=d, random_state=0).fit(Xchi_s)
    pca_ab = PCA(n_components=d, random_state=0).fit(Xab_s)
    print(f"  CHILDES variance explained: {pca_chi.explained_variance_ratio_.sum():.3f}")
    print(f"  AphasiaBank variance explained: {pca_ab.explained_variance_ratio_.sum():.3f}")

    # Per-component variance
    chi_var = pca_chi.explained_variance_ratio_
    ab_var = pca_ab.explained_variance_ratio_
    print(f"  Per-component variance ratios:")
    for j in range(d):
        print(f"    Component {j+1}: CHILDES {chi_var[j]:.3f}  AphasiaBank {ab_var[j]:.3f}")

    # Procrustes alignment of the loading matrices
    # Components are (d, n_features)
    A = pca_chi.components_  # CHILDES loadings
    B = pca_ab.components_   # AphasiaBank loadings
    # Orthogonal Procrustes: find rotation R minimizing ||A - B R||_F
    # Standard scipy.linalg.orthogonal_procrustes does this
    from scipy.linalg import orthogonal_procrustes
    R, scale = orthogonal_procrustes(A, B)
    # Residual: how much do the loadings disagree after best rotation?
    aligned_B = B @ R.T  # rotate B back to A's frame
    residual_norm = np.linalg.norm(A - aligned_B, ord="fro")
    A_norm = np.linalg.norm(A, ord="fro")
    relative_residual = residual_norm / A_norm
    print(f"  Procrustes residual (relative): {relative_residual:.3f}")
    print(f"    (0 = identical axes after rotation; ~1 = totally different)")

    # Per-component cosine similarity (between CHILDES PC_j and best-aligned AphasiaBank PC_j)
    print(f"  Per-component cosine similarity (CHILDES PC_j vs aligned AphasiaBank PC_j):")
    cos_sims = []
    for j in range(d):
        cs = float(np.dot(A[j], aligned_B[j]) /
                    (np.linalg.norm(A[j]) * np.linalg.norm(aligned_B[j])))
        cos_sims.append(cs)
        print(f"    PC{j+1}: {cs:+.3f}")

    # Top-feature agreement: top 5 features per component, do they overlap?
    print(f"  Top-5-feature overlap per component:")
    overlap_rates = []
    for j in range(d):
        chi_top = set(np.argsort(np.abs(A[j]))[::-1][:5])
        ab_top = set(np.argsort(np.abs(B[j]))[::-1][:5])
        overlap = len(chi_top & ab_top)
        overlap_rates.append(overlap)
        chi_names = [common[i] for i in chi_top]
        ab_names = [common[i] for i in ab_top]
        print(f"    PC{j+1}: {overlap}/5 overlap   "
              f"CHILDES={chi_names[:3]}...   "
              f"AB={ab_names[:3]}...")

    t1_summary = {
        "test": "T1_procrustes",
        "relative_residual": relative_residual,
        "mean_cosine_per_PC": float(np.mean(np.abs(cos_sims))),
        "median_top5_overlap": float(np.median(overlap_rates)),
        "verdict": "high_invariance" if relative_residual < 0.5
                   else "moderate_invariance" if relative_residual < 1.0
                   else "low_invariance",
    }

    # ============================================================
    # T2. Same direction of change
    # ============================================================
    print(f"\n=== T2. Direction-of-change agreement ===")

    # CHILDES developmental progression vector: principal direction along which
    # children move as they age. Compute via regression of features on age,
    # then take the regression coefficients as the "developmental direction".
    from sklearn.linear_model import Ridge
    age_y = chi["age_months"].to_numpy(dtype=float)
    devel_reg = Ridge(alpha=1.0).fit(Xchi_s, age_y)
    devel_direction = devel_reg.coef_  # in scaled feature space
    devel_direction = devel_direction / (np.linalg.norm(devel_direction) + 1e-9)
    print(f"  Developmental direction (top 5 features, |coef|):")
    top_dev = np.argsort(np.abs(devel_direction))[::-1][:5]
    for i in top_dev:
        print(f"    {common[i]:30s} {devel_direction[i]:+.3f}")

    # PWA improvement vectors: for longitudinal PWAs with increasing AQ
    ab_with_letter = ab.copy()
    ab_with_letter["patient_root"] = ab_with_letter["participant_id"].str.replace(
        r"[a-zA-Z]$", "", regex=True)
    ab_with_letter["session_letter"] = ab_with_letter["participant_id"].str.extract(
        r"([a-zA-Z])$")[0]

    # Aggregate to session level (mean of windows)
    session = ab_with_letter.groupby("participant_id").agg(
        {**{c: "mean" for c in common},
         **{m: "first" for m in ["patient_root", "session_letter",
                                  "wab_aq", "subtype", "corpus"]}}
    ).reset_index()

    # Build improvement vectors
    improvement_vectors = []
    delta_aqs = []
    subtypes_t1 = []
    for pat, g in session.groupby("patient_root"):
        g = g.dropna(subset=["wab_aq"]).sort_values("session_letter")
        if len(g) < 2:
            continue
        first, last = g.iloc[0], g.iloc[-1]
        delta_aq = last["wab_aq"] - first["wab_aq"]
        if abs(delta_aq) < 5:  # only use meaningful change
            continue
        # Feature change in scaled space
        first_feat = scaler.transform(first[common].to_numpy().reshape(1, -1))[0]
        last_feat = scaler.transform(last[common].to_numpy().reshape(1, -1))[0]
        change = last_feat - first_feat
        norm = np.linalg.norm(change)
        if norm < 1e-9:
            continue
        change = change / norm
        improvement_vectors.append(change)
        delta_aqs.append(delta_aq)
        subtypes_t1.append(first["subtype"])

    improvement_vectors = np.array(improvement_vectors)
    delta_aqs = np.array(delta_aqs)
    print(f"\n  Longitudinal PWAs with |ΔAQ| ≥ 5: {len(improvement_vectors)}")
    if len(improvement_vectors) > 0:
        # Cosine sim with developmental direction. Sign: improvers (ΔAQ > 0) should align
        # with developmental direction; decliners should anti-align.
        cos_with_devel = improvement_vectors @ devel_direction
        # Multiply by sign(delta_aq) to convert "improvement direction" to "improvement-cos".
        # An improver's change vector aligned with devel direction → positive.
        # A decliner's change vector anti-aligned with devel direction → also positive (since they're
        # moving the wrong way). For both, +ve means "consistent with developmental direction
        # tracking improvement".
        signed_cos = cos_with_devel * np.sign(delta_aqs)
        print(f"  Mean signed cosine sim (improvement_direction · devel_direction · sign(ΔAQ)): "
              f"{signed_cos.mean():+.3f}")
        print(f"  (Positive → PWAs improve along the developmental direction)")
        print(f"  Median: {np.median(signed_cos):+.3f}")
        print(f"  Fraction positive: {(signed_cos > 0).mean():.2%}")
        # Random-baseline comparison
        n_rand = 1000
        rand_cos = []
        rng = np.random.default_rng(0)
        for _ in range(n_rand):
            v = rng.normal(size=devel_direction.shape)
            v = v / np.linalg.norm(v)
            rand_cos.append(np.abs(improvement_vectors @ v).mean())
        print(f"  Random baseline mean |cos|: {np.mean(rand_cos):.3f}, "
              f"observed mean |cos|: {np.abs(cos_with_devel).mean():.3f}")

        # Per-subtype breakdown
        print(f"\n  By subtype (subtype at t1):")
        for st in sorted(set(subtypes_t1)):
            mask = np.array([s == st for s in subtypes_t1])
            if mask.sum() < 3:
                continue
            sc_mean = signed_cos[mask].mean()
            print(f"    {st:15s} n={int(mask.sum()):>3}  mean signed cos = {sc_mean:+.3f}")
    else:
        print("  No longitudinal pairs with meaningful change — cannot test")
        signed_cos = np.array([])

    t2_summary = {
        "test": "T2_direction",
        "n_pairs": int(len(improvement_vectors)),
        "mean_signed_cos": float(signed_cos.mean()) if len(signed_cos) else float("nan"),
        "fraction_positive": float((signed_cos > 0).mean()) if len(signed_cos) else float("nan"),
        "verdict": "consistent" if len(signed_cos) and signed_cos.mean() > 0.05
                   else "inconsistent" if len(signed_cos) and signed_cos.mean() < -0.05
                   else "null",
    }

    # ============================================================
    # T3. Same manifold: PWA distance to nearest CHILDES neighbor
    # ============================================================
    print(f"\n=== T3. PWA distance to CHILDES manifold ===")
    # Joint PCA fit on combined data
    Xall = np.vstack([Xchi_s, Xab_s])
    pca_joint = PCA(n_components=d, random_state=0).fit(Xall)
    Zchi = pca_joint.transform(Xchi_s)
    Zab = pca_joint.transform(Xab_s)

    # Use a sub-sample for distance computation (distance matrix scales O(n²))
    rng = np.random.default_rng(0)
    chi_sample_idx = rng.choice(len(Zchi), size=min(2000, len(Zchi)), replace=False)
    ab_sample_idx = rng.choice(len(Zab), size=min(1000, len(Zab)), replace=False)
    Zchi_sample = Zchi[chi_sample_idx]
    Zab_sample = Zab[ab_sample_idx]

    # CHILDES nearest-neighbor distances (within-CHILDES baseline)
    chi_dist = euclidean_distances(Zchi_sample, Zchi_sample)
    np.fill_diagonal(chi_dist, np.inf)
    chi_nn_dist = chi_dist.min(axis=1)

    # PWA distance to nearest CHILDES neighbor
    ab_to_chi_dist = euclidean_distances(Zab_sample, Zchi_sample)
    ab_nn_dist = ab_to_chi_dist.min(axis=1)

    print(f"  CHILDES within-NN distance: median={np.median(chi_nn_dist):.3f}  "
          f"mean={np.mean(chi_nn_dist):.3f}  90th pct={np.percentile(chi_nn_dist, 90):.3f}")
    print(f"  PWA → CHILDES NN distance: median={np.median(ab_nn_dist):.3f}  "
          f"mean={np.mean(ab_nn_dist):.3f}  90th pct={np.percentile(ab_nn_dist, 90):.3f}")
    ratio = np.median(ab_nn_dist) / np.median(chi_nn_dist)
    print(f"  Ratio (PWA→CHI) / (CHI→CHI) median: {ratio:.2f}")
    print(f"  (1.0 = PWAs sit on the developmental manifold; >> 1 = beside it)")

    t3_summary = {
        "test": "T3_manifold",
        "ratio_median_pwa_to_chi": float(ratio),
        "median_chi_nn": float(np.median(chi_nn_dist)),
        "median_ab_nn": float(np.median(ab_nn_dist)),
        "verdict": "on_manifold" if ratio < 1.5
                   else "off_manifold" if ratio > 3.0
                   else "near_manifold",
    }

    # ============================================================
    # Synthesis
    # ============================================================
    print(f"\n=== Synthesis ===")
    print(f"  T1 (Procrustes): {t1_summary['verdict']}  "
          f"residual={t1_summary['relative_residual']:.3f}")
    print(f"  T2 (Direction): {t2_summary['verdict']}  "
          f"signed cos={t2_summary['mean_signed_cos']:+.3f}, "
          f"frac+={t2_summary['fraction_positive']:.2%}")
    print(f"  T3 (Manifold): {t3_summary['verdict']}  "
          f"distance ratio={t3_summary['ratio_median_pwa_to_chi']:.2f}")

    pd.DataFrame([t1_summary, t2_summary, t3_summary]).to_csv(
        args.output_dir / "universality_summary.csv", index=False)
    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
