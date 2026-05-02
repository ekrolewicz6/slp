# Fiveash Sentence-Repetition Structured-Task Pilot

Source: Fiveash, A., Ladanyi, E., Camici, J., Chidiac, K., Bush, C. T., Canette, L.-H., Bedoin, N., Gordon, R. L., & Tillmann, B. (2023). Regular rhythmic primes improve sentence repetition in children with developmental language disorder. *npj Science of Learning*, 8, 23. https://doi.org/10.1038/s41539-023-00170-1

## Question

Brian's advice points toward pairing natural speech with tight, automatable structured tasks. This pilot asks whether the Fiveash et al. sentence-repetition task behaves like a useful state probe: does it separate DLD from TD, and does the regular rhythm manipulation add clinically interpretable information beyond overall task level?

## Data

- Participants: 33 children (18 TD, 15 DLD).
- Trial rows: 1188 ({'Regular': 594, 'Irregular': 594}).
- Outcome: ordinal grammar score coded 0, 0.5, or 1; this pilot uses transparent numeric approximations plus subject-level resampling, not the paper's ordinal mixed-effects model.

## Main Results

- Regular rhythm improved sentence repetition by 0.043 grammar-score points on the 0-1 scale (95% bootstrap CI 0.008 to 0.077; sign-flip p=0.0246).
- DLD children scored lower overall by -0.334 points relative to TD (DLD minus TD; 95% bootstrap CI -0.435 to -0.236; permutation p=0.0002).
- The DLD-vs-TD difference in rhythm benefit was 0.047 points (95% bootstrap CI -0.023 to 0.115; permutation p=0.2066). This is the key project-specific caution: rhythm helps, but the response size is not clearly DLD-specific in this sample.
- Trial-level OLS approximation: regular coefficient 0.022, DLD coefficient -0.355, regular x DLD coefficient 0.047; CIs are in `trial_model_coefficients.csv`.
- Clinical-background variables separate the two groups perfectly here (AUC 1.000), which is expected because they are close to the labeling construct and should be treated only as an upper bound.
- Best task-only leave-one-child-out DLD-vs-TD classifier: `sentence_repetition_level` with AUC 0.944, balanced accuracy 0.939, and DLD F1 0.933.
- Rhythm-response-only classification is weaker (AUC 0.652, balanced accuracy 0.628), reinforcing that the immediate rhythm benefit is not enough by itself to define a clinical subtype or treatment plan.

## Interpretation for Our Program

- Sentence repetition is a strong candidate for the tight-task half of the natural-plus-structured assessment battery.
- The rhythm manipulation is scientifically interesting as a causal perturbation of grammar processing, but the public sample does not yet show that rhythm response alone can assign treatment or predict who benefits most.
- The next version of our battery should treat sentence repetition level as a robust state measure, and rhythm response as an experimental input-sensitivity measure that needs replication in longitudinal/treatment data.
- This result aligns with Brian's point that a rich clinical output should not collapse to one score: the same structured task can expose grammar level, rhythm sensitivity, age/reading covariates, and group-risk separation.

## Output Files

- `group_prime_summary.csv`: participant-level mean grammar scores by group and prime.
- `senttype_prime_summary.csv`: score patterns by group, prime, and sentence type.
- `bootstrap_effects.csv`: bootstrap and permutation tests for rhythm and group contrasts.
- `trial_model_coefficients.csv`: transparent trial-level OLS approximation with participant-cluster bootstrap CIs.
- `classification_metrics.csv`: leave-one-child-out DLD-vs-TD classification from structured-task feature sets.

## Limits

- This is a secondary analysis of a 33-child experimental dataset, not a clinical validation study.
- The public file has no natural speech sample paired with the structured task, so it cannot answer the combined-battery question directly.
- Treatment-response claims require repeated outcomes after actual intervention; this dataset only tests an immediate rhythmic prime.
