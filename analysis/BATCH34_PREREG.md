# Batch 34 pre-registration: is G3 real once we count every test we ran? (20 Nov 2026)

Written and committed before `batch34.py` runs. Analysis only: nothing here changes the race rules.

Why: about 299 trials went into picking G3. The best of many tests always looks good partly by luck. Two public tools
check for that: the deflated Sharpe ratio (Bailey & López de Prado 2014, via the MIT `purgedcv` package) and a
reality-check style threshold for the best of N (the idea from NostroBenJ/intraday-strategy-replication, which used
White's reality check on 50 rules). Also from that repo: the noise-area breakout our noise band rule comes from
(Zarattini, Aziz & Barbon, published May 2024) faded after publication on NQ and ES. We check our version.

Data: the same daily return series as batches 29-33 (G3 and the package at 1% risk per R), both eras:
2021-26 (built on) and 2010-20 (sealed era, opened once, used for comparisons since, so not independent).

## Test A: deflated Sharpe of G3 (is it better than zero after ~299 tries?)
- Trials: N = 299. Variance of Sharpe across trials: every distinct trial result saved in `analysis/*.json`, per era.
  Also reported with N = 50 (trials are heavily correlated, so the true count is lower).
- Pass: deflated Sharpe probability >= 0.95 in BOTH eras at N = 299.

## Test B: is G3's gain over the plain package real after ~299 tries?
- Series: daily G3 return minus daily package return. One-sided test that the mean is above zero.
- t-statistic with Newey-West errors (5 lags), each era and both eras pooled; plus a stationary-bootstrap p-value
  (`arch`, 10,000 draws, average block 10 days, seed 20261120).
- Pass: pooled t >= 3.59 (Bonferroni bar for the best of 299 at 5%, one-sided). Also reported against the bar for
  the best of 50 (t >= 2.88).
- If it fails: G3 stays the frozen main book (the freeze rules already chose it, and it cannot be worse than the package
  by construction of the test), but the write-up must say its gain over the package is not proven.

## Test C: the noise band rule before and after the paper (May 2024)
- Split noise band trades at 1 May 2024. Report trades, mean R, t of mean R, and the share of total R from the best 10
  days, before and after. Same table for the other three rules for comparison.
- No pass mark (descriptive). Flag if the after-publication mean R is <= 0 or its t < 1.
