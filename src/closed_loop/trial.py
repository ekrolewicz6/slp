"""Box 3/4 plumbing: run the micro-randomized trial and log every decision.

`run_trial` is the daily loop of the closed-loop system (STRATEGY.md §1):

    for each day, for each patient:
        observe state  (Box 2 — the estimator)
        build context
        select arm + propensity  (Box 3 — the policy)
        deliver arm, observe next-day reward  (the environment / patient)
        update the policy
        LOG (everything needed for causal inference)

The log schema is the contract between the running system and the causal
layer. Each row is one decision with its propensity and realised reward —
exactly what `causal.py` needs to estimate the dose-response. In the real
pilot, the same schema is produced by the app; only the estimator and
environment are swapped for real patients.
"""

from __future__ import annotations

import pandas as pd

from .policy import Policy
from .simulator import Patient, Simulator
from .state import StateEstimator


LOG_COLUMNS = [
    "day", "patient_id", "phenotype", "state_est", "true_state_before",
    "arm", "propensity", "reward", "true_state_after",
]


def run_trial(patients: list[Patient], policy: Policy,
              estimator: StateEstimator, sim: Simulator,
              days: int = 56) -> pd.DataFrame:
    """Run `days` of the closed loop over `patients`. Returns the decision log.

    NOTE: patient state is mutated in place by the simulator, so pass a
    fresh cohort per policy you want to compare.
    """
    rows: list[dict] = []
    for day in range(days):
        for p in patients:
            est = estimator.estimate(p)
            ctx = {"phenotype": p.phenotype, "state": est}
            arm, prop = policy.select(ctx)
            s_before = p.state
            reward = sim.step(p, arm)
            policy.update(ctx, arm, reward)
            rows.append({
                "day": day,
                "patient_id": p.patient_id,
                "phenotype": p.phenotype,
                "state_est": est,
                "true_state_before": s_before,
                "arm": arm,
                "propensity": prop,
                "reward": reward,
                "true_state_after": p.state,
            })
    return pd.DataFrame(rows, columns=LOG_COLUMNS)


def total_recovery(patients: list[Patient]) -> float:
    """Mean state gain from first to last day across the cohort.

    This is the clinical value signal: how much language ability the
    cohort recovered under a given policy.
    """
    gains = [p.history[-1] - p.history[0] for p in patients if p.history]
    return float(sum(gains) / len(gains)) if gains else 0.0
