"""In-silico patient dynamics with a KNOWN ground-truth dose-response.

This is the validation substrate for the closed loop (STRATEGY.md, Leap 4).
Real patients don't come with a known dose-response — that's the whole
point of the trial. But to validate the *machinery* (policy → trial →
causal estimator) before enrolling anyone, we simulate patients whose
dose-response we control, run the loop, and check whether the causal
estimator recovers what we put in.

Model (deliberately simple, transparent, falsifiable):

  state s_t ∈ [0, 100]  — a language-ability score (higher = better)
  each patient has a phenotype (broca_like, anomic_like, ...) and a
  personal responsiveness multiplier.

  one therapy "arm" (activity) is delivered per day. The next-day change:

    Δs = spontaneous(s_t)
         + EFFECT[phenotype][arm] * responsiveness * headroom(s_t)
         + noise

  headroom(s) = (CEILING - s) / CEILING  →  diminishing returns near ceiling
  spontaneous(s) = small early-recovery drift, also shrinks near ceiling

The EFFECT matrix encodes the clinical reality that *different phenotypes
respond to different activities* — the thing the field cannot currently
quantify per patient. The causal estimator's job is to recover, per
phenotype, which arm's effect is largest.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


ARMS = ["naming", "syntax", "conversation", "script"]
PHENOTYPES = ["broca_like", "anomic_like", "wernicke_like", "conduction_like"]

# Ground-truth daily effect (state points) per (phenotype, arm), BEFORE
# the responsiveness and headroom scaling. Each phenotype has a distinct
# best arm — this is what a per-patient causal estimate must recover.
EFFECT: dict[str, dict[str, float]] = {
    "broca_like":      {"naming": 0.50, "syntax": 1.20, "conversation": 0.70, "script": 0.60},
    "anomic_like":     {"naming": 1.30, "syntax": 0.50, "conversation": 0.80, "script": 0.60},
    "wernicke_like":   {"naming": 0.70, "syntax": 0.40, "conversation": 1.10, "script": 0.50},
    "conduction_like": {"naming": 0.70, "syntax": 0.60, "conversation": 0.60, "script": 1.00},
}

CEILING = 100.0


def true_best_arm(phenotype: str) -> str:
    """The arm with the largest ground-truth effect for a phenotype."""
    eff = EFFECT[phenotype]
    return max(eff, key=eff.get)


def true_best_arm_for(patient: "Patient") -> str:
    """The arm with the largest effect for THIS patient.

    With per-patient effect jitter (see `Simulator.make_cohort`), an
    individual's best activity can differ from their phenotype's — which is
    exactly why the pilot must micro-randomize *within* each patient rather
    than trust the subtype label (cf. experiment #26: categorical labels
    collapse meaningful within-group variation).
    """
    if patient.arm_effect:
        return max(patient.arm_effect, key=patient.arm_effect.get)
    return true_best_arm(patient.phenotype)


@dataclass
class Patient:
    patient_id: str
    phenotype: str
    state: float                       # current language-ability score
    responsiveness: float = 1.0        # personal multiplier on therapy effect
    spontaneous: float = 0.15          # baseline daily drift at floor
    history: list[float] = field(default_factory=list)
    arm_effect: dict = field(default_factory=dict)  # per-patient effect/arm

    def context(self) -> dict:
        """What the policy is allowed to see when choosing an activity."""
        return {"phenotype": self.phenotype, "state": self.state}


class Simulator:
    """Stochastic patient-dynamics environment.

    `step(patient, arm)` applies one day of the given activity and returns
    the realised reward (next-day Δstate). The dose-response encoded in
    EFFECT is the hidden ground truth the causal layer must recover.
    """

    def __init__(self, seed: int = 0, obs_noise: float = 1.0,
                 reward_noise: float = 0.6):
        self.rng = np.random.default_rng(seed)
        self.obs_noise = obs_noise
        self.reward_noise = reward_noise

    def make_cohort(self, n_per_phenotype: int = 5,
                    start_low: float = 25.0, start_high: float = 55.0,
                    ind_effect_sd: float = 0.0) -> list[Patient]:
        """Build a cohort. `ind_effect_sd` > 0 jitters each patient's
        per-arm effect around their phenotype mean, so individuals can have
        a personal best activity that differs from the subtype default."""
        patients: list[Patient] = []
        for ph in PHENOTYPES:
            for i in range(n_per_phenotype):
                s0 = float(self.rng.uniform(start_low, start_high))
                resp = float(np.clip(self.rng.normal(1.0, 0.25), 0.4, 1.8))
                if ind_effect_sd > 0:
                    arm_eff = {a: float(max(0.05, EFFECT[ph][a]
                                            + self.rng.normal(0.0, ind_effect_sd)))
                               for a in ARMS}
                else:
                    arm_eff = {a: EFFECT[ph][a] for a in ARMS}
                p = Patient(patient_id=f"{ph[:4]}{i:02d}", phenotype=ph,
                            state=s0, responsiveness=resp, arm_effect=arm_eff)
                p.history.append(s0)
                patients.append(p)
        return patients

    def headroom(self, s: float) -> float:
        return max(0.0, (CEILING - s) / CEILING)

    def step(self, patient: Patient, arm: str) -> float:
        """Advance one day; mutate patient.state; return realised Δstate."""
        s = patient.state
        hr = self.headroom(s)
        base = patient.spontaneous * hr
        eff = patient.arm_effect.get(arm, EFFECT[patient.phenotype][arm]) \
            if patient.arm_effect else EFFECT[patient.phenotype][arm]
        treat = eff * patient.responsiveness * hr
        noise = float(self.rng.normal(0.0, self.reward_noise))
        delta = base + treat + noise
        new_s = float(np.clip(s + delta, 0.0, CEILING))
        realised = new_s - s
        patient.state = new_s
        patient.history.append(new_s)
        return realised

    def observe(self, patient: Patient) -> float:
        """Noisy measurement of state (stands in for the learned estimator)."""
        return float(patient.state + self.rng.normal(0.0, self.obs_noise))
