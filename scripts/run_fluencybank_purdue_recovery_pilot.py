"""First-pass FluencyBank Purdue recovery/persistence pilot.

This script uses the locally downloaded FluencyBank Purdue corpus plus its
included demographics workbook. The endpoint is intentionally conservative:
predict strict recovered versus persistent labels from the earliest available
CHAT transcript per child. It is not a clinical recovery model yet; it is a
data-feasibility and signal audit for Brian's proposed stuttering track.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
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
from src.features.extractors import extract_features  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--purdue-dir", default="data/raw/fluencybank/Purdue", type=Path)
    parser.add_argument("--output-dir", default="outputs/fluencybank_purdue_recovery_pilot", type=Path)
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument("--permutations", default=200, type=int)
    return parser.parse_args()


def norm_id(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"\s*\([^)]*\)", "", text)
    return re.sub(r"[^a-z0-9]", "", text)


def age_to_months(value: object) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return np.nan
    text = str(value).strip()
    match = re.search(r"(\d+)\s*;\s*(\d+)", text)
    if not match:
        return np.nan
    return float(int(match.group(1)) * 12 + int(match.group(2)))


def clean_numeric(value: object) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return np.nan
    text = str(value).strip()
    if not text or text.lower() in {"nan", "no data", "n/a", "na"}:
        return np.nan
    text = text.replace(",", "")
    if text.startswith("<"):
        try:
            return float(text[1:]) - 0.5
        except ValueError:
            return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def read_demographics(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="CWS", header=None)

    def block(start: int, end: int, grant: str) -> pd.DataFrame:
        rows = raw.iloc[start:end].copy()
        if grant == "Grant1":
            out = pd.DataFrame(
                {
                    "grant": grant,
                    "subject": rows[0],
                    "age_months_demo": rows[1].map(age_to_months),
                    "gender": rows[2].astype(str).str.strip(),
                    "ses": rows[3].map(clean_numeric),
                    "rec_per": rows[4].astype(str).str.strip(),
                    "spelt3": rows[8].map(clean_numeric),
                    "tacl3": rows[9].map(clean_numeric),
                    "bbtop_ci": rows[11].map(clean_numeric),
                    "bbtop_ppi": rows[12].map(clean_numeric),
                    "tocs_index": np.nan,
                    "tocs_pctile": np.nan,
                    "celf_receptive": np.nan,
                    "celf_expressive": np.nan,
                }
            )
        else:
            out = pd.DataFrame(
                {
                    "grant": grant,
                    "subject": rows[0],
                    "age_months_demo": rows[1].map(age_to_months),
                    "gender": rows[2].astype(str).str.strip(),
                    "ses": rows[3].map(clean_numeric),
                    "rec_per": rows[4].astype(str).str.strip(),
                    "spelt3": rows[8].map(clean_numeric),
                    "tacl3": np.nan,
                    "bbtop_ci": rows[11].map(clean_numeric),
                    "bbtop_ppi": rows[12].map(clean_numeric),
                    "tocs_index": rows[6].map(clean_numeric),
                    "tocs_pctile": rows[7].map(clean_numeric),
                    "celf_receptive": rows[9].map(clean_numeric),
                    "celf_expressive": rows[10].map(clean_numeric),
                }
            )
        return out

    # Rows are fixed in the distributed workbook: Grant 1 header at 1, data at
    # 2:63; Grant 2 header at 65, data at 66:end.
    demo = pd.concat([block(2, 63, "Grant1"), block(66, len(raw), "Grant2")], ignore_index=True)
    demo = demo[demo["subject"].notna()].copy()
    demo["subject_norm"] = demo["subject"].map(norm_id)
    demo["grant1_family_norm"] = demo["subject_norm"].str.replace(r"\d{2}$", "", regex=True)
    demo["persistent"] = demo["rec_per"].map({"Per": 1, "Rec": 0})
    demo["label_status"] = np.where(demo["persistent"].notna(), "strict", "excluded_or_ambiguous")
    return demo


def parse_chat_metadata(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    age = np.nan
    gender = ""
    year = np.nan
    for line in text.splitlines()[:80]:
        if line.startswith("@ID:") and "|CHI|" in line:
            parts = line.split("|")
            if len(parts) >= 4:
                age = age_to_months(parts[3])
            if len(parts) >= 5:
                gender = parts[4].strip()
        if "@Comment:" in line:
            m_year = re.search(r"\b(?:year|collect)\s*=?\s*(\d+)\b", line, flags=re.I)
            if m_year:
                year = float(m_year.group(1))
    return {"age_months_chat": age, "gender_chat": gender, "collection_year": year}


def stuttering_marker_features(path: Path, n_utterances: float) -> dict[str, float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    chi_lines = [line for line in text.splitlines() if line.startswith("*CHI:")]
    raw = "\n".join(chi_lines)
    denom = n_utterances if n_utterances else max(len(chi_lines), 1)
    # FluencyBank/Purdue often marks stuttered stretches with paired arrows,
    # e.g. "↫i-i-i↫it"; this is not captured by generic CHAT [/] counts.
    arrow_spans = raw.count("↫") / 2.0
    blocked_or_fragment = raw.count("&+") + raw.count("&-")
    repeated_sound_runs = len(re.findall(r"\b[a-zA-Z](?:-[a-zA-Z]){1,}\b", raw))
    return {
        "stutter_arrow_spans_per_utt": arrow_spans / denom,
        "blocked_fragment_markers_per_utt": blocked_or_fragment / denom,
        "repeated_sound_runs_per_utt": repeated_sound_runs / denom,
    }


def match_demographic(path: Path, demo: pd.DataFrame) -> pd.Series | None:
    stem = norm_id(path.stem)
    grant = path.parent.name
    choices = demo[demo["grant"].eq(grant)].copy()
    if choices.empty:
        return None
    exact = choices[choices["subject_norm"].eq(stem)]
    if not exact.empty:
        return exact.iloc[0]
    if grant == "Grant1":
        family = re.sub(r"\d{2}$", "", stem)
        fam = choices[choices["grant1_family_norm"].eq(family)]
        if not fam.empty:
            return fam.iloc[0]
    # Grant 2 session files usually append a visit number to the subject ID.
    choices = choices.assign(subject_len=choices["subject_norm"].str.len())
    prefix = choices[choices.apply(lambda r: stem.startswith(r["subject_norm"]), axis=1)]
    if not prefix.empty:
        return prefix.sort_values("subject_len", ascending=False).iloc[0]
    return None


def build_session_table(purdue_dir: Path, demo: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    unmatched: list[dict[str, object]] = []
    for path in sorted(purdue_dir.glob("Grant*/*.cha")):
        dem = match_demographic(path, demo)
        if dem is None:
            unmatched.append({"path": str(path), "stem": path.stem, "grant": path.parent.name})
            continue
        try:
            reader = pylangacq.read_chat(str(path))
            feats = extract_features(reader.utterances(), min_utterances=20)
        except Exception as exc:  # pragma: no cover - defensive audit path
            unmatched.append({"path": str(path), "stem": path.stem, "grant": path.parent.name, "error": str(exc)})
            continue
        if feats is None:
            unmatched.append({"path": str(path), "stem": path.stem, "grant": path.parent.name, "error": "too_few_chi_utts"})
            continue
        meta = parse_chat_metadata(path)
        row = {
            "path": str(path),
            "stem": path.stem,
            "grant": dem["grant"],
            "subject_norm": dem["subject_norm"],
            "rec_per": dem["rec_per"],
            "persistent": dem["persistent"],
            "age_months_demo": dem["age_months_demo"],
            "gender": dem["gender"],
            "ses": dem["ses"],
            "spelt3": dem["spelt3"],
            "tacl3": dem["tacl3"],
            "bbtop_ci": dem["bbtop_ci"],
            "bbtop_ppi": dem["bbtop_ppi"],
            "tocs_index": dem["tocs_index"],
            "tocs_pctile": dem["tocs_pctile"],
            "celf_receptive": dem["celf_receptive"],
            "celf_expressive": dem["celf_expressive"],
            **meta,
            **feats,
        }
        row.update(stuttering_marker_features(path, feats.get("n_utterances", 0.0)))
        rows.append(row)
    return pd.DataFrame(rows), pd.DataFrame(unmatched)


def earliest_per_child(sessions: pd.DataFrame) -> pd.DataFrame:
    labelled = sessions[sessions["persistent"].notna()].copy()
    labelled["age_sort"] = labelled["age_months_chat"].fillna(labelled["age_months_demo"]).fillna(9999)
    labelled["year_sort"] = labelled["collection_year"].fillna(9999)
    return (
        labelled.sort_values(["subject_norm", "age_sort", "year_sort", "stem"])
        .groupby(["grant", "subject_norm"], as_index=False)
        .first()
    )


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
                    max_iter=2000,
                    random_state=seed,
                ),
            ),
        ]
    )


def evaluate_feature_sets(table: pd.DataFrame, seed: int, permutations: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_sets = {
        "majority_baseline": [],
        "age_sex_ses": ["age_months_chat", "age_months_demo", "gender_male", "ses"],
        "simple_disfluency": [
            "repetition_per_utt",
            "retracing_per_utt",
            "filler_per_utt",
            "pause_per_utt",
            "stutter_arrow_spans_per_utt",
            "blocked_fragment_markers_per_utt",
            "repeated_sound_runs_per_utt",
        ],
        "language_structure": [
            "mlu_words",
            "mlu_morphemes",
            "ndw",
            "total_words",
            "verbs_per_utterance",
            "ttr",
            "function_word_ratio",
            "utt_len_mean",
            "utt_len_std",
            "single_word_ratio",
        ],
        "baseline_tests": [
            "spelt3",
            "tacl3",
            "bbtop_ci",
            "bbtop_ppi",
            "tocs_index",
            "tocs_pctile",
            "celf_receptive",
            "celf_expressive",
        ],
    }
    feature_sets["all_transcript"] = sorted(
        {
            col
            for group in ["simple_disfluency", "language_structure"]
            for col in feature_sets[group]
        }
    )
    feature_sets["all_available"] = sorted(
        {
            col
            for group in ["age_sex_ses", "simple_disfluency", "language_structure", "baseline_tests"]
            for col in feature_sets[group]
        }
    )

    work = table.copy()
    work["gender_male"] = work["gender"].astype(str).str.upper().eq("M").astype(float)
    y = work["persistent"].astype(int).to_numpy()
    min_class = int(np.bincount(y).min())
    cv = StratifiedKFold(n_splits=min(5, min_class), shuffle=True, random_state=seed)
    rng = np.random.default_rng(seed)

    rows = []
    perm_rows = []
    for name, cols in feature_sets.items():
        if name == "majority_baseline":
            model = DummyClassifier(strategy="most_frequent")
            proba = cross_val_predict(model, np.zeros((len(work), 1)), y, cv=cv, method="predict_proba")
            if proba.shape[1] == 1:
                score = np.zeros(len(work))
            else:
                score = proba[:, 1]
        else:
            X = work[cols]
            score = cross_val_predict(model_pipeline(seed), X, y, cv=cv, method="predict_proba")[:, 1]
        pred = (score >= 0.5).astype(int)
        rows.append(
            {
                "feature_set": name,
                "n": len(work),
                "n_features": len(cols),
                "persistent_rate": float(y.mean()),
                "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
                "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
                "persistent_f1": float(f1_score(y, pred, zero_division=0)),
                "auc": float(roc_auc_score(y, score)) if len(np.unique(score)) > 1 else np.nan,
            }
        )
        if name in {"all_transcript", "all_available", "simple_disfluency"}:
            vals = []
            cols_perm = cols if cols else ["age_months_chat"]
            for _ in range(permutations):
                yp = rng.permutation(y)
                score_p = cross_val_predict(
                    model_pipeline(seed),
                    work[cols_perm],
                    yp,
                    cv=StratifiedKFold(n_splits=min(5, np.bincount(yp).min()), shuffle=True, random_state=seed),
                    method="predict_proba",
                )[:, 1]
                vals.append(float(roc_auc_score(yp, score_p)))
            observed = rows[-1]["auc"]
            perm_rows.append(
                {
                    "feature_set": name,
                    "observed_auc": observed,
                    "perm_mean_auc": float(np.mean(vals)),
                    "perm_p_auc_ge_observed": float((np.sum(np.array(vals) >= observed) + 1) / (len(vals) + 1)),
                    "permutations": permutations,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(perm_rows)


def aggregate_feature_groups(table: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "mlu_words",
        "ndw",
        "ttr",
        "repetition_per_utt",
        "retracing_per_utt",
        "filler_per_utt",
        "stutter_arrow_spans_per_utt",
        "repeated_sound_runs_per_utt",
        "spelt3",
        "bbtop_ci",
    ]
    rows = []
    for label, group in table.groupby("rec_per"):
        row = {"rec_per": label, "n": len(group)}
        for col in cols:
            if col in group:
                row[f"{col}_mean"] = group[col].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    demo = read_demographics(args.purdue_dir / "demographics.xlsx")
    sessions, unmatched = build_session_table(args.purdue_dir, demo)
    earliest = earliest_per_child(sessions)
    labelled = earliest[earliest["persistent"].notna()].copy()
    metrics, perms = evaluate_feature_sets(labelled, args.seed, args.permutations)
    group_summary = aggregate_feature_groups(labelled)

    # Keep participant-level table under gitignored data/ because it contains
    # restricted corpus IDs and derived transcript features. Aggregate outputs
    # under outputs/ are safe to commit.
    parsed_dir = Path("data/parsed/fluencybank")
    parsed_dir.mkdir(parents=True, exist_ok=True)
    sessions.to_csv(parsed_dir / "purdue_session_features.csv", index=False)
    earliest.to_csv(parsed_dir / "purdue_earliest_labelled_features.csv", index=False)
    unmatched.to_csv(parsed_dir / "purdue_unmatched_or_failed.csv", index=False)

    metrics.to_csv(out_dir / "model_metrics.csv", index=False)
    perms.to_csv(out_dir / "permutation_auc.csv", index=False)
    group_summary.to_csv(out_dir / "label_group_feature_summary.csv", index=False)

    best = metrics[metrics["feature_set"].ne("majority_baseline")].sort_values("auc", ascending=False).iloc[0]
    strict_counts = demo["rec_per"].value_counts(dropna=False).rename_axis("label").reset_index(name="n")
    lines = [
        "# FluencyBank Purdue Recovery Pilot",
        "",
        "**Question:** Can earliest available Purdue transcript state predict later recovered versus persistent stuttering labels?",
        "",
        "## Data",
        "",
        "- Source: FluencyBank English Purdue Corpus, Smith, Weber, Hampton Wray, Walsh, and Usler; DOI `10.21415/P2JB-CA45`.",
        f"- Purdue CHAT files parsed: {len(sessions):,}",
        f"- Unmatched or failed CHAT files: {len(unmatched):,}",
        f"- Strict Rec/Per children with an earliest transcript: {len(labelled):,}",
        f"- Persistent rate in modeled set: {labelled['persistent'].mean():.3f}",
        "",
        "### Demographic Label Inventory",
        "",
        md_table(strict_counts),
        "",
        "## First-Pass Recovery Classification",
        "",
        "Endpoint is strict `Per` versus `Rec` from the distributed Purdue demographics workbook. Ambiguous labels such as `No Data`, `NEI`, and `Y1 only` are excluded.",
        "",
        md_table(metrics.round(3)),
        "",
        "## Shuffled-Label AUC Check",
        "",
        md_table(perms.round(3)),
        "",
        "## Label Group Feature Means",
        "",
        md_table(group_summary.round(3)),
        "",
        "## Interpretation",
        "",
        f"The best first-pass feature set is `{best['feature_set']}` with AUC {best['auc']:.3f}, balanced accuracy {best['balanced_accuracy']:.3f}, and macro-F1 {best['macro_f1']:.3f}.",
        "",
        "This is a real unblock for the stuttering track: Purdue gives us an accessible longitudinal Rec/Per endpoint. However, this is still a pilot. The model uses one earliest transcript per child, no acoustic features yet, no official severity trajectory modeling, and no external corpus-held-out validation. IISRP, Wagovich, Ratner, and Maxfield remain password-gated and are still needed for replication.",
        "",
        "Next experiment: add longitudinal change features from later Purdue transcripts and test whether early transcript state predicts final persistence beyond baseline demographics and standardized tests.",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
