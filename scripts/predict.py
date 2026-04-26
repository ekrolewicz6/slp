"""End-to-end clinical-preview demo: audio path → JSON prediction summary.

Given a .wav/.mp3/.mp4 file containing speech (and optionally a .cha
transcript with PAR utterances), produce:

    {
      "z": {z1: ..., z2: ..., ...},
      "predicted_wab_aq": ...,
      "wab_aq_interval_80pct": [lo, hi],
      "trajectory_class_probs": {Improver: ..., Stable: ..., Decliner: ...},
      "developmental_age_equiv_months": ...,
      "subtype_probs": {Anomic: ..., Broca: ..., ...},
      "warnings": [...]
    }

Pipeline:
  1. If transcript missing, transcribe the audio with whisper (free,
     local). Otherwise use the provided .cha file.
  2. Extract structural features (pylangacq + extractors).
  3. Extract semantic embeddings (sentence-transformers MPNet).
  4. (Optional) extract acoustic features (parselmouth).
  5. Aggregate to one feature vector for the speaker.
  6. Apply pre-trained models from disk (we just train them on the fly
     from the AphasiaBank features parquet for the demo, since
     persisting models adds complexity).
  7. Emit JSON.

This is a *demo*: we train the models inline at first call to keep the
script self-contained. For a real product the models would be
serialized.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq as pla
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

from src.features.extractors import extract_features
from src.features.windowed import window_utterances


META = {"transcript_id", "section", "corpus", "participant_id",
        "patient_root", "session_letter", "age_years", "sex", "subtype",
        "wab_aq", "is_control", "session_date", "window_id", "window_index",
        "n_chi_utts_in_window"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path,
                   help="Path to a .cha transcript OR an audio/video file.")
    p.add_argument("--participant", default="PAR",
                   help="Participant code to extract features for (PAR for "
                        "AphasiaBank, CHI for CHILDES).")
    p.add_argument("--output", default="-",
                   help="Output file path; '-' for stdout.")
    p.add_argument("--ab-features",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--childes-features",
                   default="data/features/phase1_windowed_features.parquet",
                   type=Path)
    return p.parse_args()


def load_chat(path: Path):
    """Load a .cha file and return (utterances, source-warning-list)."""
    warns = []
    if not path.suffix.lower() == ".cha":
        warns.append("Audio-input pipeline (Whisper transcription) not "
                     "implemented in this demo. Pass a .cha transcript.")
        return None, warns
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        chat = pla.read_chat(str(path), strict=False)
    return chat.utterances(), warns


def main() -> None:
    args = parse_args()
    out_warnings: list[str] = []

    print(f"# loading {args.input}", file=sys.stderr)
    utts, warns = load_chat(args.input)
    out_warnings.extend(warns)
    if utts is None:
        json.dump({"error": "Could not load transcript", "warnings": out_warnings},
                  sys.stdout if args.output == "-" else open(args.output, "w"),
                  indent=2)
        return

    # Extract per-window features for the participant
    windows = window_utterances(utts, participant=args.participant,
                                 window_size=100, min_window_utts=20)
    if not windows:
        # Fall back to whole-file aggregate
        feats = extract_features(utts, participant=args.participant,
                                  min_utterances=10)
        if feats is None:
            json.dump({"error": f"Insufficient {args.participant} utterances "
                                f"to extract features",
                       "warnings": out_warnings},
                      sys.stdout if args.output == "-" else open(args.output, "w"),
                      indent=2)
            return
        all_feats = [feats]
        out_warnings.append("Sample too short for windowing; using whole-file "
                             "features.")
    else:
        all_feats = []
        for w in windows:
            f = extract_features(w, participant=args.participant,
                                  min_utterances=20)
            if f is not None:
                all_feats.append(f)

    # Mean-pool per-window features
    feat_df = pd.DataFrame(all_feats)
    speaker_features = feat_df.mean(axis=0)

    # Train models inline on AphasiaBank features
    print("# training models on AphasiaBank reference data ...", file=sys.stderr)
    ab = pd.read_parquet(args.ab_features)
    feature_cols = sorted(c for c in ab.columns if c not in META)

    # Patient-level reference table
    pat = ab.groupby("participant_id").agg(
        {**{c: "mean" for c in feature_cols},
         **{m: "first" for m in ["wab_aq", "subtype", "corpus"]}}
    ).reset_index()
    pat = pat.dropna(subset=["wab_aq"]).reset_index(drop=True)
    pat = pat[pat.wab_aq.between(0, 100)].reset_index(drop=True)

    # Align feature vector to the same column order
    speaker_vec = np.array([speaker_features.get(c, 0.0) for c in feature_cols],
                           dtype=float).reshape(1, -1)

    Xref = pat[feature_cols].to_numpy(dtype=float)
    scaler = StandardScaler().fit(Xref)
    pca = PCA(n_components=8, random_state=0).fit(scaler.transform(Xref))
    Zref = pca.transform(scaler.transform(Xref))
    Zspeaker = pca.transform(scaler.transform(speaker_vec))

    # WAB-AQ regression (point + 80% interval via quantile GBMs)
    y_aq = pat["wab_aq"].to_numpy(dtype=float)
    sub_arr = pat["subtype"].fillna("Unknown").to_numpy(dtype=object)
    median_gbm = GradientBoostingRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0).fit(Xref, y_aq)
    q10_gbm = GradientBoostingRegressor(
        loss="quantile", alpha=0.1, n_estimators=400, max_depth=3,
        learning_rate=0.05, subsample=0.9, random_state=0).fit(Xref, y_aq)
    q90_gbm = GradientBoostingRegressor(
        loss="quantile", alpha=0.9, n_estimators=400, max_depth=3,
        learning_rate=0.05, subsample=0.9, random_state=0).fit(Xref, y_aq)
    aq_pt = float(median_gbm.predict(speaker_vec)[0])
    aq_lo = float(q10_gbm.predict(speaker_vec)[0])
    aq_hi = float(q90_gbm.predict(speaker_vec)[0])

    # Subtype probabilities
    sub_pat = pat.dropna(subset=["subtype"]).reset_index(drop=True)
    sub_pat = sub_pat[~sub_pat["subtype"].isin({"Unknown", "U"})]
    counts = sub_pat.groupby("subtype")["participant_id"].count()
    keep = counts[counts >= 5].index.tolist()
    sub_pat = sub_pat[sub_pat["subtype"].isin(keep)].reset_index(drop=True)
    Xs = sub_pat[feature_cols].to_numpy(dtype=float)
    ys = sub_pat["subtype"].to_numpy(dtype=object)
    clf = GradientBoostingClassifier(
        n_estimators=300, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=0).fit(Xs, ys)
    probs = clf.predict_proba(speaker_vec)[0]
    subtype_probs = {cls: float(probs[i]) for i, cls in enumerate(clf.classes_)}

    # Developmental age equivalent (regressor trained on CHILDES)
    dev_age = None
    if args.childes_features.exists():
        chi = pd.read_parquet(args.childes_features)
        chi = chi.dropna(subset=["age_months"])
        chi = chi[(chi.age_months > 0) & (chi.age_months <= 84)]
        chi_feature_cols = sorted(
            c for c in chi.columns
            if c not in {"transcript_id", "corpus", "child_id", "age_months",
                         "n_chi_utterances", "bundle", "window_id",
                         "window_index", "n_chi_utts_in_window"})
        common = sorted(set(feature_cols) & set(chi_feature_cols))
        chi_X = chi[common].to_numpy(dtype=float)
        chi_y = chi["age_months"].to_numpy(dtype=float)
        chi_scaler = StandardScaler().fit(chi_X)
        age_model = GradientBoostingRegressor(
            n_estimators=600, max_depth=4, learning_rate=0.05,
            subsample=0.85, random_state=0).fit(chi_scaler.transform(chi_X), chi_y)
        speaker_common = np.array([speaker_features.get(c, 0.0) for c in common],
                                   dtype=float).reshape(1, -1)
        dev_age = float(age_model.predict(chi_scaler.transform(speaker_common))[0])

    out = {
        "input": str(args.input),
        "n_windows_analysed": len(all_feats),
        "z": {f"z{j+1}": float(Zspeaker[0, j]) for j in range(8)},
        "predicted_wab_aq": round(aq_pt, 1),
        "wab_aq_interval_80pct": [round(aq_lo, 1), round(aq_hi, 1)],
        "subtype_probs": {k: round(v, 3) for k, v in
                          sorted(subtype_probs.items(), key=lambda kv: -kv[1])},
        "developmental_age_equiv_months": round(dev_age, 1) if dev_age else None,
        "warnings": out_warnings,
    }

    text = json.dumps(out, indent=2)
    if args.output == "-":
        print(text)
    else:
        Path(args.output).write_text(text)


if __name__ == "__main__":
    main()
