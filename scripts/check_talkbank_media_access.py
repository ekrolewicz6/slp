"""Check whether current TalkBank credentials can stream AphasiaBank media."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.talkbank_media import (  # noqa: E402
    ffmpeg_headers,
    load_dotenv,
    request_headers,
)


DEFAULT_URL = (
    "https://media.talkbank.org/aphasia/English/Protocol/"
    "NEURAL-2/Control/103-1.mp4"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--timeout", type=int, default=20)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv()
    headers, curl_url, source = request_headers()
    if "Cookie" not in headers:
        print("missing TALKBANK_COOKIE_HEADER or APHASIABANK_COOKIE in .env")
        sys.exit(2)
    url = curl_url or args.url

    response = requests.get(
        url,
        headers=headers,
        timeout=args.timeout,
        allow_redirects=True,
        stream=True,
    )
    content_type = response.headers.get("content-type", "")
    first = next(response.iter_content(chunk_size=64), b"")
    print(f"request_source={source}")
    print(f"status={response.status_code}")
    print(f"content_type={content_type}")
    if response.headers.get("content-range"):
        print(f"content_range={response.headers.get('content-range')}")
    print(f"first_bytes={first[:16]!r}")

    if "text/html" in content_type.lower() or first.lstrip().startswith(b"<html"):
        print("result=auth_html_not_media")
        sys.exit(1)
    if response.status_code >= 400:
        print("result=http_error")
        sys.exit(1)

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-headers", ffmpeg_headers(headers),
        "-i", url,
        "-t", "2", "-vn", "-ar", "16000", "-ac", "1",
        "-f", "null", "-",
    ]
    ffmpeg = subprocess.run(cmd, capture_output=True, timeout=args.timeout)
    if ffmpeg.returncode != 0:
        print("result=ffmpeg_failed")
        print(ffmpeg.stderr.decode(errors="replace")[:1000])
        sys.exit(1)
    print("result=media_stream_ok")


if __name__ == "__main__":
    main()
