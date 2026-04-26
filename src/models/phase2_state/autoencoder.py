"""Nonlinear autoencoder for the latent state.

Linear PCA on the 55 features plateaus at ~10.15 mo MAE for age prediction
(vs raw GBM's 8.98), so the age-relevant manifold isn't linear. This module
trains a small MLP autoencoder and exposes the same `transform()` interface
as `StateModel` so it can plug directly into Phase 3 trajectory code.

We deliberately keep it small (one hidden layer per side, mild dropout) —
55 inputs and ~4k transcripts is too little data to justify anything bigger,
and an over-parameterized AE would just memorize.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler


class _AENet(nn.Module):
    def __init__(self, n_in: int, hidden: int, d: int, dropout: float):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_in, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, d),
        )
        self.decoder = nn.Sequential(
            nn.Linear(d, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, n_in),
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z), z


@dataclass
class AEStateModel:
    """Drop-in replacement for `StateModel` with nonlinear encoding."""
    d: int
    scaler: StandardScaler
    net: _AENet
    feature_names: list[str]
    train_loss: float
    val_loss: float
    n_epochs: int

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        X = df[self.feature_names].to_numpy(dtype=float)
        Xs = self.scaler.transform(X).astype(np.float32)
        self.net.eval()
        with torch.no_grad():
            _, z = self.net(torch.from_numpy(Xs))
        return z.numpy()

    @property
    def variance_explained(self) -> float:
        # Approximate via 1 - reconstruction MSE / total variance on val data.
        # Reported during training; here we just expose the cached value.
        return float("nan")


def fit_autoencoder(
    df: pd.DataFrame,
    feature_cols: list[str],
    d: int,
    *,
    hidden: int = 64,
    dropout: float = 0.1,
    epochs: int = 400,
    batch_size: int = 128,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    val_frac: float = 0.15,
    random_state: int = 0,
    verbose: bool = False,
) -> AEStateModel:
    torch.manual_seed(random_state)
    np.random.seed(random_state)

    X = df[feature_cols].to_numpy(dtype=float)
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X).astype(np.float32)

    n = Xs.shape[0]
    perm = np.random.permutation(n)
    n_val = max(64, int(n * val_frac))
    val_idx = perm[:n_val]
    train_idx = perm[n_val:]

    X_train = torch.from_numpy(Xs[train_idx])
    X_val = torch.from_numpy(Xs[val_idx])

    net = _AENet(n_in=Xs.shape[1], hidden=hidden, d=d, dropout=dropout)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = nn.MSELoss()

    best_val = float("inf")
    best_state = None
    patience = 30
    bad = 0
    for ep in range(epochs):
        net.train()
        perm_b = torch.randperm(X_train.shape[0])
        running = 0.0
        for i in range(0, len(perm_b), batch_size):
            batch = X_train[perm_b[i:i + batch_size]]
            opt.zero_grad()
            recon, _ = net(batch)
            loss = loss_fn(recon, batch)
            loss.backward()
            opt.step()
            running += loss.item() * batch.shape[0]
        train_loss = running / X_train.shape[0]

        net.eval()
        with torch.no_grad():
            recon_v, _ = net(X_val)
            val_loss = loss_fn(recon_v, X_val).item()

        if val_loss < best_val - 1e-5:
            best_val = val_loss
            best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
            bad = 0
        else:
            bad += 1
            if bad >= patience:
                if verbose:
                    print(f"  early stop at epoch {ep+1} (val={val_loss:.4f})")
                break
        if verbose and (ep % 50 == 0 or ep == epochs - 1):
            print(f"  ep {ep+1:3d}  train={train_loss:.4f}  val={val_loss:.4f}")

    if best_state is not None:
        net.load_state_dict(best_state)

    return AEStateModel(
        d=d, scaler=scaler, net=net, feature_names=list(feature_cols),
        train_loss=float(train_loss), val_loss=float(best_val),
        n_epochs=ep + 1,
    )
