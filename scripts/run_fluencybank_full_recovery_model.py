"""Full FluencyBank transcript recovery and early-movement model.

This script is the first replication-grade pass after full FluencyBank
transcript access was unlocked. It parses all local FluencyBank CHAT files,
audits which corpora expose recovered/persistent endpoints, extracts transcript
features, and tests whether early within-child movement improves
recovery/persistence prediction beyond earliest-session state.

Participant/session-level rows are written under gitignored ``data/parsed``.
Only aggregate summaries and model metrics are written under ``outputs``.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from scripts.run_fluencybank_purdue_recovery_pilot import (  # noqa: E402
    age_to_months,
    clean_numeric,
    match_demographic,
    norm_id,
    read_demographics,
)
from src.features.extractors import extract_features  # noqa: E402


RAW_DIR = Path("data/raw/fluencybank")
OUT_DIR = Path("outputs/fluencybank_full_recovery_model")
PARSED_DIR = Path("data/parsed/fluencybank")
TALKBANK_EXPORT = Path("data/external/fluencybank/TalkBankDB_transcripts.tsv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--parsed-dir", type=Path, default=PARSED_DIR)
    parser.add_argument("--min-utterances", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--permutations", type=int, default=200)
    parser.add_argument("--bootstraps", type=int, default=1000)
    return parser.parse_args()


def safe_float(value: object) -> float:
    if value is None:
        return np.nan
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"nan", "na", "n/a", "no data", "."}:
        return np.nan
    return clean_numeric(text)


def parse_age_any(text: object) -> float:
    if text is None:
        return np.nan
    value = str(text).strip()
    if not value or value.lower() in {"nan", "no data", "."}:
        return np.nan
    direct = age_to_months(value)
    if not math.isnan(direct):
        return direct
    match = re.search(r"\b(?:ca|age)\s*[:=]\s*(\d+\s*;\s*\d+)", value, flags=re.I)
    if match:
        return age_to_months(match.group(1))
    return np.nan


def read_talkbank_export(path: Path) -> pd.DataFrame:
    names = ["path", "id", "lang", "modality", "extra", "doi", "design", "task", "group", "note"]
    df = pd.read_csv(path, sep="\t", header=None, names=names)
    df = df[df["path"].astype(str).str.startswith("fluency/")].copy()
    return df


def parse_header(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    header_lines = [line for line in lines if line.startswith("@")]
    tier_counts = Counter()
    for line in lines:
        if line.startswith("*") and ":" in line[:10]:
            tier_counts[line[1 : line.index(":")]] += 1

    id_rows: dict[str, list[str]] = {}
    for line in header_lines:
        if line.startswith("@ID:"):
            parts = line[4:].strip().split("|")
            if len(parts) >= 3:
                id_rows[parts[2]] = parts

    target_candidates = ["CHI", "PAR", "SUB", "SPK", "ADU"]
    target = ""
    for candidate in target_candidates:
        if tier_counts.get(candidate, 0) > 0:
            target = candidate
            break
    if not target and tier_counts:
        target = tier_counts.most_common(1)[0][0]

    age = np.nan
    sex = ""
    group = ""
    if target in id_rows:
        parts = id_rows[target]
        if len(parts) >= 4:
            age = parse_age_any(parts[3])
        if len(parts) >= 5:
            sex = str(parts[4]).strip()
        if len(parts) >= 6:
            group = str(parts[5]).strip()

    media = ""
    media_type = ""
    types = ""
    date = ""
    comment_text = []
    for line in header_lines:
        if line.startswith("@Media:"):
            media_payload = line.split(":", 1)[1].strip()
            media = media_payload.split(",", 1)[0].strip()
            media_type = media_payload.split(",", 1)[1].strip() if "," in media_payload else ""
        elif line.startswith("@Types:"):
            types = line.split(":", 1)[1].strip()
        elif line.startswith("@Date:"):
            date = line.split(":", 1)[1].strip()
        elif line.startswith("@Comment:"):
            comment_text.append(line.split(":", 1)[1].strip())

    if math.isnan(age):
        age = parse_age_any(" ".join(comment_text))
    if not sex:
        match = re.search(r"\bgender\s*[:=]\s*([a-zA-Z]+)", " ".join(comment_text), flags=re.I)
        if match:
            sex = match.group(1).strip()

    return {
        "target_participant": target,
        "target_utterance_lines": int(tier_counts.get(target, 0)),
        "age_months_header": age,
        "sex_header": sex,
        "id_group_header": group,
        "media": media,
        "media_type": media_type,
        "date": date,
        "types": types,
        "comment": " ".join(comment_text)[:500],
    }


def stuttering_marker_features(path: Path, participant: str, n_utterances: float) -> dict[str, float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    prefix = f"*{participant}:"
    tier_lines = [line for line in text.splitlines() if line.startswith(prefix)]
    raw = "\n".join(tier_lines)
    denom = n_utterances if n_utterances else max(len(tier_lines), 1)
    arrow_spans = raw.count("↫") / 2.0
    blocked_or_fragment = raw.count("&+") + raw.count("&-")
    sound_runs = len(re.findall(r"\b[a-zA-Z](?:-[a-zA-Z]){1,}\b", raw))
    word_repetitions = raw.count("[/]")
    retracing = raw.count("[//]")
    pauses = raw.count("(.)") + raw.count("(..)") + raw.count("(...)")
    fillers = raw.count("&-") + raw.count("&=")
    weighted_sld = (
        word_repetitions
        + 2.0 * retracing
        + 2.0 * sound_runs
        + 3.0 * arrow_spans
        + 3.0 * blocked_or_fragment
    )
    return {
        "stutter_arrow_spans_per_utt": arrow_spans / denom,
        "blocked_fragment_markers_per_utt": blocked_or_fragment / denom,
        "repeated_sound_runs_per_utt": sound_runs / denom,
        "raw_word_repetition_markers_per_utt": word_repetitions / denom,
        "raw_retracing_markers_per_utt": retracing / denom,
        "raw_pause_markers_per_utt": pauses / denom,
        "raw_filler_markers_per_utt": fillers / denom,
        "weighted_sld_per_utt": weighted_sld / denom,
    }


def purdue_metadata(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "Purdue" / "demographics.xlsx"
    if not path.exists():
        return pd.DataFrame()
    return read_demographics(path)


def iisrp_new_id_map(raw_dir: Path) -> pd.DataFrame:
    """Map IISRP old participant IDs to numeric local file IDs where possible."""

    path = raw_dir / "IISRP" / "0data.xlsx"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_excel(path, sheet_name="Master sheet (IISRP)")
    rows = []
    for _, row in df.iterrows():
        participant = str(row.get("Participant", "")).strip()
        status = str(row.get("status", "")).strip().lower()
        sex = str(row.get("sex", "")).strip()
        if not participant or participant.lower() == "nan":
            continue
        match = re.match(r"E(\d{3})", participant)
        local_id = match.group(1) if match else ""
        rows.append(
            {
                "corpus": "IISRP",
                "participant_numeric": local_id,
                "participant_original": participant,
                "status_demo": status,
                "sex_demo": sex,
                "age1_demo_months": parse_age_any(row.get("Age", "")),
            }
        )
    return pd.DataFrame(rows)


def ratner_demo(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "Ratner" / "0demographics.xlsx"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_excel(path)
    rows = []
    for _, row in df.iterrows():
        subject = str(row.get("Subject", "")).strip()
        if not subject:
            continue
        sid = re.match(r"(S\d+)", subject)
        rows.append(
            {
                "ratner_session": subject.replace(".cha", ""),
                "participant_numeric": sid.group(1) if sid else subject,
                "age_months_demo": parse_age_any(row.get("Age", "")),
                "sex_demo": str(row.get("Gender", "")).strip(),
                "gfta_ss": safe_float(row.get("GFTA SS")),
                "ppvt_ss": safe_float(row.get("PPVT SS")),
                "eowpvt_ss": safe_float(row.get("EOWPVT SS")),
            }
        )
    return pd.DataFrame(rows)


def wagovich_demo(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "Wagovich" / "0demo.xlsx"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_excel(path)
    rows = []
    for _, row in df.iterrows():
        subject = str(row.get("Subject Number", "")).strip()
        match = re.search(r"#\s*(\d+)", subject)
        if not match:
            continue
        rows.append(
            {
                "participant_numeric": match.group(1),
                "age_months_demo": parse_age_any(row.get("Age", "")),
                "sex_demo": str(row.get("Sex", "")).strip(),
                "ssi3": safe_float(row.get("SSI-3 Score")),
                "ssi3_severity": str(row.get("SSI-3 Severity Rating", "")).strip(),
                "pls4_total": safe_float(row.get("PLS-4 Total Language Score")),
            }
        )
    return pd.DataFrame(rows)


def path_metadata(path: Path, raw_dir: Path, purdue_demo: pd.DataFrame) -> dict[str, object]:
    rel = path.relative_to(raw_dir)
    parts = rel.parts
    corpus = parts[0]
    stem = path.stem
    subgroup = parts[1] if len(parts) > 2 else ""
    participant = ""
    session_index = np.nan
    recovery_label = ""
    persistent = np.nan
    cws_td_group = ""
    task_hint = ""
    age_demo = np.nan
    sex_demo = ""

    if corpus == "IISRP":
        subgroup = parts[1]
        participant = parts[2]
        match = re.search(r"[-_](\d+(?:_5)?)$", stem)
        session_index = float(match.group(1).replace("_5", ".5")) if match else np.nan
        if subgroup == "CWS-rec":
            recovery_label, persistent, cws_td_group = "recovered", 0.0, "CWS"
        elif subgroup == "CWS-per":
            recovery_label, persistent, cws_td_group = "persistent", 1.0, "CWS"
        elif subgroup == "CWNS":
            recovery_label, cws_td_group = "td_control", "TD"
    elif corpus == "IISRP-new":
        subgroup = parts[1]
        participant = stem.split("-", 1)[0]
        match = re.search(r"-(\d+)$", stem)
        session_index = float(match.group(1)) if match else np.nan
        if subgroup == "CWS-rec":
            recovery_label, persistent, cws_td_group = "recovered", 0.0, "CWS"
        elif subgroup == "CWS-per":
            recovery_label, persistent, cws_td_group = "persistent", 1.0, "CWS"
        elif subgroup == "CWNS":
            recovery_label, cws_td_group = "td_control", "TD"
    elif corpus == "Purdue":
        subgroup = parts[1]
        dem = match_demographic(path, purdue_demo) if not purdue_demo.empty else None
        if dem is not None:
            participant = str(dem["subject_norm"])
            age_demo = safe_float(dem.get("age_months_demo"))
            sex_demo = str(dem.get("gender", "")).strip()
            if dem.get("persistent") == 1:
                recovery_label, persistent = "persistent", 1.0
            elif dem.get("persistent") == 0:
                recovery_label, persistent = "recovered", 0.0
        else:
            participant = norm_id(stem)
        cws_td_group = "CWS"
        year_match = re.search(r"(\d{2})$", stem)
        session_index = float(year_match.group(1)) if year_match else np.nan
    elif corpus == "Ratner":
        subgroup = parts[1] if len(parts) > 1 else ""
        match = re.match(r"(S\d+)", stem)
        participant = match.group(1) if match else stem
        if subgroup == "control":
            recovery_label, cws_td_group = "td_control", "TD"
            session_index = 0.0
        else:
            cws_td_group = "CWS"
            if "intake" in stem:
                session_index = 0.0
            else:
                fu = re.search(r"_(\d+)monthFU", stem)
                session_index = float(fu.group(1)) if fu else np.nan
    elif corpus == "Wagovich":
        participant = parts[1] if len(parts) > 1 else stem.split("-", 1)[0]
        match = re.search(r"-(\d+)$", stem)
        session_index = float(match.group(1)) if match else np.nan
        cws_td_group = "CWS"
    elif corpus == "UMD-CMU":
        subgroup = parts[1] if len(parts) > 1 else ""
        cws_td_group = "CWS" if subgroup == "CWS" else "TD" if subgroup == "Control" else ""
        participant = stem.split("_", 1)[0]
        y = re.search(r"_y(\d+)", stem)
        session_index = float(y.group(1)) if y else np.nan
        if "_frog" in stem:
            task_hint = "frog"
        elif "_parent" in stem:
            task_hint = "parent"
        elif "_clinician" in stem:
            task_hint = "clinician"
        elif "_home" in stem:
            task_hint = "home"
    elif corpus in {"Voices-AWS", "Voices-AWC", "Voices-CWS"}:
        subgroup = parts[1] if len(parts) > 1 else ""
        participant = re.sub(r"[^A-Za-z0-9]+.*$", "", stem)
        task_hint = subgroup
        cws_td_group = "CWS" if corpus == "Voices-CWS" else "AWS" if corpus == "Voices-AWS" else "AWC"
    elif corpus == "Hakim":
        subgroup = parts[1] if len(parts) > 1 else ""
        cws_td_group = "CWS" if subgroup == "CWS" else "TD" if subgroup == "TD" else ""
        task_hint = parts[2] if len(parts) > 2 else ""
        participant = stem
    elif corpus == "Tellis":
        participant = parts[1] if len(parts) > 1 else stem
        match = re.search(r"-(\d+)$", stem)
        session_index = float(match.group(1)) if match else np.nan
        cws_td_group = "CWS"
    else:
        participant = parts[1] if len(parts) > 1 else stem

    return {
        "path": str(path),
        "corpus": corpus,
        "subgroup": subgroup,
        "stem": stem,
        "participant_key": f"{corpus}:{subgroup}:{participant}" if subgroup else f"{corpus}:{participant}",
        "participant_local": participant,
        "session_index_path": session_index,
        "task_hint_path": task_hint,
        "recovery_label": recovery_label,
        "persistent": persistent,
        "cws_td_group_path": cws_td_group,
        "age_months_demo": age_demo,
        "sex_demo": sex_demo,
    }


def parse_one_chat(path: Path, raw_dir: Path, purdue_demo: pd.DataFrame, min_utterances: int) -> dict[str, object]:
    row = path_metadata(path, raw_dir, purdue_demo)
    header = parse_header(path)
    row.update(header)
    participant = str(header.get("target_participant") or "CHI")
    try:
        reader = pylangacq.read_chat(str(path))
        feats = extract_features(reader.utterances(), participant=participant, min_utterances=min_utterances)
    except Exception as exc:  # pragma: no cover - audit path
        row["parse_status"] = "failed"
        row["parse_error"] = f"{type(exc).__name__}: {exc}"
        return row

    if feats is None:
        row["parse_status"] = "too_few_target_utterances"
        row["parse_error"] = ""
        return row

    row.update(feats)
    row.update(stuttering_marker_features(path, participant, feats.get("n_utterances", 0.0)))
    row["parse_status"] = "parsed"
    row["parse_error"] = ""
    row["age_months"] = safe_float(row.get("age_months_header"))
    if math.isnan(row["age_months"]):
        row["age_months"] = safe_float(row.get("age_months_demo"))
    row["sex"] = str(row.get("sex_header") or row.get("sex_demo") or "").strip().lower()
    return row


def add_session_order(sessions: pd.DataFrame) -> pd.DataFrame:
    sessions = sessions.copy()
    sessions["age_sort"] = sessions["age_months"].fillna(9999)
    sessions["session_sort"] = sessions["session_index_path"].fillna(9999)
    sessions["stem_sort"] = sessions["stem"].astype(str)
    sessions = sessions.sort_values(["participant_key", "age_sort", "session_sort", "stem_sort"])
    sessions["session_order"] = sessions.groupby("participant_key").cumcount() + 1
    return sessions.drop(columns=["age_sort", "session_sort", "stem_sort"])


def feature_columns(sessions: pd.DataFrame) -> dict[str, list[str]]:
    disfluency = [
        "repetition_per_utt",
        "retracing_per_utt",
        "pause_per_utt",
        "filler_per_utt",
        "stutter_arrow_spans_per_utt",
        "blocked_fragment_markers_per_utt",
        "repeated_sound_runs_per_utt",
        "raw_word_repetition_markers_per_utt",
        "raw_retracing_markers_per_utt",
        "raw_pause_markers_per_utt",
        "raw_filler_markers_per_utt",
        "weighted_sld_per_utt",
    ]
    language = [
        "mlu_words",
        "mlu_morphemes",
        "ndw",
        "total_words",
        "verbs_per_utterance",
        "ttr",
        "function_word_ratio",
        "hapax_ratio",
        "log_total_tokens",
        "utt_len_mean",
        "utt_len_std",
        "utt_len_p10",
        "utt_len_p50",
        "utt_len_p90",
        "single_word_ratio",
    ]
    syntax = [c for c in sessions.columns if c.startswith("pos_") or c.startswith("rel_")]
    extra = ["mean_dep_distance", "max_dep_distance", "unique_head_dep_pairs", "unique_head_rel_dep_triples"]
    groups = {
        "disfluency": [c for c in disfluency if c in sessions.columns],
        "language": [c for c in language if c in sessions.columns],
        "syntax": [c for c in syntax + extra if c in sessions.columns],
    }
    groups["all_transcript"] = sorted(set(groups["disfluency"] + groups["language"] + groups["syntax"]))
    return groups


def build_participant_table(sessions: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    labelled = sessions[sessions["persistent"].notna() & sessions["parse_status"].eq("parsed")].copy()
    rows: list[dict[str, object]] = []
    for key, group in labelled.groupby("participant_key"):
        group = group.sort_values("session_order")
        first = group.iloc[0]
        second = group.iloc[1] if len(group) > 1 else None
        row = {
            "participant_key": key,
            "corpus": first["corpus"],
            "subgroup": first["subgroup"],
            "persistent": int(first["persistent"]),
            "recovery_label": first["recovery_label"],
            "n_sessions": len(group),
            "first_age_months": first.get("age_months", np.nan),
            "first_session_index": first.get("session_index_path", np.nan),
        }
        row["sex_male"] = 1.0 if str(first.get("sex", "")).lower().startswith("m") else 0.0 if str(first.get("sex", "")).lower().startswith("f") else np.nan
        for col in cols:
            row[f"first_{col}"] = first.get(col, np.nan)
            if second is not None:
                row[f"second_{col}"] = second.get(col, np.nan)
                row[f"delta2_{col}"] = second.get(col, np.nan) - first.get(col, np.nan)
            else:
                row[f"second_{col}"] = np.nan
                row[f"delta2_{col}"] = np.nan
            values = pd.to_numeric(group[col], errors="coerce") if col in group else pd.Series(dtype=float)
            x = pd.to_numeric(group["session_order"], errors="coerce")
            ok = values.notna() & x.notna()
            if ok.sum() >= 2:
                row[f"slope_{col}"] = float(np.polyfit(x[ok], values[ok], 1)[0])
            else:
                row[f"slope_{col}"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def model_pipeline(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    C=0.5,
                    class_weight="balanced",
                    max_iter=3000,
                    random_state=seed,
                ),
            ),
        ]
    )


def metric_row(name: str, y: np.ndarray, score: np.ndarray, n_features: int) -> dict[str, object]:
    pred = (score >= 0.5).astype(int)
    return {
        "feature_set": name,
        "n": len(y),
        "n_features": n_features,
        "persistent_rate": float(np.mean(y)),
        "auc": float(roc_auc_score(y, score)) if len(np.unique(y)) == 2 and len(np.unique(score)) > 1 else np.nan,
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        "persistent_f1": float(f1_score(y, pred, zero_division=0)),
    }


def cross_validated_scores(table: pd.DataFrame, cols: list[str], seed: int) -> np.ndarray | None:
    y = table["persistent"].astype(int).to_numpy()
    if len(np.unique(y)) < 2 or np.bincount(y).min() < 2:
        return None
    cv = StratifiedKFold(n_splits=min(5, int(np.bincount(y).min())), shuffle=True, random_state=seed)
    if not cols:
        model = DummyClassifier(strategy="most_frequent")
        proba = cross_val_predict(model, np.zeros((len(table), 1)), y, cv=cv, method="predict_proba")
        return proba[:, 1] if proba.shape[1] > 1 else np.zeros(len(table))
    return cross_val_predict(model_pipeline(seed), table[cols], y, cv=cv, method="predict_proba")[:, 1]


def evaluate_feature_sets(table: pd.DataFrame, feature_sets: dict[str, list[str]], seed: int) -> pd.DataFrame:
    rows = []
    y = table["persistent"].astype(int).to_numpy()
    for name, cols in feature_sets.items():
        score = cross_validated_scores(table, cols, seed)
        if score is None:
            continue
        rows.append(metric_row(name, y, score, len(cols)))
    return pd.DataFrame(rows)


def bootstrap_cis(table: pd.DataFrame, feature_sets: dict[str, list[str]], seed: int, bootstraps: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    y = table["persistent"].astype(int).to_numpy()
    scores = {name: cross_validated_scores(table, cols, seed) for name, cols in feature_sets.items()}
    rows = []
    n = len(table)
    for name, score in scores.items():
        if score is None:
            continue
        aucs, baccs = [], []
        for _ in range(bootstraps):
            idx = rng.integers(0, n, n)
            if len(np.unique(y[idx])) < 2:
                continue
            aucs.append(roc_auc_score(y[idx], score[idx]))
            baccs.append(balanced_accuracy_score(y[idx], (score[idx] >= 0.5).astype(int)))
        rows.append(
            {
                "feature_set": name,
                "auc_ci_low": float(np.quantile(aucs, 0.025)) if aucs else np.nan,
                "auc_ci_high": float(np.quantile(aucs, 0.975)) if aucs else np.nan,
                "balanced_accuracy_ci_low": float(np.quantile(baccs, 0.025)) if baccs else np.nan,
                "balanced_accuracy_ci_high": float(np.quantile(baccs, 0.975)) if baccs else np.nan,
                "bootstraps": bootstraps,
            }
        )

    if "first_all_transcript" in scores and "first_plus_movement" in scores:
        base = scores["first_all_transcript"]
        move = scores["first_plus_movement"]
        if base is not None and move is not None:
            auc_delta, bacc_delta = [], []
            for _ in range(bootstraps):
                idx = rng.integers(0, n, n)
                if len(np.unique(y[idx])) < 2:
                    continue
                auc_delta.append(roc_auc_score(y[idx], move[idx]) - roc_auc_score(y[idx], base[idx]))
                bacc_delta.append(
                    balanced_accuracy_score(y[idx], (move[idx] >= 0.5).astype(int))
                    - balanced_accuracy_score(y[idx], (base[idx] >= 0.5).astype(int))
                )
            rows.append(
                {
                    "feature_set": "delta_first_plus_movement_minus_first_all",
                    "auc_ci_low": float(np.quantile(auc_delta, 0.025)) if auc_delta else np.nan,
                    "auc_ci_high": float(np.quantile(auc_delta, 0.975)) if auc_delta else np.nan,
                    "balanced_accuracy_ci_low": float(np.quantile(bacc_delta, 0.025)) if bacc_delta else np.nan,
                    "balanced_accuracy_ci_high": float(np.quantile(bacc_delta, 0.975)) if bacc_delta else np.nan,
                    "bootstraps": bootstraps,
                }
            )
    return pd.DataFrame(rows)


def permutation_checks(table: pd.DataFrame, feature_sets: dict[str, list[str]], seed: int, permutations: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    y = table["persistent"].astype(int).to_numpy()
    rows = []
    for name in ["first_all_transcript", "movement_only", "first_plus_movement"]:
        cols = feature_sets.get(name)
        if not cols:
            continue
        observed_score = cross_validated_scores(table, cols, seed)
        if observed_score is None:
            continue
        observed_auc = roc_auc_score(y, observed_score)
        vals = []
        for _ in range(permutations):
            yp = rng.permutation(y)
            work = table.copy()
            work["persistent"] = yp
            score = cross_validated_scores(work, cols, seed)
            if score is not None:
                vals.append(roc_auc_score(yp, score))
        rows.append(
            {
                "feature_set": name,
                "observed_auc": float(observed_auc),
                "perm_mean_auc": float(np.mean(vals)) if vals else np.nan,
                "perm_p_auc_ge_observed": float((np.sum(np.array(vals) >= observed_auc) + 1) / (len(vals) + 1)) if vals else np.nan,
                "permutations": permutations,
            }
        )
    return pd.DataFrame(rows)


def leave_corpus_out(table: pd.DataFrame, feature_sets: dict[str, list[str]], seed: int) -> pd.DataFrame:
    rows = []
    for corpus in sorted(table["corpus"].unique()):
        train = table[table["corpus"].ne(corpus)].copy()
        test = table[table["corpus"].eq(corpus)].copy()
        if len(train) < 10 or len(test) < 2:
            continue
        y_train = train["persistent"].astype(int).to_numpy()
        y_test = test["persistent"].astype(int).to_numpy()
        if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
            continue
        for name in ["first_all_transcript", "first_plus_movement"]:
            cols = feature_sets.get(name, [])
            if not cols:
                continue
            model = model_pipeline(seed)
            model.fit(train[cols], y_train)
            score = model.predict_proba(test[cols])[:, 1]
            rows.append({"held_out_corpus": corpus, **metric_row(name, y_test, score, len(cols))})
    return pd.DataFrame(rows)


def make_feature_sets(cols: dict[str, list[str]], movement_subset: bool) -> dict[str, list[str]]:
    dis = [f"first_{c}" for c in cols["disfluency"]]
    lang = [f"first_{c}" for c in cols["language"]]
    all_first = [f"first_{c}" for c in cols["all_transcript"]]
    movement = [f"delta2_{c}" for c in cols["all_transcript"]] + [f"slope_{c}" for c in cols["all_transcript"]]
    feature_sets = {
        "majority_baseline": [],
        "demographics": ["first_age_months", "sex_male"],
        "first_disfluency": dis,
        "first_language": lang,
        "first_all_transcript": all_first,
    }
    if movement_subset:
        feature_sets["movement_only"] = movement
        feature_sets["first_plus_movement"] = all_first + movement
    return {k: [c for c in v if c] for k, v in feature_sets.items()}


def inventory_tables(sessions: pd.DataFrame, participants: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    parsed = sessions[sessions["parse_status"].eq("parsed")].copy()
    corpus_rows = []
    for corpus, group in sessions.groupby("corpus"):
        parsed_group = group[group["parse_status"].eq("parsed")]
        part_group = parsed_group.drop_duplicates("participant_key")
        labelled_part = participants[participants["corpus"].eq(corpus)] if not participants.empty else pd.DataFrame()
        corpus_rows.append(
            {
                "corpus": corpus,
                "cha_files": len(group),
                "parsed_feature_rows": len(parsed_group),
                "parse_success_rate": len(parsed_group) / len(group) if len(group) else np.nan,
                "participants_with_features": part_group["participant_key"].nunique(),
                "labelled_recovery_participants": labelled_part["participant_key"].nunique() if not labelled_part.empty else 0,
                "persistent_participants": int(labelled_part["persistent"].sum()) if not labelled_part.empty else 0,
                "recovered_participants": int((labelled_part["persistent"] == 0).sum()) if not labelled_part.empty else 0,
                "median_sessions_per_featured_participant": parsed_group.groupby("participant_key").size().median() if not parsed_group.empty else np.nan,
            }
        )
    corpus_inv = pd.DataFrame(corpus_rows).sort_values("cha_files", ascending=False)

    endpoint = (
        participants.groupby(["corpus", "recovery_label"], dropna=False)
        .size()
        .reset_index(name="participants")
        .sort_values(["corpus", "recovery_label"])
        if not participants.empty
        else pd.DataFrame(columns=["corpus", "recovery_label", "participants"])
    )

    status = (
        sessions.groupby(["corpus", "parse_status"], dropna=False)
        .size()
        .reset_index(name="files")
        .sort_values(["corpus", "parse_status"])
    )
    return corpus_inv, endpoint, status


def write_summary(
    out_dir: Path,
    sessions: pd.DataFrame,
    participants: pd.DataFrame,
    corpus_inv: pd.DataFrame,
    endpoint: pd.DataFrame,
    status: pd.DataFrame,
    all_metrics: pd.DataFrame,
    move_metrics: pd.DataFrame,
    leave_out: pd.DataFrame,
    boot: pd.DataFrame,
    perms: pd.DataFrame,
) -> None:
    movement_best = move_metrics.sort_values("auc", ascending=False).iloc[0] if not move_metrics.empty else None
    first_row = move_metrics[move_metrics["feature_set"].eq("first_all_transcript")]
    plus_row = move_metrics[move_metrics["feature_set"].eq("first_plus_movement")]
    if not first_row.empty and not plus_row.empty:
        auc_delta = float(plus_row.iloc[0]["auc"] - first_row.iloc[0]["auc"])
        bacc_delta = float(plus_row.iloc[0]["balanced_accuracy"] - first_row.iloc[0]["balanced_accuracy"])
    else:
        auc_delta = np.nan
        bacc_delta = np.nan

    lines = [
        "# Full FluencyBank Transcript Recovery Model",
        "",
        "**Question:** after full FluencyBank transcript access, does early within-child transcript movement predict recovered versus persistent stuttering better than earliest-session state?",
        "",
        "## Data Audit",
        "",
        f"- Local FluencyBank `.cha` files scanned: {len(sessions):,}",
        f"- Parsed feature rows with at least the target-utterance threshold: {sessions['parse_status'].eq('parsed').sum():,}",
        f"- Recovery-labelled CWS participants with usable features: {len(participants):,}",
        f"- Labelled participants with at least two usable sessions: {(participants['n_sessions'] >= 2).sum():,}",
        "",
        "### Corpus Inventory",
        "",
        md_table(corpus_inv.round(3)),
        "",
        "### Recovery Endpoint Inventory",
        "",
        md_table(endpoint),
        "",
        "### Parse Status",
        "",
        md_table(status),
        "",
        "## Earliest-Session Model",
        "",
        md_table(all_metrics.round(3)),
        "",
        "## Early-Movement Model",
        "",
        "Movement rows restrict to labelled participants with at least two usable sessions. `movement_only` uses first-to-second-session deltas plus within-child slopes; `first_plus_movement` adds those movement features to earliest-session state.",
        "",
        md_table(move_metrics.round(3)),
        "",
        "## Bootstrap Confidence Intervals",
        "",
        md_table(boot.round(3)),
        "",
        "## Shuffled-Label Checks",
        "",
        md_table(perms.round(3)),
        "",
        "## Leave-Corpus-Out Checks",
        "",
        md_table(leave_out.round(3) if not leave_out.empty else pd.DataFrame([{"status": "no held-out corpus had both train and test classes"}])),
        "",
        "## Interpretation",
        "",
    ]
    if movement_best is not None:
        lines.extend(
            [
                f"The best movement-subset model is `{movement_best['feature_set']}` with AUC {movement_best['auc']:.3f}, balanced accuracy {movement_best['balanced_accuracy']:.3f}, and macro-F1 {movement_best['macro_f1']:.3f}.",
                "",
                f"Adding early movement to earliest transcript state changes AUC by {auc_delta:+.3f} and balanced accuracy by {bacc_delta:+.3f} on the movement-eligible participant subset.",
                "",
            ]
        )
    lines.extend(
        [
            "This is the first full-access transcript-level test of the stuttering recovery thesis. It treats IISRP/IISRP-new directory labels (`CWS-rec`, `CWS-per`) and Purdue `Rec/Per` workbook labels as recovery endpoints; other corpora contribute to the inventory but not the recovery endpoint unless they expose a comparable label.",
            "",
            "A positive early-movement delta would support the cross-disorder state-movement hypothesis. A weak or negative delta would mean the stuttering recovery track needs richer predictors, official severity trajectories, acoustics, or treatment/context metadata before it can carry the main scientific claim.",
            "",
            "Row-level transcript and participant features are stored in gitignored `data/parsed/fluencybank/`; aggregate outputs are in this directory.",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.parsed_dir.mkdir(parents=True, exist_ok=True)

    purdue_demo = purdue_metadata(args.raw_dir)
    files = sorted(p for p in args.raw_dir.rglob("*.cha") if "_zips" not in p.parts)
    rows = [parse_one_chat(path, args.raw_dir, purdue_demo, args.min_utterances) for path in files]
    sessions = add_session_order(pd.DataFrame(rows))

    cols = feature_columns(sessions)
    participants = build_participant_table(sessions, cols["all_transcript"])
    movement_participants = participants[participants["n_sessions"].ge(2)].copy()

    all_feature_sets = make_feature_sets(cols, movement_subset=False)
    movement_feature_sets = make_feature_sets(cols, movement_subset=True)
    all_metrics = evaluate_feature_sets(participants, all_feature_sets, args.seed)
    move_metrics = evaluate_feature_sets(movement_participants, movement_feature_sets, args.seed)
    boot = bootstrap_cis(movement_participants, movement_feature_sets, args.seed, args.bootstraps)
    perms = permutation_checks(movement_participants, movement_feature_sets, args.seed, args.permutations)
    leave_out = leave_corpus_out(movement_participants, movement_feature_sets, args.seed)

    corpus_inv, endpoint, status = inventory_tables(sessions, participants)

    sessions.to_csv(args.parsed_dir / "full_session_features.csv", index=False)
    participants.to_csv(args.parsed_dir / "full_recovery_participant_features.csv", index=False)
    corpus_inv.to_csv(args.output_dir / "corpus_inventory.csv", index=False)
    endpoint.to_csv(args.output_dir / "endpoint_inventory.csv", index=False)
    status.to_csv(args.output_dir / "parse_status.csv", index=False)
    all_metrics.to_csv(args.output_dir / "earliest_model_metrics.csv", index=False)
    move_metrics.to_csv(args.output_dir / "movement_model_metrics.csv", index=False)
    boot.to_csv(args.output_dir / "movement_bootstrap_cis.csv", index=False)
    perms.to_csv(args.output_dir / "movement_permutation_auc.csv", index=False)
    leave_out.to_csv(args.output_dir / "leave_corpus_out.csv", index=False)

    write_summary(
        args.output_dir,
        sessions,
        participants,
        corpus_inv,
        endpoint,
        status,
        all_metrics,
        move_metrics,
        leave_out,
        boot,
        perms,
    )
    print(f"wrote {args.output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
