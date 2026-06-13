"""Demo: one patient's daily check-in with REAL trained heads.

Proves the full measurement engine: the daily check-in now emits a real
subtype posterior (HuBERT → subtype head) from the audio and a real
language-state estimate (text features → severity head), not placeholders.

Loads the heads trained by `scripts/train_state_heads.py`. Uses the local
test wav as the day's speech sample and a real labeled patient's text
features for the severity estimate.

Run:  .venv/bin/python -m scripts.demo_daily_checkin
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from src.app.daily_checkin import run_daily_checkin
from src.features.foundation_rep import EmbedderConfig, FoundationEmbedder
from src.models.heads import SeverityHead, SubtypeHead

MODEL_DIR = Path("data/models")


def main() -> None:
    sev = SeverityHead.load(MODEL_DIR / "severity_head.joblib") \
        if (MODEL_DIR / "severity_head.joblib").exists() else None
    sub = SubtypeHead.load(MODEL_DIR / "subtype_head.joblib") \
        if (MODEL_DIR / "subtype_head.joblib").exists() else None
    if sev is None or sub is None:
        print("Heads not found — run scripts/train_state_heads.py first.")
        return
    print(f"loaded heads · severity CV r={sev.cv_r:+.3f} MAE={sev.cv_mae:.1f} · "
          f"subtype CV macro-F1={sub.cv_macro_f1:.3f} ({sub.encoder_name} L{sub.layer})")

    # Use the SAME encoder the subtype head was trained on (HuBERT).
    embedder = FoundationEmbedder(EmbedderConfig(model_name=sub.encoder_name,
                                                 layer=sub.layer))

    # A real labeled patient near the median WAB-AQ → severity head input
    # (representative rather than a floor/ceiling tail case).
    feats = pd.read_parquet("data/features/aphasiabank_windowed_features.parquet")
    labeled = feats.dropna(subset=["wab_aq"]).drop_duplicates("participant_id")
    med = labeled["wab_aq"].median()
    one = labeled.iloc[(labeled["wab_aq"] - med).abs().argmin()]["participant_id"]
    prow = feats[feats.participant_id == one]
    text_features = {n: float(prow[n].mean()) for n in sev.feature_names
                     if n in prow.columns}
    true_aq = float(prow["wab_aq"].iloc[0])
    true_sub = prow["subtype"].iloc[0]

    ema = {"ema_say": 3, "ema_breakdown": 1, "ema_limited": 1}
    weekly = {"cp_phone": 1, "cp_order": 0, "cp_stranger": 2,
              "cp_group": 2, "cp_news": 1, "cp_opinion": 1}

    rec = run_daily_checkin(
        patient_id=str(one), day=12, audio_path="data/audio/cmu01a_test.wav",
        ema_responses=ema, weekly_responses=weekly, embedder=embedder,
        subtype_head=sub, severity_head=sev, text_features=text_features)

    print("\n=== DailyRecord (real estimates) ===")
    d = asdict(rec); d.pop("embedding", None); d.pop("subtype_probs", None)
    for k, v in d.items():
        print(f"  {k:22s}: {v}")
    print("  subtype_probs        :")
    for c, p in sorted((rec.subtype_probs or {}).items(), key=lambda x: -x[1]):
        print(f"      {c:12s} {p:.2f}")

    print("\n=== sanity vs ground truth (note: audio is a different patient's "
          "sample than the text features — demo only) ===")
    print(f"  severity estimate    : {rec.language_state:.1f}  "
          f"(this patient's true WAB-AQ: {true_aq:.1f})")
    print(f"  subtype (from audio) : {rec.subtype_pred}  "
          f"(text-patient's true subtype: {true_sub})")
    print(f"  functional composite : {rec.functional_composite:.1f}")
    print(f"  audio_retained       : {rec.audio_retained}  (waveform discarded)")
    print("\nThe engine now emits real estimates. state_pending is False.")


if __name__ == "__main__":
    main()
