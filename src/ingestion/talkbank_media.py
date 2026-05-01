"""TalkBank media request helpers.

Secrets must stay in .env or docs/private/. This module deliberately returns
only request headers and never logs credential values.
"""

from __future__ import annotations

import os
import shlex
from pathlib import Path


DEFAULT_CURL_FILE = Path("docs/private/talkbank_media_request.curl")


def _clean_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.strip()


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), _clean_env_value(value))


def normalize_cookie_header(value: str) -> str:
    value = _clean_env_value(value)
    if value.lower().startswith("cookie:"):
        value = value.split(":", 1)[1].strip()
    return value


def cookie_header() -> str:
    header = normalize_cookie_header(os.environ.get("TALKBANK_COOKIE_HEADER", ""))
    if header:
        return header
    legacy = _clean_env_value(os.environ.get("APHASIABANK_COOKIE", ""))
    if legacy:
        return f"talkbank={legacy}; connect.sid={legacy}"
    return ""


def parse_curl_request(path: Path) -> tuple[dict[str, str], str | None]:
    """Parse DevTools "Copy as cURL" output into headers and URL."""

    text = path.read_text()
    text = text.replace("\\\n", " ")
    parts = shlex.split(text)
    headers: dict[str, str] = {}
    url: str | None = None

    i = 0
    while i < len(parts):
        token = parts[i]
        if token in {"curl", "curl.exe"}:
            i += 1
            continue
        if token in {"-H", "--header"} and i + 1 < len(parts):
            raw = parts[i + 1]
            if ":" in raw:
                key, value = raw.split(":", 1)
                headers[key.strip()] = value.strip()
            i += 2
            continue
        if token in {"-A", "--user-agent"} and i + 1 < len(parts):
            headers["User-Agent"] = parts[i + 1]
            i += 2
            continue
        if token in {"-e", "--referer"} and i + 1 < len(parts):
            headers["Referer"] = parts[i + 1]
            i += 2
            continue
        if token in {"--url"} and i + 1 < len(parts):
            url = parts[i + 1]
            i += 2
            continue
        if token.startswith("http://") or token.startswith("https://"):
            url = token
        i += 1

    if "Cookie" in headers:
        headers["Cookie"] = normalize_cookie_header(headers["Cookie"])
    return headers, url


def request_headers(
    range_value: str | None = "bytes=0-1023",
) -> tuple[dict[str, str], str | None, str]:
    """Return media request headers, optional cURL URL, and source label."""

    curl_file = _clean_env_value(os.environ.get("TALKBANK_MEDIA_CURL_FILE", ""))
    path = Path(curl_file) if curl_file else DEFAULT_CURL_FILE
    if path.exists():
        headers, url = parse_curl_request(path)
        if range_value and "Range" not in headers:
            headers["Range"] = range_value
        return headers, url, f"curl_file:{path}"

    cookie = cookie_header()
    headers = {"Cookie": cookie} if cookie else {}
    if range_value:
        headers["Range"] = range_value
    return headers, None, "env_cookie"


def ffmpeg_headers(headers: dict[str, str], include_range: bool = False) -> str:
    skip = {"host", "connection", "accept-encoding"}
    if not include_range:
        skip.add("range")
    lines = []
    for key, value in headers.items():
        if key.lower() in skip:
            continue
        lines.append(f"{key}: {value}")
    return "\r\n".join(lines) + "\r\n"
