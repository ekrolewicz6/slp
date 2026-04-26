"""Phase 2 visualizations: 2D latent projection + scree + dim-vs-MAE sweep."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def projection_2d(Z: np.ndarray, ages: np.ndarray, out_path: Path,
                  title: str) -> None:
    """Scatter Z[:, :2] colored by age."""
    fig, ax = plt.subplots(figsize=(7, 6))
    sc = ax.scatter(Z[:, 0], Z[:, 1], c=ages, cmap="viridis", s=14, alpha=0.7)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Age (months)")
    ax.set_xlabel("z₁")
    ax.set_ylabel("z₂")
    ax.set_title(title)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def scree(variance_ratios: np.ndarray, out_path: Path, title: str) -> None:
    cum = np.cumsum(variance_ratios)
    ks = np.arange(1, len(variance_ratios) + 1)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(ks, variance_ratios, alpha=0.7, label="per-component")
    ax.plot(ks, cum, "k.-", label="cumulative")
    ax.axhline(0.9, color="r", lw=0.8, ls="--", label="0.90")
    ax.set_xlabel("Component")
    ax.set_ylabel("Variance explained")
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def dim_sweep(metrics: pd.DataFrame, baseline_mae: float, out_path: Path,
              title: str) -> None:
    """metrics: columns ['d', 'mae_months']. Plot MAE vs d, with raw-X baseline."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(metrics["d"], metrics["mae_months"], "o-", label="GBM(z)")
    ax.axhline(baseline_mae, color="k", ls="--", lw=1,
               label=f"GBM(raw 55-feature) = {baseline_mae:.2f}")
    ax.set_xlabel("Latent dimension d")
    ax.set_ylabel("MAE (months)")
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
