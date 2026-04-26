"""Within-subtype severity prediction from Cinderella concepts.

Tests whether observed story-concept coverage captures continuous severity
inside WAB subtype labels. This is the clinically important version: a useful
state measure should explain why two people with the same subtype differ.
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
    p.add_argument("--output-dir", default="outputs/salem_within_subtype", type=Path)
    p.add_argument("--cv-folds", default=5, type=int)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    df = pd.read_csv(args.joined)
    df = df[df["extract_error"].fillna("") == ""].copy()
    df = df.dropna(subset=["wab_aq", "participant_id", "wab_type"]).reset_index(drop=True)

    observed_binary = sorted(
        c for c in df.columns
        if c.startswith("observed_concept_")
        and c not in {"observed_concept_coverage", "observed_concept_density"}
    )
    observed_all = ["observed_concept_coverage", "observed_concept_density", "observed_n_tokens"] + observed_binary
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
    setups = {
        "coverage_only": ["observed_concept_coverage"],
        "observed_all": observed_all,
        "verbosity_only": verbosity,
        "structural_core": structural_core,
        "verbosity+observed": verbosity + observed_all,
        "structure+observed": structural_core + verbosity + observed_all,
    }

    rows = []
    for subtype, group in df.groupby("wab_type"):
        if len(group) < 25 or group["participant_id"].nunique() < 10:
            continue
        for setup, cols in setups.items():
            y, pred = cross_val_predict_regressor(
                group.reset_index(drop=True),
                "wab_aq",
                {"features": cols},
                group_col="participant_id",
                cv_mode="group",
                n_splits=min(args.cv_folds, group["participant_id"].nunique()),
            )
            rows.append(
                {
                    "wab_type": subtype,
                    "setup": setup,
                    "n": len(group),
                    "n_participants": group["participant_id"].nunique(),
                    "raw_coverage_r": pearson_safe(group["observed_concept_coverage"], group["wab_aq"]),
                    **regression_summary(y, pred),
                }
            )
    out = pd.DataFrame(rows).sort_values(["wab_type", "r"], ascending=[True, False])
    out.to_csv(out_dir / "within_subtype_concept_models.csv", index=False)
    print(out.to_string(index=False))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
