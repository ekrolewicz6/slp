# Reconstruction Metric Fragility

- Items: 400
- Candidate outputs scored: 2400
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- High-cosine unsafe threshold: 0.85
- High-ROUGE unsafe threshold: 0.75

## Cosine-Threshold Summary

| candidate_family | n | mean_cosine | mean_rouge_l | unsafe_rate | high_similarity_unsafe_rate | mean_concept_recovery | mean_overreach | mean_observed_loss | mean_unknown_added | mean_negation_flip |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| negation_flip | 400 | 0.990 | 0.987 | 1.000 | 1.000 | 0.412 | 0.028 | 0.065 | 0.438 | 1.000 |
| added_plausible_concept | 400 | 0.987 | 0.992 | 0.865 | 0.858 | 0.412 | 0.782 | 0.000 | 0.718 | 0.015 |
| role_swap | 400 | 0.976 | 0.985 | 0.362 | 0.355 | 0.401 | 0.048 | 0.140 | 0.452 | 0.015 |
| content_omission | 400 | 0.984 | 0.992 | 0.262 | 0.262 | 0.410 | 0.000 | 0.065 | 0.438 | 0.018 |
| oracle_reference | 400 | 1.000 | 1.000 | 0.202 | 0.202 | 0.412 | 0.000 | 0.000 | 0.438 | 0.015 |
| preserve_raw | 400 | 0.977 | 0.957 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## ROUGE-Threshold Summary

| candidate_family | n | mean_cosine | mean_rouge_l | unsafe_rate | high_similarity_unsafe_rate | mean_concept_recovery | mean_overreach | mean_observed_loss | mean_unknown_added | mean_negation_flip |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| negation_flip | 400 | 0.990 | 0.987 | 1.000 | 1.000 | 0.412 | 0.028 | 0.065 | 0.438 | 1.000 |
| added_plausible_concept | 400 | 0.987 | 0.992 | 0.865 | 0.865 | 0.412 | 0.782 | 0.000 | 0.718 | 0.015 |
| role_swap | 400 | 0.976 | 0.985 | 0.362 | 0.362 | 0.401 | 0.048 | 0.140 | 0.452 | 0.015 |
| content_omission | 400 | 0.984 | 0.992 | 0.262 | 0.262 | 0.410 | 0.000 | 0.065 | 0.438 | 0.018 |
| oracle_reference | 400 | 1.000 | 1.000 | 0.202 | 0.202 | 0.412 | 0.000 | 0.000 | 0.438 | 0.015 |
| preserve_raw | 400 | 0.977 | 0.957 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Similarity vs Safety Correlations

| similarity_metric | safety_metric | r |
| --- | --- | --- |
| embedding_cosine_to_oracle | concept_recovery_rate | 0.139 |
| embedding_cosine_to_oracle | concept_overreach_count | -0.048 |
| embedding_cosine_to_oracle | observed_concept_loss_count | -0.174 |
| embedding_cosine_to_oracle | unknown_intent_added_concept_count | 0.107 |
| embedding_cosine_to_oracle | negation_flip_flag | 0.068 |
| rouge_l_f1_to_oracle | concept_recovery_rate | 0.217 |
| rouge_l_f1_to_oracle | concept_overreach_count | 0.075 |
| rouge_l_f1_to_oracle | observed_concept_loss_count | -0.035 |
| rouge_l_f1_to_oracle | unknown_intent_added_concept_count | 0.148 |
| rouge_l_f1_to_oracle | negation_flip_flag | 0.040 |

## Interpretation

High semantic-similarity metrics are not sufficient evidence of clinical safety. This benchmark deliberately creates small semantic perturbations that can keep embeddings or ROUGE close to the oracle while changing negation, roles, omitted observed concepts, or added event concepts. A reconstruction system should therefore be evaluated with explicit content, overreach, negation, and unknown-intent safety metrics rather than cosine similarity alone.
