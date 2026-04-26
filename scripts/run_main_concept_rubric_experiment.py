"""Parse public AphasiaBank Main Concept rubrics and score discourse.

This is a first-pass automated MCA replacement experiment. It extracts
bold/italic superscript-numbered essential slots from the public DOCX rubrics
and turns each slot plus nearby alternative productions into a conservative
lexicon. A main concept is counted complete when all required slots are hit.

The goal is not to claim full human-equivalent MCA scoring. The goal is to test
whether official rubric structure improves or cross-validates our hand-built
event-content state.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_cross_prompt_content import chat_tokens, stem  # noqa: E402
from src.analysis.review_grade import (  # noqa: E402
    bootstrap_ci,
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
STOP = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "him",
    "his",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "she",
    "that",
    "the",
    "their",
    "them",
    "they",
    "this",
    "to",
    "was",
    "were",
    "with",
    "you",
    "your",
}
TASK_DOCS = {
    "Window": "Window.docx",
    "Umbrella": "Umbrella.docx",
    "Cat": "Cat.docx",
    "Sandwich": "Sandwich.docx",
    "Cinderella": "Cinderella.docx",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rubric-dir",
        default="data/external/aphasiabank_discourse/main_concepts",
        type=Path,
    )
    parser.add_argument(
        "--segments-path",
        default="outputs/error_aware_reconstruction/segment_error_features.csv",
        type=Path,
    )
    parser.add_argument("--output-dir", default="outputs/main_concept_rubric", type=Path)
    parser.add_argument("--cv-folds", default=5, type=int)
    return parser.parse_args()


def run_text(run: ET.Element) -> str:
    return "".join(t.text or "" for t in run.findall(".//w:t", NS))


def run_flags(run: ET.Element) -> tuple[bool, bool, bool]:
    props = run.find("w:rPr", NS)
    if props is None:
        return False, False, False
    bold = props.find("w:b", NS) is not None
    italic = props.find("w:i", NS) is not None
    va = props.find("w:vertAlign", NS)
    superscript = va is not None and va.attrib.get(f"{{{NS['w']}}}val") == "superscript"
    return bold, italic, superscript


def paragraph_runs(par: ET.Element) -> list[dict[str, object]]:
    rows = []
    for run in par.findall(".//w:r", NS):
        text = run_text(run)
        if not text:
            continue
        bold, italic, superscript = run_flags(run)
        rows.append({"text": text, "bold": bold, "italic": italic, "superscript": superscript})
    return rows


def paragraph_text(par: ET.Element) -> str:
    return "".join(str(r["text"]) for r in paragraph_runs(par)).strip()


def is_concept_start(runs: list[dict[str, object]]) -> bool:
    slot_nums = [
        str(r["text"]).strip()
        for r in runs
        if r["superscript"] and re.fullmatch(r"\d+", str(r["text"]).strip())
    ]
    return "1" in slot_nums and len(slot_nums) >= 2


def extract_slots(runs: list[dict[str, object]]) -> dict[int, str]:
    slots: dict[int, list[str]] = {}
    current: int | None = None
    for r in runs:
        text = str(r["text"])
        stripped = text.strip()
        if r["superscript"] and re.fullmatch(r"\d+", stripped):
            current = int(stripped)
            slots.setdefault(current, [])
            continue
        if current is None:
            continue
        # Most essential text is bold+italic, but a few DOCX runs split a
        # required phrase into normal text. Keep short text until the next slot.
        if len(text) <= 80:
            slots[current].append(text)
    return {k: re.sub(r"\s+", " ", "".join(v)).strip(" .;:") for k, v in slots.items()}


def is_alt_line(text: str) -> bool:
    low = text.lower().strip()
    if not low or low.startswith("note") or low.startswith("†") or low.startswith("from"):
        return False
    if low.startswith("see "):
        return False
    if "indicates concepts" in low or "essential information" in low:
        return False
    return True


def clean_terms(texts: list[str]) -> list[str]:
    terms = set()
    joined = " ".join(texts)
    joined = re.sub(r"[*†“”\"()\\[\\]]", " ", joined)
    pieces = re.split(r",|;|/| and/or | or similar| etc\.?", joined, flags=re.IGNORECASE)
    for piece in pieces:
        toks = [stem(t) for t in re.findall(r"[a-z]+", piece.lower())]
        toks = [t for t in toks if len(t) > 1 and t not in STOP and not t.startswith("see")]
        if not toks:
            continue
        if len(toks) == 1:
            terms.add(toks[0])
        else:
            # Keep both individual content words and short phrases. Individual
            # words make the scorer robust to aphasic word order.
            terms.update(toks)
            if len(toks) <= 3:
                terms.add(" ".join(toks))
    return sorted(terms)


def parse_rubric_doc(path: Path, task: str) -> pd.DataFrame:
    with ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    paragraphs = root.findall(".//w:p", NS)
    rows = []
    concept_id = 0
    i = 0
    while i < len(paragraphs):
        runs = paragraph_runs(paragraphs[i])
        if not is_concept_start(runs):
            i += 1
            continue
        concept_id += 1
        slots = extract_slots(runs)
        alt_by_slot: dict[int, list[str]] = {slot: [] for slot in slots}
        j = i + 1
        alt_slot = 1
        while j < len(paragraphs):
            next_runs = paragraph_runs(paragraphs[j])
            if is_concept_start(next_runs):
                break
            text = paragraph_text(paragraphs[j])
            if is_alt_line(text) and alt_slot in alt_by_slot:
                alt_by_slot[alt_slot].append(text)
                alt_slot += 1
            j += 1
        for slot, slot_text in sorted(slots.items()):
            terms = clean_terms([slot_text] + alt_by_slot.get(slot, []))
            rows.append(
                {
                    "task": task,
                    "rubric_concept_id": concept_id,
                    "slot": slot,
                    "slot_text": slot_text,
                    "alternatives": " | ".join(alt_by_slot.get(slot, [])),
                    "terms": "|".join(terms),
                    "n_terms": len(terms),
                }
            )
        i = j
    return pd.DataFrame(rows)


def parse_all_rubrics(rubric_dir: Path) -> pd.DataFrame:
    frames = []
    for task, name in TASK_DOCS.items():
        path = rubric_dir / name
        if path.exists():
            frames.append(parse_rubric_doc(path, task))
    return pd.concat(frames, ignore_index=True)


def hit_slot(tokens: set[str], terms: list[str]) -> bool:
    for term in terms:
        term_toks = [stem(t) for t in re.findall(r"[a-z]+", term.lower())]
        if not term_toks:
            continue
        if all(tok in tokens for tok in term_toks):
            return True
    return False


def score_segment(tokens: list[str], task: str, rubric: pd.DataFrame) -> dict[str, float]:
    task_rubric = rubric[rubric["task"].eq(task)]
    token_set = {stem(t) for t in tokens}
    complete = 0
    partial_sum = 0.0
    n_concepts = 0
    slot_hits = 0
    slot_total = 0
    for concept_id, group in task_rubric.groupby("rubric_concept_id"):
        slot_results = []
        for _, row in group.iterrows():
            terms = [t for t in str(row["terms"]).split("|") if t]
            ok = hit_slot(token_set, terms)
            slot_results.append(ok)
        if not slot_results:
            continue
        n_concepts += 1
        slot_total += len(slot_results)
        slot_hits += sum(slot_results)
        frac = sum(slot_results) / len(slot_results)
        partial_sum += frac
        complete += int(all(slot_results))
    return {
        "mca_n_concepts": float(n_concepts),
        "mca_complete": float(complete),
        "mca_complete_frac": float(complete / max(n_concepts, 1)),
        "mca_partial": float(partial_sum),
        "mca_partial_frac": float(partial_sum / max(n_concepts, 1)),
        "mca_slot_hit_frac": float(slot_hits / max(slot_total, 1)),
    }


def score_segments(segments: pd.DataFrame, rubric: pd.DataFrame) -> pd.DataFrame:
    rows = []
    valid_tasks = set(rubric["task"].unique())
    for _, row in segments[segments["task"].isin(valid_tasks)].iterrows():
        raw = str(row["raw_task_text"])
        observed = score_segment(chat_tokens(raw, include_targets=False), str(row["task"]), rubric)
        augmented = score_segment(chat_tokens(raw, include_targets=True), str(row["task"]), rubric)
        out = {
            "transcript_id": row["transcript_id"],
            "participant_id": row["participant_id"],
            "patient_root": row["patient_root"],
            "corpus": row["corpus"],
            "task": row["task"],
            "subtype": row["subtype"],
            "wab_aq": row["wab_aq"],
            "is_control": row["is_control"],
            "observed_concept_coverage_frac": row["observed_concept_coverage_frac"],
            "target_augmented_concept_coverage_frac": row[
                "target_augmented_concept_coverage_frac"
            ],
            "observed_n_tokens": row["observed_n_tokens"],
            "error_rate_100": row["error_rate_100"],
        }
        out.update({f"observed_{k}": v for k, v in observed.items()})
        out.update({f"target_augmented_{k}": v for k, v in augmented.items()})
        rows.append(out)
    return pd.DataFrame(rows)


def metric_row(work: pd.DataFrame, setup: str, y: np.ndarray, pred: np.ndarray) -> dict:
    groups = work["patient_root"].astype(str).to_numpy()
    r_mean, r_lo, r_hi = bootstrap_ci(y, pred, pearson_safe, groups=groups, n_boot=500, seed=0)
    return {
        "setup": setup,
        **regression_summary(y, pred),
        "r_boot_mean": r_mean,
        "r_boot_lo": r_lo,
        "r_boot_hi": r_hi,
        "n_patients": int(work["patient_root"].nunique()),
    }


def run_models(scores: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    work = scores[scores["wab_aq"].notna() & ~scores["is_control"].astype(bool)].copy()
    work = work.dropna(subset=["patient_root"]).reset_index(drop=True)
    setups = {
        "heuristic_content+task": (
            {"heuristic": ["observed_concept_coverage_frac"]},
            ["task"],
        ),
        "mca_complete+task": (
            {"mca": ["observed_mca_complete_frac"]},
            ["task"],
        ),
        "mca_partial+task": (
            {"mca": ["observed_mca_partial_frac", "observed_mca_slot_hit_frac"]},
            ["task"],
        ),
        "heuristic+mca_partial+task": (
            {
                "heuristic": ["observed_concept_coverage_frac"],
                "mca": ["observed_mca_partial_frac", "observed_mca_slot_hit_frac"],
            },
            ["task"],
        ),
        "mca_augmented_partial+task": (
            {"mca": ["target_augmented_mca_partial_frac", "target_augmented_mca_slot_hit_frac"]},
            ["task"],
        ),
        "mca_partial+error+task": (
            {
                "mca": ["observed_mca_partial_frac", "observed_mca_slot_hit_frac"],
                "error": ["error_rate_100", "observed_n_tokens"],
            },
            ["task"],
        ),
    }
    rows = []
    for setup, (blocks, cats) in setups.items():
        y, pred = cross_val_predict_regressor(
            work,
            "wab_aq",
            blocks,
            categorical_cols=cats,
            group_col="patient_root",
            cv_mode="group",
            n_splits=cv_folds,
        )
        rows.append(metric_row(work, setup, y, pred))
    return pd.DataFrame(rows)


def summarize(scores: pd.DataFrame, rubric: pd.DataFrame, models: pd.DataFrame) -> str:
    task_counts = rubric.groupby("task").agg(
        n_concepts=("rubric_concept_id", "nunique"),
        n_slots=("slot", "size"),
        mean_terms_per_slot=("n_terms", "mean"),
    )
    task_scores = scores.groupby("task").agg(
        n=("task", "size"),
        mean_heuristic=("observed_concept_coverage_frac", "mean"),
        mean_mca_complete=("observed_mca_complete_frac", "mean"),
        mean_mca_partial=("observed_mca_partial_frac", "mean"),
        r_heuristic_mca_partial=(
            "observed_concept_coverage_frac",
            lambda s: pearson_safe(
                s,
                scores.loc[s.index, "observed_mca_partial_frac"],
            ),
        ),
    )
    pwa = scores[scores["wab_aq"].notna() & ~scores["is_control"].astype(bool)]
    corr = pd.DataFrame(
        [
            {
                "feature": "heuristic_observed_content",
                "r_wab_aq": pearson_safe(pwa["observed_concept_coverage_frac"], pwa["wab_aq"]),
            },
            {
                "feature": "mca_complete_frac",
                "r_wab_aq": pearson_safe(pwa["observed_mca_complete_frac"], pwa["wab_aq"]),
            },
            {
                "feature": "mca_partial_frac",
                "r_wab_aq": pearson_safe(pwa["observed_mca_partial_frac"], pwa["wab_aq"]),
            },
            {
                "feature": "mca_slot_hit_frac",
                "r_wab_aq": pearson_safe(pwa["observed_mca_slot_hit_frac"], pwa["wab_aq"]),
            },
        ]
    )

    def table(df: pd.DataFrame) -> str:
        data = df.reset_index() if df.index.name is not None else df.copy()
        for col in data.columns:
            if pd.api.types.is_float_dtype(data[col]):
                data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
            else:
                data[col] = data[col].astype(str)
        header = "| " + " | ".join(data.columns) + " |"
        sep = "| " + " | ".join(["---"] * len(data.columns)) + " |"
        body = ["| " + " | ".join(data.loc[i].astype(str).tolist()) + " |" for i in data.index]
        return "\n".join([header, sep] + body)

    lines = [
        "# Main Concept Rubric Experiment",
        "",
        f"- Rubric slots extracted: {len(rubric)}",
        f"- Rubric concepts extracted: {rubric[['task', 'rubric_concept_id']].drop_duplicates().shape[0]}",
        f"- Scored segments: {len(scores)}",
        "",
        "## Extracted Rubrics",
        "",
        table(task_counts),
        "",
        "## Segment Scores By Task",
        "",
        table(task_scores),
        "",
        "## Raw Correlations With WAB-AQ",
        "",
        table(corr),
        "",
        "## Patient-Grouped WAB Models",
        "",
        table(models.sort_values("r", ascending=False)[["setup", "n", "n_patients", "mae", "r", "r_boot_lo", "r_boot_hi"]]),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)
    rubric = parse_all_rubrics(args.rubric_dir)
    rubric.to_csv(out_dir / "extracted_rubric_slots.csv", index=False)

    segments = pd.read_csv(args.segments_path)
    scores = score_segments(segments, rubric)
    scores.to_csv(out_dir / "segment_mca_scores.csv", index=False)

    models = run_models(scores, args.cv_folds)
    models.to_csv(out_dir / "wab_model_results.csv", index=False)

    summary = summarize(scores, rubric, models)
    (out_dir / "summary.md").write_text(summary + "\n", encoding="utf-8")
    print(summary)
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
