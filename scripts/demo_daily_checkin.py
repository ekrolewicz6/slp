"""Demo: one patient's daily check-in, end-to-end on real audio.

Proves the patient-facing measurement engine (Leap 3) + functional-
communication instrument (Leap 2) run together and emit a closed-loop
log row — the exact record the pilot app produces. Uses the local test
wav as the day's speech sample.

Run:  .venv/bin/python -m scripts.demo_daily_checkin
"""

from __future__ import annotations

from dataclasses import asdict

from src.app.daily_checkin import run_daily_checkin
from src.features.foundation_rep import EmbedderConfig, FoundationEmbedder


def main() -> None:
    embedder = FoundationEmbedder(EmbedderConfig(model_name="facebook/wav2vec2-base"))

    # Example responses (0–4 daily; 0–3 weekly difficulty, reverse-coded)
    ema = {"ema_say": 3, "ema_breakdown": 1, "ema_limited": 1}
    weekly = {"cp_phone": 1, "cp_order": 0, "cp_stranger": 2,
              "cp_group": 2, "cp_news": 1, "cp_opinion": 1}

    rec = run_daily_checkin(
        patient_id="pilot01", day=12,
        audio_path="data/audio/cmu01a_test.wav",
        ema_responses=ema, weekly_responses=weekly,
        embedder=embedder)

    print("=== DailyRecord (what leaves the device) ===")
    d = asdict(rec)
    d.pop("embedding", None)   # raw vector kept in memory, not printed/stored
    for k, v in d.items():
        print(f"  {k:22s}: {v}")

    print("\n=== privacy posture ===")
    print(f"  audio_retained        : {rec.audio_retained}  (waveform discarded "
          f"after embedding)")
    print(f"  embedding is pooled    : {rec.embedding_dim}-d, non-invertible "
          f"summary of speech")

    print("\n=== projected closed-loop log row (feeds policy/trial/causal) ===")
    row = rec.to_log_row(arm="syntax", propensity=0.25)
    for k, v in row.items():
        print(f"  {k:20s}: {v}")

    print("\nNOTE: language_state is None / pending — the calibrated state head")
    print("is trained from the representation benchmark; we do not fabricate a")
    print("state estimate we haven't validated. functional_composite is live.")


if __name__ == "__main__":
    main()
