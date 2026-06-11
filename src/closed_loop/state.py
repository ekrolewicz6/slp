"""Box 2 of the closed loop: the language-state estimator interface.

In production this wraps the foundation-model representation
(`src/features/foundation_rep.py`, Leap 1) → a low-dimensional language
state. The loop is decoupled from *how* state is measured so that the
estimator can be swapped (hand-crafted features → learned reps → fused
multimodal) without touching the policy/trial/causal layers.

Here we provide:
  - `StateEstimator` — the abstract interface
  - `SimStateEstimator` — returns the simulator's (noisy) state, standing
    in for the real estimator during in-silico validation
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .simulator import Patient, Simulator


class StateEstimator(ABC):
    """Maps an observation of a patient to a scalar/low-dim language state.

    Production implementations consume a speech sample → foundation-model
    embedding → calibrated language-ability estimate (and, per Leap 2, a
    functional-communication estimate). The return contract is a float
    state for now; widen to a vector when the multidimensional estimator
    lands.
    """

    @abstractmethod
    def estimate(self, patient: Patient) -> float:
        ...


class SimStateEstimator(StateEstimator):
    """In-silico estimator: a noisy read of the simulator's true state.

    This is the placeholder for the learned estimator. Swapping in the
    real one (foundation_rep → calibrated head) requires only that it also
    implement `estimate`.
    """

    def __init__(self, sim: Simulator):
        self.sim = sim

    def estimate(self, patient: Patient) -> float:
        return self.sim.observe(patient)
