"""Download FluencyBank transcript ZIPs from a TalkBankDB export.

The TalkBankDB export lists transcript paths such as:

    fluency/Purdue/Grant1/103mzcy06
    fluency/Password/IISRP/CWNS/203/203-1

TalkBank serves transcript ZIPs at:

    https://talkbank.org/data/fluency/Purdue?f=zip
    https://talkbank.org/data/fluency/Password/IISRP?f=zip

This script uses the local TalkBank cookie from .env, downloads each corpus ZIP,
extracts it under data/raw/fluencybank, and writes a committed-safe inventory.
Raw transcripts and ZIPs are gitignored.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.ingestion.talkbank_media import cookie_header, load_dotenv


DEFAULT_EXPORT = Path("data/external/fluencybank/TalkBankDB_transcripts.tsv")
DEFAULT_RAW_DIR = Path("data/raw/fluencybank")
DEFAULT_OUT_DIR = Path("outputs/fluencybank_download_inventory")
BASE_URL = "https://talkbank.org/data/fluency"


@dataclass(frozen=True)
class CorpusSpec:
    corpus: str
    zip_key: str
    password: bool

    @property
    def url(self) -> str:
        return f"{BASE_URL}/{self.zip_key}?f=zip"

    @property
    def zip_name(self) -> str:
        return self.zip_key.replace("/", "__") + ".zip"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """The downloaded .xls is a TSV with no header row."""

    expected = [
        "path",
        "id",
        "lang",
        "modality",
        "extra",
        "doi",
        "design",
        "task",
        "group",
        "note",
    ]
    if "path" in df.columns:
        return df
    if len(df.columns) == len(expected):
        df = df.copy()
        df.columns = expected
        return df
    return pd.read_csv(DEFAULT_EXPORT, sep="\t", header=None, names=expected)


def corpus_spec(path: str) -> CorpusSpec:
    parts = path.split("/")
    if len(parts) < 2 or parts[0] != "fluency":
        raise ValueError(f"Unexpected FluencyBank path: {path}")
    if len(parts) >= 3 and parts[1] == "Password":
        return CorpusSpec(corpus=parts[2], zip_key=f"Password/{parts[2]}", password=True)
    return CorpusSpec(corpus=parts[1], zip_key=parts[1], password=False)


def safe_extract(zip_bytes: bytes, dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            target = dest / info.filename
            resolved = target.resolve()
            if not str(resolved).startswith(str(dest.resolve())):
                raise RuntimeError(f"Unsafe zip member path: {info.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as out:
                out.write(src.read())
            written.append(target)
    return written


def request_zip(url: str, cookie: str, timeout: int = 90) -> tuple[int, bytes, str]:
    headers = {
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
        ),
        "Accept": "application/zip,application/octet-stream,*/*",
    }
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        return int(resp.status), data, resp.headers.get("content-type", "")


def count_local_cha(raw_dir: Path, corpus: str) -> int:
    path = raw_dir / corpus
    return len(list(path.rglob("*.cha"))) if path.exists() else 0


def format_counter(counter: Counter) -> str:
    return ", ".join(f"{k}:{v}" for k, v in sorted(counter.items(), key=lambda kv: str(kv[0])))


def write_inventory(
    df: pd.DataFrame,
    specs: list[CorpusSpec],
    results: dict[str, dict[str, object]],
    raw_dir: Path,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    spec_by_corpus = {s.corpus: s for s in specs}

    rows: list[dict[str, object]] = []
    for corpus, sub in df.groupby(df["path"].map(lambda p: corpus_spec(str(p)).corpus)):
        spec = spec_by_corpus[corpus]
        result = results.get(corpus, {})
        rows.append(
            {
                "corpus": corpus,
                "zip_key": spec.zip_key,
                "talkbankdb_rows": len(sub),
                "password_rows": int(sub["path"].astype(str).str.contains("/Password/").sum()),
                "download_status": result.get("status", "not_requested"),
                "http_status": result.get("http_status", ""),
                "zip_bytes": result.get("zip_bytes", ""),
                "files_extracted": result.get("files_extracted", ""),
                "local_cha_files": count_local_cha(raw_dir, corpus),
                "languages": ", ".join(sorted(map(str, sub["lang"].dropna().unique()))),
                "designs": format_counter(Counter(sub["design"].fillna("null"))),
                "groups": format_counter(Counter(sub["group"].fillna("null"))),
                "url": spec.url,
                "error": result.get("error", ""),
            }
        )

    rows = sorted(rows, key=lambda r: (-int(r["local_cha_files"]), str(r["corpus"])))
    with (out_dir / "corpus_inventory.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    downloaded = [r for r in rows if int(r["local_cha_files"]) > 0]
    blocked = [r for r in rows if int(r["local_cha_files"]) == 0]
    total_cha = sum(int(r["local_cha_files"]) for r in rows)
    password_cha = sum(int(r["local_cha_files"]) for r in rows if int(r["password_rows"]) > 0)

    downloaded_table = "\n".join(
        "| {corpus} | {talkbankdb_rows} | {password_rows} | {local_cha_files} | {download_status} | {languages} | {designs} | {groups} |".format(
            **r
        )
        for r in downloaded
    )
    blocked_table = "\n".join(
        "| {corpus} | {talkbankdb_rows} | {password_rows} | {download_status} | {error} |".format(
            **r
        )
        for r in blocked
    )
    if not blocked_table:
        blocked_table = "| none | 0 | 0 | n/a | n/a |"

    summary = f"""# FluencyBank Download Inventory

**Source:** local TalkBankDB transcript export `{DEFAULT_EXPORT}`.

## Bottom Line

- TalkBankDB FluencyBank rows in export: {len(df):,}
- Corpus ZIPs requested: {len(specs)}
- Local `.cha` transcripts downloaded: {total_cha:,}
- Password-gated `.cha` transcripts now local: {password_cha:,}

The current TalkBank cookie can access the formerly password-gated transcript
ZIPs. This unblocks IISRP, IISRP-new, Wagovich, Ratner, Maxfield, Tellis, and
Sawyer for transcript-level modeling. Media access still needs separate probing
before acoustic extraction.

## Downloaded Corpora

| corpus | TalkBankDB rows | password rows | local `.cha` files | status | languages | designs | groups |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
{downloaded_table}

## Still Missing

| corpus | TalkBankDB rows | password rows | status | error |
| --- | ---: | ---: | --- | --- |
{blocked_table}

## Research Implication

The stuttering recovery track should move from a Purdue-only feasibility pilot
to a replication-grade FluencyBank analysis. The highest-priority next model is
not another earliest-transcript classifier. It should use longitudinal change,
group path structure (`CWS-rec`, `CWS-per`, TD/CWNS), disfluency classes,
language-growth features, and corpus-held-out validation across Purdue, IISRP,
IISRP-new, Wagovich, Ratner, and UMD-CMU where labels permit.
"""
    (out_dir / "summary.md").write_text(summary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--only-password", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    cookie = cookie_header()
    if not cookie:
        raise SystemExit("Missing TALKBANK_COOKIE_HEADER or APHASIABANK_COOKIE in .env")

    df = normalize_columns(pd.read_csv(args.export, sep="\t", header=None))
    df = df[df["path"].astype(str).str.startswith("fluency/")].copy()
    specs = sorted({corpus_spec(str(p)) for p in df["path"]}, key=lambda s: s.zip_key)
    if args.only_password:
        specs = [s for s in specs if s.password]

    zip_dir = args.raw_dir / "_zips"
    zip_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict[str, object]] = {}
    for spec in specs:
        zip_path = zip_dir / spec.zip_name
        if zip_path.exists() and zip_path.stat().st_size > 0 and not args.force:
            data = zip_path.read_bytes()
            status = "cached"
            http_status = ""
            ctype = "application/zip"
        else:
            try:
                http_status, data, ctype = request_zip(spec.url, cookie)
                zip_path.write_bytes(data)
                status = "downloaded"
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                results[spec.corpus] = {
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "url": spec.url,
                }
                print(f"[failed] {spec.zip_key}: {exc}")
                continue

        if not data.startswith(b"PK"):
            results[spec.corpus] = {
                "status": "failed",
                "http_status": http_status,
                "zip_bytes": len(data),
                "error": f"Response was not a zip: content_type={ctype}",
                "url": spec.url,
            }
            print(f"[failed] {spec.zip_key}: non-zip response {ctype}")
            continue

        written = safe_extract(data, args.raw_dir / spec.corpus)
        results[spec.corpus] = {
            "status": status,
            "http_status": http_status,
            "zip_bytes": len(data),
            "files_extracted": len(written),
            "url": spec.url,
        }
        print(
            f"[{status}] {spec.zip_key}: {len(data) / 1_000_000:.2f} MB, "
            f"{len(written)} files, {count_local_cha(args.raw_dir, spec.corpus)} .cha"
        )

    write_inventory(df, sorted({corpus_spec(str(p)) for p in df["path"]}, key=lambda s: s.zip_key), results, args.raw_dir, args.output_dir)
    print(f"wrote {args.output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
