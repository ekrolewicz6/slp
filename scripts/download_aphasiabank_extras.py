"""Download the AphasiaBank-derived extras flagged during the website crawl.

  - Salem: preprocessed Cinderella + paraphasia annotations (~3 MB).
  - C-QPA / CinderellaFiles: Adler+Capilouto sample with C-QPA spreadsheets.
  - BNT / VNT zips: naming-test scores from Portland State.

These are useful as: pre-computed C-QPA features (saves us re-deriving),
naming-test scores (extra outcome dimension beyond WAB-AQ), and the Salem
JSON which has paraphasia targets (useful for error-marker features).
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

from src.ingestion.aphasiabank import _cookies


EXTRAS = {
    "Salem.zip": "https://media.talkbank.org/aphasia/0extra/Salem.zip",
    "BNT-PortlandState.zip": "https://aphasia.talkbank.org/password/testresults/BNT-PortlandState.zip",
    "VNT-PortlandState.zip": "https://aphasia.talkbank.org/password/testresults/VNT-PortlandState.zip",
}

CQPA_BASE = "https://aphasia.talkbank.org/discourse/C-QPA/CinderellaFiles/"
# Files known to exist (from our earlier crawl):
CQPA_FILES = [
    "SummarySheet.xlsx",
    "adler17a.cha", "adler17a.cqp.AS.xls",
    "capilouto77a.cha", "capilouto77a.cqp.AS.xls",
]


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def _download(url: str, dest: Path, cookies: dict) -> str:
    if dest.exists() and dest.stat().st_size > 1024:
        return f"cached ({dest.stat().st_size} B)"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, cookies=cookies, stream=True, timeout=120) as r:
        if r.status_code != 200:
            return f"HTTP {r.status_code}"
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 15):
                f.write(chunk)
    return f"fresh ({dest.stat().st_size} B)"


def main() -> None:
    _load_dotenv()
    cookies = _cookies()
    base = Path("data/raw/aphasiabank/extras")

    print("Downloading derived datasets ...")
    for name, url in tqdm(EXTRAS.items(), desc="extras"):
        status = _download(url, base / name, cookies)
        print(f"  {name:30s} {status}")
        if name.endswith(".zip"):
            target = base / name.replace(".zip", "")
            if not target.exists():
                target.mkdir(parents=True, exist_ok=True)
                try:
                    with zipfile.ZipFile(base / name) as zf:
                        zf.extractall(target)
                except zipfile.BadZipFile as e:
                    print(f"    [skip extract] {name}: {e}")

    print("\nDownloading C-QPA Cinderella sample ...")
    cqpa_dir = base / "C-QPA-Cinderella"
    for fname in tqdm(CQPA_FILES, desc="C-QPA"):
        status = _download(f"{CQPA_BASE}{fname}", cqpa_dir / fname, cookies)
        print(f"  {fname:35s} {status}")

    print(f"\nAll extras under {base.resolve()}")


if __name__ == "__main__":
    main()
