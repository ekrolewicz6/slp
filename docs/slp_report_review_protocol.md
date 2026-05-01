# SLP Report Review Protocol

**Date:** 2026-04-30
**Status:** ready for informal review

## Purpose

Test whether the language-state report packets are understandable, useful, and
safe enough to justify prospective clinical data collection.

This is not a validation study and does not ask SLPs to diagnose or treat based
on the report. It asks whether the report format identifies clinically
meaningful questions and next probes.

## Materials

Use:

- `outputs/slp_report_packets/review_packet_index.md`
- `outputs/slp_report_packets/adult_aphasia_packet.md`
- `outputs/slp_report_packets/child_language_dld_packet.md`
- `outputs/slp_report_packets/stuttering_recovery_packet.md`

Do not include raw transcripts, audio, private meeting notes, or any
identifiable patient information.

## Reviewers

Initial informal target:

- Rebekah;
- 1 adult neuro/aphasia SLP if available;
- 1 child language/school SLP if available;
- 1 fluency specialist if available.

The first round can be 2-5 reviewers. The goal is to find failure modes, not to
estimate population-level preference.

## Session Structure

Estimated time: 30-45 minutes.

1. Give the reviewer the safety boundary:
   - these are research artifacts;
   - they are not diagnostic;
   - they do not recommend treatment;
   - reconstructed AI text is not scored as patient ability.
2. Ask them to read 2-4 cards in their domain.
3. For each card, ask the review questions below.
4. Ask for final ranking of usefulness and risk.
5. Record feedback in the template table.

## Per-Card Questions

For each report card:

1. What do you think is the main communication problem?
2. What would you assess or probe next?
3. Does the report contain enough evidence to justify that next probe?
4. Which field is most useful?
5. Which field is confusing, unsafe, or too abstract?
6. What important context is missing?
7. Would this change how you monitor progress?
8. What would make you trust it more?

## Ratings

Use 1-5 ratings:

- understandability;
- clinical usefulness;
- actionability for next assessment;
- risk of misinterpretation;
- fit with SLP workflow;
- trust if raw transcript/audio excerpts were available;
- trust without excerpts.

For risk of misinterpretation, higher means riskier.

## Required Free-Text Fields

- "I would remove or rename..."
- "I would add..."
- "This could mislead someone because..."
- "The most clinically useful part is..."
- "Before using this with a patient, I would need..."

## Success Criteria

The report format is promising if:

- reviewers can explain the main state problem without model-internal help;
- reviewers can name a plausible next probe;
- reviewers identify at least one clinically useful field;
- reviewers do not think the report implies diagnosis or treatment selection;
- risk fields lead to concrete edits rather than wholesale rejection.

The report format fails if:

- reviewers cannot interpret the axes;
- the next-probe suggestions feel arbitrary;
- the report seems more confident than the evidence;
- reviewers believe it would encourage unsafe automation;
- the missing context is so large that the report cannot be judged.

## Review Data Template

| reviewer_id | role | packet | case_id | main_problem_free_text | next_probe_free_text | understandability_1_5 | usefulness_1_5 | actionability_1_5 | misinterpretation_risk_1_5 | workflow_fit_1_5 | most_useful_field | confusing_or_unsafe_field | missing_context | would_change_monitoring_y_n | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Analysis Plan

For the first round:

1. Summarize median ratings by packet type.
2. List every confusing/unsafe field.
3. Count whether reviewers can name a plausible next probe.
4. Identify fields to rename, remove, or split.
5. Convert the feedback into V3 report changes before collecting patient data.

## Decision Gate

Do not start prospective patient collection until the first SLP review has at
least one clear positive use case and no unresolved high-risk misunderstanding.
