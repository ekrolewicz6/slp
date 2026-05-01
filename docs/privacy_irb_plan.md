# Privacy, Consent, and IRB Plan

**Date:** 2026-04-30
**Status:** planning draft, not legal advice

## Core Principle

Speech samples are potentially identifying, even when names and dates of birth
are removed. The project should treat audio/video as sensitive human-subject
data from the start.

## Near-Term Posture

Use a local-first prototype until the consent and review path is clear.

```text
local recording -> local manifest -> local validation -> manual export
```

No central server, public dataset, or TalkBank deposit should happen unless the
recording was collected under a consent path that permits it.

## Data Classes

| class | examples | default handling |
|---|---|---|
| direct identifiers | name, DOB, address, phone, MRN, school name | never typed into app fields |
| indirect identifiers | voice, rare diagnosis, location, exact age/date combinations | minimize and protect |
| research metadata | pseudonym, age, task, language, population, device | store in manifest |
| raw media | audio/video recording | local by default; upload only with consent |
| derived transcript | CHAT/ASR/human transcript | restricted if derived from protected recording |
| aggregate outputs | counts, model summaries, de-identified metrics | publish only if non-identifying |

## Pseudonymization Rules

- Use site/local participant codes, not initials.
- Store age in months or years, not date of birth.
- Store recording date only when needed for longitudinal intervals.
- For public outputs, use shifted or relative dates.
- Do not include school, facility, city, MRN, or clinician name in filenames.
- Keep any re-identification key outside this repository.

## Consent Tiers

The app should support explicit consent tiers:

1. **Local analysis only**
   - recording stays on user's device;
   - no research sharing;
   - no TalkBank deposit.
2. **Research analysis by project team**
   - recording may be shared with approved researchers;
   - no public release without separate permission.
3. **TalkBank-compatible research deposit**
   - recording/transcript may be deposited under TalkBank terms;
   - requires TalkBank-compatible consent language.
4. **Public/open derived aggregates only**
   - no raw media;
   - no transcript excerpts unless explicitly permitted and de-identified.

## Spoken PHI Risk

The recorder must warn users before each task:

> Do not say names, dates of birth, addresses, school names, medical record
> numbers, phone numbers, or other identifying details during the recording.

The manifest should include:

```json
{
  "spoken_phi_review_required": true,
  "spoken_phi_observed_by_recorder": false,
  "spoken_phi_removed_or_segment_excluded": null
}
```

For MVP, if spoken PHI is suspected, the package should be marked
`requires_review` and excluded from automatic sharing.

## HIPAA / EHR Boundary

Do not pursue EHR extraction as a near-term route.

Brian's practical guidance was that hospital/EHR data require institution-by-
institution agreements and long review cycles. The project should avoid PHI and
clinical records until there is a partner institution and formal protocol.

## IRB Paths

### Path A: Non-Human-Subjects / Public Existing Data

For analyses using public de-identified datasets and existing approved-access
TalkBank data under their terms, document data-use restrictions and avoid
publishing restricted raw data.

This path supports current retrospective modeling.

### Path B: Independent IRB For Citizen-Science / Recorder Pilot

Use an independent IRB if collecting new recordings outside a university.

Needed artifacts:

- protocol;
- consent form;
- recruitment language;
- data handling plan;
- risk assessment;
- withdrawal/deletion process;
- data sharing plan;
- child assent/parent permission if collecting child samples.

### Path C: Partner-Lab IRB

Use when collaborating with an academic or clinical lab.

Advantages:

- existing human-subjects infrastructure;
- easier data-access credibility;
- clearer route to NIH-style funding;
- better clinical review.

Tradeoff: slower and dependent on partner priorities.

## Minimal Consent Language Topics

A consent form should cover:

- purpose: research on language sample measurement;
- what is recorded;
- expected duration;
- risks: voice may be identifying, accidental personal information;
- benefits: no guaranteed personal benefit;
- voluntary participation;
- stopping/withdrawing;
- who can access recordings;
- whether recordings may be shared with TalkBank or other researchers;
- whether derived de-identified results may be published;
- data retention period;
- contact for questions.

## Data Retention Defaults

For MVP:

- raw media: local device only unless explicitly exported;
- exported packages: user-controlled folder;
- derived aggregate outputs: ok for repo if non-identifying;
- private transcripts/interviews: `docs/private/` and gitignored;
- credentials: `.env` only and gitignored.

## Repository Rules

Never commit:

- `.env`;
- raw TalkBank data;
- raw audio/video;
- private transcripts;
- participant-level text excerpts from restricted corpora;
- direct identifiers;
- cookies or bearer tokens.

Aggregate summaries and scripts may be committed when they do not include
restricted transcript text or credentials.

## Pre-Collection Checklist

- [ ] Protocol written.
- [ ] Consent tier selected.
- [ ] Pseudonym scheme defined.
- [ ] Re-identification key storage defined outside repo.
- [ ] Spoken-PHI warning implemented.
- [ ] Deletion/withdrawal process written.
- [ ] Data retention period written.
- [ ] IRB path selected.
- [ ] TalkBank deposit rules confirmed if applicable.
- [ ] SLP workflow tested with non-sensitive demo recordings.

## Open Questions

- Does TalkBank have preferred consent wording for BA Web-originated deposits?
- Can BA Web analyze recordings that are not intended for database deposit?
- What metadata are required for eventual TalkBank contribution?
- What independent IRB provider is appropriate if the project remains outside a
  university?
- What is the minimum clinical review needed before SLP-facing reports are shown
  to families or patients?
