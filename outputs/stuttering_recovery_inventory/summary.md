# Stuttering Recovery Inventory

**Date:** 2026-04-30
**Script:** `scripts/run_post_brian_data_inventory.py`

## Local Finding

- Local FluencyBank directory present: **False**
- Local fluency/stuttering/cluttering header/path candidates: **9**
- The local candidates are not enough to run Brian's proposed child stuttering
  recovery experiment. In this checkout, the only obvious fluency hits are
  local clinical/aphasia-style files, not a child longitudinal FluencyBank
  recovery corpus.

## Local Fluency Candidates By Corpus

| bank | section | corpus | files | media_headers | missing_or_unlinked_media |
| --- | --- | --- | --- | --- | --- |
| AphasiaBank | NonProtocol | Marshall | 3 | 3 | 0 |
| AphasiaBank | Protocol | UNH | 2 | 2 | 0 |
| CHILDES | Eng-NA | Brown | 2 | 0 | 0 |
| AphasiaBank | Protocol | Wozniak | 1 | 1 | 0 |
| AphasiaBank | extras | Salem | 1 | 1 | 0 |


## External FluencyBank Candidates To Request Or Download

| corpus | url | why_it_matters |
| --- | --- | --- |
| FluencyBank main access | https://talkbank.org/fluency/ | Research data are consortium/password restricted; teaching data are open. Access request is separate from AphasiaBank. |
| Purdue | https://talkbank.org/fluency/access/Purdue.html | TalkBank page references 4- and 5-year-old children who stutter and persistence/recovery. |
| Wagovich | https://talkbank.org/fluency/access/Password/Wagovich.html | Longitudinal child stuttering/language-growth protocol over roughly ten months. |
| Ratner | https://talkbank.org/fluency/access/Password/Ratner.html | Children who stutter plus matched fluent peers across published reports. |
| UMD-CMU | https://talkbank.org/fluency/access/UMD-CMU.html | Young-child disfluency work with utterance-level predictors; may support language-fluency modeling. |
| Voices-CWS | https://talkbank.org/fluency/access/Voices-CWS.html | Child stuttering teaching corpus with reading/conversation contrast; likely not recovery-focused. |


## Access Implication

The stuttering recovery track is scientifically high priority, but locally
blocked until FluencyBank access is obtained or the relevant corpora are
downloaded. Brian's point still changes the plan: stuttering should be the
first recovery-prediction target once access is available.

## Next Actions

1. Apply for or request FluencyBank access separately from AphasiaBank.
2. Prioritize Purdue, Wagovich, Ratner, and UMD-CMU because they are the most
   aligned with child stuttering, language features, and recovery/persistence.
3. After access, rerun this inventory and then run the first-pass recovery
   model from `TASKS.md` task 4.1.
