# Batch 44 (28 Nov 2026): dollar trend - 12-month momentum on five CME currency futures

Written and pushed before any run. Source: issue #3 (Dru asked for better US dollar and gold strategies).
One idea = one trial. No parameter sweep.

## Why
Trend in currencies has the same long record as trend in bonds and gold (Moskowitz, Ooi & Pedersen, "Time Series
Momentum", JFE 2012). The dollar is a different risk from the Nasdaq and from the batch 42 sleeve.

## Data (fixed)
- `data/extra/{6E,6J,6B,6A,6C}_daily.csv.gz`: euro, yen, pound, Australian and Canadian dollar futures (each quoted in
  USD), Databento ohlcv-1d, front month by volume (`.v.0`), Jun 2010 - Oct 2026.

## Rules (fixed)
- Exactly the batch 42 rule per market: at each month end, sign of the 12-month return; weight = 0.025 / (60-day
  realised vol x sqrt(252)); hold to the next month end. 2.5% (not 5%) because there are five markets.
- Ticks: 6E 0.00005, 6J 0.0000005, 6B 0.0001, 6A 0.00005, 6C 0.00005.
- First signal end of Jun 2011.

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
- The FX leg's own Sharpe, each currency's Sharpe, correlation with the core and with the batch 42 sleeve, 2022 return.
- Trial count: about 333.

## Not allowed after seeing results
Changing the markets, lookback, 2.5% vol target, 60-day window, monthly rebalance, costs, base book or pass bar.
