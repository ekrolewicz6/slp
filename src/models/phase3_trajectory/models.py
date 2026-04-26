"""Trajectory models: predict z_T given a child's prior (t, z) sessions.

Three models, increasing in flexibility:

- `MeanBaseline`        — predict z_T = mean of past z's (no time, no trend).
- `LinearExtrapolation` — per-dim least-squares line; extrapolate at t_T.
- `GPTrajectory`        — per-dim Gaussian Process; smooth interpolation +
                          extrapolation with calibrated uncertainty.

Each `.predict(history_t, history_Z, t_query)` returns a vector ẑ of shape (d,).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel


class TrajectoryModel:
    name: str

    def predict(self, history_t: np.ndarray, history_Z: np.ndarray,
                t_query: float) -> np.ndarray:
        raise NotImplementedError


@dataclass
class MeanBaseline(TrajectoryModel):
    name: str = "mean"

    def predict(self, history_t: np.ndarray, history_Z: np.ndarray,
                t_query: float) -> np.ndarray:
        return history_Z.mean(axis=0)


@dataclass
class LinearExtrapolation(TrajectoryModel):
    name: str = "linear"

    def predict(self, history_t: np.ndarray, history_Z: np.ndarray,
                t_query: float) -> np.ndarray:
        # Fit z_d(t) = a_d * t + b_d per dimension.
        d = history_Z.shape[1]
        out = np.empty(d, dtype=float)
        # Use polyfit-degree-1; cheaper than np.linalg.lstsq for this size.
        for j in range(d):
            a, b = np.polyfit(history_t, history_Z[:, j], deg=1)
            out[j] = a * t_query + b
        return out


@dataclass
class GPTrajectory(TrajectoryModel):
    name: str = "gp"
    length_scale_init: float = 6.0      # months
    noise_level_init: float = 0.5
    n_restarts: int = 2

    def predict(self, history_t: np.ndarray, history_Z: np.ndarray,
                t_query: float) -> np.ndarray:
        d = history_Z.shape[1]
        out = np.empty(d, dtype=float)
        T = history_t.reshape(-1, 1)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for j in range(d):
                kernel = (ConstantKernel(1.0, (1e-2, 1e3))
                          * RBF(length_scale=self.length_scale_init,
                                length_scale_bounds=(0.5, 60.0))
                          + WhiteKernel(noise_level=self.noise_level_init,
                                        noise_level_bounds=(1e-4, 5.0)))
                gp = GaussianProcessRegressor(
                    kernel=kernel,
                    n_restarts_optimizer=self.n_restarts,
                    normalize_y=True,
                    random_state=0,
                )
                gp.fit(T, history_Z[:, j])
                out[j] = gp.predict(np.array([[t_query]]))[0]
        return out
