#!/usr/bin/env python3
"""Analyze the Fiveash et al. sentence-repetition rhythmic priming dataset.

This is not a replacement for the paper's ordinal mixed-effects analysis. It is
an SLP-state pilot for our project: can a tight structured task expose language
state, and does the regular-vs-irregular rhythm manipulation add useful signal?
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import LeaveOneOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "external" / "literature" / "structured_tasks" / "fiveash_2023_osf"
OUT_DIR = ROOT / "outputs" / "fiveash_sentence_repetition_pilot"
PARSED_DIR = ROOT / "data" / "parsed" / "fiveash_sentence_repetition"

RNG = np.random.default_rng(20260501)
N_BOOT = 5000
N_PERM = 5000


@dataclass(frozen=True)
class EffectResult:
    effect: str
    estimate: float
    ci_low: float
    ci_high: float
    p_value: float | None = None
    n: int | None = None


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=0)


def ci(values: Iterable[float], alpha: float = 0.05) -> tuple[float, float]:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return (np.nan, np.nan)
    return tuple(np.quantile(arr, [alpha / 2, 1 - alpha / 2]).tolist())


def mean_ci(values: pd.Series) -> tuple[float, float]:
    vals = values.dropna().to_numpy(dtype=float)
    if len(vals) == 0:
        return (np.nan, np.nan)
    boot = [RNG.choice(vals, size=len(vals), replace=True).mean() for _ in range(N_BOOT)]
    return ci(boot)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    info = pd.read_csv(DATA_DIR / "ParticipantInfo_SentIm_15_18_blindnumber.csv")
    # The file contains French sentence text encoded outside UTF-8. The text is
    # not used for feature extraction, but latin1 preserves the row structure.
    trials = pd.read_csv(DATA_DIR / "longdata_SentIm_15_18_blindnumber.csv", encoding="latin1")
    data = trials.merge(info, on="Subject", how="left", validate="many_to_one")
    if data["Group"].isna().any():
        raise ValueError("Some trials did not join to participant metadata.")
    data["is_dld"] = (data["Group"] == "DLD").astype(int)
    data["regular"] = (data["Prime"] == "Regular").astype(int)
    data["regular_x_dld"] = data["regular"] * data["is_dld"]
    data["Age_z"] = zscore(data["Age"])
    data["Reading_z"] = zscore(data["Reading_SDFromNorm"])
    data["Reading_missing"] = data["Reading_SDFromNorm"].isna().astype(int)
    data["Reading_z_filled"] = data["Reading_z"].fillna(0)
    return info, data


def build_participant_features(info: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
    subject = info.copy()
    subject["is_dld"] = (subject["Group"] == "DLD").astype(int)

    prime_mean = data.pivot_table(index="Subject", columns="Prime", values="Gram_Score", aggfunc="mean")
    prime_sum = data.pivot_table(index="Subject", columns="Prime", values="Gram_Score", aggfunc="sum")
    subject = subject.merge(
        prime_mean.rename(columns={"Regular": "regular_mean", "Irregular": "irregular_mean"}),
        left_on="Subject",
        right_index=True,
        how="left",
    )
    subject = subject.merge(
        prime_sum.rename(columns={"Regular": "regular_sum", "Irregular": "irregular_sum"}),
        left_on="Subject",
        right_index=True,
        how="left",
    )
    subject["overall_mean"] = data.groupby("Subject")["Gram_Score"].mean().reindex(subject["Subject"]).to_numpy()
    subject["overall_sum"] = data.groupby("Subject")["Gram_Score"].sum().reindex(subject["Subject"]).to_numpy()
    subject["rhythm_delta_mean"] = subject["regular_mean"] - subject["irregular_mean"]
    subject["rhythm_delta_sum"] = subject["regular_sum"] - subject["irregular_sum"]

    senttype_mean = data.pivot_table(index="Subject", columns="SentType", values="Gram_Score", aggfunc="mean")
    for col in senttype_mean.columns:
        subject[f"senttype_{col.lower()}_mean"] = subject["Subject"].map(senttype_mean[col])

    senttype_prime = data.pivot_table(
        index="Subject",
        columns=["SentType", "Prime"],
        values="Gram_Score",
        aggfunc="mean",
    )
    for senttype in sorted(data["SentType"].dropna().unique()):
        reg = senttype_prime.get((senttype, "Regular"))
        irr = senttype_prime.get((senttype, "Irregular"))
        if reg is not None:
            subject[f"{senttype.lower()}_regular_mean"] = subject["Subject"].map(reg)
        if irr is not None:
            subject[f"{senttype.lower()}_irregular_mean"] = subject["Subject"].map(irr)
        if reg is not None and irr is not None:
            subject[f"{senttype.lower()}_rhythm_delta"] = subject["Subject"].map(reg - irr)

    return subject


def group_prime_summary(data: pd.DataFrame) -> pd.DataFrame:
    subj_prime = (
        data.groupby(["Subject", "Group", "Prime"], as_index=False)
        .agg(participant_mean=("Gram_Score", "mean"), participant_sum=("Gram_Score", "sum"), n_trials=("Gram_Score", "size"))
    )
    rows = []
    for (group, prime), g in subj_prime.groupby(["Group", "Prime"], sort=True):
        low, high = mean_ci(g["participant_mean"])
        rows.append(
            {
                "group": group,
                "prime": prime,
                "n_participants": g["Subject"].nunique(),
                "n_trials": int(g["n_trials"].sum()),
                "mean_participant_score": g["participant_mean"].mean(),
                "mean_participant_score_ci_low": low,
                "mean_participant_score_ci_high": high,
                "mean_participant_sum": g["participant_sum"].mean(),
                "sd_participant_sum": g["participant_sum"].std(ddof=1),
            }
        )
    return pd.DataFrame(rows)


def senttype_summary(data: pd.DataFrame) -> pd.DataFrame:
    subj = (
        data.groupby(["Subject", "Group", "SentType", "Prime"], as_index=False)
        .agg(participant_mean=("Gram_Score", "mean"), n_trials=("Gram_Score", "size"))
    )
    rows = []
    for (group, senttype, prime), g in subj.groupby(["Group", "SentType", "Prime"], sort=True):
        low, high = mean_ci(g["participant_mean"])
        rows.append(
            {
                "group": group,
                "sent_type": senttype,
                "prime": prime,
                "n_participants": g["Subject"].nunique(),
                "n_trials": int(g["n_trials"].sum()),
                "mean_participant_score": g["participant_mean"].mean(),
                "ci_low": low,
                "ci_high": high,
            }
        )
    return pd.DataFrame(rows)


def ols_fit(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    X2 = np.column_stack([np.ones(len(X)), X])
    return np.linalg.lstsq(X2, y, rcond=None)[0]


def trial_level_coefficients(data: pd.DataFrame) -> pd.DataFrame:
    sent_dummies = pd.get_dummies(data["SentType"], prefix="senttype", drop_first=True, dtype=float)
    x_df = pd.concat(
        [
            data[["regular", "is_dld", "regular_x_dld", "Age_z", "Reading_z_filled", "Reading_missing"]].astype(float),
            sent_dummies,
        ],
        axis=1,
    )
    names = ["intercept", *x_df.columns.tolist()]
    beta = ols_fit(x_df.to_numpy(), data["Gram_Score"].to_numpy())

    boot = []
    subjects = data["Subject"].drop_duplicates().to_numpy()
    grouped = {sid: data.index[data["Subject"] == sid].to_numpy() for sid in subjects}
    for _ in range(N_BOOT):
        sampled = RNG.choice(subjects, size=len(subjects), replace=True)
        idx = np.concatenate([grouped[sid] for sid in sampled])
        b = ols_fit(x_df.iloc[idx].to_numpy(), data.iloc[idx]["Gram_Score"].to_numpy())
        boot.append(b)
    boot_arr = np.asarray(boot)

    rows = []
    for i, name in enumerate(names):
        low, high = ci(boot_arr[:, i])
        rows.append(
            {
                "term": name,
                "estimate_score_points": beta[i],
                "cluster_boot_ci_low": low,
                "cluster_boot_ci_high": high,
            }
        )
    return pd.DataFrame(rows)


def sign_flip_p(delta: np.ndarray) -> float:
    observed = abs(np.nanmean(delta))
    vals = delta[np.isfinite(delta)]
    null = []
    for _ in range(N_PERM):
        signs = RNG.choice([-1, 1], size=len(vals), replace=True)
        null.append(abs(np.mean(vals * signs)))
    return (np.sum(np.asarray(null) >= observed) + 1) / (len(null) + 1)


def group_permutation_p(values: np.ndarray, labels: np.ndarray) -> float:
    labels = labels.astype(int)
    observed = abs(values[labels == 1].mean() - values[labels == 0].mean())
    null = []
    for _ in range(N_PERM):
        shuffled = RNG.permutation(labels)
        null.append(abs(values[shuffled == 1].mean() - values[shuffled == 0].mean()))
    return (np.sum(np.asarray(null) >= observed) + 1) / (len(null) + 1)


def bootstrap_effects(subject: pd.DataFrame) -> pd.DataFrame:
    effects: list[EffectResult] = []
    delta = subject["rhythm_delta_mean"].to_numpy(dtype=float)
    labels = subject["is_dld"].to_numpy(dtype=int)

    for name, mask in {
        "regular_minus_irregular_mean_all": np.ones(len(subject), dtype=bool),
        "regular_minus_irregular_mean_td": labels == 0,
        "regular_minus_irregular_mean_dld": labels == 1,
    }.items():
        vals = delta[mask]
        low, high = ci(RNG.choice(vals, size=(N_BOOT, len(vals)), replace=True).mean(axis=1))
        p_value = sign_flip_p(vals) if name.endswith("_all") else None
        effects.append(EffectResult(name, float(np.mean(vals)), low, high, p_value, len(vals)))

    diff = delta[labels == 1].mean() - delta[labels == 0].mean()
    boot_diff = []
    for _ in range(N_BOOT):
        dld = RNG.choice(delta[labels == 1], size=(labels == 1).sum(), replace=True).mean()
        td = RNG.choice(delta[labels == 0], size=(labels == 0).sum(), replace=True).mean()
        boot_diff.append(dld - td)
    low, high = ci(boot_diff)
    effects.append(
        EffectResult(
            "dld_minus_td_rhythm_delta",
            float(diff),
            low,
            high,
            group_permutation_p(delta, labels),
            len(subject),
        )
    )

    group_diff = subject.loc[labels == 1, "overall_mean"].mean() - subject.loc[labels == 0, "overall_mean"].mean()
    boot_group = []
    dld_vals = subject.loc[labels == 1, "overall_mean"].to_numpy(dtype=float)
    td_vals = subject.loc[labels == 0, "overall_mean"].to_numpy(dtype=float)
    for _ in range(N_BOOT):
        boot_group.append(
            RNG.choice(dld_vals, size=len(dld_vals), replace=True).mean()
            - RNG.choice(td_vals, size=len(td_vals), replace=True).mean()
        )
    low, high = ci(boot_group)
    effects.append(
        EffectResult(
            "dld_minus_td_overall_sentence_repetition",
            float(group_diff),
            low,
            high,
            group_permutation_p(subject["overall_mean"].to_numpy(dtype=float), labels),
            len(subject),
        )
    )

    return pd.DataFrame([e.__dict__ for e in effects])


def loocv_predictions(df: pd.DataFrame, feature_cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    y = df["is_dld"].to_numpy(dtype=int)
    prob = np.zeros(len(df), dtype=float)
    numeric_transformer = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    pipe = Pipeline(
        steps=[
            ("prep", ColumnTransformer([("num", numeric_transformer, feature_cols)], remainder="drop")),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    solver="liblinear",
                    max_iter=2000,
                    random_state=20260501,
                ),
            ),
        ]
    )
    loo = LeaveOneOut()
    for train_idx, test_idx in loo.split(df):
        pipe.fit(df.iloc[train_idx], y[train_idx])
        prob[test_idx[0]] = pipe.predict_proba(df.iloc[test_idx])[:, 1][0]
    return y, prob


def classification_metrics(df: pd.DataFrame) -> pd.DataFrame:
    feature_sets = {
        "age_only": ["Age"],
        "reading_age_only": ["Reading_SDFromNorm"],
        "sentence_repetition_level": [
            "overall_mean",
            "regular_mean",
            "irregular_mean",
            "senttype_filler_mean",
            "senttype_oo_mean",
            "senttype_os_mean",
        ],
        "rhythm_response_only": [
            "rhythm_delta_mean",
            "filler_rhythm_delta",
            "oo_rhythm_delta",
            "os_rhythm_delta",
        ],
        "sentence_repetition_plus_rhythm": [
            "overall_mean",
            "regular_mean",
            "irregular_mean",
            "senttype_filler_mean",
            "senttype_oo_mean",
            "senttype_os_mean",
            "rhythm_delta_mean",
            "filler_rhythm_delta",
            "oo_rhythm_delta",
            "os_rhythm_delta",
        ],
        "sentence_repetition_plus_reading": [
            "overall_mean",
            "regular_mean",
            "irregular_mean",
            "rhythm_delta_mean",
            "Reading_SDFromNorm",
        ],
        "clinical_background_upper_bound": [
            "Age",
            "Reading_SDFromNorm",
            "Logotome_SDFromNorm",
            "ELDP_Zscore",
            "CELF_Elab_NoteStandard",
            "CELF_Rep_NoteStandard",
        ],
    }

    rows = []
    for name, cols in feature_sets.items():
        y, prob = loocv_predictions(df, cols)
        pred = (prob >= 0.5).astype(int)
        auc = roc_auc_score(y, prob)
        bal = balanced_accuracy_score(y, pred)
        f1 = f1_score(y, pred, zero_division=0)
        acc = accuracy_score(y, pred)

        null_auc = []
        for _ in range(1000):
            shuffled = RNG.permutation(y)
            null_auc.append(roc_auc_score(shuffled, prob))
        p_auc = (np.sum(np.asarray(null_auc) >= auc) + 1) / (len(null_auc) + 1)

        rows.append(
            {
                "feature_set": name,
                "n": len(df),
                "n_features": len(cols),
                "auc": auc,
                "balanced_accuracy": bal,
                "accuracy": acc,
                "dld_f1": f1,
                "auc_label_permutation_p": p_auc,
            }
        )
    return pd.DataFrame(rows).sort_values(["auc", "balanced_accuracy"], ascending=False)


def write_summary(
    data: pd.DataFrame,
    subject: pd.DataFrame,
    gp: pd.DataFrame,
    effects: pd.DataFrame,
    coef: pd.DataFrame,
    cls: pd.DataFrame,
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    best_cls = cls.iloc[0]
    best_task_cls = cls.loc[
        ~cls["feature_set"].isin(["clinical_background_upper_bound", "age_only", "reading_age_only"])
    ].iloc[0]
    rhythm_cls = cls.loc[cls["feature_set"] == "rhythm_response_only"].iloc[0]
    regular_effect = effects.loc[effects["effect"] == "regular_minus_irregular_mean_all"].iloc[0]
    group_effect = effects.loc[effects["effect"] == "dld_minus_td_overall_sentence_repetition"].iloc[0]
    rhythm_group_effect = effects.loc[effects["effect"] == "dld_minus_td_rhythm_delta"].iloc[0]
    regular_coef = coef.loc[coef["term"] == "regular"].iloc[0]
    dld_coef = coef.loc[coef["term"] == "is_dld"].iloc[0]
    interaction_coef = coef.loc[coef["term"] == "regular_x_dld"].iloc[0]

    lines = [
        "# Fiveash Sentence-Repetition Structured-Task Pilot",
        "",
        "Source: Fiveash, A., Ladanyi, E., Camici, J., Chidiac, K., Bush, C. T., Canette, L.-H., Bedoin, N., Gordon, R. L., & Tillmann, B. (2023). Regular rhythmic primes improve sentence repetition in children with developmental language disorder. *npj Science of Learning*, 8, 23. https://doi.org/10.1038/s41539-023-00170-1",
        "",
        "## Question",
        "",
        "Brian's advice points toward pairing natural speech with tight, automatable structured tasks. This pilot asks whether the Fiveash et al. sentence-repetition task behaves like a useful state probe: does it separate DLD from TD, and does the regular rhythm manipulation add clinically interpretable information beyond overall task level?",
        "",
        "## Data",
        "",
        f"- Participants: {subject.shape[0]} children ({(subject['Group'] == 'TD').sum()} TD, {(subject['Group'] == 'DLD').sum()} DLD).",
        f"- Trial rows: {data.shape[0]} ({data['Prime'].value_counts().to_dict()}).",
        "- Outcome: ordinal grammar score coded 0, 0.5, or 1; this pilot uses transparent numeric approximations plus subject-level resampling, not the paper's ordinal mixed-effects model.",
        "",
        "## Main Results",
        "",
        f"- Regular rhythm improved sentence repetition by {regular_effect.estimate:.3f} grammar-score points on the 0-1 scale (95% bootstrap CI {regular_effect.ci_low:.3f} to {regular_effect.ci_high:.3f}; sign-flip p={regular_effect.p_value:.4f}).",
        f"- DLD children scored lower overall by {group_effect.estimate:.3f} points relative to TD (DLD minus TD; 95% bootstrap CI {group_effect.ci_low:.3f} to {group_effect.ci_high:.3f}; permutation p={group_effect.p_value:.4f}).",
        f"- The DLD-vs-TD difference in rhythm benefit was {rhythm_group_effect.estimate:.3f} points (95% bootstrap CI {rhythm_group_effect.ci_low:.3f} to {rhythm_group_effect.ci_high:.3f}; permutation p={rhythm_group_effect.p_value:.4f}). This is the key project-specific caution: rhythm helps, but the response size is not clearly DLD-specific in this sample.",
        f"- Trial-level OLS approximation: regular coefficient {regular_coef.estimate_score_points:.3f}, DLD coefficient {dld_coef.estimate_score_points:.3f}, regular x DLD coefficient {interaction_coef.estimate_score_points:.3f}; CIs are in `trial_model_coefficients.csv`.",
        f"- Clinical-background variables separate the two groups perfectly here (AUC {best_cls.auc:.3f}), which is expected because they are close to the labeling construct and should be treated only as an upper bound.",
        f"- Best task-only leave-one-child-out DLD-vs-TD classifier: `{best_task_cls.feature_set}` with AUC {best_task_cls.auc:.3f}, balanced accuracy {best_task_cls.balanced_accuracy:.3f}, and DLD F1 {best_task_cls.dld_f1:.3f}.",
        f"- Rhythm-response-only classification is weaker (AUC {rhythm_cls.auc:.3f}, balanced accuracy {rhythm_cls.balanced_accuracy:.3f}), reinforcing that the immediate rhythm benefit is not enough by itself to define a clinical subtype or treatment plan.",
        "",
        "## Interpretation for Our Program",
        "",
        "- Sentence repetition is a strong candidate for the tight-task half of the natural-plus-structured assessment battery.",
        "- The rhythm manipulation is scientifically interesting as a causal perturbation of grammar processing, but the public sample does not yet show that rhythm response alone can assign treatment or predict who benefits most.",
        "- The next version of our battery should treat sentence repetition level as a robust state measure, and rhythm response as an experimental input-sensitivity measure that needs replication in longitudinal/treatment data.",
        "- This result aligns with Brian's point that a rich clinical output should not collapse to one score: the same structured task can expose grammar level, rhythm sensitivity, age/reading covariates, and group-risk separation.",
        "",
        "## Output Files",
        "",
        "- `group_prime_summary.csv`: participant-level mean grammar scores by group and prime.",
        "- `senttype_prime_summary.csv`: score patterns by group, prime, and sentence type.",
        "- `bootstrap_effects.csv`: bootstrap and permutation tests for rhythm and group contrasts.",
        "- `trial_model_coefficients.csv`: transparent trial-level OLS approximation with participant-cluster bootstrap CIs.",
        "- `classification_metrics.csv`: leave-one-child-out DLD-vs-TD classification from structured-task feature sets.",
        "",
        "## Limits",
        "",
        "- This is a secondary analysis of a 33-child experimental dataset, not a clinical validation study.",
        "- The public file has no natural speech sample paired with the structured task, so it cannot answer the combined-battery question directly.",
        "- Treatment-response claims require repeated outcomes after actual intervention; this dataset only tests an immediate rhythmic prime.",
        "",
    ]
    (OUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    info, data = load_data()
    subject = build_participant_features(info, data)

    gp = group_prime_summary(data)
    st = senttype_summary(data)
    effects = bootstrap_effects(subject)
    coef = trial_level_coefficients(data)
    cls = classification_metrics(subject)

    # Participant-level rows include blinded child IDs; keep under gitignored data.
    subject.to_csv(PARSED_DIR / "participant_sentence_repetition_features.csv", index=False)
    data.to_csv(PARSED_DIR / "trial_sentence_repetition_features.csv", index=False)

    gp.to_csv(OUT_DIR / "group_prime_summary.csv", index=False)
    st.to_csv(OUT_DIR / "senttype_prime_summary.csv", index=False)
    effects.to_csv(OUT_DIR / "bootstrap_effects.csv", index=False)
    coef.to_csv(OUT_DIR / "trial_model_coefficients.csv", index=False)
    cls.to_csv(OUT_DIR / "classification_metrics.csv", index=False)

    write_summary(data, subject, gp, effects, coef, cls)
    print(f"Wrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()
