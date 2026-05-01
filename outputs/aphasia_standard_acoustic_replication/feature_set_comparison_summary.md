# Custom vs Standard Acoustic Feature Comparison

- eGeMAPS roots from balanced84 manifest: 84
- Custom acoustic roots on the same manifest: 83
- Common roots: 83
- Balanced common roots: 80
- eGeMAPS features: 92
- Custom acoustic features: 34
- CV: repeated stratified 4-fold, repeats=20

## Coverage

| feature_set | roots | subtype_counts |
| --- | --- | --- |
| egemaps | 84 | {'Anomic': 21, 'Broca': 21, 'Conduction': 21, 'Wernicke': 21} |
| custom | 83 | {'Anomic': 21, 'Broca': 21, 'Conduction': 21, 'Wernicke': 20} |
| common | 83 | {'Anomic': 21, 'Broca': 21, 'Conduction': 21, 'Wernicke': 20} |
| balanced_common | 80 | {'Anomic': 20, 'Broca': 20, 'Conduction': 20, 'Wernicke': 20} |

## Model Summary

| subset | model | mean_balanced_accuracy | ba_ci_low | ba_ci_high | mean_macro_f1 | f1_ci_low | f1_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| balanced_common80 | custom_plus_wab | 0.563 | 0.542 | 0.586 | 0.546 | 0.524 | 0.567 |
| balanced_common80 | wab_only | 0.542 | 0.524 | 0.561 | 0.520 | 0.501 | 0.540 |
| balanced_common80 | custom_voice_pitch_intensity | 0.496 | 0.476 | 0.516 | 0.484 | 0.462 | 0.506 |
| balanced_common80 | custom_only | 0.484 | 0.466 | 0.502 | 0.466 | 0.447 | 0.486 |
| balanced_common80 | custom_no_token_counts | 0.472 | 0.451 | 0.493 | 0.459 | 0.438 | 0.480 |
| balanced_common80 | all_acoustic_plus_wab | 0.466 | 0.446 | 0.486 | 0.452 | 0.430 | 0.474 |
| balanced_common80 | custom_token_rate_count | 0.480 | 0.461 | 0.500 | 0.452 | 0.431 | 0.472 |
| balanced_common80 | egemaps_plus_custom | 0.441 | 0.421 | 0.463 | 0.428 | 0.405 | 0.448 |
| balanced_common80 | egemaps_plus_wab | 0.436 | 0.415 | 0.456 | 0.418 | 0.398 | 0.439 |
| balanced_common80 | egemaps_only | 0.393 | 0.369 | 0.416 | 0.378 | 0.355 | 0.402 |
| balanced_common80 | shuffled_labels | 0.282 | 0.263 | 0.300 | 0.265 | 0.246 | 0.283 |
| balanced_common80 | random_features | 0.203 | 0.185 | 0.222 | 0.194 | 0.177 | 0.214 |
| balanced_common80 | majority | 0.250 | 0.250 | 0.250 | 0.100 | 0.100 | 0.100 |
| common83 | custom_plus_wab | 0.526 | 0.505 | 0.545 | 0.510 | 0.488 | 0.529 |
| common83 | wab_only | 0.530 | 0.514 | 0.548 | 0.507 | 0.490 | 0.525 |
| common83 | custom_voice_pitch_intensity | 0.466 | 0.445 | 0.488 | 0.451 | 0.429 | 0.474 |
| common83 | custom_only | 0.452 | 0.432 | 0.472 | 0.435 | 0.417 | 0.454 |
| common83 | custom_no_token_counts | 0.442 | 0.419 | 0.464 | 0.428 | 0.407 | 0.451 |
| common83 | all_acoustic_plus_wab | 0.433 | 0.414 | 0.452 | 0.422 | 0.402 | 0.440 |
| common83 | custom_token_rate_count | 0.458 | 0.440 | 0.476 | 0.420 | 0.401 | 0.439 |
| common83 | egemaps_plus_wab | 0.435 | 0.417 | 0.453 | 0.419 | 0.399 | 0.438 |
| common83 | egemaps_plus_custom | 0.423 | 0.403 | 0.444 | 0.413 | 0.393 | 0.432 |
| common83 | egemaps_only | 0.397 | 0.377 | 0.418 | 0.385 | 0.363 | 0.406 |
| common83 | shuffled_labels | 0.207 | 0.188 | 0.226 | 0.193 | 0.174 | 0.212 |
| common83 | random_features | 0.189 | 0.174 | 0.204 | 0.177 | 0.161 | 0.192 |
| common83 | majority | 0.250 | 0.250 | 0.250 | 0.097 | 0.097 | 0.098 |

## Interpretation

This comparison uses only patient roots present in both acoustic feature sets. The balanced subset is the cleaner headline check because the custom extraction is missing one Wernicke root from the eGeMAPS balanced84 manifest.
