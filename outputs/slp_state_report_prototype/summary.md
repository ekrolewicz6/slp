# SLP State Report Prototype

- Reports generated: 956
- Participants/sessions with top target recommendations: 911
- Stable-WAB mover flags in reports: 121

## Plan Summary

| recommended_plan | n | mean_wab | mean_content | mean_unknown_risk | mean_recoverable | with_top_targets | stable_wab_mover_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| High-support intent clarification / AAC scaffolding | 342 | 53.037 | 0.251 | 4.295 | 5.826 | 0.974 | 0.135 |
| Event-concept expansion | 80 | 54.427 | 0.233 | 0.027 | 0.452 | 0.775 | 0.075 |
| Known-target repair plus content expansion | 52 | 59.021 | 0.295 | 0.061 | 6.427 | 0.885 | 0.135 |
| Clarification and repair support | 134 | 76.857 | 0.596 | 1.276 | 3.971 | 0.955 | 0.172 |
| Maintenance and generalization | 348 | 87.981 | 0.657 | 0.049 | 1.258 | 0.983 | 0.112 |

## Internal Checks

| check | value |
| --- | --- |
| reports_total | 956 |
| reports_with_top_targets | 911 |
| high_risk_without_clarification_plan | 0 |
| same_wab_different_plan_pairs | 50 |

## Same-WAB / Different-Plan Examples

| participant_id_a | wab_aq_a | subtype_a | recommended_plan_a | participant_id_b | wab_aq_b | subtype_b | recommended_plan_b | axis_contrast |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | UNH02a | 21.400 | Broca | High-support intent clarification / AAC scaffolding | 71.299 |
| 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | Kansas02a | 24.500 | Broca | High-support intent clarification / AAC scaffolding | 61.724 |
| 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | Kansas01a | 21.500 | Broca | Event-concept expansion | 53.416 |
| 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | 254-2 | 21.800 | Broca | Event-concept expansion | 53.408 |
| 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | 254-1 | 21.800 | Broca | Event-concept expansion | 53.391 |
| 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | 1070-6 | 22.800 | Broca | Event-concept expansion | 53.391 |
| 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | 1070-5 | 22.800 | Broca | Event-concept expansion | 53.391 |
| 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | 1070-1 | 22.800 | Broca | Event-concept expansion | 53.391 |
| 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | 1070-4 | 22.800 | Broca | Event-concept expansion | 53.391 |
| 1067-1 | 23.100 | Broca | High-support intent clarification / AAC scaffolding | 1067-3 | 23.100 | Broca | Known-target repair plus content expansion | 52.201 |
| 1106-2 | 32.400 | Broca | Known-target repair plus content expansion | UNH04a | 30.500 | Broca | High-support intent clarification / AAC scaffolding | 47.949 |
| 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | Richardson24a | 61.000 | Broca | Event-concept expansion | 40.399 |
| 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | BU02a | 63.500 | TransMotor | Event-concept expansion | 40.276 |
| 1060-1 | 63.100 | Conduction | Maintenance and generalization | 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | 40.161 |
| 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | SCALE23a | 64.500 | Conduction | Maintenance and generalization | 40.108 |
| 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | Kansas20a | 61.600 | Conduction | Maintenance and generalization | 40.055 |
| 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | Richardson09a | 61.000 | Conduction | Event-concept expansion | 39.888 |
| 1060-6 | 63.100 | Conduction | Event-concept expansion | 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | 39.598 |
| 1060-3 | 63.100 | Conduction | Maintenance and generalization | 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | 39.501 |
| 1060-5 | 63.100 | Conduction | Clarification and repair support | 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | 39.160 |
| 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | UNH08a | 61.300 | Conduction | Event-concept expansion | 39.035 |
| 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | Kansas10a | 61.400 | Conduction | Clarification and repair support | 38.989 |
| 1060-4 | 63.100 | Conduction | Maintenance and generalization | 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | 38.896 |
| 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | MSU07a | 61.400 | Broca | Event-concept expansion | 38.826 |
| 1060-2 | 63.100 | Conduction | Known-target repair plus content expansion | 1112-2 | 63.000 | Broca | High-support intent clarification / AAC scaffolding | 38.702 |

## Interpretation

This is not a validated clinical report. It is an internally auditable prototype that converts the current two-axis state model into care-planning hypotheses: content expansion, known-target repair, clarification/AAC support, or maintenance/generalization. The same-WAB/different-plan table is the key scientific value: it shows where discourse state may recommend different care despite similar standardized severity.
