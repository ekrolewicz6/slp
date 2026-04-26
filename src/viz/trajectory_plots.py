"""Phase 3 trajectory visualizations."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.models.phase3_trajectory.sequences import ChildSequence


def trajectories_in_z(sequences: list[ChildSequence], out_path: Path,
                      title: str, max_children: int = 12) -> None:
    """Plot z₁ over time for the most-sampled children."""
    seqs = sorted(sequences, key=lambda s: -len(s.times))[:max_children]
    fig, ax = plt.subplots(figsize=(8, 5))
    cmap = plt.get_cmap("tab20")
    for i, s in enumerate(seqs):
        ax.plot(s.times, s.Z[:, 0], "-", color=cmap(i % 20), alpha=0.5,
                label=f"{s.corpus}/{s.child_id}", lw=1)
        ax.scatter(s.times, s.Z[:, 0], color=cmap(i % 20), s=10, alpha=0.7)
    ax.set_xlabel("Age (months)")
    ax.set_ylabel("z₁")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=7, ncol=2, framealpha=0.85)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def predicted_vs_actual_age(rows: list[dict], out_path: Path,
                            title: str) -> None:
    """For the GP/linear predictions: x = actual final age, y = age inferred
    from the predicted z (via the Phase 1 age model). y = x means trajectory
    + state model jointly recover the right developmental position."""
    have = [r for r in rows if "predicted_age_from_pred_z" in r]
    if not have:
        return
    actual = np.array([r["target_age"] for r in have])
    pred = np.array([r["predicted_age_from_pred_z"] for r in have])
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(actual, pred, alpha=0.6, s=18)
    lo = float(min(actual.min(), pred.min()))
    hi = float(max(actual.max(), pred.max()))
    ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="y = x")
    ax.set_xlabel("Actual age at held-out session (months)")
    ax.set_ylabel("Age inferred from predicted z (months)")
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
