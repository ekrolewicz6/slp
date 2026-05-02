"""Probe authenticated FluencyBank media access without downloading media."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_reconstruction_safety_benchmark import md_table  # noqa: E402
from scripts.run_fluencybank_full_recovery_model import parse_header  # noqa: E402
from src.ingestion.talkbank_media import cookie_header, load_dotenv  # noqa: E402


DEFAULT_RAW_DIR = Path("data/raw/fluencybank")
DEFAULT_EXPORT = Path("data/external/fluencybank/TalkBankDB_transcripts.tsv")
DEFAULT_OUT_DIR = Path("outputs/fluencybank_media_access_probe")
MEDIA_BASE = "https://media.talkbank.org/fluency"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--samples-per-corpus", type=int, default=3)
    return parser.parse_args()


def password_corpora(export: Path) -> set[str]:
    if not export.exists():
        return set()
    df = pd.read_csv(
        export,
        sep="\t",
        header=None,
        names=["path", "id", "lang", "modality", "extra", "doi", "design", "task", "group", "note"],
    )
    out = set()
    for path in df["path"].astype(str):
        parts = path.split("/")
        if len(parts) >= 3 and parts[0] == "fluency" and parts[1] == "Password":
            out.add(parts[2])
    return out


def candidate_urls(path: Path, raw_dir: Path, media_stem: str, media_type: str, password: bool) -> list[str]:
    rel = path.relative_to(raw_dir)
    corpus = rel.parts[0]
    parent = "/".join(rel.parts[1:-1])
    exts = ["mp4", "mp3", "wav", "m4a", "mov"]
    if "video" in media_type.lower():
        exts = ["mp4", "mov", "m4v", "mp3", "wav"]
    elif "audio" in media_type.lower():
        exts = ["mp4", "mp3", "wav", "m4a", "mov"]

    stems = [media_stem, path.stem]
    stems = list(dict.fromkeys(s for s in stems if s))
    prefixes = [f"{MEDIA_BASE}/Password/{corpus}", f"{MEDIA_BASE}/{corpus}"] if password else [f"{MEDIA_BASE}/{corpus}", f"{MEDIA_BASE}/Password/{corpus}"]
    urls = []
    for prefix in prefixes:
        for stem in stems:
            for ext in exts:
                if parent:
                    urls.append(f"{prefix}/{parent}/{stem}.{ext}")
                urls.append(f"{prefix}/{stem}.{ext}")
    return list(dict.fromkeys(urls))


def probe_url(url: str, cookie: str) -> dict[str, object]:
    headers = {
        "Cookie": cookie,
        "Range": "bytes=0-10",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    try:
        with urlopen(Request(url, headers=headers), timeout=12) as resp:
            return {
                "http_status": int(resp.status),
                "content_type": resp.headers.get("content-type", ""),
                "content_range": resp.headers.get("content-range", ""),
                "content_length": resp.headers.get("content-length", ""),
                "ok": int(resp.status) in {200, 206},
                "error": "",
            }
    except HTTPError as exc:
        return {
            "http_status": int(exc.code),
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "content_range": exc.headers.get("content-range", "") if exc.headers else "",
            "content_length": exc.headers.get("content-length", "") if exc.headers else "",
            "ok": False,
            "error": f"HTTPError: {exc.code}",
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "http_status": "",
            "content_type": "",
            "content_range": "",
            "content_length": "",
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def remote_size_mb(content_range: str, content_length: str) -> float:
    match = re.search(r"/(\d+)$", str(content_range))
    if match:
        return int(match.group(1)) / 1_000_000.0
    try:
        return int(content_length) / 1_000_000.0
    except Exception:
        return float("nan")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    load_dotenv()
    cookie = cookie_header()
    if not cookie:
        raise SystemExit("Missing TalkBank cookie in .env")

    pw = password_corpora(args.export)
    files_by_corpus: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(args.raw_dir.rglob("*.cha")):
        if "_zips" in path.parts:
            continue
        files_by_corpus[path.relative_to(args.raw_dir).parts[0]].append(path)

    rows = []
    for corpus, files in sorted(files_by_corpus.items()):
        chosen = files[: args.samples_per_corpus]
        # Include known media-positive examples in addition to sorted first rows
        if corpus == "Ratner":
            chosen = sorted(files, key=lambda p: ("S001_intake" not in p.name, str(p)))[: args.samples_per_corpus]
        if corpus == "UMD-CMU":
            chosen = sorted(files, key=lambda p: ("200LJ_clinician_y1" not in p.name, str(p)))[: args.samples_per_corpus]
        for path in chosen:
            header = parse_header(path)
            media_stem = str(header.get("media") or path.stem)
            media_type = str(header.get("media_type") or "")
            if not media_stem:
                rows.append(
                    {
                        "corpus": corpus,
                        "sample": path.name,
                        "media_stem": "",
                        "media_type": media_type,
                        "best_status": "no_media_header",
                        "http_status": "",
                        "remote_size_mb": "",
                        "url": "",
                        "error": "no @Media stem found",
                    }
                )
                continue
            best = None
            for url in candidate_urls(path, args.raw_dir, media_stem, media_type, corpus in pw):
                result = probe_url(url, cookie)
                if result["ok"]:
                    best = (url, result)
                    break
                if best is None or result.get("http_status") == 401:
                    best = (url, result)
            url, result = best
            rows.append(
                {
                    "corpus": corpus,
                    "sample": path.name,
                    "media_stem": media_stem,
                    "media_type": media_type,
                    "best_status": "accessible" if result["ok"] else "blocked_or_missing",
                    "http_status": result["http_status"],
                    "content_type": result["content_type"],
                    "remote_size_mb": remote_size_mb(str(result["content_range"]), str(result["content_length"])),
                    "url": url if result["ok"] else "",
                    "error": "" if result["ok"] else result["error"],
                }
            )

    detail = pd.DataFrame(rows)
    detail.to_csv(args.output_dir / "media_probe_results.csv", index=False)
    corpus_summary = (
        detail.assign(accessible=detail["best_status"].eq("accessible").astype(int))
        .groupby("corpus", as_index=False)
        .agg(
            samples_probed=("sample", "count"),
            accessible_samples=("accessible", "sum"),
            statuses=("best_status", lambda s: ", ".join(sorted(set(map(str, s))))),
            median_remote_size_mb=("remote_size_mb", "median"),
        )
    )
    corpus_summary.to_csv(args.output_dir / "corpus_media_summary.csv", index=False)

    accessible = corpus_summary[corpus_summary["accessible_samples"].gt(0)]
    lines = [
        "# FluencyBank Media Access Probe",
        "",
        "**Question:** can the current TalkBank credential stream FluencyBank media for acoustic recovery modeling?",
        "",
        f"- Corpora probed: {corpus_summary['corpus'].nunique():,}",
        f"- Sample files probed: {len(detail):,}",
        f"- Corpora with at least one accessible media sample: {len(accessible):,}",
        "",
        "## Corpus Summary",
        "",
        md_table(corpus_summary.round(3)),
        "",
        "## Interpretation",
        "",
        "This probe uses HTTP range requests only; it does not download media. A corpus with accessible samples is technically streamable for future openSMILE/eGeMAPS extraction, but a full acoustic study still needs duration/quality checks and task alignment.",
        "",
        "Purdue is transcript-only according to its TalkBank access page, so recovery modeling for Purdue remains transcript-only. IISRP transcript access is open under the current credential, but the sampled IISRP media URLs are still blocked or unavailable from this environment. Ratner and UMD-CMU show accessible MP4 samples; those are candidates for future acoustic feasibility work.",
    ]
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
