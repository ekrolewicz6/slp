"""Trained heads that turn representations into a language-state estimate.

This is the calibrated layer the daily-measurement engine
(`src/app/daily_checkin.py`) was missing — the reason it emitted
`state=None/pending`. Per the Leap-1 verdict (#52), the recipe is
task-specific:

  - SeverityHead : 55 hand-crafted text features → WAB-AQ (0–100).
                   Text features win on severity, and we have 895 labeled
                   patients — the strongest, most data-rich estimator.
  - SubtypeHead  : HuBERT layer-9 speech embedding → subtype probabilities.
                   HuBERT beat hand-crafted on subtype; this operationalizes
                   that finding.

Both heads are self-contained (carry their own scaler/PCA/classes) and
persist via joblib. The "language state" returned to the loop is the
SeverityHead's WAB-AQ estimate on 0–100 — the same scale the simulator and
closed loop already use, so the real estimator is a drop-in for the
in-silico one.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np


@dataclass
class SeverityHead:
    """Hand-crafted text features → WAB-AQ severity (0–100)."""
    model: object
    scaler: object
    feature_names: list[str]
    cv_mae: float = float("nan")
    cv_r: float = float("nan")

    def predict(self, features) -> float:
        """`features`: dict[name->value] or 1-D array aligned to feature_names."""
        if isinstance(features, dict):
            x = np.array([float(features.get(n, 0.0)) for n in self.feature_names],
                         dtype=float)
        else:
            x = np.asarray(features, dtype=float).ravel()
        xs = self.scaler.transform(x.reshape(1, -1))
        return float(np.clip(self.model.predict(xs)[0], 0.0, 100.0))

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: str | Path) -> "SeverityHead":
        return joblib.load(path)


@dataclass
class SubtypeHead:
    """Speech embedding (HuBERT layer-9 mean+std) → subtype probabilities."""
    model: object
    scaler: object
    pca: object
    classes: list[str]
    encoder_name: str
    layer: int
    cv_macro_f1: float = float("nan")

    def _project(self, embedding) -> np.ndarray:
        x = np.asarray(embedding, dtype=float).reshape(1, -1)
        xs = self.scaler.transform(x)
        return self.pca.transform(xs) if self.pca is not None else xs

    def predict_proba(self, embedding) -> dict[str, float]:
        z = self._project(embedding)
        p = self.model.predict_proba(z)[0]
        return {c: float(pr) for c, pr in zip(self.classes, p)}

    def predict(self, embedding) -> str:
        probs = self.predict_proba(embedding)
        return max(probs, key=probs.get)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: str | Path) -> "SubtypeHead":
        return joblib.load(path)
