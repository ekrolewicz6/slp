"""Deep Salem/Cinderella discourse informativeness experiment.

The highest-learning suite found that simple Cinderella concept coverage
correlates strongly with WAB-AQ on the full Salem sample, but our main
AphasiaBank feature table only intersected 43 Salem sessions. This script
extracts structural features directly from the Salem CHAT files so the
comparison is full-sample:

* structural discourse features from each Cinderella transcript;
* observed concept coverage from template text only;
* target-augmented concept coverage using Salem's human paraphasia targets;
* paraphasia count / confidence / agreement summaries.

The critical scientific split is observed vs target-augmented concepts. If
target-augmented coverage is much stronger, the signal is not just "more words"
or "better syntax"; it is recovery of intended narrative content.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pylangacq as pla

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import (  # noqa: E402
    classification_summary,
    cross_val_predict_classifier,
    cross_val_predict_regressor,
    ensure_dir,
    numeric_feature_columns,
    pearson_safe,
    regression_summary,
)
from src.features.extractors import extract_features  # noqa: E402


META = {
    "session_id",
    "participant_id",
    "date",
    "multiple_sessions",
    "wab_type",
    "wab_aq",
    "days_since_previous",
    "file_path",
}

CINDERELLA_CONCEPTS = {
    "cinderella": ["cinderella"],
    "stepfamily": ["stepmother", "stepsister", "stepsisters", "sister", "sisters", "stepchildren"],
    "prince": ["prince"],
    "ball": ["ball", "dance", "party"],
    "chores": ["clean", "sweep", "scrub", "work", "poor"],
    "fairy_godmother": ["fairy", "godmother"],
    "magic": ["magic", "magical"],
    "dress": ["dress", "gown", "beautiful"],
    "carriage": ["carriage", "coach", "pumpkin"],
    "midnight": ["midnight", "twelve"],
    "slipper": ["slipper", "shoe", "glass"],
    "loss": ["lost", "left", "leave"],
    "fit": ["fit", "fits", "try", "tried"],
    "marriage": ["marry", "married", "wedding"],
    "castle": ["castle", "palace"],
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--salem-root",
        default=(
            "data/raw/aphasiabank/extras/Salem/talkbank-preprocessed-cinderella-data/"
            "preprocessed-cinderella"
        ),
        type=Path,
    )
    p.add_argument("--output-dir", default="outputs/salem_cinderella_deep", type=Path)
    p.add_argument("--cv-folds", type=int, default=5)
    p.add_argument("--min-utterances", type=int, default=5)
    return p.parse_args()


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def _concept_features(tokens: list[str], prefix: str) -> dict[str, float]:
    token_set = set(tokens)
    hits = {
        name: int(any(term in token_set for term in terms))
        for name, terms in CINDERELLA_CONCEPTS.items()
    }
    total = int(sum(hits.values()))
    return {
        f"{prefix}_concept_coverage": float(total),
        f"{prefix}_concept_density": float(total / max(len(tokens), 1)),
        f"{prefix}_n_tokens": float(len(tokens)),
        **{f"{prefix}_concept_{k}": float(v) for k, v in hits.items()},
    }


def parse_salem_yaml(path: Path) -> pd.DataFrame:
    text = path.read_text(encoding="utf-8", errors="ignore")
    blocks = re.split(r"\n- !Session\n", text)
    rows = []
    for block in blocks:
        m = re.search(r"session_id:\s*([A-Za-z0-9_-]+)", block)
        if not m:
            continue
        sid = m.group(1)
        template_lines = []
        target_words = []
        agreements = []
        confidences = []
        in_template = False
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("template_texts:"):
                in_template = True
                continue
            if in_template and stripped.startswith("- "):
                template_lines.append(stripped[2:].strip("'\""))
                continue
            if in_template and not stripped.startswith("- "):
                in_template = False
            if "target_text:" in stripped:
                target_words.append(stripped.split("target_text:", 1)[1].strip().strip("'\""))
            if "agreement:" in stripped:
                try:
                    agreements.append(float(stripped.split("agreement:", 1)[1].strip()))
                except ValueError:
                    pass
            if "confidence:" in stripped:
                try:
                    confidences.append(float(stripped.split("confidence:", 1)[1].strip()))
                except ValueError:
                    pass
        observed_text = re.sub(r"\{[^}]+\}", " ", " ".join(template_lines))
        target_text = " ".join(target_words)
        observed_tokens = _tokenize(observed_text)
        augmented_tokens = _tokenize(f"{observed_text} {target_text}")
        rows.append(
            {
                "session_id": sid,
                "target_word_count": float(len(target_words)),
                "target_agreement_mean": float(np.mean(agreements)) if agreements else 0.0,
                "target_confidence_mean": float(np.mean(confidences)) if confidences else 0.0,
                **_concept_features(observed_tokens, "observed"),
                **_concept_features(augmented_tokens, "augmented"),
            }
        )
    return pd.DataFrame(rows)


def extract_salem_structural(chat_root: Path, min_utterances: int) -> pd.DataFrame:
    rows = []
    for path in sorted(chat_root.rglob("*.cha")):
        sid = path.stem
        try:
            chat = pla.read_chat(str(path), strict=False)
            feats = extract_features(
                chat.utterances(),
                participant="PAR",
                min_utterances=min_utterances,
            )
        except Exception as exc:
            rows.append({"session_id": sid, "file_path": str(path), "extract_error": type(exc).__name__})
            continue
        if feats is None:
            rows.append({"session_id": sid, "file_path": str(path), "extract_error": "too_few_utts"})
            continue
        rows.append({"session_id": sid, "file_path": str(path), "extract_error": "", **feats})
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    report_path = args.salem_root / "aphasia-preprocessed" / "sessions-report.csv"
    yaml_path = args.salem_root / "aphasia-preprocessed" / "sessions.yaml"
    chat_root = args.salem_root / "aphasia-chat" / "CHAT" / "aphasia" / "English" / "Aphasia"

    report = pd.read_csv(report_path)
    report.columns = [c.replace(" ", "_") for c in report.columns]
    report["wab_aq"] = pd.to_numeric(report["wab_aq_index_(CHAT)"], errors="coerce")
    report["participant_id"] = report["participant_id"].astype(str)

    concept = parse_salem_yaml(yaml_path)
    structural = extract_salem_structural(chat_root, args.min_utterances)
    structural.to_csv(out_dir / "salem_structural_features.csv", index=False)

    df = report.merge(concept, on="session_id", how="left")
    df = df.merge(structural, on="session_id", how="left")
    df.to_csv(out_dir / "salem_deep_joined.csv", index=False)

    feature_cols = numeric_feature_columns(df, META | {"extract_error"})
    structural_cols = [
        c for c in feature_cols
        if not c.startswith("observed_")
        and not c.startswith("augmented_")
        and not c.startswith("target_")
        and c not in {"wab_aq"}
    ]
    observed_cols = [c for c in feature_cols if c.startswith("observed_")]
    augmented_cols = [c for c in feature_cols if c.startswith("augmented_")]
    target_cols = [c for c in feature_cols if c.startswith("target_")]
    concept_cols = observed_cols + augmented_cols + target_cols

    model_df = df[df["extract_error"].fillna("") == ""].copy()
    model_df = model_df.dropna(subset=["wab_aq", "participant_id"]).reset_index(drop=True)

    corr_rows = []
    for col in observed_cols + augmented_cols + target_cols:
        corr_rows.append({"feature": col, "n": int(model_df[[col, "wab_aq"]].dropna().shape[0]), "r_wab_aq": pearson_safe(model_df[col], model_df["wab_aq"])})
    pd.DataFrame(corr_rows).sort_values("r_wab_aq", ascending=False).to_csv(
        out_dir / "salem_feature_correlations.csv",
        index=False,
    )

    setups = {
        "structural": structural_cols,
        "observed_concepts": observed_cols,
        "target_annotations": target_cols,
        "augmented_concepts": augmented_cols + target_cols,
        "all_concepts": concept_cols,
        "structural+observed": structural_cols + observed_cols,
        "structural+augmented": structural_cols + augmented_cols + target_cols,
    }

    rows = []
    for setup, cols in setups.items():
        if not cols:
            continue
        y, pred = cross_val_predict_regressor(
            model_df,
            "wab_aq",
            {"features": cols},
            group_col="participant_id",
            cv_mode="group",
            n_splits=args.cv_folds,
        )
        rows.append({"task": "wab_aq_regression", "setup": setup, **regression_summary(y, pred)})

    cls = model_df.dropna(subset=["wab_type"]).copy()
    keep = cls["wab_type"].value_counts()
    keep = keep[keep >= 10].index.tolist()
    cls = cls[cls["wab_type"].isin(keep)].reset_index(drop=True)
    for setup, cols in setups.items():
        if len(cls) < 50 or cls["wab_type"].nunique() < 2:
            continue
        y, pred = cross_val_predict_classifier(
            cls,
            "wab_type",
            {"features": cols},
            group_col="participant_id",
            cv_mode="group",
            n_splits=args.cv_folds,
        )
        rows.append({"task": "subtype_classification", "setup": setup, **classification_summary(y, pred)})

    pd.DataFrame(rows).to_csv(out_dir / "salem_deep_models.csv", index=False)

    summary = {
        "salem_sessions": int(len(report)),
        "chat_files": int(len(structural)),
        "structural_success": int((structural["extract_error"].fillna("") == "").sum()),
        "model_rows_with_wab": int(len(model_df)),
        "n_structural_cols": int(len(structural_cols)),
        "n_observed_concept_cols": int(len(observed_cols)),
        "n_augmented_concept_cols": int(len(augmented_cols)),
        "n_target_cols": int(len(target_cols)),
    }
    pd.DataFrame([summary]).to_csv(out_dir / "salem_deep_audit.csv", index=False)
    print(pd.DataFrame([summary]).to_string(index=False))
    print(pd.read_csv(out_dir / "salem_deep_models.csv").to_string(index=False))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
