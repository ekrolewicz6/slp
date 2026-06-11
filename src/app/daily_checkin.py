"""Leap 3 — the daily-measurement engine (the app's inference core).

One patient, one day: a short speech sample + a 3-item EMA become a
structured record that feeds the closed loop. This is the patient-facing
half of the loop (measure), decoupled from the policy/trial/causal half so
the same record schema flows from this engine in the pilot exactly as it
flows from the simulator in validation.

Pipeline per check-in:
    speech sample (wav)  ──► foundation-model embedding (on device)
                              └─► [trained state head] ─► language state 0–100
    EMA + weekly items   ──► functional-communication score 0–100
    → DailyRecord (embedding summary, state, functional score, metadata)

PRIVACY POSTURE (non-negotiable, STRATEGY.md §6):
  - The waveform is embedded and then DISCARDED. This engine never writes
    or returns raw audio; only the (non-invertible) pooled embedding and
    the scores are retained.
  - Embedding + scores are the minimal data needed for the loop.
  - In production this runs on-device / at the edge; nothing leaves the
    phone except the de-identified record the patient consents to share.

The language-state head is pluggable: pass `state_head` (embedding ->
0–100). Until it's trained from the representation benchmark, the record
carries the embedding and a `state_pending` flag rather than a fabricated
number — we do not invent a state estimate we haven't validated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from src.outcomes.functional_communication import (composite_fco,
                                                   score_daily_ema,
                                                   score_weekly_participation)


@dataclass
class DailyRecord:
    patient_id: str
    day: int
    language_state: float | None       # 0–100, None until a trained head exists
    state_pending: bool
    functional_daily: float            # 0–100
    functional_weekly: float | None    # 0–100
    functional_composite: float        # 0–100
    embedding_dim: int
    embedding_norm: float              # summary only; raw embedding kept in-memory
    audio_retained: bool = False       # always False — audio is discarded
    embedding: np.ndarray | None = field(default=None, repr=False)

    def to_log_row(self, arm: str, propensity: float,
                   reward: float | None = None) -> dict:
        """Project into the closed-loop decision-log schema (trial.py)."""
        return {
            "day": self.day,
            "patient_id": self.patient_id,
            "phenotype": "",                       # filled from enrolment metadata
            "state_est": self.language_state if self.language_state is not None
            else self.functional_composite,        # fallback signal pre-head
            "true_state_before": None,
            "arm": arm,
            "propensity": propensity,
            "reward": reward,
            "true_state_after": None,
        }


def run_daily_checkin(patient_id: str, day: int,
                      audio_path: str | Path | None,
                      ema_responses: dict[str, int],
                      weekly_responses: dict[str, int] | None = None,
                      embedder=None,
                      state_head: Callable[[np.ndarray], float] | None = None
                      ) -> DailyRecord:
    """Run one daily check-in and return a privacy-preserving DailyRecord.

    `embedder` is a FoundationEmbedder (lazy-loaded). If `audio_path` is
    None (EMA-only day), the embedding is skipped.
    """
    emb_vec = None
    emb_dim = 0
    emb_norm = float("nan")
    if audio_path is not None and embedder is not None:
        import soundfile as sf
        wav, sr = sf.read(str(audio_path))
        emb_vec = embedder.embed_segment(np.asarray(wav, dtype=np.float32), sr)
        # audio (`wav`) goes out of scope here and is never persisted.
        emb_dim = int(emb_vec.shape[0])
        emb_norm = float(np.linalg.norm(emb_vec))

    daily = score_daily_ema(ema_responses)
    weekly = (score_weekly_participation(weekly_responses)
              if weekly_responses else None)
    composite = composite_fco(daily, weekly)

    state = None
    pending = True
    if state_head is not None and emb_vec is not None:
        state = float(np.clip(state_head(emb_vec), 0.0, 100.0))
        pending = False

    return DailyRecord(
        patient_id=patient_id, day=day, language_state=state,
        state_pending=pending, functional_daily=daily,
        functional_weekly=weekly, functional_composite=composite,
        embedding_dim=emb_dim, embedding_norm=emb_norm,
        audio_retained=False, embedding=emb_vec)
