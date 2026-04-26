"""Test-retest stability of z within stable patients.

For controls and PWAs whose WAB-AQ didn't move much (|ΔAQ| < 5) across
two sessions, how much does z move between sessions? If z is wildly
unstable for stable patients, our trajectory and longitudinal claims
collapse to noise. If it's tight, the measurement is reliable enough
for clinical use.

Reports:
  - Per-dimension intraclass-correlation-style stability
    (1 - within-patient variance / between-patient variance, computed
    on the matched short-Δt pairs).
  - Per-feature MAE for stable patients.
  - Compares to known WAB-AQ test-retest reliability (3-5 AQ points).
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


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
    p.add_argument("--embeddings-path",
                   default="data/features/aphasia_window_embeddings.parquet",
                   type=Path)
    p.add_argument("--output-dir", default="outputs/test_retest", type=Path)
    p.add_argument("--max-dt-days", type=int, default=180,
                   help="Max days between sessions to count as test-retest.")
    p.add_argument("--max-aq-change", type=float, default=5.0,
                   help="Max |ΔAQ| to count as 'stable' patient.")
    p.add_argument("--use-embeddings", action="store_true")
    return p.parse_args()


def aggregate_session(df, feature_cols):
    keep = ["patient_root", "session_letter", "session_date", "subtype",
            "wab_aq", "corpus", "participant_id", "is_control"]
    return df.groupby("participant_id").agg(
        {**{f: "mean" for f in feature_cols},
         **{m: "first" for m in keep if m != "participant_id"}}
    ).reset_index()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.features_path)
    df["patient_root"] = df["participant_id"].str.replace(
        r"[a-zA-Z]$", "", regex=True)
    df["session_letter"] = df["participant_id"].str.extract(r"([a-zA-Z])$")[0]
    feature_cols = sorted(c for c in df.columns if c not in META_COLS)

    if args.use_embeddings and args.embeddings_path.exists():
        embs = pd.read_parquet(args.embeddings_path)
        df = df.merge(embs, on="window_id", how="inner")
        emb_cols = sorted(c for c in embs.columns if c.startswith("emb"))
        feature_cols = feature_cols + emb_cols
        print(f"  joined embeddings ({len(emb_cols)} dims)")

    sessions = aggregate_session(df, feature_cols)
    print(f"sessions: {len(sessions)}")

    # Build short-Δt matched pairs from same patient.
    pairs = []
    for pat, g in sessions.groupby("patient_root"):
        g = g.sort_values("session_letter").reset_index(drop=True)
        if len(g) < 2:
            continue
        for i in range(len(g) - 1):
            r1, r2 = g.iloc[i], g.iloc[i + 1]
            d1, d2 = r1.get("session_date"), r2.get("session_date")
            try:
                dt = (datetime.fromisoformat(d2) -
                      datetime.fromisoformat(d1)).days
            except (TypeError, ValueError):
                dt = None
            if dt is None or dt < 0 or dt > args.max_dt_days:
                continue
            d_aq = (r2["wab_aq"] - r1["wab_aq"]
                    if pd.notna(r1["wab_aq"]) and pd.notna(r2["wab_aq"])
                    else 0.0)
            if abs(d_aq) > args.max_aq_change:
                continue
            row = {"patient_root": pat,
                   "delta_t_days": dt,
                   "delta_aq": d_aq,
                   "is_control": bool(r1["is_control"]),
                   "subtype": r1["subtype"]}
            for f in feature_cols:
                row[f"a_{f}"] = r1[f]
                row[f"b_{f}"] = r2[f]
            pairs.append(row)
    pdf = pd.DataFrame(pairs)
    print(f"\nstable matched pairs (Δt ≤ {args.max_dt_days} days, "
          f"|ΔAQ| ≤ {args.max_aq_change}): {len(pdf)}")
    if not len(pdf):
        return

    print(f"  Δt: median {pdf['delta_t_days'].median():.0f}  "
          f"mean {pdf['delta_t_days'].mean():.0f}")
    print(f"  controls: {int(pdf['is_control'].sum())}  "
          f"pwa: {int((~pdf['is_control']).sum())}")

    # ---- z=8 reliability ----
    Xa = pdf[[f"a_{f}" for f in feature_cols]].to_numpy(dtype=float)
    Xb = pdf[[f"b_{f}" for f in feature_cols]].to_numpy(dtype=float)
    Xall = np.vstack([Xa, Xb])
    scaler = StandardScaler().fit(Xall)
    Xall_s = scaler.transform(Xall)
    pca = PCA(n_components=8, random_state=0).fit(Xall_s)
    Za = pca.transform(scaler.transform(Xa))
    Zb = pca.transform(scaler.transform(Xb))

    print(f"\n--- z=8 test-retest reliability (matched stable pairs) ---")
    print("  dim |  ICC-like  |  mean |delta|  |  pop. SD")
    for j in range(8):
        delta = Zb[:, j] - Za[:, j]
        within_var = float(np.var(delta) / 2.0)  # ICC numerator
        between_var = float(np.var(np.concatenate([Za[:, j], Zb[:, j]])))
        icc = 1.0 - within_var / between_var if between_var > 0 else float("nan")
        print(f"   z{j+1} | {icc:+.3f}  | {float(np.mean(np.abs(delta))):>8.3f}  "
              f"| {float(np.std(np.concatenate([Za[:, j], Zb[:, j]]))):>6.3f}")

    # ---- per-feature MAE for the structural features ----
    n_struct = 55  # the original feature set
    print(f"\n--- top-10 MOST stable / LEAST stable structural features ---")
    abs_diffs = []
    for f in feature_cols[:n_struct]:
        a = pdf[f"a_{f}"].to_numpy(dtype=float)
        b = pdf[f"b_{f}"].to_numpy(dtype=float)
        if np.std(np.concatenate([a, b])) < 1e-6:
            continue
        delta = b - a
        within = float(np.var(delta) / 2.0)
        between = float(np.var(np.concatenate([a, b])))
        icc = 1 - within / between if between > 0 else float("nan")
        abs_diffs.append({
            "feature": f,
            "icc": float(icc),
            "mean_abs_delta": float(np.mean(np.abs(delta))),
            "pop_sd": float(np.std(np.concatenate([a, b]))),
            "rel_delta_sd": float(np.mean(np.abs(delta)) /
                                   np.std(np.concatenate([a, b]))) if between > 0 else float("nan"),
        })
    fd = pd.DataFrame(abs_diffs).sort_values("icc", ascending=False)
    print("\n  TOP 10 most-stable features (highest ICC):")
    print(fd.head(10).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print("\n  BOTTOM 10 least-stable features:")
    print(fd.tail(10).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    fd.to_csv(args.output_dir / "feature_test_retest.csv", index=False)

    # ---- WAB-AQ test-retest in the same matched stable pairs (sanity) ----
    aqs = pdf.dropna(subset=["delta_aq"])
    if len(aqs):
        delta = aqs["delta_aq"].to_numpy(dtype=float)
        print(f"\n  WAB-AQ in same matched stable subset: "
              f"mean |delta| = {float(np.mean(np.abs(delta))):.2f}, "
              f"median = {float(np.median(np.abs(delta))):.2f}, "
              f"max = {float(np.max(np.abs(delta))):.2f}  "
              f"(literature reports ~3-5 point test-retest reliability)")

    print(f"\nDone. Outputs in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
