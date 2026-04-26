"""Cross-prompt stimulus-conditioned content experiment.

Experiment #51 made Cinderella concept coverage the strongest current signal.
This script asks whether that is a Cinderella-only result or a broader
property of elicited discourse: for a known prompt, does mention of expected
event concepts predict aphasia severity better than generic verbosity/form?

The script reads raw AphasiaBank CHAT files, splits PAR speech by @G task
blocks, scores hand-built concept lexicons for several high-frequency
protocol prompts, and evaluates WAB-AQ prediction with patient-grouped CV.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.review_grade import (  # noqa: E402
    bootstrap_ci,
    cross_val_predict_regressor,
    ensure_dir,
    pearson_safe,
    regression_summary,
)
from src.ingestion.aphasiabank import parse_cha_par_metadata  # noqa: E402


FUNCTION_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "but", "by",
    "for", "from", "he", "her", "hers", "him", "his", "i", "in", "is",
    "it", "its", "me", "my", "of", "on", "or", "our", "ours", "she",
    "so", "that", "the", "their", "them", "then", "there", "they", "this",
    "to", "was", "we", "were", "with", "you", "your",
}

TASK_ALIASES = {
    "cinderella": "Cinderella",
    "window": "Window",
    "umbrella": "Umbrella",
    "cat": "Cat",
    "sandwich": "Sandwich",
    "sandwich_picture": "Sandwich",
    "flood": "Flood",
    "cookie": "Cookie",
}

CONCEPTS = {
    "Cinderella": {
        "cinderella": ["cinderella"],
        "stepfamily": ["stepmother", "stepsister", "stepsisters", "sister", "sisters"],
        "prince": ["prince"],
        "ball": ["ball", "dance", "party"],
        "chores": ["clean", "sweep", "scrub", "work"],
        "fairy_godmother": ["fairy", "godmother"],
        "magic": ["magic", "magical"],
        "dress": ["dress", "gown"],
        "carriage": ["carriage", "coach", "pumpkin"],
        "midnight": ["midnight", "twelve"],
        "slipper": ["slipper", "shoe", "glass"],
        "loss": ["lost", "left", "leave"],
        "fit": ["fit", "fits", "try", "tried"],
        "marriage": ["marry", "married", "wedding"],
        "castle": ["castle", "palace"],
    },
    "Window": {
        "boy": ["boy", "kid", "child", "son"],
        "soccer_ball": ["soccer", "ball", "football"],
        "kick": ["kick", "kicked", "kicking", "hit"],
        "window": ["window", "glass"],
        "break": ["break", "broke", "broken", "smash", "smashed", "shatter"],
        "house": ["house", "home", "neighbor", "neighbour"],
        "man": ["man", "guy", "person", "neighbor", "neighbour"],
        "chair": ["chair", "sitting", "sat"],
        "inside": ["inside", "room", "living"],
        "look": ["look", "looks", "saw", "see"],
        "angry": ["angry", "mad", "upset", "happy"],
        "run_away": ["run", "ran", "gone", "away", "left"],
    },
    "Umbrella": {
        "boy": ["boy", "son", "child", "kid"],
        "mother": ["mother", "mom", "mum", "woman"],
        "umbrella": ["umbrella"],
        "rain": ["rain", "raining", "rainy", "pouring"],
        "outside": ["outside", "out", "walk", "school"],
        "refusal": ["no", "not", "without", "refuse", "want"],
        "wet": ["wet", "drenched", "soaked"],
        "return_home": ["home", "back", "return", "came"],
        "take": ["take", "takes", "took", "carry", "brought"],
        "lesson": ["again", "next", "time", "learn"],
    },
    "Cat": {
        "cat": ["cat", "kitty", "kitten"],
        "dog": ["dog"],
        "chase": ["chase", "chased", "bark", "barking", "scare", "scared"],
        "girl": ["girl", "daughter", "child"],
        "father": ["father", "dad", "man"],
        "tree": ["tree"],
        "climb": ["climb", "climbed", "up"],
        "stuck": ["stuck", "afraid", "scared"],
        "ladder": ["ladder"],
        "firefighters": ["fireman", "firemen", "firefighter", "firefighters", "department"],
        "rescue": ["rescue", "save", "help", "helped"],
        "call": ["call", "called", "phone"],
    },
    "Sandwich": {
        "bread": ["bread", "slice", "slices"],
        "peanut": ["peanut"],
        "butter": ["butter"],
        "jelly": ["jelly", "jam", "honey"],
        "knife": ["knife"],
        "spread": ["spread"],
        "put_on": ["put", "place", "on"],
        "together": ["together", "two"],
        "cut": ["cut"],
        "eat": ["eat", "ate"],
        "plate": ["plate"],
        "sandwich": ["sandwich"],
    },
    "Flood": {
        "water": ["water", "flood", "river"],
        "boy": ["boy", "child", "kid"],
        "girl": ["girl", "child", "kid"],
        "man": ["man", "person", "father", "dad"],
        "tree": ["tree", "branch"],
        "stuck": ["stuck", "trapped"],
        "rescue": ["rescue", "save", "help", "helped"],
        "boat": ["boat", "raft"],
        "rope": ["rope"],
        "storm": ["storm", "rain"],
    },
    "Cookie": {
        "boy": ["boy", "son", "child"],
        "girl": ["girl", "daughter", "child"],
        "mother": ["mother", "mom", "woman"],
        "cookie": ["cookie", "cookies"],
        "jar": ["jar"],
        "stool": ["stool", "chair"],
        "fall": ["fall", "falling", "fell"],
        "sink": ["sink"],
        "water": ["water", "overflow"],
        "dishes": ["dish", "dishes", "plate"],
    },
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="data/raw/aphasiabank/Protocol", type=Path)
    p.add_argument("--output-dir", default="outputs/cross_prompt_content", type=Path)
    p.add_argument("--cv-folds", default=5, type=int)
    p.add_argument("--min-tokens", default=5, type=int)
    p.add_argument("--max-files", default=0, type=int)
    return p.parse_args()


def normalize_task(label: str) -> str | None:
    key = label.strip().lower().replace("-", "_")
    key = re.sub(r"\s+", "_", key)
    return TASK_ALIASES.get(key)


def parse_task_utterances(path: Path) -> dict[str, list[str]]:
    segments: dict[str, list[str]] = defaultdict(list)
    current_task: str | None = None
    current_speaker: str | None = None
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return {}

    for raw in lines:
        if raw.startswith("@G:"):
            current_task = normalize_task(raw.split(":", 1)[1])
            current_speaker = None
            continue
        if raw.startswith("*") and ":" in raw:
            speaker, payload = raw[1:].split(":", 1)
            current_speaker = speaker.strip()
            if current_task and current_speaker == "PAR":
                segments[current_task].append(payload.strip())
            continue
        if raw.startswith("\t") and current_task and current_speaker == "PAR":
            if segments[current_task]:
                segments[current_task][-1] += " " + raw.strip()
    return dict(segments)


TARGET_RE = re.compile(r"\[:\s*([^\]]+)\]")


def chat_tokens(text: str, include_targets: bool = False) -> list[str]:
    target_text = " ".join(TARGET_RE.findall(text)) if include_targets else ""
    text = re.sub(r"\x15[^\x15]*\x15", " ", text)
    text = re.sub(r"<([^>]*)>", r" \1 ", text)
    text = text.replace("_", " ")
    text = text.replace("(", "").replace(")", "")
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"&\*INV:[^\s]+", " ", text)
    text = re.sub(r"&[=+\-]?[^\s]+", " ", text)
    text = re.sub(r"([A-Za-z]+)@[A-Za-z:]+", r"\1", text)
    text = f"{text} {target_text}"
    toks = re.findall(r"[a-z]+", text.lower())
    return [t for t in toks if t not in {"xxx", "yyy", "www", "unk", "u", "q"}]


def stem(token: str) -> str:
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 3 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def concept_hits(tokens: list[str], task: str) -> dict[str, int]:
    token_set = set(tokens)
    stem_set = {stem(t) for t in tokens}
    hits = {}
    for concept, terms in CONCEPTS[task].items():
        expanded = set()
        for term in terms:
            expanded.add(term)
            expanded.add(stem(term))
        hits[concept] = int(bool((token_set | stem_set) & expanded))
    return hits


def structural_features(utterance_tokens: list[list[str]]) -> dict[str, float]:
    tokens = [t for utt in utterance_tokens for t in utt]
    n_tokens = len(tokens)
    n_utts = len([utt for utt in utterance_tokens if utt])
    unique = len(set(tokens))
    content = [t for t in tokens if t not in FUNCTION_WORDS]
    lengths = [len(utt) for utt in utterance_tokens if utt]
    return {
        "n_tokens": float(n_tokens),
        "n_utterances": float(n_utts),
        "mean_utt_tokens": float(np.mean(lengths)) if lengths else 0.0,
        "std_utt_tokens": float(np.std(lengths)) if lengths else 0.0,
        "type_token_ratio": float(unique / max(n_tokens, 1)),
        "content_word_ratio": float(len(content) / max(n_tokens, 1)),
        "function_word_ratio": float(1.0 - len(content) / max(n_tokens, 1)),
        "single_word_utt_ratio": float(sum(1 for x in lengths if x <= 1) / max(n_utts, 1)),
    }


def concept_features(tokens: list[str], task: str, prefix: str) -> dict[str, float]:
    hits = concept_hits(tokens, task)
    n_concepts = len(CONCEPTS[task])
    coverage = int(sum(hits.values()))
    concept_vocab = {stem(term) for terms in CONCEPTS[task].values() for term in terms}
    concept_token_count = sum(1 for tok in tokens if stem(tok) in concept_vocab)
    task_key = task.lower()
    out = {
        f"{prefix}_concept_coverage": float(coverage),
        f"{prefix}_concept_coverage_frac": float(coverage / n_concepts),
        f"{prefix}_concept_density": float(coverage / max(len(tokens), 1)),
        f"{prefix}_concept_token_ratio": float(concept_token_count / max(len(tokens), 1)),
    }
    out.update({f"{prefix}_{task_key}_{name}": float(v) for name, v in hits.items()})
    return out


def patient_root(participant_id: str) -> str:
    return re.sub(r"[A-Za-z]$", "", str(participant_id))


def build_segments(root: Path, min_tokens: int, max_files: int = 0) -> pd.DataFrame:
    rows = []
    paths = sorted(root.rglob("*.cha"))
    if max_files:
        paths = paths[:max_files]
    for path in paths:
        meta_records = parse_cha_par_metadata(path)
        if not meta_records:
            continue
        meta = meta_records[0]
        segments = parse_task_utterances(path)
        if not segments:
            continue
        for task, utts in segments.items():
            observed_utts = [chat_tokens(u, include_targets=False) for u in utts]
            observed_tokens = [t for utt in observed_utts for t in utt]
            if len(observed_tokens) < min_tokens:
                continue
            augmented_tokens = chat_tokens(" ".join(utts), include_targets=True)
            row = {
                "transcript_id": meta.transcript_id,
                "section": meta.section,
                "corpus": meta.corpus,
                "participant_id": meta.participant_id,
                "patient_root": patient_root(meta.participant_id),
                "task": task,
                "subtype": meta.subtype,
                "wab_aq": meta.wab_aq,
                "age_years": meta.age_years,
                "sex": meta.sex,
                "is_control": bool(meta.is_control),
                "session_date": meta.session_date,
                "file_path": str(path.resolve()),
                "n_concepts": float(len(CONCEPTS[task])),
                "observed_n_tokens": float(len(observed_tokens)),
                "target_augmented_n_tokens": float(len(augmented_tokens)),
            }
            row.update(structural_features(observed_utts))
            row.update(concept_features(observed_tokens, task, "observed"))
            row.update(concept_features(augmented_tokens, task, "target_augmented"))
            rows.append(row)
    return pd.DataFrame(rows)


def add_control_norms(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = df.copy()
    rows = []
    for task, group in out.groupby("task"):
        controls = group[group["is_control"]]
        if len(controls) < 5:
            controls = group[group["subtype"].eq("Control")]
        for prefix in ["observed", "target_augmented"]:
            col = f"{prefix}_concept_coverage_frac"
            vals = controls[col].dropna().astype(float)
            if len(vals) < 5:
                mean = float(group[col].mean())
                sd = float(group[col].std(ddof=0) or 1.0)
                source = "all_rows"
            else:
                mean = float(vals.mean())
                sd = float(vals.std(ddof=0) or 1.0)
                source = "controls"
            if sd == 0:
                sd = 1.0
            mask = out["task"].eq(task)
            out.loc[mask, f"{prefix}_control_z"] = (out.loc[mask, col] - mean) / sd
            out.loc[mask, f"{prefix}_control_gap"] = out.loc[mask, col] - mean
            out.loc[mask, f"{prefix}_control_pct"] = out.loc[mask, col] / max(mean, 1e-6)
            rows.append(
                {
                    "task": task,
                    "prefix": prefix,
                    "source": source,
                    "n_controls": int(len(vals)),
                    "mean_coverage_frac": mean,
                    "sd_coverage_frac": sd,
                }
            )
    return out, pd.DataFrame(rows)


def metric_row(
    df: pd.DataFrame,
    setup: str,
    y: np.ndarray,
    pred: np.ndarray,
    group_col: str = "patient_root",
) -> dict[str, float | int | str]:
    groups = df[group_col].astype(str).to_numpy()
    r_mean, r_lo, r_hi = bootstrap_ci(
        y,
        pred,
        pearson_safe,
        groups=groups,
        n_boot=500,
        seed=0,
    )
    return {
        "setup": setup,
        **regression_summary(y, pred),
        "r_boot_mean": r_mean,
        "r_boot_lo": r_lo,
        "r_boot_hi": r_hi,
    }


def run_grouped_model(
    df: pd.DataFrame,
    setup: str,
    blocks: dict[str, list[str]],
    cats: list[str] | None,
    cv_folds: int,
) -> dict[str, float | int | str]:
    work = df.dropna(subset=["wab_aq", "patient_root"]).reset_index(drop=True)
    if "is_control" in work.columns:
        work = work[~work["is_control"].astype(bool)].reset_index(drop=True)
    if cats:
        work = work.dropna(subset=cats).reset_index(drop=True)
    y, pred = cross_val_predict_regressor(
        work,
        "wab_aq",
        blocks,
        categorical_cols=cats,
        group_col="patient_root",
        cv_mode="group",
        n_splits=cv_folds,
    )
    return metric_row(work, setup, y, pred)


def task_specific_models(df: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    structural = [
        "n_tokens",
        "n_utterances",
        "mean_utt_tokens",
        "std_utt_tokens",
        "type_token_ratio",
        "content_word_ratio",
        "function_word_ratio",
        "single_word_utt_ratio",
    ]
    rows = []
    pwa = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy()
    for task, group in pwa.groupby("task"):
        group = group[group["patient_root"].notna()].reset_index(drop=True)
        if len(group) < 50 or group["patient_root"].nunique() < 10:
            continue
        task_key = task.lower()
        observed_binary = sorted(c for c in group.columns if c.startswith(f"observed_{task_key}_"))
        target_binary = sorted(c for c in group.columns if c.startswith(f"target_augmented_{task_key}_"))
        setups = {
            "verbosity": ({"verbosity": ["observed_n_tokens", "n_utterances", "mean_utt_tokens"]}, None),
            "structure_light": ({"structure": structural}, None),
            "observed_count": (
                {"content": ["observed_concept_coverage", "observed_concept_coverage_frac", "observed_concept_density"]},
                None,
            ),
            "observed_binary": ({"content": observed_binary}, None),
            "observed_all": (
                {
                    "content": [
                        "observed_concept_coverage",
                        "observed_concept_coverage_frac",
                        "observed_concept_density",
                        "observed_concept_token_ratio",
                    ]
                    + observed_binary
                },
                None,
            ),
            "target_augmented_all": (
                {
                    "content": [
                        "target_augmented_concept_coverage",
                        "target_augmented_concept_coverage_frac",
                        "target_augmented_concept_density",
                        "target_augmented_concept_token_ratio",
                    ]
                    + target_binary
                },
                None,
            ),
            "structure+observed": (
                {
                    "structure": structural,
                    "content": [
                        "observed_concept_coverage",
                        "observed_concept_coverage_frac",
                        "observed_concept_density",
                    ]
                    + observed_binary,
                },
                None,
            ),
        }
        for setup, (blocks, cats) in setups.items():
            blocks = {name: [c for c in cols if c in group.columns] for name, cols in blocks.items()}
            blocks = {name: cols for name, cols in blocks.items() if cols}
            try:
                row = run_grouped_model(group, setup, blocks, cats, cv_folds)
            except Exception as exc:
                row = {"setup": setup, "error": type(exc).__name__}
            row.update(
                {
                    "task": task,
                    "n_rows": int(len(group)),
                    "n_patients": int(group["patient_root"].nunique()),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def pooled_models(df: pd.DataFrame, cv_folds: int) -> pd.DataFrame:
    model_df = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy().reset_index(drop=True)
    structural = [
        "n_tokens",
        "n_utterances",
        "mean_utt_tokens",
        "std_utt_tokens",
        "type_token_ratio",
        "content_word_ratio",
        "function_word_ratio",
        "single_word_utt_ratio",
    ]
    verbosity = ["observed_n_tokens", "n_utterances", "mean_utt_tokens"]
    observed_invariant = [
        "observed_concept_coverage",
        "observed_concept_coverage_frac",
        "observed_concept_density",
        "observed_concept_token_ratio",
        "observed_control_z",
        "observed_control_gap",
        "observed_control_pct",
    ]
    target_invariant = [
        "target_augmented_concept_coverage",
        "target_augmented_concept_coverage_frac",
        "target_augmented_concept_density",
        "target_augmented_concept_token_ratio",
        "target_augmented_control_z",
        "target_augmented_control_gap",
        "target_augmented_control_pct",
    ]
    setups = {
        "task_only": ({}, ["task"]),
        "verbosity+task": ({"verbosity": verbosity}, ["task"]),
        "structure+task": ({"structure": structural}, ["task"]),
        "observed_content_no_task": ({"content": observed_invariant}, None),
        "observed_content+task": ({"content": observed_invariant}, ["task"]),
        "target_augmented_content+task": ({"content": target_invariant}, ["task"]),
        "structure+observed+task": ({"structure": structural, "content": observed_invariant}, ["task"]),
        "subtype_only": ({}, ["subtype"]),
        "subtype+observed+task": ({"content": observed_invariant}, ["subtype", "task"]),
    }
    rows = []
    for setup, (blocks, cats) in setups.items():
        sub = model_df.copy()
        if cats:
            sub = sub.dropna(subset=cats).reset_index(drop=True)
        blocks = {name: [c for c in cols if c in sub.columns] for name, cols in blocks.items()}
        blocks = {name: cols for name, cols in blocks.items() if cols}
        if not blocks and not cats:
            continue
        try:
            row = run_grouped_model(sub, setup, blocks, cats, cv_folds)
        except Exception as exc:
            row = {"setup": setup, "error": type(exc).__name__}
        row.update({"n_rows": int(len(sub)), "n_patients": int(sub["patient_root"].nunique())})
        rows.append(row)
    return pd.DataFrame(rows)


def leave_task_out_models(df: pd.DataFrame) -> pd.DataFrame:
    work = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy().reset_index(drop=True)
    features = [
        "observed_concept_coverage_frac",
        "observed_concept_density",
        "observed_concept_token_ratio",
        "observed_control_z",
        "observed_control_gap",
        "observed_control_pct",
        "observed_n_tokens",
        "n_utterances",
        "mean_utt_tokens",
    ]
    rows = []
    for held_task, test in work.groupby("task"):
        train = work[work["task"] != held_task].copy()
        test = test.copy()
        if len(train) < 50 or len(test) < 30:
            continue
        model = Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                (
                    "model",
                    GradientBoostingRegressor(
                        n_estimators=120,
                        max_depth=3,
                        learning_rate=0.05,
                        subsample=0.9,
                        random_state=0,
                    ),
                ),
            ]
        )
        model.fit(train[features], train["wab_aq"].astype(float))
        pred = model.predict(test[features])
        y = test["wab_aq"].astype(float).to_numpy()
        rows.append(
            {
                "held_out_task": held_task,
                "split": "leave_task_out_participants_may_overlap",
                "n_train": int(len(train)),
                "n_test": int(len(test)),
                "n_test_patients": int(test["patient_root"].nunique()),
                **regression_summary(y, pred),
            }
        )

        disjoint = train[~train["patient_root"].isin(test["patient_root"])].copy()
        if len(disjoint) >= 50 and disjoint["patient_root"].nunique() >= 10:
            model2 = clone(model)
            model2.fit(disjoint[features], disjoint["wab_aq"].astype(float))
            pred2 = model2.predict(test[features])
            rows.append(
                {
                    "held_out_task": held_task,
                    "split": "leave_task_out_patient_disjoint",
                    "n_train": int(len(disjoint)),
                    "n_test": int(len(test)),
                    "n_test_patients": int(test["patient_root"].nunique()),
                    **regression_summary(y, pred2),
                }
            )
    return pd.DataFrame(rows)


def raw_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cols = [
        "observed_n_tokens",
        "n_utterances",
        "mean_utt_tokens",
        "observed_concept_coverage",
        "observed_concept_coverage_frac",
        "observed_concept_density",
        "observed_control_z",
        "target_augmented_concept_coverage_frac",
        "target_augmented_concept_density",
    ]
    work = df[df["wab_aq"].notna() & ~df["is_control"].astype(bool)].copy()
    for task, group in work.groupby("task"):
        for col in cols:
            if col in group.columns:
                rows.append(
                    {
                        "task": task,
                        "feature": col,
                        "n": int(group[[col, "wab_aq"]].dropna().shape[0]),
                        "r_wab_aq": pearson_safe(group[col], group["wab_aq"]),
                    }
                )
    for col in cols:
        if col in work.columns:
            rows.append(
                {
                    "task": "__pooled__",
                    "feature": col,
                    "n": int(work[[col, "wab_aq"]].dropna().shape[0]),
                    "r_wab_aq": pearson_safe(work[col], work["wab_aq"]),
                }
            )
    return pd.DataFrame(rows)


def write_summary(out_dir: Path, segments: pd.DataFrame, task_models: pd.DataFrame, pooled: pd.DataFrame, lto: pd.DataFrame) -> None:
    def md_table(frame: pd.DataFrame) -> str:
        if frame.empty:
            return ""
        data = frame.reset_index() if frame.index.name is not None else frame.copy()
        cols = list(data.columns)
        str_data = data.copy()
        for col in cols:
            if pd.api.types.is_float_dtype(str_data[col]):
                str_data[col] = str_data[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
            else:
                str_data[col] = str_data[col].map(lambda x: "" if pd.isna(x) else str(x))
        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join(["---"] * len(cols)) + " |"
        body = [
            "| " + " | ".join(str_data.loc[i, cols].astype(str).tolist()) + " |"
            for i in str_data.index
        ]
        return "\n".join([header, sep] + body)

    lines = []
    lines.append("# Cross-Prompt Content Summary\n")
    lines.append(f"- Segments: {len(segments)}")
    pwa_wab = segments[segments["wab_aq"].notna() & ~segments["is_control"].astype(bool)]
    lines.append(f"- WAB-labeled non-control segments: {int(len(pwa_wab))}")
    lines.append(f"- Patients/roots with WAB: {int(pwa_wab['patient_root'].nunique())}")
    lines.append("\n## Segment Counts\n")
    counts = segments.groupby("task").agg(
        n=("task", "size"),
        n_wab=("wab_aq", lambda s: int(s.notna().sum())),
        n_wab_noncontrol=("is_control", lambda s: int((segments.loc[s.index, "wab_aq"].notna() & ~s.astype(bool)).sum())),
        n_patients=("patient_root", "nunique"),
        n_controls=("is_control", "sum"),
    )
    lines.append(md_table(counts))
    if not pooled.empty:
        lines.append("\n## Best Pooled Models\n")
        view = pooled.sort_values("r", ascending=False).head(8)
        lines.append(md_table(view[["setup", "n", "mae", "r", "r_boot_lo", "r_boot_hi"]]))
    if not task_models.empty:
        lines.append("\n## Best Task-Specific Models\n")
        view = task_models.dropna(subset=["r"]).sort_values(["task", "r"], ascending=[True, False])
        view = view.groupby("task").head(3)
        lines.append(md_table(view[["task", "setup", "n", "mae", "r", "r_boot_lo", "r_boot_hi"]]))
    if not lto.empty:
        lines.append("\n## Leave-Task-Out Transfer\n")
        lines.append(md_table(lto.sort_values(["split", "held_out_task"])[["held_out_task", "split", "n_test", "mae", "r"]]))
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.output_dir)

    segments = build_segments(args.root, min_tokens=args.min_tokens, max_files=args.max_files)
    if segments.empty:
        raise RuntimeError(f"No task segments found under {args.root}")
    segments, norms = add_control_norms(segments)
    segments.to_csv(out_dir / "task_segments.csv", index=False)
    norms.to_csv(out_dir / "control_norms.csv", index=False)

    corr = raw_correlations(segments)
    corr.sort_values(["task", "r_wab_aq"], ascending=[True, False]).to_csv(
        out_dir / "feature_correlations.csv",
        index=False,
    )

    task_models = task_specific_models(segments, cv_folds=args.cv_folds)
    task_models.sort_values(["task", "r"], ascending=[True, False]).to_csv(
        out_dir / "task_model_results.csv",
        index=False,
    )

    pooled = pooled_models(segments, cv_folds=args.cv_folds)
    pooled.sort_values("r", ascending=False).to_csv(
        out_dir / "pooled_model_results.csv",
        index=False,
    )

    lto = leave_task_out_models(segments)
    lto.to_csv(out_dir / "leave_task_out_results.csv", index=False)

    write_summary(out_dir, segments, task_models, pooled, lto)

    print((out_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Done. Outputs in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
