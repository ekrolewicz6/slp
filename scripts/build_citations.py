"""Generate CITATIONS.md from the crawled corpus metadata.

Output is grouped by section and includes:
  - Corpus name + heading + DOI + n_participants + study type + media
  - Investigators + institution
  - Required citation reference(s)
  - The note that AphasiaBank itself must always be cited
"""

from __future__ import annotations

import json
import re
from pathlib import Path


PRIMARY_REFS = [
    "MacWhinney, B., Fromm, D., Forbes, M., & Holland, A. (2011). "
    "AphasiaBank: Methods for studying discourse. *Aphasiology, 25*(11), 1286–1307. "
    "https://doi.org/10.1080/02687038.2011.589893",

    "Forbes, M. M., Fromm, D., & MacWhinney, B. (2012). "
    "AphasiaBank: A Resource for Clinicians. *Seminars in Speech and Language, 33*(3), 217–222. "
    "https://doi.org/10.1055/s-0032-1320041",
]


def _clean(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def render_corpus(record: dict) -> str:
    label = record["label"]
    info = record.get("info_table", {})
    invs = record.get("investigators", [])
    refs = record.get("references", [])

    md = [f"### {label}"]
    if record.get("heading"):
        md.append(f"**{_clean(record['heading'])}**\n")

    fields = [
        ("Participants", info.get("Participants")),
        ("Type of Study", info.get("Type of Study")),
        ("Location", info.get("Location")),
        ("Media", info.get("Media type") or info.get("Media")),
        ("DOI", info.get("DOI")),
    ]
    for k, v in fields:
        if v:
            md.append(f"- **{k}:** {_clean(v)}")

    if invs:
        # Investigators come as ["Name", "", "Department", "", "Institution"] etc.
        cleaned_invs = [_clean(s) for s in invs if _clean(s)]
        if cleaned_invs:
            md.append(f"- **Contributors:** {' / '.join(cleaned_invs)}")

    citation_url = record.get("url")
    if citation_url:
        md.append(f"- **Page:** {citation_url}")

    if refs:
        # Drop the boilerplate "must be accompanied" sentences from the ref list.
        true_refs = [_clean(r) for r in refs
                     if "must be accompanied" not in r and "TalkBank rules" not in r]
        if true_refs:
            md.append("\n**Required reference(s):**")
            for r in true_refs:
                md.append(f"> {r}")
    md.append("")
    return "\n".join(md)


def main() -> None:
    meta_path = Path("data/raw/aphasiabank/metadata/corpus_metadata.json")
    out_path = Path("CITATIONS.md")
    data = json.loads(meta_path.read_text())

    by_section: dict[str, list[dict]] = {}
    for label, rec in data.items():
        section = label.split("/")[0] if "/" in label else "Standalone"
        by_section.setdefault(section, []).append(rec)

    lines = [
        "# Citations & Data Attribution",
        "",
        "This file lists all data sources used in this project, with the formal",
        "references required for any publication. AphasiaBank corpora are",
        "released under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)",
        "and require crediting both the parent project and the contributing site(s)",
        "of every corpus actually used.",
        "",
        "## How to cite this work",
        "",
        "**1. The AphasiaBank parent project** must always be cited:",
        "",
    ]
    for ref in PRIMARY_REFS:
        lines.append(f"> {ref}")
        lines.append("")

    lines += [
        "**2. CHILDES** (developmental data) requires:",
        "",
        "> MacWhinney, B. (2000). *The CHILDES Project: Tools for Analyzing Talk*. "
        "3rd Edition. Mahwah, NJ: Lawrence Erlbaum Associates.",
        "",
        "**3. Funding to acknowledge in any publication using TalkBank data:** "
        "*\"This work has used data from TalkBank, supported by NIH-NIDCD grant "
        "R01-DC008524.\"*",
        "",
        "**4. CLAN / pylangacq** for parsing and analysis:",
        "",
        "> MacWhinney, B. (1991–present). The CHILDES Language ANalysis (CLAN) Programs. "
        "Available from https://dali.talkbank.org/clan/.",
        "",
        "> Lee, J. L., Burkholder, R., Flinn, G. B., & Coppess, E. R. (2016). "
        "Working with CHAT transcripts in Python. Department of Computer Science, "
        "University of Chicago, TR-2016-02. (`pylangacq` library.)",
        "",
        "## Per-corpus citations",
        "",
        "Below: one entry per AphasiaBank corpus actually included in our",
        "feature table. If a corpus is dropped from analysis (e.g. parser",
        "failure, all-NA labels), we still list it here for completeness so",
        "that a future re-run can be properly attributed.",
        "",
    ]

    for section in ["Protocol", "NonProtocol", "Group", "Script", "Standalone"]:
        recs = by_section.get(section, [])
        if not recs:
            continue
        lines.append(f"## Section: {section}")
        lines.append("")
        for rec in sorted(recs, key=lambda r: r["label"]):
            lines.append(render_corpus(rec))

    lines += [
        "## Methods / discourse analyses cited but not (yet) used",
        "",
        "These TalkBank-hosted analytical methods exist; we mention them here so",
        "they are easy to find in any future work that builds on top of this",
        "pipeline:",
        "",
        "- **C-QPA** — Berndt, Wayland, Rochon, Saffran, & Schwartz (2000); "
        "Rochon, Saffran, Berndt, & Schwartz (2000); Saffran, Berndt, & Schwartz (1989). "
        "https://aphasia.talkbank.org/discourse/C-QPA/",
        "- **C-NNLA** — automated Northwestern Narrative Language Analysis. "
        "https://aphasia.talkbank.org/discourse/C-NNLA/",
        "- **CIU** — Correct Information Units. Fergadiotis et al. (2018); "
        "Cunningham & Haley (2020). https://aphasia.talkbank.org/discourse/CIU.docx",
        "- **Main Concepts** — Wright, Capilouto, Wagovich, Cranfill, & Davis (2005). "
        "https://aphasia.talkbank.org/discourse/MainConcepts/",
        "- **Core Lexicon** — https://aphasia.talkbank.org/discourse/CoreLexicon/",
        "- **Story Grammar** — https://aphasia.talkbank.org/discourse/StoryGrammar/",
        "- **SFL (Systemic Functional Linguistics)** — "
        "https://aphasia.talkbank.org/discourse/SFL.docx",
        "- **Spoken Discourse Analysis Resources for Clinicians** — "
        "Dutta et al. (2025), AJSLP. "
        "https://aphasia.talkbank.org/discourse/Dutta2025-Appendix.pdf",
        "",
        "## Derived datasets we know about",
        "",
        "- **Salem (preprocessed Cinderella + paraphasia annotations)** — "
        "https://media.talkbank.org/aphasia/0extra/Salem.zip "
        "(behind TalkBank auth). Companion paper: Salem et al. (medRxiv 2023.06.18).",
        "- **RaPID PSST Challenge** — post-stroke speech transcription shared task; "
        "data via https://github.com/PSST-Challenge/psstdata (separate access form).",
        "- **BNT (Boston Naming Test) — Portland State** — n=132 PWA. "
        "https://aphasia.talkbank.org/password/testresults/BNT-PortlandState.zip",
        "- **VNT (Verb Naming Test) — Portland State** — n=107 PWA. "
        "https://aphasia.talkbank.org/password/testresults/VNT-PortlandState.zip",
        "",
    ]

    out_path.write_text("\n".join(lines))
    print(f"Wrote {out_path} with {len(data)} corpus records.")


if __name__ == "__main__":
    main()
