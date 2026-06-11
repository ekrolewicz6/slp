"""End-to-end in-silico run of the closed-loop adaptive-dosing system.

Drives the whole architecture (STRATEGY.md §1) on simulated patients and
checks two things the pilot will need to be true:

  1. CLINICAL VALUE — the adaptive policy recovers more language ability
     than today's one-size-fits-all (Fixed) practice and than a pure
     micro-randomized trial (Random).
  2. CAUSAL RECOVERY — from the randomized decision log, the causal layer
     recovers each phenotype's true best activity. This is the
     per-patient dosing answer observational data cannot provide.

Also demonstrates IDENTIFIABILITY: a greedy policy with no exploration
floor starves some (phenotype, arm) cells, so their dose-response becomes
un-estimable — the concrete reason the design must micro-randomize.

Run:  .venv/bin/python -m scripts.simulate_closed_loop
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.closed_loop import (FixedPolicy, GreedyPolicy, RandomPolicy,
                             ThompsonBandit, Simulator, SimStateEstimator,
                             PHENOTYPES, true_best_arm, run_trial,
                             total_recovery, estimate_dose_response,
                             evaluate_recovery, recovered_best_arms)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=56, help="8 weeks")
    p.add_argument("--n-per-phenotype", type=int, default=8)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--output-dir", default="outputs/closed_loop", type=Path)
    return p.parse_args()


def run_policy(name: str, make_policy, args):
    """Fresh simulator+cohort (identical across policies) → run → log."""
    sim = Simulator(seed=args.seed)
    cohort = sim.make_cohort(n_per_phenotype=args.n_per_phenotype)
    est = SimStateEstimator(sim)
    policy = make_policy()
    log = run_trial(cohort, policy, est, sim, days=args.days)
    return name, policy, cohort, log


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    n_patients = args.n_per_phenotype * len(PHENOTYPES)

    print("=" * 70)
    print("CLOSED-LOOP ADAPTIVE DOSING — in-silico validation")
    print(f"{n_patients} patients · {len(PHENOTYPES)} phenotypes · "
          f"{args.days} days (8 weeks)")
    print("=" * 70)
    print("\nGround-truth best activity per phenotype (hidden from the system):")
    for ph in PHENOTYPES:
        print(f"    {ph:18s} → {true_best_arm(ph)}")

    # --- run the three policies on identical cohorts ---
    runs = [
        run_policy("Fixed (guideline default = naming)",
                   lambda: FixedPolicy(arm="naming"), args),
        run_policy("Random (pure micro-randomized trial)",
                   lambda: RandomPolicy(seed=args.seed), args),
        run_policy("Adaptive (Thompson bandit + explore floor)",
                   lambda: ThompsonBandit(explore_floor=0.15, seed=args.seed), args),
    ]

    # --- 1. CLINICAL VALUE ---
    print("\n" + "-" * 70)
    print("1. CLINICAL VALUE — mean language-ability gain over 8 weeks")
    print("-" * 70)
    value_rows = []
    logs_by_policy = {}
    for name, policy, cohort, log in runs:
        gain = total_recovery(cohort)
        value_rows.append({"policy": name, "mean_state_gain": gain})
        logs_by_policy[name] = log
        print(f"    {name:48s}  +{gain:5.2f} pts")
    pd.DataFrame(value_rows).to_csv(args.output_dir / "policy_value.csv", index=False)

    # --- 2. CAUSAL RECOVERY (from the adaptive policy's randomized log) ---
    print("\n" + "-" * 70)
    print("2. CAUSAL RECOVERY — recover each phenotype's best activity")
    print("   from the randomized decision log (IPW estimator)")
    print("-" * 70)
    adaptive_name = runs[2][0]
    adaptive_log = logs_by_policy[adaptive_name]
    est_df = estimate_dose_response(adaptive_log)
    est_df.to_csv(args.output_dir / "dose_response_estimates.csv", index=False)
    adaptive_log.to_parquet(args.output_dir / "decision_log_adaptive.parquet",
                            index=False)

    recovery = evaluate_recovery(est_df, method="ipw_mean")
    recovery.to_csv(args.output_dir / "recovery_eval.csv", index=False)
    print(recovery.to_string(index=False))
    acc = float(recovery["correct"].mean())
    print(f"\n    Recovered the true best activity for "
          f"{int(recovery['correct'].sum())}/{len(recovery)} phenotypes "
          f"({acc:.0%}).")

    # show the adaptive policy's learned assignment concentration
    print("\n    What the adaptive policy learned to deliver "
          "(assignment share by phenotype):")
    share = (adaptive_log.groupby(["phenotype", "arm"]).size()
             / adaptive_log.groupby("phenotype").size())
    for ph in PHENOTYPES:
        s = share[ph].sort_values(ascending=False)
        top = s.index[0]
        flag = "✓" if top == true_best_arm(ph) else "✗"
        print(f"    {ph:18s} top={top:13s} ({s.iloc[0]:.0%})  "
              f"truth={true_best_arm(ph):13s} {flag}")

    # --- 3. IDENTIFIABILITY — why micro-randomization is required ---
    # The formal causal-identification condition is POSITIVITY: every arm
    # must keep assignment probability bounded away from 0 in every context.
    # The floor policy guarantees min propensity >= explore_floor / K. A
    # deterministic greedy policy collapses positivity → unchosen arms are
    # never tried → their dose-response is un-estimable and IPW explodes.
    print("\n" + "-" * 70)
    print("3. IDENTIFIABILITY — positivity is what makes the loop estimable")
    print("-" * 70)
    _, _, _, greedy_log = run_policy(
        "greedy", lambda: GreedyPolicy(seed=args.seed), args)
    greedy_est = estimate_dose_response(greedy_log)
    greedy_rec = evaluate_recovery(greedy_est, method="ipw_mean")
    total_cells = len(est_df)

    def min_cell_coverage(log):
        """Smallest assignment share any activity got within any phenotype.

        This is the empirical positivity signal: 0 means some activity was
        never tried in some phenotype, so its effect cannot be estimated.
        """
        share = (log.groupby(["phenotype", "arm"]).size()
                 / log.groupby("phenotype").size())
        full = share.reindex(
            pd.MultiIndex.from_product([PHENOTYPES, sorted(adaptive_log.arm.unique())],
                                       names=["phenotype", "arm"]),
            fill_value=0.0)
        return float(full.min())

    print(f"    {'policy':24s} {'min cell coverage':>18s} {'cells estimable':>16s} "
          f"{'recovered':>11s}")
    print(f"    {'adaptive (floor 0.15)':24s} {min_cell_coverage(adaptive_log):>18.3f} "
          f"{int(est_df['identified'].sum()):>8d}/{total_cells:<6d} "
          f"{int(recovery['correct'].sum()):>6d}/{len(recovery):<4d}")
    print(f"    {'greedy (no floor)':24s} {min_cell_coverage(greedy_log):>18.3f} "
          f"{int(greedy_est['identified'].sum()):>8d}/{total_cells:<6d} "
          f"{int(greedy_rec['correct'].sum()):>6d}/{len(greedy_rec):<4d}")
    print("    → greedy never tries the activities it doesn't already favour,")
    print("      so most of the dose-response surface is un-estimable (low")
    print("      cell coverage). It may still exploit a good arm by luck, but")
    print("      it cannot RANK activities or personalize when the phenotype")
    print("      prior is wrong. Bounded exploration keeps all cells estimable —")
    print("      the reason a deployed loop must keep micro-randomizing.")

    print("\n" + "=" * 70)
    print(f"Saved logs + estimates to {args.output_dir.resolve()}")
    print("This validates the policy → trial → causal machinery BEFORE any")
    print("patient is enrolled. The 8-week pilot swaps in real patients and")
    print("the foundation-model estimator; the loop is unchanged. (STRATEGY.md §4)")
    print("=" * 70)


if __name__ == "__main__":
    main()
