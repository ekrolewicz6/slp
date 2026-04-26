"""AphasiaBank corpus + metadata download.

AphasiaBank requires "Approved Access" — credentials live in the user's
TalkBank account. We need both `talkbank` and `connect.sid` cookies (Express
session), which the user obtains by logging in at aphasia.talkbank.org and
copying from browser dev tools. Cookies go in `.env`.

Each corpus is downloaded as `<base>/<section>/<corpus>?f=zip`. We mirror
the AphasiaBank section structure under `data/raw/aphasiabank/`:

    aphasiabank/
        Protocol/<corpus>.zip + extracted/
        NonProtocol/<corpus>.zip + extracted/
        Group/<corpus>.zip + extracted/
        Script/<corpus>.zip + extracted/
        Famous.zip + extracted/
        metadata/
            demo-data.xlsx          # PWA demographics
            demo-cont-data.xlsx     # control demographics
            english-results-data.xlsx  # WAB-AQ + subtype + other tests
"""

from __future__ import annotations

import os
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests
from tqdm import tqdm

DATA_BASE = "https://talkbank.org/data/aphasia/English"
PASSWORD_BASE = "https://aphasia.talkbank.org/password"

# Enumerated 2026-04-25 from access-page listings.
PROTOCOL_CORPORA = [
    "ACWT", "APROCSA", "Adler", "BU", "Baycrest", "CC", "CMU", "Capilouto",
    "Elman", "Fridriksson", "Fridriksson-2", "Garrett", "Kansas", "Kempler",
    "Kurland", "MSU", "NEURAL", "NEURAL-2", "Richardson", "SCALE", "STAR",
    "TAP", "TCU", "TCU-bi", "Thompson", "Tucson", "UMD", "UNH", "Whiteside",
    "Williamson", "Wozniak", "Wright",
]

NONPROTOCOL_CORPORA = [
    "CAP", "ChialFlahive", "Fridriksson", "Goodwin", "Holland1", "Holland2",
    "Hopkins", "Kurland", "Kurland-BATS", "Mackie", "Marshall", "Menn",
    "Oelschlager", "Olness", "Pawleys", "Penn", "QAB", "SCALE", "Shadden",
    "SouthAL", "TeleRounds", "Thompson", "Tucson", "Ulatowska",
]

GROUP_CORPORA = ["BU", "Duquesne", "SCALE", "Trove", "Williamson", "Wozniak"]

SCRIPT_CORPORA = ["Adler", "Fridriksson"]

# Standalone bundles (not section/corpus).
SINGLES = {
    "Famous": f"{DATA_BASE}/Famous?f=zip",
}

# Metadata spreadsheets (under password/...).
METADATA_FILES = {
    "demo-data.xlsx":  f"{PASSWORD_BASE}/demographics/English/demo-data.xlsx",
    "demo-cont-data.xlsx": f"{PASSWORD_BASE}/demographics/English/demo-cont-data.xlsx",
    "english-results-data.xlsx": f"{PASSWORD_BASE}/testresults/english-results-data.xlsx",
}


@dataclass
class DownloadResult:
    label: str
    path: Path
    bytes_: int
    status: str  # "fresh", "cached", "auth-fail", "not-found", "error"


def _cookies() -> dict[str, str]:
    """Read auth cookies from environment (.env). Both names share one value
    in the current TalkBank Express setup."""
    val = os.environ.get("APHASIABANK_COOKIE", "")
    if not val:
        raise RuntimeError(
            "Set APHASIABANK_COOKIE in .env to your TalkBank session cookie value."
        )
    return {"talkbank": val, "connect.sid": val}


def _download_zip(url: str, dest_path: Path, label: str,
                  cookies: dict[str, str]) -> DownloadResult:
    """Stream-download a zip with auth cookies. Recognises the auth wall."""
    if dest_path.exists() and dest_path.stat().st_size > 1024:
        return DownloadResult(label, dest_path, dest_path.stat().st_size, "cached")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with requests.get(url, cookies=cookies, stream=True, timeout=120) as r:
            r.raise_for_status()
            ct = r.headers.get("content-type", "")
            cd = r.headers.get("content-disposition", "")
            # Auth-wall response is HTML; real download has Content-Disposition.
            if "application/zip" not in ct and "attachment" not in cd:
                body = r.text[:500]
                if "Not authorized" in body or "initAuthModals" in body:
                    return DownloadResult(label, dest_path, 0, "auth-fail")
                return DownloadResult(label, dest_path, 0, "not-found")
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 15):
                    f.write(chunk)
        return DownloadResult(label, dest_path, dest_path.stat().st_size, "fresh")
    except requests.HTTPError as e:
        return DownloadResult(label, dest_path, 0,
                              f"error:{e.response.status_code}")
    except Exception as e:
        return DownloadResult(label, dest_path, 0, f"error:{type(e).__name__}")


def _download_file(url: str, dest_path: Path, label: str,
                   cookies: dict[str, str]) -> DownloadResult:
    """For non-zip metadata spreadsheets."""
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return DownloadResult(label, dest_path, dest_path.stat().st_size, "cached")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, cookies=cookies, stream=True, timeout=60) as r:
        if r.status_code != 200 or "html" in r.headers.get("content-type", ""):
            return DownloadResult(label, dest_path, 0,
                                  f"auth-fail:{r.status_code}")
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 14):
                f.write(chunk)
    return DownloadResult(label, dest_path, dest_path.stat().st_size, "fresh")


def download_all(dest_dir: Path) -> list[DownloadResult]:
    """Download every English AphasiaBank zip + metadata spreadsheet."""
    cookies = _cookies()
    dest_dir = Path(dest_dir)
    results: list[DownloadResult] = []

    section_lists = {
        "Protocol": PROTOCOL_CORPORA,
        "NonProtocol": NONPROTOCOL_CORPORA,
        "Group": GROUP_CORPORA,
        "Script": SCRIPT_CORPORA,
    }

    work = []
    for section, names in section_lists.items():
        for name in names:
            work.append((
                f"{section}/{name}",
                f"{DATA_BASE}/{section}/{name}?f=zip",
                dest_dir / section / f"{name}.zip",
            ))
    for label, url in SINGLES.items():
        work.append((label, url, dest_dir / f"{label}.zip"))

    for label, url, path in tqdm(work, desc="aphasiabank zips"):
        results.append(_download_zip(url, path, label, cookies))

    # Metadata spreadsheets.
    for fname, url in METADATA_FILES.items():
        path = dest_dir / "metadata" / fname
        results.append(_download_file(url, path, f"metadata/{fname}", cookies))

    return results


@dataclass
class AphasiaTranscriptRecord:
    """One row per AphasiaBank `.cha` session, after parsing the PAR @ID line.

    AphasiaBank embeds the PAR's age (`years;months.`), sex, aphasia subtype,
    and WAB-AQ score in the `@ID:` line at fixed positions:

        eng|Adler|PAR|78;11.|male|Conduction||Participant||72.3|

        positions: 0:lang  1:corpus  2:code  3:age  4:sex  5:subtype
                   6:_     7:role    8:_     9:wab_aq  10:_

    pylangacq's `Headers.participants` only surfaces a subset of these. We
    re-parse the raw `@ID:` line from `Utterance.changeable_header` for each
    file (cheaper than reading the file twice) — actually pylangacq exposes
    them via `Header.other` raw lines. We parse them ourselves to be safe.
    """

    transcript_id: str         # "Protocol/Adler/adler01a"
    section: str               # "Protocol", "NonProtocol", "Group", "Script", "Famous"
    corpus: str                # "Adler"
    participant_id: str        # "Adler01a"  (matches spreadsheet IDs)
    par_code: str              # usually "PAR"; "Participant" role in @ID
    age_years: float | None
    sex: str | None            # "male" / "female" / None
    subtype: str | None        # WAB type from @ID, may be cleaned
    wab_aq: float | None       # WAB-AQ score, 0..100
    n_par_utterances: int      # PAR-only count
    file_path: str
    is_control: bool           # True for Famous/Control + Protocol entries with subtype "Control"
    session_date: str | None = None  # ISO YYYY-MM-DD from @Date header


def _parse_id_line(line: str) -> dict | None:
    """Parse a raw `@ID:` line into a dict of fields. Returns None on malformed."""
    payload = line.split(":", 1)[1].strip() if ":" in line else line.strip()
    parts = payload.split("|")
    if len(parts) < 11:
        return None
    return {
        "lang": parts[0],
        "corpus": parts[1],
        "code": parts[2],
        "age_raw": parts[3],
        "sex": parts[4] or None,
        "subtype": parts[5] or None,
        "role": parts[7],
        "wab_aq_raw": parts[9],
    }


def _age_to_years(age_raw: str) -> float | None:
    """`78;11.` → 78.92; `78;0.` → 78.0; '' → None."""
    if not age_raw:
        return None
    try:
        years_str, months_str = age_raw.split(";", 1)
        years = int(years_str.strip())
        months = int(months_str.replace(".", "").strip() or 0)
        return years + months / 12.0
    except Exception:
        return None


def _aq_to_float(raw: str) -> float | None:
    if not raw:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


_SUBTYPE_NORMALISE = {
    # control variants
    "control": "Control",
    # not-aphasic variants
    "notaphasicbywab": "NotAphasic",
    "notaphasicbywab": "NotAphasic",  # duplicate to be explicit
    "not aphasic": "NotAphasic",
    # transcortical short forms
    "transmotor": "TransMotor",
    "transsensory": "TransSensory",
    # generic "they have aphasia" with no WAB subtype assigned — drop
    "aphasia": None,
    # Research-team-specific codes used by the NEURAL group:
    #   CAPH = Chronic Aphasia, AAPH = Acute Aphasia,
    #   CNBI = Chronic Non-Brain-Injured (control), ANBI = Acute NBI control
    "caph": "Chronic_Aphasia",
    "aaph": "Acute_Aphasia",
    "cnbi": "Control",
    "anbi": "Control",
}


def _normalise_subtype(s: str | None) -> str | None:
    """Strip whitespace and unify common subtype labels.

    Returns None for unknown / unavailable labels so downstream code can
    `dropna(["subtype"])`.
    """
    if not s:
        return None
    s = s.strip()
    if not s or s.lower() in {"u", "unknown", "na", "nan"}:
        return None
    key = s.lower()
    if key in _SUBTYPE_NORMALISE:
        return _SUBTYPE_NORMALISE[key]
    # Title-case canonical labels (Anomic, Broca, Conduction, Wernicke,
    # Global, Isolation, etc.) so "anomic" and "Anomic" merge.
    return s[0].upper() + s[1:].lower() if len(s) > 1 else s.upper()


_DATE_RE = re.compile(r"@Date:\s*([0-9A-Za-z-]+)")


def _parse_date_line(line: str) -> str | None:
    """`@Date: 17-MAY-2007` or similar → ISO `2007-05-17`. None on parse fail."""
    m = _DATE_RE.search(line)
    if not m:
        return None
    raw = m.group(1).strip()
    # Common formats: 17-MAY-2007 / 17-may-2007 / 2007-05-17 / 05/17/2007
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    parts = raw.split("-")
    if len(parts) == 3 and parts[1].lower() in months:
        try:
            d, m_, y = int(parts[0]), months[parts[1].lower()], int(parts[2])
            return f"{y:04d}-{m_:02d}-{d:02d}"
        except ValueError:
            return None
    if len(parts) == 3 and len(parts[0]) == 4:  # already ISO-ish
        try:
            return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        except ValueError:
            return None
    return None


def parse_cha_par_metadata(file_path: Path) -> list[AphasiaTranscriptRecord]:
    """Open one .cha file, return one record per PAR participant in it.

    Most sessions have exactly one PAR (the patient). A few have multiple.
    Skips files where no PAR `@ID` line is present.
    """
    records: list[AphasiaTranscriptRecord] = []
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return records

    # Walk @ID lines; PAR ones are the patient(s). Also pull the @Date
    # so longitudinal Δt is exact rather than inferred from session-letter
    # ordering (which loses calendar gap information).
    par_records = []
    session_date: str | None = None
    for line in text.splitlines():
        if line.startswith("@Date") and session_date is None:
            session_date = _parse_date_line(line)
            continue
        if not line.startswith("@ID"):
            continue
        rec = _parse_id_line(line)
        if rec is None:
            continue
        # Only keep the participant role (PAR / Participant), not investigators.
        role = (rec["role"] or "").lower()
        if role not in {"participant", "control"}:
            continue
        par_records.append(rec)

    if not par_records:
        return records

    # Section / corpus inferred from path under data/raw/aphasiabank.
    parts = file_path.resolve().parts
    try:
        ab_idx = parts.index("aphasiabank")
        section = parts[ab_idx + 1]
        corpus = parts[ab_idx + 2]
    except (ValueError, IndexError):
        section, corpus = "unknown", "unknown"

    n_par = sum(1 for line in text.splitlines() if line.startswith("*PAR"))

    for rec in par_records:
        # Participant ID convention: filename stem (case-folded as in spreadsheet).
        # Spreadsheet uses e.g. "Adler01a", filename "adler01a.cha".
        # Use corpus + filename-numbersuffix.
        stem = file_path.stem
        # ID = corpus + everything in stem after the corpus prefix
        if stem.lower().startswith(corpus.lower()):
            tail = stem[len(corpus):]
            participant_id = corpus + tail
        else:
            participant_id = stem

        records.append(AphasiaTranscriptRecord(
            transcript_id=f"{section}/{corpus}/{stem}",
            section=section,
            corpus=corpus,
            participant_id=participant_id,
            par_code=rec["code"],
            age_years=_age_to_years(rec["age_raw"]),
            sex=rec["sex"],
            subtype=_normalise_subtype(rec["subtype"]),
            wab_aq=_aq_to_float(rec["wab_aq_raw"]),
            n_par_utterances=n_par,
            file_path=str(file_path.resolve()),
            is_control=(section == "Famous"
                        or (rec["subtype"] or "").lower() == "control"),
            session_date=session_date,
        ))
    return records


def index_aphasiabank(dest_dir: Path) -> list[AphasiaTranscriptRecord]:
    """Walk every .cha under aphasiabank/ and build the metadata index."""
    records: list[AphasiaTranscriptRecord] = []
    for cha in sorted(Path(dest_dir).rglob("*.cha")):
        records.extend(parse_cha_par_metadata(cha))
    return records


def extract_all(dest_dir: Path, results: list[DownloadResult]) -> dict[str, Path]:
    """Unzip every successful download into <dest>/<section>/<corpus>/.

    Returns label → extracted-root mapping.
    """
    extracted: dict[str, Path] = {}
    for r in results:
        if not str(r.path).endswith(".zip"):
            continue
        if r.status not in {"fresh", "cached"}:
            continue
        target_dir = r.path.parent / r.path.stem
        if target_dir.exists() and any(target_dir.rglob("*.cha")):
            extracted[r.label] = target_dir
            continue
        target_dir.mkdir(exist_ok=True)
        try:
            with zipfile.ZipFile(r.path) as zf:
                zf.extractall(target_dir)
            extracted[r.label] = target_dir
        except zipfile.BadZipFile:
            shutil.rmtree(target_dir, ignore_errors=True)
            r.status = "bad-zip"
    return extracted
