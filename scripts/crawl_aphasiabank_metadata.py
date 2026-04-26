"""Crawl per-corpus AphasiaBank pages for citations, contributors, and notes.

Each corpus has a description page at:
    https://aphasia.talkbank.org/access/English/<Section>/<Corpus>.html

These pages contain:
  - Investigator(s) / contributor names + institution
  - Type of study, dates
  - Reference papers (formal citations)
  - IRB / ethics notes
  - Required citation language

We scrape every English corpus + the standalone Famous protocol and emit
a single JSON record per corpus with all extracted fields. Output goes to
data/raw/aphasiabank/metadata/corpus_metadata.json.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


SECTIONS = {
    "Protocol": [
        "ACWT", "APROCSA", "Adler", "BU", "Baycrest", "CC", "CMU", "Capilouto",
        "Elman", "Fridriksson", "Fridriksson-2", "Garrett", "Kansas", "Kempler",
        "Kurland", "MSU", "NEURAL", "NEURAL-2", "Richardson", "SCALE", "STAR",
        "TAP", "TCU", "TCU-bi", "Thompson", "Tucson", "UMD", "UNH", "Whiteside",
        "Williamson", "Wozniak", "Wright",
    ],
    "NonProtocol": [
        "CAP", "ChialFlahive", "Fridriksson", "Goodwin", "Holland1", "Holland2",
        "Hopkins", "Kurland", "Kurland-BATS", "Mackie", "Marshall", "Menn",
        "Oelschlager", "Olness", "Pawleys", "Penn", "QAB", "SCALE", "Shadden",
        "SouthAL", "TeleRounds", "Thompson", "Tucson", "Ulatowska",
    ],
    "Group": ["BU", "Duquesne", "SCALE", "Trove", "Williamson", "Wozniak"],
    "Script": ["Adler", "Fridriksson"],
}

EXTRA_PAGES = {
    "Famous": "https://aphasia.talkbank.org/access/English/Famous.html",
}


def parse_corpus_page(html: str, label: str) -> dict:
    """Extract structured metadata from one corpus HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    record: dict = {"label": label, "raw_excerpt": text[:3000]}

    # Title and headings.
    if soup.title:
        record["title"] = soup.title.text.strip()
    h2 = soup.find(["h2", "h3"])
    if h2:
        record["heading"] = h2.text.strip()

    # Info table — common fields rendered as a 2-column table on these pages.
    info: dict = {}
    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) >= 2:
            k = cells[0].get_text(" ", strip=True).rstrip(":").strip()
            v = cells[1].get_text(" ", strip=True).strip()
            if k and v and len(k) < 80:
                info[k] = v
    record["info_table"] = info

    # Heuristic: extract investigator/department/institution span pairs from
    # the .info span class block.
    investigator = soup.find_all(class_=re.compile(r"investigator|institution|department"))
    if investigator:
        record["investigators"] = [s.get_text(" ", strip=True) for s in investigator]

    # References: paragraphs that look like formal citations
    # (contain a year in parens AND a journal/publisher signal).
    refs = []
    for p in soup.find_all("p"):
        ptext = p.get_text(" ", strip=True)
        if not ptext or len(ptext) < 30:
            continue
        if (re.search(r"\(\d{4}\)", ptext) and
            re.search(r"[A-Z][a-z]+,?\s+[A-Z]\.", ptext)):
            refs.append(ptext)
    record["references"] = refs

    # Required citation language ("any use of data ... must be accompanied by ...").
    must_cite = []
    for p in soup.find_all("p"):
        ptext = p.get_text(" ", strip=True)
        if re.search(r"must be accompanied|please cite|TalkBank rules|cite this",
                     ptext, re.I):
            must_cite.append(ptext)
    record["citation_requirement"] = must_cite

    # Useful download/browse URLs (already known but record them per corpus).
    links = []
    for a in soup.find_all("a", href=True):
        if any(k in a["href"] for k in ("?f=zip", "/TBB/", "media.talkbank")):
            links.append({"text": a.get_text(" ", strip=True),
                          "href": a["href"]})
    record["data_links"] = links

    return record


def crawl_all(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    work: list[tuple[str, str]] = []
    for section, corpora in SECTIONS.items():
        for c in corpora:
            url = f"https://aphasia.talkbank.org/access/English/{section}/{c}.html"
            work.append((f"{section}/{c}", url))
    for label, url in EXTRA_PAGES.items():
        work.append((label, url))

    with requests.Session() as sess:
        for label, url in tqdm(work, desc="corpus pages"):
            try:
                r = sess.get(url, timeout=30)
                if r.status_code != 200:
                    results[label] = {"label": label, "url": url,
                                      "error": f"HTTP {r.status_code}"}
                    continue
                rec = parse_corpus_page(r.text, label)
                rec["url"] = url
                results[label] = rec
            except Exception as e:
                results[label] = {"label": label, "url": url,
                                  "error": f"{type(e).__name__}: {e}"}
            time.sleep(0.05)

    out_file = out_dir / "corpus_metadata.json"
    out_file.write_text(json.dumps(results, indent=2))
    return results


def main() -> None:
    out_dir = Path("data/raw/aphasiabank/metadata")
    results = crawl_all(out_dir)
    n_ok = sum(1 for r in results.values() if "error" not in r)
    n_with_refs = sum(1 for r in results.values() if r.get("references"))
    print(f"\nCrawled {len(results)} pages, {n_ok} ok, "
          f"{n_with_refs} with extracted references.")
    print(f"Output: {out_dir / 'corpus_metadata.json'}")


if __name__ == "__main__":
    main()
