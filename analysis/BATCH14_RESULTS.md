# Batch 14 results (14 Nov 2026): the model does not carry over to the S&P, new information adds nothing, monthly refit helps slightly

Pre-registration: `BATCH14_PREREG.md` (committed before the run). Code: `batch14_dump.py`, `batch14.py`. Raw: `batch14.json`.

## Part A — S&P transfer: does NOT replicate (2 of 3 periods; the bar was 3 of 3)
The Nasdaq-trained yearly model sized 5,147 S&P trades it never saw. Average R after costs, sized ×1.5 vs ×0.5:

| Period | ×1.5 | ×0.5 | Right way round? |
|---|---|---|---|
| 2013–17 | −0.056 | −0.068 | yes, barely |
| 2018–20 | −0.071 | +0.005 | no |
| 2021–26 | −0.009 | −0.053 | yes |

For comparison, on the Nasdaq the same model's gaps were +0.07, +0.27 and +0.18. The S&P trades it liked best still lost
money in both eras (−0.064R and −0.009R a trade).

## Part B — S&P trades as a new profit source: NOT RUN (condition not met)

## Part C — New information
Each cell: return a year / Sortino / worst drop / bootstrap chance of a drop worse than −35%.

| | 2021–26 | 2010–20 | Growth mark |
|---|---|---|---|
| Package baseline | +56.4% / 3.18 / −19.4% / 1.0% | +21.6% / 1.75 / −23.5% / 7.4% | — |
| W1: 24 features, refit yearly (batch 13) | +71.5% / 3.64 / −22.2% / 1.2% | +26.8% / 2.08 / −24.4% / 6.9% | yes |
| W1m: 24 features, refit monthly | +72.3% / 3.67 / −22.5% / 1.2% | +28.1% / 2.15 / −23.5% / 6.2% | yes |
| W3: 52 features (path, volume, pre-market, calendar, outside data), monthly | +70.6% / 3.67 / −19.8% / 0.9% | +28.3% / 2.19 / −25.6% / 8.8% | no (2010–20 crash chance above the index's 8.3%) |

- The 28 new features (VWAP distance, real volume, the 08:30 reaction, expiry week, yields, the dollar, oil, the
  news-based policy-uncertainty index, VIX term structure) did not improve the model out of sample. In the latest fitted
  model the largest weights are still yesterday's direction and yesterday's rules result; no new feature is in the top three.
- By the pre-registered rule W3 does not replace W1, and **W1m replaces W1** (meets the growth mark and beats W1 on return
  and Sortino in both eras, by 0.8 and 1.3 points a year).
- Luck check for W1m: 4 of 300 shuffles beat it in 2021–26, 1 of 300 in 2010–20 (shuffled averages +59.3% and +22.0%).

## Part D — Candidate: the package with W1m sizing
+72.3% / −22.5% (2021–26) and +28.1% / −23.5% (2010–20). Strict mark: no. Growth mark: yes.
Leverage at 1.25×: fails (2010–20 crash chance 44.5%, limit 20%).

## What this batch says
Three different ways of looking harder gave one small gain and two "no"s. The sizing model looks real on the Nasdaq but is
not a general law of markets, and information beyond price history and yesterday's result does not help it. On this data
the ceiling is about +72% / +28% in backtest, and live results should be expected to come in lower.
