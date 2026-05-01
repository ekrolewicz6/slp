# Structured Task Inventory

**Date:** 2026-04-30
**Script:** `scripts/run_post_brian_data_inventory.py`

## Scope

Scanned **17,913** local CHAT files under `data/raw/`, excluding `__MACOSX`.
The scan uses file paths and CHAT headers such as `@Types`, `@Activities`,
`@Situation`, `@Media`, and `@G`. It does **not** parse or publish utterance text.

## Headline Findings

- Local data are rich for natural speech, play/conversation, narrative, and
  AphasiaBank picture/story protocol tasks.
- The local headers/path scan found **0**
  sentence-repetition candidate files and **0**
  nonword-repetition candidate files. These low counts mean Brian's preferred
  tight tasks are not well represented in the current local copy.
- Narrative/story candidates are common: **4,785**
  file-category hits.
- Conversation/interview/play candidates are common: **10,566**
  file-category hits.
- Next decision: use current local data for narrative/conversation/picture
  work, but seek or request specific sentence-repetition and nonword-repetition
  datasets before making strong claims about a full battery.

## Category Summary

| category | files | corpora | media_headers | missing_or_unlinked_media |
| --- | --- | --- | --- | --- |
| conversation_interview | 10566 | 88 | 6416 | 1607 |
| narrative_story | 4785 | 73 | 2969 | 711 |
| unclassified | 2839 | 54 | 2179 | 214 |
| picture_description | 2475 | 67 | 2281 | 45 |
| reading | 994 | 34 | 551 | 408 |
| comprehension | 76 | 11 | 32 | 15 |
| fluency_stuttering | 9 | 5 | 7 | 0 |


## Top Candidate Corpora By Structured Category

| bank | section | corpus | category | files | media_headers | missing_or_unlinked_media | gem_marker_files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CHILDES | Eng-NA | Braunwald | conversation_interview | 900 | 200 | 0 | 0 |
| CHILDES | Eng-NA | HSLLD | conversation_interview | 717 | 717 | 642 | 0 |
| CHILDES | Clinical-Eng | Gillam | narrative_story | 668 | 0 | 0 | 667 |
| CHILDES | Eng-UK | MPI-EVA-Manchester | conversation_interview | 594 | 594 | 2 | 0 |
| CHILDES | Eng-NA | NewmanRatner | conversation_interview | 579 | 579 | 0 | 0 |
| CHILDES | Clinical-Eng | EllisWeismer | conversation_interview | 574 | 574 | 1 | 0 |
| CHILDES | Eng-UK | Manchester | conversation_interview | 416 | 215 | 215 | 396 |
| CHILDES | Eng-NA | MacWhinney | conversation_interview | 409 | 408 | 0 | 8 |
| CHILDES | Clinical-Eng | ENNI | narrative_story | 379 | 377 | 375 | 377 |
| CHILDES | Eng-UK | Thomas | conversation_interview | 379 | 379 | 2 | 0 |
| CHILDES | Clinical-Eng | Feldman | conversation_interview | 376 | 0 | 0 | 0 |
| AphasiaBank | Protocol | Fridriksson-2 | narrative_story | 375 | 375 | 2 | 375 |
| AphasiaBank | Protocol | Fridriksson-2 | picture_description | 375 | 375 | 2 | 375 |
| CHILDES | Eng-UK | Edinburgh | conversation_interview | 355 | 355 | 164 | 0 |
| AphasiaBank | extras | Salem | picture_description | 353 | 353 | 0 | 353 |
| AphasiaBank | extras | Salem | narrative_story | 353 | 353 | 0 | 353 |
| CHILDES | Eng-NA | HSLLD | reading | 348 | 348 | 348 | 0 |
| CHILDES | Clinical-Eng | Conti | conversation_interview | 314 | 0 | 0 | 0 |
| CHILDES | Eng-UK | Wells | conversation_interview | 297 | 0 | 0 | 0 |
| AphasiaBank | Protocol | NEURAL-2 | narrative_story | 288 | 288 | 0 | 288 |
| AphasiaBank | Protocol | NEURAL-2 | picture_description | 288 | 288 | 0 | 288 |
| CHILDES | Eng-NA | HSLLD | narrative_story | 283 | 283 | 271 | 0 |
| AphasiaBank | Protocol | NEURAL-2 | conversation_interview | 282 | 282 | 0 | 282 |
| CHILDES | Eng-NA | Gelman | conversation_interview | 251 | 36 | 36 | 251 |
| CHILDES | Clinical-Eng | Feldman | reading | 240 | 0 | 0 | 0 |
| CHILDES | Clinical-Eng | Rescorla | conversation_interview | 239 | 219 | 14 | 58 |
| CHILDES | Clinical-Eng | Conti | narrative_story | 238 | 0 | 0 | 0 |
| CHILDES | Eng-NA | Gelman | narrative_story | 228 | 0 | 0 | 227 |
| CHILDES | Eng-NA | Brown | conversation_interview | 214 | 0 | 0 | 0 |
| CHILDES | Eng-NA | Hicks | narrative_story | 213 | 0 | 0 | 0 |
| CHILDES | Eng-NA | Kuczaj | conversation_interview | 210 | 0 | 0 | 0 |
| CHILDES | Clinical-Eng | Ambrose | conversation_interview | 196 | 196 | 0 | 0 |
| CHILDES | Eng-NA | Morisset | conversation_interview | 196 | 0 | 0 | 0 |
| CHILDES | Eng-NA | Weist | conversation_interview | 182 | 182 | 13 | 0 |
| CHILDES | Eng-NA | NewEngland | conversation_interview | 178 | 178 | 176 | 137 |
| CHILDES | Eng-NA | McCune | conversation_interview | 177 | 177 | 36 | 0 |
| CHILDES | Eng-NA | Rollins | conversation_interview | 175 | 172 | 2 | 0 |
| CHILDES | Clinical-Eng | Nicholas | conversation_interview | 159 | 0 | 0 | 0 |
| CHILDES | Eng-NA | Gopnik | narrative_story | 158 | 0 | 0 | 0 |
| CHILDES | Clinical-Eng | Hooshyar | conversation_interview | 109 | 109 | 73 | 0 |


## Interpretation

This supports the Phase 2 plan. The project can immediately study natural
speech, play/conversation, narrative, picture description, and AphasiaBank
task-conditioned content. It cannot yet fully test Brian's proposed
natural-plus-tight-task battery because sentence repetition and nonword
repetition are sparse or absent in the local headers.

## Next Actions

1. Search alternative header spellings and likely corpora manually, because
   the direct header/path scan found no sentence-repetition or nonword hits.
2. Search TalkBank/BA Web documentation for corpora with sentence repetition
   and nonword repetition.
3. Prioritize structured-task access in the Brian/Franklin follow-up, but ask
   only after producing a concrete inventory.
