"""100-utterance windowing for finer temporal resolution.

The Phase 1 spec calls for segmenting transcripts into ~100-CHI-utterance
windows. We currently aggregate at the file level, which means a 200-utt
session and a 30-utt session contribute one row each — masking within-session
variation and short-session noise.

This module re-extracts features per non-overlapping 100-utt window. Windows
shorter than `min_window_utts` are dropped (rather than padded) to keep
feature distributions comparable across rows.

Output rows have a `window_id` and a `window_index` so windows from the same
transcript can be regrouped for within-session analyses.
"""

from __future__ import annotations

from collections.abc import Iterable

import pylangacq

from src.features.extractors import extract_features


def window_utterances(
    utterances: list,
    *,
    participant: str = "CHI",
    window_size: int = 100,
    min_window_utts: int = 50,
) -> list[list]:
    """Split a transcript's CHI utterances into non-overlapping windows.

    Returns a list of lists of utterance objects. Order is preserved
    (chronological within the original transcript).
    """
    chi = [u for u in utterances if u.participant == participant]
    if len(chi) < min_window_utts:
        return []
    windows: list[list] = []
    for i in range(0, len(chi), window_size):
        chunk = chi[i:i + window_size]
        if len(chunk) >= min_window_utts:
            windows.append(chunk)
    return windows


def extract_windowed_features(
    utterances: Iterable,
    *,
    participant: str = "CHI",
    window_size: int = 100,
    min_window_utts: int = 50,
) -> list[dict]:
    """For one transcript, return one feature dict per qualifying window.

    Each dict carries `window_index` (0-based within transcript) and
    `n_chi_utts_in_window` so the row can be located in a downstream
    sequence model.
    """
    utts = list(utterances)
    windows = window_utterances(
        utts,
        participant=participant,
        window_size=window_size,
        min_window_utts=min_window_utts,
    )
    rows = []
    for w_idx, window in enumerate(windows):
        feats = extract_features(window, participant=participant,
                                 min_utterances=min_window_utts)
        if feats is None:
            continue
        feats["window_index"] = w_idx
        feats["n_chi_utts_in_window"] = len(window)
        rows.append(feats)
    return rows
