"""Encoder bake-off: does ANY learned speech rep beat hand-crafted features?

The first Leap-1 benchmark used one representation (wav2vec2 layer-8
mean+std) and it did NOT beat the 55 hand-crafted features. That tests one
encoder, not the hypothesis. wav2vec2 SSL embeddings are known to be
dominated by speaker/channel identity; the linguistically-relevant signal
may live in a different layer or a content-oriented model.

This streams each session ONCE and extracts several representations per
window — wav2vec2 layers {6,9,12} and HuBERT layer 9 — so we can compare
them fairly on the same patients without re-downloading audio. Then it runs
the identical patient-grouped benchmark (WAB-AQ regression + subtype
classification) for each representation and for hand-crafted, and prints
the comparison.

Run:  .venv/bin/python -m scripts.encoder_bakeoff --limit 60 \
        --corpus-filter "Fridriksson-2,QAB,Tucson,SCALE,Kurland,Olness,UNH"
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq as pla
import soundfile as sf
from sklearn.decomposition import PCA
from sklearn.ensemble import (GradientBoostingClassifier,
                              GradientBoostingRegressor)
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extract_aphasia_acoustic import (cha_to_media_url,
                                              get_remote_size_mb,
                                              stream_extract_audio)
from src.features.foundation_rep import EmbedderConfig, FoundationEmbedder
from src.features.windowed import window_utterances
from src.ingestion.talkbank_media import load_dotenv, request_headers

META = {"transcript_id", "section", "corpus", "participant_id", "patient_root",
        "session_letter", "age_years", "sex", "subtype", "wab_aq", "is_control",
        "session_date", "window_id", "window_index", "n_chi_utts_in_window"}

# (variant_key, model_name, layer)
VARIANTS = [
    ("w2v6", "facebook/wav2vec2-base", 6),
    ("w2v9", "facebook/wav2vec2-base", 9),
    ("w2v12", "facebook/wav2vec2-base", 12),
    ("hub9", "facebook/hubert-base-ls960", 9),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--features-path",
                   default="data/features/aphasiabank_windowed_features.parquet",
                   type=Path)
    p.add_argument("--out-parquet",
                   default="data/features/aphasia_bakeoff_embeddings.parquet",
                   type=Path)
    p.add_argument("--corpus-filter",
                   default="SCALE,Kurland,Tucson,Olness,UNH,QAB,Williamson,UMD,Richardson")
    p.add_argument("--limit", type=int, default=400)
    p.add_argument("--target-sessions", type=int, default=85,
                   help="stop after this many sessions yield embeddings")
    p.add_argument("--flush-every", type=int, default=15)
    p.add_argument("--max-mp4-mb", type=int, default=180)
    p.add_argument("--audio-tmp", default="data/audio/bakeoff", type=Path)
    p.add_argument("--pca-dim", type=int, default=48)
    p.add_argument("--output-dir", default="outputs/representation_benchmark", type=Path)
    return p.parse_args()


def extract(args) -> pd.DataFrame:
    load_dotenv()
    headers, _, _ = request_headers(range_value=None)
    feats = pd.read_parquet(args.features_path)
    by_session = feats.drop_duplicates("transcript_id")[
        ["transcript_id", "section", "corpus", "participant_id"]]
    keep = {c.strip() for c in args.corpus_filter.split(",")}
    by_session = by_session[by_session["corpus"].isin(keep)]
    idx = pd.read_parquet("data/features/aphasiabank_transcripts.parquet")
    path_lookup = idx.drop_duplicates("transcript_id").set_index(
        "transcript_id")["file_path"].to_dict()

    # one embedder per distinct model
    models = {}
    for _, name, _ in VARIANTS:
        models.setdefault(name, FoundationEmbedder(EmbedderConfig(model_name=name)))
    layers_by_model: dict[str, list[int]] = {}
    for key, name, ly in VARIANTS:
        layers_by_model.setdefault(name, [])
        if ly not in layers_by_model[name]:
            layers_by_model[name].append(ly)

    args.audio_tmp.mkdir(parents=True, exist_ok=True)
    work = list(by_session.itertuples(index=False))[:args.limit]

    existing = None
    done_sessions: set[str] = set()
    if args.out_parquet.exists():
        existing = pd.read_parquet(args.out_parquet)
        done_sessions = set(existing["transcript_id"].unique())
        print(f"resuming: {len(existing)} rows from {len(done_sessions)} sessions")

    rows = []
    n_success = len(done_sessions)
    for r in tqdm(work, desc="bakeoff"):
        if n_success >= args.target_sessions:
            break
        if r.transcript_id in done_sessions:
            continue
        cha = path_lookup.get(r.transcript_id)
        if not cha or not Path(cha).exists():
            continue
        url = cha_to_media_url(Path(cha))
        if url is None:
            continue
        sz = get_remote_size_mb(url, headers)
        if sz is not None and sz > args.max_mp4_mb:
            continue
        wav_path = args.audio_tmp / f"{Path(cha).stem}.wav"
        if not stream_extract_audio(url, wav_path, headers):
            wav_path.unlink(missing_ok=True)
            continue
        before = len(rows)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                chat = pla.read_chat(str(cha), strict=False)
            windows = window_utterances(chat.utterances(), participant="PAR",
                                        window_size=100, min_window_utts=50)
            wav, sr = sf.read(str(wav_path))
            if wav.ndim > 1:
                wav = wav.mean(axis=1)
            for w_idx, win in enumerate(windows):
                segs = []
                for u in win:
                    tm = u.time_marks
                    if tm is None or len(tm) != 2:
                        continue
                    a, b = int(tm[0] / 1000 * sr), int(tm[1] / 1000 * sr)
                    if b - a >= sr // 5:
                        segs.append(wav[max(0, a):min(len(wav), b)])
                if not segs:
                    continue
                clip = np.concatenate(segs).astype(np.float32)
                row = {"window_id": f"{r.transcript_id}#w{w_idx:02d}",
                       "transcript_id": r.transcript_id,
                       "participant_id": r.participant_id, "corpus": r.corpus}
                for name, emb in models.items():
                    vecs = emb.embed_segment_layers(clip, sr, layers_by_model[name])
                    for key, mname, ly in VARIANTS:
                        if mname == name:
                            for i, v in enumerate(vecs[ly]):
                                row[f"{key}_{i:04d}"] = float(v)
                rows.append(row)
        except Exception as e:
            tqdm.write(f"[err] {r.transcript_id}: {type(e).__name__}: {e}")
        finally:
            wav_path.unlink(missing_ok=True)
        if len(rows) > before:
            n_success += 1
            if n_success % args.flush_every == 0:
                part = pd.DataFrame(rows)
                if existing is not None:
                    part = pd.concat([existing, part], ignore_index=True)
                part.to_parquet(args.out_parquet, index=False)
                existing, rows = part, []
                tqdm.write(f"[flush] {n_success} sessions embedded")

    df = pd.DataFrame(rows)
    if existing is not None:
        df = pd.concat([existing, df], ignore_index=True)
    if len(df):
        df.to_parquet(args.out_parquet, index=False)
    return df


def reg_cv(X, y, g):
    gkf = GroupKFold(n_splits=max(2, min(5, len(set(g)))))
    pred = np.zeros_like(y, dtype=float)
    for tr, te in gkf.split(X, y, g):
        pred[te] = GradientBoostingRegressor(
            n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.9,
            random_state=0).fit(X[tr], y[tr]).predict(X[te])
    r = pearsonr(y, pred)[0] if np.std(pred) > 0 else float("nan")
    return float(np.mean(np.abs(pred - y))), float(r)


def clf_cv(X, y, g):
    gkf = GroupKFold(n_splits=max(2, min(5, len(set(g)))))
    pred = np.empty(len(y), dtype=object)
    for tr, te in gkf.split(X, y, g):
        pred[te] = GradientBoostingClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.9,
            random_state=0).fit(X[tr], y[tr]).predict(X[te])
    return float((pred == y).mean()), float(f1_score(y, pred, average="macro"))


def benchmark(emb_df: pd.DataFrame, args) -> None:
    feats = pd.read_parquet(args.features_path)
    feat_cols = sorted(c for c in feats.columns if c not in META)
    df = feats.merge(emb_df.drop(columns=["corpus", "participant_id",
                                          "transcript_id"], errors="ignore"),
                     on="window_id", how="inner")
    agg = {**{c: "mean" for c in feat_cols
              if c in df.columns},
           **{c: "mean" for c in df.columns if any(
               c.startswith(k + "_") for k, _, _ in VARIANTS)},
           **{m: "first" for m in ["subtype", "corpus", "wab_aq"]}}
    pat = df.groupby("participant_id").agg(agg).reset_index()
    print(f"\nbake-off patients: {len(pat)} · corpora: {pat.corpus.nunique()}")

    reps = {"handcrafted": feat_cols}
    for key, _, _ in VARIANTS:
        cols = [c for c in pat.columns if c.startswith(key + "_")]
        if cols:
            reps[key] = cols

    reg = pat.dropna(subset=["wab_aq"]).reset_index(drop=True)
    clf_df = pat.dropna(subset=["subtype"])
    keepc = clf_df["subtype"].value_counts()
    clf_df = clf_df[clf_df["subtype"].isin(keepc[keepc >= 6].index)].reset_index(drop=True)

    print(f"\n{'representation':14s} {'WAB-AQ MAE':>11s} {'r':>7s}   "
          f"{'subtype acc':>11s} {'macroF1':>8s}")
    rows = []
    for name, cols in reps.items():
        out = {"representation": name, "dim": len(cols)}
        if len(reg) >= 30:
            X = StandardScaler().fit_transform(reg[cols].to_numpy(float))
            if name != "handcrafted" and X.shape[1] > args.pca_dim:
                X = PCA(n_components=args.pca_dim, random_state=0).fit_transform(X)
            mae, r = reg_cv(X, reg["wab_aq"].to_numpy(float), reg["corpus"].to_numpy())
            out["wab_mae"], out["wab_r"] = mae, r
        else:
            mae = r = float("nan")
        if len(clf_df) >= 30:
            Xc = StandardScaler().fit_transform(clf_df[cols].to_numpy(float))
            if name != "handcrafted" and Xc.shape[1] > args.pca_dim:
                Xc = PCA(n_components=args.pca_dim, random_state=0).fit_transform(Xc)
            acc, mf1 = clf_cv(Xc, clf_df["subtype"].to_numpy(), clf_df["corpus"].to_numpy())
            out["acc"], out["macro_f1"] = acc, mf1
        else:
            acc = mf1 = float("nan")
        rows.append(out)
        print(f"{name:14s} {mae:>11.2f} {r:>7.3f}   {acc:>11.3f} {mf1:>8.3f}")

    pd.DataFrame(rows).to_csv(args.output_dir / "encoder_bakeoff.csv", index=False)
    print(f"\nsaved {args.output_dir / 'encoder_bakeoff.csv'}")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # extract() resumes from any existing parquet and tops up to
    # --target-sessions; it returns immediately once the target is met.
    emb = extract(args)
    if not len(emb):
        print("no embeddings extracted"); return
    benchmark(emb, args)


if __name__ == "__main__":
    main()
