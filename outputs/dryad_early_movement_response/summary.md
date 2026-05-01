# Dryad Early-Movement Response Pilot

This experiment asks whether early language-sample movement predicts later vocabulary/grammar outcomes in the randomized EMT-SF DLD dataset.

Dataset citation: Grauzer, Jeffrey; Roberts, Megan; Jones, Maranda (2026), *Maximizing outcomes for preschoolers with developmental language disorders* [Dataset], Dryad, https://doi.org/10.5061/dryad.sj3tx96g9. Trial registry context: ClinicalTrials.gov `NCT03782493` lists Megan Y. Roberts, Pamela Hadley, and Ann Kaiser as principal investigators.

## Does Treatment Move The Early Language-Sample State?

| movement_window | n | coef | ci_lo | ci_hi | p | model_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| T33 | 85 | 0.371 | -0.027 | 0.768 | 0.068 | 0.058 |
| T36 | 85 | 0.301 | -0.093 | 0.696 | 0.132 | 0.078 |
| T39 | 83 | -0.195 | -0.605 | 0.215 | 0.347 | 0.020 |

## Does Early Movement Predict Later Outcomes?

| outcome | movement_window | n | coef | ci_lo | ci_hi | p | r2_gain_vs_baseline_tx | tx_coef_before_movement | tx_coef_after_movement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T49 grammar composite | T33 | 89 | 0.401 | 0.243 | 0.559 | 0.000 | 0.176 | 0.432 | 0.282 |
| T49 grammar composite | T39 | 89 | 0.378 | 0.225 | 0.530 | 0.000 | 0.169 | 0.432 | 0.496 |
| T42 grammar composite | T39 | 90 | 0.346 | 0.201 | 0.491 | 0.000 | 0.159 | 0.365 | 0.453 |
| T42 grammar composite | T33 | 90 | 0.325 | 0.174 | 0.477 | 0.000 | 0.134 | 0.365 | 0.259 |
| T49 grammar composite | T36 | 89 | 0.318 | 0.153 | 0.483 | 0.000 | 0.113 | 0.432 | 0.322 |
| T42 grammar composite | T36 | 90 | 0.272 | 0.118 | 0.426 | 0.001 | 0.096 | 0.365 | 0.286 |
| T49 vocabulary composite | T33 | 86 | 0.295 | 0.126 | 0.465 | 0.001 | 0.103 | 0.382 | 0.289 |
| T49 vocabulary composite | T39 | 86 | 0.260 | 0.097 | 0.423 | 0.002 | 0.088 | 0.382 | 0.448 |
| T49 vocabulary composite | T36 | 86 | 0.258 | 0.093 | 0.424 | 0.003 | 0.084 | 0.382 | 0.310 |

## Interpretation

The strongest movement predictor is `T33` movement for `T49 grammar composite`: coefficient 0.401, p=0.000, with R2 gain 0.176 beyond baseline state and treatment group.

The important scientific result is mixed. Early language-sample movement is sometimes predictive of later grammar/vocabulary outcomes, but treatment assignment does not strongly move the aggregate early language-sample state in these simple models. That means this dataset supports the early-movement measurement thesis more than it supports a treatment-mediation claim.

For the broader project, this is still valuable: it is the first randomized DLD dataset here where repeated state movement can be related to later standardized outcomes. The next-generation dataset should keep this structure but add raw transcripts/audio, session dose, treatment targets, and repeated clinician goals.
