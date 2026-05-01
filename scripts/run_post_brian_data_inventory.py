#!/usr/bin/env python3
"""Inventory local task types and stuttering-recovery feasibility.

This is a post-Brian-call planning script. It scans local CHAT headers and path
metadata, not utterance text, to estimate which corpora can support the minimum
language-state battery.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd


RAW_DIR = Path("data/raw")
STRUCTURED_OUT = Path("outputs/structured_task_inventory")
STUTTER_OUT = Path("outputs/stuttering_recovery_inventory")


TASK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sentence_repetition": (
        "sentence repetition",
        "sentence repeat",
        "repeating sentences",
        "repeat sentences",
        "sentrep",
        "sent rep",
    ),
    "nonword_repetition": (
        "nonword",
        "non-word",
        "non word",
        "pseudoword",
        "pseudo-word",
        "pseudo word",
        " nwr",
    ),
    "comprehension": (
        "comprehension",
        "receptive",
        "point to",
        "pointing",
        "following directions",
        "understanding",
    ),
    "narrative_story": (
        "narrative",
        "story",
        "retell",
        "frog",
        "cinderella",
        "enni",
        "gillam",
        "storytell",
        "storybook",
        "story stem",
    ),
    "picture_description": (
        "picture description",
        "picture",
        "photo",
        "cookie theft",
        "broken window",
        "cat rescue",
        "umbrella",
        "flood",
        "picnic",
        "sandwich",
        "famous",
        "bnt",
        "vnt",
        "salem",
    ),
    "reading": (
        "reading",
        " read ",
        "read aloud",
        "passage",
    ),
    "conversation_interview": (
        "conversation",
        "interview",
        "toyplay",
        "toy play",
        "free play",
        "freeplay",
        "spontaneous",
        "parentchild",
        "adult-child",
        "mother",
        "play",
        "conv",
    ),
    "fluency_stuttering": (
        "stutter",
        "stuttering",
        "fluency",
        "disfluency",
        "clutter",
    ),
}


HEADER_PREFIXES = (
    "@Activities:",
    "@Situation:",
    "@Media:",
    "@Types:",
    "@Comment:",
    "@G:",
    "@Bg:",
    "@Eg:",
)


EXTERNAL_FLUENCY_CANDIDATES = [
    {
        "corpus": "FluencyBank main access",
        "url": "https://talkbank.org/fluency/",
        "why_it_matters": "Research data are consortium/password restricted; teaching data are open. Access request is separate from AphasiaBank.",
    },
    {
        "corpus": "Purdue",
        "url": "https://talkbank.org/fluency/access/Purdue.html",
        "why_it_matters": "TalkBank page references 4- and 5-year-old children who stutter and persistence/recovery.",
    },
    {
        "corpus": "Wagovich",
        "url": "https://talkbank.org/fluency/access/Password/Wagovich.html",
        "why_it_matters": "Longitudinal child stuttering/language-growth protocol over roughly ten months.",
    },
    {
        "corpus": "Ratner",
        "url": "https://talkbank.org/fluency/access/Password/Ratner.html",
        "why_it_matters": "Children who stutter plus matched fluent peers across published reports.",
    },
    {
        "corpus": "UMD-CMU",
        "url": "https://talkbank.org/fluency/access/UMD-CMU.html",
        "why_it_matters": "Young-child disfluency work with utterance-level predictors; may support language-fluency modeling.",
    },
    {
        "corpus": "Voices-CWS",
        "url": "https://talkbank.org/fluency/access/Voices-CWS.html",
        "why_it_matters": "Child stuttering teaching corpus with reading/conversation contrast; likely not recovery-focused.",
    },
]


@dataclass
class ChatInventoryRow:
    path: str
    bank: str
    section: str
    corpus: str
    transcript_stem: str
    has_media_header: bool
    media_missing_or_unlinked: bool
    header_task_text: str
    categories: str
    n_gem_markers: int
    gem_labels: str


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def derive_location(path: Path) -> tuple[str, str, str]:
    rel = path.relative_to(RAW_DIR)
    parts = rel.parts
    if not parts:
        return "unknown", "", ""
    if parts[0] == "aphasiabank":
        section = parts[1] if len(parts) > 1 else ""
        corpus = parts[2] if len(parts) > 2 else ""
        return "AphasiaBank", section, corpus
    if parts[0] in {"Eng-NA", "Eng-UK", "Clinical-Eng"}:
        section = parts[0]
        corpus = parts[1] if len(parts) > 1 else ""
        return "CHILDES", section, corpus
    return parts[0], parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else ""


def collect_header_task_text(path: Path) -> tuple[str, list[str], bool, bool]:
    header_bits: list[str] = []
    gem_labels: list[str] = []
    has_media = False
    media_missing = False

    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return "", [], False, False

    for line in lines:
        if not line.startswith("@"):
            continue
        for prefix in HEADER_PREFIXES:
            if line.startswith(prefix):
                value = line.split(":", 1)[1].strip() if ":" in line else line
                header_bits.append(value)
                if prefix == "@G:":
                    gem_labels.append(value)
                if prefix == "@Media:":
                    has_media = True
                    low = normalize(value)
                    media_missing = any(tok in low for tok in ("missing", "unlinked", "noaudio", "no audio"))
                break

    text = " | ".join(header_bits)
    return text, sorted(set(gem_labels)), has_media, media_missing


def classify_categories(path: Path, header_text: str, gem_labels: list[str]) -> list[str]:
    rel_text = " ".join(path.relative_to(RAW_DIR).with_suffix("").parts)
    haystack = normalize(f"{rel_text} {header_text} {' '.join(gem_labels)}")
    categories = []
    for category, keywords in TASK_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            categories.append(category)
    if not categories:
        categories.append("unclassified")
    return categories


def scan_chat_files() -> pd.DataFrame:
    rows: list[ChatInventoryRow] = []
    for path in sorted(RAW_DIR.rglob("*.cha")):
        if "__MACOSX" in path.parts:
            continue
        bank, section, corpus = derive_location(path)
        header_text, gems, has_media, media_missing = collect_header_task_text(path)
        cats = classify_categories(path, header_text, gems)
        rows.append(
            ChatInventoryRow(
                path=str(path),
                bank=bank,
                section=section,
                corpus=corpus,
                transcript_stem=path.stem,
                has_media_header=has_media,
                media_missing_or_unlinked=media_missing,
                header_task_text=header_text[:500],
                categories=";".join(cats),
                n_gem_markers=len(gems),
                gem_labels="; ".join(gems[:30]),
            )
        )
    return pd.DataFrame([row.__dict__ for row in rows])


def explode_categories(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rec in df.itertuples(index=False):
        for cat in str(rec.categories).split(";"):
            rows.append(
                {
                    "bank": rec.bank,
                    "section": rec.section,
                    "corpus": rec.corpus,
                    "category": cat,
                    "path": rec.path,
                    "has_media_header": rec.has_media_header,
                    "media_missing_or_unlinked": rec.media_missing_or_unlinked,
                    "n_gem_markers": rec.n_gem_markers,
                }
            )
    return pd.DataFrame(rows)


def write_markdown_table(df: pd.DataFrame, columns: list[str], limit: int | None = None) -> str:
    if limit is not None:
        df = df.head(limit)
    if df.empty:
        return "_No rows._\n"
    rows = df[columns].astype(str).values.tolist()
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header, sep, *body]) + "\n"


def summarize_structured_inventory(df: pd.DataFrame, exploded: pd.DataFrame) -> None:
    STRUCTURED_OUT.mkdir(parents=True, exist_ok=True)

    category_summary = (
        exploded.groupby("category", dropna=False)
        .agg(
            files=("path", "nunique"),
            corpora=("corpus", "nunique"),
            media_headers=("has_media_header", "sum"),
            missing_or_unlinked_media=("media_missing_or_unlinked", "sum"),
        )
        .reset_index()
        .sort_values(["files", "category"], ascending=[False, True])
    )

    corpus_task_summary = (
        exploded.groupby(["bank", "section", "corpus", "category"], dropna=False)
        .agg(
            files=("path", "nunique"),
            media_headers=("has_media_header", "sum"),
            missing_or_unlinked_media=("media_missing_or_unlinked", "sum"),
            gem_marker_files=("n_gem_markers", lambda s: int((s > 0).sum())),
        )
        .reset_index()
        .sort_values(["category", "files"], ascending=[True, False])
    )

    structured_categories = [
        "sentence_repetition",
        "nonword_repetition",
        "comprehension",
        "narrative_story",
        "picture_description",
        "reading",
        "conversation_interview",
    ]
    structured_corpora = corpus_task_summary[
        corpus_task_summary["category"].isin(structured_categories)
    ].copy()

    category_summary.to_csv(STRUCTURED_OUT / "category_summary.csv", index=False)
    corpus_task_summary.to_csv(STRUCTURED_OUT / "corpus_task_summary.csv", index=False)
    structured_corpora.to_csv(STRUCTURED_OUT / "structured_candidate_corpora.csv", index=False)

    sentence = structured_corpora[structured_corpora["category"] == "sentence_repetition"]
    nonword = structured_corpora[structured_corpora["category"] == "nonword_repetition"]
    narrative = structured_corpora[structured_corpora["category"] == "narrative_story"]
    conversation = structured_corpora[structured_corpora["category"] == "conversation_interview"]

    summary = f"""# Structured Task Inventory

**Date:** 2026-04-30
**Script:** `scripts/run_post_brian_data_inventory.py`

## Scope

Scanned **{len(df):,}** local CHAT files under `data/raw/`, excluding `__MACOSX`.
The scan uses file paths and CHAT headers such as `@Types`, `@Activities`,
`@Situation`, `@Media`, and `@G`. It does **not** parse or publish utterance text.

## Headline Findings

- Local data are rich for natural speech, play/conversation, narrative, and
  AphasiaBank picture/story protocol tasks.
- The local headers/path scan found **{int(sentence['files'].sum()) if not sentence.empty else 0:,}**
  sentence-repetition candidate files and **{int(nonword['files'].sum()) if not nonword.empty else 0:,}**
  nonword-repetition candidate files. These low counts mean Brian's preferred
  tight tasks are not well represented in the current local copy.
- Narrative/story candidates are common: **{int(narrative['files'].sum()) if not narrative.empty else 0:,}**
  file-category hits.
- Conversation/interview/play candidates are common: **{int(conversation['files'].sum()) if not conversation.empty else 0:,}**
  file-category hits.
- Next decision: use current local data for narrative/conversation/picture
  work, but seek or request specific sentence-repetition and nonword-repetition
  datasets before making strong claims about a full battery.

## Category Summary

{write_markdown_table(category_summary, ['category', 'files', 'corpora', 'media_headers', 'missing_or_unlinked_media'])}

## Top Candidate Corpora By Structured Category

{write_markdown_table(structured_corpora.sort_values(['files'], ascending=False), ['bank', 'section', 'corpus', 'category', 'files', 'media_headers', 'missing_or_unlinked_media', 'gem_marker_files'], limit=40)}

## Interpretation

This supports the Phase 2 plan. The project can immediately study natural
speech, play/conversation, narrative, picture description, and AphasiaBank
task-conditioned content. It cannot yet fully test Brian's proposed
natural-plus-tight-task battery because sentence repetition and nonword
repetition are sparse or absent in the local headers.

## Next Actions

1. Search alternative header spellings and likely corpora manually, because
   the direct header/path scan found no sentence-repetition or nonword hits.
2. Search TalkBank/BA Web documentation for corpora with sentence repetition
   and nonword repetition.
3. Prioritize structured-task access in the Brian/Franklin follow-up, but ask
   only after producing a concrete inventory.
"""
    (STRUCTURED_OUT / "summary.md").write_text(summary)


def summarize_stuttering_inventory(df: pd.DataFrame, exploded: pd.DataFrame) -> None:
    STUTTER_OUT.mkdir(parents=True, exist_ok=True)

    stutter = exploded[exploded["category"] == "fluency_stuttering"].copy()
    local_by_corpus = (
        stutter.groupby(["bank", "section", "corpus"], dropna=False)
        .agg(
            files=("path", "nunique"),
            media_headers=("has_media_header", "sum"),
            missing_or_unlinked_media=("media_missing_or_unlinked", "sum"),
        )
        .reset_index()
        .sort_values("files", ascending=False)
    )
    local_by_corpus.to_csv(STUTTER_OUT / "local_fluency_candidates.csv", index=False)
    pd.DataFrame(EXTERNAL_FLUENCY_CANDIDATES).to_csv(
        STUTTER_OUT / "external_fluencybank_candidates.csv", index=False
    )

    has_local_fluencybank = any(
        "fluencybank" in normalize(str(path)) for path in df["path"].astype(str)
    )
    local_files = int(stutter["path"].nunique()) if not stutter.empty else 0

    external_md = pd.DataFrame(EXTERNAL_FLUENCY_CANDIDATES)
    summary = f"""# Stuttering Recovery Inventory

**Date:** 2026-04-30
**Script:** `scripts/run_post_brian_data_inventory.py`

## Local Finding

- Local FluencyBank directory present: **{has_local_fluencybank}**
- Local fluency/stuttering/cluttering header/path candidates: **{local_files:,}**
- The local candidates are not enough to run Brian's proposed child stuttering
  recovery experiment. In this checkout, the only obvious fluency hits are
  local clinical/aphasia-style files, not a child longitudinal FluencyBank
  recovery corpus.

## Local Fluency Candidates By Corpus

{write_markdown_table(local_by_corpus, ['bank', 'section', 'corpus', 'files', 'media_headers', 'missing_or_unlinked_media'])}

## External FluencyBank Candidates To Request Or Download

{write_markdown_table(external_md, ['corpus', 'url', 'why_it_matters'])}

## Access Implication

The stuttering recovery track is scientifically high priority, but locally
blocked until FluencyBank access is obtained or the relevant corpora are
downloaded. Brian's point still changes the plan: stuttering should be the
first recovery-prediction target once access is available.

## Next Actions

1. Apply for or request FluencyBank access separately from AphasiaBank.
2. Prioritize Purdue, Wagovich, Ratner, and UMD-CMU because they are the most
   aligned with child stuttering, language features, and recovery/persistence.
3. After access, rerun this inventory and then run the first-pass recovery
   model from `TASKS.md` task 4.1.
"""
    (STUTTER_OUT / "summary.md").write_text(summary)


def main() -> None:
    df = scan_chat_files()
    exploded = explode_categories(df)
    summarize_structured_inventory(df, exploded)
    summarize_stuttering_inventory(df, exploded)
    print(f"Scanned {len(df):,} CHAT files")
    print(f"Wrote {STRUCTURED_OUT / 'summary.md'}")
    print(f"Wrote {STUTTER_OUT / 'summary.md'}")


if __name__ == "__main__":
    main()
