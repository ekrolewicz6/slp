# BA Web / Batchalign Integration Notes

**Date:** 2026-04-30
**Purpose:** define what we need to know before building a recorder or upload workflow.

## Bottom Line

Do not build a separate clinical language-sample silo yet.

Brian's guidance was that BA Web and Batchalign already cover much of the hard
pipeline: upload media, run ASR/transcription/alignment, produce CHAT-compatible
outputs, and support downstream TalkBank/CLAN analyses. Our near-term job is to
build a recorder and workflow that can feed that ecosystem cleanly, not replace it.

## What Public Sources Confirm

- CLAN is the mature desktop analysis layer for CHAT transcripts and computes
  measures such as MLU, TTR, DSS, IPSyn, EVAL, KIDEVAL, and related profiles:
  https://talkbank.org/0info/manuals/CLAN.html
- KIDEVAL is a CLAN profile program for child language samples. It combines
  measures from DSS, FREQ, MORTABLE, MLU, TIMEDUR, and VOCD into a spreadsheet:
  https://talkbank.org/0info/manuals/CLAN.html
- Batchalign2 is the Python/CLI pipeline for language sample analysis. It can
  run ASR plus segmentation, morphosyntactic analysis, and forced alignment:
  https://github.com/TalkBank/batchalign2
- Batchalign2 can also be used as a Python library around a `Document` object
  with media paths, CHAT files, and TextGrid files:
  https://github.com/TalkBank/batchalign2
- MacWhinney's 2023 Collaborative Commentary paper says clinicians/researchers
  can send a 30-minute audio or video recording to the web for ASR and forced
  alignment and receive a transcription within minutes, with work underway to
  contribute the result to TalkBank:
  https://talkbank.org/aphasia/publications/2023/MacWhinney23.pdf
- AphasiaBank uses controlled access for most clinical data, mediated through
  approved researcher access and AdminView:
  https://talkbank.org/aphasia/access.html

## What Brian Added In The Call

- BA Web already supports file upload and can return several analyses, including
  transcription and acoustic-style analyses.
- He is willing in principle to open the web service more broadly if there is a
  useful recorder/workflow.
- The database and the web service are separate things. Opening an analysis
  endpoint does not mean opening protected clinical data.
- A phone recorder is useful only if it keeps clinician burden low and returns a
  result in a form that is actually interpretable.
- If we upload to our own staging server first, we risk recreating infrastructure
  TalkBank already has. The preferred direction is direct-to-BA-Web or a thin
  compatible handoff.

## Current Local Finding

The current AphasiaBank media cookie is not usable for streaming. A request to a
controlled media URL returns the TalkBank/SLA authentication modal HTML rather
than MP4 bytes, and `ffmpeg` therefore fails. This blocks the full openSMILE
streaming replication until approved-access auth is refreshed.

This does not block local modeling from existing feature tables, and it does not
block designing the recorder workflow.

## Recorder Workflow We Should Build Toward

The first prototype should be local/export-first, not cloud-first.

1. Capture consent/protocol state.
2. Assign or enter a pseudonym; never record name or date of birth.
3. Capture age, language, population/domain, and task condition.
4. Record the minimum task battery:
   - conversation or interview;
   - picture description;
   - narrative/story retell;
   - sentence repetition;
   - nonword repetition;
   - optional comprehension;
   - optional functional rating.
5. Store a local package containing:
   - media file;
   - JSON manifest;
   - task script ID;
   - device/sample-rate metadata;
   - consent/protocol flags;
   - no PHI.
6. Export a BA-Web-compatible upload package.
7. After API details are known, replace export with direct upload/job polling.

## Minimum Manifest

```json
{
  "participant_pseudonym": "site001_p023",
  "age_months": 74,
  "sex": "unknown_or_optional",
  "language": "eng",
  "population": "child_language|aphasia|stuttering|other",
  "task_id": "picture_description_cinderella",
  "task_type": "conversation|picture|narrative|sentence_repetition|nonword_repetition",
  "recorded_at_local_date": "YYYY-MM-DD",
  "device": "ios|android|desktop|unknown",
  "sample_rate_hz": 16000,
  "media_format": "wav|m4a|mp4",
  "consent_protocol": "protocol_id_or_local_flag",
  "contains_phi_in_audio": false,
  "notes": ""
}
```

## Questions For Brian / Franklin

- Is there a documented BA Web upload API, or is the current workflow browser-only?
- What auth flow should a recorder use if the endpoint is opened?
- What media formats, sample rates, file sizes, and duration limits are preferred?
- Does BA Web return CHAT, JSON, TextGrid, CLAN spreadsheets, acoustic features,
  or a job bundle?
- Is there job polling, webhook/callback support, or only synchronous download?
- Can an uploaded file be analyzed without entering the TalkBank database?
- If a file should enter TalkBank later, what metadata and consent fields are
  required at upload time?
- How should pseudonyms, age, and task labels be represented to avoid later
  reformatting?
- Which parts of Batchalign 3 / the new desktop app are already planned so we do
  not duplicate them?
- Is there a preferred bug-report format for malformed CHAT, missing time marks,
  ASR failures, or acoustic-analysis failures?

## Near-Term Engineering Decision

Build a thin local recorder/export prototype before any cloud upload system.

That prototype should prove the UX and metadata discipline:

```text
record task -> validate no obvious PHI fields -> write media + manifest ->
run local Batchalign/CLAN where possible -> export BA-Web-compatible package
```

Direct upload can come after Brian/Franklin confirm the API contract.
