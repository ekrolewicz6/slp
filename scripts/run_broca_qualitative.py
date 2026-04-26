"""Test the strongest version of the universality finding:

  Broca aphasia is qualitatively distinct from both healthy adult speech
  AND from young child speech — even when matched on basic productivity
  measures (MLU, NDW, etc.).

If we plot CHILDES (binned by age), AB Controls, and AB PWA-by-subtype
in joint PCA / UMAP space, the Broca-vs-young-child distinction should
be visible. If Broca patients overlap with young children in 2D, the
"recovery retraces development" framing has support. If Broca occupies
a distinct region, the qualitative-distinction claim is supported.

Also run:
  - K-S test on key features (MLU, NDW, etc.) between Broca and
    age-matched young children (when MLU is comparable)
  - Confusion-style analysis: train classifier to distinguish
    Broca-PWA from low-MLU children — if accuracy is near-perfect,
    they're easily separable (qualitative distinction)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from scipy.stats import ks_2samp


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
    p.add_argument("--output-dir", default="outputs/broca_qualitative", type=Path)
    p.add_argument("--max-childes-age", type=float, default=84.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    chi = pd.read_parquet(args.childes_features)
    chi = chi.dropna(subset=["age_months"])
    chi = chi[(chi.age_months > 0) & (chi.age_months <= args.max_childes_age)]
    ab = pd.read_parquet(args.aphasia_features)

    chi_cols = sorted(c for c in chi.columns if c not in CHI_META)
    ab_cols = sorted(c for c in ab.columns if c not in AB_META)
    common_raw = sorted(set(chi_cols) & set(ab_cols))

    # CRITICAL: drop features that are corpus-asymmetric (e.g. ~100% zero in
    # one corpus but populated in the other). These reflect different feature
    # extractors between the CHILDES and AphasiaBank pipelines, NOT clinical
    # signal. Including them produces fake "qualitative distinction" by
    # letting any classifier trivially identify the corpus of origin.
    asymmetric = []
    for f in common_raw:
        ab_zero = (ab[f].fillna(0) == 0).mean()
        chi_zero = (chi[f].fillna(0) == 0).mean()
        if (ab_zero >= 0.99 and chi_zero <= 0.5) or \
           (chi_zero >= 0.99 and ab_zero <= 0.5):
            asymmetric.append(f)
    common = [c for c in common_raw if c not in asymmetric]
    print(f"Common features: {len(common_raw)} raw → "
          f"{len(common)} after dropping {len(asymmetric)} corpus-asymmetric "
          f"extraction artifacts:")
    for f in asymmetric:
        print(f"    DROPPED: {f}")

    # Slice AphasiaBank
    broca = ab[ab["subtype"] == "Broca"].copy()
    other_pwa = ab[ab["subtype"].isin(["Anomic", "Conduction", "Wernicke"])].copy()
    ctrl = ab[ab["is_control"] == True].copy()

    print(f"CHILDES: {len(chi)} windows ({chi.age_months.min():.0f}-"
          f"{chi.age_months.max():.0f} mo)")
    print(f"AB Broca PWAs: {len(broca)}")
    print(f"AB Other PWAs (Anomic/Wernicke/Conduction): {len(other_pwa)}")
    print(f"AB Controls: {len(ctrl)}")

    # Joint scaling
    Xall = pd.concat([chi[common], broca[common], other_pwa[common], ctrl[common]],
                     ignore_index=True)
    scaler = StandardScaler().fit(Xall.to_numpy(dtype=float))
    Xchi_s = scaler.transform(chi[common].to_numpy(dtype=float))
    Xbroca_s = scaler.transform(broca[common].to_numpy(dtype=float))
    Xother_s = scaler.transform(other_pwa[common].to_numpy(dtype=float))
    Xctrl_s = scaler.transform(ctrl[common].to_numpy(dtype=float))

    # Joint PCA
    Xall_s = scaler.transform(Xall.to_numpy(dtype=float))
    pca = PCA(n_components=2, random_state=0).fit(Xall_s)
    Zchi = pca.transform(Xchi_s)
    Zbroca = pca.transform(Xbroca_s)
    Zother = pca.transform(Xother_s)
    Zctrl = pca.transform(Xctrl_s)

    # ----- Test 1: K-S test on MLU between low-MLU Broca and young children -----
    print(f"\n=== T1. Broca-vs-young-children comparison on key features ===")
    # Get age-matched young children: those with MLU comparable to Broca's MLU range
    broca_mlu = broca["mlu_words"].dropna()
    chi_mlu = chi["mlu_words"].dropna()
    # Restrict to children whose MLU is within Broca's MLU range
    broca_mlu_low, broca_mlu_high = broca_mlu.quantile([0.1, 0.9])
    young_chi_mask = (chi["mlu_words"] >= broca_mlu_low) & \
                     (chi["mlu_words"] <= broca_mlu_high)
    matched_chi = chi[young_chi_mask]
    print(f"  Broca MLU range (10–90 pct): {broca_mlu_low:.2f} – {broca_mlu_high:.2f}")
    print(f"  Matched-MLU children: {len(matched_chi)} windows  "
          f"(mean age {matched_chi.age_months.mean():.1f} mo, "
          f"range {matched_chi.age_months.min():.1f}–{matched_chi.age_months.max():.1f})")

    # K-S tests on each feature comparing Broca vs matched-MLU children
    print(f"\n  K-S statistic per feature (Broca vs matched-MLU children):")
    print(f"  Higher = more different. Top-10 most-different features:")
    ks_rows = []
    for f in common:
        b = broca[f].dropna()
        c = matched_chi[f].dropna()
        if len(b) < 20 or len(c) < 20: continue
        try:
            ks_stat, p = ks_2samp(b, c)
            ks_rows.append({"feature": f, "ks_stat": ks_stat, "p_value": p,
                             "broca_mean": b.mean(), "child_mean": c.mean()})
        except Exception:
            pass
    ks_df = pd.DataFrame(ks_rows).sort_values("ks_stat", ascending=False)
    print(ks_df.head(10).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    ks_df.to_csv(args.output_dir / "broca_vs_matched_children_ks.csv", index=False)

    # ----- Test 2: classifier — can we separate Broca PWAs from MLU-matched children? -----
    print(f"\n=== T2. Classifier: Broca PWA vs MLU-matched children ===")
    Xb = broca[common].to_numpy(dtype=float)
    Xc = matched_chi[common].to_numpy(dtype=float)
    X = np.vstack([Xb, Xc])
    y = np.concatenate([np.ones(len(Xb)), np.zeros(len(Xc))])
    # Patient/child grouping for honest CV
    g = np.concatenate([broca["participant_id"].astype(str).to_numpy(),
                         matched_chi["child_id"].astype(str).to_numpy()])
    n_g = len(set(g))
    splits = max(2, min(5, n_g))
    gkf = GroupKFold(n_splits=splits)
    preds = np.empty_like(y)
    for tr, te in gkf.split(X, y, g):
        clf = GradientBoostingClassifier(n_estimators=300, max_depth=3,
                                           learning_rate=0.05,
                                           random_state=0).fit(X[tr], y[tr])
        preds[te] = clf.predict(X[te])
    acc = float((preds == y).mean())
    f1 = float(f1_score(y, preds, average="binary"))
    chance = max((y == 1).mean(), (y == 0).mean())
    print(f"  Broca PWA vs MLU-matched children classifier")
    print(f"  n: {int(y.sum())} Broca windows vs {int((y==0).sum())} matched-MLU child windows")
    print(f"  Accuracy = {acc:.3f} (chance = {chance:.3f})")
    print(f"  F1 = {f1:.3f}")
    print(f"  → Near-perfect = qualitative distinction; near-chance = same population")

    # ----- Test 2b: CRITICAL CONTROL — same classifier on AB Controls vs MLU-matched children -----
    # If AB Controls (healthy adults) are also trivially separable from
    # CHILDES, then the F1 in T2 reflects corpus-identity (different
    # recording conditions, transcription conventions, task genres),
    # NOT clinical signal. Only if AB Controls are NOT trivially separable
    # while Broca IS does the qualitative-distinction claim survive.
    print(f"\n=== T2b. CONTROL: AB Controls vs MLU-matched children ===")
    # Restrict AB Controls to the same MLU range, for an apples-to-apples comparison
    ctrl_mlu_match = ctrl[(ctrl["mlu_words"] >= broca_mlu_low) &
                           (ctrl["mlu_words"] <= broca_mlu_high)]
    print(f"  AB Controls in Broca's MLU range: {len(ctrl_mlu_match)} windows "
          f"(out of {len(ctrl)} total controls)")
    if len(ctrl_mlu_match) >= 20:
        Xcc = ctrl_mlu_match[common].to_numpy(dtype=float)
        Xc2 = matched_chi[common].to_numpy(dtype=float)
        Xctl_test = np.vstack([Xcc, Xc2])
        yctl_test = np.concatenate([np.ones(len(Xcc)), np.zeros(len(Xc2))])
        gctl = np.concatenate([
            ctrl_mlu_match["participant_id"].astype(str).to_numpy(),
            matched_chi["child_id"].astype(str).to_numpy()])
        n_g2 = len(set(gctl))
        splits2 = max(2, min(5, n_g2))
        gkf2 = GroupKFold(n_splits=splits2)
        preds2 = np.empty_like(yctl_test)
        for tr, te in gkf2.split(Xctl_test, yctl_test, gctl):
            clf2 = GradientBoostingClassifier(
                n_estimators=300, max_depth=3,
                learning_rate=0.05, random_state=0).fit(
                Xctl_test[tr], yctl_test[tr])
            preds2[te] = clf2.predict(Xctl_test[te])
        acc2 = float((preds2 == yctl_test).mean())
        f1_2 = float(f1_score(yctl_test, preds2, average="binary"))
        chance2 = max((yctl_test == 1).mean(), (yctl_test == 0).mean())
        print(f"  n: {int(yctl_test.sum())} AB-Control windows vs "
              f"{int((yctl_test==0).sum())} matched-MLU child windows")
        print(f"  Accuracy = {acc2:.3f} (chance = {chance2:.3f})")
        print(f"  F1 = {f1_2:.3f}")
        print(f"  Compare to Broca-vs-children F1 = {f1:.3f}")
        if f1_2 > 0.9:
            print(f"  ⚠ AB Controls also trivially separable: T2's "
                  f"high F1 likely reflects corpus identity, NOT clinical "
                  f"signal. Qualitative-distinction claim is compromised.")
        elif f1 - f1_2 > 0.2:
            print(f"  ✓ Broca much more separable than Controls "
                  f"(ΔF1={f1-f1_2:+.3f}): qualitative-distinction claim "
                  f"is supported beyond corpus baseline.")
        else:
            print(f"  ~ Difference ΔF1={f1-f1_2:+.3f} is modest: claim is "
                  f"partially supported but corpus confounding remains.")
    else:
        print(f"  Too few AB Controls in MLU range for control comparison")

    # ----- Test 2c: Per-subtype qualitative-distinction profile -----
    # If Broca is uniquely qualitatively distinct (vs children at matched
    # MLU), other PWA subtypes should be MUCH less separable. Run the same
    # classifier for Anomic, Conduction, Wernicke (each MLU-matched
    # to children).
    print(f"\n=== T2c. Per-subtype: PWA vs MLU-matched children ===")
    subtype_rows = []
    for stype in ["Broca", "Anomic", "Conduction", "Wernicke"]:
        sub_pwa = ab[ab["subtype"] == stype].copy()
        if len(sub_pwa) < 30:
            print(f"  {stype:12s}  too few patients (n={len(sub_pwa)})")
            continue
        # MLU-match each subtype individually (not against Broca's range)
        s_mlu = sub_pwa["mlu_words"].dropna()
        s_lo, s_hi = s_mlu.quantile([0.1, 0.9])
        s_chi = chi[(chi["mlu_words"] >= s_lo) & (chi["mlu_words"] <= s_hi)]
        if len(s_chi) < 30:
            print(f"  {stype:12s}  too few MLU-matched children (n={len(s_chi)})")
            continue
        Xp = sub_pwa[common].to_numpy(dtype=float)
        Xc3 = s_chi[common].to_numpy(dtype=float)
        Xst = np.vstack([Xp, Xc3])
        yst = np.concatenate([np.ones(len(Xp)), np.zeros(len(Xc3))])
        gst = np.concatenate([
            sub_pwa["participant_id"].astype(str).to_numpy(),
            s_chi["child_id"].astype(str).to_numpy()])
        n_g3 = len(set(gst))
        splits3 = max(2, min(5, n_g3))
        gkf3 = GroupKFold(n_splits=splits3)
        preds3 = np.empty_like(yst)
        for tr, te in gkf3.split(Xst, yst, gst):
            clf3 = GradientBoostingClassifier(
                n_estimators=300, max_depth=3,
                learning_rate=0.05, random_state=0).fit(
                Xst[tr], yst[tr])
            preds3[te] = clf3.predict(Xst[te])
        f1_3 = float(f1_score(yst, preds3, average="binary"))
        chance3 = max((yst == 1).mean(), (yst == 0).mean())
        print(f"  {stype:12s}  n_pwa={len(sub_pwa):>3} MLU={s_lo:.1f}-{s_hi:.1f}  "
              f"vs n_chi={len(s_chi):>5}  F1={f1_3:.3f}  (chance={chance3:.3f})")
        # Parallel control: AB Controls in same MLU range vs matched children
        ctl_in_range = ctrl[(ctrl["mlu_words"] >= s_lo) &
                             (ctrl["mlu_words"] <= s_hi)]
        if len(ctl_in_range) >= 30:
            Xctl_p = ctl_in_range[common].to_numpy(dtype=float)
            Xst_c = np.vstack([Xctl_p, Xc3])
            yst_c = np.concatenate([np.ones(len(Xctl_p)),
                                      np.zeros(len(Xc3))])
            gst_c = np.concatenate([
                ctl_in_range["participant_id"].astype(str).to_numpy(),
                s_chi["child_id"].astype(str).to_numpy()])
            n_g4 = len(set(gst_c))
            splits4 = max(2, min(5, n_g4))
            gkf4 = GroupKFold(n_splits=splits4)
            preds4 = np.empty_like(yst_c)
            for tr, te in gkf4.split(Xst_c, yst_c, gst_c):
                clf4 = GradientBoostingClassifier(
                    n_estimators=300, max_depth=3,
                    learning_rate=0.05, random_state=0).fit(
                    Xst_c[tr], yst_c[tr])
                preds4[te] = clf4.predict(Xst_c[te])
            f1_ctl = float(f1_score(yst_c, preds4, average="binary"))
            print(f"    {' '*12}  control AB-healthy in same MLU "
                  f"(n={len(ctl_in_range)})  F1={f1_ctl:.3f}  "
                  f"ΔF1(pwa-ctl)={f1_3 - f1_ctl:+.3f}")
        else:
            f1_ctl = float("nan")
            print(f"    {' '*12}  control: too few healthy adults "
                  f"in MLU range (n={len(ctl_in_range)})")

        subtype_rows.append({"subtype": stype, "n_pwa": len(sub_pwa),
                              "n_chi_matched": len(s_chi),
                              "n_ctl_matched": len(ctl_in_range),
                              "mlu_lo": float(s_lo), "mlu_hi": float(s_hi),
                              "f1_pwa_vs_chi": f1_3,
                              "f1_ctl_vs_chi": f1_ctl,
                              "delta_f1": f1_3 - f1_ctl,
                              "chance": chance3})

    pd.DataFrame(subtype_rows).to_csv(
        args.output_dir / "subtype_vs_children_f1.csv", index=False)

    # ----- Test 3: 2D visualization -----
    print(f"\n=== T3. 2D PCA projection ===")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: by population
    ax = axes[0]
    # Subsample CHILDES for visibility
    rng = np.random.default_rng(0)
    chi_idx = rng.choice(len(Zchi), size=min(2000, len(Zchi)), replace=False)
    ax.scatter(Zchi[chi_idx, 0], Zchi[chi_idx, 1], c=chi["age_months"].iloc[chi_idx],
                cmap="viridis", s=8, alpha=0.4, label="CHILDES (color=age)")
    ax.scatter(Zctrl[:, 0], Zctrl[:, 1], c="k", marker="x", s=20, alpha=0.6,
               label=f"AB Controls (n={len(Zctrl)})")
    ax.scatter(Zother[:, 0], Zother[:, 1], c="orange", marker="o", s=15,
               alpha=0.4, label=f"Other PWAs (Anomic/Wer/Cond, n={len(Zother)})")
    ax.scatter(Zbroca[:, 0], Zbroca[:, 1], c="red", marker="^", s=25, alpha=0.7,
               label=f"Broca PWAs (n={len(Zbroca)})")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    ax.set_title("Joint PCA: CHILDES + AphasiaBank populations")
    ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.3)

    # Right: zoom on the Broca-vs-young-child overlap region
    ax = axes[1]
    young = chi[chi["age_months"] <= 36]
    Xyoung_s = scaler.transform(young[common].to_numpy(dtype=float))
    Zyoung = pca.transform(Xyoung_s)
    ax.scatter(Zyoung[:, 0], Zyoung[:, 1], c="blue", s=12, alpha=0.4,
                label=f"CHILDES ≤36 mo (n={len(Zyoung)})")
    ax.scatter(Zbroca[:, 0], Zbroca[:, 1], c="red", marker="^", s=25, alpha=0.7,
               label=f"Broca PWAs (n={len(Zbroca)})")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    ax.set_title("Broca PWAs vs young children (≤36 mo) overlap?")
    ax.legend(loc="best", fontsize=10)
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(args.output_dir / "broca_vs_children.png", dpi=150)
    plt.close(fig)
    print(f"  saved 2D projection")

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
