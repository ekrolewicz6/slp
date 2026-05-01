"""First-pass Dryad EMT-SF DLD treatment-response pilot.

Dataset:
https://doi.org/10.5061/dryad.sj3tx96g9

This script intentionally uses transparent linear models rather than trying to
recreate the paper's lavaan SEM exactly. The goal is to determine what this
public dataset can contribute to the language-state project: treatment effects,
baseline moderators, and trajectory endpoints.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


EVENTS = {
    "t30_arm_1": 30,
    "t33_arm_1": 33,
    "t36_arm_1": 36,
    "t39_arm_1": 39,
    "t42_arm_1": 42,
    "t45_arm_1": 45,
    "t49_arm_1": 49,
}

BASELINE_MODERATORS = {
    "pls5_ac_ss": "PLS-5 auditory comprehension",
    "pls5_ec_ss": "PLS-5 expressive communication",
    "pls5_ls_ss": "PLS-5 total language",
    "lan_c_intelwd": "baseline LAN intelligible words %",
    "lan_c_ndw": "baseline LAN NDW",
    "lan_c_verbs_d": "baseline LAN different verbs",
    "lan_c_subjects_d": "baseline LAN third-person subjects",
    "lan_c_clause_utt": "baseline LAN clause/utterance proportion",
    "lan_30_c_pps": "baseline primed productive syntax",
    "ccx_c_intelwd": "baseline CCX intelligible words %",
    "focus_total": "baseline FOCUS",
    "cbcl_er_ss": "CBCL emotionally reactive",
    "cbcl_ad_ss": "CBCL anxious/depressed",
    "cbcl_sc_ss": "CBCL somatic complaints",
    "cbcl_w_ss": "CBCL withdrawn",
    "cbcl_int_ss": "CBCL internalizing",
    "demo_c_gend_num": "child female",
    "demo_m_diag_sll_num": "maternal speech/language/learning history",
    "demo_f_diag_sll_num": "paternal speech/language/learning history",
}

LANGUAGE_SAMPLE_MEASURES = [
    "lan_c_ndw",
    "lan_c_verbs_d",
    "lan_c_subjects_d",
    "lan_c_clause_utt",
    "lan_30_c_pps",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--data-dir",
        default="data/external/dryad_emt_sf_dld",
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/dryad_emt_sf_treatment_pilot", type=Path)
    p.add_argument("--permutations", type=int, default=500)
    p.add_argument("--seed", type=int, default=20260501)
    return p.parse_args()


def recode_yes_no(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    if text in {"yes", "1", "true"}:
        return 1.0
    if text in {"no", "0", "false"}:
        return 0.0
    return np.nan


def recode_gender(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    if text == "female":
        return 1.0
    if text == "male":
        return 0.0
    return np.nan


def read_long(data_dir: Path) -> pd.DataFrame:
    data_path = data_dir / "Maximizing_Outcomes_for_Toddlers_with_DLD_Data.csv"
    df = pd.read_csv(data_path)
    for col in df.columns:
        if col not in {"id", "redcap_event_name", "rand_randomization_group", "rand_exclude", "pls5_complete", "tegi_pd_dq_admin", "demo_c_gend", "demo_m_diag_sll", "demo_f_diag_sll"}:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def make_wide(df: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for event in EVENTS:
        sub = df[df["redcap_event_name"].eq(event)].copy()
        sub = sub.drop(columns=["redcap_event_name"])
        sub = sub.set_index("id")
        prefix = event.replace("_arm_1", "")
        sub = sub.add_prefix(f"{prefix}_")
        frames.append(sub)
    wide = pd.concat(frames, axis=1, join="outer").reset_index()
    wide["tx"] = wide["t30_rand_randomization_group"].map(
        {"Control = 0": 0.0, "EMT-SF = 1": 1.0}
    )
    wide["exclude"] = wide["t30_rand_exclude"].map({"No": 0.0, "Yes": 1.0})
    wide["demo_c_gend_num"] = wide["t30_demo_c_gend"].map(recode_gender)
    wide["demo_m_diag_sll_num"] = wide["t30_demo_m_diag_sll"].map(recode_yes_no)
    wide["demo_f_diag_sll_num"] = wide["t30_demo_f_diag_sll"].map(recode_yes_no)
    return wide


def zscore(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce")
    mean = vals.mean(skipna=True)
    sd = vals.std(skipna=True, ddof=0)
    if not np.isfinite(sd) or sd < 1e-9:
        return vals * np.nan
    return (vals - mean) / sd


def z_composite(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    z = pd.concat([zscore(df[col]) for col in cols], axis=1)
    return z.mean(axis=1, skipna=True).where(z.notna().any(axis=1))


def prepare_analysis_table(wide: pd.DataFrame) -> pd.DataFrame:
    out = wide[wide["tx"].notna() & wide["exclude"].fillna(0).eq(0)].copy()

    out["t36_vocab_composite_z"] = z_composite(out, ["t36_ppvt5_ss", "t36_evt3_ss"])

    t42_tps = out["t42_tegi_tps_probe_score"]
    t42_pt = out["t42_tegi_pt_probe_score"]
    out["t42_tegi_score"] = np.where(
        t42_pt.isna(),
        t42_tps,
        np.where(t42_tps.isna(), t42_pt, (t42_tps + t42_pt) / 2.0),
    )
    out.loc[
        out["t42_tegi_score"].isna() & out["t42_tegi_pd_dq_admin"].eq("Yes"),
        "t42_tegi_score",
    ] = 0.0
    out["t42_grammar_composite_z"] = z_composite(out, ["t42_spelt2_rs", "t42_tegi_score"])

    t49_tps = out["t49_tegi_tps_probe_score"]
    t49_pt = out["t49_tegi_pt_probe_score"]
    out["t49_tegi_score"] = np.where(
        t49_pt.isna(),
        t49_tps,
        np.where(t49_tps.isna(), t49_pt, (t49_tps + t49_pt) / 2.0),
    )
    out.loc[
        out["t49_tegi_score"].isna() & out["t49_tegi_pd_dq_admin"].eq("Yes"),
        "t49_tegi_score",
    ] = 0.0
    out["t49_grammar_composite_z"] = z_composite(out, ["t49_spelt2_rs", "t49_tegi_score"])
    out["t49_vocab_composite_z"] = z_composite(out, ["t49_ppvt5_ss", "t49_evt3_ss"])

    for col in ["t30_lan_c_ndw", "t30_lan_30_c_pps"]:
        out[f"{col}_mean_imputed"] = out[col].fillna(out[col].mean(skipna=True))
    return out


def ols(y: np.ndarray, X: np.ndarray) -> dict[str, np.ndarray | float]:
    mask = np.isfinite(y) & np.isfinite(X).all(axis=1)
    y = y[mask].astype(float)
    X = X[mask].astype(float)
    n, p = X.shape
    if n <= p:
        raise ValueError("not enough complete rows")
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuals = y - X @ beta
    df = n - p
    sse = float(np.sum(residuals**2))
    sigma2 = sse / df
    xtx_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(xtx_inv) * sigma2)
    tvals = beta / se
    pvals = 2 * stats.t.sf(np.abs(tvals), df)
    y_mean = float(np.mean(y))
    sst = float(np.sum((y - y_mean) ** 2))
    r2 = 1.0 - sse / sst if sst > 0 else np.nan
    sigma = math.sqrt(sigma2)
    return {
        "beta": beta,
        "se": se,
        "t": tvals,
        "p": pvals,
        "df": df,
        "n": n,
        "r2": r2,
        "sigma": sigma,
        "mask": mask,
    }


def fit_treatment_model(
    df: pd.DataFrame,
    outcome_col: str,
    covariate_col: str | None,
    outcome_label: str,
    family: str,
) -> dict[str, float | str]:
    y = pd.to_numeric(df[outcome_col], errors="coerce").to_numpy(dtype=float)
    tx = df["tx"].to_numpy(dtype=float)
    cols = [np.ones(len(df)), tx]
    names = ["intercept", "tx"]
    if covariate_col is not None:
        cov = pd.to_numeric(df[covariate_col], errors="coerce")
        cov = cov.fillna(cov.mean(skipna=True))
        cov = (cov - cov.mean()) / cov.std(ddof=0)
        cols.append(cov.to_numpy(dtype=float))
        names.append("baseline_covariate_z")
    X = np.column_stack(cols)
    fit = ols(y, X)
    tx_idx = names.index("tx")
    mask = fit["mask"]
    y_complete = y[mask]
    tx_complete = tx[mask]
    return {
        "family": family,
        "outcome": outcome_label,
        "outcome_col": outcome_col,
        "covariate": covariate_col or "none",
        "n": int(fit["n"]),
        "n_emt_sf": int(np.sum(tx_complete == 1)),
        "n_control": int(np.sum(tx_complete == 0)),
        "control_mean_raw": float(np.nanmean(y_complete[tx_complete == 0])),
        "emt_sf_mean_raw": float(np.nanmean(y_complete[tx_complete == 1])),
        "unadjusted_difference": float(np.nanmean(y_complete[tx_complete == 1]) - np.nanmean(y_complete[tx_complete == 0])),
        "adjusted_tx_effect": float(fit["beta"][tx_idx]),
        "adjusted_tx_se": float(fit["se"][tx_idx]),
        "adjusted_tx_p": float(fit["p"][tx_idx]),
        "adjusted_tx_ci_lo": float(fit["beta"][tx_idx] - stats.t.ppf(0.975, fit["df"]) * fit["se"][tx_idx]),
        "adjusted_tx_ci_hi": float(fit["beta"][tx_idx] + stats.t.ppf(0.975, fit["df"]) * fit["se"][tx_idx]),
        "adjusted_cohens_d_resid": float(fit["beta"][tx_idx] / fit["sigma"]),
        "model_r2": float(fit["r2"]),
    }


def treatment_effects(df: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("t36_vocab_composite_z", "T36 vocabulary composite z", "t30_lan_c_ndw_mean_imputed", "primary_vocabulary"),
        ("t36_ppvt5_ss", "T36 PPVT-5 SS", "t30_lan_c_ndw_mean_imputed", "primary_vocabulary"),
        ("t36_evt3_ss", "T36 EVT-3 SS", "t30_lan_c_ndw_mean_imputed", "primary_vocabulary"),
        ("t42_grammar_composite_z", "T42 grammar composite z", "t30_lan_30_c_pps_mean_imputed", "primary_grammar"),
        ("t42_spelt2_rs", "T42 SPELT-P2 raw", "t30_lan_30_c_pps_mean_imputed", "primary_grammar"),
        ("t42_spelt2_ss", "T42 SPELT-P2 SS", "t30_lan_30_c_pps_mean_imputed", "primary_grammar"),
        ("t42_tegi_score", "T42 TEGI composite", "t30_lan_30_c_pps_mean_imputed", "primary_grammar"),
        ("t49_vocab_composite_z", "T49 vocabulary composite z", "t30_lan_c_ndw_mean_imputed", "exploratory_t49"),
        ("t49_grammar_composite_z", "T49 grammar composite z", "t30_lan_30_c_pps_mean_imputed", "exploratory_t49"),
        ("t49_celfp3_ss", "T49 CELF-P3 SS", "t30_lan_30_c_pps_mean_imputed", "exploratory_t49"),
        ("t49_rbsna_total", "T49 Renfrew Bus Story", "t30_lan_c_ndw_mean_imputed", "exploratory_t49"),
    ]
    rows = []
    for outcome_col, label, cov, family in specs:
        if outcome_col not in df.columns:
            continue
        try:
            rows.append(fit_treatment_model(df, outcome_col, cov, label, family))
        except Exception as exc:
            rows.append(
                {
                    "family": family,
                    "outcome": label,
                    "outcome_col": outcome_col,
                    "covariate": cov,
                    "error": str(exc),
                }
            )
    return pd.DataFrame(rows)


def language_sample_followups(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for measure in LANGUAGE_SAMPLE_MEASURES:
        baseline = f"t30_{measure}"
        if baseline not in df.columns:
            continue
        for event in ["t33", "t36", "t39", "t42", "t45", "t49"]:
            outcome = f"{event}_{measure}"
            if outcome not in df.columns:
                continue
            label = f"{event.upper()} {measure}"
            try:
                rows.append(fit_treatment_model(df, outcome, baseline, label, "language_sample_followup"))
            except Exception:
                continue
    return pd.DataFrame(rows)


def bh_qvalues(p: pd.Series) -> pd.Series:
    pvals = pd.to_numeric(p, errors="coerce").to_numpy(dtype=float)
    q = np.full_like(pvals, np.nan, dtype=float)
    finite = np.isfinite(pvals)
    order = np.argsort(pvals[finite])
    finite_indices = np.where(finite)[0]
    sorted_idx = finite_indices[order]
    m = len(sorted_idx)
    prev = 1.0
    for rank_from_end, idx in enumerate(sorted_idx[::-1], start=1):
        rank = m - rank_from_end + 1
        val = min(prev, pvals[idx] * m / rank)
        q[idx] = val
        prev = val
    return pd.Series(q, index=p.index)


def moderator_fit(
    df: pd.DataFrame,
    outcome_col: str,
    covariate_col: str,
    moderator_col: str,
) -> dict[str, float] | None:
    y = pd.to_numeric(df[outcome_col], errors="coerce")
    tx = df["tx"].astype(float)
    cov = pd.to_numeric(df[covariate_col], errors="coerce")
    mod = pd.to_numeric(df[moderator_col], errors="coerce")
    work = pd.DataFrame({"y": y, "tx": tx, "cov": cov, "mod": mod}).dropna()
    if len(work) < 35 or work["tx"].nunique() < 2 or work["mod"].std(ddof=0) < 1e-9:
        return None
    work["cov_z"] = (work["cov"] - work["cov"].mean()) / work["cov"].std(ddof=0)
    work["mod_z"] = (work["mod"] - work["mod"].mean()) / work["mod"].std(ddof=0)
    X = np.column_stack(
        [
            np.ones(len(work)),
            work["tx"].to_numpy(),
            work["cov_z"].to_numpy(),
            work["mod_z"].to_numpy(),
            (work["tx"] * work["mod_z"]).to_numpy(),
        ]
    )
    fit = ols(work["y"].to_numpy(), X)
    return {
        "n": int(fit["n"]),
        "interaction_coef": float(fit["beta"][4]),
        "interaction_se": float(fit["se"][4]),
        "interaction_t": float(fit["t"][4]),
        "interaction_p": float(fit["p"][4]),
        "main_tx_effect_at_mean_moderator": float(fit["beta"][1]),
        "model_r2": float(fit["r2"]),
    }


def moderator_screen(df: pd.DataFrame, permutations: int, seed: int) -> pd.DataFrame:
    specs = [
        ("t36_vocab_composite_z", "T36 vocabulary composite z", "t30_lan_c_ndw_mean_imputed"),
        ("t42_grammar_composite_z", "T42 grammar composite z", "t30_lan_30_c_pps_mean_imputed"),
        ("t49_vocab_composite_z", "T49 vocabulary composite z", "t30_lan_c_ndw_mean_imputed"),
        ("t49_grammar_composite_z", "T49 grammar composite z", "t30_lan_30_c_pps_mean_imputed"),
    ]
    rows = []
    for outcome_col, outcome_label, covariate in specs:
        for base_col, moderator_label in BASELINE_MODERATORS.items():
            col = base_col if base_col.startswith("demo_") else f"t30_{base_col}"
            if col not in df.columns:
                continue
            result = moderator_fit(df, outcome_col, covariate, col)
            if result is None:
                continue
            result.update(
                {
                    "outcome": outcome_label,
                    "outcome_col": outcome_col,
                    "moderator": moderator_label,
                    "moderator_col": col,
                    "covariate": covariate,
                }
            )
            rows.append(result)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["interaction_q_bh"] = bh_qvalues(out["interaction_p"])

    rng = np.random.default_rng(seed)
    family_p = []
    for outcome_col, group in out.groupby("outcome_col"):
        max_t_null = []
        valid_mods = group[["moderator_col", "covariate"]].drop_duplicates().values.tolist()
        original_tx = df["tx"].copy()
        for _ in range(permutations):
            permuted = original_tx.sample(frac=1.0, replace=False, random_state=int(rng.integers(0, 2**31 - 1))).to_numpy()
            perm_df = df.copy()
            perm_df["tx"] = permuted
            tvals = []
            for moderator_col, covariate in valid_mods:
                result = moderator_fit(perm_df, outcome_col, covariate, moderator_col)
                if result is not None and np.isfinite(result["interaction_t"]):
                    tvals.append(abs(result["interaction_t"]))
            if tvals:
                max_t_null.append(max(tvals))
        max_t_null = np.asarray(max_t_null)
        for idx, row in group.iterrows():
            if len(max_t_null):
                p_fwer = (np.sum(max_t_null >= abs(row["interaction_t"])) + 1) / (len(max_t_null) + 1)
            else:
                p_fwer = np.nan
            family_p.append((idx, p_fwer))
    out["interaction_p_maxT_family"] = np.nan
    for idx, pval in family_p:
        out.loc[idx, "interaction_p_maxT_family"] = pval
    return out.sort_values(["interaction_p", "interaction_p_maxT_family"])


def inventory_tables(long: pd.DataFrame, analysis: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    event_rows = (
        long.groupby("redcap_event_name")
        .agg(rows=("id", "count"), participants=("id", "nunique"))
        .reset_index()
    )
    event_rows["month"] = event_rows["redcap_event_name"].map(EVENTS)
    event_rows = event_rows.sort_values("month")
    group_balance = (
        analysis.groupby("tx")
        .agg(
            n=("id", "count"),
            mean_age_m=("t30_enroll_consent_age_m", "mean"),
            mean_pls5_total=("t30_pls5_ls_ss", "mean"),
            mean_lan_ndw=("t30_lan_c_ndw", "mean"),
            mean_lan_pps=("t30_lan_30_c_pps", "mean"),
        )
        .reset_index()
    )
    group_balance["group"] = group_balance["tx"].map({0.0: "Control", 1.0: "EMT-SF"})
    key_cols = [
        "t30_lan_c_ndw",
        "t30_lan_30_c_pps",
        "t36_ppvt5_ss",
        "t36_evt3_ss",
        "t42_spelt2_rs",
        "t42_tegi_score",
        "t49_ppvt5_ss",
        "t49_evt3_ss",
        "t49_spelt2_rs",
        "t49_tegi_score",
        "t49_celfp3_ss",
        "t49_rbsna_total",
    ]
    missing = []
    for col in key_cols:
        if col in analysis.columns:
            missing.append(
                {
                    "variable": col,
                    "nonmissing_n": int(analysis[col].notna().sum()),
                    "missing_n": int(analysis[col].isna().sum()),
                    "nonmissing_rate": float(analysis[col].notna().mean()),
                }
            )
    return event_rows, group_balance, pd.DataFrame(missing)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    long = read_long(args.data_dir)
    wide = make_wide(long)
    analysis = prepare_analysis_table(wide)

    event_rows, group_balance, missing = inventory_tables(long, analysis)
    effects = treatment_effects(analysis)
    language_effects = language_sample_followups(analysis)
    moderators = moderator_screen(analysis, args.permutations, args.seed)

    event_rows.to_csv(out_dir / "event_inventory.csv", index=False)
    group_balance.to_csv(out_dir / "baseline_group_balance.csv", index=False)
    missing.to_csv(out_dir / "key_variable_missingness.csv", index=False)
    effects.to_csv(out_dir / "treatment_effects.csv", index=False)
    language_effects.to_csv(out_dir / "language_sample_followup_effects.csv", index=False)
    moderators.to_csv(out_dir / "moderator_screen.csv", index=False)

    primary_effects = effects[effects["family"].isin(["primary_vocabulary", "primary_grammar"])].copy()
    primary_view = primary_effects[
        [
            "family",
            "outcome",
            "n",
            "n_emt_sf",
            "n_control",
            "adjusted_tx_effect",
            "adjusted_tx_ci_lo",
            "adjusted_tx_ci_hi",
            "adjusted_tx_p",
            "adjusted_cohens_d_resid",
            "model_r2",
        ]
    ].round(3)

    exploratory_view = effects[effects["family"].eq("exploratory_t49")][
        [
            "outcome",
            "n",
            "adjusted_tx_effect",
            "adjusted_tx_ci_lo",
            "adjusted_tx_ci_hi",
            "adjusted_tx_p",
            "adjusted_cohens_d_resid",
        ]
    ].round(3)

    top_lang = language_effects.sort_values("adjusted_tx_p").head(12)[
        [
            "outcome",
            "n",
            "adjusted_tx_effect",
            "adjusted_tx_ci_lo",
            "adjusted_tx_ci_hi",
            "adjusted_tx_p",
            "adjusted_cohens_d_resid",
        ]
    ].round(3)

    top_mod = moderators.head(12)[
        [
            "outcome",
            "moderator",
            "n",
            "interaction_coef",
            "interaction_p",
            "interaction_q_bh",
            "interaction_p_maxT_family",
            "main_tx_effect_at_mean_moderator",
        ]
    ].round(3)

    any_moderator_robust = bool(
        (moderators["interaction_q_bh"].lt(0.10) & moderators["interaction_p_maxT_family"].lt(0.10)).any()
    ) if not moderators.empty else False

    lines = [
        "# Dryad EMT-SF DLD Treatment Pilot",
        "",
        "Dataset: Dryad DOI `10.5061/dryad.sj3tx96g9`, \"Maximizing outcomes for preschoolers with developmental language disorders.\"",
        "",
        "Citation: Grauzer, Jeffrey; Roberts, Megan; Jones, Maranda (2026), *Maximizing outcomes for preschoolers with developmental language disorders* [Dataset], Dryad, https://doi.org/10.5061/dryad.sj3tx96g9.",
        "",
        "Trial context: ClinicalTrials.gov `NCT03782493` lists Megan Y. Roberts, Pamela Hadley, and Ann Kaiser as principal investigators for *Maximizing Outcomes for Preschoolers With Developmental Language Disorders*.",
        "",
        "## Data Inventory",
        "",
        f"- Long-format rows: {len(long):,}",
        f"- Unique shared participant IDs: {long['id'].nunique():,}",
        f"- Baseline randomized analysis participants: {len(analysis):,}",
        f"- EMT-SF / control at baseline: {int(analysis['tx'].sum()):,} / {int((analysis['tx'] == 0).sum()):,}",
        "",
        "### Event Rows",
        "",
        md_table(event_rows),
        "",
        "### Baseline Group Balance",
        "",
        md_table(group_balance.drop(columns=["tx"]).round(3)),
        "",
        "### Key Variable Missingness",
        "",
        md_table(missing.round(3)),
        "",
        "## Primary Treatment Contrasts",
        "",
        "Transparent OLS models are used here rather than exact lavaan SEM replication. Vocabulary models adjust for baseline LAN NDW; grammar models adjust for baseline primed productive syntax.",
        "",
        md_table(primary_view),
        "",
        "## Exploratory T49 Outcomes",
        "",
        md_table(exploratory_view),
        "",
        "## Language-Sample Follow-Up Effects",
        "",
        md_table(top_lang),
        "",
        "## Baseline Moderator Screen",
        "",
        md_table(top_mod),
        "",
        "## Interpretation",
        "",
        "This is the first local dataset that directly links a randomized DLD intervention to later outcomes. It is therefore more clinically relevant than the previous CHILDES-only DLD work. The treatment signal is strongest for grammar-related outcomes, especially the T42 grammar composite and SPELT-P2. The vocabulary signal at T36 is weaker in these transparent Python models.",
        "",
        f"The heterogeneous-response screen should be treated as exploratory. Robust moderator found after BH and max-T controls: `{any_moderator_robust}`. The current shared dataset is too small to claim treatment matching, but it is exactly the kind of schema the project needs: baseline language sample variables, randomized treatment, repeated outcomes, and enough covariates to ask who benefits.",
        "",
        "Main limitation: the dataset contains aggregate REDCap variables, not raw transcripts/audio. It can validate treatment-response questions, but it cannot yet connect our richer CLAN/TalkBank state representation directly to EMT-SF dose, target selection, or session-level change.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
