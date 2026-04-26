"""Acoustic / prosodic feature extraction for AphasiaBank PAR utterances.

Per-utterance features (extracted from a single `parselmouth.Sound`):
  - Pitch (f0): mean, std, p10, p90, range, voiced-fraction, slope
  - Voice quality: jitter (local), shimmer (local), HNR mean
  - Intensity: mean, std
  - Timing: utterance duration, speech rate (tokens / duration)

Aggregated per 100-PAR-utterance window: mean and std of each per-utt
feature. So the output column count is roughly 2× the per-utt count.

Why these specifically: Wernicke aphasia is structurally fluent but
*prosodically* abnormal — flat pitch contour, atypical rhythm, voice-
quality changes are the discriminating dimensions our text-only features
miss. Broca aphasia produces non-fluent halting speech; speech rate and
pause distribution catch this.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import parselmouth
    from parselmouth import praat
    HAS_PARSELMOUTH = True
except ImportError:
    HAS_PARSELMOUTH = False


PITCH_FLOOR = 75.0       # Hz; standard Praat default for adults
PITCH_CEILING = 500.0    # Hz; covers female + emphatic male
F0_QUANTILES = (0.10, 0.50, 0.90)


def _safe(x, default=float("nan")) -> float:
    try:
        v = float(x)
        return v if np.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def utterance_features(sound: "parselmouth.Sound", n_tokens: int) -> dict:
    """Per-utterance acoustic feature dict.

    `sound` is a parselmouth Sound containing only this utterance's audio.
    `n_tokens` is the word count for speech-rate computation. Returns a
    dict with NaN values when extraction fails (e.g., utterance too short
    for pitch tracking).
    """
    duration = float(sound.duration)
    out = {
        "ac_duration_s": duration,
        "ac_n_tokens": float(n_tokens),
        "ac_speech_rate": (n_tokens / duration) if duration > 0 else float("nan"),
    }

    # Pitch.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pitch = sound.to_pitch(time_step=0.01,
                                    pitch_floor=PITCH_FLOOR,
                                    pitch_ceiling=PITCH_CEILING)
        f0 = pitch.selected_array["frequency"]
        voiced = f0[f0 > 0]
        if voiced.size > 5:
            out.update({
                "ac_f0_mean": _safe(np.mean(voiced)),
                "ac_f0_std": _safe(np.std(voiced)),
                "ac_f0_p10": _safe(np.quantile(voiced, 0.10)),
                "ac_f0_p50": _safe(np.quantile(voiced, 0.50)),
                "ac_f0_p90": _safe(np.quantile(voiced, 0.90)),
                "ac_f0_range": _safe(np.quantile(voiced, 0.90)
                                     - np.quantile(voiced, 0.10)),
                "ac_f0_cv": _safe(np.std(voiced) / max(np.mean(voiced), 1e-6)),
                "ac_voiced_fraction": _safe(voiced.size / f0.size),
            })
        else:
            out.update({k: float("nan") for k in [
                "ac_f0_mean", "ac_f0_std", "ac_f0_p10", "ac_f0_p50",
                "ac_f0_p90", "ac_f0_range", "ac_f0_cv", "ac_voiced_fraction",
            ]})
    except Exception:
        out.update({k: float("nan") for k in [
            "ac_f0_mean", "ac_f0_std", "ac_f0_p10", "ac_f0_p50",
            "ac_f0_p90", "ac_f0_range", "ac_f0_cv", "ac_voiced_fraction",
        ]})

    # Voice quality (jitter, shimmer, HNR).
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            point_process = praat.call(
                sound, "To PointProcess (periodic, cc)",
                PITCH_FLOOR, PITCH_CEILING)
            jitter = praat.call(point_process,
                                "Get jitter (local)",
                                0, 0, 0.0001, 0.02, 1.3)
            shimmer = praat.call([sound, point_process],
                                  "Get shimmer (local)",
                                  0, 0, 0.0001, 0.02, 1.3, 1.6)
        out["ac_jitter_local"] = _safe(jitter)
        out["ac_shimmer_local"] = _safe(shimmer)
    except Exception:
        out["ac_jitter_local"] = float("nan")
        out["ac_shimmer_local"] = float("nan")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            harmonicity = praat.call(sound, "To Harmonicity (cc)",
                                      0.01, PITCH_FLOOR, 0.1, 1.0)
            hnr_mean = praat.call(harmonicity, "Get mean", 0, 0)
        out["ac_hnr_mean"] = _safe(hnr_mean)
    except Exception:
        out["ac_hnr_mean"] = float("nan")

    # Intensity.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            intensity = sound.to_intensity()
        intensity_vals = intensity.values[0]
        intensity_vals = intensity_vals[np.isfinite(intensity_vals)]
        if intensity_vals.size > 5:
            out["ac_intensity_mean"] = _safe(np.mean(intensity_vals))
            out["ac_intensity_std"] = _safe(np.std(intensity_vals))
        else:
            out["ac_intensity_mean"] = float("nan")
            out["ac_intensity_std"] = float("nan")
    except Exception:
        out["ac_intensity_mean"] = float("nan")
        out["ac_intensity_std"] = float("nan")

    return out


def _slice_sound(full: "parselmouth.Sound",
                 start_s: float, end_s: float) -> "parselmouth.Sound":
    """Extract a time slice from a parselmouth Sound. Returns None if invalid."""
    if end_s <= start_s or start_s < 0 or end_s > full.duration:
        return None
    try:
        return full.extract_part(from_time=start_s, to_time=end_s,
                                  preserve_times=False)
    except Exception:
        return None


def aggregate_window_features(per_utt: list[dict]) -> dict:
    """Mean + std of each numeric per-utt feature across the window.

    Each output column is named like `<feat>_mean` or `<feat>_std`. NaN
    is propagated by taking finite-only means.
    """
    if not per_utt:
        return {}
    keys = [k for k in per_utt[0].keys() if k.startswith("ac_")]
    out = {}
    for k in keys:
        vals = np.array([u.get(k, float("nan")) for u in per_utt],
                        dtype=float)
        finite = vals[np.isfinite(vals)]
        if finite.size == 0:
            out[f"{k}_mean"] = float("nan")
            out[f"{k}_std"] = float("nan")
        else:
            out[f"{k}_mean"] = float(np.mean(finite))
            out[f"{k}_std"] = float(np.std(finite)) if finite.size > 1 else 0.0
    out["ac_n_utts_in_window"] = float(len(per_utt))
    out["ac_n_voiced_utts"] = float(
        sum(1 for u in per_utt
            if np.isfinite(u.get("ac_f0_mean", float("nan")))))
    return out
