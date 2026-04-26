# Prospective DLD Study Blueprint

## Core Question

Can early natural speech state predict persistent DLD risk, literacy outcomes, and treatment-relevant profiles better than age, MLU, and broad screening labels?

## Minimal Study Design

Participants:

- children ages 2.5 to 7 years
- oversample late talkers, suspected DLD, and typically developing controls
- include bilingual/multilingual children rather than excluding them

Sampling:

- baseline, 6 months, 12 months, 24 months
- optional annual school-age follow-up for literacy and participation

Speech/language samples:

- 10-minute parent-child conversation
- brief narrative retell
- picture description
- optional classroom or home naturalistic sample

## Required Measures

Language:

- standardized expressive and receptive language scores
- narrative sample
- vocabulary
- grammar/morphosyntax
- speech sound/phonology screen

Outcomes:

- reading accuracy
- reading comprehension
- spelling/writing
- teacher-rated classroom communication
- parent-rated functional communication
- social participation or peer difficulty

Intervention:

- whether child receives SLT
- therapy goals
- frequency/dose
- setting
- school support
- home practice if available

Fairness and context:

- age
- sex/gender
- race/ethnicity where appropriate and consented
- socioeconomic indicators
- parent education
- language exposure and bilingual status
- dialect/region
- hearing status
- nonverbal cognition

## AI/Measurement Rules

- Raw human transcript or validated transcript is used for assessment.
- ASR is stored with confidence/uncertainty and never silently treated as ground truth.
- LLM rewriting is communication support only unless separately validated.
- All generated summaries must preserve uncertainty and avoid diagnostic claims.

## Primary Endpoints

1. Persistent language risk at 24 months.
2. Literacy outcome at school-age follow-up.
3. Functional communication rating.
4. Change in language-state axes over time.
5. Clinician-rated usefulness of state reports.

## Main Hypotheses

1. Multi-axis language state predicts persistent risk better than age + MLU.
2. Narrative/content state predicts literacy and reading comprehension better than output length alone.
3. Children with similar broad scores separate into distinct profiles with different outcome risks.
4. Near-threshold target policies identify more plausible therapy targets than weakest-skill policies.
5. ASR uncertainty is systematically higher for children most at risk, so measurement safety must be modeled explicitly.

## Minimal Data Package For This Repo

One row per child/session:

- stable child ID
- date/age
- task IDs
- transcript path
- audio path or secure reference
- language scores
- literacy scores when available
- intervention exposure
- demographic/context fields

One row per utterance:

- child ID
- session ID
- task ID
- speaker
- start/end time if audio aligned
- raw transcript
- ASR transcript if used
- ASR confidence fields

One row per clinician/patient rating:

- child/session/report ID
- rater role
- usefulness
- safety
- interpretability
- target agreement

