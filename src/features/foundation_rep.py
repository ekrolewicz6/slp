"""Leap 1 — speech-native foundation-model representations.

Replaces the 55 hand-crafted summary statistics with learned embeddings
from a self-supervised speech model (Wav2Vec2 / HuBERT). The hypothesis
(STRATEGY.md §0, §2): the n≈400 accuracy plateau (#34) is a
*representation* ceiling, and a model that consumed thousands of hours of
raw speech carries signal our summary stats throw away — especially for
the fluent subtypes where text features are blind.

This module is the encoder only. `scripts/extract_foundation_embeddings.py`
runs it over streamed AphasiaBank audio; `scripts/benchmark_representations.py`
tests whether the learned reps beat hand-crafted features on the existing
labels (WAB-AQ, subtype) under the same GroupKFold protocol.

Design notes:
  - Pooling: mean + std over the time axis of a chosen hidden layer.
    Mid layers of wav2vec2/HuBERT carry more phonetic/linguistic content
    than the last layer, so `layer` is configurable (default 8).
  - Long audio is chunked (default 20 s) and pooled per chunk, then
    averaged — keeps memory bounded and avoids the model's positional
    limits.
  - torch/transformers are imported lazily so the rest of the codebase
    (and the in-silico closed loop) runs without them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

TARGET_SR = 16000


@dataclass
class EmbedderConfig:
    model_name: str = "facebook/wav2vec2-base"
    layer: int = 8                # hidden layer to pool (0 = embeddings)
    chunk_seconds: float = 20.0
    device: str | None = None     # None → auto (mps/cuda/cpu)


class FoundationEmbedder:
    """Self-supervised speech encoder → pooled embedding per audio segment."""

    def __init__(self, config: EmbedderConfig | None = None):
        self.config = config or EmbedderConfig()
        self._model = None
        self._processor = None
        self._device = None

    # -- lazy heavy init -------------------------------------------------
    def _ensure_loaded(self):
        if self._model is not None:
            return
        import torch
        from transformers import AutoFeatureExtractor, AutoModel

        dev = self.config.device
        if dev is None:
            if torch.backends.mps.is_available():
                dev = "mps"
            elif torch.cuda.is_available():
                dev = "cuda"
            else:
                dev = "cpu"
        self._device = dev
        self._processor = AutoFeatureExtractor.from_pretrained(self.config.model_name)
        # Prefer safetensors: torch < 2.6 refuses to load pickled .bin
        # checkpoints (CVE-2025-32434). Fall back only if unavailable.
        try:
            self._model = AutoModel.from_pretrained(
                self.config.model_name, output_hidden_states=True,
                use_safetensors=True).to(dev).eval()
        except Exception:
            self._model = AutoModel.from_pretrained(
                self.config.model_name, output_hidden_states=True).to(dev).eval()

    @property
    def device(self) -> str:
        self._ensure_loaded()
        return self._device

    # -- core ------------------------------------------------------------
    def embed_segment(self, wav: np.ndarray, sr: int = TARGET_SR) -> np.ndarray:
        """Mean+std-pooled embedding for one waveform segment.

        Returns a 1-D float32 vector of length 2 * hidden_size.
        """
        self._ensure_loaded()
        import torch

        wav = np.asarray(wav, dtype=np.float32)
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        if sr != TARGET_SR:
            wav = _resample(wav, sr, TARGET_SR)

        chunk = int(self.config.chunk_seconds * TARGET_SR)
        if chunk <= 0:
            chunk = len(wav) or 1
        pooled_chunks = []
        with torch.no_grad():
            for start in range(0, max(1, len(wav)), chunk):
                seg = wav[start:start + chunk]
                if len(seg) < TARGET_SR // 5:   # < 0.2 s — skip slivers
                    continue
                inputs = self._processor(seg, sampling_rate=TARGET_SR,
                                         return_tensors="pt")
                iv = inputs.input_values.to(self._device)
                out = self._model(iv)
                h = out.hidden_states[self.config.layer][0]   # (T, H)
                pooled = torch.cat([h.mean(0), h.std(0)], dim=-1)
                pooled_chunks.append(pooled.float().cpu().numpy())
        if not pooled_chunks:
            # too short to embed — return zeros of the right width
            hidden = self._model.config.hidden_size
            return np.zeros(2 * hidden, dtype=np.float32)
        return np.mean(np.stack(pooled_chunks, axis=0), axis=0).astype(np.float32)

    @property
    def dim(self) -> int:
        self._ensure_loaded()
        return 2 * self._model.config.hidden_size


def _resample(wav: np.ndarray, sr: int, target: int) -> np.ndarray:
    """Lightweight polyphase-free resample via scipy (no torchaudio dep)."""
    if sr == target:
        return wav
    from math import gcd
    from scipy.signal import resample_poly
    g = gcd(sr, target)
    return resample_poly(wav, target // g, sr // g).astype(np.float32)
