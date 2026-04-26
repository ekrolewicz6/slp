"""Phase 4 (preview): therapy-response signatures across AphasiaBank corpora.

We don't have explicit per-patient therapy metadata, but **the corpus name
is a strong proxy** for the therapy regime in many cases. Concretely:

    Kurland       — Constraint-Induced Verbal Aphasia therapy (intensive)
    SCALE         — Speech Comm. and Aphasia Lab Experience (4-week intensive)
    UNH           — University of New Hampshire intensive treatment
    MSU           — Montclair State intensive 6-week treatment
    Fridriksson   — treatment-study sites
    Adler         — community Aphasia Center (longer-term group + 1:1)

Two questions, both deliberately observational (no causal claim):

  1. **Do feature changes differ systematically across these corpora?**
     If yes, that's evidence that different therapy regimes produce
     distinguishable behavioral signatures — even before we can say
     anything causal about which is "better."

  2. **For corpora where WAB-AQ did change (SCALE, where some patients
     gained 20–37 points), does the feature change at sessions 1→2
     predict the AQ change at sessions 1→last?** This is the "early
     speech change predicts eventual outcome" question — clinically
     valuable as triage even without intervention metadata.

Why this matters for the project's framing: many longitudinal corpora
administer WAB only once, so AQ stays constant across the multiple
discourse-protocol sessions a patient does. Yet *the patient is in
therapy*, and our features may detect that movement. If z₂ / z₃ change
within a Kurland patient whose AQ is "stuck" at 51.5, we're picking up
something the clinical scoring system literally cannot record.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr, ttest_1samp


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
    p.add_argument("--output-dir", default="outputs/phase4_therapy", type=Path)
    p.add_argument("--min-patients-per-corpus", type=int, default=4)
    return p.parse_args()


def aggregate_session(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    keep = ["patient_root", "session_letter", "session_date", "subtype",
            "wab_aq", "corpus", "section", "participant_id", "is_control"]
    return df.groupby("participant_id").agg(
        {**{f: "mean" for f in feature_cols},
         **{m: "first" for m in keep}}
    ).reset_index(drop=True)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df["patient_root"] = df["participant_id"].str.replace(r"[a-zA-Z]$", "",
                                                          regex=True)
    df["session_letter"] = df["participant_id"].str.extract(r"([a-zA-Z])$")[0]

    feature_cols = sorted(c for c in df.columns if c not in META_COLS)

    # ----- Sessions, then per-patient first / last sessions -----
    sessions = aggregate_session(df, feature_cols)
    sessions = sessions.dropna(subset=["session_letter"])

    multi = sessions.groupby("patient_root").filter(lambda g: len(g) >= 2)
    print(f"Multi-session patients: {multi['patient_root'].nunique()} "
          f"across {multi['corpus'].nunique()} corpora")

    # PCA z=8 fit on the FULL session set (not just longitudinal) so the
    # latent space matches earlier analyses.
    Xs = StandardScaler().fit_transform(sessions[feature_cols].to_numpy(dtype=float))
    pca = PCA(n_components=8, random_state=0).fit(Xs)
    Z = pca.transform(Xs)
    for i in range(8):
        sessions[f"z{i+1}"] = Z[:, i]
    z_cols = [f"z{i+1}" for i in range(8)]

    # Re-collect first / last per patient so we have z too.
    multi = sessions.groupby("patient_root").filter(lambda g: len(g) >= 2)
    pairs = []
    for pat, g in multi.groupby("patient_root"):
        g = g.sort_values("session_letter")
        r1, rL = g.iloc[0], g.iloc[-1]
        d1, dL = r1.get("session_date"), rL.get("session_date")
        try:
            dt_days = (datetime.fromisoformat(dL) - datetime.fromisoformat(d1)).days
        except (TypeError, ValueError):
            dt_days = None
        row = {
            "patient_root": pat,
            "corpus": r1["corpus"],
            "section": r1["section"],
            "subtype": r1["subtype"],
            "n_sessions": len(g),
            "delta_t_days": dt_days,
            "aq_t1": r1["wab_aq"],
            "aq_tL": rL["wab_aq"],
        }
        for f in feature_cols + z_cols:
            row[f"d_{f}"] = rL[f] - r1[f]
            row[f"t1_{f}"] = r1[f]
        pairs.append(row)
    pairs_df = pd.DataFrame(pairs)
    pairs_df.to_csv(args.output_dir / "first_last_pairs.csv", index=False)

    # ----- Test 1: do feature changes have a systematic direction within each corpus? -----
    big_corpora = (pairs_df.groupby("corpus").size()
                           .where(lambda s: s >= args.min_patients_per_corpus)
                           .dropna().index.tolist())
    print(f"\n[T1] Corpora with ≥{args.min_patients_per_corpus} longitudinal patients:")
    print(f"  {big_corpora}")

    rows_t1 = []
    for corp in big_corpora:
        sub = pairs_df[pairs_df["corpus"] == corp]
        n = len(sub)
        for f in z_cols + ["mlu_morphemes", "mlu_words", "ttr", "ndw",
                           "verbs_per_utterance", "utt_len_std",
                           "function_word_ratio", "hapax_ratio",
                           "single_word_ratio"]:
            col = f"d_{f}"
            if col not in sub.columns:
                continue
            vals = sub[col].dropna()
            if len(vals) < 4:
                continue
            t, p = ttest_1samp(vals, 0.0)
            rows_t1.append({"corpus": corp, "feature": f, "n": int(len(vals)),
                            "mean_change": float(vals.mean()),
                            "std_change": float(vals.std()),
                            "t_stat": float(t), "p": float(p)})
    t1_df = pd.DataFrame(rows_t1)
    t1_df.to_csv(args.output_dir / "directional_changes.csv", index=False)

    # Print the meaningfully-directional ones (|t|>1.5, focus on z + MLU + TTR)
    print("\n[T1] Features with |t-stat| ≥ 1.5 (directional change vs zero):")
    sig = t1_df[t1_df["t_stat"].abs() >= 1.5].sort_values(
        ["corpus", "p"]).reset_index(drop=True)
    for _, r in sig.iterrows():
        sign = "↑" if r["mean_change"] > 0 else "↓"
        print(f"  {r['corpus']:14s}  {r['feature']:24s}  "
              f"Δ={r['mean_change']:+.3f}  n={int(r['n']):>3}  "
              f"t={r['t_stat']:+.2f}  p={r['p']:.3f}  {sign}")

    # ----- Test 2: does Δfeature predict ΔAQ on the SCALE-style change subset? -----
    print("\n[T2] Predict ΔAQ from Δfeatures (corpora with real AQ change)")
    aq_changers = pairs_df.dropna(subset=["aq_t1", "aq_tL"]).copy()
    aq_changers["delta_aq"] = aq_changers["aq_tL"] - aq_changers["aq_t1"]
    aq_changers = aq_changers[aq_changers["delta_aq"].abs() >= 5]
    print(f"  Patients with |ΔAQ| ≥ 5: {len(aq_changers)} "
          f"({aq_changers['corpus'].nunique()} corpora)")
    print(f"  ΔAQ stats: mean={aq_changers['delta_aq'].mean():+.1f}  "
          f"std={aq_changers['delta_aq'].std():.1f}  "
          f"range [{aq_changers['delta_aq'].min():+.1f}, "
          f"{aq_changers['delta_aq'].max():+.1f}]")

    rows_t2 = []
    for f in z_cols + ["mlu_words", "mlu_morphemes", "utt_len_mean", "ttr", "ndw",
                       "function_word_ratio"]:
        col = f"d_{f}"
        x = aq_changers[col].to_numpy(dtype=float)
        y = aq_changers["delta_aq"].to_numpy(dtype=float)
        if len(x) < 5:
            continue
        r, p = pearsonr(x, y)
        rows_t2.append({"feature": f, "n": int(len(x)),
                        "r": float(r), "p": float(p)})
    t2_df = pd.DataFrame(rows_t2).sort_values("r", key=lambda s: s.abs(),
                                              ascending=False)
    t2_df.to_csv(args.output_dir / "delta_feature_predicts_delta_aq.csv",
                 index=False)
    print("\n  Δfeature → ΔAQ Pearson correlations (sorted by |r|):")
    for _, r in t2_df.head(10).iterrows():
        print(f"    {r['feature']:25s}  n={int(r['n'])}  r={r['r']:+.3f}  "
              f"p={r['p']:.3f}")

    # ----- Test 3: SCALE-specific — early-session change predicts AQ improvement -----
    print("\n[T3] SCALE-only: does early-session change predict eventual ΔAQ?")
    scale = sessions[sessions["corpus"] == "SCALE"].copy()
    scale = scale.dropna(subset=["wab_aq"]).sort_values(["patient_root",
                                                          "session_letter"])
    scale_pat = scale.groupby("patient_root")
    rows_t3 = []
    for pat, g in scale_pat:
        if len(g) < 3:
            continue
        s1, s2, sL = g.iloc[0], g.iloc[1], g.iloc[-1]
        rec = {
            "patient_root": pat,
            "n_sessions": len(g),
            "aq_t1": s1["wab_aq"],
            "aq_tL": sL["wab_aq"],
            "delta_aq_total": sL["wab_aq"] - s1["wab_aq"],
        }
        for f in z_cols + ["mlu_words", "ttr", "ndw"]:
            rec[f"d12_{f}"] = s2[f] - s1[f]
        rows_t3.append(rec)
    t3 = pd.DataFrame(rows_t3)
    print(f"  SCALE patients with ≥3 sessions: {len(t3)}")
    if len(t3) >= 5:
        for f in z_cols + ["mlu_words", "ttr", "ndw"]:
            r, p = pearsonr(t3[f"d12_{f}"], t3["delta_aq_total"])
            print(f"    early Δ{f:25s}  predicts final ΔAQ  "
                  f"r={r:+.3f}  p={p:.3f}")

    # ----- Visual: side-by-side per-corpus z₂ + z₃ trajectories -----
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, dim in zip(axes, ["z2", "z3", "wab_aq"]):
        for corp in big_corpora:
            sub = sessions[(sessions["corpus"] == corp)
                           & (sessions["patient_root"].isin(
                               multi["patient_root"].unique()))]
            for pat, g in sub.groupby("patient_root"):
                g = g.sort_values("session_letter")
                if len(g) < 2:
                    continue
                xs = list(range(len(g)))
                ax.plot(xs, g[dim].values, "-", alpha=0.4, color={
                    "Kurland": "C0", "SCALE": "C1", "UNH": "C2", "MSU": "C3",
                    "Fridriksson": "C4", "Williamson": "C5", "Tucson": "C6",
                }.get(corp, "k"))
        ax.set_xlabel("Session index"); ax.set_ylabel(dim)
        ax.set_title(f"{dim} trajectories by corpus")
        ax.grid(alpha=0.3)
    # legend by corpus
    for corp in big_corpora:
        axes[0].plot([], [], "-", color={
            "Kurland": "C0", "SCALE": "C1", "UNH": "C2", "MSU": "C3",
            "Fridriksson": "C4", "Williamson": "C5", "Tucson": "C6",
        }.get(corp, "k"), label=f"{corp} (n={pairs_df[pairs_df.corpus==corp]['patient_root'].nunique()})")
    axes[0].legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(args.output_dir / "trajectories_by_corpus.png", dpi=150)
    plt.close(fig)

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
