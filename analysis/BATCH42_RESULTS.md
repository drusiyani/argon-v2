# Batch 42 results: trend sleeve, gold (GC) + 10-year Treasury (ZN), monthly momentum

Rules: `analysis/BATCH42_PREREG.md` (issue #2). Code: `analysis/batch42.py`. Data: `analysis/batch42_lockbox2010.json`,
`analysis/batch42_databento.json`. Run: https://github.com/drusiyani/argon-v2/actions/runs/46133185539 (first run, no reruns).

## Verdict: PASS (weak, could be luck) — for Dru to decide

The full book's Sharpe rose in both eras after costs, so the fixed bar is met. But the luck check is weak: in about a
quarter of the bootstrap draws the gain was zero or less, in both eras. Nothing in the live book has changed.

| | 2011-2020 (lockbox2010) | 2022-2026 (databento) |
|---|---|---|
| Book alone (core + four rules): Sharpe / CAGR / worst drop | 0.945 / 19.1% / 23.4% | 1.288 / 42.4% / 20.5% |
| Book + sleeve: Sharpe / CAGR / worst drop | **1.034** / 22.4% / 23.4% | **1.376** / 47.9% / 19.1% |
| Sharpe gain | +0.089 | +0.088 |
| Sleeve's own Sharpe (GC / ZN alone) | 0.35 (0.14 / 0.39) | 0.51 (0.42 / 0.30) |
| Sleeve volatility a year | 8.6% | 7.9% |
| Correlation with the core / the book | -0.11 / -0.08 | -0.06 / -0.00 |
| Luck check: share of draws with gain <= 0 | 0.27 | 0.25 |
| Luck check: 5th / 50th percentile gain | -0.15 / +0.08 | -0.12 / +0.08 |

- Trades: one rebalance per market per month end, 184 month ends from Jun 2011 to Sep 2026 (each a small resize; the
  side flips far less often). Avg R does not apply: the sleeve is a sized holding, not R-based trades.
- 2022 (the year it was meant for): sleeve +8.5%, book alone -5.1%, book with sleeve +3.6%.
- Sleeve by year: 2011 +13.3, 2012 -1.9, 2013 +12.2, 2014 -1.6, 2015 +7.0, 2016 -9.7, 2017 +0.3, 2018 -8.3,
  2019 +1.9, 2020 +15.2, 2022 +8.5, 2023 -7.3, 2024 +6.3, 2025 +8.6, 2026 +3.3 (to end Oct).
- Info only: whole contracts on $100k (MGC + ZN): book Sharpe 1.074 / 1.399. Roll cost 2 ticks instead of 1:
  1.031 / 1.374. Costs barely matter here (about 12 resizes a year per market).

## Plain English
The sleeve does what it was built for. It is nearly uncorrelated with the Nasdaq core, and it made money in 2022 when
the book lost. Adding it lifted the book's Sharpe by about 0.09 in both eras, with costs, and never made the worst
drop worse. But the sleeve on its own is weak (Sharpe 0.35-0.51) and lumpy: it lost 8-10% in 2016, 2018 and 2023.
A gain of 0.09 is small next to the noise. The bootstrap says roughly a 1 in 4 chance the true gain is zero or
negative in each era. Also, trend in gold and bonds is a well-known, crowded premium, so the 2011-2020 result is the
fairer guide, not a surprise discovery. Small caveats: GC/ZN daily closes are about 4 hours after the Nasdaq close, and
the data ends 30 Oct 2026, so the sleeve is flat for Nov 2026.

Trial count after this batch: about 331.
