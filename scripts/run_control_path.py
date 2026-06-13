"""Does Broca aphasia recover along a DISTINCT control path?

The dynamical-systems reframe (STRATEGY.md §5): language ability is a state
in a low-dimensional space; recovery is a trajectory toward the healthy
region; therapy is a control input. #49 showed Broca occupies a region of
that space no neurotypical speaker reaches. Here we ask whether that static
distinctiveness extends to the *direction of recovery*.

PRIMARY TEST (within-AphasiaBank — no cross-corpus confound). Each subtype
has a recovery direction = unit(healthy-adult centroid − subtype centroid)
in the within-AB z-scored feature space. If all subtypes funnel to health
along one shared axis, their recovery directions are ~parallel. We find the
fluent subtypes (Anomic/Conduction/Wernicke) share one axis (cos≈0.95–0.99)
while Broca's is a significant outlier — a measurably distinct control path,
and the longest one. Significance by bootstrap over windows.

SECONDARY (cross-corpus, honestly caveated). Whether the developmental
(CHILDES) manifold lies on the recovery corridor. This is CONFOUNDED: a
diagnostic shows healthy AphasiaBank adults sit as far from the child
manifold as Broca does (~5 vs ~4.8 units), so the CHILDES↔AphasiaBank
domain gap swamps the developmental signal. Reported for transparency, not
as a clean result. The clean static answer to "is Broca child-like" is #49
(MLU-matched Broca vs children: F1 0.988 — distinct).

TERTIARY. Longitudinal recovery vectors (small n; AQ mostly stable, #23).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

CHI_META = {"transcript_id", "corpus", "child_id", "age_months",
            "n_chi_utterances", "bundle", "window_id", "window_index",
            "n_chi_utts_in_window"}
AB_META = {"transcript_id", "section", "corpus", "participant_id",
           "patient_root", "session_letter", "age_years", "sex", "subtype",
           "wab_aq", "is_control", "session_date", "window_id",
           "window_index", "n_chi_utts_in_window"}
SUBTYPES = ["Broca", "Anomic", "Conduction", "Wernicke"]
FLUENT = ["Anomic", "Conduction", "Wernicke"]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--childes", default="data/features/phase1_windowed_features.parquet", type=Path)
    p.add_argument("--aphasia", default="data/features/aphasiabank_windowed_features.parquet", type=Path)
    p.add_argument("--output-dir", default="outputs/control_path", type=Path)
    p.add_argument("--boot", type=int, default=1000)
    p.add_argument("--seed", type=int, default=0)
    return p.parse_args()


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def recovery_dirs(Z, mask_by_subtype, ctrl_mask, rng=None, resample=False):
    """Recovery direction (unit) per subtype = toward control centroid."""
    if resample:
        idxA = np.where(ctrl_mask)[0]
        A = Z[rng.choice(idxA, len(idxA), replace=True)].mean(0)
    else:
        A = Z[ctrl_mask].mean(0)
    out = {}
    for st, m in mask_by_subtype.items():
        idx = np.where(m)[0]
        if resample:
            idx = rng.choice(idx, len(idx), replace=True)
        out[st] = unit(A - Z[idx].mean(0))
    return out, A


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    ab = pd.read_parquet(args.aphasia).reset_index(drop=True)
    feat = sorted(c for c in ab.columns if c not in AB_META)
    Z = StandardScaler().fit_transform(ab[feat].to_numpy(float))
    masks = {st: (ab.subtype == st).to_numpy() for st in SUBTYPES}
    ctrl_mask = (ab.is_control == True).to_numpy()

    # ---- PRIMARY: within-AB recovery axes ----
    print("=== PRIMARY: within-AphasiaBank recovery directions (→ healthy adult) ===")
    R, A = recovery_dirs(Z, masks, ctrl_mask)
    print("pairwise cosine of recovery directions (1.0 = same axis):")
    print("           " + "  ".join(f"{s[:6]:>6s}" for s in SUBTYPES))
    for a in SUBTYPES:
        print(f"  {a[:9]:9s} " + "  ".join(f"{R[a] @ R[b]:6.2f}" for b in SUBTYPES))
    paths = {st: float(np.linalg.norm(A - Z[masks[st]].mean(0))) for st in SUBTYPES}
    print("\n  recovery-axis isolation (mean cos to OTHER subtypes) + path length:")
    for st in SUBTYPES:
        mc = float(np.mean([R[st] @ R[o] for o in SUBTYPES if o != st]))
        print(f"    {st:11s} mean-cos={mc:+.3f}   |path to health|={paths[st]:.2f}")

    # bootstrap: is Broca's axis a significant outlier vs the fluent cluster?
    gaps = []           # fluent-internal coherence  −  Broca-to-fluent coherence
    broca_mc, fluent_mc = [], []
    for _ in range(args.boot):
        Rb, _ = recovery_dirs(Z, masks, ctrl_mask, rng=rng, resample=True)
        b2f = np.mean([Rb["Broca"] @ Rb[f] for f in FLUENT])
        fpair = [Rb[a] @ Rb[b] for i, a in enumerate(FLUENT) for b in FLUENT[i+1:]]
        f2f = np.mean(fpair)
        broca_mc.append(b2f); fluent_mc.append(f2f); gaps.append(f2f - b2f)
    gaps = np.array(gaps)
    lo, hi = np.percentile(gaps, [2.5, 97.5])
    p_gap = float((gaps <= 0).mean())   # fraction where Broca is NOT the outlier
    print(f"\n  Broca-to-fluent cos  : {np.mean(broca_mc):.3f} "
          f"[{np.percentile(broca_mc,2.5):.3f}, {np.percentile(broca_mc,97.5):.3f}]")
    print(f"  fluent-internal cos  : {np.mean(fluent_mc):.3f} "
          f"[{np.percentile(fluent_mc,2.5):.3f}, {np.percentile(fluent_mc,97.5):.3f}]")
    print(f"  coherence gap (fluent − Broca): {gaps.mean():.3f}  95% CI [{lo:.3f},{hi:.3f}]  "
          f"P(gap≤0)={p_gap:.4f}")
    print("  → CI excluding 0 ⇒ Broca recovers along a significantly distinct axis.")

    pd.DataFrame([{"subtype": st, "mean_cos_to_others":
                   float(np.mean([R[st] @ R[o] for o in SUBTYPES if o != st])),
                   "path_to_health": paths[st]} for st in SUBTYPES]
                 ).to_csv(args.output_dir / "recovery_axes.csv", index=False)

    # ---- SECONDARY: cross-corpus domain-gap diagnostic ----
    print("\n=== SECONDARY: cross-corpus developmental test (CONFOUNDED — diagnostic) ===")
    chi = pd.read_parquet(args.childes)
    chi = chi.dropna(subset=["age_months"])
    chi = chi[(chi.age_months > 0) & (chi.age_months <= 84)]
    cc = set(c for c in chi.columns if c not in CHI_META)
    common = sorted(cc & set(feat))
    asym = [f for f in common if ((ab[f].fillna(0) == 0).mean() >= .99 and (chi[f].fillna(0) == 0).mean() <= .5)
            or ((chi[f].fillna(0) == 0).mean() >= .99 and (ab[f].fillna(0) == 0).mean() <= .5)]
    common = [c for c in common if c not in asym]
    Xall = pd.concat([chi[common], ab[common]], ignore_index=True).to_numpy(float)
    sc = StandardScaler().fit(Xall)
    Zchi = sc.transform(chi[common].to_numpy(float))
    man = Zchi[rng.choice(len(Zchi), min(3000, len(Zchi)), replace=False)]
    Actrl = sc.transform(ab[ab.is_control == True][common].to_numpy(float)).mean(0)
    def ndc(p): return float(np.sqrt(((man - p) ** 2).sum(1)).min())
    print(f"  clean shared features: {len(common)}")
    print("  distance from each AB centroid to nearest CHILDES window:")
    for st in SUBTYPES:
        c = sc.transform(ab[ab.subtype == st][common].to_numpy(float)).mean(0)
        print(f"    {st:11s} {ndc(c):.2f}")
    print(f"    {'healthy adult':11s} {ndc(Actrl):.2f}   ← as far from children as Broca")
    print("  ⇒ the CHILDES↔AphasiaBank domain gap, not pathology, sets the "
          "distance to\n    the developmental manifold. Cross-corpus recovery-"
          "retraces-development is\n    not cleanly testable here; see #49 for the "
          "clean MLU-matched static test.")

    # ---- TERTIARY: longitudinal recovery vectors ----
    print("\n=== TERTIARY: longitudinal recovery vectors (small n; AQ mostly stable) ===")
    sess = ab.dropna(subset=["wab_aq"]).copy()
    sess["root"] = sess.participant_id.map(lambda p: (re.match(r"^(.*?)([a-z])$", str(p)) or [p, p, ""])[1]
                                           if re.match(r"^(.*?)([a-z])$", str(p)) else str(p))
    sess["root"] = sess.participant_id.map(lambda p: re.sub(r"[a-z]$", "", str(p)))
    sess["sl"] = sess.participant_id.map(lambda p: (re.search(r"([a-z])$", str(p)) or [""])[0])
    for st in SUBTYPES:
        s = sess[sess.subtype == st]; cosA = []; n = 0
        for root, d0 in s.groupby("root"):
            if d0.sl.nunique() < 2:
                continue
            d0 = d0.sort_values("sl"); f, l = d0.sl.iloc[0], d0.sl.iloc[-1]
            if d0[d0.sl == l].wab_aq.iloc[0] <= d0[d0.sl == f].wab_aq.iloc[0]:
                continue
            n += 1
            e = Z[ab.participant_id.isin(d0[d0.sl == f].participant_id).to_numpy()].mean(0)
            la = Z[ab.participant_id.isin(d0[d0.sl == l].participant_id).to_numpy()].mean(0)
            Rv = la - e
            if np.linalg.norm(Rv) > 1e-9:
                cosA.append(float(unit(Rv) @ unit(A - e)))
        if cosA:
            print(f"    {st:11s} improving n={n}: cos(recovery, →adult)={np.mean(cosA):+.3f}")

    # ---- Visualization: within-AB recovery axes ----
    pca = PCA(n_components=2, random_state=0).fit(Z)
    fig, ax = plt.subplots(figsize=(8.5, 7))
    for st, col in zip(SUBTYPES, ["red", "orange", "purple", "brown"]):
        P = pca.transform(Z[masks[st]])
        ax.scatter(P[:, 0], P[:, 1], s=9, alpha=0.25, color=col, label=st)
    Pc = pca.transform(Z[ctrl_mask])
    ax.scatter(Pc[:, 0], Pc[:, 1], s=12, alpha=0.4, c="k", marker="x", label="healthy adults")
    Ap = pca.transform(A[None, :])[0]
    for st, col in zip(SUBTYPES, ["red", "orange", "purple", "brown"]):
        Sp = pca.transform(Z[masks[st]].mean(0)[None, :])[0]
        ax.annotate("", xy=Ap, xytext=Sp,
                    arrowprops=dict(arrowstyle="->", color=col, lw=2.5, alpha=0.95))
    ax.scatter(*Ap, c="lime", s=200, marker="*", edgecolor="k", zorder=6, label="health (target)")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    ax.set_title("Within-AphasiaBank recovery axes — Broca's points a distinct way")
    ax.legend(loc="best", fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(args.output_dir / "recovery_axes.png", dpi=150)
    plt.close(fig)
    print(f"\nsaved → {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
