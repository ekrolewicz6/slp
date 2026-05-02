#!/usr/bin/env python3
"""Parse and analyze Calder et al. repeated grammar-probe supplements.

The Calder data are published as PDF supplemental tables rather than tidy CSVs.
This script extracts the repeated probe scores, converts them to proportions,
and asks the project-specific question: what would a treatment-response data
schema need to capture to learn target-specific response?
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
SUPP_DIR = ROOT / "data" / "external" / "literature" / "dld_treatment" / "calder_2020_figshare_supplements"
OUT_DIR = ROOT / "outputs" / "calder_repeated_probe_pilot"
PARSED_DIR = ROOT / "data" / "parsed" / "calder_repeated_probes"

RNG = np.random.default_rng(20260501)
N_BOOT = 5000


@dataclass(frozen=True)
class TableSpec:
    supplement: str
    filename: str
    modality: str
    target: str
    target_class: str
    context: str
    labels: tuple[str, ...]


B_ONLY = tuple([f"B{i}" for i in range(1, 11)] + ["Additional"])
A_B_A10 = tuple([f"A{i}" for i in range(1, 10)] + [f"B{i}" for i in range(2, 11)] + [f"A{i}" for i in range(10, 15)])
A_B_A11 = tuple([f"A{i}" for i in range(1, 10)] + [f"B{i}" for i in range(2, 11)] + [f"A{i}" for i in range(11, 16)])

TABLES: tuple[TableSpec, ...] = (
    TableSpec("S1", "LSHSS-19-00060calder_SuppS1.pdf", "expressive", "trained_past_tense", "trained", "within_session", B_ONLY),
    TableSpec("S2", "LSHSS-19-00060calder_SuppS2.pdf", "expressive", "trained_past_tense", "trained", "between_session", B_ONLY),
    TableSpec("S3", "LSHSS-19-00060calder_SuppS3.pdf", "expressive", "untrained_past_tense", "untrained_target", "probe", A_B_A10),
    TableSpec("S4", "LSHSS-19-00060calder_SuppS4.pdf", "expressive", "third_person_singular", "extension", "probe", A_B_A11),
    TableSpec("S7", "LSHSS-19-00060calder_SuppS7.pdf", "expressive", "possessive_s", "control", "probe", A_B_A11),
    TableSpec("S10", "LSHSS-19-00060calder_SuppS10.pdf", "grammaticality_judgment", "trained_past_tense", "trained", "within_session", B_ONLY),
    TableSpec("S11", "LSHSS-19-00060calder_SuppS11.pdf", "grammaticality_judgment", "trained_past_tense", "trained", "between_session", B_ONLY),
    TableSpec("S12", "LSHSS-19-00060calder_SuppS12.pdf", "grammaticality_judgment", "untrained_past_tense", "untrained_target", "probe", A_B_A11),
    TableSpec("S17", "LSHSS-19-00060calder_SuppS17.pdf", "grammaticality_judgment", "third_person_singular", "extension", "probe", A_B_A11),
    TableSpec("S20", "LSHSS-19-00060calder_SuppS20.pdf", "grammaticality_judgment", "possessive_s", "control", "probe", A_B_A11),
)


def pdftotext(path: Path) -> str:
    return subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)


def parse_score(token: str) -> tuple[float, float] | tuple[None, None]:
    token = token.strip()
    if token == "-":
        return (None, None)
    match = re.fullmatch(r"(\d+)/(\d+)", token)
    if not match:
        raise ValueError(f"Unexpected score token: {token!r}")
    return (float(match.group(1)), float(match.group(2)))


def phase_for_label(label: str) -> str:
    if label.startswith("B") or label == "Additional":
        return "intervention"
    if label.startswith("A"):
        number = int(label[1:])
        if number <= 9:
            return "baseline"
        return "maintenance"
    raise ValueError(f"Unknown label {label}")


def phase_order(label: str) -> int:
    if label == "Additional":
        return 99
    return int(label[1:])


def extract_rows(spec: TableSpec) -> list[dict]:
    text = pdftotext(SUPP_DIR / spec.filename)
    rows: list[dict] = []
    for line in text.splitlines():
        if not re.match(r"^P\d+\s+", line):
            continue
        tokens = line.split()
        participant = tokens[0]
        values = tokens[1:]
        if len(values) != len(spec.labels):
            raise ValueError(
                f"{spec.supplement} {participant}: expected {len(spec.labels)} values, got {len(values)}: {values}"
            )
        for idx, (label, token) in enumerate(zip(spec.labels, values), start=1):
            numerator, denominator = parse_score(token)
            rows.append(
                {
                    "supplement": spec.supplement,
                    "participant": participant,
                    "modality": spec.modality,
                    "target": spec.target,
                    "target_class": spec.target_class,
                    "context": spec.context,
                    "session_label": label,
                    "session_index_within_table": idx,
                    "phase": phase_for_label(label),
                    "phase_order": phase_order(label),
                    "numerator": numerator,
                    "denominator": denominator,
                    "score_prop": None if numerator is None else numerator / denominator,
                }
            )
    return rows


def lin_slope(g: pd.DataFrame) -> float:
    h = g.dropna(subset=["score_prop"])
    if len(h) < 2:
        return np.nan
    x = np.arange(len(h), dtype=float)
    return float(stats.linregress(x, h["score_prop"].to_numpy(dtype=float)).slope)


def cliff_delta(a: Iterable[float], b: Iterable[float]) -> float:
    baseline = np.asarray(list(a), dtype=float)
    intervention = np.asarray(list(b), dtype=float)
    baseline = baseline[np.isfinite(baseline)]
    intervention = intervention[np.isfinite(intervention)]
    if len(baseline) == 0 or len(intervention) == 0:
        return np.nan
    gt = sum(float(i > j) for i in intervention for j in baseline)
    lt = sum(float(i < j) for i in intervention for j in baseline)
    return (gt - lt) / (len(baseline) * len(intervention))


def ci(values: Iterable[float]) -> tuple[float, float]:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return (np.nan, np.nan)
    return tuple(np.quantile(arr, [0.025, 0.975]).tolist())


def phase_metrics(rows: pd.DataFrame) -> pd.DataFrame:
    metrics = []
    repeated = rows[rows["target_class"] != "trained"].copy()
    for keys, g in repeated.groupby(["participant", "modality", "target", "target_class"], sort=True):
        participant, modality, target, target_class = keys
        phase_means = g.groupby("phase")["score_prop"].mean()
        base = phase_means.get("baseline", np.nan)
        inter = phase_means.get("intervention", np.nan)
        maint = phase_means.get("maintenance", np.nan)
        baseline_rows = g[g["phase"] == "baseline"].dropna(subset=["score_prop"])
        intervention_rows = g[g["phase"] == "intervention"].dropna(subset=["score_prop"])
        maintenance_rows = g[g["phase"] == "maintenance"].dropna(subset=["score_prop"])
        metrics.append(
            {
                "participant": participant,
                "modality": modality,
                "target": target,
                "target_class": target_class,
                "n_baseline": len(baseline_rows),
                "n_intervention": len(intervention_rows),
                "n_maintenance": len(maintenance_rows),
                "baseline_mean": base,
                "intervention_mean": inter,
                "maintenance_mean": maint,
                "treatment_gain": inter - base,
                "maintenance_gain": maint - base,
                "baseline_slope": lin_slope(baseline_rows),
                "intervention_slope": lin_slope(intervention_rows),
                "maintenance_slope": lin_slope(maintenance_rows),
                "cliff_intervention_vs_baseline": cliff_delta(baseline_rows["score_prop"], intervention_rows["score_prop"]),
                "cliff_maintenance_vs_baseline": cliff_delta(baseline_rows["score_prop"], maintenance_rows["score_prop"]),
            }
        )
    return pd.DataFrame(metrics)


def trained_metrics(rows: pd.DataFrame) -> pd.DataFrame:
    metrics = []
    trained = rows[rows["target_class"] == "trained"].copy()
    for keys, g in trained.groupby(["participant", "modality", "context"], sort=True):
        participant, modality, context = keys
        h = g.dropna(subset=["score_prop"]).sort_values("session_index_within_table")
        early = h.head(3)["score_prop"].mean()
        late = h.tail(3)["score_prop"].mean()
        metrics.append(
            {
                "participant": participant,
                "modality": modality,
                "target": "trained_past_tense",
                "target_class": "trained",
                "context": context,
                "n_observations": len(h),
                "early_mean": early,
                "late_mean": late,
                "late_minus_early": late - early,
                "intervention_slope": lin_slope(h),
            }
        )
    return pd.DataFrame(metrics)


def aggregate_phase_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, g in metrics.groupby(["modality", "target_class", "target"], sort=True):
        modality, target_class, target = keys
        for metric in ["treatment_gain", "maintenance_gain", "cliff_intervention_vs_baseline", "cliff_maintenance_vs_baseline"]:
            vals = g[metric].dropna().to_numpy(dtype=float)
            if len(vals) == 0:
                continue
            boot = [np.mean(RNG.choice(vals, size=len(vals), replace=True)) for _ in range(N_BOOT)]
            low, high = ci(boot)
            rows.append(
                {
                    "modality": modality,
                    "target_class": target_class,
                    "target": target,
                    "metric": metric,
                    "n_participants": g["participant"].nunique(),
                    "mean": vals.mean(),
                    "median": np.median(vals),
                    "ci_low": low,
                    "ci_high": high,
                    "n_positive": int((vals > 0).sum()),
                    "n_gain_ge_0p20": int((vals >= 0.20).sum()),
                }
            )
    return pd.DataFrame(rows)


def aggregate_trained_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, g in metrics.groupby(["modality", "context"], sort=True):
        modality, context = keys
        vals = g["late_minus_early"].dropna().to_numpy(dtype=float)
        boot = [np.mean(RNG.choice(vals, size=len(vals), replace=True)) for _ in range(N_BOOT)]
        low, high = ci(boot)
        rows.append(
            {
                "modality": modality,
                "context": context,
                "n_participants": g["participant"].nunique(),
                "mean_late_minus_early": vals.mean(),
                "median_late_minus_early": np.median(vals),
                "ci_low": low,
                "ci_high": high,
                "n_positive": int((vals > 0).sum()),
                "n_gain_ge_0p20": int((vals >= 0.20).sum()),
            }
        )
    return pd.DataFrame(rows)


def paired_specificity(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for modality, g in metrics.groupby("modality", sort=True):
        for outcome in ["treatment_gain", "maintenance_gain", "cliff_intervention_vs_baseline", "cliff_maintenance_vs_baseline"]:
            pivot = g.pivot_table(index="participant", columns="target_class", values=outcome, aggfunc="mean")
            for target in ["untrained_target", "extension"]:
                if target not in pivot or "control" not in pivot:
                    continue
                diff = (pivot[target] - pivot["control"]).dropna().to_numpy(dtype=float)
                if len(diff) == 0:
                    continue
                boot = [np.mean(RNG.choice(diff, size=len(diff), replace=True)) for _ in range(N_BOOT)]
                low, high = ci(boot)
                try:
                    p_value = stats.wilcoxon(diff).pvalue
                except ValueError:
                    p_value = np.nan
                rows.append(
                    {
                        "modality": modality,
                        "comparison": f"{target}_minus_control",
                        "metric": outcome,
                        "n_participants": len(diff),
                        "mean_difference": diff.mean(),
                        "median_difference": np.median(diff),
                        "ci_low": low,
                        "ci_high": high,
                        "wilcoxon_p": p_value,
                        "n_positive": int((diff > 0).sum()),
                    }
                )
    return pd.DataFrame(rows)


def parse_audit(rows: pd.DataFrame) -> pd.DataFrame:
    return (
        rows.groupby(["supplement", "modality", "target", "target_class", "context"], as_index=False)
        .agg(
            participants=("participant", "nunique"),
            rows=("score_prop", "size"),
            nonmissing_scores=("score_prop", "count"),
            missing_scores=("score_prop", lambda s: int(s.isna().sum())),
            mean_score_prop=("score_prop", "mean"),
        )
        .sort_values("supplement")
    )


def write_summary(
    rows: pd.DataFrame,
    phase: pd.DataFrame,
    trained: pd.DataFrame,
    phase_agg: pd.DataFrame,
    trained_agg: pd.DataFrame,
    specificity: pd.DataFrame,
    audit: pd.DataFrame,
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def agg_value(modality: str, target_class: str, metric: str) -> pd.Series:
        hit = phase_agg[
            (phase_agg["modality"] == modality)
            & (phase_agg["target_class"] == target_class)
            & (phase_agg["metric"] == metric)
        ]
        return hit.iloc[0]

    exp_untrained = agg_value("expressive", "untrained_target", "maintenance_gain")
    exp_control = agg_value("expressive", "control", "maintenance_gain")
    gj_untrained = agg_value("grammaticality_judgment", "untrained_target", "maintenance_gain")
    gj_control = agg_value("grammaticality_judgment", "control", "maintenance_gain")
    trained_exp_between = trained_agg[
        (trained_agg["modality"] == "expressive") & (trained_agg["context"] == "between_session")
    ].iloc[0]
    spec_exp = specificity[
        (specificity["modality"] == "expressive")
        & (specificity["comparison"] == "untrained_target_minus_control")
        & (specificity["metric"] == "maintenance_gain")
    ].iloc[0]

    lines = [
        "# Calder Repeated-Probe Treatment-Response Pilot",
        "",
        "Source: Calder, S. D., Claessen, M., Ebbels, S., & Leitao, S. (2020). Explicit grammar intervention in young school-aged children with Developmental Language Disorder: An efficacy study using single-case experimental design. *Language, Speech, and Hearing Services in Schools*, 51(2), 298-316. https://doi.org/10.1044/2019_LSHSS-19-00060",
        "",
        "## Question",
        "",
        "This is the closest local public example of the treatment-response data structure Brian described: repeated probes, a specific target, dose, and extension/control measures. The project question is whether repeated probe curves can expose target-specific response rather than only pre/post group change.",
        "",
        "## Extraction",
        "",
        f"- Parsed {len(TABLES)} supplemental raw-score PDF tables into {rows.shape[0]} probe rows; {rows['score_prop'].notna().sum()} rows have usable numerator/denominator scores.",
        f"- Participants: {rows['participant'].nunique()} children with DLD.",
        "- Row-level extracted scores are written only to gitignored `data/parsed/calder_repeated_probes/`; committed outputs are aggregate summaries and derived response metrics.",
        "",
        "## Main Results",
        "",
        f"- Trained expressive past-tense probes improved across treatment sessions: between-session late-minus-early mean {trained_exp_between.mean_late_minus_early:.3f} (95% bootstrap CI {trained_exp_between.ci_low:.3f} to {trained_exp_between.ci_high:.3f}); {trained_exp_between.n_positive:.0f}/9 children improved.",
        f"- Expressive untrained past-tense maintenance gain averaged {exp_untrained['mean']:.3f} from baseline (95% CI {exp_untrained['ci_low']:.3f} to {exp_untrained['ci_high']:.3f}); control possessive-s maintenance gain averaged {exp_control['mean']:.3f} (95% CI {exp_control['ci_low']:.3f} to {exp_control['ci_high']:.3f}).",
        f"- Expressive target-specificity at maintenance, untrained past tense minus control, averaged {spec_exp.mean_difference:.3f} (95% CI {spec_exp.ci_low:.3f} to {spec_exp.ci_high:.3f}; Wilcoxon p={spec_exp.wilcoxon_p:.4f}).",
        f"- Grammaticality-judgment maintenance gains were smaller: untrained past tense {gj_untrained['mean']:.3f} vs control {gj_control['mean']:.3f}. This supports separating production and judgment/comprehension-like probes rather than assuming one treatment response axis.",
        "",
        "## Interpretation for Our Program",
        "",
        "- This is the correct data shape for treatment learning: target, contrast target, dose/session order, repeated probes, and maintenance.",
        "- A clinical model should learn curves and target specificity, not just diagnose DLD or predict a single post-test score.",
        "- The small single-case design is valuable mechanistically but insufficient for broad treatment allocation. It should be used as a schema template and a calibration example for future prospective collection.",
        "- The strongest next data need is not another classifier; it is paired natural-speech/structured-probe/treatment-dose data with enough children and targets to model heterogeneous response.",
        "",
        "## Output Files",
        "",
        "- `parse_audit.csv`: extracted supplemental table inventory.",
        "- `aggregate_phase_metrics.csv`: baseline-to-intervention and baseline-to-maintenance response summaries for untrained, extension, and control probes.",
        "- `aggregate_trained_metrics.csv`: early-to-late trained-probe change during intervention.",
        "- `target_specificity_metrics.csv`: paired untrained/extension minus control contrasts.",
        "- `summary.md`: this interpretation.",
        "",
        "## Limits",
        "",
        "- Scores were extracted from PDF supplemental tables, not original CSVs; the parser validates row widths but should be manually checked before publication.",
        "- We intentionally do not claim causal effects beyond the original single-case design.",
        "- There are no natural speech samples here, so this cannot validate our full natural-plus-structured battery.",
        "",
    ]
    (OUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    extracted: list[dict] = []
    for spec in TABLES:
        extracted.extend(extract_rows(spec))
    rows = pd.DataFrame(extracted)
    rows["score_prop"] = pd.to_numeric(rows["score_prop"], errors="coerce")

    audit = parse_audit(rows)
    phase = phase_metrics(rows)
    trained = trained_metrics(rows)
    phase_agg = aggregate_phase_metrics(phase)
    trained_agg = aggregate_trained_metrics(trained)
    specificity = paired_specificity(phase)

    rows.to_csv(PARSED_DIR / "extracted_probe_rows.csv", index=False)
    phase.to_csv(PARSED_DIR / "participant_phase_metrics.csv", index=False)
    trained.to_csv(PARSED_DIR / "participant_trained_metrics.csv", index=False)

    audit.to_csv(OUT_DIR / "parse_audit.csv", index=False)
    phase_agg.to_csv(OUT_DIR / "aggregate_phase_metrics.csv", index=False)
    trained_agg.to_csv(OUT_DIR / "aggregate_trained_metrics.csv", index=False)
    specificity.to_csv(OUT_DIR / "target_specificity_metrics.csv", index=False)

    write_summary(rows, phase, trained, phase_agg, trained_agg, specificity, audit)
    print(f"Wrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()
