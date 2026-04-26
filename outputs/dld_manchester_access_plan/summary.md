# Manchester Language Study Access And Join Plan

## Why This Dataset Matters

The Manchester Language Study is the best near-term route from transcript-state discovery to clinically meaningful DLD outcomes.

The ReShare age-11 page describes a longitudinal DLD cohort recruited around age 7 and followed into later childhood and young adulthood. The age-11 collection includes aims directly aligned with this project:

- sensitive markers for DLD
- literacy abilities
- social difficulties and victimization
- educational placements
- National Curriculum outcomes
- long-term educational needs

Source: https://reshare.ukdataservice.ac.uk/853965/

## Access Status

The actual SPSS/Stata data files are listed as available to registered UK Data Service users under safeguarded access. Documentation files are open access.

This means the next action is not anonymous download. It is registered access through UK Data Service, then local import.

## Desired Tables

Minimum table schema after access:

| Table | Unit | Required Fields |
| --- | --- | --- |
| `mls_participants` | child | stable ID, sex, language exposure, nonverbal cognition if available, original recruitment info |
| `mls_language_scores` | child x wave | age, standardized language scores, receptive/expressive measures, narrative measures |
| `mls_literacy_scores` | child x wave | reading accuracy, reading comprehension, spelling/writing |
| `mls_school_outcomes` | child x wave | education placement, National Curriculum outcomes, support services |
| `mls_social_outcomes` | child x wave | social difficulty, victimization, participation, mental health/well-being |
| `mls_intervention` | child x interval | SLT support, school support, therapy exposure if present |

## Join Strategy

The local CHILDES Conti/Clinical-Eng transcripts may overlap conceptually with Conti-Ramsden cohorts, but they should not be assumed to share stable IDs with MLS outcome data.

Preferred join order:

1. Use explicit participant IDs only if documentation confirms shared identifiers.
2. If no direct join exists, treat MLS as an outcome-only validation dataset and use its variables to design a prospective outcome schema.
3. Do not probabilistically join by age, sex, or corpus path.

## Modeling Questions After Access

1. Do early language-state axes predict later literacy better than MLU and age?
2. Do DLD residual subtypes predict different school/social outcomes?
3. Does narrative-state weakness predict reading comprehension more than speech-length weakness?
4. Are children with similar standardized scores separable into different risk profiles?
5. Does intervention/support exposure moderate state trajectories?

## Import Plan

After registered download:

```bash
.venv/bin/python - <<'PY'
import pandas as pd
df = pd.read_spss('SPSS_database_MLS_age_11.sav')
df.to_parquet('data/external/mls/mls_age_11.parquet', index=False)
PY
```

If Stata files are easier:

```bash
.venv/bin/python - <<'PY'
import pandas as pd
df = pd.read_stata('STATA_database_MLS_age_11.dta')
df.to_parquet('data/external/mls/mls_age_11.parquet', index=False)
PY
```

## Immediate Local Next Step

Before access, use the open documentation files to create a variable dictionary and mark each variable as:

- language
- literacy
- school
- social/participation
- intervention/support
- demographic/fairness
- unusable/free text/unknown

