"""Closed-loop adaptive-dosing system (STRATEGY.md, Leap 4).

The in-silico implementation of the target architecture:

    measure (state) → choose activity (policy) → deliver + observe (trial)
        → estimate dose-response (causal) → repeat

Run `scripts/simulate_closed_loop.py` to drive the whole loop end-to-end
on simulated patients and check that the causal layer recovers a known
per-phenotype dose-response. The same policy/trial/causal layers run the
real pilot; only `state.py` (estimator) and `simulator.py` (environment)
are swapped for real patients.
"""

from .simulator import (ARMS, CEILING, EFFECT, PHENOTYPES, Patient, Simulator,
                        true_best_arm)
from .state import SimStateEstimator, StateEstimator
from .policy import (FixedPolicy, GreedyPolicy, Policy, RandomPolicy,
                     ThompsonBandit)
from .trial import LOG_COLUMNS, run_trial, total_recovery
from .causal import (estimate_dose_response, evaluate_recovery,
                     recovered_best_arms)

__all__ = [
    "ARMS", "CEILING", "EFFECT", "PHENOTYPES", "Patient", "Simulator",
    "true_best_arm", "SimStateEstimator", "StateEstimator", "FixedPolicy",
    "GreedyPolicy", "Policy", "RandomPolicy", "ThompsonBandit",
    "LOG_COLUMNS", "run_trial",
    "total_recovery", "estimate_dose_response", "evaluate_recovery",
    "recovered_best_arms",
]
