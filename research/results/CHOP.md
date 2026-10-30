# The chop strategy, "Fade the stretch": result

Rules and pass marks were committed before this ran. Verdict: **FAIL**

| | 2011–2017 | 2018–2026 |
|---|---|---|
| Chop result | -49.8R | -63.2R |
| Book Sharpe without it | -0.578 | 1.096 |
| Book Sharpe with it | -0.899 | 0.965 |
| Correlation with the book | -0.12 | -0.26 |

Trades: 914, win rate 42.2%, before costs -88.5R, at double costs -141.8R.

| Nearby setting | Total R |
|---|---|
| base | -112.9R |
| band_lo | -125.9R |
| band_hi | -69.4R |
| calm_lo | -71.8R |
| calm_hi | -146.6R |

## Checks

- 1 positive in both eras: no
- 2 lifts the book by +0.05 in both eras, correlation < 0.3: no
- 3 positive at double costs: no
- 4 every nearby setting positive: no
