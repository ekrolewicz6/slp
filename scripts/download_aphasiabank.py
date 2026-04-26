"""One-shot download + extract of all English AphasiaBank data.

Reads APHASIABANK_COOKIE from .env (or environment). Idempotent: skips
zips already on disk and skips already-extracted directories.

Run:
    .venv/bin/python -m scripts.download_aphasiabank
"""

from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path

from src.ingestion.aphasiabank import download_all, extract_all


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dest-dir", default="data/raw/aphasiabank", type=Path)
    return p.parse_args()


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    args = parse_args()
    _load_dotenv()

    print(f"Downloading AphasiaBank to {args.dest_dir.resolve()} ...")
    results = download_all(args.dest_dir)

    by_status = Counter(r.status for r in results)
    print(f"\nDownload status counts:")
    for status, n in by_status.most_common():
        print(f"  {status:12s}  {n}")

    fails = [r for r in results if r.status not in {"fresh", "cached"}]
    if fails:
        print(f"\n{len(fails)} downloads not OK:")
        for r in fails:
            print(f"  - {r.label:35s}  {r.status}")

    print("\nExtracting zips ...")
    extracted = extract_all(args.dest_dir, results)
    print(f"  extracted {len(extracted)} corpora")

    # Summary: count .cha files per section.
    print("\nCorpus sizes (.cha file counts):")
    for section in ["Protocol", "NonProtocol", "Group", "Script"]:
        section_dir = args.dest_dir / section
        if not section_dir.exists():
            continue
        n_cha = len(list(section_dir.rglob("*.cha")))
        n_corp = len([d for d in section_dir.iterdir() if d.is_dir()])
        print(f"  {section:12s}  {n_corp} corpora, {n_cha} .cha files")
    if (args.dest_dir / "Famous").exists():
        n_cha = len(list((args.dest_dir / "Famous").rglob("*.cha")))
        print(f"  {'Famous':12s}  {n_cha} .cha files")

    meta_dir = args.dest_dir / "metadata"
    if meta_dir.exists():
        print(f"\nMetadata files:")
        for f in sorted(meta_dir.iterdir()):
            print(f"  {f.name:32s}  {f.stat().st_size:>10,} bytes")


if __name__ == "__main__":
    main()
