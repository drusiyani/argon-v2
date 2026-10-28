# Lockbox 2 (2011-2020, never seen before), opened once on 28 Oct 2026

## The base book (B0): **FAIL**
| | Sharpe | R | Sharpe, double costs | Positive years |
|---|---|---|---|---|
| v2 book, 2011-2020 | **−1.03** | **−469R** | −2.01 | 3 of 10 (2018, 2019, 2020) |
| same, costs scaled to price level (information only) | −0.30 | −128R | | |

By strategy (net of costs): QuantLab **−446R** (−62R even before costs; costs were 0.16R a trade because NQ was ~2,000-4,000),
noise band −18R (gross +40R), ATR band −8R (gross +29R), expiry +2R (gross +16R).

**What it means:** the opening-candle momentum edge (QuantLab) did not exist in 2011-2017, even before costs. The other three
had small edges that costs ate. Everything only works from about 2018, when Nasdaq volatility, price level and options and
leveraged-ETF flows changed. So either these edges are a recent market feature, or they were partly fitted to 2021-2026. The
backtest profit on 2021-2026 is very likely an overstatement of what to expect.

**As pre-registered, nothing changes because of this:** the book still goes live on 1 Jan 2027 and this result is published.

## Survivors from round 2
| | 2011-2020 Sharpe | vs base | double costs | Verdict |
|---|---|---|---|---|
| R01 risk parity, 12 months | −0.82 | +0.21 | −1.56 (base −2.01) | **KEEP** |
| R03 risk parity, capped 0.5-2 | −0.93 | +0.10 | −1.80 | **KEEP** |

Both pass the pre-registered rule (better than the base at normal and double costs), but only because they shrink
QuantLab, the strategy that failed. They are less bad, not good. R01 was better in both windows.

## Disclosures
- A crash-check before the full run showed pass/fail for 10 of the 17 adjustments (all fail). The list was already committed.
- Two code bugs were found and fixed before this run (FOMC calendar missing 2010-2020; roll days never skipped). Both are in PREREGISTRATION.md.
