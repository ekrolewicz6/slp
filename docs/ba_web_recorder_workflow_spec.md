# BA Web-Compatible Recorder Workflow Spec

**Date:** 2026-04-30
**Status:** MVP workflow spec for discussion with Brian/Franklin
**Related docs:** `docs/ba_web_integration_notes.md`,
`docs/minimum_language_state_battery.md`, `docs/slp_state_report_v2_spec.md`

## Goal

Create a low-burden recorder workflow that lets clinicians, researchers, or
families capture useful language samples and export them in a form that can feed
BA Web / Batchalign / CLAN without creating a separate data silo.

The recorder's first job is not diagnosis. Its first job is clean data capture:

```text
task script -> recording -> metadata manifest -> local validation ->
BA-Web-compatible package -> analysis -> SLP-readable state report
```

## Non-Goals

- No diagnosis.
- No treatment recommendation.
- No EHR integration.
- No permanent cloud storage in the MVP.
- No upload to TalkBank's database without explicit consent and protocol.
- No scoring of ASR/LLM-reconstructed text as patient-produced language.

## User Types

| user | primary need | product implication |
|---|---|---|
| SLP clinician | fast sample capture during real caseload pressure | two-minute setup, reusable participant profiles, minimal typing |
| researcher | protocol consistency and metadata completeness | exportable manifests, task IDs, audit logs |
| family/citizen-science participant | simple guided recording and referral-safe output | plain instructions, no raw clinical claims |
| TalkBank admin/researcher | compatible packages and consent clarity | predictable file names, manifest schema, no PHI fields |

## MVP Workflow

1. Select population:
   - adult aphasia;
   - child language/DLD;
   - stuttering;
   - other/research.
2. Create participant pseudonym.
   - Required: pseudonym, age in months or years, language(s), task date.
   - Optional: sex/gender, dialect/context, clinician/research site code.
   - Forbidden in app fields: name, date of birth, address, phone, MRN.
3. Show task script.
4. Record audio or video.
5. Run local validation.
6. Save a local package.
7. Export package for BA Web / Batchalign.
8. Optionally import returned CHAT/analysis outputs and generate a state report.

## Minimum Task Battery

The app should support modular task blocks, not one monolithic assessment.

### Adult Aphasia

- conversation/interview;
- picture description;
- narrative/story retell;
- repetition if protocol permits;
- naming/word retrieval if task materials are available;
- optional comprehension probe.

### Child Language / DLD

- natural conversation/play sample;
- picture description;
- narrative/story retell;
- sentence repetition;
- nonword repetition;
- optional comprehension;
- parent/teacher functional context rating.

### Stuttering

- natural conversation;
- reading if age-appropriate;
- sentence repetition or structured elicitation;
- optional parent/caregiver impact/context rating.

## Package Layout

Each recording package is a folder:

```text
package_id/
  manifest.json
  media/
    participant_task_001.wav
  tasks/
    task_script.md
  audit/
    local_validation.json
  derived/
    optional_chat_or_analysis_outputs/
```

Use WAV for the first prototype because it is easiest for downstream tooling.
Mobile capture may begin as M4A, but export should transcode to 16 kHz or 44.1
kHz mono WAV depending on BA Web preference.

## Manifest Schema

```json
{
  "schema_version": "0.1",
  "package_id": "site001_p023_2026-04-30_picture_cookie",
  "participant": {
    "pseudonym": "site001_p023",
    "age_months": 74,
    "language_primary": "eng",
    "languages_other": [],
    "sex_or_gender_optional": null,
    "population": "child_language"
  },
  "task": {
    "task_id": "picture_cookie_theft_v1",
    "task_type": "picture_description",
    "prompt_language": "eng",
    "script_version": "0.1"
  },
  "recording": {
    "media_file": "media/participant_task_001.wav",
    "media_format": "wav",
    "sample_rate_hz": 16000,
    "channels": 1,
    "duration_s": null,
    "device": "ios|android|desktop|unknown",
    "recorded_local_date": "2026-04-30"
  },
  "consent": {
    "consent_protocol": "local_mvp_no_upload",
    "allow_analysis": true,
    "allow_research_sharing": false,
    "allow_talkbank_deposit": false
  },
  "privacy": {
    "names_entered_in_app": false,
    "dob_entered_in_app": false,
    "phi_warning_acknowledged": true,
    "spoken_phi_review_required": true
  },
  "analysis": {
    "intended_destination": "local_export|ba_web|batchalign",
    "asr_allowed_for_support": true,
    "asr_allowed_for_measurement": false
  }
}
```

## Local Validation Gates

The recorder should refuse or warn before export when:

- participant pseudonym is missing;
- age is missing;
- task ID is missing;
- recording is too short;
- recording is silent or clipped;
- sample rate/channel metadata are missing;
- the user typed a name, date of birth, or MRN into a field;
- consent flags are internally inconsistent;
- media file is missing;
- package has no manifest.

The recorder should warn, not refuse, when:

- no structured task is present;
- no repetition/nonword task is present for child/DLD;
- no audio quality estimate is available;
- user indicates spoken PHI may be present.

## State Report Import

When BA Web / Batchalign returns transcript or analysis outputs, the recorder
can import them and generate a local state report.

Report rules:

- Raw transcript/audio is the measurement source.
- ASR text may be shown as draft transcription, not final evidence.
- LLM summaries must be labeled as generated support.
- Every report includes uncertainty and "do not infer" fields.

## Privacy Posture

MVP should be local-first:

```text
record locally -> export package -> user chooses where to upload
```

No central server until:

- consent language is reviewed;
- independent IRB or partner-lab path is selected;
- data retention/deletion policy is written;
- BA Web API/upload contract is known.

## Questions For Brian / Franklin

1. Is there a BA Web upload API, or should MVP export packages for browser upload?
2. What exact media formats and sample rates should the package use?
3. What metadata should map directly into CHAT headers?
4. Can BA Web analyze without database deposit?
5. What output bundle should we expect: CHAT, TextGrid, CLAN spreadsheet, JSON,
   acoustic CSV, or all of these?
6. Should task IDs follow an existing TalkBank naming convention?
7. What validation errors would be most useful to Franklin as bug reports?
8. How should Batchalign 3 / the new desktop app change this plan?

## Implementation Order

1. Desktop/local prototype that records or imports audio and writes manifest.
2. Local package validator.
3. Task-script library.
4. Manual BA Web export.
5. Returned-output importer.
6. Local state-report generation.
7. Direct BA Web upload only after API confirmation.
