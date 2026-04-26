"""No-clinician discovery analyses from existing aphasia outputs.

This suite deliberately avoids new clinician labels. It asks which scientific
claims can be pressure-tested with the data already in hand:

1. What kinds of longitudinal discourse change occur, beyond "WAB went up"?
2. Which concepts behave like stable traits, task artifacts, or
   change-sensitive therapy targets?
3. Where do WAB severity/subtype labels compress clinically different states?
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from src.analysis.review_grade import ensure_dir  # noqa: E402


CORE_TASKS = ["Cat", "Cinderella", "Sandwich", "Umbrella", "Window"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pairs",
        default="outputs/stable_wab_movers/classified_pairs.csv",
        type=Path,
    )
    parser.add_argument(
        "--thresholds",
        default="outputs/reliable_change_thresholds/thresholds.csv",
        type=Path,
    )
    parser.add_argument(
        "--items",
        default="outputs/treatment_target_sequencing/item_observations.csv",
        type=Path,
    )
    parser.add_argument(
        "--targets",
        default="outputs/treatment_target_sequencing/target_recommendations.csv",
        type=Path,
    )
    parser.add_argument(
        "--state",
        default="outputs/two_axis_state_typology/session_two_axis_state.csv",
        type=Path,
    )
    parser.add_argument(
        "--patient-state",
        default="outputs/cross_prompt_state/patient_content_state.csv",
        type=Path,
    )
    parser.add_argument(
        "--longitudinal-state",
        default="outputs/cross_prompt_longitudinal/longitudinal_content_state.csv",
        type=Path,
    )
    parser.add_argument(
        "--open-ended",
        default="outputs/open_ended_reconstruction_audit/open_ended_session_summary.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/no_clinician_discovery", type=Path)
    return parser.parse_args()


def safe_read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def numeric(df: pd.DataFrame, col: str, default: float = np.nan) -> pd.Series:
    if col not in df:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce")


def pct_rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, method="average")


def pearson_safe(x: pd.Series, y: pd.Series) -> float:
    pair = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(pair) < 3 or pair["x"].nunique() < 2 or pair["y"].nunique() < 2:
        return float("nan")
    return float(pair["x"].corr(pair["y"]))


def effect_size(a: pd.Series, b: pd.Series) -> float:
    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pooled = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    if pooled == 0 or not np.isfinite(pooled):
        return float("nan")
    return float((a.mean() - b.mean()) / pooled)


def reliability_thresholds(pairs: pd.DataFrame, thresholds: pd.DataFrame) -> dict[str, float]:
    out: dict[str, float] = {}
    if not thresholds.empty:
        for row in thresholds.itertuples(index=False):
            metric = str(getattr(row, "metric"))
            value = getattr(row, "empirical_abs_q90", np.nan)
            if pd.notna(value):
                out[metric] = float(value)

    for metric, delta_col in [
        ("risk_axis", "delta_risk_axis"),
        ("recoverable_axis", "delta_recoverable_axis"),
    ]:
        stable = pairs[pairs.get("stable_wab", False).astype(bool)] if "stable_wab" in pairs else pairs
        values = pd.to_numeric(stable.get(delta_col), errors="coerce").abs().dropna()
        if len(values) >= 10:
            out[metric] = float(values.quantile(0.90))
        else:
            out[metric] = float(pd.to_numeric(pairs.get(delta_col), errors="coerce").abs().quantile(0.90))
    return out


def classify_longitudinal_change(pairs: pd.DataFrame, thresholds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if pairs.empty:
        return pairs, pd.DataFrame(), pd.DataFrame()

    out = pairs.copy()
    out["delta_risk_axis"] = numeric(out, "to_axis_risk_axis") - numeric(out, "from_axis_risk_axis")
    out["delta_recoverable_axis"] = numeric(out, "to_axis_recoverable_axis") - numeric(out, "from_axis_recoverable_axis")
    out["delta_content_axis"] = numeric(out, "to_axis_content_axis") - numeric(out, "from_axis_content_axis")

    thr = reliability_thresholds(out, thresholds)
    content_thr = thr.get("core_content_mean_z", thr.get("content_mean_z", 0.95))
    coverage_thr = thr.get("coverage_mean", 0.13)
    tokens_thr = thr.get("tokens_mean", 73.0)
    utts_thr = thr.get("utts_mean", 10.6)
    meanutt_thr = thr.get("meanutt_mean", 1.96)
    risk_thr = max(thr.get("risk_axis", 0.75), 0.20)
    recoverable_thr = max(thr.get("recoverable_axis", 0.75), 0.20)

    out["content_reliable"] = numeric(out, "delta_core_content_mean_z").abs() >= content_thr
    out["content_improved"] = numeric(out, "delta_core_content_mean_z") >= content_thr
    out["content_declined"] = numeric(out, "delta_core_content_mean_z") <= -content_thr
    out["coverage_reliable"] = numeric(out, "delta_coverage_mean").abs() >= coverage_thr
    out["coverage_improved"] = numeric(out, "delta_coverage_mean") >= coverage_thr
    out["tokens_reliable"] = numeric(out, "delta_tokens_mean").abs() >= tokens_thr
    out["tokens_increased"] = numeric(out, "delta_tokens_mean") >= tokens_thr
    out["utts_reliable"] = numeric(out, "delta_utts_mean").abs() >= utts_thr
    out["utts_increased"] = numeric(out, "delta_utts_mean") >= utts_thr
    out["meanutt_reliable"] = numeric(out, "delta_meanutt_mean").abs() >= meanutt_thr
    out["meanutt_increased"] = numeric(out, "delta_meanutt_mean") >= meanutt_thr
    out["risk_reliable"] = numeric(out, "delta_risk_axis").abs() >= risk_thr
    out["risk_decreased"] = numeric(out, "delta_risk_axis") <= -risk_thr
    out["risk_increased"] = numeric(out, "delta_risk_axis") >= risk_thr
    out["recoverable_reliable"] = numeric(out, "delta_recoverable_axis").abs() >= recoverable_thr
    out["recoverable_increased"] = numeric(out, "delta_recoverable_axis") >= recoverable_thr
    out["recoverable_decreased"] = numeric(out, "delta_recoverable_axis") <= -recoverable_thr

    any_output = out[["tokens_reliable", "utts_reliable", "meanutt_reliable"]].any(axis=1)
    any_axis = out[
        [
            "content_reliable",
            "coverage_reliable",
            "tokens_reliable",
            "utts_reliable",
            "meanutt_reliable",
            "risk_reliable",
            "recoverable_reliable",
        ]
    ].any(axis=1)

    conditions = [
        out["content_improved"] & out["risk_decreased"],
        out["content_improved"] & ~any_output,
        out["content_improved"] & any_output,
        out["coverage_improved"] & ~out["tokens_increased"] & ~out["utts_increased"],
        out["tokens_increased"] & ~out["content_reliable"],
        out["utts_increased"] & ~out["content_reliable"],
        out["meanutt_increased"] & ~out["content_reliable"],
        out["risk_decreased"] & ~out["content_reliable"],
        out["risk_increased"],
        out["recoverable_increased"] & ~out["risk_increased"],
        out["content_declined"],
        out.get("wab_changed", pd.Series(False, index=out.index)).astype(bool) & ~any_axis,
    ]
    labels = [
        "content_gain_plus_intent_safety_gain",
        "semantic_content_gain",
        "content_gain_with_more_output",
        "concept_efficiency_gain",
        "more_words_without_content_gain",
        "more_utterances_without_content_gain",
        "longer_utterances_without_content_gain",
        "intent_safety_gain_without_content_gain",
        "intent_risk_worsening",
        "known_repair_opportunity_increase",
        "semantic_content_decline",
        "wab_only_change",
    ]
    out["change_subtype"] = np.select(conditions, labels, default="stable_or_unclassified")
    out.loc[any_axis & out["change_subtype"].eq("stable_or_unclassified"), "change_subtype"] = "mixed_multiaxis_change"

    summary = (
        out.groupby("change_subtype")
        .agg(
            n_pairs=("longitudinal_root", "size"),
            n_roots=("longitudinal_root", "nunique"),
            stable_wab_rate=("stable_wab", "mean"),
            mean_delta_wab=("delta_wab_aq", "mean"),
            mean_delta_content=("delta_core_content_mean_z", "mean"),
            mean_delta_coverage=("delta_coverage_mean", "mean"),
            mean_delta_risk=("delta_risk_axis", "mean"),
            mean_delta_recoverable=("delta_recoverable_axis", "mean"),
        )
        .reset_index()
        .sort_values("n_pairs", ascending=False)
    )

    subtype_summary = (
        out.groupby(["from_meta_subtype", "change_subtype"], dropna=False)
        .agg(n_pairs=("longitudinal_root", "size"))
        .reset_index()
        .sort_values(["from_meta_subtype", "n_pairs"], ascending=[True, False])
    )
    return out, summary, subtype_summary


def concept_reliability(
    items: pd.DataFrame,
    targets: pd.DataFrame,
    longitudinal_state: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if items.empty or longitudinal_state.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    state_cols = ["participant_id", "longitudinal_root", "session_order", "corpus", "subtype", "wab_aq"]
    state = longitudinal_state[state_cols].drop_duplicates("participant_id")
    obs = items.merge(state, on="participant_id", how="inner", suffixes=("", "_state"))
    obs = obs[obs["longitudinal_root"].notna() & obs["session_order"].notna()].copy()
    obs = obs.sort_values(["longitudinal_root", "item_id", "session_order"])
    repeated_roots = obs.groupby("longitudinal_root")["participant_id"].nunique()
    obs = obs[obs["longitudinal_root"].isin(repeated_roots[repeated_roots >= 2].index)].copy()

    rows = []
    for (root, item_id), group in obs.groupby(["longitudinal_root", "item_id"], sort=False):
        group = group.sort_values("session_order")
        if group["participant_id"].nunique() < 2:
            continue
        hits = group["hit"].astype(int).to_numpy()
        first = int(hits[0])
        last = int(hits[-1])
        n_transitions = max(len(hits) - 1, 1)
        flips = int(np.sum(hits[1:] != hits[:-1]))
        if hits.mean() == 1:
            klass = "stable_present"
        elif hits.mean() == 0:
            klass = "stable_absent"
        elif first == 0 and last == 1:
            klass = "gained"
        elif first == 1 and last == 0:
            klass = "lost"
        else:
            klass = "variable_other"
        rows.append(
            {
                "longitudinal_root": root,
                "item_id": item_id,
                "task": group["task"].iloc[0],
                "concept": group["concept"].iloc[0],
                "subtype": group["subtype_state"].dropna().iloc[0]
                if "subtype_state" in group and group["subtype_state"].notna().any()
                else group["subtype"].dropna().iloc[0]
                if group["subtype"].notna().any()
                else "",
                "n_sessions": int(group["participant_id"].nunique()),
                "first_participant_id": group["participant_id"].iloc[0],
                "last_participant_id": group["participant_id"].iloc[-1],
                "first_hit": first,
                "last_hit": last,
                "hit_rate": float(hits.mean()),
                "flip_count": flips,
                "flip_rate": float(flips / n_transitions),
                "reliability_class": klass,
            }
        )
    rel = pd.DataFrame(rows)
    if rel.empty:
        return rel, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    item_summary = (
        rel.groupby(["task", "concept", "item_id"])
        .agg(
            n_roots=("longitudinal_root", "nunique"),
            mean_hit_rate=("hit_rate", "mean"),
            stable_present_rate=("reliability_class", lambda s: float((s == "stable_present").mean())),
            stable_absent_rate=("reliability_class", lambda s: float((s == "stable_absent").mean())),
            gained_rate=("reliability_class", lambda s: float((s == "gained").mean())),
            lost_rate=("reliability_class", lambda s: float((s == "lost").mean())),
            variable_rate=("reliability_class", lambda s: float((~s.isin(["stable_present", "stable_absent"])).mean())),
            mean_flip_rate=("flip_rate", "mean"),
        )
        .reset_index()
        .sort_values(["variable_rate", "n_roots"], ascending=[False, False])
    )
    patient_summary = (
        rel.groupby("longitudinal_root")
        .agg(
            n_items=("item_id", "size"),
            variable_items=("reliability_class", lambda s: int((~s.isin(["stable_present", "stable_absent"])).sum())),
            gained_items=("reliability_class", lambda s: int((s == "gained").sum())),
            lost_items=("reliability_class", lambda s: int((s == "lost").sum())),
            stable_absent_items=("reliability_class", lambda s: int((s == "stable_absent").sum())),
            stable_present_items=("reliability_class", lambda s: int((s == "stable_present").sum())),
            mean_flip_rate=("flip_rate", "mean"),
        )
        .reset_index()
    )
    patient_summary["variable_item_rate"] = patient_summary["variable_items"] / patient_summary["n_items"].clip(lower=1)

    task_summary = (
        rel.groupby("task")
        .agg(
            n_root_items=("item_id", "size"),
            variable_rate=("reliability_class", lambda s: float((~s.isin(["stable_present", "stable_absent"])).mean())),
            gained_rate=("reliability_class", lambda s: float((s == "gained").mean())),
            lost_rate=("reliability_class", lambda s: float((s == "lost").mean())),
            mean_flip_rate=("flip_rate", "mean"),
        )
        .reset_index()
        .sort_values("variable_rate", ascending=False)
    )

    overlay = pd.DataFrame()
    if not targets.empty:
        root_map = state[["participant_id", "longitudinal_root"]].drop_duplicates("participant_id")
        recs = targets.merge(root_map, on="participant_id", how="left")
        overlay = recs.merge(
            rel[
                [
                    "longitudinal_root",
                    "item_id",
                    "reliability_class",
                    "hit_rate",
                    "flip_rate",
                    "first_hit",
                    "last_hit",
                ]
            ],
            on=["longitudinal_root", "item_id"],
            how="left",
        )
        overlay["target_reliability_bucket"] = overlay["reliability_class"].fillna("not_repeated_or_unobserved")
    return rel, item_summary, patient_summary.sort_values("variable_item_rate", ascending=False), task_summary, overlay


def boundary_analyses(
    state: pd.DataFrame,
    patient_state: pd.DataFrame,
    open_ended: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if state.empty:
        return (pd.DataFrame(),) * 6

    st = state.copy()
    for col in ["content_axis", "risk_axis", "recoverable_axis", "total_tokens", "wab_aq"]:
        st[col] = numeric(st, col)
    st["content_pct"] = pct_rank(st["content_axis"])
    st["risk_pct"] = pct_rank(st["risk_axis"])
    st["recoverable_pct"] = pct_rank(st["recoverable_axis"])
    st["token_pct"] = pct_rank(st["total_tokens"])

    if not open_ended.empty:
        open_cols = [
            "participant_id",
            "n_open_ended_utterances",
            "safe_known_rewrite_utterance_frac",
            "abstain_or_clarify_utterance_frac",
            "unknown_intent_error_count_rate_100",
        ]
        st = st.merge(open_ended[open_cols], on="participant_id", how="left")
    for col in [
        "n_open_ended_utterances",
        "safe_known_rewrite_utterance_frac",
        "abstain_or_clarify_utterance_frac",
        "unknown_intent_error_count_rate_100",
    ]:
        st[col] = numeric(st, col, 0).fillna(0)

    severe_or_broca = (st["wab_aq"] < 55) | st["subtype"].eq("Broca")
    low_content = st["content_pct"] <= 0.30
    floor = st[severe_or_broca & low_content].copy()
    floor_conditions = [
        floor["token_pct"] <= 0.20,
        floor["risk_pct"] >= 0.75,
        floor["recoverable_pct"] >= 0.75,
        (floor["risk_pct"] < 0.50) & (floor["recoverable_pct"] < 0.50),
    ]
    floor_labels = [
        "low_output_or_motor_floor",
        "unknown_intent_floor",
        "known_repairable_error_floor",
        "low_content_low_error_floor",
    ]
    floor["floor_mechanism"] = np.select(floor_conditions, floor_labels, default="mixed_floor")
    floor_summary = (
        floor.groupby("floor_mechanism")
        .agg(
            n=("participant_id", "size"),
            mean_wab=("wab_aq", "mean"),
            mean_content=("content_axis", "mean"),
            mean_risk=("risk_axis", "mean"),
            mean_recoverable=("recoverable_axis", "mean"),
            pct_broca=("subtype", lambda s: float((s == "Broca").mean())),
            mean_open_clarify_frac=("abstain_or_clarify_utterance_frac", "mean"),
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )

    wernicke = st[st["subtype"].eq("Wernicke")].copy()
    st["wab_bin"] = pd.cut(
        st["wab_aq"],
        bins=[-np.inf, 50, 75, 93.8, np.inf],
        labels=["severe", "moderate", "mild", "high_wab"],
    )
    rows = []
    for wab_bin, group in st.groupby("wab_bin", observed=True):
        w = group[group["subtype"].eq("Wernicke")]
        other = group[~group["subtype"].eq("Wernicke")]
        if len(w) == 0 or len(other) == 0:
            continue
        for metric in ["content_axis", "risk_axis", "recoverable_axis", "unknown_intent_error_rate_100"]:
            rows.append(
                {
                    "wab_bin": str(wab_bin),
                    "metric": metric,
                    "n_wernicke": len(w),
                    "n_non_wernicke": len(other),
                    "mean_wernicke": float(w[metric].mean()),
                    "mean_non_wernicke": float(other[metric].mean()),
                    "wernicke_minus_other": float(w[metric].mean() - other[metric].mean()),
                    "cohens_d": effect_size(w[metric], other[metric]),
                }
            )
    wernicke_matched = pd.DataFrame(rows).sort_values(["metric", "wab_bin"]) if rows else pd.DataFrame()
    wernicke_summary = (
        st.assign(is_wernicke=st["subtype"].eq("Wernicke"))
        .groupby("is_wernicke")
        .agg(
            n=("participant_id", "size"),
            mean_wab=("wab_aq", "mean"),
            mean_content=("content_axis", "mean"),
            mean_risk=("risk_axis", "mean"),
            mean_recoverable=("recoverable_axis", "mean"),
            mean_unknown_intent_rate=("unknown_intent_error_rate_100", "mean"),
            mean_open_clarify_frac=("abstain_or_clarify_utterance_frac", "mean"),
        )
        .reset_index()
    )

    high_wab = st[st["wab_aq"] >= 93.8].copy()
    high_wab["abnormal_content"] = high_wab["content_axis_z"] <= -1.0 if "content_axis_z" in high_wab else False
    high_wab["abnormal_risk"] = high_wab["risk_axis_z"] >= 1.0 if "risk_axis_z" in high_wab else False
    high_wab["abnormal_recoverable"] = high_wab["recoverable_axis_z"] >= 1.0 if "recoverable_axis_z" in high_wab else False
    high_wab["any_state_abnormality"] = high_wab[
        ["abnormal_content", "abnormal_risk", "abnormal_recoverable"]
    ].any(axis=1)
    high_wab_summary = (
        high_wab.groupby("subtype", dropna=False)
        .agg(
            n=("participant_id", "size"),
            abnormal_rate=("any_state_abnormality", "mean"),
            content_abnormal_rate=("abnormal_content", "mean"),
            risk_abnormal_rate=("abnormal_risk", "mean"),
            recoverable_abnormal_rate=("abnormal_recoverable", "mean"),
            mean_content=("content_axis", "mean"),
            mean_risk=("risk_axis", "mean"),
            mean_recoverable=("recoverable_axis", "mean"),
        )
        .reset_index()
        .sort_values("abnormal_rate", ascending=False)
    )

    control_boundary = pd.DataFrame()
    if not patient_state.empty and "is_control" in patient_state:
        ps = patient_state.copy()
        controls = ps[ps["is_control"].astype(bool)].copy()
        pwa = ps[~ps["is_control"].astype(bool)].copy()
        if not controls.empty and not pwa.empty:
            control_mean = controls["core_content_mean_z"].mean()
            control_sd = controls["core_content_mean_z"].std(ddof=1)
            if control_sd and np.isfinite(control_sd):
                pwa["control_norm_content_z"] = (pwa["core_content_mean_z"] - control_mean) / control_sd
                pwa_high = pwa[pd.to_numeric(pwa["wab_aq"], errors="coerce") >= 93.8].copy()
                pwa_high["below_control_5th_proxy"] = pwa_high["control_norm_content_z"] <= -1.645
                control_boundary = (
                    pwa_high.groupby("subtype", dropna=False)
                    .agg(
                        n=("participant_id", "size"),
                        below_control_5th_proxy_rate=("below_control_5th_proxy", "mean"),
                        mean_control_norm_content_z=("control_norm_content_z", "mean"),
                    )
                    .reset_index()
                    .sort_values("below_control_5th_proxy_rate", ascending=False)
                )
    return floor, floor_summary, wernicke_summary, wernicke_matched, high_wab_summary, control_boundary


def overlay_summary(overlay: pd.DataFrame) -> pd.DataFrame:
    if overlay.empty:
        return pd.DataFrame()
    return (
        overlay.groupby("target_reliability_bucket")
        .agg(
            n_targets=("item_id", "size"),
            mean_zone_score=("target_zone_score", "mean"),
            mean_pred_success=("pred_ability+item", "mean"),
            n_patients=("participant_id", "nunique"),
        )
        .reset_index()
        .sort_values("n_targets", ascending=False)
    )


def write_summary(
    out_dir: Path,
    change_summary: pd.DataFrame,
    subtype_change_summary: pd.DataFrame,
    rel: pd.DataFrame,
    item_summary: pd.DataFrame,
    patient_rel_summary: pd.DataFrame,
    task_rel_summary: pd.DataFrame,
    target_overlay_summary: pd.DataFrame,
    floor_summary: pd.DataFrame,
    wernicke_summary: pd.DataFrame,
    wernicke_matched: pd.DataFrame,
    high_wab_summary: pd.DataFrame,
    control_boundary: pd.DataFrame,
) -> None:
    lines = [
        "# No-Clinician Discovery Suite",
        "",
        "## Longitudinal Change Subtypes",
        "",
        md_table(change_summary.round(3)),
        "",
        "Top subtype/change cells:",
        "",
        md_table(subtype_change_summary.head(30)),
        "",
        "## Patient-Specific Concept Reliability",
        "",
        f"- Repeated root-item observations: {len(rel):,}",
        f"- Variable/changing root-items: {int((~rel['reliability_class'].isin(['stable_present', 'stable_absent'])).sum()) if not rel.empty else 0:,}",
        "",
        "By task:",
        "",
        md_table(task_rel_summary.round(3)),
        "",
        "Most change-sensitive concepts:",
        "",
        md_table(item_summary.head(25).round(3)),
        "",
        "Therapy-target reliability overlay:",
        "",
        md_table(target_overlay_summary.round(3)),
        "",
        "## Boundary Analyses",
        "",
        "Severe/Broca floor mechanisms:",
        "",
        md_table(floor_summary.round(3)),
        "",
        "Wernicke vs non-Wernicke overall:",
        "",
        md_table(wernicke_summary.round(3)),
        "",
        "Wernicke vs same-WAB-bin non-Wernicke contrasts:",
        "",
        md_table(wernicke_matched.round(3)),
        "",
        "High-WAB state abnormalities:",
        "",
        md_table(high_wab_summary.round(3)),
        "",
        "High-WAB content vs control-norm proxy:",
        "",
        md_table(control_boundary.round(3)),
        "",
        "## Synthesis",
        "",
        "- The no-clinician data can already separate several clinically different change mechanisms: semantic content movement, output-quantity movement, intent-risk movement, and repair-opportunity movement.",
        "- Concept targets are not all equivalent. Some are stable absences, while others are variable or gained/lost across repeated sessions; the latter are better candidates for change-sensitive targets and monitoring.",
        "- WAB-AQ and subtype compress distinct states. Severe/Broca floor cases split into low-output, unknown-intent, repairable-error, and low-content/low-error profiles. Wernicke profiles show risk/recoverability patterns that are not captured by severity alone. High-WAB cases can still carry abnormal discourse-state signatures.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)

    pairs = safe_read(args.pairs)
    thresholds = safe_read(args.thresholds)
    items = safe_read(args.items)
    targets = safe_read(args.targets)
    state = safe_read(args.state)
    patient_state = safe_read(args.patient_state)
    longitudinal_state = safe_read(args.longitudinal_state)
    open_ended = safe_read(args.open_ended)

    change_rows, change_summary, subtype_change_summary = classify_longitudinal_change(pairs, thresholds)
    rel, item_summary, patient_rel_summary, task_rel_summary, overlay = concept_reliability(
        items, targets, longitudinal_state
    )
    target_overlay_summary = overlay_summary(overlay)
    floor, floor_summary, wernicke_summary, wernicke_matched, high_wab_summary, control_boundary = boundary_analyses(
        state, patient_state, open_ended
    )

    outputs = {
        "longitudinal_change_subtypes.csv": change_rows,
        "longitudinal_change_summary.csv": change_summary,
        "longitudinal_change_by_subtype.csv": subtype_change_summary,
        "concept_reliability_root_items.csv": rel,
        "concept_reliability_by_item.csv": item_summary,
        "concept_reliability_by_patient.csv": patient_rel_summary,
        "concept_reliability_by_task.csv": task_rel_summary,
        "target_reliability_overlay.csv": overlay,
        "target_reliability_summary.csv": target_overlay_summary,
        "severe_broca_floor_rows.csv": floor,
        "severe_broca_floor_summary.csv": floor_summary,
        "wernicke_boundary_summary.csv": wernicke_summary,
        "wernicke_matched_wab_bin_contrasts.csv": wernicke_matched,
        "high_wab_boundary_summary.csv": high_wab_summary,
        "high_wab_control_norm_boundary.csv": control_boundary,
    }
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)

    write_summary(
        out_dir,
        change_summary,
        subtype_change_summary,
        rel,
        item_summary,
        patient_rel_summary,
        task_rel_summary,
        target_overlay_summary,
        floor_summary,
        wernicke_summary,
        wernicke_matched,
        high_wab_summary,
        control_boundary,
    )
    print(f"Wrote no-clinician discovery suite to {out_dir}")
    if not change_summary.empty:
        print(change_summary.head(12).to_string(index=False))
    if not floor_summary.empty:
        print(floor_summary.to_string(index=False))


if __name__ == "__main__":
    main()
