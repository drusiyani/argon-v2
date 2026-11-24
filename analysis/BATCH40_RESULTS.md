# Batch 40 results (24 Nov 2026): TikTok strategy sweep

Rules and pass test: `BATCH40_PREREG.md`. Numbers: `batch40_databento.json` (Jul 2021-Dec 2024) and `batch40_lockbox2010.json`
(2011-2020). 2025 onward not opened. R = net points / stop distance, after costs. "Beat" = share of 1,000 random runs the rule beat.

**Verdict: no rule passes** (pass = positive in both eras, beats >= 99% of random in both, both halves positive). All rejected.

| Rule | Mkt | 2021-24 mean R / beat | 2011-20 mean R / beat |
|---|---|---|---|
| Candle momentum (12 EMA) | NQ | +0.030 / 66.7% | +0.034 / 100% |
| First-candle direction | NQ | +0.006 / 36.2% | +0.036 / 100% |
| Larry Williams range break | NQ | +0.136 / 99.6% | +0.025 / 94.4% |
| EMA 20/50 cross | NQ | +0.121 / 99.0% | -0.036 / 72.4% |
| Bollinger squeeze | NQ | +0.091 / 98.9% | -0.073 / 32.0% |
| MACD cross | NQ | +0.043 / 92.3% | -0.039 / 88.5% |
| SuperTrend flip | NQ | +0.082 / 91.8% | -0.067 / 39.1% |
| Fair value gap | NQ | -0.049 / 76.6% | -0.197 / 73.2% |

ES is the same story or worse (full table in the JSON). Always-long at 09:35: +0.04R (2021-24), -0.01R (2011-20) on NQ.
- The 09:35 rules beat the coin flip in 2011-20 mostly because a random direction pays the costs and loses; the edge itself is 0.03R a trade, far too small to matter.
- Larry Williams, EMA cross and Bollinger squeeze looked good on NQ in 2021-24 only and did not hold in 2011-20, so they are rejected as period luck.
- Fair value gaps lose after costs in every era and market, and are no better than random entries.
- Fed-day drift: +0.50% (n=32, beat 96.6% of random) in 2021-24 but +0.16% (n=85, beat 72.7%) in 2011-20. Not significant.
- Power of three: price dips below the midnight price on 98-99% of days, and the day closes up 53-55% of the time whether or not it dipped. No information.
Nothing here changes the Argon book. 22 trials added to the count.
