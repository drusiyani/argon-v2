# Batch 14 pre-registration (14 Nov 2026) — written and committed BEFORE any batch 14 code was run

Analysis only (does not touch the race). Dru asked to look even harder. Hand-scanning this data is used up (about 195
trials), so this batch does three things that are NOT another scan. Judged by the growth mark from batch 13 unless stated.

## Part A — Does the model work on a market it never trained on? (validation only)
The batch 13 walk-forward model (W1: ridge, λ = 100, 24 features, refitted each year on earlier years' NASDAQ trades only)
is used, unchanged, to size trades of the same three rules run on the S&P future (ES; costs 0.5 pts, 0.10R cost cap).
Features are computed from the S&P's own prices and the S&P rules' own results; the VXN weight is the same.
No S&P trade is ever used to fit anything.
**Replicates** if, in all three periods (2013–17, 2018–20, 2021–26), the S&P trades the model sizes ×1.5 have a higher
average R after costs than those it sizes ×0.5.

## Part B — S&P trades as a new source of profit (only if Part A replicates)
Condition: Part A replicates AND the ×1.5 group's average R after costs is above zero in BOTH 2013–20 and 2021–26.
If so: package + every S&P trade the model puts in its top third, each at the usual 0.5 × 1% risk. Growth mark.
If the condition is not met, Part B is not run and that is the result.

## Part C — Give the model new information and let it decide, using only the past
W3 = W1's 24 features plus 28 new ones, all known at entry:
- Trade path (8): distance from the open, position in the day's range so far, distance from VWAP, opening 5-minute range,
  realised 1-minute movement so far, real futures volume so far vs its 20-day median, the S&P's move from its open,
  Nasdaq move minus S&P move (the direction-dependent ones signed by trade side, moves in ATR units).
- Pre-market (4): 04:00–09:29 volume vs its 20-day median, the 08:30 five-minute reaction, overnight range, overnight
  direction vs trade.
- Calendar (9): options-expiry week, Fed decision tomorrow, Fed decision yesterday, last two days of the month, first two
  days of the month, Tuesday, Wednesday, Thursday, Friday.
- Outside data (7), each read at least two days late: 10-year yield 5-day change, 10-year minus 2-year yield, dollar index
  5-day change, news-based Economic Policy Uncertainty index (7-day average vs its one-year median), oil 5-day change
  (all from FRED), VIX divided by 3-month VIX, VXN 5-day change.
Refitted at the start of each MONTH on all earlier trades (needs ≥ 500). Same ridge, same λ = 100, same ×0.5 / ×1 / ×1.5 rule.
W1m = W1's 24 features with the same monthly refit, to show what monthly refitting does on its own.
**Rule for replacing W1:** W3 replaces W1 only if it meets the growth mark AND beats W1 on return and Sortino in BOTH eras.
If W3 does not, W1m replaces W1 by the same rule. Otherwise W1 stays. No other variants.

## Part D — The candidate
Package with the chosen model's sizing, plus the S&P trades if Part B passed. Reported: growth mark, the lever.py test at
1.25×, and the shuffle luck check from batch 13 for the chosen model.

## Not allowed after seeing results
No changing features, λ, refit schedule, multipliers, the replication rule, or the replacement rule.
