"""CHILDES download + parsing.

Downloads the bundled English North American CHILDES MOR archive (≈91 MB) and
extracts per-transcript records with target-child metadata.

The bundle URL `https://talkbank.org/childes/access/Eng-NA/0-Eng-NA-MOR.zip`
is the only CHILDES path we have found that does not currently sit behind the
TalkBank auth modal. Per-corpus zips (e.g. `Brown.zip`) require a logged-in
session and cannot be fetched programmatically without credentials.
"""

from __future__ import annotations

import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pylangacq as pla
import requests
from tqdm import tqdm

OPEN_ENGLISH_BUNDLES = {
    "Eng-NA": "https://talkbank.org/childes/access/Eng-NA/0-Eng-NA-MOR.zip",
    "Eng-UK": "https://talkbank.org/childes/access/Eng-UK/0-Eng-UK-MOR.zip",
    "Clinical-Eng": "https://talkbank.org/childes/access/Clinical-Eng/0-Clinical-MOR.zip",
}


def download_bundle(name: str, url: str, dest_dir: Path) -> Path:
    """Download + extract a single bundle. Returns the extracted root directory.

    The Eng-NA and Eng-UK zips extract to `<dest>/<name>/`; Clinical-Eng
    extracts to `<dest>/Clinical/` (the bundle's internal top-level differs
    from its access-page name). We probe and fall back so the caller always
    gets a real directory.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / f"{Path(url).name}"

    # Heuristic root candidates (preferred → fallback).
    candidates = [dest_dir / name, dest_dir / "Clinical", dest_dir / name.replace("-", "")]
    for c in candidates:
        if c.exists():
            return c

    if not zip_path.exists():
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with open(zip_path, "wb") as f, tqdm(
                total=total, unit="B", unit_scale=True, desc=name
            ) as bar:
                for chunk in r.iter_content(chunk_size=1 << 15):
                    f.write(chunk)
                    bar.update(len(chunk))

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)

    for c in candidates:
        if c.exists():
            return c
    # Last resort: take any newly-created top-level dir.
    new_dirs = [d for d in dest_dir.iterdir() if d.is_dir()
                and d.name not in {"Eng-NA", "Eng-UK", "Clinical"}]
    if new_dirs:
        return sorted(new_dirs, key=lambda d: d.stat().st_mtime)[-1]
    raise RuntimeError(f"Could not locate extracted root for bundle {name}")


def download_english_bundles(dest_dir: Path) -> dict[str, Path]:
    """Download all openly-available English MOR bundles. Returns name → root."""
    return {name: download_bundle(name, url, dest_dir)
            for name, url in OPEN_ENGLISH_BUNDLES.items()}


def download_eng_na_bundle(dest_dir: Path) -> Path:
    """Backward-compat alias used by the original Phase 1 script."""
    return download_bundle("Eng-NA", OPEN_ENGLISH_BUNDLES["Eng-NA"], dest_dir)


@dataclass
class TranscriptRecord:
    """One row per `.cha` file (one recording session)."""

    transcript_id: str          # corpus/relpath, e.g. "Brown/Adam/020304"
    corpus: str                 # "Brown"
    child_id: str               # CHI participant name, e.g. "Adam"
    age_months: float | None    # target child age at recording
    n_chi_utterances: int       # CHI-only utterance count
    file_path: str              # absolute path

    @property
    def has_age(self) -> bool:
        return self.age_months is not None and self.age_months > 0


def load_corpus(corpus_root: Path, corpus_name: str | None = None) -> pla.CHAT:
    """Load a CHILDES corpus directory with pylangacq.

    Misaligned MOR/word utterances are tolerated (`strict=False`); their
    tokens come back empty so feature extractors must skip them.
    """
    path = Path(corpus_root)
    if corpus_name is not None:
        path = path / corpus_name
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pla.read_chat(str(path), strict=False)


def build_transcript_index(
    chat: pla.CHAT,
    corpus_root: Path,
) -> list[TranscriptRecord]:
    """Build one TranscriptRecord per file in a loaded CHAT object."""
    records: list[TranscriptRecord] = []
    file_paths = chat.file_paths
    headers = chat.headers()
    ages = chat.ages()
    utts_by_file = chat.utterances(by_file=True)

    corpus_root = Path(corpus_root).resolve()

    for fp, hdr, age, utts in zip(file_paths, headers, ages, utts_by_file):
        rel = Path(fp).resolve().relative_to(corpus_root.parent)
        # rel like "Eng-NA/Brown/Adam/020304.cha"; drop leading "Eng-NA/"
        parts = rel.parts
        if parts[0] == corpus_root.name:
            parts = parts[1:]
        corpus = parts[0] if parts else "unknown"
        child = parts[1] if len(parts) > 2 else _child_name_from_header(hdr)
        transcript_id = "/".join(parts).replace(".cha", "")

        n_chi = sum(1 for u in utts if u.participant == "CHI")
        age_months = age.in_months() if age is not None else None

        records.append(
            TranscriptRecord(
                transcript_id=transcript_id,
                corpus=corpus,
                child_id=child or "unknown",
                age_months=age_months,
                n_chi_utterances=n_chi,
                file_path=str(Path(fp).resolve()),
            )
        )
    return records


def _child_name_from_header(hdr) -> str:
    for p in hdr.participants:
        if p.role == "Target_Child" or p.code == "CHI":
            return p.name or "unknown"
    return "unknown"
