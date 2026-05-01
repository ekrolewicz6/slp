# Data Access And Literature Scan

**Date:** 2026-05-01  
**Scope:** web scan plus local download pass for the data/paper gaps identified after Brian MacWhinney's 2026-04-29 guidance: FluencyBank recovery corpora, Manchester/SCALES longitudinal DLD data, structured sentence/nonword repetition tasks, DLD treatment-response data, acoustic standards, aphasia discourse measurement, and recent treatment-personalization papers.

## Local Cache

Downloaded or indexed **35** literature/data-document records into gitignored `data/external/literature/` (**40.0 MB** counted from manifest records). Raw PDFs, spreadsheets, OSF CSVs, and documentation are intentionally not committed. The committed manifest is `outputs/data_access_scan/source_manifest.csv`.

Status counts:

| status | count |
|---|---:|
| blocked_http_403 | 1 |
| copied_from_downloads | 1 |
| downloaded | 31 |
| failed | 1 |
| html_cached | 1 |

Category counts:

| category | count |
|---|---:|
| acoustics | 1 |
| aphasia_discourse | 4 |
| aphasia_treatment | 1 |
| dld_longitudinal | 2 |
| dld_treatment | 3 |
| manchester_docs | 13 |
| nature_2025 | 1 |
| paired_tasks | 3 |
| structured_tasks | 3 |
| stuttering | 4 |

## What Is Downloadable Now

| source | access result | why it matters |
|---|---|---|
| Dryad EMT-SF DLD randomized trial dataset | Already local and public. Dryad provides de-identified longitudinal REDCap-style data and R scripts, but not raw transcripts/audio/session-by-session treatment targets. | Best current DLD treatment-response foothold; supports early-movement outcome modeling but not target/dose optimization. |
| Calder et al. 2020 explicit grammar intervention | Article PDF and all ASHA Figshare supplemental materials downloaded. | Small single-case DLD treatment dataset with repeated trained/untrained/control probes; useful for treatment-target measurement and response-curve methods. |
| Fiveash et al. 2023 rhythmic-prime sentence repetition | Article PDF plus OSF sentence-repetition data/script files downloaded. | Immediate structured-task experiment: test how sentence repetition score, age, reading, and rhythm manipulation expose DLD-related syntax state. |
| openSMILE/eGeMAPS standard | eGeMAPS paper downloaded. | Supports Brian's recommendation to align acoustic features with standard openSMILE/eGeMAPS rather than only custom Praat-style features. |
| Aphasia discourse measurement papers | FLUCALC, CIU/discourse ML, multimodal aphasia discourse, and recent digital-twin article page cached/downloaded. | Supports the measurement-firewall direction: objective discourse dimensions plus cautious treatment-personalization claims. |
| Manchester Language Study documentation | Age 7/11/16 blank forms, variable lists, and readmes downloaded where open; age 23 readme/interview forms downloaded, variable list is registered-only. | We can design the analysis before gaining UK Data Service access. |
| SCALES documentation | UK Data Service user guide downloaded. | Highest-value non-TalkBank DLD longitudinal target because it includes repeated school-age language/literacy/cognition/mental-health measures and sentence repetition markers. |

## Still Gated Or Not Fully Downloadable

| source | current status | next action |
|---|---|---|
| FluencyBank IISRP, IISRP-new, Wagovich, Ratner, Maxfield | Password/consortium-gated. The current cookie downloaded all non-password corpora, but these recovery-relevant corpora remain blocked. | Brian/password access request already in progress; once available, rerun the FluencyBank download inventory and recovery replication. |
| SCALES participant-level data | UK Data Service safeguarded/restricted access; public page says access may be granted on request. | Apply through UKDS or partner-lab route. This is now the top DLD access target. |
| Manchester Language Study participant-level data | ReShare says data downloads require registered UK Data Service users; some age-23 scanned forms are closed/request-permission. | Apply through UKDS after prioritizing SCALES, because Manchester is rich for long-term outcome trajectories but less directly tied to current transcript/audio measurement. |
| EMT-SF raw language samples/audio/session targets/dose | Not in Dryad package. | Ask Roberts/Hadley/Kaiser or collaborators only after we have a concise analysis memo from aggregate Dryad results. |
| BA Web direct upload/API | Public BA Web upload API contract not found. | Ask Brian/Franklin for the minimal auth/upload/job-status contract once recorder spec is stable. |
| Lorusso et al. Zenodo NWRT spreadsheet | Zenodo landing page is open and lists the XLSX, but this environment got HTTP 403 on the direct file. | Manual browser download or retry from a different network; the paper PDF is local. |

## Priority Implication

The next highest-learning step is no longer generic web searching. It is to use the newly local structured-task material and the access map in this order:

1. Run a Fiveash sentence-repetition structured-task pilot from the OSF CSVs.
2. Add Calder repeated-probe treatment data to the DLD treatment-response track as a single-case response-curve testbed.
3. Prepare SCALES and Manchester access packets, with SCALES first because it directly addresses Brian's natural-plus-tight-task point and has repeated longitudinal outcomes.
4. Continue Purdue stuttering robustness while waiting for password-gated FluencyBank corpora.
5. Treat the 2026 bilingual aphasia digital-twin RCT as a benchmark for how high the bar is: a prospective randomized treatment-assignment test, not just retrospective prediction.

## Files

- Local gitignored literature/data cache: `data/external/literature/`
- Committed manifest: `outputs/data_access_scan/source_manifest.csv`
- This summary: `outputs/data_access_scan/summary.md`
