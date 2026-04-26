"""V2 universality tests with adult controls included as the upper anchor.

The original test placed AphasiaBank PWAs ~5x further from their nearest
CHILDES neighbor than CHILDES samples are from each other (T3). This is
expected if CHILDES caps at 84mo and PWAs are mostly adults — they're
linguistically more mature than even the oldest children, so they sit
off the CHILDES manifold by definition.

This v2 includes AphasiaBank Famous + Control speakers as adult anchors
in the joint manifold. Asks the more refined question: do PWAs sit on
the manifold spanned by (children + healthy adults) — i.e., the
universal language-ability manifold — or off to the side?

Also runs Test 4 (intrinsic dimensionality) using the participation-ratio
estimator and the Levina-Bickel maximum-likelihood estimator.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.neighbors import NearestNeighbors
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
    p.add_argument("--output-dir", default="outputs/universality_v2", type=Path)
    p.add_argument("--max-childes-age", type=float, default=84.0)
    return p.parse_args()


def participation_ratio(eigenvalues: np.ndarray) -> float:
    """PR(X) = (sum of eigenvalues)^2 / sum of squared eigenvalues.
    Equivalent intrinsic-dimension estimate. Range [1, n_features].
    """
    s = eigenvalues.sum()
    s2 = (eigenvalues ** 2).sum()
    return float(s * s / s2) if s2 > 0 else 0.0


def levina_bickel_id(X: np.ndarray, k: int = 10) -> float:
    """Maximum-likelihood intrinsic dimensionality (Levina & Bickel 2004).
    Robust local-neighborhood estimator."""
    nn = NearestNeighbors(n_neighbors=k + 1).fit(X)
    dists, _ = nn.kneighbors(X)
    # dists[:, 0] is self (=0); use 1..k
    rk = dists[:, k]  # k-th nearest neighbor distance per point
    # Per-point ML estimator
    log_ratios = np.log(rk[:, None] / dists[:, 1:k+1])  # (n, k)
    # Each point's d_hat is k / sum(log ratios) per the LB formula
    d_hat = (k - 1) / log_ratios.sum(axis=1)
    return float(np.median(d_hat))


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    chi = pd.read_parquet(args.childes_features)
    chi = chi.dropna(subset=["age_months"])
    chi = chi[(chi.age_months > 0) & (chi.age_months <= args.max_childes_age)]
    ab = pd.read_parquet(args.aphasia_features)

    chi_cols = sorted(c for c in chi.columns if c not in CHI_META)
    ab_cols = sorted(c for c in ab.columns if c not in AB_META)
    common = sorted(set(chi_cols) & set(ab_cols))

    # Split AphasiaBank into controls + PWAs
    ab_controls = ab[ab["is_control"] == True].copy()
    ab_pwa = ab[(ab["is_control"] != True) & ab["subtype"].notna()].copy()
    ab_pwa = ab_pwa[~ab_pwa["subtype"].isin({"Control", "NotAphasic", "Unknown", "U"})]

    print(f"CHILDES: {len(chi)} windows")
    print(f"AphasiaBank Controls: {len(ab_controls)} windows")
    print(f"AphasiaBank PWAs (true aphasia subtype): {len(ab_pwa)} windows")

    Xchi = chi[common].to_numpy(dtype=float)
    Xctl = ab_controls[common].to_numpy(dtype=float)
    Xpwa = ab_pwa[common].to_numpy(dtype=float)

    scaler = StandardScaler().fit(np.vstack([Xchi, Xctl, Xpwa]))
    Xchi_s = scaler.transform(Xchi)
    Xctl_s = scaler.transform(Xctl)
    Xpwa_s = scaler.transform(Xpwa)

    # ============================================================
    # T3v2. Distance to nearest CHILDES + AphasiaBank-control neighbor
    # ============================================================
    print("\n=== T3v2. PWA distance to (CHILDES + adult controls) manifold ===")
    # Reference manifold = CHILDES + AphasiaBank controls
    Xref = np.vstack([Xchi_s, Xctl_s])

    # Use full data for PWAs but subsample reference for distance speed
    rng = np.random.default_rng(0)
    if len(Xref) > 5000:
        ref_idx = rng.choice(len(Xref), 5000, replace=False)
        Xref_sub = Xref[ref_idx]
    else:
        Xref_sub = Xref

    if len(Xpwa_s) > 2000:
        pwa_idx = rng.choice(len(Xpwa_s), 2000, replace=False)
        Xpwa_sub = Xpwa_s[pwa_idx]
    else:
        Xpwa_sub = Xpwa_s

    # Within-reference NN distance (baseline)
    ref_dist = euclidean_distances(Xref_sub, Xref_sub)
    np.fill_diagonal(ref_dist, np.inf)
    ref_nn = ref_dist.min(axis=1)

    # PWA → reference NN distance
    pwa_to_ref = euclidean_distances(Xpwa_sub, Xref_sub)
    pwa_nn = pwa_to_ref.min(axis=1)

    # Also separately: distance to nearest CHILDES vs nearest control
    pwa_to_chi = euclidean_distances(Xpwa_sub, Xchi_s[
        rng.choice(len(Xchi_s), min(3000, len(Xchi_s)), replace=False)])
    pwa_to_ctl = euclidean_distances(Xpwa_sub, Xctl_s[
        rng.choice(len(Xctl_s), min(2000, len(Xctl_s)), replace=False)])
    pwa_chi_nn = pwa_to_chi.min(axis=1)
    pwa_ctl_nn = pwa_to_ctl.min(axis=1)

    print(f"  Reference (CHI+CTL) within-NN: median={np.median(ref_nn):.3f}, "
          f"90th pct={np.percentile(ref_nn, 90):.3f}")
    print(f"  PWA → REF NN: median={np.median(pwa_nn):.3f}, "
          f"90th pct={np.percentile(pwa_nn, 90):.3f}")
    print(f"  PWA → CHILDES-only NN: median={np.median(pwa_chi_nn):.3f}")
    print(f"  PWA → AB-Controls-only NN: median={np.median(pwa_ctl_nn):.3f}")
    ratio = float(np.median(pwa_nn) / np.median(ref_nn))
    print(f"  Ratio (PWA→REF) / (REF→REF) median: {ratio:.2f}")
    print(f"  (1.0 = on manifold; >> 1 = off manifold)")

    # PWA-by-subtype distance to reference manifold
    if len(Xpwa_sub) >= len(ab_pwa):
        sub_arr = ab_pwa["subtype"].fillna("?").to_numpy()
    else:
        sub_arr = ab_pwa["subtype"].fillna("?").to_numpy()[pwa_idx]
    print(f"\n  PWA → REF NN distance by subtype (lower = closer to typical lang. ability):")
    for st in sorted(set(sub_arr)):
        m = sub_arr == st
        if m.sum() < 5: continue
        print(f"    {st:18s} n={int(m.sum()):>4}  median={np.median(pwa_nn[m]):.3f}")

    # ============================================================
    # T4. Intrinsic dimensionality
    # ============================================================
    print(f"\n=== T4. Intrinsic dimensionality ===")
    # Participation ratio on PCA eigenvalues (full)
    pca_chi_full = PCA().fit(Xchi_s)
    pca_ctl_full = PCA().fit(Xctl_s)
    pca_pwa_full = PCA().fit(Xpwa_s)

    pr_chi = participation_ratio(pca_chi_full.explained_variance_)
    pr_ctl = participation_ratio(pca_ctl_full.explained_variance_)
    pr_pwa = participation_ratio(pca_pwa_full.explained_variance_)
    print(f"  Participation ratio (effective dimensionality):")
    print(f"    CHILDES         d_eff = {pr_chi:.2f}  (of {Xchi_s.shape[1]} features)")
    print(f"    AB Controls     d_eff = {pr_ctl:.2f}")
    print(f"    AB PWAs         d_eff = {pr_pwa:.2f}")

    # Levina-Bickel local intrinsic dimensionality
    print(f"\n  Levina-Bickel local intrinsic dimensionality:")
    lb_chi = levina_bickel_id(
        Xchi_s[rng.choice(len(Xchi_s), min(2000, len(Xchi_s)), replace=False)])
    lb_ctl = levina_bickel_id(
        Xctl_s[rng.choice(len(Xctl_s), min(2000, len(Xctl_s)), replace=False)])
    lb_pwa = levina_bickel_id(
        Xpwa_s[rng.choice(len(Xpwa_s), min(2000, len(Xpwa_s)), replace=False)])
    print(f"    CHILDES         d_LB = {lb_chi:.2f}")
    print(f"    AB Controls     d_LB = {lb_ctl:.2f}")
    print(f"    AB PWAs         d_LB = {lb_pwa:.2f}")

    # Variance explained at d=8 / d=12 / d=20 per population
    print(f"\n  Variance explained at d=k:")
    for d in [3, 5, 8, 12, 20]:
        chi_v = pca_chi_full.explained_variance_ratio_[:d].sum()
        ctl_v = pca_ctl_full.explained_variance_ratio_[:d].sum()
        pwa_v = pca_pwa_full.explained_variance_ratio_[:d].sum()
        print(f"    d={d:>2}  CHI={chi_v:.3f}  CTL={ctl_v:.3f}  PWA={pwa_v:.3f}")

    # ============================================================
    # T5. Cross-population feature-importance invariance
    # ============================================================
    print(f"\n=== T5. Cross-population feature-importance invariance ===")
    # Train age regressor on CHILDES, importance ranking
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.inspection import permutation_importance

    age_y = chi["age_months"].to_numpy(dtype=float)
    age_model = GradientBoostingRegressor(
        n_estimators=200, max_depth=3, learning_rate=0.05,
        random_state=0).fit(Xchi_s, age_y)
    chi_imp = age_model.feature_importances_
    chi_top10 = np.argsort(chi_imp)[::-1][:10]

    # Train AQ regressor on AphasiaBank PWAs (where AQ is available)
    ab_with_aq = ab_pwa.dropna(subset=["wab_aq"]).copy()
    Xab_aq = scaler.transform(ab_with_aq[common].to_numpy(dtype=float))
    aq_y = ab_with_aq["wab_aq"].to_numpy(dtype=float)
    if len(aq_y) >= 100:
        aq_model = GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05,
            random_state=0).fit(Xab_aq, aq_y)
        ab_imp = aq_model.feature_importances_
        ab_top10 = np.argsort(ab_imp)[::-1][:10]

        chi_top_set = set(chi_top10)
        ab_top_set = set(ab_top10)
        overlap = chi_top_set & ab_top_set
        print(f"  Top-10 most important features for CHILDES age regression:")
        for i in chi_top10:
            mark = "✓" if i in ab_top_set else " "
            print(f"    [{mark}] {common[i]:30s} chi_imp={chi_imp[i]:.3f}")
        print(f"\n  Top-10 most important features for AphasiaBank AQ regression:")
        for i in ab_top10:
            mark = "✓" if i in chi_top_set else " "
            print(f"    [{mark}] {common[i]:30s} ab_imp={ab_imp[i]:.3f}")
        print(f"\n  Overlap: {len(overlap)} of 10 features")
        print(f"  Overlapping features: {sorted([common[i] for i in overlap])}")
    else:
        print(f"  AB sample too small")

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
