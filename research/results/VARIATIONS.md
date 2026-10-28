# Variation comparison (in-sample, post-lockbox)

Rule fixed before running: highest worst-era Sharpe, double-cost Sharpe at least the base, ties to the simpler one.

| | 2011-17 | 2018-20 | 2021-26 | worst era | all eras | all, 2x costs | total R |
|---|---|---|---|---|---|---|---|
| V0 base (4 strategies) | -2.16 | 0.96 | 1.16 | -2.16 | -0.21 | -0.88 | -161.1 |
| V1 drop QuantLab | -0.64 | 0.92 | 1.02 | -0.64 | 0.27 | -0.03 | 93.6 |
| V2 base + risk parity | -1.6 | 0.86 | 1.28 | -1.6 | -0.07 | -0.61 | -34.2 |
| V3 drop QuantLab + risk parity | -0.65 | 0.73 | 1.11 | -0.65 | 0.24 | -0.06 | 71.2 |
| V4 base + cost rule | -0.58 | 0.92 | 1.18 | -0.58 | 0.59 | 0.26 | 348.8 |
| V5 drop QuantLab + cost rule **(pick)** | -0.55 | 0.92 | 1.02 | -0.55 | 0.33 | 0.03 | 111.8 |
| V6 drop QuantLab + cost rule + risk parity | -0.54 | 0.71 | 1.11 | -0.54 | 0.3 | 0.01 | 87.9 |
| V7 noise band + ATR band only | -0.67 | 0.92 | 0.89 | -0.67 | 0.21 | -0.06 | 70.6 |
