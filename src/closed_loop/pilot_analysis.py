"""Per-patient dose-response analysis — the pilot's primary endpoint.

The 8-week pilot's scientific claim is NOT a group p-value. It is a
*personalized* causal estimate: for each individual patient, which therapy
activity most improves their language state, and how confident are we.
This module turns a decision log (the schema produced by `trial.py` and,
in the real study, by the app) into exactly that.

For each patient and arm we estimate the state-adjusted effect (reward per
unit headroom — see `causal.py` for why) with a bootstrap confidence
interval over the patient's own decision-days. A patient's best activity
is "identified" when the top arm's effect CI is separated from the
runner-up's by a clinically meaningful margin.

This is the estimator the power simulation (`scripts/pilot_power.py`)
stress-tests, and the one the real pilot will run on real logs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .simulator import CEILING


def _adjusted(log: pd.DataFrame, headroom_floor: float) -> pd.DataFrame:
    df = log.copy()
    hr = np.clip((CEILING - df["state_est"]) / CEILING, headroom_floor, 1.0)
    df["adj_reward"] = df["reward"] / hr
    return df


def per_patient_dose_response(log: pd.DataFrame, headroom_floor: float = 0.05,
                              min_cell: int = 3, n_boot: int = 2000,
                              seed: int = 0, pool: bool = False,
                              pool_k: float = 8.0) -> pd.DataFrame:
    """Per (patient, arm) effect estimate with a bootstrap 90% CI.

    Returns one row per (patient_id, arm) with: n, effect (mean adjusted
    reward), ci_lo, ci_hi, identified (n >= min_cell).

    `pool=True` enables empirical-Bayes PARTIAL POOLING: each patient's
    per-arm effect is shrunk toward that arm's phenotype-level mean by
    weight n/(n+pool_k). This borrows strength across patients of the same
    phenotype — the principled small-sample fix that makes per-patient
    estimates usable at pilot scale. Requires a `phenotype` column.
    """
    rng = np.random.default_rng(seed)
    df = _adjusted(log, headroom_floor)

    prior = {}
    if pool:
        if "phenotype" not in df.columns:
            raise ValueError("pool=True requires a 'phenotype' column in the log")
        # arm effect prior = phenotype-level mean of adjusted reward
        prior = (df.groupby(["phenotype", "arm"])["adj_reward"].mean().to_dict())
        pheno_of = df.drop_duplicates("patient_id").set_index(
            "patient_id")["phenotype"].to_dict()

    rows = []
    for pid, pdf in df.groupby("patient_id"):
        for arm, adf in pdf.groupby("arm"):
            vals = adf["adj_reward"].to_numpy()
            n = len(vals)
            if n == 0:
                continue
            eff = float(vals.mean())
            if n >= 2:
                boot = rng.choice(vals, size=(n_boot, n), replace=True).mean(axis=1)
            else:
                boot = np.full(n_boot, eff)
            if pool:
                M = prior.get((pheno_of.get(pid), arm), eff)
                w = n / (n + pool_k)
                eff = w * eff + (1 - w) * M
                boot = w * boot + (1 - w) * M
            lo, hi = np.percentile(boot, [5, 95])
            rows.append({"patient_id": pid, "arm": arm, "n": n,
                         "effect": eff, "ci_lo": float(lo), "ci_hi": float(hi),
                         "identified": n >= min_cell})
    return pd.DataFrame(rows)


def patient_best_arms(estimates: pd.DataFrame,
                      margin: float = 0.0) -> pd.DataFrame:
    """Per patient: recovered best arm + whether it's separated from #2.

    `separated` is True when the best arm's CI lower bound exceeds the
    runner-up's effect by `margin` — i.e. the pilot has enough evidence to
    recommend that activity for that patient with confidence.
    """
    rows = []
    for pid, pdf in estimates.groupby("patient_id"):
        usable = pdf[pdf["identified"]]
        if usable.empty:
            rows.append({"patient_id": pid, "best_arm": None,
                         "separated": False, "n_arms_identified": 0})
            continue
        usable = usable.sort_values("effect", ascending=False).reset_index(drop=True)
        best = usable.iloc[0]
        runner_eff = float(usable.iloc[1]["effect"]) if len(usable) > 1 else -np.inf
        separated = bool(best["ci_lo"] > runner_eff + margin)
        rows.append({"patient_id": pid, "best_arm": str(best["arm"]),
                     "separated": separated,
                     "n_arms_identified": int(usable.shape[0])})
    return pd.DataFrame(rows)


def evaluate_against_truth(best_arms: pd.DataFrame,
                           truth: dict[str, str]) -> dict:
    """Compare recovered per-patient best arms to ground truth (sim only)."""
    merged = best_arms.copy()
    merged["true_best"] = merged["patient_id"].map(truth)
    merged["correct"] = merged["best_arm"] == merged["true_best"]
    # among patients where we *claimed* confident separation, how often right
    conf = merged[merged["separated"]]
    return {
        "n_patients": int(len(merged)),
        "recovered_correct": float(merged["correct"].mean()),
        "n_confident": int(len(conf)),
        "confident_precision": float(conf["correct"].mean()) if len(conf) else float("nan"),
    }
