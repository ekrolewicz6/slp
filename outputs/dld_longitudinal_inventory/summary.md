# DLD / Late-Talker Longitudinal Inventory

**Date:** 2026-04-30
**Script:** `scripts/run_dld_longitudinal_inventory.py`

## Scope

Loaded `data/features/phase1_windowed_features.parquet` and restricted to
Clinical-Eng windows. Participant roots use the same reconstruction logic as
the DLD screening and Rescorla catch-up scripts. Ages are repaired from paths
for Rescorla and common EllisWeismer age/task tokens where needed.

## Headline Counts

- Clinical-Eng windows: **4,067**
- transcripts: **2,307**
- reconstructed participant roots: **1,562**
- participants with repeated transcripts or repeated ages: **271**
- participants with at least two distinct ages: **219**
- explicit outcome/literacy/school columns in this feature table: **0**

## Best Local Longitudinal Candidates

| corpus | clinical_label | longitudinal_participants | median_ages | max_ages | median_age_span | max_age_span | task_type_sets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EllisWeismer | TD | 66 | 3.0 | 4 | 24.0 | 36.0 | conversation,interview,unknown; conversation,unknown; interview,unknown; unknown |
| EllisWeismer | LateTalker | 53 | 3.0 | 4 | 36.0 | 36.0 | conversation,interview; conversation,interview,unknown; conversation,unknown; interview,unknown; unknown |
| Rescorla | LateTalker | 38 | 4.0 | 5 | 108.0 | 120.0 | unknown |
| Rescorla | TD | 21 | 3.0 | 5 | 72.0 | 120.0 | unknown |
| Feldman | DLD_SLI | 17 | 4.0 | 6 | 25.733333333333334 | 50.96666666666667 | narrative; narrative,play_parent_child; play_parent_child |
| Ambrose | TD | 16 | 3.0 | 4 | 14.0 | 18.0 | unknown |
| UCSD |  | 15 | 1.0 | 1 | 0.0 | 0.0 | unknown |
| Ambrose | HL | 11 | 2.0 | 3 | 9.0 | 14.0 | unknown |
| Feldman | TD | 9 | 3.0 | 3 | 12.0 | 45.1 | narrative |
| Conti | TD | 8 | 2.0 | 7 | 6.4833333333333325 | 34.0 | unknown |
| Conti | DLD_SLI | 8 | 2.0 | 7 | 0.63333333333334 | 28.5 | unknown |
| Conti |  | 5 | 1.0 | 1 | 0.0 | 0.0 | unknown |
| Conti | FamilyRisk | 4 | 1.0 | 2 | 0.0 | 2.0 | unknown |

## Corpus/Label Inventory

| corpus | clinical_label | windows | transcripts | participants | ages | min_age | max_age | task_types |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ENNI | TD | 300 | 297 | 297 | 275 | 48.4 | 119.83333333333333 | 1 |
| Feldman | DLD_SLI | 480 | 257 | 207 | 192 | 14.5 | 98.96666666666667 | 2 |
| Gillam | TD | 103 | 101 | 101 | 50 | 60.0 | 142.0 | 1 |
| Conti |  | 526 | 104 | 99 | 98 | 31.833333333333332 | 60.9 | 1 |
| Nicholas | TD | 211 | 79 | 79 | 70 | 18.466666666666665 | 55.0 | 1 |
| EllisWeismer | TD | 373 | 284 | 76 | 4 | 30.0 | 66.0 | 3 |
| ENNI | DLD_SLI | 79 | 76 | 76 | 72 | 50.13333333333333 | 117.73333333333333 | 1 |
| Hooshyar | DS | 96 | 60 | 60 | 31 | 37.0 | 119.0 | 3 |
| Feldman | TD | 133 | 73 | 58 | 42 | 15.0 | 98.66666666666667 | 2 |
| EllisWeismer | LateTalker | 300 | 251 | 55 | 4 | 30.0 | 66.0 | 3 |
| Flusberg |  | 231 | 52 | 52 | 52 | 36.5 | 99.53333333333333 | 1 |
| Rondal | DS | 132 | 41 | 41 | 10 | 39.0 | 146.0 | 1 |
| Rondal | TD | 119 | 41 | 41 | 3 | 13.0 | 26.0 | 1 |
| Rescorla | LateTalker | 335 | 142 | 38 | 6 | 36.0 | 156.0 | 1 |
| Hooshyar | TD | 45 | 37 | 37 | 0 |  |  | 3 |
| Rescorla | TD | 151 | 88 | 36 | 7 | 36.0 | 156.0 | 1 |
| UCSD |  | 65 | 55 | 35 | 35 | 47.0 | 103.0 | 1 |
| Malakoff |  | 22 | 22 | 22 | 16 | 22.633333333333333 | 25.4 | 1 |
| Conti | TD | 41 | 38 | 19 | 37 | 23.166666666666668 | 187.56666666666666 | 2 |
| Gillam | DLD_SLI | 19 | 19 | 19 | 17 | 74.0 | 127.0 | 1 |
| Ambrose | TD | 110 | 51 | 18 | 4 | 18.0 | 36.0 | 1 |
| EisenbergGuo | TD | 17 | 17 | 17 | 11 | 36.0 | 47.0 | 1 |
| Ambrose | HL | 69 | 31 | 15 | 6 | 22.0 | 36.0 | 1 |
| EisenbergGuo | DLD_SLI | 20 | 15 | 15 | 8 | 37.0 | 46.0 | 1 |
| Conti | DLD_SLI | 38 | 35 | 12 | 33 | 43.666666666666664 | 173.8 | 2 |
| Hargrove |  | 11 | 11 | 11 | 8 | 33.0 | 55.0 | 1 |
| Bliss |  | 9 | 7 | 7 | 7 | 36.0 | 140.0 | 1 |
| Feldman |  | 11 | 7 | 7 | 5 | 30.0 | 84.0 | 1 |
| Conti | FamilyRisk | 10 | 10 | 6 | 7 | 25.133333333333333 | 38.5 | 1 |
| Nicholas | HL | 9 | 4 | 4 | 4 | 36.666666666666664 | 53.5 | 1 |
| POLER |  | 2 | 2 | 2 | 2 | 87.0 | 125.0 | 1 |

## Task Proxy Inventory

| corpus | task_proxy | transcripts | participants | labels |
| --- | --- | --- | --- | --- |
| EllisWeismer | unknown | 396 | 128 | 2 |
| ENNI | narrative | 373 | 373 | 2 |
| Feldman | play_parent_child | 245 | 241 | 2 |
| Rescorla | unknown | 230 | 74 | 2 |
| Conti | unknown | 173 | 122 | 3 |
| Gillam | narrative | 120 | 120 | 2 |
| Feldman | narrative | 85 | 28 | 2 |
| Nicholas | unknown | 83 | 83 | 2 |
| Rondal | unknown | 82 | 82 | 2 |
| Ambrose | unknown | 82 | 33 | 2 |
| EllisWeismer | conversation | 74 | 74 | 2 |
| EllisWeismer | interview | 65 | 65 | 2 |
| UCSD | unknown | 55 | 35 | 0 |
| Flusberg | unknown | 52 | 52 | 0 |
| Hooshyar | unknown | 34 | 34 | 2 |
| EisenbergGuo | unknown | 32 | 32 | 2 |
| Hooshyar | play_parent_child | 32 | 32 | 2 |
| Hooshyar | narrative | 31 | 31 | 2 |
| Malakoff | unknown | 22 | 22 | 0 |
| Conti | narrative | 14 | 14 | 2 |
| Hargrove | unknown | 11 | 11 | 0 |
| Bliss | unknown | 7 | 7 | 0 |
| Feldman | unknown | 7 | 7 | 0 |
| POLER | unknown | 2 | 2 | 0 |

## Interpretation

The local Clinical-Eng data contain repeated samples, especially Rescorla and
EllisWeismer, but this feature table does not contain the outcome fields needed
for strong treatment-response or school/literacy prediction claims. Local DLD
work remains useful for mechanism, persistent-gap description, and data-needs
definition. It is not enough for the final clinical claim.

## Next Actions

1. Use Rescorla and EllisWeismer for local trajectory descriptions.
2. Keep Manchester Language Study and E-DLD access as the main outcome-linkage
   targets.
3. Do not claim DLD treatment-response prediction from local Clinical-Eng alone.
4. Pair this inventory with `outputs/structured_task_inventory/summary.md` to
   choose any natural-plus-structured child-language experiment.
