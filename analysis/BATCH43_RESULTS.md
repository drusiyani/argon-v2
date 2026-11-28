# Batch 43 results: month-end stock-bond rebalancing trade on NQ

Rules: `analysis/BATCH43_PREREG.md` (Claude's own idea, 28 Nov 2026). Code: `analysis/batch43.py`. Data:
`analysis/batch43_lockbox2010.json`, `analysis/batch43_databento.json`. First run, no reruns.

## Verdict: REJECTED

It helped a lot in 2011-2020 and hurt in 2022-2026. The bar needs both eras.

| | 2011-2020 (lockbox2010) | 2022-2026 (databento) |
|---|---|---|
| Book alone: Sharpe / CAGR / worst drop | 0.945 / 19.1% / 23.4% | 1.288 / 42.4% / 20.5% |
| Book + trade: Sharpe / CAGR / worst drop | 1.114 / 25.2% / 24.5% | **1.141** / 38.5% / 24.1% |
| Sharpe gain | +0.169 | **-0.147** |
| Trades / win rate | 114 / 54% | 58 / 50% |
| Avg return per trade after costs (1x notional) | +0.45% | -0.18% |
| Own Sharpe | 0.59 | -0.20 |
| Short side (stocks beat bonds): n / win / avg | 76 / 46% / -0.00% | 35 / 49% / -0.53% |
| Long side (bonds beat stocks): n / win / avg | 38 / 71% / +1.34% | 23 / 52% / +0.36% |
| Correlation with the book | -0.03 | +0.02 |
| Luck check: share of draws with gain <= 0 | 0.09 | 0.92 |

## Plain English
The idea was to trade against month-end pension rebalancing: short Nasdaq in the last five sessions when stocks beat
bonds that month, long when bonds won. In 2011-2020 all of the edge came from the long side (buying after a bad month
for stocks); the short side, the one the rebalancing story is really about, earned nothing. In 2022-2026 the short
side lost and the long side shrank, so the trade cut the book's Sharpe by 0.15. In the first era it was mostly a
"buy the dip near month end" trade, not a rebalancing trade, and that did not carry over.

Trial count after this batch: about 332.
