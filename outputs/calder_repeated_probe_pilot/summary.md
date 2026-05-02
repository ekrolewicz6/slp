# Calder Repeated-Probe Treatment-Response Pilot

Source: Calder, S. D., Claessen, M., Ebbels, S., & Leitao, S. (2020). Explicit grammar intervention in young school-aged children with Developmental Language Disorder: An efficacy study using single-case experimental design. *Language, Speech, and Hearing Services in Schools*, 51(2), 298-316. https://doi.org/10.1044/2019_LSHSS-19-00060

## Question

This is the closest local public example of the treatment-response data structure Brian described: repeated probes, a specific target, dose, and extension/control measures. The project question is whether repeated probe curves can expose target-specific response rather than only pre/post group change.

## Extraction

- Parsed 10 supplemental raw-score PDF tables into 1638 probe rows; 1494 rows have usable numerator/denominator scores.
- Participants: 9 children with DLD.
- Row-level extracted scores are written only to gitignored `data/parsed/calder_repeated_probes/`; committed outputs are aggregate summaries and derived response metrics.

## Main Results

- Trained expressive past-tense probes improved across treatment sessions: between-session late-minus-early mean 0.284 (95% bootstrap CI 0.176 to 0.398); 9/9 children improved.
- Expressive untrained past-tense maintenance gain averaged 0.533 from baseline (95% CI 0.386 to 0.680); control possessive-s maintenance gain averaged 0.256 (95% CI 0.087 to 0.445).
- Expressive target-specificity at maintenance, untrained past tense minus control, averaged 0.277 (95% CI 0.195 to 0.357; Wilcoxon p=0.0039).
- Grammaticality-judgment maintenance gains were smaller: untrained past tense 0.088 vs control 0.073. This supports separating production and judgment/comprehension-like probes rather than assuming one treatment response axis.

## Interpretation for Our Program

- This is the correct data shape for treatment learning: target, contrast target, dose/session order, repeated probes, and maintenance.
- A clinical model should learn curves and target specificity, not just diagnose DLD or predict a single post-test score.
- The small single-case design is valuable mechanistically but insufficient for broad treatment allocation. It should be used as a schema template and a calibration example for future prospective collection.
- The strongest next data need is not another classifier; it is paired natural-speech/structured-probe/treatment-dose data with enough children and targets to model heterogeneous response.

## Output Files

- `parse_audit.csv`: extracted supplemental table inventory.
- `aggregate_phase_metrics.csv`: baseline-to-intervention and baseline-to-maintenance response summaries for untrained, extension, and control probes.
- `aggregate_trained_metrics.csv`: early-to-late trained-probe change during intervention.
- `target_specificity_metrics.csv`: paired untrained/extension minus control contrasts.
- `summary.md`: this interpretation.

## Limits

- Scores were extracted from PDF supplemental tables, not original CSVs; the parser validates row widths but should be manually checked before publication.
- We intentionally do not claim causal effects beyond the original single-case design.
- There are no natural speech samples here, so this cannot validate our full natural-plus-structured battery.
