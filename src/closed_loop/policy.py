"""Box 3 of the closed loop: the adaptive intervention policy.

The policy chooses which therapy activity to deliver each day. Three
implementations model the spectrum from current practice to the target:

  - `FixedPolicy`        — always the guideline-default arm. Models
                           today's one-size-fits-subtype practice.
  - `RandomPolicy`       — uniform micro-randomization. A pure
                           micro-randomized trial (MRT); maximally
                           identifiable but ignores what it learns.
  - `ThompsonBandit`     — context-stratified Gaussian Thompson sampling
                           with a forced-exploration floor. Learns each
                           phenotype's best arm WHILE keeping every arm's
                           assignment probability bounded away from zero,
                           so the logged data stay causally identifiable.

Every policy returns BOTH the chosen arm and the propensity (probability
it would have chosen that arm in that context). The propensity is what
makes the resulting log a valid basis for causal inference (see
`causal.py`). A policy with un-bounded propensities (pure greedy) breaks
identification — `ThompsonBandit(explore_floor=0.0)` demonstrates exactly
that failure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from .simulator import ARMS


class Policy(ABC):
    @abstractmethod
    def select(self, context: dict) -> tuple[str, float]:
        """Return (arm, propensity) for the given context."""

    def update(self, context: dict, arm: str, reward: float) -> None:
        """Default: stateless policies learn nothing."""
        return None


class FixedPolicy(Policy):
    """Always deliver one arm. Models guideline-default practice."""

    def __init__(self, arm: str = "naming"):
        self.arm = arm

    def select(self, context: dict) -> tuple[str, float]:
        return self.arm, 1.0


class RandomPolicy(Policy):
    """Uniform micro-randomization — a pure MRT design."""

    def __init__(self, arms: list[str] = ARMS, seed: int = 0):
        self.arms = arms
        self.rng = np.random.default_rng(seed)

    def select(self, context: dict) -> tuple[str, float]:
        a = self.arms[int(self.rng.integers(len(self.arms)))]
        return a, 1.0 / len(self.arms)


class ThompsonBandit(Policy):
    """Per-context Gaussian Thompson sampling with an exploration floor.

    Posterior per (context_key, arm) is Normal-Normal with known reward
    variance. Each day we either (w.p. `explore_floor`) draw an arm
    uniformly, or (otherwise) Thompson-sample. Propensities are computed
    exactly as the epsilon-uniform mixture plus a Monte-Carlo estimate of
    the Thompson argmax probability — so they are valid importance weights
    AND bounded ≥ explore_floor / K.
    """

    def __init__(self, arms: list[str] = ARMS, context_key: str = "phenotype",
                 explore_floor: float = 0.15, reward_var: float = 1.0,
                 prior_mean: float = 0.5, prior_var: float = 4.0,
                 mc_samples: int = 4000, seed: int = 0):
        self.arms = arms
        self.context_key = context_key
        self.explore_floor = explore_floor
        self.reward_var = reward_var
        self.prior_mean = prior_mean
        self.prior_var = prior_var
        self.mc_samples = mc_samples
        self.rng = np.random.default_rng(seed)
        # per context_key value: arm -> [n, sum] sufficient statistics
        self._stats: dict[str, dict[str, list[float]]] = {}

    def _ctx(self, context: dict) -> str:
        return str(context[self.context_key])

    def _arm_stats(self, ckey: str):
        if ckey not in self._stats:
            self._stats[ckey] = {a: [0.0, 0.0] for a in self.arms}
        return self._stats[ckey]

    def _posterior(self, ckey: str, arm: str) -> tuple[float, float]:
        n, s = self._arm_stats(ckey)[arm]
        xbar = (s / n) if n > 0 else self.prior_mean
        prec = 1.0 / self.prior_var + n / self.reward_var
        post_mean = (self.prior_mean / self.prior_var + n * xbar / self.reward_var) / prec
        return post_mean, 1.0 / prec

    def _propensities(self, ckey: str) -> dict[str, float]:
        """epsilon-uniform mixture + MC Thompson argmax probability."""
        K = len(self.arms)
        means = np.empty(K); vars = np.empty(K)
        for i, a in enumerate(self.arms):
            m, v = self._posterior(ckey, a)
            means[i] = m; vars[i] = v
        draws = self.rng.normal(means, np.sqrt(vars),
                                size=(self.mc_samples, K))
        winners = np.argmax(draws, axis=1)
        p_thompson = np.bincount(winners, minlength=K) / self.mc_samples
        eps = self.explore_floor
        p = eps / K + (1.0 - eps) * p_thompson
        return {a: float(p[i]) for i, a in enumerate(self.arms)}

    def select(self, context: dict) -> tuple[str, float]:
        ckey = self._ctx(context)
        props = self._propensities(ckey)
        arms = list(props.keys())
        p = np.array([props[a] for a in arms], dtype=float)
        p = p / p.sum()
        arm = arms[int(self.rng.choice(len(arms), p=p))]
        return arm, props[arm]

    def update(self, context: dict, arm: str, reward: float) -> None:
        st = self._arm_stats(self._ctx(context))[arm]
        st[0] += 1.0
        st[1] += float(reward)


class GreedyPolicy(ThompsonBandit):
    """Deterministic exploit-only policy — the identifiability anti-pattern.

    Always delivers the current posterior-mean argmax (random tie-break),
    so the assignment propensity collapses toward 1 for one arm and ~0 for
    the rest. That violates positivity: the unchosen arms are never tried,
    their dose-response is un-estimable, and IPW weights blow up. This is
    exactly why a clinically deployed loop must keep a bounded exploration
    floor — see `scripts/simulate_closed_loop.py` section 3.
    """

    def __init__(self, *args, residual: float = 1e-3, **kwargs):
        super().__init__(*args, **kwargs)
        self.residual = residual  # tiny mass so logged propensities stay >0

    def select(self, context: dict) -> tuple[str, float]:
        ckey = self._ctx(context)
        means = [self._posterior(ckey, a)[0] for a in self.arms]
        best = float(max(means))
        winners = [a for a, m in zip(self.arms, means) if m >= best - 1e-9]
        arm = winners[int(self.rng.integers(len(winners)))]
        # propensity ~1 for the (tie-broken) argmax set, residual elsewhere
        prop = (1.0 - self.residual) / len(winners)
        return arm, prop
