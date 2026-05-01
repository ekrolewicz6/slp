# Treatment-Response Evidence Inventory

**Date:** 2026-04-30
**Question:** Can existing public or requestable data support individualized
SLP treatment-response modeling now?

## Bottom Line

The strongest immediately relevant treatment-response source is the 2026 Dryad
EMT-SF DLD randomized-trial dataset. It is public, de-identified, longitudinal,
and includes treatment assignment plus baseline language-sample variables and
follow-up vocabulary/grammar outcomes.

Most other treatment evidence is scientifically useful but not yet directly
usable for individualized modeling because it lacks shared participant-level
speech samples, treatment dose/session data, or repeated discourse measures.

## Source Inventory

| source | domain | access | individual data | speech samples | treatment/dose | outcome timing | modeling value |
|---|---|---:|---:|---:|---:|---:|---|
| Dryad EMT-SF DLD trial, DOI `10.5061/dryad.sj3tx96g9` | child DLD / late language risk | public, WAF/browser-gated download | yes | language-sample variables, not raw transcripts | treatment group; caregiver EMT-SF intervention | baseline, 6mo, 12mo | **high** for first treatment-response model |
| Calder et al. grammar intervention Figshare supplement | child DLD grammar | public | small-N single-case repeated probes | probe scores, not open transcripts | 20 sessions, 50 trials/session | repeated treatment probes and maintenance | medium; target-specific learning curves |
| RELEASE aphasia IPD meta-analysis | adult aphasia | published aggregate/IPD project; raw IPD not openly packaged | yes in RELEASE collaboration | no shared transcript/audio package | frequency, intensity, duration, dosage | multiple aphasia outcomes | high scientifically, low immediate local modeling |
| AphasiaBank script-training corpora | adult aphasia/apraxia | TalkBank approved access | likely participant/session data | transcripts/media for script training corpora | treatment context present in corpora | pre/post or therapy-related samples in some sets | medium-high after TalkBank access/auth works |
| FluencyBank Purdue | child stuttering | TalkBank/FluencyBank access | yes | transcripts/media, partial CHAT conversion | not primarily treatment, but recovery/persistence | 3-year follow-up | **very high** for recovery prediction |
| FluencyBank Ratner | child stuttering | password-restricted TalkBank | yes | transcripts/media | not primarily treatment | initial plus some follow-up samples | high for onset/early-risk modeling |
| FluencyBank UMD-CMU | child stuttering and fluent peers | TalkBank | yes | annual conversation video | not primarily treatment | 3 annual samples | high for longitudinal state and disfluency mechanisms |
| Manchester Language Study / Conti-Ramsden | DLD long-term outcomes | request/registered access | yes | child language data likely available through TalkBank subset | not treatment-response | long-term language/literacy/social outcomes | high for persistent-risk, not treatment dosing |
| What Works / intervention evidence maps | child speech/language | public summaries | no | no | intervention categories | study-level outcomes | useful for literature map, not individual models |

## Download / Access Status

### Dryad EMT-SF DLD

Dataset page: https://datadryad.org/dataset/doi:10.5061/dryad.sj3tx96g9

The public page reports:

- 108 enrolled children, with 7 excluded from the shared dataset because they
  did not consent to additional sharing;
- randomized EMT-SF treatment versus control;
- baseline around 30 months, follow-up around 36 and 42 months;
- baseline PLS-5, language-sample variables, child-caregiver interaction
  measures, and demographics;
- follow-up vocabulary outcomes at 36 months and grammar outcomes at 42 months.

Local CLI download is currently blocked by Dryad/AWS WAF:

- direct `downloads/file_stream/*` returns `403`;
- API file download returns `401` requiring a current bearer token.

Manual browser download should work. Target local folder:

```text
data/external/dryad_emt_sf_dld/
```

Expected files:

```text
Maximizing_Outcomes_for_Toddlers_with_DLD_Data.csv
Maximizing_Outcomes_for_Toddlers_with_DLD_Data_Dictionary.csv
README.md
U01_Analysis_2-1_Dryad.Rmd
U01_Analysis_2-2_Dryad.Rmd
```

Once present, the next experiment should model:

```text
baseline state + treatment assignment -> T36 vocabulary and T42 grammar
```

with baselines:

- treatment only;
- baseline language-sample variable only;
- baseline standardized score only;
- demographics only;
- state-plus-treatment interaction.

### TalkBank / AphasiaBank Media

Current local `.env` has a legacy `APHASIABANK_COOKIE`, but media requests
return TalkBank/SLA auth HTML rather than MP4 bytes. Scripts now support:

```text
TALKBANK_COOKIE_HEADER='full browser Cookie header'
```

After a refreshed browser cookie works, run:

```bash
.venv/bin/python scripts/check_talkbank_media_access.py
```

Then run full openSMILE/eGeMAPS extraction.

### FluencyBank

Local FluencyBank data are absent. Highest-value acquisition targets:

1. Purdue: persistence/recovery over three years, nearly 200 children.
2. Ratner: enrolled children within three months of stuttering onset, with
   some follow-up.
3. UMD-CMU: annual samples over three years, with stuttering and matched fluent
   children.
4. Wagovich: 10 monthly speech/language samples in preschool children who
   stutter.

The key modeling question is not treatment response yet:

```text
early language/acoustic/disfluency state -> eventual recovery or persistence
```

## Highest-Value Experiments Enabled By This Inventory

1. **DLD EMT-SF treatment-response pilot.** Use the Dryad dataset to test whether
   baseline language-sample state moderates response to caregiver-implemented
   EMT-SF.

2. **Aphasia dose/outcome bridge.** Use RELEASE as the external clinical prior:
   dosage/frequency effects are real but domain-specific. Ask whether our
   discourse state dimensions predict which outcome domain should move.

3. **Script-training discourse audit.** Once TalkBank access works, search
   AphasiaBank script-treatment corpora for pre/post or therapy-linked samples
   and test whether content/recoverability improves before broad scores.

4. **Stuttering recovery model.** Once FluencyBank is downloaded, prioritize
   recovery/persistence over treatment-response because the longitudinal outcome
   is scientifically cleaner and Brian specifically pointed to this as valuable.

5. **Evidence-to-data gap map.** For each intervention paper, score whether it
   contains the fields needed for actual treatment optimization:
   participant baseline state, treatment target, dose, session timing, repeated
   speech sample, outcome, follow-up, and data access.

## Interpretation

Brian's warning holds: the field has many treatment papers but very little
open, transcript-linked, participant-level treatment-response data. The fastest
honest path is therefore:

```text
public EMT-SF DLD response pilot
-> FluencyBank recovery prediction
-> AphasiaBank script/pre-post audit
-> prospective recorder-based treatment data collection
```

That sequence preserves the original vision while avoiding a premature claim
that we can optimize treatment before the right data exist.
