# Batch 46 (28 Nov 2026): gold vs the real interest rate

Written and pushed before any run. Source: issue #5. One idea = one trial. No parameter sweep.

## Why
Gold pays no interest, so the textbook driver is the real yield: when real yields fall, holding gold costs less and
it tends to rise (Erb & Harvey, "The Golden Dilemma", 2013). Known risk: the link broke in 2022-2024, when gold rose
while real yields rose (central-bank buying). This test checks whether it still adds anything.

## Data (fixed)
- Gold returns: `data/extra/GC_daily.csv.gz` (as batch 42).
- Real yield: FRED series DFII10 (10-year TIPS yield, daily), downloaded fresh by the workflow from
  https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10 at run time. Missing values ('.') dropped.

## Rules (fixed)
- At each GC month end (date t): ry_now = last DFII10 value dated on or before t; ry_then = last value dated on or
  before the same calendar day 3 months earlier. Change = ry_now - ry_then (percentage points).
- Signal: short gold if change > 0, long if change < 0, flat if exactly 0.
- Weight = 0.05 / (60-day realised vol x sqrt(252)) from GC returns. Hold to the next month end. Tick 0.10.
- This is a SECOND gold leg added on top of the batch 42 sleeve (which already holds gold by trend).
- First signal: end of Jun 2011, the same start as batch 42.

## The book it is compared with
- Base = the batch 42 book (Nasdaq core + the four rules at 0.5%, exactly as in `analysis/batch42.py`) PLUS the batch 42
  GC+ZN trend sleeve, because that sleeve is the live candidate for Amendment 14. The idea is added on top of that.
- Also reported (not the bar): the same comparison against the book alone, without the batch 42 sleeve.

## Pass bar (fixed)
- Sharpe of base + idea must beat the base, after costs, in BOTH eras: lockbox2010 (2011-2020) and databento
  (2021/22-2026). Both runs with `ARGON_FULL=1`.
- Luck check as in NIGHTLY.md (paired block bootstrap of the gain vs the base, 21-day blocks, 2000 draws, seed 42).
  A PASS with era-2 share above 0.10 is labelled "PASS (weak, could be luck)".

## Data handling (same as batch 42)
- Daily Databento bars; Sunday/Saturday bars merged into the next weekday; on an `instrument_id` change the day's
  return = 0 and 1 tick of roll cost is charged on the position held. Rebalance cost: 1 tick x |change in weight| / price.
- The idea's daily returns are summed onto Nasdaq sessions exactly as batch 42 does (`on_sessions`).
- Run in GitHub Actions only, one run, both eras. Code bugs may be fixed and rerun; every rerun is noted.

## Also reported
- The leg's own Sharpe, its Sharpe by era split 2011-2020 / 2022-2026, correlation with the batch 42 gold leg, 2022 return.
- Trial count: about 335.

## Not allowed after seeing results
Changing the 3-month window, the sign rule, 5% vol, the 60-day window, the series, costs, base book or pass bar.
