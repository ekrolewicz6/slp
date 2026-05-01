# DLD Conflict Review Packet Summary

- Review cases packaged: 15
- Selection rule: all `highest_clinical_fairness_review` cases plus the strongest `highest_scientific_review` cases.
- Packet: `outputs/dld_conflict_review_packet/review_packet.md`

## Priority Mix

| review_priority | n |
| --- | --- |
| highest_scientific_review | 12 |
| highest_clinical_fairness_review | 3 |

## Corpus Mix

| corpus | review_priority | n |
| --- | --- | --- |
| ENNI | highest_scientific_review | 6 |
| Feldman | highest_scientific_review | 5 |
| ENNI | highest_clinical_fairness_review | 1 |
| EisenbergGuo | highest_clinical_fairness_review | 1 |
| EisenbergGuo | highest_scientific_review | 1 |
| Feldman | highest_clinical_fairness_review | 1 |

## Task Mix

| task_bucket | n |
| --- | --- |
| narrative_story | 7 |
| natural_conversation | 6 |
| unknown | 2 |

## Case Index

| case_id | compact_participant_id | corpus | screen_label | age_min | task_bucket | conflict_archetype | review_priority | full_language_no_age | corpus_age | mlu_age |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DLD-CONFLICT-001 | TD/452 | ENNI | TD | 48.400 | narrative_story | TD_label_state_risk_language_driven | highest_clinical_fairness_review | 0.923 | 0.139 | 0.690 |
| DLD-CONFLICT-002 | TD/pgas21 | Feldman | TD | 21.000 | natural_conversation | TD_label_state_risk_language_driven | highest_clinical_fairness_review | 0.865 | 0.618 | 0.591 |
| DLD-CONFLICT-003 | TD/072ag | EisenbergGuo | TD | 39.000 | unknown | TD_label_state_risk_language_driven | highest_clinical_fairness_review | 0.818 | 0.421 | 0.301 |
| DLD-CONFLICT-004 | DLD_SLI/gla15 | Feldman | DLD_SLI | 14.933 | natural_conversation | language_risk_without_corpus_with_MLU | highest_scientific_review | 0.928 | 0.492 | 0.550 |
| DLD-CONFLICT-005 | DLD_SLI/bea15 | Feldman | DLD_SLI | 14.500 | natural_conversation | language_risk_without_corpus_not_MLU_only | highest_scientific_review | 0.914 | 0.492 | 0.376 |
| DLD-CONFLICT-006 | DLD_SLI/pop15 | Feldman | DLD_SLI | 15.000 | natural_conversation | language_risk_without_corpus_not_MLU_only | highest_scientific_review | 0.907 | 0.492 | 0.382 |
| DLD-CONFLICT-007 | DLD_SLI/fei15 | Feldman | DLD_SLI | 15.233 | natural_conversation | language_risk_without_corpus_not_MLU_only | highest_scientific_review | 0.877 | 0.492 | 0.376 |
| DLD-CONFLICT-008 | DLD_SLI/477 | ENNI | DLD_SLI | 56.100 | narrative_story | language_risk_without_corpus_with_MLU | highest_scientific_review | 0.856 | 0.120 | 0.638 |
| DLD-CONFLICT-009 | DLD_SLI/476 | ENNI | DLD_SLI | 57.233 | narrative_story | language_risk_without_corpus_not_MLU_only | highest_scientific_review | 0.847 | 0.190 | 0.220 |
| DLD-CONFLICT-010 | DLD_SLI/444 | ENNI | DLD_SLI | 50.133 | narrative_story | language_risk_without_corpus_not_MLU_only | highest_scientific_review | 0.840 | 0.139 | 0.466 |
| DLD-CONFLICT-011 | TD/077eg | EisenbergGuo | TD | 39.000 | unknown | language_risk_without_corpus_with_MLU | highest_scientific_review | 0.822 | 0.427 | 0.501 |
| DLD-CONFLICT-012 | DLD_SLI/427 | ENNI | DLD_SLI | 55.533 | narrative_story | language_risk_without_corpus_with_MLU | highest_scientific_review | 0.779 | 0.120 | 0.701 |
| DLD-CONFLICT-013 | DLD_SLI/gig21 | Feldman | DLD_SLI | 21.000 | natural_conversation | language_risk_without_corpus_not_MLU_only | highest_scientific_review | 0.777 | 0.484 | 0.467 |
| DLD-CONFLICT-014 | TD/447 | ENNI | TD | 50.167 | narrative_story | language_risk_without_corpus_not_MLU_only | highest_scientific_review | 0.774 | 0.139 | 0.226 |
| DLD-CONFLICT-015 | DLD_SLI/413 | ENNI | DLD_SLI | 58.867 | narrative_story | language_risk_without_corpus_with_MLU | highest_scientific_review | 0.761 | 0.191 | 0.578 |

## Interpretation

These 15 cases are the best current bridge from model result to field question. The clinical-fairness cases ask whether TD-labeled children can look language-risky after removing corpus/age shortcuts. The scientific cases ask whether language-only risk is capturing a non-MLU developmental signal or merely exposing label/task/context noise. The next step is expert review of the underlying transcripts and metadata, ideally paired with a structured sentence/nonword repetition probe in future data.
