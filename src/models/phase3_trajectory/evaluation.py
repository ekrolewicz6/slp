"""Leave-last-out evaluation: predict each child's final session from prior."""

from __future__ import annotations

import numpy as np

from src.models.phase3_trajectory.models import TrajectoryModel
from src.models.phase3_trajectory.sequences import ChildSequence


def evaluate_leave_last_out(
    model: TrajectoryModel,
    sequences: list[ChildSequence],
    *,
    age_predictor=None,  # optional: callable z (1, d) → predicted age (months)
) -> dict[str, float | list]:
    """For each child, fit on first n-1 sessions, predict the n-th in z-space.

    Returns aggregate MAE in z (Euclidean) and per-component MAE. If
    `age_predictor` is provided, also returns MAE in months for predicted z
    vs actual z.
    """
    z_l2_errors = []
    z_per_dim_abs = []
    age_pred_errors = []
    age_actual_errors = []
    rows = []

    for seq in sequences:
        if len(seq.times) < 3:
            continue
        history_t = seq.times[:-1]
        history_Z = seq.Z[:-1]
        target_t = float(seq.times[-1])
        target_z = seq.Z[-1]

        try:
            pred_z = model.predict(history_t, history_Z, target_t)
        except Exception as e:
            rows.append({"child_id": seq.child_id, "corpus": seq.corpus,
                         "n_sessions": len(seq.times),
                         "z_l2_error": float("nan"), "error": str(e)})
            continue

        diff = pred_z - target_z
        z_l2 = float(np.sqrt(np.sum(diff ** 2)))
        z_l2_errors.append(z_l2)
        z_per_dim_abs.append(np.abs(diff))

        row = {
            "child_id": seq.child_id,
            "corpus": seq.corpus,
            "n_sessions": len(seq.times),
            "target_age": target_t,
            "z_l2_error": z_l2,
        }
        if age_predictor is not None:
            pred_age = float(age_predictor(pred_z.reshape(1, -1))[0])
            actual_pred_age = float(age_predictor(target_z.reshape(1, -1))[0])
            row["predicted_age_from_pred_z"] = pred_age
            row["predicted_age_from_actual_z"] = actual_pred_age
            age_pred_errors.append(abs(pred_age - target_t))
            age_actual_errors.append(abs(actual_pred_age - target_t))
        rows.append(row)

    summary: dict = {
        "model": model.name,
        "n_children": len(z_l2_errors),
        "mean_z_l2_error": float(np.mean(z_l2_errors)) if z_l2_errors else float("nan"),
        "median_z_l2_error": float(np.median(z_l2_errors)) if z_l2_errors else float("nan"),
        "rows": rows,
    }
    if z_per_dim_abs:
        per_dim = np.stack(z_per_dim_abs, axis=0).mean(axis=0)
        summary["per_dim_mae"] = per_dim.tolist()
    if age_pred_errors:
        summary["age_mae_from_predicted_z"] = float(np.mean(age_pred_errors))
        summary["age_mae_from_actual_z"] = float(np.mean(age_actual_errors))
    return summary
