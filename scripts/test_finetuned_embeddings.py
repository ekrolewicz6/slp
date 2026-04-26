"""Re-embed AphasiaBank with the fine-tuned MiniLM, then test if Wernicke
classification improves vs the off-the-shelf MPNet baseline.

If the fine-tuned model captures semantic patterns specific to aphasic
speech, we should see Wernicke F1 jump from 0.18-0.20 to something
usable.
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq as pla
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

from src.features.windowed import window_utterances


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--idx-path",
                   default="data/features/aphasiabank_transcripts.parquet",
                   type=Path)
    p.add_argument("--model-dir",
                   default="data/features/finetuned_embedder/model",
                   type=Path)
    p.add_argument("--output-dir",
                   default="outputs/finetuned_embedder", type=Path)
    p.add_argument("--re-embed", action="store_true",
                   help="Re-embed all windows with the fine-tuned model "
                        "(slow). Skip to use a cached parquet.")
    p.add_argument("--cached-emb",
                   default="data/features/aphasia_window_emb_finetuned.parquet",
                   type=Path)
    return p.parse_args()


def utt_text(u) -> str:
    out = []
    for t in u.tokens:
        word = (t.word or "").strip()
        if not word or word in {".", "?", "!", ",", ";", ":"}:
            continue
        out.append(word)
    return " ".join(out)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    feats = pd.read_parquet(args.features_path)
    feature_cols = sorted(c for c in feats.columns
                           if c not in {"transcript_id", "section", "corpus",
                                         "participant_id", "patient_root",
                                         "session_letter", "age_years", "sex",
                                         "subtype", "wab_aq", "is_control",
                                         "session_date", "window_id",
                                         "window_index",
                                         "n_chi_utts_in_window"})

    if args.re_embed or not args.cached_emb.exists():
        print(f"loading fine-tuned model from {args.model_dir}")
        model = SentenceTransformer(str(args.model_dir), device="mps")

        idx = pd.read_parquet(args.idx_path)
        path_lookup = idx.drop_duplicates("transcript_id").set_index(
            "transcript_id")["file_path"].to_dict()

        rows = []
        sessions = feats["transcript_id"].unique()
        for tid in tqdm(sessions, desc="files"):
            path = path_lookup.get(tid)
            if path is None or not Path(path).exists():
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    chat = pla.read_chat(str(path), strict=False)
                utts = chat.utterances()
            except Exception:
                continue
            windows = window_utterances(utts, participant="PAR",
                                         window_size=100, min_window_utts=50)
            for w_idx, w in enumerate(windows):
                texts = [utt_text(u) for u in w]
                texts = [t for t in texts if t]
                if not texts:
                    continue
                emb = model.encode(texts, convert_to_numpy=True,
                                    show_progress_bar=False).mean(axis=0)
                row = {"window_id": f"{tid}#w{w_idx:02d}"}
                for j in range(emb.shape[0]):
                    row[f"emb{j:03d}"] = float(emb[j])
                rows.append(row)
        out = pd.DataFrame(rows)
        out.to_parquet(args.cached_emb, index=False)
        print(f"  wrote {args.cached_emb} with {len(out)} window rows")
    else:
        out = pd.read_parquet(args.cached_emb)
        print(f"  loaded cached {args.cached_emb}: {len(out)} rows")

    # ----- Subtype classification with fine-tuned embeddings -----
    df = feats.merge(out, on="window_id", how="inner")
    emb_cols = sorted(c for c in out.columns if c.startswith("emb"))
    print(f"\njoined: {len(df)} windows, {len(emb_cols)} fine-tuned emb dims")

    sub_df = df.dropna(subset=["subtype"]).copy()
    sub_df = sub_df[~sub_df["subtype"].isin({"Unknown", "U"})]
    counts = sub_df.drop_duplicates("participant_id").groupby(
        "subtype")["participant_id"].count()
    keep = counts[counts >= 5].index.tolist()
    sub_df = sub_df[sub_df["subtype"].isin(keep)].reset_index(drop=True)
    print(f"  {len(sub_df)} windows from "
          f"{sub_df['participant_id'].nunique()} patients in subtypes: "
          f"{sorted(keep)}")

    Xfeat = sub_df[feature_cols].to_numpy(dtype=float)
    Xemb = sub_df[emb_cols].to_numpy(dtype=float)
    y = sub_df["subtype"].to_numpy(dtype=object)
    groups = sub_df["participant_id"].to_numpy()

    def cv_classify(X):
        n_g = len(set(groups))
        gkf = GroupKFold(n_splits=max(2, min(5, n_g)))
        preds = np.empty_like(y, dtype=object)
        for tr, te in gkf.split(X, y, groups):
            if len(set(y[tr])) < 2:
                preds[te] = y[tr][0]; continue
            clf = GradientBoostingClassifier(
                n_estimators=300, max_depth=3, learning_rate=0.05,
                subsample=0.9, random_state=0).fit(X[tr], y[tr])
            preds[te] = clf.predict(X[te])
        per_class_f1 = {c: float(f1_score(y == c, preds == c, zero_division=0))
                         for c in sorted(set(y))}
        return {
            "accuracy": float((preds == y).mean()),
            "macro_f1": float(f1_score(y, preds, average="macro",
                                        zero_division=0)),
            "per_class_f1": per_class_f1,
        }

    setups = {
        "features_only": Xfeat,
        "finetuned_emb_only": Xemb,
        "features_plus_finetuned_emb": np.concatenate([Xfeat, Xemb], axis=1),
    }
    rows_out = []
    print()
    for name, X in setups.items():
        r = cv_classify(X)
        rows_out.append({"setup": name, "accuracy": r["accuracy"],
                          "macro_f1": r["macro_f1"]})
        print(f"  {name:35s}  acc={r['accuracy']:.3f}  macroF1={r['macro_f1']:.3f}")
        if "Wernicke" in r["per_class_f1"]:
            print(f"    Wernicke F1 = {r['per_class_f1']['Wernicke']:.3f}")
        for c, f1 in sorted(r["per_class_f1"].items()):
            n = int((y == c).sum())
            print(f"      {c:18s} n={n:>4}  F1={f1:.3f}")

    pd.DataFrame(rows_out).to_csv(args.output_dir / "classify.csv",
                                   index=False)


if __name__ == "__main__":
    main()
