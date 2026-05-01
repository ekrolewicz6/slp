# openSMILE Smoke Test

- Audio path: `data/audio/cmu01a_test.wav`
- Feature set: `egemaps`
- Feature level: `functionals`
- Rows: 1
- Columns: 88
- Duration: 1309.68s
- Sample rate: 16000 Hz
- Channels: 1

## Missingness

| feature | missing_fraction |
|---|---:|
| `F0semitoneFrom27.5Hz_sma3nz_amean` | 0.000 |
| `F0semitoneFrom27.5Hz_sma3nz_stddevNorm` | 0.000 |
| `slopeV500-1500_sma3nz_amean` | 0.000 |
| `slopeV0-500_sma3nz_stddevNorm` | 0.000 |
| `slopeV0-500_sma3nz_amean` | 0.000 |
| `hammarbergIndexV_sma3nz_stddevNorm` | 0.000 |
| `hammarbergIndexV_sma3nz_amean` | 0.000 |
| `alphaRatioV_sma3nz_stddevNorm` | 0.000 |
| `alphaRatioV_sma3nz_amean` | 0.000 |
| `F3amplitudeLogRelF0_sma3nz_stddevNorm` | 0.000 |
| `F3amplitudeLogRelF0_sma3nz_amean` | 0.000 |
| `F3bandwidth_sma3nz_stddevNorm` | 0.000 |
| `F3bandwidth_sma3nz_amean` | 0.000 |
| `F3frequency_sma3nz_stddevNorm` | 0.000 |
| `F3frequency_sma3nz_amean` | 0.000 |

## Largest Absolute Feature Values

| feature | value |
|---|---:|
| `F3frequency_sma3nz_amean` | 2764.09 |
| `F2frequency_sma3nz_amean` | 1741.33 |
| `F1bandwidth_sma3nz_amean` | 1384.68 |
| `F2bandwidth_sma3nz_amean` | 1070.85 |
| `F3bandwidth_sma3nz_amean` | 1010.44 |
| `F1frequency_sma3nz_amean` | 718.036 |
| `F0semitoneFrom27.5Hz_sma3nz_stddevRisingSlope` | 442.416 |
| `F0semitoneFrom27.5Hz_sma3nz_meanRisingSlope` | 298.144 |
| `F0semitoneFrom27.5Hz_sma3nz_stddevFallingSlope` | 231.169 |
| `F1amplitudeLogRelF0_sma3nz_amean` | 171.245 |
| `F3amplitudeLogRelF0_sma3nz_amean` | 169.636 |
| `F2amplitudeLogRelF0_sma3nz_amean` | 169.06 |
| `F0semitoneFrom27.5Hz_sma3nz_meanFallingSlope` | 151.665 |
| `F0semitoneFrom27.5Hz_sma3nz_percentile80.0` | 36.633 |
| `F0semitoneFrom27.5Hz_sma3nz_percentile50.0` | 33.2784 |

## Interpretation

This confirms that the local environment can compute standard openSMILE features. The next scientific step is not to treat all columns as clinically meaningful, but to run fold-clean ablations over feature families such as prosody, voice quality, spectral shape, and timing.
