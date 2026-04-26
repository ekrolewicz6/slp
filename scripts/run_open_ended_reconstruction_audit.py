"""Audit open-ended AphasiaBank interview speech for reconstruction safety."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import extract_target_records  # noqa: E402
from scripts.run_cross_prompt_content import chat_tokens  # noqa: E402
from scripts.run_error_aware_reconstruction_benchmark import extract_error_features  # noqa: E402
from src.analysis.review_grade import ensure_dir, pearson_safe  # noqa: E402

DEFAULT_OPEN_GROUPS = [
    "Speech",
    "Stroke",
    "Important_Event",
    "ImportantEvent",
    "Conversation",
    "Conversastion",
    "Routine",
    "Scary_Experience",
    "pleasant experience",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--segments-path",
        default="outputs/cross_prompt_content/task_segments.csv",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/open_ended_reconstruction_audit",
        type=Path,
    )
    parser.add_argument("--path-contains", default="/PWA/")
    parser.add_argument("--open-groups", default=",".join(DEFAULT_OPEN_GROUPS))
    parser.add_argument("--include-controls", action="store_true")
    parser.add_argument("--min-observed-tokens", default=1, type=int)
    return parser.parse_args()


def md_table(frame: pd.DataFrame, max_rows: int = 40) -> str:
    if frame.empty:
        return ""
    data = frame.head(max_rows).copy()
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            data[col] = data[col].astype(str)
    header = "| " + " | ".join(data.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
    body = ["| " + " | ".join(row.tolist()) + " |" for _, row in data.iterrows()]
    return "\n".join([header, sep] + body)


def parse_open_ended_par(path: Path, open_groups: set[str]) -> list[str]:
    """Return PAR utterance records from natural interview @G blocks."""
    utterances: list[str] = []
    current_speaker = ""
    current_group = ""
    current: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return utterances

    def flush() -> None:
        nonlocal current
        if current:
            utterances.append(" ".join(current))
            current = []

    for raw in lines:
        if raw.startswith("@G:"):
            flush()
            current_group = raw.split(":", 1)[1].strip()
            current_speaker = ""
            continue
        if raw.startswith("*") and ":" in raw:
            flush()
            speaker, payload = raw[1:].split(":", 1)
            current_speaker = speaker.strip()
            if current_speaker == "PAR" and current_group in open_groups:
                current = [payload.strip()]
            else:
                current = []
            continue
        if raw.startswith("\t") and current_speaker == "PAR" and current:
            current.append(raw.strip())
    else:
        flush()
    return utterances


def clean_text(text: str, include_targets: bool) -> str:
    return " ".join(chat_tokens(str(text), include_targets=include_targets))


def build_utterance_rows(args: argparse.Namespace) -> pd.DataFrame:
    segments = pd.read_csv(args.segments_path)
    meta_cols = [
        "transcript_id",
        "participant_id",
        "patient_root",
        "corpus",
        "subtype",
        "wab_aq",
        "is_control",
        "file_path",
    ]
    meta = segments[meta_cols].drop_duplicates("transcript_id").copy()
    meta["file_path"] = meta["file_path"].astype(str)
    if args.path_contains:
        meta = meta[meta["file_path"].str.contains(args.path_contains, regex=False)]
    if not args.include_controls:
        meta = meta[~meta["is_control"].astype(bool)]
    meta = meta[meta["file_path"].map(lambda p: Path(p).exists())].copy()
    open_groups = {g.strip() for g in args.open_groups.split(",") if g.strip()}

    rows = []
    for _, session in meta.iterrows():
        utterances = parse_open_ended_par(Path(str(session["file_path"])), open_groups)
        for idx, raw in enumerate(utterances):
            observed = clean_text(raw, include_targets=False)
            oracle = clean_text(raw, include_targets=True)
            observed_tokens = len(observed.split())
            if observed_tokens < args.min_observed_tokens:
                continue
            target_records = extract_target_records(raw)
            known_targets = [
                rec["target"] for rec in target_records if rec["target_status"] == "known"
            ]
            unknown_targets = [
                rec["error_code"] for rec in target_records if rec["target_status"] == "unknown"
            ]
            features = extract_error_features(raw, observed_tokens)
            rows.append(
                {
                    "utterance_id": f"{session['transcript_id']}::open::{idx:04d}",
                    "transcript_id": session["transcript_id"],
                    "participant_id": session["participant_id"],
                    "patient_root": session["patient_root"],
                    "corpus": session["corpus"],
                    "subtype": session["subtype"],
                    "wab_aq": session["wab_aq"],
                    "file_path": session["file_path"],
                    "utterance_index": idx,
                    "raw_transcript": raw,
                    "observed_clean_text": observed,
                    "oracle_clean_text": oracle,
                    "observed_n_tokens": observed_tokens,
                    "oracle_n_tokens": len(oracle.split()),
                    "known_targets": json.dumps(known_targets),
                    "unknown_target_error_codes": json.dumps(unknown_targets),
                    "known_target_count": len(known_targets),
                    "unknown_target_count": len(unknown_targets),
                    "target_token_gain": max(0, len(oracle.split()) - observed_tokens),
                    **features,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["safe_known_rewrite_candidate"] = (
        (out["known_reconstructable_error_count"] > 0)
        & (out["unknown_intent_error_count"] == 0)
    )
    out["needs_abstain_or_clarification"] = out["unknown_intent_error_count"] > 0
    out["has_any_error_tag"] = out["error_total"] > 0
    return out


def summarize_sessions(utterances: pd.DataFrame) -> pd.DataFrame:
    if utterances.empty:
        return pd.DataFrame()
    session = (
        utterances.groupby("transcript_id")
        .agg(
            participant_id=("participant_id", "first"),
            patient_root=("patient_root", "first"),
            corpus=("corpus", "first"),
            subtype=("subtype", "first"),
            wab_aq=("wab_aq", "mean"),
            n_open_ended_utterances=("utterance_id", "size"),
            observed_tokens=("observed_n_tokens", "sum"),
            error_total=("error_total", "sum"),
            known_reconstructable_error_count=("known_reconstructable_error_count", "sum"),
            unknown_intent_error_count=("unknown_intent_error_count", "sum"),
            target_token_gain=("target_token_gain", "sum"),
            safe_known_rewrite_utterances=("safe_known_rewrite_candidate", "sum"),
            abstain_or_clarify_utterances=("needs_abstain_or_clarification", "sum"),
        )
        .reset_index()
    )
    denom = session["observed_tokens"].clip(lower=1)
    for col in [
        "error_total",
        "known_reconstructable_error_count",
        "unknown_intent_error_count",
        "target_token_gain",
    ]:
        session[f"{col}_rate_100"] = 100.0 * session[col] / denom
    session["safe_known_rewrite_utterance_frac"] = (
        session["safe_known_rewrite_utterances"] / session["n_open_ended_utterances"].clip(lower=1)
    )
    session["abstain_or_clarify_utterance_frac"] = (
        session["abstain_or_clarify_utterances"] / session["n_open_ended_utterances"].clip(lower=1)
    )
    return session


def correlation_table(session: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for signal in [
        "error_total_rate_100",
        "known_reconstructable_error_count_rate_100",
        "unknown_intent_error_count_rate_100",
        "target_token_gain_rate_100",
        "safe_known_rewrite_utterance_frac",
        "abstain_or_clarify_utterance_frac",
        "n_open_ended_utterances",
        "observed_tokens",
    ]:
        rows.append(
            {
                "signal": signal,
                "n": int(session[["wab_aq", signal]].dropna().shape[0]),
                "r_wab_aq": pearson_safe(session[signal], session["wab_aq"]),
            }
        )
    return pd.DataFrame(rows).sort_values("r_wab_aq")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    utterances = build_utterance_rows(args)
    if utterances.empty:
        raise SystemExit("No open-ended utterances found.")
    sessions = summarize_sessions(utterances)
    correlations = correlation_table(sessions)
    by_subtype = (
        sessions.groupby("subtype")
        .agg(
            sessions=("transcript_id", "nunique"),
            mean_wab=("wab_aq", "mean"),
            mean_open_ended_utts=("n_open_ended_utterances", "mean"),
            error_rate_100=("error_total_rate_100", "mean"),
            known_rewrite_rate_100=("known_reconstructable_error_count_rate_100", "mean"),
            unknown_intent_rate_100=("unknown_intent_error_count_rate_100", "mean"),
            safe_rewrite_utterance_frac=("safe_known_rewrite_utterance_frac", "mean"),
            abstain_or_clarify_frac=("abstain_or_clarify_utterance_frac", "mean"),
        )
        .reset_index()
        .sort_values("unknown_intent_rate_100", ascending=False)
    )
    by_corpus = (
        sessions.groupby("corpus")
        .agg(
            sessions=("transcript_id", "nunique"),
            mean_wab=("wab_aq", "mean"),
            mean_open_ended_utts=("n_open_ended_utterances", "mean"),
            unknown_intent_rate_100=("unknown_intent_error_count_rate_100", "mean"),
            safe_rewrite_utterance_frac=("safe_known_rewrite_utterance_frac", "mean"),
        )
        .reset_index()
        .sort_values("sessions", ascending=False)
    )
    policy = pd.DataFrame(
        [
            {
                "policy_bucket": "safe_known_rewrite_candidate",
                "utterances": int(utterances["safe_known_rewrite_candidate"].sum()),
                "frac_utterances": float(utterances["safe_known_rewrite_candidate"].mean()),
            },
            {
                "policy_bucket": "needs_abstain_or_clarification",
                "utterances": int(utterances["needs_abstain_or_clarification"].sum()),
                "frac_utterances": float(utterances["needs_abstain_or_clarification"].mean()),
            },
            {
                "policy_bucket": "any_error_tag",
                "utterances": int(utterances["has_any_error_tag"].sum()),
                "frac_utterances": float(utterances["has_any_error_tag"].mean()),
            },
        ]
    )

    utterances.to_csv(out_dir / "open_ended_utterances.csv", index=False)
    sessions.to_csv(out_dir / "open_ended_session_summary.csv", index=False)
    correlations.to_csv(out_dir / "wab_correlations.csv", index=False)
    by_subtype.to_csv(out_dir / "by_subtype.csv", index=False)
    by_corpus.to_csv(out_dir / "by_corpus.csv", index=False)
    policy.to_csv(out_dir / "policy_buckets.csv", index=False)

    lines = [
        "# Open-Ended Reconstruction Audit",
        "",
        f"- Open-ended PAR utterances: {len(utterances)}",
        f"- Sessions: {sessions['transcript_id'].nunique()}",
        f"- Patients/roots: {sessions['patient_root'].nunique()}",
        f"- Corpora: {sessions['corpus'].nunique()}",
        f"- Utterances with any CHAT error tag: {int(utterances['has_any_error_tag'].sum())}",
        f"- Safe known-target rewrite candidates: {int(utterances['safe_known_rewrite_candidate'].sum())}",
        f"- Utterances needing abstain/clarification: {int(utterances['needs_abstain_or_clarification'].sum())}",
        "",
        "## Policy Buckets",
        "",
        md_table(policy.round(3)),
        "",
        "## WAB Correlations",
        "",
        md_table(correlations.round(3)),
        "",
        "## By Subtype",
        "",
        md_table(by_subtype.round(3), 40),
        "",
        "## By Corpus",
        "",
        md_table(by_corpus.round(3), 60),
        "",
        "## Interpretation",
        "",
        "This reproduces the open-ended interview setting used by recent GenAI "
        "aphasia reconstruction work, but separates utterances into safe known-"
        "target rewrite candidates versus unknown-intent cases that should trigger "
        "abstention or clarification. A useful assistant should not treat all CHAT "
        "error tags as equally reconstructable.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
