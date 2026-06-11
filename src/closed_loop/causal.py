"""Box 4 — the lever: estimate the dose-response from the decision log.

This is the part observational AphasiaBank can never give us. Because the
trial randomized the activity each day with a KNOWN, bounded propensity
(see `policy.py`), the log supports causal estimation of each activity's
effect, per phenotype — the per-patient dosing answer the field lacks.

Two estimators, both reported:

  - stratified mean   — within a phenotype, the mean (state-adjusted)
                        reward by arm. Unbiased under sequential
                        randomization with bounded propensities, because
                        assignment depends only on context + past data,
                        never on the current potential outcome.
  - Hájek IPW         — inverse-propensity-weighted counterfactual mean
                        E[Y(a)] over the stratum. Same target, corrects
                        for the adaptive (non-uniform) assignment.

State-adjustment: the realised reward is Δstate, which scales with
"headroom" (room left below the ceiling). Better arms drive faster
recovery → lower headroom later → smaller raw daily gains, a genuine
time-varying confound. We divide reward by headroom (from the *estimated*
state, i.e. what the running system actually sees) to recover the
arm effect per unit headroom, which is what ranks the arms.

Identifiability check: any (phenotype, arm) cell with fewer than
`min_cell` samples is flagged `identified=False`. A greedy policy with no
exploration floor starves some cells → the dose-response there is
un-estimable. That is the concrete reason the design MUST micro-randomize.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .simulator import ARMS, CEILING, PHENOTYPES, true_best_arm


def estimate_dose_response(logs: pd.DataFrame, headroom_floor: float = 0.05,
                           min_cell: int = 5) -> pd.DataFrame:
    """Per (phenotype, arm) causal effect estimates from the trial log."""
    df = logs.copy()
    headroom = np.clip((CEILING - df["state_est"]) / CEILING, headroom_floor, 1.0)
    df["adj_reward"] = df["reward"] / headroom

    rows = []
    for ph in PHENOTYPES:
        stratum = df[df["phenotype"] == ph]
        n_stratum = len(stratum)
        for arm in ARMS:
            cell = stratum[stratum["arm"] == arm]
            n = len(cell)
            strat_mean = float(cell["adj_reward"].mean()) if n > 0 else np.nan
            if n_stratum > 0 and n > 0:
                w = 1.0 / cell["propensity"].to_numpy()
                ipw_mean = float((w * cell["adj_reward"].to_numpy()).sum() / w.sum())
            else:
                ipw_mean = np.nan
            rows.append({
                "phenotype": ph, "arm": arm, "n": n,
                "strat_mean": strat_mean, "ipw_mean": ipw_mean,
                "identified": n >= min_cell,
            })
    return pd.DataFrame(rows)


def recovered_best_arms(estimates: pd.DataFrame,
                        method: str = "ipw_mean") -> dict[str, str | None]:
    """Best arm per phenotype by the chosen estimator (None if unidentified)."""
    out: dict[str, str | None] = {}
    for ph in PHENOTYPES:
        sub = estimates[(estimates["phenotype"] == ph) & estimates["identified"]]
        if sub.empty or sub[method].isna().all():
            out[ph] = None
        else:
            out[ph] = str(sub.loc[sub[method].idxmax(), "arm"])
    return out


def evaluate_recovery(estimates: pd.DataFrame,
                      method: str = "ipw_mean") -> pd.DataFrame:
    """Compare recovered best arm to the simulator's ground truth."""
    rec = recovered_best_arms(estimates, method=method)
    rows = []
    for ph in PHENOTYPES:
        truth = true_best_arm(ph)
        got = rec[ph]
        rows.append({
            "phenotype": ph, "true_best_arm": truth,
            "recovered_best_arm": got,
            "correct": (got == truth),
            "identified_cells": int(
                estimates[(estimates.phenotype == ph) & estimates.identified].shape[0]),
            "total_cells": len(ARMS),
        })
    return pd.DataFrame(rows)
