"""Control analyses for the Salem/Cinderella concept-coverage signal.

The deep Salem run showed observed Cinderella concept features outperform
structural discourse features for WAB-AQ prediction. This script asks whether
that signal is merely verbosity/MLU, or whether narrative content landmarks
carry independent severity information.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import (  # noqa: E402
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--joined", default="outputs/salem_cinderella_deep/salem_deep_joined.csv", type=Path)
    p.add_argument("--output-dir", default="outputs/salem_concept_controls", type=Path)
    p.add_argument("--cv-folds", default=5, type=int)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    df = pd.read_csv(args.joined)
    df = df[df["extract_error"].fillna("") == ""].copy()
    df = df.dropna(subset=["wab_aq", "participant_id"]).reset_index(drop=True)
    df["corpus"] = df["file_path"].fillna("").apply(_corpus_from_path)

    concept_binary = sorted(
        c for c in df.columns
        if c.startswith("observed_concept_") and c not in {"observed_concept_coverage", "observed_concept_density"}
    )
    augmented_binary = sorted(
        c for c in df.columns
        if c.startswith("augmented_concept_") and c not in {"augmented_concept_coverage", "augmented_concept_density"}
    )
    verbosity = [
        c for c in [
            "observed_n_tokens",
            "total_words",
            "log_total_tokens",
            "n_utterances",
            "mlu_words",
            "mlu_morphemes",
            "utt_len_mean",
            "utt_len_std",
            "ndw",
        ]
        if c in df.columns
    ]
    structural_core = [
        c for c in [
            "function_word_ratio",
            "hapax_ratio",
            "single_word_ratio",
            "verbs_per_utterance",
            "pos_unique_tags",
            "pos_n_frac",
            "pos_v_frac",
            "pos_aux_frac",
            "pos_pro_frac",
            "pos_det_frac",
            "mean_dep_distance",
            "unique_head_dep_pairs",
            "unique_head_rel_dep_triples",
        ]
        if c in df.columns
    ]
    observed_counts = [
        c for c in ["observed_concept_coverage", "observed_concept_density", "observed_n_tokens"]
        if c in df.columns
    ]
    augmented_counts = [
        c for c in ["augmented_concept_coverage", "augmented_concept_density", "augmented_n_tokens"]
        if c in df.columns
    ]

    setups: dict[str, tuple[dict[str, list[str]], list[str]]] = {
        "verbosity_only": ({"verbosity": verbosity}, []),
        "structural_core_no_verbosity": ({"structure": structural_core}, []),
        "observed_count_only": ({"concept": ["observed_concept_coverage"]}, []),
        "observed_density_only": ({"concept": ["observed_concept_density"]}, []),
        "observed_binary_only": ({"concept": concept_binary}, []),
        "observed_all_no_target": ({"concept": observed_counts + concept_binary}, []),
        "verbosity+observed_binary": ({"verbosity": verbosity, "concept": concept_binary}, []),
        "verbosity+observed_all": ({"verbosity": verbosity, "concept": observed_counts + concept_binary}, []),
        "structure+observed_binary": ({"structure": structural_core + verbosity, "concept": concept_binary}, []),
        "structure+observed_all": ({"structure": structural_core + verbosity, "concept": observed_counts + concept_binary}, []),
        "augmented_binary_only": ({"concept": augmented_binary}, []),
        "augmented_all": ({"concept": augmented_counts + augmented_binary}, []),
        "target_count_only": ({"target": ["target_word_count"]}, []),
        "wab_type_only": ({}, ["wab_type"]),
        "wab_type+observed_all": ({"concept": observed_counts + concept_binary}, ["wab_type"]),
    }

    rows = []
    for setup, (blocks, cats) in setups.items():
        blocks = {k: v for k, v in blocks.items() if v}
        if not blocks and not cats:
            continue
        sub = df.copy()
        if cats:
            sub = sub.dropna(subset=cats)
        for cv_name, group_col in [
            ("participant_grouped", "participant_id"),
            ("corpus_held_out", "corpus"),
        ]:
            y, pred = cross_val_predict_regressor(
                sub,
                "wab_aq",
                blocks,
                categorical_cols=cats,
                group_col=group_col,
                cv_mode="group",
                n_splits=args.cv_folds,
            )
            rows.append({"setup": setup, "cv": cv_name, **regression_summary(y, pred)})

    pd.DataFrame(rows).sort_values("r", ascending=False).to_csv(
        out_dir / "concept_control_models.csv",
        index=False,
    )

    corr_rows = []
    for col in concept_binary + ["observed_concept_coverage", "observed_concept_density", "observed_n_tokens"]:
        corr_rows.append({"feature": col, "r_wab_aq": pearson_safe(df[col], df["wab_aq"])})
    pd.DataFrame(corr_rows).sort_values("r_wab_aq", ascending=False).to_csv(
        out_dir / "concept_feature_correlations.csv",
        index=False,
    )

    print(pd.read_csv(out_dir / "concept_control_models.csv").to_string(index=False))
    print(f"Done. Outputs in {out_dir.resolve()}")


def _corpus_from_path(path: str) -> str:
    parts = Path(path).parts
    if "Aphasia" in parts:
        i = parts.index("Aphasia")
        if i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


if __name__ == "__main__":
    main()
